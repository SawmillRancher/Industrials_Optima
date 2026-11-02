"""Parse a Woodward earnings release (8-K Item 2.02, Ex. 99.1 HTML) into typed tables with resolved columns.

Every release since FY2011 prints the same family of schedules (statement of earnings, balance sheet, cash flows, segment net
sales and earnings, EBIT / EBITDA / free cash flow reconciliations, and from Q4 FY2018 the adjusted-earnings, adjusted nonsegment
and adjusted segment reconciliations), but titles, layouts and column order vary by era. Tables are therefore identified by
their contents (e.g. "Cost of goods sold" = statement of earnings) and each value column is resolved from the header rows to
(months, 'cur' | 'py', measure): months 3 / 6 / 9 / 12 (0 = balance-sheet instant); 'cur' = the later of the years in the
header; measure = 'pre' (before income tax), 'net' (net of tax), 'ps' (per share) or 'v' (single value).

The FY2012 and FY2013 fourth-quarter releases are fixed-width <pre> text; they are split into tables at each
"Woodward, Inc. and Subsidiaries" heading and columns are read from the whitespace-separated numbers.
Values: '(1,234' / '(1,234)' -> -1234; '-', '—', '–' -> 0.0. Amounts stay in the release units (thousands; per share in $).
"""
import re
from bs4 import BeautifulSoup

NUM = re.compile(r'^\(?-?\$?\s*\(?[\d,]*\.?\d+\)?%?$')

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace(' ', '').strip()
    if t in ('—', '–', '-', '―', '--', '— —'): return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', ' ')).strip()

# ------------------------------------------------------------------ raw tables
def html_tables(html):
    """-> list of raw tables: [{'hdr': [header text rows], 'rows': [(label, [values])], 'pre': text before the table}]"""
    soup = BeautifulSoup(html, 'lxml')
    out = []
    TITLE = re.compile(r'consolidated\s+(condensed\s+)?(statements?|balance)|reconciliation|segment net sales|calculation of', re.I)
    for t in soup.find_all('table'):
        prev = t.find_previous(string=re.compile(r'\S'))
        cur = {'hdr': [], 'rows': [], 'pre': _clean(prev) if prev else ''}
        tabs = [cur]
        for tr in t.find_all('tr'):
            cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c not in ('', '$', ')', '%', ')%')]
            if not cells: continue
            vals = [pnum(c) for c in cells[1:]]
            isyear = vals and all(v is not None and v == int(v) and 1990 <= v <= 2035 for v in vals) and ',' not in ''.join(cells[1:])
            if len(cells) >= 2 and all(v is not None for v in vals) and pnum(cells[0]) is None and not isyear:
                cur['rows'].append((cells[0], vals))
            elif len(cells) == 1 and TITLE.search(cells[0]) and cur['rows']:
                cur = {'hdr': [cells[0]], 'rows': [], 'pre': cells[0]}; tabs.append(cur)      # several schedules in one <table>
            elif not cur['rows']:
                cur['hdr'].append(' | '.join(cells))
            else:
                cur['rows'].append((' | '.join(cells), []))       # in-table sub-heading
        out.extend(x for x in tabs if x['rows'])
    if soup.find('pre') and not out:
        out = pre_tables('\n'.join(p.get_text() for p in soup.find_all('pre')))
    return out

def pre_tables(txt):
    """fixed-width statements -> raw tables (split at the 'Woodward, Inc. and Subsidiaries' headings)."""
    blocks = re.split(r'\n\s*Woodward, Inc\. and Subsidiaries\s*\n', '\n' + txt)
    out = []
    for b in blocks:
        hdr, rows, pend = [], [], ''
        for line in b.splitlines():
            if not line.strip() or re.fullmatch(r'[\s\-=]+', line): continue
            m = re.search(r'\s{2,}(\(?\$?\s*-?[\d,]*\.?\d+\)?%?|-)(\s|$)', line)
            lab = (line[:m.start()] if m else line).strip()
            nums = [pnum(x) for x in re.findall(r'\(?\$?\s*-?[\d,]*\.?\d+\)?%?|(?<=\s)-(?=\s|$)', line[m.start():])] if m else []
            nums = [x for x in nums if x is not None]
            if m and nums and not re.fullmatch(r'(20\d\d\s*)+', line.strip().split(')')[-1].strip() or 'x'):
                if lab and lab[0].islower() and pend: lab = pend + ' ' + lab
                elif not lab and pend: lab = pend
                rows.append((_clean(lab), nums)); pend = ''
            else:
                if rows: pend = (pend + ' ' + lab).strip() if pend and line.startswith('   ') else lab
                else: hdr.append(line.strip())
        if rows: out.append({'hdr': hdr, 'rows': rows, 'pre': hdr[0] if hdr else ''})
    return out

# ------------------------------------------------------------------ column resolution
KIND = [(r'three', 3), (r'six', 6), (r'nine', 9), (r'twelve', 12), (r'years? end', 12), (r'fiscal year', 12)]

def columns(t):
    """resolve value columns -> [(months, 'cur'|'py', measure)] or None if the table is not a thousands-based schedule."""
    h = ' | '.join(t['hdr'] + ([t['rows'][0][0]] if t['rows'] and not t['rows'][0][1] else []))
    hl = h.lower()
    if 'year over year' in hl: return None
    n = max((len(v) for _, v in t['rows']), default=0)
    if not n: return None
    kinds = []
    for m in re.finditer(r'(three|six|nine|twelve)[\s\-]+months?|years? end(ed|ing)|fiscal year end(ed|ing)', hl):
        s = m.group(0)
        kinds.append(next(k for p, k in KIND if re.match(p, s)))
    years = [int(y) for y in re.findall(r'(?<!\d)(20\d\d)(?!\d)', h)]
    meas = None
    if 'before income tax' in hl: meas = ['pre', 'net', 'ps']
    elif re.search(r'net earnings\s*\|\s*earnings\s*per share', hl) or ('earnings per share' in hl and 'net earnings' in hl and n % 2 == 0 and n <= 4):
        meas = ['net', 'ps']
    ymax = max(years) if years else None
    def cp(y): return 'cur' if (y is None or ymax is None or y == ymax) else 'py'
    if meas:
        m = len(meas); blocks = max(1, n // m)
        cols = []
        for b in range(blocks):
            k = kinds[b] if len(kinds) >= blocks else (kinds[0] if kinds else None)
            y = years[b] if len(years) >= blocks and len(years) <= blocks * 2 else (years[b] if len(years) > b else None)
            for mm in meas: cols.append((k, cp(y), mm))
        return cols
    if not kinds:       # balance sheet (instants): current period end first, prior fiscal year end second
        return [(0, 'cur', 'v'), (0, 'py', 'v')][:n]
    if len(years) >= n: ys = years[-n:]
    else: ys = [None] * n
    per = n // len(kinds) if len(kinds) and n % len(kinds) == 0 else n
    cols = []
    for i in range(n):
        k = kinds[min(i // per, len(kinds) - 1)] if kinds else None
        y = ys[i]
        if y is None: cps = 'cur' if i % 2 == 0 else 'py'
        else:
            blk = sorted({yy for j, yy in enumerate(ys) if j // per == i // per and yy is not None}, reverse=True)
            cps = ['cur', 'py', 'py2', 'py3'][min(blk.index(y), 3)]
        cols.append((k, cps, 'v'))
    return cols

# ------------------------------------------------------------------ typed tables
def ttype(t):
    labs = ' || '.join(l.lower() for l, _ in t['rows'])
    hdr = ' '.join(t['hdr']).lower() + ' ' + t['pre'].lower()
    first = [l.lower() for l, v in t['rows'] if v]
    if 'cost of goods sold' in labs and re.search(r'(^|\|\| )net sales', labs): return 'is'
    if 'total assets' in labs: return 'bs'
    if 'net change in cash' in labs or 'cash flows from investing' in labs or 'cash and cash equivalents at end' in labs: return 'cf'
    if 'total segment earnings' in labs or ('nonsegment expenses' in labs and re.search(r'(^|\|\| )aerospace', labs) and 'adjusted' not in labs): return 'seg'
    if 'asc 606' in hdr or 'asc 605' in hdr: return 'asc606'
    if 'adjusted income tax' in labs: return 'tax'
    if 'ebitda leverage' in labs or 'rolling twelve' in labs: return 'lev'
    if 'ebitda' in labs: return 'ebitda'
    if any(re.match(r'(adjusted )?ebit\b', l) for l in first): return 'ebit'
    if 'adjusted nonsegment' in labs: return 'nonseg'
    if re.search(r'adjusted (aerospace|industrial) segment', labs): return 'adjseg'
    if re.search(r'adjusted (net )?earnings', labs) or 'earnings (u.s. gaap)' in labs: return 'adj'
    if 'segment earnings' in labs and 'adjusted' in labs: return 'adjseg'
    if 'free cash flow' in labs or 'free cash inflow' in labs: return 'fcf'
    return None

def parse(html):
    """-> list of typed tables: {'type', 'cols', 'rows', 'hdr'}"""
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if not ty: continue
        cols = columns(t)
        if not cols: continue
        res.append({'type': ty, 'cols': cols, 'rows': t['rows'], 'hdr': t['hdr'], 'pre': t['pre']})
    return res

def get(tables, ty, label_re, months, cp='cur', meas='v', nth=0, exclude=None):
    """first matching row value in tables of type ty for column (months, cp, meas)."""
    hits = 0
    for t in tables:
        if t['type'] != ty: continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == months and c[1] == cp and c[2] == meas]
        if not idx: continue
        for lab, vals in t['rows']:
            if not vals: continue
            if re.search(label_re, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
                if hits == nth:
                    i = idx[0]
                    return vals[i] if i < len(vals) else None
                hits += 1
    return None
