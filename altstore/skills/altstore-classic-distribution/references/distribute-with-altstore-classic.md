# Distribute with AltStore Classic

Distributing your app with AltStore Classic is as simple as hosting a source file, which is just a JSON file with information about your app(s), along with your apps' exported IPA (.ipa) files. Once your source is live, anyone can add the URL in AltStore Classic to download your apps.

You control when and how you release your apps — no review by Apple necessary.

Before you start, you'll need:
- An IPA file of your app(s).
- A publicly accessible web host. GitHub Pages, Cloudflare Pages, Netlify, Vercel, S3 with CloudFront, or your own server are all fine.

Once you've got these prerequisites, follow both of the steps outlined below to distribute your apps on AltStore Classic. 🙂 

## Create a source and upload it to your web host

The first step is to make a source, which is just a JSON file with basic metadata about your apps.

Once you've created your source and validated it's correct, upload it to your web host, making sure it's also publicly accessible.

## Upload your IPA file to your web host

Next, upload your IPA file to your web host, making sure it's publicly accessible.

*Use a stable URL.* The path you publish in your source will become the download location. If your IPA URL changes between releases, existing users won't get updates. So, avoid URLs that include hashes, build IDs, or expiring tokens unless you plan to update the source JSON every release.
