"""Build the Union Pacific SEC filings index (filings.json in $UNP_SRC, filings.csv here) from the EDGAR submissions JSON
(Union Pacific Corporation, CIK 100885). Indexed: 10-K, 10-Q, 8-K Item 2.02 earnings releases (Ex. 99.1) and the deal /
financing / guidance 8-Ks (Items 1.01, 2.01, 2.03, 7.01, 8.01) since Jan-2006, plus the Norfolk Southern merger S-4 / 424B3."""
import json, subprocess, os, time, csv
S = os.environ.get('UNP_SRC', '/tmp/unp_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIK = '100885'
ITEMS = ('2.02', '1.01', '2.01', '2.03', '7.01', '8.01')
FORMS = ('10-K', '10-Q', '8-K', 'S-4', 'S-4/A', '424B3')

def get(url, p):
    for k in range(6):
        if os.path.exists(p) and open(p, 'rb').read(1) in (b'{', b'['): return
        subprocess.run(['curl', '-sS', '-A', UA, url, '-o', p]); time.sleep(0.25 * 2 ** k)

def sub_files():
    p = os.path.join(S, f'sub_{CIK}.json')
    get(f'https://data.sec.gov/submissions/CIK{int(CIK):010d}.json', p)
    d = json.load(open(p)); yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        q = os.path.join(S, f['name']); get(f'https://data.sec.gov/submissions/{f["name"]}', q)
        yield json.load(open(q))

out = []
for r in sub_files():
    for i in range(len(r['form'])):
        f, d = r['form'][i], r['filingDate'][i]
        if d < '2006-01-01': continue
        if f not in FORMS: continue
        if f == '8-K' and not any(it in r['items'][i] for it in ITEMS): continue
        if f in ('S-4', 'S-4/A', '424B3') and d < '2025-01-01': continue
        acc = r['accessionNumber'][i]; n = acc.replace('-', '')
        p = os.path.join(S, 'docs', acc + '.idx.json')
        get(f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/index.json', p)
        items = [x['name'] for x in json.load(open(p))['directory']['item']]
        out.append(dict(cik=CIK, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i], report=r['reportDate'][i],
                        files=[x for x in items if x.lower().endswith(('.htm', '.txt')) and not x.startswith('R') and 'index' not in x.lower()]))
        time.sleep(0.12)
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
