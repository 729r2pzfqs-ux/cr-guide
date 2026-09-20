#!/usr/bin/env python3
"""
Rewrite the analytics head of every published page into the canonical
Consent Mode v2 order defined in analytics_head.py:

    1. consent defaults  (denied baseline + wait_for_update)
    2. AdSense loader    (adsbygoogle.js delivers the CMP at runtime)
    3. gtag loader + gtag('js')/gtag('config')
    4. Ahrefs

The published HTML predates the generators being fixed, and the tags sit in
several different orders across the tree, so rather than patching them in
place this collects the whole run of Google/Ahrefs script tags (plus the
comments that annotate them), drops it, and re-emits the canonical block at the
position where the run started.

Pages keep whatever tags they already had: a page with no Ahrefs tag does not
gain one, and privacy/terms (AdSense but no GA property) get the consent
defaults without a gtag loader. Pages with no Google tags at all are untouched.

Idempotent - a page already in canonical order is left byte-identical.

    python3 fix_consent_order.py --check    # report only
    python3 fix_consent_order.py            # rewrite
"""

import os
import re
import sys
from collections import Counter
from pathlib import Path

import analytics_head

ROOT = Path(__file__).parent
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "data"}

GA_ID = analytics_head.GA_ID
ADS_CLIENT = analytics_head.ADS_CLIENT

TAG_PATTERNS = {
    "ads": r'<script[^>]*\bsrc="https://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client='
           + re.escape(ADS_CLIENT) + r'"[^>]*></script>',
    "gtag": r'<script[^>]*\bsrc="https://www\.googletagmanager\.com/gtag/js\?id='
            + re.escape(GA_ID) + r'"[^>]*></script>',
    "ahrefs": r'<script[^>]*\bsrc="https://analytics\.ahrefs\.com/analytics\.js"[^>]*></script>',
    # inline bootstrap: declares dataLayer/gtag, optionally sets consent, and
    # (in the current published pages) also calls gtag js/config
    "inline": r'<script>\s*window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];'
              r'(?:(?!</script>).)*?</script>',
    "adcollapse_style": r'<style>ins\.adsbygoogle\[data-ad-status="unfilled"\](?:(?!</style>).)*</style>',
    "adcollapse_script": r'<script>\(function\(\)\{{1,2}var S="data-blank-ad"(?:(?!</script>).)*</script>',
    # the standalone config script this tool emits, so re-runs are no-ops
    "config": r'<script>\s*gtag\(\s*[\'"]js[\'"]\s*,\s*new Date\(\)\s*\)\s*;\s*'
              r'gtag\(\s*[\'"]config[\'"]\s*,\s*[\'"]' + re.escape(GA_ID)
              + r'[\'"]\s*\)\s*;\s*</script>',
}
# comments that annotate the analytics block and travel with it
COMMENT = (r'<!--(?:(?!-->).)*?'
           r'(?:AdSense|Google Analytics|Consent Mode|consent|gtag|Ahrefs|adsbygoogle)'
           r'(?:(?!-->).)*?-->')

TAG_ALT = "|".join(f"(?:{p})" for p in TAG_PATTERNS.values())
ANY_TAG = re.compile("|".join(f"(?P<{k}>{v})" for k, v in TAG_PATTERNS.items()), re.S)
# a run of tags/comments, starting and ending on a real tag
CLUSTER = re.compile(
    rf'(?:(?:{COMMENT})[ \t\r\n]*)*(?:{TAG_ALT})'
    rf'(?:[ \t\r\n]*(?:(?:{COMMENT})[ \t\r\n]*)*(?:{TAG_ALT}))*',
    re.S,
)


def line_indent(text, pos):
    """Indentation of the line `pos` sits on, if the tag starts that line."""
    bol = text.rfind("\n", 0, pos) + 1
    prefix = text[bol:pos]
    return prefix if prefix.strip() == "" else None


def rebuild(text):
    """Return (new_text, kinds) or (text, None) when there is nothing to do."""
    m = CLUSTER.search(text)
    if not m:
        return text, None
    cluster = m.group(0)
    kinds = {mm.lastgroup for mm in ANY_TAG.finditer(cluster)}

    has_gtag = bool({"gtag", "config"} & kinds) or (
        "inline" in kinds and re.search(r'gtag\(\s*[\'"]config[\'"]', cluster)
    )
    has_ahrefs = "ahrefs" in kinds

    indent = line_indent(text, m.start())
    pretty = "\n" in cluster and re.search(r'<script>\s*\n', cluster)

    if pretty and has_gtag and has_ahrefs:
        block = analytics_head.PRETTY
    else:
        block = analytics_head.block(indent=indent or "", ahrefs=has_ahrefs, gtag=has_gtag)
        if indent:
            block = block[len(indent):]  # the existing indent is already in `text`

    start, end = m.start(), m.end()
    if indent is not None and not pretty:
        pass  # keep the existing leading indent, block lines carry their own
    if pretty:
        # PRETTY carries its own 4-space indent, so consume the leading one
        start = text.rfind("\n", 0, m.start()) + 1

    new = text[:start] + block + text[end:]
    return new, kinds


def html_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".html"):
                yield Path(root) / f


def main():
    check = "--check" in sys.argv
    stats = Counter()
    samples = []
    for path in html_files():
        text = path.read_text(encoding="utf-8", errors="surrogateescape")
        new, kinds = rebuild(text)
        if kinds is None:
            stats["no_tags"] += 1
            continue
        if new == text:
            stats["already_canonical"] += 1
            continue
        stats["rewritten"] += 1
        if len(samples) < 5:
            samples.append(str(path.relative_to(ROOT)))
        if not check:
            path.write_text(new, encoding="utf-8", errors="surrogateescape")

    for k, v in sorted(stats.items()):
        print(f"{k:20s} {v}")
    print("samples:", samples)


if __name__ == "__main__":
    main()
