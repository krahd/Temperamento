# Repeated Addition: score/program map

| Command | Measure | Beat | Base relation | Cell | Instruction |
|---:|---:|---:|---|---|---|
| 1 | 1 | 1 | C M → B M | `5MM` | `PUSH 3` |
| 2 | 1 | 19 | B M → B♭ M | `5MM` | `PUSH 3` |
| 3 | 1 | 37 | B♭ M → B♭ M | `0MM` | `ADD` |
| 4 | 1 | 55 | B♭ M → A M | `5MM` | `PUSH 3` |
| 5 | 1 | 73 | A M → A M | `0MM` | `ADD` |
| 6 | 1 | 91 | A M → A♭ M | `5MM` | `PUSH 3` |
| 7 | 1 | 109 | A♭ M → A♭ M | `0MM` | `ADD` |
| 8 | 1 | 127 | A♭ m → E m | `8mm` | `OUT` |
| 9 | 1 | 145 | E m → A♭ m | `4mm` | `END` |
