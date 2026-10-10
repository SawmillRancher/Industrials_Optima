"""Positional HTML-table reader for Boeing EDGAR documents (8-K Ex. 99.1 releases, 10-K / 10-Q).

Each <table> becomes a list of rows; every cell keeps its logical column span (colspan-aware), so a value can be assigned to the
period header it sits under even when neighbouring cells are empty (h2t-style text drops empty cells and misaligns sparse rows).

Row = (label, [(c0, c1, text)])   label = first text cell that is not a number; values = numeric-looking cells with spans.
"""
import re, warnings
from bs4 import BeautifulSoup
warnings.filterwarnings('ignore')

NUM = re.compile(r'^\(?\$?\s*\(?\s*-?[\d,]*\.?\d+\s*\)?\s*%?\)?$')
DASH = {'—', '–', '-', '— ', '--', '―'}


def clean(t):
    t = t.replace('\xa0', ' ').replace('​', '').replace(' ', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def parse_num(t):
    """'$1,234' -> 1234; '(1,234' / '(1,234)' -> -1234; '—' -> 0; '12.5%' -> 12.5. None if not a number."""
    t = clean(t)
    if t in DASH: return 0.0
    t2 = t.replace('$', '').replace(',', '').replace(' ', '').replace('%', '')
    neg = t2.startswith('(') or t2.startswith('-(')
    t2 = t2.strip('()-') if neg else t2.strip('()')
    if t2.startswith('-'):
        neg, t2 = True, t2[1:]
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


def is_num(t):
    t = clean(t)
    return t in DASH or bool(NUM.match(t)) or bool(NUM.match(re.sub(r'(?<=\d[.,]) (?=\d)', '', t)))


def tables(html):
    s = BeautifulSoup(html, 'lxml')
    out = []
    for tb in s.find_all('table'):
        rows = []
        for tr in tb.find_all('tr'):
            pos, cells = 0, []
            for td in tr.find_all(['td', 'th']):
                span = int(td.get('colspan', 1) or 1) if str(td.get('colspan', 1)).isdigit() else 1
                cells.append((pos, pos + span - 1, clean(td.get_text(' ', strip=True))))
                pos += span
            merged, pend = [], ''
            for c0, c1, t in cells:
                if t in ('(', '($', '$(', '$ (', '( $'):
                    pend = '('; continue
                if pend and t and t not in ('$', ')', '%', ')%'):
                    t = '(' + t.lstrip('$ ').lstrip('(') if is_num(t) else t
                    pend = ''
                merged.append((c0, c1, t))
            cells = [c for c in merged if c[2] not in ('', '$', ')', '%', ')%', '(')]
            if not cells: continue
            # merge "(" / "$" fragments: a value split into "(25,433" and ")" is already handled by dropping ")"
            label, vals = None, []
            if re.match(r'^7\d7(\b|[A-Za-z -])', cells[0][2]) and len(cells) > 1:      # program names (737, 787 ...) are labels
                label = cells[0][2]; cells_v = cells[1:]
            else:
                cells_v = cells
            for c0, c1, t in cells_v:
                if label is None and not is_num(t):
                    label = t; continue
                if is_num(t): vals.append((c0, c1, t))
                elif label is not None and not vals:
                    label = label + ' ' + t
            rows.append((label or '', vals, cells))
        if rows: out.append(rows)
    return out


def text_of(rows):
    return '\n'.join((r[0] + ' | ' + ' | '.join(v[2] for v in r[1])) for r in rows)


MONTHS = {'three': 3, 'six': 6, 'nine': 9, 'twelve': 12, '1st quarter': 3, '2nd quarter': 3, '3rd quarter': 3, '4th quarter': 3, 'first quarter': 3, 'second quarter': 3, 'third quarter': 3, 'fourth quarter': 3,
          'first half': 6, 'nine months': 9, 'full year': 12, 'year ended': 12, 'years ended': 12}
YEAR = re.compile(r'(?<!\d)(19|20)\d\d(?!\d)')
MDATE = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+((?:19|20)\d\d)')
MON = {m: i + 1 for i, m in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                                        'November', 'December'])}


def _months(t):
    t = t.lower()
    hits = []
    for k, v in MONTHS.items():
        for m in re.finditer(re.escape(k), t):
            hits.append((m.start(), v))
    hits.sort()
    return [v for _, v in hits]


def columns(rows):
    """Return [(c0, c1, months, year, date)] for the first header row of years / dates in a table, with months taken from the
    group-header row(s) above it (positional overlap). Balance-sheet tables give dates ('December 31 2013') and months=0."""
    for i, (lab, vals, cells) in enumerate(rows[:8]):
        yrs = [(c0, c1, t) for c0, c1, t in cells if YEAR.fullmatch(t.strip())]
        dts = [(c0, c1, t) for c0, c1, t in cells if MDATE.search(t)]
        if len(dts) >= 1 and (len(yrs) == 0 or len(dts) >= len(yrs)):
            out = []
            for c0, c1, t in dts:
                m = MDATE.search(t)
                out.append((c0, c1, 0, int(m.group(3)), f'{m.group(3)}-{MON[m.group(1)]:02d}-{int(m.group(2)):02d}'))
            return out, i
        if len(yrs) >= 1:
            # date header split over two rows: 'June 30' / 'December 31' above the years
            groups = []
            for lab2, vals2, cells2 in rows[max(0, i - 3):i]:
                for c0, c1, t in cells2:
                    ms = _months(t)
                    if ms: groups.append((c0, c1, ms[0]))
                    elif re.search(r'(January|March|June|September|December)\s+\d{1,2}', t) and not ms:
                        groups.append((c0, c1, 0))
            out = []
            if any(m for _, _, m in groups): groups = [g for g in groups if g[2]]
            gs = sorted({(g0, g1, m) for g0, g1, m in groups})
            if gs and len(yrs) % len(gs) == 0:          # equal consecutive chunks, in header order
                n = len(yrs) // len(gs)
                for k, (c0, c1, t) in enumerate(sorted(yrs)):
                    out.append((c0, c1, gs[k // n][2], int(t), None))
                return out, i
            for c0, c1, t in yrs:
                g = [m for g0, g1, m in groups if g0 <= c1 and c0 <= g1]
                out.append((c0, c1, g[0] if g else None, int(t), None))
            return out, i
    return [], None


def assign(cols, vals):
    """Map value cells to column indexes by span overlap, else nearest column end."""
    out = {}
    for c0, c1, t in vals:
        best, bd = None, 99
        for j, (h0, h1, *_r) in enumerate(cols):
            if h0 <= c1 and c0 <= h1: d = 0
            else: d = min(abs(c1 - h1), abs(c0 - h0))
            if d < bd: best, bd = j, d
        if best is not None and bd <= 3 and best not in out:
            out[best] = parse_num(t)
    return out
