import pytest

from temperamento.model import HarmonicCell
from temperamento.opcodes import assigned_opcodes, lookup_name, topology_table


def test_topology_table_has_48_cells_and_17_assigned_opcodes() -> None:
    table = topology_table()
    assert len(table) == 48
    assert len({row["cell"] for row in table}) == 48
    assert len(assigned_opcodes()) == 17
    assert sum(row["opcode"] == "RESERVED" for row in table) == 31


def test_every_assigned_opcode_has_a_unique_reverse_lookup() -> None:
    specs = assigned_opcodes().values()
    assert len({spec.name for spec in specs}) == len(assigned_opcodes())
    for spec in specs:
        assert lookup_name(spec.name) == spec


def test_stack_effect_metadata_matches_core_operations() -> None:
    assert lookup_name("PUSH").stack_effect == 1
    assert lookup_name("ADD").stack_effect == -1
    assert lookup_name("DUP").stack_effect == 1
    assert lookup_name("SWAP").stack_effect == 0
    assert lookup_name("OUT").stack_effect == -1


def test_harmonic_cell_validates_distance_and_modes() -> None:
    with pytest.raises(ValueError, match="distance"):
        HarmonicCell(12, "M", "M")
    with pytest.raises(ValueError, match="modes"):
        HarmonicCell(0, "x", "M")  # type: ignore[arg-type]


def test_opcode_assignment_matches_reference_table() -> None:
    expected = {
        "0MM": "ADD",
        "1MM": "SUB",
        "2MM": "MUL",
        "3MM": "DIV",
        "4MM": "NOT",
        "5MM": "PUSH",
        "6MM": "POP",
        "7MM": "DUP",
        "8MM": "AND",
        "9MM": "OR",
        "10MM": "EQ",
        "11MM": "LBL",
        "0mm": "JMC",
        "1mm": "JMP",
        "2mm": "SWAP",
        "4mm": "END",
        "8mm": "OUT",
    }
    assert {cell: spec.name for cell, spec in assigned_opcodes().items()} == expected
