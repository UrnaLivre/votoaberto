"""Independent mathematical checks and conservative source reconciliation."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .domain import ImportFailure
from .storage import KEY


def reconcile(connection: sqlite3.Connection, report_path: Path) -> dict:
    # One context per source/location is required; no equipment/section equivalence inferred.
    connection.executescript(f"""
    CREATE TEMP VIEW bu_single AS SELECT r.* FROM raw r JOIN location_families l USING({KEY})
      WHERE r.format='bweb' AND l.bu_contexts=1;
    CREATE TEMP VIEW section_rows AS SELECT * FROM raw WHERE format='section';
    """)
    stats = {
        "matched_rows": 0,
        "different_rows": 0,
        "only_section_rows": 0,
        "only_bu_rows": 0,
        "ambiguous_locations": 0,
        "bu_math_errors": 0,
    }
    stats["ambiguous_locations"] = connection.execute(
        "SELECT COUNT(*) FROM location_families WHERE bu_contexts>1"
    ).fetchone()[0]

    def emit(stream, severity, code, data):
        stream.write(
            json.dumps({"severity": severity, "code": code, "record": data}, ensure_ascii=False)
            + "\n"
        )

    with report_path.open("w", encoding="utf8") as report:
        for row in connection.execute(
            f"SELECT {KEY},bu_contexts FROM location_families WHERE bu_contexts>1"
        ):
            emit(report, "warning", "ambiguous_bu", row)
        # Totals must agree within BU context, and sum of the presidential rows equals turnout.
        bu_groups = connection.execute(f"""SELECT {KEY},MIN(eligible),MIN(turnout),MIN(abstention),SUM(votes),
          MIN(source_id),MIN(context),COUNT(DISTINCT eligible),COUNT(DISTINCT turnout),
          COUNT(DISTINCT abstention),COUNT(*)-COUNT(eligible),COUNT(*)-COUNT(turnout),
          COUNT(*)-COUNT(abstention),MIN(extra) FROM bu_single GROUP BY {KEY}""")
        for row in bu_groups:
            key, values = row[:5], row[5:]
            eligible, turnout, abstention, counted, source, context = values[:6]
            inconsistent = any(v > 1 for v in values[6:9])
            inconsistent |= any(
                d == 1 and n > 0 for d, n in zip(values[6:9], values[9:12], strict=True)
            )
            if eligible is not None and turnout is not None and abstention is not None:
                inconsistent |= eligible != turnout + abstention or turnout > eligible
            if eligible is not None and turnout is not None:
                inconsistent |= turnout > eligible
            if turnout is not None:
                inconsistent |= counted != turnout
            if inconsistent:
                stats["bu_math_errors"] += 1
                emit(report, "divergence", "bu_mathematics", row)
            else:
                raw_totals = json.loads(values[12])
                totals_status = json.dumps(
                    {
                        key: (
                            "not_recorded"
                            if raw_totals[key] in ("#NE", "#NE#", "-3")
                            else "missing"
                            if raw_totals[key] in ("#NULO", "#NULO#", "-1", "")
                            else "present"
                        )
                        for key in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")
                    },
                    sort_keys=True,
                )
                connection.execute(
                    """UPDATE section_totals SET eligible=?,turnout=?,abstention=?,
                    bu_source_id=?,bu_context=?,totals_status=? WHERE section_id=(SELECT id FROM sections WHERE
                    election=? AND uf=? AND municipality=? AND zone=? AND section=?)""",
                    (eligible, turnout, abstention, source, context, totals_status, *key),
                )
        join = (
            " AND ".join(f"s.{key}=b.{key}" for key in KEY.split(",")) + " AND s.votable=b.votable"
        )
        query = f"""SELECT s.election,s.uf,s.municipality,s.zone,s.section,s.votable,s.votes,b.votes,
          s.source_id,s.line,b.source_id,b.line,s.local,b.local FROM section_rows s
          LEFT JOIN bu_single b ON {join}
          UNION ALL
          SELECT b.election,b.uf,b.municipality,b.zone,b.section,b.votable,NULL,b.votes,
          NULL,NULL,b.source_id,b.line,NULL,b.local FROM bu_single b
          LEFT JOIN section_rows s ON {join} WHERE s.votes IS NULL"""
        for row in connection.execute(query):
            if row[6] is None:
                stats["only_bu_rows"] += 1
                emit(report, "not_verifiable", "only_bu", row)
            elif row[7] is None:
                stats["only_section_rows"] += 1
                # Full nationwide section source naturally has no BU outside supplied SC coverage.
                emit(report, "not_verifiable", "only_section", row)
            elif row[6] != row[7] or row[12] != row[13]:
                stats["different_rows"] += 1
                emit(report, "divergence", "source_difference", row)
            else:
                stats["matched_rows"] += 1
        # Mark only complete row-set equality for an unambiguous section, never global verification.
        connection.execute(f"""UPDATE section_totals SET comparison='matched'
          WHERE section_id IN (SELECT sec.id FROM sections sec JOIN location_families l USING({KEY})
          WHERE l.has_section=1 AND l.bu_contexts=1 AND NOT EXISTS (
            SELECT 1 FROM section_rows s LEFT JOIN bu_single b ON {join}
            WHERE s.election=sec.election AND s.uf=sec.uf AND s.municipality=sec.municipality
              AND s.zone=sec.zone AND s.section=sec.section
              AND (b.votes IS NULL OR b.votes<>s.votes OR b.local<>s.local))
          AND NOT EXISTS (SELECT 1 FROM bu_single b LEFT JOIN section_rows s ON {join}
            WHERE b.election=sec.election AND b.uf=sec.uf AND b.municipality=sec.municipality
              AND b.zone=sec.zone AND b.section=sec.section AND s.votes IS NULL))""")
    connection.executescript("DROP VIEW bu_single; DROP VIEW section_rows;")
    return stats


def validate_database(path: Path) -> dict:
    if not path.is_file():
        raise ImportFailure("Banco inexistente")
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ImportFailure("Versão de schema não suportada")
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = db.execute("PRAGMA foreign_key_check").fetchall()
        rows = db.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        mathematical = db.execute("""SELECT COUNT(*) FROM section_totals WHERE
          (eligible IS NOT NULL AND turnout IS NOT NULL AND abstention IS NOT NULL
             AND eligible<>turnout+abstention) OR (turnout IS NOT NULL AND counted<>turnout)
             OR (eligible IS NOT NULL AND turnout IS NOT NULL AND turnout>eligible)""").fetchone()[
            0
        ]
        aggregate_errors = db.execute("""SELECT COUNT(*) FROM (SELECT s.election,s.uf,r.candidate_id,SUM(r.votes) votes
          FROM results r JOIN sections s ON s.id=r.section_id GROUP BY s.election,s.uf,r.candidate_id
          EXCEPT SELECT election,uf,candidate_id,votes FROM aggregates)""").fetchone()[0]
        totals_errors = db.execute("""SELECT COUNT(*) FROM section_totals t WHERE counted<>
          (SELECT SUM(votes) FROM results r WHERE r.section_id=t.section_id)""").fetchone()[0]
        aggregate_errors += db.execute("""SELECT COUNT(*) FROM (
          SELECT election,uf,candidate_id,votes FROM aggregates EXCEPT
          SELECT s.election,s.uf,r.candidate_id,SUM(r.votes) FROM results r
          JOIN sections s ON s.id=r.section_id GROUP BY s.election,s.uf,r.candidate_id)""").fetchone()[
            0
        ]
        totals_errors += db.execute("""SELECT COUNT(*) FROM sections s
          LEFT JOIN section_totals t ON t.section_id=s.id WHERE t.section_id IS NULL""").fetchone()[
            0
        ]
        category_errors = db.execute("""SELECT COUNT(*) FROM section_totals t WHERE
          nominal IS NOT (SELECT SUM(r.votes) FROM results r JOIN candidates c ON c.id=r.candidate_id
            WHERE r.section_id=t.section_id AND c.kind='nominal') OR
          blank IS NOT (SELECT SUM(r.votes) FROM results r JOIN candidates c ON c.id=r.candidate_id
            WHERE r.section_id=t.section_id AND c.kind='blank') OR
          null_votes IS NOT (SELECT SUM(r.votes) FROM results r JOIN candidates c ON c.id=r.candidate_id
            WHERE r.section_id=t.section_id AND c.kind='null')""").fetchone()[0]
        election_errors = db.execute("""SELECT COUNT(*) FROM results r
          JOIN sections s ON s.id=r.section_id JOIN candidates c ON c.id=r.candidate_id
          WHERE c.election<>s.election""").fetchone()[0]
        coverage = [
            dict(zip(("election", "round", "uf", "sections", "rows", "votes"), row, strict=True))
            for row in db.execute("""
          SELECT s.election,e.round,s.uf,COUNT(DISTINCT s.id),COUNT(*),SUM(r.votes)
          FROM results r JOIN sections s ON s.id=r.section_id JOIN elections e ON e.id=s.election
          GROUP BY s.election,e.round,s.uf ORDER BY e.round,s.uf""")
        ]
        candidates = [
            dict(zip(("round", "uf", "number", "name", "kind", "votes"), row, strict=True))
            for row in db.execute("""
          SELECT e.round,s.uf,c.number,c.name,c.kind,SUM(r.votes)
          FROM results r JOIN sections s ON s.id=r.section_id JOIN elections e ON e.id=s.election
          JOIN candidates c ON c.id=r.candidate_id GROUP BY e.round,s.uf,c.id ORDER BY e.round,s.uf,c.number""")
        ]
        return {
            "valid": integrity == "ok"
            and not foreign_keys
            and rows > 0
            and not mathematical
            and not aggregate_errors
            and not totals_errors
            and not category_errors
            and not election_errors,
            "sqlite_integrity": integrity,
            "foreign_key_errors": foreign_keys,
            "mathematical_errors": mathematical,
            "aggregate_errors": aggregate_errors,
            "section_total_errors": totals_errors,
            "category_total_errors": category_errors,
            "election_link_errors": election_errors,
            "result_rows": rows,
            "coverage": coverage,
            "candidate_totals": candidates,
            "comparison": dict(
                db.execute("SELECT comparison,COUNT(*) FROM section_totals GROUP BY comparison")
            ),
        }
