#!/usr/bin/env python3
"""Generate redirects_301.csv for the Cloudflare Worker KV store.

Uses the same redirect-resolution logic as generate_redirect_stubs.py but
writes a CSV instead of HTML stubs.  Self-redirects (source == destination)
are excluded — they cause infinite loops in the Worker.

The Worker appends a trailing slash to the request path before the KV lookup,
so a flat legacy page such as about.html is requested as /about.html and looked
up as /about.html/.  Every non-index .html path therefore gets two keys: the
literal one (/about.html/) and the directory form (/about/), the latter only
when it is not itself the live target.

    python3 generate_redirects_csv.py            # write redirects_301.csv
    python3 generate_redirects_csv.py --check    # dry-run, report only
"""

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translate_to_english import translate_chemical_name

MATS = {'acetal-pom', 'aluminium', 'ectfe-etfe', 'epdm', 'fep', 'hdpe', 'ldpe',
        'nbr', 'nylon-pa', 'petg', 'pmp', 'polycarbonate', 'polystyrene',
        'polysulfone', 'pp', 'ptfe', 'pvc-flexible', 'pvc-rigid', 'pvdf', 'san',
        'silicone', 'ss316', 'ss304', 'stainless-steel-304', 'viton'}

SLUG_ALIASES = {
    'gasoline': 'gasoline-petrol',
    'tetrahydrofuran-thf': 'thf',
    'ammonia': 'ammonium-hydroxide',
    'chlorine-bleach-solution': 'sodium-hypochlorite',
    'labarraque-solution-sodium-hypochlorite': 'sodium-hypochlorite',
    'formaldehyde-solution': 'formaldehyde',
    'n-heptane': 'heptane',
    'n-hexane': 'hexane',
    'sodium-hydroxide': 'sodium-hydroxide-caustic-soda',
}

# Legacy paths whose same-language counterpart is noindexed (FR) go to the English page instead.
OVERRIDES = {
    'fr.html': '/',
    'materials/fr/nbr.html': '/materials/nbr/',
}

MISC_TARGETS = {
    'index/index.html': '/',
    'ghs-symbols.html': '/sds-decoder/',
    'materials/ss304.html': '/materials/stainless-steel-304/',
    'charts/hdpe-compatibility-chart/index.html': '/materials/hdpe/',
    'charts/nbr-compatibility-chart/index.html': '/materials/nbr/',
    'charts/ptfe-compatibility-chart/index.html': '/materials/ptfe/',
    'charts/ss316-compatibility-chart/index.html': '/materials/ss316/',
}


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def is_stub(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return 'http-equiv="refresh"' in f.read(600)
    except OSError:
        return False


def is_live_page(path):
    return os.path.isfile(path) and not is_stub(path)


def build_chem_map():
    en_dirs = {d for d in os.listdir('chemicals')
               if is_live_page(os.path.join('chemicals', d, 'index.html'))}
    dehyphenated = {d.replace('-', ''): d for d in en_dirs}

    names = set()
    for src in ('data/chemicals_burkle_full.json', 'data/chemicals.json'):
        if os.path.exists(src):
            with open(src, encoding='utf-8') as f:
                names.update(c['name'] for c in json.load(f))

    chem_map = {}
    for name in sorted(names):
        de_slug = slugify(name)
        en_slug = slugify(translate_chemical_name(name))
        live = en_slug if en_slug in en_dirs else dehyphenated.get(en_slug.replace('-', ''))
        if live:
            chem_map.setdefault(de_slug, live)
    for old, new in SLUG_ALIASES.items():
        if new in en_dirs:
            chem_map[old] = new
    return en_dirs, chem_map


def classify(path):
    seg = path.split('/')
    if seg[0] == 'chemicals':
        if len(seg) == 2:
            return 'chem', seg[1][:-5], None
        if len(seg) == 3 and seg[2] == 'index.html':
            if seg[1] in MATS:
                return 'mat_index', None, seg[1]
            return 'chem', seg[1], None
        if len(seg) == 3:
            if seg[1] in MATS:
                return 'pair', seg[2][:-5], seg[1]
            return 'chem', seg[1], None
        if len(seg) == 4 and seg[2] in MATS and seg[3] == 'index.html':
            return 'pair', seg[1], seg[2]
        if len(seg) == 4 and seg[1] in MATS and seg[3] == 'index.html':
            return 'pair', seg[2], seg[1]
        return 'misc', None, None
    if seg[0] in MATS:
        if len(seg) == 2 and seg[1] == 'index.html':
            return 'mat_index', None, seg[0]
        if len(seg) == 2:
            return 'pair', seg[1][:-5], seg[0]
        if len(seg) == 3 and seg[2] == 'index.html':
            return 'pair', seg[1], seg[0]
    return 'misc', None, None


LANGS = ('de', 'es', 'fr', 'pt', 'zh')


def is_noindexed(target):
    f = target.lstrip('/') + 'index.html'
    try:
        with open(f, encoding='utf-8', errors='replace') as fh:
            head = fh.read(4000)
    except OSError:
        return False
    return bool(re.search(r'<meta name="(?:googlebot|robots)" content="[^"]*noindex', head))


def english_counterpart(target):
    """/materials/pt/nbr/ -> /materials/nbr/, /pt/ -> /, /pt/viscosity/ -> /viscosity/"""
    parts = ['about' if p in {f'{l}-about' for l in LANGS} else p
             for p in target.strip('/').split('/') if p not in LANGS]
    return '/' + '/'.join(parts) + '/' if parts else '/'


def resolve_target(path, en_dirs, chem_map):
    if path in OVERRIDES:
        return OVERRIDES[path]
    target = _resolve_target(path, en_dirs, chem_map)
    # a legacy language URL should not land on a noindexed page when an English one exists
    is_lang = any(f'/{l}/' in '/' + path or path in (f'{l}.html', f'{l}-about.html') for l in LANGS)
    if (target and is_noindexed(target) and is_lang
            and is_live_page(english_counterpart(target).lstrip('/') + 'index.html')):
        return english_counterpart(target)
    return target


def _resolve_target(path, en_dirs, chem_map):
    kind, chem, mat = classify(path)
    if chem:
        chem = chem if chem in en_dirs else chem_map.get(chem)
    if kind == 'pair':
        if chem and is_live_page(f'chemicals/{chem}/{mat}/index.html'):
            return f'/chemicals/{chem}/{mat}/'
        if mat and is_live_page(f'materials/{mat}/index.html'):
            return f'/materials/{mat}/'
        return '/chemicals/'
    if kind == 'chem':
        return f'/chemicals/{chem}/' if chem else '/chemicals/'
    if kind == 'mat_index':
        if mat and is_live_page(f'materials/{mat}/index.html'):
            return f'/materials/{mat}/'
        return '/chemicals/'
    base = path[:-5] if path.endswith('.html') else path
    base = base[:-6] if base.endswith('/index') else base
    if is_live_page(f'{base}/index.html'):
        return f'/{base}/'
    return MISC_TARGETS.get(path)


def html_kv_key(file_path):
    """KV key for the literal .html request (/about.html -> /about.html/), or
    None for index.html and non-HTML paths."""
    if file_path.endswith('.html') and not file_path.endswith('index.html'):
        return '/' + file_path + '/'
    return None


def path_to_kv_key(file_path):
    """Convert a file path to the KV lookup key (URL path with trailing slash)."""
    if file_path.endswith('index.html'):
        return '/' + file_path[:-len('index.html')]
    if file_path.endswith('.html'):
        return '/' + file_path[:-5] + '/'
    return '/' + file_path + '/'


def main():
    check = '--check' in sys.argv

    with open('data/legacy_urls.txt', encoding='utf-8') as f:
        legacy = [l.strip() for l in f if l.strip()]

    en_dirs, chem_map = build_chem_map()

    old_mat_chems = set()
    for path in legacy:
        seg = path.split('/')
        if seg[0] in MATS and len(seg) in (2, 3):
            chem = seg[1][:-5] if seg[1].endswith('.html') else seg[1]
            old_mat_chems.add(chem)
    extra = []
    for mat in MATS:
        for chem in old_mat_chems:
            extra.append(f'chemicals/{mat}/{chem}.html')
            extra.append(f'chemicals/{mat}/{chem}/index.html')
            extra.append(f'{mat}/{chem}.html')
            extra.append(f'{mat}/{chem}/index.html')

    redirects = {}
    skipped_live = 0
    skipped_self = 0
    unmapped = 0

    for path in legacy + extra:
        if os.path.isfile(path) and not is_stub(path):
            skipped_live += 1
            continue
        target = resolve_target(path, en_dirs, chem_map)
        if not target:
            unmapped += 1
            continue
        html_key = html_kv_key(path)
        if html_key:
            redirects[html_key] = target
        key = path_to_kv_key(path)
        if key == target:
            skipped_self += 1
            continue
        if is_live_page(key.lstrip('/') + 'index.html'):
            # /fr.html -> / must not also turn the live /fr/ page into a redirect
            skipped_live += 1
            continue
        redirects[key] = target

    print(f'Redirects:        {len(redirects)}')
    print(f'Skipped (live):   {skipped_live}')
    print(f'Skipped (self):   {skipped_self}')
    print(f'Unmapped:         {unmapped}')

    if not check:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'redirects_301.csv')
        with open(out, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['source_url', 'destination_url'])
            for key in sorted(redirects):
                w.writerow([key, redirects[key]])
        print(f'Wrote {out}')


if __name__ == '__main__':
    main()
