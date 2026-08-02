from __future__ import annotations

import pytest

from temperamento.errors import RuntimeFault
from temperamento.interpreter import Interpreter
from temperamento.toscript import parse_tos


@pytest.mark.parametrize(
    "keyword",
    ["max_steps", "max_stack", "max_output", "max_integer_bits", "max_trace_cells"],
)
@pytest.mark.parametrize("value", [0, -1, True])
def test_interpreter_resource_limits_must_be_positive_integers(
    keyword: str,
    value: object,
) -> None:
    arguments = {keyword: value}
    with pytest.raises(ValueError, match="positive integer"):
        Interpreter(**arguments)  # type: ignore[arg-type]


def test_stack_budget_is_enforced() -> None:
    program = parse_tos("PUSH 1\nPUSH 2\nEND\n")
    with pytest.raises(RuntimeFault, match="stack size"):
        Interpreter(max_stack=1).run(program)


def test_output_budget_is_enforced() -> None:
    program = parse_tos("PUSH 1\nOUT\nPUSH 2\nOUT\nEND\n")
    with pytest.raises(RuntimeFault, match="output size"):
        Interpreter(max_output=1).run(program)


def test_integer_bit_budget_is_enforced_on_literals() -> None:
    program = parse_tos("PUSH 8\nEND\n")
    with pytest.raises(RuntimeFault, match="bit-length"):
        Interpreter(max_integer_bits=3).run(program)


def test_integer_bit_budget_is_enforced_on_arithmetic_results() -> None:
    program = parse_tos("PUSH 7\nPUSH 7\nMUL\nEND\n")
    with pytest.raises(RuntimeFault, match="bit-length"):
        Interpreter(max_integer_bits=5).run(program)


def test_execution_trace_budget_is_enforced() -> None:
    program = parse_tos("PUSH 1\nDUP\nEND\n")
    with pytest.raises(RuntimeFault, match="execution trace"):
        Interpreter(max_trace_cells=1).run(program, capture_trace=True)
