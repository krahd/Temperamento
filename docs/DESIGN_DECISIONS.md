# Design decisions

This record explains the decisions that materially shaped the current artefact.

## Ordered pairs, not sliding chord relations

Recognised computational Base triads are consumed in non-overlapping pairs. A sliding interpretation would make three triads yield two instructions, couple neighbouring commands, and complicate local editing. Pairing makes each command window explicit and independently testable.

## Ignored is not invalid

A Base onset is computational only when its pitch classes form an exact major or minor triad. Every other supported, well-formed Base event is ignored before pairing and retained in diagnostics.

This is not a claim that a dyad, suspended chord, seventh chord, cluster, incomplete voicing, or ambiguous collection is musically deficient. It states only that the deterministic kernel declines to read it. The previous behaviour incorrectly converted the boundary of the computational alphabet into a judgement about harmonic validity.

## No hidden harmonic analysis

The compiler does not infer a nearest chord, use surrounding context to choose a root, or resolve multiple conventional labels. C–F–G may be read as `Csus4` or `Fsus2/C`; either reading is musically available, but neither affects compilation.

Context-sensitive harmonic inference would make program meaning depend on an unstated analytical model and could cause local musical edits to alter distant instructions. Alternative and polysemic semantics remain future experimental layers, separate from the deterministic Core.

## Ignored events do not alter pairing

Noncomputational Base events are removed before recognised triads are paired. They may occur before, between, or after computational triads without splitting command windows. This permits a broader supported score surface while preserving a reproducible program projection.

Because an accidentally omitted or added chord tone can move an onset into or out of the computational alphabet, ignored events must be visible in inspection reports. Silence from the compiler would conceal consequential mistakes and erase the machine's selective reading. Inserting or removing an exact recognised triad changes subsequent non-overlapping pairing; the semantics deliberately expose rather than conceal that fragility.

## Relation and operation are separate

The 48 harmonic cells exist independently of the command table. This prevents the implementation from presenting a contingent command assignment as if it were inherent in the harmonic instruction space. Reserved cells are recognised and rejected.

## Root-relative operands

The initial design encoded Voice values as absolute pitch classes. That preserved Base opcodes under transposition but changed operands, making the whole-program invariance claim false. `v0.2.0` changed payload digits to `(voice_pitch - first_root) mod 12`. This was a semantic correction, not a cosmetic refactor.

## Duration as a length prefix

Operand length is carried by the header-note duration rather than by a special delimiter pitch. This keeps framing inside musical notation while producing a finite deterministic parse. The current unit is the quarter note and the duration must be a positive integer.

## Simultaneous Voice material is ignored

A Voice onset containing more than one note is excluded from computation. This leaves some polyphonic material available for musical purposes without introducing chord semantics into the operand channel. Singleton computational notes must remain non-overlapping. Adding a second note to an otherwise computational singleton removes that onset from decoding, so inspection and authoring tools must make the boundary visible.

## Restricted MusicXML rather than permissive guessing

MusicXML permits many notationally equivalent and structurally complex forms. The reference parser accepts only the subset whose structural meaning is specified. Malformed or unsupported representation remains an error; supported musical material outside the computational alphabet does not.

## One part and two staves

The current implementation requires one part with Voice on staff 1 and Base on staff 2. This choice reduces part-merging and timing ambiguity while the central relation is evaluated. It is a research boundary, not a claim that future Temperamento scores must use one instrument.

## Exact score time, conventional numeric runtime

Score timing uses `Fraction`, avoiding rounding during parsing. Runtime division currently uses Python floating-point values. The universality construction uses only natural-number operations and does not depend on division or floating-point behaviour.

## `SWAP` completes a constructive universal kernel

`SWAP` is assigned to cell `2mm`. It exchanges the top two stack values without changing stack depth. Together with the existing arithmetic, comparison, labels, and jumps, it permits an explicit simulation of a deterministic two-counter machine while maintaining counters as stack pair `(c1, c2)`.

The repository includes the translator, executable tests, and a proof sketch. This is stronger than asserting that branching plus an unbounded stack “looks universal,” but it is not a mechanically verified proof. See [`UNIVERSALITY.md`](UNIVERSALITY.md).

## Idealised universality, bounded implementation

Turing completeness applies to the language's idealised semantics with unbounded natural numbers, stack capacity, output capacity, program size, and execution. The reference interpreter retains configurable step, stack, output, integer-magnitude, and trace budgets and remains limited by physical memory. This distinction is explicit rather than concealed.

Computational universality is a formal property of the idealised core, not a measure of artistic value.

## MuseScore converter integration before a plugin

The alpha uses MuseScore Studio's documented converter mode instead of a QML plugin. This provides native-score input and media export while keeping language semantics in one Python implementation. A future plugin should navigate diagnostics and invoke the CLI/API; it should not reimplement the compiler.

## HTML inspection before a desktop GUI

The pre-release needs understandable source mapping more urgently than another notation editor. A self-contained report provides measure/beat diagnostics, ignored Base events, decoded instructions, and bounded execution traces while MuseScore continues to provide note entry and engraving.

## Text output as presentation, not a new opcode

`--output text` interprets emitted non-negative integers as Unicode scalar values. TOScript Core still emits numbers; the Hello World example does not force strings into the language semantics.

## Fixed Hanoi study before a general solver

The alpha includes a seven-move three-disc solution because it is a useful executable composition. The universal kernel makes a general solver expressible, but that claim belongs to a future committed score and validation package rather than being inferred from the fixed study.
