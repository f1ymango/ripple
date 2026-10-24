# Contributing to Ripple

Ripple's current code and evidence are the **2026 competition alpha**. New work
is welcome, including a future implementation that shares the initiative and
name but starts with a different technical design.

## Credit and attribution

The [README team table](README.md#team-and-credit) records the five members of
UST Ripple and their 2026 responsibilities. A teammate who wants more specific
credit can open a pull request that adds a preferred public name, optional
GitHub profile link, and a short description of their work. Non-code work such
as research, data preparation, simulation, visual design, pitch writing, and
video production belongs in the credits too. A correction to an existing entry
is equally welcome.

For example, add a sentence below the table:

> **Name or handle** — contributed [specific component or artifact];
> [profile](https://github.com/your-handle) (optional).

Use only a person's own approved public name and link. If a contribution is
shared, credit the collaborators together. Commit history and the
[team tracker](docs/project-tracker.md) can help identify work, but a Git
author name alone does not tell the whole story.

## Working on the project

1. State whether a change documents the 2026 alpha, fixes its code, or starts
   a new Ripple phase. For a new phase, use a branch and a short design note
   before replacing the existing implementation.
2. Keep the [`judge-facing-2026-10-18`](https://github.com/f1ymango/ripple/tree/judge-facing-2026-10-18)
   tag and final submission artifacts intact. Add new results alongside the
   archived evidence and label their source and date.
3. For alpha code changes, keep the relevant JSON contracts, seeded runs and
   provenance checks coherent. Never hand-edit saved simulation results.
4. Run the relevant tests and describe what was checked in the pull request.
   Data, SUMO and local-model workflows have separate setup notes in their
   respective folders.

The [project status](PROJECT_STATUS.md) explains the boundary between the
historical prototype and possible future work. The [MIT licence](LICENSE)
covers code; datasets, maps, media, models and other third-party materials can
have separate terms, as noted in the README.
