"""Build FSS_Model.xlsx (Federal Signal Corporation) from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'FSS_Model.xlsx')
G26 = MAN['guidance_fy26']

# ====================================================================== inputs (V0)
def wc_inputs():
    """working-capital drivers at 30-Sep-2026 balances on last-twelve-month (Q4/25-Q3/26) net sales / cost of sales: the 31-Dec-2025 balances
    carry New Way's receivables and inventory (acquired 25-Nov-2025) against one month of its sales."""
    q = DATA['Q3-26']['x']
    ltm = ['Q4-25', 'Q1-26', 'Q2-26', 'Q3-26']
    rev = sum(DATA[p]['x']['rev'] for p in ltm); cogs = sum(DATA[p]['x']['cogs'] for p in ltm)
    return {'dso': round(q['bs_ar'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365), 'dpo': round(q['bs_ap'] / cogs * 365),
            'dep': round(q['bs_dep'] / rev, 3), 'ocl': round(q['bs_ocl'] / rev, 3), 'rev': rev, 'cogs': cogs}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at 30-Sep-2026 balances on LTM (Q4/25–Q3/26) net sales ${WC["rev"]:,.0f}m / cost of sales ${WC["cogs"]:,.0f}m (DSO {WC["dso"]}d, inventory {WC["dio"]}d, '
              f'payables {WC["dpo"]}d, customer deposits {WC["dep"]:.1%}, other current liabilities {WC["ocl"]:.1%} of sales). The 31-Dec-2025 balances carry New Way\'s '
              'working capital against one month of its sales, so the year-end basis is not used.')
AM = MAN['amort_sched']

V0 = {
    'out_hdr': 'FY26 outlook — Q3-26 release (29-Oct-2026)',
    'out_note': ('Adjusted EPS $5.20–5.32 (raised from $5.12–5.30), net sales $2.61–2.64bn (narrowed from $2.58–2.67bn on delayed third-party refuse-truck deliveries); '
                 'capex $45–55m (FY25 release, not repeated). EDGAR-filed (Ex. 99.1 to the Q3-26 10-Q).'),
    'outlook': [
        ('out_rev', '  FY26 net sales ($m)', tuple(G26['net_sales']), 'm', 'Guided $2.61–2.64bn. Drives the Q4/26E sales calibration.'),
        ('out_eps', '  FY26 adjusted EPS ($)', tuple(G26['adj_eps']), 'ps', 'Guided $5.20–5.32. Drives the Q4/26E segment-margin calibration.'),
        ('out_capex', '  FY26 capital expenditures ($m) — memo', tuple(G26['capex']), 'm', 'Guided $45–55m in the FY25 release (information row; high = low capex).'),
        ('bb26', '  Q4/26E share repurchases ($m)', (20.0, 10.0, 0.0), 'm', '9M 2026 $5.1m (September); $152.0m remaining under the March 2020 / April 2025 programs.'),
    ],
    'points': [
        ('pt_int', '  Q4/26E interest expense, net ($m)', 4.8, 'm1', 'Q3-26 $5.3m on ~$437m average debt (~4.9%); debt $420m at 30-Sep-2026 + GVS ($29m) on the revolver.'),
        ('pt_nonop', '  Q4/26E other expense, net ($m)', 1.0, 'm1', 'Q1–Q3 2026 $0.6m / $0.8m / $1.0m (non-service pension cost).'),
        ('pt_etr', '  Q4/26E tax rate (GAAP & adjusted)', 0.24, 'pct', '9M 2026 GAAP 23.5% and adjusted 23.5%; Q3-26 24.3% / 24.2%.'),
        ('pt_dda', '  Q4/26E depreciation & amortization ($m)', 26.0, 'm1', 'Q3-26 $25.3m (rising with the rental fleet, Mega, Western Technology; GVS from 28-Oct).'),
        ('pt_amort', '  Q4/26E amortization of intangibles ($m)', AM['2026_rem'], 'm1', 'Q3-26 10-Q estimate: $6.7m remaining in 2026 (excludes GVS).'),
        ('pt_acq', '  Q4/26E acquisition & integration costs ($m)', 1.5, 'm1', 'Q1–Q3 2026 $1.2m / $0.7m / $1.2m; GVS closing in Q4 (assumption).'),
        ('pt_stepup', '  Q4/26E purchase accounting effects ($m)', 0.5, 'm1', 'Q1–Q3 2026 $1.6m / $0.9m / $0.4m (Mega, New Way step-ups running off; GVS).'),
        ('pt_capex', '  FY26 capital expenditures ($m)', 50.0, 'm1', 'Mid-point of the $45–55m guidance (9M 2026 $30.0m).'),
        ('pt_gvs', '  Q4/26E acquisition of Global Vacuum Systems ($m)', 29.0, 'm1', 'Initial price ~$29m incl. the Texas facility (closed 28-Oct-2026; Q3-26 10-Q Note 14).'),
        ('pt_gvs_ppe', '  GVS: PP&E share of the price (assumption; PPA not yet published)', 0.30, 'pct', 'Includes the manufacturing facility; replace with the FY2026 10-K allocation.'),
        ('pt_gvs_int', '  GVS: intangibles share of the price (assumption)', 0.35, 'pct', 'Federal Signal PPAs: New Way 39%, Hog 41%, Mega 41% of consideration; replace with the 10-K allocation.'),
    ],
    'lev': (1.0, 0.75, 0.5),
    'lev_note': ('Net debt $346m at 30-Sep-2026 ≈ 0.65x LTM adjusted EBITDA (FY2022–25 0.5–1.3x); covenants allow restricted payments up to 3.25x. Target = leverage up to which '
                 'surplus cash (after dividends and the M&A lever) is returned via buybacks; Bull = more buybacks (higher target). Assumption — the company sets no leverage target.'),
    'blocks': [
        ('ESG_G', 'ESG_G (Environmental Solutions net sales y/y)', 0.03, -0.06, [0.075, 0.07, 0.065, 0.06, 0.055],
         '9M 2026 +25.6% (New Way, Mega acquired; Q3 orders +43%, high-teens organic); 2027E includes ~10 months of GVS and New Way synergies; FY2021–25 sales CAGR 15% incl. acquisitions.', 'pct', False),
        ('SSG_G', 'SSG_G (Safety and Security Systems net sales y/y)', 0.02, -0.05, [0.03, 0.04, 0.04, 0.04, 0.04],
         '9M 2026 +10.8% (Q3 +2%); Q3 orders −6% and backlog $65m (−26% y/y) after large non-U.S. public-safety orders; FY2021–25 CAGR 10%.', 'pct', False),
        ('ESG_M', 'ESG_M (Environmental Solutions segment operating margin)', 0.01, -0.025, [0.185, 0.19, 0.193, 0.195, 0.195],
         'FY2025 17.7%, 9M 2026 18.2% (after amortization; New Way dilutive initially, synergies $15–20m by 2028); FY2021–24 12.0–16.8%.', 'pct', False),
        ('SSG_M', 'SSG_M (Safety and Security Systems segment operating margin)', 0.01, -0.03, [0.245, 0.245, 0.25, 0.25, 0.25],
         'FY2025 23.8%, 9M 2026 24.7%; FY2019–24 15.6–21.2%.', 'pct', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 100.0, -150.0, [150.0, 150.0, 150.0, 150.0, 150.0],
         'Acquisition spend: $501m (2025: New Way, Hog, Kinloch), $40m (2024), $55m (2023), ~$95m 9M 2026 + GVS; 15 acquisitions since 2016. Base $150m p.a. (assumption).', 'm', True),
    ],
    'b2b': {'esg': (1.0, 1.0), 'ssg': (1.0, 1.0)},
    'b2b_note': 'Book-to-bill input 1.00x (FY2025 ESG 1.01x / SSG 1.06x; 9M 2026 0.96x / 0.97x); backlog is an output.',
    'corp_pct': -0.023,
    'dda_pct': {2027: 0.038, 2028: 0.038, 2029: 0.037, 2030: 0.037, 2031: 0.037},
    'sga_pct': {2027: 0.112, 2028: 0.111, 2029: 0.110, 2030: 0.110, 2031: 0.110},
    'sbc_pct': 0.007, 'etr': 0.24, 'nonop': 4.0,
    'capex_pct': {2027: 0.018, 2028: 0.018, 2029: 0.018, 2030: 0.018, 2031: 0.018},
    'rent_pct': {2027: 0.011, 2028: 0.011, 2029: 0.011, 2030: 0.011, 2031: 0.011},
    'dps_q': 0.15, 'dps_g': 0.07, 'def_q4': 1.0, 'def_ae': 5.0, 'wh_q4': -0.5, 'wh_ae': -14.0, 'eq_q4': 0.3, 'eq_ae': 2.0, 'iss_q4': 0.0, 'iss_ae': 0.2, 'dil': 0.6,
    'amort_sched': {2027: AM['2027'], 2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: 16.0},
    'amort_note': AM['src'] + ' 2027 $26.0m, 2028 $25.3m, 2029 $20.0m, 2030 $16.9m; 2031 $16.0m assumed ($108.4m thereafter).',
    'tl_repay': {},
    'tl_note': 'Term loan $375.0m at 30-Sep-2026 ($25.0m voluntarily prepaid in Q3-26); no scheduled amortization modelled; the 29-Oct-2030 maturity is assumed refinanced (assumption).',
    'min_cash': 60.0,
    'r_tl': {2027: 0.050, 2028: 0.050, 2029: 0.051, 2030: 0.052, 2031: 0.052},
    'r_note': 'Adjusted RFR + 1.00–1.75% (2025 Credit Agreement); Q3-26 interest expense, net ≈ 4.9% of average debt. Assumption.',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $114.00 (weighted average price paid for shares repurchased 30-Aug – 26-Sep-2026, Q3-26 10-Q Part II Item 2, filed '
                '29-Oct-2026 — the latest share price in an SEC filing; ~$7.0bn market cap); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $150m p.a. of bolt-ons). Funded from cash / revolver (debt schedule).',
    'rev_guid_note': 'Company FY26 net sales guidance $2.61–2.64bn (Q3-26 release, 29-Oct-2026). Drives the sales calibration.',
    'eps_guid_note': 'Company FY26 adjusted EPS guidance $5.20–5.32 (raised 29-Oct-2026). Drives the segment-margin calibration.',
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
CAGR_G = {'is_rev', 'g_rev', 'esg_rev', 'ssg_rev', 'esg_oi', 'ssg_oi', 'esg_ord', 'ssg_ord', 'r_adj', 'r_ebit', 'is_oi', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf',
          'bs_ta', 'bs_teq', 'sh_dil', 'is_ni', 'eps_dil', 'dps', 'd_dda', 'is_gp', 'is_sga', 'd_amort'}
CAGR_A = {'esg_m', 'ssg_m', 'r_adj_m', 'r_ebit_m', 'is_gm', 'is_oi_m', 'gm_rev', 'gm_esg', 'gm_ssg', 'gm_gm', 'gm_ebitda_m', 'gm_op_m', 'gm_adj_m', 'gm_net_m',
          'gm_sga', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_sga', 'd_dda_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'e_rate',
          'fcf_eb', 'corp_pct', 'esg_mix', 'esg_b2b', 'ssg_b2b'}
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
        if row.key == 'is_rev' and col.kind in HISTK:
            nts = DATA.get(pkey(col), {}).get('notes')
            if nts: comment(cell, f'{pkey(col)}: ' + ' '.join(dict.fromkeys(nts)), 440, 150)
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

K = 'Source: Federal Signal Forms 10-K / 10-Q (SEC EDGAR, CIK 277509) — '
REL = 'Source: Federal Signal earnings releases (Ex. 99.1 to each 10-Q / 10-K; Form 8-K Item 2.02 for FY2008) — '
LABEL_SOURCES = {
    'esg_ord': REL + 'group results tables (total orders, backlog); 2006–2012 annual from the 10-K MD&A group tables. Q4 = fourth-quarter release three-month column.',
    'esg_rev': K + 'segment note / MD&A group tables (net sales, operating income), as originally reported; Q1–Q3/15 from the 2016 10-Q comparatives (Fire Rescue re-presented as discontinued). '
               'Groups: Environmental Solutions (Environmental Products to 2006); Safety and Security Systems (Safety Products to 2006).',
    'esg_aeb': REL + 'segment adjusted EBITDA reconciliations (published from Q1-17).',
    'frg_rev': K + 'segment notes as originally reported: Fire Rescue (Bronto, E-One to 2008), Tool (to 2007), Federal Signal Technologies (2009–2011).',
    'corp': K + 'derived as consolidated operating income − Σ group operating income; the segment note showed "Corporate expenses / Corporate and eliminations" to 2023 (check row).',
    'is_rev': K + 'consolidated statements of operations, as originally reported (Q1–Q3/15 restated comparatives; Q4 from the fourth-quarter release). Period notes are in the cell comments of this row.',
    'd_dda': K + 'cash-flow statements (year to date; discrete quarters derived), = the D&A line of the adjusted EBITDA reconciliation.',
    'd_acq': REL + 'adjusted EBITDA reconciliations (from FY2013 annual / Q1-17 quarterly); otherwise the pre-tax items of the adjusted EPS reconciliation (2014–2016 quarters). Labels in cell comments.',
    'r_pub': REL + 'Reconciliation of net income to adjusted EBITDA (quarterly from Q1-17; FY2013–16 from the total debt / adjusted EBITDA tables).',
    'e_pub': REL + 'Adjusted net income and EPS reconciliations (from Q1-13; Q1–Q3/13 per share only).',
    'cf_ni': K + 'statements of cash flows (year to date, as originally reported; discrete quarters derived, Q4 = FY − 9M).',
    'bs_cash': K + 'balance sheets (period ends, as originally reported); shares outstanding = shares issued − treasury shares (balance-sheet captions / XBRL).',
    'ppa_cons': 'Source: FY2025 10-K Note 2 (New Way, Hog — preliminary allocations).',
    'sh_basic': K + 'statements of operations (weighted average shares); FY2006–08 from the 10-K Note 1 text and FY2009–11 from the EPS note table (basic = diluted). No stock splits in the period.',
    'ds_total': 'Source: balance sheets; Q3-26 10-Q Note 5 and FY2025 10-K (2025 Credit Agreement, 29-Oct-2025).',
    'm_hdr': 'Source: FY2025 10-K Note 2; Q3-26 10-Q Notes 2 and 14; 8-Ks of 25-Sep-2025 (New Way deck), 1-Dec-2025, 18-Dec-2025 and 16-Jan-2026.',
}
CELL_COMMENTS = {}
def comments_setup():
    CELL_COMMENTS['is_disc'] = {A[2008]: 'FY2008: Tool Group and E-One sold / discontinued ($126.9m loss).', A[2012]: 'FY2012: FSTech Group (sold Nov-2012) and other businesses ($49.5m loss).',
                                A[2010]: 'FY2010: includes the discontinued Riverchase and financial-services activities.'}
    CELL_COMMENTS['gm_rev'] = {A[2008]: 'As reported: FY2007 included the Tool Group (discontinued in the FY2008 10-K). Like-for-like growth is in the row below.',
                               A[2012]: 'FY2011 as first reported included FSTech; see the comparative-basis row.',
                               A[2015]: 'FY2014 as first reported included Fire Rescue (Bronto), moved to discontinued operations in the FY2015 10-K.'}
    CELL_COMMENTS['tax'] = {}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('2006–2012: no adjusted EBITDA published (EBITDA quoted in the 2010 releases only) — model = EBITDA; adjusting items nil',
              'Federal Signal began publishing adjusted EBITDA in the FY2013 leverage table (total debt / adjusted EBITDA, trailing twelve months).'),
        A[2013]: ('FY2013–16: adjusted EBITDA published annually (leverage tables: + restructuring, acquisition costs, purchase accounting, debt settlement); quarters = model (EPS-bridge items)', None),
        q(2017, 1): ('Q1-17+: quarterly adjusted EBITDA reconciliation (+ acquisition & integration, restructuring, executive severance, purchase accounting, hearing-loss and pension settlement charges)', None),
        q(2020, 1): ('2020–21: coronavirus-related expenses added back', None),
        q(2023, 2): ('2023: environmental remediation costs added back', None),
        q(2026, 3): ('Q3-26: charges associated with previously discontinued operations added back (the Q1-26 $1.0m was not; to be recast)',
                     'Q3-26 release note (a): Q1-26 charges of $1.0m were not excluded from adjusted EBITDA in Q1 / 1H-26; prior periods will be recast. The model keeps the figures as published.'),
    }
    DEFS['e_def'] = {
        'C': ('2006–2012: no consistent adjusted EPS (2010–12 releases quoted per-share items for restructuring / debt settlement only) — adjusted = GAAP continuing EPS (flag)', None),
        q(2013, 1): ('2013: adjusted EPS from continuing operations; items shown net of tax (debt settlement, restructuring, special tax items incl. the $102m valuation-allowance release)', None),
        q(2014, 1): ('2014+: pre-tax items with a recomputed adjusted income tax (special tax items excluded); company definition', None),
        q(2026, 3): ('Q3-26: + charges associated with previously discontinued operations', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 net-sales and adjusted-EPS guidance end-points (high / mid / low), '
            'Q4/26E buybacks, 2027E–2031E group sales growth and segment margins, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Federal Signal Corporation (NYSE: FSS) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as originally reported · USD millions (per-share data in USD; shares in millions) · Calendar fiscal year · Source: Federal Signal Forms 10-K / 10-Q and '
                'the earnings releases filed as their Ex. 99.1 (Form 8-K for FY2008), deal 8-Ks, SEC EDGAR (CIK 277509); XBRL company facts. The investor-relations site '
                'is not used; its releases are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported; Q1–Q3/15 from the 2016 10-Q comparatives (Fire Rescue / Bronto discontinued in the FY2015 10-K) and the 2021 quarters with '
                'amortization reclassified out of SEG&A. Discontinued: Tool 2008, FSTech 2012, Fire Rescue 2015–16. Acquisitions: Westech Jan-16, Joe Johnson Equipment Jun-16, TBEI Jun-17, '
                'MRL Jul-19, OSW Feb-21, Ground Force and Deist 2021, TowHaul 2022, Trackless and Blasters 2023, Standard 2024, Hog Feb-25, New Way Nov-25, Kinloch Dec-25, Mega Jan-26, '
                'Western Technology Jul-26, GVS Oct-26. Q4/26E calibrated to the FY26 outlook (29-Oct-2026).')
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
        p = os.path.join(BASE, f'FSS_{scen}.xlsx')
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
    p = os.path.join(BASE, 'FSS_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
