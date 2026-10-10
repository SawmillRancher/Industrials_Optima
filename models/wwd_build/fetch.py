"""Download the Woodward source documents (10-K / 10-Q primary documents; Ex. 99 exhibits of the indexed 8-Ks, and the primary
document of 8-Ks without exhibits) into $WWD_SRC/docs, convert them to text ($WWD_SRC/txt) with h2t.py, and download the XBRL
company facts ($WWD_SRC/cf_108312.json). Run make_index.py first."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('WWD_SRC', '/tmp/wwd_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_108312.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000108312.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q'): want = [o['primary']]
    else:      # 8-K cover document + news-release exhibits (agreements / charters, Ex. 2, 3, 4, 10, 21, 31, are skipped)
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and not re.search(r'ex(10|2|3|4)\d*[_.a-z]|ex(10|2|3|4)\d', x.lower())]
    for w in want:
        base = f"{o['date']}_{o['form']}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.2 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
