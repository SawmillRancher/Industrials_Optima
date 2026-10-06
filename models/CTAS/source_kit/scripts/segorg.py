import json,re,os,glob
res={}
fl=sorted(glob.glob('edgar/txt/*_10-[KQ]_*.txt'))
pat_seg=r'(Uniform Rental and Facility Services|First Aid and Safety Services)(?: reportable)? operating segment revenue.{0,400}?(?:organic (?:revenue )?growth(?: rate)? for (?:this|the) (?:reportable )?operating segment was|[Oo]rganic (?:revenue )?growth for this (?:reportable )?operating segment was) (-?\d+\.\d)%'
pat_oth=r'(?:organic (?:revenue )?growth(?: rate)? for other revenue was|[Oo]rganic growth for other revenue was) (-?\d+\.\d)%'
pat_tot=r'(?:[Tt]he organic (?:revenue )?growth rate.{0,200}?was|[Tt]otal organic revenue growth was|[Oo]rganic (?:revenue )?growth was) (-?\d+\.\d)%'
for f in fl:
    d=os.path.basename(f)[:10]; form=os.path.basename(f)[11:15]
    if d<'2013-01-01': continue
    t=re.sub(r'\s+',' ',open(f,encoding='utf-8').read())
    # restrict to MD&A
    i=t.find("Management’s Discussion"); i=t.find("Management's Discussion") if i<0 else i
    i2=[m.start() for m in re.finditer(r'Results of Operations',t)]
    seg={}
    for m in re.finditer(pat_seg,t):
        seg.setdefault(m.group(1),m.group(2))
    o=re.search(pat_oth,t); tot=re.search(pat_tot,t)
    res[d]={'form':form,'urfs':seg.get('Uniform Rental and Facility Services'),'fas':seg.get('First Aid and Safety Services'),'other':o.group(1) if o else None,'total':tot.group(1) if tot else None}
    print(d,form,res[d])
json.dump(res,open('edgar/segorg.json','w'),indent=1)
