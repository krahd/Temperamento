from fractions import Fraction

import pytest

from temperamento.errors import RuntimeFault
from temperamento.interpreter import Interpreter
from temperamento.model import HarmonicCell, Instruction, Program

CELL = HarmonicCell(0, "M", "M")


def instruction(opcode: str, *operands: int) -> Instruction:
    return Instruction(opcode, tuple(operands), CELL, Fraction(0))


def test_division_by_zero_is_a_runtime_fault() -> None:
    program = Program((instruction("PUSH", 1), instruction("PUSH", 0), instruction("DIV")))
    with pytest.raises(RuntimeFault, match="division by zero"):
        Interpreter().run(program)


def test_undefined_label_is_a_runtime_fault() -> None:
    program = Program((instruction("JMP", 99),))
    with pytest.raises(RuntimeFault, match="undefined label"):
        Interpreter().run(program)


def test_duplicate_label_is_a_runtime_fault() -> None:
    program = Program((instruction("LBL", 1), instruction("LBL", 1)))
    with pytest.raises(RuntimeFault, match="duplicate label"):
        Interpreter().run(program)


def test_step_limit_stops_infinite_loop() -> None:
    program = Program((instruction("LBL", 1), instruction("JMP", 1)))
    with pytest.raises(RuntimeFault, match="step limit"):
        Interpreter(max_steps=10).run(program)


@pytest.mark.parametrize("max_steps", [0, -1, True, 1.5])
def test_step_limit_must_be_a_positive_integer(max_steps: int | float) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        Interpreter(max_steps=max_steps)


def test_unknown_opcode_is_a_runtime_fault_not_an_internal_exception() -> None:
    with pytest.raises(RuntimeFault, match="unsupported opcode"):
        Interpreter().run(Program((instruction("UNKNOWN"),)))


def test_wrong_operand_arity_is_a_runtime_fault() -> None:
    with pytest.raises(RuntimeFault, match="expects 1 operand"):
        Interpreter().run(Program((instruction("PUSH"),)))


def test_negative_operand_is_a_runtime_fault() -> None:
    with pytest.raises(RuntimeFault, match="non-negative integer"):
        Interpreter().run(Program((instruction("PUSH", -1),)))


def test_stack_underflow_reports_instruction() -> None:
    with pytest.raises(RuntimeFault, match="instruction 0"):
        Interpreter().run(Program((instruction("ADD"),)))


@pytest.mark.parametrize(
    ("opcode", "left", "right", "expected"),
    [
        ("ADD", 7, 5, 12),
        ("SUB", 7, 5, 2),
        ("MUL", 7, 5, 35),
        ("DIV", 7, 2, 3.5),
        ("AND", 7, 0, 0),
        ("AND", 7, 5, 1),
        ("OR", 0, 0, 0),
        ("OR", 0, 5, 1),
        ("EQ", 7, 7, 1),
        ("EQ", 7, 5, 0),
    ],
)
def test_binary_operations(opcode: str, left: int, right: int, expected: int | float) -> None:
    program = Program((instruction("PUSH", left), instruction("PUSH", right), instruction(opcode)))
    assert Interpreter().run(program).stack == (expected,)


@pytest.mark.parametrize(("value", "expected"), [(0, 1), (7, 0)])
def test_not_operation(value: int, expected: int) -> None:
    program = Program((instruction("PUSH", value), instruction("NOT")))
    assert Interpreter().run(program).stack == (expected,)


def test_swap_exchanges_the_top_two_values() -> None:
    program = Program(
        (
            instruction("PUSH", 1),
            instruction("PUSH", 2),
            instruction("PUSH", 3),
            instruction("SWAP"),
        )
    )
    assert Interpreter().run(program).stack == (1, 3, 2)


def test_pop_dup_out_and_end_semantics() -> None:
    program = Program(
        (
            instruction("PUSH", 3),
            instruction("DUP"),
            instruction("OUT"),
            instruction("POP"),
            instruction("END"),
            instruction("PUSH", 99),
        )
    )
    result = Interpreter().run(program)
    assert result.output == (3,)
    assert result.stack == ()
    assert result.steps == 5


def test_conditional_jump_falls_through_when_false_and_jumps_when_true() -> None:
    false_program = Program(
        (
            instruction("PUSH", 0),
            instruction("JMC", 1),
            instruction("PUSH", 7),
            instruction("JMP", 2),
            instruction("LBL", 1),
            instruction("PUSH", 99),
            instruction("LBL", 2),
        )
    )
    assert Interpreter().run(false_program).stack == (7,)

    true_program = Program(
        (
            instruction("PUSH", 1),
            instruction("JMC", 1),
            instruction("PUSH", 99),
            instruction("LBL", 1),
            instruction("PUSH", 7),
        )
    )
    assert Interpreter().run(true_program).stack == (7,)


def test_boolean_and_non_integer_operands_are_rejected() -> None:
    bool_instruction = Instruction("PUSH", (True,), CELL, Fraction(0))  # type: ignore[arg-type]
    float_instruction = Instruction("PUSH", (1.5,), CELL, Fraction(0))  # type: ignore[arg-type]
    with pytest.raises(RuntimeFault, match="non-negative integer"):
        Interpreter().run(Program((bool_instruction,)))
    with pytest.raises(RuntimeFault, match="non-negative integer"):
        Interpreter().run(Program((float_instruction,)))


def test_division_overflow_is_a_runtime_fault() -> None:
    huge = 10**10_000
    program = Program((instruction("PUSH", huge), instruction("PUSH", 1), instruction("DIV")))
    with pytest.raises(RuntimeFault, match="supported float range"):
        Interpreter().run(program)


@pytest.mark.parametrize("opcode", ["DUP", "SWAP"])
def test_stack_rearrangement_underflow_is_a_runtime_fault(opcode: str) -> None:
    instructions = () if opcode == "DUP" else (instruction("PUSH", 1),)
    with pytest.raises(RuntimeFault, match="instruction"):
        Interpreter().run(Program((*instructions, instruction(opcode))))
