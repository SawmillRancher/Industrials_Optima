"""Download the James Hardie source documents into $JHX_SRC/docs and convert them to text ($JHX_SRC/txt) with h2t.py.
Run make_index.py first.
  6-K quarterly results: every Ex. 99 exhibit (media release / earnings release, Management's Analysis of Results, condensed
  consolidated financial statements, management presentation).
  8-K: Ex. 99 exhibits (earnings releases, deal / governance releases).
  20-F / 10-K / 10-Q / F-4 / 424B3: primary document."""
import json, subprocess, os, time, re, sys
from h2t import html_to_text
S = os.environ.get('JHX_SRC', '/tmp/jhx_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)
def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)
only = sys.argv[1:]
for o in json.load(open(os.path.join(S, 'filings.json'))):
    if only and o['acc'] not in only and o['date'] not in only: continue
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', '20-F', '20-F/A', 'F-4', '424B3'): want = [o['primary']]
    elif o['form'] in ('6-K', '6-K/A'):
        want = [x for x in o['files'] if x != o['primary'] and x.lower().endswith('.htm') and not re.search(r'appendix3|substantial|notification|update-notif|asxcover|directorsreport|dividend|agm|chairman|actuar|kpmg', x.lower())]
    else: want = [x for x in o['files'] if x != o['primary'] and x.lower().endswith('.htm')]
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{n}/{w}", '-o', p]); time.sleep(0.25 * 2 ** k)
        t = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and ok(p):
            try: open(t, 'w').write(html_to_text(open(p, 'rb').read()))
            except Exception as e: print('h2t fail', base, e)
print('done')
