"""Build THEON_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'THEON_Model.xlsx')

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    rev, cogs = q['rev'], q['cogs']
    return {'dso': round(q['bs_ar'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365), 'dpo': round(q['bs_ap'] / cogs * 365),
            'oca': round(q['bs_oca'] / rev, 3), 'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at 31-Dec-2025 levels on FY2025 revenue / cost of sales (DSO {WC["dso"]}d, inventory {WC["dio"]}d, payables {WC["dpo"]}d, '
              f'other current assets {WC["oca"]:.1%} and other current liabilities {WC["ocl"]:.1%} of revenue). Year-end balances are used because '
              'deliveries are Q4-weighted (FY24 DSO 130d; FY25 118d).')
UNV = ' (company release; unverified — not on EDGAR)'

V0 = {
    'out_hdr': 'FY26 outlook — FY2025 preliminary results (16-Feb-2026); reiterated 5-May, 27-Jul and 7-Sep-2026' + UNV,
    'out_note': ('Revenue EUR 570–600m (c.30% growth: >20% organic, rest Kappa); adjusted EBIT margin "mid-twenties"; capex EUR 30m; dividend 30% of FY2025 net income. '
                 'MERIO (May-26) and HGH (Jun-26) were announced after the guidance and are modelled outside it. Unverified — company releases, not on EDGAR.'),
    'outlook': [
        ('out_rev', '  FY26 revenue, guidance basis (EUR m; excl. MERIO)', (600.0, 585.0, 570.0), 'm1', 'Guided EUR 570–600m (16-Feb-2026; first target EUR 570–590m on 3-Nov-2025).' + UNV),
        ('out_m', '  FY26 adjusted EBIT margin (guidance basis)', (0.26, 0.25, 0.24), 'pct', '"Mid-twenties" read as 24–26% (H1-26 26.2%; FY25 26.2%).' + UNV),
    ],
    'points': [
        ('pt_capex', '  FY26 capex (EUR m)', 30.0, 'm1', 'Company guidance EUR 30m (H1-26 EUR 11.8m).' + UNV),
        ('pt_etr', '  Tax rate (Q3/Q4-26E and 2027E+ base)', 0.23, 'pct', 'FY25 23.1%, FY24 23.4% (Greek 22% statutory rate). Assumption.'),
        ('pt_nci', '  Non-controlling interests % of profit after tax', 0.005, 'pct', 'FY25 0.9%, H1-26 0.2% (Harder Digital 40% minority). Assumption.'),
        ('pt_mincash', '  Minimum cash balance (EUR m)', 75.0, 'm1', 'Assumption (30-Jun-26 cash EUR 96.4m).'),
        ('pt_tl', '  HGH term loan drawn at closing (EUR m)', 325.0, 'm1', 'EUR 325m syndicated senior unsecured term loan (H1-26 report).'),
        ('pt_me_q4', '  MERIO revenue consolidated in Q4-26E (EUR m)', 2.5, 'm1', 'ASSUMPTION: c.2 months of ">EUR 15m" FY26 revenue (completion underway 29-Oct-2026).'),
        ('pt_me_fy', '  MERIO FY2026 standalone revenue (EUR m; base for 2027E)', 15.0, 'm1', 'Company: "above EUR 15 million in revenues in FY 2026".'),
        ('pt_me_m', '  MERIO adjusted EBIT margin', 0.23, 'pct', 'Company: EBIT "above EUR 3.5 million" on >EUR 15m revenue.'),
        ('pt_me_px', '  MERIO consideration for 80% (EUR m) — ASSUMPTION', 37.5, 'm1', 'Not disclosed ("accretive EBIT multiple"): ASSUMPTION 13x FY26 EBIT (c.EUR 3.6m) × 80%. Replace when published.'),
        ('pt_hg_on', '  HGH toggle (1 = closes 1-Jan-2027; 0 = excluded)', 1.0, 'gen', 'Company: closing expected "by the beginning of 2027", subject to regulatory approvals.'),
        ('pt_hg_ev', '  HGH enterprise value (EUR m)', 300.0, 'm1', 'Company: "enterprise value of approximately EUR 300 million".'),
        ('pt_hg_rev', '  HGH revenue base (EUR m; c.2026)', 40.0, 'm1', 'Company: "c. EUR 40 million of revenues", c.30% revenue CAGR (base year not stated: ASSUMPTION 2026).'),
        ('pt_hg_m', '  HGH standalone EBITDA margin (derived)', 0.455, 'pct', 'Derived: EV 300 ÷ 16.5x ("mid- to high-teens" EV/EBITDA) = EUR 18.2m ÷ EUR 40m. ASSUMPTION.'),
        ('pt_hg_syn', '  HGH run-rate synergies (EUR m)', 12.0, 'm1', 'Derived: c.10x post synergies by year 2–3 → EUR 30m EBITDA − EUR 18.2m standalone ≈ EUR 12m. ASSUMPTION.'),
        ('pt_hg_dep', '  HGH depreciation % of revenue', 0.03, 'pct', 'ASSUMPTION (asset-light, R&D-focused business).'),
        ('pt_hg_int', '  HGH identified intangibles % of EV', 0.25, 'pct', 'ASSUMPTION (Kappa: intangibles EUR 27.1m of EUR 69.9m consideration).'),
        ('pt_hg_life', '  HGH intangibles amortisation life (years)', 10.0, 'gen', 'ASSUMPTION.'),
    ],
    'levers': [
        ('lv_floor', 'Leverage floor for buybacks (net debt / adjusted EBITDA, x)', (2.0, 1.5, 1.0), 'x',
         'ASSUMPTION — no open-market programme (treasury purchases serve the LTIP). Company: c.3.0x pro forma post-HGH, c.2.5x by 2027 (unverified).'),
        ('lv_pay', 'Dividend payout ratio (% of net income attributable)', (0.30, 0.30, 0.25), 'pct', 'Company policy 20–30% (FY2025: 30%).' + UNV),
    ],
    'blocks': [
        ('NV_G', 'NV_G (night vision revenue growth)', 0.04, -0.07, [0.15, 0.12, 0.10, 0.08],
         'H1-26 +25.6%; OCCAR firm order for 100,000 NVGs (c.EUR 1bn, Bundeswehr) delivering through 2029; soft backlog EUR 1.46bn = 2.4x FY26 revenue (company). Fades with the order cycle.', 'pct', False),
        ('TH_G', 'TH_G (thermal imaging revenue growth)', 0.05, -0.08, [0.20, 0.18, 0.15, 0.12],
         'IRIS-C thermal clip-on contracts (Germany, up to 25,000 sets, >EUR 100m; OCCAR). Small base (H1-26 EUR 10.9m).', 'pct', False),
        ('PL_G', 'PL_G (platform-based / ISR & other growth; also MERIO and bolt-ons)', 0.05, -0.10, [0.35, 0.30, 0.25, 0.20],
         'Kappa order build-up, Rheinmetall PHYLAX (>EUR 40m committed), Safran UAS JV; new-digital products c.20–25% of FY26 revenue (company).', 'pct', False),
        ('MRG', 'MRG (adjusted EBIT margin — existing portfolio + MERIO)', 0.015, -0.025, [0.25, 0.25, 0.25, 0.25],
         'Company: "preserving market leading mid-twenties EBIT margins" incl. new-product roll-out (unverified). FY25 26.2%, H1-26 26.2%.', 'pct', False),
        ('HG_G', 'HG_G (HGH revenue growth)', 0.05, -0.10, [0.25, 0.22, 0.18, 0.15],
         'Company: c.30% revenue CAGR historically; Base fades from 25%. ASSUMPTION.', 'pct', False),
        ('MA', 'MA (bolt-on M&A spend, EUR m)', 50.0, -50.0, [0.0, 50.0, 50.0, 50.0],
         'Company: bolt-on M&A "without the need for a new share capital increase"; nil in 2027E while leverage falls after HGH. ASSUMPTION.', 'm', True),
    ],
    'ma_evs': 3.0, 'ma_m': 0.20, 'dna_pct': 0.022, 'etr': 0.23, 'capex_pct': 0.04, 'debt_rate': 0.05, 'cash_yield': 0.02,
    'amort_kappa': 3.7, 'nri_q': {3: 0.0, 4: 0.0}, 'nri_ae': 0.0, 'nri_hgh': 5.0, 'fv_h126': MAN['fv_gains']['H1-26'],
    'wc': WC, 'px': MAN['share_price']['value'],
    'px_note': ('VALUATION — share price input EUR 29.84 = market capitalisation EUR 2,346.2m ÷ 78,624,645 shares in issue at 30-Jun-2026 (H1 2026 semi-annual report); '
                'update to market'),
    'px_cell_note': ('EUR 29.84 = H1 2026 report market capitalisation EUR 2,346,159,408 ÷ 78,624,645 shares (30-Jun-2026). The user gave no price; no SEC-filed price exists '
                     '(Theon files no Forms 4 / 10-Q). Update to market. Other filed reference: EUR 26.10 close on 28-Nov-2025 (rights-issue announcement).'),
    'rev_guid_note': 'Company FY26 revenue guidance EUR 570–600m (FY2025 preliminary results, 16-Feb-2026; reiterated 27-Jul-2026). Unverified — company release, not on EDGAR.',
}
V0['nri_q'] = V0['nri_q'][3]

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
CAGR_G = {'is_rev', 'g_rev', 'g_org', 'nv', 'th', 'pl', 'r_adj', 'r_ebit', 'is_op', 'is_ni', 'is_nip', 'eps_dil', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta',
          'bs_teq', 'd_dna', 'is_gp', 'e_adjni', 'kp_bl'}
CAGR_A = {'g_adj_m', 'r_adj_m', 'r_ebit_m', 'is_gm', 'is_opm', 'gm_rev', 'gm_cc', 'gm_gm', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_adjop_m', 'fcf_m',
          'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'd_dna_pct', 'wc_nwc_p', 'is_etr', 'm_org', 'nv_mix', 'th_mix', 'pl_mix', 'gm_opex', 'kp_btb'}

def style_cagr(ws, r, on):
    src = 16 if on else 12
    for c in CAGR:
        ws[f'{c}{r}']._style = copy.copy(TM[f'{L(CI(c) + TSHIFT)}{src}']._style)

def write_row(ws, row):
    r = row.r; arch = ARCH[row.arch]
    clone_row_style(ws, arch, r)
    ws.cell(r, 2).value = row.label or None
    if row.kw.get('note'): ws[f'{NOTE}{r}'] = row.kw['note']
    if row.kw.get('group'):
        ws.row_dimensions[r].outlineLevel = 1; ws.row_dimensions[r].hidden = True
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
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    a = {y: ANN[y].c for y in ANN}
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({a[2030]}{r}/{a[2025]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({a[2025]}{r}/{a[2021]}{r})^(1/4)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({a[2025]}{r}/{a[2022]}{r})^(1/3)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({a[2025]}{r}/{a[2023]}{r})^(1/2)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2026, 2031))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2022, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{a[y]}{r}" for y in range(2023, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)
    for (k, c), t in CELL_NOTES.items():
        if k == row.key: comment(ws[f'{c}{r}'], t)

SRC = 'Source: Theon International Plc regulated reports (media.theon.com) — '
LABEL_SOURCES = {
    'nv': (SRC + 'revenue-disaggregation note "Major products categories" in the Q1 / 9M trading updates (condensed statements), semi-annual reports and annual reports; '
           '2023 quarters from the comparatives in the 2024 documents; FY2022 from the FY2023 annual report (restated). Discrete quarters = YTD differences.'),
    'rg_eu': SRC + 'revenue note "Primary geographic markets".',
    'kp_oi': SRC + 'results / trading-update press releases (order intake YTD, soft backlog and options at period end). See manual_items.json for each URL.',
    'is_rev': (SRC + 'consolidated statement of profit or loss: FY2021 annual report (as first reported); FY2022 restated comparative in the FY2023 annual report (note 37); '
               'FY2023–25 annual reports; Q1 / 9M trading updates and H1 semi-annual reports (Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M). 2023 quarters from the 2024 documents\' comparatives.'),
    'd_dna': SRC + '"Adjusted EBIT / EBITDA" APM reconciliation (adjusted EBITDA − adjusted EBIT).',
    'r_ebit_pub': SRC + 'APM reconciliation in each Q1 / H1 / 9M / FY document ("Adjusted EBIT"); definition flags in the row below.',
    'is_finc': SRC + 'finance income; fair-value gains on FVTPL financial assets from the cash-flow add-back in the H1 / FY statements (manual_items.json).',
    'sh_dil': SRC + 'EPS notes (weighted-average number of ordinary shares, basic = diluted).',
    'cf_ni': (SRC + 'statements of cash flows (year-to-date; discrete quarters derived). The Q1 / 9M updates print a condensed statement ("Non cash items"); '
              'H1 / FY statements are mapped to the same lines (non-cash items = cash generated before working capital − profit). FY2021 cash flow not used (no restated statement).'),
    'bs_cash': SRC + 'statements of financial position at each quarter end from Q1-24; 31-Dec-2021 and 31-Dec-2022 restated in the FY2023 annual report; 2023 quarter ends not published.',
    'me_rev': 'Source: theon.com news 4-May-2026 (binding terms) and 29-Oct-2026 (approvals received, completion underway).',
    'hg_rev': 'Source: theon.com news 17-Jun-2026 (exclusivity with Carlyle), Q2/H1-26 trading update 27-Jul-2026 and H1 2026 report (EUR 325m term loan).',
    'cal_rev': 'Source: FY2025 preliminary results (16-Feb-2026) and Q2/H1-2026 trading update (27-Jul-2026). Unverified — company releases, not on EDGAR.',
}
CELL_NOTES = {}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('FY2021: not published (pre-IPO annual report)', None),
        'D': ('FY2022: adjusted EBIT = EBIT (no non-recurring items; FY2023 annual report, restated)', None),
        q(2023, 1): ('2023 – Q1-25: EBIT + non-recurring items; share of profit of equity-accounted investees EXCLUDED (presented below operating profit)',
                     'Q1-24 update: "Adjusted EBITDA is calculated by adjusting profit for the period after tax to exclude the impact from taxation, net finance costs, '
                     'depreciation and amortization, impairment of assets, gains from the revaluation of assets, the share of profit of equity-accounted investees and non-recurring expenses."'),
        q(2025, 2): ('From Q2-25 (effective 1-Jan-2025; 2024 restated; Q1-25 restated in the Q1-26 update): share of profit of CORE equity-accounted investees INCLUDED in operating profit, adjusted EBIT and EBITDA',
                     'AR2025 note 7.a / H1-25 report: change in accounting policy to include the Group\'s share of profits from core equity-accounted investees within operating profit, '
                     'adopted in Q2 2025, effective 1 January 2025. FY2024 adjusted EBIT 88.386 as first published → 90.833 restated. The check uses each period\'s figure as first published, '
                     'except Q2-25, derived from H1-25 less the restated Q1-25 (23.777).'),
    }
    DEFS['e_def'] = {c: ('Model definition (THEON publishes no adjusted EPS): + non-recurring items after tax − fair-value gains on FVTPL financial assets', None)
                     for c in (ANN[2022].c,)}

def write_defs(ws, row):
    for c, (txt, cm) in DEFS[row.key].items():
        cell = ws[f'{c}{row.r}']; cell.value = txt
        cell.font = Font(name='Calibri', sz=10, b=True, i=True, color='FFC00000')
        if cm: comment(cell, cm)

def write_scen(ws):
    srcrow = {'hdr': 9, 'out_hdr': 11, 'pt_hdr': 15, 'out': 12, 'pt': 16, 'lev': 28, 'blk': 30, 'yr': 31}
    nfmap = {r: nf for (_, _, _, nf, _) in []}
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
            nf = 'pct' if 'payout' in lab else 'x'
            for col, v in zip([SBULL, SBASE, SBEAR], [a, b, c_]):
                ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF[nf]; set_color(ws[f'{col}{r}'], BLUE)
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 outlook end-points (revenue, adjusted EBIT margin; high / mid / low), '
            'the leverage floor and payout levers, and 2027E–2030E product-line growth, adjusted EBIT margin, HGH growth and bolt-on M&A '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Theon International Plc (Euronext Amsterdam: THEON) — 3-Statement Financial Model'
    ws['B3'] = ('IFRS as adopted by the EU · EUR millions (per-share data in EUR; shares in millions) · Sources: Theon International Plc regulated reports and releases at '
                'media.theon.com / theon.com (listing prospectus 24-Jan-2024; annual reports FY2021–25; semi-annual reports H1-24–H1-26; Q1 / 9M trading updates with condensed '
                'statements; results and deal releases). Theon is not an SEC registrant: EDGAR CIK 0002095508 holds only Schedule 13G filings on its Kopin stake, so the '
                'regulator-filed documents are used in lieu of EDGAR (user instruction). Guidance is from company releases and is marked unverified.')
    ws['B4'] = ('Basis notes: calendar fiscal year; one reportable segment (Optronics; revenue disaggregated by product and geography). FY2021 P&L as first reported; FY2022 and '
                'the 31-Dec-2021 / 31-Dec-2022 balance sheets restated in the FY2023 annual report (correction of errors). Quarters from Q1/23 (2023 from the 2024 comparatives; '
                'Q2 = H1 − Q1, Q4 = FY − 9M). Share of profit of equity-accounted investees inside operating profit in all periods (company presentation from Q2-25). Kappa '
                'Optronics consolidated from 14-Jan-2026; Exosens 9.8% (7-Jan-2026) at fair value. Q3/26E–Q4/26E calibrated to FY26 guidance; MERIO (Q4-26) and HGH (1-Jan-2027, '
                'toggle) outside guidance. IPO 7-Feb-2024 (EUR 10.00); rights issue Dec-2025 (EUR 17.40).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(EURm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '4Y CAGR', '3Y CAGR', '2Y CAGR'], ["25-'30", "21-'25", "22-'25", "23-'25"]):
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
    defs_setup()
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
        p = os.path.join(BASE, f'THEON_{scen}.xlsx')
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
    """recalculate a copy with LibreOffice and inject its values as cached results into the openpyxl-written file (charts untouched)"""
    import shutil
    p = os.path.join(BASE, 'THEON_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
