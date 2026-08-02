from pathlib import Path

import pytest

from temperamento.cli import main
from temperamento.compiler import compile_musicxml
from temperamento.toscript import parse_tos_plus_file


def test_compile_and_run_toscript_plus(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "program.tom"
    source.write_text("output 12\nend\n", encoding="utf-8")

    assert main(["compile", str(source)]) == 0
    assert capsys.readouterr().out == "PUSH 12\nOUT\nEND\n"

    assert main(["run", str(source), "--output", "numbers"]) == 0
    assert capsys.readouterr().out == "12\n"


def test_text_score_decompile_round_trip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "program.tom"
    source.write_text(
        """
        let start = 2
        push start
        loop:
        dup
        output
        push 1
        sub
        dup
        jump-if loop
        pop
        end
        """,
        encoding="utf-8",
    )
    canonical = "PUSH 2\nLBL 0\nDUP\nOUT\nPUSH 1\nSUB\nDUP\nJMC 0\nPOP\nEND\n"
    score = tmp_path / "program.musicxml"
    assert main(["score", str(source), "--output", str(score), "--transpose", "5"]) == 0
    assert capsys.readouterr().out.strip() == str(score)
    assert compile_musicxml(score).to_tos() == canonical

    lifted = tmp_path / "lifted.tom"
    assert main(["decompile", str(score), "--output", str(lifted)]) == 0
    assert capsys.readouterr().out.strip() == str(lifted)
    assert parse_tos_plus_file(lifted).to_tos() == canonical


def test_decompile_can_write_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "program.tos"
    source.write_text("PUSH 1\nOUT\nEND\n", encoding="utf-8")
    assert main(["decompile", str(source)]) == 0
    assert capsys.readouterr().out == "push 1\noutput\nend\n"
