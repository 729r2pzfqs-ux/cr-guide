#!/usr/bin/env python3
"""Strings for the generated chemical and pair pages, in the six site languages.

Sentences are built as "label: list" wherever a chemical or material name is
inserted, so no language needs articles or case endings around a name.
"""

LANGS = ['en', 'de', 'es', 'fr', 'pt', 'zh']

#: languages whose chemical pages are indexable and carry hreflang
INDEXED_LANGS = ['en', 'de', 'es']

MATERIAL_NAMES = {
    'HDPE': {'en': 'HDPE'},
    'LDPE': {'en': 'LDPE'},
    'PP': {'en': 'PP'},
    'PVC_HART': {'en': 'PVC Rigid', 'de': 'PVC hart', 'es': 'PVC rígido', 'fr': 'PVC rigide',
                 'pt': 'PVC rígido', 'zh': '硬质PVC'},
    'PVC_WEICH': {'en': 'PVC Flexible', 'de': 'PVC weich', 'es': 'PVC flexible', 'fr': 'PVC souple',
                  'pt': 'PVC flexível', 'zh': '软质PVC'},
    'PMP': {'en': 'PMP'},
    'PS': {'en': 'Polystyrene', 'de': 'Polystyrol', 'es': 'Poliestireno', 'fr': 'Polystyrène',
           'pt': 'Poliestireno', 'zh': '聚苯乙烯'},
    'SAN': {'en': 'SAN'},
    'PC': {'en': 'Polycarbonate', 'de': 'Polycarbonat', 'es': 'Policarbonato', 'fr': 'Polycarbonate',
           'pt': 'Policarbonato', 'zh': '聚碳酸酯'},
    'PETG': {'en': 'PETG'},
    'POM': {'en': 'Acetal (POM)', 'de': 'POM (Acetal)', 'es': 'Acetal (POM)', 'fr': 'Acétal (POM)',
            'pt': 'Acetal (POM)', 'zh': '聚甲醛 (POM)'},
    'PA': {'en': 'Nylon (PA)', 'de': 'Polyamid (PA)', 'es': 'Nailon (PA)', 'fr': 'Nylon (PA)',
           'pt': 'Náilon (PA)', 'zh': '尼龙 (PA)'},
    'PSU': {'en': 'Polysulfone', 'de': 'Polysulfon', 'es': 'Polisulfona', 'fr': 'Polysulfone',
            'pt': 'Polissulfona', 'zh': '聚砜'},
    'PTFE': {'en': 'PTFE'},
    'FEP': {'en': 'FEP'},
    'PVDF': {'en': 'PVDF'},
    'ECTFE_ETFE': {'en': 'ECTFE/ETFE'},
    'EPDM': {'en': 'EPDM'},
    'FPM': {'en': 'Viton (FPM)'},
    'NBR': {'en': 'NBR'},
    'SI': {'en': 'Silicone', 'de': 'Silikon', 'es': 'Silicona', 'fr': 'Silicone', 'pt': 'Silicone',
           'zh': '硅橡胶'},
    'V4A': {'en': 'SS 316', 'de': 'Edelstahl 316', 'es': 'Acero inox. 316', 'fr': 'Inox 316',
            'pt': 'Aço inox 316', 'zh': '316不锈钢'},
    'V2A': {'en': 'SS 304', 'de': 'Edelstahl 304', 'es': 'Acero inox. 304', 'fr': 'Inox 304',
            'pt': 'Aço inox 304', 'zh': '304不锈钢'},
    'AL': {'en': 'Aluminium', 'de': 'Aluminium', 'es': 'Aluminio', 'fr': 'Aluminium',
           'pt': 'Alumínio', 'zh': '铝'},
}


def material_name(code, lang):
    names = MATERIAL_NAMES[code]
    return names.get(lang, names['en'])


#: What the source means by each material, from its own legend.
MATERIAL_FULL = {
    'HDPE': 'High-density polyethylene', 'LDPE': 'Low-density polyethylene',
    'PP': 'Polypropylene', 'PVC_HART': 'Rigid (unplasticised) polyvinyl chloride',
    'PVC_WEICH': 'Flexible (plasticised) polyvinyl chloride',
    'PMP': 'Polymethylpentene (TPX)', 'PS': 'Polystyrene', 'SAN': 'Styrene-acrylonitrile',
    'PC': 'Polycarbonate', 'PETG': 'Polyethylene terephthalate glycol (co-polyester)',
    'POM': 'Polyoxymethylene (acetal)', 'PA': 'Polyamide (nylon)', 'PSU': 'Polysulfone',
    'PTFE': 'Polytetrafluoroethylene', 'FEP': 'Fluorinated ethylene propylene',
    'PVDF': 'Polyvinylidene fluoride',
    'ECTFE_ETFE': 'Ethylene chlorotrifluoroethylene / ethylene tetrafluoroethylene',
    'EPDM': 'Ethylene propylene diene rubber', 'FPM': 'Fluoroelastomer (FKM/FPM)',
    'NBR': 'Nitrile butadiene rubber', 'SI': 'Silicone rubber',
    'V4A': 'Stainless steel 1.4401 (AISI 316)', 'V2A': 'Stainless steel 1.4301 (AISI 304)',
    'AL': 'Aluminium',
}

# German concentration vocabulary of the source -> site languages.
CONC_TERMS = {
    'gesättigt': {'en': 'saturated', 'es': 'saturado', 'fr': 'saturé', 'pt': 'saturado', 'zh': '饱和'},
    'wässrig': {'en': 'aqueous', 'es': 'acuoso', 'fr': 'aqueux', 'pt': 'aquoso', 'zh': '水溶液'},
    'techn. rein': {'en': 'technical grade', 'es': 'grado técnico', 'fr': 'qualité technique',
                    'pt': 'grau técnico', 'zh': '工业纯'},
    'techn. üblich': {'en': 'usual technical grade', 'es': 'grado técnico habitual',
                      'fr': 'qualité technique usuelle', 'pt': 'grau técnico usual', 'zh': '常用工业级'},
    'jede': {'en': 'any concentration', 'es': 'cualquier concentración',
             'fr': 'toute concentration', 'pt': 'qualquer concentração', 'zh': '任意浓度'},
    'verdünnt': {'en': 'dilute', 'es': 'diluido', 'fr': 'dilué', 'pt': 'diluído', 'zh': '稀溶液'},
    'gemahlen': {'en': 'ground', 'es': 'molido', 'fr': 'moulu', 'pt': 'moído', 'zh': '研磨'},
    'konz.': {'en': 'concentrated', 'es': 'concentrado', 'fr': 'concentré', 'pt': 'concentrado',
              'zh': '浓'},
    'gering': {'en': 'low concentration', 'es': 'baja concentración', 'fr': 'faible concentration',
               'pt': 'baixa concentração', 'zh': '低浓度'},
    'flüssig': {'en': 'liquid', 'es': 'líquido', 'fr': 'liquide', 'pt': 'líquido', 'zh': '液态'},
    'fest': {'en': 'solid', 'es': 'sólido', 'fr': 'solide', 'pt': 'sólido', 'zh': '固态'},
    'wasserfrei': {'en': 'anhydrous', 'es': 'anhidro', 'fr': 'anhydre', 'pt': 'anidro', 'zh': '无水'},
    'Pulver': {'en': 'powder', 'es': 'polvo', 'fr': 'poudre', 'pt': 'pó', 'zh': '粉末'},
    'gasförmig': {'en': 'gaseous', 'es': 'gaseoso', 'fr': 'gazeux', 'pt': 'gasoso', 'zh': '气态'},
    'Gas': {'en': 'gas', 'es': 'gas', 'fr': 'gaz', 'pt': 'gás', 'zh': '气体'},
    'alkoholisch': {'en': 'alcoholic solution', 'es': 'solución alcohólica',
                    'fr': 'solution alcoolique', 'pt': 'solução alcoólica', 'zh': '醇溶液'},
    'geschmolzen': {'en': 'molten', 'es': 'fundido', 'fr': 'fondu', 'pt': 'fundido', 'zh': '熔融'},
    'ölhaltig': {'en': 'containing oil', 'es': 'con aceite', 'fr': "contenant de l'huile",
                 'pt': 'com óleo', 'zh': '含油'},
    'rein': {'en': 'pure', 'es': 'puro', 'fr': 'pur', 'pt': 'puro', 'zh': '纯'},
    'rauchend': {'en': 'fuming', 'es': 'fumante', 'fr': 'fumant', 'pt': 'fumegante', 'zh': '发烟'},
    'feucht': {'en': 'moist', 'es': 'húmedo', 'fr': 'humide', 'pt': 'úmido', 'zh': '潮湿'},
    'trocken': {'en': 'dry', 'es': 'seco', 'fr': 'sec', 'pt': 'seco', 'zh': '干燥'},
    'nass': {'en': 'wet', 'es': 'húmedo', 'fr': 'humide', 'pt': 'úmido', 'zh': '湿'},
    'Kristalle': {'en': 'crystals', 'es': 'cristales', 'fr': 'cristaux', 'pt': 'cristais', 'zh': '晶体'},
    'in Wasser': {'en': 'in water', 'es': 'en agua', 'fr': "dans l'eau", 'pt': 'em água', 'zh': '水中'},
    'bis': {'en': 'up to', 'es': 'hasta', 'fr': "jusqu'à", 'pt': 'até', 'zh': '至'},
}


def conc_label(conc, lang):
    """Localised concentration; empty string stays empty."""
    if not conc:
        return ''
    out = conc
    if lang != 'de':
        for de in sorted(CONC_TERMS, key=len, reverse=True):
            if de in out:
                out = out.replace(de, CONC_TERMS[de][lang])
    out = out.replace('%', ' %').replace('  %', ' %')
    return ' '.join(out.split())


HAZARD_SYMBOLS = {
    'E': {'en': 'explosive', 'de': 'explosiv', 'es': 'explosivo', 'fr': 'explosif',
          'pt': 'explosivo', 'zh': '爆炸性'},
    'O': {'en': 'oxidising', 'de': 'brandfördernd', 'es': 'comburente', 'fr': 'comburant',
          'pt': 'comburente', 'zh': '氧化性'},
    'F': {'en': 'flammable', 'de': 'entzündlich', 'es': 'inflamable', 'fr': 'inflammable',
          'pt': 'inflamável', 'zh': '易燃'},
    'F+': {'en': 'extremely flammable', 'de': 'hochentzündlich', 'es': 'extremadamente inflamable',
           'fr': 'extrêmement inflammable', 'pt': 'extremamente inflamável', 'zh': '极易燃'},
    'T': {'en': 'toxic', 'de': 'giftig', 'es': 'tóxico', 'fr': 'toxique', 'pt': 'tóxico', 'zh': '有毒'},
    'T+': {'en': 'very toxic', 'de': 'sehr giftig', 'es': 'muy tóxico', 'fr': 'très toxique',
           'pt': 'muito tóxico', 'zh': '剧毒'},
    'C': {'en': 'corrosive', 'de': 'ätzend', 'es': 'corrosivo', 'fr': 'corrosif',
          'pt': 'corrosivo', 'zh': '腐蚀性'},
    'Xn': {'en': 'harmful', 'de': 'gesundheitsschädlich', 'es': 'nocivo', 'fr': 'nocif',
           'pt': 'nocivo', 'zh': '有害'},
    'Xi': {'en': 'irritant', 'de': 'reizend', 'es': 'irritante', 'fr': 'irritant',
           'pt': 'irritante', 'zh': '刺激性'},
    'N': {'en': 'dangerous for the environment', 'de': 'umweltgefährlich',
          'es': 'peligroso para el medio ambiente', 'fr': "dangereux pour l'environnement",
          'pt': 'perigoso para o ambiente', 'zh': '危害环境'},
}


def hazard_text(hazard, lang):
    """'F, Xn' -> 'F (flammable), Xn (harmful)'. Unknown symbols are dropped."""
    parts = []
    for sym in [s.strip().strip('()') for s in hazard.replace('+', '+ ').split(',')]:
        sym = sym.replace(' ', '')
        key = sym if sym in HAZARD_SYMBOLS else sym.rstrip('+')
        if key in HAZARD_SYMBOLS:
            parts.append('%s (%s)' % (key, HAZARD_SYMBOLS[key][lang]))
    return ', '.join(parts)


T = {
    'site_tagline': {
        'en': 'Chemical compatibility database', 'de': 'Chemische Beständigkeitsdatenbank',
        'es': 'Base de datos de resistencia química', 'fr': 'Base de données de résistance chimique',
        'pt': 'Banco de dados de resistência química', 'zh': '化学兼容性数据库'},
    'home': {'en': 'Home', 'de': 'Startseite', 'es': 'Inicio', 'fr': 'Accueil', 'pt': 'Início',
             'zh': '首页'},
    'chemicals': {'en': 'Chemicals', 'de': 'Chemikalien', 'es': 'Productos químicos',
                  'fr': 'Produits chimiques', 'pt': 'Produtos químicos', 'zh': '化学品'},
    'h1_chem': {
        'en': '{chem} Chemical Resistance', 'de': '{chem}: Chemische Beständigkeit',
        'es': '{chem}: resistencia química', 'fr': '{chem} : résistance chimique',
        'pt': '{chem}: resistência química', 'zh': '{chem} 耐化学性'},
    'title_chem': {
        'en': '{chem} Chemical Resistance Chart: {n} Materials',
        'de': '{chem}: Beständigkeit von {n} Werkstoffen',
        'es': '{chem}: resistencia química de {n} materiales',
        'fr': '{chem} : résistance chimique de {n} matériaux',
        'pt': '{chem}: resistência química de {n} materiais',
        'zh': '{chem} 耐化学性表：{n} 种材料'},
    'title_chem_short': {
        'en': '{chem} Chemical Resistance Chart', 'de': '{chem}: Chemische Beständigkeit',
        'es': '{chem}: resistencia química', 'fr': '{chem} : résistance chimique',
        'pt': '{chem}: resistência química', 'zh': '{chem} 耐化学性表'},
    'lead_chem': {
        'en': 'Resistance ratings for {n} plastics, elastomers and metals at 20 °C and 50 °C.',
        'de': 'Beständigkeitsbewertungen für {n} Kunststoffe, Elastomere und Metalle bei 20 °C und 50 °C.',
        'es': 'Clasificaciones de resistencia de {n} plásticos, elastómeros y metales a 20 °C y 50 °C.',
        'fr': 'Évaluations de résistance de {n} plastiques, élastomères et métaux à 20 °C et 50 °C.',
        'pt': 'Classificações de resistência de {n} plásticos, elastômeros e metais a 20 °C e 50 °C.',
        'zh': '{n} 种塑料、弹性体和金属在 20 °C 和 50 °C 下的耐受等级。'},
    'lead_variants': {
        'en': 'Listed at {k} concentrations, because the rating depends on it.',
        'de': 'Für {k} Konzentrationen aufgeführt, da die Bewertung davon abhängt.',
        'es': 'Se indican {k} concentraciones, porque la clasificación depende de ellas.',
        'fr': 'Indiqué pour {k} concentrations, car l’évaluation en dépend.',
        'pt': 'Listado para {k} concentrações, pois a classificação depende delas.',
        'zh': '列出 {k} 种浓度，因为等级随浓度变化。'},
    'facts': {'en': 'Substance', 'de': 'Stoffdaten', 'es': 'Sustancia', 'fr': 'Substance',
              'pt': 'Substância', 'zh': '物质信息'},
    'cas': {'en': 'CAS number', 'de': 'CAS-Nummer', 'es': 'Número CAS', 'fr': 'Numéro CAS',
            'pt': 'Número CAS', 'zh': 'CAS 号'},
    'formula': {'en': 'Formula', 'de': 'Formel', 'es': 'Fórmula', 'fr': 'Formule', 'pt': 'Fórmula',
                'zh': '分子式'},
    'hazard': {'en': 'Hazard symbols in the source', 'de': 'Gefahrensymbole laut Quelle',
               'es': 'Símbolos de peligro en la fuente', 'fr': 'Symboles de danger dans la source',
               'pt': 'Símbolos de perigo na fonte', 'zh': '原始资料中的危险符号'},
    'hazard_note': {
        'en': 'pre-GHS European symbols; check the current safety data sheet',
        'de': 'europäische Symbole vor GHS; aktuelles Sicherheitsdatenblatt prüfen',
        'es': 'símbolos europeos anteriores al SGA; consulte la ficha de datos de seguridad vigente',
        'fr': 'symboles européens antérieurs au SGH ; consultez la fiche de données de sécurité en vigueur',
        'pt': 'símbolos europeus anteriores ao GHS; consulte a ficha de segurança atual',
        'zh': 'GHS 之前的欧洲符号；请查阅现行安全数据表'},
    'flammable': {'en': 'Flammable', 'de': 'Entzündlich', 'es': 'Inflamable', 'fr': 'Inflammable',
                  'pt': 'Inflamável', 'zh': '易燃'},
    'yes': {'en': 'yes', 'de': 'ja', 'es': 'sí', 'fr': 'oui', 'pt': 'sim', 'zh': '是'},
    'aliases': {'en': 'Also listed as', 'de': 'Auch aufgeführt als', 'es': 'También figura como',
                'fr': 'Également répertorié sous', 'pt': 'Também listado como', 'zh': '别名'},
    'source_name': {'en': 'Name in the source (German)', 'de': 'Name in der Quelle',
                    'es': 'Nombre en la fuente (alemán)', 'fr': 'Nom dans la source (allemand)',
                    'pt': 'Nome na fonte (alemão)', 'zh': '原始资料名称（德语）'},
    'concentrations': {'en': 'Concentrations listed', 'de': 'Aufgeführte Konzentrationen',
                       'es': 'Concentraciones indicadas', 'fr': 'Concentrations indiquées',
                       'pt': 'Concentrações listadas', 'zh': '所列浓度'},
    'conc_unspecified': {
        'en': 'concentration not stated', 'de': 'Konzentration nicht angegeben',
        'es': 'concentración no indicada', 'fr': 'concentration non précisée',
        'pt': 'concentração não indicada', 'zh': '未注明浓度'},
    'glance': {'en': 'At a glance', 'de': 'Auf einen Blick', 'es': 'De un vistazo',
               'fr': 'En bref', 'pt': 'Resumo', 'zh': '概览'},
    'glance_basis': {
        'en': 'Based on the row for {conc}, 20 °C.', 'de': 'Grundlage: Zeile für {conc}, 20 °C.',
        'es': 'Según la fila para {conc}, 20 °C.', 'fr': 'D’après la ligne pour {conc}, 20 °C.',
        'pt': 'Com base na linha para {conc}, 20 °C.', 'zh': '依据：{conc}，20 °C。'},
    'glance_basis_plain': {
        'en': 'Ratings at 20 °C.', 'de': 'Bewertungen bei 20 °C.', 'es': 'Clasificaciones a 20 °C.',
        'fr': 'Évaluations à 20 °C.', 'pt': 'Classificações a 20 °C.', 'zh': '20 °C 下的等级。'},
    'rated_A': {'en': 'Rated A, very good resistance', 'de': 'Bewertung A, sehr gut beständig',
                'es': 'Clasificación A, resistencia muy buena', 'fr': 'Note A, très bonne résistance',
                'pt': 'Classificação A, resistência muito boa', 'zh': 'A 级，耐受性很好'},
    'rated_B': {'en': 'Rated B, good resistance', 'de': 'Bewertung B, gut beständig',
                'es': 'Clasificación B, buena resistencia', 'fr': 'Note B, bonne résistance',
                'pt': 'Classificação B, boa resistência', 'zh': 'B 级，耐受性良好'},
    'rated_C': {'en': 'Rated C, limited resistance', 'de': 'Bewertung C, eingeschränkt beständig',
                'es': 'Clasificación C, resistencia limitada', 'fr': 'Note C, résistance limitée',
                'pt': 'Classificação C, resistência limitada', 'zh': 'C 级，耐受性有限'},
    'rated_D': {'en': 'Rated D, not resistant', 'de': 'Bewertung D, nicht beständig',
                'es': 'Clasificación D, no resistente', 'fr': 'Note D, non résistant',
                'pt': 'Classificação D, não resistente', 'zh': 'D 级，不耐受'},
    'no_data_for': {'en': 'No data in the source', 'de': 'Keine Angabe in der Quelle',
                    'es': 'Sin datos en la fuente', 'fr': 'Aucune donnée dans la source',
                    'pt': 'Sem dados na fonte', 'zh': '原始资料无数据'},
    'worse_at_50': {
        'en': 'Rated lower at 50 °C than at 20 °C', 'de': 'Bei 50 °C schlechter bewertet als bei 20 °C',
        'es': 'Clasificación inferior a 50 °C que a 20 °C', 'fr': 'Note plus basse à 50 °C qu’à 20 °C',
        'pt': 'Classificação inferior a 50 °C em relação a 20 °C', 'zh': '50 °C 时等级低于 20 °C'},
    'conc_dependent': {
        'en': 'Rating changes with concentration (20 °C)',
        'de': 'Bewertung ändert sich mit der Konzentration (20 °C)',
        'es': 'La clasificación cambia con la concentración (20 °C)',
        'fr': 'La note varie avec la concentration (20 °C)',
        'pt': 'A classificação muda com a concentração (20 °C)', 'zh': '等级随浓度变化（20 °C）'},
    'pitting_for': {
        'en': 'Risk of pitting or stress-corrosion cracking',
        'de': 'Gefahr von Lochfraß oder Spannungsrisskorrosion',
        'es': 'Riesgo de picaduras o corrosión bajo tensión',
        'fr': 'Risque de piqûres ou de corrosion sous contrainte',
        'pt': 'Risco de pites ou corrosão sob tensão', 'zh': '存在点蚀或应力腐蚀开裂风险'},
    'none': {'en': 'none', 'de': 'keine', 'es': 'ninguno', 'fr': 'aucun', 'pt': 'nenhum', 'zh': '无'},
    'matrix_h': {
        'en': 'Rating at 20 °C by concentration', 'de': 'Bewertung bei 20 °C nach Konzentration',
        'es': 'Clasificación a 20 °C por concentración', 'fr': 'Note à 20 °C par concentration',
        'pt': 'Classificação a 20 °C por concentração', 'zh': '按浓度列出的 20 °C 等级'},
    'table_h': {
        'en': 'Resistance table', 'de': 'Beständigkeitstabelle', 'es': 'Tabla de resistencia',
        'fr': 'Tableau de résistance', 'pt': 'Tabela de resistência', 'zh': '耐受性表'},
    'material': {'en': 'Material', 'de': 'Werkstoff', 'es': 'Material', 'fr': 'Matériau',
                 'pt': 'Material', 'zh': '材料'},
    'concentration': {'en': 'Concentration', 'de': 'Konzentration', 'es': 'Concentración',
                      'fr': 'Concentration', 'pt': 'Concentração', 'zh': '浓度'},
    'remark': {'en': 'Remark', 'de': 'Hinweis', 'es': 'Observación', 'fr': 'Remarque',
               'pt': 'Observação', 'zh': '备注'},
    'fam_thermoplastic': {'en': 'Thermoplastics', 'de': 'Thermoplaste', 'es': 'Termoplásticos',
                          'fr': 'Thermoplastiques', 'pt': 'Termoplásticos', 'zh': '热塑性塑料'},
    'fam_fluoropolymer': {'en': 'Fluoropolymers', 'de': 'Fluorkunststoffe', 'es': 'Fluoropolímeros',
                          'fr': 'Fluoropolymères', 'pt': 'Fluoropolímeros', 'zh': '氟塑料'},
    'fam_elastomer': {'en': 'Elastomers', 'de': 'Elastomere', 'es': 'Elastómeros',
                      'fr': 'Élastomères', 'pt': 'Elastômeros', 'zh': '弹性体'},
    'fam_metal': {'en': 'Metals', 'de': 'Metalle', 'es': 'Metales', 'fr': 'Métaux', 'pt': 'Metais',
                  'zh': '金属'},
    'est': {'en': 'estimate', 'de': 'Schätzwert', 'es': 'estimación', 'fr': 'estimation',
            'pt': 'estimativa', 'zh': '估计值'},
    'no_temp': {
        'en': 'one value, no temperature given', 'de': 'ein Wert, ohne Temperaturangabe',
        'es': 'un solo valor, sin temperatura', 'fr': 'une seule valeur, sans température',
        'pt': 'um único valor, sem temperatura', 'zh': '单一数值，未注明温度'},
    'pitting': {'en': 'pitting risk', 'de': 'Lochfraßgefahr', 'es': 'riesgo de picaduras',
                'fr': 'risque de piqûres', 'pt': 'risco de pites', 'zh': '点蚀风险'},
    'k_value': {
        'en': 'no general statement possible', 'de': 'keine allgemeine Angabe möglich',
        'es': 'no es posible una indicación general', 'fr': 'aucune indication générale possible',
        'pt': 'não é possível uma indicação geral', 'zh': '无法给出一般性结论'},
    'corrected': {'en': 'corrected, see below', 'de': 'korrigiert, siehe unten',
                  'es': 'corregido, véase abajo', 'fr': 'corrigé, voir ci-dessous',
                  'pt': 'corrigido, ver abaixo', 'zh': '已更正，见下文'},
    'disputed': {'en': 'disputed, see below', 'de': 'umstritten, siehe unten',
                 'es': 'discutido, véase abajo', 'fr': 'contesté, voir ci-dessous',
                 'pt': 'contestado, ver abaixo', 'zh': '存在争议，见下文'},
    'disputed_row': {
        'en': '{mat} ({conc}): source value {old} kept, but other published charts rate it lower.',
        'de': '{mat} ({conc}): Quellwert {old} beibehalten, andere veröffentlichte Tabellen bewerten jedoch schlechter.',
        'es': '{mat} ({conc}): se mantiene el valor de la fuente {old}, pero otras tablas publicadas lo clasifican peor.',
        'fr': '{mat} ({conc}) : valeur de la source {old} conservée, mais d’autres tableaux publiés donnent une note plus basse.',
        'pt': '{mat} ({conc}): valor da fonte {old} mantido, mas outras tabelas publicadas classificam pior.',
        'zh': '{mat}（{conc}）：保留原始值 {old}，但其他公开图表给出的等级更低。'},
    'source_scale': {
        'en': 'Source values use the scale 1 (very good) to 4 (not resistant); 1 = A, 4 = D.',
        'de': 'Quellwerte verwenden die Skala 1 (sehr gut) bis 4 (nicht beständig); 1 = A, 4 = D.',
        'es': 'Los valores de la fuente usan la escala de 1 (muy buena) a 4 (no resistente); 1 = A, 4 = D.',
        'fr': 'Les valeurs de la source utilisent l’échelle de 1 (très bonne) à 4 (non résistant) ; 1 = A, 4 = D.',
        'pt': 'Os valores da fonte usam a escala de 1 (muito boa) a 4 (não resistente); 1 = A, 4 = D.',
        'zh': '原始数值采用 1（很好）至 4（不耐受）的标度；1 = A，4 = D。'},
    'legend_h': {'en': 'Rating scale', 'de': 'Bewertungsskala', 'es': 'Escala de clasificación',
                 'fr': 'Échelle de notation', 'pt': 'Escala de classificação', 'zh': '等级说明'},
    'g_A': {'en': 'very good resistance', 'de': 'sehr gut beständig', 'es': 'resistencia muy buena',
            'fr': 'très bonne résistance', 'pt': 'resistência muito boa', 'zh': '耐受性很好'},
    'g_B': {'en': 'good resistance', 'de': 'gut beständig', 'es': 'buena resistencia',
            'fr': 'bonne résistance', 'pt': 'boa resistência', 'zh': '耐受性良好'},
    'g_C': {'en': 'limited resistance', 'de': 'eingeschränkt beständig',
            'es': 'resistencia limitada', 'fr': 'résistance limitée', 'pt': 'resistência limitada',
            'zh': '耐受性有限'},
    'g_D': {'en': 'not resistant', 'de': 'nicht beständig', 'es': 'no resistente',
            'fr': 'non résistant', 'pt': 'não resistente', 'zh': '不耐受'},
    'g_none': {'en': 'no data', 'de': 'keine Angabe', 'es': 'sin datos', 'fr': 'aucune donnée',
               'pt': 'sem dados', 'zh': '无数据'},
    'est_note': {
        'en': 'estimated rating', 'de': 'geschätzte Bewertung', 'es': 'clasificación estimada',
        'fr': 'note estimée', 'pt': 'classificação estimada', 'zh': '估计等级'},
    'legend_est': {
        'en': 'A rating marked * is an estimate in the source, not a test result. An estimate is given as one value without a temperature.',
        'de': 'Eine mit * markierte Bewertung ist ein Schätzwert der Quelle, kein Prüfergebnis. Ein Schätzwert wird als einzelner Wert ohne Temperatur angegeben.',
        'es': 'Una clasificación marcada con * es una estimación de la fuente, no un resultado de ensayo. Una estimación se da como un solo valor sin temperatura.',
        'fr': 'Une note marquée * est une estimation de la source, pas un résultat d’essai. Une estimation est donnée comme une valeur unique sans température.',
        'pt': 'Uma classificação marcada com * é uma estimativa da fonte, não um resultado de ensaio. Uma estimativa é dada como um único valor sem temperatura.',
        'zh': '标有 * 的等级为原始资料中的估计值，并非试验结果。估计值仅给出一个数值，不区分温度。'},
    'similar_h': {
        'en': 'Chemicals with a similar resistance profile',
        'de': 'Chemikalien mit ähnlichem Beständigkeitsprofil',
        'es': 'Productos químicos con un perfil de resistencia similar',
        'fr': 'Produits chimiques au profil de résistance similaire',
        'pt': 'Produtos químicos com perfil de resistência semelhante',
        'zh': '耐受性特征相近的化学品'},
    'similar_p': {
        'en': 'Same 20 °C rating on the share of materials shown.',
        'de': 'Gleiche 20-°C-Bewertung beim angegebenen Anteil der Werkstoffe.',
        'es': 'Misma clasificación a 20 °C en la proporción de materiales indicada.',
        'fr': 'Même note à 20 °C pour la part de matériaux indiquée.',
        'pt': 'Mesma classificação a 20 °C na proporção de materiais indicada.',
        'zh': '所示比例的材料在 20 °C 下等级相同。'},
    'about_h': {'en': 'About this data', 'de': 'Zu diesen Daten', 'es': 'Sobre estos datos',
                'fr': 'À propos de ces données', 'pt': 'Sobre estes dados', 'zh': '关于数据'},
    'about_p1': {
        'en': 'The ratings come from the chemical resistance list published by Bürkle GmbH, which compiled them from raw-material manufacturers’ data. They describe laboratory tests on the raw material at 20 °C and 50 °C.',
        'de': 'Die Bewertungen stammen aus der Beständigkeitsliste der Bürkle GmbH, die sie aus Angaben verschiedener Rohstoffhersteller zusammengestellt hat. Sie beziehen sich auf Labortests mit Rohstoffen bei 20 °C und 50 °C.',
        'es': 'Las clasificaciones proceden de la lista de resistencia química publicada por Bürkle GmbH, elaborada con datos de fabricantes de materias primas. Describen ensayos de laboratorio con la materia prima a 20 °C y 50 °C.',
        'fr': 'Les notes proviennent de la liste de résistance chimique publiée par Bürkle GmbH, établie à partir des données de fabricants de matières premières. Elles décrivent des essais en laboratoire sur la matière première à 20 °C et 50 °C.',
        'pt': 'As classificações provêm da lista de resistência química publicada pela Bürkle GmbH, compilada a partir de dados de fabricantes de matérias-primas. Descrevem ensaios de laboratório com a matéria-prima a 20 °C e 50 °C.',
        'zh': '等级数据来自 Bürkle GmbH 发布的耐化学性列表，该列表根据原材料制造商的数据汇编而成，反映原材料在 20 °C 和 50 °C 下的实验室测试结果。'},
    'about_p2': {
        'en': 'A finished part also sees pressure, mechanical stress, welds and mixtures that a laboratory test does not. Treat the rating as a first filter and test under your own conditions before relying on it.',
        'de': 'Ein fertiges Bauteil ist zusätzlich Druck, Materialspannungen, Schweißnähten und Gemischen ausgesetzt, die ein Labortest nicht erfasst. Die Bewertung dient als erste Orientierung; vor dem Einsatz unter eigenen Bedingungen prüfen.',
        'es': 'Una pieza terminada soporta además presión, tensiones mecánicas, soldaduras y mezclas que un ensayo de laboratorio no contempla. Use la clasificación como primer filtro y ensaye en sus propias condiciones antes de confiar en ella.',
        'fr': 'Une pièce finie subit en outre pression, contraintes mécaniques, soudures et mélanges qu’un essai en laboratoire ne reproduit pas. Utilisez la note comme premier filtre et testez dans vos propres conditions avant de vous y fier.',
        'pt': 'Uma peça acabada sofre ainda pressão, tensões mecânicas, soldas e misturas que um ensaio de laboratório não reproduz. Use a classificação como primeiro filtro e teste nas suas próprias condições antes de confiar nela.',
        'zh': '成品部件还会受到压力、机械应力、焊缝和混合物的影响，这些是实验室测试无法涵盖的。请将等级作为初步筛选依据，并在实际工况下测试后再采用。'},
    'corrections_h': {
        'en': 'Corrected and disputed values', 'de': 'Korrigierte und umstrittene Werte',
        'es': 'Valores corregidos y discutidos', 'fr': 'Valeurs corrigées et contestées',
        'pt': 'Valores corrigidos e contestados', 'zh': '已更正和存在争议的数值'},
    'corrections_row': {
        'en': '{mat} ({conc}): source value {old}, shown as {new}.',
        'de': '{mat} ({conc}): Quellwert {old}, angezeigt als {new}.',
        'es': '{mat} ({conc}): valor de la fuente {old}, mostrado como {new}.',
        'fr': '{mat} ({conc}) : valeur de la source {old}, affichée comme {new}.',
        'pt': '{mat} ({conc}): valor da fonte {old}, mostrado como {new}.',
        'zh': '{mat}（{conc}）：原始值 {old}，显示为 {new}。'},
    'see_material': {
        'en': 'All chemicals for {mat}', 'de': 'Alle Chemikalien für {mat}',
        'es': 'Todos los productos químicos para {mat}', 'fr': 'Tous les produits chimiques pour {mat}',
        'pt': 'Todos os produtos químicos para {mat}', 'zh': '{mat} 的全部化学品'},
    'see_chemical': {
        'en': 'All materials for {chem}', 'de': 'Alle Werkstoffe für {chem}',
        'es': 'Todos los materiales para {chem}', 'fr': 'Tous les matériaux pour {chem}',
        'pt': 'Todos os materiais para {chem}', 'zh': '{chem} 的全部材料'},
    # pair pages
    'h1_pair': {
        'en': '{mat} and {chem}: Chemical Resistance', 'de': '{mat} und {chem}: Beständigkeit',
        'es': '{mat} y {chem}: resistencia química', 'fr': '{mat} et {chem} : résistance chimique',
        'pt': '{mat} e {chem}: resistência química', 'zh': '{mat} 与 {chem}：耐化学性'},
    'title_pair': {
        'en': '{mat} and {chem}: Chemical Resistance Rating',
        'de': '{mat} und {chem}: Beständigkeitsbewertung',
        'es': '{mat} y {chem}: clasificación de resistencia',
        'fr': '{mat} et {chem} : note de résistance',
        'pt': '{mat} e {chem}: classificação de resistência', 'zh': '{mat} 与 {chem}：耐受等级'},
    'pair_rating_h': {
        'en': 'Rating', 'de': 'Bewertung', 'es': 'Clasificación', 'fr': 'Note', 'pt': 'Classificação',
        'zh': '等级'},
    'pair_nodata': {
        'en': 'The source gives no rating for this combination. A missing rating means untested, not resistant.',
        'de': 'Die Quelle enthält für diese Kombination keine Bewertung. Eine fehlende Bewertung bedeutet ungeprüft, nicht beständig.',
        'es': 'La fuente no da ninguna clasificación para esta combinación. La ausencia de clasificación significa que no se ha ensayado, no que sea resistente.',
        'fr': 'La source ne donne aucune note pour cette combinaison. Une note absente signifie non testé, et non résistant.',
        'pt': 'A fonte não fornece classificação para esta combinação. A ausência de classificação significa não ensaiado, e não resistente.',
        'zh': '原始资料未给出该组合的等级。没有等级表示未经测试，并不代表耐受。'},
    'alternatives_h': {
        'en': 'Materials rated A or B at 20 °C', 'de': 'Werkstoffe mit Bewertung A oder B bei 20 °C',
        'es': 'Materiales con clasificación A o B a 20 °C', 'fr': 'Matériaux notés A ou B à 20 °C',
        'pt': 'Materiais com classificação A ou B a 20 °C', 'zh': '20 °C 下为 A 或 B 级的材料'},
    'material_note_h': {
        'en': 'About {mat}', 'de': 'Über {mat}', 'es': 'Sobre {mat}', 'fr': 'À propos de {mat}',
        'pt': 'Sobre {mat}', 'zh': '关于 {mat}'},
    'desc_pair_nodata': {
        'en': 'No rating is published for {mat} against {chem}. See which of the other {n} materials are rated at 20 °C and 50 °C.',
        'de': 'Für {mat} gegenüber {chem} liegt keine Bewertung vor. Bewertungen der übrigen {n} Werkstoffe bei 20 °C und 50 °C.',
        'es': 'No hay clasificación publicada para {mat} frente a {chem}. Consulte los otros {n} materiales a 20 °C y 50 °C.',
        'fr': 'Aucune note publiée pour {mat} face à {chem}. Voir les {n} autres matériaux à 20 °C et 50 °C.',
        'pt': 'Não há classificação publicada para {mat} frente a {chem}. Veja os outros {n} materiais a 20 °C e 50 °C.',
        'zh': '未发布 {mat} 对 {chem} 的等级。查看其余 {n} 种材料在 20 °C 和 50 °C 下的等级。'},
    'at20': {'en': 'at 20 °C', 'de': 'bei 20 °C', 'es': 'a 20 °C', 'fr': 'à 20 °C', 'pt': 'a 20 °C',
             'zh': '20 °C'},
    'at50': {'en': 'at 50 °C', 'de': 'bei 50 °C', 'es': 'a 50 °C', 'fr': 'à 50 °C', 'pt': 'a 50 °C',
             'zh': '50 °C'},
    'materials_word': {'en': 'materials', 'de': 'Werkstoffe', 'es': 'materiales', 'fr': 'matériaux',
                       'pt': 'materiais', 'zh': '种材料'},
    'rated': {'en': 'Rated {g}', 'de': 'Bewertung {g}', 'es': 'Clasificación {g}', 'fr': 'Note {g}',
              'pt': 'Classificação {g}', 'zh': '{g} 级'},
    'fig_profile_h': {
        'en': 'Rating profile by material family', 'de': 'Bewertungsprofil nach Werkstoffgruppe',
        'es': 'Perfil de clasificación por familia de materiales',
        'fr': 'Profil de notation par famille de matériaux',
        'pt': 'Perfil de classificação por família de materiais', 'zh': '按材料类别的等级分布'},
    'fig_profile_cap': {
        'en': 'Number of materials in each family with each rating at 20 °C.',
        'de': 'Anzahl der Werkstoffe je Gruppe mit der jeweiligen Bewertung bei 20 °C.',
        'es': 'Número de materiales de cada familia con cada clasificación a 20 °C.',
        'fr': 'Nombre de matériaux de chaque famille pour chaque note à 20 °C.',
        'pt': 'Número de materiais de cada família com cada classificação a 20 °C.',
        'zh': '各类别中在 20 °C 下处于各等级的材料数量。'},
    'fig_temp_h': {
        'en': 'Effect of temperature, 20 °C to 50 °C', 'de': 'Einfluss der Temperatur, 20 °C bis 50 °C',
        'es': 'Efecto de la temperatura, de 20 °C a 50 °C',
        'fr': 'Effet de la température, de 20 °C à 50 °C',
        'pt': 'Efeito da temperatura, de 20 °C a 50 °C', 'zh': '温度的影响：20 °C 至 50 °C'},
    'fig_temp_cap': {
        'en': 'Materials whose rating differs between 20 °C and 50 °C. Materials not shown keep their rating or have no 50 °C value.',
        'de': 'Werkstoffe, deren Bewertung sich zwischen 20 °C und 50 °C unterscheidet. Nicht gezeigte Werkstoffe behalten ihre Bewertung oder haben keinen Wert für 50 °C.',
        'es': 'Materiales cuya clasificación difiere entre 20 °C y 50 °C. Los materiales no mostrados mantienen su clasificación o no tienen valor a 50 °C.',
        'fr': 'Matériaux dont la note diffère entre 20 °C et 50 °C. Les matériaux non représentés conservent leur note ou n’ont pas de valeur à 50 °C.',
        'pt': 'Materiais cuja classificação difere entre 20 °C e 50 °C. Os materiais não mostrados mantêm a classificação ou não têm valor a 50 °C.',
        'zh': '在 20 °C 与 50 °C 之间等级不同的材料。未显示的材料等级不变，或没有 50 °C 的数值。'},
    'fig_temp_none': {
        'en': 'No material with a rating at both temperatures changes grade between 20 °C and 50 °C.',
        'de': 'Kein Werkstoff mit Bewertungen für beide Temperaturen ändert seine Bewertung zwischen 20 °C und 50 °C.',
        'es': 'Ningún material con clasificación a ambas temperaturas cambia de grado entre 20 °C y 50 °C.',
        'fr': 'Aucun matériau noté aux deux températures ne change de note entre 20 °C et 50 °C.',
        'pt': 'Nenhum material com classificação nas duas temperaturas muda de grau entre 20 °C e 50 °C.',
        'zh': '在两个温度下均有等级的材料中，没有材料在 20 °C 与 50 °C 之间发生等级变化。'},
    'material_page': {
        'en': 'material page', 'de': 'Werkstoffseite', 'es': 'página del material',
        'fr': 'page du matériau', 'pt': 'página do material', 'zh': '材料页面'},
    'details': {'en': 'details', 'de': 'Details', 'es': 'detalles', 'fr': 'détails', 'pt': 'detalhes',
                'zh': '详情'},
    'fig_ladder_h': {
        'en': 'Rating by concentration', 'de': 'Bewertung nach Konzentration',
        'es': 'Clasificación por concentración', 'fr': 'Note par concentration',
        'pt': 'Classificação por concentração', 'zh': '按浓度列出的等级'},
    'fig_ladder_cap': {
        'en': 'Each cell shows the rating at 20 °C. Where the rating at 50 °C differs, it follows the arrow. * marks an estimate in the source.',
        'de': 'Jede Zelle zeigt die Bewertung bei 20 °C. Weicht die Bewertung bei 50 °C ab, steht sie hinter dem Pfeil. * kennzeichnet einen Schätzwert der Quelle.',
        'es': 'Cada celda muestra la clasificación a 20 °C. Si la clasificación a 50 °C es distinta, aparece tras la flecha. * indica una estimación de la fuente.',
        'fr': 'Chaque cellule indique la note à 20 °C. Si la note à 50 °C diffère, elle suit la flèche. * signale une estimation de la source.',
        'pt': 'Cada célula mostra a classificação a 20 °C. Quando a classificação a 50 °C é diferente, aparece depois da seta. * indica uma estimativa da fonte.',
        'zh': '每个单元格显示 20 °C 下的等级；若 50 °C 下的等级不同，则列于箭头之后。* 表示原始资料中的估计值。'},
    'table_view': {'en': 'Show as a table', 'de': 'Als Tabelle anzeigen', 'es': 'Ver como tabla',
                   'fr': 'Afficher sous forme de tableau', 'pt': 'Ver como tabela', 'zh': '以表格显示'},
    'fig_finger_h': {
        'en': 'Resistance by chemical class', 'de': 'Beständigkeit nach Chemikalienklasse',
        'es': 'Resistencia por clase de producto químico', 'fr': 'Résistance par classe chimique',
        'pt': 'Resistência por classe química', 'zh': '按化学品类别的耐受性'},
    'fig_finger_cap': {
        'en': 'Share of each rating at 20 °C among the source rows of a class. The number in brackets is the number of rated rows; a row is one chemical at one concentration. Classes with fewer than {n} rated rows are left out.',
        'de': 'Anteil jeder Bewertung bei 20 °C an den Quellzeilen einer Klasse. Die Zahl in Klammern ist die Anzahl der bewerteten Zeilen; eine Zeile ist eine Chemikalie bei einer Konzentration. Klassen mit weniger als {n} bewerteten Zeilen fehlen.',
        'es': 'Proporción de cada clasificación a 20 °C entre las filas de la fuente de una clase. El número entre paréntesis es el número de filas clasificadas; una fila es un producto químico a una concentración. Se omiten las clases con menos de {n} filas clasificadas.',
        'fr': 'Part de chaque note à 20 °C parmi les lignes de la source d’une classe. Le nombre entre parenthèses est le nombre de lignes notées ; une ligne est un produit chimique à une concentration. Les classes de moins de {n} lignes notées sont omises.',
        'pt': 'Proporção de cada classificação a 20 °C entre as linhas da fonte de uma classe. O número entre parênteses é o número de linhas classificadas; uma linha é um produto químico a uma concentração. Classes com menos de {n} linhas classificadas são omitidas.',
        'zh': '各等级在某类别原始数据行中所占比例（20 °C）。括号内为有等级的行数；一行代表一种化学品的一个浓度。少于 {n} 行的类别未列出。'},
    'finger_best': {
        'en': 'Most rows rated A or B', 'de': 'Meiste Zeilen mit Bewertung A oder B',
        'es': 'Más filas con clasificación A o B', 'fr': 'Le plus de lignes notées A ou B',
        'pt': 'Mais linhas com classificação A ou B', 'zh': 'A 或 B 级占比最高'},
    'finger_worst': {
        'en': 'Fewest rows rated A or B', 'de': 'Wenigste Zeilen mit Bewertung A oder B',
        'es': 'Menos filas con clasificación A o B', 'fr': 'Le moins de lignes notées A ou B',
        'pt': 'Menos linhas com classificação A ou B', 'zh': 'A 或 B 级占比最低'},
    'fig_overlay_h': {
        'en': 'Share of rows rated A or B, by chemical class',
        'de': 'Anteil der Zeilen mit Bewertung A oder B, nach Chemikalienklasse',
        'es': 'Proporción de filas con clasificación A o B, por clase',
        'fr': 'Part des lignes notées A ou B, par classe chimique',
        'pt': 'Proporção de linhas com classificação A ou B, por classe',
        'zh': '各化学品类别中 A 或 B 级的占比'},
    'fig_grid_h': {
        'en': 'How often the two ratings agree', 'de': 'Wie oft die beiden Bewertungen übereinstimmen',
        'es': 'Con qué frecuencia coinciden las dos clasificaciones',
        'fr': 'Fréquence de concordance des deux notes',
        'pt': 'Com que frequência as duas classificações coincidem', 'zh': '两种材料等级一致的频率'},
    'fig_grid_cap': {
        'en': 'Number of source rows for each pair of ratings at 20 °C. Outlined cells are rows where both materials have the same rating.',
        'de': 'Anzahl der Quellzeilen für jedes Bewertungspaar bei 20 °C. Umrandete Zellen sind Zeilen, in denen beide Werkstoffe gleich bewertet sind.',
        'es': 'Número de filas de la fuente para cada par de clasificaciones a 20 °C. Las celdas con borde son filas en las que ambos materiales tienen la misma clasificación.',
        'fr': 'Nombre de lignes de la source pour chaque paire de notes à 20 °C. Les cellules encadrées sont les lignes où les deux matériaux ont la même note.',
        'pt': 'Número de linhas da fonte para cada par de classificações a 20 °C. As células com contorno são linhas em que os dois materiais têm a mesma classificação.',
        'zh': '20 °C 下每种等级组合对应的原始数据行数。带边框的单元格表示两种材料等级相同。'},
    'fig_overlay_cap': {
        'en': 'Rating at 20 °C. Only classes with at least {n} rated rows for both materials are shown.',
        'de': 'Bewertung bei 20 °C. Gezeigt werden nur Klassen mit mindestens {n} bewerteten Zeilen für beide Werkstoffe.',
        'es': 'Clasificación a 20 °C. Solo se muestran las clases con al menos {n} filas clasificadas para ambos materiales.',
        'fr': 'Note à 20 °C. Seules les classes comptant au moins {n} lignes notées pour les deux matériaux sont représentées.',
        'pt': 'Classificação a 20 °C. São mostradas apenas as classes com pelo menos {n} linhas classificadas para ambos os materiais.',
        'zh': '20 °C 下的等级。仅显示两种材料均至少有 {n} 行有等级的类别。'},
    'fig_group_h': {
        'en': 'Share of rows rated A or B, by material and chemical class',
        'de': 'Anteil der Zeilen mit Bewertung A oder B, nach Werkstoff und Chemikalienklasse',
        'es': 'Proporción de filas con clasificación A o B, por material y clase',
        'fr': 'Part des lignes notées A ou B, par matériau et classe chimique',
        'pt': 'Proporção de linhas com classificação A ou B, por material e classe',
        'zh': '按材料和化学品类别列出的 A 或 B 级占比'},
    'fig_overall_h': {
        'en': 'All rated rows, by rating', 'de': 'Alle bewerteten Zeilen, nach Bewertung',
        'es': 'Todas las filas clasificadas, por clasificación', 'fr': 'Toutes les lignes notées, par note',
        'pt': 'Todas as linhas classificadas, por classificação', 'zh': '全部有等级的数据行（按等级）'},
    'fig_overall_cap': {
        'en': 'Share of each rating at 20 °C. The number in brackets is the number of rated source rows.',
        'de': 'Anteil jeder Bewertung bei 20 °C. Die Zahl in Klammern ist die Anzahl der bewerteten Quellzeilen.',
        'es': 'Proporción de cada clasificación a 20 °C. El número entre paréntesis es el número de filas clasificadas de la fuente.',
        'fr': 'Part de chaque note à 20 °C. Le nombre entre parenthèses est le nombre de lignes notées de la source.',
        'pt': 'Proporção de cada classificação a 20 °C. O número entre parênteses é o número de linhas classificadas da fonte.',
        'zh': '20 °C 下各等级所占比例。括号内为有等级的原始数据行数。'},
    'class_note': {
        'en': 'Chemical classes were assigned by this site, not by the source. Mixtures and trade products without a clear class are not counted.',
        'de': 'Die Chemikalienklassen wurden von dieser Website zugeordnet, nicht von der Quelle. Gemische und Handelsprodukte ohne eindeutige Klasse werden nicht gezählt.',
        'es': 'Las clases químicas fueron asignadas por este sitio, no por la fuente. Las mezclas y los productos comerciales sin una clase clara no se cuentan.',
        'fr': 'Les classes chimiques ont été attribuées par ce site, non par la source. Les mélanges et produits commerciaux sans classe claire ne sont pas comptés.',
        'pt': 'As classes químicas foram atribuídas por este site, não pela fonte. Misturas e produtos comerciais sem classe clara não são contados.',
        'zh': '化学品类别由本站划分，并非来自原始资料。无法明确归类的混合物和商品未计入。'},
    'fig_group_cap': {
        'en': 'Rating at 20 °C. A dash means fewer than {n} rated rows in that class.',
        'de': 'Bewertung bei 20 °C. Ein Strich bedeutet weniger als {n} bewertete Zeilen in dieser Klasse.',
        'es': 'Clasificación a 20 °C. Un guion indica menos de {n} filas clasificadas en esa clase.',
        'fr': 'Note à 20 °C. Un tiret signifie moins de {n} lignes notées dans cette classe.',
        'pt': 'Classificação a 20 °C. Um traço indica menos de {n} linhas classificadas nessa classe.',
        'zh': '20 °C 下的等级。短横线表示该类别中有等级的数据行少于 {n} 行。'},
    'list_sep': {'en': ', ', 'de': ', ', 'es': ', ', 'fr': ', ', 'pt': ', ', 'zh': '、'},
}

#: English material notes for pair pages: service limits and known weaknesses.
MATERIAL_NOTES_EN = {
    'HDPE': 'High-density polyethylene resists most aqueous acids, alkalis and salt solutions. Strong oxidising acids, chlorinated solvents and aromatic hydrocarbons attack or swell it. Continuous service is usually limited to about 80 °C.',
    'LDPE': 'Low-density polyethylene has a similar profile to HDPE but is softer and more permeable, so solvents swell it sooner. Continuous service is usually limited to about 60 °C.',
    'PP': 'Polypropylene resists most acids, alkalis and salt solutions. Concentrated oxidising acids, chlorinated solvents and aromatic hydrocarbons attack it, and it turns brittle below about 0 °C.',
    'PVC_HART': 'Rigid PVC resists acids, alkalis and salt solutions well. Ketones, esters, aromatic and chlorinated solvents dissolve or swell it. Service temperature is limited to about 60 °C.',
    'PVC_WEICH': 'Flexible PVC shares the solvent weaknesses of rigid PVC, and any liquid that extracts the plasticiser also hardens it. It is generally less resistant than rigid PVC.',
    'PMP': 'Polymethylpentene (TPX) is a transparent polyolefin used for labware. It resists many acids and alkalis, while aromatic and chlorinated solvents and strong oxidisers attack it.',
    'PS': 'Polystyrene is attacked by most organic solvents, including ketones, esters, aromatic and chlorinated hydrocarbons. It is used for dilute aqueous solutions.',
    'SAN': 'Styrene-acrylonitrile resists oils and dilute acids better than polystyrene, but ketones, esters and aromatic and chlorinated solvents still attack it.',
    'PC': 'Polycarbonate is attacked by alkalis, amines, ketones, esters and many organic solvents, and it stress-cracks under load in contact with them.',
    'PETG': 'PETG is a co-polyester for clear containers. Strong acids and alkalis and most organic solvents attack it.',
    'POM': 'Acetal (POM) resists many organic solvents and fuels. Strong acids and oxidising agents degrade it.',
    'PA': 'Polyamide (nylon) resists fuels, oils and many solvents. Mineral acids, even dilute, and strong oxidisers attack it, and it absorbs water.',
    'PSU': 'Polysulfone withstands hot water and steam. Ketones, esters and chlorinated and aromatic solvents attack it.',
    'PTFE': 'PTFE is resistant to almost every chemical in this list. The known exceptions are molten alkali metals, elemental fluorine and some fluorinating agents at elevated temperature.',
    'FEP': 'FEP has nearly the chemical resistance of PTFE and can be melt-processed. Its service temperature, about 200 °C, is lower than that of PTFE.',
    'PVDF': 'PVDF resists acids, halogens and hydrocarbons. Strong bases, amines, ketones and esters attack it. Service temperature is up to about 150 °C.',
    'ECTFE_ETFE': 'ECTFE and ETFE are tough fluoropolymers with broad resistance. Hot amines and some chlorinated solvents at elevated temperature are their main limits.',
    'EPDM': 'EPDM resists water, steam, alkalis, ketones and alcohols. Mineral oils, fuels and aromatic solvents swell it severely.',
    'FPM': 'Fluoroelastomer (Viton, FKM/FPM) resists fuels, oils and many acids. Ketones, esters, amines and hot water or steam attack it.',
    'NBR': 'Nitrile rubber resists mineral oils and fuels. Ketones, esters, chlorinated solvents, strong oxidisers and ozone attack it.',
    'SI': 'Silicone rubber keeps its flexibility over a wide temperature range. Concentrated acids and alkalis and hydrocarbon solvents attack or swell it.',
    'V4A': 'Stainless steel 316 (1.4401) contains molybdenum, which improves resistance to chlorides over 304. Hydrochloric acid and other halide acids still cause pitting.',
    'V2A': 'Stainless steel 304 (1.4301) resists oxidising acids and most organic chemicals. Chlorides cause pitting and stress-corrosion cracking.',
    'AL': 'Aluminium relies on a thin oxide layer. Strong acids, strong alkalis and mercury compounds destroy that layer.',
}


def t(key, lang, **kw):
    s = T[key][lang]
    return s.format(**kw) if kw else s


MATERIAL_FULL_I18N = {
    'de': {
        'HDPE': 'Polyethylen hoher Dichte', 'LDPE': 'Polyethylen niedriger Dichte', 'PP': 'Polypropylen',
        'PVC_HART': 'Hart-PVC (weichmacherfreies Polyvinylchlorid)',
        'PVC_WEICH': 'Weich-PVC (weichmacherhaltiges Polyvinylchlorid)',
        'PMP': 'Polymethylpenten (TPX)', 'PS': 'Polystyrol', 'SAN': 'Styrol-Acrylnitril',
        'PC': 'Polycarbonat', 'PETG': 'Polyethylenterephthalat-Glykol (Co-Polyester)',
        'POM': 'Polyoxymethylen (Acetal)', 'PA': 'Polyamid (Nylon)', 'PSU': 'Polysulfon',
        'PTFE': 'Polytetrafluorethylen', 'FEP': 'Tetrafluorethylen-Perfluorpropylen',
        'PVDF': 'Polyvinylidenfluorid',
        'ECTFE_ETFE': 'Ethylen-Chlortrifluorethylen / Ethylen-Tetrafluorethylen',
        'EPDM': 'Ethylen-Propylen-Dien-Kautschuk', 'FPM': 'Fluorkautschuk (FKM/FPM)',
        'NBR': 'Nitril-Butadien-Kautschuk', 'SI': 'Silikonkautschuk',
        'V4A': 'Edelstahl 1.4401 (AISI 316)', 'V2A': 'Edelstahl 1.4301 (AISI 304)', 'AL': 'Aluminium',
    },
    'es': {
        'HDPE': 'Polietileno de alta densidad', 'LDPE': 'Polietileno de baja densidad',
        'PP': 'Polipropileno', 'PVC_HART': 'PVC rígido (policloruro de vinilo sin plastificante)',
        'PVC_WEICH': 'PVC flexible (policloruro de vinilo plastificado)',
        'PMP': 'Polimetilpenteno (TPX)', 'PS': 'Poliestireno', 'SAN': 'Estireno-acrilonitrilo',
        'PC': 'Policarbonato', 'PETG': 'Tereftalato de polietileno glicol (copoliéster)',
        'POM': 'Polioximetileno (acetal)', 'PA': 'Poliamida (nailon)', 'PSU': 'Polisulfona',
        'PTFE': 'Politetrafluoroetileno', 'FEP': 'Etileno propileno fluorado',
        'PVDF': 'Fluoruro de polivinilideno',
        'ECTFE_ETFE': 'Etileno-clorotrifluoroetileno / etileno-tetrafluoroetileno',
        'EPDM': 'Caucho de etileno-propileno-dieno', 'FPM': 'Fluoroelastómero (FKM/FPM)',
        'NBR': 'Caucho de nitrilo-butadieno', 'SI': 'Caucho de silicona',
        'V4A': 'Acero inoxidable 1.4401 (AISI 316)', 'V2A': 'Acero inoxidable 1.4301 (AISI 304)',
        'AL': 'Aluminio',
    },
}


def material_full(code, lang):
    return MATERIAL_FULL_I18N.get(lang, {}).get(code, MATERIAL_FULL[code])


MATERIAL_NOTES = {
    'en': MATERIAL_NOTES_EN,
    'de': {
        'HDPE': 'Polyethylen hoher Dichte ist gegen die meisten wässrigen Säuren, Laugen und Salzlösungen beständig. Stark oxidierende Säuren, chlorierte Lösungsmittel und aromatische Kohlenwasserstoffe greifen es an oder lassen es quellen. Die Dauergebrauchstemperatur liegt meist bei etwa 80 °C.',
        'LDPE': 'Polyethylen niedriger Dichte verhält sich ähnlich wie HDPE, ist aber weicher und durchlässiger, sodass Lösungsmittel es früher quellen lassen. Die Dauergebrauchstemperatur liegt meist bei etwa 60 °C.',
        'PP': 'Polypropylen ist gegen die meisten Säuren, Laugen und Salzlösungen beständig. Konzentrierte oxidierende Säuren, chlorierte Lösungsmittel und aromatische Kohlenwasserstoffe greifen es an; unter etwa 0 °C wird es spröde.',
        'PVC_HART': 'Hart-PVC ist gegen Säuren, Laugen und Salzlösungen gut beständig. Ketone, Ester sowie aromatische und chlorierte Lösungsmittel lösen es an oder lassen es quellen. Die Gebrauchstemperatur ist auf etwa 60 °C begrenzt.',
        'PVC_WEICH': 'Weich-PVC hat die gleichen Schwächen gegenüber Lösungsmitteln wie Hart-PVC; zusätzlich verhärtet es, wenn eine Flüssigkeit den Weichmacher herauslöst. Es ist insgesamt weniger beständig als Hart-PVC.',
        'PMP': 'Polymethylpenten (TPX) ist ein transparentes Polyolefin für Laborgeräte. Es ist gegen viele Säuren und Laugen beständig; aromatische und chlorierte Lösungsmittel sowie starke Oxidationsmittel greifen es an.',
        'PS': 'Polystyrol wird von den meisten organischen Lösungsmitteln angegriffen, darunter Ketone, Ester sowie aromatische und chlorierte Kohlenwasserstoffe. Es wird für verdünnte wässrige Lösungen eingesetzt.',
        'SAN': 'Styrol-Acrylnitril ist gegen Öle und verdünnte Säuren beständiger als Polystyrol; Ketone, Ester sowie aromatische und chlorierte Lösungsmittel greifen es dennoch an.',
        'PC': 'Polycarbonat wird von Laugen, Aminen, Ketonen, Estern und vielen organischen Lösungsmitteln angegriffen und neigt im Kontakt damit unter Last zu Spannungsrissen.',
        'PETG': 'PETG ist ein Co-Polyester für transparente Behälter. Starke Säuren und Laugen sowie die meisten organischen Lösungsmittel greifen es an.',
        'POM': 'POM (Acetal) ist gegen viele organische Lösungsmittel und Kraftstoffe beständig. Starke Säuren und Oxidationsmittel bauen es ab.',
        'PA': 'Polyamid (Nylon) ist gegen Kraftstoffe, Öle und viele Lösungsmittel beständig. Mineralsäuren, auch verdünnte, und starke Oxidationsmittel greifen es an; außerdem nimmt es Wasser auf.',
        'PSU': 'Polysulfon hält heißem Wasser und Dampf stand. Ketone, Ester sowie chlorierte und aromatische Lösungsmittel greifen es an.',
        'PTFE': 'PTFE ist gegen nahezu alle Chemikalien dieser Liste beständig. Bekannte Ausnahmen sind geschmolzene Alkalimetalle, elementares Fluor und einige Fluorierungsmittel bei erhöhter Temperatur.',
        'FEP': 'FEP erreicht nahezu die chemische Beständigkeit von PTFE und lässt sich aus der Schmelze verarbeiten. Seine Gebrauchstemperatur von etwa 200 °C liegt unter der von PTFE.',
        'PVDF': 'PVDF ist gegen Säuren, Halogene und Kohlenwasserstoffe beständig. Starke Basen, Amine, Ketone und Ester greifen es an. Die Gebrauchstemperatur reicht bis etwa 150 °C.',
        'ECTFE_ETFE': 'ECTFE und ETFE sind zähe Fluorkunststoffe mit breiter Beständigkeit. Ihre Grenzen liegen vor allem bei heißen Aminen und einigen chlorierten Lösungsmitteln bei erhöhter Temperatur.',
        'EPDM': 'EPDM ist gegen Wasser, Dampf, Laugen, Ketone und Alkohole beständig. Mineralöle, Kraftstoffe und aromatische Lösungsmittel lassen es stark quellen.',
        'FPM': 'Fluorkautschuk (Viton, FKM/FPM) ist gegen Kraftstoffe, Öle und viele Säuren beständig. Ketone, Ester, Amine sowie heißes Wasser und Dampf greifen ihn an.',
        'NBR': 'Nitrilkautschuk ist gegen Mineralöle und Kraftstoffe beständig. Ketone, Ester, chlorierte Lösungsmittel, starke Oxidationsmittel und Ozon greifen ihn an.',
        'SI': 'Silikonkautschuk bleibt über einen weiten Temperaturbereich elastisch. Konzentrierte Säuren und Laugen sowie Kohlenwasserstoff-Lösungsmittel greifen ihn an oder lassen ihn quellen.',
        'V4A': 'Edelstahl 316 (1.4401) enthält Molybdän, das die Beständigkeit gegen Chloride gegenüber 304 verbessert. Salzsäure und andere Halogenwasserstoffsäuren verursachen dennoch Lochfraß.',
        'V2A': 'Edelstahl 304 (1.4301) ist gegen oxidierende Säuren und die meisten organischen Chemikalien beständig. Chloride verursachen Lochfraß und Spannungsrisskorrosion.',
        'AL': 'Aluminium ist durch eine dünne Oxidschicht geschützt. Starke Säuren, starke Laugen und Quecksilberverbindungen zerstören diese Schicht.',
    },
    'es': {
        'HDPE': 'El polietileno de alta densidad resiste la mayoría de los ácidos, álcalis y soluciones salinas en medio acuoso. Los ácidos oxidantes fuertes, los disolventes clorados y los hidrocarburos aromáticos lo atacan o lo hinchan. El servicio continuo suele limitarse a unos 80 °C.',
        'LDPE': 'El polietileno de baja densidad se comporta de forma parecida al HDPE, pero es más blando y permeable, por lo que los disolventes lo hinchan antes. El servicio continuo suele limitarse a unos 60 °C.',
        'PP': 'El polipropileno resiste la mayoría de los ácidos, álcalis y soluciones salinas. Los ácidos oxidantes concentrados, los disolventes clorados y los hidrocarburos aromáticos lo atacan, y se vuelve frágil por debajo de unos 0 °C.',
        'PVC_HART': 'El PVC rígido resiste bien los ácidos, álcalis y soluciones salinas. Las cetonas, los ésteres y los disolventes aromáticos y clorados lo disuelven o lo hinchan. La temperatura de servicio se limita a unos 60 °C.',
        'PVC_WEICH': 'El PVC flexible comparte las debilidades del PVC rígido frente a los disolventes, y además se endurece cuando un líquido extrae el plastificante. En general es menos resistente que el PVC rígido.',
        'PMP': 'El polimetilpenteno (TPX) es una poliolefina transparente usada en material de laboratorio. Resiste muchos ácidos y álcalis; los disolventes aromáticos y clorados y los oxidantes fuertes lo atacan.',
        'PS': 'El poliestireno es atacado por la mayoría de los disolventes orgánicos, entre ellos cetonas, ésteres e hidrocarburos aromáticos y clorados. Se usa con soluciones acuosas diluidas.',
        'SAN': 'El estireno-acrilonitrilo resiste los aceites y los ácidos diluidos mejor que el poliestireno, pero las cetonas, los ésteres y los disolventes aromáticos y clorados también lo atacan.',
        'PC': 'El policarbonato es atacado por álcalis, aminas, cetonas, ésteres y muchos disolventes orgánicos, y en contacto con ellos se agrieta por tensión bajo carga.',
        'PETG': 'El PETG es un copoliéster para envases transparentes. Los ácidos y álcalis fuertes y la mayoría de los disolventes orgánicos lo atacan.',
        'POM': 'El acetal (POM) resiste muchos disolventes orgánicos y combustibles. Los ácidos fuertes y los agentes oxidantes lo degradan.',
        'PA': 'La poliamida (nailon) resiste combustibles, aceites y muchos disolventes. Los ácidos minerales, incluso diluidos, y los oxidantes fuertes la atacan, y además absorbe agua.',
        'PSU': 'La polisulfona soporta agua caliente y vapor. Las cetonas, los ésteres y los disolventes clorados y aromáticos la atacan.',
        'PTFE': 'El PTFE resiste casi todos los productos químicos de esta lista. Las excepciones conocidas son los metales alcalinos fundidos, el flúor elemental y algunos agentes fluorantes a temperatura elevada.',
        'FEP': 'El FEP tiene casi la resistencia química del PTFE y puede procesarse por fusión. Su temperatura de servicio, unos 200 °C, es inferior a la del PTFE.',
        'PVDF': 'El PVDF resiste ácidos, halógenos e hidrocarburos. Las bases fuertes, las aminas, las cetonas y los ésteres lo atacan. La temperatura de servicio llega a unos 150 °C.',
        'ECTFE_ETFE': 'El ECTFE y el ETFE son fluoropolímeros tenaces de resistencia amplia. Sus límites principales son las aminas calientes y algunos disolventes clorados a temperatura elevada.',
        'EPDM': 'El EPDM resiste agua, vapor, álcalis, cetonas y alcoholes. Los aceites minerales, los combustibles y los disolventes aromáticos lo hinchan intensamente.',
        'FPM': 'El fluoroelastómero (Viton, FKM/FPM) resiste combustibles, aceites y muchos ácidos. Las cetonas, los ésteres, las aminas y el agua caliente o el vapor lo atacan.',
        'NBR': 'El caucho de nitrilo resiste aceites minerales y combustibles. Las cetonas, los ésteres, los disolventes clorados, los oxidantes fuertes y el ozono lo atacan.',
        'SI': 'El caucho de silicona conserva su flexibilidad en un amplio intervalo de temperaturas. Los ácidos y álcalis concentrados y los disolventes de hidrocarburos lo atacan o lo hinchan.',
        'V4A': 'El acero inoxidable 316 (1.4401) contiene molibdeno, que mejora la resistencia a los cloruros respecto al 304. El ácido clorhídrico y otros ácidos halogenados siguen causando picaduras.',
        'V2A': 'El acero inoxidable 304 (1.4301) resiste los ácidos oxidantes y la mayoría de los productos químicos orgánicos. Los cloruros causan picaduras y corrosión bajo tensión.',
        'AL': 'El aluminio depende de una fina capa de óxido. Los ácidos fuertes, los álcalis fuertes y los compuestos de mercurio destruyen esa capa.',
    },
}


def material_note(code, lang):
    """Note on a material, or None where it has not been translated."""
    return MATERIAL_NOTES.get(lang, {}).get(code)
