import re,json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from relparse import num, DATE
SEGW=r'(rental|uniform direct|first aid|document management|all other|corporate|total|fire protection)'
def parse_seg(path):
    lines=[re.sub(r'[ \t   ]+',' ',l).strip() for l in open(path,encoding='utf-8',errors='ignore')]
    out={}; cols=None; block=None
    for ln in lines:
        if not ln: continue
        cells=[c.strip() for c in ln.split(' | ')]
        lc=ln.lower()
        if ' | ' in ln and sum(1 for c in cells if re.search(SEGW,c,re.I) and num(c) is None)>=3:
            cs=[c for c in cells if not re.search(r'segment data|^\(in thousands\)$',c,re.I)]
            cols=[re.sub(r'\s*\(\d\)$','',c) for c in cs]; continue
        if cols is None: continue
        m=re.search(r'(three|six|nine|twelve) months ended\s+(.*)',lc)
        if m and ' | ' not in ln:
            d=DATE.search(ln)
            block=f"{m.group(1)}|{d.group(3)}-{d.group(1)[:3]}-{int(d.group(2)):02d}" if d else None; continue
        if re.search(r'balance sheet|statements of cash|^cintas corporation$',lc): cols=None; block=None; continue
        if block and ' | ' in ln:
            vals=[num(c) for c in cells[1:]]
            if any(v is None for v in vals) or len(vals)!=len(cols): 
                out.setdefault('_bad',[]).append(ln); continue
            out.setdefault(block,{})[cells[0]]=dict(zip(cols,vals))
    return out
if __name__=='__main__':
    man=json.load(open('edgar/releases.json'))
    res={}
    for d,r in sorted(man.items()):
        s=parse_seg(r['file'])
        res[d]=s
        print(d, [k for k in s if k!='_bad'], len(s.get('_bad',[])), (list(list(s.values())[0].values())[0].keys() if s and list(s.keys())[0]!='_bad' else ''))
    json.dump(res,open('edgar/segments.json','w'),indent=1)
