# Showcase and examples

## Showcase works

### Hello, World! Prelude

Outputs Unicode code points through ordinary `PUSH` and `OUT` instructions. No string opcode was added merely to support the demonstration.

### Conditional Canon

Exercises equality, conditional jump, unconditional jump, and labels. The committed execution-sonification WAV follows the actually executed instruction path; the ordinary WAV represents the notated score independently of runtime control flow.

### Countdown Étude

Uses stack duplication, output, subtraction, conditional jumping, and cleanup to emit `3, 2, 1`.

### Hanoi Three-Disc Study

Emits the fixed move sequence:

```text
A-C
A-B
C-B
A-C
B-A
B-C
A-C
```

This is a solution encoded as an executable composition, not a general solver.

### Twelve Transpositions

Twelve committed MusicXML variants use all chromatic transpositions and altered voicings. Each compiles to byte-identical TOScript and emits `12`.

## Media package

Showcase directories contain:

- MusicXML and compressed MXL;
- canonical TOScript;
- expected numeric and, where applicable, text output;
- MIDI;
- deterministic reference-synth WAV;
- execution-sonification WAV;
- SVG and PDF score/program maps;
- self-contained HTML inspection;
- annotated command table; and
- a local README.

MuseScore Studio can additionally create native MSCZ and its own engraving/audio exports.

## Tutorial ladder

The `examples/tutorial/` sequence introduces:

1. push and output;
2. Boolean negation;
3. equality;
4. repeated addition; and
5. triangular-number accumulation.

Existing technical examples remain under `arithmetic/`, `conditional/`, and `iteration/` for reproducibility.
