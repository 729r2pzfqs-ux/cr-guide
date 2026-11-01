#!/usr/bin/env python3
"""Write the descriptions of pages no generator owns.

    python3 apply_meta_descriptions.py            # rewrite
    python3 apply_meta_descriptions.py --check    # report only

data/meta_descriptions.json maps a page to its description. The page keeps its
own markup; the description, og:description, twitter:description and the
matching JSON-LD text are replaced. Idempotent. Run before build_chart_tables.py,
which copies the description into the chart pages' structured data.
"""

import html
import json
import os
import re
import sys

from meta_text import MAX_LEN, MIN_LEN

ROOT = os.path.dirname(os.path.abspath(__file__))
DESC = re.compile(r'(<meta name="description" content=")([^"]*)(")')
SOCIAL = re.compile(r'(<meta (?:property="og:description"|name="twitter:description") content=")[^"]*(")')


def attr(text):
    return text.replace('&', '&amp;').replace('"', '&quot;')


def jsonld(text):
    return json.dumps(text, ensure_ascii=False)[1:-1]


def apply(page, text):
    m = DESC.search(page)
    if not m:
        return re.sub(r'(<title>.*?</title>)', lambda t: '%s\n    <meta name="description" content="%s">'
                      % (t.group(1), attr(text)), page, count=1)
    old = html.unescape(m.group(2))
    if old != text:
        page = page.replace('"description":"%s"' % jsonld(old), '"description":"%s"' % jsonld(text))
        page = page.replace('"description": "%s"' % jsonld(old), '"description": "%s"' % jsonld(text))
    page = DESC.sub(lambda x: x.group(1) + attr(text) + x.group(3), page, count=1)
    return SOCIAL.sub(lambda x: x.group(1) + attr(text) + x.group(2), page)


def main():
    check = '--check' in sys.argv
    with open(os.path.join(ROOT, 'data', 'meta_descriptions.json'), encoding='utf-8') as f:
        pages = json.load(f)
    changed = 0
    for rel, text in pages.items():
        if not MIN_LEN <= len(text) <= MAX_LEN:
            sys.exit('%s: description has %d characters, needs %d-%d' % (rel, len(text), MIN_LEN, MAX_LEN))
        with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
            page = f.read()
        new = apply(page, text)
        if new != page:
            changed += 1
            if not check:
                with open(os.path.join(ROOT, rel), 'w', encoding='utf-8') as f:
                    f.write(new)
    print('%d pages listed; %s %d' % (len(pages), 'would change' if check else 'changed', changed))


if __name__ == '__main__':
    main()
