from __future__ import annotations

import argparse
import io
import json
import platform
import sys
import tempfile
import webbrowser
from pathlib import Path
from typing import TypedDict

from . import __version__
from .compiler import compile_score
from .errors import TemperamentoError
from .inspection import inspect_data, inspect_html, inspect_json, inspect_text
from .interpreter import Interpreter
from .model import Program
from .musescore import find_musescore, render_score
from .notation import write_musicxml
from .project import initialise_project
from .toscript import parse_tos_file, parse_tos_plus_file, to_tos_plus

_TOS_PLUS_SUFFIXES = {".tom", ".tos+", ".tosplus"}


def _configure_standard_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


class MuseScoreDoctorPayload(TypedDict):
    detected: bool
    runnable: bool
    available: bool
    executable: str | None
    version: str | None
    musicxml_export: bool
    pdf_export: bool
    audio_export: bool


class DoctorPayload(TypedDict):
    temperamento: str
    python: str
    platform: str
    musescore: MuseScoreDoctorPayload


def _positive_integer(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def _add_musescore_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--musescore",
        type=Path,
        help="path to the MuseScore Studio executable",
    )


def _load_program(source: Path, *, musescore: Path | None = None) -> Program:
    suffix = source.suffix.lower()
    if suffix == ".tos":
        return parse_tos_file(source)
    if suffix in _TOS_PLUS_SUFFIXES:
        return parse_tos_plus_file(source)
    return compile_score(source, musescore=musescore)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="temperamento")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_cmd = sub.add_parser(
        "compile", help="compile a score or TOScript+ source to canonical TOScript Core"
    )
    compile_cmd.add_argument("source", type=Path)
    _add_musescore_argument(compile_cmd)

    decompile_cmd = sub.add_parser(
        "decompile", help="write a canonical TOScript+ representation of any program source"
    )
    decompile_cmd.add_argument("source", type=Path)
    decompile_cmd.add_argument("--output", type=Path)
    _add_musescore_argument(decompile_cmd)

    score_cmd = sub.add_parser(
        "score", help="write canonical MusicXML notation from TOScript, TOScript+, or a score"
    )
    score_cmd.add_argument("source", type=Path)
    score_cmd.add_argument("--output", type=Path, required=True)
    score_cmd.add_argument("--title")
    score_cmd.add_argument("--transpose", type=int, default=0)
    score_cmd.add_argument("--reverse-voicing", action="store_true")
    score_cmd.add_argument("--double-roots", action="store_true")
    score_cmd.add_argument("--decorative-base-line", action="store_true")
    _add_musescore_argument(score_cmd)

    validate_cmd = sub.add_parser("validate", help="validate a score or textual program")
    validate_cmd.add_argument("source", type=Path)
    _add_musescore_argument(validate_cmd)

    run_cmd = sub.add_parser("run", help="compile and execute a score or textual program")
    run_cmd.add_argument("source", type=Path)
    run_cmd.add_argument("--max-steps", type=_positive_integer, default=100_000)
    run_cmd.add_argument(
        "--output",
        choices=("json", "numbers", "text"),
        default="json",
        help="presentation of the numeric OUT stream",
    )
    _add_musescore_argument(run_cmd)

    inspect_cmd = sub.add_parser(
        "inspect",
        help="explain the source-to-program mapping",
    )
    inspect_cmd.add_argument("source", type=Path)
    inspect_cmd.add_argument("--execute", action="store_true", help="include an execution trace")
    inspect_cmd.add_argument("--max-steps", type=_positive_integer, default=100_000)
    inspect_cmd.add_argument("--format", choices=("text", "json", "html"), default="text")
    inspect_cmd.add_argument("--output", type=Path, help="write the report to a file")
    _add_musescore_argument(inspect_cmd)

    gui_cmd = sub.add_parser("gui", help="open the interactive HTML source/program report")
    gui_cmd.add_argument("source", type=Path)
    gui_cmd.add_argument("--output", type=Path, help="persistent HTML destination")
    gui_cmd.add_argument(
        "--no-open",
        action="store_true",
        help="write the report without opening a browser",
    )
    gui_cmd.add_argument("--max-steps", type=_positive_integer, default=100_000)
    _add_musescore_argument(gui_cmd)

    doctor_cmd = sub.add_parser("doctor", help="diagnose the local Temperamento environment")
    doctor_cmd.add_argument("--json", action="store_true")
    _add_musescore_argument(doctor_cmd)

    init_cmd = sub.add_parser("init", help="create a new MuseScore-ready project")
    init_cmd.add_argument("target", type=Path)
    init_cmd.add_argument("--title")
    init_cmd.add_argument("--force", action="store_true")
    _add_musescore_argument(init_cmd)

    render_cmd = sub.add_parser("render", help="export score media through MuseScore Studio")
    render_cmd.add_argument("source", type=Path)
    render_cmd.add_argument("--out-dir", type=Path, default=Path("build"))
    render_cmd.add_argument(
        "--formats",
        default="pdf,svg,mid,wav,musicxml",
        help="comma-separated MuseScore export extensions",
    )
    _add_musescore_argument(render_cmd)
    return parser


def _text_output(values: tuple[int | float, ...]) -> str:
    characters: list[str] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TemperamentoError(
                f"text output requires integer Unicode scalar values; output {index} is {value!r}"
            )
        if not 0 <= value <= 0x10FFFF or 0xD800 <= value <= 0xDFFF:
            raise TemperamentoError(f"output {index} is not a Unicode scalar value: {value}")
        characters.append(chr(value))
    return "".join(characters)


def _doctor_payload(explicit: Path | None) -> DoctorPayload:
    installation = find_musescore(explicit)
    detected = installation is not None
    # find_musescore probes the executable for a version while discovering it. A file can
    # therefore be present but not runnable in the current environment; do not advertise
    # export capabilities unless that probe succeeded.
    runnable = installation is not None and installation.version is not None
    return {
        "temperamento": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "musescore": {
            "detected": detected,
            "runnable": runnable,
            "available": runnable,
            "executable": str(installation.executable) if installation else None,
            "version": installation.version if installation else None,
            "musicxml_export": runnable,
            "pdf_export": runnable,
            "audio_export": runnable,
        },
    }


def main(argv: list[str] | None = None) -> int:
    _configure_standard_streams()
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            payload = _doctor_payload(args.musescore)
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                muse = payload["musescore"]
                print(f"Temperamento {payload['temperamento']}")
                print(f"Python {payload['python']}")
                print(f"Platform {payload['platform']}")
                if muse["runnable"]:
                    version = muse["version"] or "version unavailable"
                    print(f"MuseScore Studio: {version}")
                    print(f"Executable: {muse['executable']}")
                    print("MusicXML export: available")
                    print("PDF export: available")
                    print("Audio export: available")
                elif muse["detected"]:
                    print("MuseScore Studio: executable found but not runnable")
                    print(f"Executable: {muse['executable']}")
                    print("MusicXML export: unavailable")
                    print("PDF export: unavailable")
                    print("Audio export: unavailable")
                else:
                    print("MuseScore Studio: not found")
                    print("Set TEMPERAMENTO_MUSESCORE or pass --musescore.")
            return 0

        if args.command == "init":
            created = initialise_project(
                args.target,
                title=args.title,
                force=args.force,
                musescore=args.musescore,
            )
            print(
                json.dumps(
                    {"project": str(args.target), "created": [str(path) for path in created]}
                )
            )
            return 0

        if args.command == "render":
            formats = [item.strip() for item in args.formats.split(",") if item.strip()]
            outputs = render_score(
                args.source,
                args.out_dir,
                formats,
                executable=args.musescore,
            )
            print(json.dumps({"outputs": [str(path) for path in outputs]}))
            return 0

        if args.command == "score":
            program = _load_program(args.source, musescore=args.musescore)
            title = args.title or (args.output.stem.replace("-", " ").replace("_", " ").title())
            destination = write_musicxml(
                program,
                args.output,
                title=title,
                transpose=args.transpose,
                reverse_voicing=args.reverse_voicing,
                double_roots=args.double_roots,
                decorative_base_line=args.decorative_base_line,
            )
            print(str(destination))
            return 0

        program = _load_program(args.source, musescore=args.musescore)
        if args.command == "compile":
            sys.stdout.write(program.to_tos())
            return 0
        if args.command == "decompile":
            rendered = to_tos_plus(program)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
                print(str(args.output))
            else:
                sys.stdout.write(rendered)
            return 0
        if args.command == "validate":
            print(
                json.dumps(
                    {
                        "valid": True,
                        "source": str(args.source),
                        "instructions": len(program.instructions),
                        "ignored_base_events": len(program.ignored_base_events),
                    }
                )
            )
            return 0
        if args.command in {"inspect", "gui"}:
            execute = args.execute if args.command == "inspect" else True
            data = inspect_data(program, execute=execute, max_steps=args.max_steps)
            if args.command == "gui":
                if args.output:
                    destination = args.output
                else:
                    directory = Path(tempfile.mkdtemp(prefix="temperamento-gui-"))
                    destination = directory / "report.html"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    inspect_html(data, title=f"Temperamento: {args.source.name}"),
                    encoding="utf-8",
                )
                if not args.no_open:
                    webbrowser.open(destination.resolve().as_uri())
                print(str(destination))
                return 0
            if args.format == "json":
                rendered = inspect_json(data)
            elif args.format == "html":
                rendered = inspect_html(data, title=f"Temperamento inspection: {args.source.name}")
            else:
                rendered = inspect_text(data)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
                print(str(args.output))
            else:
                sys.stdout.write(rendered)
            return 0

        result = Interpreter(max_steps=args.max_steps).run(program)
        if args.output == "text":
            sys.stdout.write(_text_output(result.output))
        elif args.output == "numbers":
            sys.stdout.write(" ".join(map(str, result.output)) + "\n")
        else:
            print(
                json.dumps({"output": result.output, "stack": result.stack, "steps": result.steps})
            )
        return 0
    except (OSError, TemperamentoError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
