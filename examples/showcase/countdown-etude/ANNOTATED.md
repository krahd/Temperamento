# Countdown Étude: score/program map

| Command | Measure | Beat | Base relation | Cell | Instruction |
|---:|---:|---:|---|---|---|
| 1 | 1 | 1 | C M → B M | `5MM` | `PUSH 3` |
| 2 | 1 | 19 | B M → E M | `11MM` | `LBL 1` |
| 3 | 1 | 37 | E M → F M | `7MM` | `DUP` |
| 4 | 1 | 55 | F m → C♯ m | `8mm` | `OUT` |
| 5 | 1 | 73 | C♯ M → C M | `5MM` | `PUSH 1` |
| 6 | 1 | 91 | C M → G M | `1MM` | `SUB` |
| 7 | 1 | 109 | G M → A♭ M | `7MM` | `DUP` |
| 8 | 1 | 127 | A♭ m → A♭ m | `0mm` | `JMC 1` |
| 9 | 1 | 145 | A♭ M → D M | `6MM` | `POP` |
| 10 | 1 | 163 | D m → F♯ m | `4mm` | `END` |
