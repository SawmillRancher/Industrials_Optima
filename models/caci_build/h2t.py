"""EDGAR HTML -> text: one line per table row, cells joined by ' | ' (empty / '$' / ')' / '%' cells dropped).
Inline tags (span, font, b, i, a, ix:* ...) are unwrapped first so that inline-XBRL facts stay on the line of their sentence."""
import re, sys, warnings
from bs4 import BeautifulSoup
warnings.filterwarnings('ignore')
INLINE = {'span', 'font', 'b', 'i', 'u', 'a', 'sup', 'sub', 'em', 'strong', 'small', 'nobr'}

def html_to_text(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style', 'ix:header']): t.decompose()
    for t in s.find_all(True):
        if t.name in INLINE or t.name.startswith('ix:'): t.unwrap()
    s.smooth()
    for tr in s.find_all('tr'):
        cells = [re.sub(r'\s+', ' ', c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
        cells = [c for c in cells if c not in ('', '$', ')', '%', ')%')]
        tr.replace_with(' | '.join(cells) + '\n')
    txt = s.get_text('\n')
    txt = '\n'.join(re.sub(r'[ \t\xa0]+', ' ', l).strip() for l in txt.split('\n'))
    return re.sub(r'\n\s*\n+', '\n', txt)

if __name__ == '__main__':
    print(html_to_text(open(sys.argv[1], 'rb').read()))
