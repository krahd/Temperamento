# Temperamento v0.5.0-alpha.1 reference semantics

## Source model

The reference implementation accepts uncompressed MusicXML and zip-based `.mxl` archives containing `score-partwise` MusicXML. The supported subset has exactly one part, attributes declaring exactly two staves, and at most one MusicXML voice per staff. Staff 1 is **Voice** and staff 2 is **Base**. Rational score time reconstructed from notes, `forward`, and `backup` elements determines execution order; XML serialization order does not.

For compressed MusicXML, `META-INF/container.xml` must identify at least one rootfile. Following MusicXML 4.0, the first rootfile is treated as the score entry point and later rootfiles may describe alternate renditions such as PDF or audio. The first rootfile must have no media type or a MusicXML media type. Duplicate, missing, directory, absolute, parent-traversing, or otherwise unsafe score entries are rejected.

The parser accepts a standard external `score-partwise` MusicXML DOCTYPE, including the declaration emitted by MuseScore Studio, but rejects entity declarations and does not resolve external DTD content. It also rejects tied notes, malformed or non-positive timing values, oversized XML or archive inputs, excessive archive entries, excessive measure or note-event counts, unsupported part structures, changing staff counts, and ambiguous chord-member sequences. These are representation or source-structure errors, not judgements about harmonic validity.

## Base: computational triads and ignored musical material

Within the supported source subset, a Base onset is computational if and only if its simultaneous pitch-class set contains exactly the three distinct pitch classes of a major or minor triad. Inversion, register, XML note order, and octave doubling do not affect recognition.

Every other supported, well-formed Base onset is noncomputational. Its distinct pitch classes, note count, score time, measure, and beat are retained as an ignored Base event. It does not cause a static error, does not become a command boundary, and does not affect pairing.

The compiler performs no contextual chord-symbol inference. A pitch collection such as C–F–G may permit multiple conventional readings, including `Csus4` and `Fsus2/C`; no reading is selected by the computational semantics.

Recognised computational triads are sorted by onset after noncomputational events have been filtered out, then consumed in non-overlapping pairs. For roots `r1`, `r2` and modes `m1`, `m2`, a pair denotes:

```text
(7 * (r2 - r1) mod 12, m1, m2)
```

The product `Z12 × {M,m} × {M,m}` contains forty-eight cells. Seventeen cells are assigned in TOScript Core and thirty-one are explicitly `RESERVED`; a reserved cell selected by a recognised pair is rejected statically.

For every chromatic transposition `k`:

```text
7 * ((r2 + k) - (r1 + k)) mod 12 = 7 * (r2 - r1) mod 12
```

The harmonic cell is therefore invariant when both chords are transposed and their modes are preserved.

## Voice: relative operands

Each opcode has a fixed arity and operand signature. Its computational Voice material lies strictly between the onsets of the two recognised Base triads defining the instruction.

Voice onsets containing more than one note are ignored computationally. The remaining singleton notes are read in time order and must not overlap or extend beyond the final triad onset.

Each operand begins with a header note. Its duration, measured in quarter-note units, is a positive integer `n` declaring exactly `n` subsequent payload notes. For the first Base-triad root `r` and payload-note pitch class `v`, the payload digit is:

```text
digit = (v - r) mod 12
```

Digits are interpreted most significant first as a non-negative base-12 integer. The header pitch is semantically irrelevant. Missing headers, non-integral or non-positive lengths, truncated payloads, overlapping singleton notes, boundary-crossing notes, and surplus singleton material are static errors.

Because payload notes and the reference root move together, global transposition preserves operands:

```text
((v + k) - (r + k)) mod 12 = (v - r) mod 12
```

Combining this equality with harmonic-cell invariance gives whole-program transposition invariance for the documented computational subset.

## Static validation

Compilation rejects:

- scores without recognised computational Base triads or with an odd number of recognised computational Base triads;
- recognised pairs selecting reserved harmonic cells;
- Voice material inconsistent with the opcode signature or command window;
- duplicate numeric labels; and
- jumps to undefined labels.

Supported nontriadic Base material is not rejected. Errors identify the command number and score time when possible. The output is an immutable instruction sequence, ignored-Base-event sequence, and canonical TOScript Core rendering.

## Machine state and execution

A machine configuration is `⟨pc, S, O, L⟩`, where `pc` is the program counter, `S` the numeric stack, `O` the output sequence, and `L` the pre-resolved label map. Operands and labels are non-negative integers. Runtime values are Python integers or, after division, floating-point numbers.

Binary operations pop the right operand and then the left operand. False is zero and true is any non-zero value. `SWAP` exchanges the top two stack values. `JMC` consumes its condition. `OUT` consumes the value it emits. `END` terminates; reaching the end of the instruction stream also terminates. Invalid instruction objects, stack underflow, division by zero, non-finite arithmetic, and exhaustion of configured step, stack, output, integer-magnitude, or trace budgets are runtime faults.

## Idealised universal semantics

For the universality result, restrict values to natural numbers and idealise integer magnitude, stack capacity, program size, output capacity, trace storage, and execution as unbounded. Under these semantics, `SWAP` together with the existing stack, arithmetic, comparison, label, and jump operations constructively simulates deterministic two-counter machines. The translator and proof obligations are specified in [`../docs/UNIVERSALITY.md`](../docs/UNIVERSALITY.md).

The finite resource budgets and physical memory of the Python interpreter constrain implementations, not the abstract language semantics.
