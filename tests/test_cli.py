import json
from pathlib import Path

import pytest

from temperamento.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_compile_command_emits_canonical_toscript(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["compile", str(ROOT / "examples/arithmetic/add/add.musicxml")])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "PUSH 7\nPUSH 5\nADD\nOUT\nEND\n"
    assert captured.err == ""


def test_run_command_emits_machine_readable_result(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["run", str(ROOT / "examples/iteration/countdown/countdown.musicxml")])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == '{"output": [3, 2, 1], "stack": [], "steps": 22}\n'
    assert captured.err == ""


def test_user_error_returns_exit_code_two(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    result = main(["compile", str(tmp_path / "missing.musicxml")])
    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err.startswith("error: cannot read MusicXML:")


def test_cli_rejects_non_positive_step_limit() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["run", str(ROOT / "examples/arithmetic/add/add.musicxml"), "--max-steps", "0"])
    assert exc.value.code == 2


def test_validate_command_reports_instruction_and_ignored_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    result = main(["validate", str(source)])
    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == {
        "valid": True,
        "source": str(source),
        "instructions": 5,
        "ignored_base_events": 0,
    }
    assert captured.err == ""


def test_version_flag_reports_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    captured = capsys.readouterr()
    assert exc.value.code == 0
    assert captured.out == "temperamento 0.5.0a1\n"


def test_cli_rejects_non_integer_step_limit() -> None:
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "run",
                str(ROOT / "examples/arithmetic/add/add.musicxml"),
                "--max-steps",
                "many",
            ]
        )
    assert exc.value.code == 2


def test_run_text_output(capsys: pytest.CaptureFixture[str]) -> None:
    source = ROOT / "examples/showcase/hello-world-prelude/hello-world-prelude.musicxml"
    result = main(["run", str(source), "--output", "text"])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "Hello, World!\n"


def test_inspect_html_writes_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    output = tmp_path / "report.html"
    result = main(
        ["inspect", str(source), "--execute", "--format", "html", "--output", str(output)]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == str(output)
    assert "Score-to-program map" in output.read_text(encoding="utf-8")


def test_doctor_json_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    result = main(["doctor", "--json"])
    captured = capsys.readouterr()
    assert result == 0
    payload = json.loads(captured.out)
    assert payload["temperamento"] == "0.5.0a1"
    assert "musescore" in payload


def test_run_numbers_output(capsys: pytest.CaptureFixture[str]) -> None:
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    result = main(["run", str(source), "--output", "numbers"])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "12\n"


def test_text_output_rejects_non_integer_and_invalid_scalar(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from temperamento.interpreter import RuntimeResult

    class FakeInterpreter:
        def __init__(self, **_: object) -> None:
            pass

        def run(self, _: object) -> RuntimeResult:
            return RuntimeResult(output=(1.5,), stack=(), steps=1)

    monkeypatch.setattr("temperamento.cli.Interpreter", FakeInterpreter)
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    assert main(["run", str(source), "--output", "text"]) == 2
    assert "requires integer Unicode" in capsys.readouterr().err

    class InvalidScalarInterpreter(FakeInterpreter):
        def run(self, _: object) -> RuntimeResult:
            return RuntimeResult(output=(0xD800,), stack=(), steps=1)

    monkeypatch.setattr("temperamento.cli.Interpreter", InvalidScalarInterpreter)
    assert main(["run", str(source), "--output", "text"]) == 2
    assert "not a Unicode scalar" in capsys.readouterr().err


def test_doctor_text_missing_and_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("temperamento.cli.find_musescore", lambda _: None)
    assert main(["doctor"]) == 0
    assert "MuseScore Studio: not found" in capsys.readouterr().out

    from temperamento.musescore import MuseScoreInstallation

    executable = tmp_path / "mscore"
    executable.write_text("x", encoding="utf-8")
    installation = MuseScoreInstallation(executable, "MuseScore Studio test")
    monkeypatch.setattr("temperamento.cli.find_musescore", lambda _: installation)
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "MuseScore Studio: MuseScore Studio test" in output
    assert "Audio export: available" in output


def test_init_command_creates_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "new-piece"
    assert main(["init", str(target), "--title", "New Piece"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["project"] == str(target)
    assert (target / "new-piece.musicxml").is_file()


def test_render_command_delegates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "piece.mscz"
    source.write_bytes(b"x")

    def fake_render(
        source_path: Path, output: Path, formats: list[str], **_: object
    ) -> tuple[Path, ...]:
        assert Path(source_path) == source
        assert formats == ["pdf", "wav"]
        return (Path(output) / "piece.pdf", Path(output) / "piece.wav")

    monkeypatch.setattr("temperamento.cli.render_score", fake_render)
    out_dir = tmp_path / "build"
    assert main(["render", str(source), "--out-dir", str(out_dir), "--formats", "pdf, wav"]) == 0
    assert json.loads(capsys.readouterr().out)["outputs"] == [
        str(out_dir / "piece.pdf"),
        str(out_dir / "piece.wav"),
    ]


def test_inspect_text_json_and_output_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    assert main(["inspect", str(source), "--execute"]) == 0
    assert "Output: [12]" in capsys.readouterr().out

    assert main(["inspect", str(source), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["instruction_count"] == 5
    assert data["ignored_base_event_count"] == 0

    destination = tmp_path / "nested" / "inspection.txt"
    assert main(["inspect", str(source), "--output", str(destination)]) == 0
    assert capsys.readouterr().out.strip() == str(destination)
    assert "Base relation" in destination.read_text(encoding="utf-8")


def test_gui_writes_report_and_can_open_browser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    destination = tmp_path / "report.html"
    opened: list[str] = []
    monkeypatch.setattr("temperamento.cli.webbrowser.open", lambda uri: opened.append(uri) or True)
    assert main(["gui", str(source), "--output", str(destination)]) == 0
    assert destination.is_file()
    assert opened == [destination.resolve().as_uri()]
    assert capsys.readouterr().out.strip() == str(destination)


def test_gui_no_output_uses_temporary_destination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    monkeypatch.setattr("temperamento.cli.tempfile.mkdtemp", lambda **_: str(tmp_path))
    assert main(["gui", str(source), "--no-open"]) == 0
    destination = Path(capsys.readouterr().out.strip())
    assert destination == tmp_path / "report.html"
    assert destination.is_file()
