"""Build the RBC Bearings SEC filings index (filings.json in $RBC_SRC, filings.csv here) from the EDGAR submissions JSON
(RBC Bearings Incorporated, CIK 1324948; NYSE / Nasdaq: RBC; IPO Aug-2005). Indexed: 10-K, 10-Q, S-1 / 424B prospectuses and the
8-Ks with earnings releases (Item 2.02, Ex. 99.1) or deal / financing / restructuring items (1.01, 2.01, 2.03, 2.05, 7.01, 8.01)."""
import json, subprocess, os, time, csv
S = os.environ.get('RBC_SRC', '/tmp/rbc_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIK = '1324948'
ITEMS = ('2.02', '1.01', '2.01', '2.03', '2.05', '7.01', '8.01')
FORMS = ('10-K', '10-Q', '8-K', '10-K/A', '10-Q/A', '8-K/A', '424B4', '424B2', '424B5', 'S-1')

def sub_files():
    p = os.path.join(S, f'sub_{CIK}.json')
    if not os.path.exists(p):
        subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/CIK{int(CIK):010d}.json', '-o', p], check=True)
    d = json.load(open(p)); yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        q = os.path.join(S, f['name'])
        if not os.path.exists(q):
            subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/{f["name"]}', '-o', q], check=True)
        yield json.load(open(q))

out = []
for r in sub_files():
    for i in range(len(r['form'])):
        f, d = r['form'][i], r['filingDate'][i]
        if f not in FORMS: continue
        if f.startswith('8-K') and r['items'][i] and not any(it in r['items'][i] for it in ITEMS): continue
        acc = r['accessionNumber'][i]; n = acc.replace('-', '')
        p = os.path.join(S, 'docs', acc + '.idx.json')
        for k in range(6):
            if os.path.exists(p) and open(p, 'rb').read(1) == b'{': break
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/index.json', '-o', p]); time.sleep(0.25 * 2 ** k)
        items = [x['name'] for x in json.load(open(p))['directory']['item']]
        out.append(dict(cik=CIK, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i], report=r['reportDate'][i],
                        files=[x for x in items if x.lower().endswith(('.htm', '.html', '.txt')) and not x.startswith('R') and 'index' not in x and not x.endswith('-index-headers.html')]))
        time.sleep(0.15)
out.sort(key=lambda o: o['date'])
json.dump(out, open(os.path.join(S, 'filings.json'), 'w'), indent=1)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['filing_date', 'form', 'period', 'accession', 'items', 'primary_document', 'exhibits', 'url'])
    for o in out:
        ex = ';'.join(x for x in o['files'] if x != o['primary'])
        w.writerow([o['date'], o['form'], o['report'], o['acc'], o['items'], o['primary'], ex,
                    f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{o['primary']}"])
print(len(out), 'filings')
