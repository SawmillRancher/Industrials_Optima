"""Per-period extraction for The Brink's Company -> data/<period>.json (schema: EXTRACTION_SCHEMA.md).

Sources (SEC EDGAR only, CIK 78890):
  * statements (is / bs / cf): XBRL company facts, value as FIRST filed in a 10-K / 10-Q (= as originally reported), FY2009+;
    FY2006-08 from the FY2008 10-K text (hand.json; continuing operations after the Brink's Home Security spin-off of 31-Oct-2008);
  * segments, "other items not allocated to segments" and the non-GAAP reconciliations: quarterly tables of the 8-K Ex. 99.1
    earnings releases. Each year's quarters come from that year's fourth-quarter release (1Q-4Q + full year, as presented at year
    end); 2013 and 2019 from the following year's release (prior-year columns: first release on the new table layout / current
    four-segment basis); 2026 from the third-quarter 2026 release;
  * organic / acquisitions-dispositions / currency revenue and profit changes: the "nQ'YY vs" table of each quarterly release;
  * free cash flow before dividends: each release's reconciliation (year to date).
Nothing is estimated: a line that is not published is omitted (null)."""
import json, os, re, glob, sys
import xbrl
from parse_release import wide_tables, cells, num
S = os.environ.get('BCO_SRC', '/tmp/bco_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
FL = json.load(open(os.path.join(S, 'filings.json')))
def url(o, f=None): return f"https://www.sec.gov/Archives/edgar/data/78890/{o['acc'].replace('-', '')}/{f or o['primary']}"

# ---------------------------------------------------------------- releases
def release_of(o):
    best = None
    for f in glob.glob(f"{S}/txt/{o['date']}_8-K_{o['acc']}_*.txt"):
        t = open(f, errors='ignore').read()
        if 'Forward-Looking' in t and ('Segment Results' in t or 'Balance Sheets' in t or 'Statements of' in t) and len(t) < 75000 and 'ex992' not in f and 'slides' not in f:
            if best is None or len(t) > len(best[1]): best = (f, t)
    return best
REL = {}          # (year, q) -> (filing, file, text)
for o in FL:
    if o['form'] != '8-K' or not ('2.02' in o['items'] or o['date'] in ('2024-05-08', '2026-05-06')) or o['date'] < '2013-04-01': continue
    r = release_of(o)
    if not r: continue
    y, m = int(o['date'][:4]), int(o['date'][5:7])
    key = (y - 1, 4) if m <= 3 else (y, 1) if m <= 5 else (y, 2) if m <= 8 else (y, 3)
    REL[key] = (o, os.path.basename(r[0]).split('_', 3)[3].replace('.txt', '.htm'), r[1])
def rel_url(key):
    o, f, _ = REL[key]; return url(o, f)

def norm(l): return re.sub(r'\s*\((?:[a-z]\)\()*[a-z]\)\s*$', '', re.sub(r'\s+', ' ', l)).strip()
SEGSETS = [('cur4', ['North America', 'Latin America', 'Europe', 'Rest of World']), ('three', ['North America', 'South America', 'Rest of World']),
           ('mkts', ['U.S.', 'France', 'Mexico', 'Brazil', 'Canada', 'Largest 5 Markets', 'Latin America', 'EMEA', 'Asia', 'Global Markets', 'Payment Services']),
           ('intl', ['Latin America', 'EMEA', 'Asia Pacific', 'International', 'North America'])]
TOT_NG = ('Operating profit - non-GAAP', 'Non-GAAP', 'Segment operating profit')
TOT_G = ('Operating profit (loss) - GAAP', 'Operating profit (loss) -GAAP', 'GAAP', 'Operating profit')

def year_tables(key, want_basis=None):
    """parse the quarterly tables of release `key`; returns {'cur': {...}, 'py': {...}} with per-column lists"""
    rows = wide_tables(REL[key][2])
    seg = [r for r in rows if r[0].lower().startswith('segment results')]
    rec = [r for r in rows if r[0].lower().startswith('non-gaap')]
    oth = [r for r in rows if r[0].startswith('Other Items')]
    # several segment bases can be shown in one release (FY2020: current four segments and the former three)
    blocks, cur = [], None
    for ti, sec, lab, v in seg:
        s = sec.lower()
        if s.startswith('revenue') and (cur is None or cur['stage'] != 'rev'):
            cur = {'stage': 'rev', 'rev': [], 'op': []}; blocks.append(cur)
        if cur is None: continue
        if s.startswith('operating profit') or s.startswith('operating margin') or s.startswith('margin'): cur['stage'] = s.split(' ')[0] + s.split(' ')[1][:1] if s.startswith('operating') else 'margin'
        if s.startswith('revenue'): cur['rev'].append((norm(lab), v))
        elif s.startswith('operating profit'): cur['op'].append((norm(lab), v))
    out = []
    for b in blocks:
        labs = [l for l, _ in b['rev']]
        basis = next((n for n, ss in SEGSETS if all(x in labs for x in ss[:3]) and (n != 'cur4' or 'Europe' in labs) and (n != 'three' or 'South America' in labs)
                      and (n != 'intl' or 'International' in labs) and (n != 'mkts' or 'U.S.' in labs)), None)
        if basis: out.append((basis, b))
    sections = {}
    for ti, sec, lab, v in rec:
        sections.setdefault(sec, []).append((norm(lab), v))
    sections['__items_op'] = [(norm(lab), v) for ti, sec, lab, v in oth if sec.lower().startswith('operating profit')]
    sections['__items_rev'] = [(norm(lab), v) for ti, sec, lab, v in oth if sec.lower().startswith('revenue')]
    return out, sections

def split(v, which, n):
    """columns of the wanted year: prior year = first 5, current = rest"""
    if n == 10: a = v[:5] if which == 'py' else v[5:]
    elif n == 9: a = v[:5] if which == 'py' else v[5:] + [None]
    else: return None
    return a

def take(rows, which, qi):
    out = []
    for lab, v in rows:
        a = split(v, which, len(v))
        if a is None: continue
        out.append([lab, a[qi]])
    return out

def sec_find(sections, pat):
    for k in sections:
        if re.match(pat, k, re.I): return sections[k]
    return []

def release_period(year, q):
    """q in 1..4 or None (full year): data of period from the designated release"""
    if year == 2013: return release_2013(q)
    if year == 2019: key, which = (2020, 4), 'py'
    elif year == 2026: key, which = (2026, 3), 'cur'
    else: key, which = (year, 4), 'cur'
    if key not in REL: return None
    if year == 2026 and q is None: return None
    qi = 4 if q is None else q - 1
    blocks, sections = year_tables(key)
    d = {'release': rel_url(key), 'release_period': f'Q{key[1]}-{key[0]}', 'seg': [], 'ng': {}}
    for basis, b in blocks:
        if year == 2019 and basis != 'cur4': continue
        if year == 2020 and basis != 'cur4': continue
        rev = take(b['rev'], which, qi); op = take(b['op'], which, qi)
        if rev and rev[0][1] is not None: d['seg'].append({'basis': basis, 'rev': rev, 'op': op})
    names = {'rev': r'^revenues?:?$', 'op': r'^operating profit( \(loss\))?:?$', 'eps': r'^EPS', 'inc': r'^income (\(loss\) )?from continuing', 'ebitda': r'^adjusted ebitda',
             'da': r'^depreciation and amort', 'int': r'^interest expense', 'oth': r'^interest and other', 'tax': r'^taxes', 'nci': r'^noncontrolling', 'recni': r'^reconciliation to net income', 'op_items': r'^__items_op', 'rev_items': r'^__items_rev'}
    for k, pat in names.items():
        rows = take(sec_find(sections, pat), which, qi)
        if rows and any(v is not None for _, v in rows): d['ng'][k] = rows
    return d

def release_2013(q):
    """FY2013 release: quarterly tables on the International / North America basis, a GAAP block followed by a non-GAAP block"""
    key = (2013, 4); qi = 4 if q is None else q - 1
    rows = [r for r in wide_tables(REL[key][2]) if len(r[3]) == 10]
    blocks, cur = [], None
    for ti, sec, lab, v in rows:
        if norm(lab) == 'Latin America' and sec.lower().startswith('revenue'):
            cur = {}; blocks.append(cur)
        if cur is not None: cur[(sec.split(':')[0].split(' ')[0].lower(), norm(lab))] = v[5:][qi]
    g, n = blocks[0], blocks[1]
    seg = [{'basis': 'intl2', 'rev': [['International', g[('revenues', 'International')]], ['North America', g[('revenues', 'North America')]]],
            'op': [['International', g[('operating', 'International')]], ['North America', g[('operating', 'North America')]], ['Non-segment', g[('operating', 'Non-segment')]]]}]
    tot = {'rev': n[('revenues', 'Revenues')], 'op': n[('operating', 'Operating profit')], 'inc': n[('amounts', 'Income from continuing operations')], 'eps': n[('amounts', 'Diluted EPS – continuing operations')]}
    gaap = {'op': g[('operating', 'Operating profit')], 'inc': g[('amounts', 'Income from continuing operations')], 'eps': g[('amounts', 'Diluted EPS – continuing operations')], 'rev': g[('revenues', 'Revenues')]}
    return {'release': rel_url(key), 'release_period': 'Q4-2013', 'seg': seg, 'ng': {}, 'ngaap_tot': tot, 'gaap_tbl': gaap}

# ---------------------------------------------------------------- growth tables (each quarterly release)
def growth_tables(year, q):
    key = (year, q)
    if key not in REL or year < 2015: return None       # 2013-14 releases: year-to-date / legacy-basis tables, not used
    lines = REL[key][2].split('\n'); res = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(?:GAAP \| )?([1-4])Q\s?'?(\d\d)(?: \([a-z]\))? \|", ln)
        if not m or int(m.group(1)) != q or 2000 + int(m.group(2)) != year - 1: continue
        sec, rows = '', []
        for l2 in lines[i + 1:i + 60]:
            c = cells(l2)
            if len(c) == 1:
                if c[0].strip().endswith(':'): sec = c[0].strip().rstrip(':')
                if c[0].startswith('Amounts may not add'): break
                continue
            v = [num(x) for x in c[1:]]
            if len(v) >= 5 and all(x is not None for x in v[:5]): rows.append([sec, norm(c[0]), v[:5]])
        if rows: res.append(rows)
    return res

# ---------------------------------------------------------------- free cash flow (year to date)
def fcf_table(year, q):
    key = (year, q)
    if key not in REL: return None
    lines = REL[key][2].split('\n')
    for i, ln in enumerate(lines):
        c = cells(ln)
        if not c[0].startswith('Free cash flow before dividends') or len(c) < 2 or '–' in ln: continue
        if num(c[-1]) is None: continue
        rows = []
        for l2 in lines[max(0, i - 14):i + 1]:
            c2 = cells(l2); v = [x for x in (num(x) for x in c2[1:]) if x is not None]
            if re.match(r'^(Cash flows? |Net cash |Operating activities - GAAP)', c2[0]): rows = []
            if len(c2) >= 2 and v: rows.append([norm(c2[0]), v[-1]])
        if rows and re.match(r'^(Cash flows? |Net cash |Operating activities - GAAP)', rows[0][0]): return rows
    return None

# ---------------------------------------------------------------- statements from XBRL
IS = {'rev': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'], 'cor': ['CostOfRevenue'],
      'sga': ['OtherSellingGeneralAndAdministrativeExpense', 'SellingGeneralAndAdministrativeExpense'], 'tce': ['CostsAndExpenses'], 'ooi': ['OtherOperatingIncomeExpenseNet'],
      'op': ['OperatingIncomeLoss'], 'int': ['InterestExpense', 'InterestExpenseNonoperating', 'InterestExpenseDebt'], 'ven_decon': ['DeconsolidationGainOrLossAmount'],
      'oth': ['NonoperatingIncomeExpense', 'OtherNonoperatingIncomeExpense'],
      'ebt': ['IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
      'tax': ['IncomeTaxExpenseBenefit'], 'cont': ['IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest'], 'disc': ['IncomeLossFromDiscontinuedOperationsNetOfTax'],
      'pl': ['ProfitLoss'], 'nci': ['NetIncomeLossAttributableToNoncontrollingInterest'], 'ni': ['NetIncomeLoss'], 'cont_att': ['IncomeLossFromContinuingOperations'],
      'disc_att': ['IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity'],
      'eps_d': ['EarningsPerShareDiluted'], 'eps_cont_d': ['IncomeLossFromContinuingOperationsPerDilutedShare'], 'eps_b': ['EarningsPerShareBasic'],
      'sh_d': ['WeightedAverageNumberOfDilutedSharesOutstanding'], 'sh_b': ['WeightedAverageNumberOfSharesOutstandingBasic'], 'dps': ['CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid']}
PS = ('eps_d', 'eps_cont_d', 'eps_b', 'dps')
CF = {'ni': ['ProfitLoss'], 'disc': ['IncomeLossFromDiscontinuedOperationsNetOfTax'], 'da': ['DepreciationDepletionAndAmortization'], 'sbc': ['ShareBasedCompensation'],
      'def_tax': ['DeferredIncomeTaxExpenseBenefit'], 'cfo': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'], 'capex': ['PaymentsToAcquirePropertyPlantAndEquipment'],
      'acq': ['PaymentsToAcquireBusinessesNetOfCashAcquired'], 'ppe_sale': ['ProceedsFromSaleOfPropertyPlantAndEquipment'], 'divest': ['ProceedsFromDivestitureOfBusinessesNetOfCashDivested'],
      'cfi': ['NetCashProvidedByUsedInInvestingActivities'], 'buyback': ['PaymentsForRepurchaseOfCommonStock'], 'div': ['PaymentsOfDividendsCommonStock'],
      'div_nci': ['PaymentsOfDividendsMinorityInterest'], 'cff': ['NetCashProvidedByUsedInFinancingActivities'],
      'fx': ['EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisclosedInAnotherLineItem', 'EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
             'EffectOfExchangeRateOnCashAndCashEquivalents', 'EffectOfExchangeRateOnCashAndCashEquivalentsContinuingOperations'],
      'net': ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 'CashAndCashEquivalentsPeriodIncreaseDecrease'],
      'amort': ['AmortizationOfIntangibleAssets'], 'tax_paid': ['IncomeTaxesPaidNet'], 'int_paid': ['InterestPaidNet', 'InterestPaid']}
BS = {'cash': ['CashAndCashEquivalentsAtCarryingValue'], 'rcash': ['RestrictedCashAndCashEquivalentsAtCarryingValue', 'RestrictedCashCurrent', 'RestrictedCashAndCashEquivalents'], 'ar': ['AccountsReceivableNetCurrent'], 'tca': ['AssetsCurrent'],
      'rou': ['OperatingLeaseRightOfUseAsset'], 'ppe': ['PropertyPlantAndEquipmentNet'], 'gw': ['Goodwill'], 'intang': ['OtherIntangibleAssetsNet', 'IntangibleAssetsNetExcludingGoodwill'],
      'ta': ['Assets'], 'stb': ['ShortTermBorrowings'], 'cltd': ['LongTermDebtCurrent', 'LongTermDebtAndCapitalLeaseObligationsCurrent'], 'ap': ['AccountsPayableCurrent'],
      'accr': ['AccruedLiabilitiesCurrent'], 'tcl': ['LiabilitiesCurrent'], 'ltd': ['LongTermDebtNoncurrent', 'LongTermDebtAndCapitalLeaseObligations'],
      'pension': ['DefinedBenefitPensionPlanLiabilitiesNoncurrent'], 'opeb': ['OtherPostretirementDefinedBenefitPlanLiabilitiesNoncurrent'], 'lease': ['OperatingLeaseLiabilityNoncurrent'],
      'tl': ['Liabilities'], 'eq': ['StockholdersEquity'], 'nci': ['MinorityInterest'], 'teq': ['StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
      'tle': ['LiabilitiesAndStockholdersEquity'], 'shares': ['CommonStockSharesOutstanding', 'CommonStockSharesIssued'],
      'cash_cf': ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']}

def r1(v, n=1): return None if v is None else round(v, n)
def statements(year, q, filed_from=None, filed=None):
    """q None = full year. is: discrete quarter (Q1-Q3) or full year; cf: year to date; bs: period end.
    filed_from: take the first value filed on / after this date (a recast comparative) instead of the first-filed value."""
    d = {'is': {}, 'cf': {}, 'bs': {}}
    for k, cs in IS.items():
        v = xbrl.first_of(cs, year, 'FY' if q is None else 'Q', q, scale=None if k in PS else 1e6, filed_from=filed_from)
        if v is not None: d['is'][k] = round(v, 2) if k in PS else r1(v)
    qq = 4 if q is None else q
    for k, cs in CF.items():
        v = xbrl.first_of(cs, year, 'YTD', qq)
        if v is not None: d['cf'][k] = r1(v)
    if d['cf']: d['cf']['ytd_months'] = 3 * qq
    for k, cs in BS.items():
        v = xbrl.first_of(cs, year, 'I', qq)
        if v is not None: d['bs'][k] = r1(v)
    i = d['is']
    if i.get('pl') is not None and i.get('ni') is not None: i['nci'] = r1(i['pl'] - i['ni'])       # sign of the XBRL NCI fact is unreliable (FY2014)
    if 'ven_decon' in i:
        if year == 2018 and q in (None, 2): i['ven_decon'] = r1(abs(i['ven_decon']))
        else: del i['ven_decon']
    da = xbrl.first_of(['WeightedAverageNumberDilutedSharesOutstandingAdjustment'], year, 'FY' if q is None else 'Q', q)
    if da is not None and i.get('sh_b') is not None: i['sh_ng'] = r1(i['sh_b'] + da)
    if d['cf'] and filed:      # opening / closing cash as presented in this period's own filing
        tag = ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'] if year >= 2018 else ['CashAndCashEquivalentsAtCarryingValue']
        b = xbrl.first_of(tag, year - 1, 'I', 4, filed_from=filed); en = xbrl.first_of(tag, year, 'I', qq, filed_from=filed)
        if b is not None: d['cf']['cash_beg'] = r1(b)
        if en is not None: d['cf']['cash_end'] = r1(en)
    return d

def filing_for(year, q):
    end = f'{year}-' + {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[q or 4]
    for o in FL:
        if o['form'] in ('10-K', '10-Q') and o['report'] == end: return o
    return None

def build(year, q):
    per = str(year) if q is None else f'Q{q}-{str(year)[2:]}'
    d = {'period': per, 'year': year, 'quarter': q, 'sources': [], 'notes': []}
    o = filing_for(year, q)
    st = statements(year, q, filed=o['date'] if o else None)
    d.update(st)
    if o: d['sources'].append(url(o))
    d['sources'].append('https://data.sec.gov/api/xbrl/companyfacts/CIK0000078890.json')
    d['notes'].append('Statements: XBRL company facts, value as first filed in the 10-K / 10-Q for the period (as originally reported).')
    i = d['is']
    if xbrl.first_of(IS['ooi'], year, 'FY' if q is None else 'Q', q) is None and all(k in i for k in ('op', 'rev', 'tce')):
        i['ooi'] = r1(i['op'] - i['rev'] + i['tce']); d['notes'].append('Other operating income (expense) not tagged in XBRL for this period: derived as operating profit − revenues + total costs and expenses (face-statement identity).')
    if year >= 2013:
        rp = release_period(year, q)
        if rp:
            d['seg'] = rp['seg']; d['ngaap'] = rp['ng']; d['sources'].append(rp['release'])
            if rp.get('ngaap_tot'): d['ngaap_tot'] = rp['ngaap_tot']; d['gaap_tbl'] = rp['gaap_tbl']
            # hybrid recast: where the year-end release re-presented the quarter (discontinued operations), take the recast
            # comparative filed in the following year's 10-Q so that the income statement ties to the release tables
            top = (rp.get('gaap_tbl') or {}).get('op')
            if top is None:
                for l, v in rp['ng'].get('op', []):
                    if l == 'GAAP': top = v
            if q and top is not None and i.get('op') is not None and abs(top - i['op']) > 0.15:
                st2 = statements(year, q, filed_from=f'{year + 1}-01-01')
                if st2['is'].get('op') is not None and abs(st2['is']['op'] - top) <= 0.15:
                    orig = {k: i.get(k) for k in ('rev', 'op', 'cont_att')}
                    for k in list(i):
                        if k in st2['is']: i[k] = st2['is'][k]
                    if 'tce' in i: i['ooi'] = r1(i['op'] - i['rev'] + i['tce'])
                    d['recast'] = {'reason': 'Re-presented at year end (discontinued operations): comparative as filed in the ' + str(year + 1) + ' Form 10-Q, consistent with the fourth-quarter ' + str(year) + ' release tables.', 'original': orig}
                    d['notes'].append(f"Income statement recast: {d['recast']['reason']} Originally reported: revenues {orig['rev']}, operating profit {orig['op']}, income from continuing operations attributable to Brink's {orig['cont_att']}.")
                else:
                    d['notes'].append(f'Release-table GAAP operating profit {top} differs from the first-filed statement {i.get("op")}; no matching recast comparative found.')
            d['notes'].append(f"Segments / non-GAAP reconciliations: quarterly tables of the {rp['release_period']} earnings release (Ex. 99.1).")
        if q or year:
            g = growth_tables(year, q or 4) if q else None
            if g:
                d['growth'] = g; d['sources'].append(rel_url((year, q)))
        f = fcf_table(year, q or 4)
        if f:
            d['fcf'] = {'ytd_months': 3 * (q or 4), 'rows': f}
            if rel_url((year, q or 4)) not in d['sources']: d['sources'].append(rel_url((year, q or 4)))
    if year == 2026 and q is None: return None
    return d

def main():
    os.makedirs(OUT, exist_ok=True)
    hand = json.load(open(os.path.join(HERE, 'hand.json')))
    n = 0
    for year in range(2006, 2027):
        for q in (None, 1, 2, 3):
            if q and year < 2013: continue
            if year == 2026 and q is None: continue
            per = str(year) if q is None else f'Q{q}-{str(year)[2:]}'
            d = build(year, q) if year >= 2009 else {'period': per, 'year': year, 'quarter': None, 'sources': [], 'notes': []}
            h = hand.get(per)
            if h:
                for k, v in h.items():
                    if k in ('sources', 'notes'): d[k] = v + [x for x in d.get(k, []) if x not in v] if year < 2009 else d.get(k, []) + v
                    elif isinstance(v, dict) and isinstance(d.get(k), dict): d[k].update(v)
                    else: d[k] = v
            json.dump(d, open(os.path.join(OUT, per + '.json'), 'w'), indent=1, ensure_ascii=False); n += 1
        if year >= 2013:      # Q4 release data (three-month column) stored with the full-year record
            pass
    # Q4 release-only records (segments / non-GAAP three-month column; statements are derived FY - 9M in normalize.py)
    for year in range(2013, 2026):
        rp = release_period(year, 4)
        d = {'period': f'Q4-{str(year)[2:]}', 'year': year, 'quarter': 4, 'sources': [rp['release']] if rp else [],
             'notes': ['Fourth quarter: segments / non-GAAP from the three-month column of the release tables; income statement and cash flow = full year − nine months (normalize.py); balance sheet = year end.']}
        if rp:
            d['seg'] = rp['seg']; d['ngaap'] = rp['ng']
            if rp.get('ngaap_tot'): d['ngaap_tot'] = rp['ngaap_tot']; d['gaap_tbl'] = rp['gaap_tbl']
        g = growth_tables(year, 4)
        if g: d['growth'] = g
        json.dump(d, open(os.path.join(OUT, d['period'] + '.json'), 'w'), indent=1, ensure_ascii=False); n += 1
    xbrl.dump_subset(xbrl.USED)
    print(n, 'period files')

if __name__ == '__main__':
    main()
