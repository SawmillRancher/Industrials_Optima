"""Build the LOAR SEC filings index (filings.json / filings.csv) from EDGAR submissions; set LOAR_SRC for the download folder."""
import json, subprocess, os, time, csv
S = os.environ.get('LOAR_SRC', '/tmp/loar_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
sub = os.path.join(S, 'sub.json')
if not os.path.exists(sub):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/submissions/CIK0002000178.json', '-o', sub], check=True)
r = json.load(open(sub))['filings']['recent']
out = []
for i in range(len(r['form'])):
    f = r['form'][i]
    if f not in ('10-K', '10-Q', '8-K', '8-K/A', 'S-1', '424B4', '424B7'): continue
    acc = r['accessionNumber'][i]; n = acc.replace('-', '')
    p = os.path.join(S, 'docs', acc + '.idx.json')
    if not os.path.exists(p):
        subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/2000178/{n}/index.json', '-o', p]); time.sleep(0.15)
    items = [x['name'] for x in json.load(open(p))['directory']['item']]
    out.append(dict(date=r['filingDate'][i], form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i],
                    files=[x for x in items if x.endswith('.htm') and not x.startswith('R') and 'index' not in x]))
json.dump(out, open(os.path.join(S, 'filings.json'), 'w'), indent=1)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['filing_date', 'form', 'accession', 'items', 'primary_document', 'url'])
    for o in out:
        w.writerow([o['date'], o['form'], o['acc'], o['items'], o['primary'],
                    f"https://www.sec.gov/Archives/edgar/data/2000178/{o['acc'].replace('-', '')}/{o['primary']}"])
print(len(out), 'filings')
