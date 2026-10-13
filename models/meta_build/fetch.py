"""Download the Meta source documents (424B4 / 10-K / 10-Q primary documents; Ex. 99 exhibits and cover documents of the indexed
8-Ks) into $META_SRC/docs, convert them to text ($META_SRC/txt) with h2t.py, and download the XBRL company facts
($META_SRC/cf_1326801.json). Run make_index.py first. Throttled (< 5 requests / s) with a User-Agent; retries back off on errors."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('META_SRC', '/tmp/meta_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_1326801.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001326801.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', '424B4'): want = [o['primary']]
    else:      # 8-K cover document + news-release exhibits (underwriting agreements, indentures, opinions, charters: Ex. 1, 2, 3, 4, 5, 10 skipped)
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and not re.search(r'ex(1|2|3|4|5|10)\d*[_.a-z]|ex(1|2|3|4|5|10)\d', x.lower())]
    for w in want:
        base = f"{o['date']}_{o['form']}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.25 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
