# Living documentation

The AltStore PAL source format is defined in the AltStore FAQ repo
(https://github.com/altstoreio/FAQ). This skill uses those pages as the
source of truth — there's no embedded copy of the spec here, so the skill
picks up spec changes the next time the agent fetches. If anything in this skill ever disagrees with those pages, they
win: update the skill rather than working around the docs.

The URLs below point at the raw GitBook source markdown. Don't substitute
the rendered pages on `faq.altstore.io`; they omit authoring cues (inline
tags, italic markers, callout blocks) that make accurate extraction easier.

## Make a Source page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md

Source of truth for the source JSON format. One page covers both PAL and
Classic — where a key differs between them the page says so, most notably
under `downloadURL`, `size`, and `marketplaceID`.

## Updating Apps page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/updating-apps.md

Source of truth for how AltStore detects and ships updates.

## Distribute with AltStore PAL page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/distribute-with-altstore-pal.md

Source of truth for everything that has to happen before a source exists:
the EU Terms Addendum, registering as a marketplace, notarization, and
getting an ADP.

## REST API page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/rest-api.md

Source of truth for the endpoints that process and download an ADP, and for
federating a source. Fetch it when the developer needs a fresh ADP.

## Patreon Integration page

- https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/patreon-integration.md

Source of truth for gating apps behind Patreon tiers. Fetch only if the
developer asks about gating — a PAL app on Patreon is attached and linked
differently from a Classic one.

## What the skill links to for developers

When pointing a developer at the docs during a conversation, share the
`faq.altstore.io` URLs. They're rendered and human-readable:

- https://faq.altstore.io/developers/make-a-source
- https://faq.altstore.io/developers/updating-apps
- https://faq.altstore.io/developers/distribute-with-altstore-pal
- https://faq.altstore.io/developers/rest-api
- https://faq.altstore.io/developers/patreon-integration
