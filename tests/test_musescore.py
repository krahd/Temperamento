from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from temperamento.compiler import compile_score
from temperamento.errors import IntegrationError
from temperamento.musescore import (
    MuseScoreInstallation,
    export_score,
    find_musescore,
    musicxml_source,
    render_score,
)

ROOT = Path(__file__).resolve().parents[1]


def test_find_musescore_uses_explicit_executable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = tmp_path / "MuseScore4"
    executable.write_text("fake", encoding="utf-8")
    monkeypatch.setattr("temperamento.musescore._version", lambda _: "MuseScore Studio 4.test")
    result = find_musescore(executable)
    assert result == MuseScoreInstallation(executable.resolve(), "MuseScore Studio 4.test")


def test_missing_musescore_is_reported(tmp_path: Path) -> None:
    source = tmp_path / "score.mscz"
    source.write_bytes(b"native")
    with pytest.raises(IntegrationError, match="was not found"):
        export_score(source, tmp_path / "score.musicxml", executable=tmp_path / "missing")


def test_native_score_is_converted_before_compilation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    native = tmp_path / "piece.mscz"
    native.write_bytes(b"native-placeholder")
    known = ROOT / "examples/arithmetic/add/add.musicxml"

    def fake_export(source: Path, output: Path, **_: object) -> Path:
        assert Path(source) == native
        shutil.copyfile(known, output)
        return Path(output)

    monkeypatch.setattr("temperamento.musescore.export_score", fake_export)
    program = compile_score(native, musescore=tmp_path / "fake")
    assert program.to_tos() == "PUSH 7\nPUSH 5\nADD\nOUT\nEND\n"
    assert program.source == str(native)


def test_musicxml_source_rejects_unknown_extension(tmp_path: Path) -> None:
    source = tmp_path / "piece.txt"
    source.write_text("not a score", encoding="utf-8")
    with pytest.raises(IntegrationError, match="unsupported score extension"):
        with musicxml_source(source):
            pass


def test_render_score_normalises_formats_and_creates_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "piece.mscz"
    source.write_bytes(b"source")

    def fake_export(source_path: Path, output: Path, **_: object) -> Path:
        assert Path(source_path) == source
        Path(output).write_bytes(b"rendered")
        return Path(output)

    monkeypatch.setattr("temperamento.musescore.export_score", fake_export)
    outputs = render_score(source, tmp_path / "build", ["pdf", "midi", "pdf", ".wav"])
    assert [path.name for path in outputs] == ["piece.pdf", "piece.mid", "piece.wav"]


def test_render_score_rejects_unknown_format(tmp_path: Path) -> None:
    with pytest.raises(IntegrationError, match="unsupported MuseScore export format"):
        render_score(tmp_path / "piece.mscz", tmp_path, ["exe"])


def test_installation_available_property(tmp_path: Path) -> None:
    executable = tmp_path / "mscore"
    installation = MuseScoreInstallation(executable, None)
    assert installation.available is False
    executable.write_text("x", encoding="utf-8")
    assert installation.available is True


def test_candidate_paths_uses_environment_path_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = tmp_path / "mscore"
    executable.write_text("x", encoding="utf-8")
    monkeypatch.setenv("TEMPERAMENTO_MUSESCORE", str(executable))
    monkeypatch.setattr("temperamento.musescore.shutil.which", lambda _: str(executable))
    monkeypatch.setattr("temperamento.musescore.platform.system", lambda: "Linux")
    from temperamento.musescore import _candidate_paths

    candidates = _candidate_paths()
    assert candidates[0] == executable
    assert candidates.count(executable) == 1


def test_candidate_paths_includes_platform_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from temperamento.musescore import _candidate_paths

    monkeypatch.delenv("TEMPERAMENTO_MUSESCORE", raising=False)
    monkeypatch.setattr("temperamento.musescore.shutil.which", lambda _: None)
    monkeypatch.setattr("temperamento.musescore.platform.system", lambda: "Darwin")
    assert any("Applications/MuseScore" in path.as_posix() for path in _candidate_paths())

    monkeypatch.setattr("temperamento.musescore.platform.system", lambda: "Windows")
    monkeypatch.setenv("PROGRAMFILES", "C:/Program Files")
    monkeypatch.delenv("PROGRAMFILES(X86)", raising=False)
    assert any(path.name == "MuseScore4.exe" for path in _candidate_paths())


def test_run_reports_start_timeout_and_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    from temperamento.musescore import _run

    def os_error(*_: object, **__: object) -> object:
        raise OSError("no executable")

    monkeypatch.setattr("temperamento.musescore.subprocess.run", os_error)
    with pytest.raises(IntegrationError, match="cannot start"):
        _run(["missing"])

    def timeout(*_: object, **__: object) -> object:
        raise subprocess.TimeoutExpired(["mscore"], 1)

    monkeypatch.setattr("temperamento.musescore.subprocess.run", timeout)
    with pytest.raises(IntegrationError, match="timeout"):
        _run(["slow"])

    completed = subprocess.CompletedProcess(["mscore"], 7, stdout="", stderr="bad score")
    monkeypatch.setattr("temperamento.musescore.subprocess.run", lambda *a, **k: completed)
    with pytest.raises(IntegrationError, match="status 7: bad score"):
        _run(["bad"])
    assert _run(["bad"], check=False) == completed


def test_version_tries_fallbacks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import subprocess

    from temperamento.musescore import _version

    calls: list[str] = []

    def fake_run(command: list[Path | str], **_: object) -> subprocess.CompletedProcess[str]:
        option = str(command[-1])
        calls.append(option)
        if option == "--long-version":
            raise IntegrationError("unsupported")
        if option == "--version":
            return subprocess.CompletedProcess(command, 1, "", "")
        return subprocess.CompletedProcess(command, 0, "MuseScore Studio 4.6\nextra", "")

    monkeypatch.setattr("temperamento.musescore._run", fake_run)
    assert _version(tmp_path / "mscore") == "MuseScore Studio 4.6"
    assert calls == ["--long-version", "--version", "-v"]


def test_export_score_with_fake_musescore(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import subprocess

    executable = tmp_path / "mscore"
    executable.write_text("fake", encoding="utf-8")
    source = tmp_path / "source.musicxml"
    source.write_text("score", encoding="utf-8")
    output = tmp_path / "nested" / "output.musicxml"

    def fake_run(command: list[Path | str], **_: object) -> subprocess.CompletedProcess[str]:
        arguments = [str(part) for part in command]
        if any(option in arguments for option in ("--long-version", "--version", "-v")):
            return subprocess.CompletedProcess(arguments, 0, "MuseScore Studio fake\n", "")
        assert arguments[0] == str(executable.resolve())
        assert "-o" in arguments
        exported = Path(arguments[arguments.index("-o") + 1])
        input_score = Path(arguments[-1])
        exported.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(input_score, exported)
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr("temperamento.musescore._run", fake_run)
    assert export_score(source, output, executable=executable) == output
    assert output.read_text(encoding="utf-8") == "score"


def test_export_score_requires_existing_source_and_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(IntegrationError, match="score does not exist"):
        export_score(tmp_path / "missing.mscz", tmp_path / "out.musicxml")

    source = tmp_path / "piece.mscz"
    source.write_bytes(b"native")
    executable = tmp_path / "mscore"
    executable.write_text("x", encoding="utf-8")
    monkeypatch.setattr("temperamento.musescore._version", lambda _: None)
    monkeypatch.setattr("temperamento.musescore._run", lambda *a, **k: None)
    with pytest.raises(IntegrationError, match="did not create"):
        export_score(source, tmp_path / "out.musicxml", executable=executable)


def test_musicxml_source_passes_through_existing_formats(tmp_path: Path) -> None:
    for suffix in (".musicxml", ".xml", ".mxl"):
        source = tmp_path / f"piece{suffix}"
        source.write_bytes(b"score")
        with musicxml_source(source) as resolved:
            assert resolved == source
