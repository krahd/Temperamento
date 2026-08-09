from __future__ import annotations

import gzip
import hashlib
import io
import os
import shutil
import sys
import tarfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temperamento import __version__

RELEASE = ROOT / "release"
_DEFAULT_SOURCE_DATE_EPOCH = 946684800  # 2000-01-01T00:00:00Z
_TEXT_SUFFIXES = {
    ".css",
    ".htm",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mscx",
    ".musicxml",
    ".py",
    ".svg",
    ".tom",
    ".tos",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def _source_date_epoch() -> int:
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw is None:
        return _DEFAULT_SOURCE_DATE_EPOCH
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("SOURCE_DATE_EPOCH must be an integer") from exc
    if value < 0:
        raise ValueError("SOURCE_DATE_EPOCH must be non-negative")
    return value


def _files(source: Path) -> list[Path]:
    if not source.is_dir():
        raise FileNotFoundError(f"release source directory does not exist: {source}")
    return sorted(path for path in source.rglob("*") if path.is_file())


def _archive_bytes(path: Path) -> bytes:
    """Return platform-independent bytes for release archives.

    Git attributes keep tracked text at LF, but release inputs can also be generated
    at runtime. Normalise recognised UTF-8 text assets so archives built from the same
    logical tree are byte-identical on Windows and POSIX systems; preserve binary
    assets exactly.
    """
    data = path.read_bytes()
    if path.suffix.lower() not in _TEXT_SUFFIXES:
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _zip_tree(source: Path, destination: Path, *, epoch: int) -> None:
    timestamp = time.gmtime(max(epoch, _DEFAULT_SOURCE_DATE_EPOCH))[:6]
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in _files(source):
            arcname = (Path(source.name) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, _archive_bytes(path), compresslevel=9)


def _tar_tree(source: Path, destination: Path, *, epoch: int) -> None:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in _files(source):
            arcname = (Path(source.name) / path.relative_to(source)).as_posix()
            data = _archive_bytes(path)
            info = tarfile.TarInfo(arcname)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = epoch
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    destination.write_bytes(gzip.compress(buffer.getvalue(), compresslevel=9, mtime=epoch))


def _write_checksums(assets: list[Path]) -> None:
    lines = []
    for path in sorted(assets):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(ROOT)}")
    (RELEASE / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    epoch = _source_date_epoch()
    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    RELEASE.mkdir()

    prefix = f"temperamento-{__version__}"
    _zip_tree(ROOT / "examples", RELEASE / f"{prefix}-examples.zip", epoch=epoch)
    _tar_tree(ROOT / "examples", RELEASE / f"{prefix}-examples.tar.gz", epoch=epoch)
    _zip_tree(ROOT / "docs", RELEASE / f"{prefix}-documentation.zip", epoch=epoch)
    _zip_tree(ROOT / "_site", RELEASE / f"{prefix}-site.zip", epoch=epoch)

    assets = sorted((ROOT / "dist").glob("*")) + sorted(RELEASE.glob("*"))
    _write_checksums(assets)


if __name__ == "__main__":
    main()
