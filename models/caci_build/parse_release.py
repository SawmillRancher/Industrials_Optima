"""Parse a CACI earnings release (8-K Item 2.02, Ex. 99 / 99.1, text version from h2t.py) into typed sections.

Every release since FY2006 prints the same family of schedules: statement of operations (quarter and year to date), balance sheet,
cash flows (year to date), revenue by customer type / contract type / prime-sub (/ expertise-technology from FY2020), contract
funding orders (to FY2018) or contract awards (from FY2019), direct costs by category (FY2008-FY2018), the organic-revenue
reconciliation (to FY2018) and the non-GAAP reconciliations (EBITDA / adjusted EBITDA, adjusted net income and EPS, free cash flow).
Titles and column layouts vary by era, so sections are found by their title line and each data row is resolved to
(quarter current, quarter prior, year-to-date current, year-to-date prior) from the header lines in force.

Values stay in release units (thousands, or millions in the summary tables; per share in $). '(1,234' / '(1,234)' -> -1234;
'-', '—' -> 0.0; '---' (guidance range separator), 'n/m' -> None.
"""
import re

DASH = ('—', '–', '-', '―', '--', '— —', '-0-')

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace('\xa0', '').replace(' ', '')
    if t in DASH: return 0.0
    if t in ('---', '') or t.lower() in ('n/m', 'nm', 'n/a'): return None
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

DATE = re.compile(r'^\(?\d{1,2}/\d{1,2}/\d{2,4}\)?$')
TITLES = [
    ('isd', r'^(statements? of operations (margin )?data|stock option expense data)'),
    ('is', r'^(condensed |consolidated |unaudited )*statements? of operations'),
    ('bs', r'^(condensed |consolidated |unaudited )*balance sheets?'),
    ('cf', r'^(condensed |consolidated |unaudited )*statements? of cash flows'),
    ('cust', r'^revenues? by customer (type|group)'),
    ('ctype', r'^revenues? by contract type'),
    ('prime', r'^revenues? (received |generated )?(as a |as |by )prime'),
    ('exptech', r'^revenues? by (expertise|technology)'),
    ('orders', r'^contract funding orders received'),
    ('awards', r'^contract awards( received)? \(unaudited\)|^contract awards$'),
    ('dcost', r'^direct costs by category'),
    ('organic', r'^reconciliation of total revenue growth'),
    ('fcf', r'^reconciliation of net cash provided by operating'),
    ('recon', r'^reconciliation of (net income|diluted)(?!.{0,12}net cash provided)'),
    ('end', r'^(source|contacts?:?|corporate communications)\b'),
]
TITLES = [(k, re.compile(p, re.I)) for k, p in TITLES]
QW = re.compile(r'(quarter|three months?) ended', re.I)
YW = re.compile(r'(six|nine|twelve) months? ended|year ended|fiscal year ended', re.I)
MONTHS = {'six': 6, 'nine': 9, 'twelve': 12, 'year': 12, 'fiscal': 12}

def norm(s):
    s = re.sub(r'\s+', ' ', s.replace('\xa0', ' ')).strip()
    s = re.sub(r'\s*\(?\d\)?$', '', s) if re.search(r'[a-zA-Z)*]\s+\(?\d\)?$', s) else s      # footnote marker "Adjusted EBITDA 1"
    return s.strip(' :*')

def resolve(vals, mode):
    """-> (q_cur, q_prior, y_cur, y_prior). mode: 'Q' | 'Y' | 'QY'. Handles interleaved % change columns."""
    v = vals; n = len(v)
    if mode in ('Q', 'Y'):
        a = (v[0], v[1] if n > 1 else None)
        return a + (None, None) if mode == 'Q' else (None, None) + a
    def pct_ok(c, p, x):
        try: return abs((c / p - 1) * 100 - x) < 0.25 or abs((c / abs(p) - p / abs(p)) * 100 - x) < 0.25
        except Exception: return False
    if n >= 6: return (v[0], v[1], v[3], v[4])
    if n == 4: return (v[0], v[1], v[2], v[3])
    if n == 5:
        if v[2] is None or pct_ok(v[0], v[1], v[2]): return (v[0], v[1], v[3], v[4])
        return (v[0], v[1], v[2], v[3])
    if n == 2: return (v[0], None, v[1], None)
    if n == 3: return (v[0], None, v[1], None) if v[2] is None else (v[0], v[1], v[2], None)
    return (v[0] if n else None, None, None, None)

def parse(path):
    """-> {'sections': {name: [block,...]}, 'text': [...]} ; block = {'mode','months','hdr':[...],'rows':[(label, vals, resolved)]}"""
    raw = [l.rstrip('\n') for l in open(path, encoding='utf-8', errors='replace')]
    out = {'sections': {}, 'lines': raw}
    sec, blk, mode, months, pend_hdr = None, None, None, None, []
    prev_text = None
    def newblk():
        nonlocal blk
        blk = {'mode': mode, 'months': months, 'hdr': list(pend_hdr), 'rows': []}
        out['sections'].setdefault(sec, []).append(blk)
    skip = 0
    for i, ln in enumerate(raw):
        if skip: skip -= 1; continue
        s = re.sub(r'\s+', ' ', ln.replace('\xa0', ' ')).strip()
        if not s: continue
        cells = [c.strip() for c in s.split(' | ')]
        low = cells[0].lower()
        if len(cells) == 1 or all(pnum(c) is None for c in cells[1:]):
            # titles can be split over several short lines ("Reconciliation" / "of Total Revenue Growth ...")
            cand, t, used = re.sub(r'^caci international inc\.?,?\s*', '', low), None, 0
            for k in range(0, 4):
                if k:
                    if i + k >= len(raw): break
                    nx = re.sub(r'\s+', ' ', raw[i + k].replace('\xa0', ' ')).strip()
                    if ' | ' in nx or len(nx) > 90 or len(s) > 90: break
                    cand = (cand + ' ' + nx.lower()).strip()
                t = next((kk for kk, p in TITLES if p.search(cand)), None)
                if t: used = k; break
            if t and len(cand) < 220 and not re.match(r'^\*|^see ', low):
                sec = None if t == 'end' else t
                blk, mode, months, pend_hdr = None, None, None, [cand]
                skip = used
                continue
        if sec is None: continue
        vals = [pnum(c) for c in cells[1:]]
        is_data = len(cells) >= 2 and any(x is not None for x in vals) and pnum(cells[0]) is None and not DATE.match(cells[0]) \
            and not all(DATE.match(c) or pnum(c) is None for c in cells[1:])
        if is_data and re.fullmatch(r'\(?(dollars |amounts |shares )?in (thousands|millions).*', low): is_data = False
        if not is_data:
            prev_text = cells[0] if len(cells) == 1 else None
            q, y = QW.search(s), YW.search(s)
            if q or y:
                mode = 'QY' if (q and y) else ('Q' if q else 'Y')
                if y: months = MONTHS[y.group(0).split()[0].lower()]
                elif q and not y: months = 3
                pend_hdr = [s]; blk = None
            else:
                pend_hdr.append(s)
            continue
        if blk is None:
            if mode is None: mode = 'I'
            newblk()
        if prev_text and cells[0][:1].islower() and len(prev_text) < 120:
            cells[0] = prev_text + ' ' + cells[0]
        prev_text = None
        res = resolve(vals, mode) if mode != 'I' else None
        blk['rows'].append((norm(cells[0]), vals, res))
    return out

def find(blocks, rx, which='first'):
    """first (or all) rows whose label matches rx across the blocks of a section -> (block, label, vals, resolved)."""
    p = re.compile(rx, re.I)
    hits = [(b, l, v, r) for b in blocks or [] for l, v, r in b['rows'] if p.search(l)]
    return hits if which == 'all' else (hits[0] if hits else None)

if __name__ == '__main__':
    import sys
    d = parse(sys.argv[1])
    for k, bl in d['sections'].items():
        for b in bl:
            print(f'== {k} mode={b["mode"]} months={b["months"]} hdr={b["hdr"][:3]}')
            for l, v, r in b['rows']: print('   ', l[:70], '|', v, '->', r)
