#!/usr/bin/env python3
"""Write sitemap.xml from the pages that are actually meant to be indexed.

    python3 build_sitemap.py            # rewrite sitemap.xml
    python3 build_sitemap.py --check    # report only

A page is listed when it is a real page (not a redirect stub), carries no
noindex for robots or googlebot, and its canonical points at itself. That
makes the sitemap a consequence of the pages instead of a list kept by hand.
lastmod is kept for a URL whose file did not change in the working tree and
set to today for one that did.
"""

import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://chemicalresistance.org'
SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'data'}
SKIP_FILES = {'404.html'}


def url_of(rel):
    if rel.endswith('index.html'):
        rel = rel[:-len('index.html')]
    return SITE + '/' + rel


def priority(url):
    path = url[len(SITE):]
    depth = path.strip('/').count('/') + (1 if path.strip('/') else 0)
    if path == '/':
        return '1.0'
    if depth == 1:
        return '0.9'
    if '/chemicals/' in path or '/materials/' in path or '/charts/' in path or '/compare/' in path:
        return '0.8'
    return '0.6'


def main():
    check = '--check' in sys.argv
    today = datetime.date.today().isoformat()
    old = {}
    path = os.path.join(ROOT, 'sitemap.xml')
    if os.path.exists(path):
        for loc, mod in re.findall(r'<loc>(.*?)</loc><lastmod>(.*?)</lastmod>', open(path).read()):
            old[loc] = mod
    dirty = set()
    try:
        out = subprocess.run(['git', '-c', 'core.quotepath=off', 'status', '--porcelain'], cwd=ROOT,
                             capture_output=True, text=True).stdout
        dirty = {l[3:].strip().strip('"') for l in out.splitlines()}
    except OSError:
        pass

    urls = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.html') or name in SKIP_FILES:
                continue
            rel = os.path.relpath(os.path.join(base, name), ROOT)
            with open(os.path.join(base, name), encoding='utf-8', errors='replace') as f:
                head = f.read(12000)
            if 'http-equiv="refresh"' in head:
                continue
            if re.search(r'<meta[^>]+name=["\'](?:robots|googlebot)["\'][^>]*content=["\'][^"\']*noindex', head, re.I):
                continue
            url = url_of(rel)
            m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', head, re.I)
            if m and m.group(1) != url:
                continue
            mod = today if (rel in dirty or url not in old) else old[url]
            urls.append((url, mod))
    urls.sort()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, mod in urls:
        lines.append('<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>'
                     % (url, mod, priority(url)))
    lines.append('</urlset>')
    print('%d URLs (was %d)' % (len(urls), len(old)))
    if not check:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
