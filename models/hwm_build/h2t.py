"""EDGAR HTML -> text: one line per table row, cells joined by ' | ' (empty / '$' / ')' / '%' cells dropped; whitespace inside
a cell collapsed so a label never breaks across lines). Known quirk: the closing ')' sits in its own cell, so '(25' is negative;
'—' is zero."""
import re, sys, warnings
from bs4 import BeautifulSoup
warnings.filterwarnings('ignore')

def _c(s): return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', '')).strip()

def html_to_text(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style']): t.decompose()
    for tr in s.find_all('tr'):
        if tr.find('tr'): continue                      # outer row of a nested table
        cells = [_c(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
        cells = [c for c in cells if c not in ('', '$', ')', '%', ')%', ')bps', 'bps')]
        tr.replace_with('\n' + ' | '.join(cells) + '\n')
    for p in s.find_all(['p', 'div']):
        if not p.find(['p', 'div', 'table']):
            p.replace_with('\n' + _c(p.get_text(' ')) + '\n')
    return re.sub(r'\n\s*\n+', '\n', s.get_text('\n'))

if __name__ == '__main__':
    print(html_to_text(open(sys.argv[1], 'rb').read()))
