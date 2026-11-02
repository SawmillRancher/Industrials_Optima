"""EDGAR HTML -> text: one line per table row, cells joined by ' | ' (empty / '$' / ')' / '%' cells dropped)."""
import re, sys, warnings
from bs4 import BeautifulSoup
warnings.filterwarnings('ignore')

def html_to_text(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style']): t.decompose()
    for tr in s.find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
        cells = [c for c in cells if c not in ('', '$', ')', '%', ')%')]
        tr.replace_with(' | '.join(cells) + '\n')
    return re.sub(r'\n\s*\n+', '\n', s.get_text('\n'))

if __name__ == '__main__':
    print(html_to_text(open(sys.argv[1], 'rb').read()))
