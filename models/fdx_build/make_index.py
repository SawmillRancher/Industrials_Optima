"""Build the FedEx SEC filings index (filings.json in $FDX_SRC, filings.csv here) from the EDGAR submissions JSON
(FedEx Corporation, CIK 1048911). Indexed: 10-K, 10-Q, 10-KT, 8-K Item 2.02 earnings releases / recast exhibits (Ex. 99.1) and the
deal / financing / restructuring 8-Ks (Items 1.01, 2.01, 2.03, 2.05, 7.01, 8.01) since Jun-2006."""
import json, subprocess, os, time, csv
S = os.environ.get('FDX_SRC', '/tmp/fdx_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIK = '1048911'
ITEMS = ('2.02', '1.01', '2.01', '2.03', '2.05', '7.01', '8.01')

def get(url, p):
    for k in range(6):
        if os.path.exists(p) and open(p, 'rb').read(1) == b'{': return
        subprocess.run(['curl', '-sS', '-A', UA, url, '-o', p]); time.sleep(0.25 * 2 ** k)

def sub_files():
    p = os.path.join(S, f'sub_{CIK}.json')
    get(f'https://data.sec.gov/submissions/CIK{int(CIK):010d}.json', p)
    d = json.load(open(p)); yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        q = os.path.join(S, f['name'])
        get(f'https://data.sec.gov/submissions/{f["name"]}', q)
        yield json.load(open(q))

out = []
for r in sub_files():
    for i in range(len(r['form'])):
        f, d = r['form'][i], r['filingDate'][i]
        if d < '2006-06-01': continue
        if f not in ('10-K', '10-Q', '10-KT', '8-K'): continue
        if f == '8-K' and not any(it in r['items'][i] for it in ITEMS): continue
        acc = r['accessionNumber'][i]; n = acc.replace('-', '')
        p = os.path.join(S, 'docs', acc + '.idx.json')
        get(f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/index.json', p)
        items = [x['name'] for x in json.load(open(p))['directory']['item']]
        out.append(dict(cik=CIK, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i], report=r['reportDate'][i],
                        files=[x for x in items if x.lower().endswith(('.htm', '.html', '.txt')) and not x.startswith('R') and 'index' not in x]))
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
