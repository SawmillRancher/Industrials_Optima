"""Build the STERIS SEC filings index (filings.json / filings.csv) from EDGAR submissions across the three registrants:
STERIS Corp (CIK 815065, to Nov-2015), STERIS plc (UK; later STERIS Ltd, CIK 1624899, Nov-2015 - Mar-2019) and
STERIS plc (Ireland, CIK 1757898, from Mar-2019). Set STE_SRC for the download folder."""
import json, subprocess, os, time, csv
S = os.environ.get('STE_SRC', '/tmp/ste_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIKS = {'815065': 'STERIS Corp', '1624899': 'STERIS plc (UK)', '1757898': 'STERIS plc (Ireland)'}
def sub_files(cik):
    p = os.path.join(S, f'sub_{cik}.json')
    if not os.path.exists(p):
        subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json', '-o', p], check=True)
    d = json.load(open(p)); yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        q = os.path.join(S, f['name'])
        if not os.path.exists(q):
            subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/{f["name"]}', '-o', q], check=True)
        yield json.load(open(q))
out = []
for cik in CIKS:
    for r in sub_files(cik):
        for i in range(len(r['form'])):
            f, d = r['form'][i], r['filingDate'][i]
            if d < '2011-04-01': continue
            if f not in ('10-K', '10-Q', '8-K'): continue
            if f == '8-K' and '2.02' not in r['items'][i]: continue
            acc = r['accessionNumber'][i]; n = acc.replace('-', '')
            p = os.path.join(S, 'docs', acc + '.idx.json')
            for k in range(6):
                if os.path.exists(p) and open(p, 'rb').read(1) == b'{': break
                subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/{cik}/{n}/index.json', '-o', p]); time.sleep(0.25 * 2 ** k)
            items = [x['name'] for x in json.load(open(p))['directory']['item']]
            out.append(dict(cik=cik, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i], report=r['reportDate'][i],
                            files=[x for x in items if x.lower().endswith('.htm') and not x.startswith('R') and 'index' not in x]))
out.sort(key=lambda o: o['date'])
json.dump(out, open(os.path.join(S, 'filings.json'), 'w'), indent=1)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['filing_date', 'registrant', 'form', 'period', 'accession', 'items', 'primary_document', 'url'])
    for o in out:
        w.writerow([o['date'], CIKS[o['cik']], o['form'], o['report'], o['acc'], o['items'], o['primary'],
                    f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{o['acc'].replace('-', '')}/{o['primary']}"])
print(len(out), 'filings')
