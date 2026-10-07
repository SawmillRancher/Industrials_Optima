import os, sys, re, warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from bs4 import BeautifulSoup
base=sys.argv[1]
for d in sorted(os.listdir(base)):
    p=os.path.join(base,d)
    if not os.path.isdir(p): continue
    for n in os.listdir(p):
        if not n.lower().endswith(('.htm','.html')) or n.startswith('R'): continue
        out=os.path.join(p,n+'.txt')
        if os.path.exists(out): continue
        html=open(os.path.join(p,n),'rb').read().decode('utf-8','ignore')
        soup=BeautifulSoup(html,'lxml')
        for t in soup(['script','style']): t.decompose()
        # tables -> pipe rows
        for tb in soup.find_all('table'):
            rows=[]
            for tr in tb.find_all('tr'):
                cells=[re.sub(r"\s+"," ",td.get_text(" ",strip=True).replace("\u200b","").replace("\xa0"," ")).strip() for td in tr.find_all(["td","th"])]
                cells=[c for c in cells if c not in ('','$',')','%','$ ')]
                if cells: rows.append(' | '.join(cells))
            tb.replace_with('\n[TABLE]\n'+'\n'.join(rows)+'\n[/TABLE]\n')
        txt=soup.get_text('\n').replace('\u200b','')
        txt=re.sub(r'\n\s*\n+','\n',txt)
        open(out,'w').write(txt)
