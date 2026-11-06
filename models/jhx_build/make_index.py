"""Build the James Hardie SEC filings index (filings.json / filings.csv) from the EDGAR submissions JSON (CIK 1159152).

James Hardie Industries plc (NYSE: JHX) was a foreign private issuer until FY2026: annual reports on Form 20-F and quarterly
results on Form 6-K (exhibits: media release, Management's Analysis of Results, condensed consolidated financial statements).
From the FY2026 annual report (May-2026) it files Forms 10-K / 10-Q and 8-K Item 2.02 earnings releases.
Set JHX_SRC for the download folder (outside the repo)."""
import json, subprocess, os, time, csv, datetime as dt
S = os.environ.get('JHX_SRC', '/tmp/jhx_src'); os.makedirs(os.path.join(S, 'docs'), exist_ok=True)
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
CIK = '1159152'

def sub_files():
    p = os.path.join(S, 'submissions.json')
    if not os.path.exists(p):
        subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/CIK{int(CIK):010d}.json', '-o', p], check=True)
    d = json.load(open(p)); yield d['filings']['recent']
    for f in d['filings'].get('files', []):
        q = os.path.join(S, f['name'])
        if not os.path.exists(q):
            subprocess.run(['curl', '-sS', '-A', UA, f'https://data.sec.gov/submissions/{f["name"]}', '-o', q], check=True)
        yield json.load(open(q))

def results_window(date):
    """6-K quarterly results: Q4 in May, Q1 in Aug, Q2 in Nov, Q3 in Feb/early Mar."""
    m, d = int(date[5:7]), int(date[8:10])
    return (m == 5 and d >= 10) or (m == 8) or (m == 11) or (m == 2) or (m == 3 and d <= 5)

out = []
for r in sub_files():
    for i in range(len(r['form'])):
        f, d = r['form'][i], r['filingDate'][i]
        if d < '2006-04-01': continue
        size = r['size'][i]; prim = r['primaryDocument'][i]
        keep = False
        if f in ('20-F', '10-K', '10-Q', 'F-4', '424B3', '20-F/A', '6-K/A'): keep = True
        elif f == '8-K': keep = True
        elif f == '6-K':
            if prim.lower().startswith('q') and '6kintro' in prim.lower(): keep = True          # 2017+ quarterly results
            elif results_window(d) and size > 2_000_000: keep = True                             # pre-2017 large results 6-Ks
        if not keep: continue
        acc = r['accessionNumber'][i]; n = acc.replace('-', '')
        p = os.path.join(S, 'docs', acc + '.idx.json')
        for k in range(6):
            if os.path.exists(p) and open(p, 'rb').read(1) == b'{': break
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/index.json', '-o', p]); time.sleep(0.25 * 2 ** k)
        try: items = [(x['name'], x.get('size')) for x in json.load(open(p))['directory']['item']]
        except Exception: items = []
        out.append(dict(cik=CIK, date=d, form=f, acc=acc, primary=prim, items=r['items'][i], report=r['reportDate'][i], size=size,
                        files=[x for x, _ in items if x.lower().endswith(('.htm', '.html', '.pdf')) and not x.startswith('R') and 'index' not in x.lower()]))
out.sort(key=lambda o: o['date'])
json.dump(out, open(os.path.join(S, 'filings.json'), 'w'), indent=1)
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'filings.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['filing_date', 'form', 'period', 'accession', 'items', 'primary_document', 'exhibits', 'url'])
    for o in out:
        w.writerow([o['date'], o['form'], o['report'], o['acc'], o['items'], o['primary'], ';'.join(o['files']),
                    f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{o['primary']}"])
print(len(out), 'filings')
