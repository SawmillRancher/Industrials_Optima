"""Build the CACI SEC filings index (filings.json in $CACI_SRC, filings.csv here) from the EDGAR submissions JSON
(CACI International Inc, CIK 16058). Indexed: 10-K, 10-Q, 8-K Item 2.02 earnings releases (Ex. 99.1) and the deal / financing
8-Ks (Items 1.01, 2.01, 2.03, 2.05, 7.01, 8.01) since Jul-2006 (the FY2006 year end)."""
import json, subprocess, os, sys, time, csv
S = os.environ.get('CACI_SRC', '/tmp/caci_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'model-build research@example.com')      # set SEC_UA to your own "name email"
CIK = '16058'
ITEMS = ('2.02', '1.01', '2.01', '2.03', '2.05', '7.01', '8.01')
START = '2006-07-01'

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
        if d < START: continue
        if f not in ('10-K', '10-Q', '8-K', '8-K/A', '10-K/A'): continue
        if f.startswith('8-K') and not any(it in r['items'][i] for it in ITEMS): continue
        acc = r['accessionNumber'][i]; n = acc.replace('-', '')
        p = os.path.join(S, 'docs', acc + '.idx.json')
        for k in range(6):
            if os.path.exists(p) and open(p, 'rb').read(1) == b'{': break
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/index.json', '-o', p]); time.sleep(0.25 * 2 ** k)
        items = [x['name'] for x in json.load(open(p))['directory']['item']]
        out.append(dict(cik=CIK, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i], report=r['reportDate'][i],
                        files=[x for x in items if x.lower().endswith(('.htm', '.html', '.txt')) and not x.startswith('R') and 'index' not in x]))
        time.sleep(0.22)
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
