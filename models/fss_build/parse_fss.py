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

def columns(t):
    """resolve value columns -> list of (months, cp, kind) or None if the table has no period columns."""
    n = max((len(v) for _, v in t['rows']), default=0)
    if not n: return None
    h = ' || '.join(t['hdr'] + ([t['rows'][0][0]] if t['rows'] and not t['rows'][0][1] else []))
    hl = h.lower()
    toks = [x.strip() for x in re.split(r'\s*\|\|?\s*', h) if x.strip()]
    kinds = []
    for tok in toks:
        tl = tok.lower()
        for p, k in KIND:
            if re.search(p, tl): kinds.append(k); break
    if not kinds and YEAR.search(h):
        # 2010-2013 releases: the period is in the sentence before the table ("...for the three month period ended December 31, 2010 and 2009")
        pl = t['pre'].lower()[-160:]
        m = re.search(r'(three|six|nine|twelve)[\s\-]+months?|year ended|years ended', pl)
        if m:
            kinds = [{'three': 3, 'six': 6, 'nine': 9, 'twelve': 12}.get(m.group(1), 12)]
    # instants (balance sheets): "June 30, 2014 | December 31, 2013" or "December 31, || 2010 | 2009"
    inst = INST.findall(h)
    cols = []
    seq = []           # sequence of ('y', year) / ('c',) value columns in header order
    for tok in toks:
        tl = tok.lower()
        if re.search(r'change|variance|\bvs\b|better', tl) and not YEAR.search(tok): seq.append(('c', None)); continue
        if re.fullmatch(r'(fy ?)?20\d\d( ?\(\d\))?( \(unaudited\))?( ?[a-z]\))?', tl) or INST.fullmatch(tok.rstrip(' (unaudited)')) or re.fullmatch(r'(' + MONTHS + r')\s+\d{1,2},?\s*20\d\d.*', tl):
            for m in YEAR.finditer(tok):
                seq.append(('y', int(m.group(1)))); break
    years = [y for k, y in seq if k == 'y']
    if not years: return None
    if inst and len(inst) == len(years) and not kinds:
        yrs = sorted(set(years), reverse=True)
        return [(0, ['cur', 'py', 'py2', 'py3'][min(yrs.index(y), 3)], 'v') for y in years]
    if not kinds:
        if re.search(r'december 31|as of', hl) and 'ended' not in hl and len(set(years)) == len(years) and n <= 3 and 'operating activities' not in hl:
            kinds = [0]                 # balance sheet with "December 31, || 2010 | 2009"
        else:
            kinds = [12]                # 10-K statements: "For the Years Ended December 31, | 2025 | 2024 | 2023"
    # distribute years over kinds in order
    ny = len(years)
    per = ny // len(kinds) if len(kinds) and ny % len(kinds) == 0 else ny
    blocks = []
    i = 0
    for kidx in range(len(kinds) if per != ny else 1):
        blk = years[i:i + per]; i += per
        blocks.append((kinds[kidx], blk))
    if per == ny and len(kinds) > 1: blocks = [(kinds[0], years)]
    ymap = {}
    yi = 0
    for k, blk in blocks:
        srt = sorted(set(blk), reverse=True)
        for y in blk:
            ymap[yi] = (k, ['cur', 'py', 'py2', 'py3', 'py4'][min(srt.index(y), 4)]); yi += 1
    yi = 0
    for kind, y in seq:
        if kind == 'c': cols.append(('chg', 'chg', 'v'))
        else:
            k, cp = ymap[yi]; yi += 1
            cols.append((k, cp, 'v'))
    return cols

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
