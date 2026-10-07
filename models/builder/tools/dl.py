import json, os, sys, time, requests, re
UA={"User-Agent":"IndustrialsOptima research admin@industrialsoptima.example"}
cik=sys.argv[1]; base=sys.argv[2]
idx=json.load(open(os.path.join(base,'index.json')))
S=requests.Session(); S.headers.update(UA)
def get(url):
    for k in range(5):
        try:
            r=S.get(url,timeout=60)
            if r.status_code==200: return r
            time.sleep(1+k*2)
        except Exception as e: time.sleep(2+k*2)
    raise RuntimeError(url)
for x in idx:
    d=os.path.join(base,f"{x['date']}_{x['form']}_{x['acc']}")
    if os.path.exists(os.path.join(d,'.done')): continue
    os.makedirs(d,exist_ok=True)
    acc=x['acc'].replace('-','')
    j=get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/index.json").json()
    for it in j['directory']['item']:
        n=it['name']; nl=n.lower()
        want = nl.endswith(('.htm','.html','.txt')) and not nl.startswith(acc[:10]) and 'index' not in nl
        if x['form']!='8-K':
            want = (n==x['doc']) or (nl.endswith('.htm') and ('ex13' in nl or 'ex-13' in nl or 'exhibit13' in nl))
        if want:
            r=get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{n}")
            open(os.path.join(d,n),'wb').write(r.content)
            time.sleep(0.15)
    open(os.path.join(d,'.done'),'w').write('1')
    print(d, os.listdir(d), flush=True)
