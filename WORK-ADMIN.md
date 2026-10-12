# Cross-Repository Administration

Global repository registry, cross-domain status, and the master calendar are maintained in `krahd/tom-work-admin`.

This repository remains canonical for **Temperamento** implementation, language semantics, releases, examples, formal proofs, tests, reproducibility, and project-specific artistic/technical state.

Editable manuscripts and publication artefacts remain canonical in `krahd/academic-writing`. Professional submission packages belong in `krahd/professional-opportunities`; grant/funding packages and evidence belong in `krahd/grant-applications`.

## Mandatory synchronisation rule

`krahd/tom-work-admin` **must be kept current** whenever work here materially changes the project's administratively meaningful state. Updating the administration repository is part of completing the change, not optional later cleanup.

Update this repository first for substantive project changes, then update `krahd/tom-work-admin` in the same work session when any of the following changes:

- project lifecycle state, language scope, formal semantics, artistic/research direction, or major implementation goal;
- release/version, compatibility, proof/test status, distribution, or major validation milestone;
- relationship to a manuscript, submission, grant, collaborator, repository, dataset, performance, or other cross-domain dependency;
- submission/publication/award outcome where it materially affects global project status or next actions;
- deadline, presentation, release target, performance, or other material cross-domain date;
- current next action or major research/technical gate.

## Ownership boundary

Keep substantive source, semantics, examples, proofs, releases, tests, and artistic/technical evidence here. `tom-work-admin` stores only the concise cross-repository view and must point back to canonical project sources rather than duplicate them.

## Completion check

Before considering a material project-state change complete, verify that:

1. this repository reflects the substantive change;
2. `krahd/tom-work-admin` reflects any resulting global status, date, relationship, or next-action change;
3. related domain repositories are updated when the change affects manuscripts, submissions, or grants;
4. no stale cross-domain status or date remains in `tom-work-admin`.

## Current research development and grant routing

The project-specific research plan is [Temperamento and the Executable Score](docs/EXECUTABLE-SCORE-RESEARCH.md): native MuseScore integration, structured source diagnostics, a supported compose–inspect–run–revise–export cycle, and compositional research into the relationship between musical decisions and machine interpretation. The January–May 2027 phase includes a finite-repetition extension, six paired short-score studies and two separate developed compositions with annotated scores, digital audio realisations and revision analysis. By 31 May 2027 it plans a versioned research release and submission of an approximately 6,000-word article to *Organised Sound*.

Comparison of the existing parser and Core control flow with MusicXML's repeat and jump semantics identified a specific research problem: conventional musical returns can intersect instruction pairs, operand windows and computational branches. The two-pass prototype now serves as an early checkpoint towards explicitly delimited, non-nested fixed-count repetition and conventional first and second endings. This scope supports sustained compositional work while retaining explicit instruction boundaries, restrictions on mixed control flow, source occurrence mapping and execution limits. It refines the prospective research scope without changing the current alpha's semantics or claiming that the extension, compositions or publication actions have been completed.

The associated CHA Small Grant application is maintained in [krahd/grant-applications/2026-10-11_cha-small-grant-fall-2026](https://github.com/krahd/grant-applications/tree/main/2026-10-11_cha-small-grant-fall-2026). That private owner holds preparation decisions, the proposed allocation, budget, routing and submission evidence. Cross-domain status and dates are derived from `krahd/tom-work-admin`, opportunity `grant-2026-cha-small-fall`. The research plan records future work; it does not establish grant submission, an award or implementation of the proposed plugins.

The earlier [Double Life of a Score](docs/DOUBLE-LIFE-OF-A-SCORE.md) suite remains documented as a historical compositional direction. It is superseded as the current January–May 2027 research plan.
