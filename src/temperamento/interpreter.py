from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import RuntimeFault
from .model import Program
from .opcodes import lookup_name

Number = int | float


@dataclass(frozen=True)
class RuntimeResult:
    output: tuple[Number, ...]
    stack: tuple[Number, ...]
    steps: int
    trace: tuple[TraceStep, ...] = ()


@dataclass(frozen=True)
class TraceStep:
    pc: int
    opcode: str
    operands: tuple[int, ...]
    stack_before: tuple[Number, ...]
    stack_after: tuple[Number, ...]
    output_after: tuple[Number, ...]


def _positive_limit(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


class Interpreter:
    def __init__(
        self,
        max_steps: int = 100_000,
        *,
        max_stack: int = 100_000,
        max_output: int = 100_000,
        max_integer_bits: int = 1_000_000,
        max_trace_cells: int = 1_000_000,
    ) -> None:
        self.max_steps = _positive_limit(max_steps, "max_steps")
        self.max_stack = _positive_limit(max_stack, "max_stack")
        self.max_output = _positive_limit(max_output, "max_output")
        self.max_integer_bits = _positive_limit(max_integer_bits, "max_integer_bits")
        self.max_trace_cells = _positive_limit(max_trace_cells, "max_trace_cells")

    @staticmethod
    def _validate(program: Program) -> dict[int, int]:
        labels: dict[int, int] = {}
        jump_targets: list[int] = []

        for index, instruction in enumerate(program.instructions):
            spec = lookup_name(instruction.opcode)
            if spec is None:
                raise RuntimeFault(
                    f"unsupported opcode {instruction.opcode} at instruction {index}"
                )
            if len(instruction.operands) != len(spec.operands):
                raise RuntimeFault(
                    f"{instruction.opcode} expects {len(spec.operands)} operand(s) "
                    f"at instruction {index}; received {len(instruction.operands)}"
                )
            for operand, kind in zip(instruction.operands, spec.operands, strict=True):
                if isinstance(operand, bool) or not isinstance(operand, int) or operand < 0:
                    raise RuntimeFault(
                        f"{instruction.opcode} {kind} operand must be a non-negative integer "
                        f"at instruction {index}"
                    )

            if instruction.opcode == "LBL":
                label = instruction.operands[0]
                if label in labels:
                    raise RuntimeFault(f"duplicate label {label}")
                labels[label] = index
            elif instruction.opcode in {"JMC", "JMP"}:
                jump_targets.append(instruction.operands[0])

        undefined = sorted(set(jump_targets) - labels.keys())
        if undefined:
            raise RuntimeFault(f"undefined label(s): {', '.join(map(str, undefined))}")
        return labels

    def _validate_value(self, value: Number) -> Number:
        if isinstance(value, int) and value.bit_length() > self.max_integer_bits:
            raise RuntimeFault("integer magnitude exceeds the configured bit-length limit")
        if isinstance(value, float) and not math.isfinite(value):
            raise RuntimeFault("floating-point result is not finite")
        return value

    def run(self, program: Program, *, capture_trace: bool = False) -> RuntimeResult:
        labels = self._validate(program)
        stack: list[Number] = []
        output: list[Number] = []
        pc = 0
        steps = 0
        trace: list[TraceStep] = []
        trace_cells = 0

        def pop() -> Number:
            if not stack:
                raise RuntimeFault(f"stack underflow at instruction {pc}")
            return stack.pop()

        def push(value: Number) -> None:
            if len(stack) >= self.max_stack:
                raise RuntimeFault("stack size exceeds the configured limit")
            stack.append(self._validate_value(value))

        def emit(value: Number) -> None:
            if len(output) >= self.max_output:
                raise RuntimeFault("output size exceeds the configured limit")
            output.append(self._validate_value(value))

        def jump(label: int) -> int:
            return labels[label] + 1

        while pc < len(program.instructions):
            if steps >= self.max_steps:
                raise RuntimeFault("step limit exceeded")
            steps += 1
            instruction = program.instructions[pc]
            opcode = instruction.opcode
            next_pc = pc + 1
            stack_before = tuple(stack) if capture_trace else ()

            if opcode == "PUSH":
                push(instruction.operands[0])
            elif opcode == "POP":
                pop()
            elif opcode == "DUP":
                if not stack:
                    raise RuntimeFault(f"stack underflow at instruction {pc}")
                push(stack[-1])
            elif opcode == "SWAP":
                if len(stack) < 2:
                    raise RuntimeFault(f"stack underflow at instruction {pc}")
                stack[-2], stack[-1] = stack[-1], stack[-2]
            elif opcode in {"ADD", "SUB", "MUL", "DIV", "AND", "OR", "EQ"}:
                right = pop()
                left = pop()
                if opcode == "ADD":
                    push(left + right)
                elif opcode == "SUB":
                    push(left - right)
                elif opcode == "MUL":
                    push(left * right)
                elif opcode == "DIV":
                    if right == 0:
                        raise RuntimeFault("division by zero")
                    try:
                        push(left / right)
                    except OverflowError as exc:
                        raise RuntimeFault(
                            "division result is outside the supported float range"
                        ) from exc
                elif opcode == "AND":
                    push(1 if left != 0 and right != 0 else 0)
                elif opcode == "OR":
                    push(1 if left != 0 or right != 0 else 0)
                elif opcode == "EQ":
                    push(1 if left == right else 0)
            elif opcode == "NOT":
                push(1 if pop() == 0 else 0)
            elif opcode == "LBL":
                pass
            elif opcode == "JMC":
                if pop() != 0:
                    next_pc = jump(instruction.operands[0])
            elif opcode == "JMP":
                next_pc = jump(instruction.operands[0])
            elif opcode == "OUT":
                emit(pop())
            elif opcode == "END":
                break
            else:  # pragma: no cover - guarded by _validate
                raise AssertionError(f"unreachable opcode {opcode}")
            if capture_trace:
                trace_cells += len(stack_before) + len(stack) + len(output)
                if trace_cells > self.max_trace_cells:
                    raise RuntimeFault("execution trace exceeds the configured size limit")
                trace.append(
                    TraceStep(
                        pc=pc,
                        opcode=opcode,
                        operands=instruction.operands,
                        stack_before=stack_before,
                        stack_after=tuple(stack),
                        output_after=tuple(output),
                    )
                )
            pc = next_pc

        return RuntimeResult(tuple(output), tuple(stack), steps, tuple(trace))
