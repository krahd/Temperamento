from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scripts.generate_examples import SourceInstruction, build_score
from temperamento.compiler import compile_musicxml
from temperamento.errors import MusicXMLError


def _score_xml() -> str:
    return ET.tostring(
        build_score([SourceInstruction("5MM", (7,))]).getroot(),
        encoding="unicode",
    )


def test_standard_external_musicxml_doctype_is_accepted(tmp_path: Path) -> None:
    source = tmp_path / "musescore-style.musicxml"
    source.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n' + _score_xml(),
        encoding="utf-8",
    )

    assert compile_musicxml(source).to_tos() == "PUSH 7\n"


def test_nonstandard_external_doctype_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "other-dtd.musicxml"
    source.write_text(
        '<!DOCTYPE score-partwise SYSTEM "https://example.invalid/score.dtd">\n' + _score_xml(),
        encoding="utf-8",
    )

    with pytest.raises(MusicXMLError, match="standard external"):
        compile_musicxml(source)


def test_entity_declaration_is_rejected_even_with_standard_doctype(tmp_path: Path) -> None:
    source = tmp_path / "entity.musicxml"
    source.write_text(
        '<!DOCTYPE score-partwise [<!ENTITY injected "unsafe">]>\n' + _score_xml(),
        encoding="utf-8",
    )

    with pytest.raises(MusicXMLError, match="entity declarations"):
        compile_musicxml(source)
