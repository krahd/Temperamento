from __future__ import annotations

from fractions import Fraction

import pytest

from temperamento.errors import StaticError
from temperamento.model import HarmonicCell, Instruction, Program
from temperamento.notation import program_to_musicxml
from temperamento.validation import validate_program


def _instruction(
    opcode: str,
    cell: HarmonicCell,
    operands: tuple[int, ...] = (),
) -> Instruction:
    return Instruction(opcode, operands, cell, Fraction(0))


def test_notation_rejects_opcode_harmonic_cell_conflict() -> None:
    program = Program((_instruction("PUSH", HarmonicCell(0, "M", "M"), (1,)),))
    with pytest.raises(StaticError, match="conflicts with harmonic cell"):
        program_to_musicxml(program)


def test_notation_rejects_reserved_harmonic_cell() -> None:
    program = Program((_instruction("END", HarmonicCell(3, "m", "m")),))
    with pytest.raises(StaticError, match="reserved harmonic cell"):
        program_to_musicxml(program)


@pytest.mark.parametrize(
    ("program", "message"),
    [
        (Program((_instruction("UNKNOWN", HarmonicCell(0, "M", "M")),)), "unsupported opcode"),
        (Program((_instruction("PUSH", HarmonicCell(5, "M", "M")),)), "expects 1 operand"),
        (
            Program((_instruction("PUSH", HarmonicCell(5, "M", "M"), (-1,)),)),
            "non-negative integer",
        ),
        (
            Program((_instruction("JMP", HarmonicCell(1, "m", "m"), (7,)),)),
            "undefined label",
        ),
    ],
)
def test_static_program_validation_rejects_malformed_dataclasses(
    program: Program,
    message: str,
) -> None:
    with pytest.raises(StaticError, match=message):
        validate_program(program)


def test_notation_rejects_invalid_xml_title() -> None:
    program = Program((_instruction("END", HarmonicCell(4, "m", "m")),))
    with pytest.raises(StaticError, match="not valid in XML"):
        program_to_musicxml(program, title="bad\x00title")


def test_notation_rejects_unbounded_title() -> None:
    program = Program((_instruction("END", HarmonicCell(4, "m", "m")),))
    with pytest.raises(StaticError, match="exceeds"):
        program_to_musicxml(program, title="x" * 4097)
