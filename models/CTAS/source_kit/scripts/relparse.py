import re, json, sys, os
MONTHS='January|February|March|April|May|June|July|August|September|October|November|December'
DATE=re.compile(r'(%s)\s+(\d{1,2}),?\s*(\d{4})'%MONTHS)
def num(c):
    c=c.strip().replace('$','').replace(',','').replace('—','').strip()
    if c in ('','—','–','-','--','---'): return 0.0
    neg=c.startswith('(') or (c.startswith('-') and len(c)>1)
    c=c.strip('()').lstrip('-').rstrip(')').strip()
    if c.endswith('%'): c=c[:-1]
    try: v=float(c)
    except: return None
    return -v if neg else v
def section_of(ctx):
    s=' '.join(ctx).lower()
    for key,pat in [('seg','segment'),('bs','balance sheet'),('cf','cash flow'),('fcf','free cash flow'),('org','organic|workday'),('eps','earnings per share|diluted eps|eps'),('ebitda','ebitda'),('supp','supplemental data'),('is','statements? of (income|operations)')]:
        pass
    return s
def parse(path):
    lines=[re.sub(r'[ \t\u00a0\u2009\u202f]+',' ',l).strip() for l in open(path,encoding='utf-8',errors='ignore')]
    tables=[]; ctx=[]; cur=None; period_groups=None
    for ln in lines:
        if not ln: continue
        cells=[c.strip() for c in ln.split(' | ')] if ' | ' in ln else None
        if cells is None:
            if len(ln)<160: ctx.append(ln); ctx=ctx[-8:]
            if re.search(r'balance sheet',ln,re.I): period_groups=['bs']
            elif re.search(r'statements? of (income|operations|cash flows)|supplemental|segment',ln,re.I): period_groups=None
            j2=' '.join(ctx[-2:])
            if re.search(r'(Three|Six|Nine|Twelve)\s+Months\s+Ended',ln,re.I):
                period_groups=[m.lower() for m in re.findall(r'(Three|Six|Nine|Twelve)\s+Months',ln,re.I)]
            elif re.search(r'^Months Ended',ln,re.I) and re.search(r'(Three|Six|Nine|Twelve)$',ctx[-2] if len(ctx)>1 else '',re.I):
                period_groups=[re.search(r'(Three|Six|Nine|Twelve)$',ctx[-2],re.I).group(1).lower()]
            if len(ln)>=160: cur=None
            continue
        if any(re.search(r'(Three|Six|Nine|Twelve) Months Ended',c,re.I) for c in cells) and not any(num(c) is not None and not DATE.search(c) for c in cells[1:] if c):
            period_groups=[re.search(r'(Three|Six|Nine|Twelve)',c,re.I).group(1).lower() for c in cells if re.search(r'(Three|Six|Nine|Twelve) Months',c,re.I)]
            continue
        dates=[DATE.search(c) for c in cells]
        if sum(1 for d in dates if d)>=1 and sum(1 for c in cells if num(c) is not None and not DATE.search(c))==0:
            hdr=[]
            for c in cells:
                d=DATE.search(c)
                if d: hdr.append(('d',f"{d.group(3)}-{d.group(1)[:3]}-{int(d.group(2)):02d}"))
                elif re.search(r'%|chng|change|growth',c,re.I): hdr.append(('p',c))
                else: hdr.append(('x',c))
            hdr=[h for h in hdr if h[0]!='x']
            nd=sum(1 for h in hdr if h[0]=='d')
            pg=period_groups or ['instant']
            # assign period group to date columns
            per=[]; di=0
            for h in hdr:
                if h[0]=='d':
                    g=pg[min(di*len(pg)//max(nd,1),len(pg)-1)] if len(pg)>1 else pg[0]
                    per.append(g); di+=1
                else: per.append(None)
            cur={'ctx':list(ctx),'hdr':hdr,'per':per,'rows':[]}; tables.append(cur)
            continue
        if cur is None: continue
        label=cells[0]; vals=[num(c) for c in cells[1:]]
        if num(label) is not None and label.strip():  # unlabeled total row
            vals=[num(c) for c in cells]; label='<total>'
        vals=[v for v in vals if v is not None]
        if not vals: 
            ctx.append(label); continue
        hdr=cur['hdr']
        dcols=[i for i,h in enumerate(hdr) if h[0]=='d']
        if len(vals)==len(hdr): m={i:vals[i] for i in dcols}
        elif len(vals)==len(dcols): m={dcols[k]:vals[k] for k in range(len(dcols))}
        else: m={'?':vals}
        out={}
        for i,v in m.items():
            if i=='?': out['?']=v
            else: out[f"{cur['per'][i]}|{hdr[i][1]}"]=v
        cur['rows'].append((label,out))
    return tables
if __name__=='__main__':
    t=parse(sys.argv[1])
    for tb in t:
        print('## CTX:',' / '.join(tb['ctx'][-3:])[:150],'| HDR:',tb['hdr'],tb['per'])
        for r in tb['rows'][:200]: print('   ',r[0][:70],r[1])
