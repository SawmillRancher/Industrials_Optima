"""Parse a Lockheed Martin earnings release (8-K Item 2.02, Ex. 99.1 HTML) into typed tables with resolved columns.

Every release since the FY2006 fourth-quarter release (Jan-2007) prints the same family of schedules: consolidated statement(s) of
earnings, business segment net sales / operating profit / margins (with the unallocated items), selected financial data (unallocated
corporate items to 2012; FAS/CAS pension detail from 2013), consolidated balance sheet, consolidated statement of cash flows and the
operating data (backlog by segment, aircraft deliveries). Titles, layouts and column order vary by era, so tables are identified by
their contents and each value column is resolved from the header rows to (months, 'cur' | 'py', measure): months 3 / 6 / 9 / 12
(0 = balance-sheet instant); 'cur' = the later of the two years in each block; measure 'v' (value) or 'pct' (% change column).

Values: '(1,234' / '(1,234)' -> -1234; '-', '—', '–' -> 0.0; 'N/M' is dropped. Amounts stay in the release units (USD millions;
per share in $; shares in millions).
"""
import re
from bs4 import BeautifulSoup

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace(' ', '').strip()
    if t in ('—', '–', '-', '―', '--', '— —', '— %', '-%'): return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', ' ')).strip()

def compact(lab):
    """label -> lower-case letters / digits / '&' only ('Total business segment operating profit 1' -> 'totalbusinesssegmentoperatingprofit1')."""
    return re.sub(r'[^a-z0-9&/]', '', lab.lower())

DROP = {'', '$', ')', '(', '%', ')%', ') %', 'N/M', 'NM', 'n/m', 'N/A', 'n/a', 'NA'}

# ------------------------------------------------------------------ raw tables
def html_tables(html):
    """-> list of raw tables: [{'hdr': [header text rows], 'rows': [(label, [values])], 'pre': text before the table}]"""
    soup = BeautifulSoup(html, 'lxml')
    out = []
    TITLE = re.compile(r'consolidated\s+(condensed\s+)?(statements?|balance)|segment|selected\s+financial|operating data|other financial|backlog|summary financial', re.I)
    for t in soup.find_all('table'):
        prev = t.find_previous(string=re.compile(r'\S'))
        cur = {'hdr': [], 'rows': [], 'pre': _clean(prev) if prev else ''}
        tabs = [cur]
        for tr in t.find_all('tr'):
            cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c not in DROP]
            if not cells: continue
            vals = [pnum(c) for c in cells[1:]]
            isyear = bool(vals) and all(v is not None and v == int(v) and 1990 <= v <= 2035 for v in vals) and ',' not in ''.join(cells[1:])
            if len(cells) >= 2 and all(v is not None for v in vals) and pnum(cells[0]) is None and not isyear:
                cur['rows'].append((cells[0], vals))
            elif len(cells) == 1 and TITLE.search(cells[0]) and cur['rows']:
                cur = {'hdr': [cells[0]], 'rows': [], 'pre': cells[0]}; tabs.append(cur)      # several schedules in one <table>
            elif not cur['rows']:
                cur['hdr'].append(' | '.join(cells))
            else:
                cur['rows'].append((' | '.join(cells), []))       # in-table sub-heading (or an unlabelled numeric row)
        out.extend(x for x in tabs if x['rows'])
    return out

# ------------------------------------------------------------------ column resolution
PER = re.compile(r'quarters? and years? ended|quarters? ended|three months ended|six months ended|nine months ended|twelve months ended|years? ended|year to date')

def columns(t):
    """resolve value columns -> [(months, 'cur'|'py'|None, 'v'|'pct')], or None if the table cannot be resolved."""
    h = ' | '.join(t['hdr'] + [l for l, v in t['rows'][:3] if not v])
    hl = h.lower()
    n = max((len(v) for _, v in t['rows']), default=0)
    if not n or n > 8: return None
    if 'outlook' in hl:
        m = re.search(r'(20\d\d)\s*outlook\s*\|\s*(20\d\d)\s*actual', hl)
        return [(12, 'out', 'v'), (12, 'cur', 'v')] if (m and n == 2) else None
    if 'historical' in hl or 'adjustments for' in hl: return None
    kinds = []
    for m in PER.finditer(hl):
        s = m.group(0)
        if 'quarter' in s and 'year' in s: kinds += [3, 12]
        elif 'quarter' in s or 'three' in s: kinds.append(3)
        elif 'six' in s: kinds.append(6)
        elif 'nine' in s: kinds.append(9)
        else: kinds.append(12)
    npct = len(re.findall(r'%\s*change', hl))
    if not kinds:
        if n <= 2 or 'backlog' in hl: return [(0, 'cur', 'v'), (0, 'py', 'v')]
        return None
    cols = []
    for k in kinds:
        cols += [(k, 'cur', 'v'), (k, 'py', 'v')] + ([(k, None, 'pct')] if npct else [])
    return cols

def align(vals, cols):
    """map a row's values to column indices (rows may omit the % change cells or trail off)."""
    n = len(cols)
    if len(vals) == n: return dict(enumerate(vals))
    nonpct = [i for i, c in enumerate(cols) if c[2] != 'pct']
    if len(vals) == len(nonpct): return dict(zip(nonpct, vals))
    pct = [i for i in range(n) if cols[i][2] == 'pct']
    if pct and len(vals) == n - 1:
        # one % change cell is missing (printed as N/M): pick the assignment whose % slots hold small integers
        def plausible(skip):
            idx = [i for i in range(n) if i != skip]
            d = dict(zip(idx, vals))
            return all(abs(d[i]) <= 999 and d[i] == int(d[i]) for i in pct if i in d)
        for skip in reversed(pct):
            if plausible(skip):
                idx = [i for i in range(n) if i != skip]
                return dict(zip(idx, vals))
        idx = [i for i in range(n) if i != pct[-1]]
        return dict(zip(idx, vals))
    if len(vals) < len(nonpct): return dict(zip(nonpct, vals))
    return dict(enumerate(vals[:n]))

# ------------------------------------------------------------------ typed tables
SEGNAMES = r'aeronautics|electronicsystems|spacesystems|missiles|missionsystems|rotary'

def ttype(t):
    labs = ' || '.join(compact(l) for l, _ in t['rows'])
    hdr = compact(' '.join(t['hdr']) + ' ' + t['pre'])
    if 'totalassets' in labs: return 'bs'
    if 'netcashprovidedbyoperatingactivities' in labs or 'cashandcashequivalentsatend' in labs or 'netchangeincash' in labs or 'netcashusedforinvesting' in labs: return 'cf'
    if 'balanceat' in labs: return 'eq'
    if 'proforma' in hdr and re.search(SEGNAMES, labs): return 'segpf'
    if 'backlog' in hdr + labs and re.search(SEGNAMES, labs) and 'operatingprofit' not in labs: return 'backlog'
    if re.search(r'f35|f16|f22|c130j|c5|helicopter', labs) and ('deliver' in hdr or 'deliveries' in labs): return 'deliv'
    if re.search(r'^(net)?sales', labs) and 'operatingprofit' in labs and 'netearnings' in labs and re.search(r'costofsales|operatingcostsandexpenses|grossprofit', labs): return 'is'
    if re.search(r'^(net)?sales', labs) and not re.search(SEGNAMES, labs) and re.search(r'segmentoperatingprofit|netearnings|freecashflow', labs): return 'summary'
    if re.search(SEGNAMES, labs) and 'operatingprofit' in labs + hdr: return 'seg'
    if re.search(r'faspensionexpense|caspensioncost|casexpense|faspensionservicecost|fas/cas', labs): return 'pension'
    if 'unallocated' in labs and re.search(r'stock|severance|other|unusual|pension', labs): return 'unalloc'
    if 'businesssegmentoperatingprofit' in labs or 'segmentoperatingprofit' in labs or 'freecashflow' in labs: return 'summary'
    return None

def parse(html):
    """-> list of typed tables: {'type', 'cols', 'rows': [(label, compact, {col index: value})], 'hdr', 'pre'}"""
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if not ty or ty == 'eq': continue
        cols = columns(t)
        if not cols: continue
        rows = [(l, compact(l), align(v, cols) if v else {}) for l, v in t['rows']]
        res.append({'type': ty, 'cols': cols, 'rows': rows, 'hdr': t['hdr'], 'pre': t['pre']})
    return res

def colidx(t, months, cp):
    for i, c in enumerate(t['cols']):
        if c[0] == months and c[1] == cp and c[2] == 'v': return i
    return None

def tables_with(tabs, ty, months, cp):
    return [t for t in tabs if t['type'] == ty and colidx(t, months, cp) is not None]

def get(tabs, ty, label_re, months, cp='cur', nth=0, exclude=None):
    """first matching row value (compact-label regex) in tables of type ty for column (months, cp)."""
    hits = 0
    for t in tabs:
        if t['type'] != ty: continue
        ci = colidx(t, months, cp)
        if ci is None: continue
        for lab, cl, vals in t['rows']:
            if not vals: continue
            if re.search(label_re, cl) and not (exclude and re.search(exclude, cl)):
                if hits == nth: return vals.get(ci)
                hits += 1
    return None
