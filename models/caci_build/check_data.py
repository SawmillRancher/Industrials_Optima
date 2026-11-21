"""Data consistency checks on the normalised CACI data (statement arithmetic, revenue tables, segments, bridges, cash, balance sheet,
quarters vs fiscal year). Prints every exception; known exceptions are listed in README.md."""
import normalize
D = normalize.run()
n = bad = 0
def chk(p, name, a, b, tol=0.02):
    global n, bad
    if a is None or b is None: return
    n += 1
    if abs(a - b) > tol: bad += 1; print(f'{p:6s} {name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')
order = sorted(D, key=lambda p: (D[p]['fy'], D[p]['q'] or 5))
for p in order:
    d = D[p]; x = d['x']; g = x.get
    chk(p, 'OI', x['rev'] - x['direct'] - x['indirect'] - x['da'], x['oi'])
    chk(p, 'EBT', x['oi'] - x['int_net'], x['ebt']); chk(p, 'NI', x['ebt'] - x['tax'], x['ni_tot'])
    chk(p, 'EPS', x['ni'] / x['sh_d'], x['eps_d'], 0.0101)
    if g('cl_dod') is not None: chk(p, 'cust legacy', x['cl_dod'] + x['cl_fed'] + g('c_comm_orig', x['c_comm']), x['rev'])
    if g('c_ic') is not None: chk(p, 'cust', x['c_dod'] + x['c_ic'] + x['c_fed'] + x['c_comm'], x['rev'])
    if g('t_cpf') is not None: chk(p, 'ctype', x['t_cpf'] + x['t_ffp'] + x['t_tm'], x['rev'])
    if g('p_prime') is not None: chk(p, 'prime', x['p_prime'] + x['p_sub'], x['rev'])
    if g('e_exp') is not None: chk(p, 'exptech', x['e_exp'] + x['e_tech'], x['rev'])
    if g('dc_labor') is not None: chk(p, 'dcost', x['dc_labor'] + x['dc_odc'], x['direct'])
    if g('sg_dom') is not None: chk(p, 'seg rev', x['sg_dom'] + x['sg_int'], x['rev'])
    if g('sgn_dom') is not None: chk(p, 'seg NI', x['sgn_dom'] + x['sgn_int'], x['ni'])
    if g('sgo_dom') is not None: chk(p, 'seg OI', x['sgo_dom'] + x['sgo_int'], x['oi'])
    if g('ebitda_pub') is not None:
        chk(p, 'EBITDA', x['ni'] + x['tax'] + x['int_net'] + x['da'] + g('da_direct', 0) + g('eb_earnout', 0) + g('eb_prod_adj', 0) + g('eb_fp_adj', 0) + g('eb_bdiff', 0), x['ebitda_pub'], 0.05)
    if g('a_intang') is not None and g('adj_ni_pub') is not None:
        chk(p, 'adj NI', x['ni'] + x['a_intang'] + x['a_tax'], x['adj_ni_pub']); chk(p, 'amort vs D&A', min(x['a_intang'], x['da']), x['a_intang'])
    elif g('a_sbc') is not None and g('adj_ni_pub') is not None:
        chk(p, 'adj NI (old)', x['ni'] + x['a_sbc'] + g('a_da', x['da']) + g('a_amfin', 0) + g('a_ncint', 0) + g('eb_earnout', 0) + x['a_tax'], x['adj_ni_pub'], 0.05)
    if g('adj_eps_pub') is not None and g('adj_ni_pub') is not None: chk(p, 'adj EPS', x['adj_ni_pub'] / x['sh_d'], x['adj_eps_pub'], 0.0101)
    if g('f_fcf') is not None: chk(p, 'FCF', x['f_cfo_ex'] + x['f_capex'], x['f_fcf'])
    if g('cf_cfo') is not None:
        chk(p, 'CFO sum', sum(x[k] for k in ('cf_ni', 'cf_da', 'cf_sbc', 'cf_def', 'cf_oth', 'cf_wc')), x['cf_cfo'])
        chk(p, 'CFI sum', x['cf_capex'] + x['cf_acq'] + x['cf_oinv'], x['cf_cfi']); chk(p, 'CFF sum', x['cf_debt'] + x['cf_bb'] + x['cf_eq'] + x['cf_ofin'], x['cf_cff'])
        chk(p, 'cash', x['cf_beg'] + x['cf_cfo'] + x['cf_cfi'] + x['cf_cff'] + x['cf_fx'], x['cf_end']); chk(p, 'BS cash', x['cf_end'], x['bs_cash'])
        if g('f_cfo') is not None: chk(p, 'CFO vs FCF table', x['f_cfo'], x['cf_cfo']); chk(p, 'capex', g('f_capex'), x['cf_capex'])
    if abs(g('eb_bdiff', 0)) > 3: print(p, 'EBITDA basis difference', x['eb_bdiff'])
    chk(p, 'TA=TLE', x['bs_ta'], x['bs_tle']); chk(p, 'TL+EQ', x['bs_tl'] + x['bs_teq'], x['bs_tle'])
    if d['q'] is None and d['fy'] >= 2013:
        qs = [D.get(f'Q{k}-{str(d["fy"])[2:]}') for k in (1, 2, 3, 4)]
        if all(qs):
            for k in ('rev', 'oi', 'ni', 'cf_cfo', 'cf_capex', 'awards', 'orders', 'amort', 'ebitda_pub', 'adj_ni_pub', 'f_fcf', 'sg_int', 'c_ic', 'e_tech'):
                if all(q['x'].get(k) is not None for q in qs) and g(k) is not None: chk(p, 'sumQ ' + k, sum(q['x'][k] for q in qs), x[k], 0.06)
miss = [p for p in order if D[p]['q'] and 'cf_cfo' not in D[p]['x']]
print(n, 'checks;', bad, 'exceptions; quarters without discrete cash flow:', miss)

# ---- optional cross-check against XBRL company facts (annual, as first filed), when the raw download is available
import os, json, datetime as dt
cf = os.path.join(os.environ.get('CACI_SRC', '/tmp/caci_src'), 'cf_16058.json')
if os.path.exists(cf):
    F = json.load(open(cf))['facts']['us-gaap']
    def first(concepts, fy, inst=False):
        best = None
        for c in concepts:
            for u in F.get(c, {}).get('units', {}).values():
                for f in u:
                    if f.get('form') != '10-K' or f['end'] != f'{fy}-06-30': continue
                    if inst != ('start' not in f): continue
                    if not inst and (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days < 350: continue
                    if best is None or f['filed'] < best[0]: best = (f['filed'], f['val'])
            if best: break
        return None if best is None else best[1]
    nx = bx = 0
    for fy in range(2010, 2027):
        x = D[str(fy)]['x']
        for name, key, concepts, inst, scale, tol in (
                ('revenue', 'rev', ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueServicesNet', 'SalesRevenueNet'], False, 1e6, 0.01),
                ('operating income', 'oi', ['OperatingIncomeLoss'], False, 1e6, 0.01), ('net income', 'ni', ['NetIncomeLoss'], False, 1e6, 0.01),
                ('diluted EPS', 'eps_d', ['EarningsPerShareDiluted'], False, 1, 0.001), ('CFO', 'cf_cfo', ['NetCashProvidedByUsedInOperatingActivities'], False, 1e6, 0.01),
                ('total assets', 'bs_ta', ['Assets'], True, 1e6, 0.01)):
            v = first(concepts, fy, inst)
            if v is None: continue
            nx += 1
            if abs(v / scale - x[key]) > tol: bx += 1; print(f'XBRL {fy} {name}: release {x[key]} vs XBRL {v / scale}')
    print(nx, 'XBRL cross-checks;', bx, 'differences')
