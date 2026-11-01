#!/usr/bin/env python3
"""Fit a meta description into the 120-160 character window.

Every page generator states the answer first and hands the rest of what it
knows to fit(), which keeps the richest combination that lands in the window.
A page that cannot fit stops the build instead of publishing a bad length.
"""

from itertools import combinations

MIN_LEN = 120
MAX_LEN = 160


def fit(lead, middles=('',), extras=(), sep=' '):
    """lead + the first middle that works + as many extras as fit, in order.

    middles is ordered best first, typically one material list at falling
    lengths, and may end with '' to allow leaving it out. Extras keep their
    order and an earlier extra is preferred over a later one."""
    extras = [e for e in extras if e]
    for middle in middles:
        for k in range(len(extras), -1, -1):
            for chosen in combinations(extras, k):
                text = sep.join(x for x in (lead, middle) + chosen if x)
                if MIN_LEN <= len(text) <= MAX_LEN:
                    return text
    raise ValueError('no description of %d-%d characters for: %s' % (MIN_LEN, MAX_LEN, lead))
