# Distribute with AltStore Classic

## Overview 

Distributing your app with AltStore Classic is as simple as hosting a [source file](https://faq.altstore.io/developers/make-a-source), which is just a JSON file with information about your app(s), along with your apps' exported IPA (.ipa) files. Once your source is live, anyone can add the URL in AltStore Classic to download your apps.

You control when and how you release your apps — no review by Apple necessary.

When ready, follow each of the steps outlined below to begin distributing your apps on AltStore Classic. 🙂 

## Upload your IPA file to your web host

The first step is to upload your IPA file to your web host making sure it's publicly accessible.

## Create a source and upload it to your web host

The next step is to [make a source](https://faq.altstore.io/developers/make-a-source), which is just a JSON file with basic metadata about your apps.

{% hint style="info" %}
You don't need to sign your IPA. AltStore Classic re-signs apps on your users' devices with their own Apple ID, so unsigned builds work fine.
{% endhint %}

Once you've created your source and validated it's correct, upload it to your web host, making sure it's also publicly accessible.
