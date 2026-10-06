"""Build the DHR SEC filings index (filings.json in $DHR_SRC, filings.csv here) from EDGAR submissions (2006 onward)."""
import json, subprocess, os, time, csv
S = os.environ.get('DHR_SRC', '/tmp/dhr_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIK = '0000313616'

def jget(url, path):
    if not os.path.exists(path):
        subprocess.run(['curl', '-sS', '-A', UA, url, '-o', path], check=True); time.sleep(0.15)
    return json.load(open(path))

sub = jget(f'https://data.sec.gov/submissions/CIK{CIK}.json', os.path.join(S, 'sub.json'))
blocks = [sub['filings']['recent']]
for f in sub['filings'].get('files', []):
    blocks.append(jget(f'https://data.sec.gov/submissions/{f["name"]}', os.path.join(S, f['name'])))
out = []
for r in blocks:
    for i in range(len(r['form'])):
        f, d = r['form'][i], r['filingDate'][i]
        if d < '2006-01-01' or f not in ('10-K', '10-Q', '8-K', '8-K/A', '10-K/A'): continue
        items = r['items'][i] or ''
        if f.startswith('8-K') and not any(x in items for x in ('2.02', '2.01', '1.01', '8.01', '7.01')): continue
        out.append(dict(date=d, form=f, acc=r['accessionNumber'][i], primary=r['primaryDocument'][i], items=items,
                        report=r['reportDate'][i]))
out.sort(key=lambda o: o['date'], reverse=True)
for o in out:
    n = o['acc'].replace('-', '')
    p = os.path.join(S, 'docs', o['acc'] + '.idx.json')
    try:
        items = [x['name'] for x in jget(f'https://www.sec.gov/Archives/edgar/data/313616/{n}/index.json', p)['directory']['item']]
    except Exception as e:
        items = []; print('idx fail', o['acc'], e)
    o['files'] = [x for x in items if x.lower().endswith(('.htm', '.html', '.txt')) and not x.startswith('R') and 'index' not in x]
json.dump(out, open(os.path.join(S, 'filings.json'), 'w'), indent=1)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['filing_date', 'form', 'accession', 'items', 'period_of_report', 'primary_document', 'url'])
    for o in out:
        w.writerow([o['date'], o['form'], o['acc'], o['items'], o['report'], o['primary'],
                    f"https://www.sec.gov/Archives/edgar/data/313616/{o['acc'].replace('-', '')}/{o['primary']}"])
print(len(out), 'filings')
