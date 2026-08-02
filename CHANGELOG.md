# Changelog

## 0.4.0-alpha.1 — 2026-07-22

- Added native MuseScore Studio MSCZ/MSCX conversion and multi-format rendering.
- Added environment diagnosis, project scaffolding, source inspection, browser GUI, and Unicode text output.
- Added measure/beat command source maps and optional interpreter execution traces.
- Added five graded tutorials and the Hello World, Conditional Canon, Countdown, Hanoi, and Twelve Transpositions showcases.
- Added deterministic MusicXML/MXL, TOScript, MIDI, WAV, execution-sonification, SVG, PDF, HTML, and annotation generation.
- Added Linux/macOS/Windows CI, a checksum-pinned real-MuseScore workflow, GitHub Pages, issue templates, and prerelease asset generation.
- Added reproducibility checks so later releases cannot silently alter generated evidence.
- Added complete MuseScore, GUI, showcase, troubleshooting, release, and updated architecture documentation.

## 0.3.0 — 2026-07-22

- Fixed package metadata for current setuptools and added package-build verification.
- Corrected compressed MusicXML handling to use the first rootfile while permitting alternate PDF/audio renditions.
- Rejected malformed container roots, non-MusicXML first rootfiles, duplicate score entries, and directory rootfiles.
- Enforced non-overlapping computational Voice notes and command-window boundaries.
- Rejected tied notes rather than silently assigning them attack-based semantics.
- Converted division overflow into a user-facing runtime fault.
- Added `temperamento --version` and `temperamento validate`.
- Derived validation counts and branch coverage from the actual test and coverage run.
- Added complete status, quick-start, language, API, architecture, design-decision, reproducibility, example, specification, and contribution documentation.
- Strengthened CI, packaging, and generated-artefact checks.
- Pinned the Python test and quality toolchain used by the reproducibility target.

## 0.2.0 — 2026-07-21

- Introduced root-relative Voice operands and whole-program transposition invariance.
- Added compressed MusicXML support, static control-flow validation, and exhaustive instruction-space tests.

## 0.1.0

- Initial restricted MusicXML compiler and TOScript Core interpreter.
