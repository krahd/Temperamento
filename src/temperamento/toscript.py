from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import cast

from .errors import StaticError
from .model import HarmonicCell, Instruction, Mode, Program
from .opcodes import OpcodeSpec, assigned_opcodes, lookup_name
from .validation import validate_program

_LABEL_PATTERN = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_-]*|[0-9]+)$")
_MAX_SOURCE_CHARACTERS = 5_000_000
_MAX_SOURCE_BYTES = 5 * 1024 * 1024
_MAX_INSTRUCTIONS = 100_000


@dataclass(frozen=True)
class _Statement:
    line: int
    operation: str
    arguments: tuple[str, ...]


def _cells_by_name() -> dict[str, HarmonicCell]:
    result: dict[str, HarmonicCell] = {}
    for token, spec in assigned_opcodes().items():
        result[spec.name] = HarmonicCell(
            int(token[:-2]), cast(Mode, token[-2]), cast(Mode, token[-1])
        )
    return result


_CELLS_BY_NAME = _cells_by_name()


def _check_text_size(text: str, dialect: str) -> None:
    if len(text) > _MAX_SOURCE_CHARACTERS:
        raise StaticError(
            f"{dialect} source exceeds the {_MAX_SOURCE_CHARACTERS}-character safety limit"
        )


def _read_source(path: Path, dialect: str) -> str:
    try:
        if path.stat().st_size > _MAX_SOURCE_BYTES:
            raise StaticError(f"{dialect} source exceeds the {_MAX_SOURCE_BYTES}-byte safety limit")
        return path.read_text(encoding="utf-8")
    except StaticError:
        raise
    except (OSError, UnicodeError) as exc:
        raise StaticError(f"cannot read {dialect}: {exc}") from exc


def _clean_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        in_string = False
        quote = ""
        escaped = False
        result: list[str] = []
        for character in raw:
            if escaped:
                result.append(character)
                escaped = False
                continue
            if character == "\\" and in_string:
                result.append(character)
                escaped = True
                continue
            if in_string:
                result.append(character)
                if character == quote:
                    in_string = False
                continue
            if character in {'"', "'"}:
                in_string = True
                quote = character
                result.append(character)
                continue
            if character == "#":
                break
            result.append(character)
        line = "".join(result).strip()
        if line:
            lines.append((line_number, line))
    return lines


def _parse_non_negative_integer(raw: str, *, line: int, role: str) -> int:
    try:
        value = int(raw, 10)
    except ValueError as exc:
        raise StaticError(
            f"line {line}: {role} must be a decimal integer; received {raw!r}"
        ) from exc
    if value < 0:
        raise StaticError(f"line {line}: {role} must be non-negative; received {value}")
    return value


def _validate_control_flow(program: Program) -> None:
    labels: dict[int, int] = {}
    targets: set[int] = set()
    for index, instruction in enumerate(program.instructions):
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


def _instruction(
    spec: OpcodeSpec,
    operands: tuple[int, ...],
    *,
    index: int,
) -> Instruction:
    return Instruction(
        spec.name,
        operands,
        _CELLS_BY_NAME[spec.name],
        Fraction(index),
        measure=index + 1,
        beat=Fraction(1),
    )


def _check_instruction_capacity(instructions: list[Instruction]) -> None:
    if len(instructions) >= _MAX_INSTRUCTIONS:
        raise StaticError(f"program exceeds the {_MAX_INSTRUCTIONS}-instruction safety limit")


def parse_tos(text: str, *, source: str | None = None) -> Program:
    _check_text_size(text, "TOScript")
    instructions: list[Instruction] = []
    for line_number, line in _clean_lines(text):
        _check_instruction_capacity(instructions)
        fields = line.split()
        name = fields[0].upper()
        spec = lookup_name(name)
        if spec is None:
            raise StaticError(f"line {line_number}: unknown TOScript operation {fields[0]!r}")
        if len(fields) - 1 != len(spec.operands):
            raise StaticError(
                f"line {line_number}: {name} expects {len(spec.operands)} operand(s); "
                f"received {len(fields) - 1}"
            )
        operands = tuple(
            _parse_non_negative_integer(raw, line=line_number, role=kind)
            for raw, kind in zip(fields[1:], spec.operands, strict=True)
        )
        instructions.append(_instruction(spec, operands, index=len(instructions)))
    if not instructions:
        raise StaticError("TOScript source contains no instructions")
    program = Program(tuple(instructions), source)
    _validate_control_flow(program)
    return program


def parse_tos_file(path: str | Path) -> Program:
    source = Path(path)
    return parse_tos(_read_source(source, "TOScript"), source=str(source))


def _parse_plus_statements(text: str) -> tuple[list[_Statement], dict[str, int]]:
    statements: list[_Statement] = []
    constants: dict[str, int] = {}
    for line_number, line in _clean_lines(text):
        if len(statements) >= _MAX_INSTRUCTIONS:
            raise StaticError(
                f"TOScript+ source exceeds the {_MAX_INSTRUCTIONS}-statement safety limit"
            )
        if line.lower().startswith("let "):
            match = re.fullmatch(r"let\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s]+)", line)
            if match is None:
                raise StaticError(f"line {line_number}: expected `let NAME = INTEGER`")
            name, raw_value = match.groups()
            if name in constants:
                raise StaticError(f"line {line_number}: duplicate constant {name!r}")
            constants[name] = _parse_non_negative_integer(
                raw_value, line=line_number, role=f"constant {name}"
            )
            continue
        if line.endswith(":"):
            label = line[:-1].strip()
            if not _LABEL_PATTERN.fullmatch(label):
                raise StaticError(f"line {line_number}: invalid label name {label!r}")
            statements.append(_Statement(line_number, "label", (label,)))
            continue
        operation, _, remainder = line.partition(" ")
        normalised = operation.lower()
        arguments = (remainder.strip(),) if remainder.strip() else ()
        if normalised in {"label", "lbl"}:
            if len(arguments) != 1 or not arguments[0]:
                raise StaticError(f"line {line_number}: label expects one name")
            label = arguments[0]
            if not _LABEL_PATTERN.fullmatch(label):
                raise StaticError(f"line {line_number}: invalid label name {label!r}")
            statements.append(_Statement(line_number, "label", (label,)))
        else:
            statements.append(_Statement(line_number, normalised, arguments))
    return statements, constants


def _label_ids(statements: list[_Statement]) -> dict[str, int]:
    explicit_numeric: set[int] = set()
    definitions: list[tuple[int, str]] = []
    seen: set[str] = set()
    for statement in statements:
        if statement.operation != "label":
            continue
        label = statement.arguments[0]
        if label in seen:
            raise StaticError(f"line {statement.line}: duplicate label {label!r}")
        seen.add(label)
        definitions.append((statement.line, label))
        if label.isdecimal():
            explicit_numeric.add(
                _parse_non_negative_integer(label, line=statement.line, role="label")
            )

    labels: dict[str, int] = {}
    next_id = 0
    for line_number, label in definitions:
        if label.isdecimal():
            labels[label] = _parse_non_negative_integer(label, line=line_number, role="label")
            continue
        while next_id in explicit_numeric or next_id in labels.values():
            next_id += 1
        labels[label] = next_id
        next_id += 1
    return labels


def _resolve_value(raw: str, constants: dict[str, int], *, line: int, role: str) -> int:
    if raw in constants:
        return constants[raw]
    return _parse_non_negative_integer(raw, line=line, role=role)


def _resolve_label(raw: str, labels: dict[str, int], *, line: int) -> int:
    if raw not in labels:
        raise StaticError(f"line {line}: undefined label {raw!r}")
    return labels[raw]


def _single_argument(statement: _Statement) -> str:
    if len(statement.arguments) != 1 or not statement.arguments[0]:
        raise StaticError(f"line {statement.line}: {statement.operation} expects one argument")
    return statement.arguments[0]


def _append_named(
    instructions: list[Instruction],
    name: str,
    operands: tuple[int, ...] = (),
) -> None:
    _check_instruction_capacity(instructions)
    spec = lookup_name(name)
    if spec is None:  # pragma: no cover - internal invariant
        raise AssertionError(name)
    instructions.append(_instruction(spec, operands, index=len(instructions)))


def parse_tos_plus(text: str, *, source: str | None = None) -> Program:
    _check_text_size(text, "TOScript+")
    statements, constants = _parse_plus_statements(text)
    labels = _label_ids(statements)
    instructions: list[Instruction] = []

    aliases = {
        "add": "ADD",
        "sub": "SUB",
        "mul": "MUL",
        "div": "DIV",
        "not": "NOT",
        "pop": "POP",
        "dup": "DUP",
        "and": "AND",
        "or": "OR",
        "eq": "EQ",
        "swap": "SWAP",
        "end": "END",
    }

    for statement in statements:
        operation = statement.operation
        if operation == "label":
            _append_named(
                instructions,
                "LBL",
                (_resolve_label(statement.arguments[0], labels, line=statement.line),),
            )
            continue
        if operation == "push":
            raw = _single_argument(statement)
            _append_named(
                instructions,
                "PUSH",
                (_resolve_value(raw, constants, line=statement.line, role="PUSH operand"),),
            )
            continue
        if operation in {"jump", "jmp"}:
            raw = _single_argument(statement)
            _append_named(
                instructions,
                "JMP",
                (_resolve_label(raw, labels, line=statement.line),),
            )
            continue
        if operation in {"jump-if", "jmc"}:
            raw = _single_argument(statement)
            _append_named(
                instructions,
                "JMC",
                (_resolve_label(raw, labels, line=statement.line),),
            )
            continue
        if operation in {"output", "out"}:
            if statement.arguments:
                raw = _single_argument(statement)
                _append_named(
                    instructions,
                    "PUSH",
                    (_resolve_value(raw, constants, line=statement.line, role="output operand"),),
                )
            _append_named(instructions, "OUT")
            continue
        if operation == "print":
            raw = _single_argument(statement)
            try:
                value = ast.literal_eval(raw)
            except (SyntaxError, ValueError) as exc:
                raise StaticError(f"line {statement.line}: print expects a quoted string") from exc
            if not isinstance(value, str):
                raise StaticError(f"line {statement.line}: print expects a quoted string")
            for character in value:
                _append_named(instructions, "PUSH", (ord(character),))
                _append_named(instructions, "OUT")
            continue
        if operation in aliases:
            if statement.arguments:
                raise StaticError(f"line {statement.line}: {operation} takes no arguments")
            _append_named(instructions, aliases[operation])
            continue

        raise StaticError(f"line {statement.line}: unknown TOScript+ operation {operation!r}")

    if not instructions:
        raise StaticError("TOScript+ source contains no executable instructions")
    program = Program(tuple(instructions), source)
    _validate_control_flow(program)
    return program


def parse_tos_plus_file(path: str | Path) -> Program:
    source = Path(path)
    return parse_tos_plus(_read_source(source, "TOScript+"), source=str(source))


def to_tos_plus(program: Program) -> str:
    validate_program(program)
    labels = {
        instruction.operands[0]: str(instruction.operands[0])
        for instruction in program.instructions
        if instruction.opcode == "LBL"
    }
    lines: list[str] = []
    for instruction in program.instructions:
        name = instruction.opcode
        if name == "LBL":
            lines.append(f"{labels[instruction.operands[0]]}:")
        elif name == "JMP":
            lines.append(f"jump {labels[instruction.operands[0]]}")
        elif name == "JMC":
            lines.append(f"jump-if {labels[instruction.operands[0]]}")
        elif name == "PUSH":
            lines.append(f"push {instruction.operands[0]}")
        elif name == "OUT":
            lines.append("output")
        else:
            lines.append(name.lower())
    return "\n".join(lines) + "\n"
