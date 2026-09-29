#!/usr/bin/env python3
"""Build the chemical pages and the chemical x material pair pages.

    python3 build_chemical_pages.py            # write pages
    python3 build_chemical_pages.py --check    # report what would change, write nothing

Input
    resistance_data.py          ratings, read from the Bürkle spreadsheet
    data/chemical_pages.json    which chemicals have pages, their names, redirects
    page_i18n.py                strings for en, de, es, fr, pt, zh
    analytics_head.py           the shared head block

Output, for every language
    chemicals/[<lang>/]<slug>/index.html              the chemical page (hub)
    chemicals/[<lang>/]<slug>/<material>/index.html   one page per material

The chemical page carries the whole data set for that chemical: every
concentration the source lists, all 24 materials, both temperatures. The pair
pages repeat one row of it, so they are kept out of Google's index and out of
the sitemap (PAIR_ROBOTS below) while staying reachable for readers.

This replaces generate_chemical_pages.py, generate_chemical_material_pages.py,
enrich_chemical_pages.py, the add_*.py scripts and the fix_ratings/fix_mappings
scripts, which patched published HTML in place and let pages drift away from
the data.
"""

import html
import json
import os
import sys
from collections import OrderedDict

import analytics_head
import diagrams
import resistance_data as rd
from redirect_stub import stub
from page_i18n import (INDEXED_LANGS, LANGS, conc_label, hazard_text, material_full,
                       material_name, material_note, t)

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://chemicalresistance.org'
CONTENT_UPDATED = '2026-09-29'

# Pair pages that have a rating: hidden from Google only, so the other search
# engines that send the site its traffic keep them. Set to
# '<meta name="robots" content="noindex,follow">' to hide them everywhere.
PAIR_ROBOTS = '<meta name="googlebot" content="noindex,follow">'
NOINDEX = '<meta name="robots" content="noindex,follow">'

# Order in which materials are named in summaries: the ones people look for first.
PRIORITY = ['PTFE', 'HDPE', 'PP', 'PVDF', 'PVC_HART', 'EPDM', 'FPM', 'NBR', 'V4A', 'V2A', 'AL',
            'LDPE', 'FEP', 'ECTFE_ETFE', 'PA', 'POM', 'PC', 'SI', 'PVC_WEICH', 'PS', 'PSU',
            'PETG', 'PMP', 'SAN']

DATASET_DESC = {
    'en': 'Chemical resistance ratings of {n} plastics, elastomers and metals against {chem} at 20 °C and 50 °C, for {k} concentration(s). Ratings A to D, from the chemical resistance list of Bürkle GmbH.',
    'de': 'Beständigkeitsbewertungen von {n} Kunststoffen, Elastomeren und Metallen gegenüber {chem} bei 20 °C und 50 °C, für {k} Konzentration(en). Bewertungen A bis D aus der Beständigkeitsliste der Bürkle GmbH.',
    'es': 'Clasificaciones de resistencia química de {n} plásticos, elastómeros y metales frente a {chem} a 20 °C y 50 °C, para {k} concentración(es). Clasificaciones de A a D, de la lista de resistencia química de Bürkle GmbH.',
}

STYLE = '''<style>
*{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}body{background:#f8fafc}
.cr-card{background:#fff;border:1px solid #e5e7eb;border-radius:1rem;padding:1.25rem;margin-bottom:1.5rem}
.cr-card h2{font-size:1.25rem;font-weight:700;color:#111827;margin:0 0 .75rem}
.cr-card p{color:#4b5563;font-size:.95rem;line-height:1.6;margin:0 0 .75rem}
.cr-card p:last-child{margin-bottom:0}
.cr-sub{color:#6b7280;font-size:.85rem}
.cr-scroll{overflow-x:auto}
.cr-tbl{width:100%;border-collapse:collapse;font-size:.9rem}
.cr-tbl th,.cr-tbl td{padding:.45rem .6rem;border-bottom:1px solid #f1f5f9;text-align:left;vertical-align:middle}
.cr-tbl .c{text-align:center;white-space:nowrap}
.cr-tbl thead th{background:#f8fafc;font-weight:600;color:#111827;border-bottom:1px solid #e5e7eb}
.cr-tbl tr.fam th{background:#ecfdf5;color:#065f46;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em}
.cr-tbl td a,.cr-tbl th a{color:#047857;text-decoration:underline}
.cr-tbl tbody th{font-weight:500;color:#111827}
.cr-tbl tr.me th,.cr-tbl tr.me td{background:#f0fdf4}
.g{display:inline-block;min-width:2rem;padding:.15rem .45rem;border-radius:.375rem;font-weight:700;text-align:center;color:#fff}
.gA{background:#15803d}.gB{background:#1d4ed8}.gC{background:#d97706;color:#111827}.gD{background:#b91c1c}
.gN{background:#e5e7eb;color:#4b5563;font-weight:500}
.fl{font-size:.75rem;color:#4b5563}
.cr-facts{display:grid;grid-template-columns:minmax(8rem,max-content) 1fr;gap:.4rem 1rem;font-size:.9rem;margin:0}
.cr-facts dt{color:#6b7280}.cr-facts dd{color:#111827;margin:0}
.cr-list{margin:0;font-size:.93rem}
.cr-list dt{font-weight:600;color:#111827;margin-top:.7rem}
.cr-list dt:first-child{margin-top:0}
.cr-list dd{color:#374151;margin:.1rem 0 0}
.cr-list a,.cr-links a,.cr-card p a{color:#047857;text-decoration:underline}
.cr-legend{display:flex;flex-wrap:wrap;gap:.5rem 1.25rem;font-size:.85rem;color:#374151;margin:0 0 .75rem;padding:0;list-style:none}
.cr-links{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;font-size:.95rem}
.cr-crumb a{text-decoration:underline}
.cr-figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.5rem 2rem;align-items:start}
.cr-fig{margin:0}
.cr-fig h3{font-size:1rem;font-weight:600;color:#111827;margin:0 0 .6rem}
.cr-fig figcaption{font-size:.8rem;color:#4b5563;line-height:1.5;margin-top:.5rem;max-width:520px}
.cr-key{display:flex;flex-wrap:wrap;gap:.25rem .9rem;font-size:.78rem;color:#374151;margin-top:.5rem}
.cr-key i{display:inline-block;width:.7rem;height:.7rem;border-radius:2px;margin-right:.3rem;vertical-align:-1px;box-sizing:border-box}
.cr-tbl td.d{white-space:nowrap}
.cr-details{margin-top:1rem}
.cr-details summary{cursor:pointer;color:#047857;font-size:.9rem;font-weight:600;margin-bottom:.5rem}
.cr-noads .google-auto-placed,.cr-noads ins.adsbygoogle,#compat-table-zone .google-auto-placed,#compat-table-zone ins.adsbygoogle{display:none!important}
</style>'''


def esc(s):
    return html.escape(str(s), quote=True)


def write(path, text, changed, check):
    full = os.path.join(ROOT, path)
    old = None
    if os.path.exists(full):
        with open(full, encoding='utf-8', errors='replace') as f:
            old = f.read()
    if old == text:
        return
    changed.append(path)
    if check:
        return
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(text)


# --- urls -------------------------------------------------------------------

def chem_base(lang):
    return '/chemicals/' if lang == 'en' else '/chemicals/%s/' % lang


def chem_url(lang, slug):
    return '%s%s/' % (chem_base(lang), slug)


def pair_url(lang, slug, mat):
    return '%s%s/%s/' % (chem_base(lang), slug, rd.MATERIALS[mat][0])


def material_url(lang, mat):
    slug = rd.MATERIALS[mat][0]
    return '/materials/%s/' % slug if lang == 'en' else '/materials/%s/%s/' % (lang, slug)


def home_url(lang):
    return '/' if lang == 'en' else '/%s/' % lang


# --- chrome harvested from the existing site, so the pages match the rest ----

def load_chrome():
    """Header and footer per language, taken from a page the generator does not
    own, with the two stale links in it repaired."""
    import re
    chrome = {}
    for lang in LANGS:
        src = os.path.join(ROOT, 'chemicals', 'index.html' if lang == 'en' else lang + '/index.html')
        with open(src, encoding='utf-8') as f:
            page = f.read()
        m = re.search(r'<header[\s\S]*?</header>\s*<script>[\s\S]*?</script>', page)
        header = m.group(0) if m else ''
        m = re.search(r'<footer[\s\S]*?</footer>', page)
        footer = m.group(0) if m else ''
        if lang != 'en':
            # /de/about/ is a redirect stub; the page lives at /de-about/
            header = header.replace('href="/%s/about/"' % lang, 'href="/%s-about/"' % lang)
            footer = footer.replace('href="/%s/about/"' % lang, 'href="/%s-about/"' % lang)
        chrome[lang] = (header, footer)
    return chrome


# --- data helpers -----------------------------------------------------------

def primary_variant(chem):
    """The row the summary is based on: the most concentrated row that still
    has near-complete data, so the summary errs on the cautious side."""
    import re
    variants = chem['variants']
    most = max(len(v['ratings']) for v in variants)
    good = [v for v in variants if len(v['ratings']) >= 0.8 * most]
    numeric = []
    for v in good:
        m = re.match(r'\s*(\d+(?:[.,]\d+)?)', v['conc'])
        if m and '%' in v['conc']:
            numeric.append((float(m.group(1).replace(',', '.')), v))
    if numeric:
        return max(numeric, key=lambda x: x[0])[1]
    return max(good, key=lambda v: len(v['ratings']))


def variant_label(v, lang):
    return conc_label(v['conc'], lang) or t('conc_unspecified', lang)


def by_priority(codes):
    return sorted(codes, key=PRIORITY.index)


def grade_span(g, worst, est=False):
    """A rating badge. An estimate carries an asterisk inside the badge, which
    the footnote under the table explains."""
    if g is None:
        return '<span class="g gN">–</span>'
    return '<span class="g g%s">%s%s</span>' % (worst, esc(g), '*' if est else '')


def est_footnote(lang, ratings):
    if any(r and r.get('est') for r in ratings):
        return '<p class="cr-sub" style="margin-top:.6rem">* %s</p>' % esc(t('est_note', lang))
    return ''


def flags(r, lang, short=True):
    out = []
    if r.get('k'):
        out.append(t('k_value', lang))
    if r.get('single') and not r.get('est'):
        out.append(t('no_temp', lang))
    if r.get('pit20') or r.get('pit50'):
        out.append(t('pitting', lang))
    if r.get('corrected'):
        out.append(t('corrected', lang))
    if r.get('disputed'):
        out.append(t('disputed', lang))
    return out


def rating_cells(r, lang):
    """The 20 °C and 50 °C cells of one rating, plus the remark cell."""
    if r is None:
        none = '<td class="c"><span class="g gN" title="%s">–</span></td>' % esc(t('g_none', lang))
        return none + none + '<td></td>'
    remark = '<td class="fl">%s</td>' % esc('; '.join(flags(r, lang)))
    if r.get('k'):
        return '<td class="c" colspan="2"><span class="g gN">K</span></td>' + remark
    if r.get('single'):
        return '<td class="c" colspan="2">%s</td>%s' % (grade_span(r['c20'], r['w20'], r.get('est')), remark)
    return '<td class="c">%s</td><td class="c">%s</td>%s' % (
        grade_span(r['c20'], r['w20'], r.get('est')), grade_span(r['c50'], r['w50'], r.get('est')), remark)


def legend(lang):
    items = ''.join('<li><span class="g g%s">%s</span> %s</li>' % (g, g, esc(t('g_' + g, lang)))
                    for g in 'ABCD')
    items += '<li><span class="g gN">–</span> %s</li>' % esc(t('g_none', lang))
    items += '<li><span class="g gN">K</span> %s</li>' % esc(t('k_value', lang))
    return '<ul class="cr-legend">%s</ul><p class="cr-sub">%s</p>' % (items, esc(t('legend_est', lang)))


def similar_chemicals(pages, chems):
    """For each live slug, the other live chemicals whose 20 °C ratings agree
    on the largest share of the materials both have data for."""
    vec = {}
    for slug, p in pages.items():
        v = primary_variant(chems[p['source']])
        vec[slug] = {m: r['w20'] for m, r in v['ratings'].items() if r.get('w20')}
    out = {}
    for a in vec:
        scored = []
        for b in vec:
            if a == b or pages[a]['source'] == pages[b]['source']:
                continue
            shared = [m for m in vec[a] if m in vec[b]]
            if len(shared) < 12:
                continue
            same = sum(1 for m in shared if vec[a][m] == vec[b][m])
            scored.append((same / len(shared), len(shared), b))
        scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
        out[a] = [(b, share) for share, _, b in scored[:6]]
    return out


# --- page head --------------------------------------------------------------

def head(lang, title, desc, canonical, robots, alternates, jsonld):
    alt = ''
    for code, href in alternates:
        alt += '    <link rel="alternate" hreflang="%s" href="%s">\n' % (code, href)
    ld = ''.join('    <script type="application/ld+json">%s</script>\n'
                 % json.dumps(j, ensure_ascii=False, separators=(',', ':')) for j in jsonld)
    return '''<!DOCTYPE html>
<html lang="%(lang)s">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
%(analytics)s
    <title>%(title)s</title>
    <meta name="description" content="%(desc)s">
%(robots)s    <link rel="icon" href="/favicon.ico">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="canonical" href="%(canonical)s">
%(alt)s    <link rel="stylesheet" href="/css/tailwind.min.css">
    %(style)s
%(ld)s    <meta property="og:title" content="%(title)s">
    <meta property="og:description" content="%(desc)s">
    <meta property="og:type" content="article">
    <meta property="og:url" content="%(canonical)s">
    <meta property="og:image" content="%(site)s/og-image.png">
    <meta property="og:site_name" content="ChemicalResistance.org">
    <meta name="twitter:card" content="summary">
</head>
<body class="text-gray-700 min-h-screen">
''' % {
        'lang': 'zh-Hans' if lang == 'zh' else lang, 'title': esc(title), 'desc': esc(desc),
        'analytics': analytics_head.block(indent='    '),
        'robots': ('    %s\n' % robots) if robots else '', 'canonical': canonical, 'alt': alt,
        'style': STYLE.replace('\n', '\n    '), 'ld': ld, 'site': SITE,
    }


def breadcrumb_ld(items):
    return {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u}
                            for i, (n, u) in enumerate(items)],
    }


def description(lang, name, variant, n_mats, limit=155):
    """Answer first: which materials are rated A and which D."""
    ratings = variant['ratings']
    a = by_priority([m for m, r in ratings.items() if r.get('w20') == 'A'])
    d = by_priority([m for m, r in ratings.items() if r.get('w20') == 'D'])
    conc = conc_label(variant['conc'], lang)
    lead = '%s, %s' % (name, conc) if conc else name
    tail = '%d %s, 20 °C / 50 °C.' % (n_mats, t('materials_word', lang))
    sep = t('list_sep', lang)

    def build(na, nd):
        parts = [lead + '.']
        if a:
            more = ' +%d' % (len(a) - na) if len(a) > na else ''
            parts.append('%s: %s%s.' % (t('rated', lang, g='A'), sep.join(material_name(m, lang) for m in a[:na]), more))
        if d:
            more = ' +%d' % (len(d) - nd) if len(d) > nd else ''
            parts.append('%s: %s%s.' % (t('rated', lang, g='D'), sep.join(material_name(m, lang) for m in d[:nd]), more))
        parts.append(tail)
        return ' '.join(parts)

    for na, nd in ((6, 5), (5, 4), (4, 4), (4, 3), (3, 3), (3, 2), (2, 2), (2, 1), (1, 1)):
        s = build(min(na, len(a)), min(nd, len(d)))
        if len(s) <= limit:
            return s
    return build(min(1, len(a)), min(1, len(d)))[:limit]


# --- chemical page ----------------------------------------------------------

def names_list(codes, lang, slug=None, link_lang=None):
    sep = t('list_sep', lang)
    if not codes:
        return esc(t('none', lang))
    if slug:
        return sep.join('<a href="%s">%s</a>' % (pair_url(link_lang, slug, m),
                                                  esc(material_name(m, lang))) for m in codes)
    return esc(sep.join(material_name(m, lang) for m in codes))


def glance(lang, slug, chem, pv):
    ratings = pv['ratings']
    rows = []
    for g in 'ABCD':
        codes = by_priority([m for m, r in ratings.items() if r.get('w20') == g])
        rows.append((t('rated_' + g, lang), '%s <span class="cr-sub">(%d)</span>'
                     % (names_list(codes, lang, slug, lang), len(codes))))
    missing = by_priority([m for m in rd.MATERIALS if m not in ratings or not ratings[m].get('w20')])
    if missing:
        rows.append((t('no_data_for', lang), names_list(missing, lang)))
    worse = by_priority([m for m, r in ratings.items() if r.get('w20') and r.get('w50')
                         and rd.GRADE_RANK[r['w50']] > rd.GRADE_RANK[r['w20']]])
    if worse:
        sep = t('list_sep', lang)
        rows.append((t('worse_at_50', lang), sep.join(
            '%s (%s → %s)' % (esc(material_name(m, lang)), ratings[m]['c20'], ratings[m]['c50'])
            for m in worse)))
    pit = by_priority([m for m, r in ratings.items() if r.get('pit20') or r.get('pit50')])
    if pit:
        rows.append((t('pitting_for', lang), names_list(pit, lang)))
    if len(chem['variants']) > 1:
        dep = []
        for m in PRIORITY:
            seen = [(v, v['ratings'][m]) for v in chem['variants']
                    if m in v['ratings'] and v['ratings'][m].get('w20')]
            if len({r['w20'] for _, r in seen}) < 2:
                continue
            best = min(seen, key=lambda x: rd.GRADE_RANK[x[1]['w20']])
            worst = max(seen, key=lambda x: rd.GRADE_RANK[x[1]['w20']])
            dep.append('%s: %s (%s), %s (%s)' % (
                esc(material_name(m, lang)), best[1]['w20'], esc(variant_label(best[0], lang)),
                worst[1]['w20'], esc(variant_label(worst[0], lang))))
        if dep:
            rows.append((t('conc_dependent', lang), '; '.join(dep)))
    basis = (t('glance_basis', lang, conc=variant_label(pv, lang))
             if len(chem['variants']) > 1 or pv['conc'] else t('glance_basis_plain', lang))
    body = ''.join('<dt>%s</dt><dd>%s</dd>' % (esc(k), v) for k, v in rows)
    return '<section class="cr-card"><h2>%s</h2><p class="cr-sub">%s</p><dl class="cr-list">%s</dl></section>' % (
        esc(t('glance', lang)), esc(basis), body)


def figures(lang, name, chem, pv):
    """Rating profile and temperature shift for the row the summary is based on."""
    basis = ''
    if len(chem['variants']) > 1 or pv['conc']:
        basis = '<p class="cr-sub">%s</p>' % esc(t('glance_basis', lang, conc=variant_label(pv, lang)))
    profile = ('<div class="cr-fig"><h3>%s</h3>%s</div>' % (
        esc(t('fig_profile_h', lang)),
        diagrams.figure(diagrams.profile_bars(lang, name, pv), t('fig_profile_cap', lang),
                        diagrams.grade_key(lang))))
    shift = diagrams.temperature_shift(lang, name, pv)
    if shift:
        temp = diagrams.figure(shift, t('fig_temp_cap', lang), diagrams.temperature_key(lang))
    else:
        temp = '<p class="cr-sub">%s</p>' % esc(t('fig_temp_none', lang))
    temp = '<div class="cr-fig"><h3>%s</h3>%s</div>' % (esc(t('fig_temp_h', lang)), temp)
    return '<section class="cr-card">%s<div class="cr-figs">%s%s</div></section>' % (basis, profile, temp)


def facts(lang, chem, name):
    rows = []
    if chem['cas']:
        rows.append((t('cas', lang), esc(chem['cas'])))
    if chem['formula']:
        rows.append((t('formula', lang), esc(chem['formula'])))
    hz = hazard_text(chem['hazard'], lang) if chem['hazard'] else ''
    if hz:
        rows.append((t('hazard', lang), '%s <span class="cr-sub">(%s)</span>'
                     % (esc(hz), esc(t('hazard_note', lang)))))
    if chem['flammable']:
        rows.append((t('flammable', lang), esc(t('yes', lang))))
    concs = [variant_label(v, lang) for v in chem['variants']]
    if len(concs) > 1 or chem['variants'][0]['conc']:
        rows.append((t('concentrations', lang), esc('; '.join(concs))))
    aliases = chem['aliases_de'] if lang == 'de' else chem['aliases_en']
    aliases = [a for a in aliases if a.lower() != name.lower()]
    if aliases:
        rows.append((t('aliases', lang), esc('; '.join(aliases[:12]))))
    if lang != 'de':
        rows.append((t('source_name', lang), '<span lang="de">%s</span>' % esc(chem['name_de'])))
    if not rows:
        return ''
    body = ''.join('<dt>%s</dt><dd>%s</dd>' % (esc(k), v) for k, v in rows)
    return '<section class="cr-card"><h2>%s</h2><dl class="cr-facts">%s</dl></section>' % (
        esc(t('facts', lang)), body)


def matrix(lang, slug, name, chem):
    variants = chem['variants']
    head_cells = ''.join('<th class="c" scope="col">%s</th>' % esc(variant_label(v, lang))
                         for v in variants)
    body = ''
    for fam in rd.FAMILIES:
        body += '<tr class="fam"><th colspan="%d" scope="colgroup">%s</th></tr>' % (
            len(variants) + 1, esc(t('fam_' + fam, lang)))
        for m, (mslug, mfam) in rd.MATERIALS.items():
            if mfam != fam:
                continue
            cells = ''
            for v in variants:
                r = v['ratings'].get(m)
                if r is None:
                    cells += '<td class="c"><span class="g gN">–</span></td>'
                elif r.get('k'):
                    cells += '<td class="c"><span class="g gN">K</span></td>'
                else:
                    cells += '<td class="c">%s</td>' % grade_span(r['c20'], r['w20'], r.get('est'))
            body += '<tr><th scope="row"><a href="%s">%s</a></th>%s</tr>' % (
                material_url(lang, m), esc(material_name(m, lang)), cells)
    ladder = diagrams.figure(
        diagrams.concentration_ladder(lang, name, chem, [variant_label(v, lang) for v in variants]),
        t('fig_ladder_cap', lang), diagrams.grade_key(lang))
    return ('<section class="cr-card cr-noads"><h2>%s</h2>%s'
            '<details class="cr-details"><summary>%s</summary><div class="cr-scroll"><table class="cr-tbl">'
            '<thead><tr><th scope="col">%s</th>%s</tr></thead><tbody>%s</tbody></table></div>'
            '%s</details></section>') % (
        esc(t('fig_ladder_h', lang)), ladder, esc(t('table_view', lang)),
        esc(t('material', lang)), head_cells, body, est_footnote(lang, [r for v in variants for r in v['ratings'].values()]))


def variant_table(lang, slug, name, chem, v, index, first):
    body = ''
    for fam in rd.FAMILIES:
        body += '<tr class="fam"><th colspan="4" scope="colgroup">%s</th></tr>' % esc(t('fam_' + fam, lang))
        for m, (mslug, mfam) in rd.MATERIALS.items():
            if mfam != fam:
                continue
            body += '<tr><th scope="row"><a href="%s">%s</a></th>%s</tr>' % (
                material_url(lang, m), esc(material_name(m, lang)),
                rating_cells(v['ratings'].get(m), lang))
    title = t('table_h', lang)
    if len(chem['variants']) > 1 or v['conc']:
        title = '%s: %s, %s' % (title, name, variant_label(v, lang))
    note = ''
    if v['note']:
        note = '<p class="cr-sub">%s: <span lang="de">%s</span></p>' % (
            esc(t('remark', lang)), esc(v['note']))
    zone = ' id="compat-table-zone"' if first else ''
    return ('<section class="cr-card cr-noads" id="c%d"><h2>%s</h2>%s<div class="cr-scroll"%s>'
            '<table class="cr-tbl"><thead><tr><th scope="col">%s</th><th class="c" scope="col">20 °C</th>'
            '<th class="c" scope="col">50 °C</th><th scope="col">%s</th></tr></thead><tbody>%s</tbody>'
            '</table></div>%s</section>') % (
        index, esc(title), note, zone, esc(t('material', lang)), esc(t('remark', lang)), body,
        est_footnote(lang, v['ratings'].values()))


def corrections(lang, chem, only=None):
    """Corrected and disputed values, with the reason (English) and references."""
    rows = []
    for v in chem['variants']:
        for c in v['corrections']:
            if only and c['material'] != only:
                continue
            key = 'disputed_row' if c['kind'] == 'disputed' else 'corrections_row'
            line = t(key, lang, mat=material_name(c['material'], lang),
                     conc=variant_label(v, lang), old=c['source_value'], new=c.get('value', ''))
            refs = ' '.join('<a href="%s" rel="nofollow noopener">[%d]</a>' % (esc(u), i + 1)
                            for i, u in enumerate(c.get('refs', [])))
            local = c.get('reasons', {}).get(lang)
            if local or lang == 'en':
                reason = esc(local or c['reason'])
            else:
                reason = '<span lang="en">%s</span>' % esc(c['reason'])
            rows.append('<li>%s %s %s</li>' % (esc(line), reason, refs))
    if not rows:
        return ''
    return ('<section class="cr-card"><h2>%s</h2><ul class="cr-list" style="padding-left:1.1rem;list-style:disc">%s</ul>'
            '<p class="cr-sub">%s</p></section>') % (
        esc(t('corrections_h', lang)), ''.join(rows), esc(t('source_scale', lang)))


def chemical_page(lang, slug, page, chem, chrome, similar, pages):
    name = page['names'][lang]
    pv = primary_variant(chem)
    n_mats = len(rd.MATERIALS)
    title = t('title_chem', lang, chem=name, n=n_mats)
    if len(title) > 62:
        title = t('title_chem_short', lang, chem=name)
    desc = description(lang, name, pv, n_mats)
    url = SITE + chem_url(lang, slug)
    indexed = lang in INDEXED_LANGS
    alternates = []
    if indexed:
        alternates = [('x-default', SITE + chem_url('en', slug))]
        alternates += [(l, SITE + chem_url(l, slug)) for l in INDEXED_LANGS]
    crumbs = [(t('home', lang), home_url(lang)), (t('chemicals', lang), chem_base(lang)),
              (name, chem_url(lang, slug))]
    ld = [breadcrumb_ld(crumbs), {
        '@context': 'https://schema.org', '@type': 'WebPage', 'name': t('h1_chem', lang, chem=name),
        'description': desc, 'url': url, 'inLanguage': 'zh-Hans' if lang == 'zh' else lang,
        'dateModified': CONTENT_UPDATED,
        'isPartOf': {'@type': 'WebSite', 'name': 'ChemicalResistance.org', 'url': SITE + '/'},
        'about': {'@type': 'ChemicalSubstance', 'name': name,
                  **({'identifier': chem['cas']} if chem['cas'] else {})},
    }]
    if indexed:
        ld.append({
            '@context': 'https://schema.org', '@type': 'Dataset',
            'name': t('h1_chem', lang, chem=name), 'url': url, 'inLanguage': lang,
            'description': DATASET_DESC[lang].format(chem=name, n=n_mats, k=len(chem['variants'])),
            'dateModified': CONTENT_UPDATED,
            'variableMeasured': ['Resistance rating at 20 °C', 'Resistance rating at 50 °C'],
            'creator': {'@type': 'Organization', 'name': 'ChemicalResistance.org', 'url': SITE + '/'},
            'isBasedOn': {'@type': 'CreativeWork', 'name': 'Beständigkeitsliste (chemical resistance list)',
                          'publisher': {'@type': 'Organization', 'name': 'Bürkle GmbH',
                                        'url': 'https://www.buerkle.de'}},
        })
    header, footer = chrome[lang]

    lead = t('lead_chem', lang, n=n_mats)
    if len(chem['variants']) > 1:
        lead += ' ' + t('lead_variants', lang, k=len(chem['variants']))

    out = [head(lang, title, desc, url, '' if indexed else NOINDEX, alternates, ld), header]
    out.append('''
    <section class="bg-gradient-to-b from-emerald-50 to-white px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <nav class="text-sm text-emerald-600 mb-3 cr-crumb" aria-label="Breadcrumb">
                <a href="%s">%s</a> › <a href="%s">%s</a> › %s
            </nav>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">%s</h1>
            <p class="text-gray-600">%s</p>
        </div>
    </section>
    <main class="max-w-4xl mx-auto px-4 py-8">
''' % (home_url(lang), esc(t('home', lang)), chem_base(lang), esc(t('chemicals', lang)), esc(name),
       esc(t('h1_chem', lang, chem=name)), esc(lead)))

    diagrams.reset_ids()
    out.append(glance(lang, slug, chem, pv))
    out.append(figures(lang, name, chem, pv))
    out.append(facts(lang, chem, name))
    if len(chem['variants']) > 1:
        out.append(matrix(lang, slug, name, chem))
    for i, v in enumerate(chem['variants']):
        out.append(variant_table(lang, slug, name, chem, v, i + 1, i == 0))
    out.append('<section class="cr-card"><h2>%s</h2>%s</section>' % (esc(t('legend_h', lang)), legend(lang)))
    out.append(corrections(lang, chem))
    out.append('<section class="cr-card"><h2>%s</h2><p>%s</p><p>%s</p></section>' % (
        esc(t('about_h', lang)), esc(t('about_p1', lang)), esc(t('about_p2', lang))))
    sim = similar.get(slug, [])
    if sim:
        links = ''.join('<a href="%s">%s <span class="cr-sub">%d %%</span></a>' % (
            chem_url(lang, s), esc(pages[s]['names'][lang]), round(share * 100)) for s, share in sim)
        out.append('<section class="cr-card"><h2>%s</h2><p class="cr-sub">%s</p><div class="cr-links">%s</div></section>' % (
            esc(t('similar_h', lang)), esc(t('similar_p', lang)), links))
    out.append('\n    </main>\n    %s\n</body>\n</html>\n' % footer)
    return '\n'.join(x for x in out if x)


# --- pair page --------------------------------------------------------------

def pair_page(lang, slug, page, chem, mat, chrome):
    name = page['names'][lang]
    mname = material_name(mat, lang)
    rated = [v for v in chem['variants'] if mat in v['ratings']]
    pv = primary_variant(chem)
    url = SITE + pair_url(lang, slug, mat)
    title = t('title_pair', lang, mat=mname, chem=name)
    if len(title) > 62:
        title = t('h1_pair', lang, mat=mname, chem=name)

    if rated:
        bits = []
        for v in rated:
            r = v['ratings'][mat]
            if r.get('k'):
                val = 'K'
            elif r.get('single'):
                val = '%s (%s)' % (r['c20'], t('est' if r.get('est') else 'no_temp', lang))
            else:
                val = '%s %s, %s %s' % (r['c20'] or '–', t('at20', lang), r['c50'] or '–', t('at50', lang))
            c = conc_label(v['conc'], lang)
            bits.append('%s: %s' % (c, val) if c else val)
        desc = '%s + %s: %s.' % (mname, name, '; '.join(bits))
        if len(desc) > 155:
            desc = '%s + %s: %s …' % (mname, name, '; '.join(bits)[:120].rsplit(';', 1)[0])
    else:
        desc = t('desc_pair_nodata', lang, mat=mname, chem=name, n=len(rd.MATERIALS) - 1)

    if lang in INDEXED_LANGS and rated:
        robots = PAIR_ROBOTS
    else:
        robots = NOINDEX
    crumbs = [(t('home', lang), home_url(lang)), (t('chemicals', lang), chem_base(lang)),
              (name, chem_url(lang, slug)), (mname, pair_url(lang, slug, mat))]
    header, footer = chrome[lang]
    out = [head(lang, title, desc, url, robots, [], [breadcrumb_ld(crumbs)]), header]
    out.append('''
    <section class="bg-gradient-to-b from-emerald-50 to-white px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <nav class="text-sm text-emerald-600 mb-3 cr-crumb" aria-label="Breadcrumb">
                <a href="%s">%s</a> › <a href="%s">%s</a> › <a href="%s">%s</a> › %s
            </nav>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">%s</h1>
            <p class="text-gray-600">%s</p>
        </div>
    </section>
    <main class="max-w-4xl mx-auto px-4 py-8">
''' % (home_url(lang), esc(t('home', lang)), chem_base(lang), esc(t('chemicals', lang)),
       chem_url(lang, slug), esc(name), esc(mname), esc(t('h1_pair', lang, mat=mname, chem=name)),
       esc(material_full(mat, lang)) if lang in ('en', 'de', 'es') else ''))

    if rated:
        body = ''
        for v in chem['variants']:
            body += '<tr><th scope="row">%s</th>%s</tr>' % (
                esc(variant_label(v, lang)), rating_cells(v['ratings'].get(mat), lang))
        out.append(('<section class="cr-card cr-noads"><h2>%s</h2><div class="cr-scroll" id="compat-table-zone">'
                    '<table class="cr-tbl"><thead><tr><th scope="col">%s</th><th class="c" scope="col">20 °C</th>'
                    '<th class="c" scope="col">50 °C</th><th scope="col">%s</th></tr></thead><tbody>%s</tbody>'
                    '</table></div>%s</section>') % (
            esc(t('pair_rating_h', lang)), esc(t('concentration', lang)), esc(t('remark', lang)), body,
            est_footnote(lang, [v['ratings'].get(mat) for v in chem['variants']])))
    else:
        out.append('<section class="cr-card"><h2>%s</h2><p>%s</p></section>' % (
            esc(t('pair_rating_h', lang)), esc(t('pair_nodata', lang))))

    out.append(corrections(lang, chem, only=mat))

    good = by_priority([m for m, r in pv['ratings'].items() if r.get('w20') in ('A', 'B') and m != mat])
    if good:
        rows = ''
        for fam in rd.FAMILIES:
            fam_codes = [m for m in good if rd.MATERIALS[m][1] == fam]
            if not fam_codes:
                continue
            rows += '<dt>%s</dt><dd>%s</dd>' % (esc(t('fam_' + fam, lang)), t('list_sep', lang).join(
                '<a href="%s">%s</a> %s' % (pair_url(lang, slug, m), esc(material_name(m, lang)),
                                           pv['ratings'][m]['w20']) for m in fam_codes))
        basis = ''
        if len(chem['variants']) > 1 or pv['conc']:
            basis = '<p class="cr-sub">%s</p>' % esc(t('glance_basis', lang, conc=variant_label(pv, lang)))
        out.append('<section class="cr-card"><h2>%s</h2>%s<dl class="cr-list">%s</dl></section>' % (
            esc(t('alternatives_h', lang)), basis, rows))

    note = material_note(mat, lang)
    if note:
        out.append('<section class="cr-card"><h2>%s</h2><p>%s</p></section>' % (
            esc(t('material_note_h', lang, mat=mname)), esc(note)))
    out.append('<section class="cr-card"><h2>%s</h2>%s</section>' % (esc(t('legend_h', lang)), legend(lang)))
    out.append('<section class="cr-card"><div class="cr-links"><a href="%s">%s</a><a href="%s">%s</a></div></section>' % (
        chem_url(lang, slug), esc(t('see_chemical', lang, chem=name)),
        material_url(lang, mat), esc(t('see_material', lang, mat=mname))))
    out.append('<section class="cr-card"><h2>%s</h2><p>%s</p><p>%s</p></section>' % (
        esc(t('about_h', lang)), esc(t('about_p1', lang)), esc(t('about_p2', lang))))
    out.append('\n    </main>\n    %s\n</body>\n</html>\n' % footer)
    return '\n'.join(x for x in out if x)


# --- the chemicals index of each language ------------------------------------

def patch_index(lang, pages, chems, changed, check):
    """Rebuild the A-Z list inside chemicals/[<lang>/]index.html from the
    registry, and replace the "1,650+" claim with the number of pages listed."""
    import re
    import unicodedata
    rel = chem_base(lang).lstrip('/') + 'index.html'
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        page = f.read()
    m = re.search(r'(<div[^>]*id="chemicalsList"[^>]*>)[\s\S]*?(</div>\s*</section>)', page)
    if not m:
        print('no list in', rel)
        return

    def key(name):
        flat = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
        return flat.lstrip('0123456789-,. ') or name.lower()

    groups = OrderedDict()
    for slug, p in sorted(pages.items(), key=lambda x: key(x[1]['names'][lang])):
        name = p['names'][lang]
        letter = key(name)[:1].upper() if lang != 'zh' else '#'
        groups.setdefault(letter, []).append((slug, name, chems[p['source']]))
    out = []
    for letter, items in groups.items():
        links = []
        for slug, name, chem in items:
            pv = primary_variant(chem)
            n_a = sum(1 for r in pv['ratings'].values() if r.get('w20') == 'A')
            n_d = sum(1 for r in pv['ratings'].values() if r.get('w20') == 'D')
            links.append(
                '<a href="%s" class="chem-link bg-white px-4 py-3 rounded-lg border border-gray-200 '
                'hover:border-emerald-500 hover:shadow-md transition-all text-sm" data-name="%s">%s'
                '<span class="block text-xs text-gray-500">%s%d A · %d D</span></a>' % (
                    chem_url(lang, slug), esc(' '.join([name, chem['name_en'], chem['cas']]).lower()),
                    esc(name), esc(chem['cas'] + ' · ') if chem['cas'] else '', n_a, n_d))
        head_html = ('<h2 class="text-2xl font-bold text-emerald-600 mb-4 border-b pb-2">%s</h2>' % letter
                     if lang != 'zh' else '')
        out.append('<div class="mb-8 letter-section">%s<div class="grid grid-cols-2 md:grid-cols-3 '
                   'lg:grid-cols-4 gap-3">\n%s\n</div></div>' % (head_html, '\n'.join(links)))
    new = page[:m.start()] + m.group(1) + '\n' + '\n'.join(out) + '\n' + m.group(2) + page[m.end():]
    new = re.sub(r'1[,.\u00a0\u202f ]?65[01]\+', str(len(pages)), new)
    write(rel, new, changed, check)


def patch_about(pages, chems, changed, check):
    """List every corrected and disputed value on the About pages."""
    import re
    scale = {'en': 'Source values use the scale 1 (very good) to 4 (not resistant).',
             'de': t('source_scale', 'de'), 'es': t('source_scale', 'es')}
    by_source = {p['source']: s for s, p in pages.items()}
    for lang, rel in (('en', 'about/index.html'), ('de', 'de-about/index.html'), ('es', 'es-about/index.html')):
        with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
            page = f.read()
        rows = []
        for chem in chems.values():
            for v in chem['variants']:
                for c in v['corrections']:
                    slug = by_source.get(chem['name_de'])
                    if slug:
                        name = '<a href="%s" class="text-emerald-600 underline">%s</a>' % (
                            chem_url(lang, slug), esc(pages[slug]['names'][lang]))
                    else:
                        name = esc(chem['name_de'] if lang == 'de' else chem['name_en'])
                    key = 'disputed_row' if c['kind'] == 'disputed' else 'corrections_row'
                    line = t(key, lang, mat=material_name(c['material'], lang), conc=variant_label(v, lang),
                             old=c['source_value'], new=c.get('value', ''))
                    refs = ' '.join('<a href="%s" rel="nofollow noopener" class="underline">[%d]</a>'
                                    % (esc(u), i + 1) for i, u in enumerate(c['refs']))
                    reason = c.get('reasons', {}).get(lang) or c['reason']
                    rows.append('<li>%s. %s %s %s</li>' % (name, esc(line), esc(reason), refs))
        block = ('<!-- corrections:start -->\n<ul class="text-sm text-gray-600 space-y-2 list-disc pl-5">\n%s\n</ul>\n'
                 '<p class="text-xs text-gray-500 mt-3">%s</p>\n'
                 '                <!-- corrections:end -->') % ('\n'.join(rows), esc(scale[lang]))
        new = re.sub(r'<!-- corrections:start -->[\s\S]*?<!-- corrections:end -->', lambda _: block, page)
        write(rel, new, changed, check)


def main():
    check = '--check' in sys.argv
    with open(os.path.join(ROOT, 'data', 'chemical_pages.json'), encoding='utf-8') as f:
        registry = json.load(f)['pages']
    chems, stats = rd.load()
    pages = OrderedDict((s, p) for s, p in registry.items() if 'redirect_to' not in p)
    redirects = {s: p['redirect_to'] for s, p in registry.items() if 'redirect_to' in p}
    for slug, p in pages.items():
        if p['source'] not in chems:
            sys.exit('data/chemical_pages.json: %s points at unknown source %r' % (slug, p['source']))
    chrome = load_chrome()
    similar = similar_chemicals(pages, chems)

    changed = []
    counts = {'hub': 0, 'pair': 0, 'stub': 0}
    patch_about(pages, chems, changed, check)
    for lang in LANGS:
        patch_index(lang, pages, chems, changed, check)
        for slug, page in pages.items():
            chem = chems[page['source']]
            write(chem_url(lang, slug).lstrip('/') + 'index.html',
                  chemical_page(lang, slug, page, chem, chrome, similar, pages), changed, check)
            counts['hub'] += 1
            for mat in rd.MATERIALS:
                write(pair_url(lang, slug, mat).lstrip('/') + 'index.html',
                      pair_page(lang, slug, page, chem, mat, chrome), changed, check)
                counts['pair'] += 1
        for slug, target in redirects.items():
            write(chem_url(lang, slug).lstrip('/') + 'index.html', stub(chem_url(lang, target)),
                  changed, check)
            counts['stub'] += 1
            for mat in rd.MATERIALS:
                write(pair_url(lang, slug, mat).lstrip('/') + 'index.html',
                      stub(pair_url(lang, target, mat)), changed, check)
                counts['stub'] += 1
    print('chemical pages %(hub)d, pair pages %(pair)d, redirect stubs %(stub)d' % counts)
    print('%s %d files' % ('would change' if check else 'wrote', len(changed)))


if __name__ == '__main__':
    main()
