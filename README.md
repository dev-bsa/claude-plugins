# Blacksmith plugin marketplace

Internal Claude plugin marketplace for Blacksmith Agency. Strategy, design and delivery tooling for the team.

## Install the marketplace

**In Claude Code:**

```
/plugin marketplace add blacksmith-agency/claude-plugins
```

**In Cowork:**

Open Settings, go to Plugins, click Add marketplace, paste the repo URL `https://github.com/blacksmith-agency/claude-plugins`.

## Install a plugin from this marketplace

**In Claude Code:**

```
/plugin install blacksmith-layout-architecture@blacksmith
```

**In Cowork:**

Settings, Plugins, Browse Blacksmith marketplace, click Install on the plugin you want.

## Available plugins

| Plugin | Version | Description |
|---|---|---|
| blacksmith-layout-architecture | 0.1.0 | Convert a discovery brief into an Octopus import XML and a block level layout spec following the Blacksmith Layout Architecture Playbook. |

## Publishing a new plugin

1. Create the plugin folder under `plugins/<plugin-name>/`
2. Add the plugin to the `plugins` array in `.claude-plugin/marketplace.json`
3. Commit and push to `main`
4. Team members update with `/plugin marketplace update blacksmith`

## Versioning a plugin

Bump the `version` field in the plugin's `.claude-plugin/plugin.json` and in the marketplace manifest entry. Tag the commit with `plugin-name-vX.Y.Z` for easy rollback.

## Support

Bring issues to the next strategy review or drop a note in the Slack channel.
