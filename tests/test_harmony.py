from fractions import Fraction

import pytest

from temperamento.errors import HarmonyError
from temperamento.harmony import (
    all_cells,
    decode_pair,
    fifths_distance,
    fifths_position,
    recognise_triad,
    root_after_distance,
    synthetic_triad,
    transpose_chord,
)
from temperamento.model import ChordEvent, NoteEvent

_ROOTS_BY_FIFTH_DISTANCE = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)


def chord(root: int, mode: str, onset: int = 0) -> ChordEvent:
    intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
    return ChordEvent(
        Fraction(onset),
        Fraction(1),
        tuple((root + interval) % 12 for interval in intervals),
        root,
        mode,
    )


def note(
    pitch_class: int,
    octave: int = 4,
    chord_member: bool = False,
    onset: int = 0,
) -> NoteEvent:
    return NoteEvent(
        Fraction(onset),
        Fraction(1),
        pitch_class,
        octave,
        2,
        "2",
        chord_member,
    )


def test_topology_contains_exactly_48_unique_cells() -> None:
    cells = all_cells()
    assert len(cells) == 48
    assert len({cell.token for cell in cells}) == 48


@pytest.mark.parametrize("distance", range(12))
@pytest.mark.parametrize("initial_mode", ["M", "m"])
@pytest.mark.parametrize("final_mode", ["M", "m"])
def test_every_harmonic_cell_decodes(
    distance: int,
    initial_mode: str,
    final_mode: str,
) -> None:
    initial = chord(0, initial_mode)
    final = chord(_ROOTS_BY_FIFTH_DISTANCE[distance], final_mode, onset=1)
    assert decode_pair(initial, final).token == f"{distance}{initial_mode}{final_mode}"


@pytest.mark.parametrize("distance", range(12))
@pytest.mark.parametrize("initial_mode", ["M", "m"])
@pytest.mark.parametrize("final_mode", ["M", "m"])
@pytest.mark.parametrize("transpose", range(12))
def test_global_transposition_preserves_cell(
    distance: int,
    initial_mode: str,
    final_mode: str,
    transpose: int,
) -> None:
    initial = chord(0, initial_mode)
    final = chord(_ROOTS_BY_FIFTH_DISTANCE[distance], final_mode, onset=1)
    original = decode_pair(initial, final)
    transformed = decode_pair(
        transpose_chord(initial, transpose),
        transpose_chord(final, transpose),
    )
    assert transformed == original


def test_triad_recognition_is_inversion_order_and_doubling_invariant() -> None:
    recognised = recognise_triad([note(7), note(0, 5, True), note(4, 3, True), note(0, 3, True)])
    assert recognised.root == 0
    assert recognised.mode == "M"


@pytest.mark.parametrize("distance", range(12))
@pytest.mark.parametrize("initial_mode", ["M", "m"])
@pytest.mark.parametrize("final_mode", ["M", "m"])
@pytest.mark.parametrize("transpose", range(12))
def test_recognition_with_voicing_transformations_preserves_cell(
    distance: int,
    initial_mode: str,
    final_mode: str,
    transpose: int,
) -> None:
    def recognised(root: int, mode: str, onset: int) -> ChordEvent:
        intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
        pitch_classes = [(root + interval + transpose) % 12 for interval in intervals]
        pitch_classes = [pitch_classes[2], pitch_classes[0], pitch_classes[1], pitch_classes[0]]
        notes = [
            note(
                pitch_class,
                octave=3 + (index % 2),
                chord_member=index > 0,
                onset=onset,
            )
            for index, pitch_class in enumerate(pitch_classes)
        ]
        return recognise_triad(notes)

    initial = recognised(0, initial_mode, 0)
    final = recognised(_ROOTS_BY_FIFTH_DISTANCE[distance], final_mode, 1)
    assert decode_pair(initial, final).token == f"{distance}{initial_mode}{final_mode}"


def test_triad_recognition_rejects_non_events_and_noncomputational_sets() -> None:
    with pytest.raises(HarmonyError, match="empty chord"):
        recognise_triad([])
    with pytest.raises(HarmonyError, match="share an onset"):
        recognise_triad([note(0, onset=0), note(4, onset=1), note(7, onset=0)])
    with pytest.raises(HarmonyError, match="not an exact major or minor triad"):
        recognise_triad([note(0), note(7, chord_member=True)])
    with pytest.raises(HarmonyError, match="not an exact major or minor triad"):
        recognise_triad([note(0), note(5, chord_member=True), note(7, chord_member=True)])


def test_fifths_helpers_and_synthetic_triads() -> None:
    assert [fifths_position(root) for root in _ROOTS_BY_FIFTH_DISTANCE] == list(range(12))
    for distance, root in enumerate(_ROOTS_BY_FIFTH_DISTANCE):
        assert root_after_distance(0, distance) == root
        assert fifths_distance(0, root) == distance
    assert synthetic_triad(13, "m", Fraction(3, 2)).root == 1
    assert synthetic_triad(13, "m", Fraction(3, 2)).pitch_classes == (1, 4, 8)
