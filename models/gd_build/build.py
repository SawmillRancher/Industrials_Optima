"""Build GD_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'GD_Model.xlsx')
DEBT = MAN['debt']
AM = MAN['amort_sched']

# ====================================================================== inputs (V0)
def wc_inputs():
    """working-capital drivers: 2027E+ at 31-Dec-2025 year-end levels on FY2025 revenue / operating costs; 2026E at 4-Oct-2026 levels on
    annualised Q3-26 revenue / costs (the 2026E balance sheet rolls forward from 4-Oct-2026)."""
    y = DATA['2025']['x']; q = DATA['Q3-26']['x']
    def drv(x, rev, cost):
        return {'dso': round(x['bs_ar'] / rev * 365), 'unb': round(x['bs_unbilled'] / rev * 365), 'dio': round(x['bs_inv'] / cost * 365),
                'oca': round(x['bs_oca'] / rev, 3), 'dpo': round(x['bs_ap'] / cost * 365), 'adv': round(x['bs_adv'] / rev, 3), 'ocl': round(x['bs_ocl'] / rev, 3)}
    wc25 = drv(y, y['rev'], y['costs']); wc26 = drv(q, q['rev'] * 4, q['costs'] * 4)
    wc = dict(wc26)
    wc['note'] = (f'Forecast inputs (2026E and 2027E+) at 4-Oct-2026 levels on annualised Q3-26 revenue / operating costs: receivables {wc26["dso"]}d, unbilled {wc26["unb"]}d, inventories {wc26["dio"]}d, '
                  f'payables {wc26["dpo"]}d, customer advances {wc26["adv"]:.1%} of revenue, other current liabilities {wc26["ocl"]:.1%}. The 31-Dec-2025 year-end levels were receivables {wc25["dso"]}d, '
                  f'unbilled {wc25["unb"]}d, inventories {wc25["dio"]}d, payables {wc25["dpo"]}d, advances {wc25["adv"]:.1%}; the latest balance sheet is used because the Q3-26 Columbia / Virginia '
                  f'multi-year awards structurally raised customer advances and inventory days have trended down as costs grew (judgement; year ends are compared with year ends in the history).')
    return wc, wc26
WC, WC26 = wc_inputs()

V0 = {
    'out_hdr': 'FY26 outlook — optional targets (none on EDGAR: GD gives guidance on its earnings call only)',
    'out_note': ('GD publishes its annual outlook on the earnings call (Jan / Apr / Jul / Oct), not in the 8-K release or any filing. Nothing is entered by default ("none" = no calibration). '
                 'If the latest call guidance is entered here it is UNVERIFIED (outside EDGAR) and must be marked as such.'),
    'outlook': [
        ('out_rev', '  FY26 revenue target ($m; "none" = no calibration)', ('none', 'none', 'none'), 'm', 'Optional. Drives the Q4/26E revenue calibration Δ when a number is entered (High / Mid / Low by scenario). UNVERIFIED if taken from the call.'),
        ('out_eps', '  FY26 diluted EPS target ($; "none" = no calibration)', ('none', 'none', 'none'), 'ps', 'Optional. Drives the Q4/26E segment-margin calibration Δ when a number is entered. UNVERIFIED if taken from the call.'),
        ('bb26', '  Q4/26E share repurchases ($m)', (300.0, 200.0, 100.0), 'm', '9M-26 $604m ($285m in Q3); 5.06m shares left on the Dec-2024 10m-share authorization at 4-Oct-2026 (10-Q Part II Item 2).'),
    ],
    'points': [
        ('pt_int', '  Q4/26E interest, net ($m; expense negative)', -45.0, 'm', 'Q3-26 $(45)m; 9M-26 $(163)m; $1,000m of notes repaid in 2026 and $4.4bn of cash earning interest.'),
        ('pt_oth', '  Q4/26E other, net ($m)', 5.0, 'm', '9M-26 $18m; Q3-26 $4m.'),
        ('pt_corp', '  Q4/26E corporate operating earnings ($m)', -55.0, 'm', '9M-26 $(140)m; Q3-26 $(53)m; FY2025 $(175)m.'),
        ('pt_amort', '  Q4/26E amortization of intangible & finance-lease ROU assets ($m)', 58.0, 'm', '9M-26 $173m (~$58m a quarter); FY2025 10-K schedule $175m of intangible amortization for 2026.'),
        ('pt_dep', '  Q4/26E depreciation of PP&E ($m)', 178.0, 'm', 'Q3-26 $177m; 9M-26 $525m.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.175, 'pct', '9M-26 17.6% (748 / 4,262); FY2025 17.5%.'),
        ('pt_capex', '  FY26 capital expenditures ($m)', 1400.0, 'm', '9M-26 $918m (Q3 $481m); FY2025 $1,161m. Assumption: Q4 ~$480m (shipyard capacity, Gulfstream).'),
    ],
    'lev': (0.5, 0.25, 0.0),
    'lev_note': ('Net debt $2.6bn at 4-Oct-2026 ≈ 0.4x adjusted EBITDA (YE2025 0.9x; YE2018 post-CSRA 1.9x). Target = leverage up to which surplus cash is returned via buybacks; GD repurchases '
                 'to offset dilution and opportunistically (10m-share authorization Dec-2024), repays notes at maturity and raises the dividend each March. Bull = more buybacks (higher target).'),
    'blocks': [
        ('AERO_G', 'AERO_G (Aerospace revenue y/y)', 0.03, -0.04, [0.08, 0.06, 0.05, 0.04, 0.04],
         '9M-26 +10.9% (FY2025 +16.5%, FY2024 +30%): G700 / G800 deliveries ramp, Jet Aviation services; Aerospace backlog $25.4bn (1.4x book-to-bill 9M-26) ≈ 1.8 years of revenue.', 'pct', False),
        ('MARINE_G', 'MARINE_G (Marine Systems revenue y/y)', 0.03, -0.04, [0.12, 0.09, 0.07, 0.06, 0.05],
         '9M-26 +17.3% (FY2025 +16.6%): Columbia- and Virginia-class submarine throughput; backlog $146.9bn after the Q3-26 multi-year awards (≈7.4 years of revenue); growth limited by shipyard capacity and the supplier base.', 'pct', False),
        ('COMBAT_G', 'COMBAT_G (Combat Systems revenue y/y)', 0.03, -0.04, [0.05, 0.05, 0.04, 0.04, 0.03],
         '9M-26 +3.7% (FY2025 +2.8%); backlog $28.7bn (≈3.0 years): munitions capacity, European land systems, Abrams / Stryker; US Army budget risk.', 'pct', False),
        ('TECH_G', 'TECH_G (Technologies revenue y/y)', 0.02, -0.03, [0.05, 0.04, 0.04, 0.04, 0.04],
         '9M-26 +6.3% (FY2025 +2.6%); backlog $19.4bn (≈1.3 years) plus $31.7bn of IDIQ potential; GDIT federal IT and Mission Systems.', 'pct', False),
        ('AERO_M', 'AERO_M (Aerospace operating margin)', 0.010, -0.015, [0.150, 0.153, 0.155, 0.157, 0.160],
         '9M-26 14.7% (FY2025 13.3%, FY2024 13.0%; FY2014–19 17–20% before the G500 / G600 / G700 development cycle): mix shift to G700 / G800 and lower R&D.', 'pct', False),
        ('MARINE_M', 'MARINE_M (Marine Systems operating margin)', 0.007, -0.010, [0.080, 0.084, 0.087, 0.090, 0.090],
         '9M-26 7.5% (FY2025 7.0%; FY2016–19 8.5–9.7%): supply-chain and new-hire productivity recovering as Columbia matures.', 'pct', False),
        ('COMBAT_M', 'COMBAT_M (Combat Systems operating margin)', 0.007, -0.010, [0.140, 0.141, 0.142, 0.142, 0.142],
         '9M-26 13.8% (FY2025 14.4%, FY2024 14.2%); mix of munitions volume and international vehicle programs.', 'pct', False),
        ('TECH_M', 'TECH_M (Technologies operating margin)', 0.005, -0.008, [0.095, 0.096, 0.097, 0.097, 0.097],
         '9M-26 9.4% (FY2025 9.5%, FY2024 9.6%); services mix.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 1000.0, 0.0, [0.0, 0.0, 0.0, 0.0, 0.0],
         'GD has made no acquisition of size since CSRA ($9.7bn, Apr-2018); Base nil, Bull $1bn p.a. of bolt-ons (assumption).', 'm', True),
    ],
    'b2b': {
        'aero': {'qe': 1.0, 'ae': {2027: 1.05, 2028: 1.05, 2029: 1.0, 2030: 1.0, 2031: 1.0}, 'note': 'Aerospace book-to-bill 1.4x in 9M-26 (1.3x FY2025); forecast input 1.05x then 1.0x (assumption).'},
        'marine': {'qe': 1.0, 'ae': {2027: 0.8, 2028: 0.9, 2029: 1.0, 2030: 1.0, 2031: 1.0}, 'note': 'Marine Systems booked ~$86bn in Q3-26 (Columbia / Virginia multi-year contracts); forecast input below 1.0x while that award is worked off (assumption).'},
        'combat': {'qe': 1.0, 'ae': {2027: 1.0, 2028: 1.0, 2029: 1.0, 2030: 1.0, 2031: 1.0}, 'note': 'Combat Systems book-to-bill 1.6x FY2025 (munitions, European awards); 1.0x input (assumption).'},
        'tech': {'qe': 1.0, 'ae': {2027: 1.0, 2028: 1.0, 2029: 1.0, 2030: 1.0, 2031: 1.0}, 'note': 'Technologies book-to-bill ~1.0–1.2x; 1.0x input (assumption).'},
    },
    'dl_qe': 45.0, 'dl_ae': {2027: 172.0, 2028: 178.0, 2029: 182.0, 2030: 185.0, 2031: 188.0},
    'corp_ae': {2027: -200.0, 2028: -205.0, 2029: -210.0, 2030: -215.0, 2031: -220.0},
    'dep_pct': {2027: 0.014, 2028: 0.014, 2029: 0.014, 2030: 0.014, 2031: 0.014},
    'sbc_pct': 0.004, 'etr': 0.175, 'oth_ae': 20.0, 'def_ae': 150.0, 'def_q4': 50.0, 'oth_cf_ae': -250.0, 'oth_q4': -100.0, 'ofin_q4': 20.0, 'ofin_ae': 100.0,
    'capex_pct': {2027: 0.022, 2028: 0.021, 2029: 0.020, 2030: 0.020, 2031: 0.020},
    'dps_q': 1.59, 'dps_g': 0.06, 'iss_q4': 0.1, 'iss_ae': 0.8, 'dil': 3.6, 'rou_q4': 0.0, 'rou_ae': 70.0,
    'amort_sched': {2027: AM['2027'] + 70.0, 2028: AM['2028'] + 70.0, 2029: AM['2029'] + 70.0, 2030: AM['2030'] + 70.0, 2031: 110.0 + 70.0},
    'amort_note': (AM['src'] + ' 2027 $169m, 2028 $147m, 2029 $131m, 2030 $121m; 2031 $110m assumed; plus ~$70m p.a. of finance-lease ROU amortization '
                   '(FY2025 cash-flow amortization $244m vs $174m of intangible amortization), offset by the ROU additions input.'),
    'iss_notes': {2027: 1250.0, 2028: 1000.0, 2029: 0.0, 2030: 1000.0, 2031: 500.0},
    'repay': {2027: 1250.0, 2028: 1000.0, 2029: 0.0, 2030: 1000.0, 2031: 500.0},
    'mat': {2026: 1250.0, 2027: 1000.0, 2028: 0.0, 2029: 1000.0, 2030: 500.0, 2031: 0.0},
    'repay_note': 'Apr-2027 3.500% $750 + Nov-2027 2.625% $500; May-2028 3.750% $1,000; Apr-2030 3.625% $1,000; Jun-2031 2.250% $500 (FY2025 10-K Note K). Assumed refinanced with new notes (input row above).',
    'min_cash': 1500.0,
    'r_notes': {2027: 0.037, 2028: 0.039, 2029: 0.040, 2030: 0.041, 2031: 0.042},
    'r_notes_note': 'Weighted coupon on the notes outstanding at 4-Oct-2026 ~3.7%; refinancing the 2027–31 maturities at ~4.75% (Aug-2035 notes 4.95%) drifts the average up.',
    'r_cash': 0.035, 'r_cash_note': 'Assumption (~3.5% on cash and equivalents; 9M-26 interest, net $(163)m on ~$7.5bn of debt and ~$3.5bn average cash).',
    'wc': WC, 'wc26': WC26,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $362.97 (average price paid for shares repurchased 31-Aug – 4-Oct-2026, Q3-26 10-Q Part II Item 2 — the latest share price in an SEC filing; '
                '~$99bn market cap); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base nil; Bull $1bn p.a.). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': 'No revenue guidance exists on EDGAR (GD guides on the call). Optional target cells in the scenario table (High / Mid / Low); "none" = no calibration (Δ = 0).',
    'eps_guid_note': 'No EPS guidance exists on EDGAR (GD guides on the call). Optional target cells in the scenario table; "none" = no calibration (Δ = 0).',
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
        if kw.get('bal') and not row.spec2 and any(x in kw for x in ('qe', 'qe_in', 'fc')): return f'={QE}{row.r}', False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'aero_rev', 'marine_rev', 'combat_rev', 'tech_rev', 'aero_oi', 'marine_oi', 'combat_oi', 'tech_oi', 'g_bl', 'g_ord', 'aero_bl', 'marine_bl', 'combat_bl', 'tech_bl',
          'dl_out', 'o_adj', 'g_oi', 'r_adj', 'r_ebitda', 'is_oi', 'd_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_te', 'sh_dil', 'is_costs', 'd_amort', 'd_dep',
          'is_ni', 'eps_dil', 'dps', 'is_cont', 'corp'}
CAGR_A = {'aero_m', 'marine_m', 'combat_m', 'tech_m', 'g_oim', 'o_adj_m', 'r_adj_m', 'r_ebitda_m', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_aero', 'gm_def', 'gm_bl', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_adjop_m', 'gm_etr', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_ga_pct', 'd_dep_pct', 'd_sbc_pct',
          'wc_nwc_p', 'is_etr', 'fcf_eb', 'aero_mix', 'marine_mix', 'combat_mix', 'tech_mix', 'g_b2b', 'g_cov', 'aero_b2b', 'marine_b2b', 'combat_b2b', 'tech_b2b'}
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
                if t: comment(cell, f'Company items ({pkey(col)}): {t}', 420, 140)
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
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2006]}{r})^(1/19)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2016, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2006, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: General Dynamics earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'aero_rev': REL + 'revenue and operating earnings by segment exhibit (three-month columns; FY = twelve-month columns), as originally reported in each period\'s release.',
    'aero_bl': REL + 'backlog exhibit (funded / unfunded / total backlog, estimated potential contract value, total estimated contract value) at each quarter end.',
    'tech_rev': REL + 'segment exhibit: Information Systems and Technology to Q1-18; Information Technology + Mission Systems Q2-18 – Q4-19 (summed); Technologies from Q4-20 (the Q4-20 release recast 2019; Q1–Q3/20 remain IT + MS as reported).',
    'dl_out': 'Source: releases 2006–09 ("Aircraft deliveries" exhibit: completions) and 2017+ ("Gulfstream aircraft deliveries"); Forms 10-Q / 10-K MD&A 2010–16 ("Gulfstream aircraft deliveries (in units): Green / Outfitted"; Q4 = FY − 9M).',
    'corp': REL + 'segment exhibit, Corporate line.',
    'is_rev': REL + 'consolidated statement of earnings, as originally reported (ASC 606 (2017), ASU 2017-07 (2018), the 2014 axle discontinued operations and the 2020 accounting change were not recast; restated comparatives are in cell comments).',
    'is_int': REL + 'statement of earnings ("Interest, net"). GD reports interest net of interest income.',
    'd_dda': 'Source: release consolidated statement of cash flows (depreciation of PP&E; amortization of intangible (and, from 2019, finance-lease ROU) assets); year to date, discrete quarters derived.',
    'd_ga': 'Source: XBRL company facts (us-gaap:GeneralAndAdministrativeExpense, 10-Q / 10-K as first filed).',
    'd_sbc': 'Source: release statement of cash flows ("Equity-based compensation expense", "Stock-based compensation expense" to 2014).',
    'd_impair': 'Source: Q4-2012 release Exhibit C ("Calculation of adjusted non-GAAP earnings from continuing operations"); Q4-2017 release Exhibits A and B (cont.) (tax-law adjustment).',
    'o_pub': 'Source: Q4-2012 release Exhibit C (cont.): adjusted non-GAAP operating earnings by segment (Q4-12 $836m; FY2012 $3,596m).',
    'e_pubni': 'Source: Q4-2012 release Exhibit C; Q4-2017 release Exhibits A and B (cont.).',
    'cf_ni': 'Source: release consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). Working capital = Σ of the release working-capital lines; other operating items derived.',
    'bs_cash': REL + 'consolidated balance sheets (period ends); FY2006 and FY2017 from the Form 10-K (no release balance sheet in Jan-2007; the Jan-2018 preliminary balance sheet differed from the 10-K by $52m of total assets).',
    'bs_shares': 'Source: release "Financial information" exhibit (shares outstanding) to 2018; Form 10-Q / 10-K cover page (dei:EntityCommonStockSharesOutstanding) from 2019.',
    'ppa_cons': 'Source: FY2018 10-K Note B (CSRA Inc., closed 3-Apr-2018; preliminary allocation).',
    'sh_basic': REL + 'statement of earnings (weighted average shares). One class of common stock; no splits since 24-Mar-2006.',
    'dps': 'Source: XBRL company facts (us-gaap:CommonStockDividendsPerShareDeclared, 10-Q) for Q1–Q3; FY from the 10-K ("Cash dividends declared per common share" selected data to FY2020; "declared dividends per share of $x" text from FY2020); Q4 = FY − 9M.',
    'ds_total': 'Source: release balance sheets; FY2025 10-K Note K (debt ladder, maturities); Q3-26 10-Q.',
    'fcf_pub': REL + '"Free cash flow (from operations)" non-GAAP table (quarter column; FY = twelve-month column).',
    'is_oi_x': 'Source: XBRL company facts (us-gaap:OperatingIncomeLoss, earliest-filed 10-K / 10-Q fact for each period).',
}
CELL_COMMENTS = {}
RESTATE = {2013: 'the 2014 releases restated prior periods for the axle business moved to discontinued operations',
           2014: 'the 2015 releases restated prior periods (axle business in discontinued operations)',
           2016: 'the 2017 releases restated 2016 for the adoption of ASC Topic 606 (1-Jan-2017)',
           2017: 'the 2018 releases restated 2017 for ASU 2017-07 (pension cost presentation) and, in the Q2-18+ releases, for the IS&T split into Information Technology and Mission Systems',
           2019: 'the Q4-2020 release restated 2019 for the retrospective change in accounting principle and the Technologies segment',
           2020: 'the Q4-2020 release restated 2020 quarters for the retrospective change in accounting principle'}
def comments_setup():
    for col in COLS:
        p = pkey(col)
        if not p: continue
        x = DATA.get(p, {}).get('x', {})
        why = RESTATE.get(col.year, 'the following year\'s release restated this period')
        for key, rk, lab in (('rev_py', 'is_rev', 'revenue'), ('oi_py', 'is_oi_pub', 'operating earnings'), ('ni_py', 'is_ni_pub', 'net earnings'),
                             ('sr_aero_py', 'aero_rev', 'Aerospace revenue'), ('sr_marine_py', 'marine_rev', 'Marine Systems revenue'), ('sr_combat_py', 'combat_rev', 'Combat Systems revenue'),
                             ('sr_tech_py', 'tech_rev', 'Technologies revenue'), ('so_aero_py', 'aero_oi', 'Aerospace operating earnings'), ('so_marine_py', 'marine_oi', 'Marine Systems operating earnings'),
                             ('so_combat_py', 'combat_oi', 'Combat Systems operating earnings'), ('so_tech_py', 'tech_oi', 'Technologies operating earnings')):
            if x.get(key) is not None:
                CELL_COMMENTS.setdefault(rk, {})[col.c] = f'{p}: as originally reported ({x.get(key.replace("_py", "")) if key != "oi_py" else x.get("oi")}); {why}, which shows {x[key]:,.0f} as the comparative. The model keeps the original.'
        if x.get('dl_note'): CELL_COMMENTS.setdefault('dl_out', {})[col.c] = f'{p}: {x["dl_note"]}.'
        if x.get('dps_note'): CELL_COMMENTS.setdefault('dps', {})[col.c] = f'{p}: {x["dps_note"]}.'
        if x.get('fcf_exc_note'): CELL_COMMENTS.setdefault('fcf_pub', {})[col.c] = f'{p}: published ${x["fcf_pub_exc"]:,.0f}m excluded from the check — {x["fcf_exc_note"]}'
    a = A
    CELL_COMMENTS.setdefault('is_rev', {})[a[2014]] = 'FY2014 (Q4-14 release / 10-K) excludes the axle business (discontinued operations from Q3-14); Q1-14 and Q2-14 as originally reported include $59m of axle revenue in Combat Systems, so the quarters do not sum to the year.'
    CELL_COMMENTS.setdefault('is_disc', {})[a[2016]] = 'FY2016 $(107)m vs Σ quarters as reported $(94)m: the Q4-16 release restated earlier quarters for the final axle-sale loss adjustment.'
    CELL_COMMENTS.setdefault('is_costs', {})[a[2020]] = 'FY2020 restated for the retrospective change in accounting principle (Q4-20 release); Q1–Q3/20 as originally reported differ by $26m (operating costs / other, net).'
    CELL_COMMENTS.setdefault('bs_ta_pub', {})[a[2017]] = 'FY2017 balance sheet from the 10-K (total assets $35,046m); the Jan-2018 release showed a preliminary $34,994m (10-K wins).'
    CELL_COMMENTS.setdefault('bs_ta_pub', {})[a[2006]] = 'FY2006 balance sheet from the 10-K (the Jan-2007 release had no balance-sheet exhibit).'
    CELL_COMMENTS.setdefault('eps_dil', {})[QC[(2013, 1)].c] = 'Q4-12 / FY2012 (annual column I): GAAP loss per share computed on basic shares (dilution anti-dilutive), so the model EPS check uses the published figure.'

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('2006–2011: no adjusted measures published — adjusted = GAAP operating earnings', None),
        A[2012]: ('FY2012 / Q4-12: company adjusted non-GAAP reconciliation (impairments $2,295m, contract disputes $292m, restructuring $98m, inventory charges $78m / $53m) — Exhibit C of the Q4-2012 release',
                  'The Q4-2012 release reconciled GAAP loss from continuing operations to adjusted non-GAAP earnings and, by segment, GAAP to adjusted operating earnings ($836m Q4; $3,596m FY2012).'),
        q(2013, 1): ('2013+: no adjusted measures published — adjusted = GAAP (the Q4-17 tax-law item affects the EPS bridge only)', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–2011: adjusted EPS = GAAP diluted EPS from continuing operations (no company measure; flag)', None),
        A[2012]: ('FY2012 / Q4-12: company definition — loss from continuing operations + items + tax effects, on 355.7m / 353.2m diluted shares',
                  'GAAP loss per share used basic shares (anti-dilution); the company adjusted EPS used diluted shares.'),
        q(2013, 1): ('2013–Q3-17 and 2018+: adjusted = GAAP (continuing operations)', None),
        q(2017, 4): ('Q4-17 / FY2017: GAAP EPS excluding the $119m one-time tax-law charge (company "adjusted non-GAAP" EPS $2.50 / $9.95)', None),
    }
    DEFS['tech_def'] = {
        'C': ('Information Systems and Technology (IS&T) — 2006 to Q1-18', None),
        q(2018, 2): ('Information Technology + Mission Systems (IS&T split after the CSRA acquisition, 3-Apr-2018; 2017 comparatives recast in the 2018 releases) — summed into the Technologies line',
                     'The Q2-2018 release first showed Information Technology (incl. CSRA from 3-Apr-2018) and Mission Systems separately; FY2017 restated comparatives sum to the originally reported IS&T.'),
        q(2020, 4): ('Technologies (Information Technology and Mission Systems recombined effective 31-Dec-2020; 2019 and Q1–Q3/20 recast in the Q4-20 release)', None),
    }
    DEFS['dl_def'] = {
        'C': ('Green deliveries (revenue recognised at green delivery; release exhibit to 2009, 10-Q / 10-K MD&A 2010–16)', None),
        q(2017, 1): ('Outfitted deliveries (ASC 606 adopted 1-Jan-2017: revenue recognised at outfitted delivery; large-cabin / mid-cabin split in the release exhibit)',
                     'The Q4-2016 release printed both bases for 2016 (green 128, outfitted 115) ahead of the accounting change.'),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: the optional FY26 revenue / EPS targets (High / Mid / Low), Q4/26E buybacks, 2027E–2031E segment revenue growth, '
            f'segment margins, M&A spend and the leverage target for 2027E+ buybacks (scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'General Dynamics Corporation (NYSE: GD) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; aircraft in units) · Calendar fiscal year (quarters end on the Sunday nearest quarter end) · '
                'Source: General Dynamics Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1) and deal / financing 8-Ks, SEC EDGAR (CIK 40533); XBRL company facts; '
                'investor-relations releases are the same documents as filed on EDGAR. No guidance exists on EDGAR (GD guides on the earnings call): FY26 targets are optional inputs.')
    ws['B4'] = ('Basis notes: as originally reported (ASC 606 (2017), ASU 2017-07 (2018), the 2014 axle discontinued operations and the 2020 accounting change not recast; restated comparatives in '
                'cell comments). Segments: Aerospace, Marine Systems, Combat Systems, Technologies (= IS&T to Q1-18; Information Technology + Mission Systems Q2-18 – 2019). Acquisitions: Jet Aviation Nov-08, '
                'CSRA Apr-18 (PPA in the schedules). Q4/26E = prior-year quarter × (1 + 9M-26 y/y) at the prior-year margin + 9M drift unless a target is entered.')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '19Y CAGR'], ["26-'31", "20-'25", "15-'25", "06-'25"]):
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
        p = os.path.join(BASE, f'GD_{scen}.xlsx')
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
    p = os.path.join(BASE, 'GD_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
