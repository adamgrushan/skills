# Living documentation

The AltStore Classic source format is defined in two markdown files in
the AltStore FAQ repo (https://github.com/altstoreio/FAQ) This skill
uses those files as the source of truth. There's no embedded copy of the
spec here, and no field rules in code. When the spec changes, the
skill picks the change up the next time the agent fetches it.

## Make a Source page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md

This page covers the format for making a source JSON file. Steps 2A.3 and 2B.3 of
SKILL.md tells the agent to fetch this page and organize it into a rule
pack.

## Updating Apps page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/updating-apps.md

This page covers how AltStore detects and ships updates (the role of
`version` / `buildVersion` / `date` in determining the "latest" release).
The agent only fetches it when a question requires it — most validation
runs don't need it.

## REST API page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/rest-api.md

This page documents AltStore's REST API, which is primarily for **AltStore
PAL** (the EU marketplace mode) — not for AltStore Classic. It covers
registering Developer IDs to receive security tokens, processing and
downloading Alternative Distribution Packages (ADPs) for EU app
distribution, and federating sources to `explore.alt.store`. The agent
should only consult this page if the developer asks about PAL marketplace
registration, ADP workflows, or federation — none of those are part of the
AltStore Classic flow this skill walks through. If the conversation is
purely about Classic distribution, ignore this page entirely.

## Patreon Integration page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/patreon-integration.md

This page documents how developers can monetize apps through AltStore by 
gating distribution behind Patreon tiers. It covers marking apps as 
Patreon-only (which shows a "Join Patreon" prompt instead of an install 
button), setting minimum pledge tiers, hiding apps from non-Patrons, and 
the automatic expiration of access when pledges lapse. The `source.json` 
integration touches three fields: the source-level `patreonURL` (a plain 
link to the developer's Patreon page, what Step 1.4 collects), a per-app 
`patreon` object specifying tier requirements, and a Patreon-attachment 
`downloadURL` for gated builds. The agent should only consult this page if 
the developer asks about gating apps behind Patreon — not when they're just 
adding a link to their Patreon page in Step 1.4, which is a much simpler 
one-field interaction.

All four URLs above point at the raw GitBook source markdown. Don't
substitute the rendered pages on `faq.altstore.io`; they omit authoring
cues (inline tags, italic markers, callout blocks) that make accurate
extraction easier.

## What the skill links to for developers

When pointing a developer at the docs during a conversation, share the
`faq.altstore.io` URLs. They're rendered and human-readable:

- https://faq.altstore.io/developers/make-a-source
- https://faq.altstore.io/developers/updating-apps
- https://faq.altstore.io/developers/rest-api
- https://faq.altstore.io/developers/patreon-integration

## Truth ordering

If anything in this skill (prose, examples) ever disagrees with the
markdown files above, the markdown wins. Update the skill rather than
working around the docs.
