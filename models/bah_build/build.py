"""Build BAH_Model.xlsx (Booz Allen Hamilton Holding Corporation) from the MLM template (same layout, formatting and process as the prior
models; kit adapted from the STE build, which has the same 31-March fiscal year, with the WWD finishing steps)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'BAH_Model.xlsx')
G27 = MAN['guidance_fy27']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2026']['x']; rev = q['rev']
    q1, q0 = DATA['Q1-27']['x'], DATA['Q1-26']['x']
    dso_ye = q['bs_ar'] / rev * 365
    dso_q1 = q1['bs_ar'] / (q1['rev'] * 4) * 365 - q0['bs_ar'] / (q0['rev'] * 4) * 365
    return {'dso': round(dso_ye + dso_q1), 'dso_ye': dso_ye, 'dso_up': dso_q1,
            'oca': round(q['bs_oca'] / rev, 4), 'ap': round(q['bs_ap'] / rev, 4), 'acc': round(q['bs_acc'] / rev, 4), 'ocl': round(q['bs_ocl'] / rev, 4)}
WC = wc_inputs()
WC['dso_note'] = (f'FY2027E+ input {WC["dso"]}d = FY2026 year-end DSO ({WC["dso_ye"]:.1f}d) + the Q1/27 y/y increase in quarter-end DSO ({WC["dso_up"]:+.1f}d; '
                  'Defy Security brought $221m of current billed and unbilled receivables). Year ends are compared with year ends (Q1 is seasonally high).')
WC['note'] = (f'Other working-capital ratios held at fiscal-year-end (31-Mar-2026) levels on FY2026 revenue: other current assets {WC["oca"]:.1%}, '
              f'accrued compensation {WC["acc"]:.1%}, other current liabilities {WC["ocl"]:.1%} (payables & accrued: solved to the FY27 FCF guidance).')
AM = MAN['amort_sched']
_leg = (15.0 - AM['defy_annual'] / 4) * 4                    # Q1/27 acquisition amortization run-rate excl. Defy
ACQAM = {y: round(_leg * AM[str(y)] / AM['2027'] + AM['defy_annual'], 1) for y in (2028, 2029, 2030, 2031)}

V0 = {
    'out_hdr': 'FY27 guidance — Q4 FY26 release (22-May-2026), reiterated in the Q1 FY27 release (24-Jul-2026)',
    'out_note': ('Revenue $11.2–11.7bn (0–4% growth), adjusted EBITDA $1,240–1,290m (~11% margin), adjusted diluted EPS $6.00–6.35, free cash flow $825–925m; '
                 'effective tax rate 20–23%, average diluted shares 118–120m, capex ~$220m ($105m new headquarters). Assumed to exclude Ultra (see the Ultra block).'),
    'outlook': [
        ('out_rev', '  FY27 revenue ($m; legacy basis, excl. Ultra)', tuple(G27['revenue']), 'm', 'Guided $11.2–11.7bn. Drives the Q2–Q4/27E revenue calibration.'),
        ('out_ebitda', '  FY27 adjusted EBITDA ($m; legacy basis)', tuple(G27['adj_ebitda']), 'm', 'Guided $1,240–1,290m. Drives the Q2–Q4/27E adjusted EBITDA margin calibration.'),
        ('out_eps', '  FY27 adjusted diluted EPS ($) — memo', tuple(G27['adj_eps']), 'ps', 'Guided $6.00–6.35 (information row; not forced).'),
        ('out_fcf', '  FY27 free cash flow ($m)', tuple(G27['fcf']), 'm', 'Guided $825–925m. Drives the FY2027E payables & accrued calibration (working-capital block).'),
        ('bb27', '  Q2–Q4/27E share repurchases ($m)', (300.0, 150.0, 50.0), 'm',
         'Assumption. Q1/27 $72m (incl. shares withheld for taxes); $634m left on the $4,085m program at 30-Jun-2026; Ultra ($720m) funded in Q2.'),
    ],
    'points': [
        ('pt_int', '  FY27 interest expense, net ($m)', 216.0, 'm1',
         'Not guided (assumption): Q1 $48m; $1.2bn notes at 5.375% / 5.900% from 4-Aug-2026, Term Loan A-1 ($714m, ~5.0%) repaid, lower interest income after the Ultra payment.'),
        ('pt_oth', '  FY27 other income (expense) ($m)', 26.0, 'm1', 'Q1 $20m (incl. $18m net gains on investments and dispositions); ~$2m a quarter after (assumption).'),
        ('pt_amort', '  FY27 acquisition amortization excl. Ultra ($m)', 60.0, 'm1', 'Q1 $15m (incl. Defy, $86m over 8 years) × 4.'),
        ('pt_dep', '  FY27 depreciation & other amortization ($m)', 120.0, 'm1', 'Q1 $30m (D&A $45m − acquisition amortization $15m) × 4.'),
        ('pt_sbc', '  FY27 stock-based compensation ($m)', 84.0, 'm1', 'Q1 $21m × 4 (FY26 $69m).'),
        ('pt_etr', '  Q2–Q4/27E effective tax rate', 0.215, 'pct', 'FY27 guidance 20–23% (Q1/27 21.1%).'),
        ('pt_capex', '  FY27 capital expenditures ($m)', G27['capex'], 'm1', 'Guided ~$220m, of which ~$105m for the new headquarters (Q1 $20m).'),
        ('pt_acqc', '  FY27 other corporate (acquisition) expenses, adjusted out ($m)', 25.0, 'm1', 'Q1 $10m (Defy; Ultra agreement). Ultra closing and integration costs (assumption).'),
        ('pt_nonop', '  FY27 non-operating adjusting items ($m)', 0.0, 'm1', 'None in Q1/27 (debt-cost amortization no longer adjusted out since FY2026).'),
        ('pt_alloc', '  Two-class allocation to participating securities (% of net income)', 0.008, 'pct', 'FY2026 0.7%, Q1/27 1.0%, FY2025 0.5%.'),
        ('pt_adjtax', '  Tax rate on adjusting items (company assumed rate)', 0.26, 'pct', 'Release footnote: "assumed effective tax rate of 26%, which approximates the blended federal and state tax rates".'),
        ('pt_ul_m', '  FY27 Ultra adjusted EBITDA margin', 0.25, 'pct', 'Company: "EBITDA margins well above 20%" (8-K Ex. 99.1, 22-Jun-2026). 25% is an assumption.'),
    ],
    'lev': (3.25, 3.0, 2.5),
    'lev_note': ('Assumption (no leverage target in the SEC filings). Net leverage ratio (net debt / LTM adjusted EBITDA, company definition) 2.6x at 31-Mar-2026, 2.7x at 30-Jun-2026; '
                 '~3.2x pro forma for Ultra. Target = leverage up to which surplus cash is returned via buybacks; below it free cash flow repays debt / builds cash.'),
    'blocks': [
        ('NS_G', 'NS_G (National Security revenue y/y, ex-Ultra)', 0.02, -0.03, [0.04, 0.05, 0.05, 0.05],
         'FY26 +2.0%, Q1/27 +1.3% (incl. Defy); FY2022–25 CAGR +9%. Record $39.5bn backlog, Q1/27 book-to-bill 1.5x; defense / intelligence budget growth (FY26 NDAA). Assumption.', 'pct', False),
        ('CC_G', 'CC_G (Civil & Commercial revenue y/y)', 0.04, -0.04, [-0.04, 0.0, 0.02, 0.03],
         'FY26 −22% (civil agency contract cuts and cancellations, contract sale Nov-2025), Q1/27 −16%. Assumed to trough in FY28. Assumption.', 'pct', False),
        ('ULTRA_G', 'ULTRA_G (Ultra Mission Solutions revenue y/y)', 0.05, -0.08, [0.15, 0.15, 0.12, 0.10],
         'Company: "expects revenue from this acquisition to grow at a strong double-digit rate for the next several years" (22-Jun-2026). Base = 15% fading to 10%.', 'pct', False),
        ('ADJ_M', 'ADJ_M (legacy adjusted EBITDA margin on revenue)', 0.005, -0.01, [0.112, 0.113, 0.114, 0.115],
         'FY26 11.0%, FY25 11.0%, FY24 11.0%; FY27 guided ~11% (calibrated). Mix shift to National Security and fixed-price / product work vs pricing pressure (outcomes-based contracts).', 'pct', False),
        ('ULTRA_M', 'ULTRA_M (Ultra adjusted EBITDA margin)', 0.03, -0.03, [0.25, 0.25, 0.25, 0.25], 'Company: "EBITDA margins well above 20%". Assumption.', 'pct', False),
        ('B2B', 'B2B (annual book-to-bill, x)', 0.10, -0.15, [1.05, 1.05, 1.05, 1.05], 'FY2022–26 1.1–1.4x (FY26 TTM 1.1x); Q1/27 1.5x.', 'x2', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 150.0, -150.0, [150.0, 150.0, 150.0, 150.0],
         'Booz Allen bought Liberty IT ($725m, FY22), EverWatch ($440m, FY23), PGSC (FY25), Defy ($235m, Q1/27) and Ultra ($720m, Q2/27). Base $150m p.a. (assumption).', 'm', True),
    ],
    'ul_run': 180.0, 'ul_intp': 0.40, 'ul_life': 10,
    'bill_pct': 0.305, 'cost_pct': 0.475, 'dep_pct': 0.010, 'sbc_pct': 0.0065, 'etr': 0.225, 'oth_ae': 8.0,
    'capex_pct': {2028: 0.009, 2029: 0.009, 2030: 0.009, 2031: 0.009},
    'dps_q': 0.59, 'dps_g': 0.06, 'def_q': 0.0, 'def_ae': 10.0, 'eq_q': 10.0, 'eq_ae': 45.0, 'iss_q3': 0.6, 'iss_ae': 1.2, 'dil': 0.25,
    'nonop_ae': 0.0,
    'acqam_sched': ACQAM,
    'acqam_note': (AM['src'] + ' Model: Q1/27 acquisition amortization excl. Defy ($' + f'{_leg:.1f}' + 'm annualised) run off with the 10-K schedule ratios '
                   f'(FY28 {AM["2028"] / AM["2027"]:.0%}, FY29 {AM["2029"] / AM["2027"]:.0%}, FY30 {AM["2030"] / AM["2027"]:.0%}, FY31 {AM["2031"] / AM["2027"]:.0%} of FY27) + Defy $10.75m a year. Ultra added separately.'),
    'iss_notes': {2027: 1200.0, 2028: 0.0, 2029: 700.0, 2030: 1200.0, 2031: 605.4},
    'repay': {2027: 728.1, 2028: 23.4, 2029: 737.5, 2030: 1237.5, 2031: 633.5},
    'mat': {2027: 23.4, 2028: 737.5, 2029: 1237.5, 2030: 633.5, 2031: 0.0},
    'repay_note': ('2027E: Term Loan A-1 $714m repaid from the Aug-2026 notes + Term Loan A-2 amortization (0.625% of $750m a quarter); 2028E: A-2 amortization (1.25% a quarter '
                   'from Feb-2028, assumed two years after funding); 2029E: 3.875% notes due Sep-2028 ($700m) + A-2; 2030E: 4.000% notes due Jul-2029 ($500m) + 5.375% notes '
                   'due 2030 ($700m) + A-2; 2031E: A-2 balloon (Feb-2031) + amortization. Maturities refinanced with new notes (input row above; assumption).'),
    'min_cash': 400.0, 'min_cash_note': 'Assumption: year-end cash FY2023–26 $405–885m; $1.5bn undrawn revolver.',
    'r_notes': {2028: 0.0515, 2029: 0.0525, 2030: 0.0545, 2031: 0.056},
    'r_notes_note': ('Weighted rate ~5.1% after the Aug-2026 issue (A-2 4.87%, notes 3.875% / 4.000% / 5.950% / 5.950% / 5.375% / 5.900%); rising as the 2028 / 2029 notes '
                     'are refinanced at ~5.75% (assumption).'),
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $75.00 (user-provided, 12-Oct-2026; Q1 FY27 10-Q average repurchase prices $76 May-2026 / $74 Jun-2026; '
                '~$9.0bn market cap); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $150m p.a. of bolt-ons from 2028E). Funded from cash / revolver (debt schedule).',
    'rev_guid_note': ('Company FY27 revenue guidance $11.2–11.7bn (22-May-2026; reiterated 24-Jul-2026). ' + G27['ultra_basis']),
    'eb_guid_note': 'Company FY27 adjusted EBITDA guidance $1,240–1,290m (~11% margin on revenue). Drives the adjusted EBITDA margin calibration (legacy basis).',
}

# ====================================================================== compute engine
PPA = {'Q1-27': {'cons': 235.0, 'nwc': 20.0, 'intang': 86.0, 'gw': 129.0, 'oth': 0.0,
                 'names': 'Defy Security (6-Apr-2026, $235m; provisional PPA, Q1 FY27 10-Q Note 5)'}}

def hist_value(row, col):
    kw = row.kw
    if kw.get('ppa'):
        v = PPA.get(pkey(col), {}).get(kw['ppa'])
        return v if kw.get('textdata') else num(v)
    path = kw.get('data')
    if col.kind == 'A' and kw.get('ann_data'): path = kw['ann_data']
    if not path: return None
    v = xget(pkey(col), path)
    return v if kw.get('textdata') else num(v)

def ppa_e26(row):
    k = row.kw['ppa']
    f = {'cons': f'={V("ul_cons")}', 'nwc': '=0', 'intang': f'={V("ul_cons")}*{V("ul_intp")}', 'gw': f'={V("ul_cons")}*(1-{V("ul_intp")})', 'oth': '=0',
         'names': 'Ultra Mission Solutions (24-Aug-2026, $720m; ASSUMED PPA: 40% intangibles, no net working capital — replace with the Q2 FY27 10-Q)'}
    return f[k]

def first(kw, keys):
    for k in keys:
        if k in kw: return k
    return None

def compute(row, col):
    kw = row.kw; k = col.kind
    CTX.col = col
    if kw.get('ann') and col.q: return None, False
    if kw.get('ppa'):
        if k in HISTK:
            v = hist_value(row, col)
            if v is not None: return v, True
            return (kw['all'](), False) if 'all' in kw and k == 'Q' and pkey(col) in PPA else (None, False)
        if k == 'E26': return ppa_e26(row), False
        return None, False
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
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r},{Q2}{row.r},{Q3}{row.r},{Q4}{row.r})', False
        if kw.get('flow') and not row.spec2 and any(x in kw for x in ('qe', 'qe_in', 'fc')): return S27(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'ns', 'cc', 'rev_xb', 'o_adj', 'g_adj', 'r_adj', 'r_ebitda', 'is_oi', 'is_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf',
          'bs_ta', 'bs_teq', 'sh_dil', 'is_nic', 'eps_dil', 'dps', 'bl_total', 'hc_total', 'r_ebita', 'r_ebit'}
CAGR_A = {'g_adjm', 'g_lm', 'o_adj_m', 'r_adj_m', 'r_adj_xm', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_ns', 'gm_cc', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m',
          'gm_bill', 'gm_ga', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_bill', 'd_cost', 'd_dep_pct', 'd_sbc_pct',
          'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'ns_mix', 'cc_mix', 'bl_b2b', 'ct_cr', 'ct_tm', 'ct_fp'}
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
        t = LABEL_SOURCES.get(row.key)
        if t: comment(ws.cell(r, 2), t)
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
    for c, t in CELL_COMMENTS.get(row.key, {}).items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2031]}{r}/{A[2026]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2021]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2016]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2026]}{r}/{A[2012]}{r})^(1/14)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2022, 2027))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2017, 2027))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2012, 2027))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: Booz Allen earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'ns': ('Source: Forms 10-Q / 10-K, revenue note "Revenue by customer type" (Defense, Intelligence, Civil, Global Commercial; "Clients" renamed "Customers" in FY2025; '
           'National Security and Civil & Commercial from Q1 FY2027, with Q1 FY26 recast). FY2017–18: FY2019 10-K comparatives (ASC 606 recast). Q4 = fiscal year − nine months.'),
    'ul_hdr': 'Source: 8-K 22-Jun-2026 (Item 1.01; Ex. 99.1 announcement), 8-K 24-Aug-2026 (Ex. 99.1, closing), Q1 FY27 10-Q Note 5 (subsequent events / agreement).',
    'bl_total': REL + 'Exhibit 5 "Operating Data" (backlog as of period end; book-to-bill; headcount; revenue by contract type).',
    'is_rev': REL + 'consolidated statements of operations, as originally reported (USD thousands to Q3 FY2025, USD millions from Q4 FY2025).',
    'd_acqam': REL + 'Exhibit 4 "Adjusted Net Income" reconciliation (amortization of intangible assets FY2012–17; significant acquisition amortization / acquisition amortization from FY2022).',
    'd_acq': REL + 'Exhibit 4 adjusted EBITDA reconciliation; per-period company labels in the cell comments.',
    'o_pub': REL + 'Exhibit 4 "Adjusted Operating Income" reconciliation (published FY2012 – Q3 FY2025).',
    'r_ebitda_pub': REL + 'Exhibit 4 "EBITDA, Adjusted EBITDA, Adjusted EBITDA Margin on Revenue" reconciliation.',
    'e_pubni': REL + 'Exhibit 4 "Adjusted Net Income" and "Adjusted Diluted Earnings Per Share".',
    'cf_ni': (REL + 'consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). Quarterly deferred taxes from the 10-Q '
              '(XBRL DeferredIncomeTaxExpenseBenefit, as first filed).'),
    'bs_cash': REL + 'consolidated balance sheets (period ends); Class A shares outstanding from XBRL (CommonStockSharesOutstanding, FY2017+).',
    'ppa_cons': 'Source: Q1 FY27 10-Q Note 5 (Defy Security, provisional); Ultra (2027E) assumed pending the Q2 FY27 10-Q.',
    'sh_basic': ('Source: XBRL company facts (WeightedAverageNumberOfSharesOutstandingBasic / Diluted, as first filed); Q4 diluted shares from the release non-GAAP '
                 'exhibit; Q4 basic = 4 × FY − (Q1+Q2+Q3).'),
    'eps_alloc': 'Source: XBRL UndistributedEarningsDiluted ("earnings for diluted computations", as first filed; Q4 = FY − 9M).',
    'ds_total': 'Source: release balance sheets; Q1 FY27 10-Q Note 8 (Debt); 8-K 4-Aug-2026 and 424B2 30-Jul-2026 (new notes, use of proceeds).',
}
CELL_COMMENTS = {}
def comments_setup():
    CELL_COMMENTS['ns'] = {A[2017]: 'FY2017 revenue by customer from the FY2019 10-K (ASC 606 recast: total $5,809.5m vs $5,804.3m as originally reported).',
                           A[2018]: 'FY2018 revenue by customer from the FY2019 10-K (ASC 606 recast: total $6,167.6m vs $6,171.9m as originally reported).',
                           QC[(2027, 1)].c: 'Q1 FY27: National Security reported as one customer type (Defense + Intelligence).'}
    CELL_COMMENTS['is_int'] = {QC[(2025, 4)].c: 'Q4 FY25: interest expense, net (interest income netted, previously in other income). The FY2025 annual column is on the new basis; Q1–Q3 FY25 on the old.'}
    CELL_COMMENTS['is_rev'] = {QC[(2025, 2)].c: 'Q2 FY25 revenue includes the $113m reduction to the provision for claimed costs (adjusted out of adjusted EBITDA).'}
    CELL_COMMENTS['is_tax'] = {QC[(2026, 1)].c: 'Q1 FY26: $86m release of tax reserves (IRS agreement); the adjusted net income bridge removes it inside the tax-effect line.'}
    CELL_COMMENTS['ul_run'] = {ANN[2027].c: 'ASSUMPTION: Ultra revenue is not disclosed. $180m ≈ $720m ÷ 4.0x EV / sales (defense software / edge-compute products). Replace with the Q2 FY27 10-Q.'}
    CELL_COMMENTS['ul_intp'] = {ANN[2027].c: 'ASSUMPTION: Defy Security intangibles were 37% of consideration (Q1 FY27 10-Q). Product businesses carry more technology intangibles.'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2012–15: adds back Carlyle-acquisition stock-based compensation and intangible amortization, transaction expenses, restructuring (FY2012)', None),
        A[2016]: ('FY2016–17: Carlyle intangible amortization and transaction expenses (option expense fully vested)', None),
        A[2018]: ('FY2018–21: transaction / acquisition costs and COVID-19 benefits only (Carlyle amortization ended FY2017)', None),
        q(2022, 1): ('FY2022+: acquisition & divestiture costs, financing transaction costs, significant acquisition amortization, restructuring, legal matters', None),
        q(2025, 4): ('Q4 FY25+: adjusted operating income no longer published — model continuation (operating income + EBITDA items + acquisition amortization)', None),
    }
    DEFS['r_def'] = {
        'C': ('Adjusted EBITDA = EBITDA + Carlyle option expense, transaction expenses, restructuring (FY2012–15)', None),
        A[2018]: ('FY2018–21: transaction / acquisition costs, COVID-19 benefits', None),
        q(2022, 1): ('FY2022+: acquisition & divestiture costs, financing transaction costs, restructuring, legal matter reserve (FY2023–24), claimed-costs provision, DC tax, insurance recoveries', None),
        q(2026, 1): ('FY2026+: "other corporate expenses" (severance, divestiture and acquisition costs); EBITDA from net income before interest expense, net and other income (expense)', None),
    }
    DEFS['e_def'] = {
        'C': ('Adjusted EPS = adjusted net income ÷ diluted shares (no two-class adjustment); tax effect at an assumed marginal rate of 40%', None),
        A[2018]: ('FY2018: 40% to Q2, 36.5% from Q3 FY2018 (2017 Tax Act blended rate); deferred-tax remeasurement adjusted out', None),
        A[2019]: ('FY2019+: tax effect at an assumed 26% (blended federal and state); discrete tax items (reserve releases, R&D credits, deferred-tax remeasurement) adjusted out', None),
        q(2022, 1): ('FY2022+: significant acquisition amortization added back; gains on investments / divestitures removed', None),
        q(2026, 1): ('FY2026: "acquisition amortization"; FY2026 tax effect includes the IRS agreement ($86m reserve release + $20m interest, net)', None),
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
                ws[f'{col}{r}'] = v; ws[f'{col}{r}'].number_format = NF['x']; set_color(ws[f'{col}{r}'], BLUE)
            ws[f'{SNOTE}{r}'] = note
        elif kind == 'blk':
            _, _, lab, db, mid, de, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBULL}{r}'] = db; ws[f'{SBASE}{r}'] = mid; ws[f'{SBEAR}{r}'] = de; ws[f'{SNOTE}{r}'] = note
            for col in (SBULL, SBEAR):
                ws[f'{col}{r}'].number_format = '\\+#,##0;\\-#,##0' if nf == 'm' else ('\\+0.00\\x;\\-0.00\\x' if nf == 'x2' else '\\+0.0%;\\-0.0%')
                set_color(ws[f'{col}{r}'], BLUE)
        elif kind == 'yr':
            _, _, lab, hdr, base, clamp, _, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBASE}{r}'] = base; set_color(ws[f'{SBASE}{r}'], BLUE)
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY27 revenue and adjusted EBITDA guidance end-points (high / mid / low), Q2–Q4/27E '
            'buybacks, 2028E–2031E customer-type growth, Ultra growth and margin, legacy adjusted EBITDA margin, book-to-bill, M&A spend and the leverage target for '
            f'2028E+ buybacks (scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Booz Allen Hamilton Holding Corporation (NYSE: BAH) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 31 March (2027 = Apr-2026 – Mar-2027) · '
                'Source: Booz Allen Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1), deal and financing 8-Ks and the Jul-2026 424B2, SEC EDGAR (CIK 1443646); '
                'XBRL company facts; investor-relations releases are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported in each period\'s release; one reportable segment (revenue by customer type: Defense / Intelligence / Civil / Global '
                'Commercial to FY2026, National Security / Civil & Commercial from Q1 FY2027); USD thousands to Q3 FY2025, millions from Q4 FY2025. Acquisitions: Liberty Jun-21, '
                'EverWatch Oct-22, PGSC FY25, Defy Apr-26, Ultra Mission Solutions 24-Aug-26 ($720m). Q2–Q4/27E calibrated to FY27 revenue and adjusted EBITDA guidance '
                '(22-May-2026, reiterated 24-Jul-2026; assumed to exclude Ultra).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '14Y CAGR'], ["26-'31", "21-'26", "16-'26", "12-'26"]):
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
        p = os.path.join(BASE, f'BAH_{scen}.xlsx')
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
    viewer; fullCalcOnLoad stays set so Excel recalculates on open (WWD / LECO / ESAB finishing step)."""
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
    p = os.path.join(BASE, 'BAH_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
