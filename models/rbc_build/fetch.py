"""Download the RBC Bearings source documents into $RBC_SRC/docs (10-K / 10-Q primary documents; the Ex. 99 exhibits of the indexed
8-Ks, or the 8-K cover document where there is no exhibit; prospectus primary documents), convert them to text ($RBC_SRC/txt) with
h2t.py, and download the XBRL company facts ($RBC_SRC/cf_1324948.json). Run make_index.py first. Throttled well under 5 requests/s."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('RBC_SRC', '/tmp/rbc_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_1324948.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001324948.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    htm = [x for x in o['files'] if x.lower().endswith(('.htm', '.html'))]
    if o['form'].startswith(('10-K', '10-Q', 'S-1', '424')): want = [o['primary']]
    else:
        ex99 = [x for x in htm if re.search(r'ex-?99|exh99|exhibit99|d99|_99-', x.lower())]
        want = ex99 or [o['primary']]
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.25 * 2 ** k)
        time.sleep(0.22)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
