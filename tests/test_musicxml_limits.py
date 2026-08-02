from __future__ import annotations

from pathlib import Path

import pytest

from temperamento.errors import MusicXMLError
from temperamento.musicxml import parse_musicxml
from temperamento.project import write_mxl

ROOT = Path(__file__).resolve().parents[1]
MUSICXML = ROOT / "examples/arithmetic/add/add.musicxml"


def _mxl(tmp_path: Path) -> Path:
    return write_mxl(MUSICXML, tmp_path / "score.mxl")


def test_compressed_archive_byte_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _mxl(tmp_path)
    monkeypatch.setattr("temperamento.musicxml._MAX_ARCHIVE_BYTES", source.stat().st_size - 1)
    with pytest.raises(MusicXMLError, match="archive exceeds"):
        parse_musicxml(source)


def test_compressed_archive_entry_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = _mxl(tmp_path)
    monkeypatch.setattr("temperamento.musicxml._MAX_ARCHIVE_ENTRIES", 1)
    with pytest.raises(MusicXMLError, match="entry safety limit"):
        parse_musicxml(source)


def test_measure_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("temperamento.musicxml._MAX_MEASURES", 0)
    with pytest.raises(MusicXMLError, match="measure safety limit"):
        parse_musicxml(MUSICXML)


def test_note_event_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("temperamento.musicxml._MAX_NOTE_EVENTS", 0)
    with pytest.raises(MusicXMLError, match="note-event safety limit"):
        parse_musicxml(MUSICXML)
