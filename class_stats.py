#!/usr/bin/env python3
"""Ratings counted by chemical class, for the fingerprint and comparison figures.

The unit is a source row: one chemical at one concentration. Classes come from
data/chemical_classes.json; chemicals classed "other" are left out.
"""

import json
import os
from collections import OrderedDict

import resistance_data as rd

ROOT = os.path.dirname(os.path.abspath(__file__))
#: a class is shown for a material only when it has at least this many rated rows
MIN_ROWS = 8

CLASS_NAMES = {
    'inorg_acid': {'en': 'Mineral acids', 'de': 'Mineralsäuren', 'es': 'Ácidos minerales',
                   'fr': 'Acides minéraux', 'pt': 'Ácidos minerais', 'zh': '无机酸'},
    'org_acid': {'en': 'Organic acids', 'de': 'Organische Säuren', 'es': 'Ácidos orgánicos',
                 'fr': 'Acides organiques', 'pt': 'Ácidos orgânicos', 'zh': '有机酸'},
    'alkali': {'en': 'Alkalis', 'de': 'Laugen', 'es': 'Álcalis', 'fr': 'Bases', 'pt': 'Álcalis',
               'zh': '碱'},
    'salt': {'en': 'Salts and salt solutions', 'de': 'Salze und Salzlösungen',
             'es': 'Sales y soluciones salinas', 'fr': 'Sels et solutions salines',
             'pt': 'Sais e soluções salinas', 'zh': '盐及盐溶液'},
    'oxidizer': {'en': 'Oxidising agents and halogens', 'de': 'Oxidationsmittel und Halogene',
                 'es': 'Oxidantes y halógenos', 'fr': 'Oxydants et halogènes',
                 'pt': 'Oxidantes e halogênios', 'zh': '氧化剂和卤素'},
    'alcohol': {'en': 'Alcohols and glycols', 'de': 'Alkohole und Glykole',
                'es': 'Alcoholes y glicoles', 'fr': 'Alcools et glycols',
                'pt': 'Álcoois e glicóis', 'zh': '醇和二醇'},
    'phenol': {'en': 'Phenols', 'de': 'Phenole', 'es': 'Fenoles', 'fr': 'Phénols', 'pt': 'Fenóis',
               'zh': '酚类'},
    'ketone_aldehyde': {'en': 'Ketones and aldehydes', 'de': 'Ketone und Aldehyde',
                        'es': 'Cetonas y aldehídos', 'fr': 'Cétones et aldéhydes',
                        'pt': 'Cetonas e aldeídos', 'zh': '酮和醛'},
    'ester_ether': {'en': 'Esters and ethers', 'de': 'Ester und Ether', 'es': 'Ésteres y éteres',
                    'fr': 'Esters et éthers', 'pt': 'Ésteres e éteres', 'zh': '酯和醚'},
    'amine_n': {'en': 'Amines and nitrogen compounds', 'de': 'Amine und Stickstoffverbindungen',
                'es': 'Aminas y compuestos nitrogenados', 'fr': 'Amines et composés azotés',
                'pt': 'Aminas e compostos nitrogenados', 'zh': '胺和含氮化合物'},
    'aromatic': {'en': 'Aromatic hydrocarbons', 'de': 'Aromatische Kohlenwasserstoffe',
                 'es': 'Hidrocarburos aromáticos', 'fr': 'Hydrocarbures aromatiques',
                 'pt': 'Hidrocarbonetos aromáticos', 'zh': '芳香烃'},
    'fuel_oil': {'en': 'Fuels, mineral oils and aliphatic hydrocarbons',
                 'de': 'Kraftstoffe, Mineralöle und aliphatische Kohlenwasserstoffe',
                 'es': 'Combustibles, aceites minerales e hidrocarburos alifáticos',
                 'fr': 'Carburants, huiles minérales et hydrocarbures aliphatiques',
                 'pt': 'Combustíveis, óleos minerais e hidrocarbonetos alifáticos',
                 'zh': '燃料、矿物油和脂肪烃'},
    'veg_oil': {'en': 'Vegetable and animal oils, fats, essential oils',
                'de': 'Pflanzliche und tierische Öle, Fette, ätherische Öle',
                'es': 'Aceites vegetales y animales, grasas, aceites esenciales',
                'fr': 'Huiles végétales et animales, graisses, huiles essentielles',
                'pt': 'Óleos vegetais e animais, gorduras, óleos essenciais',
                'zh': '动植物油脂和精油'},
    'halogenated': {'en': 'Halogenated hydrocarbons', 'de': 'Halogenkohlenwasserstoffe',
                    'es': 'Hidrocarburos halogenados', 'fr': 'Hydrocarbures halogénés',
                    'pt': 'Hidrocarbonetos halogenados', 'zh': '卤代烃'},
    'food': {'en': 'Foods and beverages', 'de': 'Lebensmittel und Getränke',
             'es': 'Alimentos y bebidas', 'fr': 'Aliments et boissons',
             'pt': 'Alimentos e bebidas', 'zh': '食品和饮料'},
}
#: short forms for narrow column heads
CLASS_SHORT = {
    'inorg_acid': {'en': 'Mineral acids', 'de': 'Mineralsäuren', 'es': 'Ácidos minerales'},
    'org_acid': {'en': 'Organic acids', 'de': 'Org. Säuren', 'es': 'Ácidos orgánicos'},
    'alkali': {'en': 'Alkalis', 'de': 'Laugen', 'es': 'Álcalis'},
    'salt': {'en': 'Salts', 'de': 'Salze', 'es': 'Sales'},
    'oxidizer': {'en': 'Oxidisers', 'de': 'Oxidationsmittel', 'es': 'Oxidantes'},
    'alcohol': {'en': 'Alcohols', 'de': 'Alkohole', 'es': 'Alcoholes'},
    'phenol': {'en': 'Phenols', 'de': 'Phenole', 'es': 'Fenoles'},
    'ketone_aldehyde': {'en': 'Ketones, aldehydes', 'de': 'Ketone, Aldehyde', 'es': 'Cetonas, aldehídos'},
    'ester_ether': {'en': 'Esters, ethers', 'de': 'Ester, Ether', 'es': 'Ésteres, éteres'},
    'amine_n': {'en': 'Amines', 'de': 'Amine', 'es': 'Aminas'},
    'aromatic': {'en': 'Aromatics', 'de': 'Aromaten', 'es': 'Aromáticos'},
    'fuel_oil': {'en': 'Fuels, mineral oils', 'de': 'Kraftstoffe, Mineralöle', 'es': 'Combustibles, aceites'},
    'veg_oil': {'en': 'Vegetable oils, fats', 'de': 'Pflanzenöle, Fette', 'es': 'Aceites vegetales'},
    'halogenated': {'en': 'Halogenated', 'de': 'Halogen-KW', 'es': 'Halogenados'},
    'food': {'en': 'Foods', 'de': 'Lebensmittel', 'es': 'Alimentos'},
}
CLASSES = list(CLASS_NAMES)


def class_name(cls, lang, short=False):
    if short:
        names = CLASS_SHORT[cls]
        return names.get(lang, names['en'])
    return CLASS_NAMES[cls][lang]


_cache = {}


def chemical_classes():
    if 'cls' not in _cache:
        with open(os.path.join(ROOT, 'data', 'chemical_classes.json'), encoding='utf-8') as f:
            _cache['cls'] = json.load(f)['chemicals']
    return _cache['cls']


def rows():
    """Every source row as (chemical, variant, class)."""
    if 'rows' not in _cache:
        chems, _ = rd.load()
        cls = chemical_classes()
        _cache['rows'] = [(c, v, cls.get(c['name_de'], 'other'))
                          for c in chems.values() for v in c['variants']]
    return _cache['rows']


def material_profile(code):
    """{class: {'A': n, 'B': n, 'C': n, 'D': n, 'n': rated rows}} plus key 'all'."""
    key = ('profile', code)
    if key not in _cache:
        out = OrderedDict((c, {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'n': 0}) for c in CLASSES + ['all'])
        for _chem, v, cls in rows():
            r = v['ratings'].get(code)
            if not r or not r.get('w20'):
                continue
            for k in ((cls, 'all') if cls in out else ('all',)):
                out[k][r['w20']] += 1
                out[k]['n'] += 1
        _cache[key] = out
    return _cache[key]


def good_share(counts):
    """Share of rated rows that are A or B, 0..1, or None without data."""
    return (counts['A'] + counts['B']) / counts['n'] if counts['n'] else None


def pair_stats(a, b):
    """Rows rated for both materials: agreement grid, and who is rated better."""
    grid = {(x, y): 0 for x in 'ABCD' for y in 'ABCD'}
    diffs = []
    for chem, v, cls in rows():
        ra, rb = v['ratings'].get(a), v['ratings'].get(b)
        if not ra or not rb or not ra.get('w20') or not rb.get('w20'):
            continue
        grid[(ra['w20'], rb['w20'])] += 1
        d = rd.GRADE_RANK[rb['w20']] - rd.GRADE_RANK[ra['w20']]   # >0: a is better
        if d:
            diffs.append((d, chem, v, cls))
    n = sum(grid.values())
    same = sum(grid[(g, g)] for g in 'ABCD')
    a_better = sum(1 for d in diffs if d[0] > 0)
    return {'grid': grid, 'n': n, 'same': same, 'a_better': a_better,
            'b_better': len(diffs) - a_better, 'diffs': diffs}
