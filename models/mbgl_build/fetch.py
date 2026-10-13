"""Download every document in filings.csv into $MBGL_SRC/docs and convert it to text ($MBGL_SRC/txt, one table row per line,
cells joined by ' | ') with h2t.py. File names: <registrant>_<filing date>_<form>_<document>. Throttled (< 5 requests/s) with a
User-Agent; retries with back-off. Run make_index.py first."""
import csv, os, subprocess, time
from h2t import html_to_text

S = os.environ.get('MBGL_SRC', '/tmp/mbgl_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research admin@industrialsoptima.com')
for d in ('docs', 'txt'): os.makedirs(os.path.join(S, d), exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))

def ok(p): return os.path.exists(p) and os.path.getsize(p) > 2000 and b'Request Rate Threshold' not in open(p, 'rb').read(5000)

def name(o): return f"{o['registrant']}_{o['filing_date']}_{o['form'].replace('/', '')}_{o['document']}"

if __name__ == '__main__':
    for o in csv.DictReader(open(os.path.join(here, 'filings.csv'))):
        p = os.path.join(S, 'docs', name(o))
        for k in range(6):
            if ok(p): break
            subprocess.run(['curl', '-sS', '-A', UA, o['url'], '-o', p]); time.sleep(0.25 * 2 ** k)
        t = os.path.join(S, 'txt', name(o).rsplit('.', 1)[0] + '.txt')
        if not os.path.exists(t) and ok(p):
            open(t, 'w').write(html_to_text(open(p, 'rb').read()))
        time.sleep(0.2)
    print('done', S)
