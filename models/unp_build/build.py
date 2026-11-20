"""Build UNP_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'UNP_Model.xlsx')
G26 = MAN['guidance_fy26']
DEAL = MAN['nsc_deal']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    return {'oca': round(q['bs_oca'] / q['rev'], 3), 'ocl': round(q['bs_ocl'] / q['rev'], 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end 2025 levels on FY2025 revenues (other current assets {WC["oca"]:.1%}, other current liabilities {WC["ocl"]:.1%} of revenues); '
              'year ends are compared with year ends. Norfolk Southern balances are added at their acquired amounts.')
MAT = {int(k): v for k, v in MAN['debt']['maturities'].items() if k != 'thereafter'}
MAT[2031] = 0.0
X25 = DATA['2025']['x']

V0 = {
    'out_hdr': 'FY26 guidance — Q3-26 release (22-Oct-2026): reported EPS growth "high-single digit"',
    'out_note': ('Affirmed 22-Oct-2026 (raised from mid-single digit on 23-Jul-2026). Also: pricing dollars above inflation dollars; operating ratio improvement from the core business, '
                 'reported OR challenged by high fuel prices; capital plan $3.5bn (from $3.3bn); consistent annual dividend increases; buybacks paused for the Norfolk Southern merger.'),
    'outlook': [
        ('out_eps', '  FY26 reported diluted EPS growth vs FY2025 ($11.98)', (G26['eps_growth_reported']['hi'], G26['eps_growth_reported']['mid'], G26['eps_growth_reported']['lo']), 'pct',
         '"High-single digit" read as 7 / 8 / 9% (Bear / Base / Bull). Drives the Q4/26E cost calibration.'),
        ('bb26', '  Q4/26E share repurchases ($m)', (0.0, 0.0, 0.0), 'm', 'Repurchases paused under the merger agreement (28-Jul-2025); 9M-26 $26m were settlements.'),
    ],
    'points': [
        ('pt_fuel', '  Q4/26E average fuel price per gallon ($)', 4.21, 'm2', 'Q3-26 actual $4.21 (+64% y/y) held flat; no forward curve available on EDGAR (assumption).'),
        ('pt_dep', '  Q4/26E depreciation ($m)', 648.0, 'm', 'Q3-26 $643m; +$5m a quarter run-rate (9M-26 +4% y/y).'),
        ('pt_othinc', '  Q4/26E other income, net ($m)', 95.0, 'm', '9M-26 $291m (~$97m a quarter); no land-sale gains assumed (Q4-25 included $234m).'),
        ('pt_int', '  Q4/26E interest expense ($m)', 310.0, 'm', 'Q3-26 $312m; debt $30.3bn at 30-Sep-2026, no issuance planned before closing (short-term investments accumulating).'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.235, 'pct', '9M-26 23.2% (Q3 23.8%); acquisition-related costs non-deductible.'),
        ('pt_acq', '  Q4/26E acquisition-related expense ($m; adjusted out)', 25.0, 'm', '9M-26 $93m ($36m / $35m / $22m); STB review costs continue.'),
        ('pt_capex', '  FY26 capital investments ($m)', G26['capex'], 'm', 'Capital plan $3.5bn (raised from $3.3bn on 22-Oct-2026); 9M-26 $2,834m incl. $320m of lease buyouts.'),
    ],
    'lev': (2.7, 2.5, 2.3),
    'lev_note': ('Net debt / adjusted EBITDA 2.5x at YE2025 (model basis; company adjusted debt incl. leases / adjusted EBITDA 2.7x, 2.4x at 30-Sep-2026). Target = leverage up to which surplus cash '
                 'is returned via buybacks (2025 authorization, paused); above it (post-closing) free cash flow repays commercial paper / builds cash. Assumption consistent with the company ratio.'),
    'blocks': [
        ('BULK_VOL', 'BULK_VOL (Bulk carloads y/y)', 0.015, -0.015, [0.010, 0.010, 0.005, 0.005], '9M-26 +3% (grain +10%, coal −1%); 2019–25 CAGR ~−1% (coal decline); grain exports and renewables offset coal (assumption).', 'pct', False),
        ('IND_VOL', 'IND_VOL (Industrial carloads y/y)', 0.015, -0.015, [0.020, 0.020, 0.015, 0.015], '9M-26 +4% (metals, energy & specialized); 2019–25 CAGR ~−1%; onshoring / Mexico (assumption).', 'pct', False),
        ('PREM_VOL', 'PREM_VOL (Premium carloads y/y)', 0.020, -0.020, [0.030, 0.025, 0.020, 0.020], '9M-26 +1% (intermodal +2%, automotive −1%; 2024 international intermodal comparison); truck-to-rail conversion (assumption).', 'pct', False),
        ('BULK_PX', 'BULK_PX (Bulk ARPC y/y: price + mix + fuel surcharge)', 0.010, -0.010, [0.020, 0.025, 0.025, 0.025], '9M-26 +6% (fuel surcharge on $3.59/gal vs $2.49); 2019–25 ARPC CAGR ~4%; fuel held flat from 2027E so ARPC ≈ core price + mix.', 'pct', False),
        ('IND_PX', 'IND_PX (Industrial ARPC y/y)', 0.010, -0.010, [0.030, 0.030, 0.030, 0.030], '9M-26 +5%; "pricing dollars in excess of inflation dollars" (2026 outlook); 2019–25 CAGR ~3%.', 'pct', False),
        ('PREM_PX', 'PREM_PX (Premium ARPC y/y)', 0.010, -0.010, [0.015, 0.020, 0.020, 0.020], '9M-26 +11% (fuel surcharge, mix toward automotive); intermodal pricing competitive with truck.', 'pct', False),
        ('OTH', 'OTH_g (Other revenues y/y)', 0.02, -0.02, [0.04, 0.04, 0.03, 0.03], '9M-26 +9% (accessorial, subsidiaries); 2019–25 CAGR ~1%.', 'pct', False),
        ('PROD', 'PROD (workforce productivity: GTMs per employee y/y)', 0.01, -0.01, [0.020, 0.020, 0.015, 0.015], '9M-26 +6% (GTMs +3%, employees −3%); 2019–25 CAGR ~5%; Bull = more productivity.', 'pct', False),
        ('COST', 'COST (uniform shift in PS&M, rents and other % of revenues, pp)', -0.0025, 0.0025, [0.0, 0.0, 0.0, 0.0], 'Base holds the 2025 cost ratios; Bull −25bp (productivity), Bear +25bp (inflation, casualty).', 'pct', False),
        ('SYN', 'SYN (net run-rate EBITDA synergies, $m)', 750.0, -500.0, [2000.0, 2000.0, 2000.0, 2000.0], 'Management: $2.75bn gross ($1.75bn revenue EBITDA + $1.0bn cost); $2.0bn net of illustrative concessions (advisors). Bull gross, Bear $1.5bn.', 'm', True),
    ],
    'gtm_pc_g': 0.0, 'fuel_rate_g': -0.01,
    'fuel_px': {2027: 3.59, 2028: 3.59, 2029: 3.59, 2030: 3.59},
    'fuel_px_note': ('Q4/26E point estimate = Q3-26 $4.21. 2027E+ held at the 9M-26 average ($3.59; FY2025 $2.49): no forward curve is available on EDGAR (assumption). Fuel surcharge revenue (lagged) '
                     'offsets most of the price change, so the OR, not EPS, is the main sensitivity.'),
    'wage_g': 0.035, 'psm_pct': round(X25['psm'] / X25['rev'], 4), 'rents_pct': round(X25['rents'] / X25['rev'], 4),
    'oth_pct': round((X25['oth_exp'] - X25['oa_other'] - X25['oa_acq']) / X25['rev'], 4), 'dep_g': 0.035,
    'nsc_g': {2026: 0.06, 2027: 0.03, 2028: 0.03, 2029: 0.03, 2030: 0.03},
    'nsc_or': {2026: 0.665, 2027: 0.655, 2028: 0.650, 2029: 0.645, 2030: 0.640},
    'nsc_debt_pct': 0.75, 'nsc_ppe_stepup': 0.0, 'acq_rr': 100.0,
    'othinc': 300.0, 'etr': 0.235, 'dtax_p': 0.10,
    'sti_26': 1000.0, 'sti_build': 2000.0, 'inv_q4': 40.0, 'inv_ae': 150.0,
    'capex_pct': 0.135, 'dps_q': 1.42, 'dps_g': 0.03, 'iss_q4': 0.1, 'iss_ae': 0.4, 'dil': 0.8,
    'repay_q4': 2.0, 'mat': MAT, 'refi': 1.0, 'newnotes_add': 0.0, 'min_cash': 1000.0,
    'r_notes': {2027: 0.042, 2028: 0.043, 2029: 0.044, 2030: 0.045}, 'lease_int': 33.0,
    'ofin_q4': 20.0, 'ofin_ae': 80.0,
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $300.62 (Form 4 filed 12-Nov-2026: dividend-reinvestment acquisition at $300.62 on 10-Nov-2026 — the latest share price in an SEC filing; '
                '~$179bn market cap); update to market'),
    'eps_guid_note': 'Company FY26 outlook: "reported earnings per share growth of high-single digit" (raised 23-Jul-2026 from mid-single digit; affirmed 22-Oct-2026). Drives the Q4/26E cost calibration.',
}

# ====================================================================== compute engine
NSC_FIELDS = {'rev': ('is', 'railway_operating_revenues'), 'adj_or': ('ngaap', 'adjusted_operating_ratio_pct'), 'adj_oi': ('ngaap', 'adjusted_income_from_railway_operations'),
              'dep': ('is', 'opex_depreciation'), 'int': ('is', 'interest_expense_on_debt'), 'debt': ('bs', 'total_debt'), 'shout': ('bs', 'shares_outstanding_m'),
              'adj_eps': ('ngaap', 'adjusted_eps_diluted')}
def hist_value(row, col):
    kw = row.kw
    if kw.get('nsc'):
        if col.kind != 'A' or str(col.year) not in NSC['periods']: return None
        sec, f = NSC_FIELDS[kw['nsc']]
        v = NSC['periods'][str(col.year)][sec].get(f)
        if v is None: return None
        return v / 100 if kw['nsc'] == 'adj_or' else v
    path = kw.get('data')
    if not path: return None
    v = xget(pkey(col), path)
    if kw.get('textdata'): return v
    v = num(v)
    if v is None: return None
    if kw.get('pctin'): v = v / 100
    if kw.get('neg'): v = -v
    return v

def first(kw, keys):
    for k in keys:
        if k in kw: return k
    return None

def compute(row, col):
    kw = row.kw; k = col.kind
    CTX.col = col
    if kw.get('ann') and col.q: return None, False
    if k in HISTK:
        v = hist_value(row, col)
        if v is not None: return v, True
        for key in ('hist', 'all'):
            if key in kw:
                return kw[key](), False
        return None, False
    if k == 'QE':
        if row.spec2 and 'qe_in' not in kw and 'qe' not in kw: return None, False
        if 'qe_in' in kw:
            v = kw['qe_in']; return (v[col.q] if isinstance(v, dict) else v), True
        key = first(kw, ('qe', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'E26':
        if 'e26_in' in kw: return kw['e26_in'], True
        if 'e26' in kw: return kw['e26'](), False
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r}:{QE}{row.r})', False
        if kw.get('flow') and not row.spec2 and any(x in kw for x in ('qe', 'qe_in', 'fc')): return S26(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        if not key: return None, False
        v = kw[key]()
        if v is None: return None, False
        if isinstance(v, str) and not v.startswith('=') and kw.get('ae_literal'):
            return float(v), True
        if isinstance(v, (int, float)): return v, True
        return v, False
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'is_frt', 'is_othrev', 'f_rev', 'f_cars', 'f_arpc', 'bulk_rev', 'industrial_rev', 'premium_rev', 'bulk_cars', 'industrial_cars', 'premium_cars',
          'bulk_arpc', 'industrial_arpc', 'premium_arpc', 'o_rev', 'v_gtm', 'v_emp', 'fu_gal', 'is_comp', 'is_fuel', 'is_dep', 'is_oi', 'o_adj', 'r_adj', 'r_ebitda', 'is_ni',
          'eps_dil', 'e_eps', 'dps', 'cf_cfo', 'fcf', 'fcf_co', 'bs_ta', 'bs_eq', 'sh_dil', 'g_rev', 'g_oi', 'co_pe', 'v_gtm_emp', 'is_opex', 'cf_capex'}
CAGR_A = {'is_or', 'or_adj', 'o_adj_or', 'gm_or', 'gm_aor', 'gm_adjop_m', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_comp', 'gm_fuel', 'cr_psm', 'cr_rents', 'cr_oth', 'cr_dep_pct',
          'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'is_etr', 'payout', 'wc_nwc_p', 'fu_rate', 'bulk_mix', 'industrial_mix', 'premium_mix',
          'g_oim', 'r_adj_m', 'r_ebit_m', 'f_fs_p'}
A = {y: ANN[y].c for y in ANN}

def style_cagr(ws, r, on):
    src = 16 if on else 12
    for c in CAGR:
        ws[f'{c}{r}']._style = copy.copy(TM[f'{L(CI(c) + TSHIFT)}{src}']._style)

def write_row(ws, row):
    r = row.r; arch = ARCH[row.arch]
    clone_row_style(ws, arch, r)
    ws.cell(r, 2).value = row.label or None
    if row.kw.get('note'): ws[f'{NOTE}{r}'] = row.kw['note']
    style_cagr(ws, r, row.key in CAGR_G or row.key in CAGR_A)
    if row.arch in ('section', 'block', 'blank', 'sub') and not row.kw.get('data'):
        return
    if row.key in DEFS:
        write_defs(ws, row); return
    nf = NF[row.nf]
    for col in COLS:
        v, inp = compute(row, col)
        if v is None: continue
        cell = ws[f'{col.c}{r}']
        cell.value = v
        if not row.kw.get('textdata'): cell.number_format = nf
        if inp:
            set_color(cell, BLUE, bold=True if col.kind in FCK else None)
            lk = row.kw.get('labkey')
            if lk and col.kind in HISTK and isinstance(v, (int, float)) and abs(v) > 1e-9:
                t = xget(pkey(col), lk)
                if t: comment(cell, f'Company items ({pkey(col)}): {t}', 380, 110)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    rc = CELL_COMMENTS.get(row.key, {})
    for c, t in rc.items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2030]}{r}/{A[2025]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2020]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2015]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2006]}{r})^(1/19)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2026, 2031))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2016, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2006, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: Union Pacific earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'bulk_cars': REL + ('"Freight Revenues Statistics" (revenue carloads, average revenue per car, freight revenues by business group). Bulk / Industrial / Premium published from the Q1-2020 '
                        'release; 2019 columns are the prior-year comparatives of the 2020 releases (recast). Each intermodal container or trailer = one carload.'),
    'f_rev': REL + 'condensed consolidated statements of income (freight revenues / other revenues). 2006–07 as re-presented in the FY2008 Form 10-K (commodity revenue → freight revenues).',
    'c_grain': REL + 'commodity detail within the business groups (from the Q1-2020 release; 2019 from the 2020 releases\' comparatives).',
    'l6_ag': REL + '"Revenue Detail" / "Freight Revenues Statistics" as originally reported: six groups 2006–2017 (Energy renamed Coal in 2012 and Energy again later); four groups 2018–2019.',
    'v_gtm': REL + '"Operating and Performance Statistics" (gross ton-miles, employees, fuel price and gallons, consumption rate, train speed, dwell, car velocity, train length, workforce productivity).',
    'is_frt': REL + 'condensed consolidated statements of income, as originally reported (quarters from each quarter\'s release; years from the Q4 releases; 2006–07 expense lines from the FY2008 10-K).',
    'o_pub': REL + '"Non-GAAP Measures Reconciliation to GAAP — Financial Performance" tables (items affecting comparability), where published.',
    'e_pub': REL + '"Financial Performance" tables: adjusted net income and adjusted diluted EPS, where published.',
    'r_co_pub': REL + '"Adjusted Debt / Adjusted EBITDA" tables (trailing twelve months at year end), published from the Q4-2016 release.',
    'cf_ni': ('Source: release condensed consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). "Other – net" = cash from operations − net income − '
              'depreciation − deferred taxes.'),
    'bs_cash': REL + 'condensed consolidated statements of financial position (period ends). Operating lease assets / liabilities (shown separately 2019–25) are folded into other assets / other long-term liabilities.',
    'sh_basic': REL + 'statements of income (weighted average shares). Shares, EPS and dividends per share before Q2-2014 are restated for the 2-for-1 split of 27-May-2014.',
    'ds_total': 'Source: release balance sheets; FY2025 Form 10-K Note 14 (debt maturities); Q3-26 Form 10-Q Note 14 (credit facility, commercial paper).',
    'ns_rev': 'Source: Norfolk Southern Forms 10-K (FY2024–25), 10-Q (Q1–Q3 2026) and 8-K earnings releases (Ex. 99.1 / 99.2), SEC EDGAR (CIK 702165); adjusted figures per NSC\'s own non-GAAP tables (see data/nsc_standalone.json).',
    'nd_cashps': 'Source: Agreement and Plan of Merger dated 28-Jul-2025 (UNP 8-K 29-Jul-2025, Ex. 2.1); joint proxy statement / prospectus (Form 424B3, 1-Oct-2025): consideration, pro forma financial information (Notes 4–7), management assumed synergies.',
    'cr_sbc': 'Source: XBRL company facts (ShareBasedCompensation, cash-flow statement, to 2024; AllocatedShareBasedCompensationExpense from 2025).',
    'f_fs': 'Source: Forms 10-K (MD&A: "fuel surcharge programs generated freight revenues of…") and 10-Q MD&A where a dollar figure is stated.',
}
CELL_COMMENTS = {}
def comments_setup():
    for y in (2006, 2007):
        c = A[y]
        for k in ('is_comp', 'is_fuel', 'is_psm', 'is_dep', 'is_rents', 'is_oth', 'is_frt', 'is_othrev'):
            CELL_COMMENTS.setdefault(k, {})[c] = (f'FY{y} as re-presented in the FY2008 Form 10-K (freight / other revenues; current six expense lines). The FY{y} release used "Operating Revenues" '
                                                   'and six legacy expense lines (memo rows below the income statement). Totals unchanged.')
    for g in ('bulk', 'industrial', 'premium'):
        for key in (f'{g}_cars', f'{g}_arpc', f'{g}_rev'):
            CELL_COMMENTS.setdefault(key, {})[A[2019]] = '2019 recast to the Bulk / Industrial / Premium basis: prior-year comparatives of the 2020 releases (2019 releases reported Agricultural Products / Energy / Industrial / Premium).'
            for q in (1, 2, 3, 4):
                CELL_COMMENTS[key][QC[(2019, q)].c] = 'Recast (2020 release comparatives).'
    CELL_COMMENTS['o_pub'] = {QC[(2022, 4)].c: 'Derived: FY2022 published adjusted operating income $10,009m − 9M-22 $7,619m (the Q4-22 release published the full-year labor-accrual adjustment only).',
                              QC[(2024, 2)].c: 'First published in the Q2-25 release as prior-year comparatives (gain on sale of intermodal equipment −$46m; environmental remediation +$23m).',
                              QC[(2024, 4)].c: 'First published in the Q4-25 release as prior-year comparatives (crew staffing agreement +$40m).',
                              A[2024]: 'First published in the Q4-25 release (year ended 2024 comparatives).'}
    CELL_COMMENTS['e_pub'] = {QC[(2022, 4)].c: 'Derived: FY2022 adjusted EPS $11.33 less 9M-22 $8.68 ≈ GAAP Q4 $2.67 − $0.02.',
                              A[2017]: 'Tax Cuts and Jobs Act: deferred-tax remeasurement benefit $5,935m ($7.40 per share) and equity-method affiliates remeasurement excluded.'}
    CELL_COMMENTS['v_gtm'] = {A[2017]: 'FY2017 GTMs as published in the Q4-17 release (898,746) differ from Σ quarters as first reported (901,144): company restatement.'}
    CELL_COMMENTS['is_ni'] = {}
    CELL_COMMENTS['n_close'] = {A[2027]: 'Q3-26 Form 10-Q Note 18: completion "currently expected in the second half of 2027" (STB application accepted 16-Jan-2026). Assumption 1-Jul-2027.'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['l_def'] = {
        'C': ('2006–17: six business groups (Agricultural / Automotive / Chemicals / Energy (Coal) / Industrial Products / Intermodal); 2006–07 "commodity revenue"', None),
        q(2018, 1): ('2018–19: four groups — Agricultural Products / Energy / Industrial / Premium (2017 recast in the 2018 releases)', None),
        q(2020, 1): ('2020+: three groups — Bulk / Industrial / Premium with ten commodity lines (2019 recast in the 2020 releases)', None),
    }
    DEFS['o_def'] = {
        'C': ('2006–Q3/17: no adjusted measures published — adjusted = GAAP', None),
        q(2017, 4): ('Q4-17 / FY17: Tax Cuts and Jobs Act items (equity-method affiliates remeasurement in OI; deferred taxes)', 'Q4-17 release (25-Jan-2018) "Financial Performance" table.'),
        q(2018, 1): ('2018–Q3/20: none published — adjusted = GAAP', None),
        q(2020, 4): ('Q4-20 / FY20: Brazos Yard impairment ($278m) excluded', None),
        q(2021, 1): ('2021–Q2/22: none published — adjusted = GAAP', None),
        q(2022, 3): ('Q3-22 / FY22: labor accrual ($114m Q3; $92m FY) excluded; Q4-22 derived', None),
        q(2023, 1): ('2023: none published — adjusted = GAAP', None),
        q(2024, 2): ('2024: items first published retroactively in the 2025 releases (intermodal equipment gain, environmental remediation, crew staffing agreement)', None),
        q(2025, 2): ('2025+: crew staffing agreement, deferred tax adjustment (Q2-25); acquisition-related expense (Norfolk Southern, from Q3-25); industrial park land sales in other income (Q4-25)', None),
        QE: ('Forecast: acquisition-related expense only (non-deductible)', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–Q3/17: no adjusted EPS published — adjusted = GAAP diluted EPS', None),
        q(2017, 4): ('Q4-17 / FY17: adjusted EPS excludes the Tax Act deferred-tax benefit ($7.54 Q4 / $7.40 FY per share) and the equity-method remeasurement', None),
        q(2020, 4): ('Q4-20 / FY20: Brazos Yard impairment, tax-effected ($0.31)', None),
        q(2022, 3): ('2022: labor accrual, tax-effected ($0.14 Q3; $0.12 FY)', None),
        q(2024, 2): ('2024–26: company items tax-effected; acquisition-related expense non-deductible; 2025 deferred tax adjustment (−$0.19) and land-sale gains (−$0.32 FY) excluded', None),
    }
def write_defs(ws, row):
    for c, (txt, cm) in DEFS[row.key].items():
        cell = ws[f'{c}{row.r}']; cell.value = txt
        cell.font = Font(name='Calibri', sz=10, b=True, i=True, color='FFC00000')
        if cm: comment(cell, cm)

def write_scen(ws):
    srcrow = {'hdr': 9, 'out_hdr': 11, 'pt_hdr': 15, 'out': 12, 'pt': 16, 'lev': 28, 'blk': 30, 'yr': 31}
    for spec_ in SCEN_ROWS:
        r, kind = spec_[0], spec_[1]
        for ci in range(CI(SL), CI(SNOTE) + 1):
            ws.cell(r, ci)._style = copy.copy(TM.cell(srcrow[kind], ci + TSHIFT)._style)
        if kind in ('hdr', 'out_hdr', 'pt_hdr'):
            _, _, a, b, c_, d_, e = spec_
            for col, v in zip([SL, SBULL, SBASE, SBEAR, SNOTE], [a, b, c_, d_, e]):
                if v is not None: ws[f'{col}{r}'] = v
        elif kind == 'out':
            _, _, lab, hi, mid, lo, note, nf = spec_
            ws[f'{SL}{r}'] = lab
            for col, v in zip([SBULL, SBASE, SBEAR], [hi, mid, lo]):
                ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF[nf]; set_color(ws[f'{col}{r}'], BLUE)
            ws[f'{SNOTE}{r}'] = note
        elif kind == 'pt':
            _, _, lab, _, val, _, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBASE}{r}'] = val; ws[f'{SBASE}{r}'].number_format = NF[nf]; set_color(ws[f'{SBASE}{r}'], BLUE); ws[f'{SNOTE}{r}'] = note
        elif kind == 'lev':
            _, _, lab, a, b, c_, note = spec_
            ws[f'{SL}{r}'] = lab
            for col, v in zip([SBULL, SBASE, SBEAR], [a, b, c_]):
                ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF['x']
            ws[f'{SNOTE}{r}'] = note
        elif kind == 'blk':
            _, _, lab, db, mid, de, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBULL}{r}'] = db; ws[f'{SBASE}{r}'] = mid; ws[f'{SBEAR}{r}'] = de; ws[f'{SNOTE}{r}'] = note
            for col in (SBULL, SBEAR):
                ws[f'{col}{r}'].number_format = '\\+#,##0;\\-#,##0' if nf == 'm' else '\\+0.00%;\\-0.00%'
        elif kind == 'yr':
            _, _, lab, hdr, base, clamp, _, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBASE}{r}'] = base
            if clamp:
                ws[f'{SBULL}{r}'] = f'=MAX(0,{SBASE}{r}+${SBULL}${hdr})'; ws[f'{SBEAR}{r}'] = f'=MAX(0,{SBASE}{r}+${SBEAR}${hdr})'
            else:
                ws[f'{SBULL}{r}'] = f'={SBASE}{r}+${SBULL}${hdr}'; ws[f'{SBEAR}{r}'] = f'={SBASE}{r}+${SBEAR}${hdr}'
            for col in (SBULL, SBASE, SBEAR): ws[f'{col}{r}'].number_format = NF[nf]

def write_header(ws):
    for r in range(1, 8):
        clone_row_style(ws, r, r, 2, CI(LASTC))
    ws[f'{NOTE}1'] = 'SCENARIO SWITCH ▼ (Bull / Base / Bear) — drives all scenario-linked forecast drivers'
    ws[f'{NOTE}2'] = 'Base'
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: the FY26 reported-EPS-growth end-point (high / mid / low), 2027E–2030E carload and ARPC growth by business group, '
            'other revenues, workforce productivity, the cost-ratio shift, Norfolk Southern synergies and the leverage target for buybacks '
            f'(scenario table {SL}:{SNOTE}). The Norfolk Southern toggle and closing date are inputs in the 2027E column of the NSC block.')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Union Pacific Corporation (NYSE: UNP) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; carloads in thousands) · Calendar fiscal year · '
                'Source: Union Pacific Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1), merger 8-Ks and Form 424B3, SEC EDGAR (CIK 100885); XBRL company facts; '
                'Norfolk Southern Forms 10-K / 10-Q / 8-K (CIK 702165); investor-relations releases at up.com are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported from each period\'s release (2006–07 expense lines re-presented per the FY2008 10-K; 2019 business groups recast to Bulk / Industrial / Premium from the '
                '2020 releases; 2-for-1 split May-2014 applied to earlier per-share data). One reportable segment (rail). Pending acquisition of Norfolk Southern (agreement 28-Jul-2025; STB review; '
                'closing assumed 1-Jul-2027, toggle in the NSC block). Q4/26E calibrated to the FY26 reported-EPS-growth guidance (22-Oct-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '19Y CAGR'], ["25-'30", "20-'25", "15-'25", "06-'25"]):
        ws[f'{c}6'] = a; ws[f'{c}7'] = b

def set_columns(ws):
    for k in list(ws.column_dimensions.keys()): del ws.column_dimensions[k]
    ws.column_dimensions['A'].width = TM.column_dimensions['A'].width
    ws.column_dimensions['B'].width = TM.column_dimensions['B'].width
    wid = {'A': 13.0, 'Q': 9.5703125, 'QE': 11.42578125, 'E26': 14.140625, 'AE': 13.0}
    for col in COLS:
        cd = ws.column_dimensions[col.c]; cd.width = wid[col.kind]
        if col.q:
            cd.outlineLevel = 1; cd.hidden = True
    for ci in range(CI(NOTE), CI(LASTC) + 1):
        ws.column_dimensions[L(ci)].width = TM.column_dimensions[L(ci + TSHIFT)].width or 13.0
    ws.sheet_format.outlineLevelCol = 1

def main():
    import openpyxl
    wb = openpyxl.load_workbook(TEMPLATE)
    if 'DCF_old' in wb.sheetnames: del wb['DCF_old']
    ws = wb['Model']
    blank_style = copy.copy(ws['A1']._style)
    for rowc in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
        for c in rowc:
            c.value = None; c.comment = None; c._style = copy.copy(blank_style)
    for k in list(ws.row_dimensions.keys()):
        rd = ws.row_dimensions[k]; rd.outlineLevel = 0; rd.hidden = False
    ws.data_validations.dataValidation = []
    scen_layout(V0)
    build_spec(V0)
    n1 = len(fw.SPEC)
    build_spec2(V0)
    for i, row in enumerate(fw.SPEC): row.spec2 = i >= n1
    last = number_rows(8)
    for r in range(1, last + 1): ws.row_dimensions[r].height = 15.0
    ws.row_dimensions[2].height = 21.0
    defs_setup(); comments_setup()
    write_header(ws)
    for row in fw.SPEC: write_row(ws, row)
    write_scen(ws)
    set_columns(ws)
    ws.freeze_panes = 'C8'
    ws.sheet_view.zoomScale = 70
    import other_sheets as osh
    osh.do_all(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    osh.inject_charts(OUT)
    print('rows', fw.SPEC[-1].r, 'saved', OUT)
    return wb

RECALC = os.environ.get('XLSX_RECALC', '/mnt/skills/public/xlsx/scripts/recalc.py')
def recalc(path, timeout=600):
    import subprocess
    out = subprocess.run(['python3', RECALC, path, str(timeout)], capture_output=True, text=True, cwd=os.path.dirname(RECALC))
    try:
        return json.loads(out.stdout)
    except Exception:
        return {'raw': out.stdout[-2000:], 'err': out.stderr[-2000:]}

def scenario_snapshots():
    import openpyxl
    import other_sheets as osh
    snaps = {}
    for scen in ('Bull', 'Bear'):
        p = os.path.join(BASE, f'UNP_{scen}.xlsx')
        wb = openpyxl.load_workbook(OUT); wb['Model'][f'{NOTE}2'] = scen; wb.save(p)
        res = recalc(p); print(scen, res.get('status'), res.get('total_errors'))
        v = openpyxl.load_workbook(p, data_only=True)['Bull-Base-Bear']
        snaps[scen] = {(r, c): v[f'{c}{r}'].value for r in range(9, 51) for c in 'CDEFGHIJKL' if v[f'{c}{r}'].value is not None}
        os.remove(p)
    wb = openpyxl.load_workbook(OUT)
    osh.snapshot_values(wb, snaps['Bull'], snaps['Bear'])
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    osh.inject_charts(OUT)

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
def inject_values(src_xlsx, recalc_xlsx):
    """Store cached formula results (from a LibreOffice-recalculated copy) in the openpyxl file, so the workbook reads correctly in any
    viewer; fullCalcOnLoad stays set so Excel recalculates on open."""
    import zipfile, shutil, openpyxl
    from lxml import etree
    wbv = openpyxl.load_workbook(recalc_xlsx, data_only=True)
    zin = zipfile.ZipFile(src_xlsx)
    wbxml = etree.fromstring(zin.read('xl/workbook.xml'))
    rels = etree.fromstring(zin.read('xl/_rels/workbook.xml.rels'))
    rid2t = {r.get('Id'): r.get('Target') for r in rels}
    sheets = {}
    for s in wbxml.iter('{%s}sheet' % NS):
        rid = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        sheets['xl/' + rid2t[rid].lstrip('/').replace('xl/', '')] = s.get('name')
    tmp = src_xlsx + '.tmp'
    zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in sheets:
            ws = wbv[sheets[item.filename]]
            root = etree.fromstring(data)
            for c in root.iter('{%s}c' % NS):
                f = c.find('{%s}f' % NS)
                if f is None: continue
                v = ws[c.get('r')].value
                old = c.find('{%s}v' % NS)
                if old is not None: c.remove(old)
                if v is None: continue
                ve = etree.SubElement(c, '{%s}v' % NS)
                if isinstance(v, bool):
                    c.set('t', 'b'); ve.text = '1' if v else '0'
                elif isinstance(v, (int, float)):
                    if 't' in c.attrib: del c.attrib['t']
                    ve.text = repr(float(v)) if isinstance(v, float) else str(v)
                elif isinstance(v, str) and v.startswith('#'):
                    c.set('t', 'e'); ve.text = v
                else:
                    c.set('t', 'str'); ve.text = str(v)
            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
        zout.writestr(item, data)
    zout.close(); zin.close()
    shutil.move(tmp, src_xlsx)

def store_values():
    import shutil
    p = os.path.join(BASE, 'UNP_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
