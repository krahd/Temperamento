# TOScript+ to Score

Primary source: `toscript-plus-to-score.tom`.

This package demonstrates `TOScript+ → TOScript Core → MusicXML → TOScript Core`. The final Core program is byte-identical to the first canonical TOScript representation.

```bash
temperamento compile toscript-plus-to-score.musicxml
temperamento score toscript-plus-to-score.tos --output toscript-plus-to-score.musicxml
temperamento decompile toscript-plus-to-score.musicxml
temperamento render toscript-plus-to-score.musicxml --out-dir rendered --formats mscz,pdf,mp3
```

MuseScore or another notation application supplies engraving and playback. Audio-to-score transcription is an external, non-deterministic input route rather than a verified Temperamento inverse.
