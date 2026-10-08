#!/usr/bin/env python3
"""Algorithmic editorial content for chemical-material pair pages.

Generates 200-300 words of unique, data-driven editorial content per pair page
using templates with enough variation to avoid duplication. Content is derived
from the actual resistance ratings, chemical properties, and material properties
— no LLM is used.

The module is imported by build_chemical_pages.py and called once per pair page.
A deterministic hash of (chemical_slug, material_code) selects template variants
so that builds are reproducible.
"""

import hashlib
import re

import resistance_data as rd
from page_i18n import conc_label, material_name, MATERIAL_FULL, INDEXED_LANGS

# ---------------------------------------------------------------------------
# Chemical categories — mapped from hazard symbols, formula patterns, and names
# ---------------------------------------------------------------------------

CHEMICAL_CATEGORIES = {
    'acid': {
        'keywords': ['acid', 'säure', 'ácido', 'acide', 'salzsäure', 'schwefelsäure',
                     'salpetersäure', 'phosphorsäure', 'essigsäure', 'ameisensäure',
                     'zitronensäure', 'milchsäure', 'oxalsäure', 'chromsäure',
                     'flusssäure', 'borsäure', 'weinsäure', 'benzoesäure',
                     'perchlorsäure', 'pikrinsäure', 'stearinsäure', 'ölsäure',
                     'linolsäure', 'palmitinsäure', 'capronsäure', 'buttersäure',
                     'propionsäure', 'acrylsäure', 'maleinsäure', 'bernsteinsäure',
                     'phthalsäure', 'tannin'],
    },
    'base': {
        'keywords': ['hydroxid', 'hydroxide', 'hidróxido', 'lauge', 'ammoniak',
                     'ammonia', 'natronlauge', 'kalilauge', 'amine', 'amin',
                     'amina', 'soda', 'alkali', 'bariumhydroxid', 'calciumhydroxid',
                     'kalkmilch', 'lime'],
    },
    'solvent': {
        'keywords': ['solvent', 'lösungsmittel', 'disolvente', 'solvant',
                     'aceton', 'acetone', 'toluol', 'toluene', 'xylol', 'xylene',
                     'benzol', 'benzene', 'chloroform', 'dichlormethan',
                     'trichlorethylen', 'tetrachlorethylen', 'methylenchlorid',
                     'ethylacetat', 'butylacetat', 'methylethylketon', 'mek',
                     'tetrahydrofuran', 'thf', 'dimethylformamid', 'dmf',
                     'dimethylsulfoxid', 'dmso', 'cyclohexanon', 'diethylether',
                     'ether', 'äther', 'petrolether', 'petroleum ether'],
    },
    'fuel': {
        'keywords': ['benzin', 'gasoline', 'petrol', 'diesel', 'heizöl', 'fuel',
                     'kerosin', 'kerosene', 'motoröl', 'motor oil', 'schmieröl',
                     'hydrauliköl', 'hydraulic', 'petroleum', 'erdöl', 'crude'],
    },
    'oxidizer': {
        'keywords': ['peroxid', 'peroxide', 'peróxido', 'permanganat', 'permanganate',
                     'chromat', 'chromate', 'dichromat', 'dichromate', 'persulfat',
                     'hypochlorit', 'hypochlorite', 'chlor', 'chlorine', 'brom',
                     'bromine', 'iod', 'iodine', 'jod', 'wasserstoffperoxid',
                     'ozon', 'ozone', 'salpetersäure', 'nitric acid',
                     'perchlorsäure', 'perchloric'],
    },
    'salt': {
        'keywords': ['chlorid', 'chloride', 'sulfat', 'sulfate', 'nitrat', 'nitrate',
                     'carbonat', 'carbonate', 'phosphat', 'phosphate', 'acetat',
                     'acetate', 'cyanid', 'cyanide', 'fluorid', 'fluoride',
                     'bromid', 'bromide', 'natriumchlorid', 'kaliumchlorid',
                     'salzwasser', 'seawater', 'meerwasser', 'alum', 'alaun',
                     'borax', 'salpeter', 'salt', 'salz'],
    },
    'alcohol': {
        'keywords': ['alkohol', 'alcohol', 'methanol', 'ethanol', 'propanol',
                     'butanol', 'isopropanol', 'glycol', 'glykol', 'glycerin',
                     'glyzerin', 'phenol', 'kresol', 'cresol'],
    },
    'food_grade': {
        'keywords': ['zucker', 'sugar', 'glucose', 'fructose', 'saccharose',
                     'stärke', 'starch', 'milch', 'milk', 'bier', 'beer',
                     'wein', 'wine', 'essig', 'vinegar', 'speiseöl', 'cooking oil',
                     'olivenöl', 'olive oil', 'zitronensäure', 'citric',
                     'essigsäure', 'acetic', 'milchsäure', 'lactic',
                     'gelatine', 'gelatin', 'hefe', 'yeast', 'rahm', 'cream',
                     'fruchtsaft', 'fruit juice', 'marmelade', 'jam', 'honig',
                     'sirup', 'syrup', 'kaffee', 'coffee', 'tee', 'tea',
                     'cola', 'limonade', 'lemonade', 'soja', 'soy'],
    },
    'hydrocarbon': {
        'keywords': ['hexan', 'hexane', 'heptan', 'heptane', 'octan', 'octane',
                     'decan', 'decane', 'pentan', 'pentane', 'cyclohexan',
                     'cyclohexane', 'naphthalin', 'naphthalene', 'paraffin',
                     'kohlenwasserstoff', 'hydrocarbon', 'mineralöl', 'mineral oil',
                     'vaseline', 'wachs', 'wax'],
    },
}

# Material application contexts
MATERIAL_APPS = {
    'thermoplastic': {
        'en': 'tanks, piping, containers and liners',
        'de': 'Tanks, Rohrleitungen, Behälter und Auskleidungen',
        'es': 'tanques, tuberías, contenedores y revestimientos',
    },
    'fluoropolymer': {
        'en': 'seals, gaskets, valve seats and lined equipment',
        'de': 'Dichtungen, Ventilsitze und ausgekleidete Anlagen',
        'es': 'sellos, juntas, asientos de válvulas y equipos revestidos',
    },
    'elastomer': {
        'en': 'seals, O-rings, hoses and flexible connections',
        'de': 'Dichtungen, O-Ringe, Schläuche und flexible Verbindungen',
        'es': 'sellos, juntas tóricas, mangueras y conexiones flexibles',
    },
    'metal': {
        'en': 'vessels, heat exchangers, fittings and structural components',
        'de': 'Behälter, Wärmetauscher, Armaturen und tragende Bauteile',
        'es': 'recipientes, intercambiadores de calor, accesorios y componentes estructurales',
    },
}

# Industry contexts per chemical category
INDUSTRY_CONTEXT = {
    'acid': {
        'en': ['chemical processing', 'metal finishing', 'water treatment', 'laboratory work', 'surface cleaning'],
        'de': ['chemische Verarbeitung', 'Metallveredelung', 'Wasseraufbereitung', 'Laborarbeit', 'Oberflächenreinigung'],
        'es': ['procesamiento químico', 'acabado de metales', 'tratamiento de agua', 'trabajo de laboratorio', 'limpieza de superficies'],
    },
    'base': {
        'en': ['chemical processing', 'pulp and paper', 'cleaning and sanitation', 'water treatment', 'textile processing'],
        'de': ['chemische Verarbeitung', 'Zellstoff- und Papierindustrie', 'Reinigung und Desinfektion', 'Wasseraufbereitung', 'Textilverarbeitung'],
        'es': ['procesamiento químico', 'industria de celulosa y papel', 'limpieza y saneamiento', 'tratamiento de agua', 'procesamiento textil'],
    },
    'solvent': {
        'en': ['cleaning and degreasing', 'coatings and paints', 'pharmaceutical manufacturing', 'chemical synthesis', 'electronics cleaning'],
        'de': ['Reinigung und Entfettung', 'Lacke und Farben', 'pharmazeutische Herstellung', 'chemische Synthese', 'Elektronikreinigung'],
        'es': ['limpieza y desengrase', 'recubrimientos y pinturas', 'fabricación farmacéutica', 'síntesis química', 'limpieza de electrónicos'],
    },
    'fuel': {
        'en': ['fuel storage and transfer', 'automotive', 'power generation', 'marine applications', 'heating systems'],
        'de': ['Kraftstofflagerung und -umschlag', 'Automobilindustrie', 'Energieerzeugung', 'maritime Anwendungen', 'Heizsysteme'],
        'es': ['almacenamiento y transferencia de combustible', 'automoción', 'generación de energía', 'aplicaciones marinas', 'sistemas de calefacción'],
    },
    'oxidizer': {
        'en': ['water disinfection', 'bleaching', 'chemical processing', 'waste treatment', 'pulp and paper'],
        'de': ['Wasserdesinfektion', 'Bleichen', 'chemische Verarbeitung', 'Abfallbehandlung', 'Zellstoff- und Papierindustrie'],
        'es': ['desinfección del agua', 'blanqueamiento', 'procesamiento químico', 'tratamiento de residuos', 'industria de celulosa y papel'],
    },
    'salt': {
        'en': ['water treatment', 'food processing', 'electroplating', 'de-icing', 'chemical storage'],
        'de': ['Wasseraufbereitung', 'Lebensmittelverarbeitung', 'Galvanotechnik', 'Enteisen', 'Chemikalienlagerung'],
        'es': ['tratamiento de agua', 'procesamiento de alimentos', 'galvanoplastia', 'descongelamiento', 'almacenamiento de productos químicos'],
    },
    'alcohol': {
        'en': ['pharmaceutical manufacturing', 'cosmetics production', 'cleaning', 'chemical synthesis', 'food and beverage processing'],
        'de': ['pharmazeutische Herstellung', 'Kosmetikproduktion', 'Reinigung', 'chemische Synthese', 'Lebensmittel- und Getränkeherstellung'],
        'es': ['fabricación farmacéutica', 'producción de cosméticos', 'limpieza', 'síntesis química', 'procesamiento de alimentos y bebidas'],
    },
    'food_grade': {
        'en': ['food processing', 'beverage production', 'dairy operations', 'commercial kitchens', 'food storage'],
        'de': ['Lebensmittelverarbeitung', 'Getränkeherstellung', 'Molkereibetrieb', 'Großküchen', 'Lebensmittellagerung'],
        'es': ['procesamiento de alimentos', 'producción de bebidas', 'operaciones lácteas', 'cocinas comerciales', 'almacenamiento de alimentos'],
    },
    'hydrocarbon': {
        'en': ['petrochemical processing', 'lubrication systems', 'chemical storage', 'oil and gas', 'laboratory work'],
        'de': ['petrochemische Verarbeitung', 'Schmiersysteme', 'Chemikalienlagerung', 'Öl und Gas', 'Laborarbeit'],
        'es': ['procesamiento petroquímico', 'sistemas de lubricación', 'almacenamiento de productos químicos', 'petróleo y gas', 'trabajo de laboratorio'],
    },
}


# ---------------------------------------------------------------------------
# "Did you know?" facts — templates keyed by (category, family)
# ---------------------------------------------------------------------------

DID_YOU_KNOW = {
    'en': [
        '{mat_full} was first developed in the {decade}s and remains one of the most widely used {family_word}s in chemical handling equipment.',
        'The chemical resistance of {mat_short} depends not only on the chemical concentration but also on exposure time, mechanical stress, and the presence of other chemicals in the mixture.',
        '{mat_full} is commonly chosen for {apps} because of its combination of chemical resistance, mechanical strength, and cost-effectiveness.',
        'Temperature is often the deciding factor when selecting materials for {chem_name}: even materials rated A at 20 °C may lose performance at elevated temperatures.',
        'In industrial practice, {mat_short} components exposed to {chem_name} are typically inspected for swelling, discoloration, or loss of mechanical strength as early indicators of chemical attack.',
        'When choosing between {family_word}s for {chem_name} service, engineers consider not just the resistance rating but also factors such as permeation rate, creep resistance, and weldability.',
        'The ratings shown here apply to pure {chem_name} in contact with the base {family_word}. In real-world applications, additives, pigments, and fillers in the material can shift resistance in either direction.',
        'Chemical resistance testing according to DIN and ISO standards typically evaluates weight change, dimensional change, and retention of tensile strength after immersion.',
    ],
    'de': [
        '{mat_full} wurde erstmals in den {decade}er Jahren entwickelt und ist nach wie vor eines der am häufigsten verwendeten {family_word} in der chemischen Verfahrenstechnik.',
        'Die chemische Beständigkeit von {mat_short} hängt nicht nur von der Konzentration ab, sondern auch von der Einwirkdauer, mechanischen Belastung und der Anwesenheit anderer Chemikalien im Gemisch.',
        '{mat_full} wird häufig für {apps} gewählt, weil es chemische Beständigkeit, mechanische Festigkeit und Wirtschaftlichkeit verbindet.',
        'Die Temperatur ist oft der entscheidende Faktor bei der Werkstoffauswahl für {chem_name}: Selbst Werkstoffe mit Bewertung A bei 20 °C können bei erhöhter Temperatur an Leistung verlieren.',
        'In der industriellen Praxis werden Bauteile aus {mat_short} im Kontakt mit {chem_name} regelmäßig auf Quellung, Verfärbung oder Verlust der mechanischen Festigkeit als Frühwarnsignale eines chemischen Angriffs untersucht.',
        'Bei der Auswahl von {family_word}n für den Einsatz mit {chem_name} berücksichtigen Ingenieure neben der Beständigkeitsbewertung auch Permeationsrate, Kriechverhalten und Schweißbarkeit.',
        'Die hier gezeigten Bewertungen gelten für reines {chem_name} im Kontakt mit dem Basiswerkstoff. In der Praxis können Additive, Pigmente und Füllstoffe die Beständigkeit in beide Richtungen verändern.',
        'Chemische Beständigkeitsprüfungen nach DIN- und ISO-Normen bewerten typischerweise Gewichtsänderung, Maßänderung und Erhalt der Zugfestigkeit nach Eintauchen.',
    ],
    'es': [
        '{mat_full} fue desarrollado por primera vez en la década de {decade} y sigue siendo uno de los {family_word}s más utilizados en equipos de manipulación de productos químicos.',
        'La resistencia química de {mat_short} depende no solo de la concentración, sino también del tiempo de exposición, las tensiones mecánicas y la presencia de otros productos químicos en la mezcla.',
        '{mat_full} se elige habitualmente para {apps} por su combinación de resistencia química, resistencia mecánica y rentabilidad.',
        'La temperatura suele ser el factor decisivo al seleccionar materiales para {chem_name}: incluso los materiales con clasificación A a 20 °C pueden perder rendimiento a temperaturas elevadas.',
        'En la práctica industrial, los componentes de {mat_short} expuestos a {chem_name} se inspeccionan regularmente en busca de hinchamiento, decoloración o pérdida de resistencia mecánica como indicadores tempranos de ataque químico.',
        'Al elegir entre {family_word}s para servicio con {chem_name}, los ingenieros consideran no solo la clasificación de resistencia, sino también factores como la tasa de permeación, la resistencia a la fluencia y la soldabilidad.',
        'Las clasificaciones mostradas aquí se aplican a {chem_name} puro en contacto con el {family_word} base. En aplicaciones reales, los aditivos, pigmentos y cargas del material pueden modificar la resistencia en ambas direcciones.',
        'Los ensayos de resistencia química según normas DIN e ISO evalúan típicamente el cambio de peso, el cambio dimensional y la retención de la resistencia a la tracción tras la inmersión.',
    ],
}

FAMILY_WORDS = {
    'thermoplastic': {'en': 'thermoplastic', 'de': 'Thermoplast', 'es': 'termoplástico'},
    'fluoropolymer': {'en': 'fluoropolymer', 'de': 'Fluorkunststoff', 'es': 'fluoropolímero'},
    'elastomer': {'en': 'elastomer', 'de': 'Elastomer', 'es': 'elastómero'},
    'metal': {'en': 'metal', 'de': 'Metall', 'es': 'metal'},
}

# Approximate decades of first commercial availability
MATERIAL_DECADES = {
    'HDPE': 1950, 'LDPE': 1930, 'PP': 1950, 'PVC_HART': 1920, 'PVC_WEICH': 1920,
    'PMP': 1960, 'PS': 1930, 'SAN': 1940, 'PC': 1950, 'PETG': 1960,
    'POM': 1950, 'PA': 1930, 'PSU': 1960, 'PTFE': 1940, 'FEP': 1960,
    'PVDF': 1960, 'ECTFE_ETFE': 1970, 'EPDM': 1960, 'FPM': 1950,
    'NBR': 1930, 'SI': 1940, 'V4A': 1920, 'V2A': 1910, 'AL': 1880,
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _det_hash(slug, mat_code):
    """Deterministic integer from slug + material, for selecting template variants."""
    h = hashlib.md5(('%s|%s' % (slug, mat_code)).encode()).hexdigest()
    return int(h, 16)


def _classify_chemical(chem):
    """Return a list of matching categories for a chemical, ordered by priority."""
    search = ' '.join([
        chem['name_de'].lower(), chem['name_en'].lower(),
        (chem.get('formula') or '').lower(),
        (chem.get('hazard') or '').lower(),
    ])
    cats = []
    for cat, info in CHEMICAL_CATEGORIES.items():
        if any(kw in search for kw in info['keywords']):
            cats.append(cat)
    # If nothing matched, try to infer from hazard symbols
    if not cats:
        hazard = (chem.get('hazard') or '').upper()
        if 'C' in hazard:
            cats.append('acid')   # corrosive often implies acid/base
        if 'O' in hazard:
            cats.append('oxidizer')
        if chem.get('flammable'):
            cats.append('solvent')
    return cats or ['salt']  # default fallback


def _worst_rating(ratings_list):
    """Return the worst rating letter from a list of rating dicts."""
    worst = 'A'
    for r in ratings_list:
        if r is None:
            continue
        for key in ('w20', 'w50'):
            g = r.get(key)
            if g and rd.GRADE_RANK.get(g, 5) > rd.GRADE_RANK.get(worst, 0):
                worst = g
    return worst


def _best_rating(ratings_list):
    """Return the best rating letter from a list of rating dicts."""
    best = 'D'
    for r in ratings_list:
        if r is None:
            continue
        g = r.get('w20')
        if g and rd.GRADE_RANK.get(g, 5) < rd.GRADE_RANK.get(best, 5):
            best = g
    return best


def _count_concentrations(chem, mat):
    """Count how many concentration variants include data for this material."""
    return sum(1 for v in chem['variants'] if mat in v['ratings'])


def _has_temp_degradation(chem, mat):
    """Check if any variant shows worse rating at 50 °C than 20 °C."""
    for v in chem['variants']:
        r = v['ratings'].get(mat)
        if r and r.get('w20') and r.get('w50'):
            if rd.GRADE_RANK.get(r['w50'], 0) > rd.GRADE_RANK.get(r['w20'], 0):
                return True
    return False


def _conc_range_text(chem, mat, lang):
    """Describe the concentration range tested for this pair."""
    concs = []
    for v in chem['variants']:
        if mat in v['ratings']:
            label = conc_label(v['conc'], lang)
            if label:
                concs.append(label)
    return concs


def _alternatives_rated_a(chem, mat):
    """Materials rated A for this chemical that are NOT the current material."""
    from build_chemical_pages import primary_variant
    pv = primary_variant(chem)
    return [m for m, r in pv['ratings'].items()
            if r.get('w20') == 'A' and m != mat]


# ---------------------------------------------------------------------------
# Paragraph generators — EN, DE, ES
# ---------------------------------------------------------------------------

def _conc_guidance(lang, chem, mat, chem_name, mat_short, slug):
    """§1: Concentration-specific guidance derived from actual ratings."""
    rated = [(v, v['ratings'][mat]) for v in chem['variants'] if mat in v['ratings']]
    if not rated:
        return ''

    n_concs = len(rated)
    all_ratings_20 = [r.get('w20') for _, r in rated if r.get('w20')]
    has_temp_deg = _has_temp_degradation(chem, mat)
    has_pitting = any(r.get('pit20') or r.get('pit50') for _, r in rated)

    all_a = all(g == 'A' for g in all_ratings_20)
    all_same = len(set(all_ratings_20)) == 1 and all_ratings_20
    has_degradation = len(set(all_ratings_20)) > 1
    concs = _conc_range_text(chem, mat, lang)
    conc_str = ', '.join(concs) if concs else ''
    family = rd.MATERIALS[mat][1]

    # Extra detail sentences based on data signals
    def _temp_sentence(lang):
        if not has_temp_deg:
            return {
                'en': ' The rating remains stable between 20 °C and 50 °C, which means this material can also handle moderately elevated process temperatures without additional risk.',
                'de': ' Die Bewertung bleibt zwischen 20 °C und 50 °C stabil, sodass dieser Werkstoff auch bei moderat erhöhten Prozesstemperaturen ohne zusätzliches Risiko eingesetzt werden kann.',
                'es': ' La clasificación se mantiene estable entre 20 °C y 50 °C, lo que significa que este material también puede soportar temperaturas de proceso moderadamente elevadas sin riesgo adicional.',
            }.get(lang, '')
        return {
            'en': ' However, at 50 °C the resistance rating drops, indicating that temperature must be factored into the design. For heated applications, additional testing under actual service conditions is strongly recommended.',
            'de': ' Bei 50 °C sinkt die Beständigkeitsbewertung jedoch, was darauf hinweist, dass die Temperatur in der Auslegung berücksichtigt werden muss. Für beheizte Anwendungen wird eine zusätzliche Prüfung unter realen Betriebsbedingungen dringend empfohlen.',
            'es': ' Sin embargo, a 50 °C la clasificación de resistencia baja, lo que indica que la temperatura debe tenerse en cuenta en el diseño. Para aplicaciones con calor, se recomienda encarecidamente realizar ensayos adicionales en condiciones reales de servicio.',
        }.get(lang, '')

    def _pitting_sentence(lang):
        if not has_pitting:
            return ''
        return {
            'en': ' Note that the source flags a risk of pitting or stress-corrosion cracking for this combination, which is particularly relevant for pressure-bearing or structurally loaded components.',
            'de': ' Beachten Sie, dass die Quelle ein Risiko von Lochfraß oder Spannungsrisskorrosion für diese Kombination angibt, was besonders für drucktragende oder strukturell belastete Bauteile relevant ist.',
            'es': ' Tenga en cuenta que la fuente señala un riesgo de picaduras o corrosión bajo tensión para esta combinación, lo cual es particularmente relevante para componentes sometidos a presión o carga estructural.',
        }.get(lang, '')

    if lang == 'en':
        if n_concs == 1:
            r = rated[0][1]
            grade = r.get('w20', '–')
            c = conc_label(rated[0][0]['conc'], lang)
            conc_at = ' at %s' % c if c else ''
            if grade == 'A':
                s = '%s shows very good resistance (A) to %s%s at 20 °C, meaning the material remains essentially unaffected by this chemical under standard laboratory test conditions.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('en') + _pitting_sentence('en')
                return s
            elif grade == 'B':
                s = '%s shows good but limited resistance (B) to %s%s at 20 °C. The material can be used in contact with this chemical, but minor effects such as slight swelling or a small reduction in mechanical properties may occur over extended exposure periods. Regular inspection of components in service is advisable.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('en') + _pitting_sentence('en')
                return s
            elif grade == 'C':
                s = '%s has limited resistance (C) to %s%s at 20 °C. This indicates that the chemical has a noticeable effect on the material, which may include visible swelling, softening, or a measurable loss of tensile strength. Use is generally limited to short-term or intermittent contact where full structural integrity is not required.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('en') + _pitting_sentence('en')
                return s
            else:
                s = '%s is not resistant (D) to %s%s and should not be used in direct contact. The chemical is expected to cause rapid degradation, which can include dissolution, cracking, severe swelling, or complete structural failure of the material.' % (mat_short, chem_name, conc_at)
                s += _pitting_sentence('en')
                return s
        else:
            if all_a:
                s = '%s shows excellent resistance to %s across all %d tested concentrations (%s) at 20 °C, making it a reliable choice for storage, transfer, and handling applications involving this chemical at any of the tested strengths.' % (mat_short, chem_name, n_concs, conc_str)
                s += _temp_sentence('en') + _pitting_sentence('en')
                return s
            elif all_same:
                s = '%s maintains a consistent rating of %s across all %d tested concentrations (%s) of %s at 20 °C. The fact that the rating does not change with concentration within the tested range simplifies material selection, though the boundary conditions beyond this range remain untested.' % (mat_short, all_ratings_20[0], n_concs, conc_str, chem_name)
                s += _temp_sentence('en') + _pitting_sentence('en')
                return s
            elif has_degradation:
                best = _best_rating([r for _, r in rated])
                worst = _worst_rating([r for _, r in rated])
                s = 'The resistance of %s to %s is concentration-dependent. Across the %d tested concentrations (%s), the 20 °C rating ranges from %s at lower concentrations to %s at higher ones. This means engineers must verify which concentration their process actually involves before relying on a single rating.' % (mat_short, chem_name, n_concs, conc_str, best, worst)
                s += _temp_sentence('en') + _pitting_sentence('en')
                return s

    elif lang == 'de':
        if n_concs == 1:
            r = rated[0][1]
            grade = r.get('w20', '–')
            c = conc_label(rated[0][0]['conc'], lang)
            conc_at = ' bei %s' % c if c else ''
            if grade == 'A':
                s = '%s zeigt sehr gute Beständigkeit (A) gegenüber %s%s bei 20 °C. Das bedeutet, dass der Werkstoff unter Standard-Laborbedingungen von dieser Chemikalie im Wesentlichen nicht angegriffen wird.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('de') + _pitting_sentence('de')
                return s
            elif grade == 'B':
                s = '%s zeigt gute, aber eingeschränkte Beständigkeit (B) gegenüber %s%s bei 20 °C. Der Werkstoff kann im Kontakt verwendet werden, es können jedoch bei längerer Einwirkung geringfügige Effekte wie leichtes Quellen oder eine geringe Abnahme der mechanischen Eigenschaften auftreten. Eine regelmäßige Inspektion der Bauteile im Betrieb ist ratsam.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('de') + _pitting_sentence('de')
                return s
            elif grade == 'C':
                s = '%s hat eingeschränkte Beständigkeit (C) gegenüber %s%s bei 20 °C. Dies weist darauf hin, dass die Chemikalie den Werkstoff merklich beeinflusst, was sichtbares Quellen, Erweichen oder einen messbaren Verlust der Zugfestigkeit umfassen kann. Die Verwendung beschränkt sich in der Regel auf kurzzeitigen oder gelegentlichen Kontakt.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('de') + _pitting_sentence('de')
                return s
            else:
                s = '%s ist nicht beständig (D) gegenüber %s%s und sollte nicht in direktem Kontakt eingesetzt werden. Die Chemikalie führt voraussichtlich zu schnellem Abbau, der Auflösung, Rissbildung, starkes Quellen oder vollständiges Strukturversagen umfassen kann.' % (mat_short, chem_name, conc_at)
                s += _pitting_sentence('de')
                return s
        else:
            if all_a:
                s = '%s zeigt ausgezeichnete Beständigkeit gegenüber %s über alle %d getesteten Konzentrationen (%s) bei 20 °C und ist damit eine zuverlässige Wahl für Lagerung, Transport und Handhabung bei jeder der getesteten Stärken.' % (mat_short, chem_name, n_concs, conc_str)
                s += _temp_sentence('de') + _pitting_sentence('de')
                return s
            elif all_same:
                s = '%s behält eine konstante Bewertung von %s über alle %d getesteten Konzentrationen (%s) von %s bei 20 °C. Dass sich die Bewertung im getesteten Bereich nicht mit der Konzentration ändert, vereinfacht die Werkstoffauswahl, wobei das Verhalten jenseits dieses Bereichs ungeprüft bleibt.' % (mat_short, all_ratings_20[0], n_concs, conc_str, chem_name)
                s += _temp_sentence('de') + _pitting_sentence('de')
                return s
            elif has_degradation:
                best = _best_rating([r for _, r in rated])
                worst = _worst_rating([r for _, r in rated])
                s = 'Die Beständigkeit von %s gegenüber %s ist konzentrationsabhängig. Über die %d getesteten Konzentrationen (%s) reicht die 20-°C-Bewertung von %s bei niedrigeren bis %s bei höheren Konzentrationen. Ingenieure müssen daher prüfen, welche Konzentration ihr Prozess tatsächlich umfasst, bevor sie sich auf eine einzelne Bewertung verlassen.' % (mat_short, chem_name, n_concs, conc_str, best, worst)
                s += _temp_sentence('de') + _pitting_sentence('de')
                return s

    elif lang == 'es':
        if n_concs == 1:
            r = rated[0][1]
            grade = r.get('w20', '–')
            c = conc_label(rated[0][0]['conc'], lang)
            conc_at = ' a %s' % c if c else ''
            if grade == 'A':
                s = '%s muestra muy buena resistencia (A) a %s%s a 20 °C, lo que significa que el material permanece esencialmente inalterado por este producto químico en condiciones estándar de ensayo de laboratorio.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('es') + _pitting_sentence('es')
                return s
            elif grade == 'B':
                s = '%s muestra buena pero limitada resistencia (B) a %s%s a 20 °C. El material puede usarse en contacto con este producto químico, pero pueden producirse efectos menores como ligero hinchamiento o una pequeña reducción de las propiedades mecánicas durante periodos de exposición prolongados. Se recomienda la inspección periódica de los componentes en servicio.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('es') + _pitting_sentence('es')
                return s
            elif grade == 'C':
                s = '%s tiene resistencia limitada (C) a %s%s a 20 °C. Esto indica que el producto químico tiene un efecto notable sobre el material, que puede incluir hinchamiento visible, ablandamiento o una pérdida medible de resistencia a la tracción. El uso se limita generalmente al contacto breve o intermitente.' % (mat_short, chem_name, conc_at)
                s += _temp_sentence('es') + _pitting_sentence('es')
                return s
            else:
                s = '%s no es resistente (D) a %s%s y no debe usarse en contacto directo. Se espera que el producto químico provoque una degradación rápida, que puede incluir disolución, agrietamiento, hinchamiento severo o fallo estructural completo del material.' % (mat_short, chem_name, conc_at)
                s += _pitting_sentence('es')
                return s
        else:
            if all_a:
                s = '%s muestra excelente resistencia a %s en las %d concentraciones ensayadas (%s) a 20 °C, lo que lo convierte en una opción fiable para almacenamiento, transferencia y manipulación de este producto químico a cualquiera de las concentraciones ensayadas.' % (mat_short, chem_name, n_concs, conc_str)
                s += _temp_sentence('es') + _pitting_sentence('es')
                return s
            elif all_same:
                s = '%s mantiene una clasificación constante de %s en las %d concentraciones ensayadas (%s) de %s a 20 °C. El hecho de que la clasificación no cambie con la concentración dentro del rango ensayado simplifica la selección de materiales, aunque las condiciones límite fuera de este rango no se han verificado.' % (mat_short, all_ratings_20[0], n_concs, conc_str, chem_name)
                s += _temp_sentence('es') + _pitting_sentence('es')
                return s
            elif has_degradation:
                best = _best_rating([r for _, r in rated])
                worst = _worst_rating([r for _, r in rated])
                s = 'La resistencia de %s a %s depende de la concentración. En las %d concentraciones ensayadas (%s), la clasificación a 20 °C varía de %s en concentraciones más bajas a %s en las más altas. Los ingenieros deben verificar qué concentración implica realmente su proceso antes de basarse en una sola clasificación.' % (mat_short, chem_name, n_concs, conc_str, best, worst)
                s += _temp_sentence('es') + _pitting_sentence('es')
                return s

    return ''


def _application_context(lang, chem, mat, chem_name, mat_short, slug):
    """§2: Application context from chemical category + material family."""
    cats = _classify_chemical(chem)
    family = rd.MATERIALS[mat][1]
    h = _det_hash(slug, mat)

    primary_cat = cats[0]
    industries = INDUSTRY_CONTEXT.get(primary_cat, INDUSTRY_CONTEXT['salt'])
    apps = MATERIAL_APPS.get(family, MATERIAL_APPS['thermoplastic'])
    family_word = FAMILY_WORDS.get(family, FAMILY_WORDS['thermoplastic'])
    mat_full = MATERIAL_FULL.get(mat, mat_short)

    # Pick two distinct industries deterministically
    ind_list = industries.get(lang, industries['en'])
    ind = ind_list[h % len(ind_list)]
    ind2 = ind_list[(h // 7) % len(ind_list)]
    while ind2 == ind and len(ind_list) > 1:
        ind2 = ind_list[(h // 13) % len(ind_list)]

    # Hazard context
    hazard = chem.get('hazard', '')
    is_corrosive = 'C' in (hazard or '').upper()
    is_flammable = chem.get('flammable', False)

    if lang == 'en':
        s = '%s is commonly encountered in %s and %s.' % (chem_name, ind, ind2)
        article = 'an' if family_word['en'][0] in 'aeiou' else 'a'
        s += ' %s (%s) is %s %s typically used for %s.' % (mat_short, mat_full, article, family_word['en'], apps['en'])
        if is_corrosive:
            s += ' Because %s is classified as corrosive, the choice of containment material is especially critical to prevent leaks, equipment damage, and safety hazards.' % chem_name
        elif is_flammable:
            s += ' Since %s is flammable, material selection must also consider the risk of static charge buildup and the need for proper grounding in storage and transfer systems.' % chem_name
        else:
            s += ' The compatibility between these two is therefore an important consideration for engineers and procurement teams selecting containment, transfer, or processing equipment.'
        return s

    elif lang == 'de':
        s = '%s kommt häufig in der %s und %s vor.' % (chem_name, ind, ind2)
        s += ' %s (%s) ist ein %s, der typischerweise für %s eingesetzt wird.' % (mat_short, mat_full, family_word['de'], apps['de'])
        if is_corrosive:
            s += ' Da %s als ätzend eingestuft ist, ist die Wahl des Behälterwerkstoffs besonders kritisch, um Leckagen, Anlagenschäden und Sicherheitsrisiken zu vermeiden.' % chem_name
        elif is_flammable:
            s += ' Da %s entzündlich ist, muss bei der Werkstoffauswahl auch das Risiko einer statischen Aufladung und die Notwendigkeit einer ordnungsgemäßen Erdung in Lager- und Umfüllsystemen berücksichtigt werden.' % chem_name
        else:
            s += ' Die Verträglichkeit beider ist daher ein wichtiger Aspekt für Ingenieure und Beschaffungsteams bei der Auswahl von Behältern, Leitungen und Verarbeitungsanlagen.'
        return s

    elif lang == 'es':
        s = '%s se encuentra habitualmente en %s y %s.' % (chem_name, ind, ind2)
        s += ' %s (%s) es un %s utilizado típicamente para %s.' % (mat_short, mat_full, family_word['es'], apps['es'])
        if is_corrosive:
            s += ' Dado que %s se clasifica como corrosivo, la elección del material de contención es especialmente crítica para prevenir fugas, daños en equipos y riesgos de seguridad.' % chem_name
        elif is_flammable:
            s += ' Dado que %s es inflamable, la selección del material también debe considerar el riesgo de acumulación de carga estática y la necesidad de una puesta a tierra adecuada en los sistemas de almacenamiento y transferencia.' % chem_name
        else:
            s += ' La compatibilidad entre ambos es, por tanto, una consideración importante para los ingenieros y equipos de compras que seleccionan equipos de contención, transferencia o procesamiento.'
        return s
    return ''


def _practical_recommendation(lang, chem, mat, chem_name, mat_short, slug):
    """§3: Practical recommendation based on overall rating."""
    from build_chemical_pages import primary_variant
    pv = primary_variant(chem)
    r = pv['ratings'].get(mat)
    if not r:
        if lang == 'en':
            return 'No resistance data is available for %s in contact with %s. Before using this combination, consult the material manufacturer or conduct independent testing.' % (
                mat_short, chem_name)
        elif lang == 'de':
            return 'Für %s im Kontakt mit %s liegen keine Beständigkeitsdaten vor. Vor der Verwendung dieser Kombination sollten Sie den Werkstoffhersteller konsultieren oder unabhängige Tests durchführen.' % (
                mat_short, chem_name)
        elif lang == 'es':
            return 'No hay datos de resistencia disponibles para %s en contacto con %s. Antes de usar esta combinación, consulte al fabricante del material o realice ensayos independientes.' % (
                mat_short, chem_name)
        return ''

    grade = r.get('w20', '')
    has_temp_deg = _has_temp_degradation(chem, mat)
    a_alts = _alternatives_rated_a(chem, mat)
    n_alts = min(len(a_alts), 3)
    alt_names = ', '.join(material_name(m, lang) for m in a_alts[:n_alts]) if a_alts else ''

    if lang == 'en':
        if grade == 'A':
            base = '%s can be used with confidence for %s containment and handling. The A rating indicates that the material shows no significant change in weight, dimensions, or mechanical properties after prolonged contact under test conditions.' % (mat_short, chem_name)
            if has_temp_deg:
                base += ' At elevated temperatures (50 °C), some reduction in resistance occurs, so periodic inspection is advisable for heated applications. Always verify performance under actual operating conditions before committing to a design.'
            else:
                base += ' This holds true at both 20 °C and 50 °C, giving a good safety margin for typical process environments.'
            return base
        elif grade == 'B':
            base = '%s is suitable for use with %s under normal conditions, but some minor effects on the material are expected over time. Periodic monitoring for swelling, softening, or weight change is recommended, especially for long-service components.' % (mat_short, chem_name)
            if has_temp_deg:
                base += ' Avoid prolonged exposure at elevated temperatures, as the resistance decreases further at 50 °C.'
            if alt_names:
                base += ' For safety-critical or long-life applications, consider %s instead, which are rated A for this chemical.' % alt_names
            return base
        elif grade == 'C':
            base = '%s has limited resistance to %s and should only be used for short-term or intermittent contact at ambient temperature. The C rating means the material undergoes noticeable changes — swelling, loss of strength, or surface degradation — that make it unsuitable for permanent installations.' % (mat_short, chem_name)
            if alt_names:
                base += ' For prolonged or continuous exposure, %s offer significantly better resistance and are rated A.' % alt_names
            return base
        else:
            base = '%s is not recommended for use with %s. The D rating indicates that the material will suffer rapid and severe degradation, which may include cracking, dissolution, severe swelling, or complete structural failure. Using this combination risks equipment damage, leaks, and potential safety incidents.' % (mat_short, chem_name)
            if alt_names:
                base += ' Consider using %s instead, which are rated A for this chemical and offer reliable long-term performance.' % alt_names
            return base

    elif lang == 'de':
        if grade == 'A':
            base = '%s kann mit Zuversicht für die Lagerung und Handhabung von %s eingesetzt werden. Die Bewertung A bedeutet, dass der Werkstoff nach längerem Kontakt unter Prüfbedingungen keine wesentlichen Änderungen in Gewicht, Abmessungen oder mechanischen Eigenschaften zeigt.' % (mat_short, chem_name)
            if has_temp_deg:
                base += ' Bei erhöhten Temperaturen (50 °C) tritt eine gewisse Verringerung der Beständigkeit auf; regelmäßige Inspektion ist bei beheizten Anwendungen ratsam. Das Verhalten unter realen Betriebsbedingungen sollte stets vorab geprüft werden.'
            else:
                base += ' Dies gilt sowohl bei 20 °C als auch bei 50 °C und bietet einen guten Sicherheitsspielraum für typische Prozessumgebungen.'
            return base
        elif grade == 'B':
            base = '%s ist unter normalen Bedingungen für den Einsatz mit %s geeignet, es ist jedoch mit geringfügigen Auswirkungen auf den Werkstoff zu rechnen. Eine regelmäßige Kontrolle auf Quellung, Erweichung oder Gewichtsänderung wird empfohlen, insbesondere bei langlebigen Bauteilen.' % (mat_short, chem_name)
            if has_temp_deg:
                base += ' Eine langzeitige Exposition bei erhöhten Temperaturen sollte vermieden werden, da die Beständigkeit bei 50 °C weiter abnimmt.'
            if alt_names:
                base += ' Für sicherheitskritische oder langlebige Anwendungen sollten %s (Bewertung A) in Betracht gezogen werden.' % alt_names
            return base
        elif grade == 'C':
            base = '%s hat eingeschränkte Beständigkeit gegenüber %s und sollte nur für kurzzeitigen oder gelegentlichen Kontakt bei Raumtemperatur verwendet werden. Die Bewertung C bedeutet, dass der Werkstoff merkliche Veränderungen erfährt — Quellung, Festigkeitsverlust oder Oberflächenabbau —, die ihn für dauerhafte Installationen ungeeignet machen.' % (mat_short, chem_name)
            if alt_names:
                base += ' Für dauerhafte oder kontinuierliche Belastung bieten %s deutlich bessere Beständigkeit (Bewertung A).' % alt_names
            return base
        else:
            base = '%s wird für den Einsatz mit %s nicht empfohlen. Die Bewertung D zeigt an, dass der Werkstoff schnell und stark abgebaut wird, was Rissbildung, Auflösung, starke Quellung oder vollständiges Strukturversagen umfassen kann. Die Verwendung dieser Kombination birgt das Risiko von Anlagenschäden, Leckagen und Sicherheitsvorfällen.' % (mat_short, chem_name)
            if alt_names:
                base += ' Erwägen Sie stattdessen %s, die für diese Chemikalie mit A bewertet sind und eine zuverlässige Langzeitleistung bieten.' % alt_names
            return base

    elif lang == 'es':
        if grade == 'A':
            base = '%s puede utilizarse con confianza para el almacenamiento y manipulación de %s. La clasificación A indica que el material no muestra cambios significativos en peso, dimensiones o propiedades mecánicas tras contacto prolongado en condiciones de ensayo.' % (mat_short, chem_name)
            if has_temp_deg:
                base += ' A temperaturas elevadas (50 °C) se produce cierta reducción de la resistencia; se recomienda inspección periódica en aplicaciones con calor. Verifique siempre el rendimiento en las condiciones reales de operación antes de definir el diseño.'
            else:
                base += ' Esto se cumple tanto a 20 °C como a 50 °C, proporcionando un buen margen de seguridad para entornos de proceso típicos.'
            return base
        elif grade == 'B':
            base = '%s es adecuado para uso con %s en condiciones normales, pero se esperan algunos efectos menores sobre el material con el tiempo. Se recomienda monitoreo periódico de hinchamiento, ablandamiento o cambio de peso, especialmente en componentes de larga vida útil.' % (mat_short, chem_name)
            if has_temp_deg:
                base += ' Evite la exposición prolongada a temperaturas elevadas, ya que la resistencia disminuye más a 50 °C.'
            if alt_names:
                base += ' Para aplicaciones críticas de seguridad o larga duración, considere %s, que tienen clasificación A para este producto químico.' % alt_names
            return base
        elif grade == 'C':
            base = '%s tiene resistencia limitada a %s y solo debe usarse para contacto breve o intermitente a temperatura ambiente. La clasificación C significa que el material experimenta cambios notables — hinchamiento, pérdida de resistencia o degradación superficial — que lo hacen inadecuado para instalaciones permanentes.' % (mat_short, chem_name)
            if alt_names:
                base += ' Para exposición prolongada o continua, %s ofrecen una resistencia significativamente mejor (clasificación A).' % alt_names
            return base
        else:
            base = '%s no se recomienda para uso con %s. La clasificación D indica que el material sufrirá una degradación rápida y severa, que puede incluir agrietamiento, disolución, hinchamiento severo o fallo estructural completo. Utilizar esta combinación supone riesgo de daños en equipos, fugas e incidentes de seguridad.' % (mat_short, chem_name)
            if alt_names:
                base += ' Considere utilizar %s en su lugar, que tienen clasificación A y ofrecen un rendimiento fiable a largo plazo.' % alt_names
            return base

    return ''


def _did_you_know(lang, chem, mat, chem_name, mat_short, slug):
    """§4: A unique 'Did you know?' fact per page."""
    if lang not in DID_YOU_KNOW:
        return ''
    h = _det_hash(slug, mat)
    family = rd.MATERIALS[mat][1]
    templates = DID_YOU_KNOW[lang]
    idx = h % len(templates)
    family_word = FAMILY_WORDS.get(family, FAMILY_WORDS['thermoplastic']).get(lang, 'material')
    apps = MATERIAL_APPS.get(family, MATERIAL_APPS['thermoplastic']).get(lang, '')
    decade = MATERIAL_DECADES.get(mat, 1950)
    return templates[idx].format(
        mat_full=MATERIAL_FULL.get(mat, mat_short),
        mat_short=mat_short,
        chem_name=chem_name,
        family_word=family_word,
        apps=apps,
        decade=decade,
    )


# ---------------------------------------------------------------------------
# Supplementary paragraph for no-data pairs
# ---------------------------------------------------------------------------

# General properties of each material family — used when no resistance data exists
FAMILY_PROPERTIES = {
    'thermoplastic': {
        'en': ('{mat_short} ({mat_full}) is a thermoplastic polymer, meaning it softens when heated '
               'and can be reshaped without chemical degradation. Thermoplastics are widely used in '
               'chemical handling because they resist many aqueous solutions and dilute acids. '
               'However, they can be attacked by strong solvents, oxidizing agents, or concentrated '
               'chemicals depending on the specific polymer. Key properties that make thermoplastics '
               'attractive for chemical equipment include low cost, ease of fabrication by welding or '
               'injection molding, good impact resistance, and low weight compared to metals. Their '
               'main limitations are a lower temperature ceiling than metals or fluoropolymers and '
               'susceptibility to stress cracking in certain chemical environments.'),
        'de': ('{mat_short} ({mat_full}) ist ein thermoplastischer Kunststoff, der beim Erhitzen erweicht '
               'und ohne chemischen Abbau umgeformt werden kann. Thermoplaste werden wegen ihrer Beständigkeit '
               'gegenüber vielen wässrigen Lösungen und verdünnten Säuren häufig in der chemischen Verfahrenstechnik '
               'eingesetzt. Sie können jedoch je nach Polymertyp von starken Lösungsmitteln, Oxidationsmitteln '
               'oder konzentrierten Chemikalien angegriffen werden. Zu ihren Vorteilen zählen niedrige '
               'Kosten, einfache Verarbeitung durch Schweißen oder Spritzguss, gute Schlagzähigkeit und '
               'geringes Gewicht im Vergleich zu Metallen. Ihre Haupteinschränkungen sind eine niedrigere '
               'Temperaturgrenze als bei Metallen oder Fluorkunststoffen und die Anfälligkeit für '
               'Spannungsrissbildung in bestimmten chemischen Umgebungen.'),
        'es': ('{mat_short} ({mat_full}) es un polímero termoplástico, lo que significa que se ablanda '
               'al calentarse y puede reformarse sin degradación química. Los termoplásticos se utilizan '
               'ampliamente en el manejo de productos químicos por su resistencia a muchas soluciones '
               'acuosas y ácidos diluidos. Sin embargo, pueden ser atacados por disolventes fuertes, '
               'agentes oxidantes o productos químicos concentrados según el polímero específico. Las '
               'propiedades clave que hacen atractivos a los termoplásticos para equipos químicos incluyen '
               'bajo coste, facilidad de fabricación por soldadura o moldeo por inyección, buena resistencia '
               'al impacto y bajo peso en comparación con los metales. Sus principales limitaciones son un '
               'techo de temperatura inferior al de los metales o fluoropolímeros y la susceptibilidad a la '
               'fisuración por tensión en ciertos entornos químicos.'),
    },
    'fluoropolymer': {
        'en': ('{mat_short} ({mat_full}) belongs to the fluoropolymer family, a class of plastics '
               'in which hydrogen atoms are partially or fully replaced by fluorine. This fluorine '
               'substitution gives fluoropolymers outstanding chemical inertness, making them resistant '
               'to virtually all acids, bases, and solvents at moderate temperatures. They also offer '
               'excellent thermal stability, low surface energy, and very low friction coefficients. '
               'The trade-offs include higher cost than standard thermoplastics, more difficult '
               'processing, and in some cases lower mechanical strength and creep resistance. '
               'Fluoropolymers are the material of choice for lining, sealing, and gasketing in the '
               'most aggressive chemical environments.'),
        'de': ('{mat_short} ({mat_full}) gehört zur Familie der Fluorkunststoffe, einer Klasse von '
               'Kunststoffen, bei denen Wasserstoffatome teilweise oder vollständig durch Fluor ersetzt '
               'sind. Diese Fluorsubstitution verleiht Fluorkunststoffen eine hervorragende chemische '
               'Inertheit, sodass sie gegen nahezu alle Säuren, Laugen und Lösungsmittel bei moderaten '
               'Temperaturen beständig sind. Sie bieten außerdem ausgezeichnete thermische Stabilität, '
               'niedrige Oberflächenenergie und sehr niedrige Reibungskoeffizienten. Zu den Nachteilen '
               'gehören höhere Kosten als bei Standardthermoplasten, schwierigere Verarbeitung und '
               'in einigen Fällen geringere mechanische Festigkeit und Kriechbeständigkeit. '
               'Fluorkunststoffe sind die erste Wahl für Auskleidungen, Dichtungen und '
               'Flanschdichtungen in besonders aggressiven chemischen Umgebungen.'),
        'es': ('{mat_short} ({mat_full}) pertenece a la familia de los fluoropolímeros, una clase de '
               'plásticos en los que los átomos de hidrógeno se sustituyen parcial o totalmente por '
               'flúor. Esta sustitución confiere a los fluoropolímeros una excepcional inercia química, '
               'haciéndolos resistentes a prácticamente todos los ácidos, bases y disolventes a '
               'temperaturas moderadas. También ofrecen excelente estabilidad térmica, baja energía '
               'superficial y coeficientes de fricción muy bajos. Las contrapartidas incluyen un coste '
               'superior al de los termoplásticos estándar, un procesamiento más difícil y, en algunos '
               'casos, menor resistencia mecánica y a la fluencia. Los fluoropolímeros son el material '
               'de elección para revestimientos, sellos y juntas en los entornos químicos más agresivos.'),
    },
    'elastomer': {
        'en': ('{mat_short} ({mat_full}) is an elastomer — a rubber-like polymer that can stretch '
               'significantly and return to its original shape. Elastomers are essential in chemical '
               'equipment as seals, O-rings, gaskets, and flexible hose linings. Their chemical '
               'resistance varies widely by type: some elastomers excel with oils and fuels, others '
               'with acids and oxidizers. Key selection factors include temperature range, compression '
               'set resistance, hardness, and compatibility with the specific process fluid. In '
               'general, elastomers have a lower temperature limit than thermoplastics or metals and '
               'can be degraded by strong solvents, but their flexibility and sealing performance '
               'make them indispensable where a rigid material cannot provide a reliable seal.'),
        'de': ('{mat_short} ({mat_full}) ist ein Elastomer — ein gummiartiger Kunststoff, der sich '
               'erheblich dehnen und in seine ursprüngliche Form zurückkehren kann. Elastomere sind '
               'in chemischen Anlagen als Dichtungen, O-Ringe und flexible Schlauchliner unverzichtbar. '
               'Ihre chemische Beständigkeit variiert je nach Typ erheblich: Einige Elastomere eignen '
               'sich hervorragend für Öle und Kraftstoffe, andere für Säuren und Oxidationsmittel. '
               'Wichtige Auswahlkriterien sind Temperaturbereich, Druckverformungsrest, Härte und '
               'Verträglichkeit mit dem jeweiligen Prozessmedium. Elastomere haben generell eine '
               'niedrigere Temperaturgrenze als Thermoplaste oder Metalle und können von starken '
               'Lösungsmitteln angegriffen werden, doch ihre Flexibilität und Dichtleistung machen '
               'sie dort unentbehrlich, wo ein starres Material keine zuverlässige Abdichtung bieten kann.'),
        'es': ('{mat_short} ({mat_full}) es un elastómero, un polímero similar al caucho que puede '
               'estirarse significativamente y volver a su forma original. Los elastómeros son esenciales '
               'en equipos químicos como sellos, juntas tóricas y revestimientos de mangueras flexibles. '
               'Su resistencia química varía ampliamente según el tipo: algunos elastómeros destacan con '
               'aceites y combustibles, otros con ácidos y oxidantes. Los factores clave de selección '
               'incluyen el rango de temperatura, la resistencia a la deformación permanente por '
               'compresión, la dureza y la compatibilidad con el fluido de proceso específico. En '
               'general, los elastómeros tienen un límite de temperatura inferior al de los termoplásticos '
               'o metales y pueden ser degradados por disolventes fuertes, pero su flexibilidad y '
               'capacidad de sellado los hacen indispensables donde un material rígido no puede '
               'proporcionar un sello fiable.'),
    },
    'metal': {
        'en': ('{mat_short} ({mat_full}) is a metallic material valued in chemical processing for '
               'its mechanical strength, thermal conductivity, and ability to withstand high pressures '
               'and temperatures. Metals and alloys are used for pressure vessels, heat exchangers, '
               'piping, and structural components in demanding process environments. Their chemical '
               'resistance depends strongly on alloy composition: stainless steels resist many '
               'aqueous solutions through a passive oxide layer, while aluminium is lightweight but '
               'vulnerable to strong acids and bases. Key concerns for metals in chemical service '
               'include pitting, crevice corrosion, stress-corrosion cracking, and galvanic corrosion '
               'when dissimilar metals are coupled. Unlike plastics, metals offer excellent fire '
               'resistance and dimensional stability at elevated temperatures.'),
        'de': ('{mat_short} ({mat_full}) ist ein metallischer Werkstoff, der in der chemischen '
               'Verfahrenstechnik wegen seiner mechanischen Festigkeit, Wärmeleitfähigkeit und '
               'Druckbeständigkeit geschätzt wird. Metalle und Legierungen werden für Druckbehälter, '
               'Wärmetauscher, Rohrleitungen und tragende Bauteile in anspruchsvollen Prozessumgebungen '
               'eingesetzt. Ihre chemische Beständigkeit hängt stark von der Legierungszusammensetzung '
               'ab: Edelstähle widerstehen vielen wässrigen Lösungen durch eine passive Oxidschicht, '
               'während Aluminium leicht, aber anfällig gegenüber starken Säuren und Laugen ist. '
               'Wichtige Aspekte bei Metallen im Chemikalienkontakt sind Lochfraß, Spaltkorrosion, '
               'Spannungsrisskorrosion und galvanische Korrosion bei Kontakt ungleicher Metalle. '
               'Im Gegensatz zu Kunststoffen bieten Metalle ausgezeichnete Brandbeständigkeit und '
               'Maßhaltigkeit bei erhöhten Temperaturen.'),
        'es': ('{mat_short} ({mat_full}) es un material metálico valorado en el procesamiento químico '
               'por su resistencia mecánica, conductividad térmica y capacidad para soportar altas '
               'presiones y temperaturas. Los metales y aleaciones se utilizan para recipientes a '
               'presión, intercambiadores de calor, tuberías y componentes estructurales en entornos '
               'de proceso exigentes. Su resistencia química depende en gran medida de la composición '
               'de la aleación: los aceros inoxidables resisten muchas soluciones acuosas gracias a '
               'una capa de óxido pasiva, mientras que el aluminio es ligero pero vulnerable a ácidos '
               'y bases fuertes. Las preocupaciones clave para los metales en servicio químico incluyen '
               'picaduras, corrosión en hendiduras, corrosión bajo tensión y corrosión galvánica '
               'cuando se acoplan metales distintos. A diferencia de los plásticos, los metales '
               'ofrecen excelente resistencia al fuego y estabilidad dimensional a temperaturas elevadas.'),
    },
}


def _material_properties(lang, chem, mat, chem_name, mat_short, slug):
    """Supplementary paragraph about material family properties.
    Used when no resistance data exists for this pair."""
    family = rd.MATERIALS[mat][1]
    props = FAMILY_PROPERTIES.get(family)
    if not props:
        return ''
    tmpl = props.get(lang, props.get('en', ''))
    if not tmpl:
        return ''
    mat_full = MATERIAL_FULL.get(mat, mat_short)
    return tmpl.format(mat_short=mat_short, mat_full=mat_full)


# ---------------------------------------------------------------------------
# Section headers
# ---------------------------------------------------------------------------

SECTION_HEADERS = {
    'guidance_h': {
        'en': 'Resistance overview',
        'de': 'Beständigkeitsübersicht',
        'es': 'Resumen de resistencia',
    },
    'context_h': {
        'en': 'Application context',
        'de': 'Anwendungskontext',
        'es': 'Contexto de aplicación',
    },
    'recommendation_h': {
        'en': 'Practical recommendation',
        'de': 'Praxisempfehlung',
        'es': 'Recomendación práctica',
    },
    'dyk_h': {
        'en': 'Did you know?',
        'de': 'Wussten Sie?',
        'es': '¿Sabía que…?',
    },
    'material_h': {
        'en': 'About this material',
        'de': 'Über diesen Werkstoff',
        'es': 'Sobre este material',
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def editorial_html(lang, slug, page, chem, mat):
    """Return the editorial HTML section for a pair page, or '' if the language
    is not in the indexed set (EN, DE, ES)."""
    if lang not in INDEXED_LANGS:
        return ''

    chem_name = page['names'][lang]
    mat_short = material_name(mat, lang)

    import html as html_mod
    esc = lambda s: html_mod.escape(str(s), quote=True)

    p1 = _conc_guidance(lang, chem, mat, chem_name, mat_short, slug)
    p2 = _application_context(lang, chem, mat, chem_name, mat_short, slug)
    p3 = _practical_recommendation(lang, chem, mat, chem_name, mat_short, slug)
    p4 = _did_you_know(lang, chem, mat, chem_name, mat_short, slug)

    # When no concentration data exists, add a material properties paragraph
    p_mat = ''
    if not p1:
        p_mat = _material_properties(lang, chem, mat, chem_name, mat_short, slug)

    parts = []
    if p1:
        parts.append('<h2>%s</h2><p>%s</p>' % (esc(SECTION_HEADERS['guidance_h'][lang]), esc(p1)))
    if p_mat:
        parts.append('<h2>%s</h2><p>%s</p>' % (esc(SECTION_HEADERS['material_h'][lang]), esc(p_mat)))
    if p2:
        parts.append('<h2>%s</h2><p>%s</p>' % (esc(SECTION_HEADERS['context_h'][lang]), esc(p2)))
    if p3:
        parts.append('<h2>%s</h2><p>%s</p>' % (esc(SECTION_HEADERS['recommendation_h'][lang]), esc(p3)))
    if p4:
        parts.append('<h2>%s</h2><p>%s</p>' % (esc(SECTION_HEADERS['dyk_h'][lang]), esc(p4)))

    if not parts:
        return ''

    return '<section class="cr-card">' + ''.join(parts) + '</section>'
