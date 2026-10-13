"""Harmonise the extracted GE Aerospace data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: GE Aerospace continuing operations (GE Vernova spun 2-Apr-2024 and GE HealthCare spun 3-Jan-2023, both in discontinued
operations). FY2022-23 and the 2023 quarters are the recast comparatives first presented on that basis (2024 Forms 10-Q / 10-K and
2024 releases); Q1-24 from the Q1-25 Form 10-Q / release; Q2-24 onward as originally reported. Q4 statement and segment data =
FY (10-K) - 9M (Q3 10-Q); Q4 non-GAAP and orders from the Q4 release. Q1-23 = H1-23 - Q2-23.
Segments: CES / DPT as reported in each period; the Jan-2026 recast (Aeroderivative CES -> DPT, T&O site revenue and cost from
Corporate & Other to the segments) applies from Q1-26, with the recast Q1-25 / Q2-25 comparatives kept as *_rc memo keys and the
FY2025 revised segment figures ($bn, unaudited estimates, Q4-25 release) in manual_items.json.
Cash flow: year-to-date statements -> discrete quarters (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M). Q1-23 and Q2-23 are not
available on the GE Aerospace basis (only H1-23 was re-presented), so their cash flows are blank and Q3-23 starts from H1-23.
Diluted / basic shares: EPS notes (10-Q three-month columns; FY from the 10-K); Q4 = 4 x FY - (Q1 + Q2 + Q3) (noted);
Q1-23 from the 11-Apr-2024 Form 8-K Ex. 99.1 (1,097 diluted / 1,089 basic)."""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
CFY = json.load(open(os.path.join(BASE, 'data', '_cf_ytd.json')))

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])
ANNUAL = ['2022', '2023', '2024', '2025']
def periods():
    out = list(ANNUAL)
    for y in range(2023, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q > 2)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# ---------------------------------------------------------------- P&L, segments, non-GAAP
def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i, s, g = r['is'], r['seg'], r['ng']
    for k in ('rev_eq', 'rev_sv', 'rev_ins', 'rev', 'cogs_eq', 'cogs_sv', 'sga', 'rd', 'int', 'ins_cost', 'nonop', 'tcost', 'oth', 'ebt', 'tax',
              'ni_cont', 'disc', 'ni', 'ni_co', 'ni_common'):
        put(p, k, i.get(k))
    put(p, 'sep', N(i.get('sep'))); put(p, 'gw_imp', N(i.get('gw_imp'))); put(p, 'debt_ext', N(i.get('debt_ext')))
    put(p, 'nci', N(i.get('nci'))); put(p, 'pref', -N(i.get('pref')))                      # preferred dividends as a positive deduction
    put(p, 'adj_rev', i['rev'] - i['rev_ins'])
    put(p, 'cogs', i['cogs_eq'] + i['cogs_sv'])
    # continuing operations attributable to common shareholders
    nci_c = i.get('nci_cont')
    if nci_c is None:
        nci_c = N(i.get('nci'))                                             # 2025+: no NCI in discontinued operations
        if i.get('ni_cc_eps') is not None and abs(i['ni_cont'] - nci_c + N(i.get('pref')) - i['ni_cc_eps']) > 5:
            # Q1-24 (Q1-25 10-Q comparative): the statement's NCI line still includes GE Vernova's NCI -> continuing NCI from the EPS note
            LOG.append(f'{p}: continuing NCI derived as NI from continuing operations - EPS-note numerator ({i["ni_cont"] - i["ni_cc_eps"]:+.0f}; statement total NCI {nci_c:+.0f})')
            nci_c = i['ni_cont'] + N(i.get('pref')) - i['ni_cc_eps']
    put(p, 'nci_cont', nci_c)
    ni_cc = i.get('ni_cont_common')
    if ni_cc is None: ni_cc = i['ni_cont'] - nci_c + N(i.get('pref'))       # preferred dividends presented negative
    if i.get('ni_cc_eps') is not None and abs(i['ni_cc_eps'] - ni_cc) > 0.6:
        LOG.append(f'{p}: continuing NI to common {ni_cc:,.0f} (statement) -> {i["ni_cc_eps"]:,.0f} (EPS note)')
        ni_cc = i['ni_cc_eps']
    put(p, 'ni_cc', ni_cc)
    put(p, 'ni_cc_eps', i.get('ni_cc_eps'))                                                   # EPS-note numerator (incl. excise / accretion 2023)
    put(p, 'eps_cont_d', i.get('eps_cont_d', g.get('eps_cont'))); put(p, 'eps_d', i.get('eps_d'))
    put(p, 'sh_d', i.get('sh_d')); put(p, 'sh_b', i.get('sh_b'))
    # segments
    for k in ('ces_eq', 'ces_sv', 'ces', 'ces_op', 'ds', 'pat', 'dpt_eq', 'dpt_sv', 'dpt', 'dpt_op', 'c_ins_rev', 'c_elim', 'c_rev', 'c_g_biz', 'c_g_eq',
              'c_restr', 'c_sep', 'c_ins_op', 'c_te_op', 'c_op_gaap', 'c_adj', 'c_costs', 'c_elim_op', 'u_ce', 'u_leap', 'u_isv', 'u_def',
              'rpo_tot', 'rpo_ces', 'rpo_dpt'):
        put(p, k, s.get(k))
    if s.get('u_isv') is not None: put(p, 'u_isv_p', s['u_isv'] / 100)
    put(p, 'c_imp', N(s.get('c_imp'))); put(p, 'c_ru', N(s.get('c_ru')))
    for k, v in (r.get('seg_rc') or {}).items(): put(p, k + '_rc', v)
    for k in ('op_op', 'c_adj'):
        v = (r.get('ng_rc') or {}).get(k)
        if v is not None: put(p, k + '_rc', v)
    if s.get('c_adj') is not None and (r.get('seg_rc') or {}).get('c_adj') is not None: put(p, 'c_adj_rc', r['seg_rc']['c_adj'])
    # non-GAAP (company-published)
    if g:
        put(p, 'adj_rev_pub', g.get('op_adj_rev')); put(p, 'op_pub', g.get('op_op'))
        for k in ('ins_rev', 'ins_cost', 'te_oi', 'te_cost', 'int', 'nonop', 'restr', 'sep', 'gw', 'g_eq', 'g_biz', 'nci_add', 'adj_oi', 'adj_cost'):
            put(p, 'ng_' + k, N(g.get('op_' + k)))
        for k in ('ins', 'te', 'nonop', 'gbiz', 'geq', 'restr', 'sep', 'gw', 'ru'):
            put(p, f'ae_{k}_pre', N(g.get(f'ae_{k}_pre'))); put(p, f'ae_{k}_tax', N(g.get(f'ae_{k}_tax')))
        put(p, 'ae_pref', N(g.get('ae_pref'))); put(p, 'ae_start', g.get('ae_start'))
        net = lambda *ks: sum(N(g.get(f'ae_{k}_pre')) + N(g.get(f'ae_{k}_tax')) for k in ks)
        put(p, 'e_ins', -net('ins')); put(p, 'e_te', -net('te')); put(p, 'e_nonop', -net('nonop')); put(p, 'e_gain', -net('gbiz', 'geq'))
        put(p, 'e_restr', -net('restr')); put(p, 'e_sep', -net('sep')); put(p, 'e_oth', -net('gw', 'ru') - N(g.get('ae_pref')))
        put(p, 'ng_te_op_neg', -(N(g.get('op_te_oi')) - N(g.get('op_te_cost'))))
        put(p, 'adj_ni_pub', g.get('ae_adj')); put(p, 'adj_eps_pub', g.get('ae_adj_eps'))
        for k in ('cfoa', 'ins_cfoa', 'capex', 'ppe_disp', 'sep', 'restr', 'tax_sale', 'fcf'):
            put(p, 'fcf_' + k, N(g.get('fcf_' + k)) if k != 'fcf' else g.get('fcf_fcf'))
        put(p, 'ord_ces', g.get('ord_ces')); put(p, 'ord_dpt', g.get('ord_dpt'))
        put(p, 'eps_cont_rel', g.get('eps_cont'))

def do_manual():
    cap = MAN['capital']
    for p, v in list(cap['dps_q'].items()) + list(cap['dps_a'].items()): put(p, 'dps', v)
    rv = MAN['seg_fy25_revised']
    for k, kk in (('ces_sv', 'ces_sv_rc'), ('ces_eq', 'ces_eq_rc'), ('ces', 'ces_rc'), ('dpt', 'dpt_rc'), ('ces_op', 'ces_op_rc'), ('dpt_op', 'dpt_op_rc'),
                  ('corp', 'c_adj_rc')):
        put('2025', kk, rv[k])
    LOG.append('2025: Jan-2026 segment structure (revised FY2025, $bn estimates) from the Q4-25 release guidance table')

def do_shares():
    """Q4 weighted shares = 4 x FY - (Q1 + Q2 + Q3); Q1-23 from the 11-Apr-2024 8-K."""
    put('Q1-23', 'sh_d', 1097.0); put('Q1-23', 'sh_b', 1089.0)
    LOG.append('Q1-23 shares: 11-Apr-2024 Form 8-K Ex. 99.1 (diluted 1,097m / basic 1,089m)')
    for y in (2023, 2024, 2025):
        for k in ('sh_d', 'sh_b'):
            q = [x_(qk(y, n), k) for n in (1, 2, 3)]
            if None not in q and x_(str(y), k) is not None:
                put(qk(y, 4), k, 4 * x_(str(y), k) - sum(q)); put(qk(y, 4), 'sh_q4_derived', 1)

# ---------------------------------------------------------------- cash flow
OPL = ['dep', 'amort', 'gw_imp', 'g_eq', 'pens', 'taxnet', 'wc', 'oth_op']
def cf_lines(c):
    o = {'cf_ni': N(c.get('ni')), 'cf_disc': N(c.get('disc')), 'cf_dep': N(c.get('dep')), 'cf_amort': N(c.get('amort')), 'cf_gw_imp': N(c.get('gw_imp')),
         'cf_geq': N(c.get('g_eq')), 'cf_pens': N(c.get('pens_cost')) + N(c.get('pens_contr')) + N(c.get('opeb')),
         'cf_taxnet': N(c.get('tax_prov')) + N(c.get('tax_paid')),
         'cf_wc': sum(N(c.get(k)) for k in ('wc_ar', 'wc_inv', 'wc_ca', 'wc_cl', 'wc_prog', 'wc_ap', 'wc_sda'))}
    o['cf_cfo'] = c['cfo']
    o['cf_oth_op'] = c['cfo'] - sum(o[k] for k in ('cf_ni', 'cf_disc', 'cf_dep', 'cf_amort', 'cf_gw_imp', 'cf_geq', 'cf_pens', 'cf_taxnet', 'cf_wc'))
    o['cf_capex'] = N(c.get('capex')); o['cf_ppe_disp'] = N(c.get('ppe_disp')); o['cf_acq'] = N(c.get('acq'))
    o['cf_biz_disp'] = N(c.get('biz_disp')) + N(c.get('ret_int'))
    o['cf_ins_sec'] = N(c.get('ins_sec')); o['cf_cfi'] = c['cfi']
    o['cf_oinv'] = c['cfi'] - o['cf_capex'] - o['cf_ppe_disp'] - o['cf_acq'] - o['cf_biz_disp'] - o['cf_ins_sec']
    o['cf_debt'] = N(c.get('st_debt')) + N(c.get('new_debt')) + N(c.get('repay'))
    o['cf_div'] = N(c.get('div')); o['cf_pref'] = N(c.get('pref_red')); o['cf_bb'] = N(c.get('bb')); o['cf_cff'] = c['cff']
    o['cf_ofin'] = c['cff'] - o['cf_debt'] - o['cf_div'] - o['cf_pref'] - o['cf_bb']
    o['cf_discops'] = N(c.get('cfo_disc')) + N(c.get('cfi_disc')) + N(c.get('cff_disc'))
    o['cf_fx'] = N(c.get('fx'))
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + o['cf_discops'] + o['cf_fx']
    return o

def do_cf():
    seq = {2023: [None, 'H1-23', '9M-23', '2023'], 2024: ['Q1-24', 'H1-24', '9M-24', '2024'], 2025: ['Q1-25', 'H1-25', '9M-25', '2025'],
           2026: ['Q1-26', 'H1-26', None, None]}
    for y in ('2022', '2023', '2024', '2025'):
        c = CFY[y]; o = cf_lines(c)
        for k, v in o.items(): put(y, k, v)
        put(y, 'cf_beg', c['beg']); put(y, 'cf_end', c['end']); put(y, 'cf_disc_cash', -N(c.get('disc_cash'))); put(y, 'cf_end_cont', c['end_cont'])
    for y, ks in seq.items():
        prev = None
        for q, k in enumerate(ks, 1):
            p = qk(y, q)
            if k is None:
                if y == 2023 and q == 1: LOG.append('Q1-23 / Q2-23: cash flow not re-presented on the GE Aerospace basis (H1-23 only)')
                prev = None if q == 1 else prev
                continue
            c = CFY[k]; lc = cf_lines(c)
            if q == 1:
                d = lc; beg = c['beg']
            elif prev is None:
                if y == 2023 and q == 2: prev = (lc, c['end']); continue           # H1-23 kept as the base for Q3-23
                continue
            else:
                d = {kk: lc[kk] - prev[0][kk] for kk in lc}; beg = prev[1]
            for kk, v in d.items(): put(p, kk, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', c['end']); put(p, 'cf_disc_cash', -N(c.get('disc_cash'))); put(p, 'cf_end_cont', c['end_cont'])
            prev = (lc, c['end'])
    # Q2-23: H1-23 base only -> the quarter itself has no discrete cash flow; record H1 values for the FY check
    LOG.append('Q3-23 cash flow = 9M-23 - H1-23; Q4-23 = FY2023 - 9M-23')

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']
    put(p, 'bs_cash', b['cash']); put(p, 'bs_invsec_cur', N(b.get('inv_sec_cur'))); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', b['inv'])
    put(p, 'bs_ctr_a', b['ca_ctr']); put(p, 'bs_tca', b['tca'])
    put(p, 'bs_oca', b['tca'] - b['cash'] - N(b.get('inv_sec_cur')) - b['ar'] - b['inv'] - b['ca_ctr'])   # derived: other current + held for sale (absorbs rounding)
    put(p, 'bs_invsec', b['inv_sec']); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_ctr_def', b['ctr_def']); put(p, 'bs_dta', b['dta']); put(p, 'bs_disc_a', N(b.get('disc_a')))
    put(p, 'bs_oa', b['ta'] - b['tca'] - b['inv_sec'] - b['ppe'] - b['gw'] - b['intang'] - b['ctr_def'] - b['dta'] - N(b.get('disc_a')))
    put(p, 'bs_ta', b['ta'])
    put(p, 'bs_std', b['std']); put(p, 'bs_ap', b['ap']); put(p, 'bs_prog', N(b.get('prog'))); put(p, 'bs_ctr_l', b['ctr_liab'])
    put(p, 'bs_sda', N(b.get('sda'))); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ocl', b['tcl'] - b['std'] - b['ap'] - N(b.get('prog')) - b['ctr_liab'] - N(b.get('sda')))
    put(p, 'bs_definc', N(b.get('def_inc'))); put(p, 'bs_ltd', b['ltd']); put(p, 'bs_insl', b['ins_liab']); put(p, 'bs_comp', b['comp'])
    put(p, 'bs_disc_l', N(b.get('disc_l')))
    put(p, 'bs_ol', b['tl'] - b['tcl'] - N(b.get('def_inc')) - b['ltd'] - b['ins_liab'] - b['comp'] - N(b.get('disc_l')))
    put(p, 'bs_ol_all', b['tl'] - b['tcl'] - b['ltd'] - b['ins_liab'] - b['comp'])
    put(p, 'bs_tl', b['tl']); put(p, 'bs_eq', b['eq']); put(p, 'bs_nci', N(b.get('nci'))); put(p, 'bs_teq', b['te']); put(p, 'bs_tle', b['tle'])
    put(p, 'bs_shares', b.get('shares_out'))
    put(p, 'debt_tot', b['std'] + b['ltd'])

def run():
    load()
    for p in periods():
        do_pl(p); do_bs(p)
    do_shares(); do_cf(); do_manual()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('adj_rev', 'op_pub', 'ni_cc', 'adj_ni_pub', 'sh_d', 'cf_cfo', 'cf_oth_op', 'cf_end_cont', 'bs_cash', 'bs_ta', 'debt_tot')})
    print('\n'.join(LOG))
