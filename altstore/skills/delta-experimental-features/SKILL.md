---
name: delta-experimental-feature
description: Build or review experimental features for Delta (rileytestut/Delta) against the repo's live contribution standards. Use this whenever the user wants to add, implement, contribute, or continue work on an experimental feature for Delta — even if they just say "add a feature to Delta" or mention @Feature/@Option, ExperimentalFeatures.swift, or Delta's settings toggles. Also use it whenever the user asks to review, check, or evaluate a PR against Delta's guidelines ("review this PR to Delta", "check my Delta PR", "does this meet Delta's guidelines"), pastes a rileytestut/Delta pull request URL or PR number, or wants their local Delta branch reviewed before opening a PR. Do not rely on remembered knowledge of Delta's guidelines — this skill fetches them live.
---

# Delta Experimental Feature

Help developers contribute experimental features to [Delta](https://github.com/rileytestut/Delta) — Riley Testut's iOS emulator — in compliance with the repo's contribution standards. Two modes:

- **Mode A — Build assist**: implement a new experimental feature (from scratch or mid-progress) in compliance with the standards.
- **Mode B — PR review**: evaluate a PR or local branch against those same standards.

## Mode selection

Use **Mode B** when the input contains a Delta PR URL or PR number, or review language ("review this PR to Delta", "check my PR to Delta", "does this meet the guidelines for Delta"). Otherwise use **Mode A** (building, implementing, continuing, or planning a feature). If genuinely ambiguous — e.g. "I'm working on a feature for Delta, here's my branch" could mean "help me finish" or "tell me if it passes" — ask the user which they want.

## Step 0 (both modes): fetch the live standards

The contribution standards are the **source of truth**, and they live in the Delta repo — not in this skill and not in your memory. They may have changed since your training data. Never review or build against remembered or assumed criteria; always fetch fresh copies at the start of a session:

```bash
mkdir -p /tmp/delta-standards
curl -fsSL https://raw.githubusercontent.com/rileytestut/Delta/main/CONTRIBUTING.md -o /tmp/delta-standards/CONTRIBUTING.md
curl -fsSL https://raw.githubusercontent.com/rileytestut/Delta/main/Docs/ExperimentalFeatures.md -o /tmp/delta-standards/ExperimentalFeatures.md
curl -fsSL https://raw.githubusercontent.com/rileytestut/Delta/main/Docs/pull_request_template.md -o /tmp/delta-standards/pull_request_template.md
```

The three documents and what each governs:

1. **CONTRIBUTING.md** — high-level guidelines, code style and conventions.
2. **Docs/ExperimentalFeatures.md** — how experimental features must be implemented (@Feature/@Option structure, user-facing options, runtime gating, isolation).
3. **Docs/pull_request_template.md** — the PR template contributors must fill out, including the compliance checklist.

After fetching, verify every file is non-empty (`test -s`). **If any fetch fails or a file is empty, tell the user which fetch failed and stop.** Do not substitute remembered content, a summary, or a cached copy from a previous session of unknown age — a review against stale criteria is worse than no review.

Save the files verbatim (no editing, no summarizing) to `/tmp/delta-standards/` so they survive context compaction — re-read them from disk whenever you need the criteria and they're no longer in context. Then **read all three files in full** before doing anything else.

## Next steps by mode

- **Mode A**: read [references/build-mode.md](references/build-mode.md) and follow its workflow, including the three mandatory checkpoints.
- **Mode B**: read [references/review-mode.md](references/review-mode.md) for acquisition commands and the exact report format.

## Guardrails (both modes)

This skill reports and edits **locally only**:

- Never post review comments to GitHub (no `gh pr review`, `gh pr comment`, or similar).
- Never push commits or branches.
- Never open PRs on the developer's behalf.
- Only modify the working tree after the developer explicitly agrees to specific changes.

The developer stays in control of everything that leaves their machine.
