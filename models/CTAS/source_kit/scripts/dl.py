import json, subprocess, time, os, sys
UA="Industrials Optima research payton.liske@gmail.com"
cik=sys.argv[1]; fl=json.load(open(sys.argv[2])); out=sys.argv[3]
os.makedirs(out,exist_ok=True)
def get(url,dest):
    if os.path.exists(dest) and os.path.getsize(dest)>500: return
    for i in range(4):
        r=subprocess.run(['curl','-sS','-A',UA,'-o',dest,url])
        if r.returncode==0 and os.path.getsize(dest)>500: break
        time.sleep(2**i)
    time.sleep(0.15)
man=[]
for x in fl:
    acc=x['accessionNumber'].replace('-','')
    base=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}"
    idx=f"{out}/{acc}_index.json"; get(base+"/index.json",idx)
    try: items=[i['name'] for i in json.load(open(idx))['directory']['item']]
    except Exception as e: print('ERR idx',x,e); continue
    want=[x['primaryDocument']]
    if x['form'].startswith('8-K'):
        want+= [n for n in items if n.lower().endswith(('.htm','.html','.txt')) and ('99' in n.lower() or 'ex' in n.lower()) and n!=x['primaryDocument'] and 'index' not in n.lower() and not n.startswith('R') and 'Financial_Report' not in n]
    files=[]
    for n in want:
        dest=f"{out}/{x['filingDate']}_{x['form'].replace('/','')}_{n}"
        get(base+"/"+n,dest); files.append(dest)
    man.append({**x,'files':files})
json.dump(man,open(f"{out}/manifest.json",'w'),indent=0)
print(len(man))
