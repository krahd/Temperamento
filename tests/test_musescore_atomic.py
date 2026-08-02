from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from temperamento.errors import IntegrationError
from temperamento.musescore import export_score


def _executable(tmp_path: Path) -> Path:
    executable = tmp_path / "mscore"
    executable.write_text("fake", encoding="utf-8")
    return executable


def test_failed_export_preserves_existing_destination(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.musicxml"
    source.write_text("source", encoding="utf-8")
    output = tmp_path / "output.pdf"
    output.write_bytes(b"previous valid export")
    executable = _executable(tmp_path)

    def fail(command: list[Path | str], **_: object) -> subprocess.CompletedProcess[str]:
        arguments = [str(part) for part in command]
        if any(option in arguments for option in ("--long-version", "--version", "-v")):
            return subprocess.CompletedProcess(arguments, 0, "MuseScore Studio fake\n", "")
        raise IntegrationError("MuseScore Studio exited with status 7: conversion failed")

    monkeypatch.setattr("temperamento.musescore._run", fail)
    with pytest.raises(IntegrationError, match="status 7"):
        export_score(source, output, executable=executable)

    assert output.read_bytes() == b"previous valid export"


def test_successful_export_atomically_replaces_destination(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.musicxml"
    source.write_text("source", encoding="utf-8")
    output = tmp_path / "output.pdf"
    output.write_bytes(b"old")
    executable = _executable(tmp_path)

    def succeed(command: list[Path | str], **_: object) -> subprocess.CompletedProcess[str]:
        arguments = [str(part) for part in command]
        if any(option in arguments for option in ("--long-version", "--version", "-v")):
            return subprocess.CompletedProcess(arguments, 0, "MuseScore Studio fake\n", "")
        temporary_output = Path(arguments[arguments.index("-o") + 1])
        assert temporary_output != output
        assert temporary_output.suffix == output.suffix
        temporary_output.write_bytes(b"new")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr("temperamento.musescore._run", succeed)
    assert export_score(source, output, executable=executable) == output
    assert output.read_bytes() == b"new"
