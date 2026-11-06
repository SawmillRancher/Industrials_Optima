"""Harmonise the extracted package data (data/<period>.json) into flat model keys: DATA[period]['x'][key].

Basis (the 'basis' key records it): every period as originally reported in its own results package. Q4 quarters whose
package shows only fiscal-year columns (FY2021-FY2025 Management's Analysis / annual report) are derived as FY - 9M and
flagged 'q4_derived'; the Q4 media-release headline figures (net sales, adjusted EBIT, adjusted net income, segment sales /
EBIT) are kept as cross-checks. Europe is a discontinued operation from Q1 FY27: FY2027 quarters are continuing operations
and the recast FY2026 comparatives published in the FY27 releases are stored under *_rc keys (ni_cont = as-reported
net income from continuing operations).
Signs: costs positive; asbestos adjustments positive = charge; interest, net positive = expense; other non-operating positive
= expense; tax positive = expense. Pre-FY2022 packages print expenses in parentheses, so each sign is resolved with the
statement identities (GP - opex = EBIT; EBIT - interest - other = EBT; EBT - tax = NI).
Cash flow: packages give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
PK = json.load(open(os.path.join(BASE, 'data', '_packages.json')))

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def ytdk(y, q): return {1: qk(y, 1), 2: f'H1-{str(y)[2:]}', 3: f'9M-{str(y)[2:]}', 4: str(y)}[q]
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4, 'H1': 2, '9M': 3}[p[:2]]

OWN = {}      # period -> ordered list of source dates (own package first, then later packages)
def index_sources():
    for p in PK:
        k = qk(p['fy'], p['q'])
        score = ('ma' in p['docs']) + 2 * ('er' in p['docs']) + ('fs' in p['docs']) + ('iar' in p['docs'])
        for kk in [k] + ([str(p['fy'])] if p['q'] == 4 else []):
            OWN.setdefault(kk, []).append((p['date'], score))
    for k in OWN:
        OWN[k] = [d for d, s in sorted(OWN[k], key=lambda x: (-x[1], x[0]))]

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def srcs(p):
    """candidate sources for period p: own package(s) first, then every other package that reports it (comparatives), by date."""
    own = [d for d in OWN.get(p, []) if d in REC.get(p, {})]
    rest = sorted(d for d in REC.get(p, {}) if d not in own)
    fy, q = fyq(p)
    if fy == 2026:
        # the FY27 releases recast the FY26 quarters to continuing operations (ex Europe) and ex-SBC adjusted metrics;
        # those comparatives are kept under *_rc (derive_q4) and must not feed the as-reported keys
        own = [d for d in own if d < '2026-07-01']; rest = [d for d in rest if d < '2026-07-01']
    return own + rest

def g(p, sec, key, sources=None, skip=()):
    for d in (sources or srcs(p)):
        if d in skip: continue
        v = REC.get(p, {}).get(d, {}).get(sec, {}).get(key)
        if v is not None: return v
    return None

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def periods():
    out = [str(y) for y in range(2006, 2027)]
    for y in range(2013, 2028):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2027 and q > 2)]
    return out

# ---------------------------------------------------------------- income statement
def close(a, b, tol=0.16): return a is not None and b is not None and abs(a - b) <= tol

def do_is(p):
    fy, q = fyq(p)
    S = srcs(p)
    i = lambda k: g(p, 'is', k, S)
    rev, gp, cogs = i('rev'), i('gp'), i('cogs')
    if rev is None: return False
    # the one-off expense lines come from a single source (the first with an EBIT line): later packages relabel them
    # (FY20 'Asset impairments' became 'Restructuring expenses' in the FY21 package) and mixing sources double counts
    prim = next((d for d in S if REC[p][d].get('is', {}).get('op') is not None), S[0])
    ic = lambda k: REC[p][prim].get('is', {}).get(k)
    if cogs is None and gp is not None: cogs = rev - gp
    if cogs is not None: cogs = abs(cogs)
    if gp is None and cogs is not None: gp = rev - cogs
    put(p, 'rev', rev); put(p, 'cogs', cogs); put(p, 'gp', gp)
    sga, rd = i('sga'), i('rd')
    put(p, 'sga', abs(sga) if sga is not None else None); put(p, 'rd', abs(rd) if rd is not None else None)
    op = i('op')
    put(p, 'op', op)
    # expense lines (charges positive): restructuring, acquisition, impairment, SCI, other operating
    def charge(k):
        v = ic(k)
        if v is None: return None
        return abs(v) if fy <= 2021 else v
    restr, acq, impair, sci, oth = charge('restr'), charge('acq_exp'), charge('impair'), charge('sci'), charge('other_op')
    m = MAN['fy06_08'].get(p, {})       # FY2006-08 old-format statements: the hand-checked one-off lines (20-F) feed the identities
    if 'impair' in m: impair = m['impair']
    if 'sci' in m: sci = m['sci']
    for k, v in (('restr', restr), ('acq_exp', acq), ('impair', impair), ('sci', sci), ('other_op', oth)): put(p, k, N(v) if gp is not None else v)
    debt_ext = abs(ic('debt_ext')) if ic('debt_ext') is not None else 0.0      # loss on early debt extinguishment (below EBIT)
    cum_eff = m.get('cum_eff', ic('cum_eff'))                                   # cumulative effect of accounting change (FY2007, after tax)
    put(p, 'debt_ext', debt_ext if gp is not None else None)
    if cum_eff is not None: put(p, 'cum_eff', cum_eff)
    # asbestos adjustments: charge positive, resolved with GP - opex = EBIT
    asb = ic('asb_adj')
    if asb is None: asb = i('asb_adj')
    if asb is not None and gp is not None and op is not None and sga is not None:
        base = gp - abs(sga) - abs(N(rd)) - N(restr) - N(acq) - N(impair) - N(sci) - N(oth)
        cand = sorted([abs(asb), -abs(asb)], key=lambda a: abs(base - a - op))
        asb_exp = cand[0]
        if abs(base - asb_exp - op) > 0.3: LOG.append(f'{p}: EBIT identity residual {base - asb_exp - op:+.1f} (asbestos sign {asb_exp:+.1f})')
    elif asb is not None:
        asb_exp = -asb if fy <= 2021 else asb
    else: asb_exp = None
    put(p, 'asb_adj', asb_exp)
    # interest / other / EBT / tax / NI
    int_net, int_exp, int_inc, onop, ebt, tax = i('int_net'), i('int_exp'), i('int_inc'), i('other_nonop'), i('ebt'), i('tax')
    if int_net is None and int_exp is not None: int_net = -(abs(int_exp) - abs(N(int_inc))) * (1 if fy <= 2021 else -1)
    ni = i('ni')
    if ni is None: ni = i('ni_cont_a')
    ni_total = i('ni_total')
    if ni_total is None: ni_total = i('ni_total_a') or ni
    disc = i('disc')
    if ebt is not None and op is not None:
        # interest expense positive, other expense positive: op - int - oth = ebt
        best = None
        for si in (1, -1):
            for so in (1, -1):
                ie = si * abs(N(int_net)); oe = so * abs(N(onop))
                r = abs(op - ie - oe - debt_ext - ebt)
                if best is None or r < best[0]: best = (r, ie, oe)
        if best[0] > 0.3: LOG.append(f'{p}: EBT identity residual {best[0]:.1f}')
        put(p, 'int_net', best[1] if int_net is not None else None); put(p, 'onop', best[2] if onop is not None else None)
        if int_net is None and onop is None: put(p, 'int_net', op - debt_ext - ebt); put(p, 'onop', 0.0)
    else:
        put(p, 'int_net', abs(N(int_net)) * (1 if (fy <= 2021 and N(int_net) < 0) or (fy > 2021 and N(int_net) > 0) else -1) if int_net is not None else None)
        put(p, 'onop', onop)
    put(p, 'ebt', ebt)
    if tax is not None and ebt is not None and ni is not None:
        ce = N(cum_eff)
        te = sorted([abs(tax), -abs(tax)], key=lambda t: abs(ebt - t + ce - ni))[0]
        if abs(ebt - te + ce - ni) > 0.3: LOG.append(f'{p}: NI identity residual {ebt - te + ce - ni:+.1f}')
        tax = te
    elif tax is not None:
        tax = -tax if fy <= 2021 else tax
    put(p, 'tax', tax)
    put(p, 'ni', ni_total); put(p, 'ni_cont', ni); put(p, 'disc', disc if disc is not None else (0.0 if ni is not None else None))
    for k in ('eps_b', 'eps_d', 'sh_b', 'sh_d'):
        put(p, k, i(k))
    if x(p, 'sh_d') is None:
        v = g(p, 'seg', 'tot_sh_d_note', S) or g(p, 'seg', 'tot_adj_sh_d', S)
        put(p, 'sh_d', v)
    return True

# ---------------------------------------------------------------- segments
SEGS = ['na', 'dra', 'apac', 'eu', 'int', 'oth', 'rd', 'corp']
def do_seg(p):
    fy, q = fyq(p)
    S = srcs(p)
    # segments as originally reported: later packages restate the comparatives on new segment structures (International Fiber
    # Cement FY17-18, Siding & Trim FY26 ...), so segment keys come from the period's own package(s) whenever those carry any
    own = [d for d in S if d in OWN.get(p, []) and any(k.endswith('_rev') for k in REC[p][d].get('seg', {}))]
    S_all = S
    if own: S = own
    def s(k, skip=(), own_only=False):
        v = g(p, 'seg', k, S, skip)
        if v is None and S is not S_all and not own_only:
            # a later package may fill a missing line (e.g. Q2 FY14 Asia Pacific EBIT) for a segment the own package reports
            sk = k.split('_')[0]
            if any(kk.startswith(sk + '_') for d in S for kk in REC[p][d].get('seg', {})): v = g(p, 'seg', k, S_all, skip)
        return v
    for sk in SEGS:
        # own package's release table, then its FS segment note, then later packages (e.g. Q3 FY16 Asia Pacific: the FS note)
        rev = s(f'{sk}_rev', own_only=True)
        if rev is None: rev = s(f'{sk}_rev_fs', own_only=True)
        if rev is None: rev = s(f'{sk}_rev')
        if rev is None: rev = s(f'{sk}_rev_fs')
        if rev is None and sk == 'na': rev = s('na_rev_mr')
        put(p, f'{sk}_rev', rev)
        ebit = s(f'{sk}_ebit', own_only=True)
        ebit_fs = s(f'{sk}_ebit_fs', own_only=True)
        ebit_ex = s(f'{sk}_ebit_ex', own_only=True)
        if ebit is None and ebit_fs is None and ebit_ex is None:
            ebit, ebit_fs, ebit_ex = s(f'{sk}_ebit'), s(f'{sk}_ebit_fs'), s(f'{sk}_ebit_ex')
        if sk == 'corp':
            # corporate: FS reconciliation value (GAAP, incl. asbestos) preferred from FY2026 (release tables show costs positive)
            if fy >= 2026 and s('corp_ebit_fs') is not None: ebit = s('corp_ebit_fs')
            elif ebit is not None and fy >= 2026: ebit = -abs(ebit)
            elif ebit is None and ebit_ex is not None: ebit = ebit_ex; put(p, 'corp_ebit_is_ex', 1)      # 'General Corporate excluding asbestos' (FY15 format)
            elif ebit is None and ebit_fs is not None and x(p, 'asb_adj') is not None:
                # only the FS segment note (General Corporate incl. asbestos adjustments and, FY24, the greenfield-site impairment):
                # add those lines back so the series stays on the release basis (corporate costs ex asbestos and one-offs); flagged
                ebit = ebit_fs + x(p, 'asb_adj') + N(x(p, 'impair')); put(p, 'corp_ebit_fs_plus_asb', 1)
        if ebit is None: ebit = ebit_fs
        if ebit is None and ebit_ex is not None: ebit = ebit_ex; put(p, f'{sk}_ebit_is_ex', 1)
        put(p, f'{sk}_ebit', ebit)
        if ebit_fs is not None: put(p, f'{sk}_ebit_fs', ebit_fs)
        if ebit_ex is not None: put(p, f'{sk}_ebit_ex', ebit_ex)
        for k in ('adj_ebit', 'adj_ebitda', 'dna', 'azek_amort', 'vol', 'asp', 'rev_lc', 'fc_rev', 'fg_rev', 'sga'):
            v = s(f'{sk}_{k}', own_only=True)
            if v is None: v = s(f'{sk}_{k}')
            if v is not None and sk == 'corp' and k == 'adj_ebitda': v = -abs(v)     # FY26+ release tables (and their comparatives) show corporate costs positive
            if v is not None: put(p, f'{sk}_{k}', v)
        if s(f'{sk}_asp_ccy'): put(p, f'{sk}_asp_ccy', s(f'{sk}_asp_ccy'))
    # FY17-FY18 International Fiber Cement (= Asia Pacific + Europe): the section heading also matches the Asia Pacific pattern
    if x(p, 'int_rev') is not None and x(p, 'apac_rev') == x(p, 'int_rev'):
        for k in list(DATA[p]['x']):
            if k.startswith('apac_'): del DATA[p]['x'][k]
    # media-release Q4 headline values (FY21-FY24) and FY columns of FY24 media release
    for k in ('tot_rev_mr', 'tot_adj_ebit_mr', 'tot_adj_ni_mr', 'na_rev_mr', 'na_adj_ebit_mr', 'na_ebit_mr', 'apac_rev_mr', 'apac_ebit_mr', 'apac_adj_ebit_mr', 'eu_rev_mr', 'eu_ebit_mr', 'eu_adj_ebit_mr', 'apac_rev_lc_mr', 'eu_rev_lc_mr'):
        v = s(k)
        if v is not None: put(p, k, v)
    # group non-GAAP
    for k in ('tot_adj_ebit', 'tot_adj_ni', 'tot_adj_eps', 'tot_adj_ebitda', 'tot_adj_ebitda_ex_asb', 'tot_ebitda', 'tot_dna', 'tot_adj_tax', 'tot_adj_etr', 'tot_adj_ebt',
              'tot_adj_sh_d', 'tot_gross_int', 'tot_cap_int', 'tot_int_inc', 'tot_aicf_int', 'tot_asb_adj_in_ebit', 'tot_aicf_sga_in_ebit', 'tot_sh_d_note',
              'tot_adj_ebitda_hl', 'tot_adj_ni_hl', 'tot_adj_eps_hl', 'tot_adj_ebit_hl', 'tot_ebit_mr'):
        v = s(k)
        if v is not None: put(p, k, v)
    if x(p, 'tot_adj_eps') is not None and abs(x(p, 'tot_adj_eps')) > 5: put(p, 'tot_adj_eps', x(p, 'tot_adj_eps') / 100.0)   # cents not flagged in the label
    # FY21-FY24 Q4 packages: the media release is the only exhibit with the fiscal-year adjusted EBITDA / adjusted EPS (and
    # the headline adjusted EBIT / NI); FY25-26 earnings releases carry the same in the headline table (*_hl)
    for k in ('tot_adj_ebit', 'tot_adj_ni', 'tot_adj_ebitda', 'tot_adj_eps'):
        alt = s(k + '_mr')
        if alt is None: alt = s(k + '_hl')
        if alt is None: continue
        cur = x(p, k)
        if cur is None: put(p, k, alt); put(p, k + '_src', 'mr' if s(k + '_mr') is not None else 'hl')
        elif abs(cur - alt) > 0.06: LOG.append(f'{p}: {k} bridge {cur} vs headline {alt}'); put(p, k, alt); put(p, k + '_src', 'headline')
    for k in ('ni_items', 'ebit_items', 'ebit_items_def', 'ebitda_items', 'adj_ni_label', 'adj_ebit_label'):
        v = g(p, 'ng', k, S)
        if v is None and fy >= 2024: v = g(p, 'ng', k, S_all)      # bridge printed only in a later package's comparative columns (FY25 / Q4 FY25)
        if v is not None: put(p, k, v)
    # AICF SG&A expenses (the claims fund's running costs, inside General Corporate): from whichever bridge lists them
    for k in ('ni_items', 'ebit_items_def', 'ebit_items'):
        for it in (x(p, k) or []):
            if re.search(r'^AICF SG&A', it[0]) and it[1] is not None and x(p, 'aicf_sga') is None: put(p, 'aicf_sga', abs(it[1]))

# ---------------------------------------------------------------- balance sheet (quarter end)
def do_bs(p):
    fy, q = fyq(p)
    S = srcs(p)
    b = lambda k: g(p, 'bs', k, S)
    if b('ta') is None: return
    cash = N(b('cash')); rc = N(b('restr_cash')) + N(b('restr_cash_nc')); rca = N(b('restr_cash_asb')); ria = N(b('restr_inv_asb'))
    ar, inv = N(b('ar')), N(b('inv'))
    tca = b('tca')
    oca = tca - cash - rc - rca - ria - ar - inv - N(b('hfs'))
    put(p, 'bs_cash', cash); put(p, 'bs_restr', rc); put(p, 'bs_restr_asb', rca); put(p, 'bs_inv_asb', ria + N(b('restr_lt_inv_asb')))
    put(p, 'bs_ar', ar); put(p, 'bs_inv', inv); put(p, 'bs_oca', oca); put(p, 'bs_hfs', N(b('hfs'))); put(p, 'bs_tca', tca)
    ta = b('ta'); ppe = N(b('ppe')); rou = N(b('rou')) + N(b('frou')); gw = N(b('gw')); it = N(b('intang'))
    ins = N(b('ins_rec_asb_nc')); dta = N(b('dta')); dta_asb = N(b('dta_asb')); ato = N(b('ato_deposit'))
    onca = ta - tca - ppe - rou - gw - it - ins - dta - dta_asb - ato - N(b('restr_lt_inv_asb'))
    put(p, 'bs_ppe', ppe); put(p, 'bs_rou', rou); put(p, 'bs_gw', gw); put(p, 'bs_int', it); put(p, 'bs_ins_asb', ins)     # non-current; the current part sits in other current assets
    put(p, 'bs_dta', dta); put(p, 'bs_dta_asb', dta_asb); put(p, 'bs_ato', ato); put(p, 'bs_onca', onca); put(p, 'bs_ta', ta)
    ap = N(b('ap')) + N(b('accrued_payroll')); std = N(b('std')) + N(b('std_asb')); asb_c = N(b('asb_liab_c')); tcl = b('tcl')
    ocl = tcl - ap - std - asb_c - N(b('lhfs'))
    put(p, 'bs_ap', ap); put(p, 'bs_std', std); put(p, 'bs_asb_c', asb_c); put(p, 'bs_lhfs', N(b('lhfs'))); put(p, 'bs_ocl', ocl); put(p, 'bs_tcl', tcl)
    ltd = N(b('ltd')); asb_nc = N(b('asb_liab_nc')); dtl = N(b('dtl')); tl = b('tl'); eq = b('equity'); tle = b('tle')
    if tl is None and tle is not None and eq is not None: tl = tle - eq
    onl = tl - tcl - ltd - asb_nc - dtl
    put(p, 'bs_ltd', ltd); put(p, 'bs_asb_nc', asb_nc); put(p, 'bs_dtl', dtl); put(p, 'bs_onl', onl); put(p, 'bs_tl', tl)
    put(p, 'bs_eq', eq); put(p, 'bs_tle', tle); put(p, 'bs_lease', N(b('lease_c')) + N(b('lease_nc')) + N(b('flease_c')) + N(b('flease_nc')))
    put(p, 'bs_asb_total', asb_c + asb_nc); put(p, 'bs_ins_asb_total', ins + N(b('ins_rec_asb_c')))
    sh = b('shares_out')
    if sh is None: sh = xbrl.value('CommonStockSharesOutstanding', fy, 'I', q) or xbrl.value('EntityCommonStockSharesOutstanding', fy, 'I', q)
    if sh: put(p, 'bs_shares', sh)

# ---------------------------------------------------------------- cash flow (year to date -> discrete)
CFK = ['ni', 'dna', 'deferred_tax', 'sbc', 'asb_adj', 'cfo', 'capex', 'ppe_proceeds', 'acq', 'cap_int', 'asb_inv_purch', 'asb_inv_proc', 'cfi',
       'div', 'buyback', 'share_iss', 'cff', 'fx', 'net_change', 'aicf_paid', 'claims_paid', 'fcf_pub', 'lease_exp', 'stepup', 'gain_land', 'restr_nc', 'int_nc', 'impair_nc']
def cf_ytd(fy, q):
    p = ytdk(fy, q)
    S = srcs(p) if p in REC else []
    if q == 4: S = srcs(str(fy))
    c = {k: g(p, 'cf', k, S) for k in CFK}
    if c['cfo'] is None: return None
    o = {k: N(c[k]) for k in CFK}
    o['cash_begin'], o['cash_end'] = g(p, 'cf', 'cash_begin', S), g(p, 'cf', 'cash_end', S)
    o['cash_basis'] = g(p, 'cf', 'cash_basis', S)
    if q == 4:
        for k, cs in (('dna', ['DepreciationDepletionAndAmortization']), ('sbc', ['ShareBasedCompensation']), ('deferred_tax', ['DeferredIncomeTaxExpenseBenefit'])):
            if not o[k]:
                v = xbrl.first_of(cs, fy, 'FY')
                if v is not None: o[k] = v
    return o

def cf_lines(c):
    o = {}
    o['cf_ni'] = c['ni']; o['cf_dna'] = c['dna']; o['cf_def'] = c['deferred_tax']; o['cf_sbc'] = c['sbc']; o['cf_asb'] = c['asb_adj']
    o['cf_cfo'] = c['cfo']
    o['cf_capex'] = c['capex']; o['cf_ppesale'] = c['ppe_proceeds']; o['cf_acq'] = c['acq']; o['cf_asb_inv'] = c['asb_inv_purch'] + c['asb_inv_proc']
    o['cf_cfi'] = c['cfi']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['ppe_proceeds'] - c['acq'] - o['cf_asb_inv'] - c['cap_int']
    o['cf_capint'] = c['cap_int']
    o['cf_div'] = c['div']; o['cf_bb'] = c['buyback']; o['cf_eq'] = c['share_iss']; o['cf_cff'] = c['cff']
    o['cf_ofin'] = c['cff'] - c['div'] - c['buyback'] - c['share_iss']
    o['cf_fx'] = c['fx']; o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    o['cf_aicf'] = c['aicf_paid']                          # supplemental: cash paid to AICF (the AFFA contribution)
    o['cf_claims'] = c['claims_paid']                      # claims and handling costs paid - asbestos (inside operating cash flow)
    o['fcf_pub'] = c['fcf_pub'] if c['fcf_pub'] else None
    o['cf_oth'] = c['cfo'] - c['ni'] - c['dna'] - c['deferred_tax'] - c['sbc'] - c['asb_adj']     # other non-cash + working capital (split below)
    return o

def do_cf():
    for y in range(2006, 2027):
        a = cf_ytd(y, 4)
        if not a: LOG.append(f'{y}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', a['cash_begin']); put(str(y), 'cf_end', a['cash_end']); put(str(y), 'cf_basis', a['cash_basis'])
    for y in range(2013, 2028):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2027 and q > 2: break
            p = qk(y, q)
            cur = cf_ytd(y, q)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['cash_begin']
            else:
                if prev is None: continue
                d = {k: (N(lc[k]) - N(prev[0][k])) if (k != 'fcf_pub' or (lc[k] is not None and prev[0][k] is not None)) else lc[k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['cash_end']); put(p, 'cf_basis', cur['cash_basis'])
            prev = (lc, cur['cash_end'])

# ---------------------------------------------------------------- derived Q4 (FY - 9M) and FY2027 continuing-ops comparatives
IS_KEYS = ['rev', 'cogs', 'gp', 'sga', 'rd', 'restr', 'acq_exp', 'impair', 'sci', 'other_op', 'asb_adj', 'op', 'int_net', 'onop', 'debt_ext', 'ebt', 'tax', 'ni', 'ni_cont', 'disc']
SEG_KEYS = [f'{s}_{k}' for s in SEGS for k in ('rev', 'ebit', 'adj_ebit', 'adj_ebitda', 'dna', 'azek_amort', 'vol', 'rev_lc', 'fc_rev', 'fg_rev')] + \
           ['tot_adj_ebit', 'tot_adj_ni', 'tot_adj_ebitda', 'tot_dna', 'tot_adj_tax', 'tot_adj_ebt', 'aicf_sga']
def derive_q4():
    for y in range(2013, 2027):
        p4 = qk(y, 4); fy = str(y)
        xs = [x(qk(y, q), 'rev') for q in (1, 2, 3)]
        if x(p4, 'rev') is None and x(fy, 'rev') is not None and all(v is not None for v in xs):
            itk = sorted({k for q in (1, 2, 3, 4) for k in DATA.get(qk(y, q) if q < 4 else fy, {}).get('x', {}) if re.match(r'^(ni|eb|ed)_it_', k) and not k.endswith('_labels')})
            for k in IS_KEYS + SEG_KEYS + itk:
                a = x(fy, k); qs = [x(qk(y, q), k) for q in (1, 2, 3)]
                if a is not None and all(v is not None for v in qs) and not k.endswith('_vol') or (k.endswith('_vol') and a is not None and all(v is not None for v in qs)):
                    put(p4, k, a - sum(qs))
            put(p4, 'q4_derived', 1); put(p4, 'sh_d', 4 * N(x(fy, 'sh_d')) - sum(N(x(qk(y, q), 'sh_d')) for q in (1, 2, 3)) if x(fy, 'sh_d') else None)
            put(p4, 'sh_b', 4 * N(x(fy, 'sh_b')) - sum(N(x(qk(y, q), 'sh_b')) for q in (1, 2, 3)) if x(fy, 'sh_b') else None)
            if x(p4, 'ni') is not None and x(p4, 'sh_d'):
                put(p4, 'eps_d', round(x(p4, 'ni') / x(p4, 'sh_d'), 4)); put(p4, 'eps_derived', 1)
            if x(p4, 'ni') is not None and x(p4, 'sh_b'): put(p4, 'eps_b', round(x(p4, 'ni') / x(p4, 'sh_b'), 4))
            LOG.append(f'{p4}: derived as FY - 9M')
        # Q4 adjusted EPS = FY - 9M where the FY and 9M adjusted EPS are published (company computes quarters separately; flagged)
        if x(p4, 'tot_adj_eps') is None and x(fy, 'tot_adj_eps') is not None and all(x(qk(y, q), 'tot_adj_eps') is not None for q in (1, 2, 3)):
            put(p4, 'tot_adj_eps', x(fy, 'tot_adj_eps') - sum(x(qk(y, q), 'tot_adj_eps') for q in (1, 2, 3))); put(p4, 'adj_eps_derived', 1)
    # FY2026 continuing-operations comparatives (ex Europe) from the FY27 releases: Q1-26, Q2-26 and 6M (recast) -> *_rc
    for y, q in ((2026, 1), (2026, 2)):
        p = qk(y, q)
        src = {1: '2026-08-06', 2: '2026-11-05'}[q]
        d = REC.get(p, {}).get(src, {})
        for k in ('rev', 'cogs', 'gp', 'sga', 'rd', 'restr', 'acq_exp', 'asb_adj', 'op', 'int_net', 'other_nonop', 'ebt', 'tax', 'ni', 'disc', 'ni_total', 'eps_d', 'sh_d'):
            v = d.get('is', {}).get(k)
            if v is not None: put(p, k + '_rc', v)
        for sk in ('na', 'dra', 'apac'):
            for k in ('rev', 'ebit', 'adj_ebitda', 'dna'):
                v = d.get('seg', {}).get(f'{sk}_{k}')
                if v is not None: put(p, f'{sk}_{k}_rc', v)
        for k in ('tot_adj_ebitda', 'tot_adj_ni', 'tot_adj_eps', 'tot_dna', 'corp_adj_ebitda', 'corp_ebit'):
            v = d.get('seg', {}).get(k)
            if v is not None: put(p, k + '_rc', v)
        if x(p, 'rev_rc') is not None: put(p, 'recast', 1)

# ---------------------------------------------------------------- bridge items -> category keys (pre-tax unless the category is 'tax')
CATS = [('asb', r'^Asbestos (adjustments?|provision|related)'), ('aicf_sga', r'^AICF SG&A'), ('aicf_int', r'^AICF interest'),
        ('restr', r'^Restructuring'), ('acq', r'^(Acquisition|Fermacell acquisition|Merger)'), ('stepup', r'Inventory fair value|step.?up'),
        ('preclose', r'^Pre-close financing'), ('fxgain', r'foreign currency forward'), ('amort', r'^Amortization of intangible assets resulting from AZEK'),
        ('sbc', r'^Share-based compensation'), ('impair', r'[Ii]mpairment|Product line discontinuation|Asset impairments?'),
        ('debtext', r'debt extinguishment'), ('nz', r'^New Zealand'), ('asic', r'^ASIC'), ('stamp', r'stamp duty'),
        ('tax', r'^Tax|[Tt]ax (adjustments?|benefit|impact|effect)|^Asbestos and other tax|^Income tax')]
def cat_of(label):
    for c, pat in CATS:
        if re.search(pat, label): return c
    return 'other'
def items_to_keys(p, src_key, prefix):
    items = x(p, src_key)
    if not items: return
    tot = {}
    for lab, cur, *_ in items:
        if cur is None: continue
        c = cat_of(lab)
        tot[c] = tot.get(c, 0.0) + cur
    for c, v in tot.items(): put(p, f'{prefix}_{c}', round(v, 6))
    put(p, f'{prefix}_labels', '; '.join(f'{lab}: {cur}' for lab, cur, *_ in items if cur is not None))

def manual_fy06_08():
    for y in ('2006', '2007', '2008'):
        m = MAN['fy06_08'][y]
        for k, v in m.items():
            if k.startswith('_'): continue
            key = {'adj_ebit_pub': 'tot_adj_ebit', 'adj_ni_pub': 'tot_adj_ni', 'dna': 'tot_dna', 'aicf_sga': 'aicf_sga'}.get(k, k)
            # the hand-checked 20-F values win over the old-format package parse (logged when they differ)
            if x(y, key) is not None and isinstance(v, (int, float)) and abs(x(y, key) - v) > 0.06:
                LOG.append(f'{y}: manual {key} {v} replaces parsed {x(y, key)}')
            put(y, key, v)
        if x(y, 'tot_adj_ni') and x(y, 'sh_d'): put(y, 'tot_adj_eps', round(x(y, 'tot_adj_ni') / x(y, 'sh_d'), 4))
        put(y, 'int_net', x(y, 'int_exp') - x(y, 'int_inc'))
        put(y, 'manual_src', MAN['fy06_08']['_src'][y])

DPS = {'2006': 0.10, '2007': 0.09, '2008': 0.27, '2009': 0.08, '2010': 0.0, '2011': 0.0, '2012': 0.04, '2013': 0.37, '2014': 0.88, '2015': 0.57, '2016': 0.38,
       '2017': 0.38, '2018': 0.40, '2019': 0.36, '2020': 0.10, '2021': 0.70, '2022': 0.70, '2023': 0.0, '2024': 0.0, '2025': 0.0, '2026': 0.0}
DPS_NOTE = ('US$ per share. FY2006-FY2012: dividends paid per share (20-F Item 3 selected financial data, FY2008 and FY2010 reports). FY2013 onward: dividends '
            'declared in respect of the fiscal year per the results-package dividend tables (FY13: 0.13 final + 0.24 special; FY14: 0.08 + 0.32 + 0.20 special + 0.28 '
            '125-year special; FY15: 0.08 + 0.27 + 0.22 special; FY16: 0.09 + 0.29; FY17: 0.10 + 0.28; FY18: 0.10 + 0.30; FY19: 0.10 + 0.26; FY20: 0.10 interim, '
            'final cancelled (COVID-19); FY21: 0.70 final (May-2021); FY22: 0.40 interim + 0.30 final; none since (buybacks FY23-FY25; AZEK deleveraging FY26-27).')

def run():
    load(); index_sources()
    for p in periods():
        if p not in REC: LOG.append(f'{p}: no record'); continue
        do_is(p); do_seg(p); do_bs(p)
        put(p, 'basis', 'own package' if OWN.get(p) and OWN[p][0] in REC[p] else 'comparative')
    do_cf()
    manual_fy06_08()
    for p in periods():
        if p in DATA:
            items_to_keys(p, 'ni_items', 'ni_it'); items_to_keys(p, 'ebit_items_def', 'eb_it'); items_to_keys(p, 'ebitda_items', 'ed_it')
    derive_q4()
    recast_q1_27()
    model_keys()
    for y, v in DPS.items(): put(y, 'dps', v)
    return DATA

# ---------------------------------------------------------------- Q1 FY27 recast to continuing operations (Europe discontinued from the Q2 FY27 release)
RC_IS = ['rev', 'cogs', 'gp', 'sga', 'rd', 'restr', 'acq_exp', 'asb_adj', 'op', 'int_net', 'other_nonop', 'ebt', 'tax', 'ni', 'disc', 'ni_total']
RC_SEG = ['na_rev', 'dra_rev', 'apac_rev', 'na_ebit', 'dra_ebit', 'apac_ebit', 'na_adj_ebitda', 'dra_adj_ebitda', 'apac_adj_ebitda', 'na_dna', 'dra_dna', 'apac_dna',
          'na_azek_amort', 'dra_azek_amort', 'corp_ebit', 'corp_adj_ebitda', 'tot_adj_ebitda', 'tot_adj_ni', 'tot_adj_ebitda_hl', 'tot_adj_ni_hl', 'tot_dna']
def recast_q1_27():
    """Q1 FY27 was reported with Europe as a segment (10-Q / release of 6-Aug-2026); the Q2 FY27 release (5-Nov-2026) recast it to
    continuing operations and to the ex-SBC adjusted definitions. Q1 = six months (Q2 FY27 release) - Q2, so FY2027 = Q1 + Q2 + Q3E + Q4E
    is on one basis (the FY27 planning-assumption basis). The originally reported Q1 values are kept under *_orig."""
    p, h, q2, src = 'Q1-27', 'H1-27', 'Q2-27', '2026-11-05'
    hr, qr = REC.get(h, {}).get(src, {}), REC.get(q2, {}).get(src, {})
    if not hr or not qr: LOG.append('Q1-27: no H1-27 record for the continuing-operations recast'); return
    rename = {'other_nonop': 'onop', 'ni': 'ni_cont', 'ni_total': 'ni'}
    n = 0
    for k in RC_IS:
        hv, qv = hr.get('is', {}).get(k), qr.get('is', {}).get(k)
        if hv is None or qv is None: continue
        mk = rename.get(k, k)
        if x(p, mk) is not None: put(p, mk + '_orig', x(p, mk))
        put(p, mk, round(hv - qv, 6)); n += 1
    for k in RC_SEG:
        hv, qv = hr.get('seg', {}).get(k), qr.get('seg', {}).get(k)
        if hv is None or qv is None: continue
        if k == 'corp_adj_ebitda': hv, qv = -abs(hv), -abs(qv)
        if x(p, k) is not None: put(p, k + '_orig', x(p, k))
        put(p, k, round(hv - qv, 6)); n += 1
    if x(p, 'ni_cont') is not None and x(p, 'sh_d'):
        put(p, 'eps_d_orig', x(p, 'eps_d')); put(p, 'eps_d', round(x(p, 'ni') / x(p, 'sh_d'), 4)); put(p, 'eps_derived', 1)
    if x(p, 'tot_adj_ni') is not None and x(p, 'sh_d'):
        put(p, 'tot_adj_eps_orig', x(p, 'tot_adj_eps')); put(p, 'tot_adj_eps', round(x(p, 'tot_adj_ni') / x(p, 'sh_d'), 4))
    # bridge items: six months - Q2
    hi, qi = hr.get('ng', {}).get('ni_items'), qr.get('ng', {}).get('ni_items')
    if hi and qi:
        q = {lab: cur for lab, cur, *_ in qi}
        items = [[lab, round(ytd - N(q.get(lab)), 6), None, None, None] for lab, cur, prior, ytd, ytdp in hi if ytd is not None]
        put(p, 'ni_items', items)
        for k in list(DATA[p]['x']):
            if k.startswith('ni_it_'): del DATA[p]['x'][k]
        items_to_keys(p, 'ni_items', 'ni_it')
    for k in [k for k in DATA[p]['x'] if k.startswith('eu_')]: del DATA[p]['x'][k]     # Europe = discontinued operations (memo in the divestiture block)
    put(p, 'recast_cont', 1)
    LOG.append(f'Q1-27: recast to continuing operations from the Q2 FY27 release six-month columns ({n} keys)')

def model_keys():
    """convenience keys for the workbook rows."""
    for p in periods():
        if p not in DATA: continue
        fy, q = fyq(p)
        # D&A for the bridges: continuing operations from FY27 (the cash-flow statement D&A includes Europe, discontinued)
        put(p, 'dna_model', x(p, 'tot_dna') if (fy >= 2027 and x(p, 'tot_dna') is not None) else x(p, 'cf_dna'))
        # AICF SG&A from FY2024 is inside the bridge line 'asbestos related expenses and adjustments' = asbestos adjustments + AICF SG&A
        if fy >= 2024 and x(p, 'aicf_sga') is None:
            if x(p, 'ni_it_asb') is not None and x(p, 'asb_adj') is not None:
                put(p, 'aicf_sga', round(x(p, 'ni_it_asb') - x(p, 'asb_adj'), 6)); put(p, 'aicf_derived', 'bridge asbestos-related line - statement asbestos adjustments')
            elif x(p, 'tot_adj_ebit') is not None and x(p, 'op') is not None and x(p, 'asb_adj') is not None:
                put(p, 'aicf_sga', round(x(p, 'tot_adj_ebit') - x(p, 'op') - x(p, 'asb_adj') - N(x(p, 'impair')) - N(x(p, 'restr')) - N(x(p, 'acq_exp')), 6))
                put(p, 'aicf_derived', 'published Adjusted EBIT - EBIT - asbestos adjustments - impairments / restructuring / merger costs')
        v = x(p, 'tot_adj_ebitda')
        if v is not None:
            if fy >= 2023: put(p, 'adj_ebitda_pub', v)          # company Adjusted EBITDA (current definition; FY23 as restated in the FY24 release)
            if fy <= 2020: put(p, 'ebitda_old_pub', v)          # FY10-20 'Adjusted EBITDA' = EBIT + D&A (asbestos included)
        if x(p, 'tot_adj_ebitda_ex_asb') is not None: put(p, 'ebitda_ex_asb_pub', x(p, 'tot_adj_ebitda_ex_asb'))
        eb = [k for k in DATA[p]['x'] if k.startswith('eb_it_') and not k.endswith('_labels') and k not in ('eb_it_asb', 'eb_it_aicf_sga')]
        if x(p, 'eb_it_labels') is not None: put(p, 'eb_items_x', round(sum(x(p, k) for k in eb), 6))
        ot = [k for k in ('ni_it_impair', 'ni_it_nz', 'ni_it_asic', 'ni_it_stamp', 'ni_it_debtext', 'ni_it_other') if x(p, k) is not None]
        if ot: put(p, 'ni_other_x', round(sum(x(p, k) for k in ot), 6))
        if x(p, 'cf_cfo') is not None: put(p, 'cf_wc', round(N(x(p, 'cf_oth')) - N(x(p, 'cf_claims')), 6))
        if x(p, 'bs_ta') is not None: put(p, 'bs_aicf_cash', round(N(x(p, 'bs_restr_asb')) + N(x(p, 'bs_inv_asb')), 6))
        if x(p, 'cf_basis') is not None: put(p, 'cf_restr_flag', 1 if 'restricted' in x(p, 'cf_basis') else 0)
        if x(p, 'cf_claims') is not None: put(p, 'as_claims', round(-x(p, 'cf_claims'), 6))
        if x(p, 'tot_adj_etr') is not None: put(p, 'tot_adj_etr_f', round(x(p, 'tot_adj_etr') / 100.0, 6))
        if x(p, 'bs_ta') is not None and x(p, 'bs_tca') is not None: put(p, 'bs_oca_x', round(N(x(p, 'bs_oca')), 6))

def save():
    """data/_normalized.json: the flat model inputs (what build.py reads), so the build needs no raw downloads."""
    out = {p: DATA[p]['x'] for p in periods() if p in DATA}
    json.dump(out, open(os.path.join(BASE, 'data', '_normalized.json'), 'w'), indent=0, sort_keys=True)
    xbrl.dump_subset()
    return out

if __name__ == '__main__':
    run(); save()
    for p in periods():
        v = DATA.get(p, {}).get('x', {})
        print(p, v.get('basis'), {k: (round(v[k], 2) if isinstance(v.get(k), float) else v.get(k)) for k in ('rev', 'op', 'asb_adj', 'int_net', 'onop', 'tax', 'ni', 'eps_d', 'sh_d', 'na_rev', 'na_ebit', 'tot_adj_ebit', 'tot_adj_ni', 'cf_cfo', 'bs_ta', 'q4_derived')})
    print('\n'.join(LOG))
