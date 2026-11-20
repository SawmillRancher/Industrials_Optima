"""Download the Talen source documents into $TLN_SRC/docs and convert them to text ($TLN_SRC/txt) with h2t.py:
S-1 / 10-K / 10-Q primary documents; the 8-K cover document plus its Ex. 99 exhibits (earnings releases, deal releases,
investor presentations, PJM auction releases, acquired-business financial statements and pro forma information). Agreements,
indentures, charters and certifications (Ex. 2, 3, 4, 10, 23, 31, 32) are skipped. Also downloads the XBRL company facts
($TLN_SRC/cf_1622536.json). Run make_index.py first. EDGAR: User-Agent on every request, < 5 requests/s, back-off on errors."""
import json, subprocess, os, re, time
from h2t import html_to_text
S = os.environ.get('TLN_SRC', '/tmp/tln_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)
SKIP = re.compile(r'(ex|exh|exhibit)[-_]?(10|2|3|4|23|31|32)\d*|certi|consent|indenture|supplementa|amendmentno|creditagreem|employme|agreement|transition|purchasean|cornerstonere|formof|descriptio|listofsub|rubric|rsu|psu', re.I)

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

cf = os.path.join(S, 'cf_1622536.json')
if not ok(cf):
    subprocess.run(['curl', '-sS', '-A', UA, 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001622536.json', '-o', cf], check=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', 'S-1'): want = [o['primary']]
    elif o['form'] == 'S-1/A': want = []
    else: want = [o['primary']] + [x for x in o['files'] if x != o['primary'] and not SKIP.search(x)]
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.25 * 2 ** k)
        time.sleep(0.25)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and os.path.exists(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
print('done')
