from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from temperamento.compiler import compile_score
from temperamento.errors import TemperamentoError
from temperamento.interpreter import Interpreter
from temperamento.musescore import render_score, require_musescore

DEFAULT_FORMATS = ("mscz", "pdf", "mp3")


def parse_formats(raw: str) -> tuple[str, ...]:
    formats: list[str] = []
    for item in raw.split(","):
        extension = item.strip().lower().lstrip(".")
        if extension and extension not in formats:
            formats.append(extension)
    if not formats:
        raise ValueError("at least one export format is required")
    return tuple(formats)


def discover_sources(roots: Sequence[Path]) -> list[Path]:
    sources: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            raise RuntimeError(f"example root does not exist: {root}")
        sources.update(path for path in root.rglob("*.musicxml") if path.is_file())
    if not sources:
        joined = ", ".join(str(root) for root in roots)
        raise RuntimeError(f"no MusicXML sources found below: {joined}")
    return sorted(sources)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def verify_round_trip(source: Path, native: Path, executable: Path) -> None:
    original = compile_score(source)
    converted = compile_score(native, musescore=executable)
    if converted.to_tos() != original.to_tos():
        raise RuntimeError(f"MuseScore round-trip changed the program: {source}")

    original_result = Interpreter().run(original)
    converted_result = Interpreter().run(converted)
    if converted_result != original_result:
        raise RuntimeError(f"MuseScore round-trip changed runtime behaviour: {source}")


def render_examples(
    roots: Sequence[Path],
    formats: Sequence[str],
    *,
    executable: Path,
    check_round_trip: bool = True,
) -> dict[str, object]:
    if check_round_trip and "mscz" not in formats:
        raise RuntimeError("round-trip verification requires mscz in the export formats")

    sources = discover_sources(roots)
    rendered: list[str] = []
    for source in sources:
        outputs = render_score(source, source.parent, formats, executable=executable)
        for output in outputs:
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"MuseScore did not create {output}")
            rendered.append(display_path(output))
        if check_round_trip:
            verify_round_trip(source, source.with_suffix(".mscz"), executable)

    return {
        "musescore": str(executable),
        "source_count": len(sources),
        "formats": list(formats),
        "output_count": len(rendered),
        "outputs": rendered,
        "round_trip_verified": check_round_trip,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render every MusicXML example through MuseScore Studio."
    )
    parser.add_argument(
        "--root",
        type=Path,
        action="append",
        dest="roots",
        help="example subtree to render; repeatable; defaults to examples/",
    )
    parser.add_argument(
        "--formats",
        default=",".join(DEFAULT_FORMATS),
        help="comma-separated export formats",
    )
    parser.add_argument("--musescore", type=Path, help="path to the MuseScore Studio executable")
    parser.add_argument(
        "--no-round-trip",
        action="store_true",
        help="skip recompilation and runtime-equivalence verification of generated MSCZ files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roots = args.roots or [ROOT / "examples"]
    roots = [root if root.is_absolute() else ROOT / root for root in roots]
    try:
        formats = parse_formats(args.formats)
        installation = require_musescore(args.musescore)
        report = render_examples(
            roots,
            formats,
            executable=installation.executable,
            check_round_trip=not args.no_round_trip,
        )
    except (TemperamentoError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
