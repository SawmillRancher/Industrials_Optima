"""UPS earnings-release / 10-Q / 10-K text parser (text produced by h2t.py: one table row per line, cells joined by ' | ').

Release schedules are split on the 'United Parcel Service, Inc.' header line; each section carries a title ('Selected Financial
Data - Second Quarter', 'Selected Operating Data - Year to Date', 'Reconciliation of GAAP and Non-GAAP Adjusted Measures' ...) and
the number of months it covers. Rows are (label, [numbers]) with the h2t quirks handled: '(141' is negative, a dash is zero."""
import re

DASH = ('—', '–', '-', '— ', '—%', 'N/A', 'N/M', 'NM', 'n/a', 'nm')
NUM = re.compile(r'^\(?\$?\s*-?[\d,]*\.?\d+\)?%?$')
MONTHS = {'three': 3, 'six': 6, 'nine': 9, 'twelve': 12, 'year': 12, 'years': 12}


def num(s):
    """'1,234' -> 1234.0; '(141' / '(141)' -> -141.0; dash -> 0.0; text -> None."""
    s = s.strip().replace('\xa0', ' ')
    if s in ('—', '–', '-', '— %', '—%'): return 0.0
    t = s.replace('$', '').replace(' ', '').replace('%', '')
    if not t or not re.match(r'^\(?-?[\d,]*\.?\d+\)?$', t): return None
    neg = t.startswith('(') or t.startswith('-')
    v = float(t.strip('()-').replace(',', ''))
    return -v if neg else v


def cells(line):
    return [c.strip() for c in line.split(' | ')]


def row(line):
    """-> (label, [values]); values keep None for text cells (N/A)."""
    cs = cells(line)
    lab = cs[0]
    vals = []
    for c in cs[1:]:
        if c in ('N/A', 'N/M', 'NM', 'n/a', 'NA'): vals.append(None)
        else:
            v = num(c)
            if v is None and not vals: lab += ' | ' + c      # label continues
            else: vals.append(v)
    return lab.strip(), vals


def norm(lab):
    lab = re.sub(r'\(\d\)|\(\d\),?\s*\(?\d?\)?', '', lab)       # footnote markers
    lab = lab.replace('’', "'").replace('&amp;', '&')
    return re.sub(r'\s+', ' ', lab).strip().rstrip(':').strip().lower()


def sections(text):
    """Split a release into sections: [{'title', 'months', 'lines'}]."""
    lines = [l.rstrip() for l in text.split('\n')]
    idx = [i for i, l in enumerate(lines) if l.strip() == 'United Parcel Service, Inc.']
    out = []
    for a, b in zip(idx, idx[1:] + [len(lines)]):
        body = lines[a + 1:b]
        title = []
        for l in body[:4]:
            if l.strip().lower().startswith(('(unaudited', '(in millions', '(amounts')) or ' | ' in l: break
            title.append(l.strip())
        t = re.sub(r'\s+', ' ', ' '.join(title)).strip()
        head = ' '.join(body[:12]).lower()
        m = re.search(r'(three|six|nine|twelve) months\s+ended|(year|years) ended|year-to-date|year to date', head)
        months = None
        if m:
            months = MONTHS.get(m.group(1) or m.group(2))
        out.append({'title': t, 'months': months, 'lines': body, 'head': head})
    return out


def rows_of(sec):
    return [row(l) for l in sec['lines'] if ' | ' in l]


def find(secs, pat, months=None, n=0):
    hits = [s for s in secs if re.search(pat, s['title'], re.I) and (months is None or s['months'] == months)]
    return hits[n] if len(hits) > n else None


def block_rows(sec):
    """Rows with their block context: yields (block, label, values). A block header is a line without numbers ending in ':' or a
    known header (Revenue:, Operating expenses:, Operating profit:, 'As adjusted income data:' ...)."""
    blk = ''
    sub = ''
    for l in sec['lines']:
        s = l.strip()
        if not s: continue
        if ' | ' not in s or all(num(c) is None and c not in ('N/A',) for c in cells(s)[1:]):
            lab = norm(cells(s)[0])
            if s.rstrip().endswith(':') or lab in ('assets', "liabilities and shareowners' equity"):
                if lab in ('u.s. domestic package', 'international package', 'supply chain & freight', 'supply chain solutions',
                           'supply chain and freight'):
                    sub = lab
                else:
                    blk = lab; sub = ''
            continue
        lab, vals = row(s)
        yield blk, sub, norm(lab), vals


def statement(text, title_pat, end_pat, start=0):
    """Face statement rows from a 10-K / 10-Q: lines after the first line matching title_pat (searched from `start`) up to end_pat."""
    lines = text.split('\n')
    out = []; on = False
    for i, l in enumerate(lines):
        if i < start: continue
        if not on:
            if re.match(title_pat, l.strip()): on = True
            continue
        if ' | ' in l:
            out.append(row(l))
        if re.match(end_pat, l.strip(), re.I):
            return out, i
    return out, None
