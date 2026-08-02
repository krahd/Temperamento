from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

Mode = Literal["M", "m"]


@dataclass(frozen=True, order=True)
class NoteEvent:
    onset: Fraction
    duration: Fraction
    pitch_class: int
    octave: int
    staff: int
    voice: str
    chord_member: bool = False
    measure: int = 1
    beat: Fraction = Fraction(0)


@dataclass(frozen=True)
class ChordEvent:
    onset: Fraction
    duration: Fraction
    pitch_classes: tuple[int, ...]
    root: int
    mode: Mode
    measure: int = 1
    beat: Fraction = Fraction(0)


@dataclass(frozen=True)
class IgnoredBaseEvent:
    """Well-formed Base material outside the computational triad alphabet."""

    onset: Fraction
    pitch_classes: tuple[int, ...]
    note_count: int
    reason: str
    measure: int = 1
    beat: Fraction = Fraction(0)


@dataclass(frozen=True)
class HarmonicCell:
    distance: int
    initial_mode: Mode
    final_mode: Mode

    def __post_init__(self) -> None:
        if not 0 <= self.distance < 12:
            raise ValueError("distance must be in [0, 11]")
        if self.initial_mode not in {"M", "m"} or self.final_mode not in {"M", "m"}:
            raise ValueError("modes must be M or m")

    @property
    def token(self) -> str:
        return f"{self.distance}{self.initial_mode}{self.final_mode}"


@dataclass(frozen=True)
class Instruction:
    opcode: str
    operands: tuple[int, ...]
    cell: HarmonicCell
    onset: Fraction
    measure: int = 1
    beat: Fraction = Fraction(0)
    initial_root: int | None = None
    final_root: int | None = None
    voice_onsets: tuple[Fraction, ...] = ()

    def to_tos(self) -> str:
        suffix = "" if not self.operands else " " + " ".join(map(str, self.operands))
        return f"{self.opcode}{suffix}"


@dataclass(frozen=True)
class Program:
    instructions: tuple[Instruction, ...]
    source: str | None = None
    ignored_base_events: tuple[IgnoredBaseEvent, ...] = ()

    def to_tos(self) -> str:
        return "\n".join(instruction.to_tos() for instruction in self.instructions) + "\n"
