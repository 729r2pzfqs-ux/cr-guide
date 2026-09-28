#!/usr/bin/env python3
"""Take French out of the index, the same way Portuguese and Chinese are.

    python3 noindex_french.py            # rewrite
    python3 noindex_french.py --check    # report only

  * every French page (fr/, materials/fr/, chemicals/fr/, fr-about/) gets
    <meta name="robots" content="noindex,follow">,
  * every hreflang="fr" declaration is removed, on every page of the site,
  * French is dropped from language menus.

The pages stay online. build_sitemap.py leaves noindex pages out by itself, so
run it afterwards. Idempotent.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'data'}
NOINDEX = '<meta name="robots" content="noindex,follow">'
ROBOTS = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*>', re.I)
HREFLANG_FR = re.compile(r'[ \t]*<link[^>]+hreflang=["\']fr["\'][^>]*>[ \t]*\n?', re.I)
OPTION_FR = re.compile(r'[ \t]*<option value="fr"(?! selected)[^>]*>[^<]*</option>[ \t]*\n?')


def is_french(rel):
    parts = rel.split(os.sep)
    return parts[0] in ('fr', 'fr-about') or parts[0] == 'fr.html' or parts[0] == 'fr-about.html' \
        or (len(parts) > 1 and parts[0] in ('materials', 'chemicals') and parts[1] == 'fr')


def main():
    check = '--check' in sys.argv
    noindexed = hreflang = menus = changed = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT)
            with open(path, encoding='utf-8', errors='replace') as f:
                page = f.read()
            if 'http-equiv="refresh"' in page[:600]:
                continue
            new, k = HREFLANG_FR.subn('', page)
            hreflang += k
            new, k = OPTION_FR.subn('', new)
            menus += k
            if is_french(rel):
                m = ROBOTS.search(new)
                if m is None:
                    new = re.sub(r'(<link[^>]+rel=["\']canonical["\'][^>]*>)', r'\1\n    ' + NOINDEX, new, count=1)
                    if NOINDEX not in new:
                        new = new.replace('</title>', '</title>\n    ' + NOINDEX, 1)
                    noindexed += 1
                elif 'noindex' not in m.group(0).lower():
                    new = new[:m.start()] + NOINDEX + new[m.end():]
                    noindexed += 1
            if new != page:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new)
    print('%s %d files: %d French pages set to noindex, %d hreflang="fr" tags and %d menu entries removed'
          % ('would change' if check else 'changed', changed, noindexed, hreflang, menus))


if __name__ == '__main__':
    main()
