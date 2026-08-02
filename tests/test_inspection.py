from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from temperamento.compiler import compile_events, compile_musicxml
from temperamento.inspection import inspect_data, inspect_html, inspect_json, inspect_text
from temperamento.model import NoteEvent

ROOT = Path(__file__).resolve().parents[1]


def test_inspection_maps_score_locations_and_runtime() -> None:
    program = compile_musicxml(ROOT / "examples/arithmetic/add/add.musicxml")
    data = inspect_data(program, execute=True)
    first = data["instructions"][0]
    assert first["command"] == 1
    assert first["measure"] == 1
    assert first["beat"] == "1"
    assert first["cell"] == "5MM"
    assert first["opcode"] == "PUSH"
    assert first["operands"] == [7]
    assert "→" in first["base_relation"]
    assert data["ignored_base_event_count"] == 0
    assert data["runtime"]["output"] == [12]
    assert data["runtime"]["trace"]


def test_inspection_reports_ignored_base_material_without_harmonic_inference() -> None:
    def base(pitches: tuple[int, ...], onset: int) -> list[NoteEvent]:
        return [
            NoteEvent(
                Fraction(onset),
                Fraction(1),
                pitch,
                4,
                2,
                "2",
                index > 0,
                measure=1,
                beat=Fraction(onset + 1),
            )
            for index, pitch in enumerate(pitches)
        ]

    events = base((0, 4, 7), 0) + base((0, 5, 7), 4) + base((0, 4, 7), 8)
    data = inspect_data(compile_events(tuple(events)))

    assert data["ignored_base_event_count"] == 1
    ignored = data["ignored_base_events"][0]
    assert ignored["pitches"] == ["C", "F", "G"]
    assert ignored["reason"] == "not an exact major or minor triad"
    assert "Csus" not in inspect_json(data)
    assert "Ignored Base material" in inspect_text(data)
    assert "Ignored Base material" in inspect_html(data)


def test_inspection_renderers_are_self_contained() -> None:
    program = compile_musicxml(ROOT / "examples/iteration/countdown/countdown.musicxml")
    data = inspect_data(program)
    assert "Base relation" in inspect_text(data)
    assert '"instruction_count"' in inspect_json(data)
    rendered = inspect_html(data, title="Inspection test")
    assert "<!doctype html>" in rendered
    assert "Inspection test" in rendered
    assert "Canonical TOScript Core" in rendered


def test_html_uses_repository_relative_source_label(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(ROOT)
    source = ROOT / "examples/arithmetic/add/add.musicxml"
    rendered = inspect_html(inspect_data(compile_musicxml(source)))
    assert "examples/arithmetic/add/add.musicxml" in rendered
    assert str(ROOT) not in rendered


def test_write_inspection_creates_parent_and_runtime_report(tmp_path: Path) -> None:
    from temperamento.inspection import write_inspection

    program = compile_musicxml(ROOT / "examples/arithmetic/add/add.musicxml")
    destination = tmp_path / "nested" / "report.html"
    assert write_inspection(program, destination) == destination
    rendered = destination.read_text(encoding="utf-8")
    assert "Execution" in rendered
    assert "Output:" in rendered
