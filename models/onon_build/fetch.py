"""Download the ONON source documents (20-F, 6-K exhibits, F-1 / 424B4 prospectus) into $ONON_SRC/docs and convert to text in $ONON_SRC/txt."""
import json, subprocess, os, time
from h2t import html_to_text
CIK = '1858985'
S = os.environ.get('ONON_SRC', '/tmp/onon_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
os.makedirs(os.path.join(S, 'txt'), exist_ok=True)
for o in json.load(open(os.path.join(S, 'filings.json'))):
    if o['form'] == 'F-1': continue
    n = o['acc'].replace('-', '')
    for w in o['files']:
        if w.endswith('_d2.htm') and len(o['files']) > 2 and o['form'] == '6-K': pass
        base = f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        if not os.path.exists(p):
            subprocess.run(['curl', '-sS', '-A', UA, f'https://www.sec.gov/Archives/edgar/data/{CIK}/{n}/{w}', '-o', p]); time.sleep(0.15)
        t = os.path.join(S, 'txt', base[:-4] + '.txt')
        if not os.path.exists(t):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
