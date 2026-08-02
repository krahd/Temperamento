from __future__ import annotations

from .errors import StaticError
from .model import Program
from .opcodes import lookup, lookup_name


def validate_program(
    program: Program,
    *,
    require_nonempty: bool = False,
    verify_harmonic_cells: bool = False,
) -> dict[int, int]:
    """Validate an in-memory TOScript Core program.

    Parsers and compilers already construct validated programs, but the public Python API
    also permits callers to instantiate dataclasses directly. Reverse conversion must not
    silently notate an opcode using an unrelated harmonic cell.
    """

    if require_nonempty and not program.instructions:
        raise StaticError("program contains no instructions")

    labels: dict[int, int] = {}
    targets: set[int] = set()
    for index, instruction in enumerate(program.instructions):
        spec = lookup_name(instruction.opcode)
        if spec is None:
            raise StaticError(
                f"unsupported opcode {instruction.opcode!r} at instruction {index + 1}"
            )
        if len(instruction.operands) != len(spec.operands):
            raise StaticError(
                f"{instruction.opcode} expects {len(spec.operands)} operand(s) at "
                f"instruction {index + 1}; received {len(instruction.operands)}"
            )
        for operand, kind in zip(instruction.operands, spec.operands, strict=True):
            if isinstance(operand, bool) or not isinstance(operand, int) or operand < 0:
                raise StaticError(
                    f"{instruction.opcode} {kind} operand must be a non-negative integer "
                    f"at instruction {index + 1}"
                )

        if verify_harmonic_cells:
            cell_spec = lookup(instruction.cell)
            if cell_spec is None:
                raise StaticError(
                    f"instruction {index + 1} uses reserved harmonic cell {instruction.cell.token}"
                )
            if cell_spec.name != instruction.opcode:
                raise StaticError(
                    f"instruction {index + 1} opcode {instruction.opcode} conflicts with "
                    f"harmonic cell {instruction.cell.token}, which encodes {cell_spec.name}"
                )

        if instruction.opcode == "LBL":
            label = instruction.operands[0]
            if label in labels:
                raise StaticError(
                    f"duplicate label {label} at instructions {labels[label] + 1} and {index + 1}"
                )
            labels[label] = index
        elif instruction.opcode in {"JMC", "JMP"}:
            targets.add(instruction.operands[0])

    undefined = sorted(targets - labels.keys())
    if undefined:
        raise StaticError(f"undefined label(s): {', '.join(map(str, undefined))}")
    return labels
