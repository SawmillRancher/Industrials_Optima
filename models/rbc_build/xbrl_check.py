"""Cross-check the normalised RBC data against XBRL company facts as first filed (10-K / 10-Q): net sales, operating income, net
income, diluted EPS and total assets for every period with XBRL (FY2010+), and cash from operations for fiscal years and first
quarters (other quarters are year to date in XBRL). Runs from the committed data/_xbrl.json subset when $RBC_SRC is not available."""
import normalize, xbrl
D = normalize.run()
REV = ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax']
bad, n = [], 0
for p in normalize.periods():
    fy, q = normalize.fyq(p); ann = p.isdigit(); x = D[p]['x']
    for name, cons, key, kind, tol in [('net sales', REV, 'rev', 'FY' if ann else 'Q', 0.15), ('operating income', ['OperatingIncomeLoss'], 'oi', 'FY' if ann else 'Q', 0.15),
                                       ('net income', ['NetIncomeLoss'], 'ni', 'FY' if ann else 'Q', 0.15), ('diluted EPS', ['EarningsPerShareDiluted'], 'eps_d', 'FY' if ann else 'Q', 0.011),
                                       ('total assets', ['Assets'], 'bs_ta', 'I', 0.15)]:
        v = xbrl.first_of(cons, fy, kind, q)
        if v is None or x.get(key) is None: continue
        n += 1
        if abs(v - x[key]) > tol: bad.append(f'{p} {name}: model {x[key]} vs XBRL {v}')
    if ann or q == 1:
        v = xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, 'FY' if ann else 'Q', q)
        if v is not None and x.get('cf_cfo') is not None:
            n += 1
            if abs(v - x['cf_cfo']) > 0.15: bad.append(f'{p} CFO: model {x["cf_cfo"]} vs XBRL {v}')
print('\n'.join(bad) or 'all XBRL cross-checks pass')
print(f'{n} XBRL checks, {len(bad)} differences')
