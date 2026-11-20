"""Download the Brink's source documents (10-K / 10-Q primary documents and Ex. 13 annual reports; Ex. 99 exhibits of the indexed
8-Ks, and the 8-K cover document) into $BCO_SRC/docs, convert them to text ($BCO_SRC/txt) with h2t.py, and download the XBRL
company facts ($BCO_SRC/cf_78890.json). Run make_index.py first. Raw filings stay outside the repository."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('BCO_SRC', '/tmp/bco_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_78890.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000078890.json', '-o', cf], check=True)
SKIP = re.compile(r'ex(hibit)?[_-]?(10|2[134]?|3[12]?|4|1-)[a-z0-9_.-]*\.htm|^\d{10}-\d\d-\d{6}\.txt$', re.I)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'].startswith('10-'):
        want = [o['primary']] + [x for x in o['files'] if re.search(r'ex(hibit)?_?13', x.lower())]
    else:
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and not SKIP.search(x)]
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p) or (os.path.exists(p) and k > 1): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.22 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            raw = open(p, 'rb').read()
            open(t, 'w').write(html_to_text(raw) if b'<' in raw[:20000] and w.lower().endswith(('.htm', '.html')) else raw.decode('latin-1'))
