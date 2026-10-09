#!/usr/bin/env python3
"""Submit changed URLs to IndexNow after a build.

    python3 ping_indexnow.py            # ping URLs whose lastmod is today
    python3 ping_indexnow.py --all      # ping every URL in the sitemap
    python3 ping_indexnow.py --check    # dry-run: list what would be pinged

Reads sitemap.xml (which already excludes noindexed, redirected, and
non-canonical pages) so the ping list is always a subset of the sitemap.
Run this AFTER build_sitemap.py.
"""

import json
import os
import re
import sys
import datetime
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SITEMAP = os.path.join(ROOT, 'sitemap.xml')
HOST = 'chemicalresistance.org'
KEY = '57631e97151c4808b331f2bfec082149'
ENDPOINT = 'https://api.indexnow.org/indexnow'
BATCH_SIZE = 10000


def urls_from_sitemap(only_today=True):
    with open(SITEMAP, encoding='utf-8') as f:
        xml = f.read()
    today = datetime.date.today().isoformat()
    urls = []
    for loc, mod in re.findall(r'<loc>(.*?)</loc><lastmod>(.*?)</lastmod>', xml):
        if only_today and mod != today:
            continue
        urls.append(loc)
    return urls


def submit(urls):
    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i + BATCH_SIZE]
        payload = json.dumps({
            'host': HOST,
            'key': KEY,
            'keyLocation': 'https://%s/%s.txt' % (HOST, KEY),
            'urlList': batch,
        }).encode()
        req = urllib.request.Request(
            ENDPOINT,
            data=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'},
            method='POST',
        )
        resp = urllib.request.urlopen(req)
        status = resp.getcode()
        if status == 200:
            print('  batch %d–%d: OK' % (i + 1, i + len(batch)))
        else:
            print('  batch %d–%d: HTTP %d' % (i + 1, i + len(batch), status))


def main():
    check = '--check' in sys.argv
    send_all = '--all' in sys.argv

    if not os.path.exists(SITEMAP):
        sys.exit('sitemap.xml not found — run build_sitemap.py first')

    urls = urls_from_sitemap(only_today=not send_all)
    print('%d URLs to ping%s' % (len(urls), ' (dry run)' if check else ''))
    if not urls:
        return
    if check:
        for u in urls[:20]:
            print('  ' + u)
        if len(urls) > 20:
            print('  ... and %d more' % (len(urls) - 20))
        return
    submit(urls)
    print('Done — pinged %d URLs via IndexNow' % len(urls))


if __name__ == '__main__':
    main()
