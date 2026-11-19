"""Parse a General Dynamics earnings release (8-K Item 2.02, Ex. 99.1) from its text version ($GD_SRC/txt, one table row per line,
cells joined by ' | ') into typed tables with resolved columns.

Every release since 2006 prints the same family of exhibits (statement of earnings, revenue / operating earnings by segment, balance
sheet, cash flows, backlog, aircraft deliveries, financial information / non-GAAP free cash flow, and in Q4-2012 / 2013 the adjusted
non-GAAP earnings calculation), but titles, column order (2011 | 2012 in the FY2012 release), and layouts vary by era, so tables are
identified by their title line or content and each value column is resolved from the header lines to (months, 'cur' | 'py').
Values: '(1,234' / '(1,234)' -> -1234; '—' / '-' -> 0.0; footnote markers (') *', '(g)') are dropped. Amounts stay in the release
units (USD millions; per share in $; shares in millions, or units for the pre-2010 "Financial Information" exhibit)."""
import re

TITLES = [
    ('is', r'CONSOLIDATED STATEMENTS? OF (EARNINGS|INCOME)'),
    ('seg', r'(NET SALES|REVENUES?) AND OPERATING EARNINGS BY SEGMENT'),
    ('bs', r'CONSOLIDATED BALANCE SHEET'),
    ('cf', r'CONSOLIDATED STATEMENTS? OF CASH FLOWS'),
    ('backlog', r'^\s*BACKLOG\b'),
    ('deliv', r'AIRCRAFT DELIVERIES|SUPPLEMENTAL AEROSPACE'),
    ('fin', r'FINANCIAL INFORMATION|NON-GAAP FINANCIAL MEASURES?|ADDITIONAL FINANCIAL'),
    ('adj', r'CALCULATION OF ADJUSTED NON-GAAP|ADJUSTED NON-GAAP|NON-GAAP .*EARNINGS'),
    ('disc', r'^\s*DISCONTINUED OPERATIONS'),
    ('orders', r'SIGNIFICANT ORDERS'),
]
EXHIBIT = re.compile(r'^\s*(EXHIBIT|Exhibit)\s+[A-Z](-\d)?(\s*\(cont|\s*$)')
NUMTOK = re.compile(r'^\(?-?\$?\s*[\d,]*\.?\d+\)?%?$')

def pnum(tok):
    t = tok.strip().replace('$', '').replace('\xa0', ' ').strip()
    if t in ('—', '–', '-', '―', '--'): return 0.0
    if t.endswith('%'): t = t[:-1]
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '').strip()
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def is_junk(tok):
    t = tok.strip()
    return t in (')', '*', ') *', ')*', '%', ')%') or re.fullmatch(r'\)?\s*\(?[a-z]\)?\s*\*?', t) is not None or re.fullmatch(r'\)\s*\([a-z]\)', t) is not None

def split_row(line):
    """-> (label, [values]) for a table row, else None. Label-less numeric rows return ('', values)."""
    if ' | ' not in line: return None
    cells = [c.strip() for c in line.split(' | ')]
    cells = [c for c in cells if c and not is_junk(c)]
    if not cells: return None
    if pnum(cells[0]) is not None and not re.search(r'[A-Za-z]', cells[0]):
        vals = [pnum(c) for c in cells]
        return ('', vals) if all(v is not None for v in vals) else None
    vals = [pnum(c) for c in cells[1:]]
    if not vals or any(v is None for v in vals): return None
    return (cells[0], vals)

def blocks(txt):
    """split the text into exhibit blocks: [{'type', 'title', 'hdr': [...], 'rows': [(label, vals)]}]"""
    out, cur = [], None
    def new(ty, title):
        nonlocal cur
        cur = {'type': ty, 'title': title, 'hdr': [], 'rows': []}; out.append(cur)
    lines = txt.splitlines()
    recent = []                                   # last non-row lines (header of an untitled statement in the narrative)
    for ln in lines:
        s = ln.strip()
        if not s or s in ('– more –', '- more -', '– more', '–') or s.startswith('– more'): continue
        if EXHIBIT.match(s):
            new(None, s); continue
        up = s.upper()
        ty = next((t for t, p in TITLES if re.search(p, up)), None)
        row = split_row(s)
        if ty and row is None and (cur is None or cur['type'] is None or cur['rows'] or cur['type'] != ty):
            if cur is not None and cur['type'] is None and not cur['rows']:
                cur['type'], cur['title'] = ty, s
            else:
                new(ty, s)
            continue
        if row is None:
            recent = (recent + [s])[-4:]
            if cur is not None:
                # an untitled income statement (Q1-2007 narrative) or in-table sub-heading
                if cur['rows']: cur['rows'].append((s, []))
                else: cur['hdr'].append(s)
            continue
        lab, vals = row
        if lab == '' and all(v == int(v) and 1990 <= v <= 2035 for v in vals):
            yl = ' | '.join(str(int(v)) for v in vals)
            recent = (recent + [yl])[-4:]
            if cur is None or not cur['rows']:
                if cur is None: new(None, 'untitled')
                cur['hdr'].append(yl)                     # a year header line ("2011 | 2012")
            else:                                        # a second column block inside the same exhibit (e.g. the free-cash-flow table)
                ty, title = cur['type'], cur['title'] + ' (cont.)'
                new(ty, title); cur['hdr'].append(yl)
            continue
        if cur is None or (cur['type'] is None and re.match(r'^(NET SALES|REVENUES?)$', lab.strip(' :').upper())):
            new('is', 'untitled statement of earnings'); cur['hdr'] = [h for h in recent if re.search(r'20\d\d|Quarter|Months', h)]
        if cur['type'] is None and cur['rows'] == [] and re.match(r'^(NET SALES|REVENUES?)$', lab.strip(' :').upper()):
            cur['type'] = 'is'
        cur['rows'].append((lab, vals))
    return [b for b in out if b['rows'] and b['type']]

MONTHS = [(r'FIRST QUARTER|SECOND QUARTER|THIRD QUARTER|FOURTH QUARTER|THREE MONTHS|\bQUARTER\b', 3), (r'SIX MONTHS', 6), (r'NINE MONTHS', 9),
          (r'TWELVE MONTHS|YEAR ENDED|FULL YEAR|YEAR-TO-DATE|TWELVE-MONTH', 12)]
DATE = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(20\d\d)')

def header_cols(b, ytd_months=None):
    """resolve value columns of a block -> list of (months, 'cur'|'py') or None (one entry per value column).
    ytd_months: months in the release's year-to-date period (for 'Year-to-date' labels and balance-sheet / cash-flow tables)."""
    hdr = [h for h in b['hdr'] if ' | ' in h or re.search(r'20\d\d|Quarter|Months|Year', h)]
    # years per column
    ytoks = []
    for h in hdr:
        cells = [re.sub(r'\s*(\([a-z]\)|\*)+\s*$', '', c.replace('\xa0', ' ').strip()) for c in h.split(' | ')]
        ys = []
        for c in cells:
            m = DATE.search(c)
            if m: ys.append(int(m.group(2))); continue
            m2 = re.fullmatch(r'.*?(20\d\d)\s*$', c)
            if m2 and not re.search(r'\d{1,2}, 20\d\d', c): ys.append(int(m2.group(1)))
        if len(ys) >= 2 and len(ys) > len(ytoks): ytoks = ys
    ptoks = []
    for h in hdr:
        cells = [c.replace('\xa0', ' ').strip() for c in h.split(' | ')]
        ps = []
        for c in cells:
            U = c.upper()
            if re.search(r'VARIANCE', U): continue
            mo = next((mth for p, mth in MONTHS if re.search(p, U)), None)
            if mo is not None: ps.append(mo)
        if ps and len(ps) >= len(ptoks): ptoks = ps
    n = max(len(v) for _, v in b['rows'])
    if not ytoks: return None
    def spread(toks, n):
        if len(toks) >= n: return toks[:n]
        k = n // len(toks) if n % len(toks) == 0 else None
        if k is None: return toks + [toks[-1]] * (n - len(toks))
        return [t for t in toks for _ in range(k)]
    nvals = min(n, max(len(ytoks), len(ptoks)))
    ys = spread(ytoks, nvals) if nvals > len(ytoks) else ytoks[:nvals]
    ps = spread(ptoks, nvals) if ptoks else [None] * nvals
    ymax = max(ys)
    cols = []
    for i in range(nvals):
        mo = ps[i]
        if mo == 12 and ytd_months and any('YEAR-TO-DATE' in h.upper() for h in hdr): mo = ytd_months
        cols.append((mo, 'cur' if ys[i] == ymax else 'py'))
    return cols

def parse(txt, ytd_months=None):
    """typed tables with resolved columns. A sub-table without its own year / period header (e.g. 'Non-GAAP Financial Measures:' or
    'Gulfstream Aircraft Deliveries (units):' under a 'Third Quarter | Nine Months' header) inherits the preceding table's header."""
    res, prev_hdr = [], []
    for b in blocks(txt):
        cols = header_cols(b, ytd_months)
        if cols is None and prev_hdr:
            b2 = dict(b, hdr=prev_hdr + b['hdr'])
            cols = header_cols(b2, ytd_months)
            if cols: b['hdr'] = b2['hdr']; b['inherited'] = True
        if cols and not b.get('inherited'): prev_hdr = [h for h in b['hdr'] if ' | ' in h or re.search(r'20\d\d|Quarter|Months', h)]
        b['cols'] = cols
        res.append(b)
    return res

def rows_of(tabs, ty):
    for t in tabs:
        if t['type'] == ty: yield t

def find(tabs, ty, label_re, months=None, cp='cur', exclude=None, nth=0):
    """value of the first row matching label_re in tables of type ty, in the column (months, cp)."""
    hits = 0
    for t in rows_of(tabs, ty):
        if not t['cols']: continue
        idx = [i for i, c in enumerate(t['cols']) if (months is None or c[0] == months) and c[1] == cp]
        if not idx: continue
        for lab, vals in t['rows']:
            if not vals: continue
            if re.search(label_re, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
                if hits == nth:
                    i = idx[0]
                    return vals[i] if i < len(vals) else None
                hits += 1
    return None
