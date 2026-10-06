import json,re,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
R=json.load(open('edgar/releases.json'))
def norm(s): return re.sub(r'\s+',' ',s.replace('\xa0',' ')).strip()
def kind(tb):
    labs=[norm(r[0]).lower() for r in tb['rows']]
    j=' || '.join(labs)
    if 'goodwill' in j and ('retained earnings' in j or 'total current assets' in j): return 'bs'
    if re.search(r'net cash (provided by|used in) operating|net cash provided by operating',j) and 'capital expenditures' in j and ('depreciation' in j or 'net income' in j): return 'cf'
    if 'total revenue' in j and 'net income' in j: return 'is'
    if 'total gross margin' in j: return 'supp'
    if 'free cash flow' in j: return 'fcf'
    if 'eps' in j and ('excluding' in j or 'after above' in j): return 'adjeps'
    if 'workday' in j or 'organic' in j: return 'org'
    return 'other'
IS_MAP=[
 ('rev_rental', r'^(rentals|rental uniforms and ancillary products|uniform rental and facility services)$'),
 ('rev_other', r'^(other services|other)$'),
 ('rev_total', r'^total revenue$'),
 ('cogs_rental', r'^cost of (rentals|rental uniforms and ancillary products|uniform rental and facility services)$'),
 ('cogs_other', r'^cost of (other services|other)$'),
 ('sga', r'^selling and administrative expenses$'),
 ('oi', r'^operating income$'),
 ('int_inc', r'^interest income$'),
 ('int_exp', r'^interest expense$'),
 ('pbt', r'^income before income taxes$'),
 ('tax', r'^income taxes?$|^income tax \(benefit\) expense$'),
 ('ni_cont', r'^income from continuing operations$'),
 ('disc', r'^(\(loss\) )?(income|loss|income \(loss\)|\(loss\) income) from discontinued operations, net of tax'),
 ('ni', r'^net income$'),
 ('eps_basic', r'^basic earnings per share$'),
 ('eps_dil', r'^diluted earnings per share$'),
 ('sh_basic', r'^(basic shares outstanding|weighted average number of shares outstanding|basic weighted average common shares outstanding)$'),
 ('sh_dil', r'^(diluted shares outstanding|diluted average number of shares outstanding|diluted weighted average common shares outstanding)$'),
]
SPECIAL=r'restructuring|impairment|legal settlement|shredding|shred-it|g&k|gain on sale|write-off|unifirst|deconsolidation|equity method|cost method'
def pick(rows,key,prefer):
    out={}
    for lab,vals in rows:
        for pk in prefer:
            if pk in vals: out[lab]=vals[pk]; break
    return out
res={}
for rd,r in sorted(R.items()):
    tabs=r['tables']
    for tb in tabs: tb['kind']=kind(tb)
    # split BS tables that swallowed the cash-flow statement
    newt=[]
    for tb in tabs:
        if tb['kind']=='bs':
            idx=[i for i,(lab,v) in enumerate(tb['rows']) if norm(lab).lower() in ('net income','income') and i>5]
            if idx:
                i0=idx[0]
                cft={'ctx':tb['ctx'],'hdr':tb['hdr'],'per':tb['per'],'rows':tb['rows'][i0:],'kind':'cf'}
                tb['rows']=tb['rows'][:i0]; newt.append(cft)
    tabs=tabs+newt
    ist=[tb for tb in tabs if tb['kind']=='is']
    if not ist: print('NO IS',rd); continue
    # period end = first date col of first IS table
    first=ist[0]; dcols=[h[1] for h in first['hdr'] if h[0]=='d']; pend=dcols[0]
    rec={'release':rd,'pend':pend,'file':r['file']}
    for tb in ist:
        prev_eps=None
        for lab,vals in tb['rows']:
            l=norm(lab).lower()
            for per in ('three','twelve','six','nine'):
                k=f'{per}|{pend}'
                if k not in vals: continue
                tgt=rec.setdefault('is_'+per,{})
                # EPS split cont/disc after 'Basic earnings per share:' header rows
                field=None
                for f,pat in IS_MAP:
                    if re.search(pat,l): field=f; break
                if l in ('continuing operations','discontinued operations'):
                    field=None
                if field is None:
                    if re.search(SPECIAL,l): field='spec:'+norm(lab)
                    elif l in ('continuing operations','discontinued operations'):
                        field='epsc:'+l
                    else: field='x:'+norm(lab)
                if field.startswith('epsc:'):
                    n=sum(1 for kk in tgt if kk.startswith('epsc:'+l))
                    field=field+('#basic' if n==0 else '#dil')
                if field in tgt and not field.startswith('x:'): continue
                tgt[field]=vals[k]
    # balance sheet
    for tb in tabs:
        if tb['kind']=='bs':
            bs={}
            for lab,vals in tb['rows']:
                for kk,v in vals.items():
                    if kk.endswith(pend):
                        nl=norm(lab)
                        if nl in bs: nl=nl+'#2'
                        bs[nl]=v
            if bs: rec['bs']=bs; break
    # cash flow: YTD col for pend
    for tb in tabs:
        if tb['kind']=='cf':
            cf={}
            for lab,vals in tb['rows']:
                for kk,v in vals.items():
                    if kk.endswith(pend):
                        nl=norm(lab)
                        if nl in cf: nl=nl+'#2'
                        cf[nl]=v; cf['_per']=kk.split('|')[0]
            if cf.get('_per') in ('bs','instant',None):
                cf['_per']={'Aug':'three','Nov':'six','Feb':'nine','May':'twelve'}.get(pend.split('-')[1],'?')
            if cf: rec['cf']=cf; break
    for tb in tabs:
        if tb['kind']=='supp':
            s={}
            for lab,vals in tb['rows']:
                for kk,v in vals.items():
                    if kk.endswith(pend): s[kk.split('|')[0]+'|'+norm(lab)]=v
            rec.setdefault('supp',{}).update(s)
    for tb in tabs:
        if tb['kind'] in ('adjeps','org','fcf'):
            s={}
            for lab,vals in tb['rows']:
                for kk,v in vals.items():
                    if kk.endswith(pend) or kk.endswith('?'): s[kk.split('|')[0]+'|'+norm(lab)]=v
            rec.setdefault(tb['kind'],[]).append({'ctx':' / '.join(tb['ctx'][-3:]),'vals':s})
    res[rd]=rec
json.dump(res,open('edgar/extract.json','w'),indent=1)
for rd,rec in res.items():
    i3=rec.get('is_three',{}); 
    print(rd,rec['pend'],'rev',i3.get('rev_total'),'ni',i3.get('ni'),'bs',len(rec.get('bs',{})),'cf',rec.get('cf',{}).get('_per'),len(rec.get('cf',{})),'12m' if 'is_twelve' in rec else '')
