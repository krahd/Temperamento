# Inspection GUI

Temperamento's alpha GUI is a self-contained HTML report rather than a second notation editor.

```bash
temperamento gui piece.mscz
```

The report contains:

- command number;
- measure and beat;
- first and second Base harmonies;
- harmonic cell;
- decoded opcode and operands;
- canonical TOScript Core;
- runtime output;
- stack before and after each executed instruction; and
- the execution path through labels and jumps.

Write a persistent report without opening a browser:

```bash
temperamento gui piece.mscz --output build/piece-report.html --no-open
```

Equivalent non-GUI forms are available:

```bash
temperamento inspect piece.mscz
temperamento inspect piece.mscz --format json --execute
temperamento inspect piece.mscz --format html --output build/report.html --execute
```

The report is intentionally generated from the same `Program` and interpreter used by the CLI. There is no separate compiler implementation in the GUI.
