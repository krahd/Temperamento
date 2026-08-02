from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temperamento.opcodes import assigned_opcodes

# Independent test/example oracle: roots reached from C by 0..11 clockwise fifths.
_ROOTS_BY_FIFTH_DISTANCE = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)
PC_SPELLING = {
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


@dataclass(frozen=True)
class SourceInstruction:
    cell: str
    operands: tuple[int, ...] = ()


def digits_base12(value: int) -> list[int]:
    if isinstance(value, bool) or value < 0:
        raise ValueError("examples use non-negative integer operands")
    if value == 0:
        return [0]
    digits: list[int] = []
    while value:
        digits.append(value % 12)
        value //= 12
    return list(reversed(digits))


def add_pitch(note: ET.Element, pitch_class: int, octave: int) -> None:
    pitch = ET.SubElement(note, "pitch")
    step, alter = PC_SPELLING[pitch_class % 12]
    ET.SubElement(pitch, "step").text = step
    if alter:
        ET.SubElement(pitch, "alter").text = str(alter)
    ET.SubElement(pitch, "octave").text = str(octave)


def add_note(
    measure: ET.Element,
    pitch_class: int,
    cursor: int,
    duration: int,
    staff: int,
    *,
    chord: bool = False,
    octave: int = 4,
    voice: str = "1",
) -> int:
    note = ET.SubElement(measure, "note")
    if chord:
        ET.SubElement(note, "chord")
    add_pitch(note, pitch_class, octave)
    ET.SubElement(note, "duration").text = str(duration * 4)
    ET.SubElement(note, "voice").text = voice
    ET.SubElement(note, "staff").text = str(staff)
    return cursor if chord else cursor + duration


def add_forward(measure: ET.Element, duration: int) -> None:
    if duration <= 0:
        return
    forward = ET.SubElement(measure, "forward")
    ET.SubElement(forward, "duration").text = str(duration * 4)


def add_backup(measure: ET.Element, duration: int) -> None:
    backup = ET.SubElement(measure, "backup")
    ET.SubElement(backup, "duration").text = str(duration * 4)


def triad(root: int, mode: str) -> tuple[int, int, int]:
    intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
    return tuple((root + interval) % 12 for interval in intervals)


def _root_pairs(instructions: list[SourceInstruction], transpose: int) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    initial_root = transpose % 12
    for instruction in instructions:
        distance = int(instruction.cell[:-2])
        final_root = (initial_root + _ROOTS_BY_FIFTH_DISTANCE[distance]) % 12
        pairs.append((initial_root, final_root))
        initial_root = final_root
    return pairs


def build_score(
    instructions: list[SourceInstruction],
    *,
    transpose: int = 0,
    reverse_voicing: bool = False,
    double_roots: bool = False,
    title: str = "Temperamento example",
    decorative_base_line: bool = False,
) -> ET.ElementTree:
    score = ET.Element("score-partwise", version="4.0")
    work = ET.SubElement(score, "work")
    ET.SubElement(work, "work-title").text = title
    part_list = ET.SubElement(score, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    ET.SubElement(score_part, "part-name").text = "Temperamento"
    part = ET.SubElement(score, "part", id="P1")
    measure = ET.SubElement(part, "measure", number="1")
    attributes = ET.SubElement(measure, "attributes")
    ET.SubElement(attributes, "divisions").text = "4"
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = "256"
    ET.SubElement(time, "beat-type").text = "4"
    ET.SubElement(attributes, "staves").text = "2"

    window = 16
    gap = 2
    starts = [index * (window + gap) for index in range(len(instructions))]
    total = starts[-1] + window + 2 if starts else 2
    root_pairs = _root_pairs(instructions, transpose)

    # Voice staff: duration-prefixed base-12 operands. Payload pitch classes are
    # measured relative to the first Base chord root, so whole-score transposition
    # preserves operand values as well as opcodes.
    cursor = 0
    opcode_specs = assigned_opcodes()
    for start, source_instruction, (initial_root, _) in zip(
        starts, instructions, root_pairs, strict=True
    ):
        spec = opcode_specs[source_instruction.cell]
        if len(spec.operands) != len(source_instruction.operands):
            raise ValueError(f"{spec.name} expects {len(spec.operands)} operands")
        target = start + 1
        if target > cursor:
            add_forward(measure, target - cursor)
            cursor = target
        for operand in source_instruction.operands:
            digits = digits_base12(operand)
            cursor = add_note(
                measure,
                (initial_root + 11) % 12,
                cursor,
                len(digits),
                1,
                octave=5,
                voice="1",
            )
            for digit in digits:
                cursor = add_note(
                    measure,
                    (initial_root + digit) % 12,
                    cursor,
                    1,
                    1,
                    octave=5,
                    voice="1",
                )
    if cursor < total:
        add_forward(measure, total - cursor)

    add_backup(measure, total)
    cursor = 0

    # Base staff: ordered, non-overlapping triad pairs.
    for command_index, (start, source_instruction, (initial_root, final_root)) in enumerate(
        zip(starts, instructions, root_pairs, strict=True)
    ):
        initial_mode, final_mode = source_instruction.cell[-2:]
        for onset, root, mode in (
            (start, initial_root, initial_mode),
            (start + window, final_root, final_mode),
        ):
            if onset > cursor:
                add_forward(measure, onset - cursor)
                cursor = onset
            pitch_classes = list(triad(root, mode))
            if reverse_voicing:
                pitch_classes.reverse()
            cursor = add_note(
                measure,
                pitch_classes[0],
                cursor,
                1,
                2,
                octave=3,
                voice="2",
            )
            for pitch_class in pitch_classes[1:]:
                add_note(
                    measure,
                    pitch_class,
                    cursor - 1,
                    1,
                    2,
                    chord=True,
                    octave=4,
                    voice="2",
                )
            if double_roots:
                add_note(
                    measure,
                    root,
                    cursor - 1,
                    1,
                    2,
                    chord=True,
                    octave=5,
                    voice="2",
                )
        if decorative_base_line:
            ornament_onset = start + window + 1
            if ornament_onset > cursor:
                add_forward(measure, ornament_onset - cursor)
                cursor = ornament_onset
            cursor = add_note(
                measure,
                (final_root + 2 + command_index * 2) % 12,
                cursor,
                1,
                2,
                octave=4 + (command_index % 2),
                voice="2",
            )
    if cursor < total:
        add_forward(measure, total - cursor)

    ET.indent(score, space="  ")
    return ET.ElementTree(score)


def write_example(
    relative: str,
    instructions: list[SourceInstruction],
    expected_tos: str,
    *,
    transpose_variant: bool = False,
) -> None:
    directory = ROOT / "examples" / relative
    directory.mkdir(parents=True, exist_ok=True)
    name = directory.name
    build_score(instructions, title=f"Temperamento: {name}").write(
        directory / f"{name}.musicxml",
        encoding="utf-8",
        xml_declaration=True,
    )
    (directory / f"{name}.tos").write_text(expected_tos, encoding="utf-8")
    if transpose_variant:
        variant = ROOT / "examples" / "equivalent-scores" / f"{name}-transposed.musicxml"
        variant.parent.mkdir(parents=True, exist_ok=True)
        build_score(
            instructions,
            transpose=5,
            reverse_voicing=True,
            double_roots=True,
            title=f"Temperamento: {name}, globally transposed",
        ).write(variant, encoding="utf-8", xml_declaration=True)


def main() -> None:
    write_example(
        "arithmetic/add",
        [
            SourceInstruction("5MM", (7,)),
            SourceInstruction("5MM", (5,)),
            SourceInstruction("0MM"),
            SourceInstruction("8mm"),
            SourceInstruction("4mm"),
        ],
        "PUSH 7\nPUSH 5\nADD\nOUT\nEND\n",
        transpose_variant=True,
    )
    write_example(
        "conditional/equal",
        [
            SourceInstruction("5MM", (3,)),
            SourceInstruction("5MM", (3,)),
            SourceInstruction("10MM"),
            SourceInstruction("0mm", (1,)),
            SourceInstruction("5MM", (0,)),
            SourceInstruction("8mm"),
            SourceInstruction("1mm", (2,)),
            SourceInstruction("11MM", (1,)),
            SourceInstruction("5MM", (1,)),
            SourceInstruction("8mm"),
            SourceInstruction("11MM", (2,)),
            SourceInstruction("4mm"),
        ],
        "PUSH 3\nPUSH 3\nEQ\nJMC 1\nPUSH 0\nOUT\nJMP 2\nLBL 1\nPUSH 1\nOUT\nLBL 2\nEND\n",
    )
    write_example(
        "iteration/countdown",
        [
            SourceInstruction("5MM", (3,)),
            SourceInstruction("11MM", (1,)),
            SourceInstruction("7MM"),
            SourceInstruction("8mm"),
            SourceInstruction("5MM", (1,)),
            SourceInstruction("1MM"),
            SourceInstruction("7MM"),
            SourceInstruction("0mm", (1,)),
            SourceInstruction("6MM"),
            SourceInstruction("4mm"),
        ],
        "PUSH 3\nLBL 1\nDUP\nOUT\nPUSH 1\nSUB\nDUP\nJMC 1\nPOP\nEND\n",
        transpose_variant=True,
    )


if __name__ == "__main__":
    main()
