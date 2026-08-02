# Bidirectional examples

These packages demonstrate the implemented semantic chain:

1. `TOScript+ ↔ TOScript Core`
2. `TOScript Core ↔ MusicXML`
3. `MusicXML → engraved sheet and playback` through MuseScore or another notation system

- [`score-to-code`](score-to-code/) begins with MusicXML and separately generates a canonical MusicXML realisation from the decoded Core.
- [`toscript-to-score`](toscript-to-score/) begins with canonical TOScript Core.
- [`toscript-plus-to-score`](toscript-plus-to-score/) begins with ergonomic TOScript+.

Every package records its primary source, generated representations, canonical round trip, expected execution, inspection HTML, and a machine-readable manifest. `make example-assets` adds MIDI, deterministic and MuseScore audio, MXL/MSCZ, and engraved PDF media. Audio-to-score transcription remains external and non-deterministic.
