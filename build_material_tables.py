#!/usr/bin/env python3
"""Rebuild the rating table inside every material page from resistance_data.

    python3 build_material_tables.py            # rewrite
    python3 build_material_tables.py --check    # report only

The material pages (materials/<slug>/ and materials/<lang>/<slug>/) carry
hand-written sections on properties and applications, so this patches them in
place instead of regenerating them. For each page it

  * replaces the table body with static rows, one per source row that has a
    rating for this material. Synonym rows and rows without a rating for the
    material are left out: they were about 40 % of every table.
  * keeps the concentration, and marks estimated values and pitting risk,
  * links each chemical that has its own page,
  * writes the A/B/C/D counts into the page instead of computing them in the
    browser,
  * replaces the script that downloaded the whole 2.9 MB data set to draw the
    table with a filter over the rows already in the page. On 25 localized
    pages that script was loaded from a wrong relative path, so their tables
    never rendered at all.
  * replaces the "1,650+ chemicals" claims with the number of chemicals that
    are actually rated for the material.

Idempotent.
"""

import html
import json
import os
import re
import sys

import class_stats as cs
import diagrams
import resistance_data as rd
from page_i18n import conc_label, material_name, t

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ['en', 'de', 'es', 'fr', 'pt', 'zh']

NOTE = {
    'en': 'est. = estimated value in the source, given without a temperature. L = risk of pitting or stress-corrosion cracking. Only chemicals with a rating for this material are listed.',
    'de': 'gesch. = Schätzwert der Quelle, ohne Temperaturangabe. L = Gefahr von Lochfraß oder Spannungsrisskorrosion. Aufgeführt sind nur Chemikalien mit einer Bewertung für diesen Werkstoff.',
    'es': 'est. = valor estimado en la fuente, sin temperatura. L = riesgo de picaduras o corrosión bajo tensión. Solo se indican los productos químicos con clasificación para este material.',
    'fr': 'est. = valeur estimée dans la source, sans température. L = risque de piqûres ou de corrosion sous contrainte. Seuls les produits chimiques notés pour ce matériau sont indiqués.',
    'pt': 'est. = valor estimado na fonte, sem temperatura. L = risco de pites ou corrosão sob tensão. São listados apenas os produtos químicos com classificação para este material.',
    'zh': '估 = 原始资料中的估计值，未注明温度。L = 存在点蚀或应力腐蚀开裂风险。仅列出对该材料有等级的化学品。',
}

CHEMICALS_WORD = {'en': 'Chemicals', 'de': 'Chemikalien', 'es': 'químicos', 'fr': 'produits',
                  'pt': 'químicos', 'zh': '种化学品'}

FILTER_SCRIPT = '''<script>
    (function () {
        var rows = [].slice.call(document.querySelectorAll('#chemTable tr[data-s]'));
        var search = document.getElementById('searchInput');
        var rating = document.getElementById('ratingFilter');
        var temp = document.getElementById('tempFilter');
        var count = document.getElementById('resultCount');
        function apply() {
            var q = search ? search.value.toLowerCase() : '';
            var r = rating ? rating.value : 'all';
            var key = temp && temp.value === 'c50' ? 'g50' : 'g20';
            var n = 0;
            rows.forEach(function (tr) {
                var g = tr.getAttribute('data-' + key) || '';
                var ok = (!q || tr.getAttribute('data-s').indexOf(q) > -1) &&
                    (r === 'all' || (r === 'AB' ? (g === 'A' || g === 'B') : g === r));
                tr.style.display = ok ? '' : 'none';
                if (ok) n++;
            });
            if (count) count.textContent = n;
        }
        if (search) search.addEventListener('input', apply);
        if (rating) rating.addEventListener('change', apply);
        if (temp) temp.addEventListener('change', apply);
        window.filterTable = apply;
        window.loadMore = function () {};
        if (window.lucide) lucide.createIcons();
    })();
    </script>'''


def esc(s):
    return html.escape(str(s), quote=True)


def load_translations(lang):
    """German (lower case) -> localized chemical name, from js/chemical_translations_<lang>.js."""
    path = os.path.join(ROOT, 'js', 'chemical_translations_%s.js' % lang)
    out = {}
    if lang in ('en', 'de') or not os.path.exists(path):
        return out
    text = open(path, encoding='utf-8').read()
    for m in re.finditer(r"""^\s*(['"])(.+?)\1\s*:\s*(['"])(.+?)\3\s*,?\s*$""", text, re.M):
        out[m.group(2).replace("\\'", "'").lower()] = m.group(4).replace("\\'", "'")
    return out


def chem_links():
    """German source name -> slug of its chemical page."""
    with open(os.path.join(ROOT, 'data', 'chemical_pages.json'), encoding='utf-8') as f:
        pages = json.load(f)['pages']
    return {p['source']: (s, p['names']) for s, p in pages.items() if 'redirect_to' not in p}


def cell(r, which, lang):
    g = r.get('c' + which)
    if r.get('k'):
        return '<span class="rating-NR px-2 py-1 rounded text-xs font-bold">K</span>' if which == '20' else '&ndash;'
    if g is None:
        return '<span class="rating-NR px-2 py-1 rounded text-xs font-bold">&ndash;</span>'
    flag = ''
    if which == '20' and r.get('est'):
        flag = ' <span class="text-xs text-gray-500">%s</span>' % esc(t('est_short', lang))
    if r.get('pit' + which):
        flag += ' <span class="text-xs text-gray-500">L</span>'
    return '<span class="rating-%s px-2 py-1 rounded text-xs font-bold">%s</span>%s' % (
        r['w' + which], esc(g), flag)


def build_rows(code, lang, columns, chems, links, trans):
    rows = []
    stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    rated_chems = 0
    for chem in chems.values():
        seen = False
        for v in chem['variants']:
            r = v['ratings'].get(code)
            if r is None:
                continue
            seen = True
            if r.get('w20') in stats:
                stats[r['w20']] += 1
            link = links.get(chem['name_de'])
            if link:
                name = link[1][lang]
            elif lang == 'de':
                name = chem['name_de']
            elif lang == 'en':
                name = chem['name_en']
            else:
                name = trans.get(chem['name_de'].lower(), chem['name_en'])
            conc = conc_label(v['conc'], lang)
            label = esc(name)
            if link:
                base = '/chemicals/' if lang == 'en' else '/chemicals/%s/' % lang
                label = '<a href="%s%s/" class="underline">%s</a>' % (base, link[0], label)
            sub = ''
            if lang != 'de' and name.lower() != chem['name_de'].lower():
                sub = '<div class="text-xs text-gray-500" lang="de">%s</div>' % esc(chem['name_de'])
            cells = []
            for col in columns:
                if col == 'name':
                    extra = ''
                    if 'conc' not in columns and conc:
                        extra = '<div class="text-xs text-gray-500">%s</div>' % esc(conc)
                    cells.append('<td class="py-3 px-4"><div class="font-medium text-gray-900">%s</div>%s%s</td>'
                                 % (label, extra, sub))
                elif col == 'conc':
                    cells.append('<td class="py-3 px-4 text-sm text-gray-600">%s</td>' % (esc(conc) or '&mdash;'))
                elif col == 'cas':
                    cells.append('<td class="py-3 px-4 text-sm text-gray-500 font-mono">%s</td>'
                                 % (esc(chem['cas']) or '&mdash;'))
                else:
                    cells.append('<td class="py-3 px-4 text-center whitespace-nowrap">%s</td>' % cell(r, col, lang))
            search = ' '.join([name, chem['name_de'], chem['name_en'], chem['cas'], conc]).lower()
            rows.append('<tr class="border-b border-gray-100 hover:bg-gray-50" data-g20="%s" data-g50="%s" data-s="%s">%s</tr>'
                        % (r.get('w20') or '', r.get('w50') or '', esc(search), ''.join(cells)))
        if seen:
            rated_chems += 1
    return rows, stats, rated_chems


FIG_STYLE = ('<style>.cr-fig{margin:0}.cr-fig figcaption{font-size:.8rem;color:#4b5563;line-height:1.5;'
             'margin-top:.5rem;max-width:520px}.cr-key{display:flex;flex-wrap:wrap;gap:.25rem .9rem;font-size:.78rem;'
             'color:#374151;margin-top:.5rem}.cr-key i{display:inline-block;width:.7rem;height:.7rem;border-radius:2px;'
             'margin-right:.3rem;vertical-align:-1px;box-sizing:border-box}.cr-fp{display:grid;'
             'grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem 2rem;align-items:start}'
             '.cr-fp dl{margin:0;font-size:.93rem}.cr-fp dt{font-weight:600;color:#111827;margin-top:.7rem}'
             '.cr-fp dt:first-child{margin-top:0}.cr-fp dd{margin:.1rem 0 0;color:#374151}</style>')


def fingerprint_block(code, lang):
    """The "resistance by chemical class" section of a material page."""
    profile = cs.material_profile(code)
    name = material_name(code, lang)
    diagrams.reset_ids()
    svg = diagrams.fingerprint(lang, name, profile, cs.class_name, cs.MIN_ROWS)
    if svg is None:
        return ''
    ranked = sorted(((cs.good_share(c), k) for k, c in profile.items()
                     if k != 'all' and c['n'] >= cs.MIN_ROWS), key=lambda x: (-x[0], x[1]))

    def listing(items):
        return '; '.join('%s %d %%' % (esc(cs.class_name(k, lang)), round(100 * share))
                         for share, k in items)

    best, worst = ranked[:3], ranked[-3:][::-1]
    overall = profile['all']
    facts = '<dl><dt>%s</dt><dd>%s</dd><dt>%s</dt><dd>%s</dd><dt>%s</dt><dd>%s</dd></dl>' % (
        esc(t('finger_best', lang)), listing(best), esc(t('finger_worst', lang)), listing(worst),
        esc(t('fig_overall_h', lang)),
        ', '.join('%s %d %%' % (g, round(100 * overall[g] / overall['n'])) for g in 'ABCD')
        + ' (%d)' % overall['n'])
    fig = diagrams.figure(svg, t('fig_finger_cap', lang, n=cs.MIN_ROWS), diagrams.grade_key(lang, with_none=False))
    return ('<!-- fingerprint:start -->\n<section class="px-4 py-8 bg-white border-t border-gray-200">%s'
            '<div class="max-w-5xl mx-auto"><h2 class="text-2xl font-bold text-gray-900 mb-4">%s</h2>'
            '<div class="cr-fp"><div>%s<p style="font-size:.8rem;color:#4b5563;margin-top:1rem">%s</p></div>%s</div>'
            '</div></section>\n<!-- fingerprint:end -->\n    ') % (
        FIG_STYLE, esc(t('fig_finger_h', lang)), facts, esc(t('class_note', lang)), fig)


def columns_of(thead):
    cols = []
    for i, th in enumerate(re.findall(r'<th[^>]*>(.*?)</th>', thead, re.S)):
        text = re.sub(r'<[^>]+>', '', th)
        if i == 0:
            cols.append('name')
        elif '20' in text:
            cols.append('20')
        elif '50' in text:
            cols.append('50')
        elif 'CAS' in text.upper():
            cols.append('cas')
        else:
            cols.append('conc')
    return cols


def patch(path, lang, code, chems, links, trans):
    with open(path, encoding='utf-8') as f:
        page = f.read()
    orig = page

    m = re.search(r'<table[^>]*>\s*<thead[\s\S]*?</thead>\s*<tbody[^>]*>[\s\S]*?</tbody>\s*</table>', page)
    if not m or 'chemTable' not in m.group(0):
        return None
    table = m.group(0)
    thead = re.search(r'<thead[\s\S]*?</thead>', table).group(0)
    columns = columns_of(thead)
    rows, stats, rated = build_rows(code, lang, columns, chems, links, trans)
    table_open = re.sub(r'\s+id="chemTable"', '', re.match(r'<table[^>]*>', table).group(0))
    new_table = '%s\n%s\n<tbody id="chemTable" class="divide-y divide-gray-100">\n%s\n</tbody>\n</table>' % (
        table_open, thead, '\n'.join(rows))
    page = page[:m.start()] + new_table + page[m.end():]

    # note under the table
    page = re.sub(r'\s*<p id="cr-table-note"[^>]*>[\s\S]*?</p>', '', page)
    note = '\n<p id="cr-table-note" class="px-4 py-3 text-xs text-gray-500">%s</p>' % esc(NOTE[lang])
    end = page.index('</table>', m.start()) + len('</table>')
    page = page[:end] + note + page[end:]

    # counts
    for g in 'ABCD':
        page = re.sub(r'(id="stat%s"[^>]*>)[^<]*(<)' % g, r'\g<1>%d\g<2>' % stats[g], page)
    page = re.sub(r'(id="resultCount"[^>]*>)[^<]*(<)', r'\g<1>%d\g<2>' % len(rows), page)

    # scripts: drop the data download, keep a filter over the static rows
    page = re.sub(r'\s*<script src="[^"]*chemical_translations_[a-z]+\.js"></script>', '', page)
    page = re.sub(r'<script>(?:(?!</script>)[\s\S])*?const MATERIAL\s*=(?:(?!</script>)[\s\S])*?</script>',
                  lambda _: FILTER_SCRIPT, page)
    page = re.sub(r'<script>\s*function filterTable\(\)(?:(?!</script>)[\s\S])*?</script>',
                  lambda _: FILTER_SCRIPT, page)
    page = re.sub(r'\s+onkeyup="filterTable\(\)"', '', page)

    # resistance by chemical class, in front of the search and table section
    page = re.sub(r'<!-- fingerprint:start -->[\s\S]*?<!-- fingerprint:end -->\s*', '', page)
    at = page.find('id="searchInput"')
    at = page.rfind('<section', 0, at) if at > 0 else -1
    if at > 0:
        page = page[:at] + fingerprint_block(code, lang) + page[at:]

    # "1,650+ chemicals" -> what is really rated for this material
    page = re.sub(r'1[,.\u00a0\u202f ]?65[01]\+', str(rated), page)
    # a title that ended in "| 1,650+" would now end in a bare number
    page = re.sub(r'\| (\d+)(?=</title>|")', lambda n: '| %s %s' % (n.group(1), CHEMICALS_WORD[lang]), page)
    return page if page != orig else orig, len(rows), rated, stats


def main():
    check = '--check' in sys.argv
    chems, _ = rd.load()
    links = chem_links()
    changed = 0
    for lang in LANGS:
        trans = load_translations(lang)
        for code, (slug, _fam) in rd.MATERIALS.items():
            rel = 'materials/%s/index.html' % slug if lang == 'en' else 'materials/%s/%s/index.html' % (lang, slug)
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                print('missing   ', rel)
                continue
            with open(path, encoding='utf-8') as f:
                before = f.read()
            if 'http-equiv="refresh"' in before[:600]:
                continue
            result = patch(path, lang, code, chems, links, trans)
            if result is None:
                print('no table  ', rel)
                continue
            page, n_rows, rated, stats = result
            if page != before:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(page)
            if lang == 'en':
                print('%-22s %4d rows, %4d chemicals  A %d  B %d  C %d  D %d  (%d KB -> %d KB)' % (
                    slug, n_rows, rated, stats['A'], stats['B'], stats['C'], stats['D'],
                    len(before) // 1024, len(page) // 1024))
    print('%s %d material pages' % ('would change' if check else 'rewrote', changed))


if __name__ == '__main__':
    main()
