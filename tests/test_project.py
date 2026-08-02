from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from temperamento.compiler import compile_musicxml
from temperamento.errors import IntegrationError
from temperamento.interpreter import Interpreter
from temperamento.project import initialise_project


def test_initialise_project_creates_valid_starter(tmp_path: Path) -> None:
    target = tmp_path / "first-piece"
    created = initialise_project(target, title="First Piece")
    assert target / "first-piece.musicxml" in created
    mxl = target / "first-piece.mxl"
    assert mxl.is_file()
    assert (target / "temperamento.toml").is_file()
    program = compile_musicxml(target / "first-piece.musicxml")
    assert program.to_tos() == "PUSH 72\nOUT\nEND\n"
    assert Interpreter().run(program).output == (72,)

    repeated = tmp_path / "second-piece"
    initialise_project(repeated, title="First Piece")
    assert mxl.read_bytes() == (repeated / "second-piece.mxl").read_bytes()
    with zipfile.ZipFile(mxl) as archive:
        members = archive.infolist()
    assert members[0].filename == "mimetype"
    assert members[0].compress_type == zipfile.ZIP_STORED
    assert all(member.date_time == (1980, 1, 1, 0, 0, 0) for member in members)


def test_initialise_project_refuses_nonempty_directory(tmp_path: Path) -> None:
    target = tmp_path / "occupied"
    target.mkdir()
    (target / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(IntegrationError, match="not empty"):
        initialise_project(target)


def test_initialise_project_force_preserves_unrelated_content(tmp_path: Path) -> None:
    target = tmp_path / "occupied"
    nested = target / "nested"
    nested.mkdir(parents=True)
    keep_file = target / "keep.txt"
    keep_file.write_text("keep", encoding="utf-8")
    nested_file = nested / "old.txt"
    nested_file.write_text("old", encoding="utf-8")

    initialise_project(target, force=True)

    assert keep_file.read_text(encoding="utf-8") == "keep"
    assert nested_file.read_text(encoding="utf-8") == "old"
    assert (target / "occupied.musicxml").is_file()


def test_initialise_project_force_overwrites_known_files(tmp_path: Path) -> None:
    target = tmp_path / "piece"
    initialise_project(target)
    source = target / "piece.musicxml"
    source.write_text("stale", encoding="utf-8")

    initialise_project(target, force=True, title="Replacement")

    assert b"Replacement" in source.read_bytes()
    assert compile_musicxml(source).to_tos() == "PUSH 72\nOUT\nEND\n"


def test_initialise_project_writes_valid_quoted_toml(tmp_path: Path) -> None:
    import tomllib

    target = tmp_path / "quoted"
    initialise_project(target, title='A "quoted" title')
    config = tomllib.loads((target / "temperamento.toml").read_text(encoding="utf-8"))
    assert config["title"] == 'A "quoted" title'


@pytest.mark.parametrize("kind", ["target-file", "source-directory", "build-file"])
def test_initialise_project_rejects_unsafe_destination_shapes(tmp_path: Path, kind: str) -> None:
    target = tmp_path / "piece"
    if kind == "target-file":
        target.write_text("not a directory", encoding="utf-8")
        message = "not a directory"
    else:
        target.mkdir()
        if kind == "source-directory":
            (target / "piece.musicxml").mkdir()
            message = "not a regular file"
        else:
            (target / "build").write_text("not a directory", encoding="utf-8")
            message = "not a directory"
    with pytest.raises(IntegrationError, match=message):
        initialise_project(target, force=True)


def test_initialise_project_creates_native_file_only_when_explicitly_requested(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from temperamento.musescore import MuseScoreInstallation

    executable = tmp_path / "mscore"
    executable.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        "temperamento.project.require_musescore",
        lambda _: MuseScoreInstallation(executable, "test"),
    )

    def fake_export(source: Path, output: Path, **_: object) -> Path:
        Path(output).write_bytes(Path(source).read_bytes())
        return Path(output)

    monkeypatch.setattr("temperamento.project.export_score", fake_export)

    without_native = tmp_path / "without-native"
    created = initialise_project(without_native)
    assert not any(path.suffix == ".mscz" for path in created)

    target = tmp_path / "native-piece"
    created = initialise_project(target, musescore=executable)
    native = target / "native-piece.mscz"
    assert native in created
    assert native.is_file()
