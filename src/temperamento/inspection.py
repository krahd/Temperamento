from __future__ import annotations

import html
import json
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from typing import Any

from .interpreter import Interpreter
from .model import IgnoredBaseEvent, Instruction, Program

_PITCH_NAMES = ("C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B")


def _fraction(value: Fraction) -> str:
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _root_name(root: int | None) -> str:
    return "?" if root is None else _PITCH_NAMES[root % 12]


def _source_label(source: object) -> str:
    if source is None or source == "":
        return "in-memory score"
    raw = str(source)
    try:
        return Path(raw).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (OSError, ValueError):
        return raw


def instruction_record(index: int, instruction: Instruction) -> dict[str, Any]:
    initial = f"{_root_name(instruction.initial_root)} {instruction.cell.initial_mode}"
    final = f"{_root_name(instruction.final_root)} {instruction.cell.final_mode}"
    return {
        "command": index + 1,
        "measure": instruction.measure,
        "beat": _fraction(instruction.beat),
        "score_time": _fraction(instruction.onset),
        "base_relation": f"{initial} → {final}",
        "cell": instruction.cell.token,
        "opcode": instruction.opcode,
        "operands": list(instruction.operands),
        "toscript": instruction.to_tos(),
        "voice_onsets": [_fraction(onset) for onset in instruction.voice_onsets],
    }


def ignored_base_record(event: IgnoredBaseEvent) -> dict[str, Any]:
    return {
        "measure": event.measure,
        "beat": _fraction(event.beat),
        "score_time": _fraction(event.onset),
        "pitch_classes": list(event.pitch_classes),
        "pitches": [_PITCH_NAMES[pitch_class % 12] for pitch_class in event.pitch_classes],
        "note_count": event.note_count,
        "reason": event.reason,
    }


def inspect_data(
    program: Program,
    *,
    execute: bool = False,
    max_steps: int = 100_000,
) -> dict[str, Any]:
    records = [instruction_record(index, item) for index, item in enumerate(program.instructions)]
    ignored = [ignored_base_record(item) for item in program.ignored_base_events]
    data: dict[str, Any] = {
        "source": program.source,
        "instructions": records,
        "instruction_count": len(records),
        "ignored_base_events": ignored,
        "ignored_base_event_count": len(ignored),
        "toscript": program.to_tos(),
    }
    if execute:
        result = Interpreter(max_steps=max_steps).run(program, capture_trace=True)
        data["runtime"] = {
            "output": list(result.output),
            "stack": list(result.stack),
            "steps": result.steps,
            "trace": [asdict(step) for step in result.trace],
        }
    return data


def inspect_text(data: dict[str, Any]) -> str:
    rows = data["instructions"]
    headers = ("Cmd", "Measure", "Beat", "Base relation", "Cell", "Opcode", "Operand")
    rendered = []
    for row in rows:
        operands = " ".join(map(str, row["operands"])) or "—"
        rendered.append(
            (
                str(row["command"]),
                str(row["measure"]),
                str(row["beat"]),
                str(row["base_relation"]),
                str(row["cell"]),
                str(row["opcode"]),
                operands,
            )
        )
    widths = [len(header) for header in headers]
    for row in rendered:
        widths = [max(width, len(value)) for width, value in zip(widths, row, strict=True)]
    lines = ["  ".join(header.ljust(width) for header, width in zip(headers, widths, strict=True))]
    lines.append("  ".join("-" * width for width in widths))
    lines.extend(
        "  ".join(value.ljust(width) for value, width in zip(row, widths, strict=True))
        for row in rendered
    )

    ignored = data.get("ignored_base_events", [])
    if ignored:
        ignored_headers = ("Measure", "Beat", "Pitches", "Notes", "Reason")
        ignored_rows = [
            (
                str(row["measure"]),
                str(row["beat"]),
                "-".join(row["pitches"]),
                str(row["note_count"]),
                str(row["reason"]),
            )
            for row in ignored
        ]
        ignored_widths = [len(header) for header in ignored_headers]
        for row in ignored_rows:
            ignored_widths = [
                max(width, len(value)) for width, value in zip(ignored_widths, row, strict=True)
            ]
        lines.extend(
            [
                "",
                "Ignored Base material",
                "  ".join(
                    header.ljust(width)
                    for header, width in zip(ignored_headers, ignored_widths, strict=True)
                ),
                "  ".join("-" * width for width in ignored_widths),
            ]
        )
        lines.extend(
            "  ".join(value.ljust(width) for value, width in zip(row, ignored_widths, strict=True))
            for row in ignored_rows
        )

    runtime = data.get("runtime")
    if runtime:
        lines.extend(
            [
                "",
                f"Output: {runtime['output']}",
                f"Final stack: {runtime['stack']}",
                f"Steps: {runtime['steps']}",
            ]
        )
    return "\n".join(lines) + "\n"


def inspect_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def inspect_html(data: dict[str, Any], *, title: str = "Temperamento inspection") -> str:
    rows = []
    for row in data["instructions"]:
        operands = " ".join(map(str, row["operands"])) or "—"
        rows.append(
            "<tr>"
            f"<td>{row['command']}</td><td>{row['measure']}</td><td>{html.escape(str(row['beat']))}</td>"
            f"<td>{html.escape(str(row['base_relation']))}</td><td><code>{row['cell']}</code></td>"
            f"<td><code>{row['opcode']}</code></td><td>{html.escape(operands)}</td>"
            "</tr>"
        )

    ignored_html = ""
    ignored = data.get("ignored_base_events", [])
    if ignored:
        ignored_rows = []
        for row in ignored:
            pitches = "-".join(row["pitches"])
            ignored_rows.append(
                "<tr>"
                f"<td>{row['measure']}</td><td>{html.escape(str(row['beat']))}</td>"
                f"<td>{html.escape(pitches)}</td><td>{row['note_count']}</td>"
                f"<td>{html.escape(str(row['reason']))}</td>"
                "</tr>"
            )
        ignored_html = (
            "<section><h2>Ignored Base material</h2>"
            "<p>These well-formed score events remain musical material but are outside the exact major/minor computational alphabet. They do not affect chord pairing.</p>"
            "<div class='scroll'><table><thead><tr><th>Measure</th><th>Beat</th><th>Pitches</th><th>Notes</th><th>Reason</th></tr></thead><tbody>"
            + "".join(ignored_rows)
            + "</tbody></table></div></section>"
        )

    trace_html = ""
    runtime = data.get("runtime")
    if runtime:
        trace_rows = []
        for step in runtime["trace"]:
            trace_rows.append(
                "<tr>"
                f"<td>{step['pc']}</td><td><code>{html.escape(step['opcode'])}</code></td>"
                f"<td><code>{html.escape(str(step['stack_before']))}</code></td>"
                f"<td><code>{html.escape(str(step['stack_after']))}</code></td>"
                f"<td><code>{html.escape(str(step['output_after']))}</code></td>"
                "</tr>"
            )
        trace_html = (
            "<section><h2>Execution</h2>"
            f"<p><strong>Output:</strong> <code>{html.escape(str(runtime['output']))}</code> · "
            f"<strong>Steps:</strong> {runtime['steps']}</p>"
            "<div class='scroll'><table><thead><tr><th>PC</th><th>Instruction</th>"
            "<th>Stack before</th><th>Stack after</th><th>Output</th></tr></thead><tbody>"
            + "".join(trace_rows)
            + "</tbody></table></div></section>"
        )
    source_label = _source_label(data.get("source"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--ink:#15171a;--muted:#626974;--line:#d9dde3;--paper:#fff;--wash:#f4f6f8;--accent:#6b3fd4}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:16px/1.5 system-ui,-apple-system,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 20px 64px}}h1{{margin-bottom:.2rem}}.lede{{color:var(--muted);margin-top:0}}
section{{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 8px 28px rgba(20,24,32,.06)}}
table{{border-collapse:collapse;width:100%}}th,td{{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;white-space:nowrap}}th{{background:var(--wash);position:sticky;top:0}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}pre{{overflow:auto;background:#11151b;color:#e7edf5;padding:16px;border-radius:10px}}.scroll{{overflow:auto}}.badge{{display:inline-block;background:#eee8ff;color:#43208e;padding:3px 9px;border-radius:999px}}
</style></head><body><main>
<h1>{html.escape(title)}</h1><p class="lede"><span class="badge">Temperamento</span> {data["instruction_count"]} instructions · {data["ignored_base_event_count"]} ignored Base events · {html.escape(source_label)}</p>
<section><h2>Score-to-program map</h2><div class="scroll"><table><thead><tr><th>Command</th><th>Measure</th><th>Beat</th><th>Base relation</th><th>Cell</th><th>Opcode</th><th>Operand</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>
{ignored_html}
<section><h2>Canonical TOScript Core</h2><pre>{html.escape(data["toscript"])}</pre></section>
{trace_html}
</main></body></html>"""


def write_inspection(
    program: Program,
    destination: str | Path,
    *,
    execute: bool = True,
    max_steps: int = 100_000,
) -> Path:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(
        inspect_html(inspect_data(program, execute=execute, max_steps=max_steps)),
        encoding="utf-8",
    )
    return destination_path
