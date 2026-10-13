"""Parser for Meta / Facebook earnings releases (8-K Item 2.02, Ex. 99.1) and 10-Q / 10-K text (h2t.py output: one table row per line,
cells joined by ' | ').

Tables are found by title (statements of operations / income, balance sheets, cash flows, segment information, reconciliations).
Each table's columns are resolved from its year header line, whatever the order (the 2012-16 releases print the prior year first,
2017+ the current year first; headers can carry footnote markers such as "2016 (1)" or "2019*"). Flow tables carry three-month and
year-to-date columns (cur3, py3, cury, pyy); balance sheets two period ends (cur, prior). Numbers: "(16" (h2t drops the closing
parenthesis) = -16; "—" = 0. KPIs are read from the release text (DAUs, MAUs, DAP, MAP, ad impressions, price per ad, headcount)."""
import re

DASH = {'—', '–', '-', '—%', '- -'}
NUMRE = re.compile(r'^\(?\$?\s*-?[\d,]*\.?\d+\s*\)?\s*%?$')

def num(c):
    c = c.strip().replace('$', '').strip()
    c = re.sub(r'(?<=\d)\s+\(\d\)$', '', c)       # footnote marker after a number: "6,436 (1)"
    c = c.rstrip('*').strip()
    if c in DASH: return 0.0
    if not NUMRE.match(c): return None
    neg = c.startswith('(')
    c = c.strip('()% ').replace(',', '')
    try: v = float(c)
    except ValueError: return None
    return -v if neg else v

def year_of(cell):
    m = re.search(r'(19|20)\d\d', cell)
    return int(m.group(0)) if m else None

TITLES = [('is', re.compile(r'CONSOLIDATED STATEMENTS? OF (OPERATIONS|INCOME)', re.I)),
          ('bs', re.compile(r'CONSOLIDATED BALANCE SHEETS?', re.I)),
          ('cf', re.compile(r'CONSOLIDATED STATEMENTS? OF CASH FLOWS', re.I)),
          ('seg', re.compile(r'^Segment Information\s*$', re.I)),
          ('rec', re.compile(r'^Reconciliation of (GAAP to Non-GAAP|Non-GAAP Results)', re.I))]

def sections(lines):
    """[(kind, start, end)] — a table runs from its title to the next title of any kind."""
    hits = []
    for i, l in enumerate(lines):
        s = l.strip()
        if len(s) > 120: continue
        for k, rx in TITLES:
            if rx.search(s): hits.append((k, i)); break
    out = []
    for j, (k, i) in enumerate(hits):
        e = hits[j + 1][1] if j + 1 < len(hits) else len(lines)
        out.append((k, i, e))
    return out

def header(lines, s, e):
    """first line in the table whose cells all carry a year -> list of years (column order)."""
    for i in range(s + 1, min(e, s + 12)):
        cells = [c.strip() for c in lines[i].split(' | ')]
        ys = [year_of(c) for c in cells]
        if cells and all(ys) and all(len(re.sub(r'[^0-9]', '', c)) <= 6 or ',' in c for c in cells) and not any(num(c) not in (None,) and year_of(c) is None for c in cells):
            if all(re.fullmatch(r'\s*((January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*)?(19|20)\d\d\s*(\(\d\)|\*)?\s*', c) for c in cells):
                return i, ys
    return None, None

def table(lines, s, e, cy, bs=False):
    """rows of one table -> list of (label, {col: value}); col keys: cur3/py3/cury/pyy (flows) or cur/prior (balance sheet)."""
    hi, ys = header(lines, s, e)
    if hi is None: return None, []
    if len(ys) == 2 and bs:
        cols = ['cur' if y == max(ys) else 'prior' for y in ys]
    elif len(ys) == 2:                                               # Q1 releases: three months only (= year to date)
        cols = ['cur3' if y == cy else 'py3' for y in ys]
    else:
        n = len(ys) // 2
        cols = [('cur' if y == cy else 'py') + ('3' if j < n else 'y') for j, y in enumerate(ys)]
    rows = []
    for l in lines[hi + 1:e]:
        cells = [c.strip() for c in l.split(' | ')]
        if len(cells) < 2:
            rows.append((cells[0], {})); continue
        lab = cells[0]; vals = [num(c) for c in cells[1:]]
        if any(v is None for v in vals):
            rows.append((lab, {})); continue
        d = {}
        if len(vals) == len(cols): d = dict(zip(cols, vals))
        elif len(vals) == len(cols) // 2 and len(cols) == 4:          # current-period-only rows (FX effect, ex-FX revenue)
            d = {'cur3': vals[0], 'cury': vals[1]}
        elif len(vals) == 1: d = {cols[0]: vals[0]}
        rows.append((lab, d))
    return ys, rows

KPI = [('dau', r'(?:Daily active users|DAUs)[^.]*?were\s+([\d.,]+)\s+(billion|million)'),
       ('mau', r'(?:Monthly active users|MAUs)[^.]*?were\s+([\d.,]+)\s+(billion|million)'),
       ('dap', r'DAP was\s+([\d.,]+)\s+(billion|million)'),
       ('map', r'MAP was\s+([\d.,]+)\s+(billion|million)'),
       ('mobile_dau', r'Mobile DAUs[^.]*?were\s+([\d.,]+)\s+(billion|million)'),
       ('headcount', r'Headcount[^.]*?was\s+([\d,]+)\s+as of'),
       ]
def kpis(text):
    t = re.sub(r'\s+', ' ', text)
    out = {}
    for k, rx in KPI:
        m = re.search(rx, t, re.I)
        if m:
            v = float(m.group(1).replace(',', ''))
            if len(m.groups()) > 1: v = v * (1000 if m.group(2).lower() == 'billion' else 1)   # millions of people
            out[k] = v
    for k, w in (('impr_g', r'ad impressions(?: delivered across our Family of Apps)?\s+(increased|decreased) by\s+(\d+)%'),
                 ('price_g', r'(?:average )?price per ad\s+(increased|decreased) by\s+(\d+)%')):
        ms = list(re.finditer(w, t, re.I))
        if ms: out[k] = (1 if ms[0].group(1).lower() == 'increased' else -1) * float(ms[0].group(2)) / 100
        fy = re.search(r'For the full year \d{4},(.{0,300})', t)
        if fy:
            m = re.search(w, fy.group(1), re.I)
            if m: out[k + '_fy'] = (1 if m.group(1).lower() == 'increased' else -1) * float(m.group(2)) / 100
    return out

def parse(text, cy):
    lines = text.split('\n')
    out = {'is': [], 'bs': [], 'cf': [], 'seg': [], 'rec': [], 'hdr': {}}
    for k, s, e in sections(lines):
        ys, rows = table(lines, s, e, cy, bs=(k == 'bs'))
        if rows:
            out[k].extend(rows); out['hdr'].setdefault(k, ys)
    out['kpi'] = kpis(text)
    return out

def find(rows, rx, col, nth=0, after=None):
    """value in column col of the nth row whose label matches rx (optionally only after a row matching `after`)."""
    r = re.compile(rx, re.I); k = 0; on = after is None
    a = re.compile(after, re.I) if after else None
    for lab, d in rows:
        if not on:
            if a.search(lab): on = True
            continue
        if r.search(lab) and col in d:
            if k == nth: return d[col]
            k += 1
    return None
