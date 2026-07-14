# Mode B — PR review

Evaluate a PR (or local branch) against the fetched standards in `/tmp/delta-standards/`. The review is only as trustworthy as its criteria, so this mode never runs against remembered guidelines — if Step 0 from SKILL.md didn't complete, stop and say so.

Prerequisite: Step 0 from SKILL.md is complete (all three docs fetched, verified non-empty, and read in full).

## 1. Acquire the material

**PR by number or URL** (extract the number, and the repo if a URL was given — default `rileytestut/Delta`):

```bash
gh pr view <number> -R rileytestut/Delta --json title,body,number
gh pr diff <number> -R rileytestut/Delta
```

The `body` is what you check against the PR template; the diff is what you check against the code standards. If the diff is very large, page through all of it — a review that silently skipped hunks isn't a review.

**Local branch with no PR yet:**

```bash
git diff main...HEAD
git status --short   # catch untracked files that belong to the feature
```

Mark PR Template Compliance as **N/A**, and after the report offer to draft the PR description from the fetched template, following the "Drafting the PR description" rules in [build-mode.md](build-mode.md) (high-level description, no AI-attribution footers).

## 2. Evaluate

Read the diff hunk-by-hunk against the criteria in the cached docs:

- **Contributing Guidelines** — judge the diff against the fetched CONTRIBUTING.md (its guidelines and its code style and conventions sections).
- **Experimental Features Guidelines** — judge the implementation against the fetched ExperimentalFeatures.md (feature/option declaration, runtime gating, behavior when disabled, isolation, anything else the current doc requires).
- **PR Template Compliance** — compare the PR body against the fetched template: is the contribution type marked, is a description present, are tested iOS versions/devices listed, is the checklist completed?

Every "Needs work" claim needs a `file:line` reference — the file path plus the line within the changed hunks — so the developer can jump straight to it. If you can't point to a line, either find it or drop the claim.

Judge only against what the fetched docs actually say. If the docs are silent on something you'd personally flag, you may mention it in Suggested Changes, but it must not affect a section's verdict.

## 3. Report

ALWAYS use this exact structure:

```markdown
# PR Review: [PR title] (#number)

## Summary
[2–3 sentences: what the PR does and the overall compliance picture]

## Contributing Guidelines — [Pass / Needs work / N/A]
[Findings, each with file:line references into the changed hunks]

## Experimental Features Guidelines — [Pass / Needs work / N/A]
[Findings, each with file:line references into the changed hunks]

## PR Template Compliance — [Pass / Needs work / N/A]
[List missing sections: contribution type marked, description present,
iOS versions tested, checklist completed. N/A for local branches with no PR.]

## Suggested Changes
1. [Numbered, concrete, actionable — specific enough to implement without guessing]
2. ...
```

For a local-branch review, use the branch name in place of the title and omit the `(#number)`.

## 4. Afterwards

Offer to implement the suggested changes in the local working tree. Only touch files after the developer explicitly agrees — and per the guardrails, never post the review to GitHub, never push, never open a PR.
