# Reading app metadata from an IPA

Every command below reads straight out of the zip and writes nothing. `$IPA` is the developer's `.ipa`.

## Locate the two files

```bash
unzip -Z1 "$IPA" | grep -E '^Payload/[^/]+\.app/(Info\.plist|embedded\.mobileprovision)$'
```

Set `$PLIST` and `$PROFILE` to the two paths it prints:

```bash
PLIST=$(unzip -Z1 "$IPA" | grep -E '^Payload/[^/]+\.app/Info\.plist$')
PROFILE=$(unzip -Z1 "$IPA" | grep -E '^Payload/[^/]+\.app/embedded\.mobileprovision$')
```

Match that exact depth — a watch app or extension nested inside the bundle has its own `Info.plist`, and a looser pattern picks those up too.

## From `Info.plist`

It's a binary plist, so always go through `plutil`:

```bash
unzip -p "$IPA" "$PLIST" | plutil -extract CFBundleIdentifier raw -o - -
```

| `source.json` key | `Info.plist` key |
| --- | --- |
| `apps[0].name` | `CFBundleDisplayName`, else `CFBundleName` |
| `apps[0].bundleIdentifier` | `CFBundleIdentifier` |
| `apps[0].versions[0].version` | `CFBundleShortVersionString` |
| `apps[0].versions[0].buildVersion` | `CFBundleVersion` — write it as a string |
| `apps[0].versions[0].minOSVersion` | `MinimumOSVersion` |

`apps[0].appPermissions.privacy` is every key ending in `UsageDescription`, mapped to its description:

```bash
unzip -p "$IPA" "$PLIST" | plutil -convert xml1 -o - - | grep -A1 'UsageDescription</key>'
```

Match on that suffix alone — not every one carries the `NS` prefix (Core NFC's is `NFCReaderUsageDescription`). An app that accesses nothing sensitive has none, which is `{}`. AltStore checks declared permissions against the IPA and refuses to install an app whose source under-declares, so a missed key breaks the install rather than the source.

## From the provisioning profile

It's a CMS-signed container wrapping a plist, so decode it first:

```bash
unzip -p "$IPA" "$PROFILE" | security cms -D -i /dev/stdin | plutil -extract TeamName raw -o - -
```

| `source.json` key | Profile key |
| --- | --- |
| `apps[0].developerName` | `TeamName` — the signing account's name, not always what they want shown |
| `apps[0].appPermissions.entitlements` | the keys of `Entitlements` (extract it as `xml1` and take the `<key>`s; an empty dict is `[]`) |

When there's no `embedded.mobileprovision` at all — App Store-stripped or genuinely unsigned builds — leave both `developerName` and `appPermissions` on the template's values, and count **both** as placeholders. A half-real `appPermissions` block, with real privacy descriptions beside the template's example entitlements, is worse than an obviously untouched one.

## From the file itself

| `source.json` key | Where |
| --- | --- |
| `apps[0].versions[0].size` | `stat -f%z "$IPA"` — bytes, as a number |
| `apps[0].versions[0].date` | today, `date +%F` |
