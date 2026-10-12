"""HTML -> text: one table row per line, cells joined by ' | ' (known quirk: a dropped ")" leaves "(25" = negative; "—" = zero)."""
import sys, re, warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
def html_to_text(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style']): t.decompose()
    for tr in s.find_all('tr'):
        cells = [re.sub(r'\s+', ' ', td.get_text(' ', strip=True)) for td in tr.find_all(['td', 'th'])]
        cells = [c for c in cells if c not in ('', '$', ')', '%')]
        tr.replace_with('\n' + ' | '.join(cells) + '\n')
    for b in s.find_all(['p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4']):
        b.insert_after('\n')
    t = s.get_text()
    t = re.sub(r'[ \t\xa0]+', ' ', t)
    return re.sub(r'\n\s*\n+', '\n', t)
if __name__ == '__main__':
    print(html_to_text(open(sys.argv[1], 'rb').read()))
