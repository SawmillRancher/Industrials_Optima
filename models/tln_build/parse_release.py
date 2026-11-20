"""Table helpers for the Talen EDGAR text files (h2t.py output: one table row per line, cells joined by ' | ').
num(): '(25,433' / '( 27 )' -> negative; em dash -> 0.0; 'N/A' / blank -> None. block(): rows between two anchors as
(label, [values]) with note references stripped from the label."""
import re

def num(s):
    s = s.strip().replace('$', '').replace('%', '').strip()
    if s in ('—', '–', '-', '— %'): return 0.0
    m = re.fullmatch(r'\(?\s*([\d,]+(?:\.\d+)?)\s*\)?', s)
    if not m: return None
    v = float(m.group(1).replace(',', ''))
    return -v if s.startswith('(') else v

def clean(label):
    label = re.sub(r'\s*\((Notes?|See Note)[^)]*\)', '', label)
    label = re.sub(r'\s*\([a-z]\)', '', label)
    return re.sub(r'\s+', ' ', label).strip()

def find(lines, pat, start=0, nth=1):
    rx = re.compile(pat); k = 0
    for i in range(start, len(lines)):
        if rx.search(lines[i]):
            k += 1
            if k == nth: return i
    return None

def block(lines, i0, end_pat, maxn=140):
    """Rows from line i0 until a line matching end_pat (inclusive). Returns [(label, [values...])]."""
    rx = re.compile(end_pat); out = []
    for ln in lines[i0:i0 + maxn]:
        cells = [c.strip() for c in ln.split(' | ')]
        vals = [num(c) for c in cells[1:]]
        if len(cells) > 1 and any(v is not None for v in vals) or (len(cells) > 1 and all(c == 'N/A' for c in cells[1:])):
            out.append((clean(cells[0]), vals))
        if rx.search(ln): break
    return out
