#!/usr/bin/env python3
"""
Canonical analytics head block for chemicalresistance.org.

Required order (GDPR / Consent Mode v2)
---------------------------------------
    1. consent defaults   - denied baseline, pushed before anything can read it
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
CONSENT = (
    '<script>window.dataLayer=window.dataLayer||[];'
    'function gtag(){dataLayer.push(arguments);}'
    'gtag("consent","default",{'
    '"analytics_storage":"denied",'
    '"ad_storage":"denied",'
    '"ad_user_data":"denied",'
    '"ad_personalization":"denied",'
    '"wait_for_update":500});</script>'
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

# --- assembled blocks -----------------------------------------------------
#: consent -> AdSense -> gtag loader + config -> Ahrefs
HEAD = "\n".join([CONSENT, ADS, GTAG_LOADER, GTAG_CONFIG, AHREFS])

#: same, minus Ahrefs (redirect stubs and most generated pages)
HEAD_NO_AHREFS = "\n".join([CONSENT, ADS, GTAG_LOADER, GTAG_CONFIG])

#: AdSense-only pages (privacy.html / terms.html) still need the denied
#: baseline, they just have no GA property attached.
HEAD_NO_GTAG = "\n".join([CONSENT, ADS, AHREFS])


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
    text = "\n".join(indent + p for p in parts)
    if escape_braces:
        text = text.replace("{", "{{").replace("}", "}}")
    return text


#: Expanded, commented variant for the hand-maintained index.html.
PRETTY = """    <!-- Consent Mode v2 defaults: denied baseline, set before any Google tag
         so AdSense's CMP has something to update via gtag('consent','update'). -->
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('consent', 'default', {
            'analytics_storage': 'denied',
            'ad_storage': 'denied',
            'ad_user_data': 'denied',
            'ad_personalization': 'denied',
            'wait_for_update': 500
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
    <script src="https://analytics.ahrefs.com/analytics.js" data-key="xrS32xSgQE4Xp1oL20j7uQ" async></script>"""
