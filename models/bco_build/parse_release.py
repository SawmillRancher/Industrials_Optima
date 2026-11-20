"""Brink's earnings-release parser (8-K Ex. 99.1 text from h2t.py). Brink's releases carry quarterly tables for the prior and the
current year ("Segment Results: 2025 and 2026", "Non-GAAP Results Reconciled to GAAP"): rows of 1Q | 2Q | 3Q | 4Q | Full Year for
each year. wide_tables() returns every such row as (section, label, [values]) with the section heading in force
(e.g. 'Revenues:', 'Operating profit:', 'EPS:', 'Adjusted EBITDA:')."""
import re
NUM = re.compile(r'^\(?-?\$?[\d,]*\.?\d+\)?%?$')

def num(s):
    s = s.strip().replace('$', '').replace('%', '').strip()
    if s in ('—', '-', '–', '— ', ''): return 0.0 if s else None
    neg = s.startswith('(') or s.startswith('-')
    s = s.strip('()-').replace(',', '')
    if s.startswith('.'): s = '0' + s
    try: v = float(s)
    except ValueError: return None
    return -v if neg else v

def cells(line): return [c.strip() for c in line.rstrip('\n').split(' | ')]

def wide_tables(text, minvals=8):
    out, sec, title, hdr = [], '', '', None
    for ln in text.split('\n'):
        c = cells(ln)
        if len(c) == 1:
            t = c[0].strip()
            if re.match(r'^(Segment Results|Non-GAAP Results Reconciled)', t, re.I) or re.match(r'^Other Items Not Allocated To Segments', t): title = t
            elif t.endswith(':') and len(t) < 90: sec = t
            elif re.match(r'^(Revenues|Operating [Pp]rofit|Operating Margin|Adjusted EBITDA|EPS|GAAP|Non-GAAP)\b.{0,40}$', t): sec = t
            continue
        if re.match(r'^1Q$', c[0]) or (c[0] == '' and '1Q' in c): hdr = c; continue
        vals = [num(x) for x in c[1:]]
        if len(vals) >= minvals and sum(v is not None for v in vals) >= minvals - 1:
            out.append((title, sec, c[0], vals))
        elif len(c) == 2 and c[0].endswith(':'): sec = c[0]
    return out

def narrow_table(text, start_pat, end_pat=None, maxlines=120):
    """rows (label, [numbers]) of the first table after the line matching start_pat"""
    lines = text.split('\n'); rows = []
    for i, ln in enumerate(lines):
        if re.search(start_pat, ln):
            for l2 in lines[i + 1:i + 1 + maxlines]:
                if end_pat and re.search(end_pat, l2): break
                c = cells(l2)
                if len(c) >= 2:
                    v = [num(x) for x in c[1:]]
                    if any(x is not None for x in v): rows.append((c[0], v))
            break
    return rows
