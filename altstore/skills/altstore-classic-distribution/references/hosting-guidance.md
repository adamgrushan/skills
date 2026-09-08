---
description: Where to host your source and your apps' IPA files.
---

# ☁️ Hosting

## Overview

Your source and your apps' IPA files both need to be hosted somewhere publicly accessible. Your source is only a few kilobytes, but IPA files are often 100 MB or larger, so it's worth picking a host that can handle them.

We suggest using GitHub Releases for both. Release assets can be up to 2 GB each, and it's free for public repos. Backblaze B2, S3 with CloudFront, and your own server or CDN all work well too.

{% hint style="warning" %}
GitHub Pages, Cloudflare Pages, Netlify, and Vercel all limit individual file sizes to well below a typical IPA. They're fine for your source, but host your IPA elsewhere.
{% endhint %}

{% hint style="info" %}
For GitHub Releases, point your source URL at `https://github.com/<you>/<repo>/releases/latest/download/source.json` rather than at a specific tag. This URL always serves your newest release, so the link your users add to AltStore keeps working as you ship updates.
{% endhint %}

## Organizing Your Files

You can put your source and IPA files in a repo dedicated to your source, or alongside your app's code in its existing repo — both work. A dedicated repo keeps your source cleanly separated and easy to point at, while reusing your app's repo is one fewer thing to maintain.

## Hosts to Avoid

Your `downloadURL` needs to serve your IPA file directly to anyone who requests it, and keep doing so.

Consumer file-sharing links won't work. iCloud and large Google Drive files return a web page instead of the file, and Dropbox share links get throttled or suspended under download traffic. Avoid signed or expiring URLs for the same reason — once the token expires, so does your app's download.

{% hint style="info" %}
Patreon-only apps are the exception — you host on Patreon itself, and attachments are capped at 200 MB each.

- **AltStore Classic** — attach the `.ipa` to your post, publish, then right-click the attachment and use **that** URL as your `downloadURL`. Not the post's own URL.
- **AltStore PAL** — attach every file in your ADP (`manifest.json`, `signature`, and all `.ipa` files), publish, and use the **post's** URL as your `downloadURL`.
[Learn more](patreon-integration.md)
{% endhint %}
