"""Table helpers for the James Hardie results packages (text from h2t.py: one table row per line, cells joined by ' | ').

num()      -> float: '(23.1' = -23.1, '1,234.5', '—' = 0.0, 'US$728' = 728, 'A$1,039' = 1039; None for text / currency-only cells.
vals()     -> numeric tokens of a row (currency-only and text cells dropped).
pick()     -> assign a row's numeric tokens to (current, prior, ytd current, ytd prior) given the table shape:
              'q'  : first two tokens (three-month columns, change columns ignored)
              'qy' : three-month and year-to-date columns, with or without interleaved change columns
              'last': the last token (the 'As Reported' column of the asbestos split tables)
row()      -> first row whose label matches a regex within [start, end) lines.
block()    -> the rows between a start label and an end label (non-GAAP bridges).
"""
import re

CUR = re.compile(r'^(US\$|A\$|€|EUR|NZ\$|\$)$')
NUMRE = re.compile(r'^\(?[-−–]?(US\$|A\$|€)?\s?\(?[-−–]?\d[\d,]*\.?\d*\)?%?$')

def num(tok):
    t = tok.strip().replace('−', '-').replace('–', '-')
    if t in ('—', '–', '-', '— %', '—%'): return 0.0
    if CUR.match(t): return None
    if t.lower() in ('nm', 'n/m', 'n/a', 'flat'): return None
    t = re.sub(r'^(US\$|A\$|NZ\$|€|EUR|\$)\s*', '', t)        # '$ (251.2)' / 'US$728' -> '(251.2)' / '728'
    neg = t.startswith('(') or t.startswith('-(') or t.startswith('-')
    t = t.strip('()').lstrip('-').replace('US$', '').replace('A$', '').replace('€', '').replace('$', '').replace(',', '').strip()
    t = t.rstrip('%').rstrip(')').strip()
    if re.search(r'[A-Za-z]', t): return None
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v

def cells(line):
    parts = [c.strip() for c in line.split(' | ')]
    return parts[0], parts[1:]

def vals(line):
    _, cs = cells(line)
    out = []
    for c in cs:
        v = num(c)
        if v is not None: out.append(v)
    return out

def pick(tokens, mode):
    """returns dict with keys cur, prior, ytd, ytd_prior (missing keys when the row has fewer columns)."""
    n = len(tokens)
    if mode == 'last': return {'cur': tokens[-1]} if tokens else {}
    if mode == 'q':
        return {k: tokens[i] for i, k in enumerate(('cur', 'prior')) if i < n}
    if mode == 'qy':
        if n >= 6: idx = (0, 1, 3, 4)
        elif n == 4: idx = (0, 1, 2, 3)
        elif n == 5:
            # one change column is blank: decide which by testing whether token 2 (or token 4) is the % change of its pair
            t = tokens
            def pct_ok(c, a, b):
                if b == 0: return False
                return abs(abs(c) - abs((a / b - 1) * 100)) <= 1.5
            if pct_ok(t[2], t[0], t[1]) and not pct_ok(t[4], t[2], t[3]): idx = (0, 1, 3, 4)
            elif pct_ok(t[4], t[2], t[3]): idx = (0, 1, 2, 3)
            else: idx = (0, 1, 3, 4) if abs(t[2]) < 1000 and float(t[2]).is_integer() and not float(t[4]).is_integer() else (0, 1, 2, 3)
        elif n == 3: idx = (0, 1)
        elif n == 2: idx = (0, 1)
        else: idx = tuple(range(n))
        keys = ('cur', 'prior', 'ytd', 'ytd_prior')
        return {keys[j]: tokens[i] for j, i in enumerate(idx) if i < n}
    if mode == 'one':
        return {'cur': tokens[0]} if tokens else {}
    raise ValueError(mode)

class Doc:
    def __init__(self, path):
        self.path = path
        raw = open(path, errors='ignore').read().replace('\xa0', ' ').split('\n')
        # re-join labels wrapped over two lines: a short text line without ' | ' followed by a continuation that holds the values
        lines = []
        i = 0
        while i < len(raw):
            l = raw[i]
            if (' | ' not in l and 0 < len(l.strip()) < 70 and i + 1 < len(raw) and ' | ' in raw[i + 1]
                    and re.match(r'^[a-z(&]', raw[i + 1].strip()) and not l.strip().endswith(':')):
                lines.append(l.strip() + ' ' + raw[i + 1].strip()); i += 2; continue
            lines.append(l); i += 1
        self.lines = lines
        self.n = len(self.lines)
    def find(self, pat, start=0, end=None, nth=0, table=True, flags=re.I):
        """line index of the nth line whose label (text before ' | ') matches pat."""
        end = self.n if end is None else min(end, self.n)
        rx = re.compile(pat, flags); k = 0
        for i in range(start, end):
            l = self.lines[i]
            if table and ' | ' not in l: continue
            lab = l.split(' | ')[0].strip() if table else l.strip()
            if rx.search(lab):
                if k == nth: return i
                k += 1
        return None
    def findtext(self, pat, start=0, end=None, nth=0, flags=re.I):
        return self.find(pat, start, end, nth, table=False, flags=flags)
    def row(self, pat, mode='qy', start=0, end=None, nth=0, flags=re.I):
        i = self.find(pat, start, end, nth, flags=flags)
        if i is None: return None
        return pick(vals(self.lines[i]), mode)
    def rawrow(self, pat, start=0, end=None, nth=0):
        i = self.find(pat, start, end, nth)
        return None if i is None else vals(self.lines[i])
    def block(self, start_pat, end_pat, start=0, end=None, mode='qy', nth=0, maxrows=40):
        """rows from the line matching start_pat through the line matching end_pat (inclusive) -> list of (label, picked)."""
        i = self.find(start_pat, start, end, nth)
        if i is None: return None
        out = []
        for j in range(i, min(i + maxrows, self.n)):
            l = self.lines[j]
            if ' | ' not in l: continue
            lab, _ = cells(l)
            v = vals(l)
            out.append((lab, pick(v, mode) if v else {}, j))
            if re.search(end_pat, lab, re.I) and j > i: return out
        return out
