# Executable examples

## Bidirectional directions

[`directions/`](directions/) contains complete packages organised by primary source:

- `score-to-code`: MusicXML → canonical TOScript Core → canonical score → Core
- `toscript-to-score`: TOScript Core → MusicXML → Core
- `toscript-plus-to-score`: TOScript+ → Core → MusicXML → Core

Each package records its primary source and verified path in `manifest.json`. Generated `-roundtrip.tos` files must be byte-identical to the package's canonical `.tos` file. Canonical `-roundtrip.tom` files must lower to the same Core.

## Regression examples

- `arithmetic/add`: `7 + 5 → 12`
- `conditional/equal`: equality and control flow
- `iteration/countdown`: loop output `3, 2, 1`
- `equivalent-scores`: fixed transposed/revoiced regression files

## Tutorials

`tutorial/01` through `tutorial/05` introduce output, Boolean negation, equality, repeated addition, and accumulation.

## Showcase

- *Hello, World! Prelude*
- *Conditional Canon*
- *Countdown Étude*
- *Hanoi Three-Disc Study*
- *Twelve Transpositions*

Deterministic packages include MusicXML/MXL, TOScript Core, expected output, MIDI, deterministic `-reference.wav`, execution audio, `-map.svg`/`-map.pdf`, HTML inspection, and annotations. Direction packages additionally include TOScript+, round-trip textual forms, and manifests. The MuseScore workflow adds editable MSCZ, engraved PDF, and MP3 score playback.

The semantic boundary is `TOScript+ ↔ TOScript Core ↔ MusicXML`. Engraving and playback are derived through external notation tools. Third-party audio-to-score transcription may produce MusicXML input but is not a deterministic Temperamento inverse.

Regenerate deterministic files with:

```bash
make examples
```

Regenerate deterministic files and MuseScore media with:

```bash
make example-assets
```
