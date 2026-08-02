# Release process

## Prepare

```bash
python -m pip install -e ".[dev]"
make reproducibility
make render-examples
make release-assets
```

`make reproducibility` validates deterministic source, code, package, and generated artefacts. `make render-examples` refreshes MuseScore engraving and score playback in a separately controlled external-tool boundary. `make release-assets` builds wheel and source distributions, regenerates the examples and site, creates example/documentation archives, and writes SHA-256 checksums.

## Tag

Stable releases use PEP 440-compatible package versions and matching readable Git tags:

```bash
git tag -a v0.5.0 -m "Temperamento v0.5.0"
git push origin v0.5.0
```

A release contains:

- wheel and source distribution;
- examples ZIP and tarball;
- documentation and site archives;
- checksums; and
- release notes.

Rendering and release tagging are intentionally separate operations. The `render-example-scores` workflow may refresh committed MSCZ, sheet, MIDI, and audio files, but it does not create or move release tags.

## External checks

Before distributing a release broadly:

- run the real-MuseScore workflow with an official AppImage and verified checksum;
- inspect the GitHub Pages deployment;
- download and verify release checksums;
- install the wheel in a clean system;
- test an MSCZ authored independently in MuseScore Studio.
