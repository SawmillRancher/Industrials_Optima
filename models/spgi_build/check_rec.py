"""Self-checks for one or more extracted period records: python3 check_rec.py data/Q1-13.json [...]. Prints failures; exit 1 if any."""
import json, sys
def N(x): return x or 0.0
def chk(path):
    r = json.load(open(path)); i = r.get('is', {}); out = []
    def eq(a, b, tol, msg):
        if a is None or b is None: return
        if abs(a - b) > tol: out.append(f'{msg}: {a:.2f} vs {b:.2f}')
    if i.get('rev') is not None and i.get('exp') is not None:
        eq(i['rev'] - i['exp'] + N(i.get('gain_disp')) + N(i.get('eq_inc')), i.get('op'), 1.01, 'rev-exp+gain+eq = op')
    if i.get('op') is not None:
        eq(i['op'] + N(i.get('oth_inc')) - N(i.get('int')), i.get('ebt'), 1.01, 'op+oth-int = ebt')
    if i.get('ebt') is not None and i.get('tax') is not None:
        eq(i['ebt'] - i['tax'], i.get('ni_cont', i.get('ni')), 1.01, 'ebt-tax = ni_cont')
    if i.get('ni') is not None and i.get('nci') is not None:
        eq(i['ni'] - i['nci'], i.get('ni_attr'), 1.01, 'ni-nci = ni_attr')
    if i.get('ni_attr') and i.get('sh_d'): eq(i['ni_attr'] / i['sh_d'], i.get('eps_d'), 0.015, 'ni_attr/sh_d = eps_d')
    seg = r.get('seg', []); so = r.get('seg_other', {})
    if seg and i.get('rev') is not None:
        eq(sum(N(s.get('rev')) for s in seg) + N(so.get('elim')), i['rev'], 1.01, 'sum seg rev + elim = rev')
    if seg and i.get('op') is not None and all(s.get('op') is not None for s in seg):
        eq(sum(s['op'] for s in seg) - N(so.get('corp')) + N(so.get('eq_inc')), i['op'], 1.01, 'sum seg op - corp + eq = op')
    for s in seg:
        if s.get('adj_op') is not None and s.get('op') is not None:
            eq(s['op'] + N(s.get('nongaap')) + N(s.get('deal_amort')), s['adj_op'], 1.01, f"{s['name']} op+items+amort = adj_op")
    n = r.get('ngaap', {})
    if n.get('adj_ni') is not None and n.get('start_ni') is not None:
        tot = n['start_ni'] + sum(N(x.get('net')) for x in n.get('items', [])) + N(n.get('deal_amort_net'))
        eq(tot, n['adj_ni'], 1.51, 'start_ni + items_net + amort_net = adj_ni')
    if n.get('adj_ni') and i.get('sh_d') and n.get('adj_eps'): eq(n['adj_ni'] / i['sh_d'], n['adj_eps'], 0.02, 'adj_ni/sh_d = adj_eps')
    return out
bad = 0
for p in sys.argv[1:]:
    o = chk(p)
    print(p, 'OK' if not o else o); bad += bool(o)
sys.exit(1 if bad else 0)
