# Score to Code

Primary source: `score-to-code.musicxml`.

This package demonstrates `MusicXML → TOScript Core → MusicXML → TOScript Core`. The final Core program is byte-identical to the first canonical TOScript representation.

```bash
temperamento compile score-to-code.musicxml
temperamento score score-to-code.tos --output score-to-code-canonical.musicxml
temperamento decompile score-to-code-canonical.musicxml
temperamento render score-to-code.musicxml --out-dir rendered --formats mscz,pdf,mp3
```

MuseScore or another notation application supplies engraving and playback. Audio-to-score transcription is an external, non-deterministic input route rather than a verified Temperamento inverse.
