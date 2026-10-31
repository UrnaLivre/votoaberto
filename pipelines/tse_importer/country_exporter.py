"""Independent, deterministic country derivative of an immutable M4 package.

No downloads, electoral ZIP processing, SQLite writes or installation into M4.
Unmapped localities are retained as a separate residual, never attributed by name.
"""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from .domain import ImportFailure
from .embedded_exporter import _add, _empty, canonical, resolve_release, validate_embedded
from .workspace import no_links

RULES_VERSION = "country-1"


def aggregate(rows):
    result = {}
    for row in rows:
        key = (row["round"], row["election"])
        if key not in result:
            result[key] = _empty(row["election"], row["round"])
        _add(result[key], row)
    return [result[key] for key in sorted(result)]


def country_derivative(localities, correspondence, exterior):
    """Pure transform; every source row belongs to exactly one partition."""
    mapping = {}
    for row in correspondence:
        code = row["tse"]
        if not isinstance(code, str) or code in mapping:
            raise ImportFailure("Código TSE duplicado ou inválido na correspondência")
        iso = row.get("iso")
        if iso is not None and (
            not re.fullmatch(r"[A-Z]{2}", iso)
            or row.get("status") != "verified_section_join"
            or not row.get("evidence")
            or not row.get("country")
        ):
            raise ImportFailure("País sem associação verificada por identificador")
        mapping[code] = row
    countries = defaultdict(list)
    missing = []
    seen = set()
    for locality in localities:
        code = locality["code"]
        if code in seen:
            raise ImportFailure("Localidade eleitoral duplicada")
        seen.add(code)
        match = mapping.get(code)
        if match and match.get("iso"):
            countries[match["iso"]].append(locality)
        else:
            missing.append(locality)
    # Reconcile the original JSON partitions independently of the crosswalk.
    if aggregate(r for loc in localities for r in loc["rounds"]) != exterior:
        raise ImportFailure("Soma das localidades difere do exterior M4")
    output = []
    for iso, locations in sorted(countries.items()):
        names = {mapping[loc["code"]]["country"] for loc in locations}
        if len(names) != 1:
            raise ImportFailure("Nomes contraditórios para um mesmo ISO")
        output.append(
            {
                "iso": iso,
                "name": names.pop(),
                "localities": sorted(loc["code"] for loc in locations),
                "locality_count_by_round": {
                    str(turn): sum(
                        any(r["round"] == turn for r in loc["rounds"]) for loc in locations
                    )
                    for turn in (1, 2)
                },
                "rounds": aggregate(r for loc in locations for r in loc["rounds"]),
            }
        )
    mapped = aggregate(r for country in output for r in country["rounds"])
    residual = aggregate(r for loc in missing for r in loc["rounds"])
    # A second route to the mapped control total catches a partition/sum error.
    expected = aggregate(
        r for loc in localities if mapping.get(loc["code"], {}).get("iso") for r in loc["rounds"]
    )
    if mapped != expected or aggregate([*mapped, *residual]) != exterior:
        raise ImportFailure("Reconciliação por país/categoria/candidato divergente")
    return {
        "countries": output,
        "coverage": "partial" if missing else "complete_for_observed_localities",
        "mapped_localities": len(localities) - len(missing),
        "unmapped_localities": [{"tse": loc["code"], "name": loc["name"]} for loc in missing],
        "reconciliation": {
            "status": "passed",
            "country_sum_equals_mapped_localities": True,
            "countries_plus_unmapped_equals_exterior": True,
            "country_sum_equals_full_exterior": not missing,
            "mapped_rounds": mapped,
            "unmapped_rounds": residual,
            "exterior_rounds": exterior,
        },
    }


def export_countries(source, correspondence, output):
    source = resolve_release(source)
    validate_embedded(source)
    correspondence = Path(correspondence).absolute()
    no_links(correspondence)
    correspondence = correspondence.resolve()
    crosswalk_bytes = correspondence.read_bytes()
    crosswalk = json.loads(crosswalk_bytes)
    if crosswalk.get("schema_version") != 1:
        raise ImportFailure("Versão da correspondência inválida")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf8"))
    if crosswalk["source_dataset_id"] != manifest["dataset_id"]:
        raise ImportFailure("Correspondência pertence a outra versão eleitoral")
    zz = json.loads((source / "municipalities/ZZ.json").read_text(encoding="utf8"))
    states = json.loads((source / "states.json").read_text(encoding="utf8"))
    exterior = next(s["rounds"] for s in states["territories"] if s["code"] == "ZZ")
    result = country_derivative(zz["municipalities"], crosswalk["localities"], exterior)
    identity = {
        "schema_version": 1,
        "rules_version": RULES_VERSION,
        "source_dataset_id": manifest["dataset_id"],
        "source_manifest_sha256": hashlib.sha256(
            (source / "manifest.json").read_bytes()
        ).hexdigest(),
        "correspondence_sha256": hashlib.sha256(crosswalk_bytes).hexdigest(),
    }
    release_id = hashlib.sha256(canonical(identity)).hexdigest()[:24]
    payload = canonical({**identity, "dataset_id": release_id, **result})
    release_manifest = canonical(
        {
            **identity,
            "dataset_id": release_id,
            "coverage": result["coverage"],
            "artifacts": {
                "countries.json": {
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            },
        }
    )
    output = Path(output).absolute()
    no_links(output)
    output = output.resolve()
    # The independent output may not live inside any immutable source release.
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ImportFailure("Destino deve ser independente da release M4")
    no_links(output)
    target = output / "releases" / release_id
    if target.exists():
        no_links(target)
        no_links(target / "manifest.json")
        no_links(target / "countries.json")
        if (target / "manifest.json").read_bytes() != release_manifest or (
            target / "countries.json"
        ).read_bytes() != payload:
            raise ImportFailure("Sobreposição de versão geográfica recusada")
    else:
        target.mkdir(parents=True, exist_ok=False)
        (target / "countries.json").write_bytes(payload)
        (target / "manifest.json").write_bytes(release_manifest)
    return {
        "release_id": release_id,
        "path": str(target),
        "bytes": len(payload) + len(release_manifest),
        **result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--correspondence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = export_countries(args.source, args.correspondence, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("release_id", "path", "bytes", "coverage", "mapped_localities")
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
