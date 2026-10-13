"""Build the Alphabet / Google SEC filings index (filings.json in $GOOG_SRC, filings.csv here) from the EDGAR submissions JSON of
both registrants: Google Inc. (CIK 1288776; 10-K / 10-Q to Q3-2015) and Alphabet Inc. (CIK 1652044; successor issuer from the
2-Oct-2015 holding-company reorganization, 10-K FY2015 onward). Indexed: 10-K, 10-Q, 8-K Item 2.02 earnings releases (Ex. 99.1)
and the deal / financing / capital 8-Ks (Items 1.01, 2.01, 2.03, 3.03, 5.03, 7.01, 8.01) since Jan-2006."""
import json, subprocess, os, time, csv
S = os.environ.get('GOOG_SRC', '/tmp/goog_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIKS = ('1288776', '1652044')
ITEMS = ('2.02', '1.01', '2.01', '2.03', '3.03', '5.03', '7.01', '8.01')

def get(url, p):
    for k in range(6):
        if os.path.exists(p) and os.path.getsize(p) > 50 and open(p, 'rb').read(1) == b'{': return json.load(open(p))
        subprocess.run(['curl', '-sS', '-A', UA, url, '-o', p]); time.sleep(0.25 * 2 ** k)
    raise RuntimeError(url)

def sub_files(cik):
    d = get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json', os.path.join(S, f'sub_{int(cik):010d}.json'))
    yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        yield get(f'https://data.sec.gov/submissions/{f["name"]}', os.path.join(S, f['name']))

out = []
for cik in CIKS:
    for r in sub_files(cik):
        for i in range(len(r['form'])):
            f, d = r['form'][i], r['filingDate'][i]
            if d < '2006-01-01' or f not in ('10-K', '10-Q', '8-K'): continue
            if f == '8-K' and not any(it in r['items'][i] for it in ITEMS): continue
            acc = r['accessionNumber'][i]; n = acc.replace('-', '')
            idx = get(f'https://www.sec.gov/Archives/edgar/data/{cik}/{n}/index.json', os.path.join(S, 'docs', acc + '.idx.json'))
            items = [x['name'] for x in idx['directory']['item']]
            out.append(dict(cik=cik, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=r['items'][i], report=r['reportDate'][i],
                            files=[x for x in items if x.lower().endswith(('.htm', '.html', '.txt', '.xml')) and not x.startswith('R')
                                   and 'index' not in x and not x.lower().startswith(('filingsummary', 'metalink'))]))
            time.sleep(0.15)
out.sort(key=lambda o: o['date'])
json.dump(out, open(os.path.join(S, 'filings.json'), 'w'), indent=1)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['filing_date', 'form', 'period', 'cik', 'accession', 'items', 'primary_document', 'exhibits', 'url'])
    for o in out:
        ex = ';'.join(x for x in o['files'] if x != o['primary'])
        w.writerow([o['date'], o['form'], o['report'], o['cik'], o['acc'], o['items'], o['primary'], ex,
                    f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{o['acc'].replace('-', '')}/{o['primary']}"])
print(len(out), 'filings')
