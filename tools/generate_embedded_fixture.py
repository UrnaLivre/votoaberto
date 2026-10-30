"""Reproducible small, explicitly FICTIONAL asset fixture; never opens real data."""

import argparse
import csv
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "pipelines"), str(ROOT / "tests")]
from conftest import row  # noqa: E402
from tse_importer.domain import TERRITORIES, Config  # noqa: E402
from tse_importer.embedded_exporter import export_embedded  # noqa: E402
from tse_importer.engine import run_import  # noqa: E402
from tse_importer.parsers import SCHEMAS  # noqa: E402


def write_zip(path, records, fmt="section"):
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=SCHEMAS[fmt], delimiter=";")
    writer.writeheader()
    writer.writerows(records)
    info = zipfile.ZipInfo(fmt + ".csv", date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, text.getvalue().encode("latin1"))


def generate(output):
    output = Path(output)
    work_parent = ROOT / ".local/m4-fixture-work"
    work_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="votoaberto-fixture-", dir=work_parent) as temporary:
        root = Path(temporary)
        assert root.resolve().is_relative_to(work_parent.resolve())
        sources = root / "sources"
        sources.mkdir()
        primary, bweb = [], []
        for uf in sorted(TERRITORIES):
            for turn in (1, 2):
                for city, name in (("00001", "São FICTÍCIO"), ("00002", "Vila FICTÍCIA")):
                    if uf == "ZZ" and turn == 2 and city == "00002":
                        continue
                    nominal = (
                        [("11", 40), ("22", 30), ("33", 20)]
                        if turn == 1
                        else [("11", 65), ("22", 25)]
                    )
                    for number, votes in nominal + [("95", 0), ("96", 10)]:
                        primary.append(
                            row(
                                turn=turn,
                                uf=uf,
                                number=number,
                                votes=votes,
                                CD_MUNICIPIO=city,
                                NM_MUNICIPIO=name,
                            )
                        )
                        bweb.append(
                            row(
                                fmt="bweb",
                                turn=turn,
                                uf=uf,
                                number=number,
                                votes=votes,
                                CD_MUNICIPIO=city,
                                NM_MUNICIPIO=name,
                            )
                        )
        write_zip(sources / "section.zip", primary)
        write_zip(sources / "bweb.zip", bweb, fmt="bweb")
        source = run_import(Config(sources, root / "sqlite", data_kind="synthetic"))
        exported = Path(export_embedded(source, root / "embedded")["release"])
        manifest = json.loads((exported / "manifest.json").read_text(encoding="utf8"))
        output.mkdir(parents=True, exist_ok=True)
        for name in ["manifest.json", *manifest["artifacts"]]:
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((exported / name).read_bytes())
        print(json.dumps({"fixture": str(output), "dataset_id": manifest["dataset_id"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    generate(parser.parse_args().output)
