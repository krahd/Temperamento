# MuseScore Studio integration

Temperamento deliberately uses MuseScore Studio as the notation editor instead of building another score editor.

The supported workflow is command-line conversion through MuseScore Studio 4:

```bash
temperamento doctor
temperamento validate piece.mscz
temperamento inspect piece.mscz --execute
temperamento gui piece.mscz
temperamento run piece.mscz --output text
temperamento render piece.mscz --out-dir build --formats pdf,svg,mid,wav,musicxml
```

MuseScore's documented converter mode uses `-o OUTPUT INPUT`; supported output extensions include MusicXML, MXL, MSCZ, PDF, SVG, MIDI, WAV, MP3, and FLAC. Temperamento discovers common executable names and platform locations, or accepts `TEMPERAMENTO_MUSESCORE` / `--musescore`.

A native QML plugin is not part of this alpha. [Temperamento and the Executable Score](../../docs/EXECUTABLE-SCORE-RESEARCH.md) plans Compose and Inspect and Run and Trace functions for MuseScore Studio. The plugin will call the existing CLI/API rather than duplicate compiler logic. [MuseScore's versioned 4.7 extension documentation](https://musescore.github.io/snapshots/4.7/index.html) and the [integration guide](../../docs/MUSESCORE.md#native-plugin-development) describe the relevant interfaces and scope.

The `real-musescore-render` workflow downloads the checksum-pinned official MuseScore Studio AppImage, renders every committed tutorial and showcase, verifies native-score round trips, commits the resulting notation and media, tags the alpha, and creates the GitHub prerelease.
