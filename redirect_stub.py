#!/usr/bin/env python3
"""The one redirect stub used for every moved or retired URL.

GitHub Pages cannot send a 301, so a moved page is a meta-refresh document.
A stub has no content, so it carries no ad or analytics tags: an ad script on
an empty page is against AdSense policy, and an analytics tag would count the
redirect and then the landing page as two page views.

    python3 redirect_stub.py            # rewrite every existing stub to this form
    python3 redirect_stub.py --check    # report only
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://chemicalresistance.org'
SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'data'}

_REFRESH = re.compile(r'http-equiv="refresh"\s+content="0;\s*url=([^"]+)"', re.I)


def stub(target):
    """target is a site path such as /chemicals/acetone/ or an absolute URL."""
    url = target if target.startswith('http') else SITE + target
    return ('<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><title>ChemicalResistance.org</title>\n'
            '<meta http-equiv="refresh" content="0;url=%s"><link rel="canonical" href="%s">\n'
            '<meta name="robots" content="noindex,follow"></head>\n'
            '<body><p><a href="%s">%s</a></p></body></html>\n') % (url, url, url, url)


def main():
    check = '--check' in sys.argv
    seen = changed = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(base, name)
            with open(path, encoding='utf-8', errors='replace') as f:
                page = f.read()
            m = _REFRESH.search(page[:6000])
            if not m:
                continue
            seen += 1
            new = stub(m.group(1))
            if new != page:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new)
    print('%d redirect stubs, %s %d' % (seen, 'would rewrite' if check else 'rewrote', changed))


if __name__ == '__main__':
    main()
