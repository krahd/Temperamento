# Temperamento and the Executable Score

Temperamento investigates musical notation as a medium for programming. A score can organise a musical experience while specifying computational actions, and these readings attend to different properties of the same inscription. The research asks what changes when a composer can specify, understand and revise a computation through musical notation.

This phase develops Temperamento as a working research environment. Its central concern is the composer's ability to move between musical intention and executable consequences: to discover what the language reads, to understand a result, and to revise either the music or the computation. Development and composition will proceed together.

## The research problem

A change of register or voicing can alter the music while preserving its programme. Conversely, adding a chord tone can move an event outside the computational alphabet and change the pairing of subsequent instructions. These consequences follow from Temperamento's designed reading of a score; they are not inherent properties of harmony.

The present representation chain supplies canonical semantic conversions between supported scores, TOScript Core and TOScript+. Canonical conversion preserves the programme but does not recover the original score's voicing, engraving or noncomputational material. A usable authoring environment must therefore expose what changes between representations while retaining the composer's authored score.

The investigation concerns the conditions under which musical notation can sustain computational authorship. Its evidence will include compositional decisions, alternatives, unexpected consequences and constraints encountered through use.

## Native notation integration

A MuseScore Studio plugin package will connect the working score to Temperamento's compiler and interpreter through two related functions:

- **Compose and Inspect** will identify computational and noncomputational material, display decoded instructions and diagnostics, and navigate to the relevant score locations.
- **Run and Trace** will execute the programme and allow its path to be followed through the score, including branches, repeated instructions and results.

Both functions will use the existing Python compiler, inspection model and interpreter. MuseScore will continue to provide note entry, engraving and ordinary score playback. The plugin will connect these activities with computation without introducing a second implementation of the language.

The initial integration will support a documented MuseScore Studio 4.7 configuration on macOS. Its distribution will state the versions and platforms actually tested.

## A complete authoring cycle

The supported workflow will connect composition, inspection, execution, revision and export. The authored score will remain available throughout that cycle. Generated canonical scores will be separate realisations, allowing their differences from the authored score to be examined rather than silently replacing musical choices.

The development will make selective machine reading visible at the point of revision. A composer should be able to locate a consequential change, understand why it matters computationally and try another musical solution. The resulting research release will include examples, installation instructions and a documented route from a working score to shareable musical and computational material.

This phase concerns the integrated workflow within Temperamento's supported notation. It does not promise unrestricted interpretation of music or automatic recovery of every musical decision from canonical code.

## Compositional research

The environment will be developed through two complementary approaches:

- Start with a musical phrase and investigate how it can acquire computational behaviour while retaining its musical purpose.
- Start with a desired computation and develop alternative musical expressions of it.

These trials will involve scoring, listening, execution, revision and comparison. Revision histories will record where musical and computational aims support one another, where they conflict and where an attempted solution fails. Those encounters will guide changes to the interfaces and bounded refinements of notation conventions. Any change to language semantics will be specified and verified through the project's established implementation and validation process.

The examples are research material through which Temperamento itself is developed. Their value lies in the decisions and possibilities they make available, rather than in meeting a fixed concert programme or suite structure.

## Work and dissemination

Tomas Laurenzo will lead the research, interface and language design, main implementation, compositional investigation and interpretation. A student technical assistant will provide bounded support for integration, verification, example preparation and documentation.

| Period | Activity |
|---|---|
| January–February 2027 | Develop the native notation integration and connect the supported authoring cycle. |
| March–April 2027 | Conduct compositional trials, examine their revision histories and refine the environment. |
| April 2027 | Present a demonstration and discussion accessible to the CU Boulder community. |
| By 31 May 2027 | Publish the research release, plugin package, examples and revision histories, installation and use documentation, and a concise critical account. |

The public release and demonstration will make the environment available for further artistic and scholarly work on notation, programming and interpretation.

## Artistic context

Daniel Temkin's [Velato](https://github.com/rottytooth/Velato) provides a direct precedent for programmes written as music. Temperamento develops within this lineage of executable artistic notation. Its contribution in this phase is an environment and a body of compositional research through which the relationship between musical decisions and machine interpretation can be examined and revised in practice.
