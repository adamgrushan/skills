---
name: altstore-pal-distribution
description: Help iOS developers manage an AltStore PAL source — update an app in their source, or add apps to their source. Use when a developer says things like "AltStore PAL", "host my ADP", "update my app", "update my source", or "add an app to my source". The skill builds the new entry from the app's ADP, validates the source JSON against the live spec, and gives hosting guidance.
---

# AltStore PAL Distribution

## Working contract

Two rules:

- **Never upload on the developer's behalf unless they explicitly ask.** No `curl`-uploads, `scp`, `rsync`, `aws s3 cp`, `gh release upload`, `git push` to a repo, or any other write to a public web host — including any harness or MCP tool that would do it for you. You tell them what their host needs and flag problems with what they describe; they run the upload.

- **Don't narrate your work.** Speak when you have a question or a result; otherwise stay quiet. Don't preface tool calls ("Let me look that key up in the spec...") or summarize what you just did ("OK, I've added your new version!"). **The one exception is a heads-up this file writes for you** — like the ⏳ line before the spec fetch. Send those as written; add none of your own.

## References

- `references/living-docs.md` — the AltStore FAQ pages: raw URLs to fetch, rendered URLs to share.
- `references/adp-metadata.md` — the commands for reading app metadata out of an ADP.
- `references/distribute-with-altstore-pal.md` — the developer-facing primer; read it for setup questions this file doesn't cover.
- `references/hosting-guidance.md` — the source of truth for hosting.

## Which flow you're in

- **Adding an app to an existing source** → [**Adding apps**](#adding-apps).
- **Shipping a new version of an app** → [**Updating apps**](#updating-apps).

Both assume two things: the developer already has a `source.json`, and Apple has notarized their build and AltStore has processed it, so there's an ADP in hand. `references/distribute-with-altstore-pal.md` covers everything that comes before that.

## Validate and host

Both flows land here once the new entry is written into `source.json`.

**Never say these labels to the developer.** Not "Step 1," not "the Adding apps flow," nor any other structural label. From their point of view you're just helping with whatever they asked for next.

### Step 1: Validate against the live spec

See [**Validate against the live spec**](#shared-procedure-validate-against-the-live-spec) below.

### Step 2: Walk through hosting requirements for the ADP and `source.json`

Help the developer upload their ADP first, then update `source.json`'s `downloadURL` to point at it, then help them upload `source.json` itself. The latest `source.json` replaces the old copy.

An ADP is a directory, so uploading it means every file in it — hierarchy intact, contents untouched. Refer to `references/hosting-guidance.md`.

### Step 3: Confirm the `source.json` and ADP are hosted

Once the developer says both are hosted, have them check it in AltStore PAL on their phone. The source is already in their AltStore — have them refresh it and confirm the new version or app shows up.

AltStore PAL only installs in the EU, Japan, and Brazil, so a developer outside those regions can't check on their own device and will need someone who can.

If the download fails, have them wait a couple of minutes and re-check — hosts need time to propagate.

## Shared procedure: Identify the ADP and read its metadata

### 1. Find the ADP

If the developer confirmed or named one, use it. Otherwise use the ADP in the working directory — if there's more than one, ask which. An ADP is a folder holding `manifest.json`, `signature`, and a `variant` directory, so look for that shape rather than for an extension.

If there's none, they'll need to download it — an ADP comes from AltStore's REST API, keyed on the ADP ID of the notarized build, and can't be built locally. `references/living-docs.md` has the page.

### 2. Read the values

Follow `references/adp-metadata.md`. It lists each value, the command that reads it, and what to do when one can't be read.

### 3. Record what you read

Keep the list of keys you filled.

## Shared procedure: Validate against the live spec

*You* are the rule engine — there's no validator to call. If you've already read the live spec, start at step 1. Otherwise send this first, so the developer reads while you read the spec:

> ⏳ Before I validate your source I'll need to refer to the live spec from AltStore documentation. Bear with me while I do that. ⏳

Then fetch it:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md
```

If you can't fetch the page, stop and tell the developer what went wrong.

### 1. Apply the rules, field by field

For every field in the developer's `source.json`, find its entry in the spec and check the field against it.

Object scope matters, because the same key name recurs at different levels with different rules: a top-level field uses `Source`; an entry in `apps[]` uses `Apps`; an entry in `versions[]` uses `App Versions`; an entry in a screenshots array uses `Screenshots`.

One page covers both PAL and Classic, and some entries split between them — `marketplaceID`'s hint box, and `downloadURL`'s and `size`'s per-app-store headings, for three. Apply the PAL side of any such split.

Four values also have to agree with the ADP the entry points at. The spec ties `version` and `buildVersion` to `CFBundleShortVersionString` and `CFBundleVersion` and `marketplaceID` to the notarized app's Apple ID, and for a notarized build all three live in `manifest.json` — as `shortVersionString`, `bundleVersion`, and `appleItemId` — alongside `bundleId`, which is `bundleIdentifier`. Diff all four against the manifest and treat a mismatch as an **error**. The manifest is read again at install time, and a disagreement stops the install.

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

### 2. Tell the developer what you found

Note the findings, with their citations, before you speak. They're your working notes, not a deliverable: don't recite them, paste them, or point the developer at them. Errors block shipping; warnings never do.

- **No errors.** One short sentence: their source is validated and ready for the next step. Raise a warning only if it's actionable — *"Heads up: your `screenshots` is an empty array. That's allowed, but most sources include at least one. Want to add some?"*

- **Errors.** Don't dump the list. Take them one at a time and ask about each in plain language. Not *"apps[0].tintColor: hint-box constraint violated — value 'red' is not hexadecimal"* but *"Your tint color is 'red', but AltStore needs a hexadecimal format like `#F54F32`. What color do you want for your source's accent?"* Collect the fixes, re-validate, and loop until no errors remain.

Don't tell the developer their source is ready while an error is outstanding.

## Updating apps

The "Updating Apps" page (URL in `references/living-docs.md`) is the source of truth. Read it before answering update questions — detection rules in its Overview, upload steps in Update Instructions. Confirm which ADP is the new version and which app in their source it belongs to.

Read the new ADP's metadata with [**Identify the ADP and read its metadata**](#shared-procedure-identify-the-adp-and-read-its-metadata). Build this release's `versions[]` entry from the `versions[0]` values you read plus the existing top entry's other keys, ask for this release's notes for `localizedDescription`, and **prepend** it to that app's `versions[]`. The existing entries stay.

`marketplaceID` sits on the app rather than the version, so it carries over untouched — but compare it against the one you read out of the ADP anyway. A mismatch means this ADP belongs to a different app than the one you're about to update.

Once the new version entry is in place, continue from [**Validate and host**](#validate-and-host) — validate, host the new ADP and the updated `source.json`, then confirm.

## Adding apps

The "Make a Source" page (URL in `references/living-docs.md`) is the source of truth. Read its `Apps` key documentation before answering app-addition questions. Confirm which ADP they'd like to add.

Read the new ADP's metadata with [**Identify the ADP and read its metadata**](#shared-procedure-identify-the-adp-and-read-its-metadata). Then download AltStore's canonical `PALSource.json` example:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/.gitbook/assets/PALSource.json
```

Keep it out of the way — don't save it over `source.json`. Write the values you read into its `apps[0]` and that app's `versions[0]`, overwriting the example's, drop the example's remaining `versions[]` entries, and **append** the `apps[0]` object to their `apps[]`. Every app already there stays as it is.

If you can't fetch the example, stop and tell the developer what went wrong. Don't write the entry from memory.

Whatever the ADP couldn't fill still holds AltStore's example values: `name`, `developerName`, `subtitle`, `localizedDescription`, `iconURL`, `tintColor`, `screenshots`, and `appPermissions` on the app, plus the release notes in that version's `localizedDescription`. Say which ones, and offer to fill them. `appPermissions` isn't cosmetic — the spec requires a source to list every entitlement and privacy permission its apps use, and it's what users read before they install.

The new entry's `bundleIdentifier` must not match an app already in the source — the spec forbids duplicates. Ask whether they want it added to `featuredApps`.

Once the new app entry is in place, continue from [**Validate and host**](#validate-and-host) — validate, host the new ADP and the updated `source.json`, then confirm.

## When the developer hits friction

- **"I changed my source's URL."** AltStore identifies a source by the URL users added, so existing users will see a brand-new source and need to re-add it. Keep the original URL live once published.
- **"Updates aren't showing up."** Rule out hosting first: (a) is the new version entry in the hosted `source.json`? `curl` it. (b) Is a CDN serving stale JSON? If the hosted file is correct and current, it's a detection question — answer it from the page, not from memory (see [**Updating apps**](#updating-apps)).
- **"The app appears but won't install."** That's the ADP, not the source. Walk the package: (a) `curl` the `downloadURL`, or `<downloadURL>/manifest.json` when it points at the ADP's directory — one of those has to return the manifest. A bare directory URL answering 404 is normal and not the fault; (b) is `signature` beside it, and does every `assetPath` in the manifest resolve? (c) did anything re-compress, re-zip, or reformat a file on the way up, or add a `.DS_Store` to the folder? Apple signed the package's paths and bytes, so one changed file anywhere in it fails the check — `dist_package_tool validate` on their local copy says so in a second, and re-uploading an untouched package is the fix. A host that flattens directories needs `assetURLs`, with an entry for every variant and delta — see `references/hosting-guidance.md`.
- **"AltStore won't load my source"** or **"it isn't treating my app as notarized."** Every app in a PAL source needs a `marketplaceID`, written as a JSON string of digits. A bare number rather than a string fails the whole source at decode time, and a missing or non-numeric one drops that app out of the notarized path. Either way the complaint lands on the source rather than the app, so check every entry, not just the new one.
- **"AltStore says `No value associated with key "X"`" or `"Hex code is invalid"` etc.** That's AltStore's Swift `Codable` decoder rejecting your source. The fix path is: (1) reread the spec's entry for field `X` carefully; (2) the docs almost certainly mark `X` as required, or carry a constraint in the body that your value violates, and your validation walkthrough missed it — redo that walkthrough more carefully; (3) supply a real value and re-validate. If the docs genuinely don't mention `X` at all, that's a docs gap — file it with the AltStore team rather than papering over it in this skill. The docs are the spec. If they and AltStore's decoder disagree, don't reconcile them yourself — not with a made-up value, not with prose added to this file.
