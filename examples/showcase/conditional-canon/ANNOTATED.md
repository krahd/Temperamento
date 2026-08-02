# Conditional Canon: score/program map

| Command | Measure | Beat | Base relation | Cell | Instruction |
|---:|---:|---:|---|---|---|
| 1 | 1 | 1 | C M → B M | `5MM` | `PUSH 7` |
| 2 | 1 | 19 | B M → B♭ M | `5MM` | `PUSH 7` |
| 3 | 1 | 37 | B♭ M → A♭ M | `10MM` | `EQ` |
| 4 | 1 | 55 | A♭ m → A♭ m | `0mm` | `JMC 1` |
| 5 | 1 | 73 | A♭ M → G M | `5MM` | `PUSH 0` |
| 6 | 1 | 91 | G m → E♭ m | `8mm` | `OUT` |
| 7 | 1 | 109 | E♭ m → B♭ m | `1mm` | `JMP 2` |
| 8 | 1 | 127 | B♭ M → E♭ M | `11MM` | `LBL 1` |
| 9 | 1 | 145 | E♭ M → D M | `5MM` | `PUSH 1` |
| 10 | 1 | 163 | D m → B♭ m | `8mm` | `OUT` |
| 11 | 1 | 181 | B♭ M → E♭ M | `11MM` | `LBL 2` |
| 12 | 1 | 199 | E♭ m → G m | `4mm` | `END` |
