"""Separate evidence dimensions from local promotion and public readiness."""

from .domain import TERRITORIES, CoverageRequirements, Selection


def coverage_assessment(
    observed: list[dict], selection: Selection, requirements: CoverageRequirements
) -> dict:
    territories = requirements.expected_territories(selection)
    turns = requirements.rounds or selection.rounds
    present = {(item["round"], item["uf"]) for item in observed}
    expected = {(turn, uf) for turn in turns for uf in territories}
    missing = expected - present
    missing_rounds = set(selection.rounds) - {turn for turn, _ in present}

    def pairs(values):
        return [{"round": turn, "uf": uf} for turn, uf in sorted(values)]

    return {
        "status": "incomplete"
        if missing or missing_rounds
        else "complete"
        if expected
        else "observed_only",
        "scope": "territory_round_presence",
        "basis": "explicit_requirements"
        if requirements.territories
        else "selection"
        if expected
        else "available_inputs",
        "expected_pairs": pairs(expected),
        "observed_pairs": pairs(present),
        "missing_pairs": pairs(missing),
        "missing_selected_rounds": sorted(missing_rounds),
        "additional_observed_pairs": pairs(present - expected) if expected else [],
        "national_presence": {
            "rounds": list(turns),
            "status": "complete"
            if {(turn, uf) for turn in turns for uf in TERRITORIES} <= present
            else "incomplete",
        },
        "section_completeness": {
            "status": "not_assessed",
            "reason": "Sem inventário exaustivo independente das seções esperadas",
        },
    }


def source_hash_assessment(catalog: dict) -> dict:
    sources = []
    for item in catalog["files"]:
        if not item["name"].lower().endswith(".zip"):
            continue
        verification = item.get("verification", {})
        status = verification.get("status", "error")
        matches = verification.get("matches")
        # Legacy 'verified' is also only an operator declaration, never authenticated origin.
        trusted = verification.get("reference", {}).get("trusted", False) is True
        sources.append(
            {
                "path": item["path"],
                "status": status,
                "digest_comparison": "match"
                if matches is True
                else "mismatch"
                if matches is False
                else "not_compared",
                "reference_trust": "operator_declared" if trusted else "not_assigned",
                "origin_authentication": "not_performed",
            }
        )
    assigned_matches = sum(
        s["digest_comparison"] == "match" and s["reference_trust"] == "operator_declared"
        for s in sources
    )
    failure = any(s["status"] in ("mismatch", "unsupported", "error") for s in sources)
    all_matches = bool(sources) and all(s["digest_comparison"] == "match" for s in sources)
    status = (
        "failed"
        if failure
        else "matched_operator_trusted"
        if sources and assigned_matches == len(sources)
        else "partially_matched_operator_trusted"
        if assigned_matches
        else "matched_without_assigned_trust"
        if all_matches
        else "unverified"
    )
    return {
        "status": status,
        "sources": sources,
        "operator_trusted_matches": assigned_matches,
        "source_count": len(sources),
        "origin_authentication": "not_performed",
        "signature_verification": "not_performed",
        "trust_basis": "operator_configuration",
    }


def reconciliation_assessment(stats: dict | None, database: dict, *, evidence: str) -> dict:
    if stats is None:
        return {"status": "not_assessed", "evidence": "unavailable"}
    differences = stats["different_rows"] + stats["bu_math_errors"]
    unmatched = stats["only_section_rows"] + stats["only_bu_rows"] + stats["ambiguous_locations"]
    matched_sections = database["comparison"].get("matched", 0)
    total_sections = sum(row["sections"] for row in database["observed_coverage"])
    status = (
        "divergent"
        if differences
        else "complete"
        if total_sections and matched_sections == total_sections and not unmatched
        else "partial"
        if stats["matched_rows"]
        else "not_verifiable"
    )
    return {
        **stats,
        "status": status,
        "evidence": evidence,
        "matched_section_rounds": matched_sections,
        "observed_section_rounds": total_sections,
        "scope": "presidential_rows_in_selected_inputs",
        "equipment_identity": "not_asserted",
    }


def assess_release(
    database: dict,
    selection: Selection,
    requirements: CoverageRequirements,
    catalog: dict,
    reconciliation: dict | None,
    data_kind: str,
    *,
    require_verified: bool = False,
    evidence: str = "import_streams",
) -> dict:
    coverage = coverage_assessment(database["observed_coverage"], selection, requirements)
    source_hashes = source_hash_assessment(catalog)
    source_hashes["evidence"] = (
        "current_import_hashes"
        if evidence == "import_streams"
        else "retained_catalog_no_source_reread"
    )
    comparison = reconciliation_assessment(reconciliation, database, evidence=evidence)
    checks = database["checks"]
    local_blockers = []
    if not database["structurally_valid"]:
        local_blockers.append("database_checks_failed")
    if checks["mathematics"]["status"] == "failed":
        local_blockers.append("mathematical_checks_failed")
    if coverage["status"] == "incomplete":
        local_blockers.append("required_coverage_missing")
    if source_hashes["status"] == "failed":
        local_blockers.append("source_hash_failure")
    if require_verified and source_hashes["status"] != "matched_operator_trusted":
        local_blockers.append("operator_trusted_hashes_required")
    if comparison["status"] in ("divergent", "not_assessed"):
        local_blockers.append("reconciliation_divergent_or_unassessed")
    public_blockers = list(local_blockers)
    if data_kind != "official":
        public_blockers.append("synthetic_data")
    if coverage["status"] != "complete":
        public_blockers.append("explicit_coverage_not_satisfied")
    if source_hashes["status"] != "matched_operator_trusted":
        public_blockers.append("operator_trusted_hashes_incomplete")
    if comparison["status"] != "complete":
        public_blockers.append("reconciliation_incomplete")
    if checks["mathematics"]["status"] != "passed":
        public_blockers.append("mathematics_not_fully_checked")
    return {
        **checks,
        "coverage": coverage,
        "source_hashes": source_hashes,
        "reconciliation": comparison,
        "local_release": {
            "status": "blocked" if local_blockers else "eligible",
            "blockers": local_blockers,
        },
        "public_readiness": {
            "status": "not_ready" if public_blockers else "ready_for_declared_scope",
            "blockers": public_blockers,
            "scope": coverage["expected_pairs"],
            "section_completeness": "not_assessed",
            "origin_authentication": "not_performed",
            "meaning": "Critérios técnicos no recorte declarado; não autoriza deploy nem certifica eleição/licença",
        },
    }
