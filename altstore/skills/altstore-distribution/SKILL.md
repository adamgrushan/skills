---
name: altstore-distribution
description: Help iOS developers manage an AltStore source — create a source, update an app in their source, or add apps to their source. Use when a developer says things like "AltStore Classic", "AltStore PAL", "make a source", "host my IPA", "host my ADP", "update my app", "update my source", or "add an app to my source". The skill generates a source JSON file from an IPA/ADP, validates it against the live spec, and gives hosting guidance.
---

# AltStore Distribution

## Working contract

Two rules:

- **Never upload on the developer's behalf unless they explicitly ask.** No `curl` uploads, `scp`, `rsync`, `aws s3 cp`, `gh release upload`, `git push` to a repo, or any other write to a public web host — including any harness or MCP tool that would do it for you. You tell them what their host needs and flag problems with what they describe; they run the upload.

- **Don't narrate your work.** Speak when you have a question or a result; otherwise stay quiet. Don't preface tool calls ("Let me look that key up in the spec...") or summarize what you just did ("OK, I've filled in your source!"). **The one exception is a heads-up this file writes for you** — like Step 1.1's kickoff.

## References

- `references/living-docs.md` — the AltStore FAQ pages: raw URLs to fetch, rendered URLs to share.
- `references/ipa-metadata.md` — the commands for reading app metadata out of an IPA.
- `references/adp-metadata.md` — the commands for reading app metadata out of an ADP.
- `references/distribute-with-altstore-classic.md` — the developer-facing primer; read it for setup questions this file doesn't cover.

## Which flow you're in

This skill does the same three jobs for AltStore Classic and AltStore PAL: make a source, add an app, or ship an update.

For PAL it assumes the developer has already agreed to Apple's Alternative EU Terms Addendum, added AltStore PAL as an alternative marketplace, and had their build notarized by Apple and processed by AltStore. None of that is covered here — if they haven't finished those steps, send them to https://faq.altstore.io/developers/distribute-with-altstore-pal (raw URL in `references/living-docs.md`).

- **No source yet** → [**Stage 1**](#stage-1-build-the-baseline-sourcejson) and [**Stage 2**](#stage-2-edit-and-host-in-the-developers-preferred-order).
- **Adding an app to an existing source** → [**Adding apps**](#adding-apps).
- **Shipping a new version of an app** → [**Updating apps**](#updating-apps).

## Stage 1: Build the baseline source.json

### Step 1.1: Fetch the canonical template

Tell the developer you're fetching the template and reading their IPA/ADP.

Download AltStore's canonical template for the developer's flow. For Classic:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/.gitbook/assets/ClassicSourceExampleForSkill.json
```

For PAL:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/.gitbook/assets/PALSourceExampleForSkill.json
```

Before saving, check whether `source.json` already exists in the working directory. If it does, ask whether they meant to [add an app](#adding-apps) or [ship an update](#updating-apps) — it may already be published; overwrite only if they plainly say they want to start over.

Otherwise save the template as `source.json` there. Every value is still a template placeholder; Steps 1.2–1.7 replace only a few and Stage 2 handles the rest.

If you can't fetch the template, stop and tell the developer what went wrong. Don't write `source.json` from memory.

### Step 1.2: Identify the IPA/ADP and read its metadata

See [**Identify the IPA/ADP and read its metadata**](#shared-procedure-identify-the-ipaadp-and-read-its-metadata) below.

### Step 1.3: Fill the template's app entry

Write the values you read into `source.json`'s `apps[0]` and its `versions[0]`, overwriting the template's. Change nothing else.

### Step 1.4: Update the `featuredApps` field

Set `featuredApps` to `[apps[0].bundleIdentifier]` (a single-element list containing the app's bundle identifier).

### Step 1.5: Ask for the source name

Ask the developer:

> What would you like to call your source?

Replace `source.json`'s top-level `name` field with their answer. Don't replace anything else.

### Step 1.6: Ask the developer for their Patreon

Ask the developer:

> Would you like to add Patreon support? If so, what's your Patreon page URL?
>
> With Patreon you can offer apps exclusively to your Patrons. Find more information here (https://faq.altstore.io/developers/patreon-integration).
>
> You can skip this if you want.

Branch on the developer's response:

- If they provided a URL: replace `source.json`'s top-level `patreonURL` field with that URL.
- If they declined, said no, or didn't give a URL: leave `patreonURL` exactly as the template has it. Don't replace it, don't delete it, don't write an empty string.

Don't replace any other key in either case.

### Step 1.7: Ask the developer for their fediverse username (PAL only)

Skip this step for Classic. For PAL, ask the developer:

> Would you like to federate your source? If so, what's your preferred username?
>
> By federating your source your apps and updates will appear automatically on AltStore's website, explore.alt.store, where anyone can easily discover them.
>
> You can skip this if you want.

Branch on the developer's response:

- If they provided a username: replace `source.json`'s top-level `fediUsername` field with just the name (`utm`, not `@utm@alt.store`).
- If they declined, said no, or didn't give one: leave `fediUsername` exactly as the template has it. Don't replace it, don't delete it, don't write an empty string.

Don't replace any other key in either case.

### Step 1.8: Present the baseline

**Compose the "filled in" line:** start from `Your source name, featuredApps and various app keys are filled in.` and, for whichever the developer gave in Steps 1.6–1.7, add `Patreon URL` and/or `fediUsername` to the list — e.g. `Your source name, featuredApps, various app keys and Patreon URL are filled in.`

**Then send this message, substituting the bracketed slots:**

> Here's your source JSON: `[absolute path to source.json]`.
>
> ```json
> [paste the entire current contents of source.json verbatim, preserving formatting]
> ```
>
> [Filled-in line, chosen above.]
>
> **⚠️ Some keys still have AltStore's example placeholder values. ⚠️**
>
> **You can upload this file to your web host now, then add the hosted file's URL in AltStore Classic on your phone to see it in action.**
>
> **Or I can help you with next steps — I can (1) guide you on hosting or (2) answer questions about specific keys and fill in placeholder values for you.**

## Stage 2: Edit and host, in the developer's preferred order

Stage 2 is editing the remaining placeholder values and hosting both `source.json` and the IPA/ADP. The developer picks the order: Host First runs Step 2.0 first; Edit First skips it. From Step 2.1 on, both are identical.

**Never say structural labels ("Stage 2," "Host First," "Step 2.0") to the developer** — from their point of view you're just helping with whatever they asked for next.

**Recognizing which path the developer wants** They pick a path at the end of Stage 1, but may also signal organically: *"how do I deploy it?"*, *"let me upload first"* → Host First; *"help me with the icon URL"*, *"I want to edit before I host"* → Edit First. If intent isn't clear, ask **one** disambiguating question without the path names — *"Want to set up hosting first, or work on filling in the rest of the source first?"*

### Step 2.0: Get `source.json` hosted (Host First only)

Help the developer upload only their `source.json`, not the IPA/ADP yet. Once it's hosted, have them add the source in AltStore on their phone; mention they can't download the app yet. Then ask:

> Want to replace the remaining placeholders now?

### Step 2.1: Replace the remaining placeholders

See [**Replace remaining placeholders**](#shared-procedure-replace-remaining-placeholders) below.

### Step 2.2: Validate against the live spec

See [**Validate against the live spec**](#shared-procedure-validate-against-the-live-spec) below.

### Step 2.3: Walk through hosting requirements for the IPA/ADP and `source.json`

Help the developer upload the IPA/ADP first, point `source.json`'s `downloadURL` at it, then have them upload `source.json` itself (replacing any already-hosted copy). For what `downloadURL` points at per spec, see the Make a Source page (URL in `references/living-docs.md`).

### Step 2.4: Confirm the `source.json` and IPA/ADP files are hosted

Once the developer says both files are hosted, have them check it in AltStore on their phone. For a new source, that's adding the source URL and downloading the app — if they don't have AltStore Classic on their phone yet, point them at the install guide for their computer: https://faq.altstore.io/altstore-classic/how-to-install-altstore-macos or https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows. For PAL direct them to https://altstore.io/download. For an update or an added app, the source is already in their AltStore — have them refresh it and confirm the new version or app shows up.

If the download fails, have them wait a couple of minutes and re-check — hosts need time to propagate.

### Step 2.5: Federate the source (only if they gave a fediverse username in Step 1.7)

Ask whether they still want to federate their source; on a yes, run the Federate Source command from the REST API page (URL in `references/living-docs.md`), passing their hosted `source.json` URL as `source`.

## Shared procedure: Identify the IPA/ADP and read its metadata

### 1. Find the IPA/ADP

Classic works from an `.ipa`, PAL from an ADP — a folder holding `manifest.json`, `signature`, and a `variant` directory, so look for that shape rather than an extension.

If the developer confirmed or named one, use it. Otherwise use the one in the working directory — if there's more than one, ask which. If there's none:

- **Classic** — if there's an `.xcodeproj` or `.xcworkspace`, offer to build one with `xcodebuild` (ad-hoc export); proceed only on an explicit yes.
- **PAL** — the developer must download the ADP using AltStore's REST API, keyed on the ADP ID of their notarized build; the REST API page (URL in `references/living-docs.md`) has the steps. Walk the developer through this.

### 2. Read the values

For Classic follow `references/ipa-metadata.md`, for PAL follow `references/adp-metadata.md`.

### 3. Record what you read

Keep the list of keys you filled.

## Shared procedure: Replace remaining placeholders

### 1. Send an initial message

**Before composing an initial message, list which keys still hold placeholder values:**
- **Source-level** — every top-level key except `apps`, `name` (Step 1.5 sets it), `featuredApps` (Step 1.4 sets it), and whichever of `patreonURL` and `fediUsername` the developer supplied (Steps 1.6 and 1.7).
- **App-level** — every `apps[0]` key except `versions` and the ones you recorded in [**Identify the IPA/ADP and read its metadata**](#shared-procedure-identify-the-ipaadp-and-read-its-metadata).
- **Version-level** — every `apps[0].versions[0]` key you didn't record, most importantly `downloadURL`, which the developer must set before the source works.

Go by the keys you recorded, not by how the values look. Then send this message, writing IPA for Classic or ADP for PAL:

> **⚠️ So you're aware, the following keys still have AltStore's example placeholder values. ⚠️**
>
> **Source-level keys**
>
> These show up on the catalog page users see when they paste your URL into AltStore — your storefront.
>
> `[bulleted list — one bullet per source-level placeholder key; each key in backticks followed by a short description]`
>
> **App-level keys (inside `apps[0]`)**
>
> These show up on the app's detail page inside AltStore.
>
> `[bulleted list — one bullet per app-level placeholder key; each key in backticks followed by a short description]`
>
> **Version-level keys (inside `apps[0].versions[0]`)**
>
> These describe this specific release — most importantly `downloadURL`, which AltStore needs to find your [IPA/ADP].
>
> `[bulleted list — one bullet per version-level placeholder key; each key in backticks followed by a short description]`
>
> I can answer questions about specific keys or fill in placeholder values for you based on what I know about your app. How would you like to proceed?

### 2. Using the spec as your reference, answer questions and fill values

First read the entire spec:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md
```

If you can't fetch the page, stop and tell the developer what went wrong. Identify each JSON object type it documents (Source, Apps, App Versions, App Permissions, Screenshots, News Items, Patreon, and any others present) and every field within each.

Then help the developer with whatever they have asked — explaining a key, filling in values you can infer from their app, answering questions while they edit. Answer in the spec's own wording, and check any value against the spec before you write it: if it would violate a constraint, explain what's needed and ask for a corrected one. The developer decides what changes — don't invent values they haven't asked for.

Continue the back-and-forth until the developer signals they're done with placeholders.

### 3. Mention what's possible beyond the basic source

Once they're done with placeholders, mention whichever of these two capabilities hasn't come up yet:

- **News items.** AltStore lets you post short announcements on your source page — things like 'New version released' or 'Now featured on X'. They're optional and your source is fine without them. If you want to add some, just tell me and we can come back to it.

- **Shipping updates.** You don't rebuild your source for a new version — you add an entry to the top of the `versions` array, upload the new `.ipa`/ADP, and re-publish `source.json`. AltStore then prompts existing users to update. The rules for what counts as 'newer' are on the Updating Apps page in the AltStore FAQ — I can walk you through them when it's time.

## Shared procedure: Validate against the live spec

*You* are the rule engine — there's no validator to call. If you haven't read the live spec yet, fetch it: https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md

### 1. Apply the rules, field by field

For every field in the developer's `source.json`, find its entry in the spec and check the field against it.

Object scope matters, because the same key name recurs at different levels with different rules: a top-level field uses `Source`; an entry in `apps[]` uses `Apps`; an entry in `versions[]` uses `App Versions`; an entry in a screenshots array uses `Screenshots`.

Check whatever the spec says — this list is a prompt of examples of what to look for, not a complete checklist:

- the value's **type**
- **required or optional** — treat an ambiguous marking as required and note the ambiguity
- a fixed set of **allowed values**
- **hint boxes** (`{% hint %}` blocks) carrying format, dimension, or conditional-requirement rules
- **cross-field rules** — uniqueness, ordering, "must reference an X elsewhere" — which live in an object's section intro or the page's overview prose

Judgement calls:

- A violation is an **error** when the spec says "must"/"cannot"/"required", a **warning** when it hedges ("recommended"/"should"/"may").
- A stated default means absence isn't a failure.
- Apply only what the spec actually says. Don't invent stricter rules than the wording supports, and don't work from memory — reread the spec.

Cite every finding: name the object and field, and quote the sentence you applied. That's what lets you re-find the text if the developer pushes back, and what makes the next pass auditable.

### 2. Tell the developer what you found

Note the findings, with their citations, before you speak. They're your working notes, not a deliverable: don't recite them, paste them, or point the developer at them. Errors block shipping; warnings never do.

- **No errors.** One short sentence: their source is validated and ready for the next step. Raise a warning only if it's actionable — *"Heads up: your `screenshots` is an empty array. That's allowed, but most sources include at least one. Want to add some?"*

- **Errors.** Don't dump the list. Take them one at a time and ask about each in plain language. Not *"apps[0].tintColor: hint-box constraint violated — value 'red' is not hexadecimal"* but *"Your tint color is 'red', but AltStore needs a hexadecimal format like `#F54F32`. What color do you want for your app's accent?"* Collect the fixes, re-validate, and loop until no errors remain.

Don't tell the developer their source is ready while an error is outstanding.

## Updating apps

Read the "Updating Apps" page (URL in `references/living-docs.md`) before answering update questions — detection rules in its Overview, upload steps in Update Instructions. Confirm which IPA/ADP is the new version and which app in their source it belongs to.

Run [**Identify the IPA/ADP and read its metadata**](#shared-procedure-identify-the-ipaadp-and-read-its-metadata) on it. Build this release's `versions[]` entry from the `versions[0]` values you read plus the existing top entry's other keys, ask for release notes for `localizedDescription`, and **prepend** it to that app's `versions[]`, leaving the existing entries alone.

Then continue from [**Step 2.2**](#step-22-validate-against-the-live-spec).

## Adding apps

Read the "Make a Source" page's `Apps` documentation (URL in `references/living-docs.md`) before answering app-addition questions. Confirm which IPA/ADP they'd like to add.

Run [**Identify the IPA/ADP and read its metadata**](#shared-procedure-identify-the-ipaadp-and-read-its-metadata) on it. Fetch a fresh copy of the canonical template for their flow (Step 1.1's URL) — don't save it over `source.json` — fill its `apps[0]` as Step 1.3 describes, and **append** that object to their `apps[]`, leaving the existing apps alone. The new entry's `bundleIdentifier` must not match an app already in the source — the spec forbids duplicates. Ask whether they want it added to `featuredApps`.

Then continue from [**Step 2.2**](#step-22-validate-against-the-live-spec).

## When the developer hits friction

- **"I changed my source's URL."** AltStore identifies a source by the URL users added, so existing users will see a brand-new source and need to re-add it. Keep the original URL live once published.
- **"Updates aren't showing up."** Rule out hosting first: (a) Is the new version entry in the hosted `source.json`? `curl` it. (b) Is a CDN serving stale JSON? If the hosted file is correct and current, it's a detection question — answer it from the page, not from memory (see [**Updating apps**](#updating-apps)).
- **"AltStore says `No value associated with key "X"`" or `"Hex code is invalid"` etc.** AltStore's `Codable` decoder rejected the source, so your validation walkthrough missed something. Reread the spec's entry for `X` — it almost certainly marks `X` required, or carries a constraint your value violates — then redo the walkthrough, supply a real value, and re-validate. If the spec genuinely doesn't mention `X`, that's a docs gap: file it with the AltStore team. The docs are the spec — never reconcile them with the decoder yourself, not with a made-up value, not with prose added to this file.
