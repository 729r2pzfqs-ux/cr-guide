#!/usr/bin/env python3
"""Migrate all noindex tags from 'robots' to 'googlebot' for non-redirect pages.

    python3 migrate_noindex_to_googlebot.py            # rewrite
    python3 migrate_noindex_to_googlebot.py --check    # report only

Redirect stubs keep <meta name="robots" content="noindex,follow"> because they
should not be indexed by any engine. All other noindexed pages switch to
<meta name="googlebot" content="noindex"> so Bing, DuckDuckGo and Yahoo
continue to index them.

build_chemical_pages.py already emits the new tag for pages it generates.
This script catches the remaining pages not owned by that generator:
material pages (fr/pt/zh), about pages, chart pages, etc.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'data'}

OLD = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex[^"\']*["\'][^>]*/?>',
                 re.I)
NEW = '<meta name="googlebot" content="noindex">'


def main():
    check = '--check' in sys.argv
    changed = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(base, name)
            with open(path, encoding='utf-8', errors='replace') as f:
                page = f.read()
            # Skip redirect stubs — they should stay noindex for ALL engines
            if 'http-equiv="refresh"' in page[:600]:
                continue
            # Skip pages that already use googlebot noindex
            if '<meta name="googlebot" content="noindex">' in page:
                continue
            m = OLD.search(page)
            if not m:
                continue
            new = page[:m.start()] + NEW + page[m.end():]
            if new != page:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new)
    print('%s %d files' % ('would change' if check else 'changed', changed))


if __name__ == '__main__':
    main()
