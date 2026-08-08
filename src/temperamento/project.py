from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import cast

from .errors import IntegrationError
from .musescore import export_score, require_musescore

_PC = {
    0: ("C", 0),
    1: ("C", 1),
    2: ("D", 0),
    3: ("E", -1),
    4: ("E", 0),
    5: ("F", 0),
    6: ("F", 1),
    7: ("G", 0),
    8: ("A", -1),
    9: ("A", 0),
    10: ("B", -1),
    11: ("B", 0),
}
_MAX_PROJECT_TITLE_CHARS = 4096


def _validate_project_title(title: str) -> None:
    if len(title) > _MAX_PROJECT_TITLE_CHARS:
        raise IntegrationError(
            f"project title exceeds the {_MAX_PROJECT_TITLE_CHARS}-character safety limit"
        )
    for character in title:
        codepoint = ord(character)
        if not (
            codepoint in {0x09, 0x0A, 0x0D}
            or 0x20 <= codepoint <= 0xD7FF
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        ):
            raise IntegrationError("project title contains text not valid in XML 1.0")


def _pitch(note: ET.Element, pc: int, octave: int) -> None:
    pitch = ET.SubElement(note, "pitch")
    step, alter = _PC[pc % 12]
    ET.SubElement(pitch, "step").text = step
    if alter:
        ET.SubElement(pitch, "alter").text = str(alter)
    ET.SubElement(pitch, "octave").text = str(octave)


def _note(
    measure: ET.Element,
    pc: int,
    duration: int,
    staff: int,
    *,
    chord: bool = False,
    octave: int = 4,
) -> None:
    note = ET.SubElement(measure, "note")
    if chord:
        ET.SubElement(note, "chord")
    _pitch(note, pc, octave)
    ET.SubElement(note, "duration").text = str(duration)
    ET.SubElement(note, "voice").text = str(staff)
    ET.SubElement(note, "staff").text = str(staff)


def _forward(measure: ET.Element, duration: int) -> None:
    forward = ET.SubElement(measure, "forward")
    ET.SubElement(forward, "duration").text = str(duration)


def _backup(measure: ET.Element, duration: int) -> None:
    backup = ET.SubElement(measure, "backup")
    ET.SubElement(backup, "duration").text = str(duration)


def starter_score(title: str) -> bytes:
    """Return a small valid PUSH 72 / OUT / END Temperamento score."""
    _validate_project_title(title)
    score = ET.Element("score-partwise", version="4.0")
    work = ET.SubElement(score, "work")
    ET.SubElement(work, "work-title").text = title
    identification = ET.SubElement(score, "identification")
    creator = ET.SubElement(identification, "creator", type="composer")
    creator.text = "Temperamento project"
    part_list = ET.SubElement(score, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    ET.SubElement(score_part, "part-name").text = "Temperamento"
    part = ET.SubElement(score, "part", id="P1")
    measure = ET.SubElement(part, "measure", number="1")
    attributes = ET.SubElement(measure, "attributes")
    ET.SubElement(attributes, "divisions").text = "4"
    time = ET.SubElement(attributes, "time")
    ET.SubElement(time, "beats").text = "56"
    ET.SubElement(time, "beat-type").text = "4"
    ET.SubElement(attributes, "staves").text = "2"

    # Voice: 72 is 60 base-12 => digits 6,0 relative to C.
    _forward(measure, 4)
    _note(measure, 11, 8, 1, octave=5)  # two-quarter header
    _note(measure, 6, 4, 1, octave=5)
    _note(measure, 0, 4, 1, octave=5)
    _forward(measure, 204)
    _backup(measure, 224)

    # Base: PUSH (5MM), OUT (8mm), END (4mm); 16 quarter-note windows.
    pairs = ((0, 11, "M", "M"), (11, 7, "m", "m"), (7, 11, "m", "m"))
    cursor = 0
    for first, second, first_mode, second_mode in pairs:
        for root, mode in ((first, first_mode), (second, second_mode)):
            intervals = (0, 4, 7) if mode == "M" else (0, 3, 7)
            _note(measure, (root + intervals[0]) % 12, 4, 2, octave=3)
            _note(measure, (root + intervals[1]) % 12, 4, 2, chord=True, octave=4)
            _note(measure, (root + intervals[2]) % 12, 4, 2, chord=True, octave=4)
            cursor += 4
            if root == first:
                _forward(measure, 60)
                cursor += 60
        _forward(measure, 8)
        cursor += 8
    if cursor < 224:
        _forward(measure, 224 - cursor)

    ET.indent(score, space="  ")
    return cast(bytes, ET.tostring(score, encoding="utf-8", xml_declaration=True))


_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _mxl_member(name: str, compress_type: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=_ZIP_TIMESTAMP)
    info.compress_type = compress_type
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def write_mxl(musicxml: Path, destination: Path) -> Path:
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="score.musicxml" '
        'media-type="application/vnd.recordare.musicxml+xml"/></rootfiles></container>'
    )
    with zipfile.ZipFile(destination, "w") as archive:
        archive.writestr(
            _mxl_member("mimetype", zipfile.ZIP_STORED),
            b"application/vnd.recordare.musicxml",
        )
        archive.writestr(
            _mxl_member("META-INF/container.xml", zipfile.ZIP_DEFLATED),
            container.encode("utf-8"),
            compresslevel=9,
        )
        archive.writestr(
            _mxl_member("score.musicxml", zipfile.ZIP_DEFLATED),
            musicxml.read_bytes(),
            compresslevel=9,
        )
    return destination


def _check_file_destination(path: Path) -> None:
    if path.is_symlink():
        raise IntegrationError(f"refusing to overwrite symbolic link: {path}")
    if path.exists() and not path.is_file():
        raise IntegrationError(f"project output path is not a regular file: {path}")


def initialise_project(
    target: str | Path,
    *,
    title: str | None = None,
    force: bool = False,
    musescore: str | Path | None = None,
) -> tuple[Path, ...]:
    root = Path(target)
    if root.is_symlink():
        raise IntegrationError(f"project directory may not be a symbolic link: {root}")
    if root.exists() and not root.is_dir():
        raise IntegrationError(f"project path is not a directory: {root}")
    if root.exists() and any(root.iterdir()) and not force:
        raise IntegrationError(f"project directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    project_name = root.name
    project_title = title or project_name.replace("-", " ").replace("_", " ").title()
    _validate_project_title(project_title)
    build = root / "build"
    if build.is_symlink() or (build.exists() and not build.is_dir()):
        raise IntegrationError(f"project build path is not a directory: {build}")
    build.mkdir(exist_ok=True)

    source = root / f"{project_name}.musicxml"
    compressed = root / f"{project_name}.mxl"
    config = root / "temperamento.toml"
    readme = root / "README.md"
    for destination in (source, compressed, config, readme):
        _check_file_destination(destination)

    source.write_bytes(starter_score(project_title))
    write_mxl(source, compressed)
    config.write_text(
        f"title = {json.dumps(project_title, ensure_ascii=False)}\n"
        f"source = {json.dumps(source.name)}\n"
        'build_directory = "build"\n',
        encoding="utf-8",
    )
    readme.write_text(
        f"# {project_title}\n\n"
        "A Temperamento score project. Open the `.musicxml` or `.mxl` file in "
        "MuseScore Studio, edit the two staves, then run:\n\n"
        f"```bash\ntemperamento inspect {source.name} --execute\n"
        f"temperamento run {source.name} --output text\n```\n",
        encoding="utf-8",
    )
    created = [source, compressed, config, readme, build]

    # Native MuseScore output is opt-in. Ambient PATH or environment discovery must not
    # make deterministic project creation depend on an external application.
    if musescore is not None:
        installation = require_musescore(musescore)
        native = root / f"{project_name}.mscz"
        _check_file_destination(native)
        export_score(source, native, executable=installation.executable)
        created.append(native)
    return tuple(created)