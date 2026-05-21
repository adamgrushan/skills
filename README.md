# AltStore Skills

[AltStore](https://altstore.io/) is an alternative app store for apps that push the boundaries of iOS.

Distribute and update iOS apps through AltStore Classic using our skill. Works with **Claude Code and OpenAI Codex via marketplaces**, and **other agentic coding environments via [skills.sh](https://www.skills.sh/)**.

## Installation

### Claude Code

From within Claude Code:

```
/plugin
```

Then select `Marketplace`, `+ Add Marketplace`, enter `altstoreio/skills`. Then install the `AltStore` plugin.

Or directly:

```
/plugin marketplace add altstoreio/skills
/plugin install AltStore@AltStore
```

### OpenAI Codex CLI

```bash
codex plugin marketplace add altstoreio/skills
codex plugin add AltStore@AltStore
```

Or start Codex, run `/plugins`, search for `AltStore`, and install.

### OpenAI Codex Desktop App

First, add the marketplace from your terminal:

```bash
codex plugin marketplace add altstoreio/skills
```

Then, in the Codex app, click **Plugins**, find `AltStore` under the AltStore marketplace, and click the **+** button.

### Other agentic coding environments

Use [`npx skills`](https://www.skills.sh/):

```bash
npx skills add altstoreio/skills
```

This auto-discovers skills from the marketplace manifest and installs them for your detected agent (Claude Code, OpenCode, etc.). To target a specific agent:

```bash
npx skills add altstoreio/skills -a claude-code
```

## Example Workflow

### AltStore Classic Distribution

```
You: Can you help me distribute my app on AltStore Classic?

Claude: I'll get started fetching the AltStore template, identifying the IPA, and enriching it from the IPA now.
        What would you like to call your source?

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
