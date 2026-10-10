"""Download DHR source documents (10-K, 10-Q, earnings-release 8-K Ex. 99) into $DHR_SRC/docs and convert to text in $DHR_SRC/txt."""
import json, subprocess, os, time, sys
from h2t import html_to_text
S = os.environ.get('DHR_SRC', '/tmp/dhr_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    if o['form'] in ('10-K', '10-Q', '10-K/A'): want = [o['primary']]
    elif '2.02' in o['items'] or '2.01' in o['items']:
        want = [x for x in o['files'] if 'ex99' in x.lower() or 'dex99' in x.lower() or 'ex-99' in x.lower()] or [o['primary']]
    else: continue
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        if not os.path.exists(p) or os.path.getsize(p) < 500:
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/313616/{n}/{w}', '-o', p]); time.sleep(0.12)
        t = os.path.join(S, 'txt', os.path.splitext(base)[0] + '.txt')
        if not os.path.exists(t):
            raw = open(p, 'rb').read()
            open(t, 'w').write(html_to_text(raw) if w.lower().endswith(('.htm', '.html')) else raw.decode('latin-1'))
print('done')
