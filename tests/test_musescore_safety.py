from __future__ import annotations

import os
from pathlib import Path

import pytest

from temperamento.errors import IntegrationError
from temperamento.musescore import export_score, render_score


def test_export_score_refuses_same_source_and_destination(tmp_path: Path) -> None:
    source = tmp_path / "score.musicxml"
    source.write_text("preserve me", encoding="utf-8")

    with pytest.raises(IntegrationError, match="must be different"):
        export_score(source, source)

    assert source.read_text(encoding="utf-8") == "preserve me"


def test_export_score_refuses_hard_link_destination(tmp_path: Path) -> None:
    source = tmp_path / "score.musicxml"
    source.write_text("preserve me", encoding="utf-8")
    linked = tmp_path / "linked.musicxml"
    os.link(source, linked)

    with pytest.raises(IntegrationError, match="must be different"):
        export_score(source, linked)

    assert source.read_text(encoding="utf-8") == "preserve me"


def test_export_score_refuses_symbolic_link_destination(tmp_path: Path) -> None:
    source = tmp_path / "score.musicxml"
    source.write_text("source", encoding="utf-8")
    target = tmp_path / "outside.musicxml"
    target.write_text("preserve me", encoding="utf-8")
    linked = tmp_path / "output.musicxml"
    linked.symlink_to(target)

    with pytest.raises(IntegrationError, match="symbolic link"):
        export_score(source, linked)

    assert target.read_text(encoding="utf-8") == "preserve me"


def test_export_score_refuses_directory_destination(tmp_path: Path) -> None:
    source = tmp_path / "score.musicxml"
    source.write_text("source", encoding="utf-8")
    output = tmp_path / "output.musicxml"
    output.mkdir()

    with pytest.raises(IntegrationError, match="not a regular file"):
        export_score(source, output)


def test_render_score_rejects_empty_format_list(tmp_path: Path) -> None:
    with pytest.raises(IntegrationError, match="at least one"):
        render_score(tmp_path / "score.musicxml", tmp_path / "build", [])
