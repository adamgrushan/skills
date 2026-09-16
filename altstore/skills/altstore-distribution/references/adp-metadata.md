# Reading app metadata from an ADP

An ADP is a directory Apple built and signed, not an archive you unpack. Every command below reads out of it and writes nothing. `$ADP` is the root of the developer's Alternative Distribution Package.

## The layout

```
$ADP/
├── manifest.json
├── signature
├── variant/
│   └── <uuid>.ipa
└── delta/            # optional
    └── <uuid>.ipa
```

The folder is `variant`, singular. `manifest.json` holds everything the ADP can tell you — read it, never rewrite it.

## From `manifest.json`

It's minified JSON on one line, and `plutil` parses JSON, so read keys the same way you would from a plist:

```bash
plutil -extract bundleId raw -o - "$ADP/manifest.json"
```

| `source.json` key | `manifest.json` key |
| --- | --- |
| `apps[0].bundleIdentifier` | `bundleId` |
| `apps[0].marketplaceID` | `appleItemId` — write it as a string |
| `apps[0].versions[0].version` | `shortVersionString` |
| `apps[0].versions[0].buildVersion` | `bundleVersion` — write it as a string |
| `apps[0].versions[0].minOSVersion` | `minimumSystemVersions.ios` |

Read them in one pass:

```bash
for k in bundleId appleItemId shortVersionString bundleVersion minimumSystemVersions.ios; do
  printf '%-26s %s\n' "$k" "$(plutil -extract "$k" raw -o - "$ADP/manifest.json")"
done
```

Copy the first four across exactly — no rounding a build number, no dropping a trailing `.0`. The manifest is re-read at install time, and a package whose `bundleId`, `appleItemId`, `shortVersionString`, or `bundleVersion` disagrees with the source won't install. `appleItemId` is the same "Apple ID" App Store Connect shows under App Information, so there's no need to ask the developer for `marketplaceID` when you have the ADP.

`minimumSystemVersions.ios` is what the build actually requires, but `minOSVersion` is what AltStore filters updates on, so if the developer's existing entry says something else, ask before overwriting it.

## From the variant files

| `source.json` key | Where |
| --- | --- |
| `apps[0].versions[0].size` | `stat -f%z` on any file in `$ADP/variant` — bytes, as a number |
| `apps[0].versions[0].date` | today, `date +%F` |

Variants are per-device builds of one release, so any of them is a fair size to show:

```bash
stat -f%z "$(ls "$ADP"/variant/*.ipa | head -1)"
```

Don't total them, and don't count `delta/` — a user downloads one variant, or a delta against the variant they already have.

## What the ADP can't tell you

The `.ipa` files under `variant/` are encrypted. `unzip` won't open one, so there's no `Info.plist` and no `embedded.mobileprovision` in reach. These keys have to come from the build the developer notarized, or from the developer:

| `source.json` key | Where |
| --- | --- |
| `apps[0].name` | ask, or the App Store Connect listing this ADP was built from |
| `apps[0].developerName` | ask — it's the name shown on the store page, not necessarily the signing team's |
| `apps[0].appPermissions.entitlements` | the archive |
| `apps[0].appPermissions.privacy` | the archive |

If they still have the `.xcarchive` Xcode built for this version — Xcode's Organizer, or `~/Library/Developer/Xcode/Archives` — both permission lists are readable from the app bundle inside it:

```bash
APP="$ARCHIVE/Products/Applications/$(ls "$ARCHIVE/Products/Applications" | head -1)"
codesign -d --entitlements :- "$APP" 2>/dev/null | plutil -convert xml1 -o - - | grep '<key>'
plutil -convert xml1 -o - "$APP/Info.plist" | grep -A1 'UsageDescription</key>'
```

Match privacy keys on the `UsageDescription` suffix alone — not every one carries the `NS` prefix (Core NFC's is `NFCReaderUsageDescription`). An app that accesses nothing sensitive has none, which is `{}`; no entitlements is `[]`. Cover app extensions too, not just the main bundle.

When neither the archive nor the developer can produce them, say so plainly and leave the keys alone rather than guessing. The spec requires a source to list every entitlement and privacy permission its apps use, and it's what users read before they install.

## Checking the package is still intact

macOS ships `dist_package_tool`, which verifies an ADP against the `signature` Apple wrote:

```bash
dist_package_tool validate "$ADP" -v
```

A good package prints `Package has a valid signature.` and `All resources are presents and valid.` and exits 0. Anything else exits non-zero — a prettified `manifest.json` and a file moved out of `variant/` both fail it, which is exactly what a botched upload looks like.

Run it before the developer uploads, and again on a local copy of what they uploaded if an install fails. `dist_package_tool display "$ADP"` lists the resource count and the signing chain without validating.
