"""Identifier evidence contracts for country aggregation; city names never identify countries."""

import re
from urllib.parse import urlparse

from .domain import ImportFailure

REGISTER_STATUS = "verified_official_section_register"
COUNTRY_FIELDS = {"DS_ENDERECO", "NM_BAIRRO", "NM_LOCAL_VOTACAO"}


def positive_id(value):
    return isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value) is not None


def validate_country_evidence(row, sources=None):
    """Validate an already reviewed assertion, not discover countries from arbitrary text.

    Legacy section joins retain their original contract. New assertions require an
    official, hash-pinned register, explicit country literals and per-turn keys.
    NM_BAIRRO is NOT generally a country field: only individually reviewed literals
    from this register may be used, with their raw fields retained for inspection.
    """
    iso = row.get("iso")
    if iso is None:
        if row.get("country") is not None:
            raise ImportFailure("Localidade residual com país atribuído")
        return
    if (
        not isinstance(iso, str)
        or not re.fullmatch(r"[A-Z]{2}", iso)
        or not isinstance(row.get("country"), str)
        or not row["country"].strip()
        or not isinstance(row.get("evidence"), list)
        or not row["evidence"]
    ):
        raise ImportFailure("País sem associação verificada por identificador")
    evidence = row["evidence"]
    if row.get("status") == "verified_section_join":
        seen = set()
        for item in evidence:
            if (
                not isinstance(item, list)
                or len(item) != 4
                or item[0] != iso
                or not positive_id(item[1])
                or not positive_id(item[2])
                or type(item[3]) is not int
                or item[3] < 1
                or tuple(item) in seen
            ):
                raise ImportFailure("Evidência de seção contraditória ou duplicada")
            seen.add(tuple(item))
        return
    if row.get("status") != REGISTER_STATUS:
        raise ImportFailure("País sem associação verificada por identificador")
    if row.get("candidate_countries") != [iso]:
        raise ImportFailure("Localidade com possível abrangência multinacional")
    seen, turns = set(), set()
    locations = set()
    for item in evidence:
        if not isinstance(item, dict):
            raise ImportFailure("Registro oficial inválido")
        source = (sources or {}).get(item.get("source"), {})
        url = urlparse(source.get("url", ""))
        if (
            url.scheme != "https"
            or url.hostname not in {"cdn.tse.jus.br", "www.tse.jus.br", "www.tre-df.jus.br"}
            or not all(
                re.fullmatch(r"[a-f0-9]{64}", source.get(key, ""))
                for key in ("sha256", "member_sha256")
            )
            or source.get("election_year") != 2026
            or not source.get("version")
            or not source.get("member")
        ):
            raise ImportFailure("Fonte oficial sem versão/hash verificável")
        field, literal = item.get("country_field"), item.get("country_literal")
        fields = item.get("fields", {})
        if (
            field not in COUNTRY_FIELDS
            or not isinstance(literal, str)
            or not literal
            or literal not in source.get("reviewed_country_literals", {}).get(iso, [])
            or not isinstance(fields.get(field), str)
            or re.search(r"(?<!\w)" + re.escape(literal) + r"(?!\w)", fields[field]) is None
            or item.get("iso") != iso
            or item.get("tse") != row["tse"]
            or type(item.get("round")) is not int
            or item["round"] not in (1, 2)
            or not positive_id(item.get("zone"))
            or not positive_id(item.get("section"))
            or not positive_id(item.get("local"))
            or type(item.get("record")) is not int
            or item["record"] < 2
            or item.get("primary_section") != "-1"
        ):
            raise ImportFailure("Registro sem identificação documental por código/zona/seção/turno")
        key = (item["round"], item["zone"], item["section"])
        if key in seen:
            raise ImportFailure("Identificador de seção/turno duplicado")
        seen.add(key)
        turns.add(item["round"])
        locations.add(tuple(fields.get(field) for field in sorted(COUNTRY_FIELDS)))
        # Reviewed literal vocabulary is used only to reject contradictory text,
        # never to assign a country from a city or from arbitrary address parsing.
        for other_iso, literals in source.get("reviewed_country_literals", {}).items():
            if other_iso != iso and any(
                re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", fields.get(field, ""))
                for value in literals
                for field in COUNTRY_FIELDS
            ):
                raise ImportFailure("Campos oficiais com países contraditórios")
    if sorted(turns) != row.get("verified_rounds"):
        raise ImportFailure("Turnos da evidência incompatíveis")
    if len(locations) != 1:
        raise ImportFailure("Locais de votação diferentes exigem revisão granular")


def validate_correspondence(rows, sources=None):
    mapping, owners = {}, {}
    for row in rows:
        code = row["tse"]
        if (
            not isinstance(code, str)
            or not re.fullmatch(r"[0-9]+", code)
            or int(code) == 0
            or code in mapping
        ):
            raise ImportFailure("Código TSE duplicado ou inválido na correspondência")
        validate_country_evidence(row, sources)
        mapping[code] = row
        if row.get("iso") is None:
            continue
        for item in row["evidence"]:
            # A legacy assertion covers both turns; never reuse its section for
            # a different locality in the new register contract.
            keys = (
                [(turn, item[1], item[2]) for turn in (1, 2)]
                if isinstance(item, list)
                else [(item["round"], item["zone"], item["section"])]
            )
            for key in keys:
                if key in owners and owners[key] != code:
                    raise ImportFailure("Seção atribuída a mais de uma localidade")
                owners[key] = code
    return mapping
