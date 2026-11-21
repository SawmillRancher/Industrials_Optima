"""Download the UPS source documents (10-K / 10-Q primary documents; Ex. 99 exhibits of the indexed 8-Ks, and the primary document
of 8-Ks without exhibits) into $UPS_SRC/docs, convert them to text ($UPS_SRC/txt) with h2t.py, and download the XBRL company facts
($UPS_SRC/cf_1090727.json). Run make_index.py first. EDGAR: User-Agent on every request, <5 requests per second."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('UPS_SRC', '/tmp/ups_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)


def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)


cf = os.path.join(S, 'cf_1090727.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001090727.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q'): want = [o['primary']]
    else:      # 8-K cover document + news-release / financial-statement exhibits (agreements, notes, charters: Ex. 1, 2, 3, 4, 5, 10 skipped)
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and re.search(r'ex[-_]?99|dex99|exhibit99|exv99', x.lower())]
    for w in want:
        base = f"{o['date']}_{o['form']}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.25 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            raw = open(p, 'rb').read()
            open(t, 'w').write(raw.decode('latin-1') if w.lower().endswith('.txt') else html_to_text(raw))
