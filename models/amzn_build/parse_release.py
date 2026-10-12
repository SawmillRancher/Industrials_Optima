"""Parse an Amazon earnings release (8-K Item 2.02, Ex. 99.1, converted to text by h2t.py) into typed tables.

Every Amazon release since 2006 prints the same family of schedules: consolidated statements of cash flows, operations and
(from 2012) comprehensive income, segment information, supplemental net sales by segment / product group, balance sheet,
supplemental financial information (TTM free cash flow, shares, net sales ex-F/X) and, from 2015, the free-cash-flow
reconciliations. Tables start at a header row ("Three Months Ended ...", "December 31, 2025 | ...", "Q2 2025 | Q3 2025 ...");
lines without a '|' inside a table are sub-headings (segment names such as "North America", "AWS").

Column order is fixed within each schedule: income statement / cash flow / segment tables print the current three months first,
then the prior-year three months, then year-to-date (Q2, Q3), trailing-twelve-month (cash flow) or twelve-month (Q4) columns
in current / prior pairs. Values: '(1,234' -> -1234; '—' -> 0.0. Amounts are USD millions as published.
"""
import re

HDR = re.compile(r'^(Three|Six|Nine|Twelve) Months Ended|^(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}(\s*\||\s*$)'
                 r'|^Q[1-4] \d{4} \|')
YEARS = re.compile(r'^(\d{4})( \| \d{4})+$')


def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace(' ', '')
    if t in ('—', '–', '-', '―', '--', '——'): return 0.0
    neg = t.startswith('(')
    t = t.strip('()').replace(',', '')
    if not re.fullmatch(r'-?\d+(\.\d+)?|-?\.\d+', t): return None
    v = float(t)
    return -v if neg else v


def tables(txt):
    """-> list of {'hdr': [header lines], 'rows': [(section, label, [values])]}"""
    out, cur, sec = [], None, ''
    for ln in txt.replace('\xa0', ' ').replace('\u2009', ' ').splitlines():
        ln = re.sub(r'\s+', ' ', ln).strip()
        if not ln: continue
        if HDR.search(ln) and (cur is None or cur['rows'] or len(cur['hdr']) > 3):
            cur = {'hdr': [ln], 'rows': []}; out.append(cur); sec = ''
            continue
        if cur is None: continue
        if YEARS.match(ln) and not cur['rows']:
            cur['hdr'].append(ln); continue
        if '|' not in ln:
            if ln.startswith('•') or ln.startswith('Page '):
                if cur['rows']: cur = None
            elif len(ln) < 70 and not re.match(r'^(Operating expenses|Non-operating|Total)', ln): sec = ln.rstrip(':').strip()
            continue
        cells = [c.strip() for c in ln.split('|') if c.strip() not in ('%)', '%', ')', ')%', '')]
        if len(cells) < 2:
            if len(cells) == 1 and len(cells[0]) < 70: sec = cells[0].rstrip(':')
            continue
        vals = [pnum(c) for c in cells]
        if all(v is not None for v in vals):                # unlabeled numeric row
            cur['rows'].append((sec, '', vals)); continue
        if not cur['rows'] and any(v is None for v in vals[1:]):
            cur['hdr'].append(ln); continue
        v = [pnum(c) for c in cells[1:]]
        if any(x is None for x in v) and all(x is not None or c.upper() in ('N/A', 'NA', 'NM') for x, c in zip(v, cells[1:])) and any(x is not None for x in v):
            ncol = len(cur['hdr'][0].split('|')) if cur['hdr'] else len(v)
            v = [None] * max(0, ncol - len(v)) + v           # blank leading cells are dropped by h2t: align right
            cur['rows'].append((sec, re.sub(r'(\s*\(\d\))+$', '', cells[0]).strip(), v)); continue
        if any(x is None for x in v):
            if cells[0] in ('•', '(1)', '(2)', '(3)', '(4)') or cells[0].startswith('('): cur = None
            continue
        cur['rows'].append((sec, re.sub(r'(\s*\(\d\))+$', '', cells[0]).strip(), v))
    return [t for t in out if t['rows']]


def labels(t): return [r[1] for r in t['rows']]


def find(tabs, pred):
    for t in tabs:
        if pred(t): return t
    return None


def classify(tabs):
    """-> dict of named tables."""
    has = lambda t, pat: any(re.search(pat, l, re.I) for l in labels(t))
    d = {}
    d['cf'] = find(tabs, lambda t: has(t, r'BEGINNING OF PERIOD') and has(t, r'END OF PERIOD'))
    d['is'] = find(tabs, lambda t: has(t, r'^(Total )?net sales$') and has(t, r'^Fulfillment$') and has(t, r'before income taxes'))
    d['seg'] = find(tabs, lambda t: has(t, r'segment operating|^Operating income|^Operating expenses|Direct segment')
                    and any(r[0] in ('North America', 'International') for r in t['rows']) and not has(t, r'^Media$|Online stores'))
    d['bs'] = find(tabs, lambda t: has(t, r'^Total assets$') and has(t, r"^Total liabilities and stockholders"))
    d['grp'] = find(tabs, lambda t: has(t, r'^Online stores'))
    d['media'] = find(tabs, lambda t: has(t, r'^Media$') and has(t, r'^Total (North America|International)$'))
    d['supp'] = [t for t in tabs if t['hdr'] and re.match(r'^Q[1-4] \d{4} \|', t['hdr'][0])]
    d['fcf'] = [t for t in tabs if has(t, r'^Free cash flow')]
    return d


def col_index(t, months, which='cur'):
    """index of the value column for a duration (3 / 6 / 9 / 12 months; 12 = 'Twelve Months Ended' in Q4 releases or TTM)."""
    h = ' '.join(t['hdr'])
    blocks = re.findall(r'(Three|Six|Nine|Twelve) Months', h)
    want = {3: 'Three', 6: 'Six', 9: 'Nine', 12: 'Twelve'}[months]
    if want not in blocks: return None
    i = 2 * blocks.index(want)
    yrs = next((re.findall(r'\d{4}', x) for x in t['hdr'] if YEARS.match(x)), None)
    if yrs and len(yrs) > i + 1:                    # from 2016 the releases print the prior year first
        cur_first = int(yrs[i]) > int(yrs[i + 1])
    else:
        cur_first = True
    return i + (0 if (which == 'cur') == cur_first else 1)


def bs_index(t, which='cur'):
    """balance sheet: column of the later (cur) or earlier (py) date."""
    yrs = re.findall(r'\b(?:19|20)\d{2}\b', ' '.join(t['hdr']))
    if len(yrs) < 2: return 0
    return 0 if (int(yrs[0]) >= int(yrs[1])) == (which == 'cur') else 1


def supp_index(t, q, y):
    """supplemental quarterly tables ('Q1 2025 | Q2 2025 | ... | Y/Y % Change') -> column of quarter q of year y."""
    cols = [c.strip() for c in t['hdr'][0].split('|')]
    k = f'Q{q} {y}'
    return cols.index(k) if k in cols else None


def rowmap(t, ci, sections=False):
    """label (or (section, label)) -> value at column ci; first occurrence wins within a section."""
    out = {}
    for sec, lab, v in t['rows']:
        if ci is None or ci >= len(v): continue
        k = (sec, lab) if sections else lab
        if k not in out: out[k] = v[ci]
    return out
