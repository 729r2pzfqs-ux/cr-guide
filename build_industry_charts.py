#!/usr/bin/env python3
"""Build industry-specific chemical resistance chart pages for EN, DE and ES.

    python3 build_industry_charts.py            # write
    python3 build_industry_charts.py --check    # report only

Adds chart pages for application-specific groupings: food-safe, fuel-resistant,
acid-resistant, solvent-resistant, high-temperature, and water/wastewater
materials.  Pages follow the same template as the existing category charts.
After running, call build_chart_tables.py to inject pre-rendered table rows
and summary figures.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://chemicalresistance.org'
CONTENT_UPDATED = '2026-10-08'

# ============================================================
# Shared boilerplate
# ============================================================

GA_HEAD = '''<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("consent","default",{"analytics_storage":"denied","ad_storage":"denied","ad_user_data":"denied","ad_personalization":"denied","wait_for_update":500,"region":["BE","BG","CZ","DK","DE","EE","IE","GR","ES","FR","HR","IT","CY","LV","LT","LU","HU","MT","NL","AT","PL","PT","RO","SI","SK","FI","SE","GB","CH","IS","LI","NO"]});gtag("consent","default",{"analytics_storage":"granted","ad_storage":"granted","ad_user_data":"granted","ad_personalization":"granted"});</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5861928596436289" crossorigin="anonymous"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-LTK6VVHYDW"></script>
<script>gtag("js",new Date());gtag("config","G-LTK6VVHYDW");</script>
<script src="https://analytics.ahrefs.com/analytics.js" data-key="xrS32xSgQE4Xp1oL20j7uQ" async></script>
<style>ins.adsbygoogle[data-ad-status="unfilled"],.google-auto-placed:has(>ins.adsbygoogle[data-ad-status="unfilled"]),[data-blank-ad],:has(>#compat-table-zone) .google-auto-placed,:has(>#compat-table-zone) ins.adsbygoogle,:has(>#compat-table-zone) iframe[id^="aswift"]{display:none!important}</style>
<script>(function(){var S="data-blank-ad",k=new WeakMap(),t=null,c=0;function b(e){return !e.querySelector("iframe")&&!e.textContent.trim()}function s(){document.querySelectorAll("ins.adsbygoogle,.google-auto-placed").forEach(function(e){var ins=e.tagName==="INS";if(ins&&e.closest(".google-auto-placed"))return;var p=ins?e:(e.querySelector("ins.adsbygoogle")||e);if(!b(e)){k.set(e,0);e.removeAttribute(S);return}if(p.tagName==="INS"&&p.getAttribute("data-adsbygoogle-status")!=="done")return;if(!e.hasAttribute(S)&&e.getBoundingClientRect().height<=0)return;var n=(k.get(e)||0)+1;k.set(e,n);if(n>=2)e.setAttribute(S,"")})}function arm(){if(t)return;c=0;t=setInterval(function(){s();if(++c>=8){clearInterval(t);t=null}},1500)}arm();try{new MutationObserver(function(m){for(var j=0;j<m.length;j++)if(m[j].addedNodes.length){arm();return}}).observe(document.documentElement,{childList:true,subtree:true})}catch(e){}addEventListener("scroll",arm,{passive:true});addEventListener("load",arm)})()</script>'''

CF_BEACON = '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{"token": "cba547e85ee54e0f9cdc27e68405eead"}\'></script>'

STYLES = '''    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #f8fafc; }
        .rating-A{background:#15803d;color:#fff}
        .rating-B{background:#1d4ed8;color:#fff}
        .rating-C{background:#d97706;color:#111827}
        .rating-D{background:#b91c1c;color:#fff}
        .rating-NR{background:#e5e7eb;color:#374151}
        @media print { header, footer, .no-print { display: none !important; } body { background: white; } }
        .diff-row { background: #fffbeb; }
    </style>'''

CONC_MAP = {
    'en': {
        'wässrig': 'Aqueous', 'gesättigt': 'Saturated', 'verdünnt': 'Diluted',
        'konz.': 'Concentrated', 'konzentriert': 'Concentrated', 'rein': 'Pure',
        'techn. rein': 'Technical Grade', 'jede': 'Any', 'gering': 'Low',
        'flüssig': 'Liquid', 'gasförmig': 'Gaseous', 'geschmolzen': 'Molten',
        'trocken': 'Dry', 'feucht': 'Wet/Moist', 'fest': 'Solid',
        'Pulver': 'Powder', 'gemahlen': 'Ground', 'ölhaltig': 'Oil-containing',
        'sulfuriert': 'Sulfurized', 'kalt': 'Cold', 'heiß': 'Hot', 'heiss': 'Hot',
        'siedend': 'Boiling', 'handelsüblich': 'Commercial Grade',
    },
    'de': {},  # source data is already German
    'es': {
        'wässrig': 'Acuoso', 'gesättigt': 'Saturado', 'verdünnt': 'Diluido',
        'konz.': 'Concentrado', 'konzentriert': 'Concentrado', 'rein': 'Puro',
        'techn. rein': 'Grado técnico', 'jede': 'Cualquiera', 'gering': 'Bajo',
        'flüssig': 'Líquido', 'gasförmig': 'Gaseoso', 'geschmolzen': 'Fundido',
        'trocken': 'Seco', 'feucht': 'Húmedo', 'fest': 'Sólido',
        'Pulver': 'Polvo', 'gemahlen': 'Molido', 'ölhaltig': 'Oleoso',
        'sulfuriert': 'Sulfurado', 'kalt': 'Frío', 'heiß': 'Caliente', 'heiss': 'Caliente',
        'siedend': 'Hirviendo', 'handelsüblich': 'Grado comercial',
    },
}


def _shared_js(lang):
    """Return the shared JS block with language-appropriate translateConc and translateName."""
    conc_entries = CONC_MAP.get(lang, {})
    if conc_entries:
        pairs = ','.join("'%s':'%s'" % (k, v) for k, v in conc_entries.items())
        translate_conc = r'''
    function translateConc(conc) {
        if (!conc) return '&mdash;';
        var map = {%s};
        for (var de in map) {
            if (conc.toLowerCase().indexOf(de.toLowerCase()) !== -1) {
                conc = conc.replace(new RegExp(de, 'gi'), map[de]);
            }
        }
        return conc;
    }''' % pairs
    else:
        # German: source data is already in German, pass through
        translate_conc = r'''
    function translateConc(conc) {
        if (!conc) return '&mdash;';
        return conc;
    }'''

    if lang == 'en':
        translate_name = r'''
    function translateName(n) {
        return n;
    }
    function displayName(c) {
        return c.name_en || c.name;
    }'''
    elif lang == 'de':
        translate_name = r'''
    function translateName(n) {
        return n;
    }
    function displayName(c) {
        return c.name;
    }'''
    else:
        translate_name = r'''
    function translateName(n) {
        var lower = n.toLowerCase();
        if (typeof chemicalTranslations !== 'undefined' && chemicalTranslations[lower]) return chemicalTranslations[lower];
        return n;
    }
    function displayName(c) {
        return translateName(c.name);
    }'''

    return r'''
    const ratingMap = { '1':'A', '2':'B', '3':'C', '4':'D', '0':'NR' };
%(translate_conc)s
%(translate_name)s

    function getRating(c, matKey, temp) {
        return ratingMap[c.ratings[matKey]?.[temp]] || 'NR';
    }
''' % dict(translate_conc=translate_conc, translate_name=translate_name)

MAT_KEY_TO_DIR = {
    'AL': 'aluminium', 'ECTFE_ETFE': 'ectfe-etfe', 'EPDM': 'epdm', 'FEP': 'fep',
    'FPM': 'viton', 'HDPE': 'hdpe', 'LDPE': 'ldpe', 'NBR': 'nbr', 'PA': 'nylon-pa',
    'PC': 'polycarbonate', 'PETG': 'petg', 'PMP': 'pmp', 'POM': 'acetal-pom', 'PP': 'pp',
    'PS': 'polystyrene', 'PSU': 'polysulfone', 'PTFE': 'ptfe', 'PVC_HART': 'pvc-rigid',
    'PVC_WEICH': 'pvc-flexible', 'PVDF': 'pvdf', 'SAN': 'san', 'SI': 'silicone',
    'V2A': 'stainless-steel-304', 'V4A': 'ss316',
}

MAT_SHORT = {
    'en': {
        'AL': 'Al', 'ECTFE_ETFE': 'ECTFE', 'EPDM': 'EPDM', 'FEP': 'FEP', 'FPM': 'Viton',
        'HDPE': 'HDPE', 'LDPE': 'LDPE', 'NBR': 'NBR', 'PA': 'Nylon', 'PC': 'PC',
        'PETG': 'PETG', 'PMP': 'PMP', 'POM': 'POM', 'PP': 'PP', 'PS': 'PS', 'PSU': 'PSU',
        'PTFE': 'PTFE', 'PVC_HART': 'uPVC', 'PVC_WEICH': 'pPVC', 'PVDF': 'PVDF',
        'SAN': 'SAN', 'SI': 'Silicone', 'V2A': 'SS304', 'V4A': 'SS316',
    },
    'de': {
        'AL': 'Al', 'ECTFE_ETFE': 'ECTFE', 'EPDM': 'EPDM', 'FEP': 'FEP', 'FPM': 'Viton',
        'HDPE': 'HDPE', 'LDPE': 'LDPE', 'NBR': 'NBR', 'PA': 'Nylon', 'PC': 'PC',
        'PETG': 'PETG', 'PMP': 'PMP', 'POM': 'POM', 'PP': 'PP', 'PS': 'PS', 'PSU': 'PSU',
        'PTFE': 'PTFE', 'PVC_HART': 'Hart-PVC', 'PVC_WEICH': 'Weich-PVC', 'PVDF': 'PVDF',
        'SAN': 'SAN', 'SI': 'Silikon', 'V2A': 'V2A', 'V4A': 'V4A',
    },
    'es': {
        'AL': 'Al', 'ECTFE_ETFE': 'ECTFE', 'EPDM': 'EPDM', 'FEP': 'FEP', 'FPM': 'Viton',
        'HDPE': 'HDPE', 'LDPE': 'LDPE', 'NBR': 'NBR', 'PA': 'Nylon', 'PC': 'PC',
        'PETG': 'PETG', 'PMP': 'PMP', 'POM': 'POM', 'PP': 'PP', 'PS': 'PS', 'PSU': 'PSU',
        'PTFE': 'PTFE', 'PVC_HART': 'PVC-U', 'PVC_WEICH': 'PVC-P', 'PVDF': 'PVDF',
        'SAN': 'SAN', 'SI': 'Silicona', 'V2A': 'SS304', 'V4A': 'SS316',
    },
}

# ============================================================
# Language data
# ============================================================

I18N = {
    'home': {'en': 'Home', 'de': 'Start', 'es': 'Inicio'},
    'charts': {'en': 'Charts', 'de': 'Tabellen', 'es': 'Tablas'},
    'search': {'en': 'Search chemicals...', 'de': 'Chemikalie suchen...', 'es': 'Buscar químicos...'},
    'all_ratings': {'en': 'All ratings', 'de': 'Alle Bewertungen', 'es': 'Todas'},
    'any_a': {'en': 'Any material rated A', 'de': 'Mindestens ein A', 'es': 'Al menos un A'},
    'any_d': {'en': 'Any material rated D', 'de': 'Mindestens ein D', 'es': 'Al menos un D'},
    'diff': {'en': 'Ratings differ (most useful!)', 'de': 'Unterschiedliche Bewertungen', 'es': 'Diferencias'},
    'all_a': {'en': 'All materials rated A', 'de': 'Alle Materialien A', 'es': 'Todos con A'},
    'showing': {'en': 'Showing', 'de': 'Zeige', 'es': 'Mostrando'},
    'chemicals': {'en': 'chemicals', 'de': 'Chemikalien', 'es': 'químicos'},
    'highlight': {'en': 'Highlight differences', 'de': 'Unterschiede hervorheben', 'es': 'Resaltar diferencias'},
    'load_more': {'en': 'Load more', 'de': 'Mehr laden', 'es': 'Cargar más'},
    'faq_h': {'en': 'Frequently Asked Questions', 'de': 'Häufig gestellte Fragen',
              'es': 'Preguntas frecuentes'},
    'more_charts': {'en': 'More Comparison Charts', 'de': 'Weitere Vergleichstabellen',
                    'es': 'Más tablas de comparación'},
    'materials_label': {'en': 'materials', 'de': 'Materialien', 'es': 'materiales'},
    'a_excellent': {'en': 'A = Excellent', 'de': 'A = Ausgezeichnet', 'es': 'A = Excelente'},
    'b_good': {'en': 'B = Good', 'de': 'B = Gut', 'es': 'B = Bueno'},
    'c_limited': {'en': 'C = Limited', 'de': 'C = Begrenzt', 'es': 'C = Limitado'},
    'd_not_rec': {'en': 'D = Not Recommended', 'de': 'D = Nicht empfohlen', 'es': 'D = No recomendado'},
    'footer': {
        'en': '<footer class="bg-gray-900 text-gray-400 py-8 px-4">'
              '<div class="max-w-5xl mx-auto text-center text-sm">'
              '<p>&copy; 2026 ChemicalResistance.org &mdash; Free chemical compatibility tool</p>'
              '<p class="mt-2">Data: B&uuml;rkle, INEOS, industry standards</p></div></footer>',
        'de': '<footer class="bg-gray-900 text-gray-400 py-8 px-4">'
              '<div class="max-w-5xl mx-auto text-center text-sm">'
              '<p>&copy; 2026 ChemicalResistance.org &mdash; Kostenlose Werkstoff-Beständigkeitstabelle</p>'
              '<p class="mt-2">Datenquellen: B&uuml;rkle, INEOS, Industriestandards</p></div></footer>',
        'es': '<footer class="bg-gray-900 text-gray-400 py-8 px-4">'
              '<div class="max-w-5xl mx-auto text-center text-sm">'
              '<p>&copy; 2026 ChemicalResistance.org &mdash; Herramienta gratuita de compatibilidad qu&iacute;mica</p>'
              '<p class="mt-2">Fuentes: B&uuml;rkle, INEOS, est&aacute;ndares industriales</p></div></footer>',
    },
}

# ============================================================
# Industry-specific chart groupings
# ============================================================

INDUSTRY_CHARTS = [
    {
        'slug': {'en': 'food-safe-materials', 'de': 'lebensmittelkontakt', 'es': 'materiales-alimentarios'},
        'title': {
            'en': 'Food-Safe Materials: Chemical Resistance Chart',
            'de': 'Lebensmittelkontakt: Beständigkeitsvergleich',
            'es': 'Materiales para alimentos: resistencia química',
        },
        'h1': {
            'en': 'Food-Safe Material Comparison',
            'de': 'Werkstoffe für Lebensmittelkontakt',
            'es': 'Materiales aptos para alimentos',
        },
        'desc': {
            'en': 'Compare chemical resistance of HDPE, PP, PTFE, PVDF, Stainless Steel 316 and Silicone — common food-contact materials — across 900+ chemicals at 20 °C and 50 °C.',
            'de': 'Vergleichen Sie die chemische Beständigkeit von HDPE, PP, PTFE, PVDF, Edelstahl 316 und Silikon — gängige Lebensmittelkontaktmaterialien — bei über 900 Chemikalien.',
            'es': 'Compare la resistencia química de HDPE, PP, PTFE, PVDF, acero inoxidable 316 y silicona — materiales comunes en contacto con alimentos — en más de 900 sustancias.',
        },
        'intro': {
            'en': 'Materials used in food and beverage processing must resist cleaning agents, acids, and food-grade chemicals without contaminating the product. This chart compares the most common FDA/EU food-contact approved materials.',
            'de': 'Werkstoffe in der Lebensmittelverarbeitung müssen Reinigungsmitteln, Säuren und Lebensmittelchemikalien standhalten, ohne das Produkt zu kontaminieren.',
            'es': 'Los materiales en procesamiento de alimentos y bebidas deben resistir agentes de limpieza, ácidos y químicos alimentarios sin contaminar el producto.',
        },
        'materials': ['HDPE', 'PP', 'PTFE', 'PVDF', 'V4A', 'SI'],
        'color': 'green',
        'faq': {
            'en': [
                ('Which material is safest for food contact?',
                 'PTFE and Stainless Steel 316 are both widely approved for food contact. PTFE is rated A (excellent) for nearly all food-related chemicals. SS 316 offers excellent resistance to cleaning agents and most food acids. The choice often depends on temperature and mechanical requirements.'),
                ('Can HDPE be used with acidic foods?',
                 'Yes, HDPE has good resistance to most food acids including citric acid, acetic acid (vinegar), and lactic acid at room temperature. It is widely used for food storage containers and beverage bottles.'),
            ],
            'de': [
                ('Welches Material ist am sichersten für Lebensmittelkontakt?',
                 'PTFE und Edelstahl 316 sind beide für den Lebensmittelkontakt zugelassen. PTFE ist bei fast allen lebensmittelbezogenen Chemikalien mit A bewertet. Edelstahl 316 bietet hervorragende Beständigkeit gegen Reinigungsmittel und die meisten Lebensmittelsäuren.'),
                ('Kann HDPE mit sauren Lebensmitteln verwendet werden?',
                 'Ja, HDPE hat eine gute Beständigkeit gegen die meisten Lebensmittelsäuren wie Zitronensäure, Essigsäure und Milchsäure bei Raumtemperatur.'),
            ],
            'es': [
                ('¿Qué material es más seguro para contacto alimentario?',
                 'PTFE y acero inoxidable 316 están ampliamente aprobados para contacto con alimentos. PTFE tiene clasificación A (excelente) para casi todos los químicos alimentarios. El acero 316 ofrece excelente resistencia a agentes de limpieza y la mayoría de ácidos alimentarios.'),
                ('¿Se puede usar HDPE con alimentos ácidos?',
                 'Sí, HDPE tiene buena resistencia a la mayoría de ácidos alimentarios como ácido cítrico, ácido acético (vinagre) y ácido láctico a temperatura ambiente.'),
            ],
        },
    },
    {
        'slug': {'en': 'fuel-resistant-materials', 'de': 'kraftstoffbestaendige-materialien',
                 'es': 'materiales-resistentes-combustibles'},
        'title': {
            'en': 'Fuel-Resistant Materials: Chemical Resistance Chart',
            'de': 'Kraftstoffbeständige Materialien: Beständigkeitsvergleich',
            'es': 'Materiales resistentes a combustibles: resistencia química',
        },
        'h1': {
            'en': 'Fuel & Oil Resistant Materials',
            'de': 'Kraftstoff- & ölbeständige Werkstoffe',
            'es': 'Materiales resistentes a combustibles y aceites',
        },
        'desc': {
            'en': 'Compare chemical resistance of HDPE, PP, PTFE, FEP, PVDF, Viton and NBR to gasoline, diesel, motor oils, hydraulic fluids, and other petroleum products.',
            'de': 'Vergleichen Sie die Beständigkeit von HDPE, PP, PTFE, FEP, PVDF, Viton und NBR gegen Benzin, Diesel, Motoröle und andere Mineralölprodukte.',
            'es': 'Compare la resistencia de HDPE, PP, PTFE, FEP, PVDF, Viton y NBR a gasolina, diésel, aceites de motor y otros productos derivados del petróleo.',
        },
        'intro': {
            'en': 'Fuel systems, storage tanks, and oil-handling equipment need materials that resist hydrocarbons, additives, and biofuel blends. This chart compares materials commonly used in fuel infrastructure.',
            'de': 'Kraftstoffsysteme, Lagertanks und Ölhandhabungsanlagen benötigen Materialien, die Kohlenwasserstoffen, Additiven und Biokraftstoffmischungen standhalten.',
            'es': 'Los sistemas de combustible, tanques y equipos de manejo de aceite necesitan materiales resistentes a hidrocarburos, aditivos y mezclas de biocombustible.',
        },
        'materials': ['HDPE', 'PP', 'PTFE', 'FEP', 'PVDF', 'FPM', 'NBR'],
        'color': 'amber',
        'faq': {
            'en': [
                ('Which material is best for gasoline storage?',
                 'PTFE and Viton (FPM) offer excellent resistance to gasoline and its additives. HDPE is commonly used for fuel tanks but is rated B (good) rather than A. NBR is the standard for fuel hoses and seals. EPDM should be avoided — it swells in gasoline.'),
                ('Is PVDF resistant to diesel?',
                 'Yes, PVDF has excellent (A-rated) resistance to diesel fuel, biodiesel blends, and most mineral oils. It is widely used in fuel transfer piping and tank linings.'),
            ],
            'de': [
                ('Welches Material eignet sich am besten für die Benzinlagerung?',
                 'PTFE und Viton (FPM) bieten hervorragende Beständigkeit gegen Benzin und Additive. HDPE wird häufig für Kraftstofftanks verwendet. NBR ist Standard für Kraftstoffschläuche. EPDM sollte vermieden werden.'),
                ('Ist PVDF beständig gegen Diesel?',
                 'Ja, PVDF hat eine ausgezeichnete Beständigkeit (A-Bewertung) gegen Dieselkraftstoff, Biodieselgemische und die meisten Mineralöle.'),
            ],
            'es': [
                ('¿Qué material es mejor para almacenar gasolina?',
                 'PTFE y Viton (FPM) ofrecen excelente resistencia a la gasolina y sus aditivos. HDPE se usa comúnmente para tanques de combustible. NBR es estándar para mangueras. Evite EPDM — se hincha en gasolina.'),
                ('¿Es el PVDF resistente al diésel?',
                 'Sí, PVDF tiene excelente resistencia (clasificación A) al diésel, mezclas de biodiésel y la mayoría de aceites minerales.'),
            ],
        },
    },
    {
        'slug': {'en': 'acid-resistant-materials', 'de': 'saeure-bestaendige-materialien',
                 'es': 'materiales-resistentes-acidos'},
        'title': {
            'en': 'Acid-Resistant Materials: Chemical Resistance Chart',
            'de': 'Säurebeständige Materialien: Beständigkeitsvergleich',
            'es': 'Materiales resistentes a ácidos: resistencia química',
        },
        'h1': {
            'en': 'Acid-Resistant Material Comparison',
            'de': 'Säurebeständige Werkstoffe im Vergleich',
            'es': 'Comparación de materiales resistentes a ácidos',
        },
        'desc': {
            'en': 'Compare chemical resistance of PTFE, FEP, PVDF, ECTFE, HDPE, PP and Viton to hydrochloric acid, sulfuric acid, nitric acid, phosphoric acid and other strong acids.',
            'de': 'Vergleichen Sie die Beständigkeit von PTFE, FEP, PVDF, ECTFE, HDPE, PP und Viton gegen Salzsäure, Schwefelsäure, Salpetersäure und andere starke Säuren.',
            'es': 'Compare la resistencia de PTFE, FEP, PVDF, ECTFE, HDPE, PP y Viton al ácido clorhídrico, sulfúrico, nítrico y otros ácidos fuertes.',
        },
        'intro': {
            'en': 'Handling strong mineral acids requires materials that can withstand highly corrosive environments. This chart compares the top acid-resistant plastics, fluoropolymers, and elastomers at 20 °C and 50 °C.',
            'de': 'Der Umgang mit starken Mineralsäuren erfordert Materialien, die hochkorrosiven Umgebungen standhalten. Diese Tabelle vergleicht die besten säurebeständigen Werkstoffe.',
            'es': 'El manejo de ácidos minerales fuertes requiere materiales que soporten ambientes altamente corrosivos. Esta tabla compara los mejores materiales resistentes a ácidos.',
        },
        'materials': ['PTFE', 'FEP', 'PVDF', 'ECTFE_ETFE', 'HDPE', 'PP', 'FPM'],
        'color': 'red',
        'faq': {
            'en': [
                ('Which plastic is best for hydrochloric acid?',
                 'PTFE and FEP are rated A (excellent) for hydrochloric acid at all concentrations and temperatures. PVDF is rated A at room temperature. HDPE and PP handle dilute HCl well but degrade at higher concentrations or temperatures.'),
                ('Can Viton seals be used with sulfuric acid?',
                 'Yes, Viton (FPM/FKM) is rated A for dilute and concentrated sulfuric acid at room temperature. It is widely used for O-rings and seals in acid service. However, it should not be used with fuming sulfuric acid (oleum).'),
            ],
            'de': [
                ('Welcher Kunststoff ist am besten für Salzsäure?',
                 'PTFE und FEP sind bei allen Konzentrationen und Temperaturen mit A bewertet. PVDF ist bei Raumtemperatur mit A bewertet. HDPE und PP sind für verdünnte HCl geeignet.'),
                ('Können Viton-Dichtungen mit Schwefelsäure verwendet werden?',
                 'Ja, Viton (FPM/FKM) ist bei verdünnter und konzentrierter Schwefelsäure mit A bewertet. Es wird für O-Ringe im Säurebetrieb verwendet, nicht jedoch für rauchende Schwefelsäure.'),
            ],
            'es': [
                ('¿Qué plástico es mejor para el ácido clorhídrico?',
                 'PTFE y FEP tienen clasificación A (excelente) para ácido clorhídrico a todas las concentraciones. PVDF tiene A a temperatura ambiente. HDPE y PP manejan bien HCl diluido.'),
                ('¿Se pueden usar sellos de Viton con ácido sulfúrico?',
                 'Sí, Viton (FPM/FKM) tiene clasificación A para ácido sulfúrico diluido y concentrado a temperatura ambiente. No usar con ácido sulfúrico fumante (óleum).'),
            ],
        },
    },
    {
        'slug': {'en': 'solvent-resistant-materials', 'de': 'loesemittel-bestaendige-materialien',
                 'es': 'materiales-resistentes-disolventes'},
        'title': {
            'en': 'Solvent-Resistant Materials: Chemical Resistance Chart',
            'de': 'Lösemittelbeständige Materialien: Beständigkeitsvergleich',
            'es': 'Materiales resistentes a disolventes: resistencia química',
        },
        'h1': {
            'en': 'Solvent-Resistant Material Comparison',
            'de': 'Lösemittelbeständige Werkstoffe im Vergleich',
            'es': 'Comparación de materiales resistentes a disolventes',
        },
        'desc': {
            'en': 'Compare chemical resistance of PTFE, FEP, PVDF, HDPE, PP, PMP and Viton to acetone, MEK, toluene, xylene, THF, dichloromethane, and other organic solvents.',
            'de': 'Vergleichen Sie die Beständigkeit von PTFE, FEP, PVDF, HDPE, PP, PMP und Viton gegen Aceton, MEK, Toluol, Xylol, THF und andere organische Lösemittel.',
            'es': 'Compare la resistencia de PTFE, FEP, PVDF, HDPE, PP, PMP y Viton a acetona, MEK, tolueno, xileno, THF y otros disolventes orgánicos.',
        },
        'intro': {
            'en': 'Organic solvents attack most plastics and elastomers. Choosing the wrong material leads to swelling, cracking, or dissolution. This chart helps you select materials for solvent contact applications.',
            'de': 'Organische Lösemittel greifen die meisten Kunststoffe und Elastomere an. Die Auswahl des falschen Materials führt zu Quellung, Rissbildung oder Auflösung.',
            'es': 'Los disolventes orgánicos atacan la mayoría de plásticos y elastómeros. Elegir el material incorrecto causa hinchamiento, agrietamiento o disolución.',
        },
        'materials': ['PTFE', 'FEP', 'PVDF', 'HDPE', 'PP', 'PMP', 'FPM'],
        'color': 'purple',
        'faq': {
            'en': [
                ('Which material resists acetone?',
                 'PTFE and FEP are rated A for acetone. HDPE and PP are also rated A. PVDF is rated B (good). Viton is rated D (not recommended) — it swells rapidly in ketone solvents. For acetone applications, avoid Viton, NBR, and PVC.'),
                ('Can any plastic withstand toluene?',
                 'PTFE, FEP, and PVDF are all rated A for toluene. HDPE is rated C (limited) and PP is rated B. Most other plastics including PVC, polycarbonate, and polystyrene dissolve or crack in toluene.'),
            ],
            'de': [
                ('Welches Material ist beständig gegen Aceton?',
                 'PTFE und FEP sind mit A bewertet. HDPE und PP ebenfalls A. PVDF ist B (gut). Viton ist mit D bewertet — es quillt in Ketonlösemitteln schnell auf.'),
                ('Kann ein Kunststoff Toluol standhalten?',
                 'PTFE, FEP und PVDF sind alle mit A bewertet. HDPE ist C (begrenzt), PP ist B. Die meisten anderen Kunststoffe einschließlich PVC und Polycarbonat lösen sich auf.'),
            ],
            'es': [
                ('¿Qué material resiste la acetona?',
                 'PTFE y FEP tienen clasificación A. HDPE y PP también A. PVDF tiene B (bueno). Viton tiene D — se hincha rápidamente en disolventes cetónicos.'),
                ('¿Hay algún plástico que resista el tolueno?',
                 'PTFE, FEP y PVDF tienen clasificación A. HDPE tiene C (limitado), PP tiene B. La mayoría de plásticos como PVC y policarbonato se disuelven.'),
            ],
        },
    },
    {
        'slug': {'en': 'high-temperature-materials', 'de': 'hochtemperatur-materialien',
                 'es': 'materiales-alta-temperatura'},
        'title': {
            'en': 'High-Temperature Chemical Resistance Chart',
            'de': 'Hochtemperatur-Beständigkeitsvergleich',
            'es': 'Resistencia química a alta temperatura',
        },
        'h1': {
            'en': 'High-Temperature Material Comparison',
            'de': 'Hochtemperatur-Werkstoffe im Vergleich',
            'es': 'Materiales para alta temperatura',
        },
        'desc': {
            'en': 'Compare chemical resistance at 50 °C+ for PTFE, FEP, PVDF, ECTFE, Viton, SS 316 and EPDM. Find which materials maintain their ratings at elevated temperatures.',
            'de': 'Vergleichen Sie die chemische Beständigkeit bei 50 °C+ für PTFE, FEP, PVDF, ECTFE, Viton, V4A und EPDM. Welche Werkstoffe behalten ihre Bewertung bei erhöhter Temperatur?',
            'es': 'Compare la resistencia química a 50 °C+ de PTFE, FEP, PVDF, ECTFE, Viton, acero 316 y EPDM. ¿Qué materiales mantienen sus clasificaciones a temperaturas elevadas?',
        },
        'intro': {
            'en': 'Many materials degrade when temperatures rise above ambient. This chart focuses on materials that maintain chemical resistance at 50 °C and above — critical for steam cleaning, hot process streams, and heat exchangers.',
            'de': 'Viele Materialien verlieren bei steigender Temperatur ihre Beständigkeit. Diese Tabelle zeigt Materialien, die auch bei 50 °C und darüber beständig bleiben.',
            'es': 'Muchos materiales se degradan cuando la temperatura sube. Esta tabla muestra materiales que mantienen su resistencia a 50 °C y más — crítico para limpieza con vapor y procesos calientes.',
        },
        'materials': ['PTFE', 'FEP', 'PVDF', 'ECTFE_ETFE', 'FPM', 'V4A', 'EPDM'],
        'color': 'orange',
        'faq': {
            'en': [
                ('Which material is best at high temperatures?',
                 'PTFE maintains excellent chemical resistance up to 260 °C. Stainless Steel 316 handles even higher temperatures. Among plastics, PTFE and FEP retain their A-ratings at 50 °C for most chemicals. PVDF starts to lose some ratings above 50 °C.'),
                ('Can Viton seals handle high-temperature chemicals?',
                 'Yes, Viton (FPM/FKM) is rated for continuous use up to 200 °C and maintains good chemical resistance at 50 °C for most chemicals. It is the standard elastomer for high-temperature sealing applications.'),
            ],
            'de': [
                ('Welches Material ist bei hohen Temperaturen am besten?',
                 'PTFE behält seine Beständigkeit bis 260 °C. Edelstahl 316 verträgt noch höhere Temperaturen. Bei Kunststoffen behalten PTFE und FEP ihre A-Bewertungen bei 50 °C für die meisten Chemikalien.'),
                ('Können Viton-Dichtungen Hochtemperaturchemikalien standhalten?',
                 'Ja, Viton (FPM/FKM) ist für Dauergebrauch bis 200 °C ausgelegt und behält bei 50 °C gute chemische Beständigkeit.'),
            ],
            'es': [
                ('¿Qué material es mejor a altas temperaturas?',
                 'PTFE mantiene excelente resistencia hasta 260 °C. Acero 316 soporta temperaturas aún más altas. PTFE y FEP mantienen sus clasificaciones A a 50 °C para la mayoría de químicos.'),
                ('¿Los sellos de Viton resisten químicos a alta temperatura?',
                 'Sí, Viton (FPM/FKM) es apto para uso continuo hasta 200 °C y mantiene buena resistencia química a 50 °C para la mayoría de químicos.'),
            ],
        },
    },
    {
        'slug': {'en': 'water-wastewater-materials', 'de': 'wasser-abwasser-materialien',
                 'es': 'materiales-agua-residual'},
        'title': {
            'en': 'Water & Wastewater Treatment Materials: Chemical Resistance Chart',
            'de': 'Wasser- und Abwassermaterialien: Beständigkeitsvergleich',
            'es': 'Materiales para agua y aguas residuales: resistencia química',
        },
        'h1': {
            'en': 'Water & Wastewater Treatment Materials',
            'de': 'Werkstoffe für Wasser- und Abwasseraufbereitung',
            'es': 'Materiales para tratamiento de agua',
        },
        'desc': {
            'en': 'Compare chemical resistance of PVC, HDPE, PP, PVDF, SS 316, EPDM and PTFE to chlorine, sodium hypochlorite, ozone, alum and other water treatment chemicals.',
            'de': 'Vergleichen Sie die Beständigkeit von PVC, HDPE, PP, PVDF, V4A, EPDM und PTFE gegen Chlor, Natriumhypochlorit, Ozon und andere Wasseraufbereitungschemikalien.',
            'es': 'Compare la resistencia de PVC, HDPE, PP, PVDF, acero 316, EPDM y PTFE al cloro, hipoclorito de sodio, ozono y otros químicos de tratamiento de agua.',
        },
        'intro': {
            'en': 'Water and wastewater treatment uses oxidising disinfectants, pH-adjustment chemicals, and coagulants that attack many materials. This chart compares materials commonly used in treatment plant piping, tanks, and seals.',
            'de': 'Wasseraufbereitung verwendet oxidierende Desinfektionsmittel, pH-Regulierungschemikalien und Flockungsmittel, die viele Materialien angreifen.',
            'es': 'El tratamiento de agua usa desinfectantes oxidantes, químicos de ajuste de pH y coagulantes que atacan muchos materiales.',
        },
        'materials': ['PVC_HART', 'HDPE', 'PP', 'PVDF', 'V4A', 'EPDM', 'PTFE'],
        'color': 'cyan',
        'faq': {
            'en': [
                ('Which material is best for chlorinated water?',
                 'PVDF and PTFE are rated A for chlorine and sodium hypochlorite at all concentrations. EPDM is the standard elastomer for chlorinated water service. PVC handles chlorinated water well at room temperature but degrades at higher concentrations and temperatures.'),
                ('Can HDPE pipes be used for wastewater?',
                 'Yes, HDPE is widely used for wastewater conveyance. It has excellent resistance to most wastewater chemicals at room temperature and is available in large diameters for gravity flow. It should be checked against specific chemicals if the wastewater contains solvents or strong oxidisers.'),
            ],
            'de': [
                ('Welches Material ist am besten für chloriertes Wasser?',
                 'PVDF und PTFE sind bei allen Konzentrationen mit A bewertet. EPDM ist das Standard-Elastomer für Chlorwasser. PVC ist bei Raumtemperatur gut geeignet.'),
                ('Können HDPE-Rohre für Abwasser verwendet werden?',
                 'Ja, HDPE wird für Abwasserleitungen weit verbreitet eingesetzt. Es hat ausgezeichnete Beständigkeit gegen die meisten Abwasserchemikalien bei Raumtemperatur.'),
            ],
            'es': [
                ('¿Qué material es mejor para agua clorada?',
                 'PVDF y PTFE tienen clasificación A para cloro e hipoclorito de sodio a todas las concentraciones. EPDM es el elastómero estándar para agua clorada. PVC funciona bien a temperatura ambiente.'),
                ('¿Se pueden usar tuberías de HDPE para aguas residuales?',
                 'Sí, HDPE se usa ampliamente para conducción de aguas residuales. Tiene excelente resistencia a la mayoría de químicos de aguas residuales a temperatura ambiente.'),
            ],
        },
    },
]


# ============================================================
# Header/footer per language
# ============================================================

def _header(lang, active='charts'):
    if lang == 'en':
        nav_items = [
            ('/', 'Lookup', False),
            ('/materials/', 'Materials', False),
            ('/chemicals/', 'Chemicals', False),
            ('/compare/', 'Compare', False),
            ('/charts/', 'Charts', True),
            ('/storage-compatibility/', 'Storage', False),
            ('/sds-decoder/', 'SDS Decoder', False),
            ('/viscosity/', 'Viscosity', False),
            ('/about/', 'About', False),
        ]
        home_href, home_label = '/', 'ChemicalResistance.org'
        sub = 'Chemical compatibility database'
    elif lang == 'de':
        nav_items = [
            ('/materials/de/', 'Materialien', False),
            ('/chemicals/de/', 'Chemikalien', False),
            ('/de/compare/', 'Vergleich', False),
            ('/de/charts/', 'Tabellen', True),
            ('/de/storage-compatibility/', 'Lagerung', False),
            ('/de/sds-decoder/', 'SDB', False),
            ('/de/viscosity/', 'Viskosität', False),
            ('/de/about/', 'Über uns', False),
        ]
        home_href, home_label = '/de/', 'ChemicalResistance.org'
        sub = 'Chemische Beständigkeitsdatenbank'
    else:
        nav_items = [
            ('/materials/es/', 'Materiales', False),
            ('/chemicals/es/', 'Químicos', False),
            ('/es/compare/', 'Comparar', False),
            ('/es/charts/', 'Tablas', True),
            ('/es/storage-compatibility/', 'Almacenamiento', False),
            ('/es/sds-decoder/', 'FDS', False),
            ('/es/viscosity/', 'Viscosidad', False),
            ('/es/about/', 'Acerca de', False),
        ]
        home_href, home_label = '/es/', 'ChemicalResistance.org'
        sub = 'Base de datos de compatibilidad química'

    desktop = '\n                    '.join(
        '<a href="%s" class="%s">%s</a>' % (
            h, 'text-emerald-600 font-medium' if act else 'text-gray-600 hover:text-gray-900 hover:underline', l)
        for h, l, act in nav_items)

    return '''    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="%(home)s" class="flex items-center gap-2">
                <img src="/logos/logo-icon-128x128.png" alt="ChemicalResistance" class="w-10 h-10 rounded-xl">
                <div>
                    <div class="font-bold text-gray-900">%(label)s</div>
                    <div class="text-xs text-gray-500 hidden sm:block">%(sub)s</div>
                </div>
            </a>
            <div class="flex items-center gap-3 text-sm">
                <nav class="hidden md:flex items-center gap-4">
                    %(desktop)s
                </nav>
                <button id="mobileMenuBtn" class="md:hidden p-2 rounded-lg hover:bg-gray-100" aria-label="Menu">
                    <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                </button>
            </div>
        </div>
    </header>
    <script>
        document.getElementById('mobileMenuBtn').addEventListener('click', function() {
            document.getElementById('mobileMenu').classList.toggle('hidden');
        });
    </script>''' % dict(home=home_href, label=home_label, sub=sub, desktop=desktop)


# ============================================================
# Page builder
# ============================================================

def _chart_base(lang):
    return '/charts/' if lang == 'en' else '/%s/charts/' % lang


def _mat_base(lang):
    return '/materials/' if lang == 'en' else '/materials/%s/' % lang


def build_chart_page(chart, lang, all_charts):
    slug = chart['slug'][lang]
    mats = chart['materials']
    shorts = MAT_SHORT[lang]
    mat_js = json.dumps([{'key': k, 'short': shorts[k], 'dir': MAT_KEY_TO_DIR[k]} for k in mats])

    chart_base = _chart_base(lang)
    mat_base = _mat_base(lang)
    home = '/' if lang == 'en' else '/%s/' % lang

    # Table header columns
    th_cols = ''
    for k in mats:
        th_cols += ('<th class="py-3 px-2 font-semibold text-gray-600 text-center whitespace-nowrap">'
                    '<a href="%s%s/" class="hover:text-emerald-600 hover:underline">%s</a></th>'
                    % (mat_base, MAT_KEY_TO_DIR[k], shorts[k]))

    # FAQ schema
    faq_list = chart['faq'][lang]
    faq_entities = []
    for q, a in faq_list:
        faq_entities.append(json.dumps({
            '@type': 'Question', 'name': q,
            'acceptedAnswer': {'@type': 'Answer', 'text': a}
        }, ensure_ascii=False))
    faq_schema = json.dumps({
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'mainEntity': [json.loads(e) for e in faq_entities]
    }, ensure_ascii=False, separators=(',', ':'))

    # FAQ HTML
    faq_html = ''
    for q, a in faq_list:
        faq_html += ('            <details class="border border-gray-200 rounded-xl overflow-hidden">\n'
                     '                <summary class="px-5 py-4 cursor-pointer font-medium text-gray-900 hover:bg-gray-50">%s</summary>\n'
                     '                <div class="px-5 py-4 border-t border-gray-100 text-gray-600 text-sm">%s</div>\n'
                     '            </details>\n' % (q, a))

    # Cross-links
    cross_links = ''
    for c in all_charts:
        if c['slug'][lang] == slug:
            continue
        cross_links += ('                <a href="%s%s/" class="p-3 rounded-xl border border-gray-200 '
                        'hover:border-emerald-300 hover:bg-emerald-50 transition-colors text-center">\n'
                        '                    <div class="font-bold text-gray-900 text-sm">%s</div>\n'
                        '                    <div class="text-xs text-gray-500">%d %s</div>\n'
                        '                </a>\n' % (
            chart_base, c['slug'][lang], c['h1'][lang],
            len(c['materials']), I18N['materials_label'][lang]))

    # Hreflang
    hreflang = ''
    for l in ['en', 'de', 'es']:
        href = SITE + _chart_base(l) + chart['slug'][l] + '/'
        hreflang += '    <link rel="alternate" hreflang="%s" href="%s">\n' % (l, href)
    hreflang += '    <link rel="alternate" hreflang="x-default" href="%s%s%s/">\n' % (
        SITE, _chart_base('en'), chart['slug']['en'])

    canonical = '%s%s%s/' % (SITE, chart_base, slug)

    header = _header(lang)

    color = chart['color']
    i = I18N

    html = '''<!DOCTYPE html>
<html lang="%(lang)s">
<head>
%(ga)s
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%(title)s</title>
    <meta name="description" content="%(desc)s">
    <link rel="canonical" href="%(canonical)s">
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <meta property="og:title" content="%(title)s">
    <meta property="og:description" content="%(desc)s">
    <meta property="og:type" content="article">
    <meta property="og:image" content="%(site)s/og-image.png">
    <link rel="stylesheet" href="/css/tailwind.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
%(hreflang)s%(styles)s
<script type="application/ld+json">
%(faq_schema)s
</script>
</head>
<body class="text-gray-700 min-h-screen">
%(header)s

    <section class="bg-gradient-to-b from-%(color)s-50 to-white px-4 py-8 md:py-12">
        <div class="max-w-5xl mx-auto">
            <div class="flex items-center gap-2 text-sm text-%(color)s-600 mb-3">
                <a href="%(home)s" class="hover:underline">%(home_label)s</a>
                <span>&rsaquo;</span>
                <a href="%(chart_base)s" class="hover:underline">%(charts_label)s</a>
                <span>&rsaquo;</span>
                <span class="text-gray-600">%(h1)s</span>
            </div>
            <h1 class="text-3xl font-bold text-gray-900 mb-3">%(h1)s</h1>
            <p class="text-lg text-gray-600 mb-4">%(intro)s</p>
            <div class="flex flex-wrap gap-4 text-sm text-gray-600">
                <span class="flex items-center gap-1"><span class="w-4 h-4 rounded rating-A"></span> %(a)s</span>
                <span class="flex items-center gap-1"><span class="w-4 h-4 rounded rating-B"></span> %(b)s</span>
                <span class="flex items-center gap-1"><span class="w-4 h-4 rounded rating-C"></span> %(c)s</span>
                <span class="flex items-center gap-1"><span class="w-4 h-4 rounded rating-D"></span> %(d)s</span>
            </div>
        </div>
    </section>

    <section class="px-4 py-6 no-print">
        <div class="max-w-7xl mx-auto">
            <div class="bg-white rounded-xl border border-gray-200 p-4">
                <div class="flex flex-col md:flex-row gap-4">
                    <div class="flex-1">
                        <input type="text" id="searchInput" placeholder="%(search)s" class="w-full px-4 py-2 border border-gray-200 rounded-lg focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 outline-none">
                    </div>
                    <select id="ratingFilter" class="px-4 py-2 border border-gray-200 rounded-lg">
                        <option value="all">%(all_ratings)s</option>
                        <option value="any-A">%(any_a)s</option>
                        <option value="any-D">%(any_d)s</option>
                        <option value="diff">%(diff)s</option>
                        <option value="all-A">%(all_a)s</option>
                    </select>
                    <select id="tempFilter" class="px-4 py-2 border border-gray-200 rounded-lg">
                        <option value="c20">20°C</option>
                        <option value="c50">50°C</option>
                    </select>
                </div>
            </div>
        </div>
    </section>

    <section class="px-4 py-4">
        <div class="max-w-7xl mx-auto">
            <div class="mb-4 flex items-center justify-between text-sm text-gray-500">
                <span>%(showing)s <span id="resultCount" class="font-semibold text-gray-700">0</span> %(chemicals)s</span>
                <label class="flex items-center gap-2 cursor-pointer no-print">
                    <input type="checkbox" id="highlightDiffs" checked class="rounded">
                    <span>%(highlight)s</span>
                </label>
            </div>
            <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full" style="min-width:600px">
                        <thead class="sticky top-0 z-10">
                            <tr class="bg-gray-50 text-left text-sm">
                                <th class="py-3 px-4 font-semibold text-gray-600 sticky left-0 z-20 bg-gray-50">%(chem_label)s</th>
                                <th class="py-3 px-3 font-semibold text-gray-600 text-sm">%(conc_label)s</th>
                                %(th_cols)s
                            </tr>
                        </thead>
                        <tbody id="chartTable" class="divide-y divide-gray-100"></tbody>
                    </table>
                </div>
            </div>
            <div id="loadMore" class="mt-4 text-center hidden">
                <button onclick="loadMore()" class="px-6 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700">%(load_more)s</button>
            </div>
        </div>
    </section>

    <section class="px-4 py-8 bg-white border-t border-gray-200">
        <div class="max-w-4xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">%(faq_h)s</h2>
            <div class="space-y-3">
%(faq_html)s            </div>
        </div>
    </section>

    <section class="px-4 py-8">
        <div class="max-w-5xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">%(more_charts)s</h2>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
%(cross_links)s            </div>
        </div>
    </section>

%(footer)s

    %(translations_script)s
    <script>
    var MATS = %(mat_js)s;
    %(shared_js)s
    var chemicals = [];
    var filtered = [];
    var displayCount = 80;

    function hasDiff(c, temp) {
        var ratings = new Set();
        for (var i = 0; i < MATS.length; i++) {
            var r = c.ratings[MATS[i].key]?.[temp];
            if (r && r !== '0') ratings.add(r);
        }
        return ratings.size > 1;
    }

    fetch('/data/chemicals_burkle_full.json')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            data = data.filter(function (c) { return !c.alias_of; });
            chemicals = data.filter(function(c) {
                var count = 0;
                for (var i = 0; i < MATS.length; i++) {
                    if (c.ratings[MATS[i].key]?.c20 && c.ratings[MATS[i].key].c20 !== '0') count++;
                    if (count >= 2) return true;
                }
                return false;
            });
            applyFilters();
        });

    function applyFilters() {
        var query = document.getElementById('searchInput').value.toLowerCase();
        var filter = document.getElementById('ratingFilter').value;
        var temp = document.getElementById('tempFilter').value;

        filtered = chemicals.filter(function(c) {
            if (query) {
                var name = displayName(c).toLowerCase();
                if (!name.includes(query) && !c.name.toLowerCase().includes(query) && !(c.cas && c.cas.includes(query))) return false;
            }
            if (filter === 'diff') return hasDiff(c, temp);
            if (filter === 'any-A') return MATS.some(function(m) { return getRating(c, m.key, temp) === 'A'; });
            if (filter === 'any-D') return MATS.some(function(m) { return getRating(c, m.key, temp) === 'D'; });
            if (filter === 'all-A') return MATS.every(function(m) {
                var r = getRating(c, m.key, temp);
                return r === 'A' || r === 'NR';
            });
            return true;
        });

        filtered.sort(function(a, b) {
            var aDiff = hasDiff(a, temp) ? 0 : 1;
            var bDiff = hasDiff(b, temp) ? 0 : 1;
            if (aDiff !== bDiff) return aDiff - bDiff;
            return displayName(a).localeCompare(displayName(b), '%(lang)s');
        });

        displayCount = 80;
        renderTable();
    }

    function renderTable() {
        var tbody = document.getElementById('chartTable');
        var temp = document.getElementById('tempFilter').value;
        var highlight = document.getElementById('highlightDiffs').checked;
        var toShow = filtered.slice(0, displayCount);

        document.getElementById('resultCount').textContent = filtered.length;
        document.getElementById('loadMore').classList.toggle('hidden', displayCount >= filtered.length);

        tbody.innerHTML = toShow.map(function(c) {
            var name = displayName(c);
            var conc = translateConc(c.concentration);
            var isDiff = hasDiff(c, temp);
            var rowClass = (highlight && isDiff) ? 'diff-row hover:bg-amber-100' : 'hover:bg-gray-50';

            var cells = '';
            for (var i = 0; i < MATS.length; i++) {
                var r = getRating(c, MATS[i].key, temp);
                cells += '<td class="py-2 px-2 text-center"><span class="rating-' + r + ' px-1.5 py-0.5 rounded text-xs font-bold">' + r + '</span></td>';
            }

            return '<tr class="' + rowClass + '">'
                + '<td class="py-2 px-4 text-sm sticky left-0 z-10 bg-white"><div class="font-medium text-gray-900">' + name + '</div>'
                + (name !== c.name ? '<div class="text-xs text-gray-400">' + c.name + '</div>' : '')
                + '</td>'
                + '<td class="py-2 px-3 text-xs text-gray-500">' + conc + '</td>'
                + cells + '</tr>';
        }).join('');
    }

    function loadMore() { displayCount += 80; renderTable(); }

    document.getElementById('searchInput').addEventListener('input', applyFilters);
    document.getElementById('ratingFilter').addEventListener('change', applyFilters);
    document.getElementById('tempFilter').addEventListener('change', applyFilters);
    document.getElementById('highlightDiffs').addEventListener('change', renderTable);
    </script>
%(cf_beacon)s
</body>
</html>'''

    chem_labels = {'en': 'Chemical', 'de': 'Chemikalie', 'es': 'Producto químico'}
    conc_labels = {'en': 'Conc.', 'de': 'Konz.', 'es': 'Conc.'}

    return html % dict(
        lang=lang, ga=GA_HEAD, title=chart['title'][lang], desc=chart['desc'][lang],
        canonical=canonical, site=SITE, hreflang=hreflang, styles=STYLES,
        faq_schema=faq_schema, header=header, color=color,
        home=home, home_label=i['home'][lang], chart_base=chart_base,
        charts_label=i['charts'][lang], h1=chart['h1'][lang], intro=chart['intro'][lang],
        a=i['a_excellent'][lang], b=i['b_good'][lang], c=i['c_limited'][lang], d=i['d_not_rec'][lang],
        search=i['search'][lang], all_ratings=i['all_ratings'][lang],
        any_a=i['any_a'][lang], any_d=i['any_d'][lang], diff=i['diff'][lang], all_a=i['all_a'][lang],
        showing=i['showing'][lang], chemicals=i['chemicals'][lang],
        highlight=i['highlight'][lang], chem_label=chem_labels[lang], conc_label=conc_labels[lang],
        th_cols=th_cols, load_more=i['load_more'][lang], faq_h=i['faq_h'][lang],
        faq_html=faq_html, more_charts=i['more_charts'][lang],
        cross_links=cross_links, footer=i['footer'][lang],
        translations_script=('<script src="/js/chemical_translations_%s.js"></script>' % lang
                              if lang != 'de' else ''),
        mat_js=mat_js, shared_js=_shared_js(lang), cf_beacon=CF_BEACON,
    )


def main():
    check = '--check' in sys.argv
    changed = 0
    for lang in ['en', 'de', 'es']:
        for chart in INDUSTRY_CHARTS:
            slug = chart['slug'][lang]
            if lang == 'en':
                outdir = os.path.join(ROOT, 'charts', slug)
            else:
                outdir = os.path.join(ROOT, lang, 'charts', slug)
            os.makedirs(outdir, exist_ok=True)
            path = os.path.join(outdir, 'index.html')
            html = build_chart_page(chart, lang, INDUSTRY_CHARTS)
            old = ''
            if os.path.exists(path):
                with open(path, encoding='utf-8') as f:
                    old = f.read()
            if html != old:
                changed += 1
                if not check:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print('  Created: %s' % os.path.relpath(path, ROOT))
    print('%d industry chart pages in 3 languages; %s %d files' % (
        len(INDUSTRY_CHARTS), 'would change' if check else 'wrote', changed))


if __name__ == '__main__':
    main()
