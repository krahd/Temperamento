from __future__ import annotations

import html
import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.generate_examples import SourceInstruction, build_score
from temperamento.compiler import compile_musicxml
from temperamento.inspection import inspect_data, inspect_html
from temperamento.interpreter import Interpreter
from temperamento.musicxml import parse_musicxml
from temperamento.project import write_mxl


def output_program(text: str) -> list[SourceInstruction]:
    instructions: list[SourceInstruction] = []
    for character in text:
        instructions.append(SourceInstruction("5MM", (ord(character),)))
        instructions.append(SourceInstruction("8mm"))
    instructions.append(SourceInstruction("4mm"))
    return instructions


def variable_length(value: int) -> bytes:
    buffer = value & 0x7F
    encoded = bytearray([buffer])
    while value >> 7:
        value >>= 7
        buffer = (value & 0x7F) | 0x80
        encoded.insert(0, buffer)
    return bytes(encoded)


def write_midi(source: Path, destination: Path) -> None:
    ticks_per_quarter = 480
    events: list[tuple[int, int, bytes]] = []
    for note in parse_musicxml(source):
        midi_note = max(0, min(127, note.pitch_class + 12 * (note.octave + 1)))
        start = round(float(note.onset) * ticks_per_quarter)
        end = round(float(note.onset + note.duration) * ticks_per_quarter)
        channel = 0 if note.staff == 1 else 1
        velocity = 72 if note.staff == 1 else 58
        events.append((start, 1, bytes([0x90 | channel, midi_note, velocity])))
        events.append((end, 0, bytes([0x80 | channel, midi_note, 0])))
    events.sort(key=lambda item: (item[0], item[1]))
    track = bytearray()
    track.extend(variable_length(0) + b"\xff\x51\x03\x07\xa1\x20")
    previous = 0
    for tick, _, payload in events:
        track.extend(variable_length(tick - previous))
        track.extend(payload)
        previous = tick
    track.extend(variable_length(0) + b"\xff\x2f\x00")
    destination.write_bytes(
        b"MThd"
        + struct.pack(">IHHH", 6, 0, 1, ticks_per_quarter)
        + b"MTrk"
        + struct.pack(">I", len(track))
        + bytes(track)
    )


def write_wav(source: Path, destination: Path) -> None:
    events = parse_musicxml(source)
    rate = 22_050
    seconds_per_quarter = 0.13
    total_seconds = (
        max(float(event.onset + event.duration) for event in events) * seconds_per_quarter + 0.2
    )
    samples = [0.0] * max(1, int(total_seconds * rate))
    for event in events:
        start = int(float(event.onset) * seconds_per_quarter * rate)
        duration = max(1, int(float(event.duration) * seconds_per_quarter * rate))
        midi_note = event.pitch_class + 12 * (event.octave + 1)
        frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
        amplitude = 0.12 if event.staff == 1 else 0.08
        for index in range(duration):
            position = start + index
            if position >= len(samples):
                break
            envelope = min(1.0, index / max(1, int(rate * 0.01)))
            envelope *= min(1.0, (duration - index) / max(1, int(rate * 0.03)))
            samples[position] += (
                amplitude * envelope * math.sin(2 * math.pi * frequency * index / rate)
            )
    peak = max(1.0, max(abs(value) for value in samples))
    frames = b"".join(
        struct.pack("<h", int(max(-1, min(1, value / peak)) * 32767)) for value in samples
    )
    with wave.open(str(destination), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(frames)


def write_execution_wav(program, destination: Path) -> None:
    result = Interpreter().run(program, capture_trace=True)
    rate = 22_050
    tone_seconds = 0.11
    gap_seconds = 0.025
    tone_samples = int(tone_seconds * rate)
    gap_samples = int(gap_seconds * rate)
    samples: list[float] = []
    opcode_index = {
        name: index for index, name in enumerate(sorted({step.opcode for step in result.trace}))
    }
    for step in result.trace:
        frequency = 220.0 * (2 ** (opcode_index[step.opcode] / 12))
        for index in range(tone_samples):
            envelope = math.sin(math.pi * index / max(1, tone_samples - 1)) ** 2
            samples.append(0.25 * envelope * math.sin(2 * math.pi * frequency * index / rate))
        samples.extend([0.0] * gap_samples)
    frames = b"".join(struct.pack("<h", int(value * 32767)) for value in samples)
    with wave.open(str(destination), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(frames)


def write_svg(title: str, program_text: str, destination: Path) -> None:
    lines = program_text.strip().splitlines()
    width = 1200
    row_height = 32
    height = max(260, 150 + len(lines) * row_height)
    rows = []
    for index, line in enumerate(lines):
        y = 118 + index * row_height
        shade = "#f1edff" if index % 2 == 0 else "#ffffff"
        rows.append(f'<rect x="70" y="{y - 22}" width="1060" height="28" rx="5" fill="{shade}"/>')
        rows.append(f'<text x="88" y="{y}" class="mono">{index + 1:02d}</text>')
        rows.append(f'<text x="142" y="{y}" class="mono strong">{html.escape(line)}</text>')
    destination.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 34px system-ui,sans-serif;fill:#17141f}}.sub{{font:18px system-ui,sans-serif;fill:#666171}}.mono{{font:17px ui-monospace,monospace;fill:#504b5c}}.strong{{font-weight:700;fill:#2d1b64}}</style>
<rect width="100%" height="100%" fill="#faf9fc"/><text x="70" y="56" class="title">{html.escape(title)}</text>
<text x="70" y="84" class="sub">Executable score · canonical TOScript Core map</text>{"".join(rows)}</svg>''',
        encoding="utf-8",
    )


def write_pdf(title: str, program_text: str, destination: Path) -> None:
    page = landscape(A4)
    document = canvas.Canvas(str(destination), pagesize=page, invariant=1)
    _, height = page
    document.setTitle(title)
    document.setFont("Helvetica-Bold", 22)
    document.drawString(42, height - 45, title)
    document.setFont("Helvetica", 10)
    document.drawString(42, height - 64, "Executable score · canonical TOScript Core map")
    y = height - 92
    document.setFont("Courier", 8.5)
    for index, line in enumerate(program_text.strip().splitlines(), start=1):
        if y < 42:
            document.showPage()
            document.setFont("Courier", 8.5)
            y = height - 42
        document.drawString(45, y, f"{index:03d}  {line}")
        y -= 12
    document.save()


def write_walkthrough(destination_gif: Path, destination_mp4: Path) -> None:
    slides = [
        ("Temperamento v0.4.0-alpha", "Write programs as two-stave musical scores"),
        ("Base → operations", "Ordered major/minor triad pairs select instructions"),
        ("Voice → operands", "Duration-framed pitch classes encode relative base-12 values"),
        ("MuseScore workflow", "Edit → validate → inspect → run → render"),
        (
            "Executable compositions",
            "Hello, World! · Twelve Transpositions · Conditional Canon · Hanoi Study",
        ),
    ]
    images: list[Image.Image] = []
    font = ImageFont.load_default(size=28)
    small = ImageFont.load_default(size=18)
    for heading, body in slides:
        image = Image.new("RGB", (960, 540), "#f8f6fc")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((50, 50, 910, 490), 24, fill="#ffffff", outline="#d7cfee", width=3)
        draw.text((90, 150), heading, font=font, fill="#29175b")
        draw.multiline_text((90, 230), body, font=small, fill="#4e4858", spacing=10)
        images.append(image)
    images[0].save(destination_gif, save_all=True, append_images=images[1:], duration=1800, loop=0)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        with subprocess.Popen(
            [
                ffmpeg,
                "-y",
                "-f",
                "gif",
                "-i",
                str(destination_gif),
                "-pix_fmt",
                "yuv420p",
                str(destination_mp4),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) as process:
            if process.wait() != 0:
                raise RuntimeError("ffmpeg could not generate the walkthrough video")


def write_composition(
    relative: str,
    title: str,
    instructions: list[SourceInstruction],
    *,
    output_text: str | None = None,
    transpose: int = 0,
) -> Path:
    directory = ROOT / "examples" / relative
    directory.mkdir(parents=True, exist_ok=True)
    name = directory.name
    musicxml = directory / f"{name}.musicxml"
    build_score(
        instructions,
        transpose=transpose,
        reverse_voicing=bool(transpose % 2),
        double_roots=bool(transpose % 3),
        title=title,
        decorative_base_line=True,
    ).write(musicxml, encoding="utf-8", xml_declaration=True)
    program = compile_musicxml(musicxml)
    result = Interpreter().run(program)
    (directory / f"{name}.tos").write_text(program.to_tos(), encoding="utf-8")
    (directory / "expected-output.json").write_text(
        json.dumps({"output": list(result.output), "steps": result.steps}, indent=2) + "\n",
        encoding="utf-8",
    )
    if output_text is not None:
        (directory / "expected-output.txt").write_text(output_text, encoding="utf-8")
    write_mxl(musicxml, directory / f"{name}.mxl")
    write_midi(musicxml, directory / f"{name}.mid")
    write_wav(musicxml, directory / f"{name}-reference.wav")
    write_execution_wav(program, directory / f"{name}-execution.wav")
    write_svg(title, program.to_tos(), directory / f"{name}-map.svg")
    write_pdf(title, program.to_tos(), directory / f"{name}-map.pdf")
    (directory / f"{name}.html").write_text(
        inspect_html(inspect_data(program, execute=True), title=title), encoding="utf-8"
    )
    records = inspect_data(program)["instructions"]
    table = "\n".join(
        f"| {row['command']} | {row['measure']} | {row['beat']} | {row['base_relation']} | `{row['cell']}` | `{row['toscript']}` |"
        for row in records
    )
    (directory / "ANNOTATED.md").write_text(
        f"# {title}: score/program map\n\n| Command | Measure | Beat | Base relation | Cell | Instruction |\n"
        "|---:|---:|---:|---|---|---|\n" + table + "\n",
        encoding="utf-8",
    )
    (directory / "README.md").write_text(
        f"# {title}\n\nA committed executable composition for Temperamento.\n\n"
        f"```bash\ntemperamento validate {name}.musicxml\n"
        f"temperamento inspect {name}.musicxml --execute\n"
        f"temperamento run {name}.musicxml"
        + (" --output text" if output_text is not None else "")
        + "\n```\n\nFiles include MusicXML/MXL source, canonical TOScript, MIDI, deterministic reference audio, PDF/SVG program maps, HTML inspection, expected output, and an annotated map. "
        "The release workflow additionally commits native `.mscz` files and MuseScore-rendered PDF, SVG, and WAV media.\n",
        encoding="utf-8",
    )
    return directory


def main() -> None:
    # Introductory examples.
    write_composition(
        "tutorial/01-push-output",
        "Push and Output",
        [SourceInstruction("5MM", (42,)), SourceInstruction("8mm"), SourceInstruction("4mm")],
    )
    write_composition(
        "tutorial/02-boolean-not",
        "Boolean Not",
        [
            SourceInstruction("5MM", (0,)),
            SourceInstruction("4MM"),
            SourceInstruction("8mm"),
            SourceInstruction("4mm"),
        ],
    )
    write_composition(
        "tutorial/03-comparison",
        "Equality",
        [
            SourceInstruction("5MM", (4,)),
            SourceInstruction("5MM", (4,)),
            SourceInstruction("10MM"),
            SourceInstruction("8mm"),
            SourceInstruction("4mm"),
        ],
    )
    write_composition(
        "tutorial/04-repeated-addition",
        "Repeated Addition",
        [
            SourceInstruction("5MM", (3,)),
            SourceInstruction("5MM", (3,)),
            SourceInstruction("0MM"),
            SourceInstruction("5MM", (3,)),
            SourceInstruction("0MM"),
            SourceInstruction("5MM", (3,)),
            SourceInstruction("0MM"),
            SourceInstruction("8mm"),
            SourceInstruction("4mm"),
        ],
    )
    write_composition(
        "tutorial/05-triangular-five",
        "Triangular Five",
        [
            SourceInstruction("5MM", (1,)),
            SourceInstruction("5MM", (2,)),
            SourceInstruction("0MM"),
            SourceInstruction("5MM", (3,)),
            SourceInstruction("0MM"),
            SourceInstruction("5MM", (4,)),
            SourceInstruction("0MM"),
            SourceInstruction("5MM", (5,)),
            SourceInstruction("0MM"),
            SourceInstruction("8mm"),
            SourceInstruction("4mm"),
        ],
    )

    hello = "Hello, World!\n"
    write_composition(
        "showcase/hello-world-prelude",
        "Hello, World! Prelude",
        output_program(hello),
        output_text=hello,
    )

    countdown = [
        SourceInstruction("5MM", (3,)),
        SourceInstruction("11MM", (1,)),
        SourceInstruction("7MM"),
        SourceInstruction("8mm"),
        SourceInstruction("5MM", (1,)),
        SourceInstruction("1MM"),
        SourceInstruction("7MM"),
        SourceInstruction("0mm", (1,)),
        SourceInstruction("6MM"),
        SourceInstruction("4mm"),
    ]
    write_composition("showcase/countdown-etude", "Countdown Étude", countdown)

    conditional = [
        SourceInstruction("5MM", (7,)),
        SourceInstruction("5MM", (7,)),
        SourceInstruction("10MM"),
        SourceInstruction("0mm", (1,)),
        SourceInstruction("5MM", (0,)),
        SourceInstruction("8mm"),
        SourceInstruction("1mm", (2,)),
        SourceInstruction("11MM", (1,)),
        SourceInstruction("5MM", (1,)),
        SourceInstruction("8mm"),
        SourceInstruction("11MM", (2,)),
        SourceInstruction("4mm"),
    ]
    write_composition("showcase/conditional-canon", "Conditional Canon", conditional)

    hanoi = "A-C\nA-B\nC-B\nA-C\nB-A\nB-C\nA-C\n"
    write_composition(
        "showcase/hanoi-three-study",
        "Hanoi Three-Disc Study",
        output_program(hanoi),
        output_text=hanoi,
    )

    transpositions_root = ROOT / "examples" / "showcase" / "twelve-transpositions"
    transpositions_root.mkdir(parents=True, exist_ok=True)
    source_program = [
        SourceInstruction("5MM", (12,)),
        SourceInstruction("8mm"),
        SourceInstruction("4mm"),
    ]
    canonical: str | None = None
    for semitones in range(12):
        directory = write_composition(
            f"showcase/twelve-transpositions/key-{semitones:02d}",
            f"Twelve Transpositions: {semitones}",
            source_program,
            transpose=semitones,
        )
        current = (directory / f"{directory.name}.tos").read_text(encoding="utf-8")
        canonical = canonical or current
        if current != canonical:
            raise RuntimeError("transposition showcase is not byte-identical")
    (transpositions_root / "README.md").write_text(
        "# Twelve Transpositions\n\nThe twelve score variants use different chromatic transpositions and voicings, but every file compiles to the same canonical TOScript and outputs `12`.\n",
        encoding="utf-8",
    )

    assets = ROOT / "docs" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    write_walkthrough(
        assets / "temperamento-walkthrough.gif", assets / "temperamento-walkthrough.mp4"
    )


if __name__ == "__main__":
    main()
