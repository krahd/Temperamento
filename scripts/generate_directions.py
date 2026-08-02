from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.generate_showcase import (
    write_execution_wav,
    write_midi,
    write_pdf,
    write_svg,
    write_wav,
)
from temperamento.compiler import compile_musicxml
from temperamento.inspection import inspect_data, inspect_html
from temperamento.interpreter import Interpreter
from temperamento.model import Program
from temperamento.notation import write_musicxml
from temperamento.project import write_mxl
from temperamento.toscript import parse_tos, parse_tos_plus, to_tos_plus

PrimarySource = Literal["MusicXML", "TOScript", "TOScript+"]


@dataclass(frozen=True)
class DirectionExample:
    name: str
    title: str
    primary_source: PrimarySource
    source: str
    output_text: str | None = None


EXAMPLES = (
    DirectionExample(
        "score-to-code",
        "Score to Code",
        "MusicXML",
        "examples/arithmetic/add/add.musicxml",
    ),
    DirectionExample(
        "toscript-to-score",
        "TOScript to Score",
        "TOScript",
        "PUSH 3\nLBL 1\nDUP\nOUT\nPUSH 1\nSUB\nDUP\nJMC 1\nPOP\nEND\n",
    ),
    DirectionExample(
        "toscript-plus-to-score",
        "TOScript+ to Score",
        "TOScript+",
        'print "Hello, World!\\n"\nend\n',
        "Hello, World!\n",
    ),
)


def _program(example: DirectionExample) -> Program:
    if example.primary_source == "MusicXML":
        return compile_musicxml(ROOT / example.source)
    if example.primary_source == "TOScript+":
        return parse_tos_plus(example.source)
    return parse_tos(example.source)


def _primary_path(example: DirectionExample) -> str:
    extension = {
        "MusicXML": "musicxml",
        "TOScript": "tos",
        "TOScript+": "tom",
    }[example.primary_source]
    return f"{example.name}.{extension}"


def _managed_paths(directory: Path, name: str) -> tuple[Path, ...]:
    filenames = (
        "README.md",
        "manifest.json",
        "expected-output.json",
        "expected-output.txt",
        f"{name}.tom",
        f"{name}.tos",
        f"{name}.musicxml",
        f"{name}.mxl",
        f"{name}-canonical.musicxml",
        f"{name}-canonical.mxl",
        f"{name}-roundtrip.tom",
        f"{name}-roundtrip.tos",
        f"{name}.mid",
        f"{name}-reference.wav",
        f"{name}-execution.wav",
        f"{name}-map.svg",
        f"{name}-map.pdf",
        f"{name}.html",
    )
    return tuple(directory / filename for filename in filenames)


def _clear_managed_paths(directory: Path, name: str) -> None:
    for path in _managed_paths(directory, name):
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            raise RuntimeError(f"managed example path is not a regular file: {path}")


def _readme(
    example: DirectionExample,
    *,
    primary_path: str,
    canonical_score: str,
) -> str:
    name = example.name
    first_command = f"temperamento compile {primary_path}"
    distinction = (
        "The hand-authored primary MusicXML and the generated canonical MusicXML are "
        "kept as separate files."
        if example.primary_source == "MusicXML"
        else "The MusicXML score is a canonical realisation generated from the textual source."
    )
    return f"""# {example.title}

Primary source: `{primary_path}`.

This package demonstrates the semantic path `{example.primary_source} → TOScript Core → MusicXML → TOScript Core`. The final canonical program is byte-identical to the first canonical TOScript representation.

```bash
{first_command}
temperamento score {name}.tos --output {canonical_score}
temperamento compile {canonical_score}
temperamento decompile {canonical_score}
temperamento render {name}.musicxml --out-dir rendered --formats mscz,pdf,mp3
```

`{name}-roundtrip.tos` and `{name}-roundtrip.tom` are regenerated from `{canonical_score}`. {distinction} `manifest.json` records each source and derived role.

MuseScore or another notation application supplies engraving and playback. Audio-to-score transcription may be performed by third-party systems, but it is not part of Temperamento's deterministic semantics and is therefore not treated as a verified inverse.
"""


def write_example(example: DirectionExample) -> None:
    directory = ROOT / "examples" / "directions" / example.name
    directory.mkdir(parents=True, exist_ok=True)
    name = example.name
    _clear_managed_paths(directory, name)

    source_core = _program(example)
    primary_path = _primary_path(example)
    primary_musicxml = directory / f"{name}.musicxml"
    canonical_musicxml = primary_musicxml

    if example.primary_source == "TOScript+":
        (directory / primary_path).write_text(example.source, encoding="utf-8")
        (directory / f"{name}.tos").write_text(source_core.to_tos(), encoding="utf-8")
        write_musicxml(
            source_core,
            primary_musicxml,
            title=example.title,
            decorative_base_line=True,
        )
    elif example.primary_source == "TOScript":
        (directory / primary_path).write_text(example.source, encoding="utf-8")
        (directory / f"{name}.tom").write_text(to_tos_plus(source_core), encoding="utf-8")
        write_musicxml(
            source_core,
            primary_musicxml,
            title=example.title,
            decorative_base_line=True,
        )
    else:
        shutil.copyfile(ROOT / example.source, directory / primary_path)
        (directory / f"{name}.tos").write_text(source_core.to_tos(), encoding="utf-8")
        (directory / f"{name}.tom").write_text(to_tos_plus(source_core), encoding="utf-8")
        canonical_musicxml = directory / f"{name}-canonical.musicxml"
        write_musicxml(
            source_core,
            canonical_musicxml,
            title=f"{example.title}: Canonical Realisation",
            decorative_base_line=True,
        )

    primary_program = compile_musicxml(primary_musicxml)
    compiled = compile_musicxml(canonical_musicxml)
    if primary_program.to_tos() != source_core.to_tos():
        raise RuntimeError(f"primary source changed during compilation: {name}")
    if compiled.to_tos() != source_core.to_tos():
        raise RuntimeError(f"direction example changed during MusicXML round trip: {name}")

    roundtrip_tos = directory / f"{name}-roundtrip.tos"
    roundtrip_plus = directory / f"{name}-roundtrip.tom"
    roundtrip_tos.write_text(compiled.to_tos(), encoding="utf-8")
    roundtrip_plus.write_text(to_tos_plus(compiled), encoding="utf-8")
    write_mxl(primary_musicxml, directory / f"{name}.mxl")
    if canonical_musicxml != primary_musicxml:
        write_mxl(canonical_musicxml, directory / f"{name}-canonical.mxl")

    result = Interpreter().run(primary_program)
    (directory / "expected-output.json").write_text(
        json.dumps(
            {
                "output": list(result.output),
                "stack": list(result.stack),
                "steps": result.steps,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if example.output_text is not None:
        (directory / "expected-output.txt").write_text(example.output_text, encoding="utf-8")

    write_midi(primary_musicxml, directory / f"{name}.mid")
    write_wav(primary_musicxml, directory / f"{name}-reference.wav")
    write_execution_wav(primary_program, directory / f"{name}-execution.wav")
    write_svg(example.title, primary_program.to_tos(), directory / f"{name}-map.svg")
    write_pdf(example.title, primary_program.to_tos(), directory / f"{name}-map.pdf")
    (directory / f"{name}.html").write_text(
        inspect_html(inspect_data(primary_program, execute=True), title=example.title),
        encoding="utf-8",
    )
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "title": example.title,
                "primary_source": example.primary_source,
                "primary_path": primary_path,
                "lowered_core_path": f"{name}.tos",
                "canonical_score_path": canonical_musicxml.name,
                "roundtrip_core_path": roundtrip_tos.name,
                "canonical_toscript_plus_path": roundtrip_plus.name,
                "semantic_path": [
                    example.primary_source,
                    "TOScript Core",
                    "MusicXML",
                    "TOScript Core",
                ],
                "presentation_path": [
                    f"{name}.musicxml",
                    f"{name}.pdf",
                    f"{name}.mp3",
                ],
                "verified": {
                    "source_to_core": True,
                    "core_to_musicxml": True,
                    "musicxml_to_core": True,
                    "canonical_round_trip_byte_identical": True,
                    "runtime_output_preserved": True,
                },
                "external_only": ["audio-to-score transcription"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (directory / "README.md").write_text(
        _readme(
            example,
            primary_path=primary_path,
            canonical_score=canonical_musicxml.name,
        ),
        encoding="utf-8",
    )


def main() -> None:
    for example in EXAMPLES:
        write_example(example)
    root = ROOT / "examples" / "directions"
    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text(
        """# Bidirectional examples

These packages separate three authoritative semantic representations from derived media:

1. `TOScript+ ↔ TOScript Core`
2. `TOScript Core ↔ MusicXML`
3. `MusicXML → engraved sheet and playback` through MuseScore or another notation system

- [`score-to-code`](score-to-code/) begins with the existing arithmetic MusicXML source and separately generates a canonical MusicXML realisation from the decoded Core.
- [`toscript-to-score`](toscript-to-score/) begins with canonical TOScript Core.
- [`toscript-plus-to-score`](toscript-plus-to-score/) begins with ergonomic TOScript+.

Every package records the exact primary path, lowered Core, canonical score, byte-identical round trip, expected execution, deterministic reference audio, execution audio, and inspection artefacts. Third-party audio-to-score transcription is permitted as an exploratory input route but is not a deterministic Temperamento inverse.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
