"""Parse a TransDigm EDGAR document (10-K / 10-Q primary document or an 8-K Ex. 99.1 earnings release) into typed tables with
resolved value columns.

TransDigm's documents print the same family of schedules in every era (statements of income, balance sheets, cash flows,
EBITDA / EBITDA As Defined and adjusted net income reconciliations, segment data, and from fiscal 2019 net sales by end market),
but titles, units (thousands to fiscal 2018, millions from fiscal 2019) and layouts vary. Tables are identified by their
contents and each value column is resolved from the header rows to (months, 'cur' | 'py' | 'py2', measure):
months 3 / 6 / 9 / 12 (0 = balance-sheet instant); 'cur' = the latest year in the header. TransDigm labels periods in weeks
("Thirteen Week Periods Ended", "Twenty-Six", "Thirty-Nine", "Fifty-Two / Fifty-Three Week Period Ended") and fiscal years
("Fiscal Years Ended September 30,").

The ASU 2023-07 segment tables (fiscal 2025 onwards) have segments as columns and the period in the table title; they are typed
'seg2' with cols = segment names and the period parsed from the title ('period' key).
Values: '(1,234)' / '( 1,234 )' -> -1234; '—' -> 0.0. Amounts stay in the document's units."""
import re
from tables import html_tables, pnum, _clean

WORDS = [(r'thirteen', 3), (r'twenty-six|twenty six', 6), (r'thirty-nine|thirty nine', 9),
         (r'fifty-two|fifty two|fifty-three|fifty three|fiscal years? end|years? ended|twelve', 12)]
MON = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'], 1)}

def period_kind(s):
    s = s.lower()
    for p, k in WORDS:
        if re.search(p, s): return k
    if re.search(r'fiscal years?', s): return 12
    return None

def hdr_text(t):
    return ' | '.join(t['hdr'] + [t['pre']] + [l for l, v in t['rows'] if not v][:2])

def columns(t):
    """resolve value columns -> list of (months, cp, meas) or None."""
    h = hdr_text(t); hl = h.lower()
    n = max((len(v) for _, v in t['rows']), default=0)
    if not n: return None
    kinds = []
    for m in re.finditer(r'thirteen|twenty[- ]six|thirty[- ]nine|fifty[- ]two|fifty[- ]three|twelve|fiscal years?|years? ended', hl):
        k = period_kind(m.group(0))
        if k and k not in kinds: kinds.append(k)
    # column dates: full dates where printed (fiscal quarters can end in the same calendar year: Dec-31-2011 vs Jan-1-2011), else years
    dates = [f'{int(y):04d}-{MON[mo.lower()]:02d}-{int(d):02d}' for mo, d, y in
             re.findall(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s*\|?\s*(20[0-3]\d)', h, re.I)]
    if not dates and re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s*(\||$)', h, re.I):
        mons = re.findall(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?', h, re.I)
        yrs = re.findall(r'(?<![\d,])(20[0-3]\d)(?!\d)', h)
        if len(mons) == len(yrs): dates = [f'{int(y):04d}-{MON[mo.lower()]:02d}-{int(d):02d}' for (mo, d), y in zip(mons, yrs)]
    years = dates if dates else [int(y) for y in re.findall(r'(?<!\d)(20[0-3]\d)(?!\d)', h)]
    if not kinds:
        if 'segment' in hl and n <= 5 and re.search(r'power|airframe', hl): return None
        return [(0, 'cur', 'v'), (0, 'py', 'v'), (0, 'py2', 'v')][:n]
    cols = []
    if len(kinds) >= 2 and n % len(kinds) == 0:
        per = n // len(kinds)
    else:
        per = n; kinds = kinds[:1]
    ys = years[-n:] if len(years) >= n else [None] * n
    for i in range(n):
        k = kinds[min(i // per, len(kinds) - 1)]
        blk = [yy for j, yy in enumerate(ys) if j // per == i // per and yy is not None]
        y = ys[i]
        if y is None or not blk: cp = ['cur', 'py', 'py2', 'py3'][min(i % per, 3)]
        else:
            order = sorted(set(blk), reverse=True)
            cp = ['cur', 'py', 'py2', 'py3'][min(order.index(y), 3)]
        cols.append((k, cp, 'v'))
    return cols

def title_period(t):
    """ASU 2023-07 segment tables: 'Thirteen Week Period Ended June 27, 2026' / 'Fiscal Year Ended September 30, 2025' -> (months, end_date)."""
    txt = hdr_text(t)
    k = period_kind(txt)
    m = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(20\d\d)', txt, re.I)
    if not k or not m: return None
    return k, f'{int(m.group(3)):04d}-{MON[m.group(1).lower()]:02d}-{int(m.group(2)):02d}'

def ttype(t):
    labs = ' || '.join(l.lower() for l, _ in t['rows'])
    hdr = hdr_text(t).lower()
    both = hdr + ' || ' + labs
    if re.search(r'power (&|and) control \| airframe', hdr): return 'seg2'
    if labs.startswith('organic sales') or '|| organic sales' in labs: return 'organic'
    if '% of' in hdr or '% change' in hdr or 'change' in hdr.split('||')[0] and '%' in hdr: return 'pct'
    if 'cost of sales' in labs and 'net sales' in labs and ('income from operations' in labs or 'income before income taxes' in labs): return 'is'
    if 'total assets' in labs and ('total current assets' in labs or 'total liabilities' in labs): return 'bs'
    if 'net cash' in labs and ('operating activities' in labs or 'investing activities' in labs) and 'ebitda' not in labs: return 'cf'
    if re.search(r'commercial (and non-aerospace )?oem', labs) and re.search(r'defense', labs): return 'em'
    if 'net sales to external customers' in both or 'ebitda as defined by segment' in hdr or (re.search(r'power (&|and) control', labs) and 'ebitda as defined' in both):
        return 'seg'
    if 'adjusted net income' in labs or 'adjusted earnings per share' in labs or 'adjusted diluted earnings per share' in labs: return 'adjni'
    if 'ebitda as defined' in labs or re.match(r'.*\|\| ebitda', labs) or 'ebitda' in labs: return 'ebitda'
    if 'participating securities' in labs or 'two-class' in hdr: return 'eps2'
    if 'term loans' in labs and ('notes' in labs or 'revolving' in labs): return 'debt'
    if 'capital expenditures' in labs and 'depreciation' in labs: return 'capex'
    if re.search(r'power (&|and) control', labs) and ('total assets' in labs or 'identifiable assets' in labs): return 'segassets'
    if 'organic' in labs or 'organic' in hdr: return 'organic'
    return None

def parse(html):
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if not ty: continue
        if ty == 'seg2':
            segs = [c.strip() for c in re.split(r'\s*\|\s*', [h for h in t['hdr'] if re.search(r'power (&|and) control', h, re.I)][-1])]
            res.append({'type': ty, 'cols': segs, 'period': title_period(t), 'rows': t['rows'], 'hdr': t['hdr'], 'pre': t['pre']})
            continue
        cols = columns(t)
        if not cols: continue
        res.append({'type': ty, 'cols': cols, 'rows': t['rows'], 'hdr': t['hdr'], 'pre': t['pre']})
    return res

def get(tables, ty, label_re, months, cp='cur', meas='v', nth=0, exclude=None, types=None):
    hits = 0
    for t in tables:
        if t['type'] != ty and not (types and t['type'] in types): continue
        if t['type'] == 'seg2': continue
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

def rows(tables, ty, months, cp='cur', meas='v'):
    """all (label, value) rows of the first table of type ty that has the requested column."""
    for t in tables:
        if t['type'] != ty or t['type'] == 'seg2': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == months and c[1] == cp and c[2] == meas]
        if not idx: continue
        i = idx[0]
        return [(lab, vals[i]) for lab, vals in t['rows'] if vals and i < len(vals)]
    return []
