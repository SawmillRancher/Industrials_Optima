"""Build V_Model.xlsx (Visa Inc.) from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'V_Model.xlsx')
G26 = MAN['guidance_fy26']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']; rev = q['rev_net']
    return {'settle': round(q['bs_settle'] / rev, 3), 'oca': round(q['bs_oca'] / rev, 3), 'onca': round(q['bs_onca'] / rev, 3),
            'settle_l': round(q['bs_settle_l'] / rev, 3), 'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = ('Forecast ratios at fiscal-year-end (30-Sep-2025) levels on FY2025 net revenue (settlement receivable {:.1%}, other current assets {:.1%}, other non-current '
              'assets {:.1%}, settlement payable {:.1%}, other current liabilities {:.1%}); year ends compared with year ends (quarter-end settlement balances swing with '
              'the calendar).').format(WC['settle'], WC['oca'], WC['onca'], WC['settle_l'], WC['ocl'])
UNV = 'UNVERIFIED (earnings call, not on EDGAR): '

V0 = {
    'out_hdr': 'Q4 FY26 outlook — Q3 FY26 earnings call (28-Jul-2026) — UNVERIFIED',
    'out_note': (UNV + 'Visa has given its outlook only on the call since FY2020 (the 8-K release has none); figures from secondary summaries found by web search. '
                 'Q4 FY26: adjusted net revenue growth similar to Q3 (+14% nominal); non-GAAP EPS growth at the low end of mid-teens; adjusted opex growth low double digits; '
                 'FY26 tax rate 18.0–18.25%, non-GAAP non-operating expense ~$165m.'),
    'outlook': [
        ('out_g', '  Q4/26E net revenue growth y/y (UNVERIFIED)', tuple(G26['q4_net_revenue_growth']), 'pct', G26['q4_net_revenue_note']),
        ('out_eps', '  Q4/26E non-GAAP EPS growth y/y (UNVERIFIED)', tuple(G26['q4_adj_eps_growth']), 'pct', G26['q4_adj_eps_note']),
        ('bb26', '  Q4/26E share repurchases ($m)', (6000.0, 5000.0, 4000.0), 'm',
         'Q3 FY26 $4.8bn (14.5m shares at $330.71); 9M FY26 $16.5bn; $28.4bn authorization remaining at 30-Jun-2026 (10-Q). Scenario input.'),
    ],
    'points': [
        ('pt_pvg', '  Q4/26E nominal payments volume growth (quarter ended 30-Jun-2026; published)', MAN['q4_inputs']['pv_growth_nominal'], 'pct', MAN['q4_inputs']['pv_growth_note']),
        ('pt_int', '  Q4/26E interest expense ($m)', 195.0, 'm', 'Q3 FY26 $194m; $24.1bn debt incl. $1.5bn commercial paper; no notes mature in Q4.'),
        ('pt_inv', '  Q4/26E investment income & other ($m)', 114.0, 'm',
         UNV + 'FY26 non-GAAP non-operating expense ~$165m; 9M $84m → Q4 −$81m = interest $195m − $114m investment income. Q3 FY26 non-GAAP $159m.'),
        ('pt_etr', '  Q4/26E non-GAAP tax rate', 0.19, 'pct', UNV + 'FY26 18.0–18.25% with 9M FY26 non-GAAP 17.8% implies ~19% in Q4 (Q3 18.4%).'),
        ('pt_litig', '  Q4/26E litigation provision ($m; adjusted out)', 0.0, 'm', 'Not forecast (assumption): covered-litigation provisions are funded through the escrow / class B conversion-rate mechanism.'),
        ('pt_amort', '  Q4/26E amortization of acquired intangibles ($m; adjusted out)', 64.0, 'm', 'Q3 FY26 $64m (Featurespace, Pismo, Tink).'),
        ('pt_acq', '  Q4/26E acquisition-related costs ($m; adjusted out)', 15.0, 'm', 'Q3 FY26 $14m.'),
        ('pt_capex', '  FY26 purchases of property, equipment & technology ($m)', 1600.0, 'm', '9M FY26 $1,178m; FY25 $1,482m (3.7% of net revenue). Not guided (assumption).'),
    ],
    'lev': (0.50, 0.35, 0.25),
    'lev_note': ('Net debt (debt − cash − investment securities) $9.9bn at 30-Jun-2026 ≈ 0.3x adjusted EBITDA (model definition). Visa returns most free cash flow via '
                 'buybacks and dividends; target = leverage up to which surplus cash is returned (assumption; Visa states no leverage target). Bull = more buybacks.'),
    'blocks': [
        ('PV', 'PV (nominal payments volume y/y)', 0.02, -0.03, [0.085, 0.08, 0.08, 0.075, 0.075],
         'FY2023–25 +5–7.5% (FY2025 +7.0%); 9M FY26 +10.2% nominal (FX tailwind ~1pt). Consumer spending + cash digitisation; U.S. ~48% of volume.', 'pct', False),
        ('PTX', 'PTX (processed transactions y/y)', 0.02, -0.03, [0.09, 0.09, 0.085, 0.08, 0.08],
         'FY2023–25 +10–10.4%; 9M FY26 +9.1%. Tap-to-pay, e-commerce, new flows.', 'pct', False),
        ('SVC_YLD', 'SVC_YLD (service yield change y/y)', 0.01, -0.015, [0.010, 0.010, 0.005, 0.005, 0.005],
         'Service revenue ÷ prior-quarter payments volume: FY2021–25 +1.1% to +5.4% a year (pricing, card benefits); 9M FY26 +2.8%.', 'pct', False),
        ('DP_RPT', 'DP_RPT (data processing revenue per transaction, y/y)', 0.015, -0.02, [0.025, 0.02, 0.02, 0.015, 0.015],
         'FY2021–25 −3.4% to +2.4%; 9M FY26 +7.5% (pricing, value-added services, cross-border mix).', 'pct', False),
        ('ITR', 'ITR (international transaction revenue y/y)', 0.03, -0.06, [0.10, 0.10, 0.09, 0.09, 0.08],
         'FY2023–25 +8.8% to +18.6% (travel recovery to FY23); 9M FY26 +7.4% (lower currency volatility). Cross-border volume ex intra-Europe growth low-teens.', 'pct', False),
        ('OTH', 'OTH (other revenue y/y: value-added services, consulting, marketing)', 0.05, -0.08, [0.22, 0.18, 0.16, 0.14, 0.13],
         'FY2023–25 +24.5% to +29.0%; 9M FY26 +40.1% (consulting, marketing services incl. FIFA World Cup 2026, Milano Cortina 2026).', 'pct', False),
        ('CI', 'CI (client incentives % of gross revenue)', -0.005, 0.010, [0.289, 0.291, 0.293, 0.295, 0.297],
         'FY2017 19.9% → FY2025 28.3% (renewals, competition for issuers); Q3 FY26 28.7%. Base +0.2pt a year.', 'pct', False),
        ('AOM', 'AOM (adjusted operating margin)', 0.01, -0.02, [0.675, 0.677, 0.68, 0.68, 0.682],
         'Non-GAAP: FY2018–25 66.5–68.0% (FY2025 67.7%, FY2020 64.7%); 9M FY26 67.8% with marketing for the FIFA World Cup 2026. Base flat-to-slightly-up.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 1000.0, -1000.0, [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
         'Visa spent ~$0.9bn (Featurespace, FY25), ~$1.0bn (Pismo, FY24), ~$2.0bn (Tink, FY23), $0.7bn (9M FY26). Base $1.0bn p.a. (assumption).', 'm', True),
    ],
    'sbc_pct': 0.023, 'etr': 0.185, 'acq_base': 60.0,
    'capex_pct': {2027: 0.037, 2028: 0.036, 2029: 0.035, 2030: 0.035, 2031: 0.035},
    'dps_q': MAN['q4_inputs']['dividend_q4'], 'dps_g': 0.12, 'def_q4': 0.0, 'def_ae': -100.0, 'ofin_q4': 0.0, 'ofin_ae': 0.0, 'iss_q4': 1.0, 'iss_ae': 4.0,
    'amort_sched': {2027: 230.0, 2028: 190.0, 2029: 150.0, 2030: 110.0, 2031: 80.0},
    'int_am': {2027: 62.0, 2028: 43.0, 2029: 29.0, 2030: 10.0, 2031: 5.0},
    'iss_notes': {2026: 0.0, 2027: 2750.0, 2028: 1428.0, 2029: 2042.0, 2030: 1500.0, 2031: 1750.0},
    'repay': {2026: 0.0, 2027: 2750.0, 2028: 1428.0, 2029: 2042.0, 2030: 1500.0, 2031: 1750.0},
    'mat': {2026: 2750.0, 2027: 1428.0, 2028: 2042.0, 2029: 1500.0, 2030: 1750.0, 2031: 0.0},
    'min_cash': 12000.0,
    'min_cash_note': 'Assumption: Visa holds $12–17bn of cash for settlement liquidity (30-Jun-2026 $12.4bn; 30-Sep-2025 $17.2bn).',
    'r_notes': {2027: 0.032, 2028: 0.033, 2029: 0.034, 2030: 0.035, 2031: 0.036},
    'r_notes_note': ('Q3 FY26 interest expense $194m ≈ 3.2% annualised on $24.1bn; maturing 0.75–2.75% notes refinanced at ~4.5% (Feb-2026 issue 3.80–4.70%) → '
                     'rate drifts up (assumption).'),
    'r_cash': {2027: 0.030, 2028: 0.029, 2029: 0.028, 2030: 0.028, 2031: 0.028},
    'r_cash_note': 'Q3 FY26 non-GAAP investment income $159m ≈ 3.1% annualised on cash (CF basis, incl. restricted) + investment securities. Easing with rates (assumption).',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $389.00 (user-provided, 12-Oct-2026; latest SEC-filed price: $330.82 weighted-average June-2026 repurchase price, '
                'Q3 FY26 10-Q Part II Item 2); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $1.0bn p.a.). Funded from cash (debt schedule).',
    'rev_guid_note': G26['q4_net_revenue_note'] + ' Drives the Q4/26E revenue calibration.',
    'eps_guid_note': G26['q4_adj_eps_note'] + ' Drives the Q4/26E operating-expense calibration.',
}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw; path = kw.get('data')
    if not path: return None
    if kw.get('ppa'):
        v = MAN['ppa'].get(pkey(col), {}).get(path.split('_', 1)[1])
        return v if kw.get('textdata') else num(v)
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
CAGR_G = {'is_rev', 'rev_build', 'rev_svc', 'rev_dp', 'rev_itr', 'rev_oth', 'rev_gross', 'rev_ci', 'k_pv', 'k_ptx', 'aox', 'aoi', 'o_adj', 'r_adj', 'r_ebitda',
          'is_oi', 'is_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_personnel', 'is_marketing', 'is_ni', 'eps_dil', 'dps', 'd_sbc'}
CAGR_A = {'svc_yld', 'ci_pct', 'aom', 'o_adj_m', 'r_adj_m', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_pv', 'gm_ptx', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m',
          'gm_adjop_m', 'gm_ci', 'gm_pers', 'gm_mkt', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_dna_pct', 'd_sbc_pct',
          'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'ny', 'k_pv_ip'}
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
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2031]}{r}/{A[2026]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2020]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2015]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2008]}{r})^(1/17)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2016, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2008, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: Visa earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
FIL = 'Source: Visa Forms 10-Q / 10-K (three-month column for Q1–Q3, identical to the release as originally reported; Q4 = Q4 release three-month column for FY2013–17 and FY2021+, fiscal year − nine months for FY2018–20, whose releases are slide images) — '
LABEL_SOURCES = {
    'k_pv': ('Source: Visa 10-Q / 10-K MD&A "Payments volume and processed transactions" — total nominal payments volume ($bn), three months (10-Q) or twelve months (10-K) ended '
             'one quarter before the fiscal period; Q4 = twelve months − nine months. Company: "service revenue in a given quarter is primarily assessed based on nominal payments '
             'volume in the prior quarter". FY2008 not tabulated on this basis (n/a). Volume figures may be updated later by the company; as first published.'),
    'k_ptx': 'Source: 10-Q / 10-K MD&A "Visa processed transactions" (millions; current period; Q4 = fiscal year − nine months). Not tabulated in the FY2008, FY2009 and FY2011 10-Ks.',
    'rev_svc': FIL + 'statement of operations to FY2018; revenue note ("Disaggregation of revenue") / MD&A from FY2019 (ASC 606). "Service fees" / "volume and support incentives" labels in FY2008.',
    'is_rev': FIL + 'consolidated statements of operations, as originally reported ("operating revenues" to FY2018, "net revenues" from FY2019).',
    'd_litig': REL + 'reconciliations of GAAP to non-GAAP financial results ("as reported / items / as adjusted", later "GAAP / items / non-GAAP"), as first published; company item labels per period in the cell comments.',
    'aox_pub': REL + 'non-GAAP operating expenses as published (n/p where the period\'s release presents no reconciliation or no operating-expense column).',
    'e_pub': REL + 'non-GAAP (adjusted) diluted class A EPS as first published, split-adjusted (÷4 before Mar-2015). n/p: Q1–Q3 FY2013, Q1–Q3 FY2014, Q1–Q2 FY2015, Q4 FY2015, Q1 / Q3 / Q4 FY2017, Q2 FY2018, Q1–Q3 FY2019, FY2013 (no reconciliation for the period).',
    'cf_ni': ('Source: 10-Q / 10-K consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). Cash basis includes restricted cash and '
              'equivalents from FY2019 (ASU 2016-18); litigation-escrow deposits / payments were financing (to FY2018).'),
    'bs_cash': FIL + 'consolidated balance sheets (period ends; Q4 = fiscal year end).',
    'ppa_cons': 'Source: FY2016 10-K Note 2 (Visa Europe, preliminary purchase price allocation).',
    'sh_dil': FIL + 'statements of operations: weighted-average diluted class A shares (as-converted). Split-adjusted ×4 for documents filed before 18-Mar-2015.',
    'ds_total': 'Source: balance sheets; Q3 FY26 10-Q Note 6 (debt: senior notes, commercial paper, maturities and effective rates).',
    'dps': ('Source: earnings releases ("the board of directors declared a quarterly cash dividend of $x per share of class A common stock", announcing the next quarter\'s '
            'dividend); fiscal year = Σ quarters (FY2008–12: 10-K selected financial data). Q2 FY16 and Q2 FY18: XBRL quarterly dividend rate. Split-adjusted.'),
    'cal_hdr': G26['status'],
}
CELL_COMMENTS = {}
def comments_setup():
    CELL_COMMENTS['eps_chk'] = {A[2008]: ('FY2008: the company computed class A EPS ($0.96 pre-split) on net income allocated to class A from the 19-Mar-2008 IPO (two-class method; '
                                          'reorganization-year weighting); net income ÷ weighted diluted shares does not reproduce it (n/m).')}
    CELL_COMMENTS['sh_dil'] = {QC[(y, 4)].c: 'Q4 = 4 × fiscal-year weighted diluted shares − (Q1 + Q2 + Q3): the Q4 release is a slide image.' for y in (2018, 2019, 2020)}
    CELL_COMMENTS['is_rev'] = {QC[(y, 4)].c: 'Q4 = fiscal year (10-K) − nine months (Q3 10-Q); the Q4 release tables are slide images.' for y in (2018, 2019, 2020)}
    CELL_COMMENTS['is_intexp'] = {A[2015]: 'Interest expense is shown separately from FY2016; earlier years carry it inside non-operating income (expense).'}
    CELL_COMMENTS['k_pv'] = {A[2008]: 'FY2008 10-K presents pro forma payments volume on a different basis; not used (n/a).'}
    CELL_COMMENTS['bs_eq'] = {A[2008]: 'Includes temporary equity (class C series II common stock, $1,136m) and minority interest.', A[2009]: 'Includes temporary equity and minority interest ($4m).'}

EXTRA_NOTES = {
    'svc_yld_pre': 'Trend input: 9M FY26 service yield ÷ 9M FY25 service yield − 1 (formula on actuals).',
    'dp_rpt_pre': 'Trend input: 9M FY26 ÷ 9M FY25 data processing revenue per transaction − 1 (formula on actuals).',
    'rev_itr_pre': 'Trend input: 9M FY26 ÷ 9M FY25 international transaction revenue − 1.',
    'rev_oth_pre': 'Trend input: 9M FY26 ÷ 9M FY25 other revenue − 1.',
    'aox_pre': 'Trend input: 9M FY26 ÷ 9M FY25 non-GAAP operating expenses − 1 (incl. FIFA World Cup / Olympics marketing).',
    'm_acq_sales': 'Spend ÷ EV/sales.', 'm_g': 'Assumption: acquired fintech / value-added-services revenue grows 15% a year.',
    'm_run': 'Prior run-rate × (1 + growth) + revenue acquired in the year.', 'm_ppe': 'Assumption: 5% of consideration to PP&E / technology.',
    'm_life': 'Assumption: 7-year life for acquired technology and customer relationships.', 'm_cum': 'Running total of acquired intangibles (gross).',
    'm_amort': 'Cumulative acquired intangibles (+ half the year\'s additions) ÷ life; added to the non-GAAP amortization item.',
    'd_sbc_pct': 'Input 2.3% of net revenue (FY2021–25 2.1–2.4%).',
    'd_amort_sch': 'Assumption: acquired-intangible amortization declining with the FY2025 10-K technology and customer-relationship schedules ($230m FY27 → $80m FY31).',
    'd_acq_pct': 'Assumption: 3% of acquisition spend + $60m integration base (FY2023–25 $90–104m a year).',
    'dps_g': 'Input +12% a year (FY2021–26 dividend growth 7–20% a year; FY26 +13.6%).',
    'cf_oinv': '2026E = 9M actual (net sales of investment securities); 2027E+ nil (investment securities held).',
    'cf_ofin': '2026E = 9M actual; 2027E+ nil (assumption): equity-plan proceeds less withholding taxes and other financing were −$0.1bn to +$0.3bn a year in FY2021–25 (9M FY26 −$184m).',
    'cf_fx': '2026E = 9M actual; 2027E+ nil.', 'bb_iss': 'Assumption: ~1m shares in Q4/26E, ~4m a year after (equity plans).',
    'wc_oca': 'FY2025 year-end ratio (accounts receivable, current client incentives, prepaid & other).',
    'wc_onca': 'FY2025 year-end ratio (non-current client incentives, deferred tax and other assets).',
    'wc_settle_l': 'FY2025 year-end ratio.', 'wc_ocl': 'FY2025 year-end ratio (accounts payable, accrued compensation, client incentives, accrued liabilities).',
    'ds_pxg': 'Assumption: buyback price grows 8% a year from the current share price.',
    'ds_mat': 'Senior-note maturities in the next fiscal year (10-Q Note 6), classified as current.',
    'ds_fees': 'Assumption: hedging, commitment fees and debt-cost amortization.',
    'v_px': 'User-provided $389 (12-Oct-2026); update to market.',
}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2008–09: "adjusted" excl. covered-litigation reserve, IPO restructuring, asset step-up amortization; normalized 41% tax rate',
              'FY2008–09 Q4 releases: adjusted net income = pre-tax income + litigation reserve, restructuring, asset step-up amortization, American Express / Discover settlement interest accretion − investment income on IPO proceeds / escrow, taxed at a normalized 41%.'),
        'E': ('FY2010–11: Visa Europe put-option revaluation only', None),
        'G': ('FY2012: litigation provision ($4.1bn interchange MDL), reversal of tax reserves, deferred tax remeasurement', None),
        q(2013, 1): ('FY2013 – Q3 FY14: no reconciliation for the period (adjusted = GAAP; flag)', 'The FY2013 releases adjust only prior-year (FY2012) figures.'),
        q(2014, 4): ('Q4 FY14: litigation provision ($450m, covered litigation)', None),
        q(2015, 3): ('Q3 FY15 / Q1 FY16: Visa Europe put-option revaluation', None),
        q(2016, 3): ('FY2016: Visa Europe acquisition — framework agreement loss, acquisition costs, currency forwards, FX on euro deposits; Q4: severance, DTL remeasurement', None),
        q(2017, 2): ('Q2 FY17: elimination of deferred tax balances, charitable contribution', None),
        q(2018, 1): ('FY2018: US tax reform (DTL remeasurement, transition tax), litigation provision, charitable contribution; Q2 FY18 none', None),
        q(2019, 1): ('Q1–Q3 FY19: no adjustments (adjusted = GAAP; later recast under the FY2020 definition — not used)', 'The FY2020 releases re-presented Q1–Q3 FY19 non-GAAP under the new definition (e.g. Q1-19 $1.30); the model keeps the originally published basis (= GAAP).'),
        q(2019, 4): ('Q4 FY19: litigation provision', None),
        q(2020, 1): ('FY2020+: definition adds (gains) losses on equity investments, amortization of acquired intangible assets and acquisition-related costs', 'Company definition from the Q1 FY2020 release.'),
        q(2022, 2): ('FY2022+: Russia-Ukraine charges; FY2024: indirect taxes, lease consolidation, charitable contribution; FY2025–26: severance, deferred tax benefit', None),
    }
    DEFS['e_def'] = dict(DEFS['o_def'])
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: Q4 FY26 outlook end-points (net revenue growth and non-GAAP EPS growth, high / mid / low; '
            'UNVERIFIED call commentary), Q4/26E buybacks, 2027E–2031E payments volume and processed transactions growth, service and data processing yields, '
            'international and other revenue growth, client incentives %, adjusted operating margin, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Visa Inc. (NYSE: V) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions, as-converted class A) · Fiscal years ended 30 September (2026 = Oct-2025 – Sep-2026) · '
                'Source: Visa Forms 10-K / 10-Q and Form 8-K earnings releases (Item 2.02, Ex. 99.1), SEC EDGAR (CIK 0001403161); XBRL company facts (cross-checks, dividends); '
                'releases on investor.visa.com are the same documents as filed on EDGAR · Q4 FY26 outlook: earnings call only (not on EDGAR) — UNVERIFIED')
    ws['B4'] = ('Basis notes: as originally reported. IPO 19-Mar-2008 (reorganization Oct-2007; FY2008 first Visa Inc. 10-K year). 4-for-1 split Mar-2015 (per-share ÷4, shares ×4 before). '
                'One reportable segment; revenue by category; client incentives deducted from gross revenue. ASC 606 from FY2019; ASU 2016-18 restricted cash in the cash flow from FY2019. '
                'Visa Europe acquired 21-Jun-2016. Non-GAAP definitions per period (flag rows). Q4/26E calibrated to the Q4 FY26 call outlook (UNVERIFIED).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '17Y CAGR'], ["26-'31", "20-'25", "15-'25", "08-'25"]):
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
    for i, row in enumerate(fw.SPEC):
        row.spec2 = i >= n1
        if row.key in EXTRA_NOTES and not row.kw.get('note'): row.kw['note'] = EXTRA_NOTES[row.key]
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
        p = os.path.join(BASE, f'V_{scen}.xlsx')
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
    p = os.path.join(BASE, 'V_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
