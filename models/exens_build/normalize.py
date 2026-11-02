"""Flatten data/<period>.json (and releases.json) into model keys per model column period:
'2021' … '2025' (annual), 'H1-23', 'H2-23', 'H1-24', 'H2-24', 'H1-25', 'H2-25', 'H1-26'.

Basis policy (hybrid recast, DHR / STE precedent):
* FY2025 and FY2024 are on the continuing-operations basis of URD 2025 (Microwave Amplification, sold 31-Dec-2025, is discontinued;
  FY2024 column = the restated comparative, file 2024R.json). FY2023 and earlier are as originally reported (MA included).
* H1-26 and H1-25 are on the restated basis of the H1-2026 report (H1-25R.json); H1-24 and H1-23 as originally reported.
* H2 = FY − H1 for every flow; balance sheets are the period-end statements (H2 balance sheet = the 31-December balance sheet).
  H2-24 therefore = FY2024 restated − H1-24 as reported (mixed by MA's H1-24 contribution; flagged in the workbook).
* Segment revenue / adjusted gross margin for 2024 use the restated quarterly tables of the FY2025 release (continuing basis), so the
  segment build is on one basis from 2024; the difference to reported revenue is carried in an explicit basis-difference row.
* Originally reported figures for restated periods are kept as memo keys (orig_*).
Expenses are returned as positive amounts (cost lines, D&A, cost of net debt, income tax); two-sided items keep their sign.
"""
import json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(HERE, 'manual_items.json')))
RAW = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, 'data', '*.json')) if not f.endswith('releases.json')}
_rp = os.path.join(HERE, 'data', 'releases.json')
REL = json.load(open(_rp)) if os.path.exists(_rp) else {}

YRS = ['2021', '2022', '2023', '2024', '2025']
H1S = ['H1-23', 'H1-24', 'H1-25', 'H1-26']
HS = ['H1-23', 'H2-23', 'H1-24', 'H2-24', 'H1-25', 'H2-25', 'H1-26']
MAIN_FILE = {'2024': '2024R', 'H1-25': 'H1-25R'}          # restated files used in the main columns
ORIG_FILE = {'2024': '2024', 'H1-25': 'H1-25'}
BS_FILE = {'H1-25': 'H1-25'}                                # restated interim file carries no balance sheet

def n(x): return 0.0 if x is None else x
def g(d, *ks):
    for k in ks:
        if d is None: return None
        d = d.get(k) if isinstance(d, dict) else None
    return d
def pos(x): return None if x is None else -x
def pct(x): return None if x is None else x / 100.0

def ng_keys(ng):
    """model keys from an 'ng' (company APM) section"""
    x = {}
    m = {'adj_ebitda_pub': 'adj_ebitda', 'ebitda_pub': 'ebitda', 'sbc': 'sbc', 'nonrec': 'nonrec', 'dna_br': 'dna_impair', 'oth_ie_br': 'oth_inc_exp',
         'adj_ebit_pub': 'adj_ebit', 'cos_m': 'mgmt_cos', 'rd_m': 'mgmt_rd', 'sga_m': 'mgmt_sga', 'oth_m': 'mgmt_oth', 'cap_rd': 'cap_rd', 'capex': 'capex',
         'capex_g': 'capex_growth', 'capex_m': 'capex_maint', 'fcf_pub': 'fcf', 'fcf_pre': 'fcf_pre_growth', 'ni_ex_ppa_pub': 'ni_ex_ppa',
         'ni_cont_ex_ppa_pub': 'ni_cont_ex_ppa', 'ni_ex_brand_pub': 'ni_ex_brand', 'cash_conv_pub': 'cash_conv_pct', 'brand': 'brand_impair', 'ppa_amort': 'ppa_amort'}
    for k, src in m.items():
        if ng.get(src) is not None: x[k] = ng[src]
    oa = ng.get('oth_adj') if ng.get('oth_adj') is not None else ng.get('other_restatements')
    if oa is not None and x.get('sbc') is None and x.get('nonrec') is None: x['oth_adj'] = oa   # combined add-back where the split is not published
    for k in ('cos_m', 'rd_m', 'sga_m', 'oth_m'):
        if x.get(k) is not None: x[k] = -x[k]                      # management-basis costs positive
    for k in ('cap_rd', 'capex', 'capex_g', 'capex_m'):
        if x.get(k) is not None: x[k] = abs(x[k])                  # some tables print capex in parentheses
    if ng.get('dna_ex_ppa') is not None: x['dna_ex_ppa'] = abs(ng['dna_ex_ppa'])
    if x.get('ppa_amort') is not None: x['ppa_amort'] = abs(x['ppa_amort'])
    if x.get('cash_conv_pub') is not None: x['cash_conv_pub'] = pct(x['cash_conv_pub'])
    if x.get('dna_br') is not None and x.get('dna_ex_ppa') is not None and x.get('ppa_amort') is None:
        x['ppa_amort'] = round(x['dna_br'] - x['dna_ex_ppa'] - n(x.get('brand')), 1)   # implied by the company bridge
    return x

def flat(per, rec, bs_rec=None):
    """model keys from one period file"""
    x = {}
    i = rec.get('is') or {}
    if i.get('rev') is not None:
        x.update(rev=i.get('rev'), cos=pos(i.get('cos')), ext=pos(i.get('ext')), taxes=pos(i.get('taxes')), staff=pos(i.get('staff')),
                 oth_op=(None if i.get('oth_op_inc') is None and i.get('oth_op_exp') is None else n(i.get('oth_op_inc')) + n(i.get('oth_op_exp'))),
                 dna_prov=pos(i.get('dna_prov')), rop=i.get('rop'),
                 oth_ie=(None if i.get('oth_inc') is None and i.get('oth_exp') is None else n(i.get('oth_inc')) + n(i.get('oth_exp'))),
                 op=i.get('op'), cost_nd=pos(i.get('cost_net_debt')), deriv=i.get('deriv'), fin_oth=i.get('fin_oth'), net_fin=i.get('net_fin'),
                 ebt=i.get('ebt'), tax=pos(i.get('tax')), ni_cont=i.get('ni_cont') if i.get('ni_cont') is not None else i.get('ni'),
                 disc=i.get('disc') if i.get('disc') is not None else (0.0 if i.get('ni') is not None else None), ni=i.get('ni'),
                 eps_basic=i.get('eps_basic'), eps_dil=i.get('eps_dil'), eps_cont=i.get('eps_basic_cont'),
                 wsh=(i.get('wsh') / 1e6 if i.get('wsh') else None), wsh_dil=(i.get('wsh_dil') / 1e6 if i.get('wsh_dil') else None),
                 pref_div=i.get('pref_div'))
    s = rec.get('seg') or {}
    for k in ('amp_rev', 'di_rev', 'elim_rev', 'amp_agp', 'di_agp', 'oth_agp'):
        if s.get(k) is not None: x[k] = s[k]
    if s.get('agp') is not None: x['agp_pub'] = s['agp']
    for k in ('amp_g', 'di_g', 'tot_g', 'amp_lfl', 'di_lfl', 'tot_lfl'):
        if s.get(k) is not None: x[k] = pct(s[k])
    x.update(ng_keys(rec.get('ng') or {}))
    d = rec.get('dna') or {}
    if d.get('dna_ex_ifrs16') is not None:
        x.update(dna_fa=-d['dna_ex_ifrs16'], dna_rou=-n(d.get('dna_rou')), dna_cur=-n(d.get('impair_current')), dna_provn=-n(d.get('provisions')))
    f = rec.get('fin') or {}
    if f.get('int_bank') is not None:
        x.update(int_bank=-f['int_bank'], int_lease=-n(f.get('int_lease')), fin_fx=f.get('fx'))
    t = rec.get('tax') or {}
    if t.get('current') is not None: x.update(tax_cur=-t['current'], tax_def=-n(t.get('deferred')) - n(t.get('deferred_brand')))
    c = rec.get('cf') or {}
    if c.get('cfo') is not None:
        x.update(cf_ni=c.get('ni'), cf_fin=n(c.get('fin_cash')) + n(c.get('fin_noncash')), cf_tax=c.get('tax'), cf_dna=c.get('dna_prov'), cf_oth=c.get('oth'),
                 cf_taxp=c.get('tax_paid'), cf_wc=c.get('wc'), cfo=c.get('cfo'),
                 cf_capex=c.get('capex'), cf_acq=n(c.get('acq')) + n(c.get('divest')),
                 cf_oinv=n(c.get('disposals')) + n(c.get('grants')) + n(c.get('oth_fin_assets')), cfi=c.get('cfi'),
                 cf_eq=n(c.get('sh_iss')) + n(c.get('sh_iss_costs')) + n(c.get('treasury')), cf_div=n(c.get('div')),
                 cf_debt=n(c.get('ncb_in')) + n(c.get('ncb_out')) + n(c.get('cb_in')) + n(c.get('cb_out')) + n(c.get('loan_costs')) + n(c.get('early_rep')),
                 cf_int=n(c.get('int_paid')) + n(c.get('lease_int')) + n(c.get('deriv_inc')) + n(c.get('inv_inc')),
                 cf_lease=n(c.get('lease_rep')), cf_ofin=n(c.get('oth_fin')) + n(c.get('conv_int')), cff=c.get('cff'),
                 cf_fx=n(c.get('fx')), cf_net=c.get('net_change'), cf_disc=n(c.get('disc_cf')), cf_beg=c.get('beg'), cf_end=c.get('end'))
        x['cf_int_paid'] = n(c.get('int_paid')) + n(c.get('lease_int'))
        # residual lines absorb presentation differences between years (2021 predecessor format, 2023 URD regrouping)
        x['cf_oth'] = x['cfo'] - n(x['cf_ni']) - x['cf_fin'] - n(x['cf_tax']) - n(x['cf_dna']) - n(x['cf_taxp']) - n(x['cf_wc'])
        x['cf_oinv'] = n(x['cfi']) - n(x['cf_capex']) - x['cf_acq']
        x['cf_ofin'] = n(x['cff']) - x['cf_eq'] - x['cf_div'] - x['cf_debt'] - x['cf_int'] - x['cf_lease']
    b = (bs_rec or rec).get('bs') or {}
    if b and b.get('ta') is not None:
        x.update(bs_gw=b.get('gw'), bs_int=b.get('intang'), bs_ppe=b.get('ppe'), bs_rou=b.get('rou'), bs_eqinv=n(b.get('eq_inv')), bs_onca=n(b.get('oth_nca')),
                 bs_dta=n(b.get('dta')), bs_tnca=b.get('tnca'), bs_inv=b.get('inv'), bs_ar=b.get('ar'), bs_oca=n(b.get('oca')) + n(b.get('deriv_a')),
                 bs_cash=b.get('cash'), bs_tca=b.get('tca'), bs_ta=b.get('ta'), bs_cap=n(b.get('sh_cap')) + n(b.get('sh_prem')), bs_res=b.get('reserves'),
                 bs_teq=b.get('teq'), bs_ncb=b.get('ncb'), bs_ncll=n(b.get('ncll')), bs_pens=n(b.get('pens')), bs_oncl=n(b.get('oncl')), bs_dtl=n(b.get('dtl')),
                 bs_tncl=b.get('tncl'), bs_cb=n(b.get('cb')), bs_cll=n(b.get('cll')), bs_ap=b.get('ap'), bs_ocl=n(b.get('ocl')) + n(b.get('deriv_l')),
                 bs_tcl=b.get('tcl'), bs_tle=b.get('tle'),
                 shares_out=(b.get('shares_out') / 1e6 if b.get('shares_out') else None), treasury=(n(b.get('treasury')) / 1e6 if b.get('shares_out') else None))
        cd = b.get('cash_detail') or {}
        if cd: x['cash_adj'] = n(cd.get('accrued_interest')) + n(cd.get('overdraft'))   # BS cash − CF cash (CF cash is net of overdrafts, excl. accrued interest)
    db = (bs_rec or rec).get('debt') or {}
    for k, src in (('nd_pub', 'net_debt'), ('gross_pub', 'gross_debt'), ('lev_pub', 'leverage_x'), ('lev_ebitda', 'adj_ebitda_lev'), ('tlb', 'tlb'), ('rcf_drawn', 'rcf_drawn'), ('deriv_net', 'deriv_net')):
        if db.get(src) is not None: x[k] = db[src]
    e = rec.get('extra') or {}
    if e.get('employees') is not None and isinstance(e.get('employees'), (int, float)): x['employees'] = e['employees']
    if e.get('dps_declared') is not None: x['dps'] = e['dps_declared']
    if e.get('amort_intang') is not None: x['amort_int'] = -e['amort_intang']
    if e.get('dep_ppe') is not None: x['dep_ppe'] = -e['dep_ppe']
    if e.get('dep_rou') is not None: x['dep_rou'] = -e['dep_rou']
    return x

FLOW = ('rev', 'cos', 'ext', 'taxes', 'staff', 'oth_op', 'dna_prov', 'rop', 'oth_ie', 'op', 'cost_nd', 'deriv', 'fin_oth', 'net_fin', 'ebt', 'tax', 'ni_cont', 'disc', 'ni',
        'amp_rev', 'di_rev', 'elim_rev', 'amp_agp', 'di_agp', 'oth_agp', 'agp_pub', 'adj_ebitda_pub', 'ebitda_pub', 'sbc', 'nonrec', 'dna_br', 'oth_ie_br', 'dna_ex_ppa',
        'adj_ebit_pub', 'ppa_amort', 'brand', 'cos_m', 'rd_m', 'sga_m', 'oth_m', 'cap_rd', 'capex', 'capex_g', 'capex_m', 'fcf_pub', 'fcf_pre', 'ni_ex_ppa_pub',
        'ni_cont_ex_ppa_pub', 'dna_fa', 'dna_rou', 'dna_cur', 'dna_provn', 'int_bank', 'int_lease', 'fin_fx', 'tax_cur', 'tax_def',
        'cf_ni', 'cf_fin', 'cf_tax', 'cf_dna', 'cf_oth', 'cf_taxp', 'cf_wc', 'cfo', 'cf_capex', 'cf_acq', 'cf_oinv', 'cfi', 'cf_eq', 'cf_div', 'cf_debt', 'cf_int',
        'cf_lease', 'cf_ofin', 'cff', 'cf_fx', 'cf_net', 'cf_disc', 'cf_int_paid', 'amort_int', 'dep_ppe', 'dep_rou')

# ------------------------------------------------------------------ quarterly segment data from the releases (memo rows + restated 2024 halves)
QSRC = {2023: ('PR_9M24', 'fy2023_quarterly_revenue', 'fy2023_quarterly_adjusted_gross_margin', 'Q{n} 2023', 'originally reported (MA included)'),
        2024: ('PR_FY25', 'restated_quarterly_figures_2024', None, '{n}Q24', 'restated, continuing operations (FY2025 release appendix)'),
        2025: ('PR_FY25', 'quarterly_figures_2025', None, '{n}Q25', 'continuing operations (FY2025 release appendix)'),
        2026: ('PR_9M26', 'quarterly_figures_9m_2026', None, 'Q{n} 2026', '9M-2026 release appendix')}
SEGK = {'amp': 'Amplification', 'di': 'Detection & Imaging', 'tot': 'Total'}
def _elim(d):
    for k in ('Eliminations & Other', 'Eliminations & other', 'Eliminations and other'):
        if k in d: return d[k]
    return None

def quarter(y, nq):
    """{'amp','di','elim','tot','g','lfl','agp_amp','agp_di','agp','basis'} for quarter nq of year y, or {}"""
    if y not in QSRC or not REL: return {}
    rel, trev, tagm, fmt, basis = QSRC[y]
    key = fmt.format(n=nq)
    tbl = g(REL, rel, trev) or {}
    rv = tbl.get('revenue', tbl).get(key) if isinstance(tbl, dict) else None
    if not rv: return {}
    out = {'amp': rv.get(SEGK['amp']), 'di': rv.get(SEGK['di']), 'elim': _elim(rv), 'tot': rv.get('Total'), 'basis': basis}
    if rv.get('Growth pct') is not None: out['g'] = pct(rv['Growth pct'])
    if rv.get('Like-for-like pct') is not None: out['lfl'] = pct(rv['Like-for-like pct'])
    am = (g(REL, rel, tagm) if tagm else tbl.get('adjusted_gross_margin')) or {}
    av = am.get(key)
    if av:
        out.update(agp_amp=av.get(SEGK['amp']), agp_di=av.get(SEGK['di']), agp_oth=_elim(av), agp=av.get('Total'))
    return {k: v for k, v in out.items() if v is not None}

def run():
    X = {}
    for per in YRS + H1S:
        fn = MAIN_FILE.get(per, per)
        rec = RAW.get(fn)
        if rec is None: continue
        bs_rec = RAW.get(BS_FILE[per]) if per in BS_FILE else None
        x = flat(per, rec, bs_rec)
        if per in ORIG_FILE and RAW.get(ORIG_FILE[per]):
            o = flat(per, RAW[ORIG_FILE[per]])
            for k in ('rev', 'op', 'ni', 'adj_ebitda_pub', 'adj_ebit_pub', 'cfo', 'amp_rev', 'di_rev', 'elim_rev', 'agp_pub', 'amp_lfl', 'di_lfl', 'tot_lfl', 'tot_g', 'amp_g', 'di_g'):
                if o.get(k) is not None: x['orig_' + k] = o[k]
            x['restated'] = True
        X[per] = {'x': x, 'basis': rec.get('basis')}
    # H1-24: the H1-2024 report prints only a top-down EBITDA bridge; the detailed lines come from the H1-2025 report's comparative column
    if 'H1-24' in X and RAW.get('H1-25'):
        back = ng_keys(g(RAW['H1-25'], 'py', 'ng') or {})
        for k, v in back.items():
            if X['H1-24']['x'].get(k) is None: X['H1-24']['x'][k] = v
        X['H1-24']['x']['ng_backfilled'] = True
    # restated 2024 segment halves from the FY2025 release (continuing basis) replace the originally reported H1-24 segment figures
    if 'H1-24' in X and REL:
        h = g(REL, 'PR_FY25', 'restated_quarterly_figures_2024', 'revenue', '1H24')
        a = g(REL, 'PR_FY25', 'restated_quarterly_figures_2024', 'adjusted_gross_margin', '1H24')
        if h:
            xx = X['H1-24']['x']
            for k in ('amp_rev', 'di_rev', 'elim_rev', 'amp_agp', 'di_agp', 'oth_agp', 'agp_pub', 'amp_g', 'di_g', 'tot_g', 'amp_lfl', 'di_lfl', 'tot_lfl'):
                if xx.get(k) is not None: xx['orig_' + k] = xx[k]
            xx.update(amp_rev=h['Amplification'], di_rev=h['Detection & Imaging'], elim_rev=_elim(h), seg_restated=True, seg_flag='restated')
            for k in ('amp_g', 'di_g', 'tot_g', 'amp_lfl', 'di_lfl', 'tot_lfl'): xx.pop(k, None)
            if a: xx.update(amp_agp=a['Amplification'], di_agp=a['Detection & Imaging'], oth_agp=_elim(a), agp_pub=a['Total'])
    # H2 = FY − H1 (flows); balance sheet, debt and shares = year end
    for y in (2023, 2024, 2025):
        fy, h1 = X.get(str(y)), X.get(f'H1-{str(y)[2:]}')
        if not fy or not h1: continue
        a, b = fy['x'], h1['x']; x = {}
        for k in FLOW:
            if a.get(k) is not None and b.get(k) is not None: x[k] = a[k] - b[k]
        for k, v in a.items():
            if k.startswith('bs_') or k in ('shares_out', 'treasury', 'cash_adj', 'nd_pub', 'gross_pub', 'lev_pub', 'lev_ebitda', 'tlb', 'rcf_drawn', 'employees'): x[k] = v
        x['cf_beg'] = b.get('cf_end'); x['cf_end'] = a.get('cf_end')
        if a.get('sbc') is not None and b.get('sbc') is None and b.get('oth_adj') is not None:   # H2-23: FY split published, H1 combined
            x['oth_adj'] = a['sbc'] + n(a.get('nonrec')) - b['oth_adj']
            for k in ('sbc', 'nonrec'): x.pop(k, None)
        if y == 2024: x['seg_flag'] = 'restated'
        X[f'H2-{str(y)[2:]}'] = {'x': x, 'basis': f'derived: FY{y} − H1 ({fy.get("basis")}; H1 basis: {h1.get("basis")})'}
    # quarterly memo rows (first / second quarter of each half)
    for per in HS:
        y = 2000 + int(per[-2:]); h = int(per[1])
        q = quarter(y, 1 if h == 1 else 3); q2 = quarter(y, 2 if h == 1 else 4)
        xx = X.setdefault(per, {'x': {}})['x']
        for k, v in q.items():
            if k != 'basis': xx['qa_' + k] = v
        for k, v in q2.items():
            if k != 'basis': xx['qb_' + k] = v
        if q: xx['q_basis'] = q.get('basis')
    # annual quarterly growth memo (Q4 LFL etc.) and FY like-for-like for the restated 2024 (FY2025 release)
    for per, ov in MAN.get('overrides', {}).items():
        if per.startswith('_') or not isinstance(ov, dict): continue
        for k, v in ov.items():
            if not k.startswith('_'): X.setdefault(per, {'x': {}})['x'][k] = v
    return X

DATA = None
def get():
    global DATA
    if DATA is None: DATA = run()
    return DATA

if __name__ == '__main__':
    D = run()
    for p in YRS + HS:
        x = D.get(p, {}).get('x', {})
        print(p, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items() if k in ('rev', 'op', 'ni', 'adj_ebitda_pub', 'adj_ebit_pub', 'cfo', 'bs_cash', 'amp_rev', 'di_rev', 'qa_tot', 'qb_tot', 'ppa_amort', 'wsh')})
