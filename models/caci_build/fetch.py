"""Download the CACI source documents (10-K / 10-Q primary documents; Ex. 99 exhibits of the indexed 8-Ks and the 8-K cover
document) into $CACI_SRC/docs, convert them to text ($CACI_SRC/txt) with h2t.py, and download the XBRL company facts
($CACI_SRC/cf_16058.json). Run make_index.py first. Raw filings stay outside the repo."""
import json, subprocess, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h2t import html_to_text
S = os.environ.get('CACI_SRC', '/tmp/caci_src')
UA = os.environ.get('SEC_UA', 'model-build research@example.com')      # set SEC_UA to your own "name email"
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_16058.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000016058.json', '-o', cf], check=True)
SKIP = re.compile(r'ex-?(10|2|3|4|21|23|31|32)\d*[_.\-a-z]|ex-?(10|2|3|4|21|23|31|32)\d|xex(10|2|3|4|21|23|31|32)|dex(10|2|3|4)\d')
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', '10-K/A'): want = [o['primary']]
    else:      # 8-K cover document + news-release exhibits (agreements / charters are skipped)
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and not x.endswith('.txt') and not SKIP.search(x.lower())]
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.25 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
print('done')
