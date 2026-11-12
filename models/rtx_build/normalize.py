"""Harmonise the extracted RTX data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy (hybrid recast, DHR-style):
  - Income statement, segments, revenue disaggregation and published adjusted figures: a quarterly year takes the comparatives
    re-presented in the FOLLOWING year's releases / filings ('py') when all four of its quarters carry such a comparative and at
    least one was restated (discontinued operations: Sikorsky 2015, Otis / Carrier 2020; ASU 2017-07 pension reclassification
    2017; segment realignments 2023; the 2026 statement presentation for 2025). Years whose quarters were only partly re-presented
    (2014: Q3-Q4 only; 2019: Q2-Q4 only; 2022: Q3-Q4 only) stay as originally reported, and the recast figures are kept as memo
    keys (*_rc). Annual-only years (2006-2012) take the latest presentation available (10-K two years later 'py2', then next
    year's 10-K 'py', then as reported), so 2007-2008 are on the SFAS 160 basis and 2010-2011 on the 2012 discontinued-ops basis.
  - Balance sheet and cash flow: as originally reported in every period (discontinued-operations cash flows kept as a line).
  - Each recast period is recorded in DATA[period]['basis'] and REC_LOG for cell comments.
Cash flow: releases give year-to-date statements; discrete quarters are derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Segments are mapped onto the current lineage rows: Collins Aerospace (= Hamilton Sundstrand -> UTC Aerospace Systems -> Collins),
Pratt & Whitney, Raytheon (= RIS + RMD in 2020-2022), plus legacy Otis, Carrier / CCS, UTC Fire & Security and Sikorsky.
"""
import json, glob, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC, REC_LOG = {}, [], {}, {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json'))) if os.path.exists(os.path.join(BASE, 'manual_items.json')) else {}

def N(x): return 0.0 if x is None or isinstance(x, (str, list, dict)) else float(x)
def isnum(x): return isinstance(x, (int, float)) and not isinstance(x, bool)
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])
YEARS = range(2006, 2026)
QYEARS = range(2013, 2027)

def periods():
    out = [str(y) for y in YEARS]
    for y in QYEARS:
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# ---------------------------------------------------------------- segment lineage
SEGMAP = [('col', r'hamilton sundstrand|aerospace systems|collins'), ('pw', r'pratt'), ('rtn', r'^raytheon$'),
          ('ris', r'intelligence'), ('rmd', r'missiles'), ('otis', r'otis'), ('car', r'carrier|climate'), ('fs', r'fire'), ('sik', r'sikorsky')]
SEGS = ['col', 'pw', 'rtn', 'otis', 'car', 'fs', 'sik']
def segkey(name):
    n = name.lower().strip()
    for k, rx in SEGMAP:
        if re.search(rx, n): return k
    return None

# ---------------------------------------------------------------- basis selection
def restated(blk): return bool(blk) and bool(blk.get('restated')) and bool(blk.get('is'))

def choose_basis():
    """-> {period: ('orig'|'py'|'py2', reason)}"""
    basis = {}
    for y in YEARS:
        p = str(y); r = REC.get(p)
        if not r: continue
        if y < 2013:
            if restated(r.get('py2')): basis[p] = ('py2', r['py2'].get('reason'))
            elif restated(r.get('py')): basis[p] = ('py', r['py'].get('reason'))
            else: basis[p] = ('orig', None)
        else:
            qs = [REC.get(qk(y, q)) for q in (1, 2, 3, 4)]
            have = all(x and x.get('py') and x['py'].get('is') for x in qs)
            anyr = any(x and restated(x.get('py')) for x in qs)
            consistent = False
            if have and r.get('py') and r['py'].get('is'):       # the four re-presented quarters must sum to the re-presented year
                sq = sum(N(x['py']['is'].get('sales')) for x in qs); so = sum(N(x['py']['is'].get('op_profit')) for x in qs)
                consistent = abs(sq - N(r['py']['is'].get('sales'))) <= 2.5 and abs(so - N(r['py']['is'].get('op_profit'))) <= 2.5
            if have and anyr and consistent:
                reason = '; '.join(dict.fromkeys(x['py'].get('reason') for x in qs if restated(x.get('py'))))
                basis[p] = ('py', reason)
                for q in (1, 2, 3, 4): basis[qk(y, q)] = ('py', reason)
            else:
                basis[p] = ('orig', None)
                for q in (1, 2, 3, 4): basis[qk(y, q)] = ('orig', None)
                if anyr:
                    partial = [qk(y, q) for q in (1, 2, 3, 4) if qs[q - 1] and restated(qs[q - 1].get('py'))]
                    LOG.append(f'{y}: partial recast ({", ".join(partial)}) - kept as originally reported; recast figures in *_rc memo keys')
    for q in (1, 2, 3): basis[qk(2026, q)] = ('orig', None)
    return basis

def blocks(p, basis):
    """(is, seg, cust, ngaap) blocks on the chosen basis for period p."""
    r = REC[p]; b = basis.get(p, ('orig', None))[0]
    if b == 'orig': return r.get('is') or {}, r.get('seg') or {}, r.get('cust') or {}, r.get('ngaap') or {}
    src = r[b]
    pi = src.get('is') or {}
    if all(isnum(pi.get(k)) for k in ('sales', 'op_profit', 'ebt')):
        # a complete recast statement stands on its own; only dividends and share counts carry over from the original
        i = {k: v for k, v in pi.items() if v is not None}
        for k in ('dps', 'shares_basic', 'shares_diluted'):
            if not isnum(i.get(k)) and isnum((r.get('is') or {}).get(k)): i[k] = r['is'][k]
    else:
        i = dict(r.get('is') or {})
        i.update({k: v for k, v in pi.items() if v is not None})     # partial recast lines overlay the as-reported statement
    if isnum(pi.get('cont_ops')) and not isnum(pi.get('net_income')):
        # comparative restates the continuing lines but prints only attributable totals: rebuild NI / NCI from its own components
        disc = N(pi['disc_ops']) if isnum(pi.get('disc_ops')) else N(pi.get('ni_parent_disc')) + N(pi.get('nci_disc'))
        i['disc_ops'] = disc; i['net_income'] = N(pi['cont_ops']) + disc
        i['nci'] = N(pi.get('nci_cont')) + N(pi.get('nci_disc')) if isnum(pi.get('nci_cont')) else i.get('nci')
        LOG.append(f'{p}: recast net income = continuing {pi["cont_ops"]} + discontinued {disc} (computed from the comparative)')
    # a recast that moves results into discontinued operations must not keep the original total-only lines inconsistent
    if isnum(i.get('cont_ops')) and isnum(i.get('disc_ops')) and isnum(i.get('net_income')) and abs(N(i['cont_ops']) + N(i['disc_ops']) - N(i['net_income'])) > 1:
        LOG.append(f'{p}: recast cont + disc != net income ({i["cont_ops"]} + {i["disc_ops"]} vs {i["net_income"]})')
    ng = dict(r.get('ngaap') or {})
    pn = src.get('ngaap') or {}
    if pn.get('items'):                 # recast item list replaces the original totals unless the comparative prints its own
        for k in ('restr_total', 'acq_acct_adj_total', 'sig_items_op_total', 'tax_effect', 'adj_ni_pub', 'adj_eps_pub', 'adj_op_pub', 'adj_etr_pct_pub', 'eps_bridge', 'eps_bridge_start'):
            ng.pop(k, None)
    for k in ('adj_sales_pub', 'adj_op_pub', 'adj_ni_pub', 'adj_eps_pub', 'adj_etr_pct_pub', 'items', 'restr_total', 'acq_acct_adj_total', 'sig_items_op_total', 'tax_effect', 'eps_bridge', 'eps_bridge_start'):
        if pn.get(k) is not None: ng[k] = pn[k]
    ADJK = ('adj_sales_pub', 'adj_op_pub', 'adj_ni_pub', 'adj_eps_pub', 'adj_etr_pct_pub')
    if not isnum(pn.get('adj_op_pub')):
        alt = next((r[o] for o in ('py', 'py2') if o != b and r.get(o) and isnum(((r[o].get('ngaap') or {}).get('adj_op_pub')))
                    and isnum((r[o].get('is') or {}).get('op_profit')) and abs(N(r[o]['is']['op_profit']) - N(i.get('op_profit'))) <= 1), None)
        if alt:
            for k in ADJK:
                if isnum(alt['ngaap'].get(k)): ng[k] = alt['ngaap'][k]
            LOG.append(f'{p}: adjusted measures taken from the comparative on the same basis (adjusted OP {alt["ngaap"]["adj_op_pub"]})')
        elif isnum(ng.get('adj_op_pub')):
            put(p, 'adj_op_orig', ng['adj_op_pub'])
            LOG.append(f'{p}: adjusted OP {ng["adj_op_pub"]} is on the original basis only - not used on the recast basis (memo)')
            for k in ADJK: ng.pop(k, None)
    if not isnum(pn.get('adj_ni_pub')) and isnum(pn.get('adj_ni_computed')):
        ng['adj_ni_pub'] = pn['adj_ni_computed']; LOG.append(f'{p}: recast adjusted NI {pn["adj_ni_computed"]} derived by the extraction ({str(pn.get("note", ""))[:80]})')
    seg = src.get('seg') if (src.get('seg') or {}).get('segments') else r.get('seg')
    return i, seg or {}, src.get('cust') or r.get('cust') or {}, ng

# ---------------------------------------------------------------- P&L / segments / non-GAAP
def do_is(p, i):
    if not i.get('sales'): LOG.append(f'{p}: no income statement'); return
    put(p, 'rev', i['sales']); put(p, 'rev_prod', i.get('sales_products')); put(p, 'rev_serv', i.get('sales_services'))
    put(p, 'cogs', i.get('cogs')); put(p, 'rnd', i.get('rnd')); put(p, 'sga', i.get('sga'))
    oth = N(i.get('other_income')) + sum(N(v) for _, v in (i.get('other_op_lines') or []))
    put(p, 'oth_inc', oth)
    put(p, 'oth_op_labels', '; '.join(f'{l} {N(v):,.0f}' for l, v in (i.get('other_op_lines') or [])) or None)
    put(p, 'op', i.get('op_profit'))
    put(p, 'nsp', N(i.get('nonservice_pension')))
    intr = N(i.get('interest_exp_net')) if isnum(i.get('interest_exp_net')) else N(i.get('interest_exp')) - N(i.get('interest_inc'))
    put(p, 'int_net', intr); put(p, 'int_exp', i.get('interest_exp')); put(p, 'int_inc', i.get('interest_inc'))
    put(p, 'oth_nonop', N(i.get('other_nonop')))
    put(p, 'ebt', i.get('ebt')); put(p, 'tax', i.get('tax'))
    ni_tot = i.get('net_income'); nci = N(i.get('nci'))
    pre160 = isnum(i.get('ebt')) and isnum(i.get('tax')) and abs(N(i['ebt']) - N(i['tax']) - N(ni_tot)) > 1 and abs(N(i['ebt']) - N(i['tax']) - nci - N(ni_tot)) <= 1
    if pre160:        # minority interest deducted above net income: re-present as NI incl. NCI (SFAS 160 style) for the model
        put(p, 'ni_tot', N(ni_tot) + nci); put(p, 'pre160', 1)
    else: put(p, 'ni_tot', ni_tot)
    put(p, 'cont', i.get('cont_ops') if isnum(i.get('cont_ops')) else DATA[p]['x'].get('ni_tot'))
    put(p, 'disc', N(i.get('disc_ops')))
    put(p, 'nci', nci); put(p, 'ni', i.get('ni_parent') if isnum(i.get('ni_parent')) else N(ni_tot))
    put(p, 'disc_nci', nci - N(i.get('nci_cont')) if isnum(i.get('nci_cont')) else 0.0)
    put(p, 'ni_cont', i.get('ni_parent_cont') if isnum(i.get('ni_parent_cont')) else DATA[p]['x'].get('ni'))
    put(p, 'sh_b', i.get('shares_basic')); put(p, 'sh_d', i.get('shares_diluted'))
    put(p, 'eps_b', i.get('eps_basic')); put(p, 'eps_d', i.get('eps_dil'))
    put(p, 'eps_d_cont', i.get('eps_dil_cont') if isnum(i.get('eps_dil_cont')) else i.get('eps_dil'))
    put(p, 'dps', i.get('dps'))

def do_seg(p, s):
    segs = s.get('segments') or []
    tot = {k: {'rev': 0.0, 'op': 0.0, 'aop': 0.0, 'restr': 0.0, 'sig': 0.0, 'n': 0, 'aop_n': 0, 'names': []} for k in SEGS + ['ris', 'rmd']}
    for x in segs:
        k = segkey(x.get('name', ''))
        if not k: LOG.append(f'{p}: unmapped segment {x.get("name")}'); continue
        t = tot[k]; t['n'] += 1; t['names'].append(x['name'])
        t['rev'] += N(x.get('sales')); t['op'] += N(x.get('op_profit')); t['restr'] += N(x.get('restr')); t['sig'] += N(x.get('other_items'))
        if isnum(x.get('adj_op')): t['aop'] += N(x['adj_op']); t['aop_n'] += 1
    if tot['rtn']['n'] == 0 and (tot['ris']['n'] or tot['rmd']['n']):
        for f in ('rev', 'op', 'aop', 'restr', 'sig', 'n', 'aop_n'): tot['rtn'][f] = tot['ris'][f] + tot['rmd'][f]
        tot['rtn']['names'] = tot['ris']['names'] + tot['rmd']['names']
        put(p, 'rtn_is_sum', 1)
    for k in SEGS + ['ris', 'rmd']:
        t = tot[k]
        if t['n']:
            put(p, f's_{k}_rev', t['rev']); put(p, f's_{k}_op', t['op']); put(p, f's_{k}_restr', t['restr']); put(p, f's_{k}_sig', t['sig'])
            put(p, f's_{k}_name', ' + '.join(t['names']))
            if t['aop_n'] == t['n']: put(p, f's_{k}_aop', t['aop'])
            put(p, f's_{k}_items', (t['aop'] - t['op']) if t['aop_n'] == t['n'] else (t['restr'] - t['sig']))
    put(p, 's_elim_rev', s.get('elim_sales')); put(p, 's_elim_op', s.get('elim_op')); put(p, 's_elim_aop', s.get('elim_adj_op'))
    put(p, 's_corp_op', s.get('corp_op')); put(p, 's_corp_aop', s.get('corp_adj_op'))
    if isnum(s.get('elim_op')): put(p, 's_elim_items', N(s.get('elim_adj_op')) - N(s['elim_op']) if isnum(s.get('elim_adj_op')) else 0.0)
    if isnum(s.get('corp_op')): put(p, 's_corp_items', N(s.get('corp_adj_op')) - N(s['corp_op']) if isnum(s.get('corp_adj_op')) else 0.0)
    put(p, 's_fascas', s.get('fas_cas')); put(p, 's_acqadj', s.get('acq_acct_adj'))
    put(p, 's_tot_rev', s.get('total_seg_sales')); put(p, 's_tot_op', s.get('total_seg_op'))
    put(p, 's_consol_rev', s.get('consol_sales')); put(p, 's_consol_op', s.get('consol_op')); put(p, 's_consol_aop', s.get('consol_adj_op'))

CUSTMAP = [('fms', r'foreign military'), ('dcs', r'foreign government'), ('usg', r'u\.?s\.? government|us government'),
           ('comm', r'commercial'), ('mil', r'military|defense'), ('prod', r'^products?$'), ('serv', r'^services?$'), ('inter', r'inter[- ]?segment')]
def do_cust(p, cu):
    if not cu: return
    for segn, rows in cu.items():
        if not isinstance(rows, dict): continue
        k = segkey(segn)
        if not k: continue
        agg = {}
        for lab, v in rows.items():
            if not isnum(v): continue
            L = lab.lower().strip()
            if L.startswith('total') or 'business segment' in L or 'consolidated' in L: continue
            for ck, rx in CUSTMAP:
                if re.search(rx, L):
                    agg[ck] = agg.get(ck, 0.0) + N(v); break
            else: LOG.append(f'{p}: unmapped customer row {segn}: {lab}')
        for ck, v in agg.items(): put(p, f'c_{k}_{ck}', v)
        if k in ('col', 'pw'):
            d = sum(agg.get(x, 0.0) for x in ('usg', 'fms', 'dcs', 'mil'))
            if d or 'comm' in agg: put(p, f'c_{k}_def', d)
        if k in ('rtn', 'ris', 'rmd'):
            put(p, f'c_{k}_intl', agg.get('fms', 0.0) + agg.get('dcs', 0.0))
    # Raytheon = RIS + RMD in 2020-2022
    x = DATA.get(p, {}).get('x', {})
    if 'c_rtn_usg' not in x and ('c_ris_usg' in x or 'c_rmd_usg' in x):
        for ck in ('usg', 'fms', 'dcs', 'comm', 'prod', 'serv', 'inter', 'intl'):
            if f'c_ris_{ck}' in x or f'c_rmd_{ck}' in x: put(p, f'c_rtn_{ck}', N(x.get(f'c_ris_{ck}')) + N(x.get(f'c_rmd_{ck}')))

def do_ngaap(p, n, i):
    put(p, 'adj_rev_pub', n.get('adj_sales_pub')); put(p, 'adj_op_pub', n.get('adj_op_pub')); put(p, 'adj_ni_pub', n.get('adj_ni_pub'))
    put(p, 'adj_eps_pub', n.get('adj_eps_pub')); put(p, 'adj_etr_pub', n.get('adj_etr_pct_pub'))
    fcf = n.get('fcf_pub'); c = (REC.get(p) or {}).get('cf') or {}
    if isnum(fcf) and not p.isdigit() and int(p[1]) > 1 and isnum(c.get('cfo')) and isnum(c.get('capex')) and c.get('ytd_months', 3) > 3 \
            and abs(N(fcf) - (N(c['cfo']) + N(c['capex']))) <= 1:
        LOG.append(f'{p}: published FCF {fcf} is year to date - dropped from the quarter column'); fcf = None
    put(p, 'fcf_pub', fcf)
    items = n.get('items') or []
    agg = {'restr': 0.0, 'acq': 0.0, 'sig_op': 0.0, 'sig_rev': 0.0, 'nsp': 0.0, 'int': 0.0, 'taxd': 0.0, 'taxeff': 0.0, 'nci': 0.0, 'disc': 0.0, 'oth': 0.0}
    labs = {k: [] for k in agg}
    for it in items:
        cat, where = (it.get('cat') or 'OTHER').upper(), (it.get('where') or 'op').lower()
        pre, aft = it.get('pretax'), it.get('aftertax')
        lab = f"{it.get('label', '')[:90]} ({it.get('segment', '')}; {('pre-tax ' + format(N(pre), ',.0f')) if isnum(pre) else ''}{(' after-tax ' + format(N(aft), ',.0f')) if isnum(aft) else ''})"
        if cat == 'TAX': agg['taxeff'] += N(aft if isnum(aft) else pre); labs['taxeff'].append(lab); continue
        if cat == 'TAXD' and where == 'tax': agg['taxd'] += N(aft if isnum(aft) else pre); labs['taxd'].append(lab); continue
        if cat == 'NCI': agg['nci'] += N(aft if isnum(aft) else pre); labs['nci'].append(lab); continue
        if where == 'disc_ops': agg['disc'] += N(aft if isnum(aft) else pre); labs['disc'].append(lab); continue
        if where == 'tax': agg['taxd'] += N(aft if isnum(aft) else pre); labs['taxd'].append(lab); continue
        v = N(pre) if isnum(pre) else N(aft)
        if where == 'nonservice_pension': agg['nsp'] += v; labs['nsp'].append(lab)
        elif where == 'interest': agg['int'] += v; labs['int'].append(lab)
        elif where in ('other_nonop', 'nonop'): agg['oth'] += v; labs['oth'].append(lab)
        elif where == 'sales' or it.get('sales_item'): agg['sig_rev'] += v; labs['sig_rev'].append(lab)
        elif cat == 'RESTR': agg['restr'] += -v; labs['restr'].append(lab)
        elif cat == 'AMORT': agg['acq'] += -v; labs['acq'].append(lab)
        else: agg['sig_op'] += v; labs['sig_op'].append(lab)
    # published totals override the item sums where given
    restr = N(n.get('restr_total')) if isnum(n.get('restr_total')) else agg['restr']
    acq = -N(n.get('acq_acct_adj_total')) if isnum(n.get('acq_acct_adj_total')) else agg['acq']
    sig = N(n.get('sig_items_op_total')) if isnum(n.get('sig_items_op_total')) else agg['sig_op']
    if p.isdigit() and int(p) < 2013 and isnum(n.get('adj_op_pub')) and isnum(i.get('op_profit')) \
            and abs(N(i['op_profit']) + restr + acq - sig - N(n['adj_op_pub'])) > 1:
        sig2 = N(i['op_profit']) + restr + acq - N(n['adj_op_pub'])
        LOG.append(f'{p}: net significant items {sig2:,.0f} derived from published adjusted OP (item list sums to {sig:,.0f}; bullet amounts are approximate / basis differs)')
        sig = sig2; put(p, 'a_sig_derived', 1)
    put(p, 'a_restr', restr); put(p, 'a_acq', acq); put(p, 'a_sig', sig); put(p, 'a_sig_rev', agg['sig_rev'])
    put(p, 'a_nsp', agg['nsp']); put(p, 'a_int', agg['int']); put(p, 'a_oth', agg['oth']); put(p, 'a_taxd', agg['taxd']); put(p, 'a_nci', agg['nci']); put(p, 'a_disc', agg['disc'])
    put(p, 'a_taxeff', N(n.get('tax_effect')) if isnum(n.get('tax_effect')) else agg['taxeff'])
    put(p, 'a_taxeff_pub', 1 if (isnum(n.get('tax_effect')) or labs['taxeff']) else 0)
    for k, v in labs.items():
        if v: put(p, f'a_{k}_lab', '; '.join(v))
    put(p, 'a_n_items', len(items))
    if n.get('definitions'): put(p, 'a_def', str(n['definitions'])[:600])
    if n.get('guidance'): put(p, 'guidance', str(n['guidance']))

def do_kpi(p, r):
    k = r.get('kpi') or {}
    put(p, 'k_org', k.get('organic_growth_pct')); put(p, 'k_fx', k.get('fx_pct')); put(p, 'k_acq', k.get('acq_div_pct'))
    for segn, v in (k.get('seg_organic_pct') or {}).items():
        sk = segkey(segn)
        if sk and isnum(v): put(p, f'k_org_{sk}', v)
    put(p, 'k_bl_tot', k.get('backlog_total_bn')); put(p, 'k_bl_com', k.get('backlog_commercial_bn')); put(p, 'k_bl_def', k.get('backlog_defense_bn'))
    put(p, 'k_book_def', k.get('defense_bookings_bn'))
    for segn, v in (k.get('seg_backlog_bn') or {}).items():
        sk = segkey(segn)
        if sk and isnum(v): put(p, f'k_bl_{sk}', v)
    ng = k.get('narrative_growth_pct') or {}
    for a, b in (('collins_commercial_oe', 'k_col_oe'), ('collins_commercial_aftermarket', 'k_col_am'), ('collins_defense', 'k_col_def'),
                 ('pw_commercial_oe', 'k_pw_oe'), ('pw_commercial_aftermarket', 'k_pw_am'), ('pw_military', 'k_pw_mil')):
        if isnum(ng.get(a)): put(p, b, ng[a])

# ---------------------------------------------------------------- cash flow
def cf_block(p):
    r = REC.get(p)
    if not r or not r.get('cf') or not isnum(r['cf'].get('cfo')): return None
    c = r['cf']
    o = {}
    o['ni_start'] = N(c.get('ni')); o['dda'] = N(c.get('dda')); o['def'] = N(c.get('deferred_tax')); o['sbc'] = N(c.get('sbc'))
    o['pens'] = N(c.get('pension_noncash')); o['k401'] = N(c.get('k401_match')); o['contrib'] = N(c.get('pension_contrib')); o['wc'] = N(c.get('wc_total'))
    o['cfo'] = N(c['cfo'])
    o['oth'] = o['cfo'] - (o['ni_start'] + o['dda'] + o['def'] + o['sbc'] + o['pens'] + o['k401'] + o['contrib'] + o['wc'])
    o['capex'] = N(c.get('capex')); o['acq'] = N(c.get('acq')); o['divest'] = N(c.get('divest')); o['cfi'] = N(c.get('cfi'))
    o['oinv'] = o['cfi'] - o['capex'] - o['acq'] - o['divest']
    o['debt'] = N(c.get('debt_issue')) + N(c.get('debt_repay')) + N(c.get('cp_change')) + N(c.get('st_debt_change'))
    o['div'] = N(c.get('dividends')); o['bb'] = N(c.get('buyback')); o['cff'] = N(c.get('cff'))
    o['ofin'] = o['cff'] - o['debt'] - o['div'] - o['bb']
    o['fx'] = N(c.get('fx')); o['disc'] = sum(N(v) for v in (c.get('disc_ops_cf') or {}).values())
    o['net'] = N(c.get('net_change')); o['beg'] = c.get('cash_begin'); o['end'] = c.get('cash_end')
    o['restr'] = N(c.get('restricted_cash')) + N(c.get('cash_held_for_sale'))      # cash in the CF total that is not BS cash
    o['months'] = c.get('ytd_months')
    return o
FLOW = ('ni_start', 'dda', 'def', 'sbc', 'pens', 'k401', 'contrib', 'wc', 'oth', 'cfo', 'capex', 'acq', 'divest', 'oinv', 'cfi', 'debt', 'div', 'bb', 'ofin', 'cff', 'fx', 'disc', 'net')
def put_cf(p, o, beg):
    for k in FLOW: put(p, f'cf_{k}', o[k])
    put(p, 'cf_beg', beg); put(p, 'cf_end', o['end']); put(p, 'cf_restr', o['restr'])
    x = DATA[p]['x']
    if 'ni_tot' in x: put(p, 'cf_discni', round(o['ni_start'] - x['ni_tot'], 6))     # 0 when the statement starts from total net income

def do_cf():
    for y in YEARS:
        p = str(y); a = cf_block(p)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        put_cf(p, a, a['beg'])
    for y in QYEARS:
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q); cur = cf_block(p)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            if cur['months'] != 3 * q: LOG.append(f'{p}: ytd_months {cur["months"]} != {3 * q}')
            if q == 1 or prev is None:
                if q != 1: continue
                d = dict(cur); beg = cur['beg']
            else:
                d = {k: cur[k] - prev[0][k] for k in FLOW}; d.update(end=cur['end'], restr=cur['restr']); beg = prev[1]
            ov = (MAN.get('cf_quarter_override') or {}).get(p)
            if ov:                                  # release three-month column where YTD differencing would mix bases
                d = {k: float(ov[k]) for k in FLOW if k in ov}
                d['oinv'] = d['cfi'] - d['capex'] - d['acq'] - d['divest']; d['ofin'] = d['cff'] - d['debt'] - d['div'] - d['bb']
                d['oth'] = d['cfo'] - sum(d[k] for k in ('ni_start', 'dda', 'def', 'sbc', 'pens', 'k401', 'contrib', 'wc'))
                d['end'] = ov['end']; d['restr'] = ov['restr']; beg = ov['beg']
                LOG.append(f'{p}: cash flow from the release quarter column ({ov["why"][:60]})')
            put_cf(p, d, beg)
            prev = (cur, cur['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs') or not isnum(r['bs'].get('ta')): return
    b = r['bs']
    ta, tca = N(b['ta']), N(b.get('tca'))
    cash, ar, ca_c, inv = N(b.get('cash')), N(b.get('ar')), N(b.get('contract_assets')), N(b.get('inventory'))
    put(p, 'bs_cash', cash); put(p, 'bs_ar', ar); put(p, 'bs_cac', b.get('contract_assets')); put(p, 'bs_inv', inv)
    put(p, 'bs_oca', tca - cash - ar - ca_c - inv); put(p, 'bs_tca', tca)
    cfa, ppe, rou, gw, intg = N(b.get('customer_financing')), N(b.get('ppe')), N(b.get('rou')), N(b.get('goodwill')), N(b.get('intangibles'))
    put(p, 'bs_cfa', cfa); put(p, 'bs_ppe', ppe); put(p, 'bs_rou', b.get('rou')); put(p, 'bs_gw', gw); put(p, 'bs_int', intg)
    put(p, 'bs_onca', ta - tca - cfa - ppe - rou - gw - intg); put(p, 'bs_ta', ta)
    std, ap, clc, ltdc, tcl = N(b.get('st_debt')), N(b.get('ap')), N(b.get('contract_liabilities')), N(b.get('ltd_current')), N(b.get('tcl'))
    put(p, 'bs_std', std); put(p, 'bs_ap', ap); put(p, 'bs_clc', b.get('contract_liabilities')); put(p, 'bs_ltdc', ltdc)
    put(p, 'bs_accr', tcl - std - ap - clc - ltdc); put(p, 'bs_tcl', tcl)
    ltd, lease, pens, tl = N(b.get('ltd')), N(b.get('lease_ltl')), N(b.get('pension_obl')), N(b.get('tl'))
    put(p, 'bs_ltd', ltd); put(p, 'bs_lease', b.get('lease_ltl')); put(p, 'bs_pens', pens)
    put(p, 'bs_oncl', tl - tcl - ltd - lease - pens); put(p, 'bs_tl', tl)
    rnci = N(b.get('redeemable_nci')); te = N(b.get('te')) if isnum(b.get('te')) else N(b.get('equity_parent')) + N(b.get('nci'))
    nci = N(b.get('nci'))
    put(p, 'bs_rnci', rnci); put(p, 'bs_eq', te - nci); put(p, 'bs_nci', nci); put(p, 'bs_teq', te); put(p, 'bs_tle', b.get('tle'))
    put(p, 'bs_shares', b.get('shares_out'))
    put(p, 'debt_tot', std + ltdc + ltd); put(p, 'debt_st', std); put(p, 'debt_lt', ltdc + ltd)

# ---------------------------------------------------------------- extras (annual) and memo of recast figures
def do_extra(p):
    r = REC.get(p); e = (r or {}).get('extra') or {}
    if not e: return
    put(p, 'emp', e.get('employees'))
    for segn, v in (e.get('seg_dda') or {}).items():
        sk = segkey(segn)
        if sk and isnum(v): put(p, f'x_dda_{sk}', v)
    for segn, v in (e.get('seg_capex') or {}).items():
        sk = segkey(segn)
        if sk and isnum(v): put(p, f'x_capex_{sk}', v)
    pe = e.get('pension') or {}
    for a, b in (('fas_service_cost', 'x_fas_sc'), ('cas_expense', 'x_cas'), ('nonservice_pension_income', 'x_nsp'), ('contributions', 'x_pcontrib'), ('funded_status', 'x_funded')):
        if isnum(pe.get(a)): put(p, b, pe[a])

def do_rc_memo(p):
    """recast comparatives kept as memo keys for periods left on the as-reported basis."""
    r = REC.get(p)
    for src in ('py', 'py2'):
        blk = r.get(src)
        if restated(blk):
            i = blk['is']
            put(p, 'rc_rev', i.get('sales')); put(p, 'rc_op', i.get('op_profit')); put(p, 'rc_ni_cont', i.get('ni_parent_cont') if isnum(i.get('ni_parent_cont')) else i.get('ni_parent'))
            put(p, 'rc_eps', i.get('eps_dil_cont') if isnum(i.get('eps_dil_cont')) else i.get('eps_dil'))
            put(p, 'rc_adj_eps', (blk.get('ngaap') or {}).get('adj_eps_pub')); put(p, 'rc_adj_op', (blk.get('ngaap') or {}).get('adj_op_pub'))
            put(p, 'rc_reason', blk.get('reason')); put(p, 'rc_src', src)
            break

def do_unalloc(p, s):
    """adjustments not allocated to a segment, so that Σ adjusted segment OP + eliminations + corporate + FAS/CAS = adjusted OP."""
    x = DATA.get(p, {}).get('x', {})
    if 's_col_op' not in x or 'op' not in x: return
    segi = sum(N(x.get(f's_{k}_items')) for k in SEGS)
    resid = N(x.get('a_restr')) + N(x.get('a_acq')) - N(x.get('a_sig')) + N(x.get('s_acqadj')) - segi - N(x.get('s_corp_items'))
    if isnum((s or {}).get('elim_adj_op')):
        if abs(resid - N(x.get('s_elim_items'))) > 1.5: LOG.append(f'{p}: unallocated adjustments {resid:,.0f} vs published eliminations adjustment {x.get("s_elim_items")}')
        return
    put(p, 's_elim_items', resid)
    if abs(resid) > 0.5: LOG.append(f'{p}: adjustments not allocated to segments {resid:,.0f} (eliminations and other; derived)')

def run():
    load()
    basis = choose_basis()
    for p in periods():
        if p not in REC: LOG.append(f'{p}: no record'); continue
        b = basis.get(p, ('orig', None))
        DATA.setdefault(p, {})['basis'] = b
        if b[0] != 'orig': REC_LOG[p] = b
        i, s, cu, n = blocks(p, basis)
        do_is(p, i); do_seg(p, s); do_cust(p, cu); do_ngaap(p, n, i); do_kpi(p, REC[p]); do_bs(p); do_extra(p)
        if b[0] == 'orig': do_rc_memo(p)
        do_unalloc(p, s)
    do_cf()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        if not x: continue
        print(p, DATA[p]['basis'][0], {k: (round(x[k], 1) if isinstance(x.get(k), float) else x.get(k)) for k in
              ('rev', 'op', 'ni', 'adj_op_pub', 'adj_eps_pub', 'sh_d', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'debt_tot', 's_col_rev', 's_rtn_rev', 'c_col_comm')})
    print('\n'.join(LOG))
