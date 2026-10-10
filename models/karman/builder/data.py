"""Historical data for the Karman (KRMN) model, USD millions.
Sources: SEC EDGAR XBRL company facts (CIK 0002040127) for the primary statements; earnings releases
(Form 8-K Ex. 99.1) for end-market revenue, Adjusted EBITDA / Adjusted EPS reconciliations and backlog;
IPO prospectus (424B4, 13-Feb-2025) for FY2022-23 end markets, Adj. EBITDA and the 31-Dec-2022 / 30-Sep-2024
balance sheets; 10-Q / 10-K notes for intangible amortization and debt."""
from xbrl import flow, inst

HQ = ['2022', '2023', 'Q1/24', 'Q2/24', 'Q3/24', 'Q4/24', '2024', 'Q1/25', 'Q2/25', 'Q3/25', 'Q4/25', '2025', 'Q1/26', 'Q2/26']
H = {}   # key -> {period: value}


def put(key, vals, periods=None):
    periods = periods or HQ
    d = H.setdefault(key, {})
    for p, v in zip(periods, vals):
        if v is not None:
            d[p] = v


def m(x):
    return None if x is None else round(x / 1e6, 3)


def xf(tag, unit=None, sign=1):
    return {p: (None if flow(tag, p, unit) is None else round(sign * flow(tag, p, unit) / 1e6, 3)) for p in HQ}


# ---------------- End-market revenue (releases; 2024 quarters on the 2025 recast basis) ----------------
put('em_hsmd', [72.296, 100.093, 24.822, 28.741, 26.927, 34.104, 114.594, 30.056, 34.960, 36.608, 48.363, 149.987, 35.688, 43.417])
put('em_sl', [79.664, 94.643, 30.256, 28.512, 27.640, 28.628, 115.036, 33.871, 39.597, 40.697, 35.660, 149.825, 43.854, 42.072])
put('em_tmids', [74.351, 85.969, 27.928, 27.786, 31.401, 28.506, 115.621, 36.197, 40.540, 44.482, 50.469, 171.688, 45.260, 63.012])
put('em_mds', [None] * 12 + [26.408, 33.562])

# ---------------- Income statement (XBRL) ----------------
for k, t in [('rev', 'RevenueFromContractWithCustomerExcludingAssessedTax'), ('cogs', 'CostOfGoodsAndServicesSold'),
             ('ga', 'GeneralAndAdministrativeExpense'), ('opex', 'OperatingExpenses'), ('oi', 'OperatingIncomeLoss'),
             ('int', 'InterestExpenseNonoperating'), ('oth', 'OtherNonoperatingIncomeExpense'),
             ('pbt', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'),
             ('tax', 'IncomeTaxExpenseBenefit'), ('ni', 'NetIncomeLoss')]:
    H[k] = xf(t)
H['da_opex'] = {p: round(H['opex'][p] - H['ga'][p], 3) for p in HQ}
# Q1/25 revenue: 100.124 per IS (end-market table total printed 100.128 in the Q1-25 release)
# shares (m) and EPS
H['sh_b'] = {p: (None if flow('WeightedAverageNumberOfSharesOutstandingBasic', p, 'shares') in (None, 0) else round(flow('WeightedAverageNumberOfSharesOutstandingBasic', p, 'shares') / 1e6, 3)) for p in HQ}
H['sh_d'] = {p: (None if flow('WeightedAverageNumberOfDilutedSharesOutstanding', p, 'shares') in (None, 0) else round(flow('WeightedAverageNumberOfDilutedSharesOutstanding', p, 'shares') / 1e6, 3)) for p in HQ}
for k in ('sh_b', 'sh_d'):
    H[k]['Q4/24'] = 166.737   # FY25 release, three months ended 31-Dec-2024 (units)
    H[k]['Q4/25'] = 132.322   # FY25 release, three months ended 31-Dec-2025
H['sh_b']['Q1/26'] = 132.526; H['sh_d']['Q1/26'] = 132.526
H['eps'] = {p: flow('EarningsPerShareDiluted', p, 'USD/shares') for p in HQ}
H['eps']['Q4/24'] = 0.01; H['eps']['Q4/25'] = 0.06

# ---------------- D&A detail ----------------
# Total D&A per Adj. EBITDA reconciliations (= CF statement D&A)
put('da', [34.982, 27.179, 7.350, 8.306, 8.136, 9.168, 32.959, 8.869, 10.307, 10.970, 12.591, 42.737, 16.632, 15.176])
# Amortization of acquired intangibles (10-Q / 10-K intangible-asset notes; Q4 = FY - 9M)
put('amort', [24.856, 14.406, 3.9, 4.4, 4.3, 4.3, 16.9, 4.4, 5.5, 6.0, 7.3, 23.2, 10.9, 9.2])
H['rou'] = xf('FinanceLeaseRightOfUseAssetAmortization')
put('da_cogs', [4.5, 6.7, 1.9, 2.0, 2.9, 2.0, 8.8, 2.7, 2.8, 2.8, 3.0, 11.3, 2.9, 3.1])

# ---------------- Adjusted EBITDA reconciliation (releases / prospectus) ----------------
put('adj_trans', [0.251, 0.356, 2.011, 0.079, 1.074, 1.612, 4.776, 1.962, 3.904, 3.533, 3.342, 12.741, 2.263, 1.392])
put('adj_integ', [3.507, 2.739, 0.416, 0.476, 0.849, 0.514, 2.255, 0.261, 0.380, 0.559, 1.079, 2.279, 1.410, 1.940])
put('adj_lender', [0.0, 0.5, 0.0, 0.0, 0.0, 0.1, 0.1, 1.260, 0.206, 0.0, 0.106, 1.572, 0.735, 0.045])
put('adj_sbc', [1.603, 1.291, 0.251, 0.246, 0.248, 0.248, 0.993, 8.084, 0.0, 0.0, 0.0, 8.084, 0.0, 1.444])
put('adj_other', [-0.281, 0.739, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 0.0, 0.8, 2.468, 0.034])
put('ebitda_pub', [55.211, 76.237, 21.619, 26.623, 25.894, 23.885, 98.020, 18.752, 30.791, 32.833, 37.450, 119.826, 37.910, 49.725])
put('adjebitda_pub', [60.291, 81.863, 24.297, 27.424, 28.065, 26.359, 106.144, 30.319, 35.281, 37.725, 41.977, 145.302, 44.786, 54.580])
# Adjusted EPS (published; per unit pre-IPO)
put('adjeps_pub', [None, None, 0.03, 0.03, 0.04, 0.03, 0.13, 0.05, 0.10, 0.10, 0.11, 0.37, 0.11, 0.14])
# Non-EBITDA non-recurring items in Adj. EPS 'other non-recurring costs' (FY25 release fn. 7)
put('adj_debtwo', [None] * 8 + [2.5, None, None, 2.5, None, None])   # write-off of TCW term-loan issuance costs (interest exp.)
put('adj_taxdisc', [None] * 10 + [1.5, 1.5, None, None])            # one-time tax expense, change in entity tax status

# ---------------- Backlog (funded backlog to FY24; 'backlog' from FY25 - same basis) ----------------
put('backlog', [265.321, 428.719, None, None, 550.603, 579.8, 579.8, 636.350, 719.3, 758.2, 801.1, 801.1, 1026.903, 1322.124])
# Incremental revenue from acquisitions where disclosed / derivable
put('acq_rev', [None, None, None, None, None, None, 11.692, None, None, None, None, None, None, 38.882])

# ---------------- Cash flow (XBRL; quarters derived from YTD) ----------------
cf = {}
cf['cf_ni'] = H['ni']
cf['cf_da'] = H['da']
cf['cf_sbc'] = H['adj_sbc']
cf['cf_fin'] = xf('AmortizationOfFinancingCosts')
cf['cf_dtax'] = xf('DeferredIncomeTaxExpenseBenefit')
cf['cfo'] = xf('NetCashProvidedByUsedInOperatingActivities')
cf['capex'] = xf('PaymentsToAcquirePropertyPlantAndEquipment', sign=-1)
cf['acq'] = xf('PaymentsToAcquireBusinessesNetOfCashAcquired', sign=-1)
cf['cfi'] = xf('NetCashProvidedByUsedInInvestingActivities')
pn = xf('ProceedsFromNotesPayable'); pl = xf('ProceedsFromLinesOfCredit')
rn = xf('RepaymentsOfNotesPayable'); rl = xf('RepaymentsOfLinesOfCredit'); ra = xf('RepaymentsOfAssumedDebt')
cf['lease_prin'] = xf('FinanceLeasePrincipalPayments', sign=-1)
cf['dic'] = xf('PaymentsOfDebtIssuanceCosts', sign=-1)
cf['ipo'] = xf('ProceedsFromIssuanceInitialPublicOffering')
cf['cff'] = xf('NetCashProvidedByUsedInFinancingActivities')
cf['dcash'] = xf('CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect')
for p in HQ:
    z = lambda d: d.get(p) or 0
    if cf['cfo'].get(p) is None:
        continue
    cf.setdefault('borrow', {})[p] = round(z(pn) + z(pl), 3)
    cf.setdefault('repay', {})[p] = round(-(z(rn) + z(rl) + z(ra)), 3)
    if (pn.get(p) is None and pl.get(p) is None):
        cf['borrow'][p] = None
    cf.setdefault('cff_oth', {})[p] = round(z(cf['cff']) - (z(cf['borrow']) + z(cf['repay']) + z(cf['lease_prin']) + z(cf['dic']) + z(cf['ipo'])), 3)
    cf.setdefault('cfi_oth', {})[p] = round(z(cf['cfi']) - z(cf['capex']) - z(cf['acq']), 3)
    cf.setdefault('wc', {})[p] = round(z(cf['cfo']) - z(cf['cf_ni']) - z(cf['cf_da']) - z(cf['cf_sbc']) - z(cf['cf_fin']) - z(cf['cf_dtax']), 3)
H.update(cf)
# Cash (incl. restricted) balances
cash_tag = 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations'

# ---------------- Balance sheet ----------------
BSP = ['2022', '2023', 'Q3/24', '2024', 'Q1/25', 'Q2/25', 'Q3/25', '2025', 'Q1/26', 'Q2/26']


def bs(tag):
    return {p: m(inst(tag, p)) for p in BSP if inst(tag, p) is not None}


H['bs_cash'] = bs(cash_tag)
H['bs_ar'] = bs('AccountsReceivableNetCurrent')
H['bs_ca'] = bs('ContractWithCustomerAssetNetCurrent')
H['bs_inv'] = bs('InventoryNet')
H['bs_pre'] = bs('PrepaidExpenseAndOtherAssetsCurrent')
H['bs_tca'] = bs('AssetsCurrent')
H['bs_ppe'] = bs('PropertyPlantAndEquipmentNet')
H['bs_gw'] = bs('Goodwill')
H['bs_int'] = bs('IntangibleAssetsNetExcludingGoodwill')
H['bs_orou'] = bs('OperatingLeaseRightOfUseAsset')
H['bs_frou'] = bs('FinanceLeaseRightOfUseAsset')
H['bs_ta'] = bs('Assets')
H['bs_ap'] = bs('AccountsPayableCurrent')
H['bs_pay'] = bs('EmployeeRelatedLiabilitiesCurrent')
H['bs_cl'] = bs('ContractWithCustomerLiabilityCurrent')
H['bs_oll_c'] = bs('OperatingLeaseLiabilityCurrent')
H['bs_fll_c'] = bs('FinanceLeaseLiabilityCurrent')
H['bs_debt_c'] = bs('NotesPayableCurrent')
H['bs_taxp'] = bs('AccruedIncomeTaxesCurrent')
H['bs_tcl'] = bs('LiabilitiesCurrent')
H['bs_rev'] = bs('LongTermLineOfCredit')
H['bs_debt_lt'] = bs('LongTermNotesPayable')
H['bs_oll_lt'] = bs('OperatingLeaseLiabilityNoncurrent')
H['bs_fll_lt'] = bs('FinanceLeaseLiabilityNoncurrent')
H['bs_oltl'] = bs('OtherLiabilitiesNoncurrent')
H['bs_dtl'] = bs('DeferredIncomeTaxLiabilitiesNet')
H['bs_tl'] = bs('Liabilities')
H['bs_apic'] = bs('AdditionalPaidInCapital')
H['bs_cs'] = bs('CommonStockValue')
H['bs_re'] = bs('RetainedEarningsAccumulatedDeficit')
H['bs_aoci'] = bs('AccumulatedOtherComprehensiveIncomeLossNetOfTax')
H['bs_eq'] = bs('StockholdersEquity')
H['bs_shares'] = {p: round(inst('CommonStockSharesOutstanding', p, 'shares') / 1e6, 6) for p in BSP if inst('CommonStockSharesOutstanding', p, 'shares')}

# 31-Dec-2022 and 30-Sep-2024 balance sheets from the IPO prospectus (424B4)
pros = {
    '2022': dict(bs_cash=6.626, bs_ar=47.594, bs_ca=61.319, bs_inv=0.0, bs_pre=4.193, bs_tca=119.733, bs_ppe=50.985, bs_gw=217.273,
                 bs_int=221.963, bs_orou=4.548, bs_frou=66.320, bs_oa=1.772, bs_ta=682.593, bs_ap=12.920, bs_pay=5.777, bs_cl=16.069,
                 bs_oll_c=1.393, bs_fll_c=4.598, bs_debt_c=6.265, bs_taxp=2.414, bs_ocl=8.868, bs_tcl=58.304, bs_rev=16.5,
                 bs_debt_lt=303.737, bs_oll_lt=0.524, bs_fll_lt=70.562, bs_oltl=7.781, bs_dtl=47.588, bs_tl=504.996, bs_eq=177.597),
    'Q3/24': dict(bs_cash=7.671, bs_ar=56.508, bs_ca=101.322, bs_inv=0.0, bs_pre=8.313, bs_tca=173.814, bs_ppe=59.360, bs_gw=225.146,
                  bs_int=213.254, bs_orou=5.996, bs_frou=69.741, bs_oa=1.164, bs_ta=748.474, bs_ap=26.160, bs_pay=6.524, bs_cl=27.192,
                  bs_oll_c=1.325, bs_fll_c=3.634, bs_debt_c=6.265, bs_taxp=18.348, bs_ocl=3.537, bs_tcl=92.985, bs_rev=20.0,
                  bs_debt_lt=328.772, bs_oll_lt=5.475, bs_fll_lt=77.261, bs_oltl=1.686, bs_dtl=28.189, bs_tl=554.367, bs_eq=194.106),
}
# 2023 prospectus split prepaid 12.458 (inventory folded into prepaid & other in the prospectus); use 10-K presentation
for p, d in pros.items():
    for k, v in d.items():
        H.setdefault(k, {})[p] = v
# residual lines so every balance sheet ties
for p in BSP:
    g = lambda k: H.get(k, {}).get(p) or 0
    if p not in H['bs_ta']:
        continue
    if p not in pros:
        H.setdefault('bs_oa', {})[p] = round(g('bs_ta') - g('bs_tca') - g('bs_ppe') - g('bs_gw') - g('bs_int') - g('bs_orou') - g('bs_frou'), 3)
        H.setdefault('bs_ocl', {})[p] = round(g('bs_tcl') - g('bs_ap') - g('bs_pay') - g('bs_cl') - g('bs_oll_c') - g('bs_fll_c') - g('bs_debt_c') - g('bs_taxp'), 3)
    H.setdefault('bs_pre2', {})[p] = round(g('bs_tca') - g('bs_cash') - g('bs_ar') - g('bs_ca') - g('bs_inv'), 3)
    H.setdefault('bs_oltl2', {})[p] = round(g('bs_tl') - g('bs_tcl') - g('bs_rev') - g('bs_debt_lt') - g('bs_oll_lt') - g('bs_fll_lt') - g('bs_dtl'), 3)
    # equity split: paid-in (members' equity pre-IPO) vs retained earnings
    if p in H['bs_re']:
        H.setdefault('bs_pic', {})[p] = round(g('bs_cs') + g('bs_apic'), 3)
    else:
        H.setdefault('bs_pic', {})[p] = g('bs_eq')
        H['bs_re'][p] = 0.0
        H['bs_aoci'][p] = 0.0
for p in BSP:
    if p in H['bs_aoci'] and H['bs_aoci'][p] is None:
        H['bs_aoci'][p] = 0.0
# Term-loan principal (debt note) and other notes
put('tl_principal', [None, 308.7, None, None, None, None, 326.662, None, 375.0, 374.1, 502.8, 502.8, 769.8, 763.962])

if __name__ == '__main__':
    for k, v in H.items():
        print(k.ljust(14), {p: v.get(p) for p in v})
