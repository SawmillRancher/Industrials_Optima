"""Build filings.csv: every ODFL 10-K, 10-Q and 8-K (Item 2.02 results / 7.01-8.01 updates) since 2006 from EDGAR submissions."""
import json, urllib.request, csv, time
UA = 'Industrials Optima research research@industrialsoptima.dev'
CIK = 878927
def get(u):
    req = urllib.request.Request(u, headers={'User-Agent': UA})
    return json.loads(urllib.request.urlopen(req).read())
sub = get(f'https://data.sec.gov/submissions/CIK{CIK:010d}.json')
blocks = [sub['filings']['recent']]
for f in sub['filings'].get('files', []):
    time.sleep(0.3); blocks.append(get('https://data.sec.gov/submissions/' + f['name']))
rows = []
for b in blocks:
    for i in range(len(b['form'])):
        form = b['form'][i]
        if form not in ('10-K', '10-Q', '8-K', '10-K/A', '10-Q/A', '8-K/A'): continue
        if b['filingDate'][i] < '2006-01-01': continue
        items = b.get('items', [''] * len(b['form']))[i]
        if form.startswith('8-K') and not any(x in items for x in ('2.02', '7.01', '8.01')): continue
        acc = b['accessionNumber'][i]
        rows.append([form, b['filingDate'][i], b['reportDate'][i], CIK, acc, b['primaryDocument'][i],
                     f'https://www.sec.gov/Archives/edgar/data/{CIK}/{acc.replace("-", "")}/', items])
rows.sort(key=lambda r: r[1])
with open('filings.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['form', 'filed', 'period', 'cik', 'accession', 'primary_doc', 'folder_url', 'items']); w.writerows(rows)
print(len(rows))
