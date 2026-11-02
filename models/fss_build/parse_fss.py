"""Parse Federal Signal EDGAR documents (10-K / 10-Q primary documents and the earnings-release exhibits attached to them) into typed
tables with resolved columns.

Tables are identified by their contents (e.g. "Cost of sales" = statement of operations; "Total assets" = balance sheet; "Orders" /
"Backlog" = group results) and each value column is resolved from the header rows to (months, 'cur' | 'py' | 'py2', 'chg'):
months 3 / 6 / 9 / 12 (0 = balance-sheet instant, 'ttm' = trailing twelve months); 'cur' = the latest year in the header block, 'py'
the year before, 'py2' two years before (10-K three-year statements); 'chg' marks the "Change" columns of the MD&A / release tables.
Values: '(1,234' / '(1,234)' -> -1234; '—' / '-' -> 0.0. Amounts stay in the document units (USD millions; per share in $).

Text quirks handled: the HTML-to-text split leaves ")" and "%)" as separate cells, so "(25,433" is negative and "%)" is dropped.
Rows with fewer value cells than the header has columns (blank cells in the 2006-2009 documents are not rendered) are kept with
their raw values; extract.py uses them only when the counts agree and otherwise records them for manual review.
"""
import re
from bs4 import BeautifulSoup

CPS = ['cur', 'py', 'py2', 'py3', 'py4', 'py5']
MONTHS = 'january|february|march|april|may|june|july|august|september|october|november|december'
DROP = {'', '$', ')', '%', ')%', '%)', '(', '$(', ')(', '—%', 'pts', 'bps'}

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace('\xa0', ' ').replace(' ', '').strip()
    if t in ('—', '–', '-', '―', '--', '— —', 'NM', 'n/m', 'N/M', 'nm'): return 0.0 if t not in ('NM', 'n/m', 'N/M', 'nm') else None
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', ' ')).strip()

# ------------------------------------------------------------------ raw tables
TITLE = re.compile(r'consolidated\s+(condensed\s+)?(statements?|balance)|reconciliation|group results|segment', re.I)

def html_tables(html):
    """-> list of raw tables: [{'hdr': [header text rows], 'rows': [(label, [values])], 'pre': text before the table}]"""
    soup = BeautifulSoup(html, 'lxml')
    for t in soup(['script', 'style']): t.decompose()
    out = []
    for t in soup.find_all('table'):
        prev = t.find_previous(string=re.compile(r'\S'))
        pre = _clean(prev) if prev else ''
        # walk back further for the sentence introducing the table (release group tables split the sentence over several text nodes)
        node = prev; steps = 0
        while node is not None and steps < 8 and len(pre) < 220 and not re.search(r'group|segment|consolidated|statements?|reconcil', pre, re.I):
            node = node.find_previous(string=re.compile(r'\S')); steps += 1
            if node is None: break
            if node.find_parent('table') is not None and node.find_parent('table') is not t:
                break
            pre = _clean(node) + ' ' + pre
        cur = {'hdr': [], 'rows': [], 'pre': pre}
        tabs = [cur]
        for tr in t.find_all('tr'):
            cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c not in DROP]
            if not cells: continue
            vals = [pnum(c) for c in cells[1:]]
            isyear = bool(vals) and all(v is not None and v == int(v) and 1990 <= v <= 2035 for v in vals) and ',' not in ''.join(cells[1:]) \
                and not re.search(r'\d\.\d', ''.join(cells[1:]))
            if len(cells) >= 2 and all(v is not None for v in vals) and pnum(cells[0]) is None and not isyear:
                cur['rows'].append((cells[0], vals))
            elif len(cells) == 1 and TITLE.search(cells[0]) and cur['rows']:
                cur = {'hdr': [cells[0]], 'rows': [], 'pre': cells[0]}; tabs.append(cur)
            elif not cur['rows']:
                cur['hdr'].append(' | '.join(cells))
            else:
                cur['rows'].append((' | '.join(cells), []))       # in-table sub-heading (e.g. "Fire Rescue Group:")
        out.extend(x for x in tabs if x['rows'])
    return out

# ------------------------------------------------------------------ column resolution
KIND = [(r'three[\s\-]+months|\bqtr\b|\bquarter\b|3 months', 3), (r'six[\s\-]+months|6 months|first half|half', 6), (r'nine[\s\-]+months|9 months', 9),
        (r'twelve[\s\-]+months|12 months|years? end|fiscal year|\bytd\b|year to date|full year|for the years', 12),
        (r'trailing twelve|ttm|last twelve', 'ttm')]
YEAR = re.compile(r'(?<!\d)(20\d\d)(?!\d)')
INST = re.compile(r'(' + MONTHS + r')\s+\d{1,2},?\s*(20\d\d)', re.I)

def _kind_of(text):
    tl = text.lower()
    for p, k in KIND:
        if re.search(p, tl): return k
    return None

def columns(t):
    """resolve value columns -> list of (months, cp, kind, year) or None if the table has no period columns.

    Column positions come from the header row that carries the year tokens ("2026 | 2025 | Change | 2026 | 2025 | Change"); period
    lengths come from the "Three / Nine Months Ended" row (or the sentence before the table in the 2010-2013 releases). Tokens with
    "change" or "vs." are change columns."""
    n = max((len(v) for _, v in t['rows']), default=0)
    if not n: return None
    hdr = list(t['hdr']) + ([t['rows'][0][0]] if t['rows'] and not t['rows'][0][1] else [])
    h = ' || '.join(hdr)
    hl = h.lower()
    def is_year(tok):
        tl = tok.lower().strip()
        return bool(re.fullmatch(r'(fy ?)?20\d\d\*?( ?\(\d\))?( ?\(unaudited\))?( ?\([a-z]\))?', tl) or
                    re.fullmatch(r'(' + MONTHS + r')\s+\d{1,2},?\s*20\d\d( ?\(unaudited\))?', tl))
    def is_chg(tok):
        tl = tok.lower()
        return bool(re.search(r'change|variance|\bvs\.?\b|better|worse', tl))
    # the row with the most year tokens defines the column order
    best, brow = 0, None
    for row in hdr:
        toks = [x.strip() for x in row.split('|') if x.strip()]
        ny = sum(1 for x in toks if is_year(x))
        if ny > best: best, brow = ny, toks
    kinds = []
    for row in hdr:
        for x in row.split('|'):
            k = _kind_of(x)
            if k is not None and not is_year(x): kinds.append(k)
    if not kinds:
        pl = t['pre'].lower()[-160:]
        m = re.search(r'(three|six|nine|twelve)[\s\-]+months?|year ended|years ended', pl)
        if m: kinds = [{'three': 3, 'six': 6, 'nine': 9, 'twelve': 12}.get(m.group(1), 12)]
    if brow is None:
        ys = YEAR.findall(h)
        if not ys: return None
        k = kinds[0] if kinds else (0 if re.search(r'december 31|as of', hl) else 12)
        return [(k, 'cur', 'v', int(ys[0]))]
    seq = []
    for x in brow:
        if is_chg(x): seq.append(('c', None))
        elif is_year(x): seq.append(('y', int(YEAR.search(x).group(1))))
    nchg = sum(1 for k, _ in seq if k == 'c')
    years = [y for k, y in seq if k == 'y']
    inst = any(re.fullmatch(r'(' + MONTHS + r')\s+\d{1,2},?\s*20\d\d.*', x.lower().strip()) for x in brow if is_year(x))
    if not kinds:
        if inst or (re.search(r'december 31|as of', hl) and 'ended' not in hl and len(set(years)) == len(years) and n <= 3):
            kinds = [0]
        else:
            kinds = [12]
    # change columns announced on another header row ("For the Years Ended | Change") go after each block of years
    if nchg == 0 and n > len(years) and re.search(r'change|\bvs\b', hl):
        nb = len(kinds) if len(years) % max(len(kinds), 1) == 0 else 1
        per = len(years) // nb
        seq2 = []
        for i in range(nb):
            seq2 += [('y', y) for y in years[i * per:(i + 1) * per]] + [('c', None)]
        seq = seq2[:n] if len(seq2) >= n else seq2
    nb = len(kinds) if len(kinds) and len(years) % len(kinds) == 0 else 1
    per = len(years) // nb
    cols, yi = [], 0
    for k, y in seq:
        if k == 'c': cols.append(('chg', 'chg', 'v', None))
        else:
            blk = min(yi // per, nb - 1); yi += 1
            cols.append((kinds[blk] if len(kinds) > blk else kinds[0], 'cur', 'v', y))
    # provisional cur / py by rank within each block (relabel() re-expresses them against the document year)
    out, yi = [], 0
    for c in cols:
        if c[3] is None: out.append(c); continue
        blk = min(yi // per, nb - 1); yi += 1
        ys = sorted({y for y in years[blk * per:(blk + 1) * per]}, reverse=True)
        out.append((c[0], CPS[min(ys.index(c[3]), len(CPS) - 1)], 'v', c[3]))
    return out

def relabel(tabs, docyear):
    """re-express each column's cur / py / py2 relative to the document's own fiscal year (a 10-K's MD&A '2024 vs 2023' table is then
    'py' / 'py2', not 'cur' / 'py')."""
    for t in tabs:
        if t.get('_rel') == docyear: continue
        t['cols'] = [(c[0], (CPS[docyear - c[3]] if c[3] is not None and 0 <= docyear - c[3] < len(CPS) else ('chg' if c[3] is None else 'other')), c[2], c[3])
                     for c in t['cols']]
        if t.get('year') is not None: t['cp'] = CPS[docyear - t['year']] if 0 <= docyear - t['year'] < len(CPS) else 'other'
        t['_rel'] = docyear
    return tabs

# ------------------------------------------------------------------ typed tables
GROUPS = [('ssg', r'safety and security|safety products'), ('frg', r'fire rescue'), ('esg', r'environmental (solutions|products)'),
          ('fst', r'federal signal technolog'), ('tool', r'\btool\b')]

def group_of(text):
    tl = text.lower()
    for k, p in GROUPS:
        if re.search(p, tl): return k
    return None

def ttype(t):
    labs = ' || '.join(l.lower() for l, _ in t['rows'])
    first = [l.lower() for l, v in t['rows'] if v]
    pre = t['pre'].lower()
    hdr = ' '.join(t['hdr']).lower()
    if 'total assets' in labs and 'total liabilities' in labs: return 'bs'
    if 'cost of sales' in labs and re.search(r'(^|\|\| )(net sales|sales|revenues)', labs): return 'is'
    if re.search(r'net cash (provided|used|\(used)', labs) and ('operating activities' in labs or 'investing' in labs) and 'ebitda' not in labs: return 'cf'
    if 'ebitda' in labs and 'total debt' in labs: return 'lev'
    if 'adjusted ebitda' in labs or ('ebitda' in labs and 'depreciation' in labs): return 'ebitda'
    if re.search(r'adjusted (net )?(income|earnings|diluted|eps)|, adjusted', labs) and re.search(r'income tax|tax expense|per share|continuing operations|net of tax', labs): return 'adjeps'
    if re.search(r'(^|\|\| )(total )?orders', labs) or re.search(r'(^|\|\| )backlog', labs): return 'grp'
    if re.search(r'(^|\|\| )(total )?net sales(\s*\(a\))?$', first[0] if first else '') and 'operating' in labs and 'corporate' in labs: return 'seg'
    if 'corporate' in labs and re.search(r'safety and security|environmental solutions', labs) and ('total net sales' in labs or 'operating income' in labs or 'operating (loss) income' in labs): return 'seg'
    if re.search(r'identifiable assets|total assets of continuing', labs) and 'environmental solutions' in labs: return 'segassets'
    if re.search(r'capital expenditures', hdr + ' ' + labs) and 'environmental solutions' in labs and 'total capital expenditures' in labs: return 'segcapex'
    if re.search(r'depreciation and amortization', hdr + ' ' + labs) and 'environmental solutions' in labs and re.search(r'total depreciation', labs): return 'segda'
    if re.search(r'restructuring', pre) and 'environmental solutions' in labs and 'corporate' in labs: return 'restr'
    if re.search(r'selected financial', pre) and 'net sales' in labs: return 'selected'
    return None

def parse(html):
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if not ty: continue
        cols = columns(t)
        if not cols: continue
        res.append({'type': ty, 'cols': cols, 'rows': t['rows'], 'hdr': t['hdr'], 'pre': t['pre'], 'grp': group_of(t['pre'] + ' ' + ' '.join(t['hdr']))})
    return res

def rowval(t, lab_re, months, cp, nth=0, exclude=None, section=None, strict=True):
    """value of the first row matching lab_re (within an in-table section matching `section`, if given) in column (months, cp)."""
    idx = [i for i, c in enumerate(t['cols']) if c[0] == months and c[1] == cp]
    if not idx: return None
    hits = 0; sec_ok = section is None
    for lab, vals in t['rows']:
        if not vals:
            if section is not None: sec_ok = bool(re.search(section, lab, re.I))
            continue
        if not sec_ok: continue
        if re.search(lab_re, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
            if hits == nth:
                if strict and len(vals) != len(t['cols']): return ('MISALIGNED', lab, vals)
                i = idx[0]
                return vals[i] if i < len(vals) else None
            hits += 1
    return None

def get(tables, ty, lab_re, months, cp, nth=0, exclude=None, grp=None, section=None, strict=True):
    for t in tables:
        if t['type'] != ty: continue
        if grp is not None and t.get('grp') != grp: continue
        v = rowval(t, lab_re, months, cp, nth, exclude, section, strict)
        if v is not None: return v
    return None
