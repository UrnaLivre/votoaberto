"""Small, fictional register fixtures: CI never downloads official data."""

import copy
import csv
import json

import pytest
from test_country_exporter import inputs
from tse_importer.country_exporter import country_derivative
from tse_importer.domain import ImportFailure
from tse_importer.overseas_evidence import validate_correspondence

from tools.geography.resolve_overseas import FIELDS, register_rows, reviewed_locality


def direct_inputs():
    _, zz, exterior, mapping = inputs()
    sources = {
        "fixture": {
            "url": "https://cdn.tse.jus.br/fixture-not-a-real-source.zip",
            "sha256": "a" * 64,
            "member_sha256": "b" * 64,
            "member": "fictional.csv",
            "election_year": 2026,
            "version": "fixture",
            "reviewed_country_literals": {"US": ["PAIS FICTICIO A"], "PT": ["PAIS FICTICIO B"]},
        }
    }
    for row, locality in zip(mapping, zz["municipalities"], strict=True):
        literal = sources["fixture"]["reviewed_country_literals"][row["iso"]][0]
        row.update(
            status="verified_official_section_register",
            candidate_countries=[row["iso"]],
            verified_rounds=[r["round"] for r in locality["rounds"]],
        )
        row["evidence"] = [
            {
                "source": "fixture",
                "record": turn["round"] + 1,
                "iso": row["iso"],
                "tse": row["tse"],
                "round": turn["round"],
                "zone": "1",
                "section": str(int(row["tse"])),
                "local": "1015",
                "primary_section": "-1",
                "country_field": "DS_ENDERECO",
                "country_literal": literal,
                "fields": {
                    "DS_ENDERECO": f"RUA FICTICIA, {literal}",
                    "NM_BAIRRO": "CENTRO",
                    "NM_LOCAL_VOTACAO": "LOCAL FICTICIO",
                },
            }
            for turn in locality["rounds"]
        ]
    return zz, exterior, mapping, sources


def test_official_code_and_section_turn_register_reconciles_exactly():
    zz, exterior, mapping, sources = direct_inputs()
    result = country_derivative(zz["municipalities"], mapping, exterior, sources)
    assert result["reconciliation"]["mapped_rounds"] == exterior
    assert result["reconciliation"]["countries_plus_unmapped_equals_exterior"]
    assert result["countries"][0]["locality_count_by_round"] == {"1": 1, "2": 0}
    # City labels are irrelevant to the identifying evidence.
    mapping[0]["name"] = "OUTRO NOME FICTICIO"
    assert country_derivative(zz["municipalities"], mapping, exterior, sources) == result


@pytest.mark.parametrize(
    "mutation",
    [
        "name_only",
        "code",
        "country",
        "duplicate",
        "source",
        "hash",
        "year",
        "missing_turn",
        "invented_turn",
        "missing_section",
        "aggregated",
        "multi_country",
        "contradictory_address",
        "cross_locality_section",
        "unknown_code",
    ],
)
def test_rejects_unidentified_conflicting_or_incomplete_assertions(mutation):
    zz, exterior, mapping, sources = direct_inputs()
    e = mapping[0]["evidence"][0]
    if mutation == "name_only":
        e["country_field"] = "NM_MUNICIPIO"
        e["fields"]["NM_MUNICIPIO"] = e["country_literal"]
    elif mutation == "code":
        e["tse"] = "99999"
    elif mutation == "country":
        e["iso"] = "PT"
    elif mutation == "duplicate":
        mapping[0]["evidence"].append(copy.deepcopy(e))
    elif mutation == "source":
        sources["fixture"]["url"] = "https://example.org/unofficial.csv"
    elif mutation == "hash":
        sources["fixture"]["member_sha256"] = "unknown"
    elif mutation == "year":
        sources["fixture"]["election_year"] = 2022
    elif mutation == "missing_turn":
        mapping[0]["evidence"].pop()
    elif mutation == "invented_turn":
        mapping[1]["verified_rounds"] = [1, 2]
    elif mutation == "missing_section":
        zz["municipalities"][0]["rounds"][0]["sections"] += 1
    elif mutation == "aggregated":
        e["primary_section"] = "2"
    elif mutation == "multi_country":
        mapping[0]["candidate_countries"] = ["US", "PT"]
    elif mutation == "contradictory_address":
        e["fields"]["NM_BAIRRO"] = "PAIS FICTICIO B"
    elif mutation == "cross_locality_section":
        mapping[1]["evidence"][0]["section"] = "1"
    elif mutation == "unknown_code":
        mapping[1]["tse"] = "99999"
        mapping[1]["evidence"][0]["tse"] = "99999"
    with pytest.raises(ImportFailure):
        country_derivative(zz["municipalities"], mapping, exterior, sources)


def test_legacy_section_join_rejects_conflicting_iso_without_name_fallback():
    _, _, _, mapping = inputs()
    mapping[0]["evidence"].append(["PT", "1", "99", 2])
    with pytest.raises(ImportFailure, match="contraditória"):
        validate_correspondence(mapping)


def test_residual_preserves_absent_rounds_and_all_fields():
    zz, exterior, mapping, sources = direct_inputs()
    result = country_derivative(zz["municipalities"], mapping[:1], exterior, sources)
    assert result["reconciliation"]["unmapped_rounds"] == zz["municipalities"][1]["rounds"]
    assert result["unmapped_localities"] == [{"tse": "00002", "name": "Vila FICTÍCIA"}]


def register_fixture():
    _, _, mapping, _ = direct_inputs()
    e = mapping[0]["evidence"][0]
    row = {
        **e["fields"],
        "AA_ELEICAO": "2026",
        "SG_UF": "ZZ",
        "CD_MUNICIPIO": "00001",
        "NR_TURNO": "1",
        "NR_ZONA": "1",
        "NR_SECAO": "1",
        "NR_LOCAL_VOTACAO": "1015",
        "NR_SECAO_PRINCIPAL": "-1",
        "CD_TIPO_SECAO_AGREGADA": "1",
        "DT_GERACAO": "25/10/2026",
        "HH_GERACAO": "00:00:00",
    }
    decision = {
        "iso": "US",
        "country": "País fictício A",
        "country_field": "DS_ENDERECO",
        "country_literal": e["country_literal"],
        "reviewed_fields": e["fields"],
    }
    key = ("00001", "1", "1", "1")
    return key, row, decision


def test_register_duplicates_are_rejected_even_when_identical(tmp_path):
    _, row, _ = register_fixture()
    path = tmp_path / "fictional.csv"
    with path.open("w", newline="", encoding="latin1") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row), delimiter=";")
        writer.writeheader()
        writer.writerows([row, row])
    with pytest.raises(ImportFailure, match="duplicado"):
        register_rows(path)


def test_missing_sections_and_multi_location_registers_are_not_inferred_by_name():
    key, row, decision = register_fixture()
    old = {"tse": "00001", "name": "LOCALIDADE FICTICIA"}
    observed = {key: "1015"}
    with pytest.raises(ImportFailure, match="ausente"):
        reviewed_locality(old, decision, {}, observed, "fixture")
    result = reviewed_locality(old, decision, {key: (2, row)}, observed, "fixture")
    assert result["evidence"][0]["tse"] == "00001"
    assert result["evidence"][0]["fields"] == {f: row[f] for f in FIELDS}
    conflicting = dict(row, DS_ENDERECO="OUTRO PAIS FICTICIO")
    with pytest.raises(ImportFailure, match="incompatíveis"):
        reviewed_locality(old, decision, {key: (2, conflicting)}, observed, "fixture")
    distributed = dict(row, CD_TIPO_SECAO_AGREGADA="3")
    with pytest.raises(ImportFailure, match="principal"):
        reviewed_locality(old, decision, {key: (2, distributed)}, observed, "fixture")


def test_review_decisions_resolve_only_26_and_preserve_two_conflicts():
    from pathlib import Path

    review = json.loads(
        (Path(__file__).resolve().parents[1] / "tools/geography/zz_review_2026.json").read_text(
            encoding="utf8"
        )
    )
    decisions = review["decisions"]
    assert len(decisions) == len({d["tse"] for d in decisions}) == 28
    assert sum(d["status"] == "verified" for d in decisions) == 26
    assert {d["tse"] for d in decisions if d["status"] == "conflicting"} == {"29432", "30686"}
