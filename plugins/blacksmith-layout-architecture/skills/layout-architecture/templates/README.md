# Intake templates

Three templates drive the Layout Architecture skill. Fill them before invoking the skill, or let the skill drive an interactive intake.

## Files

- `discovery-brief.md`: the full brief covering business model, personas, positioning, success metrics, competitive set, and brand context. This is the document a strategist authors after a discovery call.
- `sitemap-request.csv`: the page list. One row per page with node_title, slug, parent_slug, target_page, page_intent and SEO fields. Kept as CSV because sitemaps are spreadsheet shaped in practice.
- `content-checklist.md`: eight to twelve yes or no questions about what proof and content assets actually exist. Drives social proof format selection and flags content gaps.

## Three ways to use them

**Full brief, ready to run.** Fill `discovery-brief.md` and `sitemap-request.csv`. Attach both when invoking the skill. The skill reads, runs, emits XML. Best when discovery is complete and you want a clean first pass.

**Partial brief, skill fills the rest.** Fill what you know. The skill parses what is there, then asks AskUserQuestion for the missing fields, one at a time. Best when discovery is half done or when you want to hand off a rough brief and let Claude tighten it.

**No brief, live intake.** Invoke the skill with just a project name. It runs a guided conversation, asking one question at a time in the order defined in `SKILL.md`. Best for a working session with the client in the room or a fast scoping pass.

## Field naming

The skill reads field names literally. Do not rename fields. When a field does not apply, write `n/a`. When a client could not answer, write `unknown` and the skill will propose a working default per the playbook fallback rules.

## Handoff pairing

These intake artifacts travel with the project. Keep the filled brief, CSV and checklist in the project repo alongside the Octopus XML output and the markdown companion. They are the full paper trail for the strategy decisions.
