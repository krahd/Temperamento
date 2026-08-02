from fractions import Fraction

import pytest

from temperamento.compiler import compile_events
from temperamento.errors import StaticError
from temperamento.model import NoteEvent

_ROOTS_BY_FIFTH_DISTANCE = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)


def triad_events(root: int, mode: str, onset: int) -> list[NoteEvent]:
    intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
    return [
        NoteEvent(
            Fraction(onset),
            Fraction(1),
            (root + interval) % 12,
            3 + index,
            2,
            "2",
            index > 0,
        )
        for index, interval in enumerate(intervals)
    ]


def base_sonority(pitch_classes: tuple[int, ...], onset: int | Fraction) -> list[NoteEvent]:
    return [
        NoteEvent(
            Fraction(onset),
            Fraction(1),
            pitch_class,
            4,
            2,
            "2",
            index > 0,
        )
        for index, pitch_class in enumerate(pitch_classes)
    ]


def pair_events(cell: str, start: int = 0, end: int = 8) -> list[NoteEvent]:
    distance = int(cell[:-2])
    initial_mode, final_mode = cell[-2:]
    return triad_events(0, initial_mode, start) + triad_events(
        _ROOTS_BY_FIFTH_DISTANCE[distance], final_mode, end
    )


def voice_note(
    onset: int | Fraction,
    pitch_class: int,
    duration: int | Fraction = 1,
) -> NoteEvent:
    return NoteEvent(
        Fraction(onset),
        Fraction(duration),
        pitch_class,
        5,
        1,
        "1",
    )


def test_odd_number_of_base_chords_is_rejected() -> None:
    with pytest.raises(StaticError, match="odd number"):
        compile_events(tuple(triad_events(0, "M", 0)))


def test_reserved_harmonic_cell_is_rejected() -> None:
    with pytest.raises(StaticError, match="reserved"):
        compile_events(tuple(pair_events("5mm")))


def test_surplus_voice_material_is_rejected() -> None:
    events = pair_events("0MM")
    events.append(voice_note(2, 0))
    with pytest.raises(StaticError, match="surplus"):
        compile_events(tuple(events))


def test_missing_operand_is_rejected() -> None:
    with pytest.raises(StaticError, match="expects 1 operand"):
        compile_events(tuple(pair_events("5MM")))


def test_truncated_operand_is_rejected() -> None:
    events = pair_events("5MM")
    events.extend([voice_note(1, 11, duration=2), voice_note(3, 0)])
    with pytest.raises(StaticError, match="truncated"):
        compile_events(tuple(events))


def test_fractional_header_duration_is_rejected() -> None:
    events = pair_events("5MM")
    events.extend([voice_note(1, 11, duration=Fraction(1, 2)), voice_note(2, 0)])
    with pytest.raises(StaticError, match="integer number"):
        compile_events(tuple(events))


def test_duplicate_labels_are_static_errors() -> None:
    events = pair_events("11MM", 0, 8) + pair_events("11MM", 10, 18)
    events.extend(
        [
            voice_note(1, 11),
            voice_note(2, 1),
            voice_note(11, 11),
            voice_note(12, 1),
        ]
    )
    with pytest.raises(StaticError, match="duplicate label 1"):
        compile_events(tuple(events))


def test_undefined_jump_target_is_static_error() -> None:
    events = pair_events("1mm")
    events.extend([voice_note(1, 11), voice_note(2, 3)])
    with pytest.raises(StaticError, match="undefined label"):
        compile_events(tuple(events))


def test_base_requires_recognised_computational_triads() -> None:
    with pytest.raises(StaticError, match="no recognised computational triads"):
        compile_events((voice_note(0, 0),))
    with pytest.raises(StaticError, match="no recognised computational triads"):
        compile_events(tuple(base_sonority((0, 5, 7), 0)))


def test_noncomputational_base_sonorities_are_ignored_before_pairing() -> None:
    events = pair_events("0MM")
    events.extend(base_sonority((0, 7), 2))
    events.extend(base_sonority((0, 5, 7), 4))  # Csus4 / Fsus2/C
    events.extend(base_sonority((0, 4, 7, 11), 6))

    program = compile_events(tuple(events))

    assert program.to_tos() == "ADD\n"
    assert [event.pitch_classes for event in program.ignored_base_events] == [
        (0, 7),
        (0, 5, 7),
        (0, 4, 7, 11),
    ]
    assert all(
        event.reason == "not an exact major or minor triad" for event in program.ignored_base_events
    )


def test_ignored_material_does_not_repair_odd_computational_chord_count() -> None:
    events = triad_events(0, "M", 0) + base_sonority((0, 5, 7), 4)
    with pytest.raises(StaticError, match="odd number of recognised computational triads"):
        compile_events(tuple(events))


def test_zero_length_header_is_rejected_defensively() -> None:
    events = pair_events("5MM")
    events.append(voice_note(1, 0, duration=0))
    with pytest.raises(StaticError, match="length must be positive"):
        compile_events(tuple(events))


def test_simultaneous_voice_notes_are_ignored() -> None:
    events = pair_events("0MM")
    events.extend([voice_note(2, 0), voice_note(2, 7)])
    assert compile_events(tuple(events)).to_tos() == "ADD\n"


def test_overlapping_computational_voice_notes_are_rejected() -> None:
    events = pair_events("5MM")
    events.extend(
        [
            voice_note(1, 11, duration=2),
            voice_note(2, 7),
        ]
    )
    with pytest.raises(StaticError, match="must not overlap"):
        compile_events(tuple(events))


def test_computational_voice_note_may_not_cross_command_boundary() -> None:
    events = pair_events("5MM", start=0, end=4)
    events.extend(
        [
            voice_note(1, 11),
            voice_note(3, 7, duration=2),
        ]
    )
    with pytest.raises(StaticError, match="crosses the end"):
        compile_events(tuple(events))


def test_isolated_base_note_is_ignored_as_noncomputational_material() -> None:
    events = pair_events("0MM")
    events.append(NoteEvent(Fraction(4), Fraction(1), 11, 5, 2, "2"))
    program = compile_events(tuple(events))
    assert program.to_tos() == "ADD\n"
    assert len(program.ignored_base_events) == 1
    assert program.ignored_base_events[0].pitch_classes == (11,)
