"""ZIP adapter for .forge archives.

This is the only module that knows a .forge file is a ZIP. It reads headers,
the manifest, and member bytes; it never imports, executes, or deserializes
package content.
"""

from __future__ import annotations

import hashlib
import stat
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, BinaryIO

import yaml
from yaml.nodes import Node

from forgeml.core.config import PackageLimits
from forgeml.core.errors import AppError, ErrorCategory
from forgeml.domain.package.models import (
    MANIFEST_NAME,
    ArchiveEntry,
    ArchiveInspection,
    ArchiveUnreadable,
    Finding,
)

_CHUNK_BYTES = 1_048_576


class _NoAliasLoader(yaml.SafeLoader):
    """Safe YAML loader that also refuses aliases.

    yaml.safe_load still expands aliases, so a small forge.yaml can allocate
    gigabytes through repeated references. A manifest has no legitimate need
    for them.
    """

    def compose_node(self, parent: Node | None, index: int) -> Node | None:
        alias: bool = self.check_event(  # type: ignore[no-untyped-call]
            yaml.events.AliasEvent
        )
        if alias:
            raise yaml.YAMLError("YAML aliases are not permitted in forge.yaml")
        return super().compose_node(parent, index)


def _unsafe_member(name: str) -> AppError:
    return AppError(
        category=ErrorCategory.VALIDATION,
        code="archive_unsafe_member",
        message=f"archive member is not safe to extract: {name[:64]}",
    )


def _to_entry(info: zipfile.ZipInfo) -> ArchiveEntry:
    mode = info.external_attr >> 16
    # Plenty of writers (including zipfile itself) store permission bits with
    # no file-type bits at all, so an absent type means an ordinary file.
    file_type = stat.S_IFMT(mode)
    is_directory = info.is_dir()
    is_symlink = file_type == stat.S_IFLNK
    return ArchiveEntry(
        name=info.filename,
        is_directory=is_directory,
        is_regular_file=not is_directory
        and not is_symlink
        and file_type in (0, stat.S_IFREG),
        is_symlink=is_symlink,
        is_encrypted=bool(info.flag_bits & 0x1),
        has_utf8_name=bool(info.flag_bits & 0x800) or info.filename.isascii(),
        compressed_size=info.compress_size,
        uncompressed_size=info.file_size,
    )


class ZipArchiveReader:
    """Reads .forge archive structure from a seekable binary stream."""

    def inspect(self, stream: BinaryIO, limits: PackageLimits) -> ArchiveInspection:
        with self._open(stream) as archive:
            entries = tuple(_to_entry(info) for info in archive.infolist())
            document, fault = self._read_manifest(archive, limits)
        return ArchiveInspection(
            entries=entries, manifest_document=document, manifest_fault=fault
        )

    def digest(
        self, stream: BinaryIO, paths: tuple[str, ...], limits: PackageLimits
    ) -> Mapping[str, str]:
        digests: dict[str, str] = {}
        with self._open(stream) as archive:
            for path in paths:
                try:
                    info = archive.getinfo(path)
                except KeyError:
                    continue
                if info.is_dir() or info.file_size > limits.max_uncompressed_bytes:
                    continue
                hasher = hashlib.sha256()
                try:
                    with archive.open(info) as member:
                        while chunk := member.read(_CHUNK_BYTES):
                            hasher.update(chunk)
                except (zipfile.BadZipFile, OSError):
                    continue
                digests[path] = hasher.hexdigest()
        return digests

    def extract(
        self, stream: BinaryIO, destination: str, limits: PackageLimits
    ) -> None:
        root = Path(destination).resolve()
        written = 0
        with self._open(stream) as archive:
            for info in archive.infolist():
                entry = _to_entry(info)
                target = (root / entry.name).resolve()
                if not target.is_relative_to(root):
                    raise _unsafe_member(entry.name)
                if entry.is_directory:
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if entry.is_symlink or entry.is_encrypted or not entry.is_regular_file:
                    raise _unsafe_member(entry.name)

                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as member, target.open("wb") as sink:
                    while chunk := member.read(_CHUNK_BYTES):
                        written += len(chunk)
                        if written > limits.max_uncompressed_bytes:
                            raise _unsafe_member(entry.name)
                        sink.write(chunk)

    def _open(self, stream: BinaryIO) -> zipfile.ZipFile:
        stream.seek(0)
        try:
            return zipfile.ZipFile(stream)
        except (zipfile.BadZipFile, OSError, ValueError) as error:
            raise ArchiveUnreadable(
                "archive is not a readable ZIP container"
            ) from error

    def _read_manifest(
        self, archive: zipfile.ZipFile, limits: PackageLimits
    ) -> tuple[Mapping[str, Any] | None, Finding | None]:
        try:
            info = archive.getinfo(MANIFEST_NAME)
        except KeyError:
            return None, Finding.MANIFEST_MISSING
        if info.file_size > limits.max_manifest_bytes:
            return None, Finding.MANIFEST_TOO_LARGE

        try:
            with archive.open(info) as member:
                raw = member.read(limits.max_manifest_bytes + 1)
        except (zipfile.BadZipFile, OSError, RuntimeError):
            return None, Finding.MANIFEST_MALFORMED
        # The header size above is the archive's own claim. This checks what was
        # actually delivered, so a lying header cannot smuggle a larger manifest.
        if len(raw) > limits.max_manifest_bytes:
            return None, Finding.MANIFEST_TOO_LARGE

        try:
            text = raw.decode("utf-8")
            # _NoAliasLoader derives from SafeLoader and additionally bans aliases.
            document = yaml.load(text, Loader=_NoAliasLoader)  # noqa: S506
        except (yaml.YAMLError, UnicodeDecodeError):
            return None, Finding.MANIFEST_MALFORMED
        if not isinstance(document, dict):
            return None, Finding.MANIFEST_NOT_MAPPING
        return document, None
