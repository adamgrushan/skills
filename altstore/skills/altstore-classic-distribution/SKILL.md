---
name: altstore-classic-distribution
description: Help iOS developers manage an AltStore Classic source — create a source, update an app in their source, or add apps to their source. Use when a developer says things like "AltStore Classic", "make a source", "host my IPA so users can install it", "update my app", "update my source", or "add an app to my source". The skill generates a valid source JSON from an IPA, validates it against the live spec, and gives hosting guidance.
---

# AltStore Classic Distribution

Help a developer create or manage a working AltStore Classic source that real users can add in the AltStore app.

## Working contract

Two rules:

- **Never upload on the developer's behalf unless they explicitly ask.** No `curl`-uploads, `scp`, `rsync`, `aws s3 cp`, `gh release upload`, `git push` to a Pages repo, or any other write to a public web host — including any harness or MCP tool that would do it for you. You tell them what their host needs and flag problems with what they describe; they run the upload.

- **Don't narrate your work.** Speak when you have a question or a result; otherwise stay quiet. Don't preface tool calls ("Let me look that key up in the spec...") or summarize what you just did ("OK, I've enriched the source!"). **The one exception is a heads-up this file scripts for you** — like Step 1.1's kickoff or the ⏳ line before the spec fetch. Send those as written; add none of your own.

## References

`references/distribute-with-altstore-classic.md` is the developer-facing primer. Read it — it covers setup questions this file doesn't.

`references/hosting-guidance.md` is the source of truth for hosting guidance.

`references/living-docs.md` points at the canonical AltStore FAQ pages — both the raw markdown URLs the validation step fetches and the rendered URLs you'd link to the developer in conversation.

## Which flow you're in

- **No source yet** → [**Stage 1**](#stage-1-build-the-baseline-sourcejson) and [**Stage 2**](#stage-2-edit-and-host-in-the-developers-preferred-order).
- **Adding an app to an existing source** → [**Adding apps**](#adding-apps).
- **Shipping a new version of an app** → [**Updating apps**](#updating-apps).

## Stage 1: Build the baseline source.json

### Step 1.1: Fetch and edit the canonical template

Tell the user you are getting started fetching the template, identifying the IPA file, and enriching the template from the IPA.

Download AltStore's canonical `ClassicSourceExampleForSkill.json` example:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/.gitbook/assets/ClassicSourceExampleForSkill.json
```

Before saving, check whether `source.json` already exists in the working directory. If it does, you are probably not building a new source — ask whether they meant to [add an app](#adding-apps) or [ship an update](#updating-apps) to the one they have. It may be a source they've already published, and this step would replace it with AltStore's example JSON. Overwrite only if they say plainly that they want to start over.

Otherwise save it as `source.json` in the developer's working directory. Every value inside it is still a placeholder from AltStore's template. Stage 1 replaces a small set of those (the IPA-derivable ones, the source name, `featuredApps`, and possibly `patreonURL`). Stage 2 handles the rest.

If you can't fetch the template, stop and tell the developer what went wrong. Don't write `source.json` from memory instead.

### Step 1.2: Identify the IPA file and extract its app entry

Identify the IPA file in the working directory. If you can't find one, check for an `.xcodeproj` or `.xcworkspace` — if present, ask the developer if they'd like you to build the IPA with xcodebuild (ad-hoc export). Only proceed on explicit yes; on success, use the produced .ipa for the rest of Stage 1. Then run the extraction script:

```bash
python3 scripts/enrich_source.py \
  --ipa ./MyApp.ipa \
  --template ./source.json
```

It writes nothing. It prints an `---BEGIN APP_ENTRY---` block — a complete app object with every field this IPA could supply filled in, and AltStore's example values left wherever nothing was derivable — followed by a `---BEGIN PLACEHOLDERS_REPORT---` block naming what's still a placeholder. Where that app entry goes is the next step's decision, and it differs per flow, which is why the script never writes it anywhere itself.

For the field-by-field mapping and edge-case behavior (an IPA with no embedded provisioning profile, an app that declares no privacy usage descriptions, why `developerName` isn't always the display name the developer wants), see the docstrings and comments in `scripts/enrich_source.py` — you only need those when something surprising happens.

### Step 1.3: Replace the template's app entry

Replace `source.json`'s `apps[0]` with the `APP_ENTRY` object from Step 1.2, verbatim. The template ships exactly one example app, and this is the developer's app taking its place.

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

**Never say these labels to the developer.** Don't say "we're entering Stage 2," "this is the Host First path," "Step 2.0," or any structural label. From the developer's point of view, you're just helping them with whatever they asked for next. They never need to know there are two paths or that the skill has stages at all.

**Recognizing which path the developer wants** — they pick at the end of Stage 1, but they may also signal organically. Treat any of these as a path signal:

- *"I'll host it now"*, *"how do I deploy it?"*, *"walk me through hosting"*, *"let me upload first"* → Host First.
- *"let me fill in the rest first"*, *"help me with the icon URL"*, *"what's a good description?"*, *"I want to edit before I host"* → Edit First.

If the developer's intent isn't clear, ask **one** disambiguating question without using the path names. Example: *"Want to set up hosting first, or work on filling in the rest of the source first?"*

Once you've identified the path, start at Step 2.0 for Host First or Step 2.1 for Edit First, and proceed silently. Don't announce the choice ("OK, we'll do Edit First!") — just begin the work.

### Step 2.0 — Host First only: get `source.json` hosted

Help the developer upload only their `source.json` file. Ignore their IPA file for now. Refer to `references/hosting-guidance.md`. Once the developer says they've hosted the `source.json` file, have them try to add the source in AltStore. Mention that they won't be able to download their app yet. Then ask:

> Want to replace the remaining placeholders now?

### Step 2.1: Replace the remaining placeholders

See [**Replace remaining placeholders**](#shared-procedure-replace-remaining-placeholders) below.

### Step 2.2: Validate against the live spec

See [**Validate against the live spec**](#shared-procedure-validate-against-the-live-spec) below.

### Step 2.3: Walk through hosting requirements for the IPA and `source.json`

Help the developer upload their IPA file first, then update `source.json`'s downloadURL to point at it, then help them upload `source.json` itself. If `source.json` is already hosted, the latest `source.json` replaces the old copy.

Refer to `references/hosting-guidance.md`.

### Step 2.4: Confirm the `source.json` and IPA files are hosted

Once the developer says both files are hosted, have them check it in AltStore. For a new source, that's adding the source URL and downloading the app — if they don't have AltStore Classic on their phone yet, point them at the install guide for their computer — https://faq.altstore.io/altstore-classic/how-to-install-altstore-macos or https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows — and pick this back up once it's installed. For an update or an added app, the source is already in their AltStore — have them refresh it and confirm the new version or app shows up.

If they can't download the app, most hosts take a few minutes to build and propagate — have them wait a couple of minutes and re-check before debugging further.

## Shared procedure: Replace remaining placeholders

**Do this in the order below** — the message comes first so the developer has something to read; reading the spec happens in parallel with the developer's reading time; the back-and-forth uses the spec as its reference.

### 1. Send an initial message and read the live spec

**Before composing an initial message, gather:**
- The placeholders report that `enrich_source.py` printed to stdout, between the `---BEGIN PLACEHOLDERS_REPORT---` and `---END PLACEHOLDERS_REPORT---` markers in Step 1.2's output. Parse the JSON between those markers. It contains:
  - `source_level.untouched` — top-level keys still on placeholder values.
  - `app_level.untouched` — `apps[0]` keys still on placeholder values.
  - `version_level.untouched` — `apps[0].versions[0]` keys still on placeholder values (most importantly `downloadURL`, which the developer must set before the source works).
  - `caller_should_filter` — keys the report snapshotted before Stage 1 wrote them, so you must decide their status: drop `featuredApps` (Step 1.4 always sets it) and `name` (Step 1.5 always sets it); drop `patreonURL` only if the developer supplied one, keep it if they declined.

Use the report's lists verbatim — don't re-derive placeholder keys by reading the JSON yourself. The script is the source of truth here. Then send this message:

>  **⚠️ So you're aware, the following keys still have AltStore's example placeholder values. ⚠️**
>
> **Source-level keys**
>
> These show up on the catalog page users see when they paste your URL into AltStore — your storefront. 
>
> `[bulleted list — one bullet per key in source_level.untouched from the report (after applying caller_should_filter); each key in backticks followed by a short description]`
>
> **App-level keys (inside `apps[0]`)** 
>
> These show up on the app's detail page inside AltStore.
>
> `[bulleted list — one bullet per key in app_level.untouched from the report; each key in backticks followed by a short description]`
>
> **Version-level keys (inside `apps[0].versions[0]`)**
>
> These describe this specific release — most importantly `downloadURL`, which AltStore needs to find your IPA.
>
> `[bulleted list — one bullet per key in version_level.untouched from the report; each key in backticks followed by a short description]`
> 
> ⏳ Before editing the placeholder values I'll need to refer to the live spec from AltStore documentation. Bear with me for a few minutes while I do that. ⏳

Then fetch the spec at:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md
```

Use whatever URL-fetching tool your harness gives you. Use the raw markdown URL above, not the rendered page at `faq.altstore.io` — the rendered version omits authoring cues that make accurate extraction easier. If you cannot fetch the page, stop and tell the developer what went wrong.

Then, read the spec for understanding. Read the entire page. Identify each JSON object type it documents (Source, Apps, App Versions, App Permissions, Screenshots, News Items, Patreon, and any others present), and within each object type, identify every individual field.

Then say:

> Alright I'm ready to answer questions about specific keys or fill in placeholder values for you. I can even fill in as many placeholder values as I can based on what I know about your app, if you'd like. How would you like to proceed?

### 2. Answer questions and fill values, using the spec as your reference

Help the developer with whatever they ask for — explaining a key, filling in values you can infer from their app, answering questions while they edit themselves. Use the spec as your reference throughout: answer in the spec's own wording rather than your paraphrase, and check any value you're about to write against the spec first. If a value would violate a constraint, explain what's needed and ask for a corrected one rather than writing something AltStore will reject. The developer decides what changes — don't invent values they haven't asked for.

If they say they'll edit on their own, confirm briefly — *"Got it. Ping me with questions, or let me know when you're ready and I'll validate the source."*

Continue the back-and-forth until the developer signals they're done with placeholders.

### 3. Mention what's possible beyond the basic source

Once the developer is done with placeholders — and before proceeding to validation — mention two capabilities the spec supports that didn't come up:

- **News items.** AltStore lets you post short announcements on your source page — things like 'New version released' or 'Now featured on X'. They're optional and your source is fine without them. If you want to add some, just tell me and we can come back to it.

- **Shipping updates.** When you release a new version of your app, you don't rebuild your source from scratch. You add a new entry to the top of the `versions` array, upload the new `.ipa` to a new URL, and re-publish `source.json`. AltStore polls your source URL and prompts existing users to update. The exact rules for how AltStore decides what counts as 'newer' live on the Updating Apps page in the AltStore FAQ — I can walk you through them when it's time.

## Shared procedure: Validate against the live spec

*You* are the rule engine. There's no validator to call. Read the live spec first if you haven't already — the URL and fetch instructions are in step 1 of [**Replace remaining placeholders**](#shared-procedure-replace-remaining-placeholders).

### 1. Apply the rules, field by field

For every field that appears in the developer's `source.json`, find its matching entry in the spec and check it against the spec.

Object scope matters, because the same key name recurs at different levels with different rules: a top-level field uses `Source`; an entry in `apps[]` uses `Apps`; an entry in `versions[]` uses `App Versions`; an entry in a screenshots array uses `Screenshots`.

Expect to check several bits:

- a stated **type** for the value
- whether the field is **required or optional** — if the marking is ambiguous, treat it as required and note the ambiguity
- a fixed set of **allowed values**
- **hint boxes** (`{% hint %}` blocks) carrying format, dimension, or conditional-requirement rules
- **cross-field rules** that don't belong to any one field — uniqueness, ordering, "must reference an X elsewhere" — which live in an object's section intro or the page's overview prose

That list is a prompt for what to look for, not a checklist to fill in. The spec is the authority; check whatever it actually says, including anything the list doesn't anticipate.

There are also judgement calls you may have to make:

- A field in the JSON that the spec doesn't document is a **warning**, never an error — you may have missed it when reading the spec.
- A violation is an **error** when the spec says "must" / "cannot" / "required", and a **warning** when it hedges ("recommended" / "should" / "may").
- A stated default means absence isn't a failure.
- Apply only what the spec actually says. Don't invent stricter rules than the wording supports, and don't work from memory — reread the spec.

Cite every finding: name the object and field, and quote the sentence you applied. That's what lets you re-find the text if the developer pushes back, and what makes the next pass auditable.

### 2. Emit a structured report (internal — do NOT share with the developer)

Write the findings down **for yourself** before you say anything. It's what you use to decide whether to block, what to raise, and what to recheck next pass. **Don't paste it into the conversation, don't read it out, and don't hand the developer a path to a written copy.**

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

Translate the findings into plain conversation — never show the report.

- **Status 0.** One short sentence: their source is validated and ready for the next step. Raise a warning only if it's actionable — *"Heads up: your `screenshots` is an empty array. That's allowed, but most sources include at least one. Want to add some?"* Skip the housekeeping ones.

- **Status 1.** Don't dump the list. Take the errors one at a time and ask about each in plain language. Not *"apps[0].tintColor: hint-box constraint violated — value 'red' is not hexadecimal"* but *"Your tint color is 'red', but AltStore needs a hexadecimal format like `#F54F32`. What color do you want for your source's accent?"* Collect the fixes, re-validate, and loop until status is 0.

Don't tell the developer their source is ready until the structured report produces a status of 0.

## Updating apps

The "Updating Apps" page in `references/living-docs.md` is the source of truth for updating apps. Read it before answering app update questions — the detection rules are in its Overview, the upload steps in Update Instructions. Confirm with the developer which IPA is the new version, and which app in their source it belongs to.

Extract its app entry with [**Step 1.2**](#step-12-identify-the-ipa-file-and-extract-its-app-entry), pointing `--template` at a fresh copy of the canonical template rather than at their source. Take only the entry's `versions[0]` — that's this release's `version`, `buildVersion`, `minOSVersion`, `date`, and `size` — and **prepend** it to that app's `versions[]`. The existing entries stay; AltStore reads the array's first entry as the latest release.

Once the new version entry is in place, continue from [**Step 2.2**](#step-22-validate-against-the-live-spec) — validate, host the new IPA and the updated `source.json`, then confirm.

## Adding apps

The "Make a Source" page in `references/living-docs.md` is the source of truth for adding apps. Read the `Apps` key documentation on the page before answering app addition questions. Confirm with the developer which IPA they'd like to add.

Extract its app entry with [**Step 1.2**](#step-12-identify-the-ipa-file-and-extract-its-app-entry), pointing `--template` at a fresh copy of the canonical template rather than at their source. Then **append** that entry to their existing `apps[]`. Step 1.3 replaces `apps[0]` because a new source has only AltStore's example app sitting there; here every app already in the source stays exactly as it is.

The new entry's `bundleIdentifier` must not match an app already in the source — the spec forbids duplicates. Ask whether they want it added to `featuredApps`.

Once the new app entry is in place, continue from [**Step 2.2**](#step-22-validate-against-the-live-spec) — validate, host the new IPA and the updated `source.json`, then confirm.

## When the developer hits friction

- **"I changed the source identifier."** Existing users will see it as a brand-new source and will need to re-add it. Don't change `identifier` once published.
- **"Updates aren't showing up."** Rule out the hosting side first: (a) is the new version entry actually in the hosted `source.json`? `curl` it. (b) Is a CDN serving stale JSON? If the hosted file is correct and current, it's a detection question — answer it from the page rather than from memory (see [**Updating apps**](#updating-apps)).
- **"AltStore says `No value associated with key "X"`" or `"Hex code is invalid"` etc.** That's AltStore's Swift `Codable` decoder rejecting your source. The fix path is: (1) reread the entry for field `X` in the spec carefully; (2) the docs almost certainly mark `X` as required, or carry a constraint in the body that your value violates, and your validation walkthrough missed it — redo that walkthrough more carefully; (3) supply a real value and re-validate. If the docs genuinely don't mention `X` at all, that's a docs gap — file it with the AltStore team rather than papering over it in this skill. The whole point of this design is that the docs are the spec. If the docs and AltStore's decoder disagree, neither code in this repo nor prose in this file should try to reconcile them.
