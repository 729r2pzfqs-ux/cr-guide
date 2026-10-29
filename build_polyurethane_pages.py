#!/usr/bin/env python3
"""Generate the polyurethane material page in all six site languages.

    python3 build_polyurethane_pages.py            # write pages
    python3 build_polyurethane_pages.py --check    # report only

Polyurethane is NOT in the Bürkle spreadsheet, so this is a standalone
generator. The ratings come from PSI Urethanes (lab-tested, A/B/C scale)
cross-referenced with Engineering Toolbox (4-level) and Darwin Microfluidics
(A-D). PSI's C was split into site C or D based on Engineering Toolbox's
"not resistant" vs "conditionally resistant" classification.

Idempotent.
"""

import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ['en', 'de', 'es', 'fr', 'pt', 'zh']

SLUG = 'polyurethane'
FAMILY = 'elastomer'

MATERIAL_NAME = {
    'en': 'Polyurethane', 'de': 'Polyurethan', 'es': 'Poliuretano',
    'fr': 'Polyuréthane', 'pt': 'Poliuretano', 'zh': '聚氨酯',
}

TITLE = {
    'en': 'Polyurethane Chemical Resistance Chart | {n} Chemicals',
    'de': 'Polyurethan Chemikalienbeständigkeit | {n} Chemikalien A-D',
    'es': 'Resistencia Química del Poliuretano | {n} Químicos',
    'fr': 'Résistance Chimique du Polyuréthane | {n} Produits',
    'pt': 'Resistência Química do Poliuretano | {n} Químicos',
    'zh': '聚氨酯耐化学性 | {n} 种化学品',
}

DESC = {
    'en': 'Polyurethane (PU) resists oils, greases, fuels &amp; dilute acids. Poor against ketones, chlorinated solvents &amp; strong acids. A-D chart for {n} chemicals at 20 °C.',
    'de': 'Polyurethan (PU) beständig gegen Öle, Fette, Kraftstoffe &amp; verdünnte Säuren. Unbeständig gegen Ketone, chlorierte Lösemittel &amp; starke Säuren. A-D-Tabelle für {n} Chemikalien.',
    'es': 'Poliuretano (PU) resiste aceites, grasas, combustibles y ácidos diluidos. No resiste cetonas, disolventes clorados ni ácidos fuertes. Tabla A-D para {n} químicos.',
    'fr': 'Le polyuréthane (PU) résiste aux huiles, graisses, carburants et acides dilués. Faible résistance aux cétones, solvants chlorés et acides forts. Tableau A-D pour {n} produits.',
    'pt': 'Poliuretano (PU) resiste a óleos, graxas, combustíveis e ácidos diluídos. Fraco contra cetonas, solventes clorados e ácidos fortes. Tabela A-D para {n} químicos.',
    'zh': '聚氨酯 (PU) 耐油脂、燃料和稀酸。不耐酮类、氯化溶剂和强酸。{n} 种化学品 A-D 等级表。',
}

HERO_TEXT = {
    'en': 'Polyurethane (PU) is a versatile elastomer with excellent abrasion resistance and good chemical resistance to oils, fuels, greases and dilute acids. Performance varies with formulation (polyester-based vs polyether-based).',
    'de': 'Polyurethan (PU) ist ein vielseitiges Elastomer mit ausgezeichneter Abriebfestigkeit und guter Beständigkeit gegen Öle, Kraftstoffe, Fette und verdünnte Säuren. Die Leistung variiert je nach Formulierung.',
    'es': 'El poliuretano (PU) es un elastómero versátil con excelente resistencia a la abrasión y buena resistencia química a aceites, combustibles, grasas y ácidos diluidos.',
    'fr': 'Le polyuréthane (PU) est un élastomère polyvalent offrant une excellente résistance à l\'abrasion et une bonne résistance chimique aux huiles, carburants, graisses et acides dilués.',
    'pt': 'O poliuretano (PU) é um elastômero versátil com excelente resistência à abrasão e boa resistência química a óleos, combustíveis, graxas e ácidos diluídos.',
    'zh': '聚氨酯 (PU) 是一种用途广泛的弹性体，具有出色的耐磨性，对油类、燃料、脂肪和稀酸具有良好的耐化学性。性能因配方（聚酯型与聚醚型）而异。',
}

NOTE_TEXT = {
    'en': 'Polyurethane is not in the Bürkle source that supplies the other 24 materials on this site. The data below comes from PSI Urethanes (lab-tested at 21 °C / 70 °F, A-B-C scale), cross-referenced with Engineering Toolbox and Darwin Microfluidics. Polyurethane formulations vary widely; always verify with your specific resin manufacturer.',
    'de': 'Polyurethan ist nicht in der Bürkle-Quelle enthalten, die die anderen 24 Materialien auf dieser Website liefert. Die folgenden Daten stammen von PSI Urethanes (laborgeprüft bei 21 °C, A-B-C-Skala), gegengeprüft mit Engineering Toolbox und Darwin Microfluidics. PU-Formulierungen variieren stark; immer beim Hersteller rückfragen.',
    'es': 'El poliuretano no está en la fuente Bürkle que proporciona los otros 24 materiales de este sitio. Los datos provienen de PSI Urethanes (ensayados a 21 °C, escala A-B-C), verificados con Engineering Toolbox y Darwin Microfluidics. Las formulaciones de PU varían; siempre verificar con el fabricante.',
    'fr': 'Le polyuréthane ne figure pas dans la source Bürkle qui fournit les 24 autres matériaux de ce site. Les données ci-dessous proviennent de PSI Urethanes (tests en laboratoire à 21 °C, échelle A-B-C), recoupées avec Engineering Toolbox et Darwin Microfluidics. Les formulations PU varient fortement ; vérifiez auprès du fabricant.',
    'pt': 'O poliuretano não está na fonte Bürkle que fornece os outros 24 materiais neste site. Os dados abaixo vêm da PSI Urethanes (testados em laboratório a 21 °C, escala A-B-C), verificados com Engineering Toolbox e Darwin Microfluidics. As formulações de PU variam; sempre confirme com o fabricante.',
    'zh': '聚氨酯不在本站其他 24 种材料所用的 Bürkle 数据源中。以下数据来自 PSI Urethanes（实验室测试，21 °C，A-B-C 等级），并与 Engineering Toolbox 和 Darwin Microfluidics 交叉验证。PU 配方差异较大，请始终向树脂制造商确认。',
}

TABLE_NOTE = {
    'en': 'Ratings at 21 °C (70 °F). Source: PSI Urethanes, cross-referenced with Engineering Toolbox. Formulation and concentration affect actual performance.',
    'de': 'Bewertungen bei 21 °C. Quelle: PSI Urethanes, gegengeprüft mit Engineering Toolbox. Formulierung und Konzentration beeinflussen die tatsächliche Leistung.',
    'es': 'Clasificaciones a 21 °C. Fuente: PSI Urethanes, verificado con Engineering Toolbox. La formulación y concentración afectan el rendimiento real.',
    'fr': 'Évaluations à 21 °C. Source: PSI Urethanes, recoupées avec Engineering Toolbox. La formulation et la concentration influencent les performances réelles.',
    'pt': 'Classificações a 21 °C. Fonte: PSI Urethanes, verificado com Engineering Toolbox. A formulação e concentração afetam o desempenho real.',
    'zh': '21 °C 评级。来源：PSI Urethanes，与 Engineering Toolbox 交叉验证。配方和浓度影响实际性能。',
}

PROP_LABEL = {
    'en': 'Polyurethane Properties', 'de': 'Polyurethan-Eigenschaften',
    'es': 'Propiedades del Poliuretano', 'fr': 'Propriétés du Polyuréthane',
    'pt': 'Propriedades do Poliuretano', 'zh': '聚氨酯性能',
}

APP_LABEL = {
    'en': 'Common Applications', 'de': 'Typische Anwendungen',
    'es': 'Aplicaciones Comunes', 'fr': 'Applications Courantes',
    'pt': 'Aplicações Comuns', 'zh': '常见应用',
}

AVOID_LABEL = {
    'en': 'Not Recommended For', 'de': 'Nicht empfohlen für',
    'es': 'No recomendado para', 'fr': 'Non recommandé pour',
    'pt': 'Não recomendado para', 'zh': '不推荐用于',
}

COMPARE_LABEL = {
    'en': 'Compare Materials', 'de': 'Materialien vergleichen',
    'es': 'Comparar Materiales', 'fr': 'Comparer les Matériaux',
    'pt': 'Comparar Materiais', 'zh': '比较材料',
}

SEARCH_LABEL = {
    'en': 'Search chemicals', 'de': 'Chemikalien suchen',
    'es': 'Buscar químicos', 'fr': 'Rechercher',
    'pt': 'Pesquisar químicos', 'zh': '搜索化学品',
}

FILTER_LABEL = {
    'en': 'Rating filter', 'de': 'Bewertungsfilter', 'es': 'Filtro',
    'fr': 'Filtre', 'pt': 'Filtro', 'zh': '等级筛选',
}

STAT_LABELS = {
    'en': ('Excellent (A)', 'Good (B)', 'Limited (C)', 'Not Rec. (D)'),
    'de': ('Sehr gut (A)', 'Gut (B)', 'Begrenzt (C)', 'Nicht empf. (D)'),
    'es': ('Excelente (A)', 'Bueno (B)', 'Limitado (C)', 'No rec. (D)'),
    'fr': ('Excellent (A)', 'Bon (B)', 'Limité (C)', 'Non rec. (D)'),
    'pt': ('Excelente (A)', 'Bom (B)', 'Limitado (C)', 'Não rec. (D)'),
    'zh': ('优 (A)', '良 (B)', '有限 (C)', '不推荐 (D)'),
}

SHOWING = {
    'en': 'Showing', 'de': 'Ergebnisse:', 'es': 'Mostrando',
    'fr': 'Affichage', 'pt': 'Mostrando', 'zh': '显示',
}

CHEMICALS_WORD = {
    'en': 'chemicals', 'de': 'Chemikalien', 'es': 'químicos',
    'fr': 'produits', 'pt': 'químicos', 'zh': '种化学品',
}

ALL_RATINGS = {
    'en': 'All ratings', 'de': 'Alle Bewertungen', 'es': 'Todas',
    'fr': 'Toutes', 'pt': 'Todas', 'zh': '全部',
}

CHEMICAL_TH = {
    'en': 'Chemical', 'de': 'Chemikalie', 'es': 'Químico',
    'fr': 'Produit chimique', 'pt': 'Químico', 'zh': '化学品',
}

CONC_TH = {
    'en': 'Concentration', 'de': 'Konzentration', 'es': 'Concentración',
    'fr': 'Concentration', 'pt': 'Concentração', 'zh': '浓度',
}

RATING_TH = {
    'en': 'Rating (21 °C)', 'de': 'Bewertung (21 °C)',
    'es': 'Clasificación (21 °C)', 'fr': 'Évaluation (21 °C)',
    'pt': 'Classificação (21 °C)', 'zh': '等级 (21 °C)',
}

BREADCRUMB = {
    'en': ('Home', 'Materials', 'Polyurethane'),
    'de': ('Startseite', 'Materialien', 'Polyurethan'),
    'es': ('Inicio', 'Materiales', 'Poliuretano'),
    'fr': ('Accueil', 'Matériaux', 'Polyuréthane'),
    'pt': ('Início', 'Materiais', 'Poliuretano'),
    'zh': ('首页', '材料', '聚氨酯'),
}

NAV = {
    'en': {'lookup': 'Lookup', 'materials': 'Materials', 'chemicals': 'Chemicals',
           'compare': 'Compare', 'charts': 'Charts', 'storage': 'Storage',
           'sds': 'SDS Decoder', 'viscosity': 'Viscosity', 'about': 'About',
           'tagline': 'Chemical compatibility database'},
    'de': {'lookup': 'Suche', 'materials': 'Materialien', 'chemicals': 'Chemikalien',
           'compare': 'Vergleich', 'charts': 'Diagramme', 'storage': 'Lagerung',
           'sds': 'SDS-Decoder', 'viscosity': 'Viskosität', 'about': 'Info',
           'tagline': 'Chemikalienbeständigkeits-Datenbank'},
    'es': {'lookup': 'Búsqueda', 'materials': 'Materiales', 'chemicals': 'Químicos',
           'compare': 'Comparar', 'charts': 'Gráficos', 'storage': 'Almacenamiento',
           'sds': 'Decodificador SDS', 'viscosity': 'Viscosidad', 'about': 'Acerca de',
           'tagline': 'Base de datos de compatibilidad química'},
    'fr': {'lookup': 'Recherche', 'materials': 'Matériaux', 'chemicals': 'Produits chimiques',
           'compare': 'Comparer', 'charts': 'Graphiques', 'storage': 'Stockage',
           'sds': 'Décodeur SDS', 'viscosity': 'Viscosité', 'about': 'À propos',
           'tagline': 'Base de données de compatibilité chimique'},
    'pt': {'lookup': 'Pesquisa', 'materials': 'Materiais', 'chemicals': 'Químicos',
           'compare': 'Comparar', 'charts': 'Gráficos', 'storage': 'Armazenamento',
           'sds': 'Decodificador SDS', 'viscosity': 'Viscosidade', 'about': 'Sobre',
           'tagline': 'Banco de dados de compatibilidade química'},
    'zh': {'lookup': '查询', 'materials': '材料', 'chemicals': '化学品',
           'compare': '比较', 'charts': '图表', 'storage': '存储',
           'sds': 'SDS解码器', 'viscosity': '粘度', 'about': '关于',
           'tagline': '化学品兼容性数据库'},
}

# PU chemical resistance data. Source: PSI Urethanes (A-B-C scale, lab-tested
# at 21 °C / 70 °F), with PSI "C" split to site C or D using Engineering
# Toolbox cross-reference.  Each entry:
#   (english_name, concentration, rating, cas, chemical_page_slug_or_None)
PU_DATA = [
    ('Acetic Acid', '20 %', 'B', '64-19-7', 'acetic-acid'),
    ('Acetone', 'pure', 'D', '67-64-1', 'acetone'),
    ('Aluminum Chloride', 'aqueous', 'A', '7446-70-0', 'aluminum-chloride'),
    ('Ammonia', 'anhydrous', 'D', '7664-41-7', None),
    ('Ammonium Chloride', 'aqueous', 'B', '12125-02-9', 'ammonium-chloride'),
    ('Ammonium Hydroxide', 'aqueous', 'D', '1336-21-6', 'ammonium-hydroxide'),
    ('Ammonium Phosphate', 'aqueous', 'B', '7783-28-0', None),
    ('Ammonium Sulfate', 'aqueous', 'A', '7783-20-2', 'ammonium-sulfate'),
    ('Barium Hydroxide', 'aqueous', 'A', '17194-00-2', 'barium-hydroxide'),
    ('Benzene', 'pure', 'D', '71-43-2', 'benzene'),
    ('Boric Acid', 'aqueous', 'A', '10043-35-3', 'boric-acid'),
    ('Butane', 'gas', 'A', '106-97-8', 'butane'),
    ('Calcium Chloride', 'aqueous', 'A', '10043-52-4', 'calcium-chloride'),
    ('Calcium Hydroxide', 'aqueous', 'A', '1305-62-0', 'calcium-hydroxide'),
    ('Calcium Hypochlorite', 'aqueous', 'D', '7778-54-3', 'calcium-hypochlorite'),
    ('Carbon Dioxide', 'gas', 'A', '124-38-9', 'carbon-dioxide'),
    ('Carbon Tetrachloride', 'pure', 'D', '56-23-5', 'carbon-tetrachloride'),
    ('Castor Oil', 'pure', 'A', '8001-79-4', 'castor-oil'),
    ('Chlorine Gas', 'gas', 'D', '7782-50-5', 'chlorine-gas'),
    ('Chromic Acid', '2 %', 'B', '7738-94-5', 'chromic-acid'),
    ('Citric Acid', 'aqueous', 'A', '77-92-9', 'citric-acid'),
    ('Copper Sulfate', '10 %', 'A', '7758-98-7', 'copper-vitriol-copper-sulfate'),
    ('Cyclohexane', 'pure', 'A', '110-82-7', 'cyclohexane'),
    ('Diethyl Ether', 'pure', 'A', '60-29-7', 'diethyl-ether'),
    ('Ethanol', 'pure', 'C', '64-17-5', 'ethanol'),
    ('Ethyl Acetate', 'pure', 'D', '141-78-6', 'ethyl-acetate'),
    ('Ethylene Glycol', 'pure', 'B', '107-21-1', 'ethylene-glycol'),
    ('Formaldehyde', 'aqueous', 'C', '50-00-0', 'formaldehyde'),
    ('Formic Acid', 'concentrated', 'D', '64-18-6', 'formic-acid'),
    ('Gasoline', 'pure', 'B', None, 'gasoline-petrol'),
    ('Glycerin', 'pure', 'A', '56-81-5', 'glycerin'),
    ('Hexane', 'pure', 'B', '110-54-3', 'hexane'),
    ('Hydrochloric Acid', '20 %', 'B', '7647-01-0', 'hydrochloric-acid'),
    ('Hydrochloric Acid', '37 %', 'D', '7647-01-0', 'hydrochloric-acid'),
    ('Hydrogen', 'gas', 'A', '1333-74-0', None),
    ('Hydrogen Peroxide', '30 %', 'B', '7722-84-1', 'hydrogen-peroxide'),
    ('Kerosene', 'pure', 'B', '8008-20-6', 'kerosene'),
    ('Linseed Oil', 'pure', 'B', '8001-26-1', 'linseed-oil'),
    ('Magnesium Chloride', 'aqueous', 'A', '7786-30-3', 'magnesium-chloride'),
    ('Magnesium Hydroxide', 'aqueous', 'A', '1309-42-8', 'magnesium-hydroxide'),
    ('Mercury', 'pure', 'A', '7439-97-6', 'mercury'),
    ('Methanol', 'pure', 'D', '67-56-1', 'methanol'),
    ('Methyl Ethyl Ketone', 'pure', 'D', '78-93-3', 'butanone-mek'),
    ('Mineral Oil', 'pure', 'A', '8012-95-1', 'mineral-oil'),
    ('Naphtha', 'pure', 'B', '8030-30-6', 'naphtha'),
    ('Naphthalene', 'solid', 'B', '91-20-3', 'naphthalene'),
    ('Nitric Acid', '2 %', 'B', '7697-37-2', 'nitric-acid'),
    ('Nitric Acid', '10 %', 'D', '7697-37-2', 'nitric-acid'),
    ('Oleic Acid', 'pure', 'A', '112-80-1', 'oleic-acid'),
    ('Ozone', 'gas', 'A', '10028-15-6', 'ozone'),
    ('Palmitic Acid', 'pure', 'A', '57-11-4', 'palmitic-acid'),
    ('Perchloroethylene', 'pure', 'D', '127-18-4', None),
    ('Phenol', 'pure', 'D', '108-95-2', 'phenol'),
    ('Phosphoric Acid', '20–70 %', 'B', '7664-38-2', 'phosphoric-acid'),
    ('Phosphoric Acid', '85 %', 'D', '7664-38-2', 'phosphoric-acid'),
    ('Potassium Hydroxide', '10 %', 'B', '1310-58-3', 'potassium-hydroxide'),
    ('Silver Nitrate', 'aqueous', 'A', '7761-88-8', 'silver-nitrate'),
    ('Sodium Chloride', 'aqueous', 'A', '7647-14-5', 'sodium-chloride'),
    ('Sodium Hydroxide', '20 %', 'A', '1310-73-2', 'sodium-hydroxide-caustic-soda'),
    ('Sodium Hydroxide', '45 %', 'B', '1310-73-2', 'sodium-hydroxide-caustic-soda'),
    ('Sodium Hypochlorite', '1 %', 'B', '7681-52-9', 'sodium-hypochlorite'),
    ('Stearic Acid', 'pure', 'A', '57-11-4', 'stearic-acid'),
    ('Sulfuric Acid', '5–10 %', 'A', '7664-93-9', 'sulfuric-acid'),
    ('Sulfuric Acid', '10–50 %', 'C', '7664-93-9', 'sulfuric-acid'),
    ('Tannic Acid', 'aqueous', 'A', '1401-55-4', None),
    ('Tartaric Acid', 'aqueous', 'A', '87-69-4', 'tartaric-acid'),
    ('Tetrahydrofuran', 'pure', 'D', '109-99-9', 'thf'),
    ('Toluene', 'pure', 'D', '108-88-3', 'toluene'),
    ('Trichloroethylene', 'pure', 'D', '79-01-6', 'trichloroethylene'),
    ('Trisodium Phosphate', 'aqueous', 'A', '7601-54-9', None),
    ('Turpentine', 'pure', 'D', '8006-64-2', 'turpentine-oil'),
    ('Xylene', 'pure', 'D', '1330-20-7', 'xylene'),
]

# Localized chemical names (only non-English; English is the default)
CHEM_NAMES = {
    'de': {
        'Acetic Acid': 'Essigsäure', 'Acetone': 'Aceton',
        'Aluminum Chloride': 'Aluminiumchlorid', 'Ammonia': 'Ammoniak',
        'Ammonium Chloride': 'Ammoniumchlorid', 'Ammonium Hydroxide': 'Ammoniumhydroxid',
        'Ammonium Phosphate': 'Ammoniumphosphat', 'Ammonium Sulfate': 'Ammoniumsulfat',
        'Barium Hydroxide': 'Bariumhydroxid', 'Benzene': 'Benzol',
        'Boric Acid': 'Borsäure', 'Butane': 'Butan',
        'Calcium Chloride': 'Calciumchlorid', 'Calcium Hydroxide': 'Calciumhydroxid',
        'Calcium Hypochlorite': 'Calciumhypochlorit', 'Carbon Dioxide': 'Kohlendioxid',
        'Carbon Tetrachloride': 'Tetrachlorkohlenstoff', 'Castor Oil': 'Rizinusöl',
        'Chlorine Gas': 'Chlorgas', 'Chromic Acid': 'Chromsäure',
        'Citric Acid': 'Zitronensäure', 'Copper Sulfate': 'Kupfersulfat',
        'Cyclohexane': 'Cyclohexan', 'Diethyl Ether': 'Diethylether',
        'Ethanol': 'Ethanol', 'Ethyl Acetate': 'Ethylacetat',
        'Ethylene Glycol': 'Ethylenglykol', 'Formaldehyde': 'Formaldehyd',
        'Formic Acid': 'Ameisensäure', 'Gasoline': 'Benzin',
        'Glycerin': 'Glycerin', 'Hexane': 'Hexan',
        'Hydrochloric Acid': 'Salzsäure', 'Hydrogen': 'Wasserstoff',
        'Hydrogen Peroxide': 'Wasserstoffperoxid', 'Kerosene': 'Kerosin',
        'Linseed Oil': 'Leinöl', 'Magnesium Chloride': 'Magnesiumchlorid',
        'Magnesium Hydroxide': 'Magnesiumhydroxid', 'Mercury': 'Quecksilber',
        'Methanol': 'Methanol', 'Methyl Ethyl Ketone': 'Methylethylketon',
        'Mineral Oil': 'Mineralöl', 'Naphtha': 'Naphtha',
        'Naphthalene': 'Naphthalin', 'Nitric Acid': 'Salpetersäure',
        'Oleic Acid': 'Ölsäure', 'Ozone': 'Ozon',
        'Palmitic Acid': 'Palmitinsäure', 'Perchloroethylene': 'Perchlorethylen',
        'Phenol': 'Phenol', 'Phosphoric Acid': 'Phosphorsäure',
        'Potassium Hydroxide': 'Kaliumhydroxid', 'Silver Nitrate': 'Silbernitrat',
        'Sodium Chloride': 'Natriumchlorid', 'Sodium Hydroxide': 'Natriumhydroxid',
        'Sodium Hypochlorite': 'Natriumhypochlorit', 'Stearic Acid': 'Stearinsäure',
        'Sulfuric Acid': 'Schwefelsäure', 'Tannic Acid': 'Gerbsäure',
        'Tartaric Acid': 'Weinsäure', 'Tetrahydrofuran': 'Tetrahydrofuran',
        'Toluene': 'Toluol', 'Trichloroethylene': 'Trichlorethylen',
        'Trisodium Phosphate': 'Trinatriumphosphat', 'Turpentine': 'Terpentinöl',
        'Xylene': 'Xylol',
    },
    'es': {
        'Acetic Acid': 'Ácido acético', 'Acetone': 'Acetona',
        'Aluminum Chloride': 'Cloruro de aluminio', 'Ammonia': 'Amoníaco',
        'Ammonium Chloride': 'Cloruro de amonio', 'Ammonium Hydroxide': 'Hidróxido de amonio',
        'Ammonium Phosphate': 'Fosfato de amonio', 'Ammonium Sulfate': 'Sulfato de amonio',
        'Barium Hydroxide': 'Hidróxido de bario', 'Benzene': 'Benceno',
        'Boric Acid': 'Ácido bórico', 'Butane': 'Butano',
        'Calcium Chloride': 'Cloruro de calcio', 'Calcium Hydroxide': 'Hidróxido de calcio',
        'Calcium Hypochlorite': 'Hipoclorito de calcio', 'Carbon Dioxide': 'Dióxido de carbono',
        'Carbon Tetrachloride': 'Tetracloruro de carbono', 'Castor Oil': 'Aceite de ricino',
        'Chlorine Gas': 'Gas cloro', 'Chromic Acid': 'Ácido crómico',
        'Citric Acid': 'Ácido cítrico', 'Copper Sulfate': 'Sulfato de cobre',
        'Cyclohexane': 'Ciclohexano', 'Diethyl Ether': 'Éter dietílico',
        'Ethanol': 'Etanol', 'Ethyl Acetate': 'Acetato de etilo',
        'Ethylene Glycol': 'Etilenglicol', 'Formaldehyde': 'Formaldehído',
        'Formic Acid': 'Ácido fórmico', 'Gasoline': 'Gasolina',
        'Glycerin': 'Glicerina', 'Hexane': 'Hexano',
        'Hydrochloric Acid': 'Ácido clorhídrico', 'Hydrogen': 'Hidrógeno',
        'Hydrogen Peroxide': 'Peróxido de hidrógeno', 'Kerosene': 'Queroseno',
        'Linseed Oil': 'Aceite de linaza', 'Magnesium Chloride': 'Cloruro de magnesio',
        'Magnesium Hydroxide': 'Hidróxido de magnesio', 'Mercury': 'Mercurio',
        'Methanol': 'Metanol', 'Methyl Ethyl Ketone': 'Metil etil cetona',
        'Mineral Oil': 'Aceite mineral', 'Naphtha': 'Nafta',
        'Naphthalene': 'Naftaleno', 'Nitric Acid': 'Ácido nítrico',
        'Oleic Acid': 'Ácido oleico', 'Ozone': 'Ozono',
        'Palmitic Acid': 'Ácido palmítico', 'Perchloroethylene': 'Percloroetileno',
        'Phenol': 'Fenol', 'Phosphoric Acid': 'Ácido fosfórico',
        'Potassium Hydroxide': 'Hidróxido de potasio', 'Silver Nitrate': 'Nitrato de plata',
        'Sodium Chloride': 'Cloruro de sodio', 'Sodium Hydroxide': 'Hidróxido de sodio',
        'Sodium Hypochlorite': 'Hipoclorito de sodio', 'Stearic Acid': 'Ácido esteárico',
        'Sulfuric Acid': 'Ácido sulfúrico', 'Tannic Acid': 'Ácido tánico',
        'Tartaric Acid': 'Ácido tartárico', 'Tetrahydrofuran': 'Tetrahidrofurano',
        'Toluene': 'Tolueno', 'Trichloroethylene': 'Tricloroetileno',
        'Trisodium Phosphate': 'Fosfato trisódico', 'Turpentine': 'Trementina',
        'Xylene': 'Xileno',
    },
}

CONC_TERMS = {
    'pure': {'de': 'rein', 'es': 'puro', 'fr': 'pur', 'pt': 'puro', 'zh': '纯'},
    'aqueous': {'de': 'wässrig', 'es': 'acuoso', 'fr': 'aqueux', 'pt': 'aquoso', 'zh': '水溶液'},
    'gas': {'de': 'Gas', 'es': 'gas', 'fr': 'gaz', 'pt': 'gás', 'zh': '气体'},
    'concentrated': {'de': 'konz.', 'es': 'concentrado', 'fr': 'concentré', 'pt': 'concentrado', 'zh': '浓'},
    'solid': {'de': 'fest', 'es': 'sólido', 'fr': 'solide', 'pt': 'sólido', 'zh': '固态'},
    'anhydrous': {'de': 'wasserfrei', 'es': 'anhidro', 'fr': 'anhydre', 'pt': 'anidro', 'zh': '无水'},
}


def esc(s):
    return html.escape(str(s), quote=True)


def conc_label(conc, lang):
    if lang == 'en' or '%' in conc:
        return conc
    return CONC_TERMS.get(conc, {}).get(lang, conc)


def chem_name(en_name, lang):
    if lang == 'en':
        return en_name
    names = CHEM_NAMES.get(lang, {})
    return names.get(en_name, en_name)


def chem_link_base(lang):
    if lang == 'en':
        return '/chemicals/'
    return '/chemicals/%s/' % lang


def stats():
    s = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    for _, _, rating, _, _ in PU_DATA:
        s[rating] += 1
    return s


def build_rows(lang):
    rows = []
    base = chem_link_base(lang)
    for en_name, conc, rating, cas, slug in PU_DATA:
        name = chem_name(en_name, lang)
        label = esc(name)
        if slug:
            label = '<a href="%s%s/" class="underline">%s</a>' % (base, slug, label)
        sub = ''
        if lang not in ('en', 'de') and name != en_name:
            sub = '<div class="text-xs text-gray-500">%s</div>' % esc(en_name)
        elif lang == 'de':
            de_name = chem_name(en_name, 'de')
            if de_name != en_name and de_name != name:
                sub = '<div class="text-xs text-gray-500">%s</div>' % esc(en_name)
        c = conc_label(conc, lang)
        badge = '<span class="rating-%s px-2 py-1 rounded text-xs font-bold">%s</span>' % (rating, rating)
        search = ' '.join([name, en_name, cas or '', c]).lower()
        row = ('<tr class="border-b border-gray-100 hover:bg-gray-50" data-g20="%s" data-s="%s">'
               '<td class="py-3 px-4"><div class="font-medium text-gray-900">%s</div>%s</td>'
               '<td class="py-3 px-4 text-sm text-gray-600">%s</td>'
               '<td class="py-3 px-4 text-center whitespace-nowrap">%s</td>'
               '<td class="py-3 px-4 text-sm text-gray-500 font-mono">%s</td>'
               '</tr>') % (rating, esc(search), label, sub, esc(c) or '&mdash;', badge, esc(cas) if cas else '&mdash;')
        rows.append(row)
    return rows


def analytics_head():
    return '''<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("consent","default",{"analytics_storage":"denied","ad_storage":"denied","ad_user_data":"denied","ad_personalization":"denied","wait_for_update":500,"region":["BE","BG","CZ","DK","DE","EE","IE","GR","ES","FR","HR","IT","CY","LV","LT","LU","HU","MT","NL","AT","PL","PT","RO","SI","SK","FI","SE","GB","CH","IS","LI","NO"]});gtag("consent","default",{"analytics_storage":"granted","ad_storage":"granted","ad_user_data":"granted","ad_personalization":"granted"});</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5861928596436289" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-LTK6VVHYDW"></script>
<script>gtag("js",new Date());gtag("config","G-LTK6VVHYDW");</script>
<script src="https://analytics.ahrefs.com/analytics.js" data-key="xrS32xSgQE4Xp1oL20j7uQ" async></script>'''


def ad_filter():
    return '''<style>ins.adsbygoogle[data-ad-status="unfilled"],.google-auto-placed:has(>ins.adsbygoogle[data-ad-status="unfilled"]),[data-blank-ad],:has(>#compat-table-zone) .google-auto-placed,:has(>#compat-table-zone) ins.adsbygoogle,:has(>#compat-table-zone) iframe[id^="aswift"]{display:none!important}</style>
<script>(function(){var S="data-blank-ad",k=new WeakMap(),t=null,c=0;function b(e){return !e.querySelector("iframe")&&!e.textContent.trim()}function s(){document.querySelectorAll("ins.adsbygoogle,.google-auto-placed").forEach(function(e){var ins=e.tagName==="INS";if(ins&&e.closest(".google-auto-placed"))return;var p=ins?e:(e.querySelector("ins.adsbygoogle")||e);if(!b(e)){k.set(e,0);e.removeAttribute(S);return}if(p.tagName==="INS"&&p.getAttribute("data-adsbygoogle-status")!=="done")return;if(!e.hasAttribute(S)&&e.getBoundingClientRect().height<=0)return;var n=(k.get(e)||0)+1;k.set(e,n);if(n>=2)e.setAttribute(S,"")})}function arm(){if(t)return;c=0;t=setInterval(function(){s();if(++c>=8){clearInterval(t);t=null}},1500)}arm();try{new MutationObserver(function(m){for(var j=0;j<m.length;j++)if(m[j].addedNodes.length){arm();return}}).observe(document.documentElement,{childList:true,subtree:true})}catch(e){}addEventListener("scroll",arm,{passive:true});addEventListener("load",arm)})()</script>'''


def url_for(lang):
    if lang == 'en':
        return 'https://chemicalresistance.org/materials/polyurethane/'
    return 'https://chemicalresistance.org/materials/%s/polyurethane/' % lang


def mat_base(lang):
    if lang == 'en':
        return '/materials/'
    return '/materials/%s/' % lang


def build_page(lang):
    n = len(PU_DATA)
    s = stats()
    rows = build_rows(lang)
    nav = NAV[lang]
    bc = BREADCRUMB[lang]
    sl = STAT_LABELS[lang]
    canonical = url_for(lang)
    mat_url = mat_base(lang)

    hreflang = []
    for ll in ['en', 'de', 'es']:
        hreflang.append('<link rel="alternate" hreflang="%s%s" href="%s">' % (
            'x-default" href="%s">\n<link rel="alternate" hreflang="' % url_for('en') if ll == 'en' else '',
            ll, url_for(ll)))

    title = TITLE[lang].format(n=n)
    desc = DESC[lang].format(n=n)

    jsonld_web = json.dumps({
        "@context": "https://schema.org", "@type": "WebPage",
        "name": "%s Chemical Resistance Chart" % MATERIAL_NAME[lang],
        "description": esc(HERO_TEXT[lang]),
        "url": canonical, "dateModified": "2026-10-29"
    }, ensure_ascii=False, separators=(',', ':'))

    jsonld_tech = json.dumps({
        "@context": "https://schema.org", "@type": "TechArticle",
        "headline": "Polyurethane (PU) Chemical Resistance Chart",
        "description": "Chemical resistance data for Polyurethane (PU) — rated A-D against %d chemicals at 21°C. Material type: Elastomer." % n,
        "url": canonical,
        "author": {"@type": "Organization", "name": "ChemicalResistance.org", "url": "https://chemicalresistance.org"},
        "publisher": {"@type": "Organization", "name": "ChemicalResistance.org", "url": "https://chemicalresistance.org"},
        "about": [{"@type": "Thing", "name": "Polyurethane (PU)", "description": "An elastomer material used in chemical storage and handling"}],
        "keywords": "polyurethane chemical resistance, PU compatibility chart, elastomer chemical resistance"
    }, ensure_ascii=False, separators=(',', ':'))

    jsonld_bc = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": bc[0], "item": "https://chemicalresistance.org/"},
            {"@type": "ListItem", "position": 2, "name": bc[1], "item": "https://chemicalresistance.org%s" % mat_url},
            {"@type": "ListItem", "position": 3, "name": "%s Chemical Resistance Chart" % MATERIAL_NAME[lang],
             "item": canonical}
        ]
    }, ensure_ascii=False, separators=(',', ':'))

    jsonld_ds = json.dumps({
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Polyurethane chemical resistance ratings",
        "url": canonical, "inLanguage": lang,
        "description": "Chemical resistance ratings of Polyurethane (PU) against %d chemicals at 21 °C, by concentration. Ratings A to D. Source: PSI Urethanes (lab-tested), cross-referenced." % n,
        "dateModified": "2026-10-29",
        "variableMeasured": ["Resistance rating at 21 °C"],
        "creator": {"@type": "Organization", "name": "ChemicalResistance.org", "url": "https://chemicalresistance.org/"},
        "license": "https://creativecommons.org/licenses/by-nc/4.0/",
        "isBasedOn": {"@type": "CreativeWork", "name": "Polyurethane Chemical Compatibility Chart",
                      "publisher": {"@type": "Organization", "name": "PSI Urethanes", "url": "https://psiurethanes.com"}}
    }, ensure_ascii=False, separators=(',', ':'))

    if lang in ('fr', 'pt', 'zh'):
        noindex = '\n    <meta name="robots" content="noindex,follow">'
    else:
        noindex = ''

    return '''<!DOCTYPE html>
<html lang="{lang}">
<head>
{analytics}
{adfilt}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">{noindex}
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="canonical" href="{canonical}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:type" content="article">
    <meta property="og:image" content="https://chemicalresistance.org/og-image.png">
    <link rel="stylesheet" href="/css/tailwind.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@1.48.0/dist/umd/lucide.min.js"></script>
    <style>
        * {{ font-family: 'Inter', sans-serif; }}
        body {{ background: #f8fafc; }}
        .rating-A{{background:#15803d;color:#fff}}
        .rating-B{{background:#1d4ed8;color:#fff}}
        .rating-C{{background:#d97706;color:#111827}}
        .rating-D{{background:#b91c1c;color:#fff}}
        .rating-NR{{background:#e5e7eb;color:#374151}}

        #compat-table-zone .google-auto-placed,
        #compat-table-zone ins.adsbygoogle,
        #chemTable .google-auto-placed,
        #chemTable ins.adsbygoogle {{ display: none !important; }}
    </style>
<script type="application/ld+json">{jsonld_web}</script>
<script type="application/ld+json">{jsonld_tech}</script>
{hreflang}
<script type="application/ld+json" id="cr-breadcrumb">{jsonld_bc}</script>
<script type="application/ld+json" id="cr-dataset">{jsonld_ds}</script>
</head>
<body class="text-gray-700 min-h-screen">
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="/" class="flex items-center gap-2">
                <img src="/logos/logo-icon-128x128.png" alt="ChemicalResistance" class="w-10 h-10 rounded-xl">
                <div>
                    <div class="font-bold text-gray-900">ChemicalResistance.org</div>
                    <div class="text-xs text-gray-500 hidden sm:block">{tagline}</div>
                </div>
            </a>
            <div class="flex items-center gap-3 text-sm">
                <nav class="hidden md:flex items-center gap-4">
                    <a href="/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_lookup}</a>
                    <a href="{mat_url}" class="text-emerald-600 font-medium">{nav_materials}</a>
                    <a href="/chemicals/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_chemicals}</a>
                    <a href="/compare/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_compare}</a>
                    <a href="/charts/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_charts}</a>
                    <a href="/storage-compatibility/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_storage}</a>
                    <a href="/sds-decoder/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_sds}</a>
                    <a href="/viscosity/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_viscosity}</a>
                    <a href="/about/" class="text-gray-600 hover:text-gray-900 hover:underline">{nav_about}</a>
                </nav>
                <button id="mobileMenuBtn" class="md:hidden p-2 rounded-lg hover:bg-gray-100" aria-label="Menu">
                    <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                </button>
            </div>
        </div>
        <div id="mobileMenu" class="hidden md:hidden border-t border-gray-200 bg-white">
            <nav class="max-w-7xl mx-auto px-4 py-3 flex flex-col gap-2">
                <a href="/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_lookup}</a>
                <a href="{mat_url}" class="py-2 px-3 rounded-lg text-emerald-700 bg-emerald-50 font-medium">{nav_materials}</a>
                <a href="/chemicals/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_chemicals}</a>
                <a href="/compare/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_compare}</a>
                <a href="/charts/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_charts}</a>
                <a href="/storage-compatibility/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_storage}</a>
                <a href="/sds-decoder/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_sds}</a>
                <a href="/viscosity/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_viscosity}</a>
                <a href="/about/" class="py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50">{nav_about}</a>
            </nav>
        </div>
    </header>
    <script>
        document.getElementById('mobileMenuBtn').addEventListener('click', function() {{
            document.getElementById('mobileMenu').classList.toggle('hidden');
        }});
    </script>

    <section class="bg-gradient-to-b from-purple-50 to-white px-4 py-8 md:py-12">
        <div class="max-w-4xl mx-auto">
            <div class="flex items-center gap-2 text-sm text-purple-600 mb-3">
                <a href="/" class="hover:underline">{bc_home}</a>
                <span>&rsaquo;</span>
                <a href="{mat_url}" class="hover:underline">{bc_materials}</a>
                <span>&rsaquo;</span>
                <span class="text-gray-600">{bc_polyurethane}</span>
            </div>
            <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-3">{mat_name} Chemical Resistance Chart</h1>
            <p class="text-lg text-gray-600 mb-4">{hero_text}</p>
            <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">{n} {chem_word}</span>
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">21 °C data</span>
            </div>
        </div>
    </section>

    <section class="px-4 py-6">
        <div class="max-w-4xl mx-auto grid grid-cols-4 gap-4 text-center">
            <div>
                <div class="text-2xl font-bold text-emerald-600" id="statA">{sA}</div>
                <div class="text-sm text-gray-500">{lA}</div>
            </div>
            <div>
                <div class="text-2xl font-bold text-blue-600" id="statB">{sB}</div>
                <div class="text-sm text-gray-500">{lB}</div>
            </div>
            <div>
                <div class="text-2xl font-bold text-amber-600" id="statC">{sC}</div>
                <div class="text-sm text-gray-500">{lC}</div>
            </div>
            <div>
                <div class="text-2xl font-bold text-red-600" id="statD">{sD}</div>
                <div class="text-sm text-gray-500">{lD}</div>
            </div>
        </div>
    </section>

    <!-- pu-note:start -->
<section class="px-4 pt-6"><div class="max-w-5xl mx-auto"><p style="background:#faf5ff;border:1px solid #c084fc;border-radius:.75rem;padding:1rem;color:#581c87;font-size:.95rem;line-height:1.6;margin:0">{note_text}</p></div></section>
<!-- pu-note:end -->
    <section class="px-4 py-8">
        <div class="max-w-6xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
                <div class="flex flex-col md:flex-row gap-4">
                    <div class="flex-1">
                        <label class="block text-sm font-medium text-gray-700 mb-1">{search_label}</label>
                        <input type="text" id="searchInput" placeholder="e.g. Acetone, Sulfuric acid..."
                            class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-100 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">{filter_label}</label>
                        <select id="ratingFilter" class="px-4 py-2 border border-gray-200 rounded-lg focus:border-purple-500 outline-none">
                            <option value="all">{all_ratings}</option>
                            <option value="A">A - Excellent</option>
                            <option value="B">B - Good</option>
                            <option value="AB">A &amp; B (Compatible)</option>
                            <option value="C">C - Limited</option>
                            <option value="D">D - Not recommended</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="mb-4 text-sm text-gray-500">
                {showing} <span id="resultCount" class="font-semibold text-gray-700">{n}</span> {chem_word}
            </div>
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div id="compat-table-zone" class="overflow-x-auto">
                    <table class="w-full min-w-[600px]">
<thead>
                            <tr class="bg-gray-50 text-left text-sm">
                                <th class="py-3 px-4 font-semibold text-gray-600">{chem_th}</th>
                                <th class="py-3 px-4 font-semibold text-gray-600">{conc_th}</th>
                                <th class="py-3 px-4 font-semibold text-gray-600 text-center">{rating_th}</th>
                                <th class="py-3 px-4 font-semibold text-gray-600">CAS</th>
                            </tr>
                        </thead>
<tbody id="chemTable" class="divide-y divide-gray-100">
{rows}
</tbody>
</table>
<p id="cr-table-note" class="px-4 py-3 text-xs text-gray-500">{table_note}</p>
                </div>
            </div>
        </div>
    </section>

    <section class="px-4 py-12 bg-white border-t border-gray-200">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">{prop_label}</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <div class="space-y-4">
                    <div class="flex justify-between py-2 border-b border-gray-100">
                        <span class="text-gray-600">Full Name</span>
                        <span class="font-medium text-gray-900">Polyurethane (PU/PUR)</span>
                    </div>
                    <div class="flex justify-between py-2 border-b border-gray-100">
                        <span class="text-gray-600">Max Temperature</span>
                        <span class="font-medium text-gray-900">80–90 °C (176–194 °F)</span>
                    </div>
                    <div class="flex justify-between py-2 border-b border-gray-100">
                        <span class="text-gray-600">Shore Hardness</span>
                        <span class="font-medium text-gray-900">20A–75D</span>
                    </div>
                </div>
                <div class="space-y-4">
                    <div class="flex justify-between py-2 border-b border-gray-100">
                        <span class="text-gray-600">Min Temperature</span>
                        <span class="font-medium text-gray-900">−40 °C (−40 °F)</span>
                    </div>
                    <div class="flex justify-between py-2 border-b border-gray-100">
                        <span class="text-gray-600">Key Property</span>
                        <span class="font-medium text-gray-900">Abrasion resistance, load bearing</span>
                    </div>
                    <div class="flex justify-between py-2 border-b border-gray-100">
                        <span class="text-gray-600">Density</span>
                        <span class="font-medium text-gray-900">1.05–1.25 g/cm³</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="px-4 py-12">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">{app_label}</h2>
            <div class="grid md:grid-cols-3 gap-4">
                <div class="bg-white p-5 rounded-xl border border-gray-200">
                    <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
                        <i data-lucide="cog" class="w-5 h-5 text-purple-600"></i>
                    </div>
                    <h3 class="font-bold text-gray-900 mb-1">Industrial Rollers</h3>
                    <p class="text-sm text-gray-600">Conveyor rollers, printing rollers, drive wheels</p>
                </div>
                <div class="bg-white p-5 rounded-xl border border-gray-200">
                    <div class="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center mb-3">
                        <i data-lucide="shield" class="w-5 h-5 text-amber-600"></i>
                    </div>
                    <h3 class="font-bold text-gray-900 mb-1">Seals &amp; Gaskets</h3>
                    <p class="text-sm text-gray-600">Hydraulic seals, O-rings, wear rings, scrapers</p>
                </div>
                <div class="bg-white p-5 rounded-xl border border-gray-200">
                    <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
                        <i data-lucide="layers" class="w-5 h-5 text-blue-600"></i>
                    </div>
                    <h3 class="font-bold text-gray-900 mb-1">Coatings &amp; Linings</h3>
                    <p class="text-sm text-gray-600">Tank linings, pipe coatings, floor coatings</p>
                </div>
            </div>
        </div>
    </section>

    <section class="px-4 py-12 bg-purple-50 border-t border-purple-100">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">{avoid_label}</h2>
            <p class="text-gray-600 mb-4">{mat_name} may degrade when exposed to:</p>
            <div class="grid md:grid-cols-2 gap-4">
                <ul class="space-y-2">
                    <li class="flex items-center gap-2 text-gray-700">
                        <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                        Ketones (acetone, MEK)
                    </li>
                    <li class="flex items-center gap-2 text-gray-700">
                        <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                        Chlorinated solvents (TCE, carbon tet)
                    </li>
                    <li class="flex items-center gap-2 text-gray-700">
                        <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                        Aromatic solvents (benzene, toluene, xylene)
                    </li>
                </ul>
                <ul class="space-y-2">
                    <li class="flex items-center gap-2 text-gray-700">
                        <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                        Strong acids (concentrated HCl, HNO₃)
                    </li>
                    <li class="flex items-center gap-2 text-gray-700">
                        <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                        Esters (ethyl acetate)
                    </li>
                    <li class="flex items-center gap-2 text-gray-700">
                        <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                        Hot water above 80 °C (long-term)
                    </li>
                </ul>
            </div>
            <div class="mt-4 p-3 bg-white rounded-lg border border-purple-200">
                <p class="text-sm text-gray-600"><strong>Tip:</strong> For ketones and esters, use PTFE or FEP. For aggressive acids at high temperatures, use PVDF. For oil-based applications, PU outperforms EPDM and silicone.</p>
            </div>
        </div>
    </section>

    <section class="px-4 py-12 bg-white border-t border-gray-200">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">{compare_label}</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <a href="{mat_url}epdm/" class="p-4 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors text-center">
                    <div class="font-bold text-gray-900">EPDM</div>
                    <div class="text-xs text-gray-500">Water/outdoor</div>
                </a>
                <a href="{mat_url}viton/" class="p-4 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors text-center">
                    <div class="font-bold text-gray-900">Viton</div>
                    <div class="text-xs text-gray-500">Chemical seal</div>
                </a>
                <a href="{mat_url}nbr/" class="p-4 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors text-center">
                    <div class="font-bold text-gray-900">NBR</div>
                    <div class="text-xs text-gray-500">Oil seal</div>
                </a>
                <a href="{mat_url}silicone/" class="p-4 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors text-center">
                    <div class="font-bold text-gray-900">Silicone</div>
                    <div class="text-xs text-gray-500">Temperature range</div>
                </a>
            </div>
        </div>
    </section>

    <footer class="bg-gray-900 text-gray-400 py-8 px-4">
        <div class="max-w-5xl mx-auto text-center text-sm">
            <p>&copy; 2026 ChemicalResistance.org &mdash; Free chemical compatibility tool</p>
            <p class="mt-2">Data sources: B&uuml;rkle, PSI Urethanes, industry standards</p>
        </div>
    <p class="mt-3 text-xs text-center"><a href="/privacy.html" class="hover:underline">Privacy</a> <span class="mx-1">&middot;</span> <a href="/terms.html" class="hover:underline">Terms</a></p>
</footer>
    <script>
    (function () {{
        var rows = [].slice.call(document.querySelectorAll('#chemTable tr[data-s]'));
        var search = document.getElementById('searchInput');
        var rating = document.getElementById('ratingFilter');
        var count = document.getElementById('resultCount');
        function apply() {{
            var q = search ? search.value.toLowerCase() : '';
            var r = rating ? rating.value : 'all';
            var n = 0;
            rows.forEach(function (tr) {{
                var g = tr.getAttribute('data-g20') || '';
                var ok = (!q || tr.getAttribute('data-s').indexOf(q) > -1) &&
                    (r === 'all' || (r === 'AB' ? (g === 'A' || g === 'B') : g === r));
                tr.style.display = ok ? '' : 'none';
                if (ok) n++;
            }});
            if (count) count.textContent = n;
        }}
        if (search) search.addEventListener('input', apply);
        if (rating) rating.addEventListener('change', apply);
        window.filterTable = apply;
        window.loadMore = function () {{}};
        if (window.lucide) lucide.createIcons();
    }})();
    </script>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "cba547e85ee54e0f9cdc27e68405eead"}}'></script>
</body>
</html>'''.format(
        lang=lang,
        analytics=analytics_head(),
        adfilt=ad_filter(),
        title=esc(title),
        desc=desc,
        noindex=noindex,
        canonical=canonical,
        hreflang='\n'.join(hreflang),
        jsonld_web=jsonld_web,
        jsonld_tech=jsonld_tech,
        jsonld_bc=jsonld_bc,
        jsonld_ds=jsonld_ds,
        tagline=esc(nav['tagline']),
        nav_lookup=esc(nav['lookup']),
        nav_materials=esc(nav['materials']),
        nav_chemicals=esc(nav['chemicals']),
        nav_compare=esc(nav['compare']),
        nav_charts=esc(nav['charts']),
        nav_storage=esc(nav['storage']),
        nav_sds=esc(nav['sds']),
        nav_viscosity=esc(nav['viscosity']),
        nav_about=esc(nav['about']),
        mat_url=mat_url,
        bc_home=esc(bc[0]),
        bc_materials=esc(bc[1]),
        bc_polyurethane=esc(bc[2]),
        mat_name=esc(MATERIAL_NAME[lang]),
        hero_text=esc(HERO_TEXT[lang]),
        n=n,
        chem_word=esc(CHEMICALS_WORD[lang]),
        sA=s['A'], sB=s['B'], sC=s['C'], sD=s['D'],
        lA=esc(sl[0]), lB=esc(sl[1]), lC=esc(sl[2]), lD=esc(sl[3]),
        note_text=NOTE_TEXT[lang],
        search_label=esc(SEARCH_LABEL[lang]),
        filter_label=esc(FILTER_LABEL[lang]),
        all_ratings=esc(ALL_RATINGS[lang]),
        showing=esc(SHOWING[lang]),
        chem_th=esc(CHEMICAL_TH[lang]),
        conc_th=esc(CONC_TH[lang]),
        rating_th=esc(RATING_TH[lang]),
        rows='\n'.join(rows),
        table_note=esc(TABLE_NOTE[lang]),
        prop_label=esc(PROP_LABEL[lang]),
        app_label=esc(APP_LABEL[lang]),
        avoid_label=esc(AVOID_LABEL[lang]),
        compare_label=esc(COMPARE_LABEL[lang]),
    )


def main():
    check = '--check' in sys.argv
    changed = 0
    for lang in LANGS:
        if lang == 'en':
            rel = 'materials/polyurethane/index.html'
        else:
            rel = 'materials/%s/polyurethane/index.html' % lang
        path = os.path.join(ROOT, rel)
        page = build_page(lang)
        d = os.path.dirname(path)
        if not os.path.isdir(d) and not check:
            os.makedirs(d, exist_ok=True)
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                if f.read() == page:
                    continue
        changed += 1
        if not check:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(page)
        print('%s  %s' % ('would write' if check else 'wrote', rel))
    print('%s %d polyurethane pages' % ('would change' if check else 'wrote', changed))


if __name__ == '__main__':
    main()
