"""Parse Norfolk Southern EDGAR documents (earnings-release financial statements, 10-Q / 10-K MD&A tables) into typed tables with
resolved columns.

NSC's release statements (8-K Item 2.02 exhibit "financial statements" / Ex. 99.2 "Quarterly Financial Data") have carried the same
family of schedules since 2006: consolidated statements of income (railway operating revenues by commodity group, operating expenses
by major classification), balance sheet and year-to-date cash flows, plus notes. Column layouts vary by era:
  2006-2012 fourth-quarter releases: separate three-month and twelve-month statements ("Three Months Ended Dec. 31," / "Years Ended").
  2013+: one statement with "Fourth Quarter | Years ended December 31," (or "Third Quarter | First Nine Months") column blocks.
Tables are identified by content and each value column is resolved to (months, 'cur' | 'py'): months 3 / 6 / 9 / 12 (0 = instant).

Values: '(1,234' / '(1,234)' -> -1234; '-', '--', '—' -> 0.0. Amounts stay in the document units (USD millions; 2006-2007 share
counts in thousands are converted by the caller).
"""
import re
from bs4 import BeautifulSoup

def pnum(tok):
    t = tok.strip().replace('$', '').replace('​', '').replace('\xa0', ' ').strip()
    if '%' in t: return None                           # percentage-change columns are dropped
    t = t.replace(' ', '')
    if t in ('—', '–', '-', '―', '--', '— —', '−'): return 0.0
    neg = t.startswith('(') or t.startswith('-') or t.startswith('−')
    t = t.strip('()-−').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

_BROKEN = [(r'Incom e', 'Income'), (r'e nded', 'ended'), (r'Ye ars', 'Years'), (r'Quarte r', 'Quarter'), (r'Mo nths', 'Months'),
           (r'Reve nues', 'Revenues'), (r'Tot al', 'Total'), (r'Depr eciation', 'Depreciation'), (r'Railw ay', 'Railway'), (r'Oper ating', 'Operating')]
def _clean(s):
    s = re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('\u200b', ' ')).strip()
    for a, b in _BROKEN: s = re.sub(a, b, s)
    return s

def _row_cells(tr):
    cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
    out = []
    for c in cells:
        if c in ('', '$', '('): continue
        if c in (')', '%', ')%', '%)') and out: out[-1] = out[-1] + c      # closing bracket / percent sign split into its own cell
        elif c in (')', '%', ')%', '%)'): continue
        else: out.append(c)
    return out

def html_tables(html):
    """-> list of raw tables [{'hdr': [header text rows], 'rows': [(label, [values])]}] from every <table>; header rows are the
    non-numeric rows (and the year rows) before the first data row, plus in-table sub-headings as rows with no values."""
    soup = BeautifulSoup(html, 'lxml')
    for t in soup.find_all(re.compile(r'^ix:header$')): t.decompose()
    out = []
    TITLE = re.compile(r'consolidated\s+(condensed\s+)?(statements?|balance)|statements? of (income|cash flows|comprehensive)|balance sheets?', re.I)
    for t in soup.find_all('table'):
        cur = {'hdr': [], 'rows': []}
        tabs = [cur]
        for tr in t.find_all('tr'):
            cells = _row_cells(tr)
            if not cells: continue
            if len(cells) == 1 and TITLE.search(cells[0]) and cur['rows']:
                cur = {'hdr': [cells[0]], 'rows': []}; tabs.append(cur); continue
            vals = [pnum(c) for c in cells[1:]]
            years = [int(y) for y in re.findall(r'(?<!\d)(20\d\d|19\d\d)(?!\d)', ' '.join(cells))]
            isyear = bool(years) and all(re.fullmatch(r'(19|20)\d\d', c.strip()) or ' vs. ' in c or 'vs.' in c for c in cells)
            numeric = [v for v in vals if v is not None]
            lab_is_num = pnum(cells[0]) is not None
            hdr_word = re.match(r'^(units|revenues?|revenue per unit|\$ in millions|in thousands|\$ per unit|\(?\$ in millions|tons in thousands)', cells[0].lower())
            if hdr_word and numeric and all(v == int(v) and 1990 <= v <= 2035 for v in numeric) and len(numeric) <= 4: isyear = True
            if isyear or (lab_is_num and not cur['rows']):
                cur['hdr'].append(' | '.join(cells)); continue
            if len(cells) >= 2 and numeric and not lab_is_num:
                cur['rows'].append((cells[0], [v for v in vals if v is not None] if all(v is None or isinstance(v, float) for v in vals) else numeric))
            elif not cur['rows']:
                cur['hdr'].append(' | '.join(cells))
            else:
                cur['rows'].append((' | '.join(cells), []))
        out.extend(x for x in tabs if x['rows'])
    return out

KIND = [(r'twelve|years? ended|year ended|fiscal year|years ended|annual', 12), (r'nine|third quarter and|9 months', 9),
        (r'six|6 months', 6), (r'three|first quarter|second quarter|third quarter|fourth quarter|quarter ended|quarters ended|3 months', 3)]

def period_kinds(hl):
    """ordered list of (position, months) for each period phrase in a header string."""
    found = []
    for m in re.finditer(r'(three|six|nine|twelve)[\s\-]+months?|years? ended|first quarter|second quarter|third quarter|fourth quarter|'
                         r'first nine months|first six months|year(s)? ended december 31|quarter ended|as of|at december 31|december 31,', hl):
        s = m.group(0)
        if s.startswith(('three', 'first quarter', 'second quarter', 'third quarter', 'fourth quarter', 'quarter ended')): k = 3
        elif s.startswith(('six', 'first six')): k = 6
        elif s.startswith(('nine', 'first nine')): k = 9
        elif s.startswith(('twelve', 'year')): k = 12
        else: k = 0
        found.append((m.start(), k))
    return found

def columns(t):
    """resolve the value columns of a statement table -> [(months, 'cur'|'py')] or None."""
    h = ' | '.join(t['hdr']); hl = h.lower()
    n = max((len(v) for _, v in t['rows']), default=0)
    if not n: return None
    kinds = [k for _, k in period_kinds(hl)]
    kinds = [k for k in kinds if k != 0] or ([0] if re.search(r'as of|december 31,|march 31|june 30|september 30', hl) else [])
    years = [int(y) for y in re.findall(r'(?<!\d)(20\d\d)(?!\d)', h)]
    if not kinds and not years: return None
    if n == 2 and (len(kinds) <= 1):
        k = kinds[0] if kinds else 0
        return [(k, 'cur'), (k, 'py')]
    if n == 4 and len(kinds) >= 2:
        return [(kinds[0], 'cur'), (kinds[0], 'py'), (kinds[1], 'cur'), (kinds[1], 'py')]
    if n == 4 and len(kinds) == 1:
        return [(kinds[0], 'cur'), (kinds[0], 'py'), (kinds[0], 'py2'), (kinds[0], 'py3')]
    if n == 3 and kinds:
        return [(kinds[0], 'cur'), (kinds[0], 'py'), (kinds[0], 'py2')]
    if n == 1 and kinds: return [(kinds[0], 'cur')]
    if n == 2: return [(0, 'cur'), (0, 'py')]
    return None

def ttype(t):
    labs = ' || '.join(l.lower() for l, _ in t['rows'])
    if 'total railway operating revenues' in labs and 'income from railway operations' in labs: return 'is'
    if 'total assets' in labs and 'total current assets' in labs: return 'bs'
    if 'net cash provided by operating activities' in labs or ('cash flows from investing' in labs): return 'cf'
    if 'total comprehensive income' in labs: return 'oci'
    return None

def parse(html):
    """-> list of typed tables {'type', 'cols', 'rows', 'hdr'} for the financial statements."""
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if not ty: continue
        cols = columns(t)
        if not cols: continue
        if ty == 'cf' and all(c[0] == 0 for c in cols):
            hl = ' '.join(t['hdr']).lower()
            mo = 9 if 'nine' in hl else 6 if 'six' in hl else 3 if ('three' in hl or 'quarter' in hl) else 12
            cols = [(mo, c[1]) for c in cols]
        res.append({'type': ty, 'cols': cols, 'rows': t['rows'], 'hdr': t['hdr']})
    return res

def norm_label(lab):
    L = lab.lower()
    L = re.sub(r'\((note|notes)[^)]*\)', '', L)
    L = L.replace('’', "'").replace('–', '-').replace('—', '-')
    return re.sub(r'\s+', ' ', L).strip(' :*')

def get(tables, ty, label_re, months, cp='cur', nth=0, exclude=None):
    hits = 0
    for t in tables:
        if t['type'] != ty: continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == months and c[1] == cp]
        if not idx: continue
        for lab, vals in t['rows']:
            if not vals: continue
            L = norm_label(lab)
            if re.search(label_re, L) and not (exclude and re.search(exclude, L)):
                if hits == nth:
                    i = idx[0]
                    return vals[i] if i < len(vals) else None
                hits += 1
    return None

# ------------------------------------------------------------------ MD&A market-group tables (10-Q / 10-K)
GROUPS = [('coal', r'^coal'), ('merch', r'^(general )?merchandise$'), ('im', r'^intermodal'), ('total', r'^total'),
          ('chem', r'^chemicals'), ('agr', r'^agr|^agriculture'), ('metals', r'^metals'), ('auto', r'^automotive'),
          ('paper', r'^paper'), ('forest', r'^forest')]

def _group(lab):
    L = norm_label(lab)
    for k, p in GROUPS:
        if re.search(p, L): return k
    return None

def market_tables(html):
    """-> list of market-group tables: {'measure': 'rev'|'units'|'rpu'|'wide', 'cols': [(months, cp)], 'rows': {group: [values]}}.
    Wide format (to 2019): one table with Revenues | Units | Revenue per Unit column blocks; separate tables from 2020 (10-K: three
    years + % change columns; 10-Q: quarter + year-to-date blocks with % change columns)."""
    out = []
    prev_cols, prev_pat = None, None
    for t in html_tables(html):
        groups = {}
        for lab, vals in t['rows']:
            g = _group(lab)
            if g and vals: groups.setdefault(g, vals)
        if not ({'coal', 'im', 'total'} <= set(groups)): continue
        h = ' | '.join(t['hdr']); hl = h.lower()
        if 'tons in thousands' in hl or 'utility' in ' '.join(l.lower() for l, _ in t['rows']): continue
        years = [int(y) for y in re.findall(r'(?<!\d)(20\d\d)(?!\d)', h)]
        kinds = [k for _, k in period_kinds(hl) if k]
        # column pattern from the header years row: Y = value column, P = percent-change column (a "—" change parses as 0.0,
        # so rows are mapped position by position when they carry the full pattern, else trimmed to the value columns)
        pat = None
        for row in t['hdr']:
            cells = [c.strip() for c in row.split(' | ')]
            pp = ['Y' if re.fullmatch(r'(19|20)\d\d', c) else 'P' if re.search(r'% change|vs\.', c) else None for c in cells]
            pp = [x for x in pp if x]
            if pp.count('Y') >= 2 and (pat is None or len(pp) > len(pat)): pat = pp          # the years row with the most cells
        if pat is None and prev_pat: pat = prev_pat
        if pat:
            n = pat.count('Y'); yidx = [i for i, x in enumerate(pat) if x == 'Y']
            def pick(v):
                if len(v) == len(pat): return [v[i] for i in yidx]
                return v[:n]
            groups = {g: pick(v) for g, v in groups.items()}
        else:
            n = len(groups['total'])
            if any(len(v) < n for v in groups.values()): n = min(len(v) for v in groups.values())
            groups = {g: v[:n] for g, v in groups.items()}
        prev_pat = pat
        wide = ('revenue per unit' in hl or 'revenue' in hl and 'units' in hl) and n >= 6 and n % 3 == 0
        if wide:
            per = n // 3
            if per == 2: cps = [(kinds[0] if kinds else 12, 'cur'), (kinds[0] if kinds else 12, 'py')]
            else: cps = [(12, c) for c in ('cur', 'py', 'py2')][:per]
            for i, meas in enumerate(('rev', 'units', 'rpu')):
                out.append({'measure': meas, 'cols': cps, 'rows': {g: v[i * per:(i + 1) * per] for g, v in groups.items() if len(v) == n}, 'hdr': h})
            continue
        if 'revenue per unit' in hl or '$ per unit' in hl: meas = 'rpu'
        elif 'units' in hl or 'in thousands' in hl: meas = 'units'
        elif 'revenues' in hl or '$ in millions' in hl or 'in millions' in hl: meas = 'rev'
        else: continue
        # value columns (percent-change columns already dropped by pnum); years in header give the block structure
        if n == 3 and (len(years) >= 3 or not kinds): cps = [(12, 'cur'), (12, 'py'), (12, 'py2')]
        elif n == 2: cps = [(kinds[0] if kinds else 3, 'cur'), (kinds[0] if kinds else 3, 'py')]
        elif n == 4 and len(kinds) >= 2: cps = [(kinds[0], 'cur'), (kinds[0], 'py'), (kinds[1], 'cur'), (kinds[1], 'py')]
        elif prev_cols and len(prev_cols) == n: cps = prev_cols
        else: continue
        if not kinds and not years and prev_cols and len(prev_cols) == n: cps = prev_cols
        prev_cols = cps
        out.append({'measure': meas, 'cols': cps, 'rows': {g: v for g, v in groups.items() if len(v) == n}, 'hdr': h})
    return out

def market_values(html, months, cp='cur'):
    """{measure: {group: value}} for one period column."""
    res = {}
    for t in market_tables(html):
        idx = [i for i, c in enumerate(t['cols']) if c[0] == months and c[1] == cp]
        if not idx: continue
        d = res.setdefault(t['measure'], {})
        for g, v in t['rows'].items():
            if g not in d and idx[0] < len(v): d[g] = v[idx[0]]
    return res

def simple_table(html, must_labels, months, cp='cur', hdr_re=None):
    """values of a small KPI table (coal tonnage by market, intermodal units by market, operating expenses by classification) for
    one period column: {label: value}."""
    for t in html_tables(html):
        labs = [norm_label(l) for l, v in t['rows'] if v]
        if not all(any(re.search(m, L) for L in labs) for m in must_labels): continue
        h = ' | '.join(t['hdr']).lower()
        if hdr_re and not re.search(hdr_re, h): continue
        n = max(len(v) for _, v in t['rows'] if v)
        kinds = [k for _, k in period_kinds(h) if k]
        if n == 2: cols = [(kinds[0] if kinds else months, 'cur'), (kinds[0] if kinds else months, 'py')]
        elif n == 4 and len(kinds) >= 2: cols = [(kinds[0], 'cur'), (kinds[0], 'py'), (kinds[1], 'cur'), (kinds[1], 'py')]
        elif n == 3: cols = [(12, 'cur'), (12, 'py'), (12, 'py2')]
        else: continue
        idx = [i for i, c in enumerate(cols) if c[0] == months and c[1] == cp]
        if not idx: continue
        out = {}
        for lab, vals in t['rows']:
            if vals and idx[0] < len(vals): out.setdefault(norm_label(lab), vals[idx[0]])
        return out
    return None
