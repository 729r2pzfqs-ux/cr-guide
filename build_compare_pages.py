#!/usr/bin/env python3
"""Build the material comparison pages, compare/<a>-vs-<b>/, in en, de and es.

    python3 build_compare_pages.py            # write
    python3 build_compare_pages.py --check    # report only

Every page is computed from resistance_data: how often the two materials get
the same rating, which one is rated better by chemical class, and the rows
where they differ most. It also rewrites the list of comparisons on the
compare index of each language.

ETFE vs ECTFE is not a comparison this data can make: the source rates ECTFE
and ETFE in one column. That page is a redirect to the ECTFE/ETFE material
page. The French, Portuguese and Chinese comparison pages are not indexed and
are left as they are, apart from that redirect.
"""

import os
import re
import sys

import class_stats as cs
import diagrams
import resistance_data as rd
from build_chemical_pages import (ROOT, SITE, breadcrumb_ld, esc, grade_span, head, home_url,
                                  legend, material_url, variant_label, write)
from page_i18n import conc_label, material_full, material_name, material_note, t
from redirect_stub import stub

LANGS = ['en', 'de', 'es']
CONTENT_UPDATED = '2026-10-08'
MAX_DIFF_ROWS = 40

# (material a, material b, {lang: slug}); slugs of the four older pages are kept
PAIRS = [
    ('PTFE', 'FEP', {'en': 'ptfe-vs-fep'}),
    ('NBR', 'EPDM', {'en': 'nbr-vs-epdm'}),
    ('HDPE', 'PVDF', {'en': 'hdpe-vs-pvdf'}),
    ('PSU', 'PVDF', {'en': 'polysulfone-vs-pvdf', 'de': 'polysulfon-vs-pvdf', 'es': 'polisulfona-vs-pvdf'}),
    ('EPDM', 'FPM', {'en': 'epdm-vs-viton'}),
    ('NBR', 'FPM', {'en': 'nbr-vs-viton'}),
    ('V2A', 'V4A', {'en': 'ss304-vs-ss316'}),
    ('AL', 'V4A', {'en': 'aluminium-vs-ss316'}),
    ('HDPE', 'PP', {'en': 'hdpe-vs-pp'}),
    ('HDPE', 'LDPE', {'en': 'hdpe-vs-ldpe'}),
    ('PVC_HART', 'PP', {'en': 'pvc-vs-pp'}),
    ('PTFE', 'PVDF', {'en': 'ptfe-vs-pvdf'}),
    ('PC', 'PETG', {'en': 'polycarbonate-vs-petg'}),
    ('PA', 'POM', {'en': 'nylon-vs-acetal'}),
]

S = {
    'compare': {'en': 'Compare', 'de': 'Vergleich', 'es': 'Comparar'},
    'h1': {'en': '{a} vs {b}: Chemical Resistance Compared',
           'de': '{a} und {b}: Chemische Beständigkeit im Vergleich',
           'es': '{a} y {b}: comparación de resistencia química'},
    'title': {'en': '{a} vs {b}: Chemical Resistance Compared',
              'de': '{a} vs. {b}: Beständigkeit im Vergleich',
              'es': '{a} vs {b}: resistencia química comparada'},
    'lead': {
        'en': 'Of {n} source rows rated for both materials at 20 °C, {same} ({p} %) have the same rating. {a} is rated better in {ka} rows and {b} in {kb}.',
        'de': 'Von {n} Quellzeilen, die bei 20 °C für beide Werkstoffe bewertet sind, haben {same} ({p} %) die gleiche Bewertung. {a} ist in {ka} Zeilen besser bewertet, {b} in {kb}.',
        'es': 'De {n} filas de la fuente clasificadas para ambos materiales a 20 °C, {same} ({p} %) tienen la misma clasificación. {a} tiene mejor clasificación en {ka} filas y {b} en {kb}.'},
    'row_note': {
        'en': 'A row is one chemical at one concentration.',
        'de': 'Eine Zeile ist eine Chemikalie bei einer Konzentration.',
        'es': 'Una fila es un producto químico a una concentración.'},
    'desc_lead': {
        'en': '{a} and {b} have the same rating in {same} of {n} rows.',
        'de': '{a} und {b} sind in {same} von {n} Zeilen gleich bewertet.',
        'es': '{a} y {b} tienen la misma clasificación en {same} de {n} filas.'},
    'desc_better': {'en': '{m} is rated better with {c}.', 'de': '{m} ist besser bei: {c}.',
                    'es': '{m} resiste mejor: {c}.'},
    'desc_tail': {'en': 'By chemical class, 20 °C.', 'de': 'Nach Chemikalienklasse, 20 °C.',
                  'es': 'Por clase química, 20 °C.'},
    'summary_h': {'en': 'Summary', 'de': 'Zusammenfassung', 'es': 'Resumen'},
    'leads': {'en': '{m} is rated better with', 'de': '{m} ist besser bewertet bei',
              'es': '{m} tiene mejor clasificación con'},
    'close': {'en': 'Within 10 points of each other', 'de': 'Höchstens 10 Punkte Unterschied',
              'es': 'Diferencia de 10 puntos o menos'},
    'points': {'en': '{c} (+{d} points)', 'de': '{c} (+{d} Punkte)', 'es': '{c} (+{d} puntos)'},
    'points_note': {
        'en': 'Points are the difference in the share of rows rated A or B.',
        'de': 'Punkte sind die Differenz im Anteil der Zeilen mit Bewertung A oder B.',
        'es': 'Los puntos son la diferencia en la proporción de filas con clasificación A o B.'},
    'materials_h': {'en': 'The two materials', 'de': 'Die beiden Werkstoffe', 'es': 'Los dos materiales'},
    'rated_rows': {'en': 'Rated rows', 'de': 'Bewertete Zeilen', 'es': 'Filas clasificadas'},
    'full_chart': {'en': 'All chemicals for {m}', 'de': 'Alle Chemikalien für {m}',
                   'es': 'Todos los productos químicos para {m}'},
    'class_h': {'en': 'By chemical class', 'de': 'Nach Chemikalienklasse', 'es': 'Por clase química'},
    'class_col': {'en': 'Chemical class', 'de': 'Chemikalienklasse', 'es': 'Clase química'},
    'share_col': {'en': '{m}: rated A or B', 'de': '{m}: Bewertung A oder B',
                  'es': '{m}: clasificación A o B'},
    'rows_col': {'en': 'rows', 'de': 'Zeilen', 'es': 'filas'},
    'diff_h': {'en': 'Where the ratings differ most', 'de': 'Wo sich die Bewertungen am stärksten unterscheiden',
               'es': 'Dónde más difieren las clasificaciones'},
    'diff_p': {
        'en': 'Rows where the two ratings at 20 °C are at least two grades apart: {k} in total{shown}.',
        'de': 'Zeilen, in denen die beiden Bewertungen bei 20 °C mindestens zwei Stufen auseinanderliegen: insgesamt {k}{shown}.',
        'es': 'Filas en las que las dos clasificaciones a 20 °C difieren al menos dos grados: {k} en total{shown}.'},
    'diff_shown': {'en': ', the first {m} shown', 'de': ', die ersten {m} werden gezeigt',
                   'es': ', se muestran las primeras {m}'},
    'diff_none': {
        'en': 'No row has ratings more than one grade apart.',
        'de': 'In keiner Zeile liegen die Bewertungen mehr als eine Stufe auseinander.',
        'es': 'En ninguna fila las clasificaciones difieren más de un grado.'},
    'chemical': {'en': 'Chemical', 'de': 'Chemikalie', 'es': 'Producto químico'},
    'more_h': {'en': 'More comparisons', 'de': 'Weitere Vergleiche', 'es': 'Más comparaciones'},
    'vs': {'en': 'vs', 'de': 'vs.', 'es': 'vs'},
    'card': {'en': 'Same rating in {p} % of {n} rows', 'de': 'Gleiche Bewertung in {p} % von {n} Zeilen',
             'es': 'Misma clasificación en el {p} % de {n} filas'},
}


def s(key, lang, **kw):
    text = S[key][lang]
    return text.format(**kw) if kw else text


def base(lang):
    return '/compare/' if lang == 'en' else '/%s/compare/' % lang


def slug_of(pair, lang):
    return pair[2].get(lang, pair[2]['en'])


def url_of(pair, lang):
    return '%s%s/' % (base(lang), slug_of(pair, lang))


def chrome(lang):
    with open(os.path.join(ROOT, base(lang).lstrip('/'), 'index.html'), encoding='utf-8') as f:
        page = f.read()
    header = re.search(r'<header[\s\S]*?</header>\s*<script>[\s\S]*?</script>', page)
    footer = re.search(r'<footer[\s\S]*?</footer>', page)
    header = header.group(0) if header else ''
    footer = footer.group(0) if footer else ''
    if lang != 'en':
        header = header.replace('href="/%s/about/"' % lang, 'href="/%s-about/"' % lang)
    return header, footer


def chem_links(lang):
    import json
    with open(os.path.join(ROOT, 'data', 'chemical_pages.json'), encoding='utf-8') as f:
        pages = json.load(f)['pages']
    root = '/chemicals/' if lang == 'en' else '/chemicals/%s/' % lang
    return {p['source']: ('%s%s/' % (root, slug), p['names'][lang])
            for slug, p in pages.items() if 'redirect_to' not in p}


def class_gaps(pa, pb):
    """[(points, class)] where points > 0 means the first material leads."""
    out = []
    for cls in cs.CLASSES:
        if pa[cls]['n'] >= cs.MIN_ROWS and pb[cls]['n'] >= cs.MIN_ROWS:
            out.append((round(100 * cs.good_share(pa[cls])) - round(100 * cs.good_share(pb[cls])), cls))
    return out


COMPARE_FAQ = {
    'q_more_resistant': {
        'en': 'Is {a} or {b} more chemical-resistant?',
        'de': 'Ist {a} oder {b} chemisch beständiger?',
        'es': '¿Es más resistente químicamente {a} o {b}?',
    },
    'a_more_resistant': {
        'en': 'Of {n} chemicals rated for both materials at 20 °C, {a} and {b} share the same rating in {same} rows ({p} %). {a} is rated better in {ka} rows and {b} in {kb} rows.',
        'de': 'Von {n} Chemikalien, die bei 20 °C für beide Werkstoffe bewertet sind, haben {a} und {b} in {same} Zeilen ({p} %) die gleiche Bewertung. {a} ist in {ka} Zeilen besser, {b} in {kb}.',
        'es': 'De {n} productos químicos clasificados para ambos materiales a 20 °C, {a} y {b} comparten la misma clasificación en {same} filas ({p} %). {a} tiene mejor clasificación en {ka} filas y {b} en {kb}.',
    },
    'q_acids': {
        'en': 'Which material is better for acids, {a} or {b}?',
        'de': 'Welcher Werkstoff ist besser für Säuren, {a} oder {b}?',
        'es': '¿Qué material es mejor para ácidos, {a} o {b}?',
    },
    'q_solvents': {
        'en': 'Which material is better for solvents, {a} or {b}?',
        'de': 'Welcher Werkstoff ist besser für Lösungsmittel, {a} oder {b}?',
        'es': '¿Qué material es mejor para disolventes, {a} o {b}?',
    },
    'a_class_lead': {
        'en': 'For {cls}, {winner} has a higher share of A/B ratings: {wp} % rated A or B ({wn} rows) vs {lp} % for {loser} ({ln} rows).',
        'de': 'Bei {cls} hat {winner} einen höheren Anteil an A/B-Bewertungen: {wp} % mit A oder B ({wn} Zeilen) gegenüber {lp} % für {loser} ({ln} Zeilen).',
        'es': 'Para {cls}, {winner} tiene mayor proporción de clasificaciones A/B: {wp} % con A o B ({wn} filas) frente a {lp} % para {loser} ({ln} filas).',
    },
    'a_class_close': {
        'en': 'For {cls}, both materials perform similarly — the difference in A/B rated rows is 10 percentage points or less.',
        'de': 'Bei {cls} sind beide Werkstoffe vergleichbar – der Unterschied bei den A/B-Bewertungen beträgt höchstens 10 Prozentpunkte.',
        'es': 'Para {cls}, ambos materiales se comportan de forma similar: la diferencia en filas con clasificación A/B es de 10 puntos porcentuales o menos.',
    },
    'q_compare': {
        'en': 'How do {a} and {b} compare for chemical resistance?',
        'de': 'Wie vergleichen sich {a} und {b} bei der chemischen Beständigkeit?',
        'es': '¿Cómo se comparan {a} y {b} en resistencia química?',
    },
    'a_compare': {
        'en': 'Based on {n} chemicals tested for both: {a} is rated better with {a_classes}. {b} is rated better with {b_classes}. They perform similarly with {close_classes}.',
        'de': 'Basierend auf {n} Chemikalien, die für beide getestet wurden: {a} ist besser bei {a_classes}. {b} ist besser bei {b_classes}. Vergleichbar sind sie bei {close_classes}.',
        'es': 'Según {n} productos químicos ensayados para ambos: {a} es mejor con {a_classes}. {b} es mejor con {b_classes}. Similares con {close_classes}.',
    },
    'faq_h': {
        'en': 'Frequently Asked Questions',
        'de': 'Häufig gestellte Fragen',
        'es': 'Preguntas frecuentes',
    },
}


def compare_faq(lang, na, nb, st, pa, pb, gaps, a_leads, b_leads, close_list):
    """Generate FAQ items for a comparison page. Returns (faq_items, faq_html)."""
    faqs = []
    pct = round(100 * st['same'] / st['n']) if st['n'] else 0

    # Q1: Which is more resistant?
    q = COMPARE_FAQ['q_more_resistant'][lang].format(a=na, b=nb)
    a = COMPARE_FAQ['a_more_resistant'][lang].format(
        a=na, b=nb, n=st['n'], same=st['same'], p=pct,
        ka=st['a_better'], kb=st['b_better'])
    faqs.append((q, a))

    # Q2: Which is better for acids?
    acid_classes = [c for c in ['inorganic_acid', 'organic_acid'] if c in {g[1] for g in gaps}]
    for cls_key, q_key in [('inorganic_acid', 'q_acids'), ('organic_solvent', 'q_solvents')]:
        cls_gaps = [g for g in gaps if g[1] == cls_key]
        if cls_gaps:
            g = cls_gaps[0]
            q = COMPARE_FAQ[q_key][lang].format(a=na, b=nb)
            prof_a, prof_b = pa[cls_key], pb[cls_key]
            if abs(g[0]) <= 10:
                a = COMPARE_FAQ['a_class_close'][lang].format(cls=cs.class_name(cls_key, lang))
            else:
                winner, loser = (na, nb) if g[0] > 0 else (nb, na)
                wp_prof, lp_prof = (prof_a, prof_b) if g[0] > 0 else (prof_b, prof_a)
                a = COMPARE_FAQ['a_class_lead'][lang].format(
                    cls=cs.class_name(cls_key, lang), winner=winner, loser=loser,
                    wp=round(100 * cs.good_share(wp_prof)), wn=wp_prof['n'],
                    lp=round(100 * cs.good_share(lp_prof)), ln=lp_prof['n'])
            faqs.append((q, a))

    # Q3: Overall comparison
    if a_leads or b_leads or close_list:
        q = COMPARE_FAQ['q_compare'][lang].format(a=na, b=nb)
        a_cls = ', '.join(cs.class_name(c, lang) for _, c in a_leads[:4]) if a_leads else '–'
        b_cls = ', '.join(cs.class_name(c, lang) for _, c in b_leads[:4]) if b_leads else '–'
        c_cls = ', '.join(cs.class_name(c, lang) for c in close_list[:4]) if close_list else '–'
        a = COMPARE_FAQ['a_compare'][lang].format(
            n=st['n'], a=na, b=nb, a_classes=a_cls, b_classes=b_cls, close_classes=c_cls)
        faqs.append((q, a))

    if not faqs:
        return [], ''

    html_items = []
    for q, a in faqs:
        html_items.append(
            '<details><summary style="cursor:pointer;font-weight:600;color:#111827;padding:.5rem 0">'
            '%s</summary><p style="color:#374151;padding:0 0 .75rem;margin:0">%s</p></details>'
            % (esc(q), esc(a)))
    faq_html = ('<section class="cr-card"><h2>%s</h2>%s</section>'
                % (esc(COMPARE_FAQ['faq_h'][lang]), '\n'.join(html_items)))
    return faqs, faq_html


def page(pair, lang, header, footer, links, trans):
    a, b, _ = pair
    na, nb = material_name(a, lang), material_name(b, lang)
    pa, pb = cs.material_profile(a), cs.material_profile(b)
    st = cs.pair_stats(a, b)
    gaps = class_gaps(pa, pb)
    a_leads = sorted([g for g in gaps if g[0] > 10], reverse=True)
    b_leads = sorted([(-g[0], g[1]) for g in gaps if g[0] < -10], reverse=True)
    close = [g[1] for g in gaps if abs(g[0]) <= 10]
    pct = round(100 * st['same'] / st['n']) if st['n'] else 0

    title = s('title', lang, a=na, b=nb)
    desc = s('desc_lead', lang, a=na, b=nb, same=st['same'], n=st['n'])
    for m, lead in ((na, a_leads), (nb, b_leads)):
        if lead:
            add = ' ' + s('desc_better', lang, m=m, c=(cs.class_name(lead[0][1], lang, short=True) if lang == 'de'
                                                    else cs.class_name(lead[0][1], lang, short=True).lower()))
            if len(desc) + len(add) <= 140:
                desc += add
    desc += ' ' + s('desc_tail', lang)
    url = SITE + url_of(pair, lang)
    alternates = [('x-default', SITE + url_of(pair, 'en'))] + [(l, SITE + url_of(pair, l)) for l in LANGS]
    crumbs = [(t('home', lang), home_url(lang)), (s('compare', lang), base(lang)),
              ('%s %s %s' % (na, s('vs', lang), nb), url_of(pair, lang))]
    ld = [breadcrumb_ld(crumbs), {
        '@context': 'https://schema.org', '@type': 'WebPage', 'name': s('h1', lang, a=na, b=nb),
        'description': desc, 'url': url, 'inLanguage': lang, 'dateModified': CONTENT_UPDATED,
        'isPartOf': {'@type': 'WebSite', 'name': 'ChemicalResistance.org', 'url': SITE + '/'},
    }]
    faq_items, faq_html = compare_faq(lang, na, nb, st, pa, pb, gaps, a_leads, b_leads, close)
    if faq_items:
        ld.append({
            '@context': 'https://schema.org', '@type': 'FAQPage',
            'mainEntity': [{'@type': 'Question', 'name': q,
                            'acceptedAnswer': {'@type': 'Answer', 'text': a}}
                           for q, a in faq_items],
        })
    diagrams.reset_ids()
    out = [head(lang, title, desc, url, '', alternates, ld), header]
    out.append('''
    <section class="bg-gradient-to-b from-emerald-50 to-white px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <nav class="text-sm text-emerald-600 mb-3 cr-crumb" aria-label="Breadcrumb">
                <a href="%s">%s</a> › <a href="%s">%s</a> › %s
            </nav>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">%s</h1>
            <p class="text-gray-600">%s %s</p>
        </div>
    </section>
    <main class="max-w-4xl mx-auto px-4 py-8">
''' % (home_url(lang), esc(t('home', lang)), base(lang), esc(s('compare', lang)),
       esc('%s %s %s' % (na, s('vs', lang), nb)), esc(s('h1', lang, a=na, b=nb)),
       esc(s('lead', lang, n=st['n'], same=st['same'], p=pct, a=na, b=nb, ka=st['a_better'],
             kb=st['b_better'])), esc(s('row_note', lang))))

    # summary
    rows = []
    for m, lead in ((na, a_leads), (nb, b_leads)):
        if lead:
            rows.append((s('leads', lang, m=m), '; '.join(
                esc(s('points', lang, c=cs.class_name(c, lang), d=d)) for d, c in lead)))
    if close:
        rows.append((s('close', lang), '; '.join(esc(cs.class_name(c, lang)) for c in close)))
    body = ''.join('<dt>%s</dt><dd>%s</dd>' % (esc(k), v) for k, v in rows)
    out.append('<section class="cr-card"><h2>%s</h2><dl class="cr-list">%s</dl><p class="cr-sub" style="margin-top:.75rem">%s</p></section>' % (
        esc(s('summary_h', lang)), body, esc(s('points_note', lang))))

    # the two materials
    cards = ''
    for code, name, prof in ((a, na, pa), (b, nb, pb)):
        al = prof['all']
        shares = ', '.join('%s %d %%' % (g, round(100 * al[g] / al['n'])) for g in 'ABCD') if al['n'] else ''
        cards += ('<div><h3 style="font-size:1.1rem;font-weight:700;color:#111827;margin:0">%s</h3>'
                  '<p class="cr-sub">%s</p><p>%s</p><p class="cr-sub">%s: %d. %s</p>'
                  '<p><a href="%s">%s</a></p></div>') % (
            esc(name), esc(material_full(code, lang)), esc(material_note(code, lang) or ''),
            esc(s('rated_rows', lang)), al['n'], esc(shares), material_url(lang, code),
            esc(s('full_chart', lang, m=name)))
    out.append('<section class="cr-card"><h2>%s</h2><div class="cr-figs">%s</div></section>' % (
        esc(s('materials_h', lang)), cards))

    # figures
    figs = ''
    ov = diagrams.overlay(lang, na, nb, pa, pb, cs.class_name, cs.MIN_ROWS, cs.good_share)
    if ov:
        figs += '<div class="cr-fig"><h3>%s</h3>%s</div>' % (
            esc(t('fig_overlay_h', lang)),
            diagrams.figure(ov, t('fig_overlay_cap', lang, n=cs.MIN_ROWS), diagrams.series_key(na, nb)))
    figs += '<div class="cr-fig"><h3>%s</h3>%s</div>' % (
        esc(t('fig_grid_h', lang)),
        diagrams.figure(diagrams.agreement_grid(lang, na, nb, st['grid']), t('fig_grid_cap', lang)))
    out.append('<section class="cr-card"><div class="cr-figs">%s</div><p class="cr-sub" style="margin-top:1rem">%s</p></section>' % (
        figs, esc(t('class_note', lang))))

    # by class, as a table
    body = ''
    for cls in cs.CLASSES:
        if pa[cls]['n'] < cs.MIN_ROWS and pb[cls]['n'] < cs.MIN_ROWS:
            continue
        cells = ''
        for prof in (pa, pb):
            if prof[cls]['n'] < cs.MIN_ROWS:
                cells += '<td class="c">–</td>'
            else:
                cells += '<td class="c">%d %% <span class="fl">(%d %s)</span></td>' % (
                    round(100 * cs.good_share(prof[cls])), prof[cls]['n'], esc(s('rows_col', lang)))
        body += '<tr><th scope="row">%s</th>%s</tr>' % (esc(cs.class_name(cls, lang)), cells)
    out.append(('<section class="cr-card cr-noads"><h2>%s</h2><div class="cr-scroll"><table class="cr-tbl"><thead><tr>'
                '<th scope="col">%s</th><th class="c" scope="col">%s</th><th class="c" scope="col">%s</th>'
                '</tr></thead><tbody>%s</tbody></table></div></section>') % (
        esc(s('class_h', lang)), esc(s('class_col', lang)), esc(s('share_col', lang, m=na)),
        esc(s('share_col', lang, m=nb)), body))

    # largest differences
    big = sorted([d for d in st['diffs'] if abs(d[0]) >= 2],
                 key=lambda d: (-abs(d[0]), d[1]['name_en'].lower(), d[2]['conc']))
    if big:
        body = ''
        for d, chem, v, _cls in big[:MAX_DIFF_ROWS]:
            link = links.get(chem['name_de'])
            if link:
                name = '<a href="%s">%s</a>' % (link[0], esc(link[1]))
            elif lang == 'de':
                name = esc(chem['name_de'])
            elif lang == 'en':
                name = esc(chem['name_en'])
            else:
                name = esc(trans.get(chem['name_de'].lower(), chem['name_en']))
            ra, rb = v['ratings'][a], v['ratings'][b]
            body += '<tr><th scope="row">%s</th><td>%s</td><td class="c">%s</td><td class="c">%s</td></tr>' % (
                name, esc(conc_label(v['conc'], lang)), grade_span(ra['c20'], ra['w20']),
                grade_span(rb['c20'], rb['w20']))
        shown = s('diff_shown', lang, m=MAX_DIFF_ROWS) if len(big) > MAX_DIFF_ROWS else ''
        out.append(('<section class="cr-card cr-noads"><h2>%s</h2><p>%s</p><div class="cr-scroll" id="compat-table-zone">'
                    '<table class="cr-tbl"><thead><tr><th scope="col">%s</th><th scope="col">%s</th>'
                    '<th class="c" scope="col">%s</th><th class="c" scope="col">%s</th></tr></thead>'
                    '<tbody>%s</tbody></table></div></section>') % (
            esc(s('diff_h', lang)), esc(s('diff_p', lang, k=len(big), shown=shown)),
            esc(s('chemical', lang)), esc(t('concentration', lang)), esc(na), esc(nb), body))
    else:
        out.append('<section class="cr-card"><h2>%s</h2><p>%s</p></section>' % (
            esc(s('diff_h', lang)), esc(s('diff_none', lang))))

    out.append('<section class="cr-card"><h2>%s</h2>%s</section>' % (esc(t('legend_h', lang)), legend(lang)))

    related = [p for p in PAIRS if p is not pair and ({p[0], p[1]} & {a, b})]
    related += [p for p in PAIRS if p is not pair and p not in related]
    more = ''.join('<a href="%s">%s %s %s</a>' % (
        url_of(p, lang), esc(material_name(p[0], lang)), s('vs', lang), esc(material_name(p[1], lang)))
        for p in related)
    out.append('<section class="cr-card"><h2>%s</h2><div class="cr-links">%s</div></section>' % (
        esc(s('more_h', lang)), more))
    if faq_html:
        out.append(faq_html)
    out.append('<section class="cr-card"><h2>%s</h2><p>%s</p><p>%s</p></section>' % (
        esc(t('about_h', lang)), esc(t('about_p1', lang)), esc(t('about_p2', lang))))
    out.append('\n    </main>\n    %s\n</body>\n</html>\n' % footer)
    return '\n'.join(x for x in out if x)


def patch_index(lang, changed, check):
    """The list of comparisons on the compare index."""
    rel = base(lang).lstrip('/') + 'index.html'
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'(<a href="[^"]*-vs-[^"]*"[^>]*>[\s\S]*?</a>\s*)+', text)
    if not m:
        print('no comparison list in', rel)
        return
    cards = ''
    for p in PAIRS:
        st = cs.pair_stats(p[0], p[1])
        cards += ('<a href="%s" class="bg-white p-6 rounded-xl border border-gray-200 hover:border-blue-300 '
                  'hover:shadow-sm transition-all">\n'
                  '                    <h3 class="text-lg font-bold text-gray-900 mb-1">%s %s %s</h3>\n'
                  '                    <p class="text-sm text-gray-600">%s</p>\n'
                  '                </a>\n                ') % (
            url_of(p, lang), esc(material_name(p[0], lang)), s('vs', lang), esc(material_name(p[1], lang)),
            esc(s('card', lang, p=round(100 * st['same'] / st['n']), n=st['n'])))
    write(rel, text[:m.start()] + cards + text[m.end():], changed, check)


def main():
    from build_material_tables import load_translations
    check = '--check' in sys.argv
    changed = []
    for lang in LANGS:
        header, footer = chrome(lang)
        links = chem_links(lang)
        trans = load_translations(lang)
        for pair in PAIRS:
            write(url_of(pair, lang).lstrip('/') + 'index.html',
                  page(pair, lang, header, footer, links, trans), changed, check)
        patch_index(lang, changed, check)
    for lang in ['en', 'de', 'es', 'fr', 'pt', 'zh']:
        rel = base(lang).lstrip('/') + 'etfe-vs-ectfe/index.html'
        if os.path.exists(os.path.join(ROOT, rel)):
            write(rel, stub(material_url(lang, 'ECTFE_ETFE')), changed, check)
    print('%d comparison pages in %d languages; %s %d files' % (
        len(PAIRS), len(LANGS), 'would change' if check else 'wrote', len(changed)))


if __name__ == '__main__':
    main()
