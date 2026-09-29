#!/usr/bin/env python3
"""Single source of truth for the resistance data.

Reads the Bürkle spreadsheet (data/Beständigkeitsliste Bürkle.xlsx) directly and
keeps everything the older JSON exports threw away:

  * the concentration each row applies to,
  * "( )"  = Schätzwert: the value is an estimate, given without a temperature,
  * "L"    = risk of pitting or stress-corrosion cracking (metals),
  * "K"    = no general statement possible,
  * "-> siehe: X" rows, which are synonyms pointing at another row and carry
    no ratings of their own (661 of the 1,651 rows).

Rows with the same name are grouped into one chemical with several
concentration variants. English names come from data/chemical_names_en.json, with fixes
in NAME_EN_FIXES. data/chemicals_burkle_full.json is an OUTPUT: it is the file
the in-browser tools load, written by export_frontend_data.py.

Departures from the source are never made silently: they live in
data/rating_overrides.json with a reason and references, and the pages list them.
A value is either corrected (replaced) or disputed (kept, but flagged).

Run `python3 resistance_data.py` for a summary; generators import `load()`.
"""

import json
import os
import re
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(ROOT, 'data', 'Beständigkeitsliste Bürkle.xlsx')
NAMES_JSON = os.path.join(ROOT, 'data', 'chemical_names_en.json')
OVERRIDES_JSON = os.path.join(ROOT, 'data', 'rating_overrides.json')

# Spreadsheet column header -> material code, in the source's own order.
MATERIAL_COLUMNS = OrderedDict([
    ('HDPE', 'HDPE'), ('LDPE', 'LDPE'), ('PA', 'PA'), ('PC', 'PC'), ('PETG', 'PETG'),
    ('PMP', 'PMP'), ('POM', 'POM'), ('PP', 'PP'), ('PS', 'PS'), ('PSU', 'PSU'),
    ('PVC HART', 'PVC_HART'), ('PVC WEICH', 'PVC_WEICH'), ('SAN', 'SAN'),
    ('ECTFE / ETFE', 'ECTFE_ETFE'), ('FEP', 'FEP'), ('PTFE', 'PTFE'), ('PVDF', 'PVDF'),
    ('EPDM', 'EPDM'), ('FPM', 'FPM'), ('NBR', 'NBR'), ('SI', 'SI'),
    ('AL', 'AL'), ('V2A', 'V2A'), ('V4A', 'V4A'),
])

# code -> (url slug, family). Display names are per language, see page_i18n.py.
MATERIALS = OrderedDict([
    ('HDPE', ('hdpe', 'thermoplastic')),
    ('LDPE', ('ldpe', 'thermoplastic')),
    ('PP', ('pp', 'thermoplastic')),
    ('PVC_HART', ('pvc-rigid', 'thermoplastic')),
    ('PVC_WEICH', ('pvc-flexible', 'thermoplastic')),
    ('PMP', ('pmp', 'thermoplastic')),
    ('PS', ('polystyrene', 'thermoplastic')),
    ('SAN', ('san', 'thermoplastic')),
    ('PC', ('polycarbonate', 'thermoplastic')),
    ('PETG', ('petg', 'thermoplastic')),
    ('POM', ('acetal-pom', 'thermoplastic')),
    ('PA', ('nylon-pa', 'thermoplastic')),
    ('PSU', ('polysulfone', 'thermoplastic')),
    ('PTFE', ('ptfe', 'fluoropolymer')),
    ('FEP', ('fep', 'fluoropolymer')),
    ('PVDF', ('pvdf', 'fluoropolymer')),
    ('ECTFE_ETFE', ('ectfe-etfe', 'fluoropolymer')),
    ('EPDM', ('epdm', 'elastomer')),
    ('FPM', ('viton', 'elastomer')),
    ('NBR', ('nbr', 'elastomer')),
    ('SI', ('silicone', 'elastomer')),
    ('V4A', ('ss316', 'metal')),
    ('V2A', ('stainless-steel-304', 'metal')),
    ('AL', ('aluminium', 'metal')),
])
FAMILIES = ['thermoplastic', 'fluoropolymer', 'elastomer', 'metal']
SLUG_TO_CODE = {v[0]: k for k, v in MATERIALS.items()}

GRADE = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
GRADE_RANK = {'A': 1, 'B': 2, 'C': 3, 'D': 4}

# Typos in the spreadsheet's own names, and English names that were wrong in
# the JSON export.
NAME_DE_FIXES = {
    'Kalioumperoxodisulfat': 'Kaliumperoxodisulfat',
    'Matriummetabisulfit': 'Natriummetabisulfit',
    'Matriumpyrochromat': 'Natriumpyrochromat',
}
NAME_EN_FIXES = {
    'Salzwasser, Meerwasser': 'Seawater (Salt Water)',
    'Wasser, destilliertes ~': 'Distilled Water',
    'Ethylether': 'Diethyl Ether',
    'Heptan, n-': 'n-Heptane',
    'Hexan, n-': 'n-Hexane',
    'Benzin': 'Gasoline (Petrol)',
    'Methylbenzol': 'Toluene',
}


def _norm_key(s):
    return re.sub(r'[^a-z0-9äöüß]', '', s.lower())


def _grade(token):
    """One side of a cell ('1', '2L', '2-3', '0', '') -> (grade, worst, pitting).

    grade is 'A'..'D', a range such as 'B-C', or None for no data. worst is the
    single letter used for ranking and colour.
    """
    token = token.strip()
    pitting = token.endswith('L')
    if pitting:
        token = token[:-1]
    if token in GRADE:
        g = GRADE[token]
        return g, g, pitting
    m = re.fullmatch(r'([1-4])-([1-4])', token)
    if m:
        lo, hi = GRADE[m.group(1)], GRADE[m.group(2)]
        return lo + '–' + hi, hi, pitting
    return None, None, False


def parse_cell(raw):
    """Spreadsheet cell -> rating dict, or None when there is no usable value.

    Keys: c20, c50 (display grade or None), w20, w50 (worst single grade),
    est (estimated, no temperature given), pit20, pit50, k (no general
    statement possible), raw.
    """
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw or raw == '0/0':
        return None
    if raw == 'K':
        return {'c20': None, 'c50': None, 'w20': None, 'w50': None, 'est': False,
                'pit20': False, 'pit50': False, 'k': True, 'raw': raw}
    est = False
    body = raw
    m = re.fullmatch(r'\((.+)\)', raw)
    if m:
        est = True
        body = m.group(1)
    if '/' in body:
        a, b = body.split('/', 1)
        g20, w20, p20 = _grade(a)
        g50, w50, p50 = _grade(b)
    else:
        # A single value carries no temperature. It is shown once, across both
        # columns, and never presented as a 50 °C measurement.
        g20, w20, p20 = _grade(body)
        g50, w50, p50 = None, None, False
        if g20 is None:
            return None
        return {'c20': g20, 'c50': None, 'w20': w20, 'w50': None, 'est': est,
                'single': True, 'pit20': p20, 'pit50': False, 'k': False, 'raw': raw}
    if g20 is None and g50 is None:
        return None
    return {'c20': g20, 'c50': g50, 'w20': w20, 'w50': w50, 'est': est,
            'single': False, 'pit20': p20, 'pit50': p50, 'k': False, 'raw': raw}


def clean_cas(cas):
    if not cas:
        return ''
    cas = str(cas).strip()
    m = re.fullmatch(r'0*(\d{2,7})-(\d{1,2})-(\d)', cas)
    if not m:
        return ''
    return '%s-%02d-%s' % (m.group(1), int(m.group(2)), m.group(3))


def _read_rows():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    rows = list(wb['Beständigkeit'].iter_rows(values_only=True))
    header = [str(h).replace('\n', '') if h is not None else '' for h in rows[1]]
    col = {h: i for i, h in enumerate(header)}
    names_en = json.load(open(NAMES_JSON, encoding='utf-8'))['names']
    out = []
    for r in rows[2:]:
        if not r[0]:
            continue
        name = str(r[0]).strip()
        name_en = names_en.get(name) or names_en.get(NAME_DE_FIXES.get(name, name)) or name
        name = NAME_DE_FIXES.get(name, name)
        formula = '' if r[1] in (None, '—') else str(r[1]).strip()
        see = None
        if 'siehe' in formula:
            see = formula.split('siehe:')[-1].strip()
            formula = ''
        hazard = '' if r[4] in (None, '—', '?') else str(r[4]).strip()
        out.append({
            'name_de': name,
            'name_en': NAME_EN_FIXES.get(name, name_en),
            'formula': formula,
            'cas': clean_cas(r[2]),
            'conc': '' if r[3] is None else re.sub(r'\s+', ' ', str(r[3])).strip(),
            'hazard': hazard.strip('()'),
            'flammable': r[5] is not None,
            'note': '' if r[30] is None else str(r[30]).strip(),
            'see': see,
            'cells': {code: parse_cell(r[col[h]]) for h, code in MATERIAL_COLUMNS.items()},
        })
    return out


def _resolve_see(rows):
    by_name = {}
    for r in rows:
        if r['see'] is None:
            by_name.setdefault(r['name_de'], r)
    keys = {_norm_key(n): n for n in by_name}
    unresolved = []
    for r in rows:
        if r['see'] is None:
            continue
        t = r['see']
        target = None
        if t in by_name:
            target = t
        elif _norm_key(t) in keys:
            target = keys[_norm_key(t)]
        else:
            k = _norm_key(t)
            cands = [n for kk, n in keys.items() if kk.startswith(k) or k.startswith(kk)]
            if len(cands) == 1:
                target = cands[0]
        r['see_target'] = target
        if target is None:
            unresolved.append((r['name_de'], t))
    return unresolved


def load_overrides():
    if not os.path.exists(OVERRIDES_JSON):
        return []
    return json.load(open(OVERRIDES_JSON, encoding='utf-8'))['overrides']


def _conc_sort_key(conc):
    m = re.match(r'\s*(\d+(?:[.,]\d+)?)', conc)
    if m:
        return (0, float(m.group(1).replace(',', '.')), conc)
    order = ['verdünnt', 'gering', 'wässrig', 'jede', 'gesättigt', 'konz.', 'techn. rein',
             'rein', '', 'rauchend']
    return (1, order.index(conc) if conc in order else len(order), conc)


def build():
    rows = _read_rows()
    unresolved = _resolve_see(rows)

    chemicals = OrderedDict()
    for r in rows:
        if r['see'] is not None:
            continue
        c = chemicals.get(r['name_de'])
        if c is None:
            c = chemicals[r['name_de']] = {
                'name_de': r['name_de'], 'name_en': r['name_en'], 'formula': r['formula'],
                'cas': r['cas'], 'hazard': r['hazard'], 'flammable': r['flammable'],
                'aliases_de': [], 'aliases_en': [], 'variants': [],
            }
        for k in ('formula', 'cas', 'hazard'):
            if not c[k] and r[k]:
                c[k] = r[k]
        c['flammable'] = c['flammable'] or r['flammable']
        c['variants'].append({
            'conc': r['conc'], 'note': r['note'],
            'ratings': {m: v for m, v in r['cells'].items() if v is not None},
            'corrections': [],
        })
    for r in rows:
        if r['see'] is not None and r.get('see_target'):
            c = chemicals[r['see_target']]
            if r['name_de'] not in c['aliases_de']:
                c['aliases_de'].append(r['name_de'])
            en = r['name_en']
            if en and en.lower() != c['name_en'].lower() and en not in c['aliases_en']:
                c['aliases_en'].append(en)

    applied, missed = 0, []
    for o in load_overrides():
        c = chemicals.get(o['chemical_de'])
        hit = False
        if c:
            for v in c['variants']:
                if o.get('conc', '*') not in ('*', v['conc']):
                    continue
                for m in o['materials']:
                    old = v['ratings'].get(m)
                    note = {'kind': o.get('kind', 'corrected'), 'material': m,
                            'source_value': old['raw'] if old else '0/0',
                            'reason': o['reason'], 'refs': o.get('refs', []),
                            'reasons': {'de': o.get('reason_de'), 'es': o.get('reason_es')}}
                    if note['kind'] == 'disputed':
                        if old is None:
                            continue
                        old['disputed'] = True
                    else:
                        new = parse_cell(o['value'])
                        note['value'] = o['value']
                        if new is None:
                            v['ratings'].pop(m, None)
                        else:
                            new['corrected'] = True
                            v['ratings'][m] = new
                    v['corrections'].append(note)
                    hit = True
        if hit:
            applied += 1
        else:
            missed.append(o)

    for c in chemicals.values():
        c['variants'].sort(key=lambda v: _conc_sort_key(v['conc']))

    stats = {
        'source_rows': len(rows),
        'synonym_rows': sum(1 for r in rows if r['see'] is not None),
        'data_rows': sum(1 for r in rows if r['see'] is None),
        'chemicals': len(chemicals),
        'unresolved_synonyms': unresolved,
        'overrides_applied': applied,
        'overrides_missed': missed,
        'rated_cells': sum(len(v['ratings']) for c in chemicals.values() for v in c['variants']),
        'estimated_cells': sum(1 for c in chemicals.values() for v in c['variants']
                               for x in v['ratings'].values() if x['est']),
    }
    return {'chemicals': list(chemicals.values()), 'stats': stats}


_CACHE = None


def load():
    """Chemicals keyed by their German source name."""
    global _CACHE
    if _CACHE is None:
        data = build()
        _CACHE = (OrderedDict((c['name_de'], c) for c in data['chemicals']), data['stats'])
    return _CACHE


if __name__ == '__main__':
    data = build()
    s = data['stats']
    print('source rows          %d' % s['source_rows'])
    print('  synonym (see) rows %d' % s['synonym_rows'])
    print('  rows with data     %d' % s['data_rows'])
    print('distinct chemicals   %d' % s['chemicals'])
    print('rated cells          %d (%d estimated)' % (s['rated_cells'], s['estimated_cells']))
    print('unresolved synonyms  %d' % len(s['unresolved_synonyms']))
    print('overrides applied    %d, missed %d' % (s['overrides_applied'], len(s['overrides_missed'])))
