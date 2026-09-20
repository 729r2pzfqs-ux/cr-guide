#!/usr/bin/env python3
"""
Canonical analytics head block for chemicalresistance.org.

Required order (GDPR / Consent Mode v2)
---------------------------------------
    1. consent defaults   - pushed before anything can read them: a denied
                            baseline scoped to CONSENT_REGIONS, then a granted
                            fallback for every other region
    2. AdSense loader     - adsbygoogle.js delivers the CMP at runtime, so it
                            has to be requested early to spend as little of the
                            wait_for_update window as possible
    3. gtag loader        - followed by gtag('js')/gtag('config')
    4. Ahrefs             - unrelated to consent, goes last

The consent defaults live in their own <script> ahead of the AdSense tag, and
the gtag config script after the loader does NOT re-declare
window.dataLayer/gtag - those already exist from block 1.

Every generator in this repo imports these constants so the order can only be
changed in one place. `fix_consent_order.py` rewrites the already-published
HTML to match.
"""

GA_ID = "G-LTK6VVHYDW"
ADS_CLIENT = "ca-pub-5861928596436289"
AHREFS_KEY = "xrS32xSgQE4Xp1oL20j7uQ"

# --- individual tags, compact form ---------------------------------------
#: EEA + UK + Switzerland + the remaining EFTA/EEA states. These are the
#: regions where consent is required before storage, so they get the denied
#: baseline; everywhere else falls through to the granted default below.
#: ISO 3166-1 alpha-2 codes - that is what Google matches 'region' against.
#: Greece is GR, not the EU/Eurostat abbreviation EL, which matches nothing.
CONSENT_REGIONS = [
    "BE", "BG", "CZ", "DK", "DE", "EE", "IE", "GR", "ES", "FR", "HR", "IT",
    "CY", "LV", "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI",
    "SK", "FI", "SE", "GB", "CH", "IS", "LI", "NO",
]
_REGION_JSON = "[" + ",".join(f'"{c}"' for c in CONSENT_REGIONS) + "]"

CONSENT = (
    '<script>window.dataLayer=window.dataLayer||[];'
    'function gtag(){dataLayer.push(arguments);}'
    # 1. denied baseline, scoped to the regions that require consent
    'gtag("consent","default",{'
    '"analytics_storage":"denied",'
    '"ad_storage":"denied",'
    '"ad_user_data":"denied",'
    '"ad_personalization":"denied",'
    '"wait_for_update":500,'
    f'"region":{_REGION_JSON}}});'
    # 2. granted fallback for every other region. A region-scoped default
    #    wins over an unscoped one, so this does not loosen the block above.
    'gtag("consent","default",{'
    '"analytics_storage":"granted",'
    '"ad_storage":"granted",'
    '"ad_user_data":"granted",'
    '"ad_personalization":"granted"});</script>'
)
ADS = (
    '<script async src="https://pagead2.googlesyndication.com/pagead/js/'
    f'adsbygoogle.js?client={ADS_CLIENT}" crossorigin="anonymous"></script>'
)
GTAG_LOADER = f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>'
GTAG_CONFIG = f'<script>gtag("js",new Date());gtag("config","{GA_ID}");</script>'
AHREFS = (
    f'<script src="https://analytics.ahrefs.com/analytics.js" data-key="{AHREFS_KEY}" async></script>'
)

# --- blank auto-ad collapse ----------------------------------------------
# Google Auto Ads reserves a slot's height before it knows whether an ad will
# render. When nothing renders it is supposed to set data-ad-status="unfilled"
# and collapse the slot itself, but observed live on this site it often leaves
# data-ad-status unset: the <ins> reaches data-adsbygoogle-status="done" with
# an empty aswift host inside and keeps its reserved height. On mobile that is
# a blank band of 375px per slot.
#
# Suppressing by DOM position does not work - chasing auto ads out of one
# container just moves it to the next one up - so this collapses by STATE
# instead: a slot Google has finished with that rendered nothing.
#
# The CSS only handles the case Google labels for us. It deliberately does NOT
# hide slots by class alone: a blanket rule on .google-auto-placed would remove
# every auto ad on the site, filled ones included.
#
# The second rule protects the box that holds a compatibility table. The
# homepage scopes this to #results, but material and pair pages have no such
# wrapper: their ratings legend is a SIBLING of #compat-table-zone, so an ad
# placed between the table and the legend sat outside the only rule those pages
# carried. Measured on a live pair page that was a 662px band, exactly the shape
# reported. :has(> #compat-table-zone) selects whatever element holds the table
# on any page type, without needing a new id on 69k files.
AD_COLLAPSE_STYLE = (
    '<style>ins.adsbygoogle[data-ad-status="unfilled"],'
    '.google-auto-placed:has(>ins.adsbygoogle[data-ad-status="unfilled"]),'
    '[data-blank-ad],'
    ':has(>#compat-table-zone) .google-auto-placed,'
    ':has(>#compat-table-zone) ins.adsbygoogle,'
    ':has(>#compat-table-zone) iframe[id^="aswift"]'
    '{display:none!important}</style>'
)

# The sweep handles the unlabelled case. It runs only AFTER a slot reports
# "done", and requires the slot to still be empty on two consecutive passes, so
# it can never hide a slot that is mid-render - hiding one early would zero its
# width and cost the impression. A slot that later gains content is un-hidden.
#
# It must keep working for the whole page lifetime, not just a window after
# load: auto ads inserts most of its slots lazily as the reader scrolls, so a
# sweep that stopped after a fixed number of passes would miss exactly the
# slots a mobile reader scrolls into. A MutationObserver re-arms the interval
# whenever nodes are added, and scrolling re-arms it too; the interval itself
# still backs off after a few idle passes so nothing polls forever.
AD_COLLAPSE_SCRIPT = (
    '<script>(function(){var S="data-blank-ad",k=new WeakMap(),t=null,c=0;'
    'function b(e){return !e.querySelector("iframe")&&!e.textContent.trim()}'
    'function s(){document.querySelectorAll("ins.adsbygoogle,.google-auto-placed")'
    '.forEach(function(e){'
    'var ins=e.tagName==="INS";'
    'if(ins&&e.closest(".google-auto-placed"))return;'
    'var p=ins?e:(e.querySelector("ins.adsbygoogle")||e);'
    'if(!b(e)){k.set(e,0);e.removeAttribute(S);return}'
    'if(p.tagName==="INS"&&p.getAttribute("data-adsbygoogle-status")!=="done")return;'
    'if(!e.hasAttribute(S)&&e.getBoundingClientRect().height<=0)return;'
    'var n=(k.get(e)||0)+1;k.set(e,n);if(n>=2)e.setAttribute(S,"")})}'
    'function arm(){if(t)return;c=0;'
    't=setInterval(function(){s();if(++c>=8){clearInterval(t);t=null}},1500)}'
    'arm();'
    'try{new MutationObserver(function(m){for(var j=0;j<m.length;j++)'
    'if(m[j].addedNodes.length){arm();return}})'
    '.observe(document.documentElement,{childList:true,subtree:true})}catch(e){}'
    'addEventListener("scroll",arm,{passive:true});'
    'addEventListener("load",arm)})()</script>'
)

# --- assembled blocks -----------------------------------------------------
#: consent -> AdSense -> gtag loader + config -> Ahrefs -> blank-ad collapse
HEAD = "\n".join([CONSENT, ADS, GTAG_LOADER, GTAG_CONFIG, AHREFS,
                  AD_COLLAPSE_STYLE, AD_COLLAPSE_SCRIPT])

#: same, minus Ahrefs (redirect stubs and most generated pages)
HEAD_NO_AHREFS = "\n".join([CONSENT, ADS, GTAG_LOADER, GTAG_CONFIG,
                            AD_COLLAPSE_STYLE, AD_COLLAPSE_SCRIPT])

#: AdSense-only pages (privacy.html / terms.html) still need the denied
#: baseline, they just have no GA property attached.
HEAD_NO_GTAG = "\n".join([CONSENT, ADS, AHREFS,
                          AD_COLLAPSE_STYLE, AD_COLLAPSE_SCRIPT])


def block(indent="", ahrefs=True, gtag=True, escape_braces=False):
    """Render the canonical head.

    indent          - prefix for each line.
    ahrefs / gtag   - include those tags.
    escape_braces   - double every brace, for templates that go through
                      f-strings or str.format().
    """
    parts = [CONSENT, ADS]
    if gtag:
        parts += [GTAG_LOADER, GTAG_CONFIG]
    if ahrefs:
        parts.append(AHREFS)
    parts += [AD_COLLAPSE_STYLE, AD_COLLAPSE_SCRIPT]
    text = "\n".join(indent + p for p in parts)
    if escape_braces:
        text = text.replace("{", "{{").replace("}", "}}")
    return text


#: Expanded, commented variant for the hand-maintained index.html.
PRETTY = """    <!-- Consent Mode v2 defaults, set before any Google tag so AdSense's CMP
         has something to update via gtag('consent','update'). Denied in the
         regions that require consent, granted everywhere else. -->
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        // 1. Denied baseline for the regions that require consent.
        gtag('consent', 'default', {
            'analytics_storage': 'denied',
            'ad_storage': 'denied',
            'ad_user_data': 'denied',
            'ad_personalization': 'denied',
            'wait_for_update': 500,
            'region': [
                'BE', 'BG', 'CZ', 'DK', 'DE', 'EE', 'IE', 'GR', 'ES', 'FR', 'HR', 'IT',
                'CY', 'LV', 'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI',
                'SK', 'FI', 'SE', 'GB', 'CH', 'IS', 'LI', 'NO'
            ]
        });
        // 2. Granted fallback everywhere else. A region-scoped default wins
        //    over an unscoped one, so this does not loosen the block above.
        gtag('consent', 'default', {
            'analytics_storage': 'granted',
            'ad_storage': 'granted',
            'ad_user_data': 'granted',
            'ad_personalization': 'granted'
        });
    </script>
    <!-- AdSense next: adsbygoogle.js is what injects the consent banner. -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5861928596436289" crossorigin="anonymous"></script>
    <!-- Google Analytics: loader, then config. dataLayer/gtag already exist. -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-LTK6VVHYDW"></script>
    <script>
        gtag('js', new Date());
        gtag('config', 'G-LTK6VVHYDW');
    </script>
    <script src="https://analytics.ahrefs.com/analytics.js" data-key="xrS32xSgQE4Xp1oL20j7uQ" async></script>
""" + "    " + AD_COLLAPSE_STYLE + "\n    " + AD_COLLAPSE_SCRIPT
