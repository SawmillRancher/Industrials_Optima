"""Build GHM_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'GHM_Model.xlsx')
G27 = MAN['guidance_fy27']
AM = MAN['amort_sched']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2026']['x']
    rev, cogs = q['rev'], q['cogs']
    return {'dso': round(q['bs_ar'] / rev * 365), 'unb': round(q['bs_unb'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365),
            'dpo': round(q['bs_ap'] / cogs * 365), 'accc': round(q['bs_accc'] / rev, 3), 'acco': round(q['bs_acco'] / rev, 3),
            'depb': round(q['bs_dep'] / q['backlog'], 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at fiscal-year-end (31-Mar-2026) levels on FY2026 net sales / cost of products sold / backlog: receivables {WC["dso"]}d, '
              f'unbilled {WC["unb"]}d, inventories {WC["dio"]}d, payables {WC["dpo"]}d, accrued compensation {WC["accc"]:.1%} and accrued expenses '
              f'{WC["acco"]:.1%} of sales, customer deposits {WC["depb"]:.1%} of backlog. Year ends are compared with year ends.')

V0 = {
    'out_hdr': 'FY27 guidance — Q1 FY27 release (6-Aug-2026; issued 8-Jun-2026, reaffirmed)',
    'out_note': ('Net sales $285–295m; gross margin 24.5–25.5%; SG&A incl. amortization 16.5–17.5% of sales; Adjusted EBITDA $35–40m (excl. ~$5.5–6.5m of '
                 'equity-based compensation, acquisition & integration and ERP costs); ETR 18–20%; capex $18–22m. All from SEC filings (none unverified).'),
    'outlook': [
        ('out_rev', '  FY27 net sales ($m)', tuple(G27['sales']), 'm1', 'Guided $285–295m. Drives the Q2–Q4/27E sales calibration.'),
        ('out_eb', '  FY27 Adjusted EBITDA ($m)', tuple(G27['adj_ebitda']), 'm1', 'Guided $35–40m. Drives the Q2–Q4/27E gross-margin calibration.'),
        ('out_gm', '  FY27 gross margin — memo', tuple(G27['gm']), 'pct', 'Guided 24.5–25.5% (information row; compare the model).'),
        ('out_sga', '  FY27 SG&A incl. amortization % of sales', tuple(G27['sga_pct']), 'pct', 'Guided 16.5–17.5% (low end = Bull). Drives Q2–Q4/27E SG&A before the margin solve.'),
        ('out_items', '  FY27 items excluded from Adjusted EBITDA ($m) — memo', tuple(G27['items']), 'm1', G27['items_note']),
        ('out_capex', '  FY27 capital expenditures ($m) — memo', tuple(G27['capex']), 'm1', 'Guided $18–22m; the model uses the mid-point (point estimate below).'),
        ('bb27', '  Q2–Q4/27E share repurchases ($m)', (0.0, 0.0, 0.0), 'm', MAN['buyback']),
    ],
    'points': [
        ('pt_dep', '  Q2–Q4/27E depreciation per quarter ($m)', 1.78, 'm2', 'Not guided; Q1/27 $1.67m, rising with capex (FY26 $5.3m).'),
        ('pt_amort', '  Q2–Q4/27E amortization per quarter ($m)', round(AM['2027_rem'] / 3, 3), 'm2', AM['src'] + ' $2.8m remaining FY27 ÷ 3.'),
        ('pt_sbc', '  Q2–Q4/27E equity-based compensation per quarter ($m)', 0.65, 'm2', 'Q1/27 $0.65m; FY26 $2.1m.'),
        ('pt_acq', '  Q2–Q4/27E acquisition & integration costs per quarter ($m)', 0.45, 'm2',
         'FlackTek integration and earn-out fair-value accretion (Q1/27 $1.18m incl. $0.58m fair-value increase). Items total FY27 ≈ $6.0m vs ~$5.5–6.5m guided.'),
        ('pt_erp', '  Q2–Q4/27E ERP implementation costs per quarter ($m)', 0.25, 'm2', 'Batavia ERP go-live 2Q FY27 (Q1/27 $0.14m).'),
        ('pt_int', '  Q2–Q4/27E net interest expense (income) per quarter ($m)', -0.15, 'm2', 'No debt after the April-2026 repayment; interest income on ~$27m cash (Q1/27 net income $0.12m).'),
        ('pt_othnon', '  Q2–Q4/27E other non-operating expense per quarter ($m)', 0.09, 'm2', 'Q1/27 $0.09m (pension non-service cost).'),
        ('pt_etr', '  FY27 effective tax rate (Q2–Q4 rate solved to it)', G27['etr'][1], 'pct', 'Guided 18–20%; mid-point. Q1/27 ETR 6.5%.'),
        ('pt_capex', '  FY27 capital expenditures ($m)', G27['capex'][1], 'm1', 'Guidance mid-point.'),
        ('pt_b2b', '  Q2–Q4/27E book-to-bill (x)', 1.0, 'x2', 'Q1/27 1.3x; FY26 1.5x. Lumpy Navy awards; 1.0x for the remaining quarters (assumption).'),
    ],
    'lev': (-0.5, -1.0, -1.5),
    'lev_note': ('Net cash $26.9m at 30-Jun-2026 (no debt) after the $50m PIPE; the company plans to use the proceeds for organic and inorganic growth and targets '
                 'leverage <3.0x for M&A. Buybacks only return net cash above the cap (assumption); Bull = lower cap (more returned), Bear = higher.'),
    'blocks': [
        ('DEF_G', 'DEF_G (Defense sales y/y)', 0.04, -0.04, [0.09, 0.08, 0.08, 0.07],
         'FY26 +21%, Q1/27 +40% (milestone timing); Defense backlog $470m (84% of total; Virginia / Columbia class submarines, MK48 torpedo; ~$1.8bn platform opportunity to 2056 per Investor Day).', 'pct', False),
        ('SPACE_G', 'SPACE_G (Space sales y/y)', 0.10, -0.10, [0.15, 0.12, 0.10, 0.08],
         'FY26 −1%, Q1/27 +86%; Space backlog $45m (+245% y/y), FY26 orders +76%. Customers include pre-profit launch companies (Bear).', 'pct', False),
        ('EP_G', 'EP_G (Energy & Process sales y/y)', 0.03, -0.06, [0.04, 0.04, 0.03, 0.03],
         'FY26 +14% (incl. FlackTek); Q1/27 +5%. Aftermarket and New Energy (SMR) growth vs deferred large refining / petrochemical capital projects.', 'pct', False),
        ('GM', 'GM (gross margin %)', 0.01, -0.02, [0.255, 0.26, 0.265, 0.27],
         'FY27 guided 24.5–25.5% (FY26 23.5%, FY25 25.2%); Investor Day: commercial mix, automation and pricing → "mid-20s" gross margin, 14–16% Adjusted EBITDA margin by FY29.', 'pct', False),
        ('B2B', 'B2B (book-to-bill, x)', 0.15, -0.15, [1.10, 1.05, 1.00, 1.00],
         'FY24 1.4x, FY25 1.1x, FY26 1.5x; record $557m backlog (~1.9 years of sales). Normalising toward 1.0x as Defense programs move to production.', 'x2', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 20.0, -20.0, [20.0, 20.0, 20.0, 20.0],
         'Barber-Nichols $72m (FY22), P3 $11m (FY24), Xdot + FlackTek $38m (FY26); M&A as an accelerator (Investor Day), $50m PIPE (Apr-2026) partly earmarked. Base $20m p.a. (assumption).', 'm', True),
    ],
    'sga_pct': {2028: 0.160, 2029: 0.155, 2030: 0.150, 2031: 0.147},
    'dep_pct': {2028: 0.026, 2029: 0.027, 2030: 0.028, 2031: 0.028},
    'sbc_pct': 0.009, 'othnon': 0.36, 'etr': 0.20,
    'capex_pct': {2028: 0.060, 2029: 0.050, 2030: 0.045, 2031: 0.040},
    'def_ae': 0.3, 'stock_rem': 0.0, 'stock_ae': 0.6, 'withhold_rem': -0.3, 'withhold_ae': -2.0, 'iss_rem': 0.03, 'iss_ae': 0.08, 'dil': 0.11,
    'min_cash': 15.0,
    'amort_sched': {2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: AM['2031']},
    'amort_note': AM['src'] + ' FY28–FY31 $3.7m a year ($20.0m thereafter); FlackTek tradename ($6.7m) is indefinite-lived.',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $95.34 (8-Jun-2026 tax-withholding price on Form 4s filed 10-Jun-2026 — the latest share price in an SEC filing); '
                'update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $20m p.a. of bolt-ons, assumption). Funded from cash / revolver (debt schedule).',
    'rev_guid_note': 'Company FY27 net sales guidance $285–295m (8-Jun-2026; reaffirmed 6-Aug-2026). Drives the sales calibration.',
    'eb_guid_note': 'Company FY27 Adjusted EBITDA guidance $35–40m (8-Jun-2026; reaffirmed 6-Aug-2026). Drives the gross-margin calibration.',
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
        if 'hist_in' in kw:
            v = kw['hist_in']()
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
    if k == 'EC':
        if 'ec_in' in kw: return kw['ec_in'], True
        if 'ec' in kw: return kw['ec'](), False
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r}:{QE3}{row.r})', False
        if kw.get('flow') and not row.spec2 and any(x in kw for x in ('qe', 'qe_in', 'fc', 'hist_in')): return SC27(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'mk_def', 'mk_space', 'mk_ep', 'ob_ord', 'ob_bkl', 'r_adj', 'r_ebitda', 'r_ebita', 'is_op', 'd_da', 'e_adjni', 'e_eps',
          'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_gp', 'is_sga', 'd_amort', 'd_dep', 'is_ni', 'eps_dil', 'o_adj', 'rg_us'}
CAGR_A = {'mk_def_mix', 'mk_space_mix', 'mk_ep_mix', 'd_gm', 'd_sga', 'r_adj_m', 'is_gm', 'is_op_m', 'gm_gm', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_sga',
          'gm_rev', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_dep_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'fcf_eb',
          'ob_b2b', 'o_adj_m', 'r_nopb_m', 'gm_inc'}
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
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2021]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2016]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2006]}{r})^(1/20)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2022, 2027))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2017, 2027))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2006, 2027))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: Graham earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'mk_def': ('Source: Ex. 99.2 supplemental tables (FY2023+), 10-K / 10-Q revenue note "net sales disaggregated by market" and release "sales by industry" grids. '
               'Current Defense / Space / Energy & Process basis introduced with the FY2025 10-K; FY2020 Defense from the FY2021 releases\' prior-year tables (latest presentation). '
               'Energy & Process = net sales − Defense − Space for FY2020–FY2024 (sum of refining, chemical / petrochemical and other commercial).'),
    'lg_refining': ('Source: release "sales by industry" grids (USD m to one decimal, FY2008–FY2022), Ex. 99.2 supplemental tables and the 10-K / 10-Q revenue note '
                    '(USD thousands, FY2023+). Labels changed over time ("Other Commercial and Industrial (incl. NNPP)", "Other Commercial, Industrial and Defense" FY2015–19).'),
    'ob_ord': REL + 'order & backlog trend tables (USD m) and Ex. 99.2 supplemental tables (USD thousands, FY2023+).',
    'ft_rev': 'Source: FY2026 10-K Note 2 (FlackTek net sales in FY2026) and Q1 FY27 10-Q MD&A; Investor Day 8-K Ex. 99.1 (18-Jun-2026) for the FY27 expectation.',
    'is_rev': REL + 'consolidated statements of operations, as originally reported; shares and per-share data restated for the Jan-2008 and Oct-2008 stock splits.',
    'd_da': REL + 'EBITDA / Adjusted EBITDA reconciliations (FY2011+); cash-flow statements before.',
    'r_adj_pub': REL + 'Adjusted EBITDA reconciliation (FY2011, FY2015, FY2017–20, FY2022+); EBITDA reconciliation (FY2012–14, FY2016, FY2021).',
    'e_pub': REL + 'Adjusted net income / adjusted EPS reconciliation (FY2015, FY2017–Q3 FY2020, FY2022+).',
    'o_pub': REL + 'adjusted operating profit reconciliation (Q4 FY2018–Q3 FY2020).',
    'cf_ni': (REL + 'condensed consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). '
              'FY2019–20 statements deduct the change in cash held within assets held for sale (commercial nuclear utility business, sold Q1 FY2020).'),
    'bs_cash': REL + 'consolidated balance sheets (period ends); shares outstanding from XBRL (cover / balance-sheet facts).',
    'ppa_cons': 'Source: FY2022 10-K Note 2 (Barber-Nichols, final); FY2026 10-K Note 2 (P3, final; FlackTek, preliminary). Xdot (Oct-2025, $1.4m incl. earn-out) immaterial.',
    'sh_basic': REL + 'statements of operations (weighted average shares). Stock splits: 5-for-4 effective 3-Jan-2008 and 2-for-1 effective 6-Oct-2008 (FY2009 10-K); releases before each split restated (×2.5 / ×2).',
    'ds_total': 'Source: release balance sheets; FY2026 10-K Note 9 and Q1 FY27 10-Q Note 7 (debt); 8-K 15-Apr-2026 (PIPE).',
    'cal_guid': 'Source: Q4 FY26 release (8-K Ex. 99.1, 8-Jun-2026) and Q1 FY27 release (8-K Ex. 99.1, 6-Aug-2026), fiscal 2027 outlook. Investor Day targets: 8-K Ex. 99.1 (18-Jun-2026).',
}
CELL_COMMENTS = {}
def comments_setup():
    CELL_COMMENTS['is_op_pub'] = {QC[(2022, 1)].c: 'Q1 FY2022 release statement shows no operating-profit line; derived as gross profit − SG&A − amortization (− other).'}
    CELL_COMMENTS['is_int'] = {A[2021]: 'FY2021 statement line "Net other interest (income)/expense" (−$0.269m) includes other income; split per the EBITDA reconciliation (net interest income $0.156m; other $0.113m).'}
    CELL_COMMENTS['cf_hfs'] = {A[2019]: 'FY2019 statement: "Less: net increase in cash classified within current assets held for sale" (−$0.552m); reversed in FY2020.',
                               A[2020]: 'Reversal of the FY2019 held-for-sale cash ($0.552m) on the sale of the commercial nuclear utility business.'}
    CELL_COMMENTS['mk_def'] = {A[2020]: 'FY2020 Defense / Space from the FY2021 releases\' prior-year table (latest presentation; Defense was inside "Other" in the FY2020 releases).'}
    CELL_COMMENTS['ft_rev'] = {A[2026]: 'FlackTek sales 23-Jan to 31-Mar-2026 (68 days), FY2026 10-K Note 2.'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('FY2006–10: no EBITDA published — model EBITDA (net income + net interest + taxes + D&A); adjusted = EBITDA (flag)', None),
        A[2011]: ('FY2011: Adjusted EBITDA published (Energy Steel acquisition expenses added back; table in USD m)', 'Q4 FY2011 release (27-May-2011), USD m to one decimal.'),
        A[2012]: ('FY2012–14: EBITDA only (no items) — adjusted = EBITDA', None),
        q(2015, 4): ('Q4 FY2015: Adjusted EBITDA excl. restructuring charge', None),
        q(2016, 1): ('FY2016: EBITDA only — adjusted = EBITDA', None),
        q(2017, 1): ('FY2017–Q3 FY2020: Adjusted EBITDA excl. restructuring, goodwill / intangible impairments, nuclear bad debt and loss on the sale of the commercial nuclear utility business', None),
        q(2020, 4): ('Q4 FY2020–FY2021: EBITDA only — adjusted = EBITDA', None),
        q(2022, 1): ('FY2022+: Adjusted EBITDA excl. acquisition & integration costs (earn-out fair value, inventory step-up), CEO / CFO transition, debt amendment costs', None),
        q(2024, 1): ('FY2024: + Barber-Nichols performance bonus (Q1–Q3), ERP implementation (from Q3), ERC tax credit', None),
        q(2024, 4): ('Q4 FY2024+: equity-based compensation added back (definition change; prior periods not restated)', 'Q4 FY2024 release (7-Jun-2024) first excluded equity-based compensation expense.'),
    }
    DEFS['o_def'] = {
        'C': ('Not published — model definition (operating profit + non-recurring items; SBC and amortization not added back)', None),
        q(2018, 4): ('Q4 FY2018–Q3 FY2020: company-published adjusted operating profit (restructuring, impairments, nuclear items)', None),
        q(2020, 4): ('Not published from Q4 FY2020 — model definition', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006–14: no adjusted net income published — model = GAAP + items × (1 − 35%) (no items in these periods)', None),
        q(2015, 4): ('FY2015: adjusted net income excl. restructuring (shown net of tax)', None),
        q(2016, 1): ('FY2016: not published — model = GAAP', None),
        q(2017, 1): ('FY2017–Q3 FY2020: excl. restructuring, impairments, nuclear items; FY2018 also the US tax-law impact', None),
        q(2020, 4): ('Q4 FY2020–FY2021: not published — model = GAAP + items net of tax', None),
        q(2022, 1): ('FY2022+: + amortization of intangible assets; tax on adjustments at a normalized rate (19–20% FY2022; 23% statutory from FY2023)',
                     'Company: "Applies a normalized tax rate to non-GAAP adjustments, which are pre-tax, based upon the statutory tax rate of 23%."'),
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
                ws[f'{col}{r}'].number_format = '\\+#,##0;\\-#,##0' if nf == 'm' else ('\\+0.00\\x;\\-0.00\\x' if nf == 'x2' else '\\+0.0%;\\-0.0%')
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY27 net-sales and Adjusted EBITDA guidance end-points (high / mid / low), '
            'Q2–Q4/27E buybacks, 2028E–2031E Defense / Space / Energy & Process growth, gross margin, book-to-bill, M&A spend and the net-cash cap for buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Graham Corporation (NYSE: GHM) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 31 March (2027 = Apr-2026 – Mar-2027) · '
                'Source: Graham Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1), supplemental tables (Ex. 99.2), Investor Day and deal / financing 8-Ks, '
                'SEC EDGAR (CIK 716314); XBRL company facts; investor-relations releases at ir.grahamcorp.com are the same documents as filed on EDGAR · '
                'All guidance and targets used are from EDGAR filings (none unverified)')
    ws['B4'] = ('Basis notes: as originally reported; single reportable segment; markets Defense / Space / Energy & Process (current basis from FY2020; legacy industry split in memo rows). '
                'Splits 5-for-4 (Jan-2008) and 2-for-1 (Oct-2008) applied to shares / per-share data. Acquisitions: Energy Steel Dec-2010, Barber-Nichols Jun-2021, '
                'P3 Nov-2023, Xdot Oct-2025, FlackTek Jan-2026; commercial nuclear utility business sold Q1 FY2020. Q2–Q4/27E calibrated to FY27 sales and Adjusted EBITDA guidance (6-Aug-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '20Y CAGR'], ["26-'31", "21-'26", "16-'26", "06-'26"]):
        ws[f'{c}6'] = a; ws[f'{c}7'] = b

def set_columns(ws):
    for k in list(ws.column_dimensions.keys()): del ws.column_dimensions[k]
    ws.column_dimensions['A'].width = TM.column_dimensions['A'].width
    ws.column_dimensions['B'].width = TM.column_dimensions['B'].width
    wid = {'A': 13.0, 'Q': 9.5703125, 'QE': 11.42578125, 'EC': 14.140625, 'AE': 13.0}
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
        p = os.path.join(BASE, f'GHM_{scen}.xlsx')
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
    p = os.path.join(BASE, 'GHM_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
