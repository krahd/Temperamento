# Architecture

## Data flow

```text
MusicXML / MXL / MSCX / MSCZ
              |
      MuseScore conversion
       (native files only)
              |
              v
safe MusicXML parsing + rational score time
              |
      +-------+-------+
      |               |
      v               v
Base chord analysis   Voice window analysis
      |               |
      +-------+-------+
              v
canonical Program IR + measure/beat source map
              |
      +-------+-------+----------------+
      |               |                |
      v               v                v
TOScript Core     stack interpreter   inspection data
                       |                |
                       v                v
                 output + trace      text/JSON/HTML GUI
```

## Modules

- `musicxml.py`: safe uncompressed/compressed input, exact score time, source locations.
- `harmony.py`: major/minor triad recognition and fifths-distance cells.
- `compiler.py`: command pairing, operand windows, cell lookup, static validation, native score entry point.
- `model.py`: immutable score events, instructions, source maps, and canonical program.
- `opcodes.py`: assigned core operations and reserved instruction cells.
- `interpreter.py`: validated stack execution and optional per-step trace.
- `inspection.py`: human-readable tables, JSON, and self-contained HTML GUI.
- `musescore.py`: executable discovery, native conversion, and media rendering.
- `project.py`: starter project and MXL generation.
- `cli.py`: user-facing workflows.

## Trust boundaries

MusicXML and MXL are untrusted inputs. The parser enforces XML-size limits; accepts and strips only the standard external Recordare `score-partwise` MusicXML DOCTYPE without resolving its external DTD; rejects entity declarations, internal subsets, and unrecognised DTDs; and rejects unsafe archive paths, duplicate rootfiles, unsupported structures, and ambiguous notation. MuseScore is an external process: executable discovery is distinguished from successful execution, its return code and expected output files are checked, and conversion occurs in a temporary directory.

Starter-project titles are validated before any project files are written so invalid XML 1.0 characters and unreasonably long title input cannot create malformed or partially populated project artefacts.

The browser GUI contains static generated HTML and does not run a compiler in JavaScript. The CLI/API remain the single semantic implementation.

## Reproducible media

Showcase media are generated from committed MusicXML:

- MIDI through a deterministic standard-MIDI writer;
- reference WAV through a deterministic sine synthesiser;
- execution WAV through the actual interpreter trace;
- SVG/PDF from canonical instruction maps;
- HTML from the inspection model.

The release workflow commits output from a checksum-pinned MuseScore Studio version. That output is verified for semantic round-trip equivalence, but is not claimed to remain byte-identical across MuseScore versions, platforms, fonts, or sound profiles.
