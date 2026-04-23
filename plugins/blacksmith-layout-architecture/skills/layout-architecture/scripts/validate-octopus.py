#!/usr/bin/env python3
"""
Validate an Octopus scheme 1.0 XML file against the published import requirements.
Usage: python validate-octopus.py path/to/file.xml
Exit 0 on pass, 1 on fail. Prints errors and warnings to stderr.
"""
import sys
import re
import xml.etree.ElementTree as ET

# Octopus scheme 1.0 wireframe vocabulary (126 keys)
WIREFRAME_KEYS = {
    "accordeon", "accordeon_2", "app_store_buttons", "articles", "articles_2",
    "articles_3", "audio_player", "back", "breadcrumbs", "bullet_points",
    "bullet_points_double", "button", "calendar", "cards", "cards_left",
    "cards_right", "carousel", "catalog", "catalog_2", "chart",
    "contact_form", "cta", "cta_2", "cta_left", "cta_right",
    "divider", "divider_dashed", "double", "download", "dropdown",
    "error_404", "faq", "features", "features_double", "features_quarter",
    "features_triple", "features_triple_center", "filter", "footer", "footer_type_2",
    "form", "form_2", "form_3", "forward", "hamburger",
    "hamburger_right", "header", "header_type_2", "hero_with_arrows",
    "hierarchy_1", "hierarchy_2", "image", "image_placeholder", "image_right",
    "input", "inputs", "interface_header", "invoice", "language",
    "left_button", "loading", "loading_2", "logos", "map",
    "map_2", "map_3", "messengers", "mobile_bottom_bar", "mobile_top_bar",
    "newsletter", "no_logo_navigation", "pagination", "pie_chart", "post_thread",
    "pricing", "product_card", "profile", "qr_code", "quote",
    "radio_buttons", "rating", "right_button", "searchbar", "sign_up",
    "slider", "social_buttons", "spacer", "steps", "store_buttons",
    "store_buttons_2", "table", "table_2", "table_of_contents", "table_row",
    "tabs", "team", "text", "text_and_form", "text_and_form_2",
    "text_and_sidebar_form", "text_and_video", "text_and_video_2", "text_double",
    "text_on_image", "text_on_image_2", "text_on_image_3", "text_quarter",
    "text_triple", "timeline", "timeline_2", "title", "title_and_paragraph",
    "title_center", "title_left", "todo", "toggle", "triple",
    "two_column_slider", "upload_button", "video", "wide",
}

PAGE_INTENTS = {"Informational", "Commercial", "Transactional", "Navigational"}
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
SLUG_RE = re.compile(r"^/[a-z0-9\-/]*$")


def err(msg, errors):
    errors.append(msg)


def warn(msg, warnings):
    warnings.append(msg)


def validate(path):
    errors, warnings = [], []
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return [f"Not well formed XML: {e}"], []

    root = tree.getroot()

    # Root
    if root.tag != "octopus":
        err(f"Root must be <octopus>, got <{root.tag}>", errors)
    if root.get("scheme") != "1.0":
        err(f'Root must have scheme="1.0", got scheme="{root.get("scheme")}"', errors)

    # project_title
    if root.find("project_title") is None or not (root.findtext("project_title") or "").strip():
        err("<project_title> is required and must be non empty", errors)

    # tags collection
    tag_names = set()
    tags_el = root.find("tags")
    if tags_el is not None:
        for tag in tags_el.findall("tag"):
            name = (tag.text or "").strip()
            if not name:
                err("<tag> must have a non empty name", errors)
            tag_names.add(name)
            color = tag.get("color")
            if color and not HEX_RE.match(color):
                err(f"tag color must be #RRGGBB hex, got {color}", errors)

    # tree
    tree_el = root.find("tree")
    if tree_el is None:
        err("<tree> is required", errors)
        return errors, warnings

    sections = tree_el.findall("section")
    if not sections:
        err("<tree> must contain at least one <section>", errors)

    # Walk every node
    for node in tree_el.iter("node"):
        title = node.findtext("node_title")
        if not title or not title.strip():
            err("<node_title> is required on every <node>", errors)

        # Color
        color = node.get("color")
        if color and not HEX_RE.match(color):
            err(f"node color must be #RRGGBB hex, got {color}", errors)

        # Tag attribute must reference defined tag names
        tag_attr = node.get("tag")
        if tag_attr:
            for t in [t.strip() for t in tag_attr.split(",")]:
                if t and t not in tag_names:
                    err(f'node tag "{t}" is not defined in <tags>', errors)

        # SEO
        seo = node.find("seo")
        if seo is not None:
            slug = seo.findtext("slug")
            if slug is not None:
                slug = slug.strip()
                if slug and not SLUG_RE.match(slug):
                    err(f"slug must start with / and be lowercase hyphenated, got {slug}", errors)
            intent = (seo.findtext("page_intent") or "").strip()
            if intent and intent not in PAGE_INTENTS:
                err(f"page_intent must be one of {sorted(PAGE_INTENTS)}, got {intent}", errors)

        # Blocks
        blocks = node.find("blocks")
        if blocks is not None:
            for block in blocks.findall("block"):
                btitle = (block.findtext("block_title") or "").strip()
                if not btitle:
                    warn(f'block under "{title}" has no <block_title>', warnings)
                wf = (block.findtext("wireframe") or "").strip()
                if wf:
                    for key in [k.strip() for k in wf.split(",")]:
                        if key and key not in WIREFRAME_KEYS:
                            err(f'unknown wireframe key "{key}" in block "{btitle}"', errors)
                bcolor = block.get("color")
                if bcolor and not HEX_RE.match(bcolor):
                    err(f"block color must be #RRGGBB hex, got {bcolor}", errors)

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: validate-octopus.py <file.xml>", file=sys.stderr)
        sys.exit(2)
    errors, warnings = validate(sys.argv[1])
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        print(f"FAILED with {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        sys.exit(1)
    print(f"OK with {len(warnings)} warning(s)")
    sys.exit(0)


if __name__ == "__main__":
    main()
