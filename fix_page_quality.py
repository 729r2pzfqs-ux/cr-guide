#!/usr/bin/env python3
"""Structured data and badge contrast on the pages that are patched, not generated.

    python3 fix_page_quality.py            # rewrite
    python3 fix_page_quality.py --check    # report only

  * Rating badges get the colours the generated pages and the diagrams use.
    White on the old light green, amber and red failed WCAG contrast, and the
    old amber and red were hard to tell apart for colour-blind readers.
  * FAQPage markup is removed. The questions stay on the page; the markup no
    longer earns a rich result and was on every page type.
  * Pages without a BreadcrumbList get one, built from their URL and <h1>.
  * Material pages get Dataset markup that names Bürkle as the source.
  * dateModified in existing markup of material and chart pages is set to the
    date their content last changed.

Pages written by build_chemical_pages.py and build_compare_pages.py carry
their own markup and are left alone. Idempotent.
"""

import html
import json
import os
import re
import sys

import resistance_data as rd
from page_i18n import material_name

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://chemicalresistance.org'
SKIP_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'data'}
LANGS = ('de', 'es', 'fr', 'pt', 'zh')
CONTENT_UPDATED = '2026-09-29'

BADGE = {
    'A': 'background:#15803d;color:#fff', 'B': 'background:#1d4ed8;color:#fff',
    'C': 'background:#d97706;color:#111827', 'D': 'background:#b91c1c;color:#fff',
    'NR': 'background:#e5e7eb;color:#374151',
}
TAILWIND_FIX = ('<style id="cr-badge-contrast">.bg-emerald-500.text-white,.bg-green-500.text-white'
                '{background-color:#15803d!important}.bg-blue-500.text-white{background-color:#1d4ed8!important}'
                '.bg-amber-500.text-white{background-color:#d97706!important;color:#111827!important}'
                '.bg-red-500.text-white{background-color:#b91c1c!important}</style>')
TAILWIND_BADGE = re.compile(r'bg-(?:emerald|green|blue|amber|red)-500 text-white')

WORDS = {
    'home': {'en': 'Home', 'de': 'Startseite', 'es': 'Inicio', 'fr': 'Accueil', 'pt': 'Início', 'zh': '首页'},
    'materials': {'en': 'Materials', 'de': 'Materialien', 'es': 'Materiales', 'fr': 'Matériaux',
                  'pt': 'Materiais', 'zh': '材料'},
    'charts': {'en': 'Charts', 'de': 'Tabellen', 'es': 'Tablas', 'fr': 'Tableaux', 'pt': 'Gráficos',
               'zh': '图表'},
    'compare': {'en': 'Compare', 'de': 'Vergleich', 'es': 'Comparar', 'fr': 'Comparer', 'pt': 'Comparar',
                'zh': '比较'},
    'chemicals': {'en': 'Chemicals', 'de': 'Chemikalien', 'es': 'Productos químicos',
                  'fr': 'Produits chimiques', 'pt': 'Produtos químicos', 'zh': '化学品'},
}
DATASET = {
    'en': ('{m} chemical resistance ratings',
           'Chemical resistance ratings of {m} ({full}) against {n} chemicals at 20 °C and 50 °C, by concentration. Ratings A to D, from the chemical resistance list of Bürkle GmbH.'),
    'de': ('Chemische Beständigkeit von {m}',
           'Beständigkeitsbewertungen von {m} gegenüber {n} Chemikalien bei 20 °C und 50 °C, nach Konzentration. Bewertungen A bis D aus der Beständigkeitsliste der Bürkle GmbH.'),
    'es': ('Resistencia química de {m}',
           'Clasificaciones de resistencia química de {m} frente a {n} productos químicos a 20 °C y 50 °C, por concentración. Clasificaciones de A a D, de la lista de resistencia química de Bürkle GmbH.'),
}


def structure(rel):
    """(lang, section, is_index) of a page path, or None for a page this
    script does not describe."""
    parts = rel.split('/')
    if parts[-1] != 'index.html':
        return None
    parts = parts[:-1]
    lang = 'en'
    if parts and parts[0] in LANGS:
        lang, parts = parts[0], parts[1:]
    elif len(parts) > 1 and parts[0] in ('materials', 'chemicals') and parts[1] in LANGS:
        lang, parts = parts[1], [parts[0]] + parts[2:]
    elif parts and parts[0].endswith('-about'):
        lang, parts = parts[0][:2], ['about']
    return lang, parts


def section_url(lang, section):
    if section in ('materials', 'chemicals'):
        return '/%s/' % section if lang == 'en' else '/%s/%s/' % (section, lang)
    return '/%s/' % section if lang == 'en' else '/%s/%s/' % (lang, section)


def ld(obj, ident):
    return '<script type="application/ld+json" id="%s">%s</script>' % (
        ident, json.dumps(obj, ensure_ascii=False, separators=(',', ':')))


def fix(rel, page, counts, rated):
    orig = page

    # badges
    page = re.sub(r'\.rating-(A|B|C|D|NR)\s*\{[^}]*\}',
                  lambda m: '.rating-%s{%s}' % (m.group(1), BADGE[m.group(1)]), page)
    if TAILWIND_BADGE.search(page) and 'id="cr-badge-contrast"' not in page:
        page = page.replace('</head>', TAILWIND_FIX + '\n</head>', 1)

    # FAQPage markup
    def drop_faq(m):
        return '' if re.search(r'"@type"\s*:\s*"FAQPage"', m.group(0)) else m.group(0)
    page = re.sub(r'[ \t]*<script type="application/ld\+json"[^>]*>[\s\S]*?</script>[ \t]*\n?', drop_faq, page)

    st = structure(rel)
    generated = 'class="cr-card' in page
    if st and not generated:
        lang, parts = st
        url = SITE + '/' + rel[:-len('index.html')]
        h1 = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', page)
        name = html.unescape(re.sub(r'<[^>]+>', ' ', h1.group(1))) if h1 else ''
        name = ' '.join(name.split())

        page = re.sub(r'[ \t]*<script type="application/ld\+json" id="cr-(?:breadcrumb|dataset)">[\s\S]*?</script>\n?',
                      '', page)
        extra = []
        if parts and name and 'BreadcrumbList' not in page:
            items = [(WORDS['home'][lang], '/' if lang == 'en' else '/%s/' % lang)]
            if len(parts) > 1 and parts[0] in WORDS:
                items.append((WORDS[parts[0]][lang], section_url(lang, parts[0])))
            items.append((name, url[len(SITE):]))
            extra.append(ld({'@context': 'https://schema.org', '@type': 'BreadcrumbList',
                             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n,
                                                  'item': SITE + u} for i, (n, u) in enumerate(items)]},
                            'cr-breadcrumb'))
        if len(parts) == 2 and parts[0] == 'materials' and parts[1] in rd.SLUG_TO_CODE and lang in DATASET:
            code = rd.SLUG_TO_CODE[parts[1]]
            from page_i18n import material_full
            m = material_name(code, lang)
            title, desc = DATASET[lang]
            extra.append(ld({
                '@context': 'https://schema.org', '@type': 'Dataset',
                'name': title.format(m=m), 'url': url, 'inLanguage': lang,
                'description': desc.format(m=m, full=material_full(code, lang), n=rated[code]),
                'dateModified': CONTENT_UPDATED,
                'variableMeasured': ['Resistance rating at 20 °C', 'Resistance rating at 50 °C'],
                'creator': {'@type': 'Organization', 'name': 'ChemicalResistance.org', 'url': SITE + '/'},
                'isBasedOn': {'@type': 'CreativeWork', 'name': 'Beständigkeitsliste (chemical resistance list)',
                              'publisher': {'@type': 'Organization', 'name': 'Bürkle GmbH',
                                            'url': 'https://www.buerkle.de'}},
            }, 'cr-dataset'))
        if extra:
            page = page.replace('</head>', '\n'.join(extra) + '\n</head>', 1)
        if parts and parts[0] in ('materials', 'charts'):
            page = re.sub(r'("dateModified"\s*:\s*")\d{4}-\d{2}-\d{2}(?=")', r'\g<1>' + CONTENT_UPDATED, page)

    if page != orig:
        counts['pages'] += 1
    return page


def main():
    check = '--check' in sys.argv
    chems, _ = rd.load()
    rated = {code: sum(1 for c in chems.values() if any(code in v['ratings'] for v in c['variants']))
             for code in rd.MATERIALS}
    counts = {'pages': 0}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.html'):
                continue
            path = os.path.join(base, name)
            with open(path, encoding='utf-8', errors='replace') as f:
                page = f.read()
            if 'http-equiv="refresh"' in page[:600]:
                continue
            new = fix(os.path.relpath(path, ROOT), page, counts, rated)
            if new != page and not check:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
    print('%s %d pages' % ('would change' if check else 'changed', counts['pages']))


if __name__ == '__main__':
    main()
