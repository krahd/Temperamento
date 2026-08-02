from __future__ import annotations

import pytest

from temperamento.interpreter import Interpreter
from temperamento.opcodes import lookup_name
from temperamento.universality import (
    DecrementJump,
    Halt,
    Increment,
    compile_two_counter_machine,
)


def test_every_emitted_instruction_belongs_to_toscript_core() -> None:
    machine = {
        0: Increment(1, 1),
        1: Increment(2, 2),
        2: DecrementJump(1, 3, 0),
        3: Halt(),
    }
    program = compile_two_counter_machine(machine, entry_state=0)
    assert all(lookup_name(instruction.opcode) is not None for instruction in program.instructions)


@pytest.mark.parametrize(("counter_1", "counter_2"), [(0, 0), (1, 0), (3, 4), (8, 2)])
def test_two_counter_translation_moves_counter_one_into_counter_two(
    counter_1: int,
    counter_2: int,
) -> None:
    machine = {
        0: DecrementJump(1, 2, 1),
        1: Increment(2, 0),
        2: Halt(),
    }
    program = compile_two_counter_machine(
        machine,
        entry_state=0,
        initial_counters=(counter_1, counter_2),
    )
    result = Interpreter(max_steps=10_000).run(program)
    assert result.stack == (0, counter_1 + counter_2)


def test_two_counter_translation_preserves_zero_branch_and_counter_order() -> None:
    machine = {
        0: DecrementJump(2, 1, 2),
        1: Halt(),
        2: Halt(),
    }
    zero = Interpreter().run(
        compile_two_counter_machine(machine, entry_state=0, initial_counters=(5, 0))
    )
    nonzero = Interpreter().run(
        compile_two_counter_machine(machine, entry_state=0, initial_counters=(5, 3))
    )
    assert zero.stack == (5, 0)
    assert nonzero.stack == (5, 2)


def test_two_counter_machine_validation_rejects_invalid_definitions() -> None:
    with pytest.raises(ValueError, match="at least one state"):
        compile_two_counter_machine({}, entry_state=0)
    with pytest.raises(ValueError, match="undefined entry state"):
        compile_two_counter_machine({0: Halt()}, entry_state=1)
    with pytest.raises(ValueError, match="undefined machine state"):
        compile_two_counter_machine({0: Increment(1, 1)}, entry_state=0)
    with pytest.raises(ValueError, match="non-negative"):
        compile_two_counter_machine({0: Halt()}, entry_state=0, initial_counters=(-1, 0))
