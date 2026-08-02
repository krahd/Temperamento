from __future__ import annotations

import hashlib
import tarfile
import zipfile
from pathlib import Path

import pytest

import scripts.build_release as build_release
from temperamento import __version__


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_tree(root: Path) -> None:
    for directory in ("examples", "docs", "_site", "dist"):
        (root / directory).mkdir(parents=True)
    (root / "examples" / "example.txt").write_text("example\n", encoding="utf-8")
    (root / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")
    (root / "_site" / "index.html").write_text("<p>site</p>\n", encoding="utf-8")
    (root / "dist" / "temperamento.whl").write_bytes(b"wheel")


def test_release_archives_are_versioned_and_reproducible(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _prepare_tree(tmp_path)
    release = tmp_path / "release"
    monkeypatch.setattr(build_release, "ROOT", tmp_path)
    monkeypatch.setattr(build_release, "RELEASE", release)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1784678400")

    build_release.main()
    first = {path.name: _digest(path) for path in release.iterdir() if path.is_file()}
    build_release.main()
    second = {path.name: _digest(path) for path in release.iterdir() if path.is_file()}

    assert first == second
    prefix = f"temperamento-{__version__}"
    assert f"{prefix}-examples.zip" in first
    assert f"{prefix}-examples.tar.gz" in first
    assert f"{prefix}-documentation.zip" in first
    assert f"{prefix}-site.zip" in first
    assert "temperamento-0.4.0a1-examples.zip" not in first

    with zipfile.ZipFile(release / f"{prefix}-examples.zip") as archive:
        assert archive.namelist() == ["examples/example.txt"]
        assert archive.read("examples/example.txt") == b"example\n"
    with tarfile.open(release / f"{prefix}-examples.tar.gz") as archive:
        member = archive.getmember("examples/example.txt")
        assert member.uid == 0
        assert member.gid == 0
        assert member.mtime == 1784678400


def test_source_date_epoch_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-integer")
    with pytest.raises(ValueError, match="must be an integer"):
        build_release._source_date_epoch()

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "-1")
    with pytest.raises(ValueError, match="non-negative"):
        build_release._source_date_epoch()
