"""All generated rows are FICTIONAL; only column layouts imitate observed TSE files."""

import csv
import io
import zipfile

import pytest
from tse_importer.parsers import SCHEMAS


def row(fmt="section", turn=1, uf="SC", section="0001", number="11", votes=60, **changes):
    record = dict.fromkeys(SCHEMAS[fmt], "#NULO#")
    record.update(
        DT_GERACAO="01/01/2026",
        HH_GERACAO="00:00:00",
        ANO_ELEICAO="2026",
        CD_TIPO_ELEICAO="0" if fmt == "bweb" else "2",
        NM_TIPO_ELEICAO="Eleição Ordinária",
        NR_TURNO=str(turn),
        CD_ELEICAO=f"demo000{turn}",
        DS_ELEICAO="FICTÍCIA",
        SG_UF=uf,
        CD_MUNICIPIO="00001",
        NM_MUNICIPIO="Município FICTÍCIO",
        NR_ZONA="0001",
        NR_SECAO=section,
        NR_LOCAL_VOTACAO="00001",
        NR_VOTAVEL=number,
        NM_VOTAVEL={"95": "Branco", "96": "Nulo"}.get(number, "Candidatura FICTÍCIA " + number),
        QT_VOTOS=str(votes),
    )
    # Election codes remain textual, but observed parsers require decimal identifiers.
    record["CD_ELEICAO"] = f"000{turn}"
    if fmt == "bweb":
        record.update(
            CD_CARGO_PERGUNTA="1",
            DS_CARGO_PERGUNTA="Presidente",
            CD_TIPO_URNA="1",
            CD_TIPO_VOTAVEL={"95": "2", "96": "3"}.get(number, "1"),
            QT_APTOS="120",
            QT_COMPARECIMENTO="100",
            QT_ABSTENCOES="20",
            NR_URNA_EFETIVADA="0099",
            DT_EMISSAO_BU="2026-01-01 17:00:00",
            DT_BU_RECEBIDO="2026-01-01 18:00:00",
        )
    else:
        record.update(
            CD_CARGO="1",
            DS_CARGO="Presidente",
            TP_ABRANGENCIA="F",
            SG_UE="BR",
            SQ_CANDIDATO="-1" if number in ("95", "96") else "00000" + number,
        )
    record.update(changes)
    return record


def write_zip(
    path, records, fmt="section", encoding="latin1", delimiter=";", header=None, extra=None
):
    text = io.StringIO(newline="")
    fields = header or SCHEMAS[fmt]
    writer = csv.DictWriter(text, fieldnames=fields, delimiter=delimiter, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(fmt + ".csv", text.getvalue().encode(encoding))
        for name, content in (extra or {}).items():
            archive.writestr(name, content)
    return path


@pytest.fixture
def source_set(tmp_path):
    root = tmp_path / "sources with spaces"
    root.mkdir()
    records, bu = [], []
    for turn in (1, 2):
        for uf in ("SC", "DF", "ZZ"):
            for number, votes in (
                ("11", 60 if turn == 1 else 65),
                ("22", 30 if turn == 1 else 25),
                ("95", 0),
                ("96", 10),
            ):
                records.append(row(turn=turn, uf=uf, number=number, votes=votes))
                if uf == "SC":
                    bu.append(row(fmt="bweb", turn=turn, uf=uf, number=number, votes=votes))
    write_zip(root / "synthetic-section.zip", records)
    write_zip(root / "synthetic-bweb.zip", bu, fmt="bweb")
    return root
