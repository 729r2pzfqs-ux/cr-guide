#!/usr/bin/env python3
"""
Add Google Consent Mode v2 defaults ahead of the gtag config call.

Why region-scoped
-----------------
The site's consent banner is Google's Privacy & messaging (Funding Choices)
GDPR message, which is shown to EEA/UK/CH visitors only. A global "denied"
default would therefore put every visitor into denied state while the banner -
the only thing that can grant consent - never appears outside those regions,
leaving GA on cookieless pings for most of the traffic. Scoping the default to
the regions where the banner actually runs keeps the rest collecting normally.

Consent defaults must be pushed before gtag('js')/gtag('config'), so the block
is inserted directly after the gtag() function definition.

Also moves the AdSense loader ahead of the gtag loader. The consent message is
injected by that tag, so requesting it earlier gives the CMP more of the
wait_for_update window to call gtag('consent','update',...).

Idempotent: a file that already contains a consent call is skipped.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# EEA (EU 27 + IS/LI/NO) plus the UK and Switzerland - where the GDPR message runs.
REGIONS = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE", "IS", "LI", "NO", "GB", "CH",
]

GTAG_LOADER = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-LTK6VVHYDW"></script>'
ADS_LOADER = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
              '?client=ca-pub-5861928596436289" crossorigin="anonymous"></script>')

# --- minified variant (69,053 files) -------------------------------------
MIN_ANCHOR = 'function gtag(){dataLayer.push(arguments);}'
MIN_CONSENT = (
    MIN_ANCHOR
    + 'gtag("consent","default",{'
    + '"analytics_storage":"denied",'
    + '"ad_storage":"denied",'
    + '"ad_user_data":"denied",'
    + '"ad_personalization":"denied",'
    + '"wait_for_update":500,'
    + '"region":[' + ",".join(f'"{r}"' for r in REGIONS) + ']});'
)

# --- pretty variant (index.html) -----------------------------------------
PRETTY_ANCHOR = "        function gtag(){dataLayer.push(arguments);}\n"
PRETTY_CONSENT = PRETTY_ANCHOR + (
    "        // Consent Mode v2 defaults. Scoped to the regions where Google's\n"
    "        // Privacy & messaging GDPR banner actually runs - a global denied\n"
    "        // default would strand every other visitor with nothing to grant it.\n"
    "        gtag('consent', 'default', {\n"
    "            'analytics_storage': 'denied',\n"
    "            'ad_storage': 'denied',\n"
    "            'ad_user_data': 'denied',\n"
    "            'ad_personalization': 'denied',\n"
    "            'wait_for_update': 500,\n"
    "            'region': [" + ", ".join(f"'{r}'" for r in REGIONS) + "]\n"
    "        });\n"
)


def html_files():
    skip = {".git", ".venv", "__pycache__", "node_modules", "data"}
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith(".html"):
                yield Path(root) / f


def reorder_ads_before_gtag(text):
    """Request the AdSense tag (which injects the CMP) before the gtag loader."""
    if GTAG_LOADER not in text or ADS_LOADER not in text:
        return text, False
    if text.index(ADS_LOADER) < text.index(GTAG_LOADER):
        return text, False  # already ahead
    text = text.replace(ADS_LOADER, "", 1)
    text = text.replace(GTAG_LOADER, ADS_LOADER + "\n" + GTAG_LOADER, 1)
    return text, True


def main():
    stats = {"consent": 0, "reordered": 0, "already": 0, "no_gtag": 0, "anchor_miss": []}

    for path in html_files():
        text = original = path.read_text(encoding="utf-8", errors="surrogateescape")

        if "gtag(" not in text or "config" not in text:
            stats["no_gtag"] += 1
            continue
        if '"consent"' in text or "'consent'" in text:
            stats["already"] += 1
            continue

        if text.count(PRETTY_ANCHOR) == 1:
            text = text.replace(PRETTY_ANCHOR, PRETTY_CONSENT, 1)
        elif text.count(MIN_ANCHOR) == 1:
            text = text.replace(MIN_ANCHOR, MIN_CONSENT, 1)
        else:
            stats["anchor_miss"].append(str(path.relative_to(ROOT)))
            continue
        stats["consent"] += 1

        text, moved = reorder_ads_before_gtag(text)
        if moved:
            stats["reordered"] += 1

        if text != original:
            path.write_text(text, encoding="utf-8", errors="surrogateescape")

    print(f"consent defaults added : {stats['consent']}")
    print(f"AdSense moved ahead    : {stats['reordered']}")
    print(f"already had consent    : {stats['already']}")
    print(f"no gtag block          : {stats['no_gtag']}")
    if stats["anchor_miss"]:
        print(f"SKIPPED - anchor not found: {len(stats['anchor_miss'])}")
        for s in stats["anchor_miss"][:10]:
            print(f"    {s}")


if __name__ == "__main__":
    main()
