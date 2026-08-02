from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from .errors import HarmonyError, StaticError
from .harmony import decode_pair, recognise_triad
from .model import ChordEvent, IgnoredBaseEvent, Instruction, NoteEvent, Program
from .musescore import musicxml_source
from .musicxml import parse_musicxml
from .opcodes import OpcodeSpec, lookup

VOICE_STAFF = 1
BASE_STAFF = 2


def _time(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _base_chords(
    events: tuple[NoteEvent, ...],
) -> tuple[list[ChordEvent], tuple[IgnoredBaseEvent, ...]]:
    grouped: dict[Fraction, list[NoteEvent]] = defaultdict(list)
    for event in events:
        if event.staff == BASE_STAFF:
            grouped[event.onset].append(event)

    chords: list[ChordEvent] = []
    ignored: list[IgnoredBaseEvent] = []
    for onset in sorted(grouped):
        notes = grouped[onset]
        try:
            chords.append(recognise_triad(notes))
        except HarmonyError:
            ignored.append(
                IgnoredBaseEvent(
                    onset=onset,
                    pitch_classes=tuple(sorted({note.pitch_class % 12 for note in notes})),
                    note_count=len(notes),
                    reason="not an exact major or minor triad",
                    measure=notes[0].measure,
                    beat=notes[0].beat,
                )
            )

    if not chords:
        raise StaticError("Base staff contains no recognised computational triads")
    if len(chords) % 2:
        raise StaticError("Base staff contains an odd number of recognised computational triads")
    return chords, tuple(ignored)


def _voice_notes(
    events: tuple[NoteEvent, ...],
    start: Fraction,
    end: Fraction,
) -> list[NoteEvent]:
    selected = [
        event for event in events if event.staff == VOICE_STAFF and start < event.onset < end
    ]
    onset_counts: dict[Fraction, int] = defaultdict(int)
    for event in selected:
        onset_counts[event.onset] += 1

    # Simultaneous Voice notes are musically available but computationally ignored.
    computational = sorted(
        [event for event in selected if onset_counts[event.onset] == 1],
        key=lambda event: (event.onset, event.pitch_class, event.octave),
    )
    previous: NoteEvent | None = None
    for event in computational:
        if event.onset + event.duration > end:
            raise StaticError("computational Voice note crosses the end of its command window")
        if previous is not None and event.onset < previous.onset + previous.duration:
            raise StaticError("computational Voice notes must not overlap within a command window")
        previous = event
    return computational


def _decode_base12(payload: list[NoteEvent], reference_pitch_class: int) -> int:
    value = 0
    for note in payload:
        digit = (note.pitch_class - reference_pitch_class) % 12
        value = value * 12 + digit
    return value


def _parse_operands(
    notes: list[NoteEvent],
    spec: OpcodeSpec,
    reference_pitch_class: int,
) -> tuple[int, ...]:
    operands: list[int] = []
    cursor = 0
    for kind in spec.operands:
        if cursor >= len(notes):
            raise StaticError(f"{spec.name} expects {len(spec.operands)} operand(s)")
        header = notes[cursor]
        length_fraction = header.duration
        if length_fraction.denominator != 1:
            raise StaticError(
                f"{spec.name} {kind} header duration must be an integer number "
                "of quarter-note units"
            )
        length = int(length_fraction)
        if length <= 0:  # defensive: MusicXML already rejects non-positive notes
            raise StaticError("operand length must be positive")
        cursor += 1
        payload = notes[cursor : cursor + length]
        if len(payload) != length:
            raise StaticError(
                f"truncated {kind} operand for {spec.name}: expected {length} payload notes"
            )
        operands.append(_decode_base12(payload, reference_pitch_class))
        cursor += length

    if cursor != len(notes):
        raise StaticError(f"surplus Voice material in {spec.name} command window")
    return tuple(operands)


def _validate_control_flow(program: Program) -> None:
    labels: dict[int, int] = {}
    targets: set[int] = set()

    for index, instruction in enumerate(program.instructions):
        if instruction.opcode == "LBL":
            label = instruction.operands[0]
            if label in labels:
                raise StaticError(
                    f"duplicate label {label} at instructions {labels[label]} and {index}"
                )
            labels[label] = index
        elif instruction.opcode in {"JMC", "JMP"}:
            targets.add(instruction.operands[0])

    undefined = sorted(targets - labels.keys())
    if undefined:
        raise StaticError(f"undefined label(s): {', '.join(map(str, undefined))}")


def compile_events(events: tuple[NoteEvent, ...], source: str | None = None) -> Program:
    chords, ignored_base_events = _base_chords(events)
    instructions: list[Instruction] = []

    for index in range(0, len(chords), 2):
        initial, final = chords[index], chords[index + 1]
        if final.onset <= initial.onset:
            raise StaticError("Base chord pairs must advance in score time")
        command_number = index // 2 + 1
        try:
            cell = decode_pair(initial, final)
            spec = lookup(cell)
            if spec is None:
                raise StaticError(f"harmonic cell {cell.token} is reserved")
            voice_notes = _voice_notes(events, initial.onset, final.onset)
            operands = _parse_operands(voice_notes, spec, initial.root)
        except StaticError as exc:
            raise StaticError(
                f"command {command_number} at measure {initial.measure}, "
                f"beat {_time(initial.beat)} (score time {_time(initial.onset)}): {exc}"
            ) from exc
        instructions.append(
            Instruction(
                spec.name,
                operands,
                cell,
                initial.onset,
                measure=initial.measure,
                beat=initial.beat,
                initial_root=initial.root,
                final_root=final.root,
                voice_onsets=tuple(note.onset for note in voice_notes),
            )
        )

    program = Program(tuple(instructions), source, ignored_base_events)
    _validate_control_flow(program)
    return program


def compile_musicxml(path: str | Path) -> Program:
    source = Path(path)
    return compile_events(parse_musicxml(source), str(source))


def compile_score(
    path: str | Path,
    *,
    musescore: str | Path | None = None,
) -> Program:
    """Compile MusicXML directly or convert a native MuseScore score first."""
    source = Path(path)
    with musicxml_source(source, executable=musescore) as resolved:
        program = compile_events(parse_musicxml(resolved), str(source))
    return program
