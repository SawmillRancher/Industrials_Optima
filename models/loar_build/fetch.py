"""Download the LOAR source documents (10-K, 10-Q, 8-K Ex. 99, IPO prospectus) into $LOAR_SRC/docs and convert to text in $LOAR_SRC/txt."""
import json, subprocess, os, time
from h2t import html_to_text
S = os.environ.get('LOAR_SRC', '/tmp/loar_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    n = o['acc'].replace('-', '')
    want = []
    if o['form'] in ('10-K', '10-Q'): want = [o['primary']]
    elif o['form'].startswith('8-K'): want = [x for x in o['files'] if 'ex99' in x or 'dex99' in x] + [o['primary']]
    elif o['acc'] == '0001193125-24-118106': want = [o['primary']]        # IPO prospectus (424B4, 26-Apr-2024)
    for w in want:
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        if not os.path.exists(p):
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/2000178/{n}/{w}', '-o', p]); time.sleep(0.15)
        t = os.path.join(S, 'txt', base[:-4] + '.txt')
        if not os.path.exists(t):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
