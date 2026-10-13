"""Build the source index (filings.csv) for the Mobility Global build from the EDGAR submissions JSON.

Two registrants:
- Mobility Global Inc. (CIK 2090312; "S&P Global Mobility Holding Co" until 21-Jan-2026): Form 10 drafts (DRS / DRS/A), Form 10
  (10-12B / 10-12B/A, information statement Ex. 99.1), 10-Q and 8-Ks (spin completion, earnings release Ex. 99.1, FY2025 quarterly
  financial-data file Ex. 99.2).
- S&P Global Inc. (CIK 64040): earnings releases (8-K Item 2.02, Ex. 99.1) since the IHS Markit merger (28-Feb-2022), which
  report the Mobility segment (memo series in the model).

One row per document used. Raw downloads go to $MBGL_SRC (outside the repo); run fetch.py next."""
import csv, json, os, subprocess, time, re

S = os.environ.get('MBGL_SRC', '/tmp/mbgl_src'); os.makedirs(S, exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
REG = {'MBGL': '2090312', 'SPGI': '64040'}

def get(url, path):
    for k in range(6):
        if os.path.exists(path) and os.path.getsize(path) > 200 and b'Request Rate Threshold' not in open(path, 'rb').read(3000):
            return path
        subprocess.run(['curl', '-sS', '-A', UA, url, '-o', path]); time.sleep(0.25 * 2 ** k)
    return path

def docs_of(cik, acc):
    n = acc.replace('-', '')
    p = get(f'https://www.sec.gov/Archives/edgar/data/{cik}/{n}/index.json', os.path.join(S, f'idx_{acc}.json'))
    return [x['name'] for x in json.load(open(p))['directory']['item']]

def pick(tick, form, items, files, primary):
    """documents used from each filing"""
    htm = [f for f in files if f.lower().endswith('.htm') and 'index' not in f.lower()]
    if tick == 'SPGI':
        return [f for f in htm if 'earningsrelease' in f.lower()][:1]
    if form in ('10-Q',):
        return [primary]
    if form in ('DRS', 'DRS/A'):
        return [f for f in htm if f in ('filename1.htm', 'filename2.htm')]
    if form in ('10-12B', '10-12B/A'):
        return [f for f in htm if re.search(r'ex99-1\.htm$', f)]
    if form == '8-K':
        return [primary] + [f for f in htm if re.search(r'(ex99|991|992)', f.lower()) and f != primary]
    return []

rows = []
for tick, cik in REG.items():
    sub = get(f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json', os.path.join(S, f'sub_{cik}.json'))
    r = json.load(open(sub))['filings']['recent']
    for i in range(len(r['form'])):
        form, date, acc, items = r['form'][i], r['filingDate'][i], r['accessionNumber'][i], r['items'][i]
        if tick == 'SPGI':
            if not (form == '8-K' and '2.02' in items and date >= '2022-04-01'): continue
        else:
            if form not in ('10-Q', '10-K', '8-K', 'DRS', 'DRS/A', '10-12B', '10-12B/A'): continue
        files = docs_of(cik, acc); time.sleep(0.15)
        for d in pick(tick, form, items, files, r['primaryDocument'][i]):
            rows.append(dict(registrant=tick, cik=cik, filing_date=date, form=form, period=r['reportDate'][i], accession=acc, items=items,
                             document=d, url=f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/{d}'))
rows.sort(key=lambda o: (o['registrant'], o['filing_date'], o['document']))
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), 'documents indexed')
