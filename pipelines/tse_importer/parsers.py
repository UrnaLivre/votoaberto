"""Observed 2026 CSV layouts, Latin-1 and semicolon. Fail closed on drift."""

import csv
import hashlib
import json
from collections import Counter
from importlib.resources import files
from pathlib import Path

from .discovery import member_stream
from .domain import TERRITORIES, ImportFailure, Limits, Selection, VoteRecord

SCHEMAS = json.loads(files("tse_importer").joinpath("schemas.json").read_text(encoding="utf8"))
MISSING = {"", "#NULO", "#NULO#", "-1", "#NE", "#NE#", "-3"}
SPECIAL = {"95": "blank", "96": "null", "97": "separate"}


def nullable(value: str) -> str | None:
    return None if value in MISSING else value


def number(value: str, *, optional: bool = False) -> int | None:
    if optional and value in MISSING:
        return None
    if not value.isascii() or not value.isdecimal():
        raise ImportFailure(f"Contagem inválida: {value!r}")
    parsed = int(value)
    if parsed > 2**63 - 1:
        raise ImportFailure("Contagem excede SQLite INTEGER")
    return parsed


def lines(stream, limits: Limits):
    while raw := stream.readline(limits.max_line_bytes + 1):
        if len(raw) > limits.max_line_bytes:
            raise ImportFailure("Linha excede max_line_bytes")
        yield raw.decode("latin1")


def detect(header: list[str]) -> str:
    if len(set(header)) != len(header):
        raise ImportFailure("Cabeçalho contém campos duplicados")
    for name, schema in SCHEMAS.items():
        if set(header) == set(schema):
            return name
    raise ImportFailure("Schema não suportado; execute inspect e registre o leiaute")


def inspect_member(
    path: Path, member: str, limits: Limits = Limits(), sample_rows: int = 3
) -> dict:
    with member_stream(path, member, limits) as stream:
        magic = stream.peek(8)[:8]
        if not member.lower().endswith(".csv"):
            return {
                "member": member,
                "format": "pdf" if magic.startswith(b"%PDF-") else "unknown",
                "status": "unsupported",
                "reason": "Documento auxiliar/sem parser eleitoral",
            }
        reader = csv.reader(lines(stream, limits), delimiter=";", strict=True)
        header = next(reader, [])
        try:
            fmt = detect(header)
            status, reason = "supported", None
        except ImportFailure as exc:
            fmt, status, reason = "unknown", "unsupported", str(exc)
        samples = []
        for _, row in zip(range(sample_rows), reader, strict=False):
            samples.append(row)
        return {
            "member": member,
            "format": fmt,
            "status": status,
            "reason": reason,
            "encoding": "latin1",
            "delimiter": ";",
            "header": header,
            "samples": samples,
            "crc_checked": False,
        }


def parse(path: Path, member: str, selection: Selection, limits: Limits, stats: dict):
    counts, types, urn_types = Counter(), Counter(), Counter()
    stats.update(rows_read=0, rows_selected=0)
    with member_stream(path, member, limits) as stream:
        reader = csv.reader(lines(stream, limits), delimiter=";", strict=True)
        header = next(reader, [])
        fmt = detect(header)
        stats["format"] = fmt
        positions = {name: i for i, name in enumerate(header)}
        office_col = positions["CD_CARGO_PERGUNTA" if fmt == "bweb" else "CD_CARGO"]
        round_col, uf_col = positions["NR_TURNO"], positions["SG_UF"]
        year_col = positions["ANO_ELEICAO"]
        for row in reader:
            stats["rows_read"] += 1
            line = reader.line_num
            if len(row) != len(header):
                raise ImportFailure(f"{member}:{line}: registro incompleto ({len(row)} campos)")
            office, round_text, uf = row[office_col], row[round_col], row[uf_col]
            counts[(round_text, office, uf)] += 1
            if office != "1":
                continue
            if round_text not in ("1", "2"):
                raise ImportFailure(f"{member}:{line}: turno presidencial desconhecido")
            if uf not in TERRITORIES:
                raise ImportFailure(f"{member}:{line}: abrangência presidencial não suportada {uf}")
            if (
                row[year_col] != str(selection.election_year)
                or int(round_text) not in selection.rounds
            ):
                continue
            if selection.territories != ("ALL",) and uf not in selection.territories:
                continue
            r = dict(zip(header, row, strict=True))
            try:
                if (
                    r["DS_CARGO_PERGUNTA" if fmt == "bweb" else "DS_CARGO"].casefold()
                    != "presidente"
                ):
                    raise ImportFailure("Código/descrição do cargo incompatíveis")
                ordinary = "0" if fmt == "bweb" else "2"
                if r["CD_TIPO_ELEICAO"] != ordinary:
                    raise ImportFailure("Somente eleição ordinária observada está suportada")
                if fmt == "section" and (r["SG_UE"] != "BR" or r["TP_ABRANGENCIA"] != "F"):
                    raise ImportFailure("Abrangência presidencial inesperada")
                for key in (
                    "CD_ELEICAO",
                    "CD_MUNICIPIO",
                    "NR_ZONA",
                    "NR_SECAO",
                    "NR_VOTAVEL",
                    "NR_LOCAL_VOTACAO",
                ):
                    number(r[key])
                kind = SPECIAL.get(r["NR_VOTAVEL"], "nominal")
                eligible = turnout = abstention = None
                context = ""
                extra = {
                    "CD_TIPO_ELEICAO": r["CD_TIPO_ELEICAO"],
                    "DT_GERACAO": r["DT_GERACAO"],
                    "HH_GERACAO": r["HH_GERACAO"],
                }
                extra["election_date"] = r["DT_PLEITO" if fmt == "bweb" else "DT_ELEICAO"]
                if fmt == "bweb":
                    expected_type = {"nominal": "1", "blank": "2", "null": "3"}.get(kind)
                    if expected_type is None or r["CD_TIPO_VOTAVEL"] != expected_type:
                        raise ImportFailure("Tipo votável presidencial ainda não suportado")
                    if r["CD_TIPO_URNA"] != "1":
                        raise ImportFailure(
                            "Situação de BU ainda não suportada; requer regra específica"
                        )
                    types[r["CD_TIPO_VOTAVEL"]] += 1
                    urn_types[r["CD_TIPO_URNA"]] += 1
                    eligible, turnout, abstention = (
                        number(r[k], optional=True)
                        for k in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")
                    )
                    context_fields = [
                        "NR_URNA_EFETIVADA",
                        "CD_CARGA_1_URNA_EFETIVADA",
                        "CD_CARGA_2_URNA_EFETIVADA",
                        "CD_FLASHCARD_URNA_EFETIVADA",
                        "DT_CARGA_URNA_EFETIVADA",
                        "DT_EMISSAO_BU",
                        "DT_BU_RECEBIDO",
                        "DS_SECOES_AGREGADAS",
                        "CD_TIPO_URNA",
                    ]
                    context_values = {k: r[k] for k in context_fields}
                    context = hashlib.sha256(
                        json.dumps(context_values, sort_keys=True).encode()
                    ).hexdigest()
                    extra.update(context_values)
                    extra.update(
                        {
                            k: r[k]
                            for k in (
                                "QT_APTOS",
                                "QT_COMPARECIMENTO",
                                "QT_ABSTENCOES",
                                "CD_PLEITO",
                                "DS_CARGO_PERGUNTA_SECAO",
                            )
                        }
                    )
                else:
                    if kind == "separate":
                        raise ImportFailure(
                            "Voto 97 ainda não suportado; requer interpretação específica"
                        )
                    extra["SQ_CANDIDATO"] = r["SQ_CANDIDATO"]
                votes = number(r["QT_VOTOS"])
                yield VoteRecord(
                    r["CD_ELEICAO"],
                    selection.election_year,
                    int(round_text),
                    uf,
                    r["CD_MUNICIPIO"],
                    r["NM_MUNICIPIO"],
                    r["NR_ZONA"],
                    r["NR_SECAO"],
                    r["NR_LOCAL_VOTACAO"],
                    r["NR_VOTAVEL"],
                    nullable(r.get("SQ_CANDIDATO", "")),
                    r["NM_VOTAVEL"],
                    kind,
                    votes,
                    eligible,
                    turnout,
                    abstention,
                    context,
                    json.dumps(extra, ensure_ascii=False, sort_keys=True),
                    line,
                )
                stats["rows_selected"] += 1
            except ImportFailure as exc:
                raise ImportFailure(f"{member}:{line}: {exc}") from exc
    stats["coverage_read"] = [
        {"round": k[0], "office": k[1], "uf": k[2], "rows": v} for k, v in sorted(counts.items())
    ]
    stats["vote_types"] = dict(types)
    stats["bu_statuses"] = dict(urn_types)
    stats["crc_checked"] = True
