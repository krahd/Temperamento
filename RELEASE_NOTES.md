# Temperamento v0.5.0

This release separates the deterministic computational alphabet from the broader supported score material and adds the minimal stack operation needed for a constructive universality result.

## Semantic changes

- A Base onset is computational only when its pitch classes form an exact major or minor triad.
- Every other supported, well-formed Base event is ignored before computational triads are paired.
- Ignored events remain in the score and are exposed in text, JSON, and HTML inspection reports.
- The compiler performs no contextual chord analysis and does not select among alternative labels. C–F–G, for example, remains noncomputational rather than being forced into `Csus4` or `Fsus2/C`.
- Errors are reserved for unsupported or malformed representation, malformed program structure, reserved cells, invalid operands, configured resource exhaustion, and runtime faults.

## Universal core

- Harmonic cell `2mm` now denotes `SWAP`.
- TOScript Core has seventeen assigned cells and thirty-one reserved cells.
- The `temperamento.universality` module constructively translates deterministic two-counter machines into TOScript Core.
- Executable tests verify increment, zero-test, decrement, control transfer, counter ordering, complete counter-transfer behaviour, and malformed machine definitions.
- The idealised Core is Turing-complete under unbounded natural-number, stack, output, program-size, and execution semantics.
- The reference interpreter remains physically bounded and uses configurable step, stack, output, integer-magnitude, and trace budgets.

## Interoperability and safety

- The standard external `score-partwise` MusicXML 4.0 DOCTYPE emitted by MuseScore Studio is accepted; entity declarations and other DTDs remain rejected.
- MusicXML, MXL, TOScript, and TOScript+ inputs have explicit size and structural limits.
- MXL path, duplicate-entry, archive-size, entry-count, XML-size, measure-count, and note-event boundaries are validated.
- Project scaffolding no longer deletes unrelated files under `--force`; native MuseScore creation is explicit.
- MuseScore exports reject source/destination aliasing, symbolic-link destinations, and non-file destinations.
- Reverse notation validates opcode/cell consistency before writing a score.

## Example and release artefacts

- Direction-specific packages record exact primary, lowered, canonical, round-trip, and presentation roles.
- Deterministic printable maps, MIDI, reference audio, execution audio, inspection HTML, MusicXML, and MXL are committed.
- The checksum-pinned MuseScore workflow produces and round-trip verifies editable MSCZ, engraved PDF, and MP3 playback outputs.
- Release ZIP and TAR archives use the current version and deterministic timestamps, ownership, permissions, ordering, and compression metadata.
