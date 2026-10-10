"""Curated non-GAAP and supplementary history for Cintas, hand-assembled from the
EDGAR earnings releases (8-K Ex.99), 10-Ks and 10-Qs. All per-share data are
restated for the 4-for-1 split (Sep-2024): pre-FY2025 published values / 4.
USD millions unless stated."""

SPLIT = 4.0

# ---- Company-published adjusted / "excluding items" diluted EPS (as published, pre-split $) ----
# value, source release, definition text
ADJ_EPS_RAW = {
    'FY2009':   (1.83, '2009-07-16', 'EPS excl. restructuring, impairment & inventory valuation charge'),
    'FY2010':   (1.49, '2010-07-22', 'EPS excl. legal settlements & restructuring/impairment charges'),
    'FY2011':   (1.68, '2011-07-19', 'EPS excl. charges (none in FY2011)'),
    'FY2014Q4': (0.76, '2014-07-15', 'EPS adjusted for the Shred-it Transaction'),
    'FY2014':   (2.79, '2014-07-15', 'EPS adjusted for the Shred-it Transaction'),
    'FY2015Q1': (0.78, '2015-09-24', 'EPS cont. ops excl. $0.11 equity-method gain (and $0.04 Shred-it proceeds gain)'),
    'FY2015Q3': (0.85, '2015-03-18', 'EPS excl. Shred-it impact & discontinued operations'),
    'FY2015Q4': (0.86, '2015-07-16', 'EPS excl. disc. ops, Shred-it investment income/loss & certain other impacts'),
    'FY2015':   (3.35, '2015-07-16', 'EPS excl. disc. ops, Shred-it investment income/loss & certain other impacts'),
    'FY2017Q1': (1.26, '2017-09-26', 'EPS cont. ops excl. G&K transaction expenses (comparative)'),
    'FY2017Q2': (1.14, '2017-12-21', 'EPS cont. ops excl. G&K transaction expenses (comparative)'),
    'FY2017Q3': (1.11, '2017-03-22', 'EPS cont. ops excl. G&K expenses and ASU 2016-09 benefit'),
    'FY2017Q4': (1.25, '2018-07-19', 'EPS cont. ops excl. G&K transaction & integration expenses'),
    'FY2017':   (4.77, '2017-07-20', 'EPS cont. ops excl. G&K transaction & integration expenses'),
    'FY2018Q1': (1.48, '2017-09-26', 'EPS cont. ops excl. G&K expenses'),
    'FY2018Q2': (1.31, '2017-12-21', 'EPS cont. ops excl. G&K expenses'),
    'FY2018Q3': (1.37, '2018-03-22', 'EPS cont. ops excl. G&K, one-time employee payment, Tax Act benefit'),
    'FY2018Q4': (1.77, '2018-07-19', 'EPS cont. ops excl. G&K expenses'),
    'FY2018':   (5.94, '2018-09-25', 'EPS cont. ops excl. G&K, one-time employee payment, Tax Act benefit'),
    'FY2019Q1': (1.93, '2018-09-25', 'EPS cont. ops excl. G&K integration expenses'),
    'FY2019Q2': (1.76, '2018-12-20', 'EPS cont. ops excl. G&K & gain on cost-method investment'),
    'FY2019Q3': (1.84, '2019-03-21', 'EPS cont. ops excl. G&K integration expenses'),
    'FY2019Q4': (2.07, '2019-07-16', 'EPS cont. ops excl. G&K integration expenses'),
    'FY2019':   (7.60, '2019-07-16', 'EPS cont. ops excl. G&K & gain on sale of investment'),
    'FY2020Q1': (2.32, '2019-09-24', 'EPS cont. ops excl. G&K integration expenses (nil)'),
    'FY2020Q2': (2.27, '2019-12-17', 'EPS cont. ops excl. items (nil)'),
    'FY2020Q3': (2.16, '2020-03-19', 'EPS cont. ops excl. items (nil)'),
    'FY2020Q4': (1.35, '2020-07-23', 'EPS cont. ops excl. items (nil)'),
    'FY2020':   (8.11, '2020-07-23', 'EPS cont. ops excl. items (nil)'),
    'FY2021Q2': (2.37, '2021-12-22', 'Diluted EPS excl. gain on sale of operating assets (comparative)'),
    'FY2022Q1': (3.02, '2022-09-28', 'Diluted EPS excl. gain on sale of operating assets'),
    'FY2022Q2': (2.76, '2021-12-22', 'Diluted EPS excl. items (nil)'),
    'FY2022Q3': (2.69, '2022-03-23', 'Diluted EPS excl. equity-method investment gain & related tax benefit'),
    'FY2022':   (11.28, '2022-07-14', 'Diluted EPS excl. Q1 operating-asset gain & Q3 equity-method gain'),
    'FY2026Q4': (1.29, '2026-07-15', 'Adjusted diluted EPS excl. UniFirst transaction expenses'),
    'FY2026':   (4.94, '2026-07-15', 'Adjusted diluted EPS excl. UniFirst transaction expenses'),
    'FY2027Q1': (1.39, '2026-09-23', 'Adjusted diluted EPS excl. UniFirst transaction expenses'),
}

def adj_eps(period):
    if period not in ADJ_EPS_RAW:
        return None
    v, src, _ = ADJ_EPS_RAW[period]
    fy = int(period[2:6])
    return v / SPLIT if (src < '2024-09-25') else v

# ---- Company-published EBITDA (Debt/EBITDA computation; NI + gross interest expense + taxes + D&A) ----
EBITDA_PUB = {
    'FY2012': 735.734, 'FY2013': 754.997, 'FY2014': 864.542,
    'FY2013Q1': 185.813, 'FY2013Q2': 186.024, 'FY2013Q3': 180.987, 'FY2013Q4': 202.173,
    'FY2014Q1': 188.532, 'FY2014Q2': 201.583, 'FY2014Q3': 198.570,
}

# ---- Company-published free cash flow (CFO - capex), annual ----
FCF_PUB = {
    'FY2008': 354.210, 'FY2009': 363.430, 'FY2010': 450.494, 'FY2011': 158.294, 'FY2012': 309.060,
    'FY2013': 356.262, 'FY2014': 462.389, 'FY2015': 362.556, 'FY2016': 190.460, 'FY2017': 490.570,
    'FY2018': 692.461, 'FY2019': 791.143, 'FY2020': 1061.194, 'FY2021': 1217.270, 'FY2022': 1296.953,
    'FY2023': 1266.705, 'FY2024': 1670.312, 'FY2025': 1757.021, 'FY2026': 1881.175,
    'FY2027Q1': 464.799,
}

# ---- Organic revenue growth, company total (published, %) ----
ORG = {
    'FY2010': -6.4, 'FY2011': 5.1, 'FY2014': 5.9, 'FY2021': 0.2, 'FY2022': 10.2, 'FY2023': 12.2,
    'FY2012': 6.1, 'FY2013Q1': 3.2, 'FY2013Q2': 3.4, 'FY2013Q3': 6.9, 'FY2013Q4': 6.2, 'FY2013': 4.9,
    'FY2014Q1': 7.1, 'FY2014Q2': 7.1, 'FY2014Q3': 3.1, 'FY2014Q4': 6.1,
    'FY2015Q1': 7.2, 'FY2015Q2': 7.2, 'FY2015Q3': 7.5, 'FY2015Q4': 6.0, 'FY2015': 7.1,
    'FY2016Q1': 6.8, 'FY2016Q2': 6.5, 'FY2016Q3': 6.8, 'FY2016Q4': 6.7, 'FY2016': 6.7,
    'FY2017Q1': 5.7, 'FY2017Q2': 5.7, 'FY2017Q3': 6.5, 'FY2017Q4': 8.1, 'FY2017': 6.7,
    'FY2018Q1': 8.3, 'FY2018Q2': 7.7, 'FY2018Q3': 7.8, 'FY2018Q4': 5.1, 'FY2018': 7.1,
    'FY2019Q1': 5.2, 'FY2019Q2': 7.0, 'FY2019Q3': 6.0, 'FY2019Q4': 7.6, 'FY2019': 6.5,
    'FY2020Q1': 8.3, 'FY2020Q2': 7.3, 'FY2020Q3': 5.7, 'FY2020Q4': -8.4, 'FY2020': 3.1,
    'FY2021Q1': -5.0, 'FY2021Q2': -4.4, 'FY2021Q3': 0.1, 'FY2021Q4': 11.5,
    'FY2022Q1': 8.6, 'FY2022Q2': 9.3, 'FY2022Q3': 10.0, 'FY2022Q4': 12.7,
    'FY2023Q1': 13.9, 'FY2023Q2': 12.8, 'FY2023Q3': 11.8, 'FY2023Q4': 10.3,
    'FY2024Q1': 8.1, 'FY2024Q2': 9.0, 'FY2024Q3': 7.7, 'FY2024Q4': 7.5, 'FY2024': 8.0,
    'FY2025Q1': 8.0, 'FY2025Q2': 7.1, 'FY2025Q3': 7.9, 'FY2025Q4': 9.0, 'FY2025': 8.0,
    'FY2026Q1': 7.8, 'FY2026Q2': 8.6, 'FY2026Q3': 8.2, 'FY2026Q4': 8.4, 'FY2026': 8.3,
    'FY2027Q1': 8.9,
}
# Segment organic growth (%), from releases (FY2016-FY2021) and 10-Q MD&A (FY2022+)
ORG_URFS = {
    'FY2016Q3': 6.1, 'FY2017Q2': 6.5, 'FY2017Q3': 7.3, 'FY2017Q4': 8.0,
    'FY2018Q1': 8.1, 'FY2018Q2': 7.3, 'FY2018Q3': 6.5, 'FY2018Q4': 5.3,
    'FY2019Q1': 4.9, 'FY2019Q2': 6.6, 'FY2019Q3': 6.2, 'FY2019Q4': 6.8,
    'FY2020Q1': 7.5, 'FY2020Q2': 5.8, 'FY2020Q3': 4.8, 'FY2020Q4': -9.6,
    'FY2021Q1': -5.4, 'FY2021Q2': -3.6, 'FY2021Q3': 0.0, 'FY2021Q4': 13.7,
    'FY2022Q2': 8.3, 'FY2022Q3': 8.9, 'FY2022Q4': 10.5,
    'FY2023Q1': 12.3, 'FY2023Q2': 11.3, 'FY2023Q3': 10.8, 'FY2023': 10.8,
    'FY2024Q1': 7.6, 'FY2024Q2': 7.9, 'FY2024Q3': 7.1,
    'FY2025Q1': 7.0, 'FY2025Q2': 6.9, 'FY2025Q3': 7.0,
    'FY2026Q1': 7.3, 'FY2026Q2': 7.8, 'FY2026Q3': 7.3,
}
ORG_FAS = {
    'FY2017Q4': 9.2, 'FY2018Q1': 11.9, 'FY2018Q2': 10.8, 'FY2018Q3': 10.0, 'FY2018Q4': 9.4,
    'FY2019Q1': 9.0, 'FY2019Q2': 10.2, 'FY2019Q3': 8.6, 'FY2019Q4': 10.7,
    'FY2020Q1': 13.8, 'FY2020Q2': 10.6, 'FY2020Q3': 12.5, 'FY2020Q4': 21.9,
    'FY2021Q1': 17.1, 'FY2021Q2': 14.5, 'FY2021Q3': 17.7, 'FY2021Q4': -6.8,
    'FY2022Q2': 3.2, 'FY2022Q3': 6.2,
    'FY2023Q1': 15.8, 'FY2023Q2': 15.1, 'FY2023Q3': 7.8, 'FY2023': 13.1,
    'FY2024Q1': 11.0, 'FY2024Q2': 12.7, 'FY2024Q3': 11.5, 'FY2024': 11.6,
    'FY2025Q1': 14.0, 'FY2025Q2': 12.3, 'FY2025Q3': 15.0, 'FY2025': 15.0,
    'FY2026Q1': 14.1, 'FY2026Q2': 14.1, 'FY2026Q3': 14.6, 'FY2026': 14.0,
}

# ---- Dividends declared per share (pre-split $ where noted) ----
DPS_ANNUAL_RAW = {2006: .35, 2007: .39, 2008: .46, 2009: .47, 2010: .48, 2011: .49, 2012: .54, 2013: .64,
                  2014: .77, 2015: 1.70, 2016: 1.05, 2017: 1.33, 2018: 1.62, 2019: 2.05, 2020: 2.55,
                  2021: 5.01, 2022: 3.80, 2023: 4.60, 2024: 5.40}
DPS_ANNUAL_POST = {2025: 1.56, 2026: 1.80}
def dps_annual(fy):
    if fy in DPS_ANNUAL_POST:
        return DPS_ANNUAL_POST[fy]
    return DPS_ANNUAL_RAW[fy] / SPLIT
# quarterly declared (pre-split raw for <=FY2024); annual dividend declared in Q2 through FY2020
DPS_Q_RAW = {}
for fy in range(2013, 2021):
    for q in (1, 2, 3, 4):
        DPS_Q_RAW[(fy, q)] = DPS_ANNUAL_RAW[fy] if q == 2 else 0.0
DPS_Q_RAW.update({(2021, 1): 0.0, (2021, 2): 3.51, (2021, 3): 0.75, (2021, 4): 0.75})
for fy, v in ((2022, .95), (2023, 1.15), (2024, 1.35)):
    for q in (1, 2, 3, 4):
        DPS_Q_RAW[(fy, q)] = v
DPS_Q_POST = {(2025, q): .39 for q in (1, 2, 3, 4)}
DPS_Q_POST.update({(2026, q): .45 for q in (1, 2, 3, 4)})
DPS_Q_POST[(2027, 1)] = .52
def dps_q(fy, q):
    if (fy, q) in DPS_Q_POST:
        return DPS_Q_POST[(fy, q)]
    return DPS_Q_RAW[(fy, q)] / SPLIT

# ---- Adjusting items not shown on a separate income-statement line (pre-tax, expense = +) ----
# inventory valuation charge recorded in cost of sales (FY2009 Q4)
INV_CHARGE = {'FY2009': 27.486}
# items recorded within selling & administrative expenses
SGA_ITEMS = {
    'FY2018Q3': 40.0, 'FY2018': 40.0,                      # one-time cash payment to employees (Tax Act)
    'FY2021Q2': -17.963, 'FY2021Q3': -3.898, 'FY2021Q4': -0.169, 'FY2021': -22.030,   # gains on sale of operating assets
    'FY2022Q1': -12.129, 'FY2022Q3': -30.151, 'FY2022': -42.280,                     # operating-asset gain; equity-method gain
}
# discrete tax items excluded by the company (after-tax, benefit = negative): Tax Act revaluation FY2018 Q3
TAX_ITEMS = {'FY2018Q3': -1.59 * 110.175, 'FY2018': -1.59 * 110.175}
