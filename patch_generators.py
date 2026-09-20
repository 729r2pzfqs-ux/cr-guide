#!/usr/bin/env python3
"""
Rewrite the analytics head baked into every page generator so it emits the
canonical Consent Mode v2 order from analytics_head.py:

    consent defaults -> AdSense -> gtag loader + config -> Ahrefs

Each generator holds the tags as literal text inside an f-string or a
str.format() template, so this walks the .py source, finds every cluster of
Google/Ahrefs script tags (tags separated only by whitespace) and swaps the
cluster for the canonical block - preserving the cluster's indentation and its
brace-escaping convention.

Run with --check to print what would change without writing.
"""

import re
import sys
from pathlib import Path

import analytics_head

ROOT = Path(__file__).parent

# Each tag as it appears in the templates. Braces are doubled ({{ }}) when the
# surrounding literal is an f-string / str.format template, so brace runs are
# matched as "one or two".
TAG_PATTERNS = {
    "ads": r'<script async src="https://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=ca-pub-5861928596436289" crossorigin="anonymous"></script>',
    "gtag": r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=G-LTK6VVHYDW"></script>',
    "ahrefs": r'<script src="https://analytics\.ahrefs\.com/analytics\.js" data-key="xrS32xSgQE4Xp1oL20j7uQ" async></script>',
    "adcollapse_style": r'<style>ins\.adsbygoogle\[data-ad-status="unfilled"\](?:(?!</style>).)*</style>',
    "adcollapse_script": r'<script>\(function\(\)\{{1,2}var S="data-blank-ad"(?:(?!</script>).)*</script>',
    # already-canonical output, so re-running is a no-op
    "consent": (
        r'<script>\s*window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];\s*'
        r'function gtag\(\)\{{1,2}dataLayer\.push\(arguments\);?\}{1,2}\s*'
        r'gtag\(\s*[\'"]consent[\'"]\s*,\s*[\'"]default[\'"].*?\)\s*;\s*</script>'
    ),
    "config": (
        r'<script>\s*gtag\(\s*[\'"]js[\'"]\s*,\s*new Date\(\)\s*\)\s*;\s*'
        r'gtag\(\s*[\'"]config[\'"]\s*,\s*[\'"]G-LTK6VVHYDW[\'"]\s*\)\s*;\s*</script>'
    ),
    "inline": (
        r'<script>\s*window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];\s*'
        r'function gtag\(\)\{{1,2}dataLayer\.push\(arguments\);?\}{1,2}\s*'
        r'(?:(?!</script>).)*?'
        r'gtag\(\s*[\'"]js[\'"]\s*,\s*new Date\(\)\s*\)\s*;\s*'
        r'gtag\(\s*[\'"]config[\'"]\s*,\s*[\'"]G-LTK6VVHYDW[\'"]\s*\)\s*;\s*'
        r'</script>'
    ),
}
ALT = "|".join(f"(?:{p})" for p in TAG_PATTERNS.values())
ANY_TAG = re.compile("|".join(f"(?P<{k}>{v})" for k, v in TAG_PATTERNS.items()), re.S)
CLUSTER = re.compile(rf"(?P<indent>[ \t]*)(?P<body>(?:{ALT})(?:[ \t\r\n]*(?:{ALT}))*)", re.S)

# Generators whose tag cluster carries no inline script, so no brace evidence.
# True  = cluster sits in an f-string/format template and must double braces.
BRACE_OVERRIDE = {
    "build_index.py": True,   # f''' ... ''' page template
}


def canonical(kinds, indent, escape):
    return analytics_head.block(
        indent=indent,
        ahrefs="ahrefs" in kinds,
        gtag=bool({"gtag", "inline", "config"} & kinds),
        escape_braces=escape,
    )


def patch(path):
    src = path.read_text(encoding="utf-8")
    if not ANY_TAG.search(src):
        return None
    changes = []

    def repl(m):
        body, indent = m.group("body"), m.group("indent")
        kinds = {mm.lastgroup for mm in ANY_TAG.finditer(body)}
        if "{{dataLayer" in body:
            escape = True
        elif "{dataLayer" in body:
            escape = False
        else:
            escape = BRACE_OVERRIDE.get(path.name)
            if escape is None:
                raise SystemExit(f"{path.name}: cannot infer brace style for cluster {sorted(kinds)}")
        new = canonical(kinds, indent, escape)
        if m.group(0).strip() == new.strip():
            return m.group(0)  # already canonical
        changes.append((sorted(kinds), escape, m.group(0), new))
        return new

    out = CLUSTER.sub(repl, src)
    return out, changes


def main():
    check = "--check" in sys.argv
    targets = sorted(p for p in ROOT.glob("*.py")
                     if p.name not in {"analytics_head.py", "patch_generators.py",
                                       "fix_consent_order.py", "add_consent_mode.py"})
    touched = 0
    for path in targets:
        res = patch(path)
        if not res:
            continue
        out, changes = res
        if not changes:
            continue
        touched += 1
        print(f"\n########## {path.name}  ({len(changes)} cluster(s))")
        for kinds, escape, old, new in changes:
            print(f"  --- kinds={kinds} escape_braces={escape}")
            for line in old.splitlines():
                print(f"  - {line}")
            for line in new.splitlines():
                print(f"  + {line}")
        if not check:
            path.write_text(out, encoding="utf-8")
    print(f"\n{'would patch' if check else 'patched'}: {touched} generator(s)")


if __name__ == "__main__":
    main()
