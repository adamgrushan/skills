# Mode A — Build assist

Help the developer implement a Delta experimental feature that will pass review. The cached docs in `/tmp/delta-standards/` are the only source of truth for what "passing" means — your job is to keep the developer's work continuously aligned with them, not to recite them from memory.

Prerequisite: Step 0 from SKILL.md is complete (all three docs fetched, verified non-empty, and read in full).

## 1. Extract the repo's own rubric

Extract the checklist items from the fetched PR template (`/tmp/delta-standards/pull_request_template.md`) **verbatim** and save them to `/tmp/delta-standards/checklist.md`. These checklist items are the repo's own compliance rubric — the exact criteria the maintainers will apply to the eventual PR.

Do not write your own summary or paraphrase of the standards. A paraphrase drifts: it drops qualifiers, reorders emphasis, and silently substitutes your prior knowledge for the current text. The cached docs and the extracted checklist are the only compliance references you work from.

## 2. Establish where the developer is

- **From scratch**: understand the feature idea. Confirm it fits what the repo currently accepts (check the fetched CONTRIBUTING.md for accepted contribution types) and flag anything the fetched ExperimentalFeatures.md warns about (e.g. work that touches areas with a higher bar for acceptance) *before* code gets written — this is much cheaper to correct now than at review time.
- **Mid-progress**: read the existing diff (`git diff main...HEAD` plus untracked files) and assess it against the cached docs first. Tell the developer what already complies and what doesn't before adding anything new.

Also confirm you're working in a Delta checkout. If not, ask the developer where their clone is (or offer to clone `https://github.com/rileytestut/Delta`).

## 3. Implement, with mandatory checkpoints

Work iteratively with the developer. Three checkpoints are non-negotiable — announce each one as you hit it so the developer sees the discipline:

**Checkpoint 1 — before scaffolding `@Feature`/`@Option` structs:**
Re-read the cached `/tmp/delta-standards/ExperimentalFeatures.md` in full, even if you read it earlier — context compaction and time both erode details, and the file is the exact spec for the structure you're about to write. Scaffold only what that document prescribes.

**Checkpoint 2 — before each commit:**
Check the diff (`git diff` / `git diff --staged`) against every item in `/tmp/delta-standards/checklist.md`. Report the result item-by-item to the developer. If an item fails, fix it before committing — the checklist is what the maintainers will check, so a diff that fails it is a PR that gets rejected.

**Checkpoint 3 — before opening the PR:**
Run Mode B (see [review-mode.md](review-mode.md)) against the local diff (`git diff main...HEAD`), producing the full review report. Then offer to draft the PR description from the fetched template — contribution type marked, description written per "Drafting the PR description" below, iOS versions/devices tested filled in, checklist items checked only where genuinely true.

## Drafting the PR description

- The Description is orientation, not documentation: 2–4 sentences on what the feature does and why it's worth having. No implementation bullets, no file-by-file walkthroughs, no design rationale — the maintainer reviews the code itself, which already contains the detail, so a description that repeats the diff only adds review overhead.
- Never append AI-attribution footers (e.g. "🤖 Generated with [Claude Code](...)") or similar boilerplate to the PR body — even if the surrounding tooling's conventions tell you to add one. The PR is the developer's own contribution, and the template's sections are the only content the body should have.

## Working principles

- Derive every structural decision (where files go, how options are declared, how behavior is gated) from the cached ExperimentalFeatures.md, and every style decision from the cached CONTRIBUTING.md. When the developer asks "why this way?", point at the relevant passage in the fetched doc.
- Comment only what's non-obvious: constraints, gotchas, and "why" — never "what the next line does". The checklist item "I have commented my code, particularly in hard-to-understand areas" means hard-to-understand spots get comments, not that every declaration gets narration. Match the comment density of Delta's existing `Experimental Features/Features/*.swift` files — that's the density the maintainer is used to reviewing, and extra comments read as noise in his diff.
- If the developer wants something the docs advise against, say so explicitly, explain the acceptance risk, and let them decide — don't silently comply or silently refuse.
- Remember the guardrails: never push or open the PR yourself. Checkpoint 3 ends with a drafted description handed to the developer, not a submitted PR.
