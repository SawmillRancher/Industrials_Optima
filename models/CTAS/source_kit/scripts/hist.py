import json,re
D=json.load(open('edgar/canon.json')); S=json.load(open('edgar/segments.json'))
MONQ={1:'Aug',2:'Nov',3:'Feb',4:'May'}
def pend(fy,q):
    y=fy-1 if q in (1,2) else fy
    d={1:31,2:30,3:28,4:31}[q]
    if q==3 and (y%4==0): d=29
    return f"{y}-{MONQ[q]}-{d:02d}"
periods=[f'FY{y}' for y in range(2006,2027)]+[f'FY{y}Q{q}' for y in range(2013,2028) for q in range(1,5) if not (y==2027 and q>1)]
H={}
def is_keys(i):
    o={}
    o['rev_urfs_line']=i.get('rev_rental'); o['rev_other_line']=i.get('rev_other'); o['rev']=i['rev_total']
    o['cogs_urfs']=i.get('cogs_rental'); o['cogs_other']=i.get('cogs_other'); o['sga']=i['sga']
    trans=0; opo=0; nonop=0; eqat=0; seen_oi='oi' in i; after_oi=False; after_tax=False
    for k,v in i.items():
        if k=='oi': after_oi=True
        if k=='tax': after_tax=True
        if not k.startswith('spec:'): continue
        lk=k.lower()
        if after_tax: eqat+=v; continue
        if seen_oi: operating = not after_oi
        else: operating = bool(re.search(r'restructuring|impairment|legal|write-off|g&k|inventory',lk))
        if operating:
            if 'g&k' in lk or 'unifirst' in lk: trans+=v
            else: opo+=v
        else: nonop+=v
    o['sp_trans']=trans; o['sp_other_op']=opo; o['nonop_gain']=nonop; o['eq_at']=eqat
    o['oi']=i.get('oi', i['rev_total']-i['cogs_rental']-i['cogs_other']-i['sga']-trans-opo)
    o['int_inc']=-i['int_inc']; o['int_exp']=i['int_exp']; o['pbt']=i['pbt']; o['tax']=i['tax']
    o['ni_cont']=i.get('ni_cont',i['ni']); o['disc']=i.get('disc',0.0); o['ni']=i['ni']
    o['eps_basic']=i['eps_basic']; o['eps_dil']=i['eps_dil']
    o['eps_dil_cont']=i.get('epsc:continuing operations#dil',i['eps_dil'])
    o['sh_basic']=i['sh_basic']; o['sh_dil']=i['sh_dil']
    return o
for p in periods:
    d=D.get(p,{}); h={}
    if 'is' in d: h.update(is_keys(d['is']))
    if 'bs' in d:
        b=d['bs']; h.update({'bs_'+k:v for k,v in b.items() if not k.startswith('_') and ':' not in k})
        for k,v in b.items():
            if ':' in k: h.setdefault('bs_unmapped',[]).append((k,v))
    if 'cf' in d:
        h.update({'cf_'+k:v for k,v in d['cf'].items() if not k.startswith('_')})
    H[p]=h
# segments: current basis (FY2015+) from release where period is current, FY2015 quarters from 2015-09-24 restatement, FY2015 annual from 2016-07-19
def segrow(blk):
    out={}
    names={'Uniform Rental and Facility Services':'urfs','First Aid and Safety Services':'fas','All Other':'oth','Corporate':'corp','Total':'tot',
           'Rental Uniforms and Ancillary Products':'l_rental','Rental Uniforms & Ancillary Products':'l_rental','Uniform Direct Sales':'l_uds','First Aid, Safety and Fire Protection':'l_fasfp','First Aid, Safety & Fire Protection':'l_fasfp','Document Management':'l_doc'}
    for lab,vals in blk.items():
        ll=lab.lower()
        key=('rev' if ll=='revenue' else 'gm' if ll=='gross margin' else 'sga' if ll.startswith('selling') else 'oi' if ll.startswith('operating income') else 'pbt' if 'before income taxes' in ll else
             'assets' if ll=='assets' else 'iinc' if ll=='interest income' else 'iexp' if ll=='interest expense' else 'spec')
        for nm,v in vals.items():
            s=names.get(nm.strip())
            if not s: continue
            kk=f'seg_{s}_{key}'
            out[kk]=out.get(kk,0)+v/1000
    return out
def find_seg(fy,q,per):
    pe=pend(fy,q); key=f'{per}|{pe}'
    # first release reporting this period as current
    cands=sorted(S.keys())
    if fy==2015:
        for r in ('2015-09-24','2015-12-21','2016-03-22','2016-07-19'):
            if key in S[r]: return segrow(S[r][key]),r
    for r in cands:
        if r< f'{fy-1}-06-01': continue
        if key in S[r]:
            return segrow(S[r][key]),r
    return None,None
for p in periods:
    fy=int(p[2:6]); q=int(p[-1]) if 'Q' in p else 4
    per='three' if 'Q' in p else 'twelve'
    s,r=find_seg(fy,q,per)
    if s: H[p].update(s); H[p]['seg_src']=r
json.dump(H,open('edgar/hist.json','w'),indent=1)
# report
for p in periods:
    h=H[p]
    print(p, 'rev',round(h.get('rev',0),1),'oi',round(h.get('oi',0),1),'trans',round(h.get('sp_trans',0),2),'opo',round(h.get('sp_other_op',0),2),'nonop',round(h.get('nonop_gain',0),2),'eqat',round(h.get('eq_at',0),2),
      'seg', 'urfs' if 'seg_urfs_rev' in h else ('legacy' if 'seg_l_rental_rev' in h else '-'), round(h.get('seg_urfs_rev',h.get('seg_l_rental_rev',0)),1), h.get('seg_src'), 'unm' if 'bs_unmapped' in h else '')
