"""Build separate M5 geography from locally inspected, hash-pinned public sources.

Never downloads or reads electoral ZIPs. Requires authoring dependencies in requirements.txt.
Input directory: municipio_tse_ibge.csv, ibge-localities.zip, ne-50m-map-units.zip,
tre-carga.pdf. The SQLite is opened query_only/read-only solely for section identity.
"""

import argparse
import csv
import hashlib
import io
import json
import sqlite3
import sys
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pipelines"))
from tse_importer.embedded_exporter import canonical  # noqa: E402


def normalize(value):
    return " ".join(
        "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c))
        .upper()
        .split()
    )


COUNTRY_ALIASES = {
    "AUSTRIA": "AT",
    "CHINA, HONG KONG": "HK",
    "CORÉIA DO SUL": "KR",
    "ESCÓCIA": "GB",
    "ESTADOS UNIDOS DA AMÉRICA": "US",
    "GUIANA FRANCESA": "GF",
    "HOLANDA": "NL",
    "INDIA": "IN",
    "IRLANDA": "IE",
    "PALESTINA": "PS",
    "QUÊNIA": "KE",
    "REPÚBLICA TCHECA": "CZ",
    "RÚSSIA (FEDERAÇÃO RUSSA)": "RU",
    "SUIÇA": "CH",
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_only(path):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def municipal_points(directory, source):
    from pyproj import Transformer

    crosswalk = defaultdict(set)
    with (directory / "municipio_tse_ibge.csv").open(encoding="latin1", newline="") as stream:
        for row in csv.DictReader(stream, delimiter=";"):
            crosswalk[(row["SG_UF"], row["CD_MUNICIPIO_TSE"])].add(row["CD_MUNICIPIO_IBGE"])
    with zipfile.ZipFile(directory / "ibge-localities.zip") as archive:
        # Extract only the known GeoPackage into the isolated input workspace.
        gpkg = directory / "BR_localidades_2022.gpkg"
        data = archive.read("BR_localidades_2022.gpkg")
        if not gpkg.exists():
            gpkg.write_bytes(data)
        elif gpkg.read_bytes() != data:
            raise ValueError("GeoPackage local difere da fonte inspecionada")
    points = defaultdict(set)
    with read_only(gpkg) as db:
        for uf, ibge, category, lat, lon in db.execute(
            "SELECT SIGLA_UF,CD_MUN,CT_LOCALIDADE,LAT_LOCALIDADE,LONG_LOCALIDADE "
            "FROM BR_localidades_2022 WHERE CD_LOCALIDADE=CD_MUN "
            "AND CT_LOCALIDADE IN ('Cidade','Distrito Estadual de Fernando de Noronha')"
        ):
            points[(uf, ibge)].add(
                (lat, lon, "representative" if uf == "DF" or category != "Cidade" else "seat")
            )
    transform = Transformer.from_crs(4674, 4326, always_xy=True)
    locations, missing = [], []
    for path in sorted((source / "municipalities").glob("*.json")):
        uf = path.stem
        if uf == "ZZ":
            continue
        for municipality in json.loads(path.read_text(encoding="utf8"))["municipalities"]:
            code = municipality["code"]
            official_code = code.zfill(5)
            candidates = crosswalk[(uf, official_code)]
            ibge = next(iter(candidates)) if len(candidates) == 1 else None
            positions = points[(uf, ibge)]
            if len(positions) != 1:
                missing.append(
                    {
                        "uf": uf,
                        "tse": code,
                        "ibge": ibge,
                        "reason": "missing_or_ambiguous_identifier_point",
                    }
                )
                continue
            lat, lon, kind = positions.pop()
            points[(uf, ibge)].add((lat, lon, kind))
            longitude, latitude = transform.transform(lon, lat)
            if not (-74 <= longitude <= -32 and -34 <= latitude <= 6):
                raise ValueError(f"Ponto fora do Brasil: {uf}/{code}")
            locations.append(
                [uf, code, ibge, round(latitude, 6), round(longitude, 6), kind, official_code]
            )
    return {
        "schema_version": 1,
        "crs": "EPSG:4326",
        "columns": ["uf", "tse", "ibge", "latitude", "longitude", "kind", "official_tse"],
        "correspondence_source": "tse_crosswalk",
        "point_source": "ibge_localities",
        "correspondence_version": "25/10/2026 09:00:09",
        "transform": {"operation": transform.description, "accuracy_m": transform.accuracy},
        "locations": sorted(locations),
        "missing": missing,
    }


def world_shapes(directory):
    import shapefile
    from shapely.geometry import mapping, shape

    with zipfile.ZipFile(directory / "ne-50m-map-units.zip") as archive:
        base = "ne_50m_admin_0_map_units"
        reader = shapefile.Reader(
            shp=io.BytesIO(archive.read(base + ".shp")),
            dbf=io.BytesIO(archive.read(base + ".dbf")),
            encoding="utf8",
        )
        if archive.read(base + ".VERSION.txt").decode().strip() != "5.1.1":
            raise ValueError("Versão Natural Earth inesperada")
        grouped = defaultdict(list)
        names = {}
        for record in reader.iterShapeRecords():
            properties = record.record.as_dict()
            iso = properties["ISO_A2_EH"]
            # Non-ISO cartographic units stay neutral with a technical NE key.
            code = iso if len(iso) == 2 and iso != "XK" else "NE_" + properties["GU_A3"]
            geometry = shape(record.shape.__geo_interface__).simplify(0.04, preserve_topology=True)
            geo = mapping(geometry)
            polygons = [geo["coordinates"]] if geo["type"] == "Polygon" else geo["coordinates"]
            grouped[code].extend(polygons)
            names.setdefault(code, properties["NAME_PT"] or properties["NAME"])
        # Map units include constituent regions (e.g. Flanders, Madeira).
        # Use the country layer's label for their shared ISO identity.
        with zipfile.ZipFile(directory / "ne-50m.zip") as countries_archive:
            country_reader = shapefile.Reader(
                dbf=io.BytesIO(countries_archive.read("ne_50m_admin_0_countries.dbf")),
                encoding="utf8",
            )
            for record in country_reader.iterRecords():
                properties = record.as_dict()
                iso = properties["ISO_A2_EH"]
                if iso in names and (properties["ISO_A2"] == iso or iso in ("FR", "NO")):
                    names[iso] = properties["NAME_PT"] or properties["NAME"]
        names["GB"] = "Reino Unido"
        result = []
        for code, polygons in sorted(grouped.items()):
            coordinates = [
                [[[round(x, 4), round(y, 4)] for x, y in ring] for ring in polygon]
                for polygon in polygons
            ]
            result.append(
                {
                    "type": "Feature",
                    "properties": {"iso": code, "name": names[code]},
                    "geometry": {"type": "MultiPolygon", "coordinates": coordinates},
                }
            )
    return {"type": "FeatureCollection", "features": result}, names


def foreign_correspondence(directory, source, sqlite, names):
    import pdfplumber

    by_country_name = {normalize(name): iso for iso, name in names.items() if len(iso) == 2}
    by_country_name.update({normalize(name): iso for name, iso in COUNTRY_ALIASES.items()})
    sections = defaultdict(set)
    country = None
    # The first 30 pages contain the exterior schedule. Do not extract personnel
    # names/electoral IDs on subsequent pages into any public artifact.
    with pdfplumber.open(directory / "tre-carga.pdf") as pdf:
        for page_number, page in enumerate(pdf.pages[:30], 1):
            for table in page.extract_tables():
                for row in table:
                    if len(row) not in (6, 8):
                        continue
                    if (
                        row[0]
                        and normalize(row[0]) != "PAIS"
                        and not any(c.isdigit() for c in row[0])
                    ):
                        label = normalize(row[0])
                        if label not in by_country_name:
                            raise ValueError(f"País oficial sem ISO revisado: {label}")
                        country = by_country_name[label]
                    # PDF columns are split by internal rules. Only PRIMARY
                    # section columns, never the aggregated-section column.
                    for cell in row[3:6] if len(row) == 8 else row[3:5]:
                        if cell and cell.strip().isdigit():
                            if country is None:
                                raise ValueError("Seção sem contexto de país")
                            sections[str(int(cell))].add((country, page_number))
    observed = defaultdict(set)
    with read_only(sqlite) as db:
        records = db.execute(
            "SELECT DISTINCT municipality,zone,section FROM sections WHERE uf='ZZ'"
        ).fetchall()
    # A section must identify a unique locality/zone in the observed year.
    owners = defaultdict(set)
    for code, zone, section in records:
        owners[section].add((code, zone))
    for code, zone, section in records:
        if len(owners[section]) == 1:
            for iso, page in sections[section]:
                observed[code].add((iso, zone, section, page))
    zz = json.loads((source / "municipalities/ZZ.json").read_text(encoding="utf8"))
    localities = []
    for loc in zz["municipalities"]:
        evidence = sorted(observed[loc["code"]])
        countries = sorted({item[0] for item in evidence})
        iso = countries[0] if len(countries) == 1 else None
        localities.append(
            {
                "tse": loc["code"],
                "name": loc["name"],
                "iso": iso,
                "country": names[iso] if iso else None,
                "status": "verified_section_join"
                if iso
                else "conflicting_section_countries"
                if countries
                else "no_verified_section_join",
                "origin": "tre_carga",
                "evidence_columns": ["iso", "zone", "section", "page"],
                "evidence": evidence,
                "candidate_countries": countries,
            }
        )
    return {"schema_version": 1, "source_dataset_id": zz["dataset_id"], "localities": localities}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Refuse to overwrite any cartographic package; install is a separate step.
    args.output.mkdir(parents=True, exist_ok=False)
    world, names = world_shapes(args.inputs)
    points = municipal_points(args.inputs, args.source)
    foreign = foreign_correspondence(args.inputs, args.source, args.sqlite, names)
    for name, data in [
        ("world.geojson", world),
        ("municipal_locations.json", points),
        ("overseas_correspondence.json", foreign),
    ]:
        (args.output / name).write_bytes(canonical(data))
    manifest = {
        "schema_version": 1,
        "version": "geography-2026-1",
        "sources": {
            "tse_crosswalk": {
                "url": "https://cdn.tse.jus.br/estatistica/sead/odsele/municipio_tse_ibge/municipio_tse_ibge.zip",
                "file": "municipio_tse_ibge.csv",
                "sha256": digest(args.inputs / "municipio_tse_ibge.csv"),
                "version": "25/10/2026 09:00:09",
                "license": "CC-BY (TSE portal)",
            },
            "ibge_localities": {
                "url": "https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/Localidades_Brasil_gpkg.zip",
                "sha256": digest(args.inputs / "ibge-localities.zip"),
                "version": "Censo 2022, published 2025-11-19",
                "license": "IBGE public data, attribution required",
            },
            "natural_earth": {
                "url": "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_map_units.zip",
                "sha256": digest(args.inputs / "ne-50m-map-units.zip"),
                "version": "5.1.1",
                "license": "Public domain",
            },
            "natural_earth_country_labels": {
                "url": "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip",
                "sha256": digest(args.inputs / "ne-50m.zip"),
                "version": "5.1.1",
                "license": "Public domain",
            },
            "tre_carga": {
                "url": "https://www.tre-df.jus.br/comunicacao/noticias/arquivos/edital-carga_e_lacracao_das_urnas_eletronicas__df_e_zz____2026/@@download/file",
                "sha256": digest(args.inputs / "tre-carga.pdf"),
                "version": "2026-09-15T15:32:26Z",
                "license": "Official public electoral notice, attribution",
            },
        },
        "artifacts": {
            path.name: {"bytes": path.stat().st_size, "sha256": digest(path)}
            for path in sorted(args.output.iterdir())
        },
    }
    (args.output / "manifest.json").write_bytes(canonical(manifest))
    print(
        json.dumps(
            {
                "points": len(points["locations"]),
                "missing_points": points["missing"],
                "mapped_foreign": sum(r["iso"] is not None for r in foreign["localities"]),
                "world_features": len(world["features"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
