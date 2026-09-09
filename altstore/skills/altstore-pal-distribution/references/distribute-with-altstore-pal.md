# Distribute with AltStore PAL

## Overview

Distributing your app with AltStore PAL is closer to submitting to the App Store than to sideloading. You still submit through App Store Connect with a paid Apple Developer account, and Apple still notarizes the build. What's different is that you host the result yourself, and your apps are available in the EU, Japan, and Brazil.

You can distribute with AltStore PAL from anywhere. You **do not** need to be located in or have a business in the EU, Japan, or Brazil.

When ready, follow each of the steps outlined below to begin distributing your apps on AltStore PAL. 🙂

## Agree to the Alternative EU Terms Addendum

An additional agreement with Apple, required to distribute outside the App Store in the EU: https://developer.apple.com/contact/request/alternative-eu-terms-addendum/

It changes your commission rates and fees for apps distributed in the EU. If you're only distributing in Japan, you don't need it.

## Add AltStore PAL as an alternative marketplace

Register your Developer ID with AltStore PAL using the [REST API](https://faq.altstore.io/developers/rest-api), then enter the security token you get back in App Store Connect under Users and Access → Integrations → Marketplace. Select the apps you want to distribute with AltStore PAL, and let AltStore PAL process your builds automatically.

Every app must be processed by AltStore PAL before it can be distributed. If you'd rather not have it happen automatically, process a build yourself through the same REST API.

## Submit your app for Notarization

Even outside the App Store, Apple still reviews your app — Notarization is that review, with fewer guidelines. In App Store Connect, set the Review Type to "Notarization" and submit. An app you're also shipping on the App Store is notarized automatically when it's approved.

## Host your Alternative Distribution Package (ADP)

Once notarized, download the ADP with the [REST API](https://faq.altstore.io/developers/rest-api) and upload the complete package to your host. Preserve the directory hierarchy exactly and don't change any file's contents — **do not modify `manifest.json` in any way, including prettifying it.**

## Create a source and upload it to your web host

The last step is to [make a source](https://faq.altstore.io/developers/make-a-source), which is just a JSON file with basic metadata about your apps. Once you've created your source and validated it's correct, upload it to your web host, making sure it's publicly accessible.

Anyone can then add the URL to download your apps. (Requires AltStore PAL 2.2 or later.)

## Make your source discoverable (optional)

Add a `fediUsername` to your source and federate it through the REST API, and your apps and updates appear automatically on https://explore.alt.store, where anyone can find them.
