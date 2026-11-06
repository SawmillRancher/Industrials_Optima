"""Print one line per period from the extracted data (own package = the results package for that period) to spot gaps.
Usage: python3 review.py [period ...]"""
import json, os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
pk = json.load(open(os.path.join(BASE, 'data', '_packages.json')))
OWN = {}
for p in pk:
    k = f"Q{p['q']}-{str(p['fy'])[2:]}"
    score = (('ma' in p['docs']) + ('er' in p['docs']) * 2 + ('fs' in p['docs']) + ('iar' in p['docs']))
    for kk in ([k] + ([str(p['fy'])] if p['q'] == 4 else [])):
        if score > OWN.get(kk, (0, ''))[0]: OWN[kk] = (score, p['date'])

def own(per):
    return OWN.get(per, (0, None))[1]

def show(per):
    f = os.path.join(BASE, 'data', per + '.json')
    if not os.path.exists(f): print(per, 'NO DATA'); return
    d = json.load(open(f))
    s = own(per)
    if s not in d:
        s = sorted(d)[0]
    i = d[s].get('is', {}); sg = d[s].get('seg', {}); cf = d[s].get('cf', {}); bs = d[s].get('bs', {}); ng = d[s].get('ng', {})
    def f(k, sec=i, fmt='%.1f'):
        v = sec.get(k)
        return (fmt % v) if isinstance(v, (int, float)) else '-'
    print(f"{per:6} {s} rev {f('rev')} gp {f('gp')} sga {f('sga')} op {f('op')} ni {f('ni')} eps {f('eps_d', fmt='%.2f')} shd {f('sh_d')} | "
          f"na {f('na_rev', sg)}/{f('na_ebit', sg)} ap {f('apac_rev', sg)}/{f('apac_ebit', sg)} eu {f('eu_rev', sg)}/{f('eu_ebit', sg)} dra {f('dra_rev', sg)} "
          f"corp {f('corp_ebit', sg)} rd {f('rd_ebit', sg)} vol {f('na_vol', sg)} asp {f('na_asp', sg)} apvol {f('apac_vol', sg)} | "
          f"adjEBIT {f('tot_adj_ebit', sg)} adjNI {f('tot_adj_ni', sg)} adjEPS {f('tot_adj_eps', sg, '%.2f')} aEBITDA {f('tot_adj_ebitda', sg)} dna {f('tot_dna', sg)} "
          f"| cfo {f('cfo', cf)} capex {f('capex', cf)} | ta {f('ta', bs)} cash {f('cash', bs)} ltd {f('ltd', bs)} | ni_items {len(ng.get('ni_items', []))} ebit_items {len(ng.get('ebit_items_def', ng.get('ebit_items', [])))}")

if __name__ == '__main__':
    pers = sys.argv[1:]
    if not pers:
        pers = [str(y) for y in range(2006, 2027)]
        for y in range(2013, 2028):
            for q in (1, 2, 3, 4):
                if y == 2027 and q > 2: break
                pers.append(f'Q{q}-{str(y)[2:]}')
    for per in pers: show(per)
