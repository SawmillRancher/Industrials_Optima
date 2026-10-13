"""Table helpers for the RBC Bearings EDGAR text files (h2t.py output: one table row per line, cells joined by ' | ').

Numbers: '(25,433' (the ')' cell is dropped) and '( 85.8' are negative; '-' / '—' / '–' are zero; '22.0%' -> 22.0.
Each parsed row is (line_no, label, [numbers]); a row with no leading text cell has label ''."""
import re

NUM = re.compile(r'^\(?\s*-?\$?\s*[\d,]*\.?\d+\s*%?\)?$')

def num(c):
    c = c.strip().replace('$', '').replace(' ', ' ').strip()
    if c in ('-', '—', '–', '—-', '--'): return 0.0
    if not NUM.match(c): return None
    neg = c.startswith('(') or c.startswith('-')
    v = float(re.sub(r'[^\d.]', '', c))
    return -v if neg else v

def row(line):
    cells = [re.sub(r'\s+', ' ', c.replace('\u00a0', ' ')).strip() for c in line.split(' | ')]
    lab, vals = [], []
    for c in cells:
        v = num(c)
        if v is None and not vals: lab.append(c)
        elif v is not None: vals.append(v)
    return ' '.join(lab).strip(), vals

def lines(path):
    return open(path, encoding='utf-8', errors='replace').read().split('\n')

def rows(L, a=0, b=None):
    out = []
    for i in range(a, len(L) if b is None else min(b, len(L))):
        lab, vals = row(L[i])
        out.append((i, lab, vals))
    return out

def find(L, pat, a=0, b=None, n=None, flags=re.I):
    """first line index in [a, b) whose label matches pat (and has >= n numbers if n given)."""
    p = re.compile(pat, flags)
    for i in range(a, len(L) if b is None else min(b, len(L))):
        lab, vals = row(L[i])
        if p.search(lab) and (n is None or len(vals) >= n): return i
    return None

def get(L, pat, a, b, col=0, n=1, flags=re.I, last=False):
    """value in column col of the first (or last) row in [a, b) whose label matches pat."""
    p = re.compile(pat, flags); hit = None
    for i in range(a, min(b, len(L))):
        lab, vals = row(L[i])
        if p.search(lab) and len(vals) >= max(n, col + 1):
            hit = (i, vals[col])
            if not last: break
    return hit

def scale_of(L, i, back=40):
    """'k' (USD thousands) or 'm' (USD millions) from the nearest unit caption before line i."""
    for j in range(i, max(0, i - back), -1):
        s = L[j].lower()
        if 'thousand' in s: return 'k'
        if 'million' in s: return 'm'
    return None
