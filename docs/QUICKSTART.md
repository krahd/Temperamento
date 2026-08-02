# Quick start

## Install

```bash
python -m pip install -e .
```

For development and showcase regeneration:

```bash
python -m pip install -e ".[dev]"
```

## Diagnose MuseScore Studio

```bash
temperamento doctor
```

Temperamento searches common platform locations and executable names. Override discovery with:

```bash
export TEMPERAMENTO_MUSESCORE="/path/to/MuseScore"
# or
temperamento doctor --musescore /path/to/MuseScore
```

## Create a project

```bash
temperamento init hello-piece
cd hello-piece
```

The project contains editable MusicXML and compressed MXL sources, configuration, documentation, and a build directory. When MuseScore Studio is found, `init` also requests a native MSCZ conversion.

## Compile and run

```bash
temperamento validate hello-piece.musicxml
temperamento compile hello-piece.musicxml
temperamento inspect hello-piece.musicxml --execute
temperamento gui hello-piece.musicxml
temperamento run hello-piece.musicxml --output text
```

The starter emits `H`.

## Use a native MuseScore file

```bash
temperamento validate piece.mscz
temperamento run piece.mscz
temperamento render piece.mscz --out-dir build --formats pdf,svg,mid,wav,musicxml
```

## Render all repository examples

```bash
make render-examples
```

This recursively renders every `examples/**/*.musicxml` source beside itself as an editable MSCZ score, an engraved PDF sheet, and MP3 score playback. Each MSCZ is recompiled and checked for canonical-program and runtime equivalence.

To regenerate both Temperamento's computational artefacts and MuseScore's human-facing engraving and playback:

```bash
make example-assets
```

Additional formats can be requested explicitly:

```bash
MUSESCORE_FORMATS=mscz,pdf,wav make render-examples
```

## Run Hello World

```bash
temperamento run examples/showcase/hello-world-prelude/hello-world-prelude.musicxml --output text
```

Expected output:

```text
Hello, World!
```

## Verify the repository

```bash
make reproducibility
```
