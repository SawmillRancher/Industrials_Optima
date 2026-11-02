"""Download the Federal Signal source documents (10-K / 10-Q primary documents; the exhibits of the indexed 8-Ks and their cover
documents) into $FSS_SRC/docs, convert them to text ($FSS_SRC/txt) with h2t.py, and download the XBRL company facts
($FSS_SRC/cf_277509.json). Run make_index.py first. Federal Signal does not furnish its earnings releases on Form 8-K (only three
Item 2.02 filings exist, 2006 and 2009), so the quarterly statements come from the 10-Q / 10-K filings themselves."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('FSS_SRC', '/tmp/fss_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_277509.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000277509.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', '10-K/A', '10-Q/A'):
        # primary document + the earnings release / presentation exhibits (Ex. 99.1 / 99.2) that Federal Signal attaches to each 10-Q / 10-K
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and x.lower().endswith('.htm')
                                 and re.search(r'ex[a-z]*99|dex99|earni|presentation', x.lower())]
    else:      # 8-K cover document + exhibits (agreements / charters, Ex. 2, 3, 4, 10, are skipped; the full-submission .txt is skipped)
        want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and x.lower().endswith('.htm')
                                 and not re.search(r'ex(10|2|3|4)\d*[_.a-z]|ex(10|2|3|4)\d|exv(10|2|3|4)', x.lower())]
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
