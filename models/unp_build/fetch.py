"""Download the Union Pacific source documents (10-K / 10-Q primary documents; Ex. 99 exhibits of the indexed 8-Ks and the
primary document of 8-Ks without exhibits; S-4 / 424B3) into $UNP_SRC/docs, convert them to text ($UNP_SRC/txt) with h2t.py,
and download the XBRL company facts ($UNP_SRC/companyfacts.json). Run make_index.py first."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('UNP_SRC', '/tmp/unp_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'companyfacts.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000100885.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', 'S-4', 'S-4/A', '424B3'): want = [o['primary']]
    else:      # 8-K cover document + exhibits 99 (agreements / charters, Ex. 2, 3, 4, 10 are skipped)
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and re.search(r'99', x.lower())]
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.22 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
print('done')
