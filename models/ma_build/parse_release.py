"""Mastercard earnings-release (8-K Ex. 99.1) parser: finds the statement tables in the text version (h2t.py: one table row
per line, cells joined by ' | ') and returns each as an ordered list of (label, [values]) in USD millions.

Tables: consolidated statement of operations (three-month current / prior, then year-to-date current / prior), balance sheet
(current period end first), cash-flow statement (year to date, current first) and the worldwide row of the operating-performance
(GDV) table. Releases to 2012 are in USD thousands, later ones in millions; the unit is read from each table header.
Number conventions in the text: a dropped ')' means '(25,433' is negative; '—' / '-' is zero."""
import re

NUM = re.compile(r'^\(?-?\$?\s*[\d,]+(\.\d+)?\)?$')

def to_num(s):
    s = s.strip().replace('$', '').replace(' ', '')
    if s in ('—', '-', '–', '— ', '**'): return 0.0
    neg = s.startswith('(')
    s = s.strip('()').replace(',', '')
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v

def cells(line):
    return [c.strip() for c in line.split(' | ')]

def row(line):
    """label + numeric values (None when a cell is not numeric)."""
    cs = cells(line)
    if len(cs) < 2: return None, []
    lab = cs[0]
    vals = []
    for c in cs[1:]:
        if c in ('—', '-', '–'): vals.append(0.0); continue
        if NUM.match(c.replace(' ', '')): vals.append(to_num(c))
    return lab, vals

def find_title(lines, pat, start=0):
    rx = re.compile(pat, re.I)
    for i in range(start, len(lines)):
        t = lines[i].strip()
        if len(t) < 90 and rx.search(t) and '|' not in t: return i
    return None

def unit_scale(block):
    for l in block[:12]:
        if re.search(r'in thousands', l, re.I): return 0.001
        if re.search(r'in millions', l, re.I): return 1.0
    return None

def table(lines, i0, end_pat, maxlen=140, scale_default=1.0, keep_ps=()):
    out, scale = [], None
    rx = re.compile(end_pat, re.I)
    block = lines[i0:i0 + maxlen]
    scale = scale_default          # units handled per release in extract.py (USD thousands to 2009)
    for l in block[1:]:
        lab, vals = row(l)
        if lab and vals:
            per_share = re.search(r'per share|earnings per|net income per', lab, re.I) and not re.search(r'shares outstanding', lab, re.I)
            per_share = per_share or any(k in lab.lower() for k in keep_ps)
            out.append((re.sub(r'\s+', ' ', lab), [v if per_share else round(v * scale, 6) for v in vals]))
        if rx.search(l): break
    return out, scale

def header_months(lines, i0):
    blk = ' '.join(lines[i0:i0 + 6]).lower()
    ytd = 12 if re.search(r'twelve months|years ended|year ended', blk) else 9 if 'nine months' in blk else 6 if 'six months' in blk else 3
    return ytd

def parse(text):
    lines = [l.rstrip() for l in text.split('\n')]
    res = {}
    i = find_title(lines, r'statements? of operations')
    if i is not None:
        res['is'], res['is_scale'] = table(lines, i, r'diluted.*(shares|weighted)', 80)
        res['is_ytd_months'] = header_months(lines, i)
    j = find_title(lines, r'balance sheets?', i or 0)
    if j is not None:
        res['bs'], _ = table(lines, j, r'^total liabilities.*(equity|stockholders)', 120)
    k = find_title(lines, r'statements? of cash flows', j or 0)
    if k is not None:
        res['cf'], _ = table(lines, k, r'end of (period|year)', 120)
        res['cf_ytd_months'] = header_months(lines, k)
    # operating performance: first 'Worldwide' row (all programs, three months)
    m = find_title(lines, r'operating performance', k or 0)
    if m is None:
        for t in range(k or 0, len(lines)):
            if lines[t].startswith('GDV') or 'GDV (Bil.)' in lines[t]: m = t; break
    if m is not None:
        hdr = None
        for t in range(m, min(m + 40, len(lines))):
            if 'GDV' in lines[t] and '|' in lines[t] and hdr is None: hdr = cells(lines[t])
            if lines[t].startswith('Worldwide |'):
                lab, vals = row(lines[t]); res['op'] = {'hdr': hdr, 'worldwide': vals, 'line': t}; break
        # all 'Worldwide' rows of the operating-performance tables, in order (all programs / credit / debit per table;
        # tables: current three months, current year to date, prior three months, prior year to date; Q1: current, prior)
        ws = []
        for t in range(res['op']['line'], min(res['op']['line'] + 200, len(lines))):
            if lines[t].startswith('Worldwide |'): ws.append(row(lines[t])[1])
        res['op']['all_rows'] = ws
    return res
