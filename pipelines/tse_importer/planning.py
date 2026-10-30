"""Read-only input preflight. Samples never establish complete electoral coverage."""

import shutil
from collections import defaultdict
from dataclasses import asdict

from .discovery import inventory
from .parsers import inspect_member


def plan(config):
    catalog = inventory(
        config.input_dir,
        config.limits,
        config.references,
        config.inventory_cache,
        config.source_paths,
    )
    errors, samples, duplicates = [], [], defaultdict(list)
    primary_bytes = largest_bweb = 0
    for item in catalog["files"]:
        if not item["name"].lower().endswith(".zip"):
            continue
        if digest := item.get("hashes", {}).get("sha256"):
            duplicates[digest].append(item["path"])
        if item["status"] != "ok" or item.get("verification", {}).get("status") in (
            "mismatch",
            "error",
            "unsupported",
        ):
            errors.append(
                {
                    "path": item["path"],
                    "status": item["status"],
                    "error": item.get("error"),
                    "hash_status": item.get("verification", {}).get("status"),
                }
            )
            continue
        item["inspection"] = []
        for member in item["members"]:
            if member["directory"]:
                continue
            description = inspect_member(
                config.input_dir / item["path"], member["name"], config.limits
            )
            item["inspection"].append(description)
            if description["status"] != "supported":
                if member["extension"] != ".pdf":
                    errors.append(
                        {
                            "path": item["path"],
                            "member": member["name"],
                            "error": description["reason"],
                        }
                    )
                continue
            if description["format"] == "section":
                primary_bytes += member["bytes"]
            else:
                largest_bweb = max(largest_bweb, member["bytes"])
            positions = {field: i for i, field in enumerate(description["header"])}
            for row in description["samples"]:
                samples.append(
                    {
                        "archive": item["path"],
                        "format": description["format"],
                        "uf": row[positions["SG_UF"]],
                        "round": row[positions["NR_TURNO"]],
                    }
                )
    existing = config.output_dir
    while not existing.exists():
        existing = existing.parent
    free = shutil.disk_usage(existing).free
    projected = config.storage.projected_peak_bytes
    capacity = (
        projected <= config.storage.max_work_disk_bytes
        and free - projected >= config.storage.min_free_disk_bytes
    )
    return {
        "plan_version": 1,
        "input_eligible": not errors,
        "capacity_for_declared_projection": capacity if projected else None,
        "national_load_allowed": not errors and capacity and bool(projected),
        "errors": errors,
        "sources": catalog,
        "sampled_pairs": samples,
        "sample_coverage_scope": "header and initial rows only; not full-file or section completeness",
        "duplicate_bytes": [paths for paths in duplicates.values() if len(paths) > 1],
        "storage": {
            "policy": asdict(config.storage),
            "free_bytes": free,
            "primary_declared_csv_bytes": primary_bytes,
            "largest_bweb_declared_csv_bytes": largest_bweb,
            "projection_basis": "operator-supplied pilot projection; 0 means not yet estimated",
            "unfiltered_envelope_bytes": 4 * primary_bytes + 3 * largest_bweb + 256 * 1024**2,
            "envelope_scope": "deliberately unfiltered disk amplification bound for planning; calibrate selected rows using pilot, not a measured national peak",
        },
    }
