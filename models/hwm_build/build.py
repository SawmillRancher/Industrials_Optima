"""Build HWM_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'HWM_Model.xlsx')
G26 = MAN['guidance_fy26']

# ====================================================================== inputs (V0)
def wc_inputs():
    q, b = DATA['Q4-25']['x'], DATA['2025']['x']
    rev, cogs = q['rev'] * 4, q['cogs'] * 4
    return {'dso': round(b['bs_ar'] / rev * 365, 1), 'dio': round(b['bs_inv'] / cogs * 365, 1), 'dpo': round(b['bs_ap'] / cogs * 365, 1),
            'ocl': round(b['bs_ocl'] / rev, 4)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end (31-Dec-2025) levels on annualised Q4/25 sales / cost of goods sold (DSO {WC["dso"]}d, inventory {WC["dio"]}d, '
              f'payables {WC["dpo"]}d, other current liabilities {WC["ocl"]:.1%} of sales); year ends are compared with year ends (receivables are seasonally low at year end).')

V0 = {
    'out_hdr': 'FY26 guidance — Q3 2026 release (8-K Ex. 99.1, 29-Oct-2026)',
    'out_note': ('FY26 increased: revenue $10.29–10.31bn (baseline $10.30bn, +$250m), Adjusted EBITDA $3.325–3.335bn (+$100m), adjusted EPS $5.49–5.51 (+$0.23), free cash flow '
                 '$1.95–2.05bn (+$100m). Q4: revenue $2.74–2.76bn, Adjusted EBITDA $895–905m, adjusted EPS $1.49–1.51. FY2027 revenue ~$11.5bn. All from the SEC-filed release; '
                 'no guidance from outside EDGAR is used.'),
    'outlook': [
        ('out_rev', '  FY26 revenue ($m)', tuple(G26['rev']), 'm', 'Guided $10,290–10,310m. Drives the Q4/26E sales calibration.'),
        ('out_ebitda', '  FY26 Adjusted EBITDA ($m)', tuple(G26['adj_ebitda']), 'm', 'Guided $3,325–3,335m. Drives the Q4/26E segment-margin calibration.'),
        ('out_eps', '  FY26 adjusted EPS ($) — memo', tuple(G26['adj_eps']), 'ps', 'Guided $5.49–5.51 (information row; compare the model).'),
        ('out_fcf', '  FY26 free cash flow ($m) — memo', tuple(G26['fcf']), 'm', 'Guided $1,950–2,050m (information row).'),
        ('out_q4rev', '  Q4 2026 revenue ($m) — memo', tuple(G26['q4_rev']), 'm', 'Guided $2,740–2,760m (information row; the FY guidance less nine months actual gives $2,727–2,747m).'),
        ('bb26', '  Q4/26E share repurchases ($m)', (600.0, 500.0, 300.0), 'm', 'Q3 2026 $500m at $264.77; $1.1bn year to date to 28-Oct-2026; $5.397bn authorized (assumption by scenario).'),
    ],
    'points': [
        ('pt_corp', '  Q4/26E adjusted corporate expense ($m)', 29.0, 'm1', 'Q2 and Q3 2026 $29m each (Σ Segment Adjusted EBITDA − Adjusted EBITDA).'),
        ('pt_da', '  Q4/26E depreciation and amortization ($m)', 95.0, 'm1', 'Q3 $93m (first full quarters of CAM); rising with capex.'),
        ('pt_amort', '  Q4/26E amortization of intangibles ($m; assumption)', 15.0, 'm1',
         'Legacy ~$8m a quarter (FY2025 10-K: ~$30–36m a year) + CAM / Brunner intangibles $425m over an assumed 15 years (~$7m a quarter; lives not disclosed).'),
        ('pt_int', '  Q4/26E interest expense, net ($m)', 48.0, 'm1', 'Q3 $48m (notes $4.05bn + $390m commercial paper).'),
        ('pt_oth', '  Q4/26E other expense, net ($m)', 8.0, 'm1', 'Q3 $8m; nine months $21m.'),
        ('pt_etr', '  Q4/26E tax rate (GAAP & operational)', 0.20, 'pct', 'Operational tax rate 20.3% in nine months 2026 and 20.0% in Q3; the Q4 guidance (EPS $1.50 on EBITDA $900m) implies ~20%.'),
        ('pt_capex', '  FY26 capital expenditures ($m; assumption)', 500.0, 'm1', 'Nine months $345m (Q3 $147m). Not guided as a number; consistent with FCF guidance of ~$2.0bn.'),
    ],
    'lev': (1.25, 1.0, 0.75),
    'lev_note': ('Net debt $3.9bn at 30-Sep-26 ≈ 1.3x LTM Adjusted EBITDA after the debt-funded CAM acquisition (1.0x at YE2025). Target = leverage up to which surplus cash is returned '
                 'via buybacks ($5.397bn authorization); below it free cash flow reduces net debt. No published leverage target — assumption. Bull = more buybacks (higher target).'),
    'blocks': [
        ('EP_G', 'EP_G (Engine Products sales y/y)', 0.03, -0.05, [0.14, 0.12, 0.10, 0.08],
         'Q3/26 +33% (commercial aerospace +32%, gas turbines +45%, spares); normalising as new airfoil capacity comes on. Base 2027E is set so total sales ≈ the $11.5bn outlook.', 'pct', False),
        ('FS_G', 'FS_G (Fastening Systems sales y/y)', 0.03, -0.05, [0.12, 0.08, 0.07, 0.06],
         'Q3/26 +41% reported, +10% organic. 2027E includes the first-quarter annualisation of CAM (acquired 6-Apr-2026; FY2026 revenue ~$485–495m) on ~8% organic.', 'pct', False),
        ('ES_G', 'ES_G (Engineered Structures sales y/y)', 0.03, -0.05, [0.03, 0.05, 0.05, 0.04],
         'Q3/26 −4% reported, +8% organic (Savannah disk forging sold 31-Mar-2026: $34m a quarter). 2027E includes one more quarter without Savannah; product-mix rationalisation continues.', 'pct', False),
        ('FW_G', 'FW_G (Forged Wheels sales y/y)', 0.04, -0.08, [0.06, 0.05, 0.04, 0.03],
         'Q3/26 +32% (North America truck recovery and aluminum cost pass-through); cyclical — 2023–25 sales fell from $1.15bn to $1.04bn.', 'pct', False),
        ('EP_M', 'EP_M (Engine Products Segment Adjusted EBITDA margin)', 0.01, -0.03, [0.395, 0.400, 0.405, 0.410],
         'Q3/26 39.1% (FY2025 33.4%, FY2021 24.7%); volume leverage, price and spares mix vs headcount added ahead of growth.', 'pct', False),
        ('FS_M', 'FS_M (Fastening Systems margin)', 0.01, -0.03, [0.300, 0.310, 0.315, 0.320],
         'Q3/26 29.4% (FY2025 30.4%) after CAM dilution (CAM >20% before synergies); synergies and wide-body recovery.', 'pct', False),
        ('ES_M', 'ES_M (Engineered Structures margin)', 0.01, -0.03, [0.240, 0.245, 0.250, 0.250],
         'Q3/26 23.7% (FY2025 21.6%, FY2022 13.9%); footprint optimisation and exit of lower-margin work.', 'pct', False),
        ('FW_M', 'FW_M (Forged Wheels margin)', 0.01, -0.03, [0.270, 0.275, 0.280, 0.280],
         'Q3/26 26.3% (FY2025 28.5%); aluminum pass-through dilutes the margin when metal prices rise.', 'pct', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 0.0, 0.0, [0.0, 0.0, 0.0, 0.0],
         'Base none: after CAM ($1.8bn) and Brunner ($120m) the company emphasises buybacks ($5.4bn authorization). Lever available for bolt-ons (set a Base amount or a Bull Δ).', 'm', True),
    ],
    'corp_pct': 0.011,
    'da_pct': {2027: 0.0345, 2028: 0.035, 2029: 0.035, 2030: 0.035},
    'amort_in': {2027: 61.0, 2028: 61.0, 2029: 60.0, 2030: 59.0},
    'amort_note': (MAN['amort']['src'] + ' Model input (assumption): legacy ~$33m a year + CAM / Brunner $425m over 15 years (~$28m a year). Used only to split the PP&E and intangibles roll-forwards; '
                   'history is not shown because the releases print total D&A only.'),
    'sga_pct': 0.045, 'rd_pct': 0.004, 'sbc_pct': 0.0105, 'etr': 0.21, 'oth': 35.0,
    'capex_pct': {2027: 0.05, 2028: 0.05, 2029: 0.045, 2030: 0.04},
    'dps_q': 0.14, 'dps_g': 0.15, 'def_q4': 15.0, 'def_ae': 50.0, 'ofin_q4': -5.0, 'ofin_ae': -75.0, 'iss_q4': 0.1, 'iss_ae': 0.8, 'dil': 2.0,
    'iss_notes': {2026: 0.0, 2027: 0.0, 2028: 1200.0, 2029: 1500.0, 2030: 500.0},
    'repay': {2026: 0.0, 2027: 0.0, 2028: 700.0, 2029: 1000.0, 2030: 0.0},
    'mat': {2026: 0.0, 2027: 700.0, 2028: 1000.0, 2029: 0.0, 2030: 500.0},
    'repay_note': ('Q3-26 10-Q Note O: 2028 — 6.750% Bonds $300m + 3.750% Notes $400m; 2029 — 3.000% Notes $700m + 3.900% Notes $300m; 2031 — 4.850% Notes $500m; then 2032 $500m, '
                   '2036 $500m, 2037 $625m, 2042 $250m. No maturities in Q4 2026 or 2027.'),
    'min_cash': 500.0,
    'r_notes': 0.046,
    'r_notes_note': ('Weighted coupon ~4.6% on $4,075m of notes at 30-Sep-2026 (3.000%–6.750%; the 2028 Bonds and 2031 Notes are swapped to JPY 3.880% / EUR 3.720%, which lowers the '
                     'cash cost slightly). Q3 2026 interest expense, net $48m.'),
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $220.00 (provided by the user, 20-Nov-2026; ~$88bn market cap). Reference: latest SEC-filed price $251.49 = average price paid for '
                'shares repurchased in September 2026 (Q3-26 10-Q Part II Item 2). Update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base none). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': 'Company FY26 revenue guidance $10,290m / $10,300m / $10,310m (low / baseline / high; increased 29-Oct-2026). Drives the sales calibration.',
    'eb_guid_note': 'Company FY26 Adjusted EBITDA guidance $3,325m / $3,330m / $3,335m (increased 29-Oct-2026). Drives the segment-margin calibration.',
    'eps_guid_note': 'Company FY26 adjusted EPS guidance $5.49 / $5.50 / $5.51 (information row; the model is calibrated to revenue and Adjusted EBITDA, the measures above it).',
    'rev_2027': G26['rev_2027'],
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
            v = kw['ae_in']; return (v.get(col.year) if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'ep_rev', 'fs_rev', 'es_rev', 'fw_rev', 'ep_ebitda', 'fs_ebitda', 'es_ebitda', 'fw_ebitda', 'em_ca', 'em_df', 'em_ct', 'em_io',
          'o_adj', 'g_adj', 'r_adj', 'r_ebitda', 'r_ebit', 'is_oi', 'd_da', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_sga',
          'is_ni', 'is_cont', 'eps_dil', 'dps', 'corp'}
CAGR_A = {'ep_m', 'fs_m', 'es_m', 'fw_m', 'g_adjm', 'o_adj_m', 'r_adj_m', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_ep', 'gm_fs', 'gm_es', 'gm_fw', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_sga', 'gm_rd', 'gm_adjop_m', 'gm_cogs', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x',
          'd_sga', 'd_da_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'corp_pct', 'ep_mix', 'fs_mix', 'es_mix', 'fw_mix',
          'em_ca_p', 'em_df_p', 'em_ct_p', 'em_io_p'}
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
                if t: comment(cell, f'Company items ({pkey(col)}): {t}', 400, 130)
            if col.kind in HISTK and xget(pkey(col), 'seg_recast') and row.kw.get('data', '')[:2] in ('ep', 'es'):
                o = xget(pkey(col), row.kw['data'] + '_orig')
                if o is not None and abs(o - v) > 1e-9:
                    comment(cell, f'Recast for the Q1-26 segment realignment (titanium alloy location moved from Engine Products to Engineered Structures), '
                                  f'from the 2026 release panels. As originally reported: {o:,.0f}.', 380, 90)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    rc = CELL_COMMENTS.get(row.key, {})
    for c, t in rc.items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2030]}{r}/{A[2025]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2020]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2022]}{r})^(1/3)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2019]}{r})^(1/6)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2026, 2031))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2023, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2019, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: Howmet Aerospace earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'ep_rev': REL + ('"Segment Information" panels, each period from its own release (as originally reported). FY2019 and Q1/20: recast continuing-operations comparatives '
                     '(Q4-20 and Q1-21 releases). 2025: as recast in the 2026 releases for the Q1-26 segment realignment.'),
    'ep_ebitda': REL + ('Segment Adjusted EBITDA (segment measure from Q1-22; 2021 from the 2022 release panels). 2019–2020: segment operating profit + segment provision for '
                        'depreciation and amortization, the identity behind the company recast (verified on every 2021 period).'),
    'corp': 'Derived: Σ Segment Adjusted EBITDA − Adjusted EBITDA. The release line "Corporate expense" (memo row) also carries corporate D&A and the special items booked in Corporate.',
    'em_ca': ('Source: Forms 10-Q / 10-K, revenue note (disaggregation by end market). Q4 = year (10-K) − nine months (Q3 10-Q). Q1/20, Q2/20 and FY2019 from the following year\'s '
              'comparatives (continuing operations; commercial / defense split first shown in Q3-20).'),
    'em_gt': 'Gas turbines / other basis introduced in the FY2025 Form 10-K; 2025 quarters from the prior-year columns of the 2026 Forms 10-Q (Q4/25 = year − nine months).',
    'is_rev': REL + 'Statement of Consolidated Operations, as originally reported (FY2019 and Q1/20 recast for the 1-Apr-2020 separation of Arconic Corporation). Cross-checked to XBRL company facts.',
    'd_da': REL + 'Statement of Consolidated Operations ("Provision for depreciation and amortization").',
    'sp_oth': REL + '"Operating income excluding special items" / "Adjusted operating income" and Adjusted EBITDA reconciliations; company item labels in the cell comments.',
    'o_pub': REL + 'published Q1/20–Q4/21 and again from Q3/23 (2019–21 annual included); not published Q1/22–Q2/23.',
    'r_adj_pub': REL + '"Adjusted EBITDA excluding special items" (to 2025) / "Adjusted EBITDA" (2026). Not in the release schedules for FY2019, Q1/20, Q3/20, Q4/20, FY2020 and FY2021.',
    'e_pub': REL + '"Income from continuing operations excluding special items" (to FY2021), "Net income excluding special items" (2022–25), "Adjusted net income" (2026).',
    'cf_ni': REL + ('Statement of Consolidated Cash Flows (year to date; discrete quarters derived, Q4 = FY − 9M). Q1/20 and FY2020 include Arconic Corporation to 31-Mar-2020 '
                    '(not segregated by the company). H1-20 as revised in Q3-20 (from the Q2-21 release).'),
    'bs_cash': REL + 'Consolidated Balance Sheet (period ends); 31-Dec-2020 per the 2020 Form 10-K. No balance sheet before 30-Jun-2020 (pre-separation).',
    'ppa_cons': 'Source: Q3-26 Form 10-Q Note C (preliminary allocation for CAM and Brunner combined); cash paid from the cash-flow statement.',
    'sh_basic': REL + 'Statement of Consolidated Operations (average number of shares). No stock splits in the period.',
    'ds_total': 'Source: release balance sheets; Q3-26 Form 10-Q Note O (debt); 8-K 3-Mar-2026 (notes offering).',
    'fcf_pub': REL + '"Adjusted free cash flow" (2020–21) / "Free cash flow" (2022+) reconciliations.',
}
CELL_COMMENTS = {}
def comments_setup():
    q = lambda y, n: QC[(y, n)].c
    basis19 = ('Recast continuing operations: prior-year column of the Q4-20 release (Arconic Corporation in discontinued operations). The FY2019 Form 10-K reported '
               'consolidated Arconic Inc. (sales $14,192m).')
    basis20 = ('Recast continuing operations: prior-year column of the Q1-21 release. The Q1-20 Form 10-Q reported consolidated Arconic Inc. (sales $3,209m) because the '
               'separation completed on 1-Apr-2020.')
    CELL_COMMENTS['is_rev'] = {'C': basis19, q(2020, 1): basis20}
    CELL_COMMENTS['is_int'] = {q(2021, 2): MAN['corrections'][0]['note']}
    CELL_COMMENTS['is_loss'] = {q(2021, 2): MAN['corrections'][0]['note']}
    CELL_COMMENTS['bs_ta_pub'] = {q(2020, 4): MAN['corrections'][1]['note'], A[2020]: MAN['corrections'][1]['note']}
    CELL_COMMENTS['cf_cfo'] = {q(2020, 1): 'Consolidated cash flow incl. Arconic Corporation (prior-year column of the Q1-21 release, as revised); the company did not segregate discontinued operations.',
                               q(2020, 2): 'Derived from H1-20 as revised (prior-year column of the Q2-21 release) − Q1/20. The Q2-20 release showed $31m for the quarter before the Q3-20 reclassification of accounts payable / capital expenditures.',
                               A[2020]: 'FY2020 includes Arconic Corporation for Q1 (not segregated).'}
    CELL_COMMENTS['eps_pub'] = {'C': 'FY2019: sum of the continuing ($0.27) and discontinued ($0.76) diluted per-share lines; the release prints no total. Per-share amounts are computed independently (release footnote), so net income ÷ diluted shares differs by $0.02.',
                                A[2020]: 'FY2020: sum of the continuing ($0.48) and discontinued ($0.11) diluted per-share lines; the full-year statement prints no total.'}
    CELL_COMMENTS['sp_in_da'] = {q(2020, 2): 'Q2/20: operating income excluding special items $180m + D&A $73m = $253m vs published Adjusted EBITDA excluding special items $247m: $6m of the special items is recorded in D&A.'}
    CELL_COMMENTS['ep_ebitda'] = {'C': 'Derived: segment operating profit $621m + segment D&A $131m (see label comment).'}
    CELL_COMMENTS['ppa_cons'] = {q(2026, 2): MAN['ppa_note']}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2019–Q1/20: recast continuing operations; "operating income excluding special items"; Adjusted EBITDA n/p for FY2019, Q1/20, Q3/20–Q4/20, FY2020–21 (model = adjusted OI + D&A)',
              'The releases of Q3-20 and Q4-20 carry no Adjusted EBITDA reconciliation schedule; the Q1-21 and Q2-21 releases reconcile "Adjusted EBITDA excluding special items" for the current quarters only.'),
        q(2020, 2): ('Q2/20: first post-separation release; special items = restructuring, separation costs, plant fires, Grenfell Tower legal costs; $6m of special items in D&A', None),
        q(2022, 1): ('Q1/22: segment measure = Segment Adjusted EBITDA (2021 recast); adjusted operating income not published Q1/22–Q2/23 (model bridge from Adjusted EBITDA)', None),
        q(2023, 3): ('Q3/23: "adjusted operating income excluding special items" published again', None),
        q(2026, 1): ('Q1/26: labels shortened to Adjusted operating income / Adjusted EBITDA (special items excluded as before); acquisition and acquisition-related costs (CAM, Brunner; from Q4/25) in special items',
                     'From the Q1-26 release "Adjusted EBITDA" excludes special items; to 2025 the same measure was called "Adjusted EBITDA excluding special items" and "Adjusted EBITDA" meant the figure before special items.'),
    }
    DEFS['e_def'] = {
        'C': ('FY2019–FY2021: "income from continuing operations excluding special items" (discontinued operations excluded); FY2019 adjusted EPS on the company share count (±0.02)', None),
        q(2022, 1): ('Q1/22+: "net income excluding special items" (no discontinued operations after 2021)', None),
        q(2026, 1): ('Q1/26: renamed Adjusted net income / Adjusted EPS; tax impact at statutory rates and discrete tax items unchanged', None),
    }
    DEFS['fcf_def'] = {
        q(2020, 2): ('Q2/20–Q4/21: "adjusted free cash flow" = cash from operations + cash receipts from sold receivables − capital expenditures (Q1/20 n/p)',
                     'The receivables securitization was restructured in 2021, after which collections are inside cash from operations.'),
        q(2022, 1): ('Q1/22+: free cash flow = cash from operations − capital expenditures', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 revenue and Adjusted EBITDA guidance end-points (high / baseline / low), '
            'Q4/26E buybacks, 2027E–2030E segment sales growth, segment margins, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Howmet Aerospace Inc. (NYSE: HWM) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP · USD millions (per-share data in USD; shares in millions) · Calendar fiscal year · Source: Howmet Aerospace Forms 10-K / 10-Q, Form 8-K earnings releases '
                '(Ex. 99.1) and deal / financing 8-Ks, SEC EDGAR (CIK 4281; named Arconic Inc. to 31-Mar-2020 and Alcoa Inc. to Oct-2016); XBRL company facts as cross-check; '
                'investor-relations releases at howmet.com are the same documents as filed on EDGAR. Guidance: SEC-filed release of 29-Oct-2026 only (nothing from outside EDGAR)')
    ws['B4'] = ('Basis notes: history starts with the post-separation company (Arconic Corporation spun off 1-Apr-2020). FY2019 and Q1/20 = recast continuing operations (P&L and '
                'segments only; first balance sheet 30-Jun-2020; Q1/20 and FY2020 cash flow include Arconic Corporation). Otherwise as originally reported. Segment Adjusted EBITDA '
                '2019–20 = segment operating profit + D&A. 2025 segments recast for the Q1-26 realignment (FY2024 not). Acquisitions: Brunner Feb-26, CAM 6-Apr-26; divestiture: '
                'Savannah disk forging 31-Mar-26. Q4/26E calibrated to FY26 revenue and Adjusted EBITDA guidance (29-Oct-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '3Y CAGR', '6Y CAGR'], ["25-'30", "20-'25", "22-'25", "19-'25"]):
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
        p = os.path.join(BASE, f'HWM_{scen}.xlsx')
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
    p = os.path.join(BASE, 'HWM_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
