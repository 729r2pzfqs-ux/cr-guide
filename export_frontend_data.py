#!/usr/bin/env python3
"""Write data/chemicals_burkle_full.json, the file the in-browser tools load
(homepage lookup, compare, charts), from resistance_data.

The file keeps the shape those scripts expect, one object per row with
ratings[material] = {c20, c50} on the source's 1-4 scale, so none of them had
to change. What is different from the old export:

  * corrections from data/rating_overrides.json are applied, so the tools and
    the pages agree,
  * a synonym ("see ...") row carries the ratings of the chemical it points
    at instead of being empty, so a search for "Ammonia" finds data,
  * an estimated value is given for 20 °C only, never copied to 50 °C,
  * est / pitting flags are included for scripts that want them,
  * alias_of marks a synonym row, so tables can list each chemical once.
"""

import json
import os

import resistance_data as rd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'data', 'chemicals_burkle_full.json')
CODE = {'A': '1', 'B': '2', 'C': '3', 'D': '4', None: '0'}


def row(name_de, name_en, chem, v, alias_of=None):
    ratings = {}
    for m in rd.MATERIAL_COLUMNS.values():
        r = v['ratings'].get(m)
        if r is None:
            ratings[m] = {'c20': '0', 'c50': '0'}
        elif r.get('k'):
            ratings[m] = {'c20': 'K', 'c50': 'K'}
        else:
            cell = {'c20': CODE[r.get('w20')], 'c50': CODE[r.get('w50')]}
            if r.get('est'):
                cell['est'] = True
            if r.get('pit20') or r.get('pit50'):
                cell['pit'] = True
            ratings[m] = cell
    out = {'name': name_de, 'name_en': name_en, 'formula': chem['formula'], 'cas': chem['cas'],
           'concentration': v['conc'], 'hazard': chem['hazard'], 'flammable': chem['flammable'],
           'comment': v['note'], 'ratings': ratings}
    if alias_of:
        out['alias_of'] = alias_of
    return out


def main():
    chems, _ = rd.load()
    names_en = json.load(open(rd.NAMES_JSON, encoding='utf-8'))['names']
    out = []
    for chem in chems.values():
        for v in chem['variants']:
            out.append(row(chem['name_de'], chem['name_en'], chem, v))
        for alias in chem['aliases_de']:
            for v in chem['variants']:
                out.append(row(alias, names_en.get(alias, alias), chem, v, chem['name_de']))
    out.sort(key=lambda r: r['name'].lower())
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote %d rows to %s (%d KB)' % (len(out), os.path.relpath(OUT, ROOT), os.path.getsize(OUT) // 1024))


if __name__ == '__main__':
    main()
