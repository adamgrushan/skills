---
name: altstore-classic-distribution
description: Help iOS developers publish, update, or add an app thier existing source via AltStore Classic. Use this whenever a developer wants to distribute, update, or add an app to their existing source through AltStore — including phrases like "AltStore source", "AltStore Classic", "self-host my iOS app", "sideload distribution", "create a source.json", "host my IPA so users can install it", "let people add my app to AltStore", "update my app", or "update my source", or "add an app to my source". Trigger even when the user doesn't say "AltStore" explicitly but is asking how to let other people install their iOS app from a URL outside the App Store, how to update their app, or add an app to their source. The skill walks through generating a valid AltStore Classic source JSON from an IPA, validating it, and giving host-agnostic deployment guidance.
---

# AltStore Classic Distribution

Help a developer who has (1) an `.ipa` file and (2) a public web host get a working AltStore Classic source that real users can add in the AltStore app.

## Two stages at a glance

The skill runs in two stages:

1. **Stage 1 — Build the baseline source.json.** Fetch and edit AltStore's ClassicSource.json template (Step 1.1), run enrich_source.py to fill in the ten IPA-derived fields (Step 1.2), and ask the developer for their source name plus optional Patreon URL (Steps 1.3–1.4). Hand back the baseline (Step 1.5). Every other field carries AltStore's example placeholder values, ready to be replaced in Stage 2.
2. **Stage 2 — Edit the remaining placeholders and set up hosting, in whichever order the developer prefers.** The two orderings are labeled internally as Host First (Stage 2A: host source.json → edit → validate → host IPA + updated source) and Edit First (Stage 2B: edit → validate → host everything). These labels are for your reference only — don't speak them to the developer. See ## Stage 2 below for how to recognize which path the developer wants.

## Working contract

Five rules make the rest of this skill work. Don't bend them.

- **Build the `source.json` from AltStore's canonical example template, not from memory.** Make the `ClassicSource.json` example you fetch in Step 1.1 the first draft of the developer's `source.json` file. 

- **In Stage 2, walk the developer through every placeholder. Don't invent values.** After `enrich_source.py` overwrites the ten IPA-derivable fields and you set the source name, every other value in the template should remain AltStore's example placeholder values. The developer (not you) decides what to change.

- **Don't hand an edited `source.json` back to the developer until you've validated it field-by-field against the live spec and produced a report whose status is `0`.** *You* are the rule engine: you fetch the live spec, organize it into a rule pack, and apply each rule. Treat a status of `1` (errors present) as a blocker. Fix the JSON and re-validate until status is `0`. (Validation lives inside both Stage 2 paths — it's not part of Stage 1.)

- **Never upload anything on the developer's behalf unless the developer asks explicitly.** Hosting is theirs to do on their own infrastructure, with their own credentials. Don't run `curl`-uploads, `scp`, `rsync`, `aws s3 cp`, `gh release upload`, `git push` to a Pages repo, or any other write operation that touches a public web host unless the developer asks explicitly. You walk them through the requirements; they execute the upload.

- **Don't narrate your work.** Speak to the developer when you have a question or a result; otherwise stay quiet. Don't preface tool calls ("Let me fetch the template...") and don't summarize what you just did ("OK, I've enriched the source!"). The developer doesn't need to follow your internal execution. They need clear questions, clean outputs, and concise findings.

## References

The stub `references/distribute-with-altstore-classic.md` is a short developer-facing primer. Read it for orientation; it summarizes the same prerequisites you'll be asking about.

`references/living-docs.md` points at the canonical AltStore FAQ pages — both the raw markdown URLs the validation step fetches and the rendered URLs you'd link to the developer in conversation.

The AltStore Classic source format is owned by the AltStore project, not by this skill. The canonical example template at `gitbook.io` and the spec markdown in the [AltStore FAQ repo](https://github.com/altstoreio/FAQ) are the source of truth. This skill defers to them.

## Stage 1: Build the baseline source.json

### Step 1.1: Fetch and edit the canonical template

Tell the user you are getting started fetching the template, identifying the IPA file, and enriching the template from the IPA.

Download AltStore's canonical `ClassicSourceExampleForSkill.json` example:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/.gitbook/assets/ClassicSourceExampleForSkill.json
```

Save it as `source.json` in the developer's working directory. Every value inside it is still a placeholder from AltStore's template. Stage 1 replaces a small set of those (the IPA-derivable ones and the source name). Stage 2 handles the rest.

If you can't fetch the template, stop and tell the developer Stage 1 needs internet access.

### Step 1.2: Identify the IPA file and enrich from the IPA

Identify the IPA file in the working directory. If you can't find one, check for an `.xcodeproj` or `.xcworkspace` — if present, ask the developer if they'd like you to build the IPA with xcodebuild (ad-hoc export). Only proceed on explicit yes; on success, use the produced .ipa for the rest of Stage 1. Then run the enrichment script:

```bash
python scripts/enrich_source.py \
  --ipa ./MyApp.ipa \
  --placeholder ./source.json
```

The script overwrites these ten fields with values pulled from the IPA — eight from the `.app` bundle's `Info.plist` (including the privacy usage descriptions), plus two from the IPA's embedded code signature:

| Path                                       | Value                                       |
| ------------------------------------------ | ------------------------------------------- |
| `apps[0].name`                             | `CFBundleDisplayName` / `CFBundleName`      |
| `apps[0].bundleIdentifier`                 | `CFBundleIdentifier`                        |
| `apps[0].developerName`                    | signing identity name (code signature)      |
| `apps[0].appPermissions.entitlements`      | entitlement keys (code signature)           |
| `apps[0].appPermissions.privacy`           | `NS*UsageDescription` keys from `Info.plist`|
| `apps[0].versions[0].version`              | `CFBundleShortVersionString`                |
| `apps[0].versions[0].buildVersion`         | `CFBundleVersion`                           |
| `apps[0].versions[0].minOSVersion`         | `MinimumOSVersion`                          |
| `apps[0].versions[0].date`                 | today (ISO 8601)                            |
| `apps[0].versions[0].size`                 | file size in bytes                          |

The script never touches any other key.

For edge-case behavior (when the IPA has no embedded provisioning profile, what happens to `appPermissions.privacy` if the app declares no usage descriptions, why `developerName` from the profile's TeamName isn't always the display name the developer wants), see the docstring at the top of `scripts/enrich_source.py`. You only need to consult it when something surprising happens.

### Step 1.3: Update the `featuredApps` field

Set `featuredApps` to `[apps[0].bundleIdentifier]` (a single-element list containing the app's bundle identifier).

### Step 1.4: Ask for the source name

Ask the developer:

> What would you like to call your source?

Replace `source.json`'s top-level `name` field with their answer. Don't replace anything else.

### Step 1.5: Ask the developer for their Patreon

Ask the developer:

> Want to add your Patreon URL to your source? If so, what's the URL? 
>
> With Patreon you can offer apps exclusively to your Patrons. Find more information here (https://faq.altstore.io/developers/patreon-integration). 
>
> You can skip this is you want.

Branch on the developer's response:

- If they provided a URL: replace source.json's top-level `patreonURL` field with that URL.
- If they declined, said no, or didn't give a URL: leave `patreonURL` exactly as the template has it. Don't replace it, don't delete it, don't write an empty string.

Don't replace any other key in either case.

### Step 1.6: Present the baseline

**Before composing the message, gather two things:**
- Whether `patreonURL` has a real value (developer provided one) or is absent (they declined).
- The full current contents of `source.json`.

**Choose the "filled in" line:**
- If Patreon was provided: `Your source name, featuredApps, various app keys and Patreon URL are filled in.`
- If they declined: `Your source name, featuredApps and various app keys are filled in.`

 Then send this message, substituting the bracketed slots:**
 
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
> **☁️⬆️ You can upload this file to your web host now, then add the hosted file's URL in AltStore Classic on your phone to see it in action.☁️⬆️**
>
> **💬 Or you can get my help — I can guide you on hosting or answer questions about specific keys and fill in placeholder values for you.💬**

## Stage 2: edit and host, in the developer's preferred order

Stage 2 is always the same two activities: **editing** the remaining placeholder values in `source.json` and **hosting** `source.json` + the IPA on the developer's web host. The order varies; the activities don't. Internally, the two orderings are:

- **Stage 2A — Host First**: host `source.json` → edit placeholders → validate → host the IPA + updated `source.json`
- **Stage 2B — Edit First**: edit placeholders → validate → host `source.json` + IPA

**Internal labels — do not say these to the developer.** Don't say "we're entering Stage 2," "this is the Host First path," "Stage 2A," "Path B," or any structural label. From the developer's point of view, you're just helping them with whatever they asked for next. They never need to know there are two paths or that the skill has stages at all.

**Recognizing which path the developer wants** — they pick at the end of Step 1.5, but they may also signal organically. Treat any of these as a path signal:

- *"I'll host it now"*, *"how do I deploy it?"*, *"walk me through hosting"*, *"let me upload first"* → Stage 2A.
- *"let me fill in the rest first"*, *"help me with the icon URL"*, *"what's a good description?"*, *"I want to edit before I host"* → Stage 2B.

If the developer's intent isn't clear, ask **one** disambiguating question without using the path names. Example: *"Want to set up hosting first, or work on filling in the rest of the source first?"*

Once you've identified the path, start from its first step (Step 2A.1 or Step 2B.1) and proceed silently. Don't announce the choice ("OK, we'll do Edit First!") — just begin the work.

### Stage 2A — Host First

#### Step 2A.1: Walk through hosting requirements for the `source.json` file

Help the developer upload only their `source.json` file. Ignore their IPA file for now. See [**Hosting guidance**](#shared-procedure-hosting-guidance) below.

#### Step 2A.2: Confirm the `source.json` file is hosted

Once the developer says they've hosted the `source.json` file, have them try to add the source in AltStore. Mention that they won't be able to download their app yet.

Once they can add the source, take a beat and ask the developer:

> Want to replace the remaining placeholders now?

#### Step 2A.3: Replace the remaining placeholders

Follow the shared procedure [**Replace remaining placeholders**](#shared-procedure-replace-remaining-placeholders) below. That procedure handles the conversation framing, kicks off the rule-pack build in parallel with the developer's reading time, and uses the rule pack to answer the developer's questions and fill values. Don't invoke the rule-pack build separately — the shared procedure does it.

#### Step 2A.4: Validate against the live spec

See [**Validate against the live spec**](#shared-procedure-validate-against-the-live-spec) below. Treat status `1` (errors present) as a blocker; fix and re-validate until status is `0`.

#### Step 2A.5: Walk through hosting requirements for the IPA and latest `source.json` files

Help the developer upload their IPA file. Then, update `source.json` to reflect the downloadURL for the IPA file. Then, help the developer upload their latest `source.json` file.

See [**Hosting guidance**](#shared-procedure-hosting-guidance) below.

#### Step 2A.6: Confirm the `source.json` and IPA files are hosted

Once the developer says they've hosted the IPA and latest `source.json` files, have them try to add the source in AltStore and downlad their app.

### Stage 2B — Edit First

#### Step 2B.1: Replace the remaining placeholders

Follow the shared procedure [**Replace remaining placeholders**](#shared-procedure-replace-remaining-placeholders) below. That procedure handles the conversation framing, kicks off the rule-pack build in parallel with the developer's reading time, and uses the rule pack to answer the developer's questions and fill values. Don't invoke the rule-pack build separately — the shared procedure does it.

#### Step 2B.2: Validate against the live spec

See [**Validate against the live spec**](#shared-procedure-validate-against-the-live-spec) below. Treat status `1` as a blocker.

#### Step 2B.3: Walk through hosting requirements

Help the developer upload their IPA file. Update `source.json` to reflect the downloadURL for the IPA file. Then, help the developer upload their latest `source.json` file.

See [**Hosting guidance**](#shared-procedure-hosting-guidance) below.

#### Step 2B.4: Confirm the hosting is live

Once the developer says they've hosted the IPA and latest `source.json` files, have them try to add the source in AltStore and downlad their app.

## Shared procedure: Replace remaining placeholders

Used by Step 2A.3 and Step 2B.1. The flow has four phases. **Do them in the order below** — the message comes first so the developer has something to read; the rule-pack build happens in parallel with the developer's reading time; the back-and-forth uses the now-ready rule pack as its reference.

### 1. Send an initial message and build the rule pack from the live spec

**Before composing an initial message, gather five things:**
  - The placeholders report that `enrich_source.py` printed to stdout, between the `---BEGIN PLACEHOLDERS_REPORT---` and `---END PLACEHOLDERS_REPORT---` markers in Step 1.2's output. Parse the JSON between those markers. It contains:
  - `source_level.untouched` — top-level keys still on placeholder values.
  - `app_level.untouched` — `apps[0]` keys still on placeholder values.
  - `version_level.untouched` — `apps[0].versions[0]` keys still on placeholder values (most importantly `downloadURL`, which the developer must set before the source works).
  - `caller_should_filter` — keys you must drop from `source_level.untouched` based on later steps' outcomes: drop `name` (Step 1.3 always sets it); drop `patreonURL` only if Step 1.4 set a real value, keep it if the developer declined.

Use the report's lists verbatim — don't re-derive placeholder keys by reading the JSON yourself. The script is the source of truth here.

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

**Then build the rule pack following the shared procedure [**Build the rule pack from the live spec**](#shared-procedure-build-the-rule-pack-from-the-live-spec).**

Then say:

> Alright I'm ready to answer questions about specific keys or fill in placeholder values for you. I can even fill in as many placeholder values as I can based on what I know about your app, if you'd like. How would you like to proceed?

### 3. Answer questions and fill values, using the rule pack as your reference

When the developer responds, route their request through the following logic:

- **If they ask you to take a stab at filling in as many placeholder values as you can based on what you know about your app**, edit the `source.json` using the context you have about their app, then share which keys still have AltStore's example placeholder values.

- **If they say they'll self-edit:** confirm with something brief — *"Got it. Ping me with questions, or let me know when you're ready and I'll validate the source."* Stop the back-and-forth and proceed to the next step (validation). Re-enter this procedure on demand if they come back with questions.

- **If they ask about a specific key:** look it up in the rule pack at `spec.objects[<Object>].fields[<keyname>]`. Use the field's `body` to answer accurately — the spec's own prose is the authoritative explanation, so prefer its wording over your own paraphrase when explaining what a field is for. Surface any hint-box constraint (hex format, URL form, character count, etc.). If there's a non-null `enum`, list the allowed values.

- **If they want you to fill in a specific value:** ask any clarifying questions, then validate the value against the rule pack's `type`, `enum`, and hint-box constraints before writing. If the value doesn't satisfy a constraint (e.g. they offer `"red"` for a hex `tintColor`), explain what's needed and ask for a corrected one rather than writing something the decoder will reject.

- **If they ask about something not in the rule pack:** the field may have been added to the spec since you last built the pack, or they may be confusing concepts. Reread the relevant object section in the rule pack first; if it genuinely isn't there, say so plainly.

Continue the back-and-forth until the developer signals they're done with placeholders.

### 4. Mention what's possible beyond the basic source

Once the developer is done with placeholders — and before proceeding to validation — mention two capabilities the spec supports that didn't come up:

- **News items.** AltStore lets you post short announcements on your source page — things like 'New version released' or 'Now featured on X'. They're optional and your source is fine without them. If you want to add some, just tell me and we can come back to it.

- **Shipping updates.** When you release a new version of your app, you don't rebuild your source from scratch. You add a new entry to the top of the `versions` array, upload the new `.ipa` to a new URL, and re-publish `source.json`. AltStore polls your source URL and prompts existing users to update. The exact rules for how AltStore decides what counts as 'newer' live on the Updating Apps page in the AltStore FAQ — I can walk you through them when it's time.

If the developer engages on either topic:

- **News items** have their own object type in the rule pack at `spec.objects['News Items']`. Build each news item by asking the developer for the relevant fields (looking them up in the rule pack like any other key), append to `source.news`, and loop if they want more than one.
- **Updates** are a Stage 1 re-run with the new IPA, where the new version object gets prepended to `apps[0].versions[]` rather than overwriting the existing entry. The detailed update-detection rules live at `https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/updating-apps.md`. Fetch and apply the [**Build the rule pack from the live spec**](#shared-procedure-build-the-rule-pack-from-the-live-spec) procedure to that URL if the conversation goes there.

## Shared procedure: Build the rule pack from the live spec

The editing and validation steps need a structured representation of the AltStore Classic source spec, called a **rule pack**. You produce it yourself by reading the spec and organizing it into the schema below.

**1. Fetch the spec.** Read the raw markdown at:

```
https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md
```

Use whatever URL-fetching tool your harness gives you. If the fetch fails, stop and tell the developer this step needs internet access. Use the raw markdown URL above, not the rendered page at `faq.altstore.io` — the rendered version omits authoring cues that make accurate extraction easier.

**2. Read the spec for understanding.** Read the entire page. Identify which JSON object types it documents (Source, Apps, App Versions, App Permissions, Screenshots, News Items, Patreon, and any others present), and within each object type, identify every individual field.

**3. For each field, capture five things:**

- `name` — the field's identifier as it appears in JSON (e.g. `bundleIdentifier`).
- `type` — the spec's stated type for the value (e.g. `string`, `array of strings`, `App Permissions object`). Use the spec's own wording.
- `optional` — `true` if the spec marks this field as optional, `false` if the spec treats it as required. Use your judgment based on how the spec presents it; if the marking is ambiguous, default to `false` (treat as required) and note the ambiguity in the body.
- `enum` — if the spec restricts this field to a fixed set of allowed values, list them. Otherwise `null`.
- `body` — verbatim text of every word the spec writes about this field, including any constraint callouts, examples, and default-value notes. Don't paraphrase. Don't summarize. Future steps will reread this text to apply rules, and they need the original wording.

**4. Assemble the rule pack** in this exact shape:

```json
{
  "source_path": "<path to the developer's source.json, or empty string if none yet>",
  "source": <the developer's source.json parsed as an object, or {} if none yet>,
  "spec": {
    "url": "https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/make-a-source.md",
    "objects": {
      "<ObjectType>": {
        "intro": "<verbatim text the spec places at the top of this object's section, before any specific field>",
        "field_order": ["<fieldName1>", "<fieldName2>", "..."],
        "fields": {
          "<fieldName>": {
            "type": "<spec's stated type>",
            "optional": <true|false>,
            "enum": <list of allowed values, or null>,
            "body": "<verbatim spec prose for this field>"
          }
        }
      }
    },
    "page_text": "<any spec content that doesn't belong to a specific object type — overview prose, cross-field rules, and the like>"
  }
}
```

The schema is fixed; downstream steps depend on these exact key names. Object names and field names should match the spec's own spelling. `field_order` should match the order the spec presents fields in.

**5. Capture cross-field rules.** Some constraints in the spec apply across fields rather than to one field — uniqueness rules, ordering rules, "must reference an existing X" rules. Anything that doesn't fit cleanly under a single field's `body` goes into `spec.page_text` or the relevant object's `intro`, verbatim. Don't drop it; the validation step will look for it.

**6. Sanity-check before continuing.** Verify:

- `spec.objects` includes a `Source` and an `Apps` entry at minimum, each with a non-empty `fields` map. If either is missing, you've misread the page; reread it.
- Save the rule pack somewhere persistent (e.g. `/tmp/rules.json`) so you can refer back to it without re-fetching.

**Failure handling.** If you cannot fetch the page, or if your sanity-check fails after a careful re-read, declare **Status: 2** to the developer and stop. Don't proceed with a malformed rule pack — every check depends on it.

## Shared procedure: Validate against the live spec

Used by Step 2A.4 and Step 2B.2. Validation is a structured walkthrough where you apply the rule pack's rules to the developer's `source.json` field-by-field, then emit a status `0`/`1`/`2` report. Build the rule pack first if you haven't already (see [**Build the rule pack from the live spec**](#shared-procedure-build-the-rule-pack-from-the-live-spec)).

### Apply the rules, field by field

For every field that appears in the developer's `source.json`, find its matching entry in the rule pack and check it against six rule families. Object scope matters: a top-level field uses the `Source` section; an entry in `apps[]` uses the `Apps` section; an entry in a screenshots array uses `Screenshots`; an entry in a `versions[]` array uses `App Versions`; etc.

1. **Find the field section.** Look up the field by name inside the right object section (`spec.objects[<Object>].fields[<fieldname>]`). If the field exists in the JSON but no matching section exists in the spec, flag it as a warning ("unknown field, not in spec") — don't error, since the spec may have added something you missed when building the rule pack.

2. **Apply the type.** Read the field's `type`. It tells you what shape to expect: `string`, `number`, `boolean`, `array of <X>`, `dictionary of <X>`, or a named object type (e.g. `App Permissions object`). Check the JSON value against it. A type mismatch is an **error**.

3. **Apply required/optional.** Read the field's `optional` boolean. `false` → required, `true` → optional. **Exception:** a hint box in the body can modify this — e.g. `marketplaceID` is documented with prose like "required for marketplace apps, omit for AltStore Classic". Always read the body for "required when…" / "must be present if…" / "omit if…" language before deciding. If a required field is absent from the JSON, it's an **error**. If an optional field is absent, that's fine.

4. **Apply the enum.** Read the field's `enum`. If it's a non-null list, the JSON value must be one of those entries. If the prose mentions a default ("If no value is provided it will default to `other`"), absence isn't an error. A value outside the enum is an **error**.

5. **Apply hint-box constraints.** Each `{% hint %}…{% endhint %}` block in the body is an authoritative rule the AltStore developers wrote. Read each one and translate it into a check against the JSON value. Examples of patterns to watch for:
   - "must be in hexadecimal format" → check the value matches `^#?[0-9A-Fa-f]{6}$`.
   - "must be a fully qualified URL" → check the value parses as an http(s) URL.
   - "must be at least N characters" → measure the string.
   - "if not provided, defaults to X" → relaxes required-ness, doesn't impose a constraint.
   - "this is automatically derived from Y" → don't error if it's missing. Warn if it's present and doesn't match.

   A failed hint constraint is an **error**. A hint that softens a requirement is informational.

6. **Apply cross-field rules from prose.** Some constraints don't sit under a single field — they live in the object's `intro`, in `spec.page_text`, or on the on-demand "Updating Apps" page (`https://raw.githubusercontent.com/altstoreio/FAQ/main/developers/updating-apps.md` — fetch and apply the rule-pack-building procedure to it if a question requires it). Walk each of these locations and translate any rule you find into a check against the developer's JSON.

   For each piece of cross-field prose you find:

   - **Identify the rule.** Look for sentences that describe a constraint across fields or objects: uniqueness within a list, ordering within a list, "must reference an X elsewhere in the source," "must be present if Y is present," default-value cascades, polymorphic shapes (where one field can take two or more accepted forms), etc.
   - **Locate the relevant slice of the JSON.** A uniqueness rule about an array → iterate that array. A cross-reference rule → resolve both endpoints in the JSON. A polymorphism rule → identify which of the accepted shapes the JSON actually uses, then check it against that shape's requirements.
   - **Translate to a check.** Express the rule as a yes/no test the JSON either passes or fails.
   - **Decide error vs. warning.** If the rule's prose says "must" / "cannot" / "required," a violation is an **error**. Hedged language ("recommended" / "should" / "may") is a **warning**.
   - **Cite the source.** In the report, quote the exact sentence and name where you found it (which object's `intro`, or `spec.page_text`, or the updating-apps page). The citation is what lets you re-find the spec text if the developer pushes back on a finding during the conversation that follows.

   Don't pattern-match these from memory. Reread the relevant `intro` / `page_text` / updating-apps section each time. Cross-field rules change less often than field schemas, but they do change.

### Emit a structured report (internal — do NOT share with the developer)

Produce a report with the shape below **for your own use**. It's the artifact you use to decide whether to block, what to ask the developer about, and what to recheck on the next pass. **Don't paste this report into the conversation, don't read it out, and don't hand the developer the path to a written copy.** It's internal scaffolding, not user-facing output.

```
Status: 0 | 1 | 2
Source: <source_path>

Errors:
  - apps[0].tintColor: hint-box constraint violated — value "" is not hexadecimal
    (rule: hint in "Apps > tintColor" — "This must be in hexadecimal format (e.g **#F54F32** or **C9B632**)")
  - apps[0].versions[0].size: required field missing
    (rule: "Apps > versions[].size" — no _(optional)_ or *(optional)* marker)

Warnings:
  - apps[0].screenshots: spec describes three accepted shapes; current value is empty array (allowed but not useful)
  - source.foo: unknown field, not present in the spec at this URL — may be a docs-chunker miss

Status meaning:
  0 = no errors (warnings allowed)
  1 = at least one error — block deployment until fixed
  2 = the rule pack itself could not be produced (read or fetch failure)
```

Each error or warning must cite **which rule** it came from (object > field, plus whether it's the type annotation, the optional marker, an enum, a hint box, or a cross-field prose rule) so *you* can find the spec text again if pressed and so the next validation pass can be audited.

### How to communicate validation results to the developer

The developer should never see the report itself. Instead, translate it into plain-language conversation:

- **Status 0 (no errors).** Tell the developer their source is validated and ready for the next step. One short sentence. Don't list the warnings unless one is actionable (e.g. *"Heads up: your `screenshots` is an empty array. That's allowed, but most sources include at least one screenshot. Want to add some?"*); ignore the housekeeping warnings (unknown-field-may-be-chunker-miss and similar).

- **Status 1 (errors present).** Don't dump the error list. Pick the errors up one at a time, in the order they affect the developer's source, and ask about each in plain language. Bad: *"apps[0].tintColor: hint-box constraint violated — value 'red' is not hexadecimal."* Good: *"Your tint color is 'red', but AltStore needs a 6-digit hex code like `F54F32`. What color do you want for your source's accent?"* After collecting fixes, rerun the validation procedure and check the new report. Loop until status is 0.

- **Status 2 (couldn't validate).** Tell the developer plainly that validation couldn't run and why (couldn't fetch the spec, couldn't parse `source.json`, etc.). Don't try to interpret partial results — the rule pack isn't trustworthy, so any errors or absences in it would be misleading.

In short: the report is for your reasoning; the conversation is for the developer's experience. Keep them separate.

## Shared procedure: Hosting guidance

Used by Step 2A.1, 2A.5 and Step 2B.3. Start by saying to the developer that we suggest using GitHub Pages, but that any web host works —  Cloudflare Pages, Netlify, Vercel, S3+CloudFront, or a plain VPS. Then provide the developer guidance based on their questions.

**Hosting layout — new repo or existing project repo, both work.** The developer can put `source.json` and their IPA in a fresh repo dedicated to the source, or drop them into their existing Xcode-project repo alongside the code. A dedicated repo keeps the source cleanly separated and easy to point at; reusing the app's repo is one fewer thing to maintain.

- **On GitHub, put the app version in the IPA's filename** — e.g., `MyApp-1.2.3.ipa`, not `MyApp.ipa`. Each release gets its own distinct, permanent URL, older versions stay reachable, and the `downloadURL` in `source.json` can point at the new release without overwriting the previous one. Reinforces the "use a stable URL" guidance from the AltStore primer: stable *per version*, not one URL forever.

**Guidance only — never upload anything yourself unless the developer asks explicitly.** The developer hosts; you advise. Even if your harness has tools for it (S3, GitHub Pages, generic SCP, etc.), don't reach for them unless the developer asks explicitly. Your job here is to tell the developer what their host needs to satisfy and to spot problems if they describe what they've set up.

## Updating apps

The "Updating Apps" page in `references/living-docs.md` is the source of truth for updating apps. Read the "Update Instructions" on the page before answering app update questions.

## Adding apps

The "Make a Source" page in `references/living-docs.md` is the source of truth for adding apps. Read the `Apps` key documentation on the page before answering app addition questions. Your first attempt to add the app should update an existing `source.json` file.

## When the developer hits friction

- **"My IPA is on Dropbox / Google Drive / iCloud."** That's a sharing UI, not a static file host. The `downloadURL` must return raw IPA bytes on a plain GET. Steer them to a real host.
- **"I changed the source identifier."** Existing users will see it as a brand-new source and will need to re-add it. Don't change `identifier` once published.
- **"Updates aren't showing up."** Check, in order: (a) is the new version entry actually in the hosted `source.json`? `curl` it. (b) Is its `version` string greater than what's installed? (c) Is a CDN serving stale JSON? (d) Is the `date` in the past?
- **"Should I sign the IPA?"** AltStore Classic re-signs apps on-device with the user's own Apple ID; you don't need to ship a distribution-signed IPA. A development build is fine. (Defer to the live AltStore docs if the developer asks for specifics — this area changes.)
- **"AltStore says `No value associated with key "X"`" or `"Hex code is invalid"` etc.** That's AltStore's Swift `Codable` decoder rejecting your source. The fix path is: (1) rebuild the rule pack and reread the entry for field `X` carefully; (2) the docs almost certainly mark `X` as required, or carry a constraint in the body that your value violates, and your validation walkthrough missed it — redo that walkthrough more carefully; (3) supply a real value and re-validate. If the docs genuinely don't mention `X` at all, that's a docs gap — file it with the AltStore team rather than papering over it in this skill. The whole point of this design is that the docs are the spec. If the docs and AltStore's decoder disagree, neither code in this repo nor prose in this file should try to reconcile them.
