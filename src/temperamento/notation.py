from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import IntegrationError, StaticError
from .harmony import root_after_distance
from .model import Instruction, Mode, Program
from .validation import validate_program

_PC_SPELLING: dict[int, tuple[str, int]] = {
    0: ("C", 0),
    1: ("C", 1),
    2: ("D", 0),
    3: ("D", 1),
    4: ("E", 0),
    5: ("F", 0),
    6: ("F", 1),
    7: ("G", 0),
    8: ("G", 1),
    9: ("A", 0),
    10: ("A", 1),
    11: ("B", 0),
}
_MAX_TITLE_CHARACTERS = 4096


def digits_base12(value: int) -> tuple[int, ...]:
    if isinstance(value, bool) or value < 0:
        raise StaticError("notation operands must be non-negative integers")
    if value == 0:
        return (0,)
    digits: list[int] = []
    while value:
        digits.append(value % 12)
        value //= 12
    return tuple(reversed(digits))


def _validate_title(title: str) -> None:
    if len(title) > _MAX_TITLE_CHARACTERS:
        raise StaticError(f"score title exceeds {_MAX_TITLE_CHARACTERS} characters")
    for character in title:
        codepoint = ord(character)
        if (
            codepoint < 0x20 and character not in {"\t", "\n", "\r"}
        ) or 0xD800 <= codepoint <= 0xDFFF:
            raise StaticError("score title contains a character that is not valid in XML 1.0")


def _pitch(note: ET.Element, pitch_class: int, octave: int) -> None:
    pitch = ET.SubElement(note, "pitch")
    step, alter = _PC_SPELLING[pitch_class % 12]
    ET.SubElement(pitch, "step").text = step
    if alter:
        ET.SubElement(pitch, "alter").text = str(alter)
    ET.SubElement(pitch, "octave").text = str(octave)


def _note(
    measure: ET.Element,
    pitch_class: int,
    duration: int,
    staff: int,
    *,
    chord: bool = False,
    octave: int = 4,
    voice: str,
) -> None:
    note = ET.SubElement(measure, "note")
    if chord:
        ET.SubElement(note, "chord")
    _pitch(note, pitch_class, octave)
    ET.SubElement(note, "duration").text = str(duration * 4)
    ET.SubElement(note, "voice").text = voice
    ET.SubElement(note, "staff").text = str(staff)


def _forward(measure: ET.Element, duration: int) -> None:
    if duration <= 0:
        return
    forward = ET.SubElement(measure, "forward")
    ET.SubElement(forward, "duration").text = str(duration * 4)


def _backup(measure: ET.Element, duration: int) -> None:
    backup = ET.SubElement(measure, "backup")
    ET.SubElement(backup, "duration").text = str(duration * 4)


def _triad(root: int, mode: Mode) -> tuple[int, int, int]:
    intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
    return (
        (root + intervals[0]) % 12,
        (root + intervals[1]) % 12,
        (root + intervals[2]) % 12,
    )


def _write_triad(
    measure: ET.Element,
    root: int,
    mode: Mode,
    *,
    reverse_voicing: bool,
    double_root: bool,
) -> None:
    pitches = list(_triad(root, mode))
    if reverse_voicing:
        pitches.reverse()
    _note(measure, pitches[0], 1, 2, octave=3, voice="2")
    for pitch_class in pitches[1:]:
        _note(measure, pitch_class, 1, 2, chord=True, octave=4, voice="2")
    if double_root:
        _note(measure, root, 1, 2, chord=True, octave=5, voice="2")


def _voice_duration(instruction: Instruction) -> int:
    return sum(2 * len(digits_base12(operand)) for operand in instruction.operands)


def _attributes(measure: ET.Element, beats: int, *, first: bool) -> None:
    attributes = ET.SubElement(measure, "attributes")
    ET.SubElement(attributes, "divisions").text = "4"
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = str(beats)
    ET.SubElement(time, "beat-type").text = "4"
    if first:
        ET.SubElement(attributes, "staves").text = "2"
        clef_voice = ET.SubElement(attributes, "clef", number="1")
        ET.SubElement(clef_voice, "sign").text = "G"
        ET.SubElement(clef_voice, "line").text = "2"
        clef_base = ET.SubElement(attributes, "clef", number="2")
        ET.SubElement(clef_base, "sign").text = "F"
        ET.SubElement(clef_base, "line").text = "4"


def _instruction_label(measure: ET.Element, instruction: Instruction) -> None:
    direction = ET.SubElement(measure, "direction", placement="above")
    direction_type = ET.SubElement(direction, "direction-type")
    words = ET.SubElement(direction_type, "words")
    words.text = instruction.to_tos()
    ET.SubElement(direction, "staff").text = "1"


def program_to_musicxml(
    program: Program,
    *,
    title: str = "Temperamento program",
    transpose: int = 0,
    reverse_voicing: bool = False,
    double_roots: bool = False,
    decorative_base_line: bool = False,
) -> ET.ElementTree:
    if not program.instructions:
        raise StaticError("cannot notate an empty program")
    validate_program(program, verify_harmonic_cells=True)
    _validate_title(title)

    score = ET.Element("score-partwise", version="4.0")
    work = ET.SubElement(score, "work")
    ET.SubElement(work, "work-title").text = title
    identification = ET.SubElement(score, "identification")
    encoding = ET.SubElement(identification, "encoding")
    ET.SubElement(encoding, "software").text = "Temperamento"
    part_list = ET.SubElement(score, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    ET.SubElement(score_part, "part-name").text = "Temperamento"
    part = ET.SubElement(score, "part", id="P1")

    initial_root = transpose % 12
    for index, instruction in enumerate(program.instructions):
        voice_duration = _voice_duration(instruction)
        final_onset = voice_duration + 2
        measure_duration = final_onset + (2 if decorative_base_line else 1)
        measure = ET.SubElement(part, "measure", number=str(index + 1))
        _attributes(measure, measure_duration, first=index == 0)
        _instruction_label(measure, instruction)

        _forward(measure, 1)
        for operand in instruction.operands:
            digits = digits_base12(operand)
            _note(
                measure,
                (initial_root + 11) % 12,
                len(digits),
                1,
                octave=5,
                voice="1",
            )
            for digit in digits:
                _note(
                    measure,
                    (initial_root + digit) % 12,
                    1,
                    1,
                    octave=5,
                    voice="1",
                )
        remaining_voice = measure_duration - 1 - voice_duration
        _forward(measure, remaining_voice)

        _backup(measure, measure_duration)
        final_root = root_after_distance(initial_root, instruction.cell.distance)
        _write_triad(
            measure,
            initial_root,
            instruction.cell.initial_mode,
            reverse_voicing=reverse_voicing,
            double_root=double_roots,
        )
        _forward(measure, final_onset - 1)
        _write_triad(
            measure,
            final_root,
            instruction.cell.final_mode,
            reverse_voicing=reverse_voicing,
            double_root=double_roots,
        )
        if decorative_base_line:
            _note(
                measure,
                (final_root + 2 + 2 * index) % 12,
                1,
                2,
                octave=4 + index % 2,
                voice="2",
            )
        initial_root = final_root

    ET.indent(score, space="  ")
    return ET.ElementTree(score)


def write_musicxml(
    program: Program,
    destination: str | Path,
    *,
    title: str = "Temperamento program",
    transpose: int = 0,
    reverse_voicing: bool = False,
    double_roots: bool = False,
    decorative_base_line: bool = False,
) -> Path:
    path = Path(destination)
    tree = program_to_musicxml(
        program,
        title=title,
        transpose=transpose,
        reverse_voicing=reverse_voicing,
        double_roots=double_roots,
        decorative_base_line=decorative_base_line,
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(path, encoding="utf-8", xml_declaration=True)
    except OSError as exc:
        raise IntegrationError(f"cannot write MusicXML: {exc}") from exc
    return path
