"""Per-period extraction for the Alphabet / Google model -> data/<period>.json (FY2006-FY2025 annual, Q1-13 .. Q2-26).

Sources (SEC EDGAR only):
  * FY2006-FY2008: each year's own Form 10-K (pre09.py; Google's XBRL starts with the Q2-2009 10-Q).
  * FY2009+ and every quarter: the XBRL instance of the period's own 10-K / 10-Q (as originally reported):
      - income statement: Q1-Q3 = the 10-Q three-month facts; Q4 = 10-K fiscal year - Q3 10-Q nine months (stated in notes);
        Q4 EPS / weighted shares from the Q4 earnings release (Ex. 99.1) three-month column;
      - cash flow: year-to-date facts (ytd_months); discrete quarters are derived in normalize.py;
      - balance sheet: instant facts at the period end.
  * Revenue by type and segment revenue / operating income (dimensional XBRL facts): from the LATEST filing that presents
    the period (recast basis), with the as-first-reported values kept for the legacy structures.
  * Google Inc. non-GAAP (excl. SBC; published Q1-13 .. Q4-14) and free cash flow: earnings releases (Ex. 99.1), parse_release.py.
Units: USD millions; shares millions; per share USD; all AS FILED (pre-split) - split factors are applied in normalize.py.
Signs: costs positive; other income / expense signed by its effect on income; cash flow as presented."""
import json, os, re, glob, datetime as dt
import xinst, pre09, parse_release

S = xinst.S
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
FL = json.load(open(os.path.join(S, 'filings.json')))
def url(o, doc=None):
    return f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{o['acc'].replace('-', '')}/{doc or o['primary']}"

# ---------------------------------------------------------------- concept aliases (regex on the local concept name; first hit wins)
A = {
  # income statement (durations)
  'rev': [r'^Revenues$', r'^RevenueFromContractWithCustomerExcludingAssessedTax$', r'^SalesRevenueNet$'],
  'cor': [r'^CostOfRevenue$'], 'rd': [r'^ResearchAndDevelopmentExpense$'], 'sm': [r'^SellingAndMarketingExpense$'],
  'ga': [r'^GeneralAndAdministrativeExpense$'], 'opex_tot': [r'^CostsAndExpenses$'], 'oi': [r'^OperatingIncomeLoss$'],
  'oie': [r'^NonoperatingIncomeExpense$'],
  'ebt': [r'^IncomeLossFromContinuingOperationsBeforeIncomeTaxes(MinorityInterestAndIncomeLossFromEquityMethodInvestments|ExtraordinaryItemsNoncontrollingInterest)$'],
  'tax': [r'^IncomeTaxExpenseBenefit$'], 'ni_cont': [r'^IncomeLossFromContinuingOperations$'],
  'disc': [r'^IncomeLossFromDiscontinuedOperationsNetOfTax$', r'^IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity$'],
  'ni': [r'^NetIncomeLoss$'], 'pref_div': [r'^PreferredStockDividendsIncomeStatementImpact$'],
  'eps_b': [r'^EarningsPerShareBasic$'], 'eps_d': [r'^EarningsPerShareDiluted$'],
  'sh_b': [r'^WeightedAverageNumberOfSharesOutstandingBasic$'], 'sh_d': [r'^WeightedAverageNumberOfDilutedSharesOutstanding$'],
  'dps': [r'^CommonStockDividendsPerShareDeclared$'],
  'sbc_is': [r'^AllocatedShareBasedCompensationExpense$'],
  'int_inc': [r'^InvestmentIncomeInterest$', r'^InterestIncomeOther$', r'^InvestmentIncomeInterestAndDividend$'],
  'int_exp': [r'^InterestExpenseNonoperating$', r'^InterestExpense$'],
  'eq_gain': [r'^EquitySecuritiesFvNiGainLoss$', r'^EquitySecuritiesFVNIGainLossTotal$'],
  'amort_int': [r'^AmortizationOfIntangibleAssets$', r'^AmortizationOfAcquiredIntangibleAssets$'],
  # cash flow (YTD durations)
  'cf_dep': [r'^Depreciation$', r'^DepreciationAndImpairmentOnDispositionOfPropertyAndEquipment$', r'^DepreciationandImpairmentonDispositionofPropertyandEquipment$',
             r'^DepreciationandLossonDispositionofPropertyPlantandEquipment$', r'^DepreciationAmortizationAndImpairmentOnDispositionOfPropertyAndEquipment$',
             r'^DepreciationAmortizationandImpairmentonDispositionofPropertyandEquipment$', r'^DepreciationOfPropertyAndEquipment$'],
  'cf_amort': [r'^AmortizationAndImpairmentOfIntangibleAssets$', r'^AmortizationandImpairmentofIntangibleAssets$', r'^AmortizationandImpairmentofIntangibleandOtherAssets$',
               r'^AmortizationOfIntangibleAssets$', r'^AmortizationOfAcquiredIntangibleAssets$'],
  'cf_sbc': [r'^ShareBasedCompensation$'], 'cf_def': [r'^DeferredIncomeTaxExpenseBenefit$', r'^DeferredIncomeTaxesAndTaxCredits$'],
  'cf_gain': [r'^GainLossOnInvestments$', r'^DebtAndEquitySecuritiesGainLoss$', r'^GainLossonDebtandEquitySecuritiesNet$', r'^GainLossOnDebtAndEquitySecuritiesNet$',
              r'^GainLossonMarketableandNonmarketableInvestmentsNet$', r'^GainLossOnMarketableAndNonMarketableInvestmentsNet$', r'^MarketableSecuritiesRealizedGainLoss.*$'],
  'cf_cfo': [r'^NetCashProvidedByUsedInOperatingActivities$', r'^NetCashProvidedByUsedInOperatingActivitiesContinuingOperations$'],
  'cf_capex': [r'^PaymentsToAcquirePropertyPlantAndEquipment$', r'^PaymentsToAcquireProductiveAssets$'],
  'cf_acq': [r'^PaymentsToAcquireBusinessesNetOfCashAcquired$', r'^AcquisitionsNetOfCashAcquiredAndPurchasesOfIntangibleAndOtherAssets$',
             r'^AcquisitionsNetofCashAcquiredAndPurchasesOfIntangibleandOtherAssets$', r'^AcquisitionsNetOfCashAcquiredAndProceedsFromDivestitureAndPurchasesOfIntangibleAndOtherAssets$',
             r'^PaymentsToAcquireBusinessesNetOfCashAcquiredAndPurchasesOfIntangibleAndOtherAssets$'],
  'cf_divest': [r'^ProceedsFromDivestitureOfBusinesses$', r'^ProceedsFromDivestitureOfBusinessesNetOfCashDivested$', r'^ProceedsFromSaleOfBusinesses.*$'],
  'cf_cfi': [r'^NetCashProvidedByUsedInInvestingActivities$', r'^NetCashProvidedByUsedInInvestingActivitiesContinuingOperations$'],
  'cf_bb': [r'^PaymentsForRepurchaseOfCommonStock$', r'^PaymentsForRepurchaseOfEquity$'],
  'cf_div': [r'^PaymentsOfDividendsCommonStock$', r'^PaymentsOfOrdinaryDividends$', r'^PaymentsOfDividends$'],
  'cf_minority': [r'^ProceedsFromMinorityShareholders$'],
  'cf_div_pref': [r'^PaymentsOfDividendsPreferredStockAndPreferenceStock$'],
  'cf_sbcnet': [r'^ProceedsFromPaymentsForOtherFinancingActivitiesRelatedToStockBasedAwardActivities$', r'^PaymentsRelatedToTaxWithholdingForShareBasedCompensation$',
                r'^NetPaymentsRelatedToStockBasedAwardActivities$', r'^NetProceedsPaymentsRelatedToStockBasedAwardActivities$',
                r'^ProceedsFromPaymentsForOtherFinancingActivities.*StockBased.*$', r'^NetProceedsFromPaymentsForStockBasedAwardActivities$'],
  'cf_eq_iss': [r'^ProceedsFromIssuanceOfCommonStock$'], 'cf_pref_iss': [r'^ProceedsFromIssuanceOfConvertiblePreferredStock$', r'^ProceedsFromIssuanceOfPreferredStockAndPreferenceStock$'],
  'cf_debt_iss': [r'^ProceedsFromIssuanceOfDebt$', r'^ProceedsFromDebtNetOfIssuanceCosts$', r'^ProceedsFromIssuanceOfLongTermDebt$'],
  'cf_debt_rep': [r'^RepaymentsOfDebt$', r'^RepaymentsOfDebtAndCapitalLeaseObligations$', r'^RepaymentsOfLongTermDebtAndCapitalSecurities$', r'^RepaymentsOfLongTermDebt$'],
  'cf_cff': [r'^NetCashProvidedByUsedInFinancingActivities$', r'^NetCashProvidedByUsedInFinancingActivitiesContinuingOperations$'],
  'cf_fx': [r'^EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents$', r'^EffectOfExchangeRateOnCashAndCashEquivalents$'],
  # balance sheet / cash (instants)
  'cf_cash': [r'^CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents$', r'^CashAndCashEquivalentsAtCarryingValue$'],
  'bs_cash': [r'^CashAndCashEquivalentsAtCarryingValue$'],
  'bs_msec': [r'^MarketableSecuritiesCurrent$', r'^AvailableForSaleSecuritiesCurrent$', r'^ShortTermInvestments$'],
  'bs_ar': [r'^AccountsReceivableNetCurrent$'], 'bs_tca': [r'^AssetsCurrent$'],
  'bs_nmsec': [r'^OtherLongTermInvestments$', r'^LongTermInvestments$', r'^NonMarketableSecurities$'],
  'bs_ppe': [r'^PropertyPlantAndEquipmentNet$', r'^PropertyPlant[Aa]nd[Ee]quipment[Aa]nd[Ff]inance[Ll]ease[Rr]ight[Oo]f[Uu]se[Aa]sset[Aa]fter[Aa]ccumulated[Dd]epreciation[Aa]nd[Aa]mortization$'], 'bs_rou': [r'^OperatingLeaseRightOfUseAsset$'],
  'bs_gw': [r'^Goodwill$'], 'bs_int': [r'^IntangibleAssetsNetExcludingGoodwill$', r'^FiniteLivedIntangibleAssetsNet$'],
  'bs_ta': [r'^Assets$'], 'bs_ap': [r'^AccountsPayableCurrent$'], 'bs_tcl': [r'^LiabilitiesCurrent$'],
  'bs_cp': [r'^CommercialPaper$', r'^ShortTermBorrowings$'],
  'bs_cltd': [r'^LongTermDebtCurrent$', r'^LongTermDebtAndCapitalLeaseObligationsCurrent$', r'^DebtCurrent$'],
  'bs_ltd': [r'^LongTermDebtNoncurrent$', r'^LongTermDebtAndCapitalLeaseObligations$'],
  'bs_oll': [r'^OperatingLeaseLiabilityNoncurrent$'],
  'bs_tl': [r'^Liabilities$'], 'bs_pref': [r'^PreferredStockIncludingAdditionalPaidInCapital$', r'^PreferredStockValue$'],
  'bs_eq': [r'^StockholdersEquity$'], 'bs_tle': [r'^LiabilitiesAndStockholdersEquity$'],
  'bs_sh': [r'^CommonandCapitalStockSharesOutstanding$', r'^CommonStockSharesOutstanding$'],
}
DUR_IS = ['rev', 'cor', 'rd', 'sm', 'ga', 'opex_tot', 'oi', 'oie', 'ebt', 'tax', 'ni_cont', 'disc', 'ni', 'pref_div', 'sbc_is', 'int_inc', 'int_exp',
          'eq_gain', 'amort_int', 'dps']
PS = ['eps_b', 'eps_d', 'sh_b', 'sh_d']
DUR_CF = ['cf_dep', 'cf_amort', 'cf_sbc', 'cf_def', 'cf_gain', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_divest', 'cf_cfi', 'cf_bb', 'cf_div', 'cf_div_pref', 'cf_sbcnet',
          'cf_eq_iss', 'cf_pref_iss', 'cf_minority', 'cf_debt_iss', 'cf_debt_rep', 'cf_cff', 'cf_fx']
INST = ['cf_cash', 'bs_cash', 'bs_msec', 'bs_ar', 'bs_tca', 'bs_nmsec', 'bs_ppe', 'bs_rou', 'bs_gw', 'bs_int', 'bs_ta', 'bs_ap', 'bs_tcl', 'bs_cp', 'bs_cltd', 'bs_ltd',
        'bs_oll', 'bs_tl', 'bs_pref', 'bs_eq', 'bs_tle', 'bs_sh']
COMP = {k: [re.compile(p) for p in v] for k, v in A.items()}
CF_NEG = {'cf_capex', 'cf_acq', 'cf_bb', 'cf_div', 'cf_div_pref', 'cf_debt_rep'}      # payment concepts are tagged positive

def days(a, b): return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days

def index(facts):
    """{concept: [(start, end, dims, value)]} for undimensioned facts, plus the dimensional list."""
    und, dim = {}, []
    for c, v, st, en, d, u, dec in facts:
        if d: dim.append((c, v, st, en, tuple(tuple(x) for x in d)))
        else: und.setdefault(c, []).append((st, en, v))
    return und, dim

def pick(und, key, st, en):
    for rx in COMP[key]:
        for c in und:
            if rx.search(c):
                for s, e, v in und[c]:
                    if e == en and s == st: return v, c
    return None, None

def scale(key, v):
    if v is None: return None
    if key in ('eps_b', 'eps_d', 'dps'): return v
    return v / 1e6

def fy_start(end): return f'{end[:4]}-01-01'

def per_filing(o):
    facts = xinst.filing_facts(o)
    if not facts: return None
    und, dim = index(facts)
    end = o['report']; y = int(end[:4]); q = int(end[5:7]) // 3
    qs = (dt.date.fromisoformat(end).replace(day=1) - dt.timedelta(days=62)).replace(day=1).isoformat()
    r = {'end': end, 'form': o['form'], 'filed': o['date'], 'acc': o['acc'], 'url': url(o), 'q': q, 'y': y, 'x': {}, 'ytd': {}, 'used': {}}
    starts = sorted({s for c in und for s, e, v in und[c] if s and e == end})
    q_st = [s for s in starts if 80 <= days(s, end) <= 100]
    y_st = [s for s in starts if days(s, end) > 100 or (q == 1 and 80 <= days(s, end) <= 100)]
    ytd0 = fy_start(end)
    def get(key, st):
        v, c = pick(und, key, st, end)
        if c: r['used'][key] = c
        return v
    qst = q_st[0] if q_st else None
    for k in DUR_IS + PS:
        if o['form'] == '10-Q' and qst: r['x'][k] = scale(k, get(k, qst))
        r['ytd'][k] = scale(k, get(k, ytd0))
    for k in DUR_CF:
        v = scale(k, get(k, ytd0))
        if v is not None and k in CF_NEG: v = -abs(v)
        r['ytd'][k] = v
    for k in INST:
        v, c = pick(und, k, None, end)
        if c: r['used'][k] = c
        r['x'][k] = scale(k, v)
    # beginning cash: instant at the prior fiscal year end
    pye = f'{y - 1}-12-31'
    v, c = pick(und, 'cf_cash', None, pye); r['x']['cf_cash_beg'] = scale('cf_cash', v)
    # two-class EPS (2009-2023 tagged by class only): basic shares = A + B + C; diluted = Class A diluted (assumes conversion of
    # Class B) + Class C diluted; EPS = Class C (GOOG) where it exists, else Class A
    def cls(concept, st):
        out = {}
        for c, v, s0, e0, d in dim:
            if c == concept and s0 == st and e0 == end and len(d) == 1 and d[0][0] == 'StatementClassOfStockAxis': out[d[0][1]] = v
        return out
    for tgt, st in (('x', qst), ('ytd', ytd0)):
        if st is None or (tgt == 'x' and o['form'] != '10-Q'): continue
        b = cls('WeightedAverageNumberOfSharesOutstandingBasic', st); dl = cls('WeightedAverageNumberOfDilutedSharesOutstanding', st)
        if r[tgt].get('sh_b') is None and b:
            r[tgt]['sh_b'] = sum(v for k, v in b.items() if k in ('CommonClassAMember', 'CommonClassBMember', 'CapitalClassCMember', 'CommonClassCMember')) / 1e6
        if r[tgt].get('sh_d') is None and dl:
            r[tgt]['sh_d'] = sum(v for k, v in dl.items() if k in ('CommonClassAMember', 'CapitalClassCMember', 'CommonClassCMember')) / 1e6
        for k, cc in (('eps_d', 'EarningsPerShareDiluted'), ('eps_b', 'EarningsPerShareBasic')):
            e = cls(cc, st)
            if r[tgt].get(k) is None and e:
                r[tgt][k] = e.get('CommonClassAMember', e.get('CommonClassAandCommonClassBMember', e.get('CapitalClassCMember', e.get('CommonClassCMember'))))
    if r['x'].get('bs_sh') is None:                    # shares outstanding at the period end, by class
        so = {}
        for c, v, s0, e0, d in dim:
            if c in ('CommonStockSharesOutstanding', 'CapitalStockSharesOutstanding') and s0 is None and e0 == end and len(d) == 1 and d[0][0] == 'StatementClassOfStockAxis': so[d[0][1]] = v
        if so: r['x']['bs_sh'] = sum(v for k, v in so.items() if k in ('CommonClassAMember', 'CommonClassBMember', 'CapitalClassCMember', 'CommonClassCMember')) / 1e6
    r['dim'] = dim
    return r

# ---------------------------------------------------------------- dimensional data: latest filing presenting the period
SEGAX = 'StatementBusinessSegmentsAxis'
STREAM = {'GoogleSearchOtherMember': 'search', 'YouTubeAdvertisingRevenueMember': 'youtube', 'GoogleNetworkMember': 'network',
          'GoogleNetworkMembersPropertiesMember': 'network', 'SubscriptionsPlatformsAndDevicesRevenueMember': 'subs', 'OtherRevenuesMember': 'subs',
          'GoogleCloudMember': 'cloud'}
SEGM = {'GoogleServicesMember': 'svc', 'GoogleServicesSegmentMember': 'svc', 'GoogleCloudMember': 'cloud', 'GoogleCloudSegmentMember': 'cloud',
        'AllOtherSegmentsMember': 'ob', 'GoogleInc.Member': 'google', 'GoogleSegmentMember': 'google', 'MobileSegmentMember': 'moto', 'HomeSegmentMember': 'home'}
REVC = ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet')

def pkey_of(st, en):
    d = days(st, en)
    y = int(en[:4]); m = int(en[5:7])
    if 80 <= d <= 100 and m in (3, 6, 9, 12): return f'Q{m // 3}-{str(y)[2:]}'
    if 350 <= d <= 380 and m == 12: return str(y)
    return None

def dims_by_filing():
    """per period: {'streams': (filing date, url, {stream: v}), 'seg_new': ..., 'seg_old': ...} keeping the latest filing for each block."""
    out = {}
    for o in FL:
        if o['form'] not in ('10-K', '10-Q'): continue
        facts = xinst.filing_facts(o)
        if not facts: continue
        blocks = {}
        for c, v, st, en, d, u, dec in facts:
            if not st or not d: continue
            pk = pkey_of(st, en)
            if not pk: continue
            dd = dict((a, b) for a, b in d)
            if c in REVC:
                ps, sg = dd.get('ProductOrServiceAxis'), dd.get(SEGAX)
                other = [a for a in dd if a not in ('ProductOrServiceAxis', SEGAX)]
                if other: continue
                if ps in STREAM and ps != 'GoogleCloudMember' and (sg is None or SEGM.get(sg) in ('svc', 'google')):
                    blocks.setdefault((pk, 'streams'), {})[STREAM[ps]] = v / 1e6
                elif ps == 'GoogleCloudMember' and SEGM.get(sg) == 'google':
                    blocks.setdefault((pk, 'streams'), {})['cloud'] = v / 1e6
                elif ps is None and sg in SEGM:
                    blk = 'seg_new' if SEGM[sg] in ('svc', 'cloud') else ('seg_old' if SEGM[sg] == 'google' else 'seg_x')
                    blocks.setdefault((pk, 'segrev'), {})[SEGM[sg]] = v / 1e6
            elif c == 'OperatingIncomeLoss':
                sg = dd.get(SEGAX); ci = dd.get('ConsolidationItemsAxis')
                other = [a for a in dd if a not in (SEGAX, 'ConsolidationItemsAxis')]
                if other: continue
                if sg in SEGM and ci in (None, 'OperatingSegmentsMember'):
                    blocks.setdefault((pk, 'segoi'), {})[SEGM[sg]] = v / 1e6
                elif sg is None and ci == 'CorporateNonSegmentMember':
                    blocks.setdefault((pk, 'segoi'), {})['alpha'] = v / 1e6
        for (pk, b), vals in blocks.items():
            if b == 'streams' and 'search' not in vals: continue          # old taxonomy ("Google other" incl. Cloud) - not used
            if b in ('segrev', 'segoi'):
                new = {k: v for k, v in vals.items() if k in ('svc', 'cloud', 'ob', 'alpha')}
                old = {k: v for k, v in vals.items() if k in ('google', 'ob', 'moto', 'home', 'alpha')}
                if 'svc' in vals:
                    out.setdefault(pk, {})[b + '_new'] = (o['date'], url(o), new)
                if 'google' in vals or 'moto' in vals:
                    out.setdefault(pk, {})[b + '_old'] = (o['date'], url(o), old)
                continue
            out.setdefault(pk, {})[b] = (o['date'], url(o), vals)
    return out

# ---------------------------------------------------------------- legacy revenue split (MD&A text of the period's own filing)
LEG = [('leg_web', r"^(Google )?(web ?sites|properties|Websites)( \(\d\))*$"), ('leg_net', r"^(Google )?Network( Members.?)? (web ?sites|properties)( ?\(\d\))*$"),
       ('leg_oth', r"^(Other revenues|Google other revenues|Licensing and other revenues)( ?\(\d\))*$"), ('leg_moto', r"^Motorola Mobile( \(hardware and other\))?$"),
       ('leg_ob', r"^Other Bets revenues$")]
def legacy(o):
    """legacy revenue split from the MD&A revenue table of the period's own filing (three-month column of a 10-Q, FY of a 10-K);
    percentage rows are skipped (values must be dollar amounts > 100)."""
    p = glob.glob(os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_*.txt"))
    if not p: return {}
    t = open(p[0]).read().split('\n'); r = {}
    for k, rx in LEG:
        for l in t:
            if re.search(rx, l.split(' | ')[0].strip(), re.I):
                v = pre09.nums(l)
                if o['form'] == '10-Q' and len(v) >= 2 and abs(v[1]) > 100 and '.' not in l.split(' | ')[2]: r[k] = v[1]; break
                if o['form'] == '10-K' and len(v) == 3 and abs(v[2]) > 100 and '.' not in l.split(' | ')[3]:
                    r[k] = v[2] / 1e3 if abs(v[2]) > 2e5 else v[2]; break           # FY2009 10-K tables in USD thousands
    return r

def text_shares(o):
    """weighted shares from the EPS note text when XBRL carries none (FY2009 10-K): Class A + B basic; Class A diluted (incl. B)."""
    p = glob.glob(os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_*.txt"))
    t = open(p[0]).read().split('\n')
    b = [pre09.nums(l) for l in t if re.search(r'^Number of shares used in basic computation', l)]
    d = [pre09.nums(l) for l in t if re.search(r'^Number of shares used in per share computation', l)]
    return (b[-1][-2] + b[-1][-1]) / 1e3, d[-1][-2] / 1e3

def main():
    os.makedirs(OUT, exist_ok=True)
    rel = parse_release.run()
    dims = dims_by_filing()
    recs = {}
    for y in pre09.TENK:
        r = pre09.extract(y)
        recs[str(y)] = {'period': str(y), 'period_end': f'{y}-12-31', 'basis': '10-K text (pre-XBRL)', 'sources': {'filing': r.pop('src')}, 'pre09': r,
                        'filed': pre09.TENK[y][:10]}
    for o in FL:
        if o['form'] not in ('10-K', '10-Q') or o['report'] < '2009-12-31': continue
        f = per_filing(o)
        if not f: continue
        y, q = f['y'], f['q']
        pk = str(y) if o['form'] == '10-K' else f'Q{q}-{str(y)[2:]}'
        if o['form'] == '10-K' and y < 2009: continue
        rec = recs.setdefault(pk, {'period': pk, 'period_end': f['end']})
        if 'xbrl' in rec: continue                  # keep the first (original) filing for the period
        rec['sources'] = {'filing': f['url']}; rec['filed'] = o['date']
        rec['xbrl'] = {'q': f['x'], 'ytd': f['ytd'], 'concepts': f['used']}
        rec['ytd_months'] = q * 3
        rec['legacy'] = legacy(o)
        if o['form'] == '10-K' and f['ytd'].get('sh_b') is None:
            rec['xbrl']['ytd']['sh_b'], rec['xbrl']['ytd']['sh_d'] = text_shares(o); rec['notes'] = 'Weighted shares from the 10-K EPS note text (not tagged in XBRL).'
    for y in range(2013, 2026):
        pk = f'Q4-{str(y)[2:]}'
        recs[pk] = {'period': pk, 'period_end': f'{y}-12-31', 'basis': 'Q4 = fiscal year (10-K) - nine months (Q3 10-Q); EPS from the Q4 release',
                    'sources': {'filing': recs[str(y)]['sources']['filing'], 'nine_months': recs[f'Q3-{str(y)[2:]}']['sources']['filing']}}
    recs = {k: v for k, v in recs.items() if not (k.startswith('Q') and int(k[-2:]) < 13)}
    for pk, rec in recs.items():
        for b, (fd, u, vals) in dims.get(pk, {}).items():
            rec.setdefault('dims', {})[b] = {'values': vals, 'source': u, 'filed': fd}
        if pk in rel:
            rec['release'] = rel[pk]; rec.setdefault('sources', {})['release'] = rel[pk]['url']
    for pk, rec in recs.items():
        json.dump(rec, open(os.path.join(OUT, pk + '.json'), 'w'), indent=1, sort_keys=True)
    # Q4 releases for years before the quarterly columns are not needed; release-only quarters
    print(len(recs), 'periods written')

if __name__ == '__main__':
    main()
