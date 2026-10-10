import json,re
E=json.load(open('edgar/extract.json'))
MON={'Aug':1,'Nov':2,'Feb':3,'May':4}
def fyq(pend):
    y,m,d=pend.split('-'); y=int(y)
    q=MON[m]; fy=y if m in ('Feb','May') else y+1
    return fy,q
def split_factor(release): return 1 if release>='2024-09-25' else 4
def mapbs(bs):
    out={}; sec='ca'; extra={}
    for lab,v in bs.items():
        l=re.sub(r'#\d$','',lab).lower().replace('&','and')
        if lab.startswith('<total>'):
            if sec in ('nca','ca'): out['ta']=v; sec='cl'
            else: out['tle']=v; sec='done'
            continue
        if sec=='done': continue
        if l.startswith('total current assets'): out['tca']=v; sec='nca'; continue
        if l.startswith('total current liabilities'): out['tcl']=v; sec='ltl'; continue
        if l.startswith('total long-term liabilities'): out['tltl']=v; sec='eq'; continue
        if 'total shareholders' in l: out['te']=v; continue
        if l in ('current','deferred') and sec=='cl':
            key='cl_taxes' if l=='current' else 'cl_deftax'
        elif sec=='ca':
            key=('cash' if 'cash' in l else 'mktsec' if 'marketable' in l else 'ar' if 'receivable' in l else 'inv' if l.startswith('inventor') else
                 'uniforms' if 'uniforms' in l else 'ca_taxes' if 'income taxes' in l else 'ca_deftax' if 'deferred tax' in l else
                 'ca_hfs' if 'held for sale' in l else 'prepaid' if 'prepaid' in l else 'ca_other:'+lab)
        elif sec=='nca':
            key=('ppe' if 'property' in l else 'invest' if l.startswith('investments') else 'gw' if 'goodwill' in l else 'svc' if 'service contracts' in l else
                 'rou' if 'right-of-use' in l else 'nca_hfs' if 'held for sale' in l else 'oth_assets' if 'other assets' in l else 'nca_other:'+lab)
        elif sec=='cl':
            key=('ap' if 'accounts payable' in l else 'accr_comp' if 'compensation' in l else 'accr_liab' if 'accrued liabilities' in l else
                 'cl_taxes' if 'income taxes' in l else 'cl_deftax' if 'deferred tax' in l else 'cl_hfs' if 'held for sale' in l else
                 'cl_lease' if 'lease' in l else 'debt_st' if 'debt' in l else 'cl_other:'+lab)
        elif sec=='ltl':
            key=('debt_lt' if 'debt' in l else 'deftax' if 'deferred income taxes' in l else 'lt_lease' if 'lease' in l else 'lt_accr' if 'accrued' in l else 'ltl_other:'+lab)
            if l.startswith('preferred') or l.startswith('common') or 'retained' in l or 'treasury' in l or 'paid' in l or 'comprehensive' in l or 'translation' in l or 'unrealized' in l or 'shares' in l or l=='other':
                sec='eq'
        if sec=='eq':
            key=('pref' if 'preferred' in l or 'authorized, none' in l else 'cs' if l.startswith('common') or 'shares outstanding' in l or 'issued and' in l else 'apic' if 'paid' in l else
                 're' if 'retained' in l else 'treas' if 'treasury' in l or re.search(r'^fy ?\d+: [\d,]+(;| shares)|^[\d,]+ shares$',l) else 'aoci' if 'comprehensive' in l or 'translation' in l or 'unrealized' in l or l=='other' else 'eq_other:'+lab)
            if key=='cs':
                m=re.search(r'issued and ([\d,]+)\s*(shares )?outstanding',lab)
                if m: extra['so_label']=float(m.group(1).replace(',',''))
        out[key]=out.get(key,0)+v
    out.update(extra); return out
def mapcf(cf):
    out={}; sec='op'
    for lab,v in cf.items():
        if lab=='_per': continue
        l=re.sub(r'#\d$','',lab).lower()
        if re.search(r'net cash (provided by|used in|\(used in\) provided by|provided by \(used in\)) operating',l): out['cfo']=v; sec='inv'; continue
        if re.search(r'net cash .*investing',l): out['cfi']=v; sec='fin'; continue
        if re.search(r'net cash .*financing',l): out['cff']=v; sec='post'; continue
        if 'effect of exchange' in l: out['fx']=v; continue
        if re.search(r'net (increase|decrease|\(decrease\)|\(decrease\) increase|increase \(decrease\)).*cash',l): out['netchg']=v; continue
        if 'at beginning' in l: out['cash_beg']=v; continue
        if 'at end' in l: out['cash_end']=v; continue
        if sec=='op':
            if l in ('net income','income'): k='ni'
            elif l.startswith('depreciation'): k='dep'
            elif l.startswith('amortization'): k='amort'
            elif 'stock-based compensation' in l or l=='compensation': k='sbc'
            elif 'deferred income taxes' in l: k='deftax'
            elif re.search(r'receivable|inventor|uniforms|rental items|prepaid|accounts payable|payable|compensation and related|accrued liabilities|income taxes|^expenses$|^net$|^and other$|^taxes$',l): k='wc'
            else: k='op_other'
        elif sec=='inv':
            if 'capital expenditures' in l or l=='expenditures': k='capex'
            elif 'acquisitions of businesses' in l or 'of businesses' in l: k='acq'
            elif 'marketable' in l or 'investments' in l and 'purchase' in l or l.startswith('purchases of investments'): k='mktsec'
            elif l.startswith('proceeds'): k='divest'
            else: k='inv_other'
        elif sec=='fin':
            if 'repurchase of common' in l or l=='of common stock': k='buyback'
            elif 'dividends paid' in l or l=='paid': k='div'
            elif 'issuance of debt' in l or 'from issuance of debt' in l: k='debt_iss'
            elif 'repayment' in l or l=='of debt': k='debt_rep'
            elif 'commercial paper' in l: k='cp'
            elif 'exercise' in l or 'options exercised' in l or 'tax benefit on exercise' in l: k='opt'
            else: k='fin_other'
        else: k='post_other'
        out[k]=out.get(k,0)+v
    return out
data={}  # key: ('FY2013','Q1') etc
def put(key,sect,d): data.setdefault(key,{}).setdefault(sect,{}).update(d)
ytd={}
for rd,rec in sorted(E.items()):
    if rec['pend'].split('-')[1] not in MON: continue
    fy,q=fyq(rec['pend'])
    sf=split_factor(rd)
    def adj(isd):
        isd=dict(isd)
        for k in list(isd):
            if k.startswith('sh_'): isd[k]=isd[k]*sf/1000
            elif k.startswith('eps') : isd[k]=isd[k]/sf
            elif not k.startswith('x:'): isd[k]=isd[k]/1000
        return isd
    if 'is_three' in rec and fy>=2010: put(f'FY{fy}Q{q}','is',{**adj(rec['is_three']),'_src':rd})
    if 'is_twelve' in rec and q==4: put(f'FY{fy}','is',{**adj(rec['is_twelve']),'_src':rd})
    if 'bs' in rec:
        b=mapbs(rec['bs']); b={k:(v/1000 if k!='so_label' else v*sf/(1000 if v>1e6 else 1)) for k,v in b.items()}
        b['_src']=rd
        put(f'FY{fy}Q{q}','bs',b)
        if q==4: put(f'FY{fy}','bs',b)
    if 'cf' in rec:
        per=rec['cf'].get('_per'); c={k:v/1000 for k,v in mapcf(rec['cf']).items()}; c['_src']=rd; c['_per']=per
        ytd[(fy,q)]=c
        if q==4: put(f'FY{fy}','cf',c)
for (fy,q),c in ytd.items():
    exp={1:'three',2:'six',3:'nine',4:'twelve'}[q]
    if c['_per']!=exp: print('CF period mismatch',fy,q,c['_per']); continue
    if q==1: put(f'FY{fy}Q1','cf',c); continue
    p=ytd.get((fy,q-1))
    if not p or p['_per']!={1:'three',2:'six',3:'nine'}[q-1]: print('no prior ytd',fy,q); continue
    d={k:c.get(k,0)-p.get(k,0) for k in set(c)|set(p) if not k.startswith('_') and k not in ('cash_beg','cash_end')}
    d['cash_beg']=p.get('cash_end'); d['cash_end']=c.get('cash_end'); d['_src']=c['_src']
    put(f'FY{fy}Q{q}','cf',d)
json.dump(data,open('edgar/canon.json','w'),indent=1)
# checks
def chk(key):
    d=data[key]; msgs=[]
    i=d.get('is',{})
    if i:
        if 'rev_rental' in i and abs(i['rev_rental']+i['rev_other']-i['rev_total'])>0.01: msgs.append('rev')
        spec_op=sum(v for k,v in i.items() if k.startswith('spec:') )
        if 'oi' in i:
            calc=i['rev_total']-i['cogs_rental']-i['cogs_other']-i['sga']
            ops=[v for k,v in i.items() if k.startswith('spec:')]
            if abs(calc-sum_ops(i)-i['oi'])>0.01: msgs.append(f"oi calc {calc-sum_ops(i):.3f} vs {i['oi']:.3f}")
        nic=i.get('ni_cont',i.get('ni'))
        if abs(i['pbt']-i['tax']-nic - nonop_after(i))>0.01: msgs.append(f"ni {i['pbt']-i['tax']:.3f} vs {nic}")
    b=d.get('bs',{})
    if b and 'ta' in b and 'tle' in b and abs(b['ta']-b['tle'])>0.01: msgs.append('bs bal')
    if b and 'tca' in b:
        s=sum(v for k,v in b.items() if k in ('cash','mktsec','ar','inv','uniforms','ca_taxes','ca_deftax','ca_hfs','prepaid') or k.startswith('ca_other'))
        if abs(s-b['tca'])>0.01: msgs.append(f'tca {s:.3f} vs {b["tca"]:.3f}')
    c=d.get('cf',{})
    if c and all(k in c for k in ('cfo','cfi','cff')):
        if abs(c['cfo']+c['cfi']+c['cff']+c.get('fx',0)-c.get('netchg',0))>0.01: msgs.append('cf sum')
        if c.get('cash_beg') is not None and c.get('cash_end') is not None and abs(c['cash_beg']+c.get('netchg',0)-c['cash_end'])>0.01: msgs.append('cash roll')
        s=sum(v for k,v in c.items() if k in ('ni','dep','amort','sbc','deftax','wc','op_other'))
        if abs(s-c['cfo'])>0.01: msgs.append(f'cfo sum {s:.3f} vs {c["cfo"]:.3f}')
    return msgs
def sum_ops(i):
    # operating specials: those appearing before 'oi' in dict order
    s=0
    for k,v in i.items():
        if k=='oi': break
        if k.startswith('spec:'): s+=v
    return s
def nonop_after(i):
    s=0; seen_tax=False
    for k,v in i.items():
        if k=='tax': seen_tax=True; continue
        if seen_tax and k.startswith('spec:'): s+=v
    return s
for k in sorted(data, key=lambda x:(int(x[2:6]), x)):
    m=chk(k)
    if m: print(k, m)
print(len(data))
