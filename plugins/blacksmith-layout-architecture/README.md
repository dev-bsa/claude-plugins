# Layout Architecture (Blacksmith)

Blacksmith Agency skill for converting a discovery brief into an Octopus import XML and a block level layout spec. Encodes the Blacksmith Layout Architecture Playbook so strategists get consistent layouts across clients and across teammates.

## What it does

Takes a filled discovery brief and a sitemap request, runs the playbook's five phases (discovery, synthesis, IA, block selection, pressure test), and emits three artifacts.

1. Valid Octopus scheme 1.0 XML ready to import via File → Import project
2. JSON intermediate with synthesis state, decision log, pressure test results
3. Markdown companion with block justification memo and handoff package

## Three ways to invoke

- **Prepared brief.** Fill `discovery-brief.md` and `sitemap-request.csv`, attach both, tell Claude to run the skill.
- **Partial brief.** Fill what you have. The skill asks for the rest interactively, one question at a time.
- **Live intake.** Invoke with just a project name. The skill runs a guided intake via AskUserQuestion following the playbook's Phase 1 order.

## Installation

Local install from a `.plugin` bundle:

```
/plugin install ./blacksmith-layout-architecture-0.1.0.plugin
```

Or via the Blacksmith internal marketplace (once configured):

```
/plugin marketplace add blacksmith-agency/claude-plugins
/plugin install blacksmith-layout-architecture
```

## Usage

After install, trigger the skill with any of these phrases:

- "Run the layout architecture skill on this brief"
- "Generate Octopus XML from these notes"
- "Build a sitemap for {client}"
- "Turn this discovery into a section and block plan"

## What's inside

```
skills/layout-architecture/
  SKILL.md                  operating manual Claude reads when the skill fires
  spec.md                   full decision logic, block library, rule set
  templates/
    discovery-brief.md      the authored brief
    sitemap-request.csv     the page list
    content-checklist.md    asset availability gate
    README.md               how strategists use the templates
  examples/
    blacksmith-site.xml     worked example, scheme 1.0 validated
  scripts/
    validate-octopus.py     schema check against the published vocabulary
```

## Chains with

- `marketing:draft-content` for block copy after the XML imports
- `design:design-handoff` for engineering specs
- `design:accessibility-review` once visual design is in place
- `anthropic-skills:client-ready-review` before sharing with the client

## Versioning

Pinned to Octopus scheme 1.0 and the Blacksmith Layout Architecture Playbook v1. Breaking changes to either bump the minor version. Tuning to thresholds or rubrics bumps the patch version. Changes reviewed at strategy review.

## Support

Bring bugs, rubric disagreements and pattern proposals to the next strategy review. The spec is a living artifact.
