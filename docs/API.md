# Python API

## Compile MusicXML or a native MuseScore score

```python
from temperamento import compile_score

program = compile_score("piece.mscz")
print(program.to_tos())
```

For native MSCZ/MSCX input, `compile_score` converts to temporary MusicXML through MuseScore Studio. Pass an explicit executable when needed:

```python
program = compile_score("piece.mscz", musescore="/Applications/MuseScore 4.app/Contents/MacOS/mscore")
```

`compile_musicxml` remains available when conversion is neither needed nor wanted.

## Source mapping

Each immutable `Instruction` includes:

- absolute score onset;
- measure and one-based beat;
- harmonic cell;
- initial and final chord roots;
- decoded operands; and
- computational Voice onsets.

```python
for instruction in program.instructions:
    print(instruction.measure, instruction.beat, instruction.to_tos())
```

## Execute and trace

```python
from temperamento import Interpreter

result = Interpreter(max_steps=100_000).run(program, capture_trace=True)
print(result.output)
for step in result.trace:
    print(step.pc, step.opcode, step.stack_before, step.stack_after)
```

## Inspection data

```python
from temperamento.inspection import inspect_data, inspect_html

data = inspect_data(program, execute=True)
html = inspect_html(data, title="My score")
```

## MuseScore integration

```python
from temperamento.musescore import find_musescore, render_score

installation = find_musescore()
outputs = render_score("piece.mscz", "build", ["pdf", "svg", "mid", "wav"])
```

## Errors

All user-facing errors inherit from `TemperamentoError`:

| Class | Meaning |
|---|---|
| `MusicXMLError` | Unsupported or malformed MusicXML/MXL. |
| `HarmonyError` | A chord relation cannot be decoded. |
| `StaticError` | A score is not a valid Temperamento program. |
| `RuntimeFault` | Execution cannot continue. |
| `IntegrationError` | MuseScore discovery, conversion, or rendering failed. |

The Python API remains alpha-level. The score semantics, canonical TOScript rendering, CLI behaviour, and tagged release artefacts are the stronger compatibility commitments.
