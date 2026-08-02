from __future__ import annotations

import json
from pathlib import Path

import pytest

from temperamento.cli import main
from temperamento.errors import IntegrationError
from temperamento.musescore import MuseScoreInstallation
from temperamento.project import initialise_project, starter_score


def test_doctor_distinguishes_detected_from_runnable_musescore(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    executable = tmp_path / "mscore"
    executable.write_text("not runnable here", encoding="utf-8")
    installation = MuseScoreInstallation(executable, None)
    monkeypatch.setattr("temperamento.cli.find_musescore", lambda _: installation)

    assert main(["doctor", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)["musescore"]
    assert payload == {
        "detected": True,
        "runnable": False,
        "available": False,
        "executable": str(executable),
        "version": None,
        "musicxml_export": False,
        "pdf_export": False,
        "audio_export": False,
    }

    assert main(["doctor"]) == 0
    text = capsys.readouterr().out
    assert "executable found but not runnable" in text
    assert "export: unavailable" in text


@pytest.mark.parametrize("title", ["bad\x00title", "x" * 4097])
def test_starter_score_rejects_unsafe_project_titles(title: str) -> None:
    with pytest.raises(IntegrationError):
        starter_score(title)


def test_invalid_project_title_does_not_create_partial_project(tmp_path: Path) -> None:
    target = tmp_path / "unsafe"
    with pytest.raises(IntegrationError, match="not valid in XML"):
        initialise_project(target, title="bad\x00title")
    assert target.is_dir()
    assert list(target.iterdir()) == []
