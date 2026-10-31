import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "apps/votoaberto_flutter/assets/geo"


def test_independent_geographic_assets_have_exact_hashes_and_version():
    raw = (GEO / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    assert manifest["version"] == "geography-2026-2"
    dart = (
        ROOT / "apps/votoaberto_flutter/lib/features/map/domain/geographic_catalog.dart"
    ).read_text(encoding="utf8")
    assert hashlib.sha256(raw).hexdigest() in dart
    for name, info in manifest["artifacts"].items():
        content = (GEO / name).read_bytes()
        assert len(content) == info["bytes"]
        assert hashlib.sha256(content).hexdigest() == info["sha256"]


def test_municipal_identifier_audit_includes_special_units_without_name_matching():
    asset = json.loads((GEO / "municipal_locations.json").read_text(encoding="utf8"))
    rows = asset["locations"]
    assert len(rows) == 5571
    assert not asset["missing"]
    assert len({(r[0], r[1]) for r in rows}) == len(rows)
    assert len({r[2] for r in rows}) == len(rows)
    assert all(isinstance(r[1], str) and isinstance(r[2], str) for r in rows)
    assert all(-34 <= r[3] <= 6 and -74 <= r[4] <= -32 for r in rows)
    assert all(r[1].zfill(5) == r[6] for r in rows)
    assert next(r for r in rows if r[2] == "2605459")[5] == "representative"
    assert next(r for r in rows if r[0] == "DF")[5] == "representative"
    assert next(r for r in rows if r[2] == "5101837")[0] == "MT"


def test_foreign_evidence_has_no_silent_country_for_ambiguous_sections():
    data = json.loads((GEO / "overseas_correspondence.json").read_text(encoding="utf8"))
    rows = data["localities"]
    assert len(rows) == 145
    assert len({r["tse"] for r in rows}) == 145
    assert data["schema_version"] == 2
    assert sum(r["iso"] is not None for r in rows) == 143
    assert len({r["iso"] for r in rows if r["iso"]}) == 100
    from tse_importer.overseas_evidence import validate_correspondence

    validate_correspondence(rows, data["evidence_sources"])
    for row in rows:
        if row["iso"]:
            assert row["evidence"]
            assert row["status"] in {"verified_section_join", "verified_official_section_register"}
        else:
            assert row["country"] is None
    ambiguous = [r for r in rows if r["status"] == "conflicting_section_countries"]
    assert len(ambiguous) == 1
    assert set(ambiguous[0]["candidate_countries"]) == {"BE", "LU"}
    assert {r["tse"] for r in rows if not r["iso"]} == {"29432", "30686"}
    legacy = [r for r in rows if r["status"] == "verified_section_join"]
    assert len(legacy) == 117
    raw = json.dumps(legacy, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "722352ad52031de5bd6839f795954633478a9364206bb80244d628df473fffbb"
    )
    assert (
        hashlib.sha256((GEO / "municipal_locations.json").read_bytes()).hexdigest()
        == "b71dc3461ac3292fff3ea997978889e96304ac5be882fb435b7c3bcddaebd011"
    )
    assert (
        hashlib.sha256((GEO / "world.geojson").read_bytes()).hexdigest()
        == "2bf9d5b50da3b76ca389f10fd96537affb82113375dfa26e0caff6741fe82103"
    )


def test_app_runtime_has_no_new_network_transport_or_tile_service():
    paths = [
        ROOT / "apps/votoaberto_flutter/lib/features/map",
        ROOT / "apps/votoaberto_flutter/lib/features/explorer",
    ]
    for directory in paths:
        for file in directory.rglob("*.dart"):
            text = file.read_text(encoding="utf8")
            assert not any(
                token in text
                for token in [
                    "HttpClient(",
                    "http.get(",
                    "NetworkImage(",
                    "Image.network(",
                    "tile.openstreetmap",
                    "package:http/",
                ]
            )
