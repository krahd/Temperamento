# Computational universality

## Claim

The idealised TOScript Core implemented in Temperamento `v0.5.0` is Turing-complete.

This is a claim about the deterministic computational sublanguage, not about all musical notation, all performances, or all possible harmonic interpretations. The proof is constructive: [`src/temperamento/universality.py`](../src/temperamento/universality.py) translates a deterministic two-counter machine into TOScript Core, and [`tests/test_universality.py`](../tests/test_universality.py) executes representative translations.

## Idealised semantics

The universality result assumes:

- non-negative integers of unbounded magnitude;
- an unbounded stack;
- unbounded output and program size;
- unbounded execution; and
- the documented deterministic semantics of `PUSH`, `ADD`, `SUB`, `DUP`, `EQ`, `LBL`, `JMC`, `JMP`, `SWAP`, and `END`.

The Python reference interpreter necessarily runs with finite host memory and configurable step, stack, output, integer-magnitude, and trace budgets. These bound particular executions without changing the abstract language definition, as is conventional for implementations of universal languages.

## Source model

A deterministic two-counter machine has two counters containing natural numbers and finitely many labelled instructions:

- `INC(i, q)`: increment counter `i` and continue at state `q`;
- `DECJZ(i, q0, q1)`: if counter `i` is zero continue at `q0`; otherwise decrement it and continue at `q1`; and
- `HALT`.

Two-counter machines with this form are a standard universal model of computation. The undecidability of their halting problem and their relationship to universal counter-machine models are surveyed and mechanised by Dudenhefner; classical universality originates in Minsky's counter-machine constructions.

## Representation invariant

A machine configuration with counters `(c1, c2)` is represented by a TOScript stack whose bottom-to-top contents are exactly:

```text
(c1, c2)
```

Every translated machine-state block begins and ends with this ordering.

## Instruction macros

### Increment counter 2

```text
PUSH 1
ADD
JMP q
```

This maps `(c1, c2)` to `(c1, c2 + 1)`.

### Increment counter 1

```text
SWAP
PUSH 1
ADD
SWAP
JMP q
```

The first `SWAP` exposes `c1`; the second restores the representation invariant.

### Conditional decrement of counter 2

```text
DUP
PUSH 0
EQ
JMC helper_zero
PUSH 1
SUB
JMP q_nonzero
LBL helper_zero
JMP q_zero
```

`EQ` produces a Boolean without consuming the retained counter value. `JMC` consumes that Boolean. The zero branch preserves `(c1, 0)`; the non-zero branch produces `(c1, c2 - 1)`.

### Conditional decrement of counter 1

```text
SWAP
DUP
PUSH 0
EQ
JMC helper_zero
PUSH 1
SUB
SWAP
JMP q_nonzero
LBL helper_zero
SWAP
JMP q_zero
```

Both branches restore `(c1, c2)` ordering before transferring control.

### Halt

```text
END
```

Helper labels are generated outside the machine-state label set, so the translation preserves deterministic control flow.

## Simulation theorem

For every deterministic two-counter machine `M`, initial counters `(a, b)`, and finite machine execution

```text
⟨q, a, b⟩ →* ⟨q', a', b'⟩
```

the translated TOScript program reaches the block for `q'` with stack `(a', b')` after finitely many TOScript steps.

### Proof sketch

Proceed by induction on the number of machine transitions.

- The translation initialises the stack to `(a, b)` and jumps to the entry-state block, establishing the invariant.
- For the induction step, inspect the machine instruction at the current state. Each macro above performs exactly the corresponding counter update, restores the invariant, and jumps to the translated successor state.
- A `HALT` state executes `END`.

Therefore the translation simulates every finite computation of `M`. Because deterministic two-counter machines can simulate arbitrary Turing machines, idealised TOScript Core is Turing-complete.

## Score-level corollary

Every opcode used by the construction has an assigned harmonic cell, including `SWAP` at `2mm`. Every machine state and literal is a non-negative integer and is therefore encodable through Temperamento's duration-framed root-relative base-12 Voice representation. Consequently, every finite translated TOScript construction has a corresponding Temperamento score within the documented computational grammar.

This corollary establishes formal expressibility. It does not establish source-preserving invertibility, compositional persuasiveness, unaided performability, perceptual legibility, or practical tractability. Large labels and literals remain finitely encodable but can generate proportionally large scores.

## Boundaries of the claim

Turing completeness does not imply:

- that Temperamento interprets arbitrary music;
- that Western staff notation is a universal representation of music;
- that ambiguous harmony has one correct computational reading;
- that every performance determines the same acoustic event;
- that computational universality is a measure of artistic value;
- that the constructive proof has been mechanically verified end to end; or
- that finite executions on the reference interpreter escape configured or physical limits.

Turing completeness is stated only as a formal property of the idealised core; it does not establish musical or artistic value.

## References

- Andrej Dudenhefner. “Certified Decision Procedures for Two-Counter Machines.” *FSCD 2022*. DOI: `10.4230/LIPIcs.FSCD.2022.16`.
- Marvin Minsky. *Computation: Finite and Infinite Machines*. Prentice-Hall, 1967.
- Kenichi Morita. “Universality of a Reversible Two-Counter Machine.” *Theoretical Computer Science* 168(2), 303–320, 1996. DOI: `10.1016/S0304-3975(96)00081-3`.
