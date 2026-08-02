from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from temperamento.errors import StaticError
from temperamento.model import HarmonicCell, Instruction, Program
from temperamento.toscript import parse_tos, parse_tos_file, parse_tos_plus, to_tos_plus


def test_in_memory_source_character_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("temperamento.toscript._MAX_SOURCE_CHARACTERS", 3)
    with pytest.raises(StaticError, match="character safety limit"):
        parse_tos("END\n")


def test_file_source_byte_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("temperamento.toscript._MAX_SOURCE_BYTES", 3)
    source = tmp_path / "large.tos"
    source.write_text("END\n", encoding="utf-8")
    with pytest.raises(StaticError, match="byte safety limit"):
        parse_tos_file(source)


def test_core_instruction_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("temperamento.toscript._MAX_INSTRUCTIONS", 2)
    with pytest.raises(StaticError, match="instruction safety limit"):
        parse_tos("END\nEND\nEND\n")


def test_plus_expansion_instruction_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("temperamento.toscript._MAX_INSTRUCTIONS", 3)
    with pytest.raises(StaticError, match="instruction safety limit"):
        parse_tos_plus('print "ab"\n')


def test_canonical_lifting_rejects_invalid_control_flow() -> None:
    jump = Instruction(
        "JMP",
        (8,),
        HarmonicCell(1, "m", "m"),
        Fraction(0),
    )
    with pytest.raises(StaticError, match="undefined label"):
        to_tos_plus(Program((jump,)))
