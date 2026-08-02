from pathlib import Path

import pytest

from temperamento.compiler import compile_musicxml
from temperamento.errors import StaticError
from temperamento.model import Program
from temperamento.notation import digits_base12, program_to_musicxml, write_musicxml
from temperamento.toscript import parse_tos_plus


def test_base12_digits() -> None:
    assert digits_base12(0) == (0,)
    assert digits_base12(12) == (1, 0)
    assert digits_base12(143) == (11, 11)


@pytest.mark.parametrize("value", [-1, True])
def test_base12_digits_reject_invalid_values(value: int) -> None:
    with pytest.raises(StaticError, match="non-negative integers"):
        digits_base12(value)


def test_empty_program_cannot_be_notated() -> None:
    with pytest.raises(StaticError, match="empty program"):
        program_to_musicxml(Program(()))


def test_program_musicxml_core_round_trip(tmp_path: Path) -> None:
    program = parse_tos_plus(
        """
        let start = 3
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
        """
    )
    destination = tmp_path / "countdown.musicxml"
    write_musicxml(
        program,
        destination,
        title="Countdown",
        transpose=5,
        reverse_voicing=True,
        double_roots=True,
        decorative_base_line=True,
    )
    compiled = compile_musicxml(destination)
    assert compiled.to_tos() == program.to_tos()
    assert len(compiled.ignored_base_events) == len(program.instructions)


def test_notation_uses_one_measure_per_instruction(tmp_path: Path) -> None:
    import xml.etree.ElementTree as ET

    program = parse_tos_plus("output 12\nend\n")
    destination = tmp_path / "piece.musicxml"
    write_musicxml(program, destination)
    root = ET.parse(destination).getroot()
    measures = root.findall("./part/measure")
    assert len(measures) == 3
    labels = [item.text for item in root.findall(".//direction-type/words")]
    assert labels == ["PUSH 12", "OUT", "END"]
