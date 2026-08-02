# Project status

## Current state

Temperamento `v0.5.0` is a musician-facing and research-facing release extending the deterministic score language established in `v0.3.0` and the integrated environment introduced in `v0.4.0-alpha.1`.

The release provides:

- deterministic MusicXML/MXL compilation within a documented one-part, two-stave subset;
- native MuseScore Studio MSCX/MSCZ conversion;
- parsing and canonicalisation of TOScript Core;
- an initial TOScript+ authoring subset with comments, constants, named labels, branch sugar, numeric output, and string output;
- canonical TOScript+ lifting from any supported program source;
- deterministic TOScript Core to MusicXML notation, with byte-identical Core recovery from the generated score;
- a 48-cell harmonic instruction space with seventeen assigned core operations;
- exact major/minor computational triads embedded within supported noncomputational Base material;
- inspection diagnostics that preserve ignored Base events without assigning them a harmonic analysis;
- root-relative base-12 operands and whole-program chromatic-transposition invariance;
- a validated stack interpreter including `SWAP` and explicit resource budgets;
- a constructive translation from deterministic two-counter machines and a documented Turing-completeness argument for the idealised core;
- measure/beat source maps, bounded execution traces, text/JSON/HTML inspection, and a browser GUI;
- non-destructive project scaffolding and multi-format MuseScore rendering;
- tutorial programs, executable compositions, and direction-specific examples with score, program, media, output, manifest, and inspection artefacts; and
- cross-platform CI, package/release workflows, a documentation site, and reproducibility checks.

## Representation boundary

The implemented semantic chain is:

```text
TOScript+ ↔ TOScript Core ↔ MusicXML / MXL
```

These are canonical semantic conversions, not textual or visual bijections. TOScript+ lowers to Core and can be regenerated in a canonical form. MusicXML compiles to Core; Core can be realised as a canonical two-stave score whose recompilation recovers byte-identical Core. Original comments, symbolic label names, voicings, layout, engraving decisions, and noncomputational score material are not reconstructed by canonical reverse conversion.

MuseScore or another notation application remains responsible for score engraving and playback. Third-party sound-to-score transcription may feed MusicXML into Temperamento, but sound transcription is neither deterministic nor part of the language semantics.

## Release maturity

The release is suitable for:

- independent inspection of the programming-language mechanism and universality construction;
- authoring experiments in MuseScore Studio, TOScript Core, and the implemented TOScript+ subset;
- canonical score/text demonstrations and round-trip verification;
- demonstrations, workshops, teaching, and early external testing;
- reproducing the current release artefact; and
- composing within the documented restricted language.

It is a completed `v0.5.0` release, not a stable `1.0` language or production notation ecosystem. The Python API, score grammar, textual syntax, canonical notation, opcode assignments, and project layout may still change before `1.0`.

## Deliberately excluded

The current release does not implement or claim:

- all 48 opcode assignments;
- contextual chord recognition or a general harmonic-analysis system;
- computational semantics for extended, diminished, augmented, suspended, rootless, or ambiguous harmonies;
- unrestricted parts, voices, or polyphony;
- tied-note computational semantics;
- signed, fractional, string, array, or function values in TOScript Core;
- runtime variables, procedures, `CALL`, or `RET`;
- the complete historical TOScript+ design;
- source-preserving decompilation or recovery of original score layout;
- JavaScript generation;
- a native MuseScore QML plugin;
- deterministic sound-to-score transcription;
- perceptual or performer validation of musical legibility;
- musical, cultural, or notational universality; or
- a polysemic runtime that executes multiple harmonic interpretations.

Within the supported MusicXML subset, nontriadic Base sonorities are valid score material but are ignored by the current computational grammar. For example, C–F–G may be analysed as `Csus4` or `Fsus2/C`; the compiler records the event and declines to choose.

## Universality qualification

The Turing-completeness claim applies to the idealised deterministic TOScript Core with unbounded natural-number values, stack capacity, output capacity, program size, and execution. The reference interpreter is bounded by host resources and configurable step, stack, output, integer-magnitude, and trace budgets. See [`UNIVERSALITY.md`](UNIVERSALITY.md).

Computational universality is a formal property of the idealised core, not evidence of musical or artistic value.

## Showcase qualification

The *Hanoi Three-Disc Study* emits the canonical seven-move solution for one fixed three-disc instance. It is **not a general Towers of Hanoi solver**. The universal core makes such a solver expressible, but a specific score, validation package, and compositional study still need to be produced before that showcase claim is made.

Each deterministic example package contains MusicXML/MXL, TOScript Core, TOScript+, expected output, MIDI, deterministic `-reference.wav` audio, execution audio, maps, HTML inspection, and a manifest. The separate example-rendering workflow commits native MSCZ scores, MuseScore-rendered PDF sheets, and MP3 score playback. MusicXML/MXL remain the authoritative portable score sources; MuseScore output may differ across application versions, fonts, and sound profiles.
