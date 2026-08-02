from __future__ import annotations

import json
from pathlib import Path

import pytest

from temperamento.compiler import compile_musicxml
from temperamento.interpreter import Interpreter

ROOT = Path(__file__).resolve().parents[1]

SHOWCASES = [
    ("hello-world-prelude", "Hello, World!\n"),
    ("hanoi-three-study", "A-C\nA-B\nC-B\nA-C\nB-A\nB-C\nA-C\n"),
]


@pytest.mark.parametrize(("name", "expected_text"), SHOWCASES)
def test_text_showcases_execute_and_ship_complete_media(name: str, expected_text: str) -> None:
    directory = ROOT / "examples" / "showcase" / name
    source = directory / f"{name}.musicxml"
    result = Interpreter().run(compile_musicxml(source))
    assert "".join(chr(value) for value in result.output) == expected_text
    artifacts = [
        directory / f"{name}.mxl",
        directory / f"{name}.mid",
        directory / f"{name}-reference.wav",
        directory / f"{name}-execution.wav",
        directory / f"{name}-map.svg",
        directory / f"{name}-map.pdf",
        directory / f"{name}.html",
        directory / f"{name}.tos",
    ]
    for artifact in artifacts:
        assert artifact.is_file()
        assert artifact.stat().st_size > 0
    expected = json.loads((directory / "expected-output.json").read_text(encoding="utf-8"))
    assert expected["output"] == list(result.output)


def test_all_twelve_transpositions_compile_identically() -> None:
    root = ROOT / "examples" / "showcase" / "twelve-transpositions"
    programs = []
    for semitones in range(12):
        name = f"key-{semitones:02d}"
        programs.append(compile_musicxml(root / name / f"{name}.musicxml").to_tos())
    assert len(set(programs)) == 1


def test_hanoi_study_is_labelled_as_fixed_solution_not_general_solver() -> None:
    readme = (ROOT / "examples/showcase/hanoi-three-study/README.md").read_text(encoding="utf-8")
    assert "executable composition" in readme
    # The project documentation must not overclaim this fixed move sequence.
    status = (ROOT / "docs/STATUS.md").read_text(encoding="utf-8")
    assert "not a general Towers of Hanoi solver" in status
