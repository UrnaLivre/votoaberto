"""Sequential presidential projection: primary units + one BWEB/partition at a time."""

import json
import re
import sqlite3
import time
from dataclasses import replace

from .discovery import drain, member_stream
from .domain import ImportFailure
from .integrity import fingerprint, hashes
from .parsers import inspect_member, parse
from .storage import (
    RECORD_COLUMNS,
    compact,
    connect,
    create_stage,
    create_unit,
    insert_records,
    project,
)
from .validation import reconcile


def public_records(records, profile):
    for record in records:
        if profile == "public":
            extra = json.loads(record.extra)
            extra = {
                key: extra[key]
                for key in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "DS_SECOES_AGREGADAS")
                if key in extra
            }
            record = replace(record, extra=json.dumps(extra, ensure_ascii=False, sort_keys=True))
        yield record


def merge_partition(final, partition):
    final.execute("ATTACH DATABASE ? AS part", (str(partition),))
    try:
        for table, key in (("sources", "id"), ("elections", "id")):
            # Matching keys must contain identical metadata, never silently pick one.
            if final.execute(
                f"SELECT 1 FROM part.{table} p JOIN main.{table} m USING({key}) WHERE "
                + " OR ".join(
                    f"p.{row[1]} IS NOT m.{row[1]}"
                    for row in final.execute(f"PRAGMA main.table_info({table})")
                    if row[1] != key
                )
                + " LIMIT 1"
            ).fetchone():
                raise ImportFailure(f"Identificação inconsistente entre partições: {table}")
            final.execute(f"INSERT OR IGNORE INTO main.{table} SELECT * FROM part.{table}")
        if final.execute("""SELECT 1 FROM part.candidates p JOIN main.candidates m
            ON p.election=m.election AND p.number=m.number WHERE p.name<>m.name OR p.kind<>m.kind
            OR (p.source_candidate_id IS NOT NULL AND m.source_candidate_id IS NOT NULL
              AND p.source_candidate_id<>m.source_candidate_id) LIMIT 1""").fetchone():
            raise ImportFailure("Identificação de candidato inconsistente entre partições")
        final.execute("""INSERT OR IGNORE INTO main.candidates(election,number,source_candidate_id,name,kind)
            SELECT election,number,source_candidate_id,name,kind FROM part.candidates ORDER BY id""")
        final.execute("""UPDATE main.candidates SET source_candidate_id=(SELECT p.source_candidate_id
            FROM part.candidates p WHERE p.election=candidates.election AND p.number=candidates.number)
            WHERE source_candidate_id IS NULL AND EXISTS (SELECT 1 FROM part.candidates p
            WHERE p.election=candidates.election AND p.number=candidates.number AND p.source_candidate_id IS NOT NULL)""")
        offset = final.execute("SELECT COALESCE(MAX(id),0) FROM main.sections").fetchone()[0]
        final.execute(
            "INSERT INTO main.sections SELECT id+?,election,uf,municipality,municipality_name,zone,section,local FROM part.sections ORDER BY id",
            (offset,),
        )
        final.execute(
            """INSERT INTO main.results SELECT r.section_id+?,m.id,r.votes,r.source_id,r.source_line
            FROM part.results r JOIN part.candidates p ON p.id=r.candidate_id
            JOIN main.candidates m ON p.election=m.election AND p.number=m.number ORDER BY r.section_id,m.id""",
            (offset,),
        )
        columns = [row[1] for row in final.execute("PRAGMA main.table_info(section_totals)")]
        final.execute(
            "INSERT INTO main.section_totals SELECT section_id+?,"
            + ",".join(columns[1:])
            + " FROM part.section_totals ORDER BY section_id",
            (offset,),
        )
        if final.execute(
            "SELECT 1 FROM part.sqlite_master WHERE name='analyst_presidential'"
        ).fetchone():
            final.execute(
                "CREATE TABLE IF NOT EXISTS main.analyst_presidential AS SELECT * FROM part.analyst_presidential WHERE 0"
            )
            final.execute(
                "INSERT INTO main.analyst_presidential SELECT * FROM part.analyst_presidential"
            )
        final.commit()
    finally:
        final.rollback()
        final.execute("DETACH DATABASE part")


def build(config, root, archives, semantics, work, stage, progress, identity, write_json):
    """Read each CSV once; checkpoints opt in to retention and are hash checked on reuse."""
    from .reporting import DivergenceReport

    stats, primary, bweb = [], [], []
    reused = 0
    parse_seconds = consolidation_seconds = 0.0
    old_units = {}
    if config.resume and config.storage.retain_checkpoints:
        for ledger in sorted((work.output / ".runs").glob("*.json")):
            try:
                value = json.loads(ledger.read_text(encoding="utf8"))
                if (
                    value.get("ownership_version") != 1
                    or value.get("checkpoint_key") != work.checkpoint_key
                    or not re.fullmatch(r"[a-f0-9]{32}", value.get("run_id", ""))
                ):
                    continue
                prior = (
                    work.output / config.storage.work_directory / value["run_id"] / "checkpoints"
                )
                from .workspace import no_links

                no_links(prior)
                for meta_path in prior.glob("*.json"):
                    no_links(meta_path)
                    meta = json.loads(meta_path.read_text(encoding="utf8"))
                    unit = meta_path.with_suffix(".sqlite")
                    no_links(unit)
                    recorded = {entry["path"]: entry["identity"] for entry in value["created"]}
                    info = unit.stat()
                    if (
                        recorded.get(str(unit)) == [info.st_dev, info.st_ino]
                        and unit.is_file()
                        and hashes(unit)["sha256"] == meta["sha256"]
                    ):
                        db = sqlite3.connect(unit.resolve().as_uri() + "?mode=ro", uri=True)
                        try:
                            embedded = json.loads(
                                db.execute("SELECT json FROM checkpoint").fetchone()[0]
                            )
                            if embedded == {"unit_id": meta["unit_id"], "stats": meta["stats"]}:
                                old_units[meta["unit_id"]] = (unit, meta["stats"])
                        finally:
                            db.close()
            except (OSError, ValueError, KeyError, sqlite3.Error, TypeError):
                continue
    for item in archives:
        for member in item["members"]:
            if member["directory"]:
                continue
            description = inspect_member(
                root / item["path"], member["name"], config.limits, sample_rows=0
            )
            if description["status"] != "supported":
                if member["extension"] != ".pdf":
                    raise ImportFailure(f"Formato não suportado: {item['path']}:{member['name']}")
                with member_stream(root / item["path"], member["name"], config.limits) as stream:
                    drain(stream, config.limits)
                stats.append(
                    {
                        "archive": item["path"],
                        "member": member["name"],
                        "status": "auxiliary_unsupported",
                        "crc_checked": True,
                    }
                )
                continue
            source_id = identity([item["hashes"]["sha256"], member["name"]])
            unit = (item, member, source_id)
            (primary if description["format"] == "section" else bweb).append(unit)

    def load(unit):
        nonlocal reused, parse_seconds
        item, member, source_id = unit
        source_path = root / item["path"]
        before = fingerprint(source_path)
        if list(before) != item["fingerprint"]:
            raise ImportFailure("Fonte mudou desde o inventário")
        unit_id = identity([source_id, semantics])
        if unit_id in old_units:
            path, source_stats = old_units[unit_id]
            reused += 1
            progress(f"Checkpoint conferido: {item['name']}:{member['name']}")
        else:
            path = work.root / "checkpoints" / (unit_id + ".sqlite")
            source_stats = {}
            progress(f"Processando em fluxo: {item['name']}:{member['name']}")
            timer = time.perf_counter()
            db = connect(path, config.limits)
            try:
                create_unit(db)
                insert_records(
                    db,
                    public_records(
                        parse(
                            source_path,
                            member["name"],
                            config.selection,
                            config.limits,
                            source_stats,
                        ),
                        config.selection.profile,
                    ),
                )
                db.execute("CREATE INDEX records_scope ON records(round,uf)")
                db.execute(
                    "INSERT INTO checkpoint VALUES (?)",
                    (json.dumps({"unit_id": unit_id, "stats": source_stats}),),
                )
                db.commit()
            finally:
                db.close()
            if fingerprint(source_path) != before:
                raise ImportFailure("Fonte mudou durante parsing; checkpoint recusado")
            parse_seconds += time.perf_counter() - timer
            meta = work.file(path.with_suffix(".json"))
            write_json(
                meta, {"unit_id": unit_id, "sha256": hashes(path)["sha256"], "stats": source_stats}
            )
            work.completed_checkpoints.update((str(path), str(meta)))
        stats.append(
            {
                "archive": item["path"],
                "member": member["name"],
                "checkpoint_reused": unit_id in old_units,
                **source_stats,
            }
        )
        return (path, source_id, item, member, source_stats["format"])

    def pairs(unit):
        with sqlite3.connect(unit[0].resolve().as_uri() + "?mode=ro", uri=True) as db:
            result = db.execute(
                "SELECT DISTINCT round,uf FROM records ORDER BY round,uf"
            ).fetchall()
        db.close()
        return result

    def discard(unit):
        if (
            config.storage.cleanup_policy == "owned"
            and not config.storage.retain_checkpoints
            and unit[0].is_relative_to(work.root)
        ):
            work.remove(unit[0])
            work.remove(unit[0].with_suffix(".json"))

    primary_units = [load(unit) for unit in primary]
    primary_pairs = {pair for unit in primary_units for pair in pairs(unit)}
    db_path = stage / "election.sqlite"
    final = connect(db_path, config.limits)
    detail_path = work.file(stage / "divergences.jsonl")
    summary_path = work.file(stage / "divergences-summary.json")
    processed = set()
    try:
        create_stage(final)
        project(final, "public")
        compact(final)
        with DivergenceReport(
            detail_path, summary_path, config.storage.detailed_report_bytes
        ) as report:

            def partition(pair, bu_unit=None):
                nonlocal consolidation_seconds
                turn, uf = pair
                progress(f"Consolidando {uf} turno {turn}")
                timer = time.perf_counter()
                path = work.root / f"partition-{turn}-{uf}.sqlite"
                db = connect(path, config.limits)
                try:
                    create_stage(db)
                    for unit_path, source_id, item, member, fmt in primary_units + (
                        [bu_unit] if bu_unit else []
                    ):
                        db.execute("ATTACH DATABASE ? AS unit", (str(unit_path),))
                        db.execute(
                            f"INSERT INTO raw SELECT ?,?,{RECORD_COLUMNS} FROM unit.records WHERE round=? AND uf=?",
                            (source_id, fmt, turn, uf),
                        )
                        db.execute(
                            "INSERT INTO sources VALUES (?,?,?,?,?,?)",
                            (
                                source_id,
                                item["path"],
                                member["name"],
                                item["hashes"]["sha256"],
                                fmt,
                                json.dumps(item["verification"], sort_keys=True),
                            ),
                        )
                        db.commit()
                        db.execute("DETACH DATABASE unit")
                    project(db, config.selection.profile)
                    reconcile(db, report)
                    compact(db)
                finally:
                    db.close()
                work.reserve_batch()
                merge_partition(final, path)
                if config.storage.cleanup_policy == "owned":
                    work.remove(path)
                processed.add(pair)
                consolidation_seconds += time.perf_counter() - timer

            for descriptor in bweb:
                unit = load(descriptor)
                for pair in pairs(unit):
                    if pair in processed:
                        raise ImportFailure(
                            f"BWEBs separados com cobertura sobreposta {pair}: consolidação multifonte não suportada neste modo"
                        )
                    partition(pair, unit)
                discard(unit)
            for pair in sorted(primary_pairs - processed):
                partition(pair)
        for unit in primary_units:
            discard(unit)
        final.execute("DELETE FROM aggregates")
        final.execute("""INSERT INTO aggregates SELECT s.election,s.uf,r.candidate_id,SUM(r.votes),COUNT(*)
            FROM results r JOIN sections s ON s.id=r.section_id GROUP BY s.election,s.uf,r.candidate_id ORDER BY s.election,s.uf,r.candidate_id""")
        final.commit()
    finally:
        final.close()
    for item in archives:
        if list(fingerprint(root / item["path"])) != item["fingerprint"]:
            raise ImportFailure("Fonte mudou durante processamento; consolidação recusada")
    return (
        report.stats,
        stats,
        reused,
        {
            "parsing_seconds": round(parse_seconds, 3),
            "consolidation_seconds": round(consolidation_seconds, 3),
        },
    )
