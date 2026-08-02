from pathlib import Path

import pytest

from scripts.generate_examples import SourceInstruction, build_score
from temperamento.compiler import compile_musicxml
from temperamento.opcodes import assigned_opcodes


@pytest.mark.parametrize("cell", sorted(assigned_opcodes()))
@pytest.mark.parametrize("transpose", range(12))
def test_every_assigned_cell_compiles_end_to_end(
    cell: str,
    transpose: int,
    tmp_path: Path,
) -> None:
    spec = assigned_opcodes()[cell]
    operands = tuple(143 - index for index, _ in enumerate(spec.operands))
    source_instructions = [SourceInstruction(cell, operands)]
    if spec.name in {"JMC", "JMP"}:
        source_instructions.append(SourceInstruction("11MM", (operands[0],)))
    score = build_score(
        source_instructions,
        transpose=transpose,
        reverse_voicing=True,
        double_roots=True,
    )
    source = tmp_path / f"{cell}-{transpose}.musicxml"
    score.write(source, encoding="utf-8", xml_declaration=True)
    program = compile_musicxml(source)
    assert len(program.instructions) == len(source_instructions)
    assert program.instructions[0].cell.token == cell
    assert program.instructions[0].opcode == spec.name
    assert program.instructions[0].operands == operands
