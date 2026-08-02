# Normative specification

This directory defines the deterministic TOScript Core score semantics. `v0.5.0-alpha.1` extends the earlier core with ignored noncomputational Base events and the `SWAP` operation while preserving the established harmonic coordinate and root-relative operand encoding.

- [`grammar.ebnf`](grammar.ebnf): abstract score and operand grammar.
- [`semantic-subset.md`](semantic-subset.md): accepted MusicXML structures, computational filtering, cells, operands, validation, runtime semantics, and the idealised universal model.
- [`opcode-table.json`](opcode-table.json): all 48 cells, including seventeen assigned operations and thirty-one reserved cells.
- [`../docs/UNIVERSALITY.md`](../docs/UNIVERSALITY.md): constructive two-counter-machine translation and proof boundary.

Native MSCX/MSCZ conversion is an input adapter: the normative program begins after MuseScore Studio has exported MusicXML. HTML, text output, reference media, ignored-event reports, and execution sonification are presentation layers and do not alter decoded instructions.

A nontriadic Base event is outside the computational alphabet but remains valid score material. Malformed MusicXML and malformed Temperamento programs remain errors.

Regenerate the opcode table and current release measurements with:

```bash
make metadata
```
