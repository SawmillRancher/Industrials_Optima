"""Row-level reader for the EDGAR text conversions (h2t.py): every table row becomes (line number, label, tokens).

Tokens: numbers as published ('( 177 )' / '(177)' -> -177; '—' -> 0.0; '$', ',' and '%' stripped); anything else (V% flags
such as 'F', 'U', 'n/m', 'bps' cells) is kept as None so that token positions are preserved. GE tables put the year-on-year
column (V%) only on total rows, so a release row has either 4 tokens (3M cur, 3M py, YTD cur, YTD py) or 6 tokens
(3M cur, 3M py, V%, YTD cur, YTD py, V%); cols() resolves both layouts."""
import re, os

S = os.environ.get('GE_SRC', '/tmp/ge_src')
NUM = re.compile(r'^\(?\s*-?\$?\s*[\d,]*\.?\d+\s*\)?%?$')

def tok(s):
    s = s.strip().replace('—', '—').replace('–', '—')
    if s in ('—', '-', '— %', '—%'): return 0.0
    if 'bps' in s: return None
    s2 = s.replace('$', '').replace(',', '').replace('%', '').replace(' ', '')
    if NUM.match(s2):
        neg = s2.startswith('(') and s2.endswith(')') or s2.startswith('(') or s2.startswith('-')
        v = float(s2.strip('()-'))
        return -v if neg else v
    return None

def norm(label):
    l = label.lower().replace('’', "'").replace('–', '-').replace('—', '-')
    l = re.sub(r'\(note \d+\)', '', l)
    l = re.sub(r'\s+', ' ', l).strip()
    return l

_cache = {}
def rows(path):
    if path in _cache: return _cache[path]
    out, pend = [], None
    for i, line in enumerate(open(path, encoding='utf-8', errors='ignore')):
        line = line.rstrip('\n')
        if '|' not in line:
            # label split across lines by <br>: keep a label-only line to prefix the next row starting in lower case
            t = line.strip()
            pend = t if t and not t[0].isdigit() and len(t) < 160 else None
            continue
        cells = [c.strip() for c in line.split('|')]
        lab = cells[0]
        if pend and lab and lab[0].islower(): lab = pend + ' ' + lab
        pend = None
        toks = [tok(c) for c in cells[1:]]
        out.append((i, lab, norm(lab), toks))
    _cache[path] = out
    return out

def doc(date, kind):
    """text file for a filing date and document kind ('10-Q' / '10-K' / 'release' / exhibit name fragment)."""
    d = os.path.join(S, 'txt')
    for f in sorted(os.listdir(d)):
        if not f.startswith(date): continue
        if kind in ('10-Q', '10-K') and f'_{kind}_' in f: return os.path.join(d, f)
        if kind == 'release' and 'earningsrelease' in f: return os.path.join(d, f)
        if kind not in ('10-Q', '10-K', 'release') and kind in f: return os.path.join(d, f)
    raise FileNotFoundError(f'{date} {kind}')

def section(path, head, stop=None, after=0, nmax=400, confirm=r'^\((in|dollars in) millions|^\d{4}$|^three months|^for the', nth=0):
    """rows from the `nth` row whose label matches regex `head` (searched from line `after`) and whose next row matches `confirm`
    (skips table-of-contents hits), until `stop` matches or nmax rows."""
    rs = rows(path); out = []; on = False; k = 0
    for j, r in enumerate(rs):
        if r[0] < after: continue
        if not on:
            if re.search(head, r[2]) and (confirm is None or (j + 1 < len(rs) and re.search(confirm, rs[j + 1][2]))):
                if k == nth: on = True; out.append(r)
                k += 1
            continue
        if stop and re.search(stop, r[2]): break
        out.append(r)
        if len(out) >= nmax: break
    if not on: raise KeyError(f'section {head!r} not found in {os.path.basename(path)}')
    return out

def anchor(path, header, first, within=6):
    """line number of the raw header line (regex, case-sensitive) that is followed within `within` lines by a row starting with
    `first` (regex on the raw line) - locates the face statements in both 10-Q (header in a table row) and 10-K (plain line)."""
    lines = open(path, encoding='utf-8', errors='ignore').read().split('\n')
    for i, l in enumerate(lines):
        if re.match(header, l.strip()):
            for j in range(i, min(len(lines), i + within + 1)):
                if re.match(first, lines[j].strip()): return j
    raise KeyError(f'anchor {header!r}/{first!r} not found in {os.path.basename(path)}')

def stmt(path, header, first, stop, nmax=200):
    a = anchor(path, header, first)
    return section(path, '.', stop, after=a, nmax=nmax, confirm=None)

def find(sec, pat, nth=0, need=True):
    hits = [r for r in sec if re.search(pat, r[2])]
    if len(hits) <= nth:
        if need: raise KeyError(f'row {pat!r} not found (section starting {sec[0][1]!r} line {sec[0][0]})')
        return None
    return hits[nth]

def nums(r):
    return [t for t in r[3]]

def cols(r):
    """(3M cur, 3M py, YTD cur, YTD py) for release / MD&A rows with or without V% columns."""
    t = r[3]
    t = [x for x in t]
    while t and t[-1] is None: t.pop()
    if len(t) in (6, 7): return t[0], t[1], t[3], t[4]     # 7: trailing reference cell (Q3-25 release CFOA row)
    if len(t) == 4: return t[0], t[1], t[2], t[3]
    if len(t) == 3: return t[0], t[1], None, None
    if len(t) == 2: return t[0], t[1], None, None
    if len(t) == 5:
        # one V% missing: decide by position of the None / flag token
        if t[2] is None or abs(t[2]) < 100 and t[3] is not None and abs(t[3]) > 10 * max(1, abs(t[2])):
            return t[0], t[1], t[3], t[4]
        return t[0], t[1], t[2], t[3]
    raise ValueError(f'unexpected token count {len(t)} in {r[1]!r}: {t}')
