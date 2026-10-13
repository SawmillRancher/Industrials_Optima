"""EDGAR HTML -> list of tables. Each table: {'ctx': text just before the table, 'rows': [[cell, ...], ...]} with cell text
whitespace-normalised and the '$' / ')' / '%' / empty layout cells dropped (a dropped ')' leaves '(25,433', which num() reads as
negative). Used by extract.py for the earnings releases (8-K Ex. 99.1), the 10-K / 10-Q statements and the segment recast 8-Ks."""
import re, sys, warnings
from bs4 import BeautifulSoup
warnings.filterwarnings('ignore')

_WS = re.compile(r'\s+')
DROP = {'', '$', ')', '%', ')%', '(', '*'}

def clean(t):
    return _WS.sub(' ', t.replace('\xa0', ' ').replace('​', '')).strip()

def tables(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style']): t.decompose()
    out = []
    for tb in s.find_all('table'):
        rows = []
        for tr in tb.find_all('tr'):
            cells = [clean(c.get_text(' ')) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c not in DROP]
            # join '(1,234' + ')' style splits and '%' suffix cells already dropped
            if cells: rows.append(cells)
        if not rows: continue
        # context: the text of up to ~6 preceding block elements
        ctx, n = [], 0
        for el in tb.find_all_previous(string=True):
            if el.find_parent('table') is not None and el.find_parent('table') is not tb: break
            tx = clean(el)
            if tx: ctx.append(tx); n += 1
            if n >= 8: break
        prev = ' '.join(' '.join(r) for r in out[-1]['rows'][-3:]) if out and len(out[-1]['rows']) <= 3 else ''
        out.append({'ctx': ' '.join(reversed(ctx)), 'rows': rows, 'prev': prev})
    return out

NUMRE = re.compile(r'^\(?-?\$?\s*\(?[\d,]*\.?\d+\)?%?\)?$')
def num(c):
    """'1,234' -> 1234.0; '(1,234' / '(1,234)' / '$(1,234)' -> -1234.0; '-' / '—' -> 0.0; otherwise None."""
    c = c.replace('$', '').replace(' ', '').replace(' ', '')
    if c in ('-', '—', '–', '—', '−'): return 0.0
    neg = c.startswith('(') or c.startswith('-') or c.startswith('−')
    c2 = c.strip('()').lstrip('-−').rstrip(')').replace(',', '')
    if c2.endswith('%'): return None
    try:
        v = float(c2)
    except ValueError:
        return None
    return -v if neg else v

def split_row(r):
    """(label, [numbers]) — label = leading non-numeric cells joined; numbers = the numeric cells after it."""
    lab, vals = [], []
    for c in r:
        v = num(c)
        if v is None and not vals: lab.append(c)
        elif v is not None: vals.append(v)
    return ' '.join(lab), vals

if __name__ == '__main__':
    for i, t in enumerate(tables(open(sys.argv[1], 'rb').read())):
        print(f'--- table {i}  ctx: {t["ctx"][-150:]}')
        for r in t['rows'][: int(sys.argv[2]) if len(sys.argv) > 2 else 60]:
            print('   ', ' | '.join(r))
