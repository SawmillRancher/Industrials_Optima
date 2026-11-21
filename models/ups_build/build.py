"""Build UPS_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'UPS_Model.xlsx')
G26 = MAN['guidance_fy26']
PX = MAN['price']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    rev = q['rev']
    return {'dso': round(q['bs_ar'] / rev * 365, 1), 'ap': round(q['bs_ap'] / rev, 4), 'wg': round(q['bs_wages'] / rev, 4), 'ocl': round(q['bs_ocl'] / rev, 4)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end 2025 levels on FY2025 revenue (DSO {WC["dso"]}d, payables {WC["ap"]:.1%}, accrued wages {WC["wg"]:.1%}, '
              f'other current liabilities {WC["ocl"]:.1%} of revenue); year ends are compared with year ends (Q4 is the seasonal peak).')
YRS = range(FYC + 1, FYL + 1)

V0 = {
    'out_hdr': 'FY26 guidance — Q3-26 release (8-K Ex. 99.1, 27-Oct-2026; SEC EDGAR)',
    'out_note': ('Point guidance ("approximately"): FY26 revenue ~$92.6bn, non-GAAP adjusted operating profit ~$8.75bn, adjusted diluted EPS ~$7.28, adjusted free cash flow ~$6.1bn; '
                 'Q4/26 revenue ~$25.7bn and adjusted operating profit ~$3.3bn; capex ~$3.0bn, dividends ~$5.4bn, tax rate ~23%, pension contributions $1.3bn. '
                 'Mid = company guidance. High / Low = MODEL ASSUMPTIONS around the point (UPS gives no range).'),
    'outlook': [
        ('out_rev', '  FY26 consolidated revenue ($m)', (G26['revenue'] + 300.0, G26['revenue'], G26['revenue'] - 300.0), 'm',
         'Guided ~$92.6bn (raised 27-Oct-2026). Drives the Q4/26E revenue calibration. High / Low ±$300m = model assumption (≈ ±1.2% of Q4 revenue).'),
        ('out_op', '  FY26 non-GAAP adjusted operating profit ($m)', (G26['adj_op'] + 150.0, G26['adj_op'], G26['adj_op'] - 150.0), 'm',
         'Guided ~$8.75bn (raised 27-Oct-2026). Drives the Q4/26E margin calibration. High / Low ±$150m = model assumption (peak-season execution).'),
        ('bb26', '  Q4/26E share repurchases ($m)', (500.0, 0.0, 0.0), 'm', 'No repurchases in 9M 2026; $1.3bn left on the 2023 authorization at 30-Sep-2026. Base: none (dividends ~$5.4bn absorb free cash flow). Assumption.'),
    ],
    'points': [
        ('pt_q4rev', '  Q4/26 revenue guidance ($m) — information', G26['q4_revenue'], 'm', 'Guided ~$25.7bn (information row; the model is solved to the FY point).'),
        ('pt_q4op', '  Q4/26 adjusted operating profit guidance ($m) — information', G26['q4_adj_op'], 'm', 'Guided ~$3.3bn (information row).'),
        ('pt_eps', '  FY26 adjusted diluted EPS guidance ($) — information', G26['adj_eps'], 'ps', 'Guided ~$7.28 (information row, not forced).'),
        ('pt_fcf', '  FY26 adjusted free cash flow guidance ($m) — information', G26['adj_fcf'], 'm', 'Guided ~$6.1bn (information row, not forced).'),
        ('pt_int', '  Q4/26E interest expense ($m)', 300.0, 'm', 'Not guided; Q3 $289m; a full quarter of the Aug-2026 notes ($1.0bn 4.850% 2031, $325m floating 2076) less the $500m 2.400% notes maturing Nov-2026. Assumption.'),
        ('pt_othinc', '  Q4/26E other pension income + investment income ($m)', 110.0, 'm', '9M 2026 $342m ($123m / $103m / $116m). Excludes any year-end pension mark-to-market. Assumption.'),
        ('pt_da', '  Q4/26E depreciation & amortization ($m)', 970.0, 'm', 'Q3 $965m, Q2 $980m. Assumption.'),
        ('pt_etr', '  Q4/26E tax rate', G26['etr'], 'pct', 'FY26 effective tax rate guided ~23% (9M 2026 23.9%).'),
        ('pt_capex', '  FY26 capital expenditures ($m)', G26['capex'], 'm', 'Guided ~$3.0bn (9M $2,221m).'),
        ('pt_transf', '  Q4/26E transformation strategy costs ($m)', 100.0, 'm',
         'FY26 costs excluded from adjusted results guided at $1.4–1.6bn; $1,398m incurred in 9M → ~$100m in Q4 at the mid-point. Booked in U.S. Domestic Package.'),
        ('pt_sbc', '  Q4/26E stock compensation expense ($m)', 35.0, 'm', 'Q3 $37m, Q2 $34m. Assumption.'),
        ('pt_pen', '  Q4/26E pension expense net of contributions ($m)', -190.0, 'm',
         'FY26 contributions guided at $1.3bn ($897m in 9M → ~$403m in Q4) against ~$215m of quarterly expense. Assumption.'),
    ],
    'lev': (1.6, 1.5, 1.4),
    'lev_note': ('Net debt (debt − cash) $19.2bn at 30-Sep-26 ≈ 1.6x LTM model adjusted EBITDA (pension obligations $5.8bn and operating leases $4.2bn excluded). '
                 'Target = leverage up to which surplus cash is returned via buybacks; below it free cash flow repays commercial paper. Assumption (UPS manages to an adjusted-debt '
                 'ratio that includes pensions and leases). Bull = more buybacks (higher target).'),
    'blocks': [
        ('US_ADV', 'US_ADV (U.S. Domestic average daily volume y/y)', 0.015, -0.02, [-0.01, 0.01, 0.015, 0.015],
         'Q3/26 −3.3% y/y (9M −4.9%): planned reduction of the largest customer\'s volume (>50% vs 2024) completed in Q2-26 and annualises through 1H-27; then growth from SMB and healthcare customers (company priorities per the 10-Q). Assumption.', 'pct', False),
        ('US_RPP', 'US_RPP (U.S. Domestic revenue per piece y/y)', 0.01, -0.015, [0.03, 0.025, 0.025, 0.025],
         'Q3/26 +6.1% y/y (9M +7.4%, as the largest customer\'s volume was reduced); 2015–25 CAGR 3.6%. Assumption.', 'pct', False),
        ('US_M', 'US_M (U.S. Domestic adjusted operating margin)', 0.01, -0.02, [0.08, 0.087, 0.092, 0.095],
         '9M 2026 6.3% (Q3 7.0%; Q4/25 10.2%); FY2021 11.1%, FY2022 11.8%, FY2023 9.0%, FY2025 7.7%. Network Reconfiguration / Efficiency Reimagined program benefits (nearly $3bn expected in 2026, per the Q3-26 10-Q) vs labour-cost inflation. Assumption.', 'pct', False),
        ('INTL_ADV', 'INTL_ADV (International average daily volume y/y)', 0.015, -0.03, [0.0, 0.02, 0.025, 0.025],
         'Q3/26 −8.7% y/y (9M −6.9%): trade-policy changes on certain lanes (10-Q); stabilisation assumed in 2027. Assumption.', 'pct', False),
        ('INTL_RPP', 'INTL_RPP (International revenue per piece y/y)', 0.01, -0.02, [0.03, 0.02, 0.02, 0.02],
         'Q3/26 +15.0% y/y (9M +14.9%); normalising toward the long-run rate. Assumption.', 'pct', False),
        ('INTL_M', 'INTL_M (International adjusted operating margin)', 0.015, -0.02, [0.15, 0.158, 0.163, 0.168],
         '9M 2026 13.2% (Q3 14.9%; Q4/25 18.0%); FY2021 24.2%, FY2023 18.4%, FY2025 15.8%. Assumption.', 'pct', False),
        ('SCS_G', 'SCS_G (Supply Chain Solutions revenue y/y)', 0.02, -0.04, [0.05, 0.04, 0.04, 0.04],
         'Q3/26 +18.2% y/y (forwarding and logistics incl. healthcare; AHG acquired Q4-25); 9M +6.2%. Assumption.', 'pct', False),
        ('SCS_M', 'SCS_M (Supply Chain Solutions adjusted operating margin)', 0.01, -0.02, [0.095, 0.098, 0.10, 0.10],
         '9M 2026 9.2% (Q3 9.2%); FY2025 10.6%, FY2024 8.0%, FY2021 9.8%. Assumption.', 'pct', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 300.0, -200.0, [200.0, 200.0, 200.0, 200.0],
         'Acquisitions, net of cash: $1,968m in 2025 (AHG, Frigo-Trans / BPL), $71m in 2024, $1,329m in 2023; $11m in 9M 2026. Base $200m p.a. of healthcare-logistics bolt-ons (assumption).', 'm', True),
    ],
    'days_q4': 62.0, 'days_ae': 254.0,
    'da_pct': 0.042, 'amort_26': 740.0, 'amort_ae': {2027: 760.0, 2028: 780.0, 2029: 800.0, 2030: 820.0},
    'sbc_ae': 150.0, 'othinc': 420.0, 'etr': 0.23,
    'ae_transf': {2027: 300.0, 2028: 150.0, 2029: 0.0, 2030: 0.0},
    'transf_note': ('History = published adjusted segment operating profit − GAAP segment operating profit (company item wording in the cell comments of the total row of the bridge). '
                    'Q4/26E: transformation strategy costs to the mid-point of the FY26 range ($1.4–1.6bn). 2027E+: Efficiency Reimagined is "not expected to conclude" in 2026 — '
                    '$300m / $150m then nil is an assumption.'),
    'dps_q': 1.64, 'dps_g': 0.006,
    'pen_ae': -400.0, 'def_q4': 0.0, 'def_ae': 0.0, 'iss_q4_cash': 30.0, 'iss_ae_cash': 120.0, 'iss_q4': 0.9, 'iss_ae': 3.5, 'dil': 1.0,
    'disp_ae': 100.0,
    'capex_pct': {2027: 0.038, 2028: 0.042, 2029: 0.044, 2030: 0.044},
    'iss_notes': {2026: 0.0, 2027: 1000.0, 2028: 2068.0, 2029: 2649.0, 2030: 3526.0},
    'repay': {2026: 500.0, 2027: 1000.0, 2028: 568.0, 2029: 1149.0, 2030: 1526.0},
    'mat': {2026: 1000.0, 2027: 568.0, 2028: 1149.0, 2029: 1526.0, 2030: 1000.0},
    'min_cash': 5000.0,
    'r_notes': {2027: 0.046, 2028: 0.046, 2029: 0.047, 2030: 0.047},
    'r_notes_note': ('9M 2026 interest expense $827m on ~$25bn average debt (~4.4% annualised; Q3 $289m on $26.1bn = 4.4%); coupons 2.5–6.2% on fixed notes, SOFR-linked floating notes, '
                     'finance leases. Drifting up as low-coupon notes (2.400% 2026, 3.050% 2027, EUR 1.000% 2028) are refinanced. Assumption.'),
    'wc': WC,
    'px': PX['px'],
    'px_note': (f'VALUATION — share price input ${PX["px"]:.2f} ({PX["form"]}; the latest share price in an SEC filing — market-data sites are not reachable from the build '
                'environment; ~$90bn market cap). UPDATE TO MARKET'),
    'mna_note': 'Scenario lever M&A_spend (Base $200m p.a. of bolt-ons; assumption). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': 'Company FY26 consolidated revenue guidance ~$92.6bn (Q3-26 release, 27-Oct-2026). Mid = guidance; High / Low ±$300m are model assumptions. Drives the revenue calibration.',
    'op_guid_note': 'Company FY26 non-GAAP adjusted operating profit guidance ~$8.75bn (Q3-26 release). Mid = guidance; High / Low ±$150m are model assumptions. Drives the margin calibration.',
}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw; path = kw.get('data')
    if not path: return None
    v = xget(pkey(col), path)
    return v if kw.get('textdata') else num(v)

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
        if row.spec2: return None, False
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
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'us_rev', 'intl_rev', 'scs_rev', 'us_adv', 'intl_adv', 'g_adv', 'us_rpp', 'intl_rpp', 'g_rpp', 'g_vol', 'us_oi', 'intl_oi', 'scs_oi',
          'us_nda', 'us_def', 'us_gnd', 'intl_dom', 'intl_exp', 'scs_fl', 'us_nda_adv', 'us_def_adv', 'us_gnd_adv', 'intl_dom_adv', 'intl_exp_adv',
          'us_nda_rpp', 'us_def_rpp', 'us_gnd_rpp', 'intl_dom_rpp', 'intl_exp_rpp',
          'o_adj', 'g_adj', 'r_adj', 'r_ebitda', 'is_ebit', 'd_da', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_comp', 'is_pt', 'is_opex',
          'is_ni', 'eps_dil', 'dps', 'us_cpp', 'intl_cpp'}
CAGR_A = {'us_m', 'intl_m', 'scs_m', 'g_adjm', 'o_adj_m', 'r_adj_m', 'is_ebit_m', 'r_ebit_m', 'gm_rev', 'gm_adv', 'gm_rpp', 'gm_us', 'gm_intl', 'gm_scs', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_comp', 'gm_pt', 'gm_adjop_m', 'fcf_m', 'fcf_conv', 'fcf_div', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x',
          'd_da_pct', 'd_comp', 'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'us_mix', 'intl_mix', 'scs_mix', 'us_adv_g', 'us_rpp_g', 'intl_adv_g', 'intl_rpp_g'}
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

REL = 'Source: UPS earnings releases (Form 8-K Item 2.02, Ex. 99.1 / 99.2) — '
LABEL_SOURCES = {
    'days': REL + '"Selected Operating Data" (operating weekdays / operating days). Q3-2026: Form 10-Q MD&A (the 27-Oct-2026 8-K has no Ex. 99.2).',
    'us_nda_adv': REL + '"Selected Operating Data": average daily package volume (thousands) and average revenue per piece by product, as originally reported. Q3-2026 from the Form 10-Q MD&A.',
    'us_rev': REL + '"Selected Financial Data": segment revenue and operating profit, as originally reported. Q1–Q3 2024 on the recast basis of the 2025 releases (cell comments).',
    'us_oi': REL + '"As adjusted income data" / "Non-GAAP Adjusted Income Data" in the Selected Financial Data (segment operating profit); published in periods with adjusting items.',
    'us_cargo': REL + '"Selected Operating Data" from the Q4-2024 release (FY2024 and the 2024 quarters as recast in the 2025 releases).',
    'scs_fl': REL + '"Selected Operating Data": Supply Chain & Freight / Supply Chain Solutions revenue lines.',
    'is_rev': REL + '"Selected Financial Data", as originally reported. FY2020 / Q4-2020 operating profit, tax and net income from the 2020 Form 10-K (cell comments).',
    'is_comp': ('Source: Forms 10-K / 10-Q, statements of consolidated income (operating-expense lines); from 2021 also the release "Detail of Operating Expenses". '
                'Q4 = fiscal year (10-K) − nine months (Q3 10-Q) where the release has no quarterly detail.'),
    'd_amort': 'Source: Form 10-K (XBRL us-gaap:AmortizationOfIntangibleAssets, as first filed), annual only.',
    'o_pub': REL + '"As adjusted" operating profit (to Q3-2018) / "Non-GAAP Adjusted" operating profit; reconciliation schedules from Q4-2018.',
    'e_pub': REL + 'as adjusted / non-GAAP adjusted net income and diluted EPS.',
    'cf_ni': 'Source: Forms 10-K / 10-Q, statements of consolidated cash flows (year to date; discrete quarters derived, Q4 = FY − 9M).',
    'bs_cash': 'Source: Forms 10-K / 10-Q, consolidated balance sheets (period ends); "derived" lines are residuals to the reported subtotals. Shares issued by class from the balance-sheet captions.',
    'sh_basic': REL + '"Selected Financial Data" (weighted-average shares, whole millions). Q3-2026: Form 10-Q earnings-per-share note. No stock splits in the period.',
    'dps': 'Source: Forms 10-K / 10-Q, "Dividends declared per share" (year to date; quarters differenced).',
    'fcf_pub': REL + '"Reconciliation of Free Cash Flow" (year to date; quarters differenced).',
    'ds_total': 'Source: balance sheets; Q3-2026 Form 10-Q debt note (30-Sep-2026) and 2025 Form 10-K contractual-commitments table.',
}
CELL_COMMENTS = {}
def comments_setup():
    for col in COLS:
        if col.kind not in HISTK: continue
        p = pkey(col); d = DATA.get(p, {})
        lab = xget(p, 'oa_lab')
        if lab: CELL_COMMENTS.setdefault('o_tot', {})[col.c] = f'Company footnotes to the adjusted data in the {p} release (verbatim; they may also describe the prior-year comparative): {lab}'[:1990]
        if d.get('recast'):
            for k in ('us_rev', 'scs_rev', 'us_gaap', 'scs_gaap'): CELL_COMMENTS.setdefault(k, {})[col.c] = d['recast']
        if d.get('corr'):
            for k in ('is_ebit', 'is_ni_pub', 'scs_gaap'): CELL_COMMENTS.setdefault(k, {})[col.c] = d['corr']
        if d.get('corr_ops'): CELL_COMMENTS.setdefault('scs_log', {})[col.c] = d['corr_ops']
        for nt in d.get('notes', []):
            CELL_COMMENTS.setdefault('is_rev', {})[col.c] = nt
    CELL_COMMENTS.setdefault('us_cargo', {})[A[2024]] = ('FY2024 as presented in the Q4-2024 release, which shows air cargo (incl. the USPS air cargo volumes onboarded in 2024) in '
                                                          'U.S. Domestic Package "Cargo and Other" (in Supply Chain Solutions in the Q1–Q3 2024 releases).')
    CELL_COMMENTS.setdefault('scs_m', {})[QC[(2025, 3)].c] = 'Q3/25 includes a $330m pre-tax gain on a sale-leaseback transaction in Supply Chain Solutions (release footnote); not adjusted out by the company.'

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2006: no adjusted measures published — adjusted = GAAP. FY2006–10 on the pension accounting in force before the Q4-2011 change (the 8-K of 27-Jan-2012 recast is not used)',
              'UPS changed its pension accounting in Q4-2011 (mark-to-market gains / losses outside a 10% corridor recognised immediately) and applied it retrospectively (8-K 27-Jan-2012). '
              'The model keeps FY2006–FY2010 as originally reported.'),
        A[2007]: ('FY2007–10: "as adjusted" excludes named items — 2007 Central States Pension Fund withdrawal ($6.1bn), aircraft impairment, SVSO, France restructuring; '
                  '2008 UPS Freight goodwill and European intangible impairments; 2009 DC-8 impairment; 2010 restructuring charge and gains / losses on sales',
                  'The items are quoted from the release footnotes in the cell comment on the "Total adjusting items" row of each period.'),
        A[2011]: ('FY2011+: pension mark-to-market loss outside the 10% corridor (in operating expenses) excluded from "as adjusted"; also 2012 multiemployer plan withdrawal, '
                  '2013 TNT termination fee and related currency gain, 2014 health & welfare plan transfer', None),
        q(2018, 1): ('Q1-18+: ASU 2017-07 — the pension mark-to-market is in "other pension income (expense)", below operating profit (separate adjusting-item row); '
                     'transformation strategy costs excluded from adjusted operating profit from 2018',
                     'From 2018 the releases show "other pension income (expense)" as a separate line of other income; the Q4-2018 release excludes the mark-to-market loss from adjusted other income (expense).'),
        q(2018, 4): ('Q4-18+: adjusted data shown as "Non-GAAP" with reconciliation schedules by segment', None),
        q(2020, 4): ('Q4-20+: goodwill / asset impairments and divestiture gains / losses (UPS Freight) excluded with "Transformation & other"', None),
        q(2023, 1): ('2023: also excludes a one-time compensation payment, goodwill / intangible impairments, the incentive compensation program redesign charge and the MD-11 residual-value change', None),
        q(2024, 4): ('Q4-24+: transformation strategy costs (Transformation 2.0, Fit to Serve, Network Reconfiguration and Efficiency Reimagined), asset impairments, multiemployer plan withdrawal', None),
        q(2026, 3): ('Q3-26: transformation strategy costs, Supply Chain Solutions goodwill & asset impairment ($182m) and gains on sales of previously impaired MD-11 parts excluded', None),
    }
    DEFS['r_def'] = {
        'C': ('Model definition for all periods: adjusted EBITDA = non-GAAP adjusted operating profit + D&A. UPS reconciles "adjusted EBITDA" only on a trailing-twelve-month basis '
              'for its adjusted-debt ratio (also adjusting pension items); that measure is not rebuilt', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006: no adjusted EPS published — adjusted = GAAP diluted EPS (flag)', None),
        A[2007]: ('FY2007+: "as adjusted" EPS = GAAP diluted EPS excluding the after-tax named items (published only in periods with items; otherwise adjusted = GAAP)', None),
        q(2017, 4): ('Q4-17: also excludes income-tax benefits attributable to the 2017 Tax Cuts and Jobs Act', None),
        q(2018, 4): ('Q4-18+: "Non-GAAP adjusted" EPS; pension mark-to-market (other income), transformation costs and discrete tax items excluded', None),
        q(2025, 2): ('2025: reversal of income-tax valuation allowance excluded', None),
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
                ws[f'{col}{r}'].number_format = '\\+#,##0;\\-#,##0' if nf == 'm' else '\\+0.0%;\\-0.0%'
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 revenue and adjusted-operating-profit end-points (high / mid / low around the guidance point), '
            'Q4/26E buybacks, 2027E–2030E average daily volume, revenue per piece, Supply Chain Solutions growth, segment margins, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'United Parcel Service, Inc. (NYSE: UPS) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; average daily volume in thousands) · Calendar fiscal year · '
                'Source: UPS Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1 / 99.2) and financing 8-Ks, SEC EDGAR (CIK 1090727); XBRL company facts for cross-checks; '
                'investor-relations releases at investors.ups.com are the same documents as filed on EDGAR. FY26 guidance: Q3-26 release (EDGAR-filed; no call-only guidance used)')
    ws['B4'] = ('Basis notes: as originally reported (pre-2011 pension accounting to FY2010; ASU 2017-07 from Q1-18, earlier periods not recast; FY2020 / Q4-20 per the 10-K; '
                'Q1–Q3/24 segments on the 2025 recast basis). Segments: U.S. Domestic Package, International Package, Supply Chain Solutions (Supply Chain & Freight to Q1-21). '
                'Disposals: UPS Freight Apr-21, Coyote Sep-24; acquisitions: Frigo-Trans / BPL and Andlauer Healthcare Group (AHG) 2025. Q4/26E calibrated to FY26 revenue and adjusted operating profit guidance (27-Oct-2026).')
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
        p = os.path.join(BASE, f'UPS_{scen}.xlsx')
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
    viewer; fullCalcOnLoad stays set so Excel recalculates on open. Same approach as the LECO / ESAB finishing step."""
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
    p = os.path.join(BASE, 'UPS_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
