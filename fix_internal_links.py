#!/usr/bin/env python3
"""Point internal links straight at the page they end up on.

    python3 fix_internal_links.py            # rewrite
    python3 fix_internal_links.py --check    # report only

Two kinds of link cost a hop on every click and every crawl:

  * links to a redirect stub (for example the /de/about/ link in every German
    header, which is a stub for /de-about/) are rewritten to the stub's target,
  * links to a directory without the trailing slash (/materials/pp), which
    GitHub Pages answers with a 301, get the slash.

Links that resolve to nothing are reported and left alone. Idempotent.
"""

import os
import posixpath
import re
import sys
from collections import Counter
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_HOSTS = {'chemicalresistance.org', 'www.chemicalresistance.org'}
SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'data'}
REFRESH = re.compile(r'http-equiv="refresh"\s+content="0;\s*url=([^"]+)"', re.I)
HREF = re.compile(r'(<a\s[^>]*?href=)(["\'])([^"\']+)\2')

_stub_cache = {}


def stub_target(rel):
    """Site path a stub file redirects to, or None when rel is a real page."""
    if rel not in _stub_cache:
        with open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace') as f:
            m = REFRESH.search(f.read(3000))
        _stub_cache[rel] = urlparse(m.group(1)).path if m else None
    return _stub_cache[rel]


def lookup(path):
    """(file, needs_slash) for a site path, or (None, False)."""
    rel = path.lstrip('/')
    if rel == '' or rel.endswith('/'):
        f = rel + 'index.html'
        return (f, False) if os.path.isfile(os.path.join(ROOT, f)) else (None, False)
    if os.path.isfile(os.path.join(ROOT, rel)):
        return rel, False
    if os.path.isfile(os.path.join(ROOT, rel + '.html')):
        return rel + '.html', False
    if os.path.isfile(os.path.join(ROOT, rel, 'index.html')):
        return rel + '/index.html', True
    return None, False


def fix_page(rel, page, stats, broken):
    def repl(m):
        href = m.group(3)
        if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')) or '${' in href:
            return m.group(0)
        u = urlparse(href)
        if u.scheme and u.scheme not in ('http', 'https'):
            return m.group(0)
        if u.netloc and u.netloc not in SITE_HOSTS:
            return m.group(0)
        path = u.path
        if not path:
            return m.group(0)
        if not path.startswith('/'):
            path = posixpath.join('/' + posixpath.dirname(rel), path)
        keep_slash = path.endswith('/')
        path = posixpath.normpath(unquote(path))
        if keep_slash and path != '/':
            path += '/'
        f, needs_slash = lookup(path)
        if f is None:
            broken[href] += 1
            return m.group(0)
        new = None
        target = stub_target(f) if f.endswith('.html') else None
        hops = 0
        while target and hops < 5:
            new = target
            f2, _ = lookup(target)
            target = stub_target(f2) if f2 else None
            hops += 1
        if new:
            stats['stub'] += 1
        elif needs_slash:
            new = path + '/'
            stats['slash'] += 1
        if not new:
            return m.group(0)
        tail = ('?' + u.query if u.query else '') + ('#' + u.fragment if u.fragment else '')
        return '%s%s%s%s%s' % (m.group(1), m.group(2), new, tail, m.group(2))

    return HREF.sub(repl, page)


def main():
    check = '--check' in sys.argv
    stats, broken = Counter(), Counter()
    changed = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ROOT)
            with open(path, encoding='utf-8', errors='replace') as f:
                page = f.read()
            if REFRESH.search(page[:3000]):
                continue
            new = fix_page(rel, page, stats, broken)
            if new != page:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new)
    print('%s %d pages: %d links to redirect stubs, %d links missing a trailing slash'
          % ('would change' if check else 'changed', changed, stats['stub'], stats['slash']))
    if broken:
        print('%d distinct links resolve to nothing:' % len(broken))
        for href, n in broken.most_common(20):
            print('  %5d  %s' % (n, href))


if __name__ == '__main__':
    main()
