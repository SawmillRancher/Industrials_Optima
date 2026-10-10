"""Download ODFL source documents listed in filings.csv into SRC (earnings-release exhibits, 10-Q, 10-K) and convert to text."""
import csv, json, os, sys, time, urllib.request, subprocess
UA = 'Industrials Optima research research@industrialsoptima.dev'
SRC = os.environ.get('ODFL_SRC', '/tmp/claude-0/-home-user-Industrials-Optima/9730001d-1163-52b2-9b31-6b83e69b543f/scratchpad/src')
os.makedirs(SRC, exist_ok=True)
def raw(u):
    for a in range(4):
        try:
            req = urllib.request.Request(u, headers={'User-Agent': UA})
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            time.sleep(2 ** (a + 1)); err = e
    raise err
man = {}
ROWS = list(csv.DictReader(open('filings.csv')))
if os.environ.get('REVERSE'): ROWS = ROWS[::-1]
for r in ROWS:
    form, items = r['form'], r['items']
    tag = f"{r['filed']}_{form.replace('/', '')}_{r['accession']}"
    if form.startswith('8-K') and '2.02' not in items and '7.01' not in items and '8.01' not in items: continue
    try:
        idx = json.loads(raw(r['folder_url'] + 'index.json')); time.sleep(0.25)
    except Exception as e:
        print('ERR idx', tag, e); continue
    names = [i['name'] for i in idx['directory']['item']]
    if form.startswith('8-K'):
        docs = [n for n in names if n.lower().endswith(('.htm', '.html', '.txt')) and 'index' not in n.lower() and not n.startswith('0')
                and ('99' in n.lower() and 'ex' in n.lower() or 'press' in n.lower())]
        if not docs: docs = [n for n in names if n.lower().endswith(('.htm', '.html')) and n != r['primary_doc'] and 'index' not in n and not n.startswith('0')]
        docs = docs[:2] + [r['primary_doc']]
    else:
        docs = [r['primary_doc']]
    got = []
    for d in docs:
        p = os.path.join(SRC, f'{tag}__{d}')
        if not os.path.exists(p):
            try:
                open(p, 'wb').write(raw(r['folder_url'] + d)); time.sleep(0.25)
            except Exception as e:
                print('ERR doc', tag, d, e); continue
        t = p.rsplit('.', 1)[0] + '.txt'
        if not os.path.exists(t) and p.lower().endswith(('.htm', '.html')):
            with open(t, 'w') as fh: subprocess.run(['python3', 'h2t.py', p], stdout=fh)
        got.append(os.path.basename(p))
    man[tag] = {'form': form, 'filed': r['filed'], 'period': r['period'], 'items': items, 'url': r['folder_url'], 'docs': got}
json.dump(man, open(os.path.join(SRC, 'manifest%s.json' % ('_rev' if os.environ.get('REVERSE') else '')), 'w'), indent=1)
print('done', len(man))
