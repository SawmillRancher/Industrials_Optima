"""Build RBC_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'RBC_Model.xlsx')
G = MAN['guidance_q2fy27']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2026']['x']
    rev, cogs = q['rev'], q['cogs']
    return {'dso': round(q['bs_ar'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365), 'dpo': round(q['bs_ap'] / cogs * 365),
            'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['dio_ae'] = {2028: WC['dio'] - 4, 2029: WC['dio'] - 8, 2030: WC['dio'] - 12, 2031: WC['dio'] - 15, 2032: WC['dio'] - 15}
WC['note'] = (f'Forecast inputs at fiscal-year-end (28-Mar-2026) levels on FY2026 net sales / cost of sales (DSO {WC["dso"]}d, inventory {WC["dio"]}d, '
              f'payables {WC["dpo"]}d, accrued & other current liabilities {WC["ocl"]:.1%} of sales); year ends are compared with year ends. '
              'Inventory days ease 4–15 days by FY2031E (assumption: aerospace & defense ramp absorbs the inventory built in FY2025–26).')
AM = MAN['amort_sched']
VAC = MAN['deals']['vacco']; PSC = MAN['deals']['psc']

V0 = {
    'out_hdr': 'Q2 FY27 guidance — Q1 FY27 release (31-Jul-2026)',
    'out_note': G['text'],
    'outlook': [
        ('out_sal', '  Q2 FY27 net sales ($m)', tuple(G['sales']), 'm1', 'Guided ~$505–515m. Drives the Q2/27E sales calibration (Δ carried into Q3–Q4).'),
        ('out_gm', '  Q2 FY27 gross margin %', tuple(G['gm']), 'pct', 'Guided 45.5–45.75%. Drives the Q2/27E segment gross-margin calibration (Δ carried).'),
        ('out_sga', '  Q2 FY27 SG&A % of net sales (Bull = low end)', tuple(G['sga']), 'pct', 'Guided 16.5–16.75%. Applied directly in Q2/27E.'),
    ],
    'points': [
        ('pt_etr', '  Q2–Q4/27E tax rate (GAAP)', 0.225, 'pct', 'Not guided. Q1 FY27 22.1% (23.2% excluding discrete stock-compensation benefits); FY2026 22.1%.'),
        ('pt_aetr', '  Q2–Q4/27E adjusted tax rate', 0.22, 'pct', 'Q1 FY27 "overall tax rate applied to adjusted pre-tax earnings" 22.0% (Q1 FY26 22.5%).'),
        ('pt_restr', '  Q2–Q4/27E restructuring & consolidation per quarter ($m)', 0.5, 'm1', 'Q1 FY27 $0.4m; FY2026 $6.2m (assumption).'),
        ('pt_othx', '  Q2–Q4/27E other, net excl. M&A amortization & items per quarter ($m)', 1.5, 'm1',
         'Q1 FY27 $1.3m ($21.0m amortization of intangible assets − $19.5m M&A-related + $0.4m restructuring − $0.2m other items); mostly software amortization.'),
        ('pt_dff', '  Q2–Q4/27E amortization of deferred finance fees per quarter ($m)', 0.4, 'm1',
         'Q1 FY27 $0.8m; $0.6m of term-loan fees remain to Nov-2026 and $2.1m of revolver fees amortize to Oct-2030 (10-Q Note 10).'),
        ('pt_onop', '  Q2–Q4/27E other non-operating expense per quarter ($m)', 0.5, 'm1', 'Q1 FY27 $0.5m; FY2026 $1.9m (pension and other).'),
    ],
    'lev': (1.5, 1.0, 0.5),
    'lev_note': ('Net debt $682m at 27-Jun-2026 ≈ 1.0x LTM adjusted EBITDA (FY2026 $605m); the credit agreement allows up to 4.5x. RBC has made no open-market buybacks '
                 '(the $100m 2019 authorization is unused) and has deployed cash to debt reduction and acquisitions. Target = leverage up to which surplus cash after the '
                 'M&A lever is returned via buybacks (assumption).'),
    'blocks': [
        ('AERO_G', 'AERO_G (Aerospace & Defense sales y/y, organic + future acquisitions excluded)', 0.03, -0.05, [0.11, 0.10, 0.09, 0.08, 0.07],
         'Q1 FY27 +36.9% (+16.0% organic ex VACCO $34.4m); backlog $2.3bn. Defense (submarines, munitions, space) and commercial aerospace rate increases; FY2023–26 A&D sales CAGR 22% incl. VACCO.', 'pct', False),
        ('IND_G', 'IND_G (Industrial sales y/y)', 0.02, -0.06, [0.06, 0.055, 0.05, 0.05, 0.045],
         'Q1 FY27 +8.4% (semicon, grain, food & beverage); FY2023–26 Industrial sales flat to +4% a year after the Dodge-led FY2023 step-up; cyclical downside (FY2021 −12% legacy industrial).', 'pct', False),
        ('AERO_M', 'AERO_M (Aerospace & Defense segment gross margin %)', 0.01, -0.025, [0.440, 0.445, 0.450, 0.452, 0.455],
         'Q1 FY27 44.5%; FY2026 40.7% (VACCO integration), FY2023 39.7%; volume leverage and VACCO margin improvement.', 'pct', False),
        ('IND_M', 'IND_M (Industrial segment gross margin %)', 0.01, -0.025, [0.485, 0.490, 0.495, 0.497, 0.500],
         'Q1 FY27 50.2%; FY2026 47.1%, FY2023 41.8%: Dodge pricing and productivity (synergies); cyclical downside.', 'pct', False),
        ('SGA', 'SGA (SG&A % of net sales)', -0.003, 0.005, [0.163, 0.162, 0.161, 0.160, 0.160],
         'Q1 FY27 16.5%; FY2026 16.9%, FY2025 17.1%; operating leverage on fixed corporate costs. Bull = lower ratio.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 150.0, -250.0, [250.0, 250.0, 250.0, 250.0, 250.0],
         'RBC spent $276.7m on VACCO (FY2026), $24.2m on PSC (FY2027), $2.9bn on Dodge (FY2022), $500m on Sargent (FY2016). Base $250m p.a. (assumption).', 'm', True),
    ],
    'aero_acq': {2: round(VAC['q1fy27_sales'] * 3 / 13, 1), 3: 0.0, 4: 0.0},
    'aero_acq_note': ('Q1 FY27: VACCO $34.4m (release: "$34.4 of net sales this quarter came from VACCO, which we acquired on July 18, 2025"; not in the Q1 FY26 base). '
                      'Q2/27E: VACCO sales for the ~3 weeks before the 18-Jul anniversary that are not in the Q2 FY26 base = $34.4m × 3/13 (assumption). Q3–Q4: nil.'),
    'ind_acq': {2: round(PSC['ltm_sales'] * 47 / 365, 1), 3: round(PSC['ltm_sales'] * 91 / 365, 1), 4: round(PSC['ltm_sales'] * 98 / 365, 1)},
    'ind_acq_note': ('PSC Couplings (closed 10-Aug-2026; LTM net sales ~$15.1m, 8-K 11-Aug-2026): run-rate × days consolidated (47 days in Q2, 91 in Q3, 98 in the 14-week Q4). '
                     'Outside the Q2 guidance (issued 31-Jul-2026).'),
    'amort_q': {2: 20.8, 3: 20.8, 4: 21.0},
    'amort_sched': {2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: AM['2031'], 2032: AM['2032']},
    'amort_note': AM['src'] + ': remainder of FY2027 $62.6m (split $20.8m / $20.8m / $21.0m), FY2028 $81.3m, FY2029 $78.8m, FY2030 $73.0m, FY2031 $69.3m, FY2032 $69.3m.',
    'amort_share': 0.93,
    'dxa_pct': 0.028, 'sbc_pct': 0.018, 'othx_pct': 0.003, 'etr': 0.23, 'aetr': 0.225, 'onop': 2.0, 'dff': 0.6,
    'ae_restr': {2028: 2.0, 2029: 2.0, 2030: 2.0, 2031: 2.0, 2032: 2.0},
    'int_q': {2: 9.3, 3: 8.6, 4: 8.6},
    'int_q_note': ('Point estimates (not guided): Q1 FY27 $10.1m. Notes $500m × 4.375% ($5.5m a quarter) + term loan / revolver (~$250m → ~$220m after the Nov-2026 term-loan '
                   'maturity) at ~5.0% + fees and deferred-fee amortization; Q4 has 14 weeks (assumption).'),
    'capex_q': 0.045, 'capex_pct': {2028: 0.040, 2029: 0.038, 2030: 0.035, 2031: 0.035, 2032: 0.035},
    'def_q': 0.0, 'def_ae': 0.0, 'wh_q': 1.0, 'wh_ae': 12.0, 'eq_q': 3.0, 'eq_ae': 12.0,
    'iss_q': {2: 0.02, 3: 0.02, 4: 0.02}, 'iss_ae': 0.15, 'dil': 0.16,
    'iss_notes': {2028: 0.0, 2029: 0.0, 2030: 500.0, 2031: 0.0, 2032: 0.0},
    'repay': {2028: 0.0, 2029: 0.0, 2030: 500.0, 2031: 0.0, 2032: 0.0},
    'mat': {2027: 0.0, 2028: 0.0, 2029: 500.0, 2030: 0.0, 2031: 0.0, 2032: 0.0},
    'repay_note': ('FY2027E: term loan $96.0m ($50.0m repaid Jul-2026, $46.0m at the 2-Nov-2026 maturity; 10-Q Note 10 and MD&A). FY2030E: $500m 4.375% senior notes due '
                   '15-Oct-2029, assumed refinanced (input row above). Schaublin borrowings (to 2036) and finance leases held flat.'),
    'min_cash': 75.0, 'rev_lq': 200.0,
    'r_notes': {2028: 0.045, 2029: 0.045, 2030: 0.050, 2031: 0.055, 2032: 0.055},
    'r_notes_note': ('4.375% senior notes + 2.00% Schaublin line + finance leases ≈ 4.5%; the 2029 notes are assumed refinanced at ~5.5% (assumption) from FY2030E.'),
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $510.00 (provided by the user on 13-Oct-2026; not an SEC-filed price); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $250m p.a. of acquisitions from FY2028E). Funded from cash / revolver (debt schedule).',
    'rev_guid_note': 'Company Q2 FY27 net sales outlook $505.0–515.0m (Q1 FY27 release, 31-Jul-2026). Drives the sales calibration.',
    'gm_guid_note': 'Company Q2 FY27 gross margin outlook 45.5–45.75% (Q1 FY27 release). Drives the segment gross-margin calibration.',
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
CAGR_G = {'is_rev', 'g_rev', 'aero_rev', 'ind_rev', 'o_adj', 'r_adj', 'is_oi', 'd_dda', 'e_adjnic', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_eq', 'sh_dil',
          'is_gp', 'is_sga', 'd_amA', 'aero_gm', 'ind_gm', 'is_ni', 'eps_dil', 'g_gm', 'r_ebitda'}
CAGR_A = {'aero_gmp', 'ind_gmp', 'g_gmp', 'o_adj_m', 'r_adj_m', 'is_gm', 'is_oim', 'r_ebit_m', 'gm_rev', 'gm_aero', 'gm_ind', 'gm_gm', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_sga', 'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x',
          'd_sga', 'd_dxa_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'aero_mix', 'ind_mix'}
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
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2032]}{r}/{A[2027]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2021]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2016]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2006]}{r})^(1/20)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2028, 2033))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2022, 2027))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2017, 2027))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2006, 2027))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: RBC Bearings earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
SEGN = 'Source: RBC Bearings Forms 10-Q / 10-K, segment note ("Reportable Segments"; Q4 = fiscal year (10-K) − nine months (Q3 10-Q)). '
LABEL_SOURCES = {
    'aero_rev': REL + 'segment data, net external sales (Aerospace & Defense / Industrial from the Q3 FY22 release; FY2021 and Q3 FY21–Q2 FY22 from the re-presented comparatives in the FY2022–23 releases).',
    'aero_gm': SEGN + 'Segment gross margin (the CODM measure). Q1–Q2 FY22 and FY2021 from the re-presented comparatives in the following year\'s filings.',
    'aero_soi': SEGN + 'Segment operating income was presented FY2022–FY2025 (with SG&A by segment); from FY2026 the note shows gross margin only.',
    'leg_plain': REL + 'segment data, net external sales on the legacy four-segment structure (FY2006: 10-K segment note).',
    'is_rev': ('Source: quarters — earnings releases (8-K Ex. 99.1) three-month columns; fiscal years — Form 10-K statements of operations; as originally reported '
               '(the FY2022 10-K/A restatement of FY2020–22 is shown as memo rows, not recast).'),
    'd_dda': 'Source: 10-Q / 10-K cash-flow statements (year to date; discrete quarters derived, Q4 = FY − 9M).',
    'd_amA': REL + '"M&A related amortization" in the adjusted-net-income reconciliation (published from the Q2 FY23 release; re-presented for Q1 FY22–Q1 FY23 in memo only).',
    'o_pub': REL + 'Reconciliation of Reported Operating Income to Adjusted Operating Income (FY2006+; none in FY2012 and Q1 FY15, when nothing was adjusted).',
    'e_pub': REL + 'Reconciliation of Reported Net Income to Adjusted Net Income and adjusted EPS (definition in force: old to Q1 FY23, current from Q2 FY23).',
    'r_adj_pub': REL + '"Adjusted operating income plus depreciation/amortization plus incentive stock compensation expense" (selected financial data, Q2 FY16–Q2 FY22) and Adjusted EBITDA (Q3 FY22+).',
    'cf_ni': 'Source: 10-Q / 10-K consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M).',
    'bs_cash': 'Source: 10-Q / 10-K consolidated balance sheets (period ends); shares outstanding = shares issued − treasury shares (XBRL).',
    'ppa_cons': 'Source: FY2023 10-K Note (Dodge, final allocation; net assets $2,962.7m less cash $81.9m); FY2026 10-K Note 21 (VACCO, final allocation $276.7m).',
    'sh_basic': REL + 'statements of operations (weighted average shares). No stock splits since the Aug-2005 IPO; the Series A MCPS converted into common stock in Oct-2024.',
    'ds_total': 'Source: balance sheets; Q1 FY27 10-Q Note 10 (debt); 8-Ks 21-Jul-2025 (VACCO revolver draw) and 30-Oct-2025 (revolver extended to Oct-2030).',
    'psc_h': MAN['deals']['psc']['src'],
    'is_oi_rs': MAN['restated']['src'],
    'bkl': REL + 'selected financial data / text ("Backlog as of ...").',
}
CELL_COMMENTS = {}
def comments_setup():
    q = lambda y, n: QC[(y, n)].c
    CELL_COMMENTS['aero_rev'] = {A[2021]: 'FY2021 on the current segment basis, from the FY2022 Q4 release comparative (re-presented).',
                                 q(2021, 3): 'Re-presented comparative (Q3 FY22 release).', q(2021, 4): 'Re-presented comparative (Q4 FY22 release).',
                                 q(2022, 1): 'Re-presented comparative (Q1 FY23 release).', q(2022, 2): 'Re-presented comparative (Q2 FY23 release).'}
    CELL_COMMENTS['aero_acq'] = {q(2027, 1): MAN['deals']['vacco']['src']}
    CELL_COMMENTS['is_oi'] = {A[2022]: 'As originally reported ($130.1m). Restated to $121.1m in the FY2022 10-K/A (5-Aug-2022) for stock-based compensation timing — memo row below.',
                              A[2021]: 'As originally reported ($111.5m); restated to $114.7m in the FY2022 10-K/A.', A[2020]: 'As originally reported ($156.8m); restated to $149.4m in the FY2022 10-K/A.'}
    CELL_COMMENTS['e_pub'] = {q(2023, 1): 'Q1 FY23: headline adjusted EPS on the old definition ($1.19); the release also showed "new adjusted" EPS of $1.79 (current definition — memo row).',
                              q(2023, 2): 'Q2 FY23: the adjusted EPS definition changes to add back M&A-related amortization, stock compensation and amortization of deferred finance fees (pre-tax, tax-effected); the Q2 FY22 comparative was re-presented ($1.16 vs $0.89 originally).',
                              q(2022, 3): 'Loss quarter: GAAP diluted EPS uses basic shares (28.6m); adjusted EPS uses 28.9m diluted shares (company count).'}
    CELL_COMMENTS['e_tax'] = {A[2007]: 'Old definition: items shown net of tax ("Item was tax effected at the effective tax rate"); this row = published adjusted net income − GAAP net income − pre-tax operating items − after-tax non-operating items.'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2006–FY2021: adjusted operating income excludes restructuring / plant consolidation, acquisition costs, inventory purchase accounting, litigation reserves, '
              'disposal losses and (FY2006–07) IPO-related compensation, management fees and stock-option expense', 'Release reconciliations; FY2012 and Q1 FY15 releases adjusted nothing (adjusted = GAAP).'),
        q(2022, 3): ('Q3 FY22+: Dodge transaction and related costs, transition services, inventory step-up; Adjusted EBITDA published', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006–Q1 FY23 (old): GAAP net income + items net of tax (incl. FX translation, debt extinguishment, discrete tax); FY2006 adjusted EPS not published', None),
        A[2012]: ('FY2012: no adjusting items, releases show GAAP only (adjusted = GAAP)', None),
        q(2022, 3): ('Q3 FY22–Q1 FY23: pre-tax items with a tax line; preferred dividends (MCPS) deducted; "adjusted cash net income" (Q3–Q4 FY22) and "new adjusted" (Q1 FY23) shown alongside', None),
        q(2023, 2): ('Q2 FY23+ (current): also adds back M&A-related amortization, stock compensation and amortization of deferred finance fees, tax-effected',
                     'Release definition: "exclude non-cash expenses for amortization related to acquired intangible assets other than internal-use software, stock-based compensation, amortization of deferred finance fees, acquisition expenses ... restructuring ... net of their income tax impact and other tax matters". Comparatives re-presented back to Q1 FY22 (memo row).'),
        q(2025, 3): ('Q3 FY25: Series A MCPS converted into common stock (Oct-2024); no preferred dividends thereafter', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: Q2 FY27 sales, gross-margin and SG&A guidance end-points (high / mid / low), '
            'FY2028E–FY2032E segment sales growth and gross margins, SG&A %, M&A spend and the leverage target for FY2028E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'RBC Bearings Incorporated (NYSE: RBC) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Fiscal years end on the Saturday nearest 31 March (FY2027 = 29-Mar-2026 – 3-Apr-2027, '
                '53 weeks) · Source: RBC Bearings Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1) and deal / financing 8-Ks, SEC EDGAR (CIK 1324948); XBRL company facts; '
                'investor-relations releases are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported (the FY2022 10-K/A restatement of FY2020–22 stock-based compensation is shown as memo rows). Segments: Roller / Plain / Ball / Other '
                '(Engineered Products from FY2016) to Q2 FY22; Aerospace & Defense / Industrial from Q3 FY22 (FY2021 and Q3 FY21–Q2 FY22 re-presented). Acquisitions: Sargent Apr-15, '
                'Dodge 1-Nov-21 (MCPS / notes / term loan), VACCO 18-Jul-25, PSC Couplings 10-Aug-26. Q2/27E calibrated to the Q2 FY27 outlook (31-Jul-2026), Δ carried to Q3–Q4/27E; '
                'Q4/27E has 14 weeks.')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '20Y CAGR'], ["27-'32", "21-'26", "16-'26", "06-'26"]):
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
        p = os.path.join(BASE, f'RBC_{scen}.xlsx')
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
    p = os.path.join(BASE, 'RBC_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
