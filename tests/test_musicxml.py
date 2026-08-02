from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

import temperamento.musicxml as musicxml
from scripts.generate_examples import SourceInstruction, build_score
from temperamento.compiler import compile_musicxml
from temperamento.errors import MusicXMLError
from temperamento.musicxml import parse_musicxml


def write_tree(tree: ET.ElementTree, path: Path) -> Path:
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def first(element: ET.Element, tag: str) -> ET.Element:
    found = element.find(f".//{tag}")
    assert found is not None
    return found


def test_zero_arity_program_may_have_no_pitched_voice_material(tmp_path: Path) -> None:
    source = write_tree(build_score([SourceInstruction("0MM")]), tmp_path / "add.musicxml")
    assert compile_musicxml(source).to_tos() == "ADD\n"


def test_default_namespace_is_supported(tmp_path: Path) -> None:
    source = tmp_path / "namespaced.musicxml"
    raw = ET.tostring(build_score([SourceInstruction("5MM", (7,))]).getroot(), encoding="unicode")
    raw = raw.replace(
        '<score-partwise version="4.0">',
        '<score-partwise xmlns="http://www.musicxml.org/ns/musicxml" version="4.0">',
        1,
    )
    source.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + raw, encoding="utf-8")
    assert compile_musicxml(source).to_tos() == "PUSH 7\n"


def test_compressed_mxl_is_supported(tmp_path: Path) -> None:
    score = ET.tostring(
        build_score([SourceInstruction("5MM", (143,))]).getroot(),
        encoding="utf-8",
        xml_declaration=True,
    )
    container = b"""<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="score.musicxml"
      media-type="application/vnd.recordare.musicxml+xml"/>
  </rootfiles>
</container>"""
    source = tmp_path / "score.mxl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("score.musicxml", score)
    assert compile_musicxml(source).to_tos() == "PUSH 143\n"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("divisions", "zero", "divisions must be an integer"),
        ("duration", "1.5", "duration must be an integer"),
        ("alter", "0.5", "alter must be an integer"),
    ],
)
def test_invalid_numeric_fields_are_user_facing_errors(
    field: str,
    value: str,
    message: str,
    tmp_path: Path,
) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    first(tree.getroot(), field).text = value
    source = write_tree(tree, tmp_path / f"bad-{field}.musicxml")
    with pytest.raises(MusicXMLError, match=message):
        parse_musicxml(source)


def test_reference_subset_requires_two_declared_staves(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    first(tree.getroot(), "staves").text = "3"
    source = write_tree(tree, tmp_path / "three-staves.musicxml")
    with pytest.raises(MusicXMLError, match="exactly two staves"):
        parse_musicxml(source)


def test_multiple_voices_on_one_staff_are_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (143,))])
    voice_notes = [
        note for note in tree.getroot().findall(".//note") if first(note, "staff").text == "1"
    ]
    assert len(voice_notes) >= 2
    first(voice_notes[-1], "voice").text = "9"
    source = write_tree(tree, tmp_path / "multiple-voices.musicxml")
    with pytest.raises(MusicXMLError, match="one MusicXML voice per staff"):
        parse_musicxml(source)


def test_chord_member_must_immediately_follow_anchor(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("0MM")])
    measure = first(tree.getroot(), "measure")
    elements = list(measure)
    first_base_index = next(
        index
        for index, element in enumerate(elements)
        if element.tag == "note" and first(element, "staff").text == "2"
    )
    measure.insert(first_base_index + 1, ET.Element("direction"))
    source = write_tree(tree, tmp_path / "broken-chord.musicxml")
    with pytest.raises(MusicXMLError, match="immediately follow"):
        parse_musicxml(source)


def test_dtd_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "dtd.musicxml"
    source.write_text(
        '<?xml version="1.0"?><!DOCTYPE score-partwise [<!ENTITY x "x">]>'
        '<score-partwise version="4.0"></score-partwise>',
        encoding="utf-8",
    )
    with pytest.raises(MusicXMLError, match="DTD"):
        parse_musicxml(source)


def test_mxl_requires_safe_declared_rootfile(tmp_path: Path) -> None:
    source = tmp_path / "unsafe.mxl"
    container = (
        b'<container><rootfiles><rootfile full-path="../score.musicxml"/></rootfiles></container>'
    )
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("score.musicxml", b"<score-partwise/>")
    with pytest.raises(MusicXMLError, match="unsafe"):
        parse_musicxml(source)


def test_missing_and_out_of_range_integer_values_are_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    first(tree.getroot(), "duration").text = None
    source = write_tree(tree, tmp_path / "missing-duration.musicxml")
    with pytest.raises(MusicXMLError, match="requires an integer"):
        parse_musicxml(source)

    tree = build_score([SourceInstruction("5MM", (7,))])
    first(tree.getroot(), "duration").text = "0"
    source = write_tree(tree, tmp_path / "zero-duration.musicxml")
    with pytest.raises(MusicXMLError, match="at least 1"):
        parse_musicxml(source)


def test_malformed_xml_is_reported(tmp_path: Path) -> None:
    source = tmp_path / "malformed.musicxml"
    source.write_text("<score-partwise><part>", encoding="utf-8")
    with pytest.raises(MusicXMLError, match="cannot parse MusicXML"):
        parse_musicxml(source)


def test_uncompressed_xml_size_limit_is_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(musicxml, "_MAX_XML_BYTES", 8)
    source = tmp_path / "large.musicxml"
    source.write_bytes(b"<score-partwise/>")
    with pytest.raises(MusicXMLError, match="safety limit"):
        parse_musicxml(source)


def test_missing_mxl_is_reported_as_user_error(tmp_path: Path) -> None:
    with pytest.raises(MusicXMLError, match="cannot read compressed MusicXML"):
        parse_musicxml(tmp_path / "missing.mxl")


def test_mxl_container_is_required_exactly_once(tmp_path: Path) -> None:
    missing = tmp_path / "missing-container.mxl"
    with zipfile.ZipFile(missing, "w") as archive:
        archive.writestr("score.musicxml", b"<score-partwise/>")
    with pytest.raises(MusicXMLError, match="exactly one META-INF/container\\.xml"):
        parse_musicxml(missing)

    duplicate = tmp_path / "duplicate-container.mxl"
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(duplicate, "w") as archive:
            archive.writestr("META-INF/container.xml", b"<container/>")
            archive.writestr("META-INF/container.xml", b"<container/>")
    with pytest.raises(MusicXMLError, match="exactly one META-INF/container\\.xml"):
        parse_musicxml(duplicate)


def test_mxl_container_size_limit_is_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(musicxml, "_MAX_XML_BYTES", 8)
    source = tmp_path / "large-container.mxl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", b"<container/>")
    with pytest.raises(MusicXMLError, match="container\\.xml exceeds"):
        parse_musicxml(source)


def test_mxl_requires_a_score_rootfile(tmp_path: Path) -> None:
    source = tmp_path / "rootfiles.mxl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", b"<container><rootfiles/></container>")
    with pytest.raises(MusicXMLError, match="identify a score rootfile"):
        parse_musicxml(source)


def test_mxl_uses_first_rootfile_and_allows_alternate_renditions(tmp_path: Path) -> None:
    score = ET.tostring(
        build_score([SourceInstruction("5MM", (7,))]).getroot(),
        encoding="utf-8",
        xml_declaration=True,
    )
    container = b"""<container><rootfiles>
      <rootfile full-path='score.musicxml' media-type='application/vnd.recordare.musicxml+xml'/>
      <rootfile full-path='preview.pdf' media-type='application/pdf'/>
    </rootfiles></container>"""
    source = tmp_path / "alternate-rootfiles.mxl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("score.musicxml", score)
        archive.writestr("preview.pdf", b"not read")
    assert compile_musicxml(source).to_tos() == "PUSH 7\n"


def test_mxl_rejects_non_musicxml_first_rootfile(tmp_path: Path) -> None:
    source = tmp_path / "pdf-first.mxl"
    container = b"""<container><rootfiles>
      <rootfile full-path='preview.pdf' media-type='application/pdf'/>
      <rootfile full-path='score.musicxml' media-type='application/vnd.recordare.musicxml+xml'/>
    </rootfiles></container>"""
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("preview.pdf", b"pdf")
        archive.writestr("score.musicxml", b"<score-partwise/>")
    with pytest.raises(MusicXMLError, match="first compressed MusicXML rootfile"):
        parse_musicxml(source)


def test_mxl_rejects_duplicate_score_entry(tmp_path: Path) -> None:
    source = tmp_path / "duplicate-score.mxl"
    container = (
        b"<container><rootfiles><rootfile full-path='score.musicxml'/></rootfiles></container>"
    )
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("META-INF/container.xml", container)
            archive.writestr("score.musicxml", b"<score-partwise/>")
            archive.writestr("score.musicxml", b"<score-partwise/>")
    with pytest.raises(MusicXMLError, match="is duplicated"):
        parse_musicxml(source)


def test_mxl_container_root_is_validated(tmp_path: Path) -> None:
    source = tmp_path / "wrong-container-root.mxl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            b"<wrong><rootfiles><rootfile full-path='score.musicxml'/></rootfiles></wrong>",
        )
        archive.writestr("score.musicxml", b"<score-partwise/>")
    with pytest.raises(MusicXMLError, match="container root element"):
        parse_musicxml(source)


def test_mxl_declared_rootfile_must_exist(tmp_path: Path) -> None:
    source = tmp_path / "missing-root.mxl"
    container = (
        b"<container><rootfiles><rootfile full-path='score.musicxml'/></rootfiles></container>"
    )
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
    with pytest.raises(MusicXMLError, match="rootfile 'score\\.musicxml' is missing"):
        parse_musicxml(source)


def test_mxl_score_size_limit_is_enforced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(musicxml, "_MAX_XML_BYTES", 128)
    source = tmp_path / "large-score.mxl"
    container = (
        b"<container><rootfiles><rootfile full-path='score.musicxml'/></rootfiles></container>"
    )
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("score.musicxml", b"<score-partwise>" + b" " * 256 + b"</score-partwise>")
    with pytest.raises(MusicXMLError, match="score exceeds"):
        parse_musicxml(source)


def test_only_partwise_single_part_scores_with_measures_are_accepted(tmp_path: Path) -> None:
    timewise = tmp_path / "timewise.musicxml"
    timewise.write_text("<score-timewise/>", encoding="utf-8")
    with pytest.raises(MusicXMLError, match="score-partwise"):
        parse_musicxml(timewise)

    no_part = tmp_path / "no-part.musicxml"
    no_part.write_text("<score-partwise/>", encoding="utf-8")
    with pytest.raises(MusicXMLError, match="exactly one part"):
        parse_musicxml(no_part)

    two_parts = tmp_path / "two-parts.musicxml"
    two_parts.write_text("<score-partwise><part/><part/></score-partwise>", encoding="utf-8")
    with pytest.raises(MusicXMLError, match="exactly one part"):
        parse_musicxml(two_parts)

    no_measures = tmp_path / "no-measures.musicxml"
    no_measures.write_text("<score-partwise><part/></score-partwise>", encoding="utf-8")
    with pytest.raises(MusicXMLError, match="no measures"):
        parse_musicxml(no_measures)


def test_declared_staff_count_may_not_change(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    measure = first(tree.getroot(), "measure")
    attributes = ET.Element("attributes")
    ET.SubElement(attributes, "staves").text = "3"
    measure.append(attributes)
    source = write_tree(tree, tmp_path / "changing-staves.musicxml")
    with pytest.raises(MusicXMLError, match="may not change"):
        parse_musicxml(source)


def test_backup_cannot_move_before_measure_start(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("0MM")])
    measure = first(tree.getroot(), "measure")
    backup = ET.Element("backup")
    ET.SubElement(backup, "duration").text = "9999"
    measure.insert(1, backup)
    source = write_tree(tree, tmp_path / "negative-cursor.musicxml")
    with pytest.raises(MusicXMLError, match="before the measure start"):
        parse_musicxml(source)


def test_rest_chord_members_and_unpitched_notes_are_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("0MM")])
    note = first(tree.getroot(), "note")
    pitch = first(note, "pitch")
    note.remove(pitch)
    note.insert(0, ET.Element("rest"))
    note.insert(0, ET.Element("chord"))
    source = write_tree(tree, tmp_path / "chord-rest.musicxml")
    with pytest.raises(MusicXMLError, match="rests cannot be chord members"):
        parse_musicxml(source)

    tree = build_score([SourceInstruction("0MM")])
    note = first(tree.getroot(), "note")
    note.remove(first(note, "pitch"))
    source = write_tree(tree, tmp_path / "unpitched.musicxml")
    with pytest.raises(MusicXMLError, match="unpitched"):
        parse_musicxml(source)


def test_pitch_requires_valid_step_and_octave(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("0MM")])
    first(tree.getroot(), "step").text = "H"
    source = write_tree(tree, tmp_path / "bad-step.musicxml")
    with pytest.raises(MusicXMLError, match="valid step and octave"):
        parse_musicxml(source)

    tree = build_score([SourceInstruction("0MM")])
    octave = first(tree.getroot(), "octave")
    parent = first(tree.getroot(), "pitch")
    parent.remove(octave)
    source = write_tree(tree, tmp_path / "missing-octave.musicxml")
    with pytest.raises(MusicXMLError, match="valid step and octave"):
        parse_musicxml(source)


def test_empty_measure_and_all_rest_score_are_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "empty-measure.musicxml"
    empty.write_text(
        "<score-partwise><part><measure><attributes><staves>2</staves></attributes>"
        "</measure></part></score-partwise>",
        encoding="utf-8",
    )
    with pytest.raises(MusicXMLError, match="no explicit temporal extent"):
        parse_musicxml(empty)

    rests = tmp_path / "rests.musicxml"
    rests.write_text(
        "<score-partwise><part><measure><attributes><divisions>1</divisions>"
        "<staves>2</staves></attributes>"
        "<note><rest/><duration>1</duration><voice>2</voice><staff>2</staff></note>"
        "</measure></part></score-partwise>",
        encoding="utf-8",
    )
    with pytest.raises(MusicXMLError, match="no pitched notes"):
        parse_musicxml(rests)


def test_extra_staff_material_is_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    for staff in tree.getroot().findall(".//staff"):
        if staff.text == "1":
            staff.text = "3"
    source = write_tree(tree, tmp_path / "staff-three.musicxml")
    with pytest.raises(MusicXMLError, match="only on staves 1 and 2"):
        parse_musicxml(source)


def test_rest_and_forward_advance_measure_time(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("0MM")])
    measure = first(tree.getroot(), "measure")
    rest = ET.Element("note")
    ET.SubElement(rest, "rest")
    ET.SubElement(rest, "duration").text = "4"
    ET.SubElement(rest, "voice").text = "1"
    ET.SubElement(rest, "staff").text = "1"
    measure.insert(1, rest)
    source = write_tree(tree, tmp_path / "rest.musicxml")
    events = parse_musicxml(source)
    assert events


def test_mxl_requires_rootfiles_element(tmp_path: Path) -> None:
    source = tmp_path / "no-rootfiles-element.mxl"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", b"<container/>")
    with pytest.raises(MusicXMLError, match="no rootfiles element"):
        parse_musicxml(source)


def test_mxl_score_rootfile_must_be_a_regular_file(tmp_path: Path) -> None:
    source = tmp_path / "directory-rootfile.mxl"
    container = (
        b"<container><rootfiles><rootfile full-path='score.musicxml/'/></rootfiles></container>"
    )
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("score.musicxml/", b"")
    with pytest.raises(MusicXMLError, match="regular file"):
        parse_musicxml(source)


def test_rest_voices_are_included_in_single_voice_validation(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    measure = first(tree.getroot(), "measure")
    rest = ET.Element("note")
    ET.SubElement(rest, "rest")
    ET.SubElement(rest, "duration").text = "1"
    ET.SubElement(rest, "voice").text = "alternate"
    ET.SubElement(rest, "staff").text = "1"
    measure.append(rest)
    source = write_tree(tree, tmp_path / "rest-second-voice.musicxml")
    with pytest.raises(MusicXMLError, match="one MusicXML voice per staff"):
        parse_musicxml(source)


def test_rest_material_outside_two_staves_is_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    measure = first(tree.getroot(), "measure")
    rest = ET.Element("note")
    ET.SubElement(rest, "rest")
    ET.SubElement(rest, "duration").text = "1"
    ET.SubElement(rest, "voice").text = "1"
    ET.SubElement(rest, "staff").text = "3"
    measure.append(rest)
    source = write_tree(tree, tmp_path / "third-staff-rest.musicxml")
    with pytest.raises(MusicXMLError, match="only on staves 1 and 2"):
        parse_musicxml(source)


def test_tied_notes_are_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    note = first(tree.getroot(), "note")
    ET.SubElement(note, "tie", type="start")
    source = write_tree(tree, tmp_path / "tie.musicxml")
    with pytest.raises(MusicXMLError, match="tied notes"):
        parse_musicxml(source)


def test_notated_tied_notes_are_rejected(tmp_path: Path) -> None:
    tree = build_score([SourceInstruction("5MM", (7,))])
    note = first(tree.getroot(), "note")
    notations = ET.SubElement(note, "notations")
    ET.SubElement(notations, "tied", type="start")
    source = write_tree(tree, tmp_path / "tied-notation.musicxml")
    with pytest.raises(MusicXMLError, match="tied notes"):
        parse_musicxml(source)
