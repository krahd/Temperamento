# Reproducibility

## Complete deterministic check

```bash
python -m pip install -e ".[dev]"
make reproducibility
```

The check performs:

1. Ruff format and lint validation;
2. strict mypy checking;
3. deterministic example and showcase regeneration;
4. branch-aware tests with a 95% floor;
5. current release metric generation;
6. documentation-site generation;
7. wheel and source-distribution construction;
8. clean-environment wheel installation;
9. CLI doctor, validation, compilation, inspection, execution, and text-output smoke tests; and
10. a Git diff check over deterministic generated committed artefacts.

## Complete example-media generation

```bash
make example-assets
```

This first performs the deterministic Temperamento generation behind `make examples`, then asks MuseScore Studio to render every `examples/**/*.musicxml` file as MSCZ, PDF, and MP3. Each generated MSCZ is recompiled and executed to confirm equivalence with the original MusicXML. Other MuseScore formats can be requested explicitly.

MuseScore rendering is intentionally not part of `make reproducibility`: engraving and playback depend on an external application version, fonts, sound profile, and platform. The checksum-pinned `render-example-scores` workflow provides a controlled reference rendering environment.

## Generated current-release artefacts

Do not edit manually:

- `examples/showcase/**` and `examples/tutorial/**` computational media;
- MuseScore-rendered `.mscz`, `.pdf`, and `.mp3` files below `examples/`;
- `docs/assets/temperamento-walkthrough.*`;
- `spec/opcode-table.json`;
- `_site/` during a build.

## Continuous integration

- Linux, macOS, and Windows run the full Python test/coverage suite on Python 3.11 and 3.13.
- Ubuntu runs quality, packaging, documentation, deterministic media, and reproducibility checks.
- A checksum-pinned workflow verifies the official MuseScore Studio 4.7.4 AppImage, renders every MusicXML example, and recompiles every MSCZ to confirm program and runtime equivalence.

## Determinism boundary

Compiler output, tests, canonical TOScript, generated reference audio, execution audio, and PDF instruction maps are deterministic. MuseScore engraving/audio are not claimed to be byte-identical across application versions, platforms, fonts, sound profiles, or user preferences. Their semantic round trip is verified instead.
