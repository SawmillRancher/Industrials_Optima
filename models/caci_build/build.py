"""Build CACI_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'CACI_Model.xlsx')
G = MAN['guidance_fy27']
AM = MAN['amort_sched']
fw.MAN['ppa'] = {'Q3-26': (lambda p: {'cons': p['cons'], 'ca': round(p['ar'] + p['oca'], 3), 'ppe': p['ppe'], 'intang': p['intang'], 'gw': p['gw'],
                                      'onca': round(p['rou'] + p['onca'], 3), 'cl': round(p['ap'] + p['accr'] + p['ocl'], 3),
                                      'ncl': round(p['def_tax'] + p['lease'], 3)})(MAN['arka']['ppa'])}

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2026']['x']
    return {'dso': round(q['bs_ar'] / q['rev'] * 365), 'oca': round(q['bs_oca'] / q['rev'], 3), 'dpo': round(q['bs_ap'] / q['direct'] * 365),
            'comp': round(q['bs_comp'] / q['rev'], 3), 'ocl': round(q['bs_ocl'] / q['rev'], 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at fiscal-year-end (30-Jun-2026) levels on FY2026 revenue / direct costs (DSO {WC["dso"]}d, prepaid & other {WC["oca"]:.1%}, payables {WC["dpo"]}d, '
              f'accrued compensation {WC["comp"]:.1%}, other accrued {WC["ocl"]:.1%} of revenue); year ends are compared with year ends. FY2026 revenue includes ARKA for under four months, '
              'so the ratios are slightly high on a pro forma basis.')
mid = lambda a: round((a[0] + a[1]) / 2, 2)
Q1A = DATA['Q1-27']['x']
V0 = {
    'out_hdr': 'FY27 guidance — Q1 FY27 release (21-Oct-2026)',
    'out_note': ('Revenue $10.70–10.90bn (raised from $10.65–10.85bn), adjusted net income $740–760m (from $735–755m), adjusted diluted EPS $33.18–34.08 on 22.3m shares, '
                 'free cash flow at least $900m (CFO $1,015m − capex $115m); reconciliation: net income $579–599m, intangible amortization $215m, tax effect $(54)m. Source: Form 8-K Ex. 99.1 (SEC EDGAR).'),
    'outlook': [
        ('out_rev', '  FY27 revenue ($m)', (G['revenue'][1], mid(G['revenue']), G['revenue'][0]), 'm', 'Guided $10,700–10,900m. Drives the Q2–Q4/27E organic-growth calibration.'),
        ('out_ani', '  FY27 adjusted net income ($m)', (G['adj_ni'][1], mid(G['adj_ni']), G['adj_ni'][0]), 'm', 'Guided $740–760m. Drives the Q2–Q4/27E EBITDA-margin calibration.'),
        ('out_eps', '  FY27 adjusted diluted EPS ($) — memo', (G['adj_eps'][1], mid(G['adj_eps']), G['adj_eps'][0]), 'ps', 'Guided $33.18–34.08 on 22.3m diluted shares (information row; compare the model).'),
        ('out_ni', '  FY27 GAAP net income ($m) — memo', (G['net_income'][1], mid(G['net_income']), G['net_income'][0]), 'm', 'Guidance reconciliation: $579–599m (information row).'),
        ('bb27', '  Q2–Q4/27E share repurchases ($m)', (150.0, 50.0, 0.0), 'm',
         'Assumption. $187.3m remained under the 2023 Repurchase Program at 30-Sep-2026 (10-Q); no open-market repurchases since the ARKA financing (Q1/27 $4.4m, plan-related).'),
    ],
    'points': [
        ('pt_int', '  Q2–Q4/27E interest expense and other, net ($m per quarter)', 71.0, 'm1', 'Not guided; Q1/27 $73.2m on ~$4.9bn of debt; term-loan amortization and revolver repayment from free cash flow.'),
        ('pt_amort', '  Q2–Q4/27E intangible amortization ($m per quarter)', round((G['intangible_amortization'] - Q1A['amort']) / 3, 3), 'm1',
         'FY27 guidance reconciliation $215m less Q1/27 $54.3m, ÷ 3 (10-K schedule: $216.6m).'),
        ('pt_dep', '  Q2–Q4/27E depreciation ($m per quarter; incl. within direct costs)', 27.5, 'm1', 'Q1/27 $27.0m ($81.3m D&A in the EBITDA reconciliation − $54.3m amortization).'),
        ('pt_etr', '  Q2–Q4/27E effective tax rate', 0.25, 'pct', 'Q1/27 25.2%; FY2026 23.9%. Guidance mid-point implies ~25% (net income $589m).'),
        ('pt_stat', '  Assumed statutory rate on the amortization add-back (company)', G['assumed_statutory_rate'], 'pct', 'Company: "assumed full year statutory tax rate of 25.3%" (Q1 FY27 release).'),
        ('pt_capex', '  FY27 capital expenditures ($m)', G['capex'], 'm1', 'Guided $115m (free-cash-flow reconciliation); Q1/27 $11.4m.'),
        ('pt_fcf', '  FY27 free cash flow guidance floor ($m) — memo', G['fcf_at_least'], 'm1', 'Guided "at least $900m" (information row).'),
        ('pt_sh', '  FY27 diluted weighted-average shares guidance (m) — memo', G['diluted_shares'], 'm1', 'Guided 22.3m; Q1/27 22.316m.'),
    ],
    'lev': (2.5, 2.0, 1.5),
    'lev_note': ('Assumption (no published leverage target on EDGAR). Net debt $4.56bn at 30-Sep-26 ≈ 3.7x FY2026 EBITDA after the $2.6bn ARKA acquisition (≈3.3x on 2027E). '
                 'Free cash flow repays the revolver until leverage reaches the target; cash beyond it is returned via buybacks. Bull = more buybacks (higher target).'),
    'blocks': [
        ('ORG', 'ORG (organic revenue growth y/y)', 0.02, -0.03, [0.065, 0.065, 0.06, 0.06],
         'FY2026 +7.2%, FY2025 +7.2%, FY2024 +13.7% (10-K); Q1/27 +2.1%. FY27 guidance implies ~+7% organic for Q2–Q4. Backlog $34.0bn (3.3x revenue), trailing book-to-bill ~1.1x; '
         'national-security technology demand vs budget / continuing-resolution risk. Assumption.', 'pct', False),
        ('EBITDA_M', 'EBITDA_M (EBITDA margin)', 0.005, -0.010, [0.132, 0.134, 0.136, 0.138],
         'FY2026 12.3%, FY2025 11.2%, FY2024 10.4%; Q1/27 13.3%; FY27 guidance implies ~13%. Mix shift to Technology (58.6% of Q1/27 revenue) and fixed-price work, ARKA accretive. Assumption.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 300.0, -300.0, [300.0, 300.0, 300.0, 300.0],
         'Acquisition spend: FY2026 $2.65bn (ARKA), FY2025 $1.68bn (Azure Summit, Applied Insight), FY2024 $0.11bn, FY2022 $0.62bn. Base $300m p.a. of bolt-ons while deleveraging (assumption).', 'm', True),
    ],
    'btb': 1.15,
    'dep_pct': {2028: 0.0105, 2029: 0.0105, 2030: 0.0105, 2031: 0.0105},
    'ind_pct': {2028: 0.222, 2029: 0.221, 2030: 0.220, 2031: 0.219},
    'sbc_pct': 0.0082, 'etr': 0.25,
    'capex_pct': {2028: 0.011, 2029: 0.011, 2030: 0.011, 2031: 0.011},
    'def_q': 15.0, 'def_ae': 40.0, 'eq_q': -11.0, 'eq_ae': -40.0,
    'amort_sched': {2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: AM['2031']},
    'amort_note': AM['source'] + ': FY27 $216.6m, FY28 $205.9m, FY29 $197.1m, FY30 $185.5m, FY31 $168.2m ($1,099.7m thereafter).',
    'repay': {2027: 35.063, 2028: 62.375, 2029: 78.0, 2030: 78.0, 2031: 78.0},
    'mat': {2027: 62.375, 2028: 78.0, 2029: 78.0, 2030: 78.0, 2031: 78.0},
    'repay_note': ('FY2026 10-K maturity schedule: FY27 $46.75m (Q2–Q4/27E = $46.75m − $11.7m paid in Q1), FY28 $62.4m, FY29 $78.0m, FY30 $78.0m. FY31: $1,706.75m falls due (Revolving Facility and Term Loan, Nov-2030) — '
                   'assumed refinanced on the same amortization ($78.0m shown; assumption). Term Loan B (Oct-2031), Term Loan B-2 and the 2033 Notes mature after the forecast.'),
    'min_cash': 200.0,
    'r_notes': {2028: 0.057, 2029: 0.057, 2030: 0.057, 2031: 0.057},
    'r_notes_note': ('30-Sep-2026 stated rates: Term Loan 5.40%, Term Loan B / B-2 5.65% (floating, SOFR + margin), 2033 Notes 6.375% fixed → ~5.8% weighted before swaps '
                     '($1.5bn of floating-to-fixed swaps at 1.7–3.8% paid fixed lower the cost). Input 5.7%.'),
    'fees': 12.0,
    'debt_note': MAN['debt']['facility'] + '. Source: ' + MAN['debt']['source'] + '.',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $625.00 (provided by the user on 20-Nov-2026; not an SEC-filed price; ~$14bn market cap) — update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $300m p.a. of bolt-on acquisitions from 2028E). Funded from cash / revolver (debt schedule).',
    'rev_guid_note': 'Company FY27 revenue guidance $10,700–10,900m (raised 21-Oct-2026 from $10,650–10,850m). Drives the organic-growth calibration.',
    'ani_guid_note': 'Company FY27 adjusted net income guidance $740–760m (raised 21-Oct-2026 from $735–755m). Drives the EBITDA-margin calibration.',
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
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r}:{Q4}{row.r})', False
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
CAGR_G = {'is_rev', 'g_rev', 'b_orgrev', 'c_dod', 'c_ic', 'c_fed', 'c_comm', 'k_bl', 'k_fund', 'k_awd', 'sg_dom', 'sg_int', 'g_adj', 'r_adj', 'r_ebit', 'is_oi',
          'is_dda', 'e_adjni', 'e_eps', 'e_cd_ni', 'e_cd_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_gp', 'is_ind', 'd_amort', 'd_dep', 'is_ni',
          'eps_dil', 'is_direct', 'k_emp', 'e_tech', 'e_exp', 't_ffp'}
CAGR_A = {'b_org_g', 'b_org_pub', 'b_m', 'g_adjm', 'r_adj_m', 'r_ebit_m', 'is_gm', 'is_oi_m', 'gm_rev', 'gm_org', 'gm_gm', 'gm_ind', 'gm_ebitda_m', 'gm_ebita_m',
          'gm_op_m', 'gm_net_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_ind', 'd_dep_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr',
          'fcf_eb', 's_dod', 's_ic', 's_fed', 's_comm', 'k_btb', 'k_cov', 'sg_int_p', 'mx_ffp', 'mx_tech', 'mx_prime', 'b_acq_p', 'wc_dso'}
A = {y: ANN[y].c for y in ANN}

def style_cagr(ws, r, on):
    src = 16 if on else 12
    for c in CAGR:
        ws[f'{c}{r}']._style = copy.copy(TM[f'{L(CI(c) + TSHIFT)}{src}']._style)

PYNOTE = {'e_pubni': 'adj_ni_pub', 'e_pub': 'adj_eps_pub', 'e_amort': 'a_intang', 'fcf_pub': 'f_fcf', 'fcf_marpa': 'f_marpa', 'e_tech': 'e_tech', 'e_exp': 'e_exp',
          'k_awd': 'awards', 'c_dod': 'cust', 'c_ic': 'cust', 'c_fed': 'cust', 'c_comm': 'cust'}
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
            if col.kind in HISTK:
                per = pkey(col); lk = row.kw.get('labkey')
                if lk and isinstance(v, (int, float)) and abs(v) > 1e-9:
                    t = xget(per, lk)
                    if t: comment(cell, f'Company items ({per}, USDm): {t}', 380, 110)
                elif PYNOTE.get(row.key) in (xget(per, '_py') or []):
                    comment(cell, f'{per}: as presented in the following year\'s release (prior-year comparative) — '
                            + ('customer types recast for the Intelligence Community split (first shown Q1 FY26).' if PYNOTE[row.key] == 'cust'
                               else 'the measure was first published after this period.'), 360, 80)
                elif row.key == 'b_acq' and xget(per, 'acq_rev') is None:
                    comment(cell, f'{per}: derived = revenue − prior-year revenue × (1 + published organic growth {xget(per, "org_pub"):.1%}). '
                            f'Quote: "…{(xget(per, "org_quote") or "")[-120:]}"', 420, 110)
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
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['x2'] if row.nf in ('x2', 'x') else NF['d'] if row.nf == 'd' else NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: CACI earnings releases (Form 8-K Item 2.02, Ex. 99 / 99.1, SEC EDGAR) — '
LABEL_SOURCES = {
    'b_acq': REL + '"Reconciliation of Total Revenue Growth and Organic Revenue Growth" (published FY2006–FY2013); later periods derived from the organic growth stated in the release / 10-K text.',
    'c_dod': REL + '"Revenues by Customer Type" schedule (three-month columns; fiscal years from the Q4 release). FY2025 on the current basis = comparatives in the FY2026 releases.',
    'cl_dod': REL + '"Revenue by Customer Type / Group", as originally reported. State and local government (separate to FY2013) is included in Commercial and other.',
    't_cpf': REL + 'revenue by contract type, prime / subcontractor and Expertise / Technology schedules, as originally reported.',
    'k_bl': REL + 'backlog as stated in the release text (rounded); contract awards / contract funding orders schedules.',
    'sg_dom': 'Source: CACI Forms 10-K / 10-Q, business-segment note (Domestic Operations, International Operations).',
    'is_rev': REL + 'condensed consolidated statements of operations, as originally reported (three-month columns; fiscal years from the Q4 release twelve-month column).',
    'd_amort': 'Source: Form 10-K intangible-assets note (annual); adjusted-net-income reconciliation in the releases (quarterly, from Q3 FY21); XBRL AmortizationOfIntangibleAssets as first filed.',
    'r_adj_pub': REL + '"Reconciliation of Net Income to EBITDA" (published from the Q3 FY08 release).',
    'e_pubni': REL + '"Reconciliation of Net Income to Adjusted Net Income and Diluted EPS to Adjusted Diluted EPS" (definitions per the definition row).',
    'cf_ni': REL + 'condensed consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M).',
    'bs_cash': REL + 'condensed consolidated balance sheets (period ends). Goodwill split from the 10-K / 10-Q where the release combines it with intangible assets.',
    'fcf_pub': REL + '"Reconciliation of Net Cash Provided by Operating Activities to … Excluding MARPA and to Free Cash Flow" (free cash flow from Q3 FY21; FY2020–21 from comparatives).',
    'ppa_cons': 'Source: FY2026 Form 10-K, Note 4 (ARKA Group L.P., acquired 9-Mar-2026; preliminary allocation, adjusted in the measurement period).',
    'sh_basic': REL + 'statements of operations (weighted-average shares). No stock splits in the period.',
    'ds_total': 'Source: release balance sheets; Q1 FY27 10-Q debt note; FY2026 10-K Note 11; 8-Ks of 9-Mar-2026 (Term Loan B-2) and 12-Mar-2026 (2033 Notes-2).',
    'bs_shares': 'Source: Forms 10-K / 10-Q balance sheets (XBRL shares issued less treasury shares, as first filed; available from FY2010).',
}
CELL_COMMENTS = {}
def comments_setup():
    q = lambda y, n: QC[(y, n)].c
    CELL_COMMENTS['cf_debt'] = {q(2022, 2): 'Q2 FY22: the release printed the borrowing and exchange-rate lines without amounts; borrowings derived from the financing subtotal, '
                                            'the exchange-rate effect from the net change in cash (year to date less Q1).',
                                q(2022, 3): 'Q3 FY22 = nine months less six months (six-month borrowings derived, see Q2 FY22).'}
    CELL_COMMENTS['is_ni_pub'] = {q(2016, 4): 'Q4 FY16 as shown in the Q4 FY16 release (three-month column). The release applied the early adoption of ASU 2016-09 to the full year: '
                                              'FY2016 net income $142.8m vs Σ quarters as first reported $141.8m.'}
    CELL_COMMENTS['k_bl'] = {A[2016]: 'FY2016: USD 11.0bn after a USD 2.5bn reduction from a review of backlog reporting definitions (release 17-Aug-2016).'}
    CELL_COMMENTS['e_pubni'] = {A[2014]: 'FY2014 as published in the Q4 FY14 release (USD 190.6m); Σ quarters as first published = USD 193.1m (Six3 Systems transaction-cost presentation in Q2 FY14).'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2006–07: no EBITDA published — model = net income + income taxes + interest and other, net + D&A', 'EBITDA was first published in the Q3 FY08 release (1-May-2008).'),
        A[2008]: ('FY2008+ (from Q3 FY08): EBITDA = net income + income taxes + net interest + depreciation and amortization', None),
        A[2011]: ('FY2011–12: "pro forma EBITDA" excludes earn-out adjustments', 'Q4 FY11 release (18-Aug-2011): earn-out adjustment (gain) removed; FY2010 comparative restated to $245.0m (originally $247.1m).'),
        q(2013, 1): ('FY2013: "adjusted EBITDA" excludes earn-out, product-sale and fixed-price contract adjustments', None),
        q(2014, 1): ('FY2014–Q1 FY16: EBITDA (no adjusting items)', None),
        q(2016, 2): ('Q2 FY16–FY2021: "adjusted EBITDA" excludes earn-out adjustments', None),
        q(2020, 1): ('FY2020+: D&A add-back includes depreciation within direct costs', 'Company wording: "depreciation and amortization expense, including depreciation within direct costs" (from the Q1 FY20 release).'),
        q(2022, 1): ('FY2022–Q3 FY23: labelled "adjusted EBITDA"; no adjusting items', None),
        q(2023, 4): ('Q4 FY23+: "EBITDA" (net income + net interest + income taxes + D&A incl. within direct costs)', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006–08: no adjusted net income published — adjusted = GAAP (flag)', None),
        A[2009]: ('FY2009–10: "cash net income" / "adjusted net income" = net income + stock-based compensation + D&A + financing-cost amortization + non-cash interest, net of tax',
                  'First published in the Q4 FY09 release (12-Aug-2009) as "cash net income"; renamed "adjusted net income" in the Q3 FY10 release.'),
        A[2011]: ('FY2011–Q2 FY18: adjusted net income also excludes earn-out adjustments ("pro forma" FY2011–12)', None),
        q(2017, 3): ('Q3 FY17–Q2 FY18: adjusted net income published without a per-share figure', None),
        q(2018, 3): ('Q3 FY18–Q2 FY20: no adjusted net income published — adjusted = GAAP (flag)', 'The releases showed tax-reform pro forma tables only.'),
        A[2018]: ('FY2018–19: no adjusted net income published for the year — adjusted = GAAP (flag)', None),
        q(2020, 3): ('Q3 FY20+: current definition — net income + intangible amortization − tax effect at the assumed statutory rate (first published Q3 FY21; earlier periods from comparatives)',
                     'Q3 FY21 release (21-Apr-2021): "Adjusted net income … GAAP net income … excluding intangible amortization expense and the related tax impact". Q3 FY20–Q2 FY21 and FY2020 are the prior-year comparatives of the FY2021–22 releases.'),
        A[2020]: ('FY2020+: current definition (FY2020 from the Q4 FY21 comparatives)', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY27 revenue and adjusted-net-income guidance end-points (high / mid / low), '
            'Q2–Q4/27E buybacks, 2028E–2031E organic revenue growth, EBITDA margin, M&A spend and the leverage target for 2028E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'CACI International Inc (NYSE: CACI) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 30 June (2027 = Jul-2026 – Jun-2027) · '
                'Source: CACI Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99 / 99.1) and deal / financing 8-Ks, SEC EDGAR (CIK 0000016058); XBRL company facts; '
                'investor-relations releases at caci.com are the same documents as filed on EDGAR. No guidance from outside EDGAR is used.')
    ws['B4'] = ('Basis notes: as originally reported (each period from its own release). Customer types on the Department of War / Intelligence Community / Federal civilian basis from FY2025 '
                '(FY2026 comparatives); legacy basis in memo rows. Measures first published with comparatives (adjusted net income Q3 FY20+, free cash flow FY2019+, Technology / Expertise FY2020, '
                'contract awards FY2018) use those comparatives (cell comments). Major acquisitions: Six3 Systems Nov-13, L-3 NSS Feb-16, Azure Summit and Applied Insight Oct-24, ARKA 9-Mar-26 ($2.6bn). '
                'Q2–Q4/27E calibrated to the FY27 revenue and adjusted-net-income guidance (21-Oct-2026).')
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
        p = os.path.join(BASE, f'CACI_{scen}.xlsx')
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
    p = os.path.join(BASE, 'CACI_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
