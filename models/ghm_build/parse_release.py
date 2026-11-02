"""Parse a Graham Corporation earnings release (8-K Item 2.02, Ex. 99.1 HTML) or supplemental exhibit (Ex. 99.2) into typed
tables with resolved columns.

Graham's releases (Kei Advisors / Alliance Advisors format since FY2006) carry the same schedules in every era: statement of
operations, balance sheet, cash flows (year to date), an orders & backlog trend grid, sales by industry / region grids, and
from FY2011 EBITDA reconciliations, from FY2018 adjusted net income / adjusted operating profit reconciliations and from FY2022
the current adjusted EBITDA / adjusted net income tables. Statements are in USD thousands and carry "% Change" columns; the
grids are in USD millions (one decimal) in the release body through FY2022 and in USD thousands in the Ex. 99.2 exhibits
from FY2023.

Cells are placed by their grid column (colspan-aware), so rows that leave cells blank (no change figure, dashes dropped by
the typesetter) stay aligned with the header. Tables are identified by their contents, and each value column is resolved
from the header tokens above it to (months, 'cur' | 'py' | 'py2', measure): months 3 / 6 / 9 / 12 (0 = balance-sheet
instant); 'cur' = the later year of a block; measure 'v' (value), 'ps' (per share) or None (change / percent-of-total
column, ignored). Grids resolve to (fiscal year, quarter 1-4 or 'FY').
Values: '(1,234' / '(1,234)' -> -1234; '—', '–', '-' -> 0.0; 'NA' / 'N/A' / 'NM' / 'bps' cells -> None placeholders.
Amounts stay in the document units; `unit(t, type, ref)` reports 'k' or 'm' per table.
"""
import re
from bs4 import BeautifulSoup

DROP = {'', '$', ')', '%', ')%', '%)', '(', '$)', ')$', '*', '**', '|', '#', '†'}
NAV = re.compile(r'^(n/?a|nm|n/m|n\.m\.|\*+)$', re.I)
DASH = {'—', '–', '-', '―', '--', '— —', '−'}

def pnum(tok):
    t = tok.strip().replace('$', '').replace('​', '').replace('\xa0', ' ').strip()
    if t in DASH: return 0.0
    t = t.replace(' ', '')
    neg = t.startswith('(') or t.startswith('-') or t.startswith('−')
    t = t.strip('()-−').replace(',', '').rstrip('%')
    if t.endswith('x'): t = t[:-1]
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', ' ')).strip()

def _tok(cell):
    """-> ('num', value) | ('none', None) placeholder | ('text', str) | None (symbol / empty)"""
    c = cell.strip()
    if c in DROP: return None
    if NAV.match(c) or re.fullmatch(r'[+-]?\d[\d,]*\.?\d*\s*(bps|pts)', c, re.I): return ('none', None)
    v = pnum(c)
    if v is not None and not re.fullmatch(r'\d{1,2}/\d{1,2}/\d{2,4}', c): return ('num', v)
    return ('text', _clean(c))

YEAR = re.compile(r'^(20\d\d)$')
DTOK = re.compile(r'^(\d{1,2})/(\d{1,2})/+(\d{2,4})$')
def _fy(y):
    y = int(y); return y + 2000 if y < 100 else y
def ytok(x):
    x = x.strip()
    if YEAR.match(x): return int(x)
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$', x)
    if m: return _fy(m.group(3))
    return None

SECTION = re.compile(r'(sales|orders|backlog) by (market|region|industry)|book-to-bill|order & backlog', re.I)

# ------------------------------------------------------------------ raw tables (grid positions)
def _grid_rows(table):
    """-> list of rows; each row = list of (col, span, text) for non-empty cells."""
    rows = []
    for tr in table.find_all('tr'):
        col, cells = 0, []
        for td in tr.find_all(['td', 'th']):
            try: span = int(td.get('colspan', 1) or 1)
            except ValueError: span = 1
            txt = _clean(td.get_text(' ', strip=True))
            if txt: cells.append((col, span, txt))
            col += span
        rows.append(cells)
    return rows

def _finish(cur):
    """align data rows and header rows on the numeric grid columns."""
    pos = sorted({c for r in cur['data'] for c, k, v in r['cells'] if k in ('num', 'none')})
    if not pos: return None
    def place(cells):
        vals = [None] * len(pos)
        for c, k, v in cells:
            if k not in ('num', 'none'): continue
            if c in pos: vals[pos.index(c)] = v
            else:
                j = next((i for i, p in enumerate(pos) if p >= c), None)
                if j is not None and vals[j] is None: vals[j] = v
        return vals
    rows = [(r['label'], place(r['cells'])) if r['cells'] else (r['label'], []) for r in cur['data']]
    hdr = []
    for h in cur['hdr']:
        line = [''] * len(pos)
        for c, span, txt in h:
            cov = [i for i, p in enumerate(pos) if c <= p < c + span]
            if not cov:                          # header cell ends on the '$' column just before the figure
                cov = [i for i, p in enumerate(pos) if c + span <= p <= c + span + 1][:1]
            for i in cov:
                if not line[i]: line[i] = txt
        hdr.append(line)
    hdr_text = ' | '.join(' | '.join(t for _, _, t in h) for h in cur['hdr'])
    return {'hdr': hdr, 'hdr_text': hdr_text, 'rows': rows, 'pre': cur['pre'], 'pos': pos}

def _hstr(k, v):
    if k == 'num': return str(int(v)) if v == int(v) else str(v)
    return v or ''

def html_tables(html):
    """-> list of raw tables: {'hdr': [per-column header tokens], 'hdr_text', 'rows': [(label, [values])], 'pre', 'pos'}"""
    soup = BeautifulSoup(html, 'lxml')
    out = []
    for t in soup.find_all('table'):
        if t.find('table'): continue
        prev = t.find_previous(string=re.compile(r'\S'))
        cur = {'hdr': [], 'data': [], 'pre': _clean(prev) if prev else ''}
        tabs = [cur]
        for cells in _grid_rows(t):
            toks = [(c, span, _tok(txt)) for c, span, txt in cells]
            toks = [(c, span, x) for c, span, x in toks if x is not None]
            if not toks: continue
            first = toks[0][2]
            rest = toks[1:]
            nnum = sum(1 for _, _, (k, v) in rest if k == 'num')
            yr_cells = rest if first[0] == 'text' else toks
            allyears = bool(yr_cells) and all(k == 'num' and v == int(v) and 1990 <= v <= 2040 for _, _, (k, v) in yr_cells) and \
                       not any(',' in txt for _, _, txt in cells)
            if first[0] == 'text' and nnum >= 1 and all(k in ('num', 'none') for _, _, (k, v) in rest) and not (allyears and not cur['data']):
                cur['data'].append({'label': first[1], 'cells': [(c, k, v) for c, span, (k, v) in rest]})
            elif first[0] == 'text' and cur['data'] and SECTION.search(first[1]):
                cur = {'hdr': [[(c, span, _hstr(k, v)) for c, span, (k, v) in toks]], 'data': [], 'pre': first[1]}
                tabs.append(cur)
            else:
                hcells = [(c, span, _hstr(k, v)) for c, span, (k, v) in toks]
                if allyears and first[0] == 'text' and not cur['data']:
                    cur['hdr'].append([hcells[0]]); hcells = hcells[1:]
                if cur['data']:
                    cur['data'].append({'label': ' | '.join(x[2] for x in hcells), 'cells': []})
                else:
                    cur['hdr'].append(hcells)
        for x in tabs:
            if x['data']:
                f = _finish(x)
                if f: out.append(f)
    return out

def nvals(t): return len(t['pos'])

# ------------------------------------------------------------------ column resolution (statements / reconciliations)
KIND = [(r'three', 3), (r'six', 6), (r'nine', 9), (r'twelve', 12), (r'years? ended', 12), (r'fiscal years?', 12), (r'year ended', 12), (r'quarter ended', 3)]
KINDRE = re.compile(r'(three|six|nine|twelve)[\s\-]+months?|years? ended|fiscal years?:?|quarter ended', re.I)

def kind_of(txt):
    m = KINDRE.search(txt.lower())
    if not m: return None
    return next(k for p, k in KIND if re.search(p, m.group(0).lower()))

def columns(t, ty):
    n = nvals(t)
    if not n: return None
    if ty == 'bs':
        return [(0, 'cur', 'v'), (0, 'py', 'v')][:n] if n <= 2 else None
    toks = [[h[i] for h in t['hdr'] if h[i]] for i in range(n)]
    kinds, cur = [], None
    for i in range(n):
        k = next((kind_of(x) for x in toks[i] if kind_of(x)), None)
        if k: cur = k
        kinds.append(cur)
    if not any(kinds):
        ht = kind_of(t.get('hdr_text') or '')
        kinds = [ht] * n
    years = [next((ytok(x) for x in toks[i] if ytok(x) is not None), None) for i in range(n)]
    chg = [any(re.search(r'change|variance', x, re.I) or x.strip() in ('$', '%') for x in toks[i]) for i in range(n)]
    ps = [any(re.search(r'per (diluted )?share', x, re.I) for x in toks[i]) for i in range(n)]
    if not any(y is not None for y in years): return None
    cols, prev, prev_i = [], None, None
    for i in range(n):
        if chg[i] or years[i] is None:
            cols.append(None); continue
        y = years[i]
        if ps[i] and prev_i == i - 1 and years[prev_i] == y and cols[prev_i] and cols[prev_i][2] == 'v' and ps[prev_i]:
            cols.append((cols[prev_i][0], cols[prev_i][1], 'ps')); prev_i = i; continue
        if prev is None or y > prev or (prev_i is not None and kinds[i] != kinds[prev_i]): cp = 'cur'
        elif y == prev: cp = 'cur'
        else: cp = 'py' if cols[prev_i] and cols[prev_i][1] == 'cur' else 'py2'
        cols.append((kinds[i], cp, 'v')); prev, prev_i = y, i
    return cols

# ------------------------------------------------------------------ column resolution (period grids)
QTOK = re.compile(r'^Q\s?([1-4])\s*(FY)?\s*\'?(\d{2}|\d{4})$', re.I)
QTOK2 = re.compile(r'^([1-4])Q\s*(FY)?\s*(\d{2}|\d{4})$', re.I)
FYTOK = re.compile(r'^(FY|YTD\s*FY|YTD)\s?\'?(\d{2}|\d{4})$', re.I)
PCT = re.compile(r'^(%|% of|% of total|total|variance)$', re.I)

def grid_columns(t):
    n = nvals(t)
    if not n: return None
    toks = [[h[i] for h in t['hdr'] if h[i]] for i in range(n)]
    cols = []
    for i in range(n):
        parts = []
        for x in toks[i]:
            x = x.strip()
            if SECTION.search(x): continue
            if QTOK.match(x) or FYTOK.match(x) or QTOK2.match(x): parts.append(x)
            else: parts += x.replace(':', ' ').split()
        dq = dfy = fq = ffy = yr = None; ytd = False
        for x in parts:
            m = QTOK.match(x) or QTOK2.match(x)
            if m: dq, dfy = int(m.group(1)), _fy(m.group(3)); continue
            m = re.match(r'^Q([1-4])$', x, re.I) or re.match(r'^([1-4])Q$', x, re.I)
            if m: dq = dq or int(m.group(1)); continue
            m = DTOK.match(x)
            if m:
                mo, yy = int(m.group(1)), _fy(m.group(3))
                if mo == 3 and (ytd or fq == 'FY'): fq, ffy = 'FY', yy
                else: dq, dfy = {6: 1, 9: 2, 12: 3, 3: 4}.get(mo), yy + (1 if mo >= 4 else 0)
                continue
            m = FYTOK.match(x)
            if m: fq, ffy = 'FY', _fy(m.group(2)); continue
            if re.match(r'^ytd$', x, re.I): ytd = True; continue
            if YEAR.match(x): yr = int(x); continue
            if re.fullmatch(r'[0-3]\d', x) and (dq is not None or fq is not None) and yr is None: yr = 2000 + int(x); continue
            if re.match(r'^(FY|fiscal)$', x, re.I): fq = 'FY'; continue
        col = None
        if ytd and dq is not None and fq is None: col = None
        elif dq is not None:
            y_ = dfy or yr or ffy
            col = (y_, dq) if y_ else None
        elif fq == 'FY' and (ffy or yr): col = (ffy or yr, 'FY')
        elif ytd and yr: col = (yr, 'FY')
        elif yr and not any(re.search(r'variance|change', x, re.I) for x in toks[i]): col = (yr, 'FY')
        cols.append(col)
    for i in range(1, n):
        if cols[i] is not None and cols[i] == cols[i - 1] and any(PCT.match(x.strip()) for x in toks[i]): cols[i] = None
    last = None
    for i in range(n):
        if cols[i] is None: continue
        fy, q = cols[i]
        if last is not None and q == 1 and last[1] in (4, 'FY') and fy <= last[0]: fy = last[0] + 1; cols[i] = (fy, q)
        last = cols[i]
    return cols

# ------------------------------------------------------------------ typing
def labels(t): return ' || '.join(l.lower() for l, _ in t['rows'])
def ttype(t):
    labs = labels(t)
    hdr = ((t.get('hdr_text') or '') + ' ' + t['pre']).lower()
    first = next((l.lower() for l, v in t['rows'] if v), '')
    if re.search(r'cost of (products|goods) sold', labs) and labs.startswith('net sales'): return 'is'
    if labs.startswith('net sales') or (labs.startswith('adjusted ebitda') and 'depreciation' not in labs) or labs.startswith('ebitda'): return 'summary'
    if 'total assets' in labs and 'total liabilities' in labs: return 'bs'
    if 'operating activities' in labs or 'cash and cash equivalents at end' in labs or re.search(r'net cash.*operating', labs): return 'cf'
    if re.search(r'backlog by (market|industry)', hdr) and re.search(r'refining|defense|energy', labs): return 'backlog_mkt'
    if re.search(r'(^|\|\| )orders', labs) and 'backlog' in labs: return 'orders'
    if 'book-to-bill' in labs and 'orders' not in labs: return 'b2b'
    if re.search(r'refining|defense|energy & process|chemical', labs):
        if re.search(r'orders by', hdr): return 'orders_mkt'
        if re.search(r'backlog by', hdr): return 'backlog_mkt'
        return 'sales_mkt'
    if re.search(r'united states|middle east', labs):
        if re.search(r'orders by', hdr): return 'orders_reg'
        if re.search(r'backlog by', hdr): return 'backlog_reg'
        return 'sales_reg'
    if 'guidance' in hdr and ('net sales' in labs or 'gross margin' in labs): return 'guidance'
    if re.search(r'adjusted operating', labs) and first.startswith('operating'): return 'adjop'
    if 'ebitda' in labs: return 'ebitda'
    if re.search(r'adjusted net|normaliz|tax impact|income tax effect', labs) and first.startswith('net'): return 'adjni'
    if first.startswith('net') and 'depreciation' in labs: return 'ebitda'
    return None

def unit(t, ty, ref=None):
    """'k' or 'm'. Grids: by magnitude or header text; reconciliations: by matching the first row to a reference value (USD k)."""
    hdr = ((t.get('hdr_text') or '') + ' ' + t['pre']).lower()
    if 'in thousands' in hdr: return 'k'
    if 'in millions' in hdr: return 'm'
    vals = [abs(v) for _, vs in t['rows'] for v in vs if isinstance(v, (int, float))]
    if ty in ('is', 'bs', 'cf'): return 'k'
    if ref is not None:
        fv = next((v for _, vs in t['rows'] if vs for v in vs if v is not None), None)
        if fv is not None and abs(ref) > 0:
            if abs(fv - ref) <= max(1.0, 0.002 * abs(ref)): return 'k'
            if abs(fv * 1000 - ref) <= max(60.0, 0.01 * abs(ref)): return 'm'
    return 'k' if vals and max(vals) >= 2000 else 'm'

GRIDS = ('orders', 'b2b', 'orders_mkt', 'backlog_mkt', 'sales_mkt', 'orders_reg', 'backlog_reg', 'sales_reg')

def parse(html):
    """-> list of typed tables: {'type', 'cols', 'rows', 'hdr', 'pre', 'raw'}"""
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if not ty: continue
        if ty in GRIDS: cols = grid_columns(t)
        elif ty == 'guidance': cols = None
        else: cols = columns(t, ty)
        res.append({'type': ty, 'cols': cols, 'rows': t['rows'], 'hdr': t['hdr'], 'pre': t['pre'], 'raw': t})
    return res

def get(tables, ty, label_re, months, cp='cur', meas='v', nth=0, exclude=None):
    hits = 0
    for t in tables:
        if t['type'] != ty or not t['cols']: continue
        idx = [i for i, c in enumerate(t['cols']) if c and c[0] == months and c[1] == cp and c[2] == meas]
        if not idx: continue
        for lab, vals in t['rows']:
            if not vals: continue
            if re.search(label_re, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
                if hits == nth:
                    i = idx[0]
                    return vals[i] if i < len(vals) else None
                hits += 1
    return None
