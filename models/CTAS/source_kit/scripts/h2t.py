import sys,re,html
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore")
from bs4 import BeautifulSoup
s=BeautifulSoup(open(sys.argv[1],encoding='utf-8',errors='ignore').read(),'lxml')
for t in s(['script','style']): t.decompose()
for tr in s.find_all('tr'):
    cells=[re.sub(r'\s+',' ',c.get_text(' ',strip=True)).strip() for c in tr.find_all(['td','th'])]
    cells=[c for c in cells if c not in ('','$',')','%')]
    tr.replace_with(s.new_string('\n'+' | '.join(cells)+'\n'))
txt=s.get_text('\n')
txt=re.sub(r'\n\s*\n+','\n',txt)
print(txt)
