#!/usr/bin/env python3
"""Inline SVG diagrams, drawn from resistance_data.

Rules every diagram here follows:

  * inline SVG, no script; the hover text of a mark is its own <title>,
  * colours are hex, because SVG presentation attributes do not resolve var(),
  * sizing is inline, so a page lays out correctly against a cached stylesheet,
  * the viewBox is 320 wide, so text is about 10 px on a 375 px phone,
  * <title> and <desc> carry the content for screen readers,
  * a grade is never shown by colour alone: the letter is always on the mark
    or in the row.

The four grade colours were checked with the dataviz palette validator
(lightness band, chroma floor, colour-blind separation, contrast). The amber
of grade C takes dark text; the other three take white.
"""

import html

import resistance_data as rd
from page_i18n import material_name, t

W = 320
INK = '#111827'
MUTED = '#4b5563'
GRID = '#e5e7eb'
SURFACE = '#ffffff'
GRADE_FILL = {'A': '#15803d', 'B': '#1d4ed8', 'C': '#d97706', 'D': '#b91c1c', None: '#d1d5db'}
GRADE_TEXT = {'A': '#ffffff', 'B': '#ffffff', 'C': '#111827', 'D': '#ffffff', None: '#374151'}
FONT = 'font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif"'

_counter = [0]


def esc(s):
    return html.escape(str(s), quote=True)


def _svg(height, title, desc, body, max_width=520):
    _counter[0] += 1
    n = _counter[0]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" '
            'aria-labelledby="fg%dt fg%dd" style="display:block;width:100%%;max-width:%dpx;height:auto" %s>'
            '<title id="fg%dt">%s</title><desc id="fg%dd">%s</desc>%s</svg>') % (
        W, height, n, n, max_width, FONT, n, esc(title), n, esc(desc), body)


def reset_ids():
    """Call once per page so figure ids are stable from build to build."""
    _counter[0] = 0


def figure(svg, caption, key=''):
    return '<figure class="cr-fig">%s%s<figcaption>%s</figcaption></figure>' % (svg, key, esc(caption))


def grade_key(lang, with_none=True):
    items = ''.join(
        '<span><i style="background:%s"></i>%s %s</span>' % (GRADE_FILL[g], g, esc(t('g_' + g, lang)))
        for g in 'ABCD')
    if with_none:
        items += '<span><i style="background:%s"></i>%s</span>' % (GRADE_FILL[None], esc(t('g_none', lang)))
    return '<div class="cr-key">%s</div>' % items


def _text(x, y, s, size=10, fill=INK, anchor='start', weight='400'):
    return '<text x="%.1f" y="%.1f" font-size="%d" fill="%s" text-anchor="%s" font-weight="%s">%s</text>' % (
        x, y, size, fill, anchor, weight, esc(s))


# --- C: rating profile by material family -------------------------------------

def profile_bars(lang, name, variant):
    """One stacked bar per material family: how many materials hold each grade
    at 20 °C."""
    rows = []
    for fam in rd.FAMILIES:
        codes = [m for m, (_s, f) in rd.MATERIALS.items() if f == fam]
        groups = []
        for g in ('A', 'B', 'C', 'D', None):
            members = [m for m in codes
                       if (variant['ratings'].get(m) or {}).get('w20') == g]
            if members:
                groups.append((g, members))
        rows.append((fam, codes, groups))

    body, y, desc = [], 0, []
    gap = 2
    for fam, codes, groups in rows:
        label = '%s (%d)' % (t('fam_' + fam, lang), len(codes))
        body.append(_text(0, y + 10, label, 10, INK, weight='600'))
        y += 15
        avail = W - gap * (len(groups) - 1)
        x = 0.0
        parts = []
        for g, members in groups:
            w = avail * len(members) / len(codes)
            grade_word = t('g_' + g, lang) if g else t('g_none', lang)
            names = ', '.join(material_name(m, lang) for m in members)
            tip = '%s: %d × %s (%s)' % (t('fam_' + fam, lang), len(members),
                                        ('%s, %s' % (g, grade_word)) if g else grade_word, names)
            mark = '<rect x="%.1f" y="%d" width="%.1f" height="16" rx="2" fill="%s"/>' % (x, y, w, GRADE_FILL[g])
            inner = '%s %d' % (g, len(members)) if g else '– %d' % len(members)
            if w >= 7 * len(inner) + 6:
                mark += _text(x + w / 2, y + 11.5, inner, 10, GRADE_TEXT[g], 'middle', '600')
            body.append('<g><title>%s</title>%s</g>' % (esc(tip), mark))
            parts.append('%d %s' % (len(members), g or grade_word))
            x += w + gap
        desc.append('%s: %s' % (t('fam_' + fam, lang), ', '.join(parts)))
        y += 16 + 12
    title = '%s: %s' % (name, t('fig_profile_h', lang))
    return _svg(y - 8, title, '. '.join(desc) + '.', ''.join(body))


# --- B: temperature shift -----------------------------------------------------

def temperature_shift(lang, name, variant):
    """Materials whose grade differs between 20 °C and 50 °C, each as a line
    from its 20 °C grade (open circle) to its 50 °C grade (filled circle).
    Returns None when no material changes."""
    rows = []
    for m in rd.MATERIALS:
        r = variant['ratings'].get(m)
        if r and r.get('w20') and r.get('w50') and r['w20'] != r['w50']:
            rows.append((m, r['w20'], r['w50']))
    if not rows:
        return None

    left = 104
    col = {g: left + 27 + i * 54 for i, g in enumerate('ABCD')}
    top = 22
    step = 20
    height = top + step * len(rows) + 4
    body = []
    for g in 'ABCD':
        body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (
            col[g], top - 4, col[g], height - 4, GRID))
        body.append(_text(col[g], 11, g, 11, INK, 'middle', '700'))
    desc = []
    for i, (m, g20, g50) in enumerate(rows):
        y = top + step * i + step / 2
        mname = material_name(m, lang)
        tip = '%s: %s %s, %s %s' % (mname, g20, t('at20', lang), g50, t('at50', lang))
        mark = _text(0, y + 3.5, mname, 10, INK)
        mark += '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (
            col[g20], y, col[g50], y, MUTED)
        mark += '<circle cx="%d" cy="%.1f" r="5" fill="%s" stroke="%s" stroke-width="2"/>' % (
            col[g20], y, SURFACE, MUTED)
        mark += '<circle cx="%d" cy="%.1f" r="7" fill="%s"/>' % (col[g50], y, SURFACE)
        mark += '<circle cx="%d" cy="%.1f" r="5" fill="%s"/>' % (col[g50], y, GRADE_FILL[g50])
        body.append('<g><title>%s</title>%s</g>' % (esc(tip), mark))
        desc.append('%s %s → %s' % (mname, g20, g50))
    title = '%s: %s' % (name, t('fig_temp_h', lang))
    return _svg(height, title, '; '.join(desc) + '.', ''.join(body))


def temperature_key(lang):
    return ('<div class="cr-key"><span><i style="background:#fff;border:2px solid %s;border-radius:50%%"></i>20 °C</span>'
            '<span><i style="background:%s;border-radius:50%%"></i>50 °C</span></div>') % (MUTED, MUTED)


# --- A: concentration ladder --------------------------------------------------

def _wrap(label, width, size=9):
    """Split a column label over at most two lines; shorten what still does not fit."""
    per = size * 0.54
    fits = max(3, int(width / per))
    if len(label) <= fits:
        return [label]
    words = label.split(' ')
    if len(words) > 1:
        best = None
        for i in range(1, len(words)):
            a, b = ' '.join(words[:i]), ' '.join(words[i:])
            longest = max(len(a), len(b))
            if best is None or longest < best[0]:
                best = (longest, [a, b])
        lines = best[1]
    else:
        lines = [label]
    return [l if len(l) <= fits else l[:fits - 1] + '…' for l in lines]


def concentration_ladder(lang, name, chem, labels):
    """Materials down, concentrations across. A cell shows the 20 °C grade, and
    the 50 °C grade after an arrow when it differs. labels are the localized
    concentration names, one per variant."""
    variants = chem['variants']
    left = 100
    gap = 2
    cw = (W - left - gap * (len(variants) - 1)) / len(variants)
    heads = [_wrap(l, cw) for l in labels]
    top = 12 * max(len(h) for h in heads) + 6
    body = []
    for i, lines in enumerate(heads):
        x = left + i * (cw + gap) + cw / 2
        for j, line in enumerate(lines):
            body.append(_text(x, 10 + 12 * j + (12 if len(lines) == 1 and top > 18 else 0), line, 9, INK,
                              'middle', '600'))
    y = top
    desc = []
    for fam in rd.FAMILIES:
        codes = [m for m, (_s, f) in rd.MATERIALS.items() if f == fam
                 and any(m in v['ratings'] for v in variants)]
        if not codes:
            continue
        body.append(_text(0, y + 9, t('fam_' + fam, lang).upper(), 8, MUTED, weight='600'))
        y += 13
        for m in codes:
            mname = material_name(m, lang)
            body.append(_text(0, y + 11, mname, 10, INK))
            said = []
            for i, v in enumerate(variants):
                x = left + i * (cw + gap)
                r = v['ratings'].get(m)
                if r is None or (not r.get('w20') and not r.get('k')):
                    g, label, word = None, '–', t('g_none', lang)
                elif r.get('k'):
                    g, label, word = None, 'K', t('k_value', lang)
                else:
                    g = r['w20']
                    label = r['c20']
                    word = '%s %s' % (r['c20'], t('at20', lang))
                    if r.get('w50') and r['w50'] != r['w20']:
                        label = '%s→%s' % (r['c20'], r['c50'])
                    if r.get('w50'):
                        word += ', %s %s' % (r['c50'], t('at50', lang))
                    if r.get('est'):
                        label += '*'
                        word += ' (%s)' % t('est', lang)
                tip = '%s, %s: %s' % (mname, labels[i], word)
                size = 9 if len(label) * 5.4 + 4 <= cw else 8
                body.append('<g><title>%s</title><rect x="%.1f" y="%d" width="%.1f" height="15" rx="2" fill="%s"/>%s</g>' % (
                    esc(tip), x, y, cw, GRADE_FILL[g],
                    _text(x + cw / 2, y + 11, label, size, GRADE_TEXT[g], 'middle', '600')))
                said.append('%s %s' % (labels[i], label))
            desc.append('%s: %s' % (mname, ', '.join(said)))
            y += 17
        y += 4
    title = '%s: %s' % (name, t('fig_ladder_h', lang))
    return _svg(y, title, '. '.join(desc) + '.', ''.join(body), max_width=640)
