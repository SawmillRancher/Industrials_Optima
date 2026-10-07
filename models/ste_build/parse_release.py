"""Parse a STERIS earnings release (8-K Ex. 99.1, text form from h2t.py) into sections of table rows.

Sections are keyed by the statement titles printed in every release since FY2012:
IS (Statements of Income / Operations), BS (Balance Sheets), SEG (Segment Data), CF (Statements of Cash Flows),
FCF (Calculation of Free Cash Flow), NG (Non-GAAP Financial Measures, incl. "(Continued)"), SUP (Unaudited Supplemental
Financial Data). Each row: (label, [values], context) where context is the list of recent non-table header lines.
Values: '(1,234' / '(1,234)' -> -1234; '—' -> 0.0; 'n/a', 'na' -> None.
"""
import re

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('`', '').strip()
    if t in ('—', '–', '-', '―', '— —'): return 0.0
    if t.lower() in ('n/a', 'na', 'nm', 'n/m'): return None
    neg = t.startswith('(') or t.startswith('-(')
    t = t.strip('()-').replace(',', '').strip()
    if not re.fullmatch(r'\d+(\.\d+)?', t): return 'X'
    v = float(t)
    return -v if neg else v

SECTIONS = [('IS', r'^Consolidated (Condensed )?Statements? of (Income|Operations)'), ('BS', r'^Consolidated (Condensed )?Balance Sheets?'),
            ('SEG', r'^Segment Data\s*$'), ('CF', r'^Consolidated (Condensed )?Statements? of Cash Flows'), ('FCF', r'^Calculation of Free Cash Flow'),
            ('NG', r'^Non-GAAP (Financial Measures|Earnings Per Share)'), ('SUP', r'^Unaudited Supplemental Financial Data')]

def _prep(txt):
    txt = re.sub(r'\n\s*Non-GAAP\s*\n\s*Financial Measures', '\nNon-GAAP Financial Measures', txt)
    return txt

def sections(txt):
    """-> {section: [rows]}; a section starts at its title line and runs to the next title (first IS title only after the narrative)."""
    out, cur, ctx = {}, None, []
    started = False
    for line in _prep(txt).splitlines():
        s = line.strip()
        if not s: continue
        if '|' not in s:
            for name, pat in SECTIONS:
                if re.match(pat, s, re.I) and len(s) < 120:
                    if name == 'IS': started = True
                    if started:
                        cur = name; out.setdefault(cur, []); ctx = []
                    break
            else:
                if cur: ctx = (ctx + [s])[-14:]
            continue
        if not cur: continue
        cells = [c.strip() for c in s.split('|')]
        lab, vals = cells[0], [pnum(c) for c in cells[1:]]
        if not vals or pnum(lab) not in ('X',) or 'X' in vals:
            ctx = (ctx + [s])[-14:]
            continue
        out[cur].append((lab, vals, list(ctx)))
    return out

def units(txt):
    """'k' if the statements are in thousands (to FY2026), 'm' if in millions (from Q1 FY2027)."""
    m = re.search(r'\(([^)]*)(in thousands|in millions)', txt, re.I)
    return 'm' if m and 'millions' in m.group(2).lower() else 'k'

# ---------------------------------------------------------------- column-aligned matrix tables (Non-GAAP reconciliations)
def _cells(tr):
    out, c = [], 0
    for td in tr.find_all(['td', 'th']):
        span = int(td.get('colspan', 1) or 1)
        out.append((c, c + span - 1, re.sub(r'\s+', ' ', td.get_text(' ', strip=True).replace('\xa0', ' ')).strip()))
        c += span
    return out

MEAS = [('gp', r'^Gross Profit'), ('op', r'^Income from Operations'), ('ni_cont', r'^Income from continuing operations|^Income, net of income tax'),
        ('disc', r'from discontinued operations, net'), ('ni_attr', r'^Net (income|\(loss\) income|income \(loss\)) attributable'),
        ('eps_cont', r'^Diluted EPS from continuing'), ('eps_disc', r'^Diluted EPS from discontinued'), ('eps', r'^Diluted EPS')]

def matrix_tables(html):
    """Non-GAAP reconciliation matrices (FY2016+ releases): measures across, adjustments down. A <table> may hold several
    blocks (three months / twelve months); a block starts at each row of fiscal years.
    -> [{'period': text, 'meas': [key..], 'rows': [(label, {(meas, 0|1): value})]}] ; 0 = current year, 1 = prior year."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    res = []
    for t in soup.find_all('table'):
        trs = t.find_all('tr')
        prev = t.find_previous(string=re.compile(r'(Three|Six|Nine|Twelve) months ended', re.I))
        period = prev.strip() if prev else ''
        meas, blk = None, None
        for tr in trs:
            cells = [x for x in _cells(tr) if x[2]]
            if not cells: continue
            txts = [x[2] for x in cells]
            pt = ' '.join(txts)
            m = re.search(r'(Three|Six|Nine|Twelve) months ended', pt, re.I)
            if m and len(pt) < 200: period = pt
            names = [x for x in cells if any(re.search(p, x[2], re.I) for _, p in MEAS)]
            if len(names) >= 3 and not any(pnum(x) not in ('X', None) for x in txts[1:]):
                meas = [next(k for k, p in MEAS if re.search(p, x[2], re.I)) for x in names]
                continue
            if meas and len(cells) >= 4 and all(re.fullmatch(r'\d{4}', x) for x in txts):
                spans = [(meas[j // 2], j % 2, x[0], x[1]) for j, x in enumerate(cells) if j // 2 < len(meas)]
                blk = {'period': period, 'meas': list(meas), 'rows': [], 'spans': spans}
                res.append(blk); continue
            if not blk: continue
            lab = txts[0]
            vals = {}
            for c0, c1, txt in cells[1:]:
                v = pnum(txt)
                if v == 'X' or v is None: continue
                inside = [sp for sp in blk['spans'] if sp[2] <= c0 <= sp[3]]
                sp = inside[0] if inside else min(blk['spans'], key=lambda sp: min(abs(c0 - sp[2]), abs(c0 - sp[3])))
                vals[(sp[0], sp[1])] = v
            if vals: blk['rows'].append((lab, vals))
    for b in res: b.pop('spans', None)
    return res
