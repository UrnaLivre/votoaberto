"""Copy the current app + read-only asset inputs into a NEW isolated build area.

No Git worktree/branch, no deletion, no installation over an electoral release.
Usage: python tools/geography/prepare_preview.py --target .local/m5/preview
"""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.is_relative_to(ROOT / ".local") or target.exists():
        raise ValueError("Destino deve ser um novo diretório dentro de .local")
    target.mkdir(parents=True, exist_ok=False)
    ignore = shutil.ignore_patterns(
        "build",
        ".dart_tool",
        ".vs",
        "ephemeral",
        "coverage",
        ".gradle",
        "__pycache__",
        ".embedded-build.lock",
        ".flutter-plugins",
        ".flutter-plugins-dependencies",
    )
    shutil.copytree(
        ROOT / "apps/votoaberto_flutter", target / "apps/votoaberto_flutter", ignore=ignore
    )
    shutil.copytree(
        ROOT / "pipelines/tse_importer", target / "pipelines/tse_importer", ignore=ignore
    )
    print(target / "apps/votoaberto_flutter")


if __name__ == "__main__":
    main()
