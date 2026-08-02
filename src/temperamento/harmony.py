from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import product

from .errors import HarmonyError
from .model import ChordEvent, HarmonicCell, Mode, NoteEvent

MAJOR = frozenset({0, 4, 7})
MINOR = frozenset({0, 3, 7})


def recognise_triad(notes: list[NoteEvent]) -> ChordEvent:
    if not notes:
        raise HarmonyError("empty chord")
    onsets = {n.onset for n in notes}
    if len(onsets) != 1:
        raise HarmonyError("chord notes must share an onset")
    pcs = frozenset(n.pitch_class % 12 for n in notes)
    if len(pcs) != 3:
        raise HarmonyError(f"pitch-class set {sorted(pcs)} is not an exact major or minor triad")
    candidates: list[tuple[int, Mode]] = []
    for root in range(12):
        rel = frozenset((pc - root) % 12 for pc in pcs)
        if rel == MAJOR:
            candidates.append((root, "M"))
        elif rel == MINOR:
            candidates.append((root, "m"))
    if len(candidates) != 1:
        raise HarmonyError(f"pitch-class set {sorted(pcs)} is not an exact major or minor triad")
    root, mode = candidates[0]
    return ChordEvent(
        onset=notes[0].onset,
        duration=max(n.duration for n in notes),
        pitch_classes=tuple(sorted(Counter(n.pitch_class % 12 for n in notes).elements())),
        root=root,
        mode=mode,
        measure=notes[0].measure,
        beat=notes[0].beat,
    )


def fifths_position(root: int) -> int:
    """Position on C-G-D-A-E-B-F#-C#-G#-D#-A#-F."""
    return (7 * (root % 12)) % 12


def fifths_distance(initial_root: int, final_root: int) -> int:
    return (fifths_position(final_root) - fifths_position(initial_root)) % 12


def decode_pair(initial: ChordEvent, final: ChordEvent) -> HarmonicCell:
    return HarmonicCell(fifths_distance(initial.root, final.root), initial.mode, final.mode)


def root_after_distance(initial_root: int, distance: int) -> int:
    """Return the pitch class reached by moving clockwise by distance fifths."""
    return (initial_root + 7 * distance) % 12


def all_cells() -> tuple[HarmonicCell, ...]:
    modes: tuple[Mode, Mode] = ("M", "m")
    return tuple(
        HarmonicCell(distance, initial_mode, final_mode)
        for initial_mode, final_mode, distance in product(modes, modes, range(12))
    )


def transpose_chord(chord: ChordEvent, semitones: int) -> ChordEvent:
    return ChordEvent(
        onset=chord.onset,
        duration=chord.duration,
        pitch_classes=tuple((pc + semitones) % 12 for pc in chord.pitch_classes),
        root=(chord.root + semitones) % 12,
        mode=chord.mode,
        measure=chord.measure,
        beat=chord.beat,
    )


def synthetic_triad(root: int, mode: Mode, onset: int | Fraction = 0) -> ChordEvent:
    intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
    return ChordEvent(
        onset=Fraction(onset),
        duration=Fraction(1),
        pitch_classes=tuple((root + i) % 12 for i in intervals),
        root=root % 12,
        mode=mode,
        measure=1,
        beat=Fraction(onset),
    )
