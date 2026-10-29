"""Incremental SQLite storage and compact public projection."""

import sqlite3
from dataclasses import astuple, fields
from pathlib import Path

from .domain import ImportFailure, Limits, VoteRecord

KEY = "election,uf,municipality,zone,section"
RECORD_COLUMNS = ",".join(f.name for f in fields(VoteRecord))
RECORD_SCHEMA = """
 election TEXT NOT NULL, year INTEGER NOT NULL, round INTEGER NOT NULL,
 uf TEXT NOT NULL, municipality TEXT NOT NULL, municipality_name TEXT NOT NULL,
 zone TEXT NOT NULL, section TEXT NOT NULL, local TEXT NOT NULL,
 votable TEXT NOT NULL, candidate_id TEXT, name TEXT NOT NULL, kind TEXT NOT NULL,
 votes INTEGER NOT NULL CHECK(votes>=0), eligible INTEGER, turnout INTEGER,
 abstention INTEGER, context TEXT NOT NULL, extra TEXT NOT NULL, line INTEGER NOT NULL
"""


def connect(path: Path, limits: Limits = Limits()) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("PRAGMA temp_store=FILE")
    connection.execute(f"PRAGMA cache_size=-{limits.sqlite_cache_kib}")
    return connection


def create_unit(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"CREATE TABLE records ({RECORD_SCHEMA}, PRIMARY KEY({KEY},context,votable)) WITHOUT ROWID"
    )
    connection.execute("CREATE TABLE checkpoint (json TEXT NOT NULL)")


def insert_records(connection: sqlite3.Connection, records) -> None:
    query = f"INSERT INTO records VALUES ({','.join('?' for _ in fields(VoteRecord))})"
    batch = []
    try:
        for record in records:
            batch.append(astuple(record))
            if len(batch) >= 2000:
                connection.executemany(query, batch)
                batch.clear()
        connection.executemany(query, batch)
    except sqlite3.IntegrityError as exc:
        raise ImportFailure(
            f"Registro duplicado/inválido na fonte; última linha lida: {record.line}"
        ) from exc


def create_stage(connection: sqlite3.Connection) -> None:
    connection.executescript(f"""
    CREATE TABLE raw (source_id TEXT NOT NULL, format TEXT NOT NULL, {RECORD_SCHEMA});
    CREATE TABLE sources (
      id TEXT PRIMARY KEY, archive TEXT NOT NULL, member TEXT NOT NULL,
      sha256 TEXT NOT NULL, format TEXT NOT NULL, verification TEXT NOT NULL
    );
    """)


def project(connection: sqlite3.Connection, profile: str) -> None:
    """No sum across BU contexts. Public results prefer section source per location."""
    connection.executescript(f"""
    CREATE INDEX raw_location ON raw({KEY},format,votable);
    CREATE TEMP VIEW location_families AS
      SELECT {KEY}, MAX(format='section') has_section, COUNT(DISTINCT CASE WHEN format='bweb'
        THEN source_id||':'||context END) bu_contexts FROM raw GROUP BY {KEY};
    CREATE TEMP VIEW chosen AS SELECT r.* FROM raw r JOIN location_families l USING({KEY})
      WHERE (l.has_section=1 AND r.format='section') OR
            (l.has_section=0 AND l.bu_contexts=1 AND r.format='bweb');
    """)
    duplicate = connection.execute(
        f"SELECT {KEY},votable,COUNT(*) FROM chosen GROUP BY {KEY},votable HAVING COUNT(*)>1 LIMIT 1"
    ).fetchone()
    if duplicate:
        raise ImportFailure(f"Múltiplas fontes primárias para o mesmo resultado: {duplicate}")
    ambiguous_only = connection.execute(
        "SELECT COUNT(*) FROM location_families WHERE has_section=0 AND bu_contexts<>1"
    ).fetchone()[0]
    if ambiguous_only:
        raise ImportFailure(f"{ambiguous_only} seções sem fonte primária inequívoca")
    # Identifiers/metadata must be stable within an election/location, not arbitrarily MIN'd.
    for query, message in [
        (
            f"SELECT {KEY} FROM chosen GROUP BY {KEY} HAVING COUNT(DISTINCT local)>1 OR COUNT(DISTINCT municipality_name)>1 LIMIT 1",
            "Localidade inconsistente",
        ),
        (
            "SELECT election FROM chosen GROUP BY election HAVING COUNT(DISTINCT year||':'||round)>1 LIMIT 1",
            "Código de eleição ambíguo",
        ),
        (
            "SELECT election,votable FROM chosen GROUP BY election,votable HAVING COUNT(DISTINCT kind)>1 OR COUNT(DISTINCT candidate_id)>1 OR COUNT(DISTINCT name)>1 LIMIT 1",
            "Identificação de candidato inconsistente",
        ),
    ]:
        if row := connection.execute(query).fetchone():
            raise ImportFailure(f"{message}: {row}")
    connection.executescript(f"""
    CREATE TABLE metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE elections (id TEXT PRIMARY KEY,year INTEGER NOT NULL,round INTEGER NOT NULL,
      office TEXT NOT NULL CHECK(office='president'));
    INSERT INTO elections SELECT DISTINCT election,year,round,'president' FROM chosen ORDER BY election;
    CREATE TABLE sections (id INTEGER PRIMARY KEY,election TEXT NOT NULL REFERENCES elections(id),
      uf TEXT NOT NULL,municipality TEXT NOT NULL,municipality_name TEXT NOT NULL,
      zone TEXT NOT NULL,section TEXT NOT NULL,local TEXT NOT NULL,
      UNIQUE({KEY}));
    INSERT INTO sections(election,uf,municipality,municipality_name,zone,section,local)
      SELECT election,uf,municipality,MIN(municipality_name),zone,section,MIN(local)
      FROM chosen GROUP BY {KEY} ORDER BY {KEY};
    CREATE TABLE candidates (id INTEGER PRIMARY KEY,election TEXT NOT NULL REFERENCES elections(id),
      number TEXT NOT NULL,source_candidate_id TEXT,name TEXT NOT NULL,kind TEXT NOT NULL,
      UNIQUE(election,number));
    INSERT INTO candidates(election,number,source_candidate_id,name,kind)
      SELECT election,votable,MIN(candidate_id),MIN(name),kind FROM chosen
      GROUP BY election,votable,kind ORDER BY election,votable;
    CREATE TABLE results (section_id INTEGER NOT NULL REFERENCES sections(id),
      candidate_id INTEGER NOT NULL REFERENCES candidates(id),votes INTEGER NOT NULL CHECK(votes>=0),
      source_id TEXT NOT NULL REFERENCES sources(id),source_line INTEGER NOT NULL,
      PRIMARY KEY(section_id,candidate_id)) WITHOUT ROWID;
    INSERT INTO results SELECT s.id,c.id,r.votes,r.source_id,r.line FROM chosen r
      JOIN sections s USING({KEY}) JOIN candidates c ON c.election=r.election AND c.number=r.votable
      ORDER BY s.id,c.id;
    CREATE TABLE section_totals (section_id INTEGER PRIMARY KEY REFERENCES sections(id),
      counted INTEGER NOT NULL,nominal INTEGER,blank INTEGER,null_votes INTEGER,
      eligible INTEGER,turnout INTEGER,abstention INTEGER,bu_source_id TEXT REFERENCES sources(id),
      bu_context TEXT,totals_status TEXT NOT NULL DEFAULT 'unavailable_no_unique_bu',
      comparison TEXT NOT NULL DEFAULT 'not_verifiable');
    INSERT INTO section_totals(section_id,counted,nominal,blank,null_votes)
      SELECT s.id,SUM(r.votes),SUM(CASE WHEN c.kind='nominal' THEN r.votes END),
        SUM(CASE WHEN c.kind='blank' THEN r.votes END),SUM(CASE WHEN c.kind='null' THEN r.votes END)
      FROM results r JOIN sections s ON s.id=r.section_id JOIN candidates c ON c.id=r.candidate_id
      GROUP BY s.id ORDER BY s.id;
    CREATE INDEX results_candidate ON results(candidate_id,section_id);
    CREATE TABLE aggregates AS SELECT s.election,s.uf,c.id candidate_id,SUM(r.votes) votes,
      COUNT(*) sections_with_record FROM results r JOIN sections s ON s.id=r.section_id
      JOIN candidates c ON c.id=r.candidate_id GROUP BY s.election,s.uf,c.id ORDER BY s.election,s.uf,c.id;
    CREATE UNIQUE INDEX aggregates_scope ON aggregates(election,uf,candidate_id);
    """)
    if profile == "analyst":
        connection.execute(
            "CREATE TABLE analyst_presidential AS SELECT * FROM raw ORDER BY source_id,line"
        )


def compact(connection: sqlite3.Connection) -> None:
    connection.executescript("DROP VIEW chosen; DROP VIEW location_families; DROP TABLE raw;")
    connection.commit()
    connection.execute("VACUUM")
    connection.execute("PRAGMA optimize")
    connection.commit()
