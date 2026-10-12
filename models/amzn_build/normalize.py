"""Harmonise the extracted Amazon data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m; shares m).

Basis policy (documented in README.md and in the workbook cell comments):
  - Income statement, cash flow, balance sheet: as originally reported in each period's own earnings release (quarters: the
    three-month columns; FY: the twelve-month columns of the Q4 release). Amazon's releases print discrete three-month cash
    flows, so no year-to-date derivation is needed (quarters vs FY are checked in check_data.py).
  - Segments: NA / International until 2014 (AWS inside North America; segment operating income before stock-based compensation
    and "other operating expense (income), net", which were unallocated). AWS segment from Q1-15, with FY2013 and Q1-Q4/FY2014
    recast in the 8-K Ex. 99.3 of 23-Apr-2015 (taken as the current-segment basis; the original NA-incl.-AWS figures are kept as
    legacy memo keys). From Q1-16 stock-based compensation and other operating items are allocated to the segments, and the 2016
    releases restated the 2015 comparatives on that basis: 2015 segment operating income takes the restated comparative
    (hybrid recast, commented). 2013-2014 current-basis segment operating income stays before SBC (unallocated row).
  - Net sales by groups of similar products (online stores, physical stores, third-party seller services, subscription services,
    advertising services, AWS, other): from the latest release presenting each quarter (Amazon re-presents the groups, e.g.
    advertising services split out of "other" from the Q4-21 release, back to Q3-20); available from Q2-16. FY = sum of quarters.
  - Per-share data and share counts: 20-for-1 stock split effective 6-Jun-2022 — figures in documents filed before that date
    are multiplied (shares) / divided (per-share) by 20.
  - Debt: the face balance sheet shows only long-term debt; the current portion of long-term debt (XBRL LongTermDebtCurrent, from
    2011) and short-term borrowings (XBRL ShortTermBorrowings, from 2021) sit inside "accrued expenses and other". Finance-lease
    liabilities (capital leases before 2019) from XBRL. Restricted cash: the cash-flow statement includes it from 2018 (memo).
"""
import json, glob, os, datetime as dt
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SPLIT_DATE = '2022-06-06'
FY0, FYQ0, FYC = 2006, 2013, 2026


def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return 2000 + int(p[-2:]), int(p[1])


def periods():
    out = [str(y) for y in range(FY0 - 1, FYC)]
    for y in range(FYQ0 - 1, FYC + 1):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == FYC and q > 2)]
    return out


def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v


def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)


def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        REC[k] = json.load(open(f))


def split_f(r): return 20.0 if r.get('filed', '9999') < SPLIT_DATE else 1.0


# ------------------------------------------------------------------ income statement
def do_is(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i = r['is']; sf = split_f(r)
    put(p, 'filed', r.get('filed')); put(p, 'src', r['sources']['release'])
    put(p, 'rev', i['rev']); put(p, 'rev_prod', i.get('rev_prod')); put(p, 'rev_serv', i.get('rev_serv'))
    for k in ('cogs', 'ful', 'mkt', 'tech', 'ga', 'oi', 'int_inc', 'int_exp', 'ebt', 'tax', 'ni'):
        put(p, k, i.get(k))
    put(p, 'othop', N(i.get('othop')))
    put(p, 'oth_inc', N(i.get('oth_inc')) + N(i.get('remeas')))          # 2006-08: "remeasurements and other" shown separately
    put(p, 'equity', N(i.get('equity')) + N(i.get('cum_eff')))
    for k in ('eps_b', 'eps_d'):
        if i.get(k) is not None: put(p, k, i[k] / sf)
    for k in ('sh_b', 'sh_d'):
        if i.get(k) is not None: put(p, k, i[k] * sf)
    put(p, 'split_f', sf)


# ------------------------------------------------------------------ segments
RC = None
def seg_current(p):
    """current segment basis (NA ex AWS, International, AWS) or None."""
    fy, q = fyq(p)
    r = REC.get(p, {})
    if p in RC['periods']:                                  # FY2013, Q1-Q4/FY2014: AWS recast (8-K 23-Apr-2015, Ex. 99.3)
        return RC['periods'][p], 'recast_aws'
    if fy == 2015:                                          # 2015: restated comparatives in the 2016 releases (SBC allocated)
        nk = '2016' if p.isdigit() else qk(2016, q)
        py = (REC.get(nk, {}).get('py') or {}).get('seg')
        if py: return py, 'recast_sbc'
    s = r.get('seg') or {}
    if s.get('aws_rev') is not None: return s, 'reported'
    return None, None


def do_seg(p):
    r = REC.get(p)
    if not r: return
    s = r.get('seg') or {}
    fy, q = fyq(p)
    if s.get('aws_rev') is None:                            # legacy two-segment basis (as originally reported)
        put(p, 'leg_na_rev', s.get('na_rev')); put(p, 'leg_na_oi', s.get('na_oi'))
        put(p, 'leg_intl_rev', s.get('intl_rev')); put(p, 'leg_intl_oi', s.get('intl_oi'))
        put(p, 'leg_unalloc', N(s.get('unalloc_sbc')) + N(s.get('unalloc_oth')) if s else None)
    cur, basis = seg_current(p)
    if cur:
        for k in ('na', 'intl', 'aws'):
            put(p, f'{k}_rev', cur.get(f'{k}_rev')); put(p, f'{k}_oi', cur.get(f'{k}_oi'))
        un = N(cur.get('unalloc_sbc')) + N(cur.get('unalloc_oth'))
        if basis == 'recast_sbc' or fy >= 2016: un = 0.0
        put(p, 'seg_unalloc', un)
        put(p, 'seg_basis', basis)
        if basis != 'reported': LOG.append(f'{p}: segments on {basis}')
    if s.get('aws_rev') is not None and basis == 'recast_sbc':      # as originally reported 2015 (memo)
        put(p, 'orig_na_oi', s.get('na_oi')); put(p, 'orig_intl_oi', s.get('intl_oi')); put(p, 'orig_aws_oi', s.get('aws_oi'))
        put(p, 'orig_unalloc', N(s.get('unalloc_sbc')) + N(s.get('unalloc_oth')))
    if basis == 'recast_aws':                               # original 2014 NA (incl. AWS) and International
        put(p, 'leg_na_rev', s.get('na_rev')); put(p, 'leg_na_oi', s.get('na_oi'))
        put(p, 'leg_intl_rev', s.get('intl_rev')); put(p, 'leg_intl_oi', s.get('intl_oi'))
        put(p, 'leg_unalloc', N(s.get('unalloc_sbc')) + N(s.get('unalloc_oth')))
    m = r.get('media') or {}
    if m:
        for k in ('media', 'egm', 'other'):
            put(p, f'mx_{k}', N(m.get(f'na_{k}')) + N(m.get(f'intl_{k}')))


GRP = ('online', 'physical', 'tp', 'subs', 'ads', 'aws', 'other')
def do_groups():
    g = json.load(open(os.path.join(BASE, 'data', '_groups.json')))
    for p, rec in g.items():
        v = rec['v']
        for k in GRP:
            if f'grp_{k}' in v: put(p, f'grp_{k}', v[f'grp_{k}'])
        put(p, 'grp_src', rec['source'])
        if 'grp_physical' not in v and 'grp_online' in v: put(p, 'grp_physical', 0.0)    # blank before Whole Foods (Aug-2017)
        if 'grp_ads' not in v and 'grp_online' in v: put(p, 'grp_ads_in_other', 1)
    for y in range(FY0, FYC):
        qs = [qk(y, q) for q in (1, 2, 3, 4)]
        if all(x_(q, 'grp_online') is not None for q in qs):
            partial_ads = any(x_(q, 'grp_ads') is None for q in qs)
            for k in GRP:
                vals = [x_(q, f'grp_{k}') for q in qs]
                if k == 'ads' and partial_ads: continue
                if k == 'other' and partial_ads: vals = [N(x_(q, 'grp_other')) + N(x_(q, 'grp_ads')) for q in qs]
                if all(v is not None for v in vals): put(str(y), f'grp_{k}', sum(vals))
            if partial_ads: put(str(y), 'grp_ads_in_other', 1)


# ------------------------------------------------------------------ cash flow
WC_PAT = ('Inventories', 'Accounts receivable', 'Other assets', 'Accounts payable', 'Accrued expenses', 'Additions to unearned',
          'Amortization of previously unearned', 'Unearned revenue')
def do_cf(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return
    c = r['cf']
    ni, dda, sbc, dt_ = c.get('ni', x_(p, 'ni')), N(c.get('dda')), N(c.get('sbc')), N(c.get('deftax'))
    wc = 0.0; seen = set()
    for l, v in c['lines_raw']:
        if l in seen: continue
        if l.startswith(WC_PAT): wc += v; seen.add(l)
        if 'operating activities' in l: break
    cfo = c['cfo']
    put(p, 'cf_ni', ni); put(p, 'cf_dda', dda); put(p, 'cf_sbc', sbc); put(p, 'cf_def', dt_)
    put(p, 'cf_othnc', cfo - ni - dda - sbc - dt_ - wc); put(p, 'cf_wc', wc); put(p, 'cf_cfo', cfo)
    capex, proc = c.get('capex', 0.0), N(c.get('capex_proc'))
    put(p, 'cf_capex', capex); put(p, 'cf_capex_proc', proc); put(p, 'cf_acq', N(c.get('acq')))
    sec = N(c.get('sec_sales')) + N(c.get('sec_purch'))
    put(p, 'cf_sec', sec); put(p, 'cf_oinv', c['cfi'] - capex - proc - N(c.get('acq')) - sec); put(p, 'cf_cfi', c['cfi'])
    put(p, 'cf_bb', N(c.get('bb'))); put(p, 'cf_debt', N(c.get('debt_net'))); put(p, 'cf_lease', N(c.get('lease_prin')))
    put(p, 'cf_ofin', c['cff'] - N(c.get('bb')) - N(c.get('debt_net')) - N(c.get('lease_prin'))); put(p, 'cf_cff', c['cff'])
    put(p, 'cf_fx', N(c.get('fx'))); put(p, 'cf_net', c.get('net', cfo + c['cfi'] + c['cff'] + N(c.get('fx'))))
    put(p, 'cf_beg', c.get('beg')); put(p, 'cf_end', c.get('end'))
    put(p, 'fcf_mod', cfo + capex + proc)
    s = r.get('supp') or {}
    for k in ('fcf_ttm', 'fcf_lease_ttm', 'fcf_eq_ttm', 'ocf_ttm', 'fx_ww', 'fx_na', 'fx_intl', 'fx_aws', 'employees'):
        put(p, k, s.get(k))
    if s.get('fx_ww') is not None: put(p, 'fx_ww_f', s['fx_ww'] / 100.0)
    # finance-lease additions and operating-lease cash payments (supplemental cash-flow information)
    raw = dict(c['lines_raw'])
    fl = next((v for l, v in raw.items() if l.startswith('Property and equipment acquired under finance leases') or l.startswith('Property and equipment acquired under capital leases')), None)
    put(p, 'fl_add', fl)


# ------------------------------------------------------------------ balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']; fy, q = fyq(p)
    ta, tca, tcl, te = b['ta'], b['tca'], b['tcl'], b['te']
    put(p, 'bs_cash', b['cash']); put(p, 'bs_msec', N(b.get('msec'))); put(p, 'bs_inv', b['inv']); put(p, 'bs_ar', b['ar'])
    put(p, 'bs_oca', tca - b['cash'] - N(b.get('msec')) - b['inv'] - b['ar']); put(p, 'bs_tca', tca)
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_oplease', N(b.get('oplease'))); put(p, 'bs_gw', b['gw'])
    put(p, 'bs_onca', ta - tca - b['ppe'] - N(b.get('oplease')) - b['gw']); put(p, 'bs_ta', ta)
    put(p, 'bs_ap', b['ap']); put(p, 'bs_accr', b['accr']); put(p, 'bs_unearned', N(b.get('unearned')))
    put(p, 'bs_tcl', tcl)
    put(p, 'bs_ltlease', N(b.get('ltlease'))); put(p, 'bs_ltd', N(b.get('ltd')))
    put(p, 'bs_oltl', b['tle'] - te - tcl - N(b.get('ltlease')) - N(b.get('ltd')))
    put(p, 'bs_eq', te); put(p, 'bs_tle', b['tle'])
    # XBRL debt / lease detail (instant at the period end; as first filed)
    cur = xbrl.value('LongTermDebtCurrent', fy, 'I', q); st = xbrl.value('ShortTermBorrowings', fy, 'I', q)
    face_cur = b.get('cltd')                                 # 2008 releases: current portion shown as its own face line
    put(p, 'debt_cur', cur if cur is not None else (0.0 if fy < 2011 else None)); put(p, 'debt_st', st if st is not None else 0.0)
    if cur is None and fy < 2011: put(p, 'debt_cur_nd', 1)
    put(p, 'debt_lt', N(b.get('ltd')))
    put(p, 'debt_tot', N(b.get('ltd')) + N(x_(p, 'debt_cur')) + N(x_(p, 'debt_st')))
    put(p, 'debt_notes', N(b.get('ltd')) + N(x_(p, 'debt_cur')))
    put(p, 'bs_std', N(x_(p, 'debt_cur')) + N(x_(p, 'debt_st')))
    if face_cur is not None:
        put(p, 'debt_cur', face_cur); put(p, 'debt_tot', N(b.get('ltd')) + face_cur + N(x_(p, 'debt_st'))); put(p, 'debt_notes', N(b.get('ltd')) + face_cur)
        put(p, 'bs_std', face_cur + N(x_(p, 'debt_st'))); put(p, 'bs_accr_x', b['accr'])
    else:
        put(p, 'bs_accr_x', b['accr'] - N(x_(p, 'debt_cur')) - N(x_(p, 'debt_st')))
    flc = xbrl.value('FinanceLeaseLiabilityCurrent', fy, 'I', q); fll = xbrl.value('FinanceLeaseLiabilityNoncurrent', fy, 'I', q)
    if flc is None:
        flc = xbrl.value('CapitalLeaseObligationsCurrent', fy, 'I', q); fll = xbrl.value('CapitalLeaseObligationsNoncurrent', fy, 'I', q)
    if flc is not None: put(p, 'fl_tot', abs(flc) + abs(N(fll)))
    s = r.get('supp') or {}
    if s.get('sh_out') is not None: put(p, 'bs_shares', s['sh_out'] * split_f(r))


def do_xbrl(p):
    fy, q = fyq(p)
    kind = 'FY' if p.isdigit() else 'Q'
    put(p, 'xb_rev', xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'], fy, kind, q))
    put(p, 'xb_oi', xbrl.value('OperatingIncomeLoss', fy, kind, q))
    put(p, 'xb_ni', xbrl.value('NetIncomeLoss', fy, kind, q))
    put(p, 'xb_ta', xbrl.value('Assets', fy, 'I', q))


# published TTM free cash flow vs the sum of the originally reported quarters: prior-quarter cash flows restated in the release
FCF_RESTATED = {'Q1-17': 'ASU 2016-09 (adopted Q1-17, retrospective): excess tax benefits from stock-based compensation reclassified from financing to operating cash flow in the prior-year quarters (Q2-Q4/16: $113m, $173m, $336m)',
                'Q2-17': 'ASU 2016-09 restatement of the Q3-Q4/16 operating cash flows (excess tax benefits $173m + $336m)',
                'Q3-17': 'ASU 2016-09 restatement of the Q4/16 operating cash flow (excess tax benefits $336m)',
                'Q1-18': 'ASU 2016-15 / ASU 2016-18 (adopted Q1-18, retrospective): 2017 quarterly operating cash flows restated (Q1-17 -$29m, Q2-17 +$21m, Q3-17 -$74m, Q4-17 per the FY2017 restatement)',
                'Q2-18': 'ASU 2016-15 / ASU 2016-18 restatement of the Q3-Q4/17 operating cash flows',
                'Q3-18': 'ASU 2016-15 / ASU 2016-18 restatement of the Q4/17 operating cash flow'}
def do_fcf_basis():
    for p in periods():
        if p.isdigit() or x_(p, 'fcf_ttm') is None: continue
        ps = [p]
        for _ in range(3):
            y, q = fyq(ps[-1]); ps.append(qk(y, q - 1) if q > 1 else qk(y - 1, 4))
        if any(x_(k, 'fcf_mod') is None for k in ps): continue
        d = x_(p, 'fcf_ttm') - sum(x_(k, 'fcf_mod') for k in ps)
        if p in FCF_RESTATED:
            put(p, 'fcf_basis', d); put(p, 'fcf_basis_note', FCF_RESTATED[p])
            if x_(p, 'fcf_lease_ttm') is not None: put(p, 'fcf_lease_basis', x_(p, 'fcf_lease_ttm') - sum(x_(k, 'fcf_mod') + x_(k, 'cf_lease') for k in ps))


def do_manual():
    """company-quantified special charges (release text), energy-derivative remeasurements (10-Q), P&E depreciation (XBRL)."""
    sc, en = MAN['special_charges'], MAN['energy_derivatives']
    for p in periods():
        if not DATA.get(p): continue
        fy, q = fyq(p)
        if p.isdigit():
            qs = [qk(fy, k) for k in (1, 2, 3, 4)]
            put(p, 'sc_tot', sum(sc.get(k, {}).get('amount', 0.0) for k in qs)); put(p, 'sc_na', sum(sc.get(k, {}).get('na', 0.0) for k in qs))
            put(p, 'en', sum(en.get(k, 0.0) for k in qs))
            dep = xbrl.value('Depreciation', fy, 'FY')
        else:
            put(p, 'sc_tot', sc.get(p, {}).get('amount', 0.0)); put(p, 'sc_na', sc.get(p, {}).get('na', 0.0)); put(p, 'en', en.get(p, 0.0))
            if sc.get(p): put(p, 'sc_text', sc[p]['text'])
            dep = xbrl.value('Depreciation', fy, 'Q', q)
            if dep is None and q == 4:
                a, n9 = xbrl.value('Depreciation', fy, 'FY'), xbrl.value('Depreciation', fy, 'YTD', 3)
                if a is not None and n9 is not None: dep = a - n9; put(p, 'dep_derived', 1)
        put(p, 'dep', dep)
    put('Q3-25', 'oi_ex_sc_pub', 21700.0); put('Q4-25', 'oi_ex_sc_pub', 27400.0)


def run():
    global RC
    load()
    RC = REC['_recast']
    for p in periods():
        do_is(p); do_seg(p); do_cf(p); do_bs(p); do_xbrl(p)
    do_groups(); do_fcf_basis(); do_manual()
    return DATA


if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'na_rev', 'aws_oi', 'seg_unalloc', 'grp_ads', 'cf_cfo', 'fcf_ttm', 'bs_ta', 'debt_tot', 'fl_tot', 'bs_shares')})
    print('\n'.join(LOG))
