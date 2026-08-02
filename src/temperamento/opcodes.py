from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .model import HarmonicCell

OperandKind = Literal["number", "label"]


@dataclass(frozen=True)
class OpcodeSpec:
    name: str
    operands: tuple[OperandKind, ...]
    description: str
    stack_inputs: int
    stack_outputs: int

    @property
    def stack_effect(self) -> int:
        return self.stack_outputs - self.stack_inputs


# TOScript Core uses the established Temperamento command positions where possible.
# Unassigned cells remain part of the topology and are explicitly reserved.
_ASSIGNED: dict[str, OpcodeSpec] = {
    "0MM": OpcodeSpec("ADD", (), "Pop y and x; push x + y.", 2, 1),
    "1MM": OpcodeSpec("SUB", (), "Pop y and x; push x - y.", 2, 1),
    "2MM": OpcodeSpec("MUL", (), "Pop y and x; push x * y.", 2, 1),
    "3MM": OpcodeSpec("DIV", (), "Pop y and x; push x / y.", 2, 1),
    "4MM": OpcodeSpec("NOT", (), "Pop x; push 1 if x is zero, otherwise 0.", 1, 1),
    "5MM": OpcodeSpec("PUSH", ("number",), "Push a non-negative integer literal.", 0, 1),
    "6MM": OpcodeSpec("POP", (), "Discard the top value.", 1, 0),
    "7MM": OpcodeSpec("DUP", (), "Duplicate the top value.", 1, 2),
    "8MM": OpcodeSpec("AND", (), "Boolean conjunction over two stack values.", 2, 1),
    "9MM": OpcodeSpec("OR", (), "Boolean disjunction over two stack values.", 2, 1),
    "10MM": OpcodeSpec("EQ", (), "Push 1 when two values are equal, otherwise 0.", 2, 1),
    "11MM": OpcodeSpec("LBL", ("label",), "Declare a numeric jump label.", 0, 0),
    "0mm": OpcodeSpec("JMC", ("label",), "Pop condition; jump when non-zero.", 1, 0),
    "1mm": OpcodeSpec("JMP", ("label",), "Unconditional jump.", 0, 0),
    "2mm": OpcodeSpec("SWAP", (), "Exchange the top two stack values.", 2, 2),
    "4mm": OpcodeSpec("END", (), "Terminate execution.", 0, 0),
    "8mm": OpcodeSpec("OUT", (), "Pop and append the top value to output.", 1, 0),
}
_BY_NAME = {spec.name: spec for spec in _ASSIGNED.values()}

if len(_BY_NAME) != len(_ASSIGNED):  # pragma: no cover - import-time invariant
    raise RuntimeError("opcode names must be unique")


def lookup(cell: HarmonicCell) -> OpcodeSpec | None:
    return _ASSIGNED.get(cell.token)


def lookup_name(name: str) -> OpcodeSpec | None:
    return _BY_NAME.get(name)


def assigned_opcodes() -> dict[str, OpcodeSpec]:
    return dict(_ASSIGNED)


def topology_table() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for initial_mode in ("M", "m"):
        for final_mode in ("M", "m"):
            for distance in range(12):
                token = f"{distance}{initial_mode}{final_mode}"
                spec = _ASSIGNED.get(token)
                rows.append(
                    {
                        "cell": token,
                        "distance": distance,
                        "initial_mode": initial_mode,
                        "final_mode": final_mode,
                        "opcode": spec.name if spec else "RESERVED",
                        "arity": len(spec.operands) if spec else None,
                        "stack_inputs": spec.stack_inputs if spec else None,
                        "stack_outputs": spec.stack_outputs if spec else None,
                    }
                )
    return rows
