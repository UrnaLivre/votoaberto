"""Reconcile an independent country release and record the 28 M5.2 investigations.

Reads installed M4 JSONs and section identities only; never reimports results.
The report includes full integer candidate/metric/availability vectors, not ratios.
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pipelines"))
from resolve_overseas import FIELDS, register_rows  # noqa: E402
from tse_importer.country_exporter import export_countries  # noqa: E402
from tse_importer.embedded_exporter import canonical  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(source, correspondence, previous, register, sqlite, output, report):
    result = export_countries(source, correspondence, output)
    assert result == export_countries(source, correspondence, output)
    crosswalk = json.loads(correspondence.read_bytes())
    old_manifest = json.loads((previous / "manifest.json").read_bytes())
    assert (
        digest(previous / "countries.json") == old_manifest["artifacts"]["countries.json"]["sha256"]
    )
    before = json.loads((previous / "countries.json").read_bytes())
    assert before["source_dataset_id"] == crosswalk["source_dataset_id"]
    assert (
        result["reconciliation"]["exterior_rounds"] == before["reconciliation"]["exterior_rounds"]
    )
    assert digest(register) == crosswalk["evidence_sources"]["tse_locations_2026"]["member_sha256"]
    rows = register_rows(register)
    review = json.loads(Path(__file__).with_name("zz_review_2026.json").read_text(encoding="utf8"))
    codes = {d["tse"] for d in review["decisions"]}
    observed = []
    with sqlite3.connect(sqlite.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        for code, turn, zone, section, local in db.execute(
            "SELECT s.municipality,e.round,s.zone,s.section,s.local FROM sections s "
            "JOIN elections e ON s.election=e.id WHERE s.uf='ZZ' AND e.year=2026"
        ):
            if code not in codes:
                continue
            key = (code, str(turn), zone, section)
            number, row = rows[key]
            assert row["NR_LOCAL_VOTACAO"] == local
            observed.append(
                {
                    "tse": code,
                    "round": turn,
                    "zone": zone,
                    "section": section,
                    "local": local,
                    "record": number,
                    "primary_section": row["NR_SECAO_PRINCIPAL"],
                    "fields": {f: row[f] for f in FIELDS},
                }
            )
    cases = []
    for d in review["decisions"]:
        cases.append(
            {
                "tse": d["tse"],
                "name": d["name"],
                "status": "multi_country_pending_section_aggregation"
                if d["tse"] == "29432"
                else d["status"],
                "iso": d["iso"],
                "rationale": d["rationale"],
                "manual_sheet_row": d.get("manual_sheet_row"),
                "registered_observed_sections": sorted(
                    (r for r in observed if r["tse"] == d["tse"]),
                    key=lambda r: (r["round"], int(r["section"])),
                ),
            }
        )
    manifest_path = correspondence.with_name("manifest.json")
    data = {
        "schema_version": 1,
        "consulted_at": "2026-10-31",
        "source_dataset_id": crosswalk["source_dataset_id"],
        "public_readiness": json.loads((source / "manifest.json").read_bytes())["public_readiness"],
        "before": {
            "mapped_localities": before["mapped_localities"],
            "countries": len(before["countries"]),
            "release_id": before["dataset_id"],
            "reconciliation": before["reconciliation"],
        },
        "after": {
            k: result[k]
            for k in [
                "release_id",
                "bytes",
                "mapped_localities",
                "coverage",
                "unmapped_localities",
                "reconciliation",
            ]
        },
        "country_count": len(result["countries"]),
        "new_countries": sorted(
            {c["iso"] for c in result["countries"]} - {c["iso"] for c in before["countries"]}
        ),
        "country_localities": {c["iso"]: c["localities"] for c in result["countries"]},
        "geographic_manifest_sha256": digest(manifest_path),
        "geographic_artifacts": json.loads(manifest_path.read_bytes())["artifacts"],
        "country_release_manifest": json.loads(
            (Path(result["path"]) / "manifest.json").read_bytes()
        ),
        "sources": {
            **crosswalk["evidence_sources"],
            "manual": review["corroborating_manual_source"],
        },
        "cases": cases,
    }
    report.write_bytes(canonical(data))
    print(
        json.dumps(
            {
                "release_id": result["release_id"],
                "report_sha256": digest(report),
                "mapped": result["mapped_localities"],
                "countries": len(result["countries"]),
                "observed_keys_investigated": len(observed),
                "new_countries": data["new_countries"],
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "correspondence", "previous", "register", "sqlite", "output", "report"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    audit(
        args.source,
        args.correspondence,
        args.previous,
        args.register,
        args.sqlite,
        args.output,
        args.report,
    )


if __name__ == "__main__":
    main()
