from pathlib import Path

import pytest

from scripts.generate_examples import SourceInstruction, build_score
from temperamento.compiler import compile_musicxml
from temperamento.interpreter import Interpreter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLES = [
    ("arithmetic/add/add", (12,)),
    ("conditional/equal/equal", (1,)),
    ("iteration/countdown/countdown", (3, 2, 1)),
]

PROGRAMS = {
    "add": [
        SourceInstruction("5MM", (7,)),
        SourceInstruction("5MM", (5,)),
        SourceInstruction("0MM"),
        SourceInstruction("8mm"),
        SourceInstruction("4mm"),
    ],
    "equal": [
        SourceInstruction("5MM", (3,)),
        SourceInstruction("5MM", (3,)),
        SourceInstruction("10MM"),
        SourceInstruction("0mm", (1,)),
        SourceInstruction("5MM", (0,)),
        SourceInstruction("8mm"),
        SourceInstruction("1mm", (2,)),
        SourceInstruction("11MM", (1,)),
        SourceInstruction("5MM", (1,)),
        SourceInstruction("8mm"),
        SourceInstruction("11MM", (2,)),
        SourceInstruction("4mm"),
    ],
    "countdown": [
        SourceInstruction("5MM", (3,)),
        SourceInstruction("11MM", (1,)),
        SourceInstruction("7MM"),
        SourceInstruction("8mm"),
        SourceInstruction("5MM", (1,)),
        SourceInstruction("1MM"),
        SourceInstruction("7MM"),
        SourceInstruction("0mm", (1,)),
        SourceInstruction("6MM"),
        SourceInstruction("4mm"),
    ],
}


@pytest.mark.parametrize(("relative", "expected_output"), EXAMPLES)
def test_example_compilation_and_execution(
    relative: str,
    expected_output: tuple[int, ...],
) -> None:
    base = ROOT / "examples" / relative
    program = compile_musicxml(base.with_suffix(".musicxml"))
    assert program.to_tos() == base.with_suffix(".tos").read_text(encoding="utf-8")
    assert Interpreter().run(program).output == expected_output


@pytest.mark.parametrize(
    ("name", "expected_output"),
    [("add", (12,)), ("equal", (1,)), ("countdown", (3, 2, 1))],
)
@pytest.mark.parametrize("transpose", range(12))
def test_whole_score_transposition_preserves_program_and_result(
    name: str,
    expected_output: tuple[int, ...],
    transpose: int,
    tmp_path: Path,
) -> None:
    original_tree = build_score(PROGRAMS[name], transpose=0)
    transformed_tree = build_score(
        PROGRAMS[name],
        transpose=transpose,
        reverse_voicing=True,
        double_roots=True,
    )
    original_path = tmp_path / f"{name}-original.musicxml"
    transformed_path = tmp_path / f"{name}-{transpose}.musicxml"
    original_tree.write(original_path, encoding="utf-8", xml_declaration=True)
    transformed_tree.write(transformed_path, encoding="utf-8", xml_declaration=True)

    original = compile_musicxml(original_path)
    transformed = compile_musicxml(transformed_path)
    assert transformed.to_tos() == original.to_tos()
    assert Interpreter().run(transformed).output == expected_output


@pytest.mark.parametrize(
    ("original", "transformed"),
    [
        (
            "examples/arithmetic/add/add.musicxml",
            "examples/equivalent-scores/add-transposed.musicxml",
        ),
        (
            "examples/iteration/countdown/countdown.musicxml",
            "examples/equivalent-scores/countdown-transposed.musicxml",
        ),
    ],
)
def test_committed_equivalent_scores_are_bytecode_identical(
    original: str,
    transformed: str,
) -> None:
    original_program = compile_musicxml(ROOT / original)
    transformed_program = compile_musicxml(ROOT / transformed)
    assert transformed_program.to_tos() == original_program.to_tos()
    assert Interpreter().run(transformed_program) == Interpreter().run(original_program)


def test_compilation_is_deterministic() -> None:
    source = ROOT / "examples/conditional/equal/equal.musicxml"
    outputs = {compile_musicxml(source).to_tos() for _ in range(20)}
    assert len(outputs) == 1
