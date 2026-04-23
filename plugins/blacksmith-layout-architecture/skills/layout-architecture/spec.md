# Layout Architecture Skill Specification

Source: Blacksmith Layout Architecture Playbook
Target system: Octopus (octopus.do), scheme 1.0
Purpose: machine executable spec for a Claude skill that converts discovery inputs into an Octopus XML project ready for import.

This document replaces the playbook prose with a form an automated system can run. It covers inputs, decision rules, the block library with Octopus wireframe mappings, output format, edge cases and open questions. Octopus XML is the canonical output. JSON is an internal intermediate.

---

## 1. Inputs

The skill collects a single `DiscoveryBrief` object. Required fields must be present or resolved through fallbacks before rule evaluation begins. Optional fields refine the output but do not block execution.

### 1.1 Input schema

```yaml
DiscoveryBrief:
  # Business model
  business_model:
    type: enum
    required: true
    values: [b2b_saas, b2b_services, ecommerce_dtc, ecommerce_marketplace, professional_services, nonprofit_donation, cultural_institution, content_publisher, hybrid]
    example: "b2b_saas"
    fallback: ask the user, do not guess

  revenue_streams:
    type: array<RevenueStream>
    required: true
    min_items: 1
    fallback: ask for at least one primary stream
    schema:
      name: string
      percent_of_revenue: number 0-100
      average_order_value_usd: number
      sales_cycle_days: integer
      is_growth_target: boolean

  # Buyer
  personas:
    type: array<Persona>
    required: true
    min_items: 1
    max_items: 3
    fallback: if more than three, ask the user to pick the top three
    schema:
      name: string
      role_or_segment: string
      trigger_event: string
      top_objections: array<string> min 1 max 5
      decision_committee_size: integer
      is_technical: boolean
      state_of_mind: enum [skeptical, inspired, cautious, distracted, credential_checking, task_focused, returning]

  buyer_journey:
    type: array<string>
    required: true
    description: ordered list of the three to five questions every buyer asks
    fallback: propose the generic five step pattern and ask the user to confirm
    min_items: 3
    max_items: 5

  # Positioning
  positioning_claim:
    type: enum
    required: true
    values: [trust, price, craft, speed, vertical_fit, relationships, unclear]
    example: "trust"
    fallback: mark as "unclear" and halt with escalation

  positioning_statement:
    type: string
    required: false
    example: "We are the only platform built on the data model logistics teams actually use."

  # Competitive
  competitors_direct:
    type: array<string>
    required: false
    max_items: 3

  competitors_adjacent:
    type: array<string>
    required: false
    max_items: 3

  structural_conventions_to_break:
    type: array<string>
    required: false
    description: conventions competitors use that this brand will not

  # Success
  success_metric:
    type: enum
    required: true
    values: [demo_requests, qualified_meetings, first_time_buyer_conversion, repeat_purchase, donor_acquisition, ticket_sales, enrollment, inbound_inquiries, newsletter_signup, other]
    fallback: ask; if client cannot answer, flag project as not ready for wireframing

  success_metric_other:
    type: string
    required: false
    description: free text when success_metric is "other"

  # Page context
  target_page:
    type: enum
    required: true
    values: [home, product_detail, program_detail, visit_detail, lodging_detail, event_detail, tickets, company_detail, donate, contact, resource_listing, resource_detail, simple_content_page]
    example: "home"

  device_priority:
    type: enum
    required: false
    default: both
    values: [desktop_first, mobile_first, both]

  brand_awareness_level:
    type: enum
    required: false
    default: emerging
    values: [unknown, emerging, established, high_awareness]
    description: drives whether value prop block can be skipped

  content_availability:
    type: ContentAvailability
    required: false
    schema:
      has_named_case_studies: boolean
      has_logos_with_permission: boolean
      has_reviews: boolean
      has_before_after_imagery: boolean
      has_analyst_coverage: boolean
      has_photography_budget: boolean

  risk_log_entries:
    type: array<string>
    required: false
    description: known disagreements or unresolved strategic questions

  # Octopus project fields
  project_title:
    type: string
    required: true
    example: "Chautauqua Institution"

  sitemap_pages:
    type: array<PageRequest>
    required: true
    min_items: 1
    schema:
      node_title: string
      slug: string starting with /
      target_page: enum (see target_page values)
      parent_slug: optional string
      is_utility: boolean default false
      seo_title: optional string
      seo_description: optional string
      h1: optional string
      keywords: optional array<string>
      page_intent: enum [Informational, Commercial, Transactional, Navigational]

  color_palette:
    type: object
    required: false
    description: hex values used for node and block color attributes
    schema:
      primary: "#RRGGBB"
      proof: "#RRGGBB"
      conversion: "#RRGGBB"
      editorial: "#RRGGBB"
```

### 1.2 Input gathering order

The skill collects inputs in this sequence so downstream questions are informed by upstream answers.

1. `business_model` and `revenue_streams`
2. `target_page`
3. `personas`
4. `buyer_journey`
5. `positioning_claim` and `positioning_statement`
6. `success_metric`
7. `competitors_direct` and `structural_conventions_to_break`
8. `brand_awareness_level` and `content_availability`

When a required field is missing, the skill issues a single targeted AskUserQuestion rather than a bulk form. When a client cannot answer, follow the fallback column above. Disagreements inside the client team get logged to `risk_log_entries`, the skill picks a working answer for the current build and notes the alternative.

---

## 2. Decision rules

Rules run phase by phase. Each phase produces intermediate state that later phases read. Rules are expressed as `if condition then action`. Where the playbook relies on judgment the rule falls back to a scored rubric or a clarifying question.

### 2.1 Phase 1 rules, discovery completeness

```text
R1.1  if any required field is missing
      then halt with ESCALATION_DISCOVERY_INCOMPLETE and ask for it.

R1.2  if positioning_claim == "unclear"
      then halt with ESCALATION_POSITIONING_UNCLEAR,
           do not proceed to Phase 2.

R1.3  if success_metric is not set or is "other" without success_metric_other
      then ask user to resolve before continuing.

R1.4  if revenue_streams.length > 3
      then ask user to identify the top three by share of revenue.

R1.5  if risk_log_entries is non empty
      then mark the handoff output as needs_human_review = true.
```

### 2.2 Phase 2 rules, synthesis

Synthesis produces a `SynthesisProfile` consumed by block selection.

```text
R2.1  state_of_mind := personas[0].state_of_mind

R2.2  blocking_friction by (state_of_mind, positioning_claim):
        (skeptical, trust) credibility | (skeptical, price) value_justification
        (skeptical, vertical_fit) comprehension | (inspired, craft) inspiration
        (cautious, relationships) confidence_in_fit | (distracted, any) comprehension_fast
        (credential_checking, any) credential_depth | (task_focused or returning, any) task_completion
      fallback: ask the user to pick from the list.

R2.3  proof_hierarchy by (business_model, positioning_claim):
        B2B SaaS or services with trust or vertical_fit:
          named_case_studies (vertical preferred), logo_wall (filtered to vertical),
          analyst_quote, numerical_metrics
        DTC consumer with trust or craft:
          before_after_photography, expert_endorsement (dermatologist, editor),
          editorial_quote (press), user_reviews
        Professional services with relationships:
          reported_outcomes_list, senior_partner_bios, published_work, awards (only if recognizable)
        Cultural institution with craft:
          editorial_storytelling (legacy as proof), historical_legacy, community_testimonial
        Nonprofit with trust:
          impact_numbers (dollars raised, people served), named_giving_circles,
          beneficiary_stories

R2.4  positioning_to_structure flags:
        trust        social_proof_above_fold, editorial_about_required
        price        price_visible_first_scroll, comparison_block_required
        craft        editorial_hero_preferred, low_density_required
        speed        outcome_first_hero, before_after_required
        vertical_fit vertical_claim_in_hero, vertical_case_study_required
        relationships low_density_required, editorial_hero_preferred, single_contact_path
```

### 2.3 Phase 3 rules, page level IA

The skill may be called with a single page target or a full sitemap request. For sitemap mode each candidate page runs through the four conditions.

```text
R3.1  score_page(candidate):
        score = 0
        if distinct_job                then score += 1
        if distinct_audience           then score += 1
        if distinct_search_intent      then score += 1
        if distinct_conversion_model   then score += 1
        return score

R3.2  if score == 0 then do_not_create
      if score == 1 then create_as_section_on_parent, flag_revisit_post_launch
      if score >= 2 then create_as_page with its own template

R3.3  depth_limit = 3
      if a candidate page lives at depth 4 or deeper
      then flag FLATTEN_HIERARCHY or propose filters and facets

R3.4  hierarchy must be organized by buyer task, not internal org chart.
      if proposed nav mirrors departmental structure
      then rewrite using task groupings and ask user to confirm

R3.5  breadcrumbs required when depth >= 2
R3.6  subnav required when a page has siblings the user may compare
R3.7  related content block required when lateral relationship strength >= moderate
R3.8  journey CTA required when a linear next step exists
```

Distinctness is a judgment call. The skill handles it by asking the user a multiple choice question for each candidate page, with the four conditions as checkboxes. Two or more checked, it is a page. Zero or one, it is a section.

### 2.4 Phase 4 rules, section and block selection

Block selection runs per page. Each page produces an ordered list of blocks.

```text
Hero
R4.1  high_awareness AND target_page==home -> entry_led
R4.2  positioning in [trust, vertical_fit, price] AND state_of_mind in [skeptical, cautious, credential_checking] -> claim_led
R4.3  positioning==craft AND has_photography_budget -> visual_led
R4.4  state_of_mind in [returning, task_focused] -> entry_led
R4.5  target_page in [visit_detail, program_detail, product_detail, lodging_detail, event_detail, resource_detail] -> half_hero
R4.6  audience mixes first time and returning -> hybrid_claim_plus_entry

Value proposition
R4.7  high_awareness -> skip (replace with utility ribbon)
R4.8  positioning_statement strong and single threaded -> single_sentence
R4.9  three genuinely distinct legs all required -> three_column (never default; confirm distinctness)
R4.10 else -> single_sentence

Social proof
R4.11 pick top two from proof_hierarchy with content available; else ask which assets exist
R4.12 if social_proof_above_fold flag -> immediately after hero; else after value_prop
R4.13 cap at two formats per page

Feature explanation
R4.14 buyer_mode = compare if is_technical AND committee>=3;
                  imagine if state_of_mind==inspired;
                  else understand
R4.15 by buyer_mode: understand -> numbered_steps or animated_walkthrough;
                     compare -> side_by_side or before_after_screenshots;
                     imagine -> editorial_with_photography
R4.16 icon_grid only when understand AND claim_is_technical==false

Objection handling
R4.17 blocking_friction in [credibility, comprehension, value_justification, confidence_in_fit] -> foregrounded
R4.18 else -> hidden FAQ accordion
R4.19 pull top three objections from persona; flag if fewer

Conversion
R4.20 friction_score: +2 if success_metric in [demo_requests, qualified_meetings, inbound_inquiries];
                      +1 if committee>=3; +1 if AOV>=5000
R4.21 score>=2 -> repeat_high_visibility (hero, mid page, end, sticky on long pages);
      else single_late_placement
R4.22 never stack two primary CTAs; secondaries must be visually subordinate
R4.23 big_box_cta at end when target_page in [program_detail, tickets, company_detail, donate, product_detail]

Editorial or narrative
R4.24 include when positioning in [craft, relationships, trust] AND business_model in
      [cultural_institution, professional_services, content_publisher, nonprofit_donation]
R4.25 enterprise B2B with published research -> research_library block
```

### 2.5 Phase 5 rules, pressure tests

```text
R5.1  buyer_test: walk the assembled block list as persona[0].
      for each adjacent block pair, check continuity.
      if continuity_score < threshold, flag ORDERING_ISSUE.

R5.2  business_test:
      if the block that moves success_metric is not in the first 40 percent of the page
      then flag SUCCESS_METRIC_BURIED.

R5.3  ia_test:
      if target_page depth > 1 and breadcrumb not present in output then add breadcrumb.
      if siblings exist and subnav not present then add subnav.

R5.4  content_test:
      for each block, check content_availability fields.
      if a required asset is missing, mark the block content_gap = true
      and add a content workstream item.

R5.5  responsive_test:
      for each block, check mobile_variant defined.
      if three_column or side_by_side block lacks a stack or horizontal scroll plan,
      flag RESPONSIVE_GAP.

R5.6  if any test fails, mark output status = needs_fixes
      and list the specific gaps. Do not mark ready for handoff.
```

---

## 3. Block library

Each variant below carries its Octopus wireframe key(s). When the skill emits XML, the `block_title` captures the playbook variant name and the `wireframe` element carries the Octopus key. Comma separated wireframe values are allowed when one block needs two keys rendered together (for example a hero that uses `text_on_image` plus `button`).

### 3.1 Hero
Purpose: name the audience, make a claim, offer an entry point.

| Variant | Trigger | Wireframe key(s) |
|---|---|---|
| claim_led | sharp positioning, skeptical cold buyer (R4.2) | `cta_left` or `cta_right` |
| visual_led | craft positioning, photography available (R4.3) | `text_on_image` or `hero_with_arrows` |
| entry_led | high awareness home, or returning task focused user (R4.1, R4.4) | `searchbar`, `header` |
| hybrid_claim_plus_entry | mixed first time and returning audience (R4.6) | `cta_left`, `searchbar` |
| half_hero | any detail page deep in the site (R4.5) | `title_and_paragraph`, `breadcrumbs` |

Data required: `block_title`, `content` (headline plus subhead), primary CTA label, optional secondary CTA, hero image asset ref when visual or hybrid, breadcrumb path when half hero.

### 3.2 Value proposition
Purpose: translate positioning into user facing language.

| Variant | Trigger | Wireframe key(s) |
|---|---|---|
| single_sentence | strong single threaded positioning, default (R4.8, R4.10) | `title_and_paragraph` |
| three_column | three genuinely distinct legs all required to evaluate (R4.9) | `features_triple` |
| statement_plus_animation | when motion clarifies the claim | `text_and_video` |
| skip (utility ribbon) | high awareness brand, skip convincing (R4.7) | `features` or `steps` |

Data required: headline, supporting legs (1 or 3), optional supporting visual.

### 3.3 Social proof
Purpose: answer the question, who else has done this. Max two formats per page (R4.13).

| Variant | Buyer context | Wireframe key(s) |
|---|---|---|
| named_case_studies | B2B, long cycle | `articles` or `cards` |
| logo_wall | B2B, trust | `logos` |
| press_mentions | consumer, editorial | `logos` or `quote` |
| editorial_quotes | consumer, craft | `quote` |
| user_reviews | consumer, trust | `rating`, `articles_2` |
| numerical_proof_points | B2B, impact | `features_quarter` |
| community_testimonials | nonprofit, cultural | `articles_3` |
| before_after_photography | DTC, craft | `double`, `text_on_image_3` |
| editorial_storytelling | cultural, legacy | `articles_2`, `text_and_video` |

Data required: format variant, items with source and attribution, placement per R4.12.

### 3.4 Feature explanation
Purpose: make the thing concrete for the buyer.

| Variant | Buyer mode | Wireframe key(s) |
|---|---|---|
| icon_grid | understand | `features_triple`, `features_quarter` |
| side_by_side_comparison | compare | `image_right`, `text_and_video` |
| animated_walkthrough | understand, compare | `text_and_video` |
| numbered_steps | understand | `steps` |
| product_carousel | imagine | `carousel`, `slider` |
| editorial_long_form | imagine | `text_double`, `articles_2` |
| before_after_screenshots | compare | `double` |

Data required: buyer_mode, steps or panels array, per step title body and visual ref.

### 3.5 Objection handling
Purpose: clear the reasons a buyer will not act.

| Variant | Placement | Wireframe key(s) |
|---|---|---|
| faq_accordion | hidden | `faq`, `accordeon` |
| foregrounded_section | near conversion | `features_double`, `title_and_paragraph` |
| comparison_table | foregrounded | `table`, `pricing` |
| guarantee_statement | inline | `cta` or `title_center` |
| return_policy | hidden | `faq` |
| trust_badges | inline | `logos` |
| myth_vs_fact | foregrounded | `text_double` |

Data required: objections array with question and answer, placement, minimum three items (R4.19).

### 3.6 Conversion
Purpose: move the user to the next step.

| Variant | Use when | Wireframe key(s) |
|---|---|---|
| primary_form_fill | high friction | `form`, `contact_form`, `sign_up` |
| big_box_cta | end of page | `cta`, `cta_2` |
| sticky_bar | long page, high friction | `mobile_bottom_bar` |
| inline_text_link | low friction | `button`, `left_button` |
| dedicated_section_card | mid page repeat | `cta_left`, `cta_right` |

Data required: action label, form fields when applicable, success URL, placement list, is_primary boolean. R4.22 forbids stacked primaries.

### 3.7 Editorial or narrative
Purpose: carry story, craft or legacy.

| Variant | Use when | Wireframe key(s) |
|---|---|---|
| editorial_feature | craft, trust | `articles`, `articles_2` |
| research_library | enterprise B2B | `cards`, `catalog` |
| this_week_ribbon | seasonal, cultural | `features`, `slider` |
| history_storytelling | legacy brand | `timeline`, `timeline_2` |

### 3.8 Supporting blocks

| Block | Trigger | Wireframe key(s) |
|---|---|---|
| breadcrumb | R3.5 | `breadcrumbs` |
| subnav | R3.6 | `tabs`, `no_logo_navigation` |
| related_content | R3.7 | `cards`, `articles_3` |
| header | every page | `header`, `header_type_2` |
| footer | every page | `footer`, `footer_type_2` |
| newsletter signup | low friction conversion | `newsletter` |
| utility_ribbon | R4.7 | `features`, `store_buttons` |

### 3.9 Lossy mapping note

Octopus has 126 wireframe keys and the playbook has roughly 40 variants. The mapping is many to one. When the skill emits XML, the playbook variant is preserved in `block_title` so the intent is not lost on round trip. Justification memo and decision log stay in the markdown companion for the same reason.

---

## 4. Outputs

The skill emits three artifacts.

1. **Octopus XML** (primary). A valid `octopus scheme="1.0"` document ready to import via Octopus → File → Import project. This is the canonical deliverable.
2. **JSON intermediate** (internal). Captures synthesis state, pressure test results and decision log. Not imported into Octopus but kept alongside the XML for traceability.
3. **Markdown companion** (review). Block justification memo, decision log, content gaps and pressure test results. This is what strategists and designers read on review.

### 4.1 Octopus XML requirements

Mandatory elements: `<octopus scheme="1.0">`, `<project_title>`, `<tree>`, at least one `<section>`, and `<node_title>` on every node. Slugs must start with `/`, be lowercase and hyphen separated. `page_intent` must be one of `Informational`, `Commercial`, `Transactional`, `Navigational`. Colors must be hex, no named or rgba. Tag values on nodes must match entries in the project level `<tags>` block.

Structural rules pulled from the Octopus import docs. Multiple sections are allowed and should be used to separate main site pages from utility pages (404, legal, login). Nodes can nest via `<children>` to multiple levels. Use `<children/>` self closing when a page has no child pages. Omit optional fields entirely when content does not exist, do not emit empty tags.

### 4.2 Wireframe vocabulary

The skill restricts `<wireframe>` values to the Octopus scheme 1.0 vocabulary of 126 keys documented at https://help.octopus.do/article/195-how-to-import-a-project. Section 3 of this spec lists every key the skill is allowed to emit per block family. The skill never invents a key. If no key in the vocabulary fits, the skill omits the `<wireframe>` element and flags the block for review.

### 4.3 Example output

```xml
<?xml version="1.0" encoding="UTF-8"?>
<octopus scheme="1.0">
  <project_title>Acme Logistics Platform</project_title>
  <tags>
    <tag color="#18C4A9">Primary</tag>
    <tag color="#EA5E5E">Needs content</tag>
  </tags>
  <tree>
    <section>
      <node color="#18C4A9" tag="Primary">
        <node_title>Home</node_title>
        <seo>
          <seo_title>Workflow automation for logistics</seo_title>
          <slug>/</slug>
          <description>The only platform built on the data model logistics teams use.</description>
          <h1>Built for how logistics teams actually operate</h1>
          <keywords>logistics automation, workflow platform</keywords>
          <page_intent>Commercial</page_intent>
        </seo>
        <blocks>
          <block color="#18C4A9">
            <block_title>Hero claim_led</block_title>
            <wireframe>cta_left</wireframe>
            <content>Headline and subhead naming the vertical claim, primary CTA Request demo.</content>
          </block>
          <block>
            <block_title>Social proof named_case_studies</block_title>
            <wireframe>articles</wireframe>
            <content>Two logistics case studies with named operators and metrics.</content>
          </block>
          <block>
            <block_title>Social proof logo_wall</block_title>
            <wireframe>logos</wireframe>
            <content>Filtered to logistics customers.</content>
          </block>
          <block>
            <block_title>Feature explanation side_by_side</block_title>
            <wireframe>image_right</wireframe>
            <content>Before and after screenshots of the data model in use.</content>
          </block>
          <block color="#EA5E5E" tag="Needs content">
            <block_title>Objection handling foregrounded</block_title>
            <wireframe>features_double</wireframe>
            <content>Integration timeline, security posture, data residency, procurement.</content>
          </block>
          <block>
            <block_title>Conversion big_box_cta</block_title>
            <wireframe>cta</wireframe>
            <content>Demo request with self qualifying fields.</content>
          </block>
        </blocks>
        <children/>
      </node>
    </section>
  </tree>
</octopus>
```

### 4.4 Example output, nested sitemap

Home page with two children, demonstrating `<children>` nesting, multiple sections (main vs utility), and proper use of `<children/>` on leaf nodes. Drawn from the Chautauqua pattern.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<octopus scheme="1.0">
  <project_title>Chautauqua Institution</project_title>
  <tags>
    <tag color="#18C4A9">Primary</tag>
    <tag color="#EA5E5E">Needs content</tag>
  </tags>
  <tree>
    <section>
      <node color="#18C4A9" tag="Primary">
        <node_title>Home</node_title>
        <seo>
          <seo_title>Chautauqua Institution</seo_title>
          <slug>/</slug>
          <description>Cultural and educational programming on a historic lakeside campus.</description>
          <page_intent>Informational</page_intent>
        </seo>
        <blocks>
          <block>
            <block_title>Hero hybrid_claim_plus_entry</block_title>
            <wireframe>cta_left, searchbar</wireframe>
            <content>Orientation headline with a plan your visit entry widget.</content>
          </block>
          <block>
            <block_title>Editorial this_week_ribbon</block_title>
            <wireframe>features</wireframe>
            <content>This week at Chautauqua, time sensitive programming tiles.</content>
          </block>
        </blocks>
        <children>
          <node>
            <node_title>Visit</node_title>
            <seo>
              <seo_title>Plan your visit</seo_title>
              <slug>/visit</slug>
              <page_intent>Navigational</page_intent>
            </seo>
            <blocks>
              <block>
                <block_title>Half hero</block_title>
                <wireframe>title_and_paragraph, breadcrumbs</wireframe>
                <content>Visit overview with breadcrumb.</content>
              </block>
              <block>
                <block_title>Related content</block_title>
                <wireframe>cards</wireframe>
                <content>Lodging, dining, programs.</content>
              </block>
            </blocks>
            <children>
              <node>
                <node_title>Plan and Prepare</node_title>
                <seo>
                  <slug>/visit/plan-and-prepare</slug>
                  <page_intent>Informational</page_intent>
                </seo>
                <blocks>
                  <block>
                    <block_title>FAQ</block_title>
                    <wireframe>faq</wireframe>
                  </block>
                </blocks>
                <children/>
              </node>
            </children>
          </node>
          <node color="#EA5E5E" tag="Needs content">
            <node_title>Programs</node_title>
            <seo>
              <slug>/programs</slug>
              <page_intent>Commercial</page_intent>
            </seo>
            <blocks>
              <block>
                <block_title>Catalog</block_title>
                <wireframe>catalog</wireframe>
                <content>Filter left, program cards right.</content>
              </block>
            </blocks>
            <children/>
          </node>
        </children>
      </node>
    </section>
    <section>
      <node>
        <node_title>404</node_title>
        <seo><slug>/404</slug><page_intent>Navigational</page_intent></seo>
        <blocks>
          <block><block_title>Error 404</block_title><wireframe>error_404</wireframe></block>
        </blocks>
        <children/>
      </node>
    </section>
  </tree>
</octopus>
```

Notes on the example. The main site and utility pages live in separate `<section>` blocks. Leaf nodes use self closing `<children/>`. The Programs node carries a tag and a color because it has a content gap flagged by the content test. Optional SEO fields are omitted where no content exists (for example no `description` on Plan and Prepare), not emitted as empty tags.

### 4.5 JSON intermediate

The JSON captures fields Octopus XML cannot hold, including `synthesis` (state_of_mind, blocking_friction, proof_hierarchy), `pressure_tests` results, `decision_log` entries and `content_workstream` items. It references each block by `block_title` so it aligns one to one with nodes in the XML.

### 4.6 Markdown companion

Structured as Synthesis, IA Context, Page Blocks with one sentence justification each, Pressure Test Results, Handoff Package. Designed for a live walkthrough with the designer and account lead.

---

## 5. Edge cases and escalations

The skill stops and asks rather than guesses in these cases.

```text
E1  positioning_claim == "unclear"
    -> halt. Return to discovery. Do not wireframe.

E2  required input missing after two clarification rounds
    -> halt with ESCALATION_DISCOVERY_INCOMPLETE and list the exact fields.

E3  internal disagreement detected in the brief
    (for example conflicting success metrics or two personas described as primary)
    -> pick the first as working answer, log the second in risk_log_entries,
       flag needs_human_review = true.

E4  target_page not in supported list
    -> ask user whether to treat as simple_content_page or add a new template.

E5  block that needs proof has no matching content availability
    (for example social_proof variant named_case_studies but has_named_case_studies is false)
    -> swap to next format in proof_hierarchy with available content,
       add content_workstream item for the preferred format.

E6  three_column value prop selected but only one or two distinct legs identified
    -> force single_sentence variant and note the reason.

E7  sitemap exceeds three levels of depth
    -> recommend flattening, offer filters and facets, ask user to confirm the restructure.

E8  positioning to structure produces conflicts
    (for example price forces visible price in first scroll but business model is
     donation based and has no price)
    -> flag POSITIONING_MISMATCH and ask user to reclassify positioning_claim.
```

The skill flags the output for human review when any of the following are true.

```text
H1  risk_log_entries is not empty.
H2  content_test status is fail.
H3  a block includes content_gap = true.
H4  blocking_friction could not be derived unambiguously.
H5  personas[0].top_objections length < 3 and objection_handling is foregrounded.
H6  business_model == hybrid and revenue_streams have no clear growth target.
H7  Phase 3 condition scoring relied on user judgment rather than structured signals.
```

In all human review cases the JSON status is `needs_human_review` and the markdown companion lists the reasons at the top of the file.

---

## 6. Open questions

Playbook logic that is too ambiguous to automate today. These are the areas to refine in the next playbook revision or to accept as human judgment calls the skill surfaces rather than resolves.

```text
Q1  Three column value prop distinctness. No structural test in the prose.
    Resolution: require one sentence per leg, ask the user to confirm each
    names a different buyer benefit.

Q2  Compound buyers with two dominant frictions (skincare example).
    Resolution: fallback question asking which friction dominates. A scoring
    rubric would be better with calibration data.

Q3  Structural differentiation from the competitive set requires reading
    competitor sites, out of scope for a discovery skill. Resolution: accept
    structural_conventions_to_break as user input.

Q4  Content outline drafting is a separate step. Chain into
    marketing:draft-content after XML export.

Q5  Responsive choices beyond stacking. Tables become cards or horizontal
    scroll. Resolution: cards when rows <= 4, scroll otherwise, surface to user.

Q6  Distinct search intent relies on judgment. Skill asks the user. Future
    revision could pull keyword data from Ahrefs.

Q7  Brand awareness thresholds for skipping value prop are not data driven.
    Four levels used today. Resolution: add branded search volume when
    connected.

Q8  Editorial storytelling as disguised social proof (Chautauqua). Heuristic
    is fragile. Resolution: let the user tag assets as proof eligible.

Q9  Primary persona selection when two personas are equally primary. The
    hybrid hero handles home, deeper pages still need a pick. Resolution:
    ask per page when the split is not obvious.

Q10 Conversion friction_score thresholds in R4.21 are drawn from playbook
    examples, not validated. Treat as tunable, review after ten runs.
```

---

## 7. Notes for implementers

The skill runs in a single pass, discovery in and Octopus XML out. No second model call. Fold the Octopus transformation rules directly into Phase 4 so the block selection logic already emits valid wireframe keys. Validate the XML against the scheme 1.0 requirements before returning it, reject any `page_intent` outside the four allowed values and any wireframe key outside the published vocabulary.

The skill chains with other Blacksmith skills. After export, hand the block list to `marketing:draft-content` for copy and `design:design-handoff` for engineering specs. Pressure tests can run as a separate pass once content is drafted.

Block library, rule set and wireframe vocabulary are versioned together under `playbook_version` and `octopus_scheme`. Changes to either increment the version so historical outputs stay traceable. Blacksmith strategy review owns the bumps.
