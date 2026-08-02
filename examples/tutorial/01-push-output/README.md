# Push and Output

A committed executable composition for Temperamento.

```bash
temperamento validate 01-push-output.musicxml
temperamento inspect 01-push-output.musicxml --execute
temperamento run 01-push-output.musicxml
```

Files include MusicXML/MXL source, canonical TOScript, MIDI, deterministic reference audio, PDF/SVG program maps, HTML inspection, expected output, and an annotated map. The release workflow additionally commits native `.mscz` files and MuseScore-rendered PDF, SVG, and WAV media.
