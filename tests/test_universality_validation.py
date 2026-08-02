from __future__ import annotations

from typing import Any, cast

import pytest

from temperamento.universality import (
    DecrementJump,
    Halt,
    Increment,
    compile_two_counter_machine,
)


@pytest.mark.parametrize("counters", [(0,), (0, 1, 2)])
def test_initial_counter_tuple_must_have_exactly_two_values(counters: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="exactly two"):
        compile_two_counter_machine(
            {0: Halt()},
            entry_state=0,
            initial_counters=cast(tuple[int, int], counters),
        )


@pytest.mark.parametrize(
    "operation",
    [
        Increment(cast(Any, 0), 0),
        Increment(cast(Any, 3), 0),
        DecrementJump(cast(Any, True), 0, 0),
    ],
)
def test_machine_operations_reject_invalid_counter_numbers(operation: object) -> None:
    with pytest.raises(ValueError, match="counter must be 1 or 2"):
        compile_two_counter_machine(
            {0: cast(Any, operation)},
            entry_state=0,
        )


@pytest.mark.parametrize(
    "operation",
    [
        Increment(1, cast(Any, -1)),
        Increment(1, cast(Any, True)),
        DecrementJump(1, cast(Any, "zero"), 0),
        DecrementJump(1, 0, cast(Any, -1)),
    ],
)
def test_machine_operations_reject_invalid_target_labels(operation: object) -> None:
    with pytest.raises(ValueError, match="must be a non-negative integer"):
        compile_two_counter_machine(
            {0: cast(Any, operation)},
            entry_state=0,
        )


def test_machine_rejects_unsupported_instruction_objects() -> None:
    with pytest.raises(ValueError, match="unsupported instruction"):
        compile_two_counter_machine(
            {0: cast(Any, object())},
            entry_state=0,
        )


@pytest.mark.parametrize("entry", [-1, True, cast(Any, "0")])
def test_machine_rejects_invalid_entry_state(entry: object) -> None:
    with pytest.raises(ValueError, match="entry state must be"):
        compile_two_counter_machine({0: Halt()}, entry_state=cast(Any, entry))
