from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.generate_examples import SourceInstruction, build_score
from temperamento.compiler import compile_musicxml


def test_standard_external_musicxml_doctype_is_accepted(tmp_path: Path) -> None:
    score = ET.tostring(
        build_score([SourceInstruction("5MM", (7,))]).getroot(),
        encoding="unicode",
    )
    source = tmp_path / "musescore-style.musicxml"
    source.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">\n'
        + score,
        encoding="utf-8",
    )

    assert compile_musicxml(source).to_tos() == "PUSH 7\n"
