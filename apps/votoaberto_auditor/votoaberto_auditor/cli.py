"""Thin, noninteractive adapter to the shared engine."""

import argparse
import csv
import json
import sqlite3
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path

from tse_importer.discovery import drain, inventory, member_stream
from tse_importer.domain import Config, ImportFailure, Limits
from tse_importer.engine import run_import, validate_release, write_json
from tse_importer.parsers import inspect_member
from tse_importer.validation import validate_database


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="votoaberto-auditor",
        description="Inventário e processamento reprodutível de fontes TSE",
    )
    sub = root.add_subparsers(dest="command", required=True)
    for name in ("inventory", "inspect", "verify"):
        command = sub.add_parser(name)
        command.add_argument("--input", required=True, type=Path)
        command.add_argument("--json", type=Path, dest="json_path")
        command.add_argument(
            "--references",
            type=Path,
            help="JSON com algoritmo, digest, origin e trusted por caminho relativo",
        )
        if name == "verify":
            command.add_argument("--crc", action="store_true", help="Ler todos os membros até EOF")
    command = sub.add_parser("import")
    command.add_argument("--config", type=Path)
    command.add_argument("--input", type=Path)
    command.add_argument("--output", type=Path)
    command.add_argument("--office", choices=["president"], action="append")
    command.add_argument("--round", choices=[1, 2], type=int, action="append")
    command.add_argument("--territory", action="append")
    command.add_argument("--profile", choices=["public", "analyst"])
    command.add_argument("--synthetic", action="store_true", default=None)
    command.add_argument("--no-resume", action="store_true", default=None)
    command.add_argument("--require-verified", action="store_true", default=None)
    for name in ("validate", "report"):
        command = sub.add_parser(name)
        command.add_argument("--dataset", required=True, type=Path)
        command.add_argument("--json", type=Path, dest="json_path")
    return root


def import_config(args) -> Config:
    values = {}
    base = Path.cwd()
    if args.config:
        base = args.config.resolve().parent
        values = json.loads(args.config.read_text(encoding="utf8"))
    for key in ("input", "output"):
        if value := getattr(args, key):
            values[key + "_dir"] = str(value.resolve())
    selection = values.setdefault("selection", {})
    for key, target in (
        ("office", "offices"),
        ("round", "rounds"),
        ("territory", "territories"),
        ("profile", "profile"),
    ):
        if (value := getattr(args, key)) is not None:
            selection[target] = value
    if args.synthetic:
        values["data_kind"] = "synthetic"
    if args.no_resume:
        values["resume"] = False
    if args.require_verified:
        values["require_verified"] = True
    return Config.from_dict(values, base)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "import":
            release = run_import(
                import_config(args), lambda m: print(m, file=sys.stderr, flush=True)
            )
            print(json.dumps({"release": str(release)}, ensure_ascii=False))
            return 0
        if args.command in ("validate", "report"):
            target = args.dataset
            if (target / "current.json").is_file():
                pointer = json.loads((target / "current.json").read_text(encoding="utf8"))
                resolved = (target / pointer["path"]).resolve()
                if not resolved.is_relative_to(target.resolve() / "releases"):
                    raise ImportFailure("Ponteiro de release fora do diretório permitido")
                target = resolved
            if target.is_dir():
                result = validate_release(target)
                if args.command == "report":
                    result = {
                        **json.loads((target / "validation.json").read_text(encoding="utf8")),
                        "current_validation": result,
                    }
            else:
                result = validate_database(target)
        else:
            refs = json.loads(args.references.read_text(encoding="utf8")) if args.references else {}
            limits = Limits()
            result = inventory(args.input, limits, refs)
            for item in result["files"]:
                if item["status"] != "ok":
                    continue
                if args.command == "inspect":
                    item["inspection"] = [
                        inspect_member(args.input / item["path"], m["name"], limits)
                        for m in item["members"]
                        if not m["directory"]
                    ]
                if args.command == "verify" and args.crc:
                    for member in item["members"]:
                        if member["directory"]:
                            continue
                        with member_stream(
                            args.input / item["path"], member["name"], limits
                        ) as stream:
                            drain(stream, limits)
                        member["crc_checked"] = True
            result["valid"] = all(
                item["status"] in ("ok", "auxiliary")
                and item.get("verification", {}).get("status")
                not in ("mismatch", "unsupported", "error")
                for item in result["files"]
            )
            result["summary"] = {
                "files": len(result["files"]),
                "zip_bytes": sum(
                    i["bytes"] for i in result["files"] if i["name"].lower().endswith(".zip")
                ),
                "limits": asdict(limits),
            }
        if args.json_path:
            write_json(args.json_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("valid", True) else 1
    except KeyboardInterrupt:
        print(
            "Cancelado; publicação anterior preservada. Checkpoints completos podem ser retomados.",
            file=sys.stderr,
        )
        return 130
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        csv.Error,
        zipfile.BadZipFile,
        sqlite3.Error,
        NotImplementedError,
    ) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
