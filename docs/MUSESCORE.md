# MuseScore Studio workflow

Temperamento uses MuseScore Studio as its notation editor and renderer. It does not attempt to recreate note entry, engraving, playback, parts, or media export in a separate desktop editor.

## Supported integration

MuseScore Studio's documented command-line converter uses:

```text
mscore -o OUTPUT INPUT
```

Current MuseScore documentation lists MusicXML, MXL, MSCX, MSCZ, PDF, SVG, PNG, MIDI, WAV, MP3, FLAC, and other export formats. Temperamento invokes this interface for:

- converting `.mscz` or `.mscx` to temporary MusicXML before compilation;
- creating native `.mscz` files from starter or imported score sources; and
- rendering notation, interchange, MIDI, and audio media.

Official references:

- https://handbook.musescore.org/appendix/command-line-usage
- https://handbook.musescore.org/file-management/file-export
- https://handbook.musescore.org/file-management/working-with-musicxml-files

## Executable discovery

Discovery order:

1. explicit `--musescore` argument;
2. `TEMPERAMENTO_MUSESCORE` environment variable;
3. common executable names on `PATH`;
4. standard macOS, Windows, and Linux locations.

Use `temperamento doctor --json` for machine-readable diagnostics.

## Authoring loop

1. Open the MusicXML/MXL/MSCZ source in MuseScore Studio.
2. Keep Voice on staff 1 and Base on staff 2.
3. Save the native score.
4. Run `temperamento inspect piece.mscz --execute`.
5. Correct any measure/beat diagnostic in MuseScore.
6. Run `temperamento gui piece.mscz` to inspect the mapping and trace.
7. Render release media with `temperamento render`.

## Batch-render the repository examples

```bash
make render-examples
```

The target runs `scripts/render_examples_musescore.py`, recursively discovers every `.musicxml` file below `examples/`, and writes these files beside each source by default:

| Extension | Role |
|---|---|
| `.mscz` | editable native MuseScore score |
| `.pdf` | printable engraved music sheet |
| `.mp3` | compressed MuseScore playback |

The generated MSCZ is compiled back through Temperamento. Its canonical TOScript and interpreter result must match the original MusicXML source. This verifies the notation round trip without claiming that MuseScore's PDF or audio bytes are identical across application versions, platforms, fonts, or sound profiles.

The compact committed set avoids duplicating the deterministic MIDI, reference WAV, and execution WAV artefacts already produced by Temperamento. Other MuseScore formats remain available explicitly:

```bash
MUSESCORE_FORMATS=mscz,pdf,wav make render-examples
```

To render only selected subtrees, call the script directly with repeatable roots:

```bash
python scripts/render_examples_musescore.py \
  --root examples/tutorial \
  --root examples/showcase
```

`make example-assets` combines the batch rendering with Temperamento's computational artefact generation. This preserves the distinction between score playback and execution audio.

## Native plugin development

The current alpha integrates through the converter and does not include a native plugin. The next research phase, [Temperamento and the Executable Score](EXECUTABLE-SCORE-RESEARCH.md), develops native Compose and Inspect and Run and Trace functions around the same Python compiler and interpreter.

MuseScore publishes [versioned 4.7 extension documentation](https://musescore.github.io/snapshots/4.7/index.html). Its [4.7.4 QML API implementation](https://github.com/musescore/MuseScore/blob/v4.7.4/src/engraving/api/v1/qmlpluginapi.cpp) registers the `QProcess` type and provides score export and import. The [process API](https://github.com/musescore/MuseScore/blob/v4.7.4/src/engraving/api/v1/util.h) exposes `startWithArgs(program, args)`; [cursor](https://github.com/musescore/MuseScore/blob/v4.7.4/src/engraving/api/v1/cursor.h) and [selection](https://github.com/musescore/MuseScore/blob/v4.7.4/src/engraving/api/v1/selection.h) interfaces provide navigation within a score. These interfaces supply the basis for calling Temperamento and relating its diagnostics and traces to notation.

The QML `QProcess` type is distinct from the unimplemented `newQProcess()` factory. The FileIO API restricts writes to MuseScore's user-data directories. Integration must accommodate these interfaces and the supported host version rather than infer behaviour from older plugin documentation.

The planned plugin will retain the authored score, expose consequences of edits and provide in-score navigation. Language semantics will remain in the existing CLI/API. Native plugin behaviour and platform compatibility remain development work; the current release's converter verification does not establish them.

## Real-integration verification

Normal CI uses deterministic integration doubles on Linux, macOS, and Windows. The `render-example-scores` workflow downloads the checksum-pinned official MuseScore Studio 4.7.4 AppImage, verifies the deterministic repository state, renders every MusicXML example to MSCZ/PDF/MP3, recompiles each native score, compares canonical programs and runtime results, and commits changed engraving and playback media to `main`. Release tagging remains a separate explicit process.
