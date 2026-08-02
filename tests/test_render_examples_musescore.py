from pathlib import Path

import pytest

from scripts import render_examples_musescore as renderer


def test_default_formats_cover_native_sheet_and_playback_without_media_collisions() -> None:
    assert renderer.DEFAULT_FORMATS == ("mscz", "pdf", "mp3")


def test_parse_formats_normalises_and_deduplicates() -> None:
    assert renderer.parse_formats(".PDF, wav,PDF,mp3") == ("pdf", "wav", "mp3")


def test_parse_formats_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one"):
        renderer.parse_formats(" , ")


def test_discover_sources_is_recursive_sorted_and_unique(tmp_path: Path) -> None:
    first = tmp_path / "a" / "first.musicxml"
    second = tmp_path / "b" / "second.musicxml"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("<score-partwise/>", encoding="utf-8")
    second.write_text("<score-partwise/>", encoding="utf-8")

    assert renderer.discover_sources((tmp_path, tmp_path / "a")) == [first, second]


def test_discover_sources_rejects_missing_or_empty_roots(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="does not exist"):
        renderer.discover_sources((tmp_path / "missing",))
    with pytest.raises(RuntimeError, match="no MusicXML"):
        renderer.discover_sources((tmp_path,))


def test_render_examples_exports_every_source_and_checks_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sources = [tmp_path / "a.musicxml", tmp_path / "nested" / "b.musicxml"]
    sources[1].parent.mkdir()
    for source in sources:
        source.write_text("<score-partwise/>", encoding="utf-8")

    rendered_sources: list[Path] = []
    verified_sources: list[Path] = []

    def fake_render_score(
        source: Path,
        output_directory: Path,
        formats: tuple[str, ...],
        *,
        executable: Path,
    ) -> tuple[Path, ...]:
        assert executable == tmp_path / "MuseScore"
        rendered_sources.append(source)
        outputs = tuple(output_directory / f"{source.stem}.{extension}" for extension in formats)
        for output in outputs:
            output.write_bytes(b"rendered")
        return outputs

    def fake_verify_round_trip(source: Path, native: Path, executable: Path) -> None:
        assert native == source.with_suffix(".mscz")
        assert executable == tmp_path / "MuseScore"
        verified_sources.append(source)

    monkeypatch.setattr(renderer, "render_score", fake_render_score)
    monkeypatch.setattr(renderer, "verify_round_trip", fake_verify_round_trip)

    report = renderer.render_examples(
        (tmp_path,),
        ("mscz", "pdf", "wav"),
        executable=tmp_path / "MuseScore",
    )

    assert rendered_sources == sources
    assert verified_sources == sources
    assert report["source_count"] == 2
    assert report["output_count"] == 6
    assert report["round_trip_verified"] is True


def test_round_trip_requires_native_export(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="requires mscz"):
        renderer.render_examples((tmp_path,), ("pdf",), executable=tmp_path / "MuseScore")
