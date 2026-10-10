"""Map each model period to its source documents in $DHR_SRC/txt: earnings release (8-K Ex. 99.1), 10-Q / 10-K, and the
filing one year later whose prior-year comparatives provide the hybrid recast basis (see README)."""
import json, os, re, glob
S = os.environ.get('DHR_SRC', '/tmp/dhr_src')
T = os.path.join(S, 'txt')
fl = json.load(open(os.path.join(S, 'filings.json')))
QN = {'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4}
rel = {}
for f in sorted(glob.glob(os.path.join(T, '*_8-K_*ex99*')) + glob.glob(os.path.join(T, '*_8-K_*dex99*'))):
    head = open(f).read(3000)
    m = re.search(r'REPORTS\s+(?:RECORD\s+)?(?:RESULTS\s+FOR\s+)?(FIRST|SECOND|THIRD|FOURTH)\s+QUARTER(?:\s+AND\s+FULL\s+YEAR)?\s+(?:OF\s+)?(20\d\d)', head, re.I)
    if not m: continue
    key = f'Q{QN[m.group(1).upper()]}-{m.group(2)[2:]}'
    rel.setdefault(key, []).append(os.path.basename(f))
per = {}
for o in fl:
    if o['form'] not in ('10-Q', '10-K'): continue
    rd = o['report']; y, mth = int(rd[:4]), int(rd[5:7])
    if o['form'] == '10-K': key = str(y)
    else: key = f'Q{min(4, (mth - 1) // 3 + 1 + (1 if int(rd[8:10]) <= 7 and mth in (4, 7, 10) else 0) - (0))}-{str(y)[2:]}'
    # 10-Q period ends fall late Mar/Jun/Sep or the first days of Apr/Jul/Oct (fiscal quarters end on a Friday)
    if o['form'] == '10-Q':
        q = {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3}[mth]; key = f'Q{q}-{str(y)[2:]}'
    base = f"{o['date']}_{o['form']}_{o['acc']}_{os.path.splitext(o['primary'])[0]}.txt"
    per.setdefault(key, []).append(base)
out = {}
def nxt(k):
    if k.isdigit(): return str(int(k) + 1)
    q, yy = k[1], int(k[3:]); return f'Q{q}-{yy + 1:02d}'
keys = [str(y) for y in range(2006, 2026)] + [f'Q{q}-{yy:02d}' for yy in range(13, 27) for q in (1, 2, 3, 4) if (yy, q) <= (26, 2)]
for k in keys:
    rk = f'Q4-{k[2:]}' if k.isdigit() else k
    d = {'release': rel.get(rk, []), 'filing': per.get(k if k.isdigit() else k, [])}
    if k.startswith('Q4'): d['filing'] = per.get('20' + k[3:], [])
    n = nxt(k); rn = f'Q4-{n[2:]}' if n.isdigit() else n
    d['next_release'] = rel.get(rn, [])
    d['next_filing'] = per.get(n if not n.startswith('Q4') else '20' + n[3:], [])
    out[k] = d
json.dump(out, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
miss = [k for k, d in out.items() if not d['release'] or not d['filing']]
print('periods', len(out), 'missing', miss)
for k in ('2006', 'Q1-20', 'Q4-23', 'Q2-26'): print(k, out[k])
