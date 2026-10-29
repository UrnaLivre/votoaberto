"""Same path resolution as CLI: TSE_REAL_INPUT overrides JSON input_dir."""

from collections.abc import Mapping
from pathlib import Path

from tse_importer.domain import Config
from votoaberto_auditor.cli import import_config, parser


def official_config(environment: Mapping[str, str], default_output: Path) -> Config:
    args = ["import"]
    if config_path := environment.get("TSE_REAL_CONFIG"):
        args += ["--config", config_path]
    if input_dir := environment.get("TSE_REAL_INPUT"):
        args += ["--input", input_dir]
    if not (config_path or input_dir):
        raise ValueError("Defina TSE_REAL_INPUT ou TSE_REAL_CONFIG")
    if not config_path:
        args += ["--output", str(default_output), "--territory", "SC"]
    return import_config(parser().parse_args(args))
