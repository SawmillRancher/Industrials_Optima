"""EDGAR XBRL company facts (us-gaap, S&P Global Inc., CIK 64040) -> values by fiscal period (calendar fiscal year).

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value. Values in USD millions (shares in millions; per-share as filed)."""
import json, os, datetime as dt
S = os.environ.get('SPGI_SRC', '/tmp/spgi_src')
CIK = '64040'
_F = None
USED = ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'CostOfRevenue', 'SellingGeneralAndAdministrativeExpense', 'Depreciation',
        'AmortizationOfIntangibleAssets', 'CostsAndExpenses', 'OperatingIncomeLoss', 'IncomeLossFromEquityMethodInvestments',
        'OtherNonoperatingIncomeExpense', 'InterestExpense', 'InterestExpenseNonoperating', 'InterestIncomeExpenseNonoperatingNet',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest', 'IncomeTaxExpenseBenefit',
        'IncomeLossFromContinuingOperations', 'IncomeLossFromDiscontinuedOperationsNetOfTax', 'IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity',
        'ProfitLoss', 'NetIncomeLoss', 'NetIncomeLossAttributableToNoncontrollingInterest', 'MinorityInterestInNetIncomeLossOfConsolidatedEntities',
        'IncomeLossFromContinuingOperationsAttributableToNoncontrollingEntity', 'NetIncomeLossAttributableToRedeemableNoncontrollingInterest',
        'IncomeLossFromContinuingOperationsPerDilutedShare', 'EarningsPerShareBasic', 'EarningsPerShareDiluted',
        'WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'CommonStockDividendsPerShareDeclared',
        'ShareBasedCompensation', 'DeferredIncomeTaxExpenseBenefit', 'NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInInvestingActivities',
        'NetCashProvidedByUsedInFinancingActivities', 'PaymentsToAcquireProductiveAssets', 'PaymentsToAcquireBusinessesNetOfCashAcquired',
        'PaymentsForRepurchaseOfCommonStock', 'PaymentsOfDividendsCommonStock', 'PaymentsOfDividendsMinorityInterest',
        'CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 'AccountsReceivableNetCurrent',
        'AssetsCurrent', 'PropertyPlantAndEquipmentNet', 'OperatingLeaseRightOfUseAsset', 'Goodwill', 'IntangibleAssetsNetExcludingGoodwill', 'Assets',
        'AccountsPayableCurrent', 'ShortTermBorrowings', 'DebtCurrent', 'ContractWithCustomerLiabilityCurrent', 'DeferredRevenueCurrent', 'LiabilitiesCurrent',
        'LongTermDebtNoncurrent', 'Liabilities', 'RedeemableNoncontrollingInterestEquityCarryingAmount', 'StockholdersEquity', 'MinorityInterest',
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 'LiabilitiesAndStockholdersEquity', 'CommonStockSharesOutstanding',
        'CommonStockSharesIssued', 'TreasuryStockCommonShares', 'TreasuryStockShares',
        'FiniteLivedIntangibleAssetsAmortizationExpenseNextTwelveMonths', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearTwo',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearThree', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearFour',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearFive', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths',
        'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree',
        'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive',
        'LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive', 'StockRepurchasedDuringPeriodShares',
        'AccruedIncomeTaxesCurrent', 'CashProvidedByUsedInFinancingActivitiesDiscontinuedOperations', 'CashProvidedByUsedInInvestingActivitiesDiscontinuedOperations', 'CashProvidedByUsedInOperatingActivitiesDiscontinuedOperations', 'DeferredIncomeTaxLiabilitiesNet', 'EffectOfExchangeRateOnCashAndCashEquivalents', 'EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 'EmployeeRelatedLiabilitiesCurrent', 'EquityMethodInvestments', 'InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures', 'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations', 'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations', 'OperatingLeaseLiabilityNoncurrent', 'ProceedsFromDivestitureOfBusinesses', 'ProceedsFromDivestitureOfBusinessesNetOfCashDivested']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')

def dump_subset():
    """write the concepts used by the model (10-K / 10-Q facts only) to data/_xbrl.json so the build runs without the raw downloads."""
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in ('10-K', '10-Q', '10-K/A', '10-Q/A')] for k in USED}
    raw = json.load(open(os.path.join(S, f'cf_{CIK}.json')))['facts']['dei']['EntityCommonStockSharesOutstanding']['units']['shares']
    out['_dei_shares'] = [{a: f[a] for a in keep if a in f} for f in raw]
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and not os.path.exists(raw) and os.path.exists(SUBSET):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts'].get('us-gaap', {})
        for k, v in d.items():
            for u, fs in v['units'].items():
                _F.setdefault(k, []).extend(fs)
    return _F

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

def value(concept, fy, kind, q=None, pick='first'):
    """kind: 'FY' | 'Q' | 'YTD' (q: 1->Q, 2->H, 3->9M, 4->FY) | 'I' (instant at quarter q end; q=4 -> FY end)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A'): continue
        if dur(f) != want: continue
        e = dt.date.fromisoformat(f['end'])
        if e.year != fy or (e.month + 2) // 3 != qq: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    if 'PerShare' in concept or concept.startswith('EarningsPerShare'): return v
    return v / 1e6

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
