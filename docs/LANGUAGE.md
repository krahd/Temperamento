# Language guide

This document explains the implemented `v0.5.0-alpha.1` language. The normative score constraints are in [`spec/grammar.ebnf`](../spec/grammar.ebnf), [`spec/semantic-subset.md`](../spec/semantic-subset.md), and [`spec/opcode-table.json`](../spec/opcode-table.json).

## Representation chain

Temperamento currently implements:

```text
TOScript+ ↔ TOScript Core ↔ MusicXML / MXL
```

TOScript Core is the canonical executable representation. The conversions are semantic and canonical, not source-preserving bijections:

- TOScript+ lowers to Core; Core can be printed as canonical TOScript+.
- MusicXML/MXL compiles to Core; Core can be realised as canonical MusicXML.
- Recompiling generated MusicXML must recover byte-identical Core.
- Comments, symbolic label spelling, source layout, voicing, engraving, and noncomputational musical material are not recovered by canonical reverse conversion.

## TOScript Core

TOScript Core files use the `.tos` suffix. Each non-empty line contains one opcode and its required non-negative integer operand, if any. `#` begins a comment outside quoted text. Opcode names are case-insensitive on input and uppercase in canonical output.

```text
PUSH 3
LBL 1
DUP
OUT
PUSH 1
SUB
DUP
JMC 1
POP
END
```

Parsing validates opcode names, arity, non-negative operands, duplicate labels, undefined jump targets, source size, and expanded instruction count.

## TOScript+

TOScript+ files use `.tom`, `.tos+`, or `.tosplus`. The current alpha implements a deliberately small ergonomic subset that lowers completely to TOScript Core:

- `#` comments;
- `let NAME = INTEGER` compile-time constants;
- symbolic or numeric labels written as `name:` or `label name`;
- `jump name` and `jump-if name`;
- lowercase Core operations;
- `output` for `OUT`;
- `output VALUE` for `PUSH VALUE` followed by `OUT`; and
- `print "text"` for Unicode scalar `PUSH`/`OUT` pairs.

Example:

```text
let start = 3
push start
loop:
dup
output
push 1
sub
dup
jump-if loop
pop
end
```

Symbolic labels are assigned deterministic non-negative numeric labels in first-definition order while avoiding explicitly used numeric labels. Canonical lifting from Core uses numeric labels so that lowering the result recovers byte-identical Core.

This subset does not yet implement the complete historical TOScript+ design: runtime variables, arrays, procedures, functions, or expanded value types remain outside the alpha.

## Core to score notation

`temperamento score` writes a deterministic two-stave MusicXML realisation of any supported source. Each Core instruction receives one measure, an instruction label above the Voice staff, an ordered Base-triad pair, and any required duration-framed Voice operands. Optional global transposition, reversed voicing, root doubling, and ignored decorative Base notes test the invariances of the computational projection.

The generated score is canonical evidence of one valid realisation. It does not attempt to reconstruct an author's original score, voicing, layout, or noncomputational material.

## Two staves, two computational roles

Temperamento accepts one MusicXML `score-partwise` part containing exactly two declared staves and at most one MusicXML voice per staff:

- **Voice** — staff 1; encodes immediate operands.
- **Base** — staff 2; contains computational triads and supported noncomputational musical material.

Score time, not XML serialization order, determines instruction order. Tied-note semantics, unrestricted parts, unrestricted voices, and general polyphony are outside the reference subset.

## Base: a computational alphabet inside a musical score

Within the supported source subset, a Base onset is computational if and only if its simultaneous pitch-class set is exactly a major or minor triad. Inversion, register, note order, and repeated chord tones do not change the recognised root or mode.

Every other supported, well-formed Base onset is valid musical material but noncomputational. Single notes, dyads, suspended chords, seventh chords, added-note chords, diminished and augmented structures, clusters, incomplete or rootless voicings, and other pitch collections are ignored before computational triads are paired. They remain present in the score and are retained in inspection diagnostics.

Temperamento does not perform contextual harmonic analysis or choose a preferred chord symbol. For example, the pitch collection C–F–G with C in the bass may be heard or labelled as `Csus4` or `Fsus2/C`; the compiler records its pitches and declines to select either interpretation.

Recognised computational triads are ordered by onset and consumed in non-overlapping pairs:

```text
(C0, C1), (C2, C3), ...
```

Ignored Base events do not split a pair, create a command boundary, or change subsequent pairing. Conversely, inserting or removing an exact recognised triad changes pairing and may therefore change the program; this is a deliberate consequence of the projection, not contextual harmony analysis.

For roots `r1` and `r2`, the clockwise circle-of-fifths distance is:

```text
d = 7 * (r2 - r1) mod 12
```

Together with the initial and final modes, this gives a cell:

```text
(d, initial_mode, final_mode)
```

There are `12 × 2 × 2 = 48` cells. Seventeen are assigned in TOScript Core; thirty-one remain explicitly reserved and are rejected when selected by a recognised chord pair.

## Voice: operands relative to harmony

Each assigned opcode declares how many operands it expects. Computational Voice notes occur strictly between the two Base-triad onsets defining the command.

An operand consists of:

1. a header note whose duration is a positive integer `n` in quarter-note units; and
2. exactly `n` non-overlapping payload notes.

For a payload pitch class `v` and the first Base-triad root `r`, the digit is:

```text
digit = (v - r) mod 12
```

Payload digits are decoded most significant first as a non-negative base-12 integer. The header pitch does not matter.

Simultaneous Voice onsets are treated as noncomputational musical material and ignored. Adding a second note to an otherwise singleton computational Voice onset therefore removes that entire onset from operand decoding. Singleton computational notes may not overlap or cross the end of the command window.

## Why transposition preserves the program

Transposing both Base roots by `k` preserves their difference:

```text
(r2 + k) - (r1 + k) = r2 - r1
```

Transposing a Voice payload and its reference root also preserves their relative pitch class:

```text
(v + k) - (r + k) = v - r
```

Both the operation and every operand therefore remain unchanged. Within the computational subset, the compiled TOScript Core is byte-identical after global chromatic transposition.

## TOScript Core operations

| Cell | Operation | Stack behaviour / operand |
|---|---|---|
| `0MM` | `ADD` | pop `y`, `x`; push `x + y` |
| `1MM` | `SUB` | pop `y`, `x`; push `x - y` |
| `2MM` | `MUL` | pop `y`, `x`; push `x * y` |
| `3MM` | `DIV` | pop `y`, `x`; push `x / y` |
| `4MM` | `NOT` | zero becomes `1`; non-zero becomes `0` |
| `5MM` | `PUSH n` | push non-negative integer `n` |
| `6MM` | `POP` | discard top value |
| `7MM` | `DUP` | duplicate the top value |
| `8MM` | `AND` | Boolean conjunction |
| `9MM` | `OR` | Boolean disjunction |
| `10MM` | `EQ` | equality test |
| `11MM` | `LBL n` | declare a numeric jump label |
| `0mm` | `JMC n` | pop condition; jump to `n` when non-zero |
| `1mm` | `JMP n` | unconditional jump |
| `2mm` | `SWAP` | exchange the top two stack values |
| `4mm` | `END` | terminate execution |
| `8mm` | `OUT` | pop and append value to output |

False is zero; true is any non-zero value. Binary operations pop the right operand before the left. Division produces a Python floating-point value in the reference interpreter.

## Computational universality

The idealised TOScript Core uses unbounded natural-number values, an unbounded stack, unbounded output and program size, and unbounded execution. With `SWAP`, it can simulate any deterministic two-counter machine while representing its counters as the bottom-to-top stack pair `(c1, c2)`. The repository includes the constructive translator in [`src/temperamento/universality.py`](../src/temperamento/universality.py), executable tests, and the proof in [`docs/UNIVERSALITY.md`](UNIVERSALITY.md).

The reference interpreter retains configurable finite step, stack, output, integer-magnitude, and trace budgets and is necessarily limited by host resources. These safeguards bound a particular execution, not the abstract language semantics.

## Static errors

Compilation or parsing rejects, among other conditions:

- malformed or unsupported MusicXML structures, including tied-note computational semantics;
- malformed or unsafe `.mxl` containers;
- entity declarations and unsafe or excessive source structures;
- unknown textual operations, wrong arity, negative operands, duplicate labels, and undefined labels;
- no recognised computational Base triads or an odd number of recognised computational triads;
- reserved harmonic cells;
- overlapping or boundary-crossing computational Voice notes; and
- missing, truncated, or surplus operands.

A supported, well-formed nontriadic Base sonority is not a static error. It is ignored computationally and reported by inspection.

## Runtime faults

Execution rejects malformed instruction objects and reports stack underflow, division by zero, non-finite arithmetic, undefined control flow, and exhaustion of configured step, stack, output, integer-magnitude, or trace budgets as user-facing runtime faults.

## External notation and sound tools

MuseScore Studio or another notation application may turn MusicXML into engraved sheets and playback files. The parser accepts the standard external `score-partwise` MusicXML DOCTYPE emitted by MuseScore while rejecting entity declarations. Sound-to-score systems may produce MusicXML that Temperamento can subsequently validate and compile. Neither engraving, playback, nor audio transcription changes Temperamento's canonical semantic boundary; sound-to-score is not claimed to be deterministic or invertible.
