from __future__ import annotations

import json
from pathlib import Path

import pytest

from temperamento.compiler import compile_musicxml
from temperamento.toscript import parse_tos_plus_file

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("score-to-code", "toscript-to-score", "toscript-plus-to-score")


@pytest.mark.parametrize("name", NAMES)
def test_direction_packages_are_complete_and_round_trip(name: str) -> None:
    directory = ROOT / "examples" / "directions" / name
    core_path = directory / f"{name}.tos"
    musicxml = directory / f"{name}.musicxml"
    semantic_artifacts = [
        directory / f"{name}.tom",
        core_path,
        musicxml,
        directory / f"{name}-roundtrip.tos",
        directory / f"{name}-roundtrip.tom",
        directory / "expected-output.json",
        directory / "manifest.json",
        directory / "README.md",
    ]
    if name == "score-to-code":
        semantic_artifacts.append(directory / f"{name}-canonical.musicxml")
    for artifact in semantic_artifacts:
        assert artifact.is_file()
        assert artifact.stat().st_size > 0

    canonical = core_path.read_text(encoding="utf-8")
    assert compile_musicxml(musicxml).to_tos() == canonical
    assert (directory / f"{name}-roundtrip.tos").read_text(encoding="utf-8") == canonical
    assert parse_tos_plus_file(directory / f"{name}.tom").to_tos() == canonical
    assert parse_tos_plus_file(directory / f"{name}-roundtrip.tom").to_tos() == canonical

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    canonical_score = directory / manifest["canonical_score_path"]
    assert compile_musicxml(canonical_score).to_tos() == canonical
    assert manifest["verified"]["canonical_round_trip_byte_identical"] is True
    assert manifest["external_only"] == ["audio-to-score transcription"]


@pytest.mark.parametrize("name", NAMES)
def test_generated_direction_media_are_nonempty_when_present(name: str) -> None:
    directory = ROOT / "examples" / "directions" / name
    generated_media = [
        directory / f"{name}.mxl",
        directory / f"{name}.mid",
        directory / f"{name}-reference.wav",
        directory / f"{name}-execution.wav",
        directory / f"{name}-map.svg",
        directory / f"{name}-map.pdf",
        directory / f"{name}.html",
    ]
    generated_media.extend(directory.glob("*.mscz"))
    generated_media.extend(directory.glob("*.pdf"))
    generated_media.extend(directory.glob("*.mp3"))
    for artifact in generated_media:
        if artifact.exists():
            assert artifact.stat().st_size > 0
