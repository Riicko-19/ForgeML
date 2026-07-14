"""Builders for .forge archive fixtures.

Fixtures are constructed in memory rather than committed as binaries, so the
reference matrix stays readable and carries no model, credential, or personal
data.
"""

from __future__ import annotations

import copy
import io
import warnings
import zipfile
from collections.abc import Iterable, Mapping
from typing import Any

import yaml

SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

ENTRYPOINT_SOURCE = b"""def predict(document):
    return {"score": float(document["value"])}
"""

VALID_MANIFEST: dict[str, Any] = {
    "forge_version": 1,
    "model": {
        "name": "Reference Scorer",
        "framework": "python-callable",
        "version": "1.0.0",
    },
    "runtime": {"python": "3.11"},
    "entrypoint": {"module": "model", "callable": "predict"},
    "input": {
        "schema": {
            "$schema": SCHEMA_DIALECT,
            "type": "object",
            "properties": {"value": {"type": "number"}},
            "required": ["value"],
            "additionalProperties": False,
        }
    },
    "output": {
        "schema": {
            "type": "object",
            "properties": {"score": {"type": "number"}},
            "required": ["score"],
        }
    },
    "dependencies": ["numpy==2.1.0"],
    "metadata": {"team": "platform"},
}

DEFAULT_FILES: dict[str, bytes] = {"src/model.py": ENTRYPOINT_SOURCE}


def manifest(**overrides: Any) -> dict[str, Any]:
    """A valid manifest with top-level sections replaced."""

    document = copy.deepcopy(VALID_MANIFEST)
    document.update(overrides)
    return document


def build_forge(
    document: Mapping[str, Any] | None = None,
    *,
    raw_manifest: bytes | None = None,
    include_manifest: bool = True,
    files: Mapping[str, bytes] | None = None,
    hostile: Iterable[tuple[zipfile.ZipInfo, bytes]] = (),
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    """Build a .forge archive. Passing hostile members bypasses no check."""

    if document is None and raw_manifest is None:
        document = VALID_MANIFEST
    members = DEFAULT_FILES if files is None else files

    buffer = io.BytesIO()
    with warnings.catch_warnings():
        # Deliberate duplicate members are the point of one fixture.
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buffer, "w", compression) as archive:
            if include_manifest:
                payload = (
                    raw_manifest
                    if raw_manifest is not None
                    else yaml.safe_dump(dict(document or {})).encode("utf-8")
                )
                archive.writestr("forge.yaml", payload)
            for name, content in members.items():
                archive.writestr(name, content)
            for info, content in hostile:
                archive.writestr(info, content)
    return buffer.getvalue()


def symlink_member(name: str, target: str) -> tuple[zipfile.ZipInfo, bytes]:
    """A ZIP member whose mode marks it a symbolic link."""

    info = zipfile.ZipInfo(name)
    info.external_attr = 0o120777 << 16
    return info, target.encode("utf-8")


def patch_general_purpose_flags(
    data: bytes, *, set_bits: int, clear_bits: int
) -> bytes:
    """Rewrite the general-purpose bit flag in every ZIP header.

    The stdlib writer recomputes these flags, so an encrypted or non-UTF-8
    member can only be produced by editing the finished container.
    """

    patched = bytearray(data)
    for signature, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        index = patched.find(signature)
        while index != -1:
            flags = int.from_bytes(
                patched[index + offset : index + offset + 2], "little"
            )
            flags = (flags | set_bits) & ~clear_bits
            patched[index + offset : index + offset + 2] = flags.to_bytes(2, "little")
            index = patched.find(signature, index + 4)
    return bytes(patched)
