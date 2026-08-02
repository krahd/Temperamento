# Contributing

## Setup

```bash
python -m pip install -e ".[dev]"
make reproducibility
```

## Change classes

### Core language

Update the normative grammar and semantics, opcode metadata, parser/compiler/interpreter, independent-oracle tests, error cases, examples, and documentation.

### MuseScore integration

Test discovery, converter invocation, non-zero exits, missing outputs, native conversion, and rendering without assuming a particular installation path. Keep actual MuseScore verification in the checksum-pinned real-render workflow; do not substitute unverified binaries.

### Inspection or GUI

Derive all output from `Program`, `Instruction`, and interpreter traces. Do not add a second parser or JavaScript compiler.

### Showcase

Update `scripts/generate_showcase.py`, regenerate media, record expected output, and state whether the work is an in-language algorithm, a fixed output study, or a host-generated score. Do not blur these categories.

## Test rules

- Use independent harmonic/opcode oracles.
- Add rejection cases for every accepted syntax.
- Test score semantics end to end through MusicXML.
- Preserve canonical TOScript determinism.
- Test all claimed invariances.

## Style

Python 3.11-compatible syntax, Ruff formatting/linting, strict mypy, British English, and specific user-facing errors without tracebacks for expected faults.
