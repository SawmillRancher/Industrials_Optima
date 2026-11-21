"""Build NSC_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'NSC_Model.xlsx')
LRP = MAN['lrp']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    rev = q['rev']; cash_opex = q['opex'] - q['dep'] - (q['merger'] + q['restr'] + q['eoi'] + q['loss_disp'])
    return {'dso': round(q['bs_ar'] / rev * 365), 'dms': round(q['bs_ms'] / cash_opex * 365), 'dpo': round(q['bs_ap'] / cash_opex * 365),
            'taxp': round(q['bs_taxes'] / rev, 3), 'oclp': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end 2025 levels on 2025 revenues / cash operating expenses (DSO {WC["dso"]}d, materials & supplies {WC["dms"]}d, payables {WC["dpo"]}d, '
              f'taxes {WC["taxp"]:.1%} and other current liabilities {WC["oclp"]:.1%} of revenues — the latter includes the $609m current Eastern Ohio incident liability at 31-Dec-2025); '
              'year ends are compared with year ends.')
lrp_years = LRP['years']
LRPD = {'rev': {y: v * 1000 for y, v in zip(lrp_years, LRP['revenue_bn'])}, 'oi': {y: v * 1000 for y, v in zip(lrp_years, LRP['adj_oi_bn'])},
        'ebitda': {y: v * 1000 for y, v in zip(lrp_years, LRP['adj_ebitda_bn'])}, 'capex': {y: v * 1000 for y, v in zip(lrp_years, LRP['capex_bn'])},
        'eps': dict(zip(lrp_years, LRP['adj_eps'])), 'note': LRP['_note']}
LRPD['or'] = {y: round(1 - LRPD['oi'][y] / LRPD['rev'][y], 4) for y in lrp_years}

def seq_or_formula(fn):
    """Q3→Q4 change in the adjusted operating ratio, 2016–2025 excluding 2024 (Q3/24 adjusted OR carried $380m of railway line-sale gains)."""
    return lambda: f'={fn}(' + ','.join(f'{QC[(y, 4)].c}{R["or_seq"]}' for y in range(2016, 2026) if y != 2024) + ')'

V0 = {
    'out_hdr': 'Q4/26E anchors — no numeric company outlook on EDGAR (calls only); 9M-26 / Q3-26 trends + scenario Δ; OR seasonality',
    'out_note': ('NSC files no revenue / operating-ratio / EPS guidance (its Q3-26 10-Q gives only 2026 property additions ≈ $2.1bn and says Q4 fuel expense and fuel surcharge revenue '
                 'will rise y/y on current fuel prices). The long-range plan in the Union Pacific merger proxy (Oct-2025) is shown as information rows, not used as an anchor.'),
    'outlook': [
        ('q4_vol_d', '  Q4/26E units y/y: Δ vs the 9M-26 y/y trend (pts, all groups)', (0.010, 0.0, -0.015), 'pct',
         'Base = 9M-26 y/y units growth by group (merchandise +1.8%, intermodal +1.3%, coal +4.7%); Bull +1pt, Bear −1.5pts (Q3-26: +3% total; tighter trucking market per the release).'),
        ('q4_rpu_d', '  Q4/26E revenue per unit y/y: Δ vs the Q3-26 y/y trend (pts, all groups)', (0.010, 0.0, -0.010), 'pct',
         'Base = Q3-26 y/y revenue-per-unit growth by group (merchandise +8%, intermodal +18%, coal +9%, of which fuel surcharge ≈ 8 pts of total revenue growth); the 10-Q expects Q4 fuel surcharge revenue to increase y/y.'),
        ('seq_or', '  Q4/26E adjusted operating ratio: Q3→Q4 sequential change (pts; 2016–25 best / average / worst, excl. 2024)', (seq_or_formula('MIN'), seq_or_formula('AVERAGE'), seq_or_formula('MAX')), 'pct',
         'Live formulas on the Q4 columns of the "Adjusted OR change vs prior quarter" row (2016–23, 2025): min −2.6 pts (2018), average +0.4 pts, max +2.0 pts (2025). 2024 excluded (Q3-24 line-sale gains inside the base).'),
    ],
    'points': [
        ('pt_dep', '  Q4/26E depreciation ($m)', 366.0, 'm', 'Q3-26 $363m; rising with the asset base (+$3m a quarter in 2026).'),
        ('pt_othinc', '  Q4/26E other income – net ($m)', 30.0, 'm', '9M-26 $97m (~$32m a quarter); Q3-26 $30m.'),
        ('pt_int', '  Q4/26E interest expense on debt ($m)', 192.0, 'm', 'Q3-26 $193m; no new issuance (Merger Agreement debt restrictions), $649m current maturities.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.233, 'pct', '9M-26 effective rate 23.3% ($621m / $2,661m); 2025 21.6% (incl. discrete benefits).'),
        ('pt_merger', '  Q4/26E merger-related expenses ($m)', 45.0, 'm', '9M-26 $145m ($52m / $51m / $42m by quarter): retention agreements, advisors, legal.'),
        ('pt_eoi', '  Q4/26E Eastern Ohio incident expense, net of recoveries ($m)', 20.0, 'm', '9M-26 $53m ($10m / $15m / $28m); recoveries largely exhausted ($7m in 9M-26).'),
        ('pt_sbc', '  Q4/26E share-based compensation ($m)', 16.0, 'm', '2025 $63m; 9M-26 per XBRL cash-flow statement.'),
        ('pt_capex', '  2026E property additions ($m)', MAN['guidance']['capex_2026'], 'm', MAN['guidance']['capex_src']),
    ],
    'lev': (2.75, 2.50, 2.25),
    'lev_note': ('Net debt $15.0bn at 30-Sep-2026 ≈ 2.7x adjusted EBITDA (2025 2.75x; 2019 ~2.3x). Debt-to-total-capitalization 49.8% (company metric). Target = maximum net debt / adjusted EBITDA '
                 'up to which surplus cash is returned via buybacks once the merger restriction lapses (model: from 2028E, standalone case); below it, cash accumulates / repays commercial paper. Bull = more buybacks.'),
    'blocks': [
        ('MER_VOL', 'MER_VOL (Merchandise units y/y)', 0.010, -0.020, [0.020, 0.020, 0.020, 0.015, 0.015],
         '9M-26 +1.8% (chemicals +9%, metals +1%, agriculture flat, automotive −2%); 2015–25 CAGR −1%. Base +2% / +1.5% on industrial-production-led growth and truck conversion (assumption).', 'pct', False),
        ('MER_RPU', 'MER_RPU (Merchandise revenue per unit y/y)', 0.010, -0.020, [0.030, 0.030, 0.030, 0.030, 0.030],
         '9M-26 +5% (fuel surcharge + pricing); 2015–25 CAGR +3%. Base +3%: core pricing above rail inflation, flat fuel surcharge (assumption).', 'pct', False),
        ('IM_VOL', 'IM_VOL (Intermodal units y/y)', 0.015, -0.030, [0.030, 0.030, 0.025, 0.025, 0.020],
         '9M-26 +1.3% (domestic +7%, international −7% on East Coast port congestion); 2015–25 CAGR +1%. Base +3% → +2% on truck conversion (assumption).', 'pct', False),
        ('IM_RPU', 'IM_RPU (Intermodal revenue per unit y/y)', 0.010, -0.020, [0.020, 0.025, 0.025, 0.025, 0.025],
         '9M-26 +12% (fuel surcharge; Q3-26 +18%); 2015–25 CAGR +2%. Base +2–2.5%: pricing, flat fuel (assumption).', 'pct', False),
        ('COAL_VOL', 'COAL_VOL (Coal units y/y)', 0.020, -0.030, [-0.030, -0.030, -0.030, -0.030, -0.030],
         '9M-26 +4.7% (export +11%, utility +4% on gas prices / restocking); 2015–25 CAGR −4%. Base −3% p.a.: secular utility decline, export volatility (assumption).', 'pct', False),
        ('COAL_RPU', 'COAL_RPU (Coal revenue per unit y/y)', 0.020, -0.030, [0.000, 0.010, 0.010, 0.010, 0.010],
         '9M-26 +1% (fuel surcharge offset by lower export pricing); 2015–25 CAGR +3% (2022–23 export spike). Base flat then +1% (assumption).', 'pct', False),
        ('OR', 'OR (Adjusted operating ratio, 2027E+)', -0.010, 0.015, [0.635, 0.625, 0.615, 0.605, 0.600],
         'Adjusted OR: 2025 65.0%, 9M-26 ≈ 66.4% (fuel +3 pts); 2019 best 64.9% (GAAP). Long-range plan (merger proxy) implied 61.8% (2027) → 58.7% (2030). Base 63.5% → 60.0% (assumption: productivity, fuel normalising); Bull −1pt, Bear +1.5pts.', 'pct', False),
        ('FUEL', 'FUEL (Fuel % of revenues, 2027E+)', 0.000, 0.000, [0.100, 0.095, 0.095, 0.095, 0.095],
         '2025 7.7%, 9M-26 10.8% (higher diesel; ~95% of revenue carries fuel surcharges, so the surcharge sits in revenue per unit). Base 10% → 9.5% (pass-through, no scenario Δ).', 'pct', False),
    ],
    'etr': 0.235, 'sbc_pct': 0.005, 'dps_q': 1.35, 'dps_g': 0.05, 'deftax_pct': 0.25,
    'gains_ae': -100.0, 'gains_q4': -10.0, 'oth_ae': -150.0, 'oth_q4': -60.0, 'props_ae': 150.0, 'props_q4': 40.0, 'inv_ae': -100.0, 'stock_ae': 0.0,
    'iss_q4': 0.05, 'iss_ae': 0.3, 'dil': 0.6, 'bb_cap': 3500.0,
    'capex_pct': {2027: 0.170, 2028: 0.165, 2029: 0.160, 2030: 0.160, 2031: 0.160},
    'dep_rate': 0.039, 'refi': 1.0,
    'mat': {2026: 607.0, 2027: 625.0, 2028: 602.0, 2029: 611.0, 2030: 600.0, 2031: 600.0},
    'repay_note': ('FY2025 10-K Note 11 maturities: 2026 $607m, 2027 $625m, 2028 $602m, 2029 $611m, 2030 $600m, 2031 and later $14,042m (2031E $600m assumed). '
                   '9M-26 repayments $618m (incl. the 2026 maturity). 2027E+ maturities refinanced per the refinancing % (assumption).'),
    'repay_q4': 0.0, 'min_cash': 1000.0,
    'r_notes': {y: 0.0465 for y in range(2027, 2032)},
    'r_notes_note': 'Weighted-average coupons 4.19–5.22% (10-K Note 11); 2025 interest $792m on ~$17.1bn ≈ 4.6%; May-2025 notes 5.10%.',
    'inv_yield': 0.025, 'othinc_oth': 30.0,
    'merger_ae': {2027: 100.0, 2028: 0.0, 2029: 0.0, 2030: 0.0, 2031: 0.0},
    'eoi_ae': {2027: 40.0, 2028: 30.0, 2029: 20.0, 2030: 10.0, 2031: 0.0},
    'wc': WC, 'lrp': LRPD,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $332.09 (price of shares withheld for taxes on RSU vestings on 24-Oct-2026, Forms 4 filed 26-Oct-2026 — the latest share price in an SEC filing; '
                '~$75bn market cap); update to market. Union Pacific consideration: 1.0 UNP share + $88.82 cash (UNP $300.62 on 10-Nov-2026 per UNP Forms 4).'),
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
        if row.spec2 and 'qe' not in kw and 'qe_in' not in kw: return None, False
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
            v = kw['ae_in']
            if isinstance(v, dict):
                if col.year not in v: return None, False
                return v[col.year], True
            return v, True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'g_units', 'g_rpu', 'merch_units', 'merch_rpu', 'merch_rev', 'im_units', 'im_rpu', 'im_rev', 'coal_units', 'coal_rpu', 'coal_rev',
          'o_adj', 'r_adj', 'r_ebit', 'is_oi', 'is_dep', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_comp', 'is_fuel', 'is_ni', 'eps_dil', 'dps',
          'is_rev_merch', 'is_rev_im', 'is_rev_coal', 'bs_ppe', 'cf_capex'}
CAGR_A = {'or_gaap', 'or_adj', 'o_adj_m', 'r_adj_m', 'r_ebit_m', 'is_or', 'gm_rev', 'gm_units', 'gm_rpu', 'gm_or', 'gm_aor', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_comp', 'gm_fuel',
          'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'c_comp', 'c_psr', 'c_fuel', 'c_dep', 'c_mat', 'd_sbc_pct', 'wc_nwc_p', 'is_etr',
          'e_rate', 'fcf_eb', 'merch_mix', 'im_mix', 'coal_mix', 'fsc_p', 'im_dom_p', 'payout', 'hr_d2c'}
A = {y: ANN[y].c for y in ANN}

def style_cagr(ws, r, on):
    src = 16 if on else 12
    for c in CAGR:
        ws[f'{c}{r}']._style = copy.copy(TM[f'{L(CI(c) + TSHIFT)}{src}']._style)

def write_row(ws, row):
    r = row.r; arch = ARCH[row.arch]
    clone_row_style(ws, arch, r)
    ws.cell(r, 2).value = row.label or None
    if row.kw.get('note'):
        nt = row.kw['note']; ws[f'{NOTE}{r}'] = ('→ ' + nt[2:]) if nt.startswith('= ') else nt
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
                if t: comment(cell, f'{pkey(col)}: {t}', 420, 120)
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

REL = 'Source: Norfolk Southern earnings releases (Form 8-K Item 2.02; financial statements exhibit / Ex. 99.2 "Quarterly Financial Data") — '
LABEL_SOURCES = {
    'merch_units': ('Source: Forms 10-Q / 10-K, MD&A "Railway Operating Revenues" tables (revenues, units and average revenue per unit by market group). Q4 = year (10-K) − nine months (Q3 10-Q); '
                    'Q4 revenue per unit derived as revenue ÷ units. Units = carloads (intermodal: containers and trailers).'),
    'merch_rev': REL + 'consolidated statements of income, railway operating revenues by commodity group ("General merchandise" to 2012), as originally reported.',
    'ms_u_agr': 'Source: 10-Q / 10-K MD&A market-group tables. Group definitions changed: five groups to 2018 (Chemicals; Agriculture/consumer products/government; Metals and construction; Automotive; Paper, clay and forest products); '
                '2019: Chemicals, Agriculture products, Metals and construction, Automotive, Forest and consumer; from 2020 four groups (Agriculture, forest and consumer products; Chemicals; Metals and construction; Automotive). Each basis as published, not restated.',
    'im_dom': 'Source: 10-Q / 10-K MD&A "Intermodal units by market" (domestic / international), where published.',
    'coal_t_utility': 'Source: 10-Q / 10-K MD&A "Coal tonnage by market" (utility, export, domestic metallurgical, industrial).',
    'fsc': 'Source: 10-Q / 10-K MD&A narrative ("fuel surcharge revenue totaled $x million…"); only periods where the sentence was parsed; Q4 not derived.',
    'is_rev': REL + 'consolidated statements of income, as originally reported in each period\'s release (FY2006–12 from the fourth-quarter releases; quarters from Q1-13).',
    'is_comp': ('Source: release statements of income. Expense classifications since 2008: compensation & benefits; purchased services & rents; fuel; depreciation; materials & other. '
                'FY2006–07 were presented in seven lines (materials, services & rents; Conrail rents & services; diesel fuel; casualties & other claims; other) — the model uses the FY2008 10-K recast into the five classifications (totals unchanged).'),
    'is_merger': REL + 'separate income-statement lines: "Merger-related expenses" (from Q3-25), "Restructuring and other charges" (2024+), "Eastern Ohio incident" (2023+), "Loss on asset disposal" (2020).',
    'is_ni_pub': REL + 'consolidated statements of income (net income, diluted EPS, weighted-average diluted shares). Shares in thousands in the 2006–07 releases, converted to millions.',
    'o_pub': 'Source: press releases (Form 8-K Ex. 99.1), "Reconciliation of Non-GAAP Financial Measures" tables, published only in periods with special items (Q4/FY2017; Q1/FY2020; 2023–26 quarters).',
    'e_pub': 'Source: press-release non-GAAP reconciliations (adjusted diluted EPS), published only in periods with special items.',
    'sp_other': 'Source: Q3-20 release note 1 ($99m equity-method investment impairment in purchased services & rents); Q4-24 release note 1 (railway line-sale gains $433m in materials & other: Q3 $380m, Q4 $53m); '
                'Q4-17 reconciliation (−$151m tax-reform effect in operating expenses). manual_items.json.',
    'e_nonop': 'Source: 2024 release notes "Shareholder Advisory Costs" (other income – net: Q1 $21m, Q2 $29m, Q3 $1m, Q4 $8m; FY $59m). manual_items.json.',
    'e_disc': 'Source: Q4-17 reconciliation (remeasurement of net deferred tax liabilities, $3,482m benefit); Q4-24 release note 6 ($27m deferred-tax reduction from a subsidiary restructuring, Q1-24).',
    'cf_ni': REL + 'consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). Share-based compensation from XBRL (AllocatedShareBasedCompensationExpense).',
    'bs_cash': REL + 'consolidated balance sheets (period ends). 2006: cash, cash equivalents and short-term investments were one line; split using the cash-flow ending cash (derived). Shares outstanding from the common-stock caption.',
    'ds_total': 'Source: FY2025 10-K Note 11 (debt maturities, facilities); Q3-26 10-Q Notes 1 and 10 (merger restrictions, finance lease).',
    'sec_mg': 'Source: Form 8-K 29-Jul-2025 (Merger Agreement, Item 1.01); DEFM14A 1-Oct-2025; 8-K 17-Nov-2025 (shareholder vote); 8-K 19-Dec-2025 (STB application); Q3-26 10-Q Note 1.',
    'dps': 'Source: XBRL (CommonStockDividendsPerShareDeclared); 2007 onward.',
    'lrp_rev': 'Source: DEFM14A (1-Oct-2025), "Certain Norfolk Southern Unaudited Prospective Financial Information" — Norfolk Southern management unaudited projections, 2025E–2030E. Not guidance.',
}
CELL_COMMENTS = {}
def comments_setup():
    a06, a07, a17 = A[2006], A[2007], A[2017]
    rc06 = ('FY2006 expense classifications per the FY2008 10-K recast (compensation & benefits $2,637m; purchased services & rents $1,578m; fuel $1,095m; depreciation $738m; materials & other $802m). '
            'As originally reported (seven lines): compensation & benefits 2,637; materials, services & rents 1,895; Conrail rents & services 126; depreciation 738; diesel fuel 977; casualties & other claims 220; other 257.')
    rc07 = ('FY2007 expense classifications per the FY2008 10-K recast. As originally reported (seven lines): compensation & benefits 2,552; materials, services & rents 1,853; Conrail rents & services 102; '
            'depreciation 775; diesel fuel 1,062; casualties & other claims 208; other 295 (FY2007 fourth-quarter release).')
    CELL_COMMENTS['is_comp'] = {a06: rc06, a07: rc07}
    CELL_COMMENTS['is_opex'] = {a17: 'FY2017 as originally reported ($6,965m). The 2018 releases restated 2017 to $7,029m (ASU 2017-07: non-service pension benefit moved from operating expenses to other income – net; '
                                     'income from railway operations $3,586m → $3,522m). The model keeps the original; 2018 y/y is therefore ~1 pt flattered on the operating ratio.'}
    CELL_COMMENTS['bs_cash'] = {a06: 'Balance sheet printed "Cash, cash equivalents and short-term investments" $918m; cash $527m per the cash-flow statement, short-term investments $391m derived.'}
    CELL_COMMENTS['sh_basic'] = {a06: 'Release shares in thousands (405,988 basic / 414,700 diluted) converted to millions.'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('2006–Q3/17: no adjusted measures published — adjusted = GAAP (NSC publishes reconciliations only when special items occur)', None),
        q(2017, 4): ('Q4/FY2017: tax-reform effects adjusted (−$151m in operating expenses; $3,482m deferred-tax remeasurement benefit)', 'Press release 24-Jan-2018, "Reconciliation of Non-GAAP Financial Measures".'),
        q(2018, 1): ('2018–19: no special items — adjusted = GAAP', None),
        q(2020, 1): ('2020: loss on asset disposal (Q1 locomotive rationalization $385m) and Q3 equity-investment impairment ($99m) adjusted out; 2021–22 adjusted = GAAP', None),
        q(2023, 1): ('2023+: Eastern Ohio incident costs net of insurance recoveries adjusted out ("adjusted income from railway operations / operating ratio / diluted EPS")', None),
        q(2024, 1): ('2024: + restructuring and other charges, railway line-sale gains (Q3 $380m, Q4 $53m), shareholder advisory costs (EPS) and a deferred-tax adjustment (EPS)', None),
        q(2025, 3): ('Q3/25+: + merger-related expenses (Union Pacific)', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–Q3/17: no adjusted EPS published — adjusted = GAAP diluted EPS (flag)', None),
        q(2017, 4): ('Q4/FY2017: adjusted EPS excludes the $3,482m deferred-tax remeasurement and the $151m operating-expense effect of tax reform', None),
        q(2020, 1): ('2020: adjusted EPS excludes the locomotive charge ($385m; $1.11/share Q1) and investment impairment ($99m; FY $1.41/share total)', None),
        q(2023, 1): ('2023+: items tax-effected "based on the applicable tax rates to which the non-GAAP adjustments related" (company wording)', None),
        q(2024, 1): ('2024: + shareholder advisory costs (other income – net) and the $27m deferred-tax adjustment (Q1); railway line-sale gains removed', None),
    }
    DEFS['ms_def'] = {
        'C': ('2006–18: five market groups — Chemicals; Agriculture / consumer products / government; Metals & construction; Automotive; Paper, clay & forest products', None),
        q(2019, 1): ('2019: five groups — Chemicals; Agriculture products; Metals & construction; Automotive; Forest & consumer (2018 comparatives recast in the 2019 filings; not applied)', None),
        q(2020, 1): ('2020+: four groups — Agriculture, forest & consumer products; Chemicals; Metals & construction; Automotive', None),
    }
def write_defs(ws, row):
    for c, (txt, cm) in DEFS[row.key].items():
        cell = ws[f'{c}{row.r}']; cell.value = txt
        cell.font = Font(name='Calibri', sz=10, b=True, i=True, color='FFC00000')
        if cm: comment(cell, cm)

def write_scen(ws):
    srcrow = {'hdr': 9, 'out_hdr': 11, 'pt_hdr': 15, 'out': 12, 'pt': 16, 'lev': 28, 'blk': 30, 'yr': 31}
    def val(v): return v() if callable(v) else v
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
                v = val(v); ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF[nf]
                set_color(ws[f'{col}{r}'], BLACK if isinstance(v, str) and v.startswith('=') else BLUE)
            ws[f'{SNOTE}{r}'] = note
        elif kind == 'pt':
            _, _, lab, _, v, _, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBASE}{r}'] = val(v); ws[f'{SBASE}{r}'].number_format = NF[nf]; set_color(ws[f'{SBASE}{r}'], BLUE); ws[f'{SNOTE}{r}'] = note
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: the Q4/26E volume and revenue-per-unit Δs and the operating-ratio seasonality anchor (best / average / worst), '
            '2027E–2031E units and revenue-per-unit growth by commodity group, the adjusted operating-ratio lever and the leverage ceiling for 2028E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Norfolk Southern Corporation (NYSE: NSC) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; units in thousands; revenue per unit in USD) · Calendar fiscal year · '
                'Source: Norfolk Southern Forms 10-K / 10-Q, Form 8-K earnings releases (financial statements exhibits / Ex. 99.1–99.2) and merger filings (8-K 29-Jul-2025, DEFM14A 1-Oct-2025), '
                'SEC EDGAR CIK 0000702165; XBRL company facts; investor-relations releases at norfolksouthern.com are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported. FY2006–07 expense classifications per the FY2008 10-K recast (five lines); 2017 not restated for ASU 2017-07 (memo in cell comment). One reportable segment '
                '(railway operations); revenues by commodity group (merchandise / intermodal / coal) with market-group memo rows on each published basis. Adjusted measures only where NSC published them '
                '(2017 tax reform; 2020 impairments; 2023+ Eastern Ohio incident; 2024 line sales / restructuring; 2025+ merger costs). Pending acquisition by Union Pacific (1.0 UNP share + $88.82 cash; '
                'STB review; expected "by early 2027"): operating forecast is standalone; buybacks suspended; merger block values the consideration. Q4/26E anchored on 9M-26 trends and OR seasonality (no guidance on EDGAR).')
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
        p = os.path.join(BASE, f'NSC_{scen}.xlsx')
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
    p = os.path.join(BASE, 'NSC_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
