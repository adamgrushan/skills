# AltStore Skills

[AltStore](https://altstore.io/) is an alternative app store for apps that push the boundaries of iOS.

Distribute and update iOS apps through AltStore Classic using our skill. Works with **Claude Code and OpenAI Codex via marketplaces, Xcode 27 via Agents in XCode,** and **other agentic coding environments via [skills.sh](https://www.skills.sh/)**.

Across agentic coding environments, the agent should mention it's using an AltStore skill once prompted. You may need to start a new session after adding the skill so it loads.

## Installation

### Claude Code Desktop App

First, run the following command in your terminal:

```
/plugin
```

Then select `Marketplace`, `+ Add Marketplace`, enter `altstoreio/skills`. Then install the `AltStore` plugin.

### Claude Code CLI

```
claude plugins marketplace add altstoreio/skills
claude plugins install AltStore
```

### OpenAI Codex Desktop App

First, install the marketplace by running the following command in your terminal:

```
codex plugin marketplace add altstoreio/skills
```

Then, in the Codex app, click **Plugins**, find `AltStore` under the AltStore marketplace, and click the **Install** button.

### OpenAI Codex CLI

```
codex plugin marketplace add altstoreio/skills
codex plugin add AltStore@AltStore
```

### Xcode 27

Go to Xcode -> Settings -> Intelligence and click the Plug-ins row under Agents in Xcode. Then click the Add Plug-in button. In the sheet, choose Add from URL and click Continue. In the next sheet, enter the following URL: https://github.com/altstoreio/skills.git. Click Continue. In the final sheet, select the skills that you want to install and click Import. 

### Other agentic coding environments

Use [`npx skills`](https://www.skills.sh/):

```bash
npx skills add altstoreio/skills
```

## Example Workflow

### AltStore Classic Distribution

```
You: Can you help me distribute my app on AltStore Classic?

Claude: I'll get started fetching the AltStore template, identifying the IPA, and enriching 
        it from the IPA now. What would you like to call your source?

You: Adam's Source

...

Claude: Here's your source JSON:
        [source.json]
        ...
        🚀 You can upload this file to your web host now, then add the hosted file's URL in 
        AltStore Classic on your phone to see it in action. 🚀
```

## Support

- [AltStore FAQ](https://faq.altstore.io/)
- File an issue in this repository

## License

TBD
