#!/usr/bin/env python3
"""Pack a package directory into a .forge archive.

A .forge file is just a ZIP containing a root-level forge.yaml and a src/ tree,
so this is deliberately tiny and depends on nothing but the standard library --
you do not need the backend virtualenv to build a package.

    python3 scripts/forge_pack.py examples/hello-model
    python3 scripts/forge_pack.py examples/hello-model -o /tmp/hello.forge

The archive it writes is exactly what POST /v1/packages expects. The platform
validates it; this script does not, so an invalid package will still pack and
will then be rejected with findings -- which is a useful thing to be able to try.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

MANIFEST = "forge.yaml"
SOURCE_ROOT = "src"
EXCLUDED = {"__pycache__", ".DS_Store", ".git"}


def _members(source: Path) -> list[Path]:
    return sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and not any(part in EXCLUDED for part in path.parts)
    )


def pack(source: Path, destination: Path) -> Path:
    if not (source / MANIFEST).is_file():
        raise SystemExit(f"error: {source}/{MANIFEST} is missing")
    if not (source / SOURCE_ROOT).is_dir():
        raise SystemExit(f"error: {source}/{SOURCE_ROOT}/ is missing")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for member in _members(source):
            archive.write(member, member.relative_to(source).as_posix())
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="directory holding forge.yaml and src/")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output path (default: <source>.forge next to the directory)",
    )
    arguments = parser.parse_args(argv)

    source = arguments.source.resolve()
    output = arguments.output or source.with_suffix(".forge")

    written = pack(source, output)
    print(f"packed {written} ({written.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
