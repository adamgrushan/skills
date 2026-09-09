---
name: altstore-classic-distribution
description: Help iOS developers manage an AltStore Classic source — create a source, update an app in their source, or add apps to their source. Use when a developer says things like "AltStore Classic", "make a source", "host my IPA so users can install it", "update my app", "update my source", or "add an app to my source". The skill generates a valid source JSON from an IPA, validates it against the live spec, and gives hosting guidance.
---

# AltStore Classic Distribution

## Working contract

Two rules:

- **Never upload on the developer's behalf unless they explicitly ask.** No `curl`-uploads, `scp`, `rsync`, `aws s3 cp`, `gh release upload`, `git push` to a Pages repo, or any other write to a public web host — including any harness or MCP tool that would do it for you. You tell them what their host needs and flag problems with what they describe; they run the upload.

- **Don't narrate your work.** Speak when you have a question or a result; otherwise stay quiet. Don't preface tool calls ("Let me look that key up in the spec...") or summarize what you just did ("OK, I've filled in your source!"). **The one exception is a heads-up this file writes for you** — like Step 1.1's kickoff or the ⏳ line before the spec fetch. Send those as written; add none of your own.

## References

- `references/distribute-with-altstore-classic.md` — the developer-facing primer; read it for setup questions this file doesn't cover.
- `references/hosting-guidance.md` — the source of truth for hosting.
- `references/living-docs.md` — the AltStore FAQ pages: raw URLs to fetch, rendered URLs to share.
- `references/ipa-metadata.md` — the commands for reading app metadata out of an IPA.

## Which flow you're in

- **No source yet** → [**Stage 1**](#stage-1-build-the-baseline-sourcejson) and [**Stage 2**](#stage-2-edit-and-host-in-the-developers-preferred-order).
- **Adding an app to an existing source** → [**Adding apps**](#adding-apps).
- **Shipping a new version of an app** → [**Updating apps**](#updating-apps).

## Stage 1: Build the baseline source.json

### Step 1.1: Fetch and edit the canonical template

Tell the developer you're fetching the template and reading their IPA.

Download AltStore's canonical `ClassicSourceExampleForSkill.json` example:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/.gitbook/assets/ClassicSourceExampleForSkill.json
```

Before saving, check whether `source.json` already exists in the working directory. If it does, ask whether they meant to [add an app](#adding-apps) or [ship an update](#updating-apps) — saving now would replace a source they may have already published. Overwrite only if they plainly say they want to start over.

Otherwise save it as `source.json` in the developer's working directory. Every value is still a placeholder from AltStore's template. Stage 1 replaces a small set: the IPA-derivable ones, the source name, `featuredApps`, and possibly `patreonURL`. Stage 2 handles the rest.

If you can't fetch the template, stop and tell the developer what went wrong. Don't write `source.json` from memory instead.

### Step 1.2: Identify the IPA and read its metadata

See [**Identify the IPA and read its metadata**](#shared-procedure-identify-the-ipa-and-read-its-metadata) below.

### Step 1.3: Fill the template's app entry

Write the values you read into `source.json`'s `apps[0]` and its `versions[0]`, overwriting the template's. `buildVersion` and `minOSVersion` are new keys in `versions[0]`. Change nothing else.

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

- If they provided a URL: replace source.json's top-level `patreonURL` field with that URL.
- If they declined, said no, or didn't give a URL: leave `patreonURL` exactly as the template has it. Don't replace it, don't delete it, don't write an empty string.

Don't replace any other key in either case.

### Step 1.7: Present the baseline

**Before composing the message, gather two things:**
- Whether `patreonURL` holds the developer's real URL, or still holds the template's example value (they declined).
- The full current contents of `source.json`.

**Choose the "filled in" line:**
- If Patreon was provided: `Your source name, featuredApps, various app keys and Patreon URL are filled in.`
- If they declined: `Your source name, featuredApps and various app keys are filled in.`

**Then send this message, substituting the bracketed slots:**

> Here's your source JSON: `[absolute path to source.json]`. 
>
> ```json
> [paste the entire current contents of source.json verbatim, preserving formatting]
> ```
>
> [Filled-in line, chosen above.]
> 
> **⚠️ Some keys still have AltStore's example placeholder values.⚠️**
>
> **You can upload this file to your web host now, then add the hosted file's URL in AltStore Classic on your phone to see it in action.**
>
> **Or I can help you with next steps — I can (1) guide you on hosting or (2) answer questions about specific keys and fill in placeholder values for you.**

## Stage 2: edit and host, in the developer's preferred order

Stage 2 is editing the remaining placeholder values and hosting `source.json` + the IPA. The developer picks the order: Host First runs Step 2.0 first, Edit First skips it. From Step 2.1 on, both are identical.

**Never say these labels to the developer.** Not "Stage 2," not "the Host First path," not "Step 2.0," nor any other structural label. From their point of view you're just helping with whatever they asked for next.

**Recognizing which path the developer wants** — they pick at the end of Stage 1, but may also signal organically:

- *"I'll host it now"*, *"how do I deploy it?"*, *"walk me through hosting"*, *"let me upload first"* → Host First.
- *"let me fill in the rest first"*, *"help me with the icon URL"*, *"what's a good description?"*, *"I want to edit before I host"* → Edit First.

If the developer's intent isn't clear, ask **one** disambiguating question without using the path names. Example: *"Want to set up hosting first, or work on filling in the rest of the source first?"*

### Step 2.0 — Host First only: get `source.json` hosted

Help the developer upload only their `source.json`, not the IPA yet — see `references/hosting-guidance.md`. Once it's hosted, have them add the source in AltStore; mention they can't download the app yet. Then ask:

> Want to replace the remaining placeholders now?

### Step 2.1: Replace the remaining placeholders

See [**Replace remaining placeholders**](#shared-procedure-replace-remaining-placeholders) below.

### Step 2.2: Validate against the live spec

See [**Validate against the live spec**](#shared-procedure-validate-against-the-live-spec) below.

### Step 2.3: Walk through hosting requirements for the IPA and `source.json`

Help the developer upload their IPA file first, then update `source.json`'s downloadURL to point at it, then help them upload `source.json` itself. If `source.json` is already hosted, the latest `source.json` replaces the old copy.

Refer to `references/hosting-guidance.md`.

### Step 2.4: Confirm the `source.json` and IPA files are hosted

Once the developer says both files are hosted, have them check it in AltStore. For a new source, that's adding the source URL and downloading the app — if they don't have AltStore Classic on their phone yet, point them at the install guide for their computer: https://faq.altstore.io/altstore-classic/how-to-install-altstore-macos or https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows. For an update or an added app, the source is already in their AltStore — have them refresh it and confirm the new version or app shows up.

If the download fails, have them wait a couple of minutes and re-check — hosts need time to propagate.

## Shared procedure: Identify the IPA and read its metadata

Stop once you have the values; where they go differs per flow, so return to the step that sent you here.

**Which IPA:** the one the developer confirmed, if the sending section had them confirm one; otherwise the `.ipa` in the working directory — ask if there's more than one. If there's none but there is an `.xcodeproj` or `.xcworkspace`, offer to build one with xcodebuild (ad-hoc export); proceed only on an explicit yes.

**Read the values** in `references/ipa-metadata.md` — it gives the command for each and what to do when one can't be read. Record which keys you read; Step 2.1 works from that list.

## Shared procedure: Replace remaining placeholders

**Do this in the order below** — the message first, so the developer reads while you read the spec.

### 1. Send an initial message and read the live spec

**Before composing an initial message, list which keys still hold placeholder values:**
- **Source-level** — every top-level key except `apps`, `name` (Step 1.5 sets it), `featuredApps` (Step 1.4 sets it), and `patreonURL` if the developer supplied one.
- **App-level** — every `apps[0]` key except `versions` and the ones you recorded in [**Identify the IPA and read its metadata**](#shared-procedure-identify-the-ipa-and-read-its-metadata).
- **Version-level** — every `apps[0].versions[0]` key you didn't record, most importantly `downloadURL`, which the developer must set before the source works.

Go by the keys you recorded, not by how the values look. Then send this message:

>  **⚠️ So you're aware, the following keys still have AltStore's example placeholder values. ⚠️**
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
> These describe this specific release — most importantly `downloadURL`, which AltStore needs to find your IPA.
>
> `[bulleted list — one bullet per version-level placeholder key; each key in backticks followed by a short description]`
> 
> ⏳ Before editing the placeholder values I'll need to refer to the live spec from AltStore documentation. Bear with me for a few minutes while I do that. ⏳

Then fetch the spec at:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md
```

If you can't fetch the page, stop and tell the developer what went wrong.

Read the entire page. Identify each JSON object type it documents (Source, Apps, App Versions, App Permissions, Screenshots, News Items, Patreon, and any others present) and every field within each.

Then say:

> Alright I'm ready to answer questions about specific keys or fill in placeholder values for you. I can even fill in as many placeholder values as I can based on what I know about your app, if you'd like. How would you like to proceed?

### 2. Answer questions and fill values, using the spec as your reference

Help the developer with whatever they ask — explaining a key, filling in values you can infer from their app, answering questions while they edit. Answer in the spec's own wording, and check any value against the spec before you write it: if it would violate a constraint, explain what's needed and ask for a corrected one. The developer decides what changes — don't invent values they haven't asked for.

If they say they'll edit on their own, confirm briefly — *"Got it. Ping me with questions, or let me know when you're ready and I'll validate the source."*

Continue the back-and-forth until the developer signals they're done with placeholders.

### 3. Mention what's possible beyond the basic source

Once they're done with placeholders, mention two capabilities that didn't come up:

- **News items.** AltStore lets you post short announcements on your source page — things like 'New version released' or 'Now featured on X'. They're optional and your source is fine without them. If you want to add some, just tell me and we can come back to it.

- **Shipping updates.** You don't rebuild your source for a new version — you add an entry to the top of the `versions` array, upload the new `.ipa`, and re-publish `source.json`. AltStore then prompts existing users to update. The rules for what counts as 'newer' are on the Updating Apps page in the AltStore FAQ — I can walk you through them when it's time.

## Shared procedure: Validate against the live spec

*You* are the rule engine — there's no validator to call. If you haven't read the live spec yet, fetch it: https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md

### 1. Apply the rules, field by field

For every field in the developer's `source.json`, find its entry in the spec and check the field against it.

Object scope matters, because the same key name recurs at different levels with different rules: a top-level field uses `Source`; an entry in `apps[]` uses `Apps`; an entry in `versions[]` uses `App Versions`; an entry in a screenshots array uses `Screenshots`.

Expect to check:

- a stated **type** for the value
- whether the field is **required or optional** — treat an ambiguous marking as required and note the ambiguity
- a fixed set of **allowed values**
- **hint boxes** (`{% hint %}` blocks) carrying format, dimension, or conditional-requirement rules
- **cross-field rules** that don't belong to any one field — uniqueness, ordering, "must reference an X elsewhere" — which live in an object's section intro or the page's overview prose

That list is a prompt for what to look for, not a checklist to fill in — check whatever the spec says, including what the list doesn't anticipate.

Judgement calls:

- A violation is an **error** when the spec says "must"/"cannot"/"required", a **warning** when it hedges ("recommended"/"should"/"may").
- A stated default means absence isn't a failure.
- Apply only what the spec actually says. Don't invent stricter rules than the wording supports, and don't work from memory — reread the spec.

Cite every finding: name the object and field, and quote the sentence you applied. That's what lets you re-find the text if the developer pushes back, and what makes the next pass auditable.

### 2. Emit a structured report (internal — do NOT share with the developer)

Write the findings down **for yourself** before you say anything — it's how you decide whether to block, what to raise, and what to recheck. **Don't paste it into the conversation, read it out, or point the developer at a written copy.**

```
Status: 0 = no errors (warnings are fine)
        1 = at least one error — don't ship until fixed

Errors:
  - <json path>: <what's wrong>
    (<Object> > <field> — "<the sentence you applied>")

Warnings:
  - <json path>: <what's worth raising>
```

### 3. How to communicate validation results to the developer

Translate the findings into plain conversation.

- **Status 0.** One short sentence: their source is validated and ready for the next step. Raise a warning only if it's actionable — *"Heads up: your `screenshots` is an empty array. That's allowed, but most sources include at least one. Want to add some?"*

- **Status 1.** Don't dump the list. Take the errors one at a time and ask about each in plain language. Not *"apps[0].tintColor: hint-box constraint violated — value 'red' is not hexadecimal"* but *"Your tint color is 'red', but AltStore needs a hexadecimal format like `#F54F32`. What color do you want for your source's accent?"* Collect the fixes, re-validate, and loop until status is 0.

Don't tell the developer their source is ready until the structured report produces a status of 0.

## Updating apps

The "Updating Apps" page (URL in `references/living-docs.md`) is the source of truth. Read it before answering update questions — detection rules in its Overview, upload steps in Update Instructions. Confirm which IPA is the new version and which app in their source it belongs to.

Read the new IPA's metadata with [**Identify the IPA and read its metadata**](#shared-procedure-identify-the-ipa-and-read-its-metadata). Build this release's `versions[]` entry from the `versions[0]` values you read plus the existing top entry's other keys, ask for this release's notes for `localizedDescription`, and **prepend** it to that app's `versions[]`. The existing entries stay.

Once the new version entry is in place, continue from [**Step 2.2**](#step-22-validate-against-the-live-spec) — validate, host the new IPA and the updated `source.json`, then confirm.

## Adding apps

The "Make a Source" page (URL in `references/living-docs.md`) is the source of truth. Read its `Apps` key documentation before answering app-addition questions. Confirm which IPA they'd like to add.

Read the new IPA's metadata with [**Identify the IPA and read its metadata**](#shared-procedure-identify-the-ipa-and-read-its-metadata). Fetch a fresh copy of the canonical template (Step 1.1's URL) — don't save it over `source.json` — fill its `apps[0]` as Step 1.3 describes, and **append** that object to their `apps[]`. Every app already there stays as it is.

The new entry's `bundleIdentifier` must not match an app already in the source — the spec forbids duplicates. Ask whether they want it added to `featuredApps`.

Once the new app entry is in place, continue from [**Step 2.2**](#step-22-validate-against-the-live-spec) — validate, host the new IPA and the updated `source.json`, then confirm.

## When the developer hits friction

- **"I changed my source's URL."** AltStore identifies a source by the URL users added, so existing users will see a brand-new source and need to re-add it. Keep the original URL live once published.
- **"Updates aren't showing up."** Rule out hosting first: (a) is the new version entry in the hosted `source.json`? `curl` it. (b) Is a CDN serving stale JSON? If the hosted file is correct and current, it's a detection question — answer it from the page, not from memory (see [**Updating apps**](#updating-apps)).
- **"AltStore says `No value associated with key "X"`" or `"Hex code is invalid"` etc.** That's AltStore's Swift `Codable` decoder rejecting your source. The fix path is: (1) reread the spec's entry for field `X` carefully; (2) the docs almost certainly mark `X` as required, or carry a constraint in the body that your value violates, and your validation walkthrough missed it — redo that walkthrough more carefully; (3) supply a real value and re-validate. If the docs genuinely don't mention `X` at all, that's a docs gap — file it with the AltStore team rather than papering over it in this skill. The docs are the spec. If they and AltStore's decoder disagree, don't reconcile them yourself — not with a made-up value, not with prose added to this file.
