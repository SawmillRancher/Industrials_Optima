"""Download the STERIS source documents (10-K, 10-Q primary documents; 8-K Item 2.02 Ex. 99 earnings releases) into
$STE_SRC/docs and convert them to text ($STE_SRC/txt) with h2t.py. Run make_index.py first."""
import json, subprocess, os, time
from h2t import html_to_text
S = os.environ.get('STE_SRC', '/tmp/ste_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)
def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q'): want = [o['primary']]
    else: want = [x for x in o['files'] if 'ex99' in x.lower() or 'dex99' in x.lower()]
    for w in want:
        base = f"{o['date']}_{o['form']}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.2 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
