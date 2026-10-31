import copy
import hashlib
import json
from pathlib import Path

import pytest
from tse_importer.country_exporter import aggregate, country_derivative, export_countries
from tse_importer.domain import ImportFailure
from tse_importer.embedded_exporter import canonical

ASSETS = Path(__file__).resolve().parents[1] / "apps/votoaberto_flutter/assets"


def inputs():
    source = ASSETS / "data/synthetic"
    zz = json.loads((source / "municipalities/ZZ.json").read_text(encoding="utf8"))
    states = json.loads((source / "states.json").read_text(encoding="utf8"))
    exterior = next(row["rounds"] for row in states["territories"] if row["code"] == "ZZ")
    mapping = [
        {
            "tse": "00001",
            "iso": "US",
            "country": "País fictício A",
            "status": "verified_section_join",
            "evidence": [["US", "1", "1", 1]],
        },
        {
            "tse": "00002",
            "iso": "PT",
            "country": "País fictício B",
            "status": "verified_section_join",
            "evidence": [["PT", "1", "2", 1]],
        },
    ]
    return source, zz, exterior, mapping


def test_complete_partition_reconciles_every_metric_candidate_and_section():
    _, zz, exterior, mapping = inputs()
    result = country_derivative(zz["municipalities"], mapping, exterior)
    assert result["coverage"] == "complete_for_observed_localities"
    assert result["reconciliation"]["country_sum_equals_full_exterior"]
    assert result["reconciliation"]["mapped_rounds"] == exterior
    assert result["countries"][0]["iso"] == "PT"
    assert len(result["countries"][0]["rounds"]) == 1  # Never invent round two.
    assert result["countries"][0]["locality_count_by_round"] == {"1": 1, "2": 0}
    assert len(result["countries"][1]["rounds"][0]["candidates"]) == 3
    assert len(result["countries"][1]["rounds"][1]["candidates"]) == 2


def test_partial_country_sum_is_not_promoted_to_full_exterior():
    _, zz, exterior, mapping = inputs()
    result = country_derivative(zz["municipalities"], mapping[:1], exterior)
    assert result["coverage"] == "partial"
    check = result["reconciliation"]
    assert check["countries_plus_unmapped_equals_exterior"]
    assert not check["country_sum_equals_full_exterior"]
    assert aggregate([*check["mapped_rounds"], *check["unmapped_rounds"]]) == exterior
    assert result["unmapped_localities"] == [{"tse": "00002", "name": "Vila FICTÍCIA"}]


def test_missing_fields_and_partial_sections_survive_aggregation():
    _, zz, _, mapping = inputs()
    rows = copy.deepcopy(zz["municipalities"])
    rows[0]["rounds"][0]["totals"]["blank"] = None
    rows[0]["rounds"][0]["available_sections"]["blank"] = 0
    mapping[1]["iso"], mapping[1]["country"] = "US", mapping[0]["country"]
    mapping[1]["evidence"][0][0] = "US"
    exterior = aggregate(r for loc in rows for r in loc["rounds"])
    result = country_derivative(rows, mapping, exterior)
    turn = result["countries"][0]["rounds"][0]
    assert turn["totals"]["blank"] == 0  # Only the explicitly published zero.
    assert turn["available_sections"]["blank"] == 1
    assert turn["sections"] == 2
    assert "percentages" not in turn  # Ratios are not produced by this exporter.


@pytest.mark.parametrize("mutation", ["duplicate", "unverified", "no_evidence", "mismatch"])
def test_rejects_ambiguous_unverified_or_unreconciled_input(mutation):
    _, zz, exterior, mapping = inputs()
    if mutation == "duplicate":
        mapping.append(mapping[0])
    elif mutation == "unverified":
        mapping[0]["status"] = "city_name_guess"
    elif mutation == "no_evidence":
        mapping[0]["evidence"] = []
    else:
        exterior[0]["totals"]["counted"] += 1
    with pytest.raises(ImportFailure):
        country_derivative(zz["municipalities"], mapping, exterior)


def test_export_is_deterministic_separate_and_refuses_overwrite(tmp_path):
    source, zz, _, mapping = inputs()
    before = {str(path): path.read_bytes() for path in source.rglob("*.json")}
    correspondence = tmp_path / "mapping.json"
    correspondence.write_bytes(
        canonical(
            {"schema_version": 1, "source_dataset_id": zz["dataset_id"], "localities": mapping}
        )
    )
    first = export_countries(source, correspondence, tmp_path / "countries")
    second = export_countries(source, correspondence, tmp_path / "countries")
    assert first == second
    assert {str(path): path.read_bytes() for path in source.rglob("*.json")} == before
    release = Path(first["path"])
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf8"))
    assert (
        manifest["public_readiness"]
        == json.loads((source / "manifest.json").read_text(encoding="utf8"))["public_readiness"]
    )
    assert len(manifest["rules_sha256"]) == 64
    assert (
        manifest["artifacts"]["countries.json"]["sha256"]
        == hashlib.sha256((release / "countries.json").read_bytes()).hexdigest()
    )
    (release / "countries.json").write_text("tampered", encoding="utf8")
    with pytest.raises(ImportFailure, match="Sobreposição"):
        export_countries(source, correspondence, tmp_path / "countries")
    with pytest.raises(ImportFailure, match="independente"):
        export_countries(source, correspondence, source / "new")


def test_version_binding_and_previous_derivatives_are_preserved(tmp_path):
    source, zz, _, mapping = inputs()
    correspondence = tmp_path / "mapping.json"
    data = {"schema_version": 1, "source_dataset_id": zz["dataset_id"], "localities": mapping}
    correspondence.write_bytes(canonical(data))
    first = export_countries(source, correspondence, tmp_path / "countries")
    first_files = {p.name: p.read_bytes() for p in Path(first["path"]).iterdir()}
    data["localities"] = mapping[:1]
    correspondence.write_bytes(canonical(data))
    partial = export_countries(source, correspondence, tmp_path / "countries")
    assert partial["release_id"] != first["release_id"]
    assert {p.name: p.read_bytes() for p in Path(first["path"]).iterdir()} == first_files
    data["source_dataset_id"] = "other-version"
    correspondence.write_bytes(canonical(data))
    with pytest.raises(ImportFailure, match="outra versão"):
        export_countries(source, correspondence, tmp_path / "countries")
