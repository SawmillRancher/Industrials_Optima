"""Normalise data/<period>.json into flat model keys: DATA[period]['x'][key] (USD millions; per share in $; shares in millions).

Basis: as originally reported (each period from its own earnings release), with these documented exceptions
(latest filing that first presents the period; flagged in x['_notes'] and in the workbook):
  - Customer type: Department of War / Intelligence Community / Federal civilian (introduced Q1 FY26). FY2025 quarters and FY2025 take the
    comparatives of the FY2026 releases; the originally reported DoD / Federal civilian split is kept in legacy keys for every period.
  - Measures first published with prior-year comparatives (adjusted net income on the intangible-amortization definition, free cash flow,
    expertise / technology revenue, contract awards): the comparative fills the period it was first published for.
Cash flow: releases are year to date; discrete quarters = year to date less prior year to date (Q1 as reported)."""
import json, glob, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def load():
    D = {}
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        if os.path.basename(f).startswith('_'): continue
        d = json.load(open(f)); D[d['period']] = d
    return D

OP = [('cf_ni', r'^net income'), ('cf_da', r'^depreciation and amortization'), ('cf_sbc', r'^stock-based compensation'),
      ('cf_def', r'deferred income tax')]
def cf_buckets(lines):
    x = {k: 0.0 for k in ('cf_ni', 'cf_da', 'cf_sbc', 'cf_def', 'cf_oth', 'cf_wc', 'cf_capex', 'cf_acq', 'cf_oinv', 'cf_debt', 'cf_bb', 'cf_eq', 'cf_ofin')}
    wc = False
    for lab, st, v in lines:
        L = lab.lower()
        if v is None: continue
        if re.search(r'^net cash.*operating', L): x['cf_cfo'] = v
        elif re.search(r'^net cash.*investing', L): x['cf_cfi'] = v
        elif re.search(r'^net cash.*financing', L): x['cf_cff'] = v
        elif st == 'op':
            if L.startswith('accounts receivable'): wc = True
            k = 'cf_wc' if wc else next((k for k, p in OP if re.search(p, L)), 'cf_oth')
            x[k] += v
        elif st == 'inv':
            k = 'cf_capex' if L.startswith('capital exp') else 'cf_acq' if re.search(r'(purchases?|acquisitions?) of business|cash paid for business|working capital|divestiture', L) else 'cf_oinv'
            x[k] += v
        elif st == 'fin':
            k = ('cf_bb' if re.search(r'(re)?purchases? of common stock', L) else
                 'cf_debt' if re.search(r'credit facilit|borrowings|line of credit|financing costs|convertible note', L) else
                 'cf_ofin' if re.search(r'contingent consideration', L) else 'cf_eq')
            x[k] += v
        else:
            if L.startswith('effect of'): x['cf_fx'] = v
            elif re.search(r'^net (increase|decrease|change|\(decrease\)|\(increase\))', L): x['cf_net'] = v
            elif 'beginning' in L: x['cf_beg'] = v
            elif 'end of' in L: x['cf_end'] = v
    if 'cf_fx' not in x and 'cf_net' in x: x['cf_fx'] = x['cf_net'] - x['cf_cfo'] - x['cf_cfi'] - x['cf_cff']      # line printed without amounts (Q2 FY22 release)
    x.setdefault('cf_fx', 0.0)
    res = x['cf_cff'] - (x['cf_debt'] + x['cf_bb'] + x['cf_eq'] + x['cf_ofin'])
    if abs(res) > 0.02: x['cf_debt'] += res      # borrowing lines printed without amounts (Q2 FY22 release): derived as the residual to the subtotal
    if 'cf_net' not in x: x['cf_net'] = x['cf_cfo'] + x['cf_cfi'] + x['cf_cff'] + x['cf_fx']
    return {k: round(v, 6) for k, v in x.items()}
FLOW = ('cf_ni', 'cf_da', 'cf_sbc', 'cf_def', 'cf_oth', 'cf_wc', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_oinv', 'cf_cfi', 'cf_debt', 'cf_bb', 'cf_eq', 'cf_ofin', 'cf_cff', 'cf_fx', 'cf_net')

def run():
    D = load()
    P = lambda fy, q: f'Q{q}-{str(fy)[2:]}' if q else str(fy)
    for p, d in D.items():
        x, notes = {}, []
        i = d['is']
        for k in ('rev', 'direct', 'indirect', 'da', 'oi', 'int_net', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d'):
            if k in i: x[k] = i[k]
        x['ni_tot'] = i.get('ni_tot', round(i['ebt'] - i['tax'], 6))
        x['nci'] = round(x['ni_tot'] - x['ni'], 6)
        # ---- revenue tables
        c = d.get('cust', {})
        x['cl_dod'] = c.get('dod') if 'ic' not in c else None           # legacy basis (DoD incl. intelligence agencies)
        x['cl_fed'] = c.get('fedciv') if 'ic' not in c else None
        if 'ic' in c: x.update(c_dod=c['dod'], c_ic=c['ic'], c_fed=c['fedciv'])
        x['c_comm'] = round(c.get('comm', 0) + c.get('state', 0), 6) if c else None
        for sec, mp in (('ctype', (('t_cpf', 'cpf'), ('t_ffp', 'ffp'), ('t_tm', 'tm'))), ('prime', (('p_prime', 'prime'), ('p_sub', 'sub'))),
                        ('exptech', (('e_exp', 'exp'), ('e_tech', 'tech'))), ('dcost', (('dc_labor', 'labor'), ('dc_odc', 'odc')))):
            for a, b in mp:
                if b in d.get(sec, {}): x[a] = d[sec][b]
        if d.get('orders') is not None: x['orders'] = d['orders']
        if d.get('awards') is not None: x['awards'] = d['awards']
        k = d.get('kpi', {})
        if 'backlog_total' in k: x['bl_total'] = k['backlog_total']
        if 'backlog_funded' in k: x['bl_funded'] = k['backlog_funded']
        o = d.get('organic', {})
        if 'acq' in o:
            x['acq_rev'] = o['acq']
            if o.get('base'): x['org_pub'] = round((o['org_rev'] / o['base'] - 1), 6)
        if d['q'] and 'organic_text_pct' in k and 'acq' not in o and d['fy'] >= 2020:
            v = MAN['organic_overrides'].get(p, k['organic_text_pct'])
            if v is not None: x['org_pub'] = v / 100.0; x['org_quote'] = k['organic_text'][-170:]
        if d['q'] is None and 'organic_pct' in d.get('k10', {}):
            x['org_pub'] = d['k10']['organic_pct'] / 100.0; x['org_quote'] = d['k10']['organic_quote'][-150:]
        # ---- segments
        s = d.get('seg') or {}
        if s:
            x['sg_dom'], x['sg_int'] = s['rev_dom'], s['rev_intl']
            if p == 'Q4-16': s = dict(s, p_dom=None, p_intl=None)      # FY - 9M mixes pre- and post-ASU 2016-09 net income; not derived
            pre = 'sgo_' if s['measure'] == 'income from operations' else 'sgn_'
            if s['p_dom'] is not None: x[pre + 'dom'], x[pre + 'int'] = s['p_dom'], s['p_intl']
        # ---- non-GAAP
        n = d.get('ngaap', {})
        if 'rec_da' in n: x['da_direct'] = round(n['rec_da'] - i['da'], 6)
        for a in ('earnout', 'prod_adj', 'fp_adj'):
            if a in n: x['eb_' + a] = n[a]
        pub = n.get('adj_ebitda_pub', n.get('ebitda_pub'))
        if pub is not None: x['ebitda_pub'] = pub; x['ebitda_lab'] = 'adjusted' if 'adj_ebitda_pub' in n else 'ebitda'
        if pub is not None:      # basis difference: company reconciliation uses net interest (excl. other items) and, FY2010-16, NCI
            x['eb_bdiff'] = round(pub - (x['ni'] + x['tax'] + x['int_net'] + i['da'] + x.get('da_direct', 0) + sum(x.get('eb_' + a_, 0) for a_ in ('earnout', 'prod_adj', 'fp_adj'))), 6)
        for a, b in (('adj_ni_pub', 'adj_ni_pub'), ('adj_eps_pub', 'adj_eps_pub'), ('a_sbc', 'a_sbc'), ('a_amfin', 'a_amfin'), ('a_ncint', 'a_ncint'),
                     ('a_tax', 'a_tax'), ('a_intang', 'a_intang'), ('a_da', 'a_da'), ('pf_adj_ni', 'pf_adj_ni'), ('pf_adj_eps', 'pf_adj_eps')):
            if b in n: x[a] = n[b]
        if 'pf_adj_ni' in x:      # FY2011-12 "pro forma" (ex earn-out) adjusted net income = the published headline measure
            x['adj_ni_pub'] = x['pf_adj_ni']; x['adj_eps_pub'] = x.get('pf_adj_eps')
        for a in ('cfo', 'marpa', 'cfo_ex', 'capex', 'fcf'):
            if 'fcf_' + a in n: x['f_' + a] = n['fcf_' + a]
        # ---- balance sheet
        b = d.get('bs') or {}
        g = lambda *ks: round(sum(b.get(kk, 0) or 0 for kk in ks), 6)
        if b:
            x.update(bs_cash=b['cash'], bs_ar=b['ar'], bs_oca=b['oca'], bs_tca=b['tca'], bs_ta=b['ta'], bs_ppe=b['ppe'], bs_rou=b.get('rou', 0.0),
                     bs_cd=b['cur_debt'], bs_ap=b['ap'], bs_comp=b['accr_comp'], bs_ocl=b['ocl'], bs_tcl=b['tcl'], bs_ltd=b['ltd'],
                     bs_lease=b.get('lease_l', 0.0), bs_teq=b['teq'], bs_tle=b['tle'])
            x['bs_tl'] = b.get('tl', round(b['tle'] - b['teq'], 6))
            if 'gw' in b: x['bs_gw'], x['bs_int'] = b['gw'], b['intang']
            else:
                gw = (d.get('k10') or {}).get('gw') if d['q'] in (None, 4) else None
                if gw is None: gw = (d.get('x') or {}).get('gw')
                if gw is None and d['q'] == 4: gw = (D.get(str(d['fy']), {}).get('k10') or {}).get('gw')
                if gw is not None and 0 < b['gw_int'] - gw < 0.45 * b['gw_int']:
                    x['bs_gw'], x['bs_int'] = gw, round(b['gw_int'] - gw, 6)
                else:
                    x['bs_gwint'] = b['gw_int']; notes.append('goodwill / intangibles split not available; combined line shown')
            x['bs_onca'] = round(x['bs_ta'] - x['bs_tca'] - x['bs_ppe'] - x['bs_rou'] - (x.get('bs_gw', 0) + x.get('bs_int', 0) + x.get('bs_gwint', 0)), 6)
            x['bs_def'] = b.get('def_tax', 0.0)
            x['bs_oltl'] = round(x['bs_tl'] - x['bs_tcl'] - x['bs_ltd'] - x['bs_lease'] - x['bs_def'], 6)
            x['bs_nci'] = b.get('nci', 0.0)
        xx = d.get('x') or {}
        if 'sh_out' in xx: x['bs_shares'] = xx['sh_out']
        am = MAN['amortization_annual'].get(p) if d['q'] is None else None
        am = am if am is not None else n.get('a_intang', xx.get('amort') if (d['q'] is None or d['fy'] >= 2021) else None)
        if am is not None: x['amort'] = am
        if 'employees' in (d.get('k10') or {}): x['employees'] = d['k10']['employees']
        x['_notes'] = notes
        d['x'] = x
    # ---- cash flow: discrete quarters from year to date
    for p, d in D.items():
        if 'cf' not in d: continue
        ytd = cf_buckets(d['cf']['lines'])
        x = d['x']
        if d['q'] in (None, 1):
            x.update(ytd)
        else:
            prev = D.get(P(d['fy'], d['q'] - 1))
            if prev and 'cf' in prev:
                pv = cf_buckets(prev['cf']['lines'])
                for kk in FLOW: x[kk] = round(ytd[kk] - pv[kk], 6)
                x['cf_beg'] = pv['cf_end']; x['cf_end'] = ytd['cf_end']
            elif d['q'] == 2 and d['fy'] == 2013: pass
        # FCF discrete where the release gave only year to date is not needed: releases give three-month columns
    # ---- fills from the following year's comparatives (first publication of the measure / customer recast)
    for p, d in D.items():
        fy, q = d['fy'], d['q']
        nx = D.get(P(fy + 1, q))
        if not nx: continue
        x, py = d['x'], nx.get('py', {})
        pn = py.get('ngaap', {})
        for a, b in (('adj_ni_pub', 'adj_ni_pub'), ('adj_eps_pub', 'adj_eps_pub'), ('a_intang', 'a_intang'), ('a_tax', 'a_tax'),
                     ('f_cfo', 'fcf_cfo'), ('f_marpa', 'fcf_marpa'), ('f_cfo_ex', 'fcf_cfo_ex'), ('f_capex', 'fcf_capex'), ('f_fcf', 'fcf_fcf')):
            if a not in x and pn.get(b) is not None and fy >= 2019 and (a.startswith('f_') or 'a_intang' in pn):
                x[a] = pn[b]; x.setdefault('_py', []).append(a)
        if 'amort' not in x and 'a_intang' in x: x['amort'] = x['a_intang']
        for sec, mp in (('exptech', (('e_exp', 'exp'), ('e_tech', 'tech'))),):
            for a, b in mp:
                if a not in x and b in py.get(sec, {}): x[a] = py[sec][b]; x.setdefault('_py', []).append(a)
        if 'awards' not in x and py.get('awards') is not None: x['awards'] = py['awards']; x.setdefault('_py', []).append('awards')
        pc = py.get('cust', {})
        if 'ic' in pc and 'c_ic' not in x:
            x.update(c_dod=pc['dod'], c_ic=pc['ic'], c_fed=pc['fedciv'], c_comm_rc=round(pc.get('comm', 0), 6)); x.setdefault('_py', []).append('cust')
            x['c_comm_orig'] = x['c_comm']; x['c_comm'] = x['c_comm_rc']
    # derived acquired revenue where only narrative organic growth exists: (total growth - organic growth) x prior-year revenue
    for p, d in D.items():
        x = d['x']; pr = D.get(P(d['fy'] - 1, d['q']))
        if 'acq_rev' not in x and 'org_pub' in x and pr:
            x['acq_rev_d'] = round(x['rev'] - pr['x']['rev'] * (1 + x['org_pub']), 3)
    # ---- model helper keys
    for p, d in D.items():
        x = d['x']
        if x.get('c_ic') is None and x.get('cl_dod') is not None: x['c_ns'] = round(x['cl_dod'] + x['cl_fed'], 6)
        if x.get('c_ic') is not None and x.get('cl_dod') is None and d['fy'] <= 2025: pass
        v = x.get('acq_rev', x.get('acq_rev_d'))
        if v is not None: x['acq_any'] = v
        if 'ebitda_pub' in x: x['eb_adj'] = round(sum(x.get('eb_' + a_, 0) for a_ in ('earnout', 'prod_adj', 'fp_adj')), 6)
        if 'a_sbc' in x and 'a_intang' not in x:
            x['a_old'] = round(x['a_sbc'] + x.get('a_da', x['da']) + x.get('a_amfin', 0) + x.get('a_ncint', 0) + x.get('eb_earnout', 0), 6)
            x['a_old_lab'] = ('stock-based compensation %.1f; depreciation and amortization %.1f; amortization of financing costs %.1f; non-cash interest %.1f; earn-out adjustments %.1f'
                              % (x['a_sbc'], x.get('a_da', x['da']), x.get('a_amfin', 0), x.get('a_ncint', 0), x.get('eb_earnout', 0)))
        if 'amort' in x: x['dep_tot'] = round(x['da'] + x.get('da_direct', 0) - x['amort'], 6)
        if 'f_marpa' in x: x['f_marpa'] = x['f_marpa']
    dd = MAN['debt']['at_2026_09_30']
    D['Q1-27']['x']['ds_rev_in'] = dd['revolver']; D['2026']['x']['ds_rev_in'] = 660.0; D['Q4-26']['x']['ds_rev_in'] = 660.0; D['2025']['x']['ds_rev_in'] = 124.5; D['Q4-25']['x']['ds_rev_in'] = 124.5
    return D

if __name__ == '__main__':
    D = run()
    for p in ('2010', 'Q2-21', 'Q3-25', 'Q1-27'):
        print(p, {k: v for k, v in D[p]['x'].items() if not k.startswith('org_q')})
