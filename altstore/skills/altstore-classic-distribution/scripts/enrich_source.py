#!/usr/bin/env python3
"""
Enrich a placeholder source.json with metadata extracted from an .ipa file.

This script is the *IPA-derived* leg of Stage 1. The agent calling this skill
is expected to have already loaded the canonical AltStore example template
(`ClassicSource.json`) and pruned it to one app + one version; this script's
job is to walk that pruned template and replace its example values for the
ten IPA-derivable fields with values drawn from the developer's actual IPA.

Fields filled in from the IPA. These ALWAYS overwrite whatever was in the
template, since the template's values are example placeholders the developer
will replace anyway:

  apps[0].name                                ← CFBundleDisplayName | CFBundleName
  apps[0].bundleIdentifier                    ← CFBundleIdentifier
  apps[0].developerName                       ← code signing identity name
  apps[0].appPermissions.entitlements         ← code signature entitlement keys
  apps[0].appPermissions.privacy              ← NS*UsageDescription keys from Info.plist
  apps[0].versions[0].version                 ← CFBundleShortVersionString
  apps[0].versions[0].buildVersion            ← CFBundleVersion
  apps[0].versions[0].minOSVersion            ← MinimumOSVersion
  apps[0].versions[0].date                    ← today (ISO 8601)
  apps[0].versions[0].size                    ← file size in bytes

Most of these come from the `.app` bundle's `Info.plist` (read directly out
of the zipped IPA). Two come from the IPA's embedded provisioning profile
(`developerName` ← `TeamName`, `appPermissions.entitlements` ←
`Entitlements` keys), also read directly out of the zip.

Why the provisioning profile and not `codesign`: `embedded.mobileprovision`
is a CMS-signed plist that lives at `Payload/<App>.app/embedded.mobileprovision`
inside every Apple-Developer-Program-signed IPA. It carries the same
`TeamName` and `Entitlements` payload the code signature does, but we can
read it with stdlib `plistlib` — no `codesign` shell-out, no tempdir, no
macOS dependency, no parsing of stderr text. Earlier versions of this
script invoked `codesign -d --entitlements :- --xml ...`, which on
macOS 15+ writes per-component output files like `codesign0`, `codesign1`
into the caller's working directory and emits a deprecation warning. The
plist read is also faster (no subprocess, no full bundle extract).

Behavior:
  - IPA contains embedded.mobileprovision (the normal case — Development,
    Ad Hoc, In-House, and pre-App-Store-strip Distribution builds):
      `developerName` ← TeamName (e.g. "Jane Doe" personal, "Acme Inc"
      organization). `appPermissions.entitlements` ← list of Entitlements
      keys.
  - IPA has no embedded.mobileprovision (App-Store-distributed binaries
    that have been re-signed by Apple, or genuinely unsigned IPAs):
      both fields stay as template values. The developer overrides them
      in Stage 2.

Note on `developerName`: TeamName is whatever name the developer registered
their Apple Developer account under. If they want to display something
different in AltStore (e.g. a brand name distinct from the legal entity),
they can override it in Stage 2 like any other field. This script provides
a sane default; it doesn't make a final UX decision.

Privacy usage descriptions (`appPermissions.privacy`) come from `Info.plist`,
not the code signature. The script extracts every key matching
`NS*UsageDescription` (e.g. `NSCameraUsageDescription`,
`NSLocationWhenInUseUsageDescription`) and maps each to its description
string. If the app declares none, the template's example privacy values are
replaced with `{}` — same rationale as the entitlements empty-list case.

What this script never does:
  - Modifies any key outside the ten listed above. `iconURL`, `tintColor`,
    `subtitle`, `localizedDescription`, `downloadURL`, `screenshots`,
    `sourceURL`, the top-level `name`, etc. all keep their template
    placeholder values until Stage 2.
  - Asks the developer anything. The agent collects all developer-supplied
    values in Step 1.3+.
  - Uploads anything anywhere. The script reads the IPA locally and writes
    the placeholder JSON locally.

Exit codes:
  0  success (placeholder updated)
  2  IPA, placeholder, or arguments could not be read/parsed

Usage:
    python enrich_source.py \\
        --ipa path/to/MyApp.ipa \\
        --placeholder path/to/source.json \\
        [-o output.json]   # default: write back to --placeholder
"""
from __future__ import annotations

import argparse
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

    # Privacy usage descriptions: every key matching NS*UsageDescription, mapped
    # to the string the developer wrote at build time. AltStore's source spec
    # expects this as a dict on apps[0].appPermissions.privacy. If the app
    # has none (doesn't access any sensitive APIs), this is an empty dict.
    privacy = {
        k: v
        for k, v in plist.items()
        if isinstance(k, str)
        and k.startswith("NS")
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
    parsed. Callers should treat None as "leave the template's example value
    in place" — Stage 2 will catch the unreplaced placeholder later.

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


def _set_field(obj: dict, key: str, value) -> bool:
    """Set obj[key] to value, overwriting whatever was there. Returns True if
    the stored value actually changed (so the caller can log the diff), False
    if it already matched or if the incoming value is None (don't write junk)."""
    if value is None:
        return False
    if obj.get(key) == value:
        return False
    obj[key] = value
    return True


# Keys the script is responsible for filling. Used both during enrichment and
# afterwards to compute the complement (which keys still hold AltStore's
# example placeholder values) for the Step 1.5 report. Kept as module-level
# constants so the "filled" and "untouched" lists can't drift apart.
#
# `apps` is a structural container — the script modifies apps[0]'s contents,
# not the `apps` key itself, but we exclude it from the source-level
# placeholder list because Step 1.5 reports the storefront keys the developer
# still needs to edit, and `apps` isn't one of them.
_STRUCTURAL_SOURCE_KEYS = {"apps"}
_FILLED_APP_KEYS = {
    "name",
    "bundleIdentifier",
    "developerName",
    "appPermissions",  # children entitlements + privacy are filled
    "versions",        # structural container — versions[0]'s contents tracked separately
}
_FILLED_VERSION_KEYS = {
    "version",
    "buildVersion",
    "minOSVersion",
    "date",
    "size",
}


def enrich(placeholder: dict, meta: dict) -> list[str]:
    """Mutate `placeholder` in place, overwriting the ten IPA-derived fields
    regardless of what the template had in them. Returns a list of
    human-readable notes describing what was written (so the caller can show
    the developer)."""
    notes: list[str] = []

    apps = placeholder.get("apps")
    if not isinstance(apps, list) or not apps:
        notes.append("warning: placeholder has no apps[] array — nothing to enrich.")
        return notes

    app = apps[0]
    if not isinstance(app, dict):
        notes.append("warning: apps[0] is not an object — nothing to enrich.")
        return notes

    if _set_field(app, "name", meta["name"]):
        notes.append(f"apps[0].name ← {meta['name']!r} (from Info.plist)")
    if _set_field(app, "bundleIdentifier", meta["bundleIdentifier"]):
        notes.append(f"apps[0].bundleIdentifier ← {meta['bundleIdentifier']!r} (from Info.plist)")
    if _set_field(app, "developerName", meta.get("developerName")):
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
                f"apps[0].appPermissions.entitlements ← {ent!r} (from code signature)"
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
                f"apps[0].appPermissions.privacy ← {priv!r} (from Info.plist NS*UsageDescription keys)"
            )

    versions = app.get("versions")
    if not isinstance(versions, list) or not versions:
        notes.append("warning: apps[0] has no versions[] array — version metadata not enriched.")
        return notes

    v = versions[0]
    if not isinstance(v, dict):
        notes.append("warning: apps[0].versions[0] is not an object — version metadata not enriched.")
        return notes

    today = _dt.date.today().isoformat()
    if _set_field(v, "version", meta["version"]):
        notes.append(f"apps[0].versions[0].version ← {meta['version']!r} (from Info.plist)")
    if _set_field(v, "buildVersion", meta["buildVersion"]):
        notes.append(f"apps[0].versions[0].buildVersion ← {meta['buildVersion']!r} (from Info.plist)")
    if _set_field(v, "minOSVersion", meta["minOSVersion"]):
        notes.append(f"apps[0].versions[0].minOSVersion ← {meta['minOSVersion']!r} (from Info.plist)")
    if _set_field(v, "date", today):
        notes.append(f"apps[0].versions[0].date ← {today!r} (today)")
    if _set_field(v, "size", meta["size"]):
        notes.append(f"apps[0].versions[0].size ← {meta['size']} (file size in bytes)")

    return notes


def compute_placeholders(placeholder: dict) -> dict:
    """Walk the (already-enriched) source.json and return a structured report
    of which keys still hold AltStore's example placeholder values, so Step
    1.5 can show the developer exactly what's left to edit without re-deriving
    the list from prose.

    Returned shape (always present, may be empty lists):

        {
            "source_level": {
                "untouched": [<top-level key>, ...],   # preserves source.json order
                "filled":    [<top-level key>, ...]
            },
            "app_level": {
                "untouched": [<apps[0] key>, ...],
                "filled":    [<apps[0] key>, ...]
            },
            "version_level": {
                "untouched": [<apps[0].versions[0] key>, ...],
                "filled":    [<apps[0].versions[0] key>, ...]
            }
        }

    `version_level` is reported separately rather than folded into `app_level`
    because the script fills five of the version-object's keys (version,
    buildVersion, minOSVersion, date, size) but leaves others (downloadURL,
    localizedDescription, etc.) — and `downloadURL` is the single most
    important key the developer still has to set, so Step 1.5 needs to
    surface it on its own line.

    Two categories deliberately excluded from `source_level.untouched`:
      - `apps` — structural container, not a developer-facing storefront field.
      - `name` and `patreonURL` — both *could* still hold placeholders here
        (Steps 1.3 and 1.4 set them later). The script can't know whether
        they're real values yet, so it leaves them in the untouched list and
        the caller filters at Step 1.5 time. (They're flagged in the
        `caller_should_filter` list below.)

    Caller-side filtering: `caller_should_filter` lists keys whose status
    depends on Steps 1.3/1.4 outcomes — drop them from `source_level.untouched`
    only if the corresponding step set a real value."""
    report: dict = {
        "source_level": {"untouched": [], "filled": []},
        "app_level": {"untouched": [], "filled": []},
        "version_level": {"untouched": [], "filled": []},
        "caller_should_filter": ["name", "patreonURL"],
    }

    for key in placeholder.keys():
        if key in _STRUCTURAL_SOURCE_KEYS:
            # apps is filled-via-children; not a developer-facing key to flag.
            report["source_level"]["filled"].append(key)
            continue
        report["source_level"]["untouched"].append(key)

    apps = placeholder.get("apps")
    if isinstance(apps, list) and apps and isinstance(apps[0], dict):
        app = apps[0]
        for key in app.keys():
            if key in _FILLED_APP_KEYS:
                report["app_level"]["filled"].append(key)
            else:
                report["app_level"]["untouched"].append(key)

        versions = app.get("versions")
        if isinstance(versions, list) and versions and isinstance(versions[0], dict):
            for key in versions[0].keys():
                if key in _FILLED_VERSION_KEYS:
                    report["version_level"]["filled"].append(key)
                else:
                    report["version_level"]["untouched"].append(key)

    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ipa", required=True, type=Path, help="Path to the .ipa file")
    p.add_argument(
        "--placeholder",
        required=True,
        type=Path,
        help=(
            "Path to the pruned ClassicSource.json template "
            "(must contain apps[0] with at least one entry in versions[])"
        ),
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path. Default: write back to --placeholder.",
    )
    p.add_argument(
        "--placeholders-out",
        type=Path,
        default=None,
        help=(
            "Path to write the structured placeholders report (JSON) listing "
            "which source.json keys still hold AltStore's example values. "
            "Default: <output>.placeholders.json next to the enriched JSON. "
            "Step 1.5 reads this file to drive the baseline message reliably."
        ),
    )
    args = p.parse_args(argv)

    try:
        placeholder = json.loads(args.placeholder.read_text())
    except OSError as e:
        print(f"error: cannot read {args.placeholder}: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: {args.placeholder} is not valid JSON: {e}", file=sys.stderr)
        return 2

    if not isinstance(placeholder, dict):
        print(f"error: {args.placeholder} top-level value must be a JSON object", file=sys.stderr)
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

    notes = enrich(placeholder, meta)

    output = args.output or args.placeholder
    output.write_text(json.dumps(placeholder, indent=2) + "\n")

    # Sidecar report listing which keys still hold AltStore's example values.
    # Step 1.5 reads this so a small model doesn't have to re-derive the list
    # by reasoning over the JSON itself.
    placeholders_out = args.placeholders_out or output.with_suffix(
        output.suffix + ".placeholders.json"
    )
    report = compute_placeholders(placeholder)
    placeholders_out.write_text(json.dumps(report, indent=2) + "\n")

    print(f"wrote {output}")
    print(f"wrote {placeholders_out}")
    if notes:
        print("filled in from IPA:")
        for n in notes:
            print(f"  {n}")
    else:
        print("nothing changed — placeholder already had IPA-matching values.")
    print(
        f"still placeholder: {len(report['source_level']['untouched'])} source-level, "
        f"{len(report['app_level']['untouched'])} app-level, "
        f"{len(report['version_level']['untouched'])} version-level key(s) "
        f"(see {placeholders_out.name} for the full list)."
    )
    print(
        "next: ask the developer for a source name, then present the baseline "
        "and ask whether they want to set up hosting first or replace the "
        "remaining template placeholders first (see Stage 2 in SKILL.md)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
