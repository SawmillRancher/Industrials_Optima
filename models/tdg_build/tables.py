"""Raw HTML table reader for TransDigm EDGAR documents (10-K / 10-Q primary documents and 8-K Ex. 99.1 releases).

html_tables(html) -> [{'hdr': [header text rows], 'rows': [(label, [values])], 'pre': text before the table}]
A row is a value row when every cell after the label parses as a number; leading text-only rows form the header. A single-cell
title row inside a table ("Consolidated ... / Reconciliation of ...") starts a new logical table (several schedules in one <table>).
Values: '(1,234)' / '( 1,234 )' / '-1,234' -> -1234; '—', '–', '-' -> 0.0; '$', '%' and ')' cells are dropped. Amounts stay in the
document's units (parse_filing.py / extract.py resolve thousands vs millions)."""
import re
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace(' ', '').strip()
    if t in ('—', '–', '-', '―', '--', '——'): return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', ' ')).strip()

TITLE = re.compile(r'consolidated\s+(condensed\s+)?(statements?|balance)|reconciliation|segment net sales|calculation of', re.I)

def html_tables(html):
    soup = BeautifulSoup(html, 'lxml')
    out = []
    for t in soup.find_all('table'):
        prev = t.find_previous(string=re.compile(r'\S'))
        cur = {'hdr': [], 'rows': [], 'pre': _clean(prev) if prev else ''}
        tabs = [cur]
        for tr in t.find_all('tr'):
            cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c not in ('', '$', ')', '%', ')%')]
            if not cells: continue
            vals = [pnum(c) for c in cells[1:]]
            isyear = vals and all(v is not None and v == int(v) and 1990 <= v <= 2035 for v in vals) and ',' not in ''.join(cells[1:])
            if len(cells) >= 2 and all(v is not None for v in vals) and pnum(cells[0]) is None and not isyear:
                cur['rows'].append((cells[0], vals))
            elif len(cells) == 1 and TITLE.search(cells[0]) and cur['rows']:
                cur = {'hdr': [cells[0]], 'rows': [], 'pre': cells[0]}; tabs.append(cur)
            elif not cur['rows']:
                cur['hdr'].append(' | '.join(cells))
            else:
                cur['rows'].append((' | '.join(cells), []))       # in-table sub-heading
        out.extend(x for x in tabs if x['rows'])
    return out
