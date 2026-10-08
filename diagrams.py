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


# --- D: material fingerprint --------------------------------------------------

#: comparison series, validated as a pair; deliberately not a grade colour
SERIES = ('#6d28d9', '#0891b2')
#: share of rows rated A or B, five steps of one hue (validated as an ordinal ramp)
RAMP = ('#a3b3d3', '#7d95c1', '#5876ad', '#3b5991', '#243c6b')
RAMP_TEXT = ('#111827', '#111827', '#ffffff', '#ffffff', '#ffffff')


def _ramp(share):
    i = min(4, int(share * 5))
    return RAMP[i], RAMP_TEXT[i]


def _stacked(y, counts, tip_prefix, lang, height=16):
    """A 100 % bar of the four grades. Returns (svg, text for desc)."""
    groups = [(g, counts[g]) for g in 'ABCD' if counts[g]]
    gap = 2
    avail = W - gap * (len(groups) - 1)
    x, out, said = 0.0, [], []
    for g, k in groups:
        w = avail * k / counts['n']
        pct = round(100 * k / counts['n'])
        tip = '%s: %s %d %% (%d)' % (tip_prefix, g, pct, k)
        mark = '<rect x="%.1f" y="%d" width="%.1f" height="%d" rx="2" fill="%s"/>' % (
            x, y, w, height, GRADE_FILL[g])
        inner = '%s %d %%' % (g, pct)
        if w >= 5.6 * len(inner) + 6:
            mark += _text(x + w / 2, y + height / 2 + 3.5, inner, 10, GRADE_TEXT[g], 'middle', '600')
        elif w >= 14:
            mark += _text(x + w / 2, y + height / 2 + 3.5, g, 10, GRADE_TEXT[g], 'middle', '600')
        out.append('<g><title>%s</title>%s</g>' % (esc(tip), mark))
        said.append('%s %d %%' % (g, pct))
        x += w + gap
    return ''.join(out), ', '.join(said)


def fingerprint(lang, mname, profile, class_name, min_rows):
    """One 100 % bar per chemical class: how the material is rated across the
    rows of that class at 20 °C."""
    body, desc, y = [], [], 0
    for cls, counts in profile.items():
        if cls == 'all' or counts['n'] < min_rows:
            continue
        label = '%s (%d)' % (class_name(cls, lang), counts['n'])
        body.append(_text(0, y + 10, label, 10, INK, weight='600'))
        bar, said = _stacked(y + 14, counts, class_name(cls, lang), lang)
        body.append(bar)
        desc.append('%s: %s' % (class_name(cls, lang), said))
        y += 14 + 16 + 10
    if not body:
        return None
    title = '%s: %s' % (mname, t('fig_finger_h', lang))
    return _svg(y - 6, title, '. '.join(desc) + '.', ''.join(body))


def overall_bars(lang, items, title):
    """items: [(material name, counts)]. One 100 % bar per material."""
    body, desc, y = [], [], 0
    for name, counts in items:
        if not counts['n']:
            continue
        body.append(_text(0, y + 10, '%s (%d)' % (name, counts['n']), 10, INK, weight='600'))
        bar, said = _stacked(y + 14, counts, name, lang, height=14)
        body.append(bar)
        desc.append('%s: %s' % (name, said))
        y += 14 + 14 + 9
    return _svg(y - 5, title, '. '.join(desc) + '.', ''.join(body))


# --- E: comparison overlay and agreement grid ---------------------------------

def overlay(lang, name_a, name_b, prof_a, prof_b, class_name, min_rows, good_share):
    """Per class, the share of rows rated A or B for each of two materials."""
    body, desc, y = [], [], 0
    track = W - 40
    for cls in prof_a:
        if cls == 'all' or prof_a[cls]['n'] < min_rows or prof_b[cls]['n'] < min_rows:
            continue
        body.append(_text(0, y + 10, class_name(cls, lang), 10, INK, weight='600'))
        y += 14
        said = []
        for i, (name, prof) in enumerate(((name_a, prof_a), (name_b, prof_b))):
            share = good_share(prof[cls])
            w = max(2.0, track * share)
            pct = round(100 * share)
            tip = '%s, %s: %d %% (%d)' % (class_name(cls, lang), name, pct, prof[cls]['n'])
            body.append('<g><title>%s</title><rect x="0" y="%d" width="%d" height="9" rx="2" fill="#f1f5f9"/>'
                        '<rect x="0" y="%d" width="%.1f" height="9" rx="2" fill="%s"/>%s</g>' % (
                            esc(tip), y, track, y, w, SERIES[i],
                            _text(track + 6, y + 8, '%d %%' % pct, 9, INK)))
            said.append('%s %d %%' % (name, pct))
            y += 11
        desc.append('%s: %s' % (class_name(cls, lang), ', '.join(said)))
        y += 8
    if not body:
        return None
    title = '%s, %s: %s' % (name_a, name_b, t('fig_overlay_h', lang))
    return _svg(y - 6, title, '. '.join(desc) + '.', ''.join(body))


def pair_mini_chart(lang, chem_name, chem, mat, pv):
    """Small bar chart showing all 24 materials ranked by 20 °C grade for this
    chemical, with the current material highlighted. Returns (svg, key)."""
    ratings = pv['ratings']
    items = []
    for m in rd.MATERIALS:
        r = ratings.get(m)
        g = r['w20'] if r and r.get('w20') else None
        items.append((m, g))
    # sort: A first, then B, C, D, None
    rank = {'A': 0, 'B': 1, 'C': 2, 'D': 3, None: 4}
    items.sort(key=lambda x: (rank.get(x[1], 4), x[0]))

    bar_w = 10
    gap = 2
    left = 0
    top = 14
    bar_h = 40
    total_w = left + len(items) * (bar_w + gap) - gap
    height = top + bar_h + 24

    body = []
    desc_parts = []
    for i, (m, g) in enumerate(items):
        x = left + i * (bar_w + gap)
        h = {None: 5, 'D': 10, 'C': 20, 'B': 30, 'A': 40}[g]
        y = top + bar_h - h
        fill = GRADE_FILL[g]
        mname = material_name(m, lang)
        grade_label = g or '–'
        is_current = m == mat
        tip = '%s: %s' % (mname, grade_label)
        stroke = ' stroke="#111827" stroke-width="1.5"' if is_current else ''
        body.append('<g><title>%s</title>'
                    '<rect x="%.1f" y="%d" width="%d" height="%d" rx="1" fill="%s"%s/>'
                    '</g>' % (esc(tip), x, y, bar_w, h, fill, stroke))
        if is_current:
            # label below the highlighted bar
            body.append(_text(x + bar_w / 2, top + bar_h + 11,
                              short_name(m, lang), 8, INK, 'middle', '700'))
            desc_parts.insert(0, '%s: %s (highlighted)' % (mname, grade_label))
        else:
            desc_parts.append('%s: %s' % (mname, grade_label))
    title = '%s: %s' % (chem_name, t('fig_pair_chart', lang))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" '
           'aria-labelledby="fg%dt fg%dd" style="display:block;width:100%%;max-width:400px;height:auto" %s>'
           '<title id="fg%dt">%s</title><desc id="fg%dd">%s</desc>%s</svg>') % (
        total_w, height, _counter[0] + 1, _counter[0] + 1, FONT,
        _counter[0] + 1, esc(title), _counter[0] + 1, esc('; '.join(desc_parts[:6]) + '.'), ''.join(body))
    _counter[0] += 1
    return svg


def series_key(name_a, name_b):
    return '<div class="cr-key"><span><i style="background:%s"></i>%s</span><span><i style="background:%s"></i>%s</span></div>' % (
        SERIES[0], esc(name_a), SERIES[1], esc(name_b))


def agreement_grid(lang, name_a, name_b, grid):
    """4 x 4 counts: rows are the grade of the first material, columns the
    grade of the second. The diagonal is where they agree."""
    left, top, cw, ch, gap = 96, 34, 54, 26, 2
    peak = max(grid.values()) or 1
    body = [_text(left + (4 * cw + 3 * gap) / 2, 10, name_b, 10, INK, 'middle', '600')]
    for j, g in enumerate('ABCD'):
        body.append(_text(left + j * (cw + gap) + cw / 2, 26, g, 11, INK, 'middle', '700'))
    body.append(_text(0, top + 2 * ch + gap, name_a[:16], 10, INK, weight='600'))
    desc = []
    for i, ga in enumerate('ABCD'):
        y = top + i * (ch + gap)
        body.append(_text(left - 10, y + 17, ga, 11, INK, 'end', '700'))
        for j, gb in enumerate('ABCD'):
            k = grid[(ga, gb)]
            x = left + j * (cw + gap)
            if k:
                fill, ink = _ramp(min(0.999, k / peak))
            else:
                fill, ink = '#f1f5f9', MUTED
            tip = '%s %s, %s %s: %d' % (name_a, ga, name_b, gb, k)
            ring = ' stroke="#111827" stroke-width="1.5"' if ga == gb else ''
            body.append('<g><title>%s</title><rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s"%s/>%s</g>' % (
                esc(tip), x, y, cw, ch, fill, ring,
                _text(x + cw / 2, y + 17, str(k), 10, ink, 'middle', '600')))
            if k:
                desc.append(tip)
    title = '%s, %s: %s' % (name_a, name_b, t('fig_grid_h', lang))
    return _svg(top + 4 * (ch + gap) + 2, title, '; '.join(desc) + '.', ''.join(body))


# --- F: group chart -----------------------------------------------------------

def class_grid(lang, names, profiles, class_name, min_rows, good_share, title, heads=None):
    """Classes down, materials across; each cell is the share of rows rated
    A or B, as a number on a tinted cell. heads are the column labels when the
    full names are too long for a column; a line break in one is kept."""
    left, gap = 116, 2
    cw = (W - left - gap * (len(names) - 1)) / len(names)
    top = 30
    body = []
    heads = heads or names
    for i, name in enumerate(heads):
        lines = name.split('\n') if '\n' in name else _wrap(name, cw)
        for j, line in enumerate(lines[:2]):
            body.append(_text(left + i * (cw + gap) + cw / 2, 10 + 11 * j + (11 if len(lines) == 1 else 0),
                              line, 9, INK, 'middle', '600'))
    y, desc = top, []
    for cls in profiles[0]:
        if cls == 'all' or not any(p[cls]['n'] >= min_rows for p in profiles):
            continue
        label = class_name(cls, lang, short=True)
        body.append(_text(0, y + 12, label, 9, INK))
        said = []
        for i, (name, prof) in enumerate(zip(names, profiles)):
            x = left + i * (cw + gap)
            if prof[cls]['n'] < min_rows:
                fill, ink, label_c = '#f1f5f9', MUTED, '–'
                tip = '%s, %s: %s' % (class_name(cls, lang), name, t('g_none', lang))
            else:
                share = good_share(prof[cls])
                fill, ink = _ramp(min(0.999, share))
                label_c = '%d %%' % round(100 * share)
                tip = '%s, %s: %s (%d)' % (class_name(cls, lang), name, label_c, prof[cls]['n'])
                said.append('%s %s' % (name, label_c))
            body.append('<g><title>%s</title><rect x="%.1f" y="%d" width="%.1f" height="17" rx="2" fill="%s"/>%s</g>' % (
                esc(tip), x, y, cw, fill, _text(x + cw / 2, y + 12, label_c, 9, ink, 'middle', '600')))
        desc.append('%s: %s' % (class_name(cls, lang), ', '.join(said)))
        y += 19
    return _svg(y, title, '. '.join(desc) + '.', ''.join(body))


def ramp_key(lang):
    steps = ''.join('<span><i style="background:%s"></i>%s</span>' % (c, lab)
                    for c, lab in zip(RAMP, ('0–19 %', '20–39 %', '40–59 %', '60–79 %', '80–100 %')))
    return '<div class="cr-key">%s</div>' % steps


# --- G: viscosity scale -------------------------------------------------------

def viscosity_scale(title, desc_unit, items):
    """items: [(name, mPa·s)], drawn as dots on a logarithmic axis from 1 to
    100,000 mPa·s."""
    import math
    left, right, top, step = 118, W - 34, 20, 15
    lo, hi = 0, 5
    span = right - left
    body = []
    for d in range(lo, hi + 1):
        x = left + span * (d - lo) / (hi - lo)
        body.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>' % (
            x, top - 4, x, top + step * len(items), GRID))
        label = {0: '1', 1: '10', 2: '100', 3: '1,000', 4: '10k', 5: '100k'}[d]
        body.append(_text(x, 10, label, 9, MUTED, 'middle'))
    said = []
    for i, (name, value) in enumerate(items):
        y = top + step * i + step / 2
        x = left + span * (math.log10(max(value, 1)) - lo) / (hi - lo)
        shown = '{:,}'.format(int(value)) if value >= 10 else ('%g' % value)
        tip = '%s: %s %s' % (name, shown, desc_unit)
        side = _text(x + 8, y + 3.5, shown, 9, INK) if x < right - 30 else _text(x - 8, y + 3.5, shown, 9, INK, 'end')
        body.append('<g><title>%s</title>%s<circle cx="%.1f" cy="%.1f" r="4" fill="#1d4ed8"/>%s</g>' % (
            esc(tip), _text(0, y + 3.5, name, 9.5, INK), x, y, side))
        said.append('%s %s' % (name, shown))
    return _svg(top + step * len(items) + 2, title, ', '.join(said) + ' ' + desc_unit + '.', ''.join(body))


# --- H: storage segregation matrix --------------------------------------------

STORAGE_FILL = {'ok': '#15803d', 'caution': '#d97706', 'separate': '#475569', 'never': '#b91c1c', None: '#f1f5f9'}
STORAGE_TEXT = {'ok': '#ffffff', 'caution': '#111827', 'separate': '#ffffff', 'never': '#ffffff', None: '#4b5563'}


def storage_matrix(title, names, rating, labels):
    """names: [(key, label)] in order. rating(a, b) -> key of labels or None.
    Lower triangle of the class-by-class table, the rule written in each cell."""
    n = len(names)
    left, gap = 78, 2
    cw = (W - left - gap * (n - 1)) / n
    ch = 24
    body, said = [], []
    for i, (ka, la) in enumerate(names):
        y = i * (ch + gap)
        body.append(_text(0, y + 15, la, 9, INK, weight='600'))
        for j, (kb, lb) in enumerate(names[:i + 1]):
            x = left + j * (cw + gap)
            r = rating(ka, kb)
            word = labels[r]
            tip = '%s + %s: %s' % (la, lb, word)
            short = _wrap(word, cw, 8)[0]
            body.append('<g><title>%s</title><rect x="%.1f" y="%d" width="%.1f" height="%d" rx="2" fill="%s"/>%s</g>' % (
                esc(tip), x, y, cw, ch, STORAGE_FILL[r], _text(x + cw / 2, y + 15, short, 8, STORAGE_TEXT[r], 'middle', '600')))
            if r:
                said.append(tip)
    y = n * (ch + gap) + 4
    for j, (_k, lb) in enumerate(names):
        x = left + j * (cw + gap) + cw / 2
        for k, line in enumerate(_wrap(lb, cw, 8)[:2]):
            body.append(_text(x, y + 8 + 10 * k, line, 8, INK, 'middle', '600'))
    return _svg(y + 24, title, '; '.join(said) + '.', ''.join(body))


#: column labels for narrow grids; the full name stays in the hover text
SHORT = {'PVC_HART': 'PVC-U', 'PVC_WEICH': 'PVC-P', 'PS': 'PS', 'PC': 'PC', 'POM': 'POM', 'PA': 'PA',
         'PSU': 'PSU', 'ECTFE_ETFE': 'ECTFE', 'FPM': 'FPM', 'V4A': '316', 'V2A': '304', 'AL': 'Al'}


def short_name(code, lang):
    return SHORT.get(code) or material_name(code, lang)
