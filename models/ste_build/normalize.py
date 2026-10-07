"""Harmonise the extracted release data (data/<period>.json) into flat model keys: DATA[period]['x'][key].

Source rule per period (the 'basis' key records it):
  - FY2012-FY2022 (annual) and FY2022 quarters: the period's own release, as originally reported (Dental in continuing ops
    from the Cantel acquisition, Jun-2021).
  - FY2023 quarters Q1-Q3: continuing-operations recast in the Q4 FY24 release (8-May-2024: quarterly GAAP and adjusted
    results, Q1-Q3 FY24 reconciliations with FY23 comparatives); segment Healthcare / AST / Life Sciences lines, revenue by type,
    balance sheet and cash flow from the own release (not affected by the Dental reclassification).
  - Q4 FY23 and FY2023: comparatives in the Q4 FY24 release (continuing operations).
  - FY2024 quarters Q1-Q3: comparatives in the Q1-Q3 FY25 releases (continuing operations); Q4 FY24 / FY2024: own release.
  - FY2025 onward: own release.
  The originally reported (incl. Dental) adjusted EPS of every restated period is kept as e_pub_orig.
Cash flow: releases give year-to-date statements; discrete quarters derived (Q4 = FY - 9M). D&A, share-based compensation and
deferred taxes from the 10-K / 10-Q XBRL (year to date, as first filed).
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG = {}, []
REC = {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def ytdk(y, q): return {1: qk(y, 1), 2: f'H1-{str(y)[2:]}', 3: f'9M-{str(y)[2:]}', 4: str(y)}[q]
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4, 'H1': 2, '9M': 3}[p[:2]]

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def rel_date(fy, q):
    """filing date of the release that first reports fiscal quarter q of fy."""
    for src in REC.get('_dates', []): pass
    return RELD.get((fy, q))

RELD = {}
def index_releases():
    for r in json.load(open(os.path.join(BASE, 'data', '_releases.json'))): RELD[(r['fy'], r['q'])] = r['date']

def src_own(p):
    fy, q = fyq(p); return RELD.get((fy, q))

def g(p, src, sec, key=None):
    d = REC.get(p, {}).get(src or '', {}).get(sec)
    if d is None: return None
    return d if key is None else d.get(key)

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def periods():
    out = [str(y) for y in range(2012, 2027)]
    for y in range(2022, 2028):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2027 and q > 1)]
    return out

SEGS = ['hc', 'ast', 'ls', 'dental', 'oth']
CATS = ['amort', 'acq', 'stepup', 'restr', 'taxrestr', 'divest', 'impair', 'litig', 'covid', 'other']

def basis(p):
    fy, q = fyq(p)
    if fy == 2023 and q < 4 and not p.isdigit(): return 'rc23'
    if fy == 2023: return 'q4fy24'
    if fy == 2024 and q < 4 and not p.isdigit(): return 'fy25'
    return 'own'

# ---------------------------------------------------------------- income statement / segments / non-GAAP
def do_pl(p):
    own = src_own(p)
    b = basis(p)
    fy, q = fyq(p)
    put(p, 'basis', b)
    if b == 'own': main = own
    elif b == 'q4fy24': main = '2024-05-08'
    elif b == 'fy25': main = RELD.get((2025, q))
    else: main = own
    i = g(p, main, 'is') or {}
    if b == 'rc23':
        i = dict(g(p, own, 'is') or {})
    if not i: return
    rev, gp = i.get('rev'), i.get('gp')
    put(p, 'rev', rev); put(p, 'gp', gp); put(p, 'cogs', rev - gp if rev is not None and gp is not None else None)
    put(p, 'sga', i.get('sga')); put(p, 'rd', i.get('rd')); put(p, 'restr', N(i.get('restr')))
    if i.get('opex') is not None:
        put(p, 'oth_opex', i['opex'] - N(i.get('sga')) - N(i.get('rd')) - N(i.get('restr')))
    put(p, 'op', i.get('op'))
    nonop = i.get('nonop')
    if nonop is None and i.get('ebt') is not None: nonop = i['op'] - i['ebt']
    put(p, 'nonop', nonop)
    put(p, 'int_exp', i.get('int_exp'))
    ebt = i.get('ebt') if i.get('ebt') is not None else (i['op'] - nonop if nonop is not None else None)
    put(p, 'ebt', ebt); put(p, 'tax', i.get('tax'))
    disc = N(i.get('disc')); ni = i.get('ni')
    put(p, 'disc', disc); put(p, 'ni', ni)
    put(p, 'ni_cont', i.get('ni_cont') if i.get('ni_cont') is not None else (ni - disc if ni is not None else None))
    nci = N(i.get('nci')); put(p, 'nci', nci)
    ni_attr = i.get('ni_attr') if i.get('ni_attr') is not None else ni
    put(p, 'ni_attr', ni_attr)
    put(p, 'ni_cont_attr', (ni_attr - disc) if ni_attr is not None else None)
    for k in ('eps_b', 'eps_d', 'eps_d_cont', 'eps_b_cont', 'dps'):
        put(p, k, i.get(k))
    put(p, 'sh_b', i.get('sh_b')); put(p, 'sh_d', i.get('sh_d'))
    # interest expense not shown separately before FY2024 releases -> XBRL (InterestExpense) in build via manual fill
    if b == 'rc23':
        rc = g(p, '2024-05-08#recast', 'rc_gaap') or {}
        ng = g(p, '2024-05-08#recast', 'ngm') or {}
        orig = dict(i)
        put(p, 'rev', rc['rev']); put(p, 'gp', rc['gp']); put(p, 'cogs', rc['rev'] - rc['gp'])
        op = ng.get('gaap_op'); put(p, 'op', op)
        put(p, 'ebt', rc['ebt']); put(p, 'tax', rc['tax']); put(p, 'nonop', op - rc['ebt'])
        put(p, 'ni_cont', rc['ni_cont']); put(p, 'disc', rc['disc']); put(p, 'ni', rc['ni']); put(p, 'ni_attr', rc['ni_attr'])
        put(p, 'ni_cont_attr', rc['ni_attr'] - rc['disc']); put(p, 'nci', rc['ni'] - rc['ni_attr'])
        put(p, 'eps_d_cont', rc['eps_d_cont']); put(p, 'eps_d', rc['eps_d'])
        put(p, 'eps_b', None)
        # opex lines: R&D, restructuring and other operating items scaled to the FY2023 restated totals; SG&A = plug
        fyr = g('2023', '2024-05-08', 'is') or {}
        fyo = {}
        for qq in (1, 2, 3, 4):
            o = g(qk(2023, qq), RELD[(2023, qq)], 'is') or {}
            for k in ('rd', 'restr', 'opex', 'sga'): fyo[k] = fyo.get(k, 0.0) + N(o.get(k))
        oth_o = fyo['opex'] - fyo['sga'] - fyo['rd'] - fyo['restr']
        oth_r = fyr['opex'] - fyr['sga'] - fyr['rd'] - N(fyr.get('restr'))
        rd = orig['rd'] * fyr['rd'] / fyo['rd']
        rs = N(orig.get('restr')) * (N(fyr.get('restr')) / fyo['restr'] if fyo['restr'] else 0.0)
        oo = orig['opex'] - orig['sga'] - orig['rd'] - N(orig.get('restr'))
        oth = 0.0 if abs(oth_o) < 1e-9 else oo * oth_r / oth_o
        if abs(oo - 490.565) < 1.0: oth = 0.0          # Q2-23 Dental goodwill impairment -> discontinued operations
        put(p, 'rd', rd); put(p, 'restr', rs); put(p, 'oth_opex', oth)
        put(p, 'sga', rc['gp'] - op - rd - rs - oth)
        put(p, 'restated_opex_derived', 1)
    # segments
    sb = main if b != 'rc23' else own
    s = g(p, sb, 'seg') or {}
    if s:
        hc = s.get('rev_hc', (s.get('rev_hcp') or 0) + (s.get('rev_hss') or 0) if s.get('rev_hcp') is not None else None)
        put(p, 'sr_hc', hc); put(p, 'sr_ast', s.get('rev_ast')); put(p, 'sr_ls', s.get('rev_ls'))
        put(p, 'sr_dental', N(s.get('rev_dental')) if b in ('own',) else 0.0); put(p, 'sr_oth', N(s.get('rev_corp')))
        put(p, 'sr_hcp', s.get('rev_hcp')); put(p, 'sr_hss', s.get('rev_hss'))
        oihc = s.get('oi_hc', (s.get('oi_hcp') or 0) + (s.get('oi_hss') or 0) if s.get('oi_hcp') is not None else None)
        put(p, 'so_hc', oihc); put(p, 'so_ast', s.get('oi_ast')); put(p, 'so_ls', s.get('oi_ls'))
        put(p, 'so_dental', N(s.get('oi_dental')) if b == 'own' else 0.0)
        put(p, 'so_hcp', s.get('oi_hcp')); put(p, 'so_hss', s.get('oi_hss'))
        put(p, 'so_corp', s.get('oi_corp'))
        if b == 'rc23':
            ng = g(p, '2024-05-08#recast', 'ngm') or {}
            put(p, 'so_corp_orig', s.get('oi_corp'))
            put(p, 'so_corp', ng['adj_op'] - sum(N(DATA[p]['x'].get(f'so_{k}')) for k in ('hc', 'ast', 'ls')))
        nv = g(p, main, 'ngv') or {}
        if nv.get('adjseg_hc') is not None:          # FY2012-15: segment operating income published on a GAAP basis -> adjusted segment OI
            for sg in ('hc', 'ls', 'ast'):
                put(p, f'so_{sg}_gaap', DATA[p]['x'].get(f'so_{sg}'))
                if nv.get(f'adjseg_{sg}') is not None: put(p, f'so_{sg}', nv[f'adjseg_{sg}'])
            put(p, 'so_corp_gaap', s.get('oi_corp')); put(p, 'so_basis', 'gaap')
            if nv.get('adj_op') is not None:
                put(p, 'so_corp', nv['adj_op'] - sum(N(DATA[p]['x'].get(f'so_{sg}')) for sg in ('hc', 'ls', 'ast')))
    # revenue by type (segment level)
    su = g(p, sb, 'sup') or {}
    if b == 'own' and (su or {}).get('hc_cap') is None and (su or {}).get('hcp_cap') is None:
        for alt in sorted(REC.get(p, {})):
            if alt > (own or '') and not alt.endswith('#recast') and ((g(p, alt, 'sup') or {}).get('hc_cap') is not None or (g(p, alt, 'sup') or {}).get('hcp_cap') is not None):
                su = dict(su or {}, **g(p, alt, 'sup')); LOG.append(f'{p}: revenue by type from {alt} comparative'); break
    if su:
        if su.get('hc_cap') is not None:
            for t in ('cap', 'cons', 'serv'): put(p, f'ty_hc_{t}', su.get(f'hc_{t}'))
        elif su.get('hcp_cap') is not None:
            put(p, 'ty_hc_cap', su['hcp_cap']); put(p, 'ty_hc_cons', su['hcp_cons'])
            put(p, 'ty_hc_serv', su['hcp_serv'] + N(DATA[p]['x'].get('sr_hss')))     # Healthcare Specialty Services = service
        for t in ('cap', 'cons', 'serv'): put(p, f'ty_ls_{t}', su.get(f'ls_{t}'))
        put(p, 'ty_ast_cap', N(su.get('ast_cap'))); put(p, 'ty_ast_serv', su.get('ast_serv', DATA[p]['x'].get('sr_ast')))
        if LOG and LOG[-1].startswith(p + ':'):         # comparative from a later (recast) release: scale the mix to the original segment revenue
            for sg in ('hc', 'ls'):
                tot = sum(N(DATA[p]['x'].get(f'ty_{sg}_{t}')) for t in ('cap', 'cons', 'serv'))
                if tot:
                    f = DATA[p]['x'][f'sr_{sg}'] / tot
                    for t in ('cap', 'cons', 'serv'): put(p, f'ty_{sg}_{t}', DATA[p]['x'][f'ty_{sg}_{t}'] * f)
            put(p, 'ty_scaled', 1)
        put(p, 'ty_co_cap', su.get('co_cap')); put(p, 'ty_co_cons', su.get('co_cons')); put(p, 'ty_co_serv', su.get('co_serv'))
    # non-GAAP
    ngsrc = main if b != 'rc23' else '2024-05-08#recast'
    if b == 'own' and fy == 2024 and q == 4: ngsrc = '2024-05-08'
    m = g(p, ngsrc, 'ngm') or g(p, ngsrc, 'ngv') or {}
    if b == 'rc23': m = g(p, '2024-05-08#recast', 'ngm') or {}
    opadj = g(p, ngsrc, 'opadj') or {}
    gpadj = g(p, ngsrc, 'gpadj') or {}
    niadj = g(p, ngsrc, 'niadj') or {}
    if m:
        put(p, 'adj_gp_pub', m.get('adj_gp')); put(p, 'adj_op_pub', m.get('adj_op'))
        adj_ni = m.get('adj_ni_attr', m.get('adj_ni'))
        if adj_ni is not None: adj_ni -= N(m.get('adj_disc'))
        put(p, 'adj_ni_pub', adj_ni)
        put(p, 'e_pub', m.get('adj_eps_cont', m.get('adj_eps')))
        for k in CATS:
            put(p, 'oa_' + k, N(opadj.get(k)))
            put(p, 'ga_' + k, N(gpadj.get(k)))
        put(p, 'ga_tot', sum(N(gpadj.get(k)) for k in CATS) if gpadj else None)
        put(p, 'na_nonop', sum(N(v) for k, v in niadj.items() if k != '_labels'))
        put(p, 'oa_labels', '; '.join(opadj.get('_labels', [])))
        put(p, 'na_labels', '; '.join(niadj.get('_labels', [])))
    # originally reported adjusted EPS (incl. Dental) for restated periods
    if b != 'own' or (fy == 2024 and q == 4):
        mo = g(p, own, 'ngm') or {}      # Q4 FY24 / FY2024: own release already on continuing ops -> total-company adjusted EPS (incl. Dental)
        if mo: put(p, 'e_pub_orig', mo.get('adj_eps')); put(p, 'adj_op_orig', mo.get('adj_op')); put(p, 'rev_orig', (g(p, own, 'is') or {}).get('rev'))
    # adjusted discontinued-operations income (Dental) for the rebuild of the originally reported adjusted EPS
    if fy in (2023, 2024):
        rca = g(p, '2024-05-08#recast', 'rc_adj') or {}
        if rca.get('disc') is not None: put(p, 'e_disc_adj', rca['disc'])
        elif (g(p, '2024-05-08', 'ngm') or {}).get('adj_disc') is not None: put(p, 'e_disc_adj', g(p, '2024-05-08', 'ngm')['adj_disc'])
    if p in MAN.get('e_sh_override', {}): put(p, 'e_sh_in', MAN['e_sh_override'][p])
    if p in MAN.get('notes_hist', {}): put(p, 'ds_notes_in', MAN['notes_hist'][p])
    # organic growth bridge (own release; FY2024 quarters Q1-Q3 incl. Dental in the total)
    o = g(p, own, 'org') or {}
    if b == 'fy25': o = g(p, own, 'org') or {}
    if o:
        for k in ('g', 'og', 'ccog', 'acq', 'div', 'fx', 'rev_py', 'rev'):
            put(p, f'org_{k}', o.get(f'tot_{k}'))
        for sg in ('hc', 'ast', 'ls'):
            if o.get(f'{sg}_ccog') is not None: put(p, f'org_{sg}_ccog', o[f'{sg}_ccog'])

# ---------------------------------------------------------------- cash flow
CFK = ['cf_ni', 'cf_noncash', 'cf_cfo', 'cf_capex', 'cf_ppesale', 'cf_acq', 'cf_divest', 'cf_cfi', 'cf_bb', 'cf_div', 'cf_cff', 'cf_fx', 'fcf_pub']
XB = {'cf_dda': ['DepreciationDepletionAndAmortization'], 'cf_sbc': ['ShareBasedCompensation'], 'cf_def': ['DeferredIncomeTaxExpenseBenefit']}

def cf_ytd(fy, q):
    src = RELD.get((fy, q))
    c = g(ytdk(fy, q), src, 'cf')
    if not c: return None
    o = {k: N(c.get(k)) for k in CFK}
    for k, cs in XB.items(): o[k] = N(xbrl.first_of(cs, fy, 'FY' if q == 4 else 'YTD', q))
    o['cf_beg'], o['cf_end'] = c.get('cf_beg'), c.get('cf_end')
    if o['cf_cfi'] == 0 and c.get('cf_cfi') is None:
        o['cf_cfi'] = o['cf_cfo'] * 0
    return o

def cf_lines(c):
    o = {k: c[k] for k in ('cf_ni', 'cf_dda', 'cf_sbc', 'cf_def', 'cf_cfo', 'cf_capex', 'cf_ppesale', 'cf_acq', 'cf_divest', 'cf_cfi', 'cf_bb', 'cf_div', 'cf_cff', 'cf_fx', 'fcf_pub')}
    o['cf_oth'] = c['cf_noncash'] - c['cf_dda'] - c['cf_sbc'] - c['cf_def']
    o['cf_wc'] = c['cf_cfo'] - c['cf_ni'] - c['cf_noncash']
    o['cf_oinv'] = c['cf_cfi'] - c['cf_capex'] - c['cf_ppesale'] - c['cf_acq'] - c['cf_divest']
    o['cf_ofin'] = c['cf_cff'] - c['cf_bb'] - c['cf_div']
    o['cf_net'] = c['cf_cfo'] + c['cf_cfi'] + c['cf_cff'] + c['cf_fx']
    return o

def do_cf():
    for y in range(2012, 2027):
        a = cf_ytd(y, 4)
        if not a: LOG.append(f'{y}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', a['cf_beg']); put(str(y), 'cf_end', a['cf_end'])
    for y in range(2022, 2028):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2027 and q > 1: break
            p = qk(y, q)
            cur = cf_ytd(y, q)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['cf_beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['cf_end'])
            prev = (lc, cur['cf_end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    fy, q = fyq(p)
    src = RELD.get((fy, q))
    key = str(fy) if q == 4 else p
    b = g(key, src, 'bs')
    if not b: return
    ta, tca = b['ta'], b['tca']
    gw = b.get('gw'); it = b.get('intang')
    if gw is None and b.get('gwi') is not None:
        gw = xbrl.value('Goodwill', fy, 'I', q) or 0.0; it = b['gwi'] - gw
    rou = N(b.get('rou'))
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', b['inv']); put(p, 'bs_oca', tca - b['cash'] - b['ar'] - b['inv'])
    put(p, 'bs_tca', tca); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', gw); put(p, 'bs_int', it); put(p, 'bs_rou', rou)
    put(p, 'bs_onca', ta - tca - b['ppe'] - gw - it - rou); put(p, 'bs_ta', ta)
    std = N(b.get('std'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_std', std); put(p, 'bs_ocl', b['tcl'] - b['ap'] - std); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_ol', ta - b['teq'] - b['tcl'] - b['ltd'])
    nci = N(xbrl.value('MinorityInterest', fy, 'I', q))
    put(p, 'bs_nci', nci); put(p, 'bs_eq', b['teq'] - nci); put(p, 'bs_teq', b['teq']); put(p, 'bs_tle', b['tle'])
    sh = xbrl.value('CommonStockSharesOutstanding', fy, 'I', q)
    if sh: put(p, 'bs_shares', sh)

def do_xbrl_is(p):
    """Interest expense and income-statement lines not shown in older releases (from XBRL, as first filed)."""
    fy, q = fyq(p)
    x = DATA.get(p, {}).get('x', {})
    if x.get('int_exp') is None:
        cs = ['InterestExpense', 'InterestExpenseDebt', 'InterestExpenseNonoperating']
        if p.isdigit(): v = xbrl.first_of(cs, fy, 'FY')
        elif q < 4: v = xbrl.first_of(cs, fy, 'Q', q)
        else:
            a, b = xbrl.first_of(cs, fy, 'FY'), xbrl.first_of(cs, fy, 'YTD', 3)
            v = a - b if a is not None and b is not None else None
        put(p, 'int_exp', v)

def derived(p):
    x = DATA.get(p, {}).get('x', {})
    if x.get('nonop') is not None and x.get('int_exp') is not None: put(p, 'onop', x['nonop'] - x['int_exp'])

def run():
    load(); index_releases()
    for p in periods():
        do_pl(p); do_bs(p); do_xbrl_is(p); derived(p)
    do_cf()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, x.get('basis'), {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in ('rev', 'op', 'ni_cont_attr', 'adj_op_pub', 'e_pub', 'sh_d', 'cf_cfo', 'bs_ta', 'int_exp')})
    print('\n'.join(LOG))
