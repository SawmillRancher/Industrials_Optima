"""Parse a Howmet Aerospace earnings release (8-K Item 2.02, Ex. 99.1, converted to text by h2t.py) into sections.

Every release since Q2 2020 prints the same family of schedules: Statement of Consolidated Operations (current quarter, prior
quarter, prior-year quarter; the fourth-quarter release adds a full-year statement), Consolidated Balance Sheet, Statement of
Consolidated Cash Flows (year to date), Segment Information (a panel of quarters and years headed '1Q25 | 2Q25 | ... | 2025'),
and the 'Calculation of Financial Measures' reconciliations (free cash flow, adjusted / excluding-special-items net income,
operating income and EBITDA, organic revenue). Titles and labels drift between years, so sections are found by title keywords
and rows by label regular expressions. Values: '(1,234' -> -1234; '—' -> 0. Amounts are USD millions as published."""
import re

DASH = ('—', '–', '-', '―', '--')
def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace(' ', '')
    if t in DASH: return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

TITLES = [('is', r'statement of consolidated operations \(unaudited'), ('bs', r'consolidated balance sheet \(unaudited'),
          ('cf', r'statement of consolidated cash flows \(unaudited'), ('seg', r'segment information \(unaudited'),
          ('calc', r'calculation of financial measures \(unaudited'), ('calc', r'^reconciliation of ')]

def sections(txt):
    """-> list of (type, title, rows); rows = [(label, [values], raw cells)] incl. header rows (values None where not numeric)."""
    out, cur = [], None
    for line in txt.split('\n'):
        l = line.strip()
        if not l: continue
        low = l.lower()
        ty = next((t for t, p in TITLES if re.search(p, low) and len(l.split(' | ')[0]) < 260 and
                   (' | ' not in l or p.startswith('^'))), None)
        if ty:
            cur = (ty, l.split(' | ')[0], []); out.append(cur)
            if ' | ' not in l: continue
        if cur is None: continue
        cells = [c.strip() for c in l.split(' | ')]
        vals = [pnum(c) for c in cells[1:]]
        cur[2].append((cells[0], vals, cells))
    return out

def rows_of(secs, ty, nth=0):
    hits = [s for s in secs if s[0] == ty]
    return hits[nth][2] if len(hits) > nth else []

def find(rows, rx, col=0, exclude=None, nth=0, start=0):
    """value in numeric column `col` of the nth row whose label matches rx (rows with at least col+1 numeric cells)."""
    n = 0
    for i, (lab, vals, _) in enumerate(rows[start:]):
        nums = [v for v in vals if v is not None]
        if len(nums) <= col: continue
        if re.search(rx, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
            if n == nth: return nums[col]
            n += 1
    return None

def index(rows, rx, start=0):
    for i, (lab, vals, _) in enumerate(rows[start:]):
        if re.search(rx, lab, re.I): return start + i
    return None

PER = re.compile(r'^([1-4])Q(\d\d)$|^(20\d\d)$|^FY ?(20\d\d)$')
def panel_header(cells):
    """['1Q25','2Q25',...,'2025'] -> ['Q1-25','Q2-25',...,'2025'] or None."""
    out = []
    for c in cells:
        m = PER.match(c.replace(' ', ''))
        if not m: return None
        out.append(f'Q{m.group(1)}-{m.group(2)}' if m.group(1) else (m.group(3) or m.group(4)))
    return out if len(out) >= 2 else None
