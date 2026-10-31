import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "apps/votoaberto_flutter/assets/geo"


def test_independent_geographic_assets_have_exact_hashes_and_version():
    raw = (GEO / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    assert manifest["version"] == "geography-2026-1"
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
    assert sum(r["iso"] is not None for r in rows) == 117
    for row in rows:
        if row["iso"]:
            assert row["status"] == "verified_section_join"
            assert row["evidence"]
            assert {e[0] for e in row["evidence"]} == {row["iso"]}
        else:
            assert row["country"] is None
    ambiguous = [r for r in rows if r["status"] == "conflicting_section_countries"]
    assert len(ambiguous) == 1
    assert set(ambiguous[0]["candidate_countries"]) == {"BE", "LU"}


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
