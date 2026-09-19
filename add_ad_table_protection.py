#!/usr/bin/env python3
"""
Protect the compatibility tables from Google Auto Ads insertion.

Auto ads will drop a placement between two rows of a data table, splitting the
core content. index.html already carries the fix; this applies the same one to
the other page types that render a compatibility table:

  * materials/<slug>/index.html   (24 pages, 1,651-row table, <tbody id="chemTable">)
  * chemicals/<chem>/<mat>/index.html (4,518 pair pages, "Comparison Table")

Each page gets the table's scroll wrapper tagged id="compat-table-zone", plus a
rule in its existing <style> block that hides anything auto ads places inside
that zone.

The chemicals/<chem>/index.html detail pages are deliberately skipped: they are
material link grids with no table at all.

Idempotent - a page that already has compat-table-zone is left alone.
"""

import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
LOCALES = {"de", "es", "fr", "pt", "zh"}

# --- material pages -------------------------------------------------------
MAT_ANCHOR = (
    '<div class="overflow-x-auto">\n'
    '                    <table class="w-full min-w-[600px]">'
)
MAT_REPLACEMENT = (
    '<div id="compat-table-zone" class="overflow-x-auto">\n'
    '                    <table class="w-full min-w-[600px]">'
)
MAT_CSS = """
        /* Keep Google Auto Ads out of the compatibility table: auto ads will
           otherwise drop a placement between two material rows. */
        #compat-table-zone .google-auto-placed,
        #compat-table-zone ins.adsbygoogle,
        #chemTable .google-auto-placed,
        #chemTable ins.adsbygoogle { display: none !important; }
    </style>"""

# --- chemical x material pair pages --------------------------------------
# These ship a minified single-line <style>, and their table has no tbody id,
# so the zone selector alone carries the rule.
PAIR_ANCHOR = (
    '<div style="overflow-x:auto">\n'
    '            <table style="width:100%;border-collapse:collapse;font-size:0.9rem">'
)
PAIR_REPLACEMENT = (
    '<div id="compat-table-zone" style="overflow-x:auto">\n'
    '            <table style="width:100%;border-collapse:collapse;font-size:0.9rem">'
)
PAIR_CSS = (
    "#compat-table-zone .google-auto-placed,"
    "#compat-table-zone ins.adsbygoogle{display:none!important}</style>"
)

MARKER = "compat-table-zone"


def material_pages():
    return sorted(
        p for p in ROOT.glob("materials/*/index.html")
        if p.parent.name not in LOCALES
    )


def pair_pages():
    """chemicals/<chem>/<material>/index.html, excluding localized subtrees."""
    out = []
    for p in ROOT.glob("chemicals/*/*/index.html"):
        if any(part in LOCALES for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def patch(path, anchor, replacement, css_with_close_tag, stats):
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        stats["already"] += 1
        return False
    if "<table" not in text:
        stats["no_table"] += 1
        return False
    if text.count(anchor) != 1:
        stats["anchor_miss"].append(str(path.relative_to(ROOT)))
        return False
    if text.count("</style>") != 1:
        stats["style_miss"].append(str(path.relative_to(ROOT)))
        return False

    text = text.replace(anchor, replacement, 1)
    text = text.replace("</style>", css_with_close_tag, 1)
    path.write_text(text, encoding="utf-8")
    stats["patched"] += 1
    return True


def run(label, pages, anchor, replacement, css):
    stats = {"patched": 0, "already": 0, "no_table": 0, "anchor_miss": [], "style_miss": []}
    for p in pages:
        patch(p, anchor, replacement, css, stats)
    print(f"\n{label}: {len(pages)} candidate pages")
    print(f"  patched            : {stats['patched']}")
    print(f"  already protected  : {stats['already']}")
    print(f"  skipped (no table) : {stats['no_table']}")
    for key, name in (("anchor_miss", "table wrapper not found"),
                      ("style_miss", "no single <style> block")):
        if stats[key]:
            print(f"  SKIPPED - {name}: {len(stats[key])}")
            for s in stats[key][:5]:
                print(f"      {s}")
    return stats


def main():
    m = run("material pages", material_pages(), MAT_ANCHOR, MAT_REPLACEMENT, MAT_CSS)
    p = run("chemical x material pair pages", pair_pages(), PAIR_ANCHOR, PAIR_REPLACEMENT, PAIR_CSS)
    print(f"\ntotal pages patched: {m['patched'] + p['patched']}")


if __name__ == "__main__":
    main()
