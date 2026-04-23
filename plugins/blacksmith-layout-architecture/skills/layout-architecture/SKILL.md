---
name: layout-architecture
description: Convert a discovery brief into an Octopus import XML and a block level layout spec following the Blacksmith Layout Architecture Playbook. Trigger on phrases like "layout architecture", "build a sitemap", "generate Octopus XML", "turn this brief into a layout", "section and block plan", or when a strategist uploads a filled discovery brief for a site build. Supports three intake modes: filled Markdown brief, structured YAML, or live interactive intake where the skill asks questions one at a time.
---

# Layout Architecture skill

You are running Blacksmith's Layout Architecture skill. The authoritative logic lives in `spec.md` in this skill directory. Read it first. The templates the strategist fills live in `templates/`. Worked example XML lives in `examples/`.

Do the work in this order.

## Step 1. Detect intake mode

Check what the user provided.

- If they attached a filled `discovery-brief.md`, parse it.
- If they attached a `discovery-brief.yaml` or `.json`, load it directly.
- If they attached a `sitemap-request.csv` alongside the brief, load the page list from there.
- If they provided nothing structured (just a request like "help me plan a layout for this client"), enter interactive intake mode.

You can mix modes. A strategist may hand you a filled brief but no sitemap. In that case parse the brief, then ask just the sitemap questions interactively.

## Step 2. Read the spec

Read `spec.md` in full before running any rules. Everything that follows depends on it. The spec defines the input schema in Section 1, the decision rules in Section 2, the block library and Octopus wireframe mapping in Section 3, the output format in Section 4, edge cases in Section 5, and open questions in Section 6.

Do not paraphrase the spec. Execute it literally.

## Step 3. Run interactive intake when needed

When any required field is missing after parsing the provided files, ask for it using AskUserQuestion. Ask one question at a time. Do not dump the full schema on the user. Follow this order, and skip questions the brief already answered.

1. Project title
2. Business model (single pick from the enum in spec.md Section 1.1)
3. Revenue streams (up to three, each with share of revenue, AOV, sales cycle days, growth target flag)
4. Primary persona (name, role, trigger, top three objections, committee size, is technical, state of mind)
5. Secondary personas if any, max two more
6. Buyer journey (the three to five questions buyers ask in order)
7. Positioning claim (single pick from enum)
8. Positioning statement in one sentence
9. Success metric
10. Brand awareness level
11. Content availability checklist (the eight booleans)
12. Sitemap pages (node_title, slug, parent_slug, target_page, page_intent for each)
13. Any known risks or internal disagreements

When the user cannot answer a required field, follow the fallback rules in spec.md. Do not invent values. If positioning_claim is unclear, halt with `ESCALATION_POSITIONING_UNCLEAR` and stop.

## Step 4. Run synthesis and block selection

Execute the rules in spec.md Sections 2.1 through 2.5. Produce the internal state: blocking_friction, proof_hierarchy, positioning_to_structure flags, per page block lists with Octopus wireframe keys.

Pressure test the result against Section 2.5 rules R5.1 through R5.6. When a test fails, list the specific gaps. Do not silently fix them.

## Step 5. Emit three artifacts

Write all three to `outputs/` (or the user's selected folder when one is connected).

1. `{project-slug}.xml`. Valid Octopus scheme 1.0. Validate against the rules in Section 4.1 of spec.md before writing. Run `scripts/validate-octopus.py` on the output. If it fails validation, fix and revalidate. Do not hand off invalid XML.
2. `{project-slug}-layout.json`. The intermediate with synthesis state, pressure test results, decision log, content workstream items.
3. `{project-slug}-layout.md`. The markdown companion: Synthesis, IA Context, Page Blocks with one sentence justification each, Pressure Test Results, Handoff Package, open questions the skill flagged.

Present the files with short computer:// links and a two sentence summary. Do not paste the full XML into chat.

## Step 6. Handle escalations

When the output status is `needs_fixes` or `needs_human_review`, say so plainly at the top of your message and list the specific reasons. Do not bury them.

When a block has `content_gap = true`, tag the node or block in the XML with the `Needs content` tag (color #EA5E5E) as shown in `examples/blacksmith-site.xml`.

## Rules of engagement

- Ask one question at a time in interactive intake. Do not batch.
- Never invent Octopus wireframe keys. Use only the 126 published keys documented in `spec.md` Section 4.2 and in the block library Section 3. If no key fits, omit the `<wireframe>` element and flag the block.
- Never invent content. The `<content>` element in Octopus holds a short note, not drafted copy. Chain to `marketing:draft-content` for actual copy.
- Always run `scripts/validate-octopus.py` before declaring the XML ready.
- When the user says "just give me a sitemap", still run synthesis. Do not skip Phase 2.
- Preserve playbook variant names in `block_title`. This is how we avoid losing intent in the lossy Octopus mapping (see spec.md Section 3.9).
- Use Claude as the author on any tracked changes or comments in output documents.

## When to chain

After the XML imports into Octopus, these skills commonly run next. Mention them at the end when relevant.

- `marketing:draft-content` for block copy
- `design:design-handoff` for engineering specs
- `design:accessibility-review` once visual design is in place
- `anthropic-skills:client-ready-review` before sharing with the client

## Templates

The canonical intake templates live in `templates/`:
- `discovery-brief.md` for the full brief
- `sitemap-request.csv` for the page list
- `content-checklist.md` for content availability

Point the strategist to them when they ask how to prepare inputs.
