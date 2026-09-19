#!/usr/bin/env python3
"""
Replace German chemical names left in the pre-rendered (static) tables on the
English pages with their English equivalents.

Background
----------
The material pages ship a server-rendered copy of the full 1,651-row table
inside <tbody id="chemTable">. Once the page's JS fetches the dataset it
re-renders that tbody through translateName(), so visitors with JS enabled see
English. The static copy is what crawlers and no-JS clients see, and 346 of its
rows were baked with the raw German `name` instead of the translated one.

This script rewrites those rows into the same shape the JS produces:

    <div class="font-medium text-gray-900">English</div>
    <div class="text-xs text-gray-500">German</div>

and fixes the single German entry on the chemicals/ browse index.

Translations come from the existing js/chemical_translations_en.js map - the
same map the runtime uses - so the static HTML and the hydrated HTML agree.

Idempotent: rows that already carry a subtitle are not matched.
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
TRANSLATIONS_JS = ROOT / "js" / "chemical_translations_en.js"
BROWSE_INDEX = ROOT / "chemicals" / "index.html"
LOCALES = {"de", "es", "fr", "pt", "zh"}

# The one German entry on the browse index, and where it belongs once renamed.
BROWSE_GERMAN_NAME = "Abgase, Alkalisch"
BROWSE_ENGLISH_NAME = "Exhaust Gases, Alkaline"
BROWSE_TARGET_LETTER = "E"


def load_translations():
    """Parse the German -> English map out of chemical_translations_en.js."""
    src = TRANSLATIONS_JS.read_text(encoding="utf-8")
    body = src[src.index("{"): src.rindex("}") + 1]
    pairs = re.findall(r"'((?:[^'\\]|\\.)*)'\s*:\s*'((?:[^'\\]|\\.)*)'", body)
    if not pairs:
        sys.exit(f"no translations parsed from {TRANSLATIONS_JS}")
    return {k.replace("\\'", "'"): v.replace("\\'", "'") for k, v in pairs}


def english_material_pages():
    """materials/<slug>/index.html, excluding the localized sub-trees."""
    return sorted(
        p for p in ROOT.glob("materials/*/index.html")
        if p.parent.name not in LOCALES
    )


def esc(text):
    """Escape for use as HTML text content (quotes are not special here)."""
    return html.escape(text, quote=False)


# A name cell with no subtitle: the <div> is closed immediately by </td>.
# Rows that already carry a German subtitle therefore never match, which is
# what makes re-running this script a no-op.
NAME_CELL = re.compile(
    r'<div class="font-medium text-gray-900">([^<]+)</div></td>'
)


def patch_material_page(path, translations, stats):
    original = path.read_text(encoding="utf-8")

    tbody = re.search(
        r'(?s)(<tbody id="chemTable"[^>]*>)(.*?)(</tbody>)', original
    )
    if not tbody:
        stats["no_table"].append(path)
        return False

    open_tag, inner, close_tag = tbody.groups()

    def replace(match):
        raw = match.group(1)
        german = html.unescape(raw).strip()
        english = translations.get(german.lower())
        if not english or english == german:
            # Untranslatable, or identical in both languages (Butanol, Phenol).
            if not english:
                stats["untranslated"].add(german)
            return match.group(0)
        stats["rows"] += 1
        stats["names"].add(german)
        return (
            f'<div class="font-medium text-gray-900">{esc(english)}</div>'
            f'<div class="text-xs text-gray-500">{esc(german)}</div></td>'
        )

    new_inner = NAME_CELL.sub(replace, inner)
    if new_inner == inner:
        return False

    # Splice the tbody back in without disturbing the rest of the document.
    updated = original[:tbody.start()] + open_tag + new_inner + close_tag + original[tbody.end():]
    path.write_text(updated, encoding="utf-8")
    return True


def patch_browse_index(stats):
    """Rename the lone German entry and move it into the right letter section."""
    original = BROWSE_INDEX.read_text(encoding="utf-8")

    anchor = re.search(
        r'[ \t]*<a href="[^"]*" class="chem-link[^"]*" data-name="[^"]*">'
        + re.escape(BROWSE_GERMAN_NAME) + r'</a>\n?',
        original,
    )
    if not anchor:
        return False

    old = anchor.group(0)
    # Keep the href pointing at the existing stub: those slugs stay as they are.
    new = (old.replace(f'>{BROWSE_GERMAN_NAME}</a>', f'>{BROWSE_ENGLISH_NAME}</a>')
              .replace('data-name="abgase, alkalisch"',
                       f'data-name="{BROWSE_ENGLISH_NAME.lower()}"'))

    without = original[:anchor.start()] + original[anchor.end():]

    # Find the target letter section and append the entry after its last link,
    # which keeps the section alphabetically ordered.
    section = None
    for m in re.finditer(r'(?s)<div class="mb-8 letter-section">(.*?)</div>\s*</div>', without):
        letter = re.search(r'<h2[^>]*>([^<]+)</h2>', m.group(1))
        if letter and letter.group(1).strip() == BROWSE_TARGET_LETTER:
            section = m
            break
    if section is None:
        sys.exit(f'letter section "{BROWSE_TARGET_LETTER}" not found in {BROWSE_INDEX}')

    links = list(re.finditer(r'[ \t]*<a href="[^"]*" class="chem-link[^"]*"[^>]*>[^<]*</a>\n?',
                             without[section.start():section.end()]))
    insert_at = section.start() + links[-1].end()
    updated = without[:insert_at] + new + without[insert_at:]

    BROWSE_INDEX.write_text(updated, encoding="utf-8")
    stats["browse"] = f'{BROWSE_GERMAN_NAME} -> {BROWSE_ENGLISH_NAME} (moved to section {BROWSE_TARGET_LETTER})'
    return True


def main():
    translations = load_translations()
    print(f"translations loaded: {len(translations)}")

    stats = {"rows": 0, "names": set(), "untranslated": set(), "no_table": [], "browse": None}

    pages = english_material_pages()
    print(f"English material pages: {len(pages)}")
    changed = sum(patch_material_page(p, translations, stats) for p in pages)

    patch_browse_index(stats)

    print(f"\npages changed        : {changed}")
    print(f"rows rewritten       : {stats['rows']}")
    print(f"distinct names fixed : {len(stats['names'])}")
    if stats["browse"]:
        print(f"browse index         : {stats['browse']}")
    if stats["no_table"]:
        print(f"pages w/o chemTable  : {[str(p) for p in stats['no_table']]}")
    if stats["untranslated"]:
        print(f"\nNO TRANSLATION ({len(stats['untranslated'])}) - left untouched:")
        for n in sorted(stats["untranslated"]):
            print(f"   {n}")


if __name__ == "__main__":
    main()
