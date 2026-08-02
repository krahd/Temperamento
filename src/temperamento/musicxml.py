from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from fractions import Fraction
from pathlib import Path, PurePosixPath

from .errors import MusicXMLError
from .model import NoteEvent

_STEP_TO_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_MAX_XML_BYTES = 20 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
_MAX_ARCHIVE_ENTRIES = 256
_MAX_MEASURES = 10_000
_MAX_NOTE_EVENTS = 100_000


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if _local(child.tag) == name:
            return child
    return None


def _text(element: ET.Element, name: str, default: str | None = None) -> str | None:
    child = _child(element, name)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _integer(
    raw: str | None,
    context: str,
    *,
    minimum: int | None = None,
) -> int:
    if raw is None or not raw.strip():
        raise MusicXMLError(f"{context} requires an integer value")
    try:
        value = int(raw)
    except ValueError as exc:
        raise MusicXMLError(f"{context} must be an integer; received {raw!r}") from exc
    if minimum is not None and value < minimum:
        raise MusicXMLError(f"{context} must be at least {minimum}; received {value}")
    return value


def _parse_xml_bytes(data: bytes, context: str) -> ET.Element:
    if len(data) > _MAX_XML_BYTES:
        raise MusicXMLError(f"{context} exceeds the {_MAX_XML_BYTES}-byte safety limit")
    upper = data.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise MusicXMLError("DTD and entity declarations are not supported")
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise MusicXMLError(f"cannot parse MusicXML: {exc}") from exc


def _read_root(path: Path) -> ET.Element:
    declared_archive = path.suffix.lower() == ".mxl"
    try:
        source_size = path.stat().st_size
        is_archive = declared_archive or zipfile.is_zipfile(path)
    except OSError as exc:
        kind = "compressed MusicXML" if declared_archive else "MusicXML"
        raise MusicXMLError(f"cannot read {kind}: {exc}") from exc

    if not is_archive:
        try:
            return _parse_xml_bytes(path.read_bytes(), str(path))
        except OSError as exc:
            raise MusicXMLError(f"cannot read MusicXML: {exc}") from exc

    if source_size > _MAX_ARCHIVE_BYTES:
        raise MusicXMLError(
            f"compressed MusicXML archive exceeds the {_MAX_ARCHIVE_BYTES}-byte safety limit"
        )

    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > _MAX_ARCHIVE_ENTRIES:
                raise MusicXMLError(
                    "compressed MusicXML archive exceeds the "
                    f"{_MAX_ARCHIVE_ENTRIES}-entry safety limit"
                )
            container_entries = [
                info for info in entries if info.filename == "META-INF/container.xml"
            ]
            if len(container_entries) != 1:
                raise MusicXMLError(
                    "compressed MusicXML must contain exactly one META-INF/container.xml"
                )
            if container_entries[0].file_size > _MAX_XML_BYTES:
                raise MusicXMLError(
                    f"META-INF/container.xml exceeds the {_MAX_XML_BYTES}-byte safety limit"
                )
            container_data = archive.read(container_entries[0])
            container = _parse_xml_bytes(container_data, "META-INF/container.xml")
            if _local(container.tag) != "container":
                raise MusicXMLError("META-INF/container.xml must have a container root element")
            rootfiles_parent = _child(container, "rootfiles")
            if rootfiles_parent is None:
                raise MusicXMLError("compressed MusicXML container has no rootfiles element")
            rootfiles = [
                element
                for element in rootfiles_parent
                if _local(element.tag) == "rootfile" and element.get("full-path")
            ]
            if not rootfiles:
                raise MusicXMLError("compressed MusicXML must identify a score rootfile")

            # MusicXML 4.0 permits additional rootfiles for alternate PDF/audio
            # renditions. The first rootfile is the score entry point.
            rootfile = rootfiles[0]
            media_type = rootfile.get("media-type")
            if media_type not in {
                None,
                "application/vnd.recordare.musicxml+xml",
                "application/vnd.recordare.musicxml",
            }:
                raise MusicXMLError(
                    "the first compressed MusicXML rootfile must identify a MusicXML score"
                )
            raw_score_path = rootfile.get("full-path", "")
            if raw_score_path.endswith("/"):
                raise MusicXMLError("compressed MusicXML rootfile must be a regular file")
            score_path = PurePosixPath(raw_score_path)
            if (
                not score_path.parts
                or score_path.is_absolute()
                or ".." in score_path.parts
                or "\\" in score_path.as_posix()
            ):
                raise MusicXMLError("compressed MusicXML rootfile path is unsafe")
            matching_entries = [info for info in entries if info.filename == score_path.as_posix()]
            if not matching_entries:
                raise MusicXMLError(
                    f"compressed MusicXML rootfile {score_path.as_posix()!r} is missing"
                )
            if len(matching_entries) != 1:
                raise MusicXMLError(
                    f"compressed MusicXML rootfile {score_path.as_posix()!r} is duplicated"
                )
            info = matching_entries[0]
            if info.is_dir():
                raise MusicXMLError("compressed MusicXML rootfile must be a regular file")
            if info.file_size > _MAX_XML_BYTES:
                raise MusicXMLError(
                    f"compressed MusicXML score exceeds the {_MAX_XML_BYTES}-byte safety limit"
                )
            return _parse_xml_bytes(
                archive.read(info), f"compressed MusicXML rootfile {score_path.as_posix()}"
            )
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise MusicXMLError(f"cannot read compressed MusicXML: {exc}") from exc


def parse_musicxml(path: str | Path) -> tuple[NoteEvent, ...]:
    path = Path(path)
    root = _read_root(path)
    if _local(root.tag) != "score-partwise":
        raise MusicXMLError("only score-partwise MusicXML is supported")

    parts = [element for element in root if _local(element.tag) == "part"]
    if len(parts) != 1:
        raise MusicXMLError("the reference subset requires exactly one part")

    divisions = 1
    declared_staves: int | None = None
    absolute_measure_start = Fraction(0)
    events: list[NoteEvent] = []
    voices_seen_by_staff: dict[int, set[str]] = {}
    measures = [element for element in parts[0] if _local(element.tag) == "measure"]
    if not measures:
        raise MusicXMLError("score contains no measures")
    if len(measures) > _MAX_MEASURES:
        raise MusicXMLError(f"score exceeds the {_MAX_MEASURES}-measure safety limit")

    for measure_index, measure in enumerate(measures, start=1):
        cursor = Fraction(0)
        max_end = Fraction(0)
        chord_anchor_key: tuple[str, int] | None = None
        chord_anchor_onset: Fraction | None = None

        for element in measure:
            tag = _local(element.tag)
            if tag == "attributes":
                raw_divisions = _text(element, "divisions")
                if raw_divisions is not None:
                    divisions = _integer(
                        raw_divisions,
                        f"measure {measure_index} divisions",
                        minimum=1,
                    )
                raw_staves = _text(element, "staves")
                if raw_staves is not None:
                    staves = _integer(
                        raw_staves,
                        f"measure {measure_index} staves",
                        minimum=1,
                    )
                    if declared_staves is not None and staves != declared_staves:
                        raise MusicXMLError("the number of staves may not change")
                    declared_staves = staves
                chord_anchor_key = None
                chord_anchor_onset = None
                continue

            if tag in {"backup", "forward"}:
                duration = Fraction(
                    _integer(
                        _text(element, "duration"),
                        f"measure {measure_index} {tag} duration",
                        minimum=1,
                    ),
                    divisions,
                )
                cursor = cursor - duration if tag == "backup" else cursor + duration
                if cursor < 0:
                    raise MusicXMLError(
                        f"measure {measure_index} backup moved before the measure start"
                    )
                max_end = max(max_end, cursor)
                chord_anchor_key = None
                chord_anchor_onset = None
                continue

            if tag != "note":
                chord_anchor_key = None
                chord_anchor_onset = None
                continue

            if any(_local(descendant.tag) in {"tie", "tied"} for descendant in element.iter()):
                raise MusicXMLError("tied notes are not supported in the reference subset")
            is_chord_member = _child(element, "chord") is not None
            duration = Fraction(
                _integer(
                    _text(element, "duration"),
                    f"measure {measure_index} note duration",
                    minimum=1,
                ),
                divisions,
            )
            voice = _text(element, "voice", "1") or "1"
            staff = _integer(
                _text(element, "staff", "1"),
                f"measure {measure_index} note staff",
                minimum=1,
            )
            if staff not in {1, 2}:
                raise MusicXMLError(
                    "the reference subset permits note and rest material only on staves 1 and 2"
                )
            voices_seen_by_staff.setdefault(staff, set()).add(voice)
            key = (voice, staff)

            if _child(element, "rest") is not None:
                if is_chord_member:
                    raise MusicXMLError("rests cannot be chord members in the reference subset")
                cursor += duration
                max_end = max(max_end, cursor)
                chord_anchor_key = None
                chord_anchor_onset = None
                continue

            pitch = _child(element, "pitch")
            if pitch is None:
                raise MusicXMLError("unpitched notes are not supported")
            step = _text(pitch, "step")
            octave_raw = _text(pitch, "octave")
            if step is None or step not in _STEP_TO_PC or octave_raw is None:
                raise MusicXMLError("pitch requires a valid step and octave")
            alter = _integer(_text(pitch, "alter", "0"), "pitch alter")
            octave = _integer(octave_raw, "pitch octave")
            pitch_class = (_STEP_TO_PC[step] + alter) % 12

            if is_chord_member:
                if chord_anchor_key != key or chord_anchor_onset is None:
                    raise MusicXMLError(
                        "chord member must immediately follow its anchor note "
                        "in the same voice/staff"
                    )
                onset = chord_anchor_onset
            else:
                onset = cursor
                cursor += duration
                chord_anchor_key = key
                chord_anchor_onset = onset

            max_end = max(max_end, onset + duration, cursor)
            if len(events) >= _MAX_NOTE_EVENTS:
                raise MusicXMLError(f"score exceeds the {_MAX_NOTE_EVENTS}-note-event safety limit")
            events.append(
                NoteEvent(
                    onset=absolute_measure_start + onset,
                    duration=duration,
                    pitch_class=pitch_class,
                    octave=octave,
                    staff=staff,
                    voice=voice,
                    chord_member=is_chord_member,
                    measure=measure_index,
                    beat=onset + 1,
                )
            )

        if max_end <= 0:
            raise MusicXMLError(
                f"measure {measure_index} has no explicit temporal extent in the reference subset"
            )
        absolute_measure_start += max_end

    if not events:
        raise MusicXMLError("score contains no pitched notes")

    if declared_staves != 2:
        raise MusicXMLError(
            "the reference subset requires MusicXML attributes declaring exactly two staves"
        )
    staffs = {event.staff for event in events}
    if not staffs.issubset({1, 2}) or 2 not in staffs:
        raise MusicXMLError(
            "the reference subset permits pitched material only on staves 1 and 2 "
            "and requires a non-empty Base staff"
        )
    ambiguous = {
        staff: sorted(voices) for staff, voices in voices_seen_by_staff.items() if len(voices) > 1
    }
    if ambiguous:
        details = ", ".join(f"staff {staff}: {voices}" for staff, voices in ambiguous.items())
        raise MusicXMLError(
            "the reference subset permits one MusicXML voice per staff; received " + details
        )

    return tuple(
        sorted(
            events,
            key=lambda event: (
                event.onset,
                event.staff,
                event.voice,
                event.chord_member,
                event.pitch_class,
                event.octave,
            ),
        )
    )
