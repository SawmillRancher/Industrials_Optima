"""Table helpers for Visa 10-K / 10-Q / release text (h2t.py output: one table row per line, cells joined by ' | ').

Statements are located by content, not by headings: the statement of operations is the first block whose rows run from a revenue
line to 'Personnel'; the balance sheet the first block running 'Cash and cash equivalents' ... 'Total assets'; the cash-flow
statement the block ending with 'Net cash provided by (used in) operating activities' and running to cash at end of period."""
import re

NUM = re.compile(r'^\(?\s*-?\$?\s*[\d,]+(\.\d+)?\s*\)?%?$')

def num(c):
    c = c.strip().replace('$', '').replace(' ', '').strip()
    if c in ('—', '–', '-', '— ', '*'): return 0.0
    if not NUM.match(c): return None
    neg = c.startswith('(') or c.startswith('-')
    v = float(re.sub(r'[^\d.]', '', c))
    return -v if neg else v

def is_marker(c):
    return re.fullmatch(r'\(\d\)|\(\d\),\(\d\)', c.strip()) is not None

def rows(text):
    out = []
    for i, line in enumerate(text.split('\n')):
        if '|' not in line: continue
        cells = [c.strip() for c in line.split('|')]
        lab = cells[0]
        vals = [num(c) for c in cells[1:] if not is_marker(c) and c.strip() not in ('%', ')')]
        vals = [v for v in vals if v is not None]
        allv = [num(c) for c in cells[1:] if c.strip() not in ('%', ')')]
        out.append((i, lab, vals, cells, [v for v in allv if v is not None]))
    return out

def norm(lab):
    lab = re.sub(r'\s*\((Note|Notes) [^)]*\)', '', lab)
    lab = re.sub(r'\s*\(\d\)(,\s*\(\d\))*', '', lab)
    return re.sub(r'\s+', ' ', lab).strip()

def block(R, start_pat, must_pat, end_pat, within=40, after=0, nvals=None):
    """first block: a row matching start_pat (line >= after) followed within `within` rows by must_pat; runs to end_pat."""
    for k, (i, lab, vals, *_) in enumerate(R):
        if i < after or not re.search(start_pat, norm(lab), re.I) or not vals: continue
        if nvals and len(vals) not in nvals: continue
        ok = any(re.search(must_pat, norm(R[j][1]), re.I) for j in range(k, min(k + within, len(R))))
        if not ok: continue
        out = []
        for j in range(k, len(R)):
            out.append(R[j])
            if re.search(end_pat, norm(R[j][1]), re.I) and R[j][2]: break
        return out
    return []
