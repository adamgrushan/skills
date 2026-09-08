#!/usr/bin/env python3
"""
Build an AltStore Classic app entry from an .ipa file.

Reads the canonical AltStore example template
(`ClassicSourceExampleForSkill.json`) and an .ipa, and prints the template's
`apps[0]` object with every field this IPA can supply filled in. **Writes
nothing.** Where the app entry belongs is the caller's decision, and it
differs by flow: replacing `apps[0]` when building a new source, appending to
`apps[]` when adding an app to an existing one, or taking just its
`versions[0]` when shipping an update. Two of those destinations are sources
the developer has already published, so this script does not touch files.

Prints to stdout:
  - a summary of what was derived
  - `---BEGIN APP_ENTRY---` … the app object … `---END APP_ENTRY---`
  - `---BEGIN PLACEHOLDERS_REPORT---` … which keys still hold AltStore's
    example values … `---END PLACEHOLDERS_REPORT---`

Fields filled in from the IPA. Each overwrites whatever the template had,
since the template's values are example placeholders the developer will
replace anyway — but only when this IPA actually yields a value. Any field
that can't be derived keeps the template's example value and is named in the
placeholders report so the developer sees it:

  apps[0].name                                ← CFBundleDisplayName | CFBundleName
  apps[0].bundleIdentifier                    ← CFBundleIdentifier
  apps[0].developerName                       ← provisioning profile TeamName
  apps[0].appPermissions.entitlements         ← provisioning profile Entitlements keys
  apps[0].appPermissions.privacy              ← *UsageDescription keys from Info.plist
  apps[0].versions[0].version                 ← CFBundleShortVersionString
  apps[0].versions[0].buildVersion            ← CFBundleVersion
  apps[0].versions[0].minOSVersion            ← MinimumOSVersion
  apps[0].versions[0].date                    ← today (ISO 8601)
  apps[0].versions[0].size                    ← file size in bytes

Most of these come from the `.app` bundle's `Info.plist` (read directly out
of the zipped IPA). Two come from the IPA's embedded provisioning profile
(`developerName` ← `TeamName`, `appPermissions.entitlements` ←
`Entitlements` keys), also read directly out of the zip.

Exit codes:
  0  success (app entry and report printed)
  2  IPA, template, or arguments could not be read/parsed

Usage:
    python3 enrich_source.py \\
        --ipa path/to/MyApp.ipa \\
        --template path/to/ClassicSourceExampleForSkill.json
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import plistlib
import sys
import zipfile
from pathlib import Path


def extract_ipa_metadata(ipa_path: Path) -> dict:
    """Pull the fields we care about from the IPA's Info.plist + the file size."""
    if not ipa_path.exists():
        raise FileNotFoundError(f"IPA not found: {ipa_path}")

    size = ipa_path.stat().st_size

    with zipfile.ZipFile(ipa_path) as zf:
        info_plist_names = [
            n for n in zf.namelist()
            if n.startswith("Payload/")
            and n.count("/") == 2
            and n.endswith(".app/Info.plist")
        ]
        if not info_plist_names:
            raise ValueError(
                f"No Payload/*.app/Info.plist found inside {ipa_path}. "
                "Is this a valid .ipa?"
            )
        info_plist_name = sorted(info_plist_names, key=len)[0]
        with zf.open(info_plist_name) as fp:
            plist = plistlib.load(fp)

    # Privacy usage descriptions: every key ending in UsageDescription, mapped
    # to the string the developer wrote at build time. AltStore's source spec
    # expects this as a dict on apps[0].appPermissions.privacy. If the app
    # has none (doesn't access any sensitive APIs), this is an empty dict.
    #
    # Match on the suffix alone — not every usage-description key carries the
    # NS prefix (Core NFC's is NFCReaderUsageDescription). The spec asks for
    # "all the 'UsageDescription' keys", and AltStore checks the declared
    # permissions against the .ipa and refuses to install an app that under-
    # declares, so a missed key breaks the install rather than the source.
    privacy = {
        k: v
        for k, v in plist.items()
        if isinstance(k, str)
        and k.endswith("UsageDescription")
        and isinstance(v, str)
    }

    return {
        "bundleIdentifier": plist.get("CFBundleIdentifier") or None,
        "name": (
            plist.get("CFBundleDisplayName")
            or plist.get("CFBundleName")
            or None
        ),
        "version": plist.get("CFBundleShortVersionString") or None,
        "buildVersion": (
            str(plist["CFBundleVersion"]) if "CFBundleVersion" in plist else None
        ),
        "minOSVersion": plist.get("MinimumOSVersion") or None,
        "size": size,
        "privacy": privacy,
    }


def extract_signing_metadata(ipa_path: Path) -> dict:
    """Read TeamName and Entitlements out of the IPA's embedded provisioning
    profile.

    Returns a dict with two keys:
      - developerName: str or None — TeamName from the profile (e.g.
        'Jane Doe' personal account, 'Acme Inc' organization).
      - entitlements: list[str] or None — the Entitlements dict's keys.

    Both keys are None when the IPA has no embedded.mobileprovision (App
    Store-stripped binaries, genuinely unsigned IPAs) or the file can't be
    parsed. None means "leave the template's example value in place" — and
    `enrich()` then omits the key from its `filled` set, so the placeholders
    report lists it and the developer is told it still needs a real value.

    Implementation note: embedded.mobileprovision is a CMS (PKCS#7) signed
    container wrapping an XML plist. We don't need to verify the signature
    to read the payload — locate the `<?xml ... </plist>` window inside the
    DER bytes and hand it to plistlib. This avoids shelling out to
    `codesign` (which on macOS 15+ writes stray output files like
    `codesign0`, `codesign1` into the caller's cwd, emits a `:-` deprecation
    warning, and won't run at all on non-macOS hosts)."""
    result: dict = {"developerName": None, "entitlements": None}

    if not ipa_path.exists():
        return result

    try:
        with zipfile.ZipFile(ipa_path) as zf:
            profile_names = [
                n for n in zf.namelist()
                if n.startswith("Payload/")
                and n.count("/") == 2
                and n.endswith(".app/embedded.mobileprovision")
            ]
            if not profile_names:
                return result
            with zf.open(sorted(profile_names, key=len)[0]) as fp:
                raw = fp.read()
    except Exception:
        return result

    # Carve the XML plist out of the CMS envelope. The plist is the only
    # `<?xml ... </plist>` window in the file, so a literal byte search is
    # enough — no ASN.1 parsing required.
    start = raw.find(b"<?xml")
    end = raw.rfind(b"</plist>")
    if start < 0 or end < 0 or end <= start:
        return result

    try:
        profile = plistlib.loads(raw[start:end + len(b"</plist>")])
    except Exception:
        return result
    if not isinstance(profile, dict):
        return result

    name = profile.get("TeamName")
    if isinstance(name, str) and name.strip():
        result["developerName"] = name.strip()

    # The profile carries Entitlements as a dict. Distinct from "couldn't
    # read the profile" (None above): an empty Entitlements dict resolves to
    # [], overwriting the template's misleading example entitlement strings.
    ent = profile.get("Entitlements")
    if isinstance(ent, dict):
        result["entitlements"] = list(ent.keys())

    return result


def _fill(obj: dict, key: str, value, filled: set) -> bool:
    """Set obj[key] to value, overwriting whatever was there.

    Records `key` in `filled` whenever the IPA actually yielded a value —
    including when that value already matched what the template had. "Derived
    from the IPA" and "changed the file" are different questions, and the
    placeholders report needs the first one: a key we could not derive is
    still holding AltStore's example value and has to be reported as such.

    Returns True only if the stored value changed, so the caller can log a
    note. A None value means we couldn't derive it — don't write junk, and
    don't mark it filled."""
    if value is None:
        return False
    filled.add(key)
    if obj.get(key) == value:
        return False
    obj[key] = value
    return True


# Structural containers — the script fills their *contents*, not the keys
# themselves, so they never belong in the placeholders report. Which leaf keys
# actually got filled is decided per-run by `enrich()`, not declared here: a
# static list would claim fields this IPA may not have yielded.
#
# `apps`     — the script modifies apps[0]'s contents, not the `apps` key.
# `versions` — likewise; versions[0]'s contents are reported separately.
_STRUCTURAL_SOURCE_KEYS = {"apps"}
_STRUCTURAL_APP_KEYS = {"versions"}


def enrich(placeholder: dict, meta: dict) -> tuple[list[str], dict]:
    """Mutate `placeholder` in place, overwriting the IPA-derived fields with
    whatever this IPA actually yielded.

    Returns `(notes, filled)`:
      - `notes` — human-readable lines describing what was written, so the
        caller can show the developer.
      - `filled` — `{"app": set[str], "version": set[str]}`, naming only the
        keys this run genuinely derived. Anything absent from these sets still
        holds AltStore's example value, and `compute_placeholders` must report
        it. Not every field is derivable from every IPA: an .ipa with no
        embedded provisioning profile yields no `developerName` and no
        entitlements, and an Info.plist missing `CFBundleVersion` yields no
        `buildVersion`."""
    notes: list[str] = []
    filled: dict = {"app": set(), "version": set()}

    apps = placeholder.get("apps")
    if not isinstance(apps, list) or not apps:
        notes.append("warning: placeholder has no apps[] array — nothing to enrich.")
        return notes, filled

    app = apps[0]
    if not isinstance(app, dict):
        notes.append("warning: apps[0] is not an object — nothing to enrich.")
        return notes, filled

    fa = filled["app"]
    if _fill(app, "name", meta["name"], fa):
        notes.append(f"apps[0].name ← {meta['name']!r} (from Info.plist)")
    if _fill(app, "bundleIdentifier", meta["bundleIdentifier"], fa):
        notes.append(f"apps[0].bundleIdentifier ← {meta['bundleIdentifier']!r} (from Info.plist)")
    if _fill(app, "developerName", meta.get("developerName"), fa):
        notes.append(f"apps[0].developerName ← {meta['developerName']!r} (from provisioning profile)")

    # Entitlements and privacy descriptions live one level deeper, under
    # apps[0].appPermissions. The template likely already has an
    # appPermissions dict with example values; we replace its `entitlements`
    # list and `privacy` dict while leaving anything else under
    # appPermissions untouched.
    ent = meta.get("entitlements")
    if ent is not None:
        perms = app.get("appPermissions")
        if not isinstance(perms, dict):
            perms = {}
            app["appPermissions"] = perms
        if perms.get("entitlements") != ent:
            perms["entitlements"] = ent
            notes.append(
                f"apps[0].appPermissions.entitlements ← {ent!r} (from provisioning profile)"
            )

    priv = meta.get("privacy")
    if priv is not None:
        perms = app.get("appPermissions")
        if not isinstance(perms, dict):
            perms = {}
            app["appPermissions"] = perms
        if perms.get("privacy") != priv:
            perms["privacy"] = priv
            notes.append(
                f"apps[0].appPermissions.privacy ← {priv!r} (from Info.plist UsageDescription keys)"
            )

    # `appPermissions` counts as filled only if BOTH children were derived.
    # AltStore checks the declared permissions against the downloaded .ipa, so
    # a half-derived block — real privacy descriptions next to the template's
    # example entitlements — is worse than an obviously untouched one. Leaving
    # it out of `filled` puts it back in the report for the developer to fix.
    if ent is not None and priv is not None:
        fa.add("appPermissions")

    versions = app.get("versions")
    if not isinstance(versions, list) or not versions:
        notes.append("warning: apps[0] has no versions[] array — version metadata not enriched.")
        return notes, filled

    v = versions[0]
    if not isinstance(v, dict):
        notes.append("warning: apps[0].versions[0] is not an object — version metadata not enriched.")
        return notes, filled

    fv = filled["version"]
    today = _dt.date.today().isoformat()
    if _fill(v, "version", meta["version"], fv):
        notes.append(f"apps[0].versions[0].version ← {meta['version']!r} (from Info.plist)")
    if _fill(v, "buildVersion", meta["buildVersion"], fv):
        notes.append(f"apps[0].versions[0].buildVersion ← {meta['buildVersion']!r} (from Info.plist)")
    if _fill(v, "minOSVersion", meta["minOSVersion"], fv):
        notes.append(f"apps[0].versions[0].minOSVersion ← {meta['minOSVersion']!r} (from Info.plist)")
    if _fill(v, "date", today, fv):
        notes.append(f"apps[0].versions[0].date ← {today!r} (today)")
    if _fill(v, "size", meta["size"], fv):
        notes.append(f"apps[0].versions[0].size ← {meta['size']} (file size in bytes)")

    return notes, filled


def compute_placeholders(placeholder: dict, filled: dict) -> dict:
    """Walk the (already-enriched) source.json and return a structured report
    of which keys still hold AltStore's example placeholder values, so the
    Replace-remaining-placeholders procedure can show the developer exactly
    what's left to edit without re-deriving the list from prose.

    `filled` is the second return value of `enrich()` — the keys that run
    actually derived. It is required, and it must come from the same run: a
    static list of "keys the script fills" would be a lie for any IPA that
    didn't yield all of them, and would hide a stale value instead of
    reporting it.

    Returned shape (always present, may be empty lists):

        {
            "source_level":  {"untouched": [<top-level key>, ...]},          # preserves source.json order
            "app_level":     {"untouched": [<apps[0] key>, ...]},
            "version_level": {"untouched": [<apps[0].versions[0] key>, ...]},
            "caller_should_filter": [...]
        }

    `version_level` is reported separately rather than folded into `app_level`
    because the script fills five of the version-object's keys (version,
    buildVersion, minOSVersion, date, size) but leaves others (downloadURL,
    localizedDescription, etc.) — and `downloadURL` is the single most
    important key the developer still has to set, so the report needs to
    surface it on its own line.

    `apps` is excluded from `source_level.untouched` outright — it's a
    structural container, not a developer-facing storefront field.

    `featuredApps`, `name` and `patreonURL` are a different case. This report
    is a snapshot taken before the steps that write them, so all three still
    hold the template's values when it's computed. The script can't know how
    those steps turn out, so it leaves the keys in `untouched` and names them
    in `caller_should_filter` for the caller to drop once it knows. Report a
    key the caller has since filled and you contradict what the developer was
    just told; hide one it hasn't and they publish an example value."""
    report: dict = {
        "source_level": {"untouched": []},
        "app_level": {"untouched": []},
        "version_level": {"untouched": []},
        "caller_should_filter": ["featuredApps", "name", "patreonURL"],
    }

    # apps is filled-via-children; not a developer-facing key to flag.
    report["source_level"]["untouched"] = [
        k for k in placeholder.keys() if k not in _STRUCTURAL_SOURCE_KEYS
    ]

    apps = placeholder.get("apps")
    if isinstance(apps, list) and apps and isinstance(apps[0], dict):
        app = apps[0]
        app_filled = filled.get("app", set()) | _STRUCTURAL_APP_KEYS
        report["app_level"]["untouched"] = [
            k for k in app.keys() if k not in app_filled
        ]

        versions = app.get("versions")
        if isinstance(versions, list) and versions and isinstance(versions[0], dict):
            version_filled = filled.get("version", set())
            report["version_level"]["untouched"] = [
                k for k in versions[0].keys() if k not in version_filled
            ]

    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ipa", required=True, type=Path, help="Path to the .ipa file")
    p.add_argument(
        "--template",
        required=True,
        type=Path,
        help=(
            "Path to the ClassicSourceExampleForSkill.json template "
            "(must contain apps[0] with at least one entry in versions[]). "
            "Read only — this script never writes to it."
        ),
    )
    args = p.parse_args(argv)

    try:
        template = json.loads(args.template.read_text())
    except OSError as e:
        print(f"error: cannot read {args.template}: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: {args.template} is not valid JSON: {e}", file=sys.stderr)
        return 2

    if not isinstance(template, dict):
        print(f"error: {args.template} top-level value must be a JSON object", file=sys.stderr)
        return 2

    try:
        meta = extract_ipa_metadata(args.ipa)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # Provisioning-profile extraction is best-effort. If the IPA has no
    # embedded.mobileprovision (App Store-stripped binary or genuinely
    # unsigned IPA), this returns Nones and the script continues with just
    # the Info.plist-derived fields.
    meta.update(extract_signing_metadata(args.ipa))

    # Work on a copy. Nothing this script does may touch a file on disk — the
    # caller decides where the app entry goes, and for two of the three flows
    # that destination is a source the developer has already published.
    merged = copy.deepcopy(template)
    notes, filled = enrich(merged, meta)

    apps = merged.get("apps")
    if not isinstance(apps, list) or not apps or not isinstance(apps[0], dict):
        print(f"error: {args.template} has no apps[0] object to build from", file=sys.stderr)
        return 2
    app_entry = apps[0]

    report = compute_placeholders(merged, filled)

    if notes:
        print("filled in from IPA:")
        for n in notes:
            print(f"  {n}")
    else:
        print("nothing derived — the template already matched this IPA.")
    print(
        f"still placeholder: {len(report['source_level']['untouched'])} source-level, "
        f"{len(report['app_level']['untouched'])} app-level, "
        f"{len(report['version_level']['untouched'])} version-level key(s) "
        "(full list in the PLACEHOLDERS_REPORT block below)."
    )

    # Both blocks go to stdout rather than a sidecar file, so the caller reads
    # them straight out of this run and there's nothing to clean up.
    print("---BEGIN APP_ENTRY---")
    print(json.dumps(app_entry, indent=2))
    print("---END APP_ENTRY---")
    print("---BEGIN PLACEHOLDERS_REPORT---")
    print(json.dumps(report, indent=2))
    print("---END PLACEHOLDERS_REPORT---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
