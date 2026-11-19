"""Build CSX_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC, MK
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'CSX_Model.xlsx')
OUTLOOK = MAN['outlook_fy26']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    return {'oca': round(q['bs_oca'] / q['rev'], 3), 'ocl': round(q['bs_ocl'] / q['rev'], 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end 2025 levels on FY2025 revenue (other current assets {WC["oca"]:.1%}, other current liabilities {WC["ocl"]:.1%} of revenue); '
              'year ends are compared with year ends (the condensed releases give no receivables / payables split; DSO memo from the 10-K / 10-Q).')
DEBT = MAN['debt']['maturities']

V0 = {
    'out_hdr': 'FY26 outlook — UNVERIFIED (Q3-26 earnings call commentary, 21-Oct-2026, as summarised by a third-party transcript site; CSX files no numeric guidance on EDGAR)',
    'out_note': ('Not in any EDGAR document: "revenue growth raised to high single digits for 2026" and "more than 350 bps of operating-margin expansion" vs the 2025 adjusted margin (33.2%); '
                 'Q4 y/y margin improvement "above 300–350 bps". Verified on EDGAR: 2026 capital investment "less than $2.4 billion" (Q3-26 10-Q). Clear a cell to switch that calibration off.'),
    'outlook': [
        ('out_g', '  FY26 revenue growth (UNVERIFIED call commentary: "high single digits")', (0.09, 0.08, 0.07), 'pct', 'Drives the Q4/26E revenue-per-unit calibration Δ (9M-26 revenue +8.0%). Blank = no calibration.'),
        ('out_m', '  Q4/26E operating-margin improvement y/y (bps; UNVERIFIED: "above 300–350 bps")', (400.0, 350.0, 300.0), 'm', 'On the Q4/25 margin of 31.6% → ~35.1% Base. Drives the Q4/26E labor / purchased-services calibration Δ. Blank = no calibration.'),
        ('bb26', '  Q4/26E share repurchases ($m)', (600.0, 500.0, 400.0), 'm', '9M-26 $1,061m ($543m in Q3); $5.16bn authority remaining at 30-Sep-2026 (10-Q Part II Item 2).'),
    ],
    'points': [
        ('pt_int', '  Q4/26E interest expense ($m)', 207.0, 'm', 'Q3-26 $207m; no issuance in 9M-26; the 2026 maturity (~$0.7bn) is repaid from cash in Q4.'),
        ('pt_othinc', '  Q4/26E other income — net ($m)', 21.0, 'm', 'Q3-26 $21m; 9M-26 $69m.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.240, 'pct', '9M-26 24.1% (Q3 24.0%).'),
        ('pt_dep', '  Q4/26E depreciation and amortization ($m)', 414.0, 'm', 'Q3-26 $413m (equipment depreciation study lowered the run-rate from Q2-26).'),
        ('pt_ppg', '  Q4/26E locomotive fuel price per gallon ($)', 4.20, 'm2', 'Assumption near the Q3-26 average ($4.24; 9M-26 $3.69). Fuel surcharge recovers most of the change on a two-month lag.'),
        ('pt_capex', '  FY26 property additions ($m)', 2350.0, 'm', 'Q3-26 10-Q: 2026 capital investment "expected to be less than $2.4 billion" (9M-26 $1,712m). Point estimate $2,350m.'),
        ('pt_sbc', '  Q4/26E share-based compensation ($m)', 20.0, 'm', '9M-26 $60m (XBRL).'),
        ('pt_def', '  Q4/26E deferred income tax expense ($m)', 50.0, 'm', '9M-26 $115m; Q4-25 $51m.'),
        ('pt_disp', '  Q4/26E proceeds from property dispositions ($m)', 20.0, 'm', '9M-26 $144m (lumpy); Q4-25 $14m.'),
        ('pt_affil', '  Q4/26E increase in investment in affiliates ($m)', 25.0, 'm', '9M-26 +$73m (equity earnings retained).'),
    ],
    'lev': (2.5, 2.25, 2.0),
    'lev_note': ('Net debt $17.2bn at 30-Sep-2026 ≈ 2.3x LTM adjusted EBITDA (2.9x at YE2025 on the lower 2025 EBITDA; 2.3–2.7x in 2019–24). CSX states an investment-grade commitment but no numeric '
                 'target in its filings (assumption: ~2.25x Base). Target = leverage up to which surplus cash is returned via buybacks ($5.16bn authority); below it free cash flow repays commercial paper. '
                 'Borrowing above the $1.0bn CP program (headroom memo) is a financing assumption (new notes). Bull = more buybacks.'),
    'blocks': [
        ('MERCH_VOL', 'MERCH_VOL (merchandise volume y/y; per-market offsets in the build)', 0.02, -0.02, [0.02, 0.02, 0.02, 0.015, 0.015],
         '2025 −2%, 9M-26 +2% (Q3 +3%); industrial production and truck-to-rail conversions. Base +2% p.a. fading to +1.5%.', 'pct', False),
        ('MERCH_RPU', 'MERCH_RPU (merchandise revenue per unit y/y; all-in incl. fuel surcharge)', 0.015, -0.015, [0.035, 0.035, 0.03, 0.03, 0.03],
         '2025 +0.6% (fuel surcharge down), 9M-26 +4.7% (fuel up); 2019–25 CAGR ~4%. Base +3.5% then +3% (core price ~3–4%, flat fuel).', 'pct', False),
        ('IM_VOL', 'IM_VOL (intermodal volume y/y)', 0.03, -0.03, [0.05, 0.04, 0.04, 0.03, 0.03],
         '2025 +3.5%, 9M-26 +7% (domestic wins, tightening truck market); 2019–25 CAGR +1%. Base +5% fading to +3%.', 'pct', False),
        ('IM_RPU', 'IM_RPU (intermodal revenue per unit y/y)', 0.015, -0.015, [0.03, 0.03, 0.025, 0.025, 0.025],
         '2025 −2.3% (fuel, mix), 9M-26 +9.5% (fuel surcharge +); 2019–25 CAGR +2%. Base +3% then +2.5%.', 'pct', False),
        ('COAL_VOL', 'COAL_VOL (coal volume y/y)', 0.03, -0.03, [-0.02, -0.02, -0.03, -0.03, -0.03],
         '2025 −2.4%, 9M-26 +2% (export +6%, domestic utility −1%); 2019–25 CAGR −1%. Base −2% to −3% (utility retirements; export flat).', 'pct', False),
        ('COAL_RPU', 'COAL_RPU (coal revenue per unit y/y; export benchmark-linked)', 0.03, -0.03, [0.0, 0.01, 0.01, 0.01, 0.01],
         '2025 −13% (seaborne benchmarks), 9M-26 +4%; 2019–25 CAGR +2%. Base flat in 2027 then +1%.', 'pct', False),
        ('TRUCK', 'TRUCK (trucking revenue y/y; Quality Carriers)', 0.03, -0.03, [0.03, 0.03, 0.03, 0.03, 0.03],
         '2025 −3%, 9M-26 +5.6% (fuel surcharge); extended truck-market recession through 2025 (goodwill impaired). Base +3%.', 'pct', False),
        ('LABOR', 'LABOR (labor and fringe % of revenue)', -0.0075, 0.0075, [0.205, 0.202, 0.200, 0.198, 0.195],
         '2025 23.1%; 9M-26 21.7% (Q3 20.8%): headcount −6% y/y and operating leverage. Base 20.5% → 19.5% (inflation ~4% vs revenue growth ~5%). Bull = lower ratio.', 'pct', False),
        ('PSO', 'PSO (purchased services and other % of revenue)', -0.0075, 0.0075, [0.167, 0.165, 0.163, 0.162, 0.160],
         '2025 21.4% (network disruptions, rerouting, technology costs); 9M-26 16.8% (Q3 16.4%, incl. property gains). Base 16.7% → 16.0%. Bull = lower ratio.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 500.0, 0.0, [0.0, 0.0, 0.0, 0.0, 0.0],
         'Quality Carriers $544m (2021), Pan Am $600m (2022), small trucking deals since. Base nil (no pending transaction disclosed). Bull +$500m p.a. (assumption).', 'm', True),
    ],
    'vol_off': {'chem': 0.01, 'agfood': 0.0, 'minerals': 0.005, 'auto': -0.015, 'metals': 0.01, 'forest': -0.01, 'fert': -0.015},
    'vol_off_note': {
        'chem': '9M-26 +5% (petcoke, waste, plastics, crude) vs merchandise +2% → +1pp above the lever (assumption).',
        'agfood': '9M-26 +2% (grain, feed; ethanol down) → in line with the lever.',
        'minerals': '9M-26 +3% (construction materials) → +0.5pp.',
        'auto': '9M-26 −1% (customer re-tooling outage; light-vehicle production flat) → −1.5pp.',
        'metals': '9M-26 +5% (steel, equipment, aluminum) → +1pp.',
        'forest': '9M-26 −1% (pulp and paper plant closures; lumber up) → −1pp.',
        'fert': '9M-26 −1% (input costs) → −1.5pp.'},
    'other_pct': 0.039, 'fuel_eff_g': 0.01,
    'ppg': {2027: 3.70, 2028: 3.70, 2029: 3.70, 2030: 3.70, 2031: 3.70},
    'nonloco_pct': 0.016, 'dep_pct': 0.046, 'rents_pct': 0.023, 'othinc': 90.0, 'etr': 0.245, 'sbc_pct': 0.0045,
    'dps_q': 0.14, 'dps_g': 0.08, 'def_ae': 150.0, 'disp_ae': 80.0, 'ofin_ae': 0.0,
    'capex_pct': {2027: 0.155, 2028: 0.15, 2029: 0.15, 2030: 0.15, 2031: 0.15},
    'iss_q4': 0.5, 'iss_ae': 2.0, 'dil': 4.0, 'affil_g': 90.0,
    'iss_notes': {2026: 0.0, 2027: DEBT['2027'], 2028: DEBT['2028'], 2029: DEBT['2029'], 2030: DEBT['2030'], 2031: 0.0},
    'repay': {2026: DEBT['2026'] - 10.0, 2027: DEBT['2027'], 2028: DEBT['2028'], 2029: DEBT['2029'], 2030: DEBT['2030'], 2031: 0.0},
    'mat': {2026: DEBT['2027'], 2027: DEBT['2028'], 2028: DEBT['2029'], 2029: DEBT['2030'], 2030: 0.0, 2031: 0.0},
    'repay_note': ('FY2025 10-K Note 10 maturity ladder: 2026 $708m (of which $10m repaid in 9M-26 → $698m in Q4/26E), 2027 $1,001m (incl. the $850m 3.25% notes), 2028 $1,002m, 2029 $951m, '
                   '2030 $400m, thereafter $14,811m (2031 maturities not disclosed by year → 0; input).'),
    'min_cash': 800.0,
    'r_notes': {2027: 0.045, 2028: 0.0455, 2029: 0.046, 2030: 0.0465, 2031: 0.047},
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $47.67 (average price paid for shares repurchased in September 2026, Q3-26 10-Q Part II Item 2 — the latest share price in an SEC filing; '
                '~$88bn market cap); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base nil). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': ('UNVERIFIED: Q3-26 call commentary ("revenue growth expectations raised to high single digits for 2026") per a third-party transcript summary; not in the 8-K release or 10-Q. '
                      'Scenario end-points 9% / 8% / 7%. Clear the scenario cells to run Q4/26E on the 9M-26 y/y trends only.'),
    'om_guid_note': ('UNVERIFIED: Q3-26 call commentary ("Q4 y/y margin improvement above 300–350 bps"; FY26 expansion "more than 350 bps" vs the 2025 adjusted margin of 33.2%). '
                     'Scenario 400 / 350 / 300 bps on the Q4/25 margin of 31.6%.'),
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
        if 'qe_in' in kw:
            v = kw['qe_in']; return (v[col.q] if isinstance(v, dict) else v), True
        if row.spec2: return None, False
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
CAGR_G = {'is_rev', 'g_rev', 'merch_rev', 'merch_vol', 'intermodal_rev', 'intermodal_vol', 'coal_rev', 'coal_vol', 'truck_rev', 'other_rev', 'tot_vol', 'rail_rev',
          'o_adj', 'r_adj', 'r_ebitda', 'is_oi', 'is_ni', 'e_adjni', 'e_eps', 'eps_dil', 'dps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_te', 'sh_dil', 'labor', 'pso', 'fuel', 'dep',
          'merch_rpu', 'intermodal_rpu', 'coal_rpu', 'g_rpu', 'fuel_gal', 'st_gtm', 'cf_capex'} | {f'{k}_vol' for k in MK} | {f'{k}_rev' for k in MK} | {f'{k}_rpu' for k in MK}
CAGR_A = {'labor_pct', 'pso_pct', 'or_', 'is_om', 'o_adj_m', 'r_adj_m', 'r_aebit_m', 'gm_or', 'gm_adjop_m', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_labor', 'gm_pso', 'gm_fuel', 'gm_dda',
          'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'dep_pct', 'rents_pct', 'nonloco_pct', 'is_etr', 'e_rate', 'fcf_eb', 'other_pct', 'fsc_pct', 'wc_nwc_p',
          'sbc_pct', 'hr_dda', 'hr_payout'}
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

REL = 'Source: CSX earnings releases (Form 8-K Item 2.02, Ex. 99.1 press release / Ex. 99.2 Quarterly Financial Report) — '
LABEL_SOURCES = {
    'chem_vol': (REL + '"Volume and Revenue" table (volume in thousands of units; revenue per unit in $), quarter column of each quarter\'s release; twelve-month column for the annual columns. '
                 'Current market basis from the Q3-2016 release; Q3/15 – Q2/16 and FY2015 from the recast prior-year comparatives of the Q3-16 … Q2-17 releases (cell comments). Earlier periods: legacy memo block.'),
    'merch_vol': REL + '"Total Merchandise" line (2006 – Q1/10: Total Merchandise + Automotive, which was then outside merchandise).',
    'intermodal_vol': REL + '"Intermodal" line ("Total Intermodal" = international + domestic + other to Q1/10).',
    'coal_vol': REL + '"Coal" line ("Total Coal" incl. coke and iron ore to Q1/10).',
    'truck_rev': REL + '"Trucking" line (Quality Carriers, from the Q3-2021 release).',
    'other_rev': REL + '"Other" revenue line (rail "Other" to Q1/10; intermodal "Other" sits inside Total Intermodal).',
    'labor': REL + 'consolidated income statement expense lines, as originally reported (2006–08: Surface Transportation expense; 2013 Q1–Q3 and 2024 Q1 later revised by the company — memo comments).',
    'fuel_gal': REL + '"Fuel Expense" table: estimated locomotive fuel consumption (gallons), price per gallon, locomotive / non-locomotive fuel expense.',
    'is_rev': REL + 'consolidated income statement, as originally reported (each period from its own release; Q4 = fourth-quarter release three-month column).',
    'is_int': REL + 'consolidated income statement (interest expense shown net of capitalised interest; includes equipment obligations and finance leases).',
    'sh_dil': REL + 'average shares outstanding, assuming dilution (thousands to 2008, millions after), restated ×9 before Jun-2011 and ×3 before Jun-2021 for the two 3-for-1 splits.',
    'dps': 'Source: release income statements (cash dividends paid per share) to 2016; 10-K / 10-Q XBRL (CommonStockDividendsPerShareCashPaid / Declared) after, Q4 = FY − 9M; split-adjusted.',
    'o_pub': REL + '"GAAP Reconciliation" (2006–09 "comparable") / "Non-GAAP Measures" (2017, 2024–25 "adjusted") tables; transcribed in manual_items.json with sources.',
    'e_pub': REL + 'comparable EPS (2006–08, from continuing operations) / adjusted EPS (2017, 2024–25); split-adjusted.',
    'cf_ni': REL + 'condensed consolidated cash-flow statements (year to date; discrete quarters derived: Q2 = 6M − Q1, Q3 = 9M − 6M, Q4 = FY − 9M).',
    'bs_cash': REL + 'condensed consolidated balance sheets (period ends). 2010 – Q2/13 releases combine cash and short-term investments: cash from the cash-flow statement, short-term investments = remainder.',
    'bs_shares': 'Source: 10-K balance sheets (common shares outstanding) and 10-Q cover pages (dei:EntityCommonStockSharesOutstanding, dated after the quarter end); split-adjusted.',
    'ds_total': 'Source: release balance sheets; FY2025 10-K Note 10 (maturity ladder, 4.4% average rate, $1.2bn revolver to Feb-2028, $1.0bn CP program); Q3-26 10-Q Note 7.',
    'st_rtm': REL + '"Operating Statistics" table (estimated by the company; revenue ton-miles, gross ton-miles, velocity, dwell, fuel efficiency).',
    'coal_tons': REL + '"Coal Tonnage" table (millions of tons; published from the Q1-2014 release).',
    'fsc_rev': REL + '"Fuel Surcharge" table (published from the Q1-2014 release; fuel surcharge revenue inside the individual markets, excl. trucking).',
    'lg_ag_rev': REL + '"Volume and Revenue" tables on the legacy market bases, as originally reported.',
    'seg_rail_rev': REL + '"Operating Income Detail" (Rail / Intermodal reportable segments to the Q1-2010 release).',
    'v_px': 'Source: Q3-26 10-Q Part II Item 2 (CSX Purchases of Equity Securities): September 2026 average price paid per share $47.67 (Q3 average $48.75). Update to market.',
}
CELL_COMMENTS = {}
def comments_setup():
    q = lambda y, n: QC[(y, n)].c
    rec = {q(2015, 3): 'Q3-2016 release', q(2015, 4): 'Q4-2016 release', A[2015]: 'Q4-2016 release (twelve-month comparatives)', q(2016, 1): 'Q1-2017 release', q(2016, 2): 'Q2-2017 release'}
    for k in MK:
        CELL_COMMENTS[f'{k}_vol'] = {c: f'Recast to the current market basis: prior-year comparative column of the {src} (markets re-cut in Q3-2016: Agricultural and Food Products, Fertilizers, Metals and Equipment, Minerals). '
                                     'As originally reported this period used the 2013 basis (legacy memo block).' for c, src in rec.items()}
    CELL_COMMENTS['is_rev'] = {A[2013]: 'FY2013 as reported in the Q4-2013 release, which revised the first three quarters of 2013 (revenue −$32m; accounts-receivable review) — the quarter columns are as originally reported, so Σ quarters exceeds the year by $32m (operating income +$32m, net earnings +$19m).',
                               A[2024]: 'FY2024 as reported in the Q4-2024 release. The Q2-2024 release revised prior periods for engineering scrap and support labor misstatements (immaterial); Q1/24 is as originally reported, so Σ quarters differs from the year (operating income +$17m, net earnings +$13m).',
                               A[2010]: '53-week fiscal year (ended 31-Dec-2010; 14-week fourth quarter). The release also prints 52-week comparable tables (not used).',
                               A[2016]: '53-week fiscal year (ended 30-Dec-2016; 14-week fourth quarter). Calendar quarters from 2017.',
                               A[2006]: 'Fiscal year ended 29-Dec-2006. 2006–08 releases present "Surface Transportation" expense lines plus a separate "Other Operating Income" line; the model uses consolidated operating income and carries other operating income in the "other operating items" expense row (negative).'}
    CELL_COMMENTS['pso'] = {A[2017]: 'FY2017 purchased services ($2,113m) and rents ($429m) as reported in the Q4-2017 release differ from Σ quarters as first reported ($2,097m / $398m): within-year reclassification between expense lines (total expense ties).',
                            q(2021, 1): 'Q1/21 as originally reported (gains on property dispositions inside purchased services and other); shown as a separate line from the Q2-2021 release.'}
    CELL_COMMENTS['is_oi'] = {q(2017, 4): 'Q4/17 as originally reported ($1,121m). The 2018 releases reclassified 2017 for ASU 2017-07 (pension cost below operating income): $1,126m (FY2017 $3,667m → $3,720m) — memo row in the adjusted-OI bridge.',
                              q(2023, 4): 'As originally reported ($1,320m). The Q4-23 three-month XBRL facts were first tagged in the FY2024 10-K after the 2024 revision ($1,315m).'}
    CELL_COMMENTS['e_tax'] = {A[2006]: 'Comparable EPS from continuing operations $2.22 (pre-split; $0.247 restated) × diluted shares; items: insurance recoveries (0.22), Conrail property gain (0.06), income tax benefits (0.32).',
                              A[2007]: 'Comparable EPS $2.70 (pre-split) = $2.99 − insurance recoveries (0.04) − discontinued operations (0.25); tax effect of the $27m insurance gain ≈ $9m.',
                              A[2008]: 'Comparable EPS from continuing operations $3.52 (pre-split) = $3.34 + Greenbrier impairment (0.27) − equity earnings adjustment (0.05) − income tax benefits (0.04).',
                              q(2017, 4): 'Tax Reform benefit (net) $(3,577)m incl. the $(142)m remeasurement in operating income; restructuring after tax $10m.'}
    CELL_COMMENTS['fuel_ppg'] = {q(2026, 4): 'Point estimate (scenario table).'}
    CELL_COMMENTS['bs_shares'] = {q(2026, 3): 'Q3-26 10-Q cover page: 1,843,398,210 shares (dei:EntityCommonStockSharesOutstanding).'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['merch_def'] = {
        'C': ('2006 – Q1/10 basis: Chemicals / Emerging Markets / Forest / Agricultural / Metals / Phosphates & Fertilizers / Food & Consumer = Merchandise; Coal + Coke & Iron Ore = Total Coal; Automotive separate; Intermodal international / domestic',
              'Releases Q4-2006 … Q1-2010. Group rows above: merchandise incl. automotive; coal incl. coke and iron ore.'),
        A[2010]: ('Q2/10 basis: automotive inside merchandise (eight markets); coke & iron ore into metals / emerging markets; one Intermodal line', 'Q2-2010 release onward (FY2010 annual on this basis).'),
        q(2013, 1): ('Q1/13 basis: Emerging Markets split into Minerals and Waste & Equipment (nine merchandise markets)', 'Q1-2013 release (2012 comparatives recast).'),
        q(2015, 3): ('Current basis (recast comparatives): Agricultural & Food Products, Fertilizers, Metals & Equipment, Minerals (seven markets)', 'Prior-year comparatives of the Q3-16 … Q2-17 releases.'),
        q(2016, 3): ('Current basis as reported (Q3-2016 release onward)', None),
        q(2021, 3): ('Trucking line added (Quality Carriers, acquired 1-Jul-2021)', None),
    }
    DEFS['o_def'] = {
        'C': ('2006–08: company "comparable" operating income = Surface Transportation OI excl. gains on insurance recoveries (basis-difference line for other operating income)',
              'GAAP Reconciliation tables in the Q4-2006 – Q1-2009 releases.'),
        A[2009]: ('2009–16: no adjusted operating income published — adjusted = GAAP (flag)', None),
        q(2017, 1): ('2017: restructuring charge (management workforce reduction) added back; Q4/17 Tax Reform remeasurement in equity earnings of affiliates removed', 'Non-GAAP reconciliations in the 2017 releases; 2017 later reclassified for ASU 2017-07 (memo row).'),
        q(2018, 1): ('2018 – Q3/24: no adjusting items — adjusted = GAAP (flag)', None),
        q(2024, 4): ('Q4/24: Quality Carriers goodwill impairment ($108m) added back', None),
        q(2025, 3): ('Q3/25: Quality Carriers goodwill impairment ($164m) added back; Q4/25 severance and technology rationalization (~$50m) named but not adjusted', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–08: comparable EPS from continuing operations (per-share only): insurance gains, Conrail property gain, income tax benefits, Greenbrier impairment, equity-earnings adjustment, discontinued operations', None),
        A[2009]: ('2009–16: no adjusted EPS published — adjusted = GAAP diluted EPS (flag)', None),
        q(2017, 1): ('2017: adjusted EPS excl. restructuring charge (after tax); Q4/17 also excl. the Tax Reform benefit (net)', None),
        q(2018, 1): ('2018 – Q3/24: adjusted = GAAP (flag)', None),
        q(2024, 4): ('Q4/24 and Q3/25: adjusted EPS excl. goodwill impairment, tax-effected at the applicable rates', None),
    }
    DEFS['fcf_def'] = {
        'C': ('2006–16: no company FCF published — model: CFO − property additions + proceeds from property dispositions', None),
        A[2017]: ('2017–21: company FCF = CFO − property additions + other investing activities (incl. disposition proceeds; excl. acquisitions and short-term investments)', 'Non-GAAP table "Free Cash Flow (before payment of dividends)".'),
        A[2022]: ('2022+: company FCF = CFO − property additions + proceeds and advances from property dispositions', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: the (unverified) FY26 revenue-growth and Q4 margin-improvement end-points (high / mid / low), '
            'Q4/26E buybacks, 2027E–2031E volume and revenue-per-unit growth by market group, trucking growth, labor and purchased-services cost ratios, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'CSX Corporation (NASDAQ: CSX) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; volumes in thousands of units; revenue per unit in USD) · Calendar fiscal years (52/53-week years to 2016) · '
                'Source: CSX Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1 / 99.2 Quarterly Financial Report) and deal / financing 8-Ks, SEC EDGAR (CIK 277948); XBRL company facts; '
                'investor-relations releases at investors.csx.com are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported from each period\'s release (2013 Q1–Q3 and 2024 Q1 later revised by the company — cell comments; 2017 ASU 2017-07 reclassification in memo). '
                'Markets on the current basis from Q3/16 (Q3/15 – Q2/16 recast); legacy bases in memo. One rail segment plus Quality Carriers trucking (acquired 1-Jul-2021); Pan Am acquired 1-Jun-2022. '
                '3-for-1 splits 31-May-2011 and 28-Jun-2021 (per-share data restated). 53-week years 2010 and 2016. Q4/26E calibrated to unverified call commentary (optional cells).')
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
    wid = {'A': 11.0, 'Q': 9.5703125, 'QE': 11.42578125, 'E26': 14.140625, 'AE': 13.0}
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
        p = os.path.join(BASE, f'CSX_{scen}.xlsx')
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
    p = os.path.join(BASE, 'CSX_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
