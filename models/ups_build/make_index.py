"""Build the UPS SEC filings index (filings.json in $UPS_SRC, filings.csv here) from the EDGAR submissions JSON
(United Parcel Service, Inc., CIK 1090727; the Delaware registrant since the 1999 IPO — no predecessor CIK is needed for 2006+).

Indexed: 10-K (FY2006+), 10-Q (2012+), 8-K Item 2.02 earnings releases (Ex. 99.1; from the Q4-2006 release, Jan-2007) and, from
2024, the deal / financing / restructuring 8-Ks (Items 1.01, 2.01, 2.03, 2.05, 7.01, 8.01)."""
import json, subprocess, os, time, csv
S = os.environ.get('UPS_SRC', '/tmp/ups_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIK = '1090727'
DEAL_ITEMS = ('1.01', '2.01', '2.03', '2.05', '7.01', '8.01')


def sub_files():
    p = os.path.join(S, f'sub_{CIK}.json')
    if not os.path.exists(p):
        subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/CIK{int(CIK):010d}.json', '-o', p], check=True)
    d = json.load(open(p)); yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        q = os.path.join(S, f['name'])
        if not os.path.exists(q):
            subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/{f["name"]}', '-o', q], check=True)
            time.sleep(0.3)
        yield json.load(open(q))


def wanted(f, d, items):
    if f == '10-K': return d >= '2007-01-01'
    if f == '10-Q': return d >= '2012-01-01'
    if f == '8-K':
        if '2.02' in items: return d >= '2007-01-01'
        return d >= '2024-01-01' and any(it in items for it in DEAL_ITEMS)
    return False


out = []
for r in sub_files():
    for i in range(len(r['form'])):
        f, d, items = r['form'][i], r['filingDate'][i], r['items'][i]
        if not wanted(f, d, items): continue
        acc = r['accessionNumber'][i]; n = acc.replace('-', '')
        p = os.path.join(S, 'docs', acc + '.idx.json')
        for k in range(6):
            if os.path.exists(p) and open(p, 'rb').read(1) == b'{': break
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/index.json', '-o', p]); time.sleep(0.25 * 2 ** k)
        names = [x['name'] for x in json.load(open(p))['directory']['item']]
        out.append(dict(cik=CIK, date=d, form=f, acc=acc, primary=r['primaryDocument'][i], items=items, report=r['reportDate'][i],
                        files=[x for x in names if x.lower().endswith(('.htm', '.html', '.txt')) and not x.startswith('R')
                               and 'index' not in x and x != acc + '.txt']))
        time.sleep(0.2)
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
