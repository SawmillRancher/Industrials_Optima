"""Data consistency checks on the normalised GOOG data (normalize.run()): statement arithmetic, EPS, segment / revenue-type sums,
cash-flow and balance-sheet tie-outs, release cross-checks (Q4 revenue / EPS, free cash flow) and an XBRL company-facts
cross-check of revenue, operating income, net income, CFO and total assets (earliest-filed fact). Prints every failure and a
summary; known exceptions are listed in EXPECTED with the reason."""
import json, os, sys
import normalize as n

S = os.environ.get('GOOG_SRC', '/tmp/goog_src')
EXPECTED = {(p, 'segment OI sum = OI'): 'performance-fee recast (2019)' for p in ('2017', '2018')}
EXPECTED.update({(p, 'legacy segment OI = OI'): 'performance-fee recast (2019) / 2013 unallocated items' for p in ('2013', '2017', '2018', 'Q4-17', 'Q1-18', 'Q2-18', 'Q3-18', 'Q4-18')})
EXPECTED[('2015', 'sum Q = FY ni')] = 'Q1-15 tax revision in the Q2-15 10-Q (manual_items known_exceptions)'
EXPECTED[('Q3-16', 'FCF published')] = 'release predates the 10-Q cash-flow revision'
fails, count = [], [0]
def chk(p, name, a, b, tol):
    if a is None or b is None: return
    count[0] += 1
    if abs(a - b) > tol and (p, name) not in EXPECTED:
        fails.append(f'{p:6s} {name:28s} {a:14,.3f} vs {b:14,.3f}  diff {a - b:,.3f}')

def main():
    D = n.run(); X = lambda p, k: D.get(p, {}).get('x', {}).get(k)
    for p in n.periods():
        x = D.get(p, {}).get('x', {})
        if not x: fails.append(f'{p} no data'); continue
        chk(p, 'rev - opex = OI', x['rev'] - x['opex_tot'], x['oi'], 1.01)
        chk(p, 'OI + OI&E = EBT', x['oi'] + x['oie'], x['ebt'], 1.01)
        if x.get('sh_d') and x.get('eps_d') is not None:
            chk(p, 'eps', (x['ni'] - x.get('pref_div', 0) - x.get('c_alloc', 0)) / x['sh_d'], x['eps_d'], 0.0151)
        if x.get('cf_cfo') is not None and x.get('cf_beg') is not None:
            chk(p, 'CF: beg + net = end', x['cf_beg'] + x['cf_net'], x['cf_end'], 1.01)
        if x.get('bs_ta') is not None:
            chk(p, 'BS: TA = TL&E', x['bs_ta'], x['bs_tle'], 1.01)
        if x.get('so_svc') is not None:
            chk(p, 'segment OI sum = OI', x['so_svc'] + x['so_cloud'] + x['so_ob'] + x['so_alpha'], x['oi'], 2.01)
        if x.get('lso_google') is not None and x.get('lso_alpha') is not None:
            chk(p, 'legacy segment OI = OI', x['lso_google'] + N(x.get('lso_ob')) + x['lso_alpha'] + N(x.get('lso_moto')), x['oi'], 2.01)
        if x.get('bs_cash') is not None and x.get('cf_end') is not None and not (p.startswith(('Q1-14', 'Q2-14', 'Q3-14'))) and (int(p[-2:]) if p[0] == 'Q' else int(p) - 2000) < 18:
            chk(p, 'BS cash = CF cash (pre-2018)', x['bs_cash'], x['cf_end'], 1.01)
        if x.get('st_search') is not None and x.get('sr_svc') is not None:
            chk(p, 'streams = Services rev', x['st_search'] + x['st_youtube'] + x['st_network'] + x['st_subs'], x['sr_svc'], 2.01)
        if x.get('st_search') is not None and x.get('sr_svc') is None:
            chk(p, 'streams + OB ~ rev (pre-2020)', x['st_search'] + x['st_youtube'] + x['st_network'] + x['st_subs'] + x['st_cloud'], x['rev'] - N(x.get('lsr_ob')), 2500)
        if x.get('fcf_pub') is not None and x.get('cf_cfo') is not None:
            chk(p, 'FCF published', x['cf_cfo'] + x['cf_capex'], x['fcf_pub'], 1.01)
        if x.get('ng_ni_pub') is not None and x.get('ng_eps_pub') is not None and x.get('sh_d'):
            chk(p, 'Google non-GAAP EPS', x['ng_ni_pub'] / x['sh_d'], x['ng_eps_pub'], 0.0151)
        if p.startswith('Q4'):
            rel = n.REC.get(p, {}).get('release') or {}
            chk(p, 'Q4 rev vs release', x['rev'], rel.get('rev_q'), 1.01)
            chk(p, 'Q4 NI vs release', x['ni'], rel.get('ni_q'), 1.01)
    for y in range(2013, 2026):
        for k in ('cf_cfo', 'cf_capex', 'cf_cfi', 'cf_cff', 'cf_bb', 'cf_div'):
            qs = [X(n.qk(y, q), k) for q in (1, 2, 3, 4)]
            if all(v is not None for v in qs): chk(str(y), f'sum Q = FY {k}', sum(qs), X(str(y), k), 1.01)
        for k in ('rev', 'oi', 'ni'):
            qs = [X(n.qk(y, q), k) for q in (1, 2, 3, 4)]
            chk(str(y), f'sum Q = FY {k}', sum(qs), X(str(y), k), 1.01)
    # XBRL company facts (earliest-filed 10-K / 10-Q fact for each period)
    cf = {}
    for cik in ('1288776', '1652044'):
        pth = os.path.join(S, f'cf_{cik}.json')
        if not os.path.exists(pth): continue
        for c, v in json.load(open(pth))['facts'].get('us-gaap', {}).items():
            for u, fs in v['units'].items():
                for f in fs:
                    if f.get('form') not in ('10-K', '10-Q'): continue
                    cf.setdefault(c, []).append(f)
    def fact(concepts, p, inst=False):
        y = int(p) if p.isdigit() else 2000 + int(p[-2:]); q = 4 if p.isdigit() else int(p[1])
        end = f'{y}-{[0, 3, 6, 9, 12][q]:02d}-{[0, 31, 30, 30, 31][q]:02d}'
        best = None
        for c in concepts:
            for f in cf.get(c, []):
                if f['end'] != end: continue
                if inst != ('start' not in f): continue
                if not inst:
                    import datetime as dt
                    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
                    if (p.isdigit() and not 350 < d < 380) or (not p.isdigit() and not 80 < d < 100): continue
                if best is None or f['filed'] < best[0]: best = (f['filed'], f['val'] / 1e6)
            if best: return best[1]
        return None
    for p in n.periods():
        if p.isdigit() and int(p) < 2009: continue
        x = D[p]['x']
        chk(p, 'XBRL facts: revenue', x['rev'], fact(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'], p), 1.01)
        chk(p, 'XBRL facts: OI', x['oi'], fact(['OperatingIncomeLoss'], p), 1.01)
        chk(p, 'XBRL facts: NI', x['ni'], fact(['NetIncomeLoss'], p), 1.01)
        if x.get('bs_ta') is not None: chk(p, 'XBRL facts: TA', x['bs_ta'], fact(['Assets'], p, True), 1.01)
        if p.isdigit(): chk(p, 'XBRL facts: CFO', x['cf_cfo'], fact(['NetCashProvidedByUsedInOperatingActivities'], p), 1.01)
    print('\n'.join(fails))
    print(f'{count[0]} checks, {len(fails)} failures')
    print('\n'.join(n.LOG))
    return len(fails)

def N(v): return v or 0.0

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
