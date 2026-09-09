---
description: Where to host your source and your apps' ADPs.
---

# ☁️ Hosting

## Overview

Your source and your apps' Alternative Distribution Packages both need to be hosted somewhere publicly accessible. Your source is only a few kilobytes, but an ADP is a folder of per-device builds and upgrade deltas — 15 to 35 files, and five to fifteen times the bytes of the single IPA it replaces. Budget for that per version you keep listed, and pick a host that can handle it.

We suggest using GitHub Releases for both. Release assets can be up to 2 GB each, and it's free for public repos. Backblaze B2, S3 with CloudFront, and your own server or CDN all work well too.

{% hint style="warning" %}
GitHub Pages, Cloudflare Pages, Netlify, and Vercel serve directories exactly as you upload them, so the structure is no problem — the per-file size limit is. Unless your variants are small, keep your source there and host your ADP elsewhere.
{% endhint %}

{% hint style="info" %}
For GitHub Releases, point your source URL at `https://github.com/<you>/<repo>/releases/latest/download/source.json` rather than at a specific tag. This URL always serves your newest release, so the link your users add to AltStore keeps working as you ship updates.
{% endhint %}

## Uploading an ADP

AltStore reads an ADP as the directory Apple built. Upload every file in it — `manifest.json`, `signature`, and everything under `variant/` and `delta/` — preserving the hierarchy exactly, and leave the contents alone. The `signature` pins each file's bytes *and* its path, so prettifying `manifest.json`, renaming a variant, moving one up a level, or letting a host re-compress a file all break the package and the install fails.

A stray `.DS_Store` inside the folder is enough to fail it, and so is a variant or delta that didn't finish uploading.

macOS can tell you before you upload. `dist_package_tool validate <your ADP folder> -v` reports `Package has a valid signature.` on an intact package, and names the category of problem — modified, added, or missing files — on a broken one.

Point `downloadURL` at the hosted `manifest.json`, or at the ADP's root directory — AltStore accepts either.

{% hint style="success" %}
If your host can't preserve directories — GitHub Releases puts every asset in one flat list — upload the files anyway and add an `assetURLs` object to your version entry saying where each one landed. The keys are bare file names with the extension and the folder dropped: `manifest`, `signature`, and the UUID of every variant **and every delta**. Miss one and that download has nowhere to go. Keep `downloadURL` too; it's required either way, and it's how AltStore recognizes the release.
{% endhint %}

## Organizing Your Files

You can put your source and your ADPs in a repo dedicated to your source, or alongside your app's code in its existing repo — both work. A dedicated repo keeps your source cleanly separated and easy to point at, while reusing your app's repo is one fewer thing to maintain.

Give each release its own folder or tag. An older version's ADP has to stay reachable for users whose device the newest build doesn't support.

## Hosts to Avoid

Your `downloadURL` needs to serve your ADP's files directly to anyone who requests them, and keep doing so.

Consumer file-sharing links won't work. iCloud and large Google Drive files return a web page instead of the file, and Dropbox share links get throttled or suspended under download traffic. Avoid signed or expiring URLs for the same reason — once the token expires, so does your app's download.

{% hint style="info" %}
Patreon-only apps are the exception — you host on Patreon itself, and attachments are capped at 200 MB each. Attach every file in your ADP (`manifest.json`, `signature`, and all `.ipa` files), publish, and use the **post's** URL as your `downloadURL`. To attach more than one ADP to a post, rename each `manifest.json` and `signature` to something unique and name them in `assetURLs`.
[Learn more](patreon-integration.md)
{% endhint %}
