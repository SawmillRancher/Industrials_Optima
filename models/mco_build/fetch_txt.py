"""Supplement to fetch.py: 2007-08 Moody's 8-K exhibits (press releases) were filed as plain-text .txt documents, which
make_index.py does not list. Download the Ex. 99 .txt exhibits of the indexed 8-Ks into $MCO_SRC/docs and copy them to
$MCO_SRC/txt (no conversion needed)."""
import json, os, re, subprocess, time, shutil
S = os.environ.get('MCO_SRC', '/tmp/mco_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
for o in json.load(open(os.path.join(S, 'filings.json'))):
    if o['form'] != '8-K': continue
    idx = json.load(open(os.path.join(S, 'docs', o['acc'] + '.idx.json')))
    names = [x['name'] for x in idx['directory']['item']]
    for w in names:
        if not re.search(r'ex-?99', w.lower()) or not w.lower().endswith('.txt'): continue
        base = f"{o['date']}_{o['form']}_{o['acc']}_{w}"
        p = os.path.join(S, 'docs', base)
        if not os.path.exists(p):
            subprocess.run(['curl', '-sS', '-A', UA, f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{o['acc'].replace('-', '')}/{w}", '-o', p]); time.sleep(0.3)
        shutil.copy(p, os.path.join(S, 'txt', base))
        print(base)
