"""Download the Alphabet / Google source documents into $GOOG_SRC/docs and convert HTML to text ($GOOG_SRC/txt) with h2t.py:
10-K / 10-Q primary documents and their XBRL instance documents (from 2009; '<ticker>-<date>.xml' or the inline-XBRL extract
'<...>_htm.xml'); Ex. 99 exhibits of the indexed 8-Ks and the primary document of 8-Ks without exhibits. Also downloads the
XBRL company facts of both registrants ($GOOG_SRC/cf_<cik>.json). Run make_index.py first. Throttled (<5 requests/s), retries."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('GOOG_SRC', '/tmp/goog_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

def dl(url, p):
    for k in range(6):
        if ok(p): return
        subprocess.run(['curl', '-sS', '-A', UA, url, '-o', p]); time.sleep(0.25 * 2 ** k)

for cik in ('1288776', '1652044'):
    dl(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json', os.path.join(S, f'cf_{cik}.json'))

def instance(files):
    xs = [x for x in files if x.lower().endswith('.xml') and not re.search(r'_(cal|def|lab|pre)\.xml$', x.lower()) and 'defnref' not in x.lower()]
    h = [x for x in xs if x.lower().endswith('_htm.xml')]
    return (h or xs)[:1]

for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q'):
        want = [o['primary']] + instance(o['files'])
    else:
        ex = [x for x in o['files'] if x != o['primary'] and re.search(r'ex-?99|exhibit99|ex99|dex99', x.lower())]
        want = [o['primary']] + ex
    for w in want:
        base = f"{o['date']}_{o['form']}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        dl(f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", p)
        if w.lower().endswith(('.htm', '.html', '.txt')):
            t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
            if not os.path.exists(t) and os.path.exists(p):
                open(t, 'w').write(html_to_text(open(p, 'rb').read()))
        time.sleep(0.12)
