# Troubleshooting

## MuseScore Studio was not found

Run `temperamento doctor`. Add the executable to `PATH`, set `TEMPERAMENTO_MUSESCORE`, or pass `--musescore`.

## A native MSCZ file fails before compilation

Run the equivalent MuseScore export manually:

```bash
mscore -o debug.musicxml piece.mscz
```

If MuseScore cannot produce the file, the problem is in the native score or installation. If it can, run `temperamento validate debug.musicxml` to isolate the Temperamento subset error.

## The score is valid MusicXML but rejected

Temperamento intentionally rejects ambiguous or unsupported notation. Common causes include:

- more than one part;
- a staff count other than two;
- multiple MusicXML voices on one staff;
- tied notes;
- unsupported Base sonorities;
- overlapping Voice operands;
- reserved harmonic cells; or
- missing or surplus operand notes.

Use `temperamento inspect` where compilation succeeds and read the measure/beat context in errors where it fails.

## Text output fails

`--output text` requires each emitted value to be a valid Unicode scalar integer. Use the default JSON output to inspect floats, negative values, or out-of-range values.

## Committed audio sounds synthetic

The committed WAV is deliberately a deterministic dependency-light reference render. Use `temperamento render ... --formats wav` with MuseScore Studio for its installed sound profile.

## The Hanoi example is not general

Correct. It emits a fixed seven-move solution. The language does not yet include addressable memory or procedures required by the planned general solver.
