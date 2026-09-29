#!/usr/bin/env python3
"""Figures and data-driven sections on the tool and index pages.

    python3 build_tool_pages.py            # rewrite
    python3 build_tool_pages.py --check    # report only

  * viscosity: a logarithmic scale of common liquids, and the table written
    into the page where the names exist in the page language (en, de),
  * storage compatibility: the segregation rules of the checker as a matrix,
  * materials index: which materials suit which chemical class,
  * charts index: share rated A or B by material family and chemical class,
  * silicone material pages: a notice that the source rates silicone for very
    few chemicals.

Each block sits between HTML comment markers and is replaced on every run.
"""

import html
import json
import os
import re
import sys

import class_stats as cs
import diagrams
import resistance_data as rd
from build_material_tables import FIG_STYLE
from page_i18n import material_name, t

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ['en', 'de', 'es', 'fr', 'pt', 'zh']

# liquids on the viscosity scale: English name in data/viscosity.json -> names
SCALE = [
    ('Milk', {'de': 'Milch', 'es': 'Leche'}),
    ('Transformer Oil', {'de': 'Transformatorenöl', 'es': 'Aceite de transformador'}),
    ('Glycol', {'de': 'Glykol', 'es': 'Glicol'}),
    ('Sodium Hydroxide 50%', {'en': 'Sodium hydroxide 50 %', 'de': 'Natronlauge 50 %', 'es': 'Hidróxido de sodio 50 %'}),
    ('Soybean Oil', {'de': 'Sojaöl', 'es': 'Aceite de soja'}),
    ('Dipropylene Glycol', {'de': 'Dipropylenglykol', 'es': 'Dipropilenglicol'}),
    ('Hydraulic Oil HLP 46', {'de': 'Hydrauliköl HLP 46', 'es': 'Aceite hidráulico HLP 46'}),
    ('Rapeseed Oil', {'de': 'Rapsöl', 'es': 'Aceite de colza'}),
    ('Latex Emulsion', {'de': 'Latexemulsion', 'es': 'Emulsión de látex'}),
    ('Hydraulic Oil HLP 100', {'de': 'Hydrauliköl HLP 100', 'es': 'Aceite hidráulico HLP 100'}),
    ('Motor Oil SAE 15W40', {'de': 'Motoröl SAE 15W40', 'es': 'Aceite de motor SAE 15W40'}),
    ('Machine Oil, Heavy', {'de': 'Maschinenöl, schwer', 'es': 'Aceite de máquina, pesado'}),
    ('Gear Oil SAE 90', {'de': 'Getriebeöl SAE 90', 'es': 'Aceite de engranajes SAE 90'}),
    ('Glycerin 100%', {'en': 'Glycerin 100 %', 'de': 'Glycerin 100 %', 'es': 'Glicerina 100 %'}),
    ('Mayonnaise', {'de': 'Mayonnaise', 'es': 'Mayonesa'}),
    ('Gear Oil SAE 140', {'de': 'Getriebeöl SAE 140', 'es': 'Aceite de engranajes SAE 140'}),
    ('Shampoo', {'de': 'Shampoo', 'es': 'Champú'}),
    ('Cocoa Mass', {'de': 'Kakaomasse', 'es': 'Pasta de cacao'}),
    ('Hand Cream', {'de': 'Handcreme', 'es': 'Crema de manos'}),
    ('Molasses 80°Bx', {'en': 'Molasses 80 °Bx', 'de': 'Melasse 80 °Bx', 'es': 'Melaza 80 °Bx'}),
    ('Polymer Solution', {'de': 'Polymerlösung', 'es': 'Solución de polímero'}),
    ('Molasses 85°Bx', {'en': 'Molasses 85 °Bx', 'de': 'Melasse 85 °Bx', 'es': 'Melaza 85 °Bx'}),
]

S = {
    'visc_h': {'en': 'Viscosity of common liquids at 20 °C', 'de': 'Viskosität gängiger Flüssigkeiten bei 20 °C',
               'es': 'Viscosidad de líquidos comunes a 20 °C'},
    'visc_cap': {
        'en': 'Dynamic viscosity in mPa·s on a logarithmic scale: each gridline is ten times the one before it. Values from the viscosity list of Bürkle GmbH; the full list is in the table below.',
        'de': 'Dynamische Viskosität in mPa·s auf logarithmischer Skala: Jede Gitterlinie entspricht dem Zehnfachen der vorherigen. Werte aus der Viskositätsliste der Bürkle GmbH; die vollständige Liste steht in der Tabelle unten.',
        'es': 'Viscosidad dinámica en mPa·s en escala logarítmica: cada línea equivale a diez veces la anterior. Valores de la lista de viscosidad de Bürkle GmbH; la lista completa está en la tabla de abajo.'},
    'store_h': {'en': 'Segregation rules at a glance', 'de': 'Trennregeln auf einen Blick',
                'es': 'Reglas de segregación de un vistazo', 'fr': 'Règles de séparation en bref',
                'pt': 'Regras de segregação em resumo'},
    'store_cap': {
        'en': 'The rules of the table above in a form that fits a phone screen. The safety data sheet of each product takes precedence.',
        'de': 'Die Regeln der obigen Tabelle in einer Form, die auf ein Telefon passt. Maßgeblich ist das Sicherheitsdatenblatt des jeweiligen Produkts.',
        'es': 'Las reglas de la tabla anterior en un formato que cabe en la pantalla de un teléfono. Prevalece la ficha de datos de seguridad de cada producto.',
        'fr': 'Les règles du tableau ci-dessus sous une forme adaptée à un écran de téléphone. La fiche de données de sécurité de chaque produit prévaut.',
        'pt': 'As regras da tabela acima num formato que cabe na tela de um telefone. Prevalece a ficha de dados de segurança de cada produto.'},
    'rules_h': {'en': 'The rules in words', 'de': 'Die Regeln in Worten', 'es': 'Las reglas en palabras',
                'fr': 'Les règles en toutes lettres', 'pt': 'As regras por extenso'},
    'ok': {'en': 'Together', 'de': 'Zusammen', 'es': 'Juntos', 'fr': 'Ensemble', 'pt': 'Juntos'},
    'caution': {'en': 'Check', 'de': 'Prüfen', 'es': 'Verificar', 'fr': 'Vérifier', 'pt': 'Verificar'},
    'separate': {'en': 'Separate', 'de': 'Getrennt', 'es': 'Separado', 'fr': 'Séparé', 'pt': 'Separado'},
    'never': {'en': 'Never', 'de': 'Nie', 'es': 'Nunca', 'fr': 'Jamais', 'pt': 'Nunca'},
    'guide_h': {'en': 'Which material for which chemical class', 'de': 'Welcher Werkstoff für welche Chemikalienklasse',
                'es': 'Qué material para qué clase química', 'fr': 'Quel matériau pour quelle classe chimique',
                'pt': 'Qual material para qual classe química', 'zh': '各化学品类别适用的材料'},
    'guide_p': {
        'en': 'For each chemical class, the materials with at least 90 % of their rated rows at A or B, and those with less than 25 %. A row is one chemical at one concentration, rated at 20 °C. A class is only counted for a material with at least {n} rated rows.',
        'de': 'Für jede Chemikalienklasse die Werkstoffe, bei denen mindestens 90 % der bewerteten Zeilen A oder B sind, und jene mit weniger als 25 %. Eine Zeile ist eine Chemikalie bei einer Konzentration, bewertet bei 20 °C. Eine Klasse zählt für einen Werkstoff nur bei mindestens {n} bewerteten Zeilen.',
        'es': 'Para cada clase química, los materiales con al menos el 90 % de sus filas clasificadas en A o B, y los que tienen menos del 25 %. Una fila es un producto químico a una concentración, clasificado a 20 °C. Una clase solo cuenta para un material con al menos {n} filas clasificadas.',
        'fr': 'Pour chaque classe chimique, les matériaux dont au moins 90 % des lignes notées sont A ou B, et ceux qui en ont moins de 25 %. Une ligne est un produit chimique à une concentration, noté à 20 °C. Une classe n’est comptée pour un matériau qu’à partir de {n} lignes notées.',
        'pt': 'Para cada classe química, os materiais com pelo menos 90 % das linhas classificadas em A ou B, e os que têm menos de 25 %. Uma linha é um produto químico a uma concentração, classificado a 20 °C. Uma classe só conta para um material com pelo menos {n} linhas classificadas.',
        'zh': '对每个化学品类别，列出至少 90 % 的数据行为 A 或 B 级的材料，以及不足 25 % 的材料。一行代表一种化学品的一个浓度，等级为 20 °C 下的数值。某材料在该类别中至少有 {n} 行有等级时才计入。'},
    'col_good': {'en': 'At least 90 % rated A or B', 'de': 'Mindestens 90 % mit A oder B',
                 'es': 'Al menos 90 % con A o B', 'fr': 'Au moins 90 % notés A ou B',
                 'pt': 'Pelo menos 90 % com A ou B', 'zh': '至少 90 % 为 A 或 B 级'},
    'col_bad': {'en': 'Less than 25 % rated A or B', 'de': 'Weniger als 25 % mit A oder B',
                'es': 'Menos del 25 % con A o B', 'fr': 'Moins de 25 % notés A ou B',
                'pt': 'Menos de 25 % com A ou B', 'zh': '不足 25 % 为 A 或 B 级'},
    'families_h': {'en': 'Material families compared', 'de': 'Werkstoffgruppen im Vergleich',
                   'es': 'Familias de materiales comparadas', 'fr': 'Familles de matériaux comparées',
                   'pt': 'Famílias de materiais comparadas', 'zh': '材料类别对比'},
    'families_cap': {
        'en': 'Share of rated rows at A or B, 20 °C, pooled over the materials of each family.',
        'de': 'Anteil der bewerteten Zeilen mit A oder B bei 20 °C, zusammengefasst über die Werkstoffe jeder Gruppe.',
        'es': 'Proporción de filas clasificadas con A o B a 20 °C, sumando los materiales de cada familia.',
        'fr': 'Part des lignes notées A ou B à 20 °C, tous matériaux de chaque famille confondus.',
        'pt': 'Proporção de linhas classificadas com A ou B a 20 °C, somando os materiais de cada família.',
        'zh': '20 °C 下 A 或 B 级数据行所占比例，按各类别所含材料合并计算。'},
    'silicone': {
        'en': 'The source rates silicone for only {n} chemicals, far fewer than the other materials. A chemical that is missing from this table has not been rated; that does not mean silicone resists it. For seals, compare EPDM, Viton (FPM) and NBR, which the source rates for more than 800 chemicals each.',
        'de': 'Die Quelle bewertet Silikon nur für {n} Chemikalien, deutlich weniger als die anderen Werkstoffe. Eine Chemikalie, die in dieser Tabelle fehlt, wurde nicht bewertet; das bedeutet nicht, dass Silikon beständig ist. Für Dichtungen lohnt der Vergleich mit EPDM, Viton (FPM) und NBR, die die Quelle jeweils für mehr als 800 Chemikalien bewertet.',
        'es': 'La fuente clasifica la silicona solo para {n} productos químicos, muchos menos que los demás materiales. Un producto que no aparece en esta tabla no ha sido clasificado; eso no significa que la silicona lo resista. Para juntas, compare EPDM, Viton (FPM) y NBR, que la fuente clasifica para más de 800 productos cada uno.',
        'fr': 'La source ne note le silicone que pour {n} produits chimiques, bien moins que les autres matériaux. Un produit absent de ce tableau n’a pas été noté ; cela ne signifie pas que le silicone y résiste. Pour les joints, comparez l’EPDM, le Viton (FPM) et le NBR, notés chacun pour plus de 800 produits.',
        'pt': 'A fonte classifica o silicone para apenas {n} produtos químicos, muito menos do que os outros materiais. Um produto ausente desta tabela não foi classificado; isso não significa que o silicone resista. Para vedações, compare EPDM, Viton (FPM) e NBR, que a fonte classifica para mais de 800 produtos cada.',
        'zh': '原始资料仅对 {n} 种化学品给出了硅橡胶的等级，远少于其他材料。表中未列出的化学品表示未经评定，并不代表硅橡胶耐受。密封件可对比 EPDM、Viton (FPM) 和 NBR，原始资料对它们各评定了 800 多种化学品。'},
}


def s(key, lang, **kw):
    text = S[key].get(lang) or S[key]['en']
    return text.format(**kw) if kw else text


def esc(x):
    return html.escape(str(x), quote=True)


def block(marker, inner, width='max-w-5xl'):
    return ('<!-- %s:start -->\n<section class="px-4 py-8 bg-white border-t border-gray-200">%s'
            '<div class="%s mx-auto">%s</div></section>\n<!-- %s:end -->\n    ') % (
        marker, FIG_STYLE, width, inner, marker)


def place(page, marker, html_block, before):
    page = re.sub(r'<!-- %s:start -->[\s\S]*?<!-- %s:end -->\s*' % (marker, marker), '', page)
    at = before(page)
    if at is None or at < 0:
        return page
    return page[:at] + html_block + page[at:]


def before_footer(page):
    return page.find('<footer')


def before_section_with(needle):
    def find(page):
        at = page.find(needle)
        return page.rfind('<section', 0, at) if at > 0 else -1
    return find


H2 = '<h2 class="text-2xl font-bold text-gray-900 mb-4">%s</h2>'
TABLE_STYLE = ('<style>.cr-t{width:100%;border-collapse:collapse;font-size:.9rem}.cr-t th,.cr-t td{padding:.5rem .6rem;'
               'border-bottom:1px solid #f1f5f9;text-align:left;vertical-align:top}.cr-t thead th{background:#f8fafc;'
               'font-weight:600;color:#111827}.cr-t tbody th{font-weight:600;color:#111827}.cr-t a{color:#047857;'
               'text-decoration:underline}</style>')


def viscosity(lang, page):
    with open(os.path.join(ROOT, 'data', 'viscosity.json'), encoding='utf-8') as f:
        data = json.load(f)
    if lang in S['visc_h']:
        value = {}
        for row in data:
            if str(row['temperature_c']) == '20' and re.fullmatch(r'[\d.]+', str(row['viscosity_mPas'])):
                value.setdefault(row['medium_en'], float(row['viscosity_mPas']))
        items = sorted(((names.get(lang, en), value[en]) for en, names in SCALE if en in value),
                       key=lambda x: x[1])
        diagrams.reset_ids()
        fig = diagrams.figure(diagrams.viscosity_scale(s('visc_h', lang), 'mPa·s', items), s('visc_cap', lang))
        page = place(page, 'viscosity-scale', block('viscosity-scale', H2 % esc(s('visc_h', lang)) + fig, 'max-w-4xl'),
                     before_section_with('id="viscosityTable"'))
    if lang in ('en', 'de'):
        rows = []
        for row in data:
            name = row['medium_en'] if lang == 'en' else row['medium']
            sub = ('<div class="text-xs text-gray-500" lang="de">%s</div>' % esc(row['medium'])
                   if lang == 'en' and row['medium'] != name else '')
            rows.append('<tr class="border-b border-gray-100 hover:bg-gray-50"><td class="py-3 px-2 sm:px-4">'
                        '<div class="font-medium text-gray-900 text-sm sm:text-base">%s</div>%s</td>'
                        '<td class="py-3 px-2 sm:px-4 text-center text-gray-600 text-sm whitespace-nowrap">%s°C</td>'
                        '<td class="py-3 px-2 sm:px-4 text-right font-mono text-gray-900 text-sm whitespace-nowrap">%s</td></tr>'
                        % (esc(name), sub, esc(row['temperature_c']), esc(row['viscosity_mPas'])))
        page = re.sub(r'(<tbody id="viscosityTable"[^>]*>)[\s\S]*?(</tbody>)',
                      lambda m: m.group(1) + '\n' + '\n'.join(rows) + '\n' + m.group(2), page, count=1)
    return page


MARKS = {'✓': 'ok', '✗': 'never', '↔': 'separate', '⚠': 'caution'}


def storage(lang, page):
    """The page's own segregation table, redrawn so that it fits a phone, with
    the reasons from data/hazard_classes.json written out next to it. The table
    on the page stays the single statement of the rules."""
    if lang not in S['store_h']:
        return page
    bare = re.sub(r'<!-- storage-matrix:start -->[\s\S]*?<!-- storage-matrix:end -->', '', page)
    m = re.search(r'<table[\s\S]*?</table>', bare)
    if not m:
        return page
    grid = []
    for tr in re.findall(r'<tr[\s\S]*?</tr>', m.group(0)):
        grid.append([' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', c)).split())
                     for c in re.findall(r'<t[hd][\s\S]*?</t[hd]>', tr)])
    if len(grid) < 3 or any(len(r) != len(grid[0]) for r in grid):
        return page
    heads = grid[0][1:]
    table = {}
    for i, row in enumerate(grid[1:]):
        for j, cell in enumerate(row[1:]):
            table[(i, j)] = MARKS.get(cell[:1])
    names = [(i, h) for i, h in enumerate(heads)]
    labels = {k: s(k, lang) for k in ('ok', 'caution', 'separate', 'never')}
    labels[None] = '–'
    diagrams.reset_ids()
    svg = diagrams.storage_matrix(s('store_h', lang), names, lambda a, b: table.get((a, b)), labels)

    with open(os.path.join(ROOT, 'data', 'hazard_classes.json'), encoding='utf-8') as f:
        data = json.load(f)
    order = ['acid', 'base', 'flammable', 'oxidizer', 'toxic']
    listing = ''
    for i, ka in enumerate(order):
        for j, kb in enumerate(order[:i + 1]):
            r = data['compatibility'].get('%s+%s' % (ka, kb)) or data['compatibility'].get('%s+%s' % (kb, ka))
            if r and r['rating'] == table.get((i, j)) and i < len(heads):
                listing += '<tr><th scope="row">%s + %s</th><td>%s</td><td>%s</td></tr>' % (
                    esc(heads[j]), esc(heads[i]), esc(labels[r['rating']]), esc(r['reason'][lang]))
    inner = (H2 % esc(s('store_h', lang)) + '<div class="cr-fp"><div>%s</div><div>%s<h3 class="font-semibold text-gray-900 mb-2">%s</h3>'
             '<table class="cr-t"><tbody>%s</tbody></table></div></div>') % (
        diagrams.figure(svg, s('store_cap', lang)), TABLE_STYLE, esc(s('rules_h', lang)), listing)
    return place(page, 'storage-matrix', block('storage-matrix', inner), before_footer)


FAMILY_HEADS = {
    'en': ['Thermo-\nplastics', 'Fluoro-\npolymers', 'Elasto-\nmers', 'Metals'],
    'de': ['Thermo-\nplaste', 'Fluor-\nkunststoffe', 'Elasto-\nmere', 'Metalle'],
    'es': ['Termo-\nplásticos', 'Fluoro-\npolímeros', 'Elastó-\nmeros', 'Metales'],
    'fr': ['Thermo-\nplastiques', 'Fluoro-\npolymères', 'Élasto-\nmères', 'Métaux'],
    'pt': ['Termo-\nplásticos', 'Fluoro-\npolímeros', 'Elastô-\nmeros', 'Metais'],
}


def family_counts(fam):
    out = {c: {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'n': 0} for c in cs.CLASSES + ['all']}
    for m, (_slug, f) in rd.MATERIALS.items():
        if f != fam:
            continue
        for c, counts in cs.material_profile(m).items():
            for k in counts:
                out[c][k] += counts[k]
    return out


def materials_index(lang, page):
    rows = ''
    root = '/materials/' if lang == 'en' else '/materials/%s/' % lang
    for c in cs.CLASSES:
        good, bad = [], []
        for m, (slug, _f) in rd.MATERIALS.items():
            counts = cs.material_profile(m)[c]
            if counts['n'] < cs.MIN_ROWS:
                continue
            share = cs.good_share(counts)
            link = '<a href="%s%s/">%s</a>' % (root, slug, esc(material_name(m, lang)))
            if share >= 0.9:
                good.append(link)
            elif share < 0.25:
                bad.append(link)
        rows += '<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (
            esc(cs.class_name(c, lang)), ', '.join(good) or '–', ', '.join(bad) or '–')
    inner = (H2 % esc(s('guide_h', lang)) + '<p class="text-gray-600 mb-4" style="font-size:.95rem">%s</p>%s'
             '<div style="overflow-x:auto"><table class="cr-t"><thead><tr><th scope="col">%s</th><th scope="col">%s</th>'
             '<th scope="col">%s</th></tr></thead><tbody>%s</tbody></table></div>'
             '<p style="font-size:.8rem;color:#4b5563;margin-top:1rem">%s</p>') % (
        esc(s('guide_p', lang, n=cs.MIN_ROWS)), TABLE_STYLE, esc(t('fig_finger_h', lang).split(' ')[0] if False else cs_head(lang)),
        esc(s('col_good', lang)), esc(s('col_bad', lang)), rows, esc(t('class_note', lang)))
    return place(page, 'material-guide', block('material-guide', inner), before_footer)


def cs_head(lang):
    return {'en': 'Chemical class', 'de': 'Chemikalienklasse', 'es': 'Clase química', 'fr': 'Classe chimique',
            'pt': 'Classe química', 'zh': '化学品类别'}[lang]


def charts_index(lang, page):
    names = [t('fam_' + f, lang) for f in rd.FAMILIES]
    profiles = [family_counts(f) for f in rd.FAMILIES]
    diagrams.reset_ids()
    svg = diagrams.class_grid(lang, names, profiles, cs.class_name, cs.MIN_ROWS, cs.good_share,
                              s('families_h', lang), heads=FAMILY_HEADS.get(lang))
    overall = diagrams.overall_bars(lang, [(n, p['all']) for n, p in zip(names, profiles)],
                                    t('fig_overall_h', lang))
    inner = (H2 % esc(s('families_h', lang)) + '<div class="cr-fp"><div>%s</div><div>%s</div></div>'
             '<p style="font-size:.8rem;color:#4b5563;margin-top:1rem">%s</p>') % (
        diagrams.figure(svg, s('families_cap', lang), diagrams.ramp_key(lang)),
        diagrams.figure(overall, t('fig_overall_cap', lang), diagrams.grade_key(lang, with_none=False)),
        esc(t('class_note', lang)))
    return place(page, 'family-figures', block('family-figures', inner), before_footer)


def silicone(lang, page):
    n = cs.material_profile('SI')['all']['n']
    chems, _ = rd.load()
    rated = sum(1 for c in chems.values() if any('SI' in v['ratings'] for v in c['variants']))
    note = ('<!-- silicone-note:start -->\n<section class="px-4 pt-6"><div class="max-w-5xl mx-auto">'
            '<p style="background:#fffbeb;border:1px solid #fcd34d;border-radius:.75rem;padding:1rem;color:#78350f;'
            'font-size:.95rem;line-height:1.6;margin:0">%s</p></div></section>\n<!-- silicone-note:end -->\n    ') % esc(
        s('silicone', lang, n=rated))
    def spot(text):
        at = text.find('<!-- fingerprint:start -->')
        return at if at > 0 else before_section_with('id="searchInput"')(text)
    return place(page, 'silicone-note', note, spot)


def targets(lang):
    pre = '' if lang == 'en' else lang + '/'
    mat = 'materials/' if lang == 'en' else 'materials/%s/' % lang
    return [
        (pre + 'viscosity/index.html', viscosity),
        (pre + 'storage-compatibility/index.html', storage),
        (pre + 'charts/index.html', charts_index),
        (mat + 'index.html', materials_index),
        (mat + 'silicone/index.html', silicone),
    ]


def main():
    check = '--check' in sys.argv
    changed = 0
    for lang in LANGS:
        for rel, fn in targets(lang):
            path = os.path.join(ROOT, rel)
            if not os.path.isfile(path):
                continue
            with open(path, encoding='utf-8') as f:
                page = f.read()
            if 'http-equiv="refresh"' in page[:600]:
                continue
            new = fn(lang, page)
            if new != page:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new)
    print('%s %d tool and index pages' % ('would change' if check else 'rewrote', changed))


if __name__ == '__main__':
    main()
