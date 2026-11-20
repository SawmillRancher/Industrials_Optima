"""EDGAR XBRL company facts (us-gaap, Northrop Grumman Corporation, CIK 1133421) -> values by fiscal period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. Calendar fiscal year (FY = calendar year).
pick='first' returns the value as originally filed (10-K / 10-Q only), pick='last' the latest (restated) value.
Values are returned in USD millions (shares in millions; per-share and ratios as filed)."""
import json, os, datetime as dt
S = os.environ.get('NOC_SRC', '/tmp/noc_src')
CIK = '1133421'
_F = None
USED = ['Revenues', 'SalesRevenueNet', 'SalesRevenueGoodsNet', 'SalesRevenueServicesNet', 'CostOfGoodsSold', 'CostOfServices',
        'CostOfGoodsAndServicesSold', 'CostOfRevenue', 'GeneralAndAdministrativeExpense', 'OperatingIncomeLoss', 'InterestAndDebtExpense',
        'OtherNonoperatingIncomeExpense', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
        'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments', 'IncomeTaxExpenseBenefit',
        'IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest', 'IncomeLossFromContinuingOperations',
        'IncomeLossFromDiscontinuedOperationsNetOfTax', 'IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity', 'NetIncomeLoss',
        'EarningsPerShareBasic', 'EarningsPerShareDiluted', 'IncomeLossFromContinuingOperationsPerBasicShare', 'IncomeLossFromContinuingOperationsPerDilutedShare',
        'WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'CommonStockDividendsPerShareDeclared',
        'DefinedBenefitPlanNetPeriodicBenefitCost', 'NetPeriodicDefinedBenefitsExpenseReversalOfExpenseExcludingServiceCostComponent',
        'DefinedBenefitPlanActuarialGainLossImmediateRecognitionAsComponentInNetPeriodicBenefitCostCredit', 'GainLossOnSaleOfBusiness',
        'DepreciationDepletionAndAmortization', 'Depreciation', 'AdjustmentForAmortization', 'AmortizationOfIntangibleAssets', 'ShareBasedCompensation',
        'AllocatedShareBasedCompensationExpense', 'DeferredIncomeTaxesAndTaxCredits', 'DeferredIncomeTaxExpenseBenefit', 'IncreaseDecreaseInDeferredIncomeTaxes',
        'PensionAndOtherPostretirementBenefitsExpenseReversalOfExpenseNoncash', 'PensionAndOtherPostretirementBenefitContributions', 'PensionContributions',
        'IncreaseDecreaseInPensionAndPostretirementObligations', 'OtherNoncashIncomeExpense', 'ExcessTaxBenefitFromShareBasedCompensationOperatingActivities',
        'NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations',
        'CashProvidedByUsedInOperatingActivitiesDiscontinuedOperations', 'PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireBusinessesNetOfCashAcquired',
        'ProceedsFromDivestitureOfBusinessesNetOfCashDivested', 'ProceedsFromDivestitureOfBusinesses', 'NetCashProvidedByUsedInInvestingActivities',
        'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations', 'CashProvidedByUsedInInvestingActivitiesDiscontinuedOperations',
        'ProceedsFromIssuanceOfLongTermDebt', 'RepaymentsOfLongTermDebt', 'RepaymentsOfLongTermDebtAndCapitalSecurities', 'ProceedsFromRepaymentsOfShortTermDebt',
        'PaymentsOfDividendsCommonStock', 'PaymentsForRepurchaseOfCommonStock', 'ProceedsFromIssuanceOrSaleOfEquity', 'ProceedsFromStockOptionsExercised',
        'PaymentsRelatedToTaxWithholdingForShareBasedCompensation', 'NetCashProvidedByUsedInFinancingActivities', 'CashAndCashEquivalentsPeriodIncreaseDecrease',
        'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
        'CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
        'AccountsReceivableNetCurrent', 'ReceivablesLongTermContractsOrPrograms', 'UnbilledReceivablesCurrent', 'ContractWithCustomerAssetNetCurrent',
        'InventoryNet', 'InventoryForLongTermContractsOrPrograms', 'InventoryNetOfAllowancesCustomerAdvancesAndProgressBillings', 'OtherAssetsCurrent',
        'PrepaidExpenseAndOtherAssetsCurrent', 'IncomeTaxReceivable', 'AssetsCurrent', 'PropertyPlantAndEquipmentNet', 'OperatingLeaseRightOfUseAsset',
        'Goodwill', 'IntangibleAssetsNetExcludingGoodwill', 'DeferredIncomeTaxAssetsNet', 'DefinedBenefitPlanAssetsForPlanBenefitsNoncurrent', 'OtherAssetsNoncurrent',
        'Assets', 'AccountsPayableCurrent', 'EmployeeRelatedLiabilitiesCurrent', 'ContractWithCustomerLiabilityCurrent', 'OtherLiabilitiesCurrent',
        'LongTermDebtCurrent', 'LongTermDebtAndCapitalLeaseObligationsCurrent', 'NotesPayableCurrent', 'LiabilitiesCurrent', 'LongTermDebtNoncurrent',
        'LongTermDebtAndCapitalLeaseObligations', 'LongTermDebt', 'PensionAndOtherPostretirementDefinedBenefitPlansLiabilitiesNoncurrent',
        'OperatingLeaseLiabilityNoncurrent', 'DeferredIncomeTaxLiabilities', 'DeferredTaxAndOtherLiabilitiesNoncurrent', 'DeferredTaxLiabilitiesNoncurrent',
        'OtherLiabilitiesNoncurrent', 'Liabilities', 'StockholdersEquity', 'MinorityInterest', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
        'LiabilitiesAndStockholdersEquity', 'CommonStockSharesOutstanding', 'CommonStockSharesIssued', 'TreasuryStockShares', 'RevenueRemainingPerformanceObligation',
        'FiniteLivedIntangibleAssetsAmortizationExpenseNextTwelveMonths', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearTwo',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearThree', 'FiniteLivedIntangibleAssetsAmortizationExpenseYearFour',
        'FiniteLivedIntangibleAssetsAmortizationExpenseYearFive', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths',
        'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearThree',
        'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFour', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInYearFive',
        'LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive', 'StockRepurchasedAndRetiredDuringPeriodShares', 'EffectiveIncomeTaxRateContinuingOperations',
        'IncrementalCommonSharesAttributableToShareBasedPaymentArrangements']
DEI = ['EntityCommonStockSharesOutstanding']
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
FORMS = ('10-K', '10-Q', '10-K/A', '10-Q/A')

def dump_subset():
    """write the concepts used by the model (10-K / 10-Q facts only) to data/_xbrl.json so the build runs without the raw downloads."""
    keep = ('start', 'end', 'val', 'filed', 'form', 'fp', 'frame')
    F = facts()
    out = {k: [{a: f[a] for a in keep if a in f} for f in F.get(k, []) if f.get('form') in FORMS] for k in USED + DEI if k in F}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts']
        for tax in ('us-gaap', 'dei'):
            for k, v in d.get(tax, {}).items():
                for u, fs in v['units'].items():
                    _F.setdefault(k, []).extend(fs)
    return _F

def fy_of(end): return dt.date.fromisoformat(end).year

def qtr_of(end):
    return {3: 1, 6: 2, 9: 3, 12: 4}.get(dt.date.fromisoformat(end).month)

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if 80 <= d < 100 else 'H' if 170 <= d < 190 else '9M' if 260 <= d < 280 else 'FY' if 350 <= d < 380 else None

def scale(concept, v):
    if concept in ('EffectiveIncomeTaxRateContinuingOperations',) or 'PerShare' in concept or 'PerDilutedShare' in concept or 'PerBasicShare' in concept: return v
    return v / 1e6

def value(concept, fy, kind, q=None, pick='first', raw=False):
    """kind: 'FY' | 'Q' | 'YTD' (q months-to-date: 1->Q, 2->H, 3->9M, 4->FY) | 'I' (instant at quarter q end, q=4 -> FY end)."""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in FORMS: continue
        if dur(f) != want: continue
        if fy_of(f['end']) != fy or qtr_of(f['end']) != qq: continue
        key = (f['filed'], f.get('accn', ''))
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f)
    if best is None: return None
    f = best[1]
    if raw: return f
    return scale(concept, f['val'])

def first_of(concepts, *a, **k):
    """earliest-filed fact across the candidate concepts (so a concept introduced in a later, recast filing does not win)"""
    best = None
    for c in concepts:
        f = value(c, *a, raw=True, **k)
        if f is None: continue
        key = (f['filed'], f.get('accn', ''))
        if best is None or key < best[0]: best = (key, scale(c, f['val']))
    return None if best is None else best[1]

def series(concept, fy, kind, q=None):
    """all filed values (first and later) of a fact, for restatement checks: [(filed, val)]"""
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    out = []
    for f in facts().get(concept, []):
        if f.get('form') not in FORMS or dur(f) != want: continue
        if fy_of(f['end']) != fy or qtr_of(f['end']) != qq: continue
        out.append((f['filed'], scale(concept, f['val'])))
    return sorted(out)
