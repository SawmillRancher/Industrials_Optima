"""Harmonise the extracted S&P Global data (data/<period>.json, release transcriptions) and XBRL company facts into flat model keys:
DATA[period]['x'][key] (USD m).

Basis (hybrid recast, see README):
  - FY2010-11: continuing operations as recast for the McGraw-Hill Education / Broadcasting sales (FY2012 10-K; Q4-2012 release
    comparative). FY2012 - FY2024 and Q1/13 - Q4/24: as originally reported in each period's own release (Mobility, Engineering
    Solutions and the other divested businesses included while owned).
  - FY2025, Q1/25 - Q4/25 and Q1/26 - Q2/26: pro forma continuing operations excluding Mobility (Article 11; 8-K/A 6-Jul-2026 and
    the Q2-2026 release), with division revenue / adjusted OP on the July-2026 recast basis. The difference to reported net income
    attributable is shown as discontinued operations; balance sheet and cash flow stay as reported (incl. Mobility to 30-Jun-2026).
Segments map to the current divisions by lineage: S&P Capital IQ -> Market Intelligence; Commodities & Commercial -> Energy
(Commodity Insights / Platts); the combined Market & Commodities Intelligence segment (Q4/16 - 2017) is a legacy row, with its
revenue split from the company's organic-revenue table where printed.
Balance sheet and cash flow: XBRL company facts (earliest-filed value = as originally reported), Q2-2026 from the 10-Q; cash flow
quarters derived from year to date (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
"""
import json, glob, os
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
RECAST = MAN['recast_2025_26']['periods']

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2010, 2026)]
    for y in range(2013, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q >= 3)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

SEGROW = {'RAT': 'RAT', 'IDX': 'IDX', 'CI': 'CI', 'CC': 'CI', 'MI': 'MI', 'CIQ': 'MI', 'MCI': 'LEG', 'MOB': 'MOB', 'ES': 'ES', 'OTH': 'LEG'}
TYPES = {
    'RAT': {'TR': ('transaction', 'non-subscription / transaction'), 'NT': ('non-transaction', 'subscription / non-transaction')},
    'IDX': {'ALF': ('asset linked fees', 'asset-linked fees'), 'ETD': ('sales usage-based royalties', 'non-subscription / transaction', 'non-subscription'),
            'SUB': ('subscription', 'subscription / non-transaction')},
    'CI': {'SUB': ('subscription', 'subscription / non-transaction', 'commodities markets - subscription', 'commercial markets - subscription'),
           'NS': ('non-subscription', 'non-subscription / transaction', 'commodities markets - non-subscription', 'commercial markets - non-subscription'),
           'ROY': ('sales usage-based royalties',)},
    'MI': {'SUB': ('subscription', 'subscription / non-transaction'), 'NS': ('non-subscription', 'non-subscription / transaction'), 'RV': ('recurring variable',)}}
CATS = ['SEVER', 'ACQ', 'DISP', 'GAIN', 'LEGAL', 'IMPAIR', 'OTHER']
# FY2013-2015 adjusted measures did not add back deal-related amortization (added from the 2016 releases; 2015 restated in Q4-15)
NO_AMORT = lambda fy: fy <= 2015

def do_types(p, r):
    rt = r.get('rev_type') or {}
    seen = set()
    for code, d in rt.items():
        row = SEGROW.get(code)
        if row not in TYPES: continue
        for line, labs in TYPES[row].items():
            v = sum(val for lab, val in d.items() if isinstance(val, (int, float)) and lab.strip().lower() in labs)
            if any(lab.strip().lower() in labs for lab in d):
                put(p, f't_{row}_{line}', N(x_(p, f't_{row}_{line}')) + v); seen.add(row)
    return seen

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i, n, so = r.get('is', {}), r.get('ngaap', {}), r.get('seg_other', {})
    put(p, 'rev', i.get('rev')); put(p, 'exp', i.get('exp'))
    for k, kk in (('op_rel', 'op_rel'), ('sga', 'sga'), ('dep', 'dep'), ('amort', 'amort')): put(p, kk, i.get(k))
    put(p, 'gain', N(i.get('gain_disp'))); put(p, 'eq_inc', N(i.get('eq_inc')))
    put(p, 'op', i.get('op'))
    oth = N(i.get('oth_inc'))
    for lab, v in i.get('other_lines', []):           # (gain) loss on extinguishment of debt (2019-22) shown below interest: folded into other (expense)
        if 'extinguishment' in lab.lower() and isinstance(v, (int, float)) and v and i.get('ebt') is not None:
            oth = i['ebt'] - i['op'] + N(i.get('int'))     # derived so that OP + other - interest = EBT (sign conventions differ between releases)
            LOG.append(f'{p}: {lab} ({v}) folded into other income (expense): {oth:+g}')
    put(p, 'oth_inc', oth); put(p, 'int', N(i.get('int'))); put(p, 'ebt', i.get('ebt')); put(p, 'tax', i.get('tax'))
    put(p, 'nci', N(i.get('nci_cont', i.get('nci'))) if i.get('nci_cont') is not None else N(i.get('nci')))
    ni_attr = i.get('ni_attr'); put(p, 'ni_attr', ni_attr)
    ni_cont = i.get('ni_cont', i.get('ni'))
    if i.get('ebt') is not None and i.get('tax') is not None: ni_cont = i['ebt'] - i['tax']
    nic_attr = ni_cont - N(x_(p, 'nci')) if ni_cont is not None else None
    put(p, 'disc', (ni_attr - nic_attr) if (ni_attr is not None and nic_attr is not None) else 0.0)
    put(p, 'eps_d', i.get('eps_d')); put(p, 'sh_b', i.get('sh_b')); put(p, 'sh_d', i.get('sh_d')); put(p, 'sh_end', i.get('sh_end'))
    # segments
    adj_op_m = None
    rev, sop, aop = {}, {}, {}
    calc = n.get('adj_op') is None and n.get('items_total_pre') is not None    # adjusted measures published only pro forma (Q1-22): actual-scope rebuild
    for s in r.get('seg', []):
        row = SEGROW.get(s['code'], 'LEG')
        rev[row] = N(rev.get(row)) + N(s.get('rev'))
        if s.get('op') is not None: sop[row] = N(sop.get(row)) + s['op']
        a = s.get('adj_op')
        if a is None and calc and s.get('op') is not None: a = s['op'] + N(s.get('nongaap')) + N(s.get('deal_amort'))
        if a is not None: aop[row] = N(aop.get(row)) + a
    if so.get('corp_rev'): rev['LEG'] = N(rev.get('LEG')) + so['corp_rev']   # Kensho revenue in Corporate (2018)
    split = r.get('mci_split')
    if split and 'LEG' in rev:
        rev['MI'] = split['MI_rev']; rev['CI'] = split['CI_rev']; rev['LEG'] -= split['MI_rev'] + split['CI_rev']
        LOG.append(f'{p}: MCI revenue split MI {split["MI_rev"]} / Platts {split["CI_rev"]} (organic-revenue exhibit)')
    for row, v in rev.items(): put(p, f'sr_{row}', v)
    for row, v in sop.items(): put(p, f'se_{row}', v)
    for row, v in aop.items(): put(p, f'sa_{row}', v)
    put(p, 'elim', so.get('elim'))
    put(p, 'corp', so.get('corp'))
    if so.get('adj_corp') is None and calc and so.get('corp') is not None:
        so = dict(so, adj_corp=so['corp'] - N(so.get('corp_nongaap')) - N(so.get('corp_deal_amort')), adj_eq_inc=N(so.get('eq_inc')) + N(so.get('eq_deal_amort')))
    if so.get('adj_corp') is None and n.get('adj_op') is not None and aop:     # no corporate adjustments printed (Q1-17, Q1-18): derived
        so = dict(so, adj_corp=sum(aop.values()) + N(so.get('adj_eq_inc', so.get('eq_inc'))) - n['adj_op'])
        LOG.append(f'{p}: adjusted corporate derived {so["adj_corp"]:g} (Σ adjusted divisions − published adjusted OP)')
    if so.get('adj_corp') is not None: put(p, 'adj_corp', so['adj_corp'])
    eqa = so.get('adj_eq_inc', so.get('eq_inc'))
    put(p, 'adj_eq', N(eqa) if eqa is not None else N(i.get('eq_inc')))
    do_types(p, r)
    # non-GAAP
    adj_op = n.get('adj_op')
    if calc and i.get('op') is not None:
        adj_op_m = i['op'] + n['items_total_pre'] + N(n.get('deal_amort_pre'))
        put(p, 'adj_ni_mod', n.get('start_ni', ni_attr) + N(n.get('items_total_net')) + N(n.get('deal_amort_net')))
        LOG.append(f'{p}: adjusted measures published only pro forma; actual-scope rebuild adj OP {adj_op_m:.0f}, adj NI {x_(p, "adj_ni_mod"):.0f}')
    tot = {c: 0.0 for c in CATS}; lab = {c: [] for c in CATS}; nonop = 0.0; nonop_lab = []
    for it in n.get('items', []):
        c = it.get('cat'); pre = it.get('pre')
        if not isinstance(pre, (int, float)): continue
        if c in ('NONOP',): nonop += pre; nonop_lab.append(f"{it['label']} {pre:+g}"); continue
        if c in ('TAX',): continue
        if c == 'EQ': c = 'OTHER'
        c = c if c in tot else 'OTHER'
        tot[c] += pre; lab[c].append(f"{it.get('seg', '')}: {it['label']} {pre:+g}")
    amort_op = n.get('deal_amort_pre_op', n.get('deal_amort_pre'))
    if n.get('deal_amort_pre_oth'): nonop += n['deal_amort_pre_oth']; nonop_lab.append(f"Deal-related amortization in other income {n['deal_amort_pre_oth']:+g}")
    if NO_AMORT(fy): amort_op = 0.0
    ref = adj_op if adj_op is not None else (adj_op_m if calc and i.get('op') is not None else None)
    if ref is not None and i.get('op') is not None:
        # tie the op items to the published adjusted OP: residual vs the itemised footnotes goes to OTHER (company rounding)
        res = ref - i['op'] - N(amort_op) - sum(tot.values())
        if abs(res) > 0.01:
            tot['OTHER'] += res; lab['OTHER'].append(f'Rounding / unitemised vs published adjusted OP {res:+g}')
            if abs(res) > 1.01: LOG.append(f'{p}: op items residual {res:+.0f} put in OTHER')
    for c in CATS:
        put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(lab[c]))
    put(p, 'deal_amort', N(amort_op) if ref is not None else None)
    put(p, 'nonop', nonop); put(p, 'nonop_lab', '; '.join(nonop_lab))
    put(p, 'adj_op_pub', adj_op)
    put(p, 'adj_ni_pub', n.get('adj_ni')); put(p, 'e_pub', n.get('adj_eps'))
    put(p, 'start_ni', n.get('start_ni', ni_attr))
    if n.get('adj_sh_d'): put(p, 'adj_sh_d', n['adj_sh_d'])
    # company residual between published adjusted OP and its components
    if ref is not None and aop:
        comp = sum(aop.values()) - N(so.get('adj_corp')) + N(x_(p, 'adj_eq'))
        if so.get('adj_corp') is not None: put(p, 'g_res', ref - comp)
    put(p, 'dps', None)

TENK_2012 = {'2011': {'op_rel': 1392, 'sga': 1387, 'dep': 78, 'amort': 33}, '2012': {'op_rel': 1460, 'sga': 1709, 'dep': 74, 'amort': 48}}   # FY2012 10-K (continuing ops)
OPEX = {'op_rel': 'CostOfRevenue', 'sga': 'SellingGeneralAndAdministrativeExpense', 'dep': 'Depreciation', 'amort': 'AmortizationOfIntangibleAssets'}
def do_opex(p):
    """expense lines not shown in the condensed release income statement: XBRL (as first filed); Q4 = FY - 9M."""
    fy, q = fyq(p)
    if p in TENK_2012:
        for k, v in TENK_2012[p].items():
            if x_(p, k) is None: put(p, k, v)
        return
    if fy < 2013: return
    for k, c in OPEX.items():
        if x_(p, k) is not None: continue
        if p.isdigit(): v = xv(c, fy, 'FY')
        elif q < 4: v = xv(c, fy, 'Q', q)
        else:
            a, b = xv(c, fy, 'FY'), xv(c, fy, 'YTD', 3)
            v = a - b if a is not None and b is not None else None
        if v is not None: put(p, k, v); put(p, k + '_x', 1)

def do_recast():
    """2025 and 1H-2026: pro forma continuing operations excluding Mobility (manual_items.recast_2025_26)."""
    for p, m in RECAST.items():
        if p in ('2023', '2024'):
            put(p, 'pf_rev', m['is']['rev']); put(p, 'pf_op', m['is']['op']); put(p, 'pf_ni', m['is']['ni_attr_cont']); continue
        r = REC.get(p, {}); i = m['is']
        orig = dict(DATA.get(p, {}).get('x', {}))
        for k in ('rev', 'op_rel', 'sga', 'dep', 'amort', 'exp', 'op', 'int', 'ebt', 'tax', 'nci', 'sh_b', 'sh_d'): put(p, k, i[k])
        put(p, 'gain', i['gain_disp']); put(p, 'eq_inc', i['eq_inc']); put(p, 'oth_inc', i['oth_inc'])
        put(p, 'disc', orig['ni_attr'] - i['ni_attr_cont']); put(p, 'start_ni', i['ni_attr_cont'])
        put(p, 'pf_rev', i['rev']); put(p, 'pf_op', i['op']); put(p, 'pf_ni', i['ni_attr_cont'])
        s = m['seg']
        for row in ('RAT', 'IDX', 'CI', 'MI'):
            put(p, f'sr_{row}', s[row][0]); put(p, f'sa_{row}', s[row][1])
            DATA[p]['x'].pop(f'se_{row}', None)
        for row in ('MOB', 'ES', 'LEG'):
            for pre in ('sr_', 'se_', 'sa_'): DATA[p]['x'].pop(pre + row, None)
        put(p, 'elim', s['elim']); put(p, 'adj_eq', s['adj_eq'])
        ng = m['ngaap']
        adj_corp = sum(s[row][1] for row in ('RAT', 'IDX', 'CI', 'MI')) + s['adj_eq'] - ng['adj_op']
        put(p, 'adj_corp', adj_corp)
        if abs(adj_corp - s['adj_corp']) > 0.5:
            LOG.append(f'{p}: pro forma adjusted corporate derived {adj_corp:.0f} vs recast table {s["adj_corp"]} (company rounding)')
        put(p, 'g_res', 0.0)
        put(p, 'e_pub_orig', orig.get('e_pub'))
        put(p, 'adj_op_pub', ng['adj_op']); put(p, 'adj_ni_pub', ng['adj_ni']); put(p, 'e_pub', ng['adj_eps'])
        put(p, 'deal_amort', ng['amort']); put(p, 'nonop', ng['premium']); put(p, 'nonop_lab', 'Premium amortization benefit (interest)')
        # op items: total from the pro forma reconciliation; category detail from the original release where the totals agree
        # categories: the period's own release items excluding the Mobility division; the residual (pro forma TSA adjustment, Mobility
        # costs reallocated, rounding) goes to OTHER
        tot = {c: 0.0 for c in CATS}; lab = {c: [] for c in CATS}
        for it in (r.get('ngaap') or {}).get('items', []) + ((r.get('pro_forma') or {}).get('ngaap') or {}).get('items', []) * 0:
            c = it.get('cat'); pre = it.get('pre')
            if it.get('seg') == 'MOB' or c in ('NONOP', 'TAX') or not isinstance(pre, (int, float)): continue
            c = c if c in tot else 'OTHER'
            tot[c] += pre; lab[c].append(f"{it.get('seg', '')}: {it['label']} {pre:+g}")
        res = ng['items_op'] - sum(tot.values())
        if abs(res) > 0.01: tot['OTHER'] += res; lab['OTHER'].append(f'Pro forma adjustment (Transition Services Agreement, reallocated costs) / rounding {res:+g}')
        for c in CATS: put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(lab[c]))
        # revenue types: Energy / MI recast types (8-K/A tables; Q2 release Exhibit 7)
        for row, d in (m.get('types') or {}).items():
            for line, v in d.items(): put(p, f't_{row}_{line}', v)
        for row in ('CI', 'MI'):
            if row not in (m.get('types') or {}):
                for line in TYPES[row]: DATA[p]['x'].pop(f't_{row}_{line}', None)

# ---------------------------------------------------------------- XBRL statements
def xv(c, y, kind, q=None, pick='first'): return xbrl.value(c, y, kind, q, pick)
def xf(cs, y, kind, q=None):
    for c in cs:
        v = xv(c, y, kind, q)
        if v is not None: return v
    return None

CASH = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 'CashAndCashEquivalentsAtCarryingValue']
def bs_x(y, q):
    g = lambda cs: xf(cs if isinstance(cs, list) else [cs], y, 'I', q)
    ta = g('Assets')
    if ta is None: return None
    o = {'cash': g(CASH), 'ar': g('AccountsReceivableNetCurrent'), 'tca': g('AssetsCurrent'), 'ppe': g('PropertyPlantAndEquipmentNet'),
         'rou': g('OperatingLeaseRightOfUseAsset'), 'gw': g('Goodwill'), 'int': g('IntangibleAssetsNetExcludingGoodwill'),
         'eqi': g(['InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures', 'EquityMethodInvestments']), 'ta': ta,
         'ap': g('AccountsPayableCurrent'), 'acc': g('EmployeeRelatedLiabilitiesCurrent'), 'std': g(['DebtCurrent', 'ShortTermBorrowings']),
         'taxp': g('AccruedIncomeTaxesCurrent'), 'unr': g(['ContractWithCustomerLiabilityCurrent', 'DeferredRevenueCurrent']),
         'tcl': g('LiabilitiesCurrent'), 'ltd': g('LongTermDebtNoncurrent'), 'lease': g('OperatingLeaseLiabilityNoncurrent'),
         'dtl': g('DeferredIncomeTaxLiabilitiesNet'), 'tl': g('Liabilities'), 'rnci': g('RedeemableNoncontrollingInterestEquityCarryingAmount'),
         'eq': g('StockholdersEquity'), 'nci': g('MinorityInterest'), 'tle': g('LiabilitiesAndStockholdersEquity')}
    return o

def dei_shares(fy, q):
    """cover-page shares outstanding of the 10-Q / 10-K for the period (dei; a few weeks after period end)."""
    import datetime as dt
    raw = os.path.join(xbrl.S, 'cf_64040.json')
    if os.path.exists(raw): fs = json.load(open(raw))['facts']['dei']['EntityCommonStockSharesOutstanding']['units']['shares']
    elif os.path.exists(xbrl.SUBSET): fs = json.load(open(xbrl.SUBSET)).get('_dei_shares', [])
    else: return None
    pe = dt.date(fy, q * 3, 30 if q in (2, 3) else 31)
    c = [f for f in fs if 0 <= (dt.date.fromisoformat(f['end']) - pe).days <= 75]
    return min(c, key=lambda f: f['end'])['val'] / 1e6 if c else None

BS_Q226 = {'cash': 4141, 'ar': 3438, 'tca': 8709, 'ppe': 254, 'rou': 392, 'gw': 36348, 'int': 15695, 'eqi': 613, 'ta': 62906, 'ap': 611, 'acc': 581, 'std': 2572,
           'taxp': 238, 'unr': 3929, 'tcl': 9125, 'ltd': 12598, 'lease': 452, 'dtl': 3150, 'tl': 26266, 'rnci': 5024, 'eq': 31501, 'nci': 115, 'tle': 62906}

def do_bs(p):
    fy, q = fyq(p)
    b = BS_Q226 if p == 'Q2-26' else bs_x(fy, q)
    if not b: LOG.append(f'{p}: no XBRL balance sheet'); return
    if fy < 2012: return
    for k in ('cash', 'ar', 'ppe', 'rou', 'gw', 'int', 'eqi', 'ap', 'acc', 'std', 'taxp', 'unr', 'ltd', 'lease', 'dtl', 'rnci', 'nci'): b[k] = N(b.get(k))
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_oca', b['tca'] - b['cash'] - b['ar'])
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_rou', b['rou']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['int']); put(p, 'bs_eqi', b['eqi'])
    put(p, 'bs_onca', b['ta'] - b['tca'] - b['ppe'] - b['rou'] - b['gw'] - b['int'] - b['eqi']); put(p, 'bs_ta', b['ta'])
    put(p, 'bs_ap', b['ap']); put(p, 'bs_acc', b['acc']); put(p, 'bs_std', b['std']); put(p, 'bs_taxp', b['taxp']); put(p, 'bs_unr', b['unr'])
    put(p, 'bs_ocl', b['tcl'] - b['ap'] - b['acc'] - b['std'] - b['taxp'] - b['unr'])
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_lease', b['lease']); put(p, 'bs_dtl', b['dtl'])
    tl = b['tl'] if b.get('tl') is not None else b['tle'] - b['rnci'] - N(b.get('eq')) - b['nci']
    put(p, 'bs_onl', tl - b['tcl'] - b['ltd'] - b['lease'] - b['dtl'])
    put(p, 'bs_rnci', b['rnci']); put(p, 'bs_eq', b['eq']); put(p, 'bs_nci', b['nci']); put(p, 'bs_tle', b['tle'])
    put(p, 'debt_tot', b['std'] + b['ltd'])
    sh = (REC.get(p, {}).get('is') or {}).get('sh_end')
    if sh is None: sh = xv('CommonStockSharesOutstanding', fy, 'I', q)
    if sh is None: sh = dei_shares(fy, q)
    if sh is not None: put(p, 'bs_shares', sh)

# cash flow, year to date
CF_Q226 = {'ni': 2828, 'dep': 64, 'amort': 551, 'sbc': 95, 'def': -114, 'cfo': 2476, 'capex': -65, 'acq': -26, 'divest': 361, 'cfi': 252,
           'bb': -1500, 'div': -575, 'ncid': -162, 'cff': -292, 'fx': -40, 'beg': 1745, 'end': 4141}
def cf_ytd(y, q):
    if (y, q) == (2026, 2): return dict(CF_Q226)
    kind = 'FY' if q == 4 else 'YTD'
    g = lambda cs: xf(cs if isinstance(cs, list) else [cs], y, kind, q)
    def tot(total, cont, disc):          # 2013-15 10-Qs tag continuing and discontinued cash flows separately
        v = g(total)
        if v is None and g(cont) is not None: v = g(cont) + N(g(disc))
        return v
    cfo = tot('NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 'CashProvidedByUsedInOperatingActivitiesDiscontinuedOperations')
    if cfo is None: return None
    o = {'ni': g('ProfitLoss'), 'dep': g('Depreciation'), 'amort': g('AmortizationOfIntangibleAssets'), 'sbc': g('ShareBasedCompensation'),
         'def': g('DeferredIncomeTaxExpenseBenefit'), 'cfo': cfo, 'capex': -N(g('PaymentsToAcquireProductiveAssets')),
         'acq': -N(g('PaymentsToAcquireBusinessesNetOfCashAcquired')), 'divest': N(g(['ProceedsFromDivestitureOfBusinessesNetOfCashDivested', 'ProceedsFromDivestitureOfBusinesses'])),
         'cfi': tot('NetCashProvidedByUsedInInvestingActivities', 'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations', 'CashProvidedByUsedInInvestingActivitiesDiscontinuedOperations'), 'bb': -N(g('PaymentsForRepurchaseOfCommonStock')), 'div': -N(g('PaymentsOfDividendsCommonStock')),
         'ncid': -N(g('PaymentsOfDividendsMinorityInterest')), 'cff': tot('NetCashProvidedByUsedInFinancingActivities', 'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations', 'CashProvidedByUsedInFinancingActivitiesDiscontinuedOperations'),
         'fx': g(['EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 'EffectOfExchangeRateOnCashAndCashEquivalents'])}
    rc = (REC.get(str(y) if q == 4 else qk(y, q)) or {}).get('cfpub') or {}
    if rc.get('ytd_months') == 3 * q:            # release cash-flow fields where XBRL lacks the tag (distributions to NCI in some 10-Qs)
        for k, rk in (('ncid', 'nci_dist'), ('capex', 'capex')):
            if not o[k] and rc.get(rk): o[k] = -abs(rc[rk]); LOG.append(f'{y} Q{q} YTD: {k} from the release ({o[k]})')
    o['_rel_cfo'] = rc.get('cfo') if rc.get('ytd_months') == 3 * q else None
    end = xf(CASH, y, 'I', q)
    beg = xf(CASH, y - 1, 'I', 4)
    o['end'], o['beg'] = end, beg
    if o['fx'] is None and end is not None and beg is not None: o['fx'] = end - beg - cfo - N(o['cfi']) - N(o['cff'])
    return o

def cf_lines(c):
    c = {k: v for k, v in c.items() if not k.startswith('_')}
    o = {'cf_ni': c['ni'], 'cf_dep': N(c['dep']), 'cf_amort': N(c['amort']), 'cf_sbc': N(c['sbc']), 'cf_def': N(c['def'])}
    o['cf_wc'] = c['cfo'] - N(c['ni']) - o['cf_dep'] - o['cf_amort'] - o['cf_sbc'] - o['cf_def']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest']
    o['cf_oinv'] = N(c['cfi']) - c['capex'] - c['acq'] - c['divest']; o['cf_cfi'] = N(c['cfi'])
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_ncid'] = c['ncid']
    o['cf_ofin'] = N(c['cff']) - c['bb'] - c['div'] - c['ncid']; o['cf_cff'] = N(c['cff']); o['cf_fx'] = N(c['fx'])
    o['cf_net'] = c['cfo'] + N(c['cfi']) + N(c['cff']) + N(c['fx'])
    return o

def do_cf():
    for y in range(2012, 2026):
        p = str(y); a = cf_ytd(y, 4)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q >= 3: break
            p = qk(y, q); cur = cf_ytd(y, q)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end'])
            prev = (lc, cur['end'])

def do_misc(p):
    fy, q = fyq(p)
    # dividends declared per share (XBRL), FY2012 regular only (special $2.50 excluded)
    v = xv('CommonStockDividendsPerShareDeclared', fy, 'FY' if q == 4 and p.isdigit() else 'Q', None if p.isdigit() else q)
    if v is not None:
        if p == '2012' and v > 3: v -= 2.5
        if p == 'Q4-12' and v > 2: v -= 2.5
        put(p, 'dps', v)
    elif p == 'Q2-26': put(p, 'dps', 0.97)
    elif q == 4 and not p.isdigit():
        fyv = xv('CommonStockDividendsPerShareDeclared', fy, 'FY')
        qs = [xv('CommonStockDividendsPerShareDeclared', fy, 'Q', k) for k in (1, 2, 3)]
        if fyv is not None and all(v is not None for v in qs):
            v = fyv - sum(qs)
            if fy == 2012 and v > 2: v -= 2.5
            put(p, 'dps', round(v, 4))

def run():
    load()
    for p in periods():
        do_pl(p); do_opex(p); do_bs(p); do_misc(p)
    do_cf()
    do_recast()
    # FY2022: adjusted measures published only pro forma -> actual-scope sum of quarters (model basis, flagged)
    for k in ('adj_ni_mod',):
        pass
    q22 = [qk(2022, q) for q in (1, 2, 3, 4)]
    for k in [f'sa_{r}' for r in ('RAT', 'IDX', 'CI', 'MI', 'MOB', 'ES')] + ['adj_corp', 'adj_eq', 'deal_amort', 'nonop', 'g_res'] + [f'oa_{c}' for c in CATS]:
        put('2022', k, sum(N(x_(q, k)) for q in q22))
    for c in CATS: put('2022', f'oa_{c}_lab', 'FY2022 = sum of the quarters (adjusted measures for the year were published only pro forma for IHS Markit)')
    LOG.append('2022: adjusted division OP / items = sum of quarters (FY adjusted published only pro forma)')
    if all(x_(q, 'adj_ni_pub') is not None or x_(q, 'adj_ni_mod') is not None for q in q22) and x_('2022', 'adj_ni_pub') is None:
        put('2022', 'adj_ni_mod', sum(x_(q, 'adj_ni_pub') if x_(q, 'adj_ni_pub') is not None else x_(q, 'adj_ni_mod') for q in q22))
    put('Q2-26', 'debt_notes', 15170 - 825 - MAN['mobility_spin']['mobility_notes_carrying_2026_06_30']); put('Q2-26', 'debt_cp', 825)
    # FCF (company definition: CFO - capex - distributions to NCI) as published
    for p in periods():
        c = (REC.get(p) or {}).get('cfpub') or {}
        v = None
        if c.get('fcf_pub_q') is not None and not p.isdigit(): v = c['fcf_pub_q']
        elif p.isdigit() and c.get('fcf_pub') is not None: v = c['fcf_pub']
        elif c.get('ytd_months') == 3 and c.get('fcf_pub') is not None: v = c['fcf_pub']
        if v is None: continue
        # compare only where the release cash-flow statement agrees with the 10-Q / 10-K (XBRL) operating cash flow used in the model
        same = (p.isdigit() and c.get('ytd_months') == 12) or (not p.isdigit() and c.get('ytd_months') == 3)
        if same and c.get('cfo') is not None and x_(p, 'cf_cfo') is not None and abs(c['cfo'] - x_(p, 'cf_cfo')) > 1.01:
            LOG.append(f'{p}: published FCF {v} not compared: release CFO {c["cfo"]} vs 10-Q/10-K {x_(p, "cf_cfo")}'); put(p, 'fcf_pub_nc', v); continue
        put(p, 'fcf_pub', v)
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'op', 'adj_op_pub', 'e_pub', 'disc', 'sr_RAT', 'sr_CI', 'sr_MI', 'cf_cfo', 'bs_ta', 'bs_shares', 'dps')})
    print('\n'.join(LOG))
