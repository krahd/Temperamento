from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, cast

from .model import HarmonicCell, Instruction, Mode, Program
from .opcodes import assigned_opcodes

Counter = Literal[1, 2]


@dataclass(frozen=True)
class Increment:
    counter: Counter
    next_state: int


@dataclass(frozen=True)
class DecrementJump:
    counter: Counter
    zero_state: int
    nonzero_state: int


@dataclass(frozen=True)
class Halt:
    pass


CounterInstruction = Increment | DecrementJump | Halt


def _cells_by_opcode() -> dict[str, HarmonicCell]:
    cells: dict[str, HarmonicCell] = {}
    for token, spec in assigned_opcodes().items():
        cells[spec.name] = HarmonicCell(
            int(token[:-2]),
            cast(Mode, token[-2]),
            cast(Mode, token[-1]),
        )
    return cells


_CELLS_BY_OPCODE = _cells_by_opcode()


def _is_natural(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _validate_counter(counter: object, *, state: int) -> None:
    if isinstance(counter, bool) or counter not in {1, 2}:
        raise ValueError(f"state {state} counter must be 1 or 2")


def _validate_target(target: object, *, state: int, role: str) -> int:
    if not _is_natural(target):
        raise ValueError(f"state {state} {role} must be a non-negative integer")
    return cast(int, target)


def compile_two_counter_machine(
    states: Mapping[int, CounterInstruction],
    *,
    entry_state: int,
    initial_counters: tuple[int, int] = (0, 0),
) -> Program:
    """Construct a TOScript Core program simulating a deterministic two-counter machine.

    The stack representation is bottom-to-top ``(counter_1, counter_2)``. The
    construction assumes the idealised language semantics: unbounded natural-number
    values, stack capacity, and execution. The reference interpreter may impose a
    practical step limit.
    """

    if not states:
        raise ValueError("two-counter machine must define at least one state")
    if any(not _is_natural(state) for state in states):
        raise ValueError("state labels must be non-negative integers")
    if not _is_natural(entry_state):
        raise ValueError("entry state must be a non-negative integer")
    if entry_state not in states:
        raise ValueError(f"undefined entry state {entry_state}")
    if len(initial_counters) != 2:
        raise ValueError("initial counters must contain exactly two values")
    if any(not _is_natural(value) for value in initial_counters):
        raise ValueError("initial counters must be non-negative integers")

    targets: set[int] = set()
    for state, operation in states.items():
        if isinstance(operation, Increment):
            _validate_counter(operation.counter, state=state)
            targets.add(_validate_target(operation.next_state, state=state, role="next state"))
        elif isinstance(operation, DecrementJump):
            _validate_counter(operation.counter, state=state)
            targets.add(_validate_target(operation.zero_state, state=state, role="zero state"))
            targets.add(
                _validate_target(operation.nonzero_state, state=state, role="nonzero state")
            )
        elif not isinstance(operation, Halt):
            raise ValueError(f"state {state} has an unsupported instruction")
    undefined = sorted(targets - states.keys())
    if undefined:
        raise ValueError(f"undefined machine state(s): {', '.join(map(str, undefined))}")

    instructions: list[Instruction] = []

    def emit(opcode: str, *operands: int) -> None:
        cell = _CELLS_BY_OPCODE.get(opcode)
        if cell is None:  # pragma: no cover - import-time opcode construction
            raise RuntimeError(f"universality construction requires opcode {opcode}")
        instructions.append(
            Instruction(
                opcode,
                tuple(operands),
                cell,
                Fraction(len(instructions)),
            )
        )

    emit("PUSH", initial_counters[0])
    emit("PUSH", initial_counters[1])
    emit("JMP", entry_state)

    next_helper_label = max(states) + 1
    for state, operation in sorted(states.items()):
        emit("LBL", state)
        if isinstance(operation, Halt):
            emit("END")
            continue

        if isinstance(operation, Increment):
            if operation.counter == 1:
                emit("SWAP")
                emit("PUSH", 1)
                emit("ADD")
                emit("SWAP")
            else:
                emit("PUSH", 1)
                emit("ADD")
            emit("JMP", operation.next_state)
            continue

        helper_label = next_helper_label
        next_helper_label += 1
        if operation.counter == 1:
            emit("SWAP")
        emit("DUP")
        emit("PUSH", 0)
        emit("EQ")
        emit("JMC", helper_label)
        emit("PUSH", 1)
        emit("SUB")
        if operation.counter == 1:
            emit("SWAP")
        emit("JMP", operation.nonzero_state)
        emit("LBL", helper_label)
        if operation.counter == 1:
            emit("SWAP")
        emit("JMP", operation.zero_state)

    return Program(tuple(instructions), source="two-counter-machine construction")
