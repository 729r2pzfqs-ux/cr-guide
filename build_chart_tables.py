#!/usr/bin/env python3
"""Give the chart and comparison pages a table in their HTML.

    python3 build_chart_tables.py            # rewrite
    python3 build_chart_tables.py --check    # report only

charts/<group>/ and compare/<a>-vs-<b>/ (and their localized copies) drew their
table in the browser from the full data set; the HTML itself said "Showing 0
chemicals" above an empty table. This writes the first screen of rows into the
page, in the same order the script would show them, and the real total. The
script still takes over for filtering and "load more".

It also makes those scripts skip synonym rows (alias_of), so a chemical that
the source lists under three names is not shown three times. Idempotent.
"""

import html
import os
import re
import sys

import class_stats as cs
import diagrams
import resistance_data as rd
from build_material_tables import FIG_STYLE
from page_i18n import material_name, t
from build_material_tables import load_translations

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ['en', 'de', 'es', 'fr', 'pt', 'zh']
CHART_ROWS = 80
COMPARE_ROWS = 30
ALIAS_FILTER = 'data = data.filter(function (c) { return !c.alias_of; });'


def esc(s):
    return html.escape(str(s), quote=True)


def grade(v, m):
    r = v['ratings'].get(m)
    if r is None or not r.get('w20'):
        return 'NR'
    return r['w20']


def display(chem, lang, trans):
    if lang == 'de':
        return chem['name_de']
    if lang == 'en':
        return chem['name_en']
    return trans.get(chem['name_de'].lower(), chem['name_en'])


def span(g, cls):
    return '<span class="rating-%s %s rounded text-xs font-bold">%s</span>' % (g, cls, g)


def chart_rows(mats, lang, chems, trans):
    rows = []
    for chem in chems.values():
        for v in chem['variants']:
            gs = [grade(v, m) for m in mats]
            if sum(1 for g in gs if g != 'NR') < 2:
                continue
            differ = len({g for g in gs if g != 'NR'}) > 1
            rows.append((0 if differ else 1, chem['name_en'].lower(), chem, v, gs))
    rows.sort(key=lambda r: (r[0], r[1]))
    out = []
    for _, _, chem, v, gs in rows[:CHART_ROWS]:
        name = display(chem, lang, trans)
        sub = ('<div class="text-xs text-gray-400">%s</div>' % esc(chem['name_de'])
               if name != chem['name_de'] else '')
        cells = ''.join('<td class="py-2 px-2 text-center">%s</td>' % span(g, 'px-1.5 py-0.5') for g in gs)
        out.append('<tr class="hover:bg-gray-50"><td class="py-2 px-4 text-sm sticky left-0 z-10 bg-white">'
                   '<div class="font-medium text-gray-900">%s</div>%s</td>'
                   '<td class="py-2 px-3 text-xs text-gray-500">%s</td>%s</tr>'
                   % (esc(name), sub, esc(v['conc']) or '&mdash;', cells))
    return out, len(rows)


def compare_rows(a, b, lang, chems, trans):
    rows = []
    for chem in chems.values():
        for v in chem['variants']:
            ga, gb = grade(v, a), grade(v, b)
            if 'NR' in (ga, gb) or ga == gb:
                continue
            rows.append((-abs(rd.GRADE_RANK[ga] - rd.GRADE_RANK[gb]), chem['name_en'].lower(), chem, v, ga, gb))
    rows.sort(key=lambda r: (r[0], r[1]))
    out = []
    for _, _, chem, v, ga, gb in rows[:COMPARE_ROWS]:
        name = display(chem, lang, trans)
        if v['conc']:
            name = '%s (%s)' % (name, v['conc'])
        out.append('<tr class="hover:bg-gray-50"><td class="py-3 px-4 text-sm font-medium text-gray-900">%s</td>'
                   '<td class="py-3 px-4 text-center">%s</td><td class="py-3 px-4 text-center">%s</td></tr>'
                   % (esc(name), span(ga, 'px-2 py-1'), span(gb, 'px-2 py-1')))
    return out, len(rows)


CENTER_STYLE = ('<style id="cr-chart-center">.cr-hero-center{text-align:center}.cr-hero-center .flex{justify-content:center}'
                '.cr-hero-center p{margin-left:auto;margin-right:auto}.cr-center{text-align:center}'
                '.cr-center svg{margin-left:auto;margin-right:auto}.cr-center .cr-key{justify-content:center}'
                '.cr-center figcaption{margin-left:auto;margin-right:auto}</style>')


def center_hero(page):
    """Centre the title block of a chart page: breadcrumb, title, description
    and rating key. The style travels with the page, not the shared stylesheet."""
    # replaced where it stands, so that it does not trade places with the
    # markup fix_page_quality.py adds at the end of the head
    if 'id="cr-chart-center"' in page:
        page = re.sub(r'<style id="cr-chart-center">[\s\S]*?</style>', lambda _: CENTER_STYLE, page, count=1)
    else:
        page = page.replace('</head>', CENTER_STYLE + '\n</head>', 1)
    return re.sub(r'<section class="(?:cr-hero-center )?(bg-gradient-to-b[^"]*)"',
                  r'<section class="cr-hero-center \1"', page, count=1)


def group_block(mats, lang):
    """Summary figures of a chart page: overall rating shares per material and,
    for groups of up to six materials, the share rated A or B by chemical class."""
    names = [material_name(m, lang) for m in mats]
    profiles = [cs.material_profile(m) for m in mats]
    diagrams.reset_ids()
    figs = diagrams.figure(
        diagrams.overall_bars(lang, [(n, p['all']) for n, p in zip(names, profiles)], t('fig_overall_h', lang)),
        t('fig_overall_cap', lang), diagrams.grade_key(lang, with_none=False))
    figs = '<div><h3 class="font-semibold text-gray-900 mb-2">%s</h3>%s</div>' % (esc(t('fig_overall_h', lang)), figs)
    if len(mats) <= 6:
        grid = diagrams.figure(
            diagrams.class_grid(lang, names, profiles, cs.class_name, cs.MIN_ROWS, cs.good_share,
                                t('fig_group_h', lang), heads=[diagrams.short_name(m, lang) for m in mats]),
            t('fig_group_cap', lang, n=cs.MIN_ROWS), diagrams.ramp_key(lang))
        figs += '<div><h3 class="font-semibold text-gray-900 mb-2">%s</h3>%s</div>' % (esc(t('fig_group_h', lang)), grid)
    return ('<!-- group-figures:start -->\n<section class="cr-center px-4 py-8 bg-white border-t border-gray-200">%s'
            '<div class="max-w-5xl mx-auto"><div class="cr-fp">%s</div>'
            '<p style="font-size:.8rem;color:#4b5563;margin-top:1rem">%s</p></div></section>\n'
            '<!-- group-figures:end -->\n    ') % (FIG_STYLE, figs, esc(t('class_note', lang)))


def patch(page, lang, chems, trans):
    total = None
    if 'id="chartTable"' in page:
        m = re.search(r'MATS\s*=\s*\[(.*?)\];', page, re.S)
        mats = re.findall(r'["\']?key["\']?\s*:\s*["\'](\w+)["\']', m.group(1)) if m else []
        if not mats:
            return page
        rows, total = chart_rows(mats, lang, chems, trans)
        page = re.sub(r'<!-- group-figures:start -->[\s\S]*?<!-- group-figures:end -->\s*', '', page)
        at = page.find('id="searchInput"')
        at = page.rfind('<section', 0, at) if at > 0 else -1
        if at > 0:
            page = page[:at] + group_block(mats, lang) + page[at:]
        page = center_hero(page)
        page = re.sub(r'(<tbody id="chartTable"[^>]*>)[\s\S]*?(</tbody>)',
                      lambda x: x.group(1) + '\n' + '\n'.join(rows) + '\n' + x.group(2), page, count=1)
    elif 'id="compareTable"' in page:
        a = re.search(r'MAT_A\s*=\s*["\'](\w+)["\']', page)
        b = re.search(r'MAT_B\s*=\s*["\'](\w+)["\']', page)
        if not (a and b):
            return page
        rows, total = compare_rows(a.group(1), b.group(1), lang, chems, trans)
        page = re.sub(r'(<tbody id="compareTable"[^>]*>)[\s\S]*?(</tbody>)',
                      lambda x: x.group(1) + '\n' + '\n'.join(rows) + '\n' + x.group(2), page, count=1)
    else:
        return page
    page = re.sub(r'(id="resultCount"[^>]*>)[^<]*(<)', r'\g<1>%d\g<2>' % total, page)
    if ALIAS_FILTER not in page:
        page = re.sub(r"(fetch\('/data/chemicals_burkle_full\.json'\)[\s\S]{0,200}?\.then\(\s*(?:function\s*\(\s*data\s*\)|\(?\s*data\s*\)?\s*=>)\s*\{)",
                      lambda x: x.group(1) + '\n            ' + ALIAS_FILTER, page, count=1)
    return page


def main():
    check = '--check' in sys.argv
    chems, _ = rd.load()
    changed = seen = 0
    for lang in LANGS:
        trans = load_translations(lang)
        for section in ('charts', 'compare'):
            base = os.path.join(ROOT, section if lang == 'en' else os.path.join(lang, section))
            if not os.path.isdir(base):
                continue
            for d in sorted(os.listdir(base)):
                path = os.path.join(base, d, 'index.html')
                if not os.path.isfile(path):
                    continue
                with open(path, encoding='utf-8') as f:
                    page = f.read()
                if 'http-equiv="refresh"' in page[:600]:
                    continue
                new = patch(page, lang, chems, trans)
                seen += 1
                if new != page:
                    changed += 1
                    if not check:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new)
    print('%d chart and comparison pages, %s %d' % (seen, 'would change' if check else 'rewrote', changed))


if __name__ == '__main__':
    main()
