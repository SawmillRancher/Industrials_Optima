"""Build JHX_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'JHX_Model.xlsx')
G27 = MAN['guidance_fy27']
AZ = MAN['azek_ppa']; AM = MAN['amort_schedule']; DEBT = MAN['debt']; EU = MAN['europe_divestiture']; AICF = MAN['aicf']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2026']['x']
    rev, cogs = q['rev'], q['cogs']
    return {'dso': round(q['bs_ar'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365), 'dpo': round(q['bs_ap'] / cogs * 365), 'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at fiscal-year-end (31-Mar-2026) levels on FY2026 net sales / cost of goods sold (DSO {WC["dso"]}d, inventory {WC["dio"]}d, '
              f'payables & accrued {WC["dpo"]}d, other current liabilities {WC["ocl"]:.1%} of net sales); year ends are compared with year ends (Q2 is seasonally high in receivables).')
def mid(lohi): return round((lohi[0] + lohi[1]) / 2, 1)
def hml(lohi): return (lohi[1], mid(lohi), lohi[0])

V0 = {
    'out_hdr': 'FY27 planning assumptions — Q2 FY27 release (5-Nov-2026; continuing operations, ex share-based compensation)',
    'out_note': ('Q3 FY27 and full-year FY27 ranges for net sales and Adjusted EBITDA by segment (Siding & Trim, Deck, Rail & Accessories; total). Free cash flow > US$650m; '
                 'capex 6–7% of net sales; net leverage < 2.0x by the end of Q2 FY28. Q3/27E = Q3 range end-point, Q4/27E = FY range end-point − Q1–Q3.'),
    'outlook': [
        ('q3_tot', '  Q3 FY27 net sales — total ($m)', hml(G27['q3_sales']['tot']), 'm1', 'Guided US$1,058–1,140m. Drives Q3/27E net sales (ANZ = total − S&T − DR&A).'),
        ('q3_st', '  Q3 FY27 net sales — Siding & Trim ($m)', hml(G27['q3_sales']['st']), 'm1', 'Guided US$758–800m.'),
        ('q3_dra', '  Q3 FY27 net sales — Deck, Rail & Accessories ($m)', hml(G27['q3_sales']['dra']), 'm1', 'Guided US$164–190m (seasonally low quarter).'),
        ('q3e_tot', '  Q3 FY27 Adjusted EBITDA — total ($m)', hml(G27['q3_ebitda']['tot']), 'm1', 'Guided US$298–320m. Corporate = total − segments.'),
        ('q3e_st', '  Q3 FY27 Adjusted EBITDA — Siding & Trim ($m)', hml(G27['q3_ebitda']['st']), 'm1', 'Guided US$245–262m.'),
        ('q3e_dra', '  Q3 FY27 Adjusted EBITDA — DR&A ($m)', hml(G27['q3_ebitda']['dra']), 'm1', 'Guided US$38–49m.'),
        ('fy_tot', '  FY27 net sales — total ($m)', hml(G27['fy_sales']['tot']), 'm1', 'Guided US$4,990–5,133m (reaffirmed 5-Nov-2026). Drives Q4/27E = FY − Q1–Q3.'),
        ('fy_st', '  FY27 net sales — Siding & Trim ($m)', hml(G27['fy_sales']['st']), 'm1', 'Guided US$3,236–3,314m.'),
        ('fy_dra', '  FY27 net sales — DR&A ($m)', hml(G27['fy_sales']['dra']), 'm1', 'Guided US$1,198–1,240m.'),
        ('fye_tot', '  FY27 Adjusted EBITDA — total ($m)', hml(G27['fy_ebitda']['tot']), 'm1', 'Guided US$1,446–1,534m.'),
        ('fye_st', '  FY27 Adjusted EBITDA — Siding & Trim ($m)', hml(G27['fy_ebitda']['st']), 'm1', 'Guided US$1,046–1,085m.'),
        ('fye_dra', '  FY27 Adjusted EBITDA — DR&A ($m)', hml(G27['fy_ebitda']['dra']), 'm1', 'Guided US$355–375m.'),
        ('bb27', '  Q3–Q4/27E share repurchases ($m)', (100.0, 0.0, 0.0), 'm', 'US$250m authorization to 20-Aug-2027, none executed to 30-Sep-2026; Base / Bear: deleveraging first (net leverage < 2.0x target).'),
    ],
    'points': [
        ('pt_int', '  Interest, net ($m; FY27)', 230.0, 'm1', 'Not guided; H1 FY27 US$116.1m (US$4.0bn debt at a 5.7% weighted rate less interest income); 2028E+ from the debt schedule.'),
        ('pt_etr', '  Tax rate (GAAP; FY27)', 0.34, 'pct', 'H1 FY27 GAAP effective tax rate 33.9% (non-deductible AZEK items); 2028E+ inputs on the tax-rate row.'),
        ('pt_aetr', '  Adjusted effective tax rate (FY27)', 0.218, 'pct', 'H1 FY27 adjusted effective tax rate 21.8% (company: 21.7% Q1, 21.8% Q2).'),
        ('pt_amort', '  Amortization of AZEK intangibles ($m; FY27)', 310.0, 'm1', 'H1 FY27 US$155.1m (US$77.5m a quarter); 10-K schedule FY27 US$315.4m incl. legacy / Europe intangibles.'),
        ('pt_capex_pct', '  Capex % of net sales (FY27)', mid(G27['capex_pct']), 'pct', 'Planning assumption 6–7% of net sales (H1 FY27 US$158.3m = 5.8%).'),
        ('pt_fcf', '  Free cash flow planning assumption ($m; FY27) — memo', G27['fcf'], 'm1', 'Raised to > US$650m on 5-Nov-2026 (H1 FY27 US$535.4m); information row.'),
        ('pt_claims', '  Asbestos claims & handling costs paid ($m; FY27)', 130.0, 'm1', 'H1 FY27 US$65.2m; FY26 US$107.0m; FY25 US$114.4m (A$-denominated, actuarial central estimate).'),
        ('pt_contrib', '  AFFA contribution to AICF ($m; FY27)', AICF['contribution_fy27_est_usd_mar26_rate'], 'm1', 'A$128.2m for FY27 (≈US$93m at the 31-Mar-2026 rate); US$22.2m paid in H1 FY27.'),
        ('pt_disc', '  Europe discontinued operations — net income per quarter until closing ($m)', 10.0, 'm1', 'Q1 FY27 US$13.7m (recast), Q2 FY27 US$1.2m after €-fibre-cement closure costs (US$13.1m booked in H1); assumption.'),
        ('pt_close', '  Europe sale — closing fiscal year (2028 = Q1 FY28; 2027 = inside Q4 FY27)', 2028, 'gen', 'Company: closing expected in the first half of calendar 2027 (model: Q1 FY28). Set 2027 to test an earlier close.'),
        ('pt_proceeds', '  Europe sale proceeds ($m)', EU['proceeds_usd_announced'], 'm1', '€840m enterprise value (≈US$980m at the 20-Aug-2026 announcement rate; unhedged in the model); ~US$600m earmarked for debt repayment.'),
    ],
    'lev': (2.0, 1.75, 1.5),
    'lev_note': ('Net debt US$3.7bn at 30-Sep-2026 ≈ 2.4x LTM Adjusted EBITDA (model definition; company pro forma ~2.3x). Company target < 2.0x by the end of Q2 FY28. '
                 'Target = leverage up to which surplus cash is returned via buybacks (2028E+); below it free cash flow prepays the term loans. Bull = more buybacks (higher target).'),
    'blocks': [
        ('ST_G', 'ST_G (Siding & Trim net sales y/y)', 0.03, -0.04, [0.06, 0.06, 0.055, 0.05],
         'US repair & remodel + new construction recovery, material conversion (fiber cement vs vinyl / wood), ColorPlus and Exteriors mix, price. FY26 NA fiber cement +3.5%; FY27E +10% incl. AZEK Exteriors.', 'pct', False),
        ('DRA_G', 'DRA_G (Deck, Rail & Accessories net sales y/y)', 0.03, -0.05, [0.08, 0.07, 0.06, 0.06],
         'TimberTech composite share gains vs wood (sell-through up mid-single digits), channel and shelf-space expansion, new products. FY27E ~US$1.22bn (planning assumption).', 'pct', False),
        ('ANZ_G', 'ANZ_G (Australia & New Zealand net sales y/y, US$)', 0.02, -0.03, [0.04, 0.04, 0.04, 0.04],
         'Australian housing cycle, price, A$/US$. FY26 +0.1% (Philippines exit), H1 FY27 +11%.', 'pct', False),
        ('ST_M', 'ST_M (Siding & Trim Adjusted EBITDA margin)', 0.01, -0.02, [0.335, 0.34, 0.345, 0.35],
         'FY26 32.1% (post-AZEK Exteriors mix), H1 FY27 34.0%, FY27E ~32.5% (planning assumption mid-point); HOS savings, Fontana / Summerville closures (~US$25m), price vs input costs.', 'pct', False),
        ('DRA_M', 'DRA_M (Deck, Rail & Accessories Adjusted EBITDA margin)', 0.01, -0.02, [0.305, 0.315, 0.325, 0.33],
         'FY27E ~30% (US$355–375m on US$1.2bn); AZEK cost synergies (US$125m target, ahead of plan), recycling and Boise plant absorption.', 'pct', False),
        ('ANZ_M', 'ANZ_M (Australia & New Zealand Adjusted EBITDA margin)', 0.01, -0.015, [0.33, 0.33, 0.33, 0.33],
         'FY26 34.1%, H1 FY27 35.1% (R&D now allocated to the segment).', 'pct', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 100.0, -100.0, [100.0, 100.0, 100.0, 100.0],
         'No bolt-on programme guided; capital priorities are organic investment, deleveraging and buybacks. Base US$100m p.a. of bolt-ons from 2028E (assumption).', 'm', True),
    ],
    'corp_pct': -0.027, 'corp_pct_note': 'FY27E corporate Adjusted EBITDA ≈ −US$140m (H1 FY27 −US$66.5m) ≈ −2.7% of net sales; held at that ratio.',
    'corp_dna': 4.0,
    'seg_dna_pct': {'st': 0.056, 'dra': 0.062, 'anz': 0.045},
    'amort_sched': {int(y): AM[y] - 5.0 for y in ('2028', '2029', '2030', '2031')},
    'amort_note': ('FY2026 10-K Note 7 estimated amortization: FY28 US$332.2m, FY29 US$345.5m, FY30 US$332.5m, FY31 US$295.2m; less ~US$5m p.a. of legacy / Europe intangible amortization '
                   '(Europe intangibles held for sale). Trade names (5–15 years) roll off from FY31.'),
    'sga_pct': {2028: 0.195, 2029: 0.192, 2030: 0.19, 2031: 0.188}, 'rd_pct': 0.011, 'sbc_pct': 0.011,
    'etr': {2028: 0.30, 2029: 0.28, 2030: 0.27, 2031: 0.26},
    'etr_note': 'H1 FY27 GAAP 33.9% (non-deductible AZEK amortization / integration costs; Irish parent, US ~75% of sales); trending to the adjusted rate as the one-offs fade (assumption).',
    'aetr': 0.22, 'aetr_note': 'Company adjusted effective tax rate: FY25 23.5%, FY26 20.2%, H1 FY27 21.8%.',
    'qe_restr': {3: 3.0, 4: 3.0}, 'ae_restr': {2028: 10.0, 2029: 5.0, 2030: 0.0, 2031: 0.0},
    'restr_note': 'H1 FY27 US$6.0m (Fontana, CA and Summerville, SC closures); FY26 US$16.2m; FY25 US$50.3m (Philippines). European fibre-cement closure costs sit in discontinued operations. Assumption.',
    'qe_acq': {3: 10.0, 4: 10.0}, 'ae_acq': {2028: 15.0, 2029: 5.0, 2030: 0.0, 2031: 0.0},
    'acq_note': 'AZEK integration and Europe divestiture costs: FY26 US$206.9m (incl. deal costs), H1 FY27 US$31.5m. Assumption: US$10m a quarter in H2 FY27, tapering to nil by 2030E.',
    'capex_pct': {2028: 0.065, 2029: 0.06, 2030: 0.06, 2031: 0.06},
    'def_rate': 0.20, 'eq_h2': 5.0, 'eq_ae': 10.0, 'iss_e26': 0.4, 'iss_ae': 0.8, 'dil': 4.5,
    'claims': {2028: 135.0, 2029: 140.0, 2030: 145.0, 2031: 150.0},
    'claims_note': 'Q3–Q4/27E = FY27 point estimate less H1. 2028E+ inputs (~3–4% p.a. growth in A$ claims; assumption).',
    'as_yield': 0.04,
    'wc': WC,
    'notes_sep26': DEBT['notes_2031']['principal'] + DEBT['notes_2032']['principal'] + DEBT['unamortized_costs_sep26'],
    'tla_sep26': DEBT['tla1']['balance_sep26'] + DEBT['tla2']['balance_sep26'],
    'tla_sched': {2027: 27.4, 2028: 54.7, 2029: 704.7, 2030: 54.7, 2031: 54.7},
    'mat': {2027: 54.7, 2028: 704.7, 2029: 54.7, 2030: 54.7, 2031: 54.7},
    'refi': {2028: 0.0, 2029: 650.0, 2030: 0.0, 2031: 700.0}, 'nrep': {2028: 0.0, 2029: 0.0, 2030: 0.0, 2031: 700.0},
    'min_cash': 350.0, 'prepay_27': 0.0,
    'r_notes': {2028: 0.06, 2029: 0.06, 2030: 0.06, 2031: 0.06}, 'r_tla': 0.055, 'r_rev': 0.055, 'fees': 8.0,
    'debt_note': ('30-Sep-2026 (10-Q Note 8): 5.875% senior notes due 2031 US$700m, 6.125% senior notes due 2032 US$1,000m, Term Loan A-1 US$650m (due 2028), Term Loan A-2 US$1,695.3m '
                  '(due 2030; US$54.7m current), US$1.0bn revolver undrawn, unamortized costs −US$28.0m: total US$4,017.3m; weighted-average rate 5.7%. 5.000% 2028 notes (US$400m) redeemed 25-Jun-2026.'),
    'px': MAN['share_price']['value'],
    'px_note': 'VALUATION — share price input US$30.45 (NYSE: JHX; Form 4 open-market sale of 25-Aug-2026, filed 27-Aug-2026 — latest EDGAR-filed price); update to market',
    'mna_note': 'Scenario lever M&A_spend (Base US$100m p.a. of bolt-ons from 2028E). Funded from cash / revolver (debt schedule).',
    'dps_note': 'Semi-annual dividends FY2008–FY2022 (fiscal-year totals; FY2006–12 per the 20-F selected data: paid; FY2013–22: declared); none since FY2023 (buybacks FY2023–25; AZEK deleveraging FY2026–27). Forecast nil (input).',
}
PPA = {'Q2-26': {'cons': AZ['consideration'], 'cash': AZ['cash'], 'ar': AZ['ar'], 'inv': AZ['inventories'], 'prepaid': AZ['prepaid'], 'ppe': AZ['ppe'], 'intang': AZ['intangibles'],
                 'gw': AZ['goodwill'], 'onca': AZ['other_nca'], 'ap': AZ['ap'], 'ocl': AZ['other_cl'], 'dtl': AZ['dtl'], 'oncl': AZ['other_ncl'],
                 'names': 'The AZEK Company Inc. (1-Jul-2025)'}}
MANP = {'azek': 'azek_memo', 'misc': 'misc'}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw; path = kw.get('data')
    if not path: return None
    if kw.get('ppa'):
        v = PPA.get(pkey(col), {}).get(path.split('_', 1)[1])
        return v if kw.get('textdata') else num(v)
    if path.startswith('man:'):
        _, grp, key = path.split(':')
        return num(MAN[MANP[grp]].get(pkey(col) or '', {}).get(key))
    v = xget(pkey(col), path)
    if v is None and kw.get('bs') and col.kind == 'Q' and col.q == 4: v = xget(str(col.year), path)     # Q4 balance = fiscal-year-end balance
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
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r},{Q2}{row.r},{Q3}{row.r},{Q4}{row.r})', False
        if kw.get('flow') and (any(x in kw for x in ('qe', 'qe_in')) or getattr(row, 'has_qe', False)): return S27(row.key), False     # flows: FY2027E = Σ quarters
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'st_rev', 'dra_rev', 'anz_rev', 'eu_rev', 'st_oi', 'dra_oi', 'anz_oi', 'st_adj', 'dra_adj', 'anz_adj', 'g_adj', 'r_adj', 'r_ebita', 'r_ebit', 'o_adj',
          'is_op', 'is_gp', 'is_sga', 'is_nic', 'e_adjni', 'e_eps', 'eps_dilc', 'cf_cfo', 'fcf', 'bs_ta', 'bs_eq', 'sh_dil', 'd_dna', 'd_dep', 'd_amort', 'st_vol', 'as_liab', 'as_claims'}
CAGR_A = {'st_oim', 'dra_oim', 'anz_oim', 'st_adjm', 'dra_adjm', 'anz_adjm', 'eu_adjm', 'g_adjm', 'r_adj_m', 'o_adj_m', 'r_ebit_m', 'is_gm', 'is_opm', 'is_etr', 'e_rate', 'gm_rev', 'gm_st',
          'gm_gm', 'gm_ebitda_m', 'gm_adjebit_m', 'gm_op_m', 'gm_net_m', 'gm_sga', 'gm_rd', 'fcf_m', 'fcf_conv', 'fcf_eb', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'lv_asb',
          'd_sga', 'd_rd', 'd_dep_pct', 'd_sbc_pct', 'wc_nwc_p', 'corp_pct', 'st_dna_pct', 'dra_dna_pct', 'anz_dna_pct'}
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
        if col.kind == 'QE': row.has_qe = True
        cell = ws[f'{col.c}{r}']
        cell.value = v
        if not row.kw.get('textdata'): cell.number_format = nf
        if inp:
            set_color(cell, BLUE, bold=True if col.kind in FCK else None)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
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

SRC = 'Source: James Hardie results packages filed on SEC EDGAR (Form 6-K exhibits to Q3 FY26: Management\'s Analysis of Results, media release, financial statements; Form 8-K Ex. 99.1 earnings releases and Forms 10-K / 10-Q from Q4 FY26) — '
LABEL_SOURCES = {
    'st_rev': SRC + ('segment net sales as originally reported: "USA Fibre Cement" FY2006–08, "USA and Europe Fibre Cement" FY2009–16, "North America Fiber Cement" FY2017–Q1 FY26, "Siding & Trim" from Q2 FY26 '
                     '(incl. AZEK Exteriors from 1-Jul-2025). Q1 FY27 from the Q2 FY27 release six-month columns less Q2.'),
    'st_oi': SRC + 'segment EBIT tables (FY2006–08 fiscal-year tables, 20-F); "operating income" in the FY26+ releases. Q4 FY21–FY24 = fiscal year − 9 months (Q4 packages show fiscal-year tables only).',
    'st_adj': SRC + 'segment EBITDA / Adjusted EBITDA reconciliations (from FY2024; FY2024 segment EBITDA = EBIT + D&A).',
    'anz_rev': SRC + '"Asia Pacific Fibre Cement" FY2006–Q1 FY26 (International Fiber Cement FY2017–18 in the legacy memo), "Australia & New Zealand" from Q2 FY26.',
    'eu_rev': SRC + '"Europe Building Products" FY2019–Q4 FY26 (as originally reported; Fermacell acquired 3-Apr-2018). Discontinued operations from Q1 FY27 (Q2 FY27 release recast).',
    'corp': SRC + 'General Corporate row of the segment EBIT tables (ex asbestos adjustments; FY2015–16 "General Corporate excluding asbestos"); FY2024 from the 20-F segment note plus asbestos and the greenfield impairment.',
    'is_rev': ('Source: consolidated statements of operations in the results packages (FY2006–08: 20-F / results releases, 6-K; FY2009–Q3 FY26: 6-K financial-statement exhibits; Q4 FY26 onward: 10-K / 10-Q and 8-K Ex. 99.1). '
               'Q4 FY21–FY24: fiscal year − 9 months (the Q4 packages carry fiscal-year statements only). Q1 FY27: Q2 FY27 release six months − Q2 (continuing operations).'),
    'd_dna': 'Source: cash-flow statements (year to date as filed; discrete quarters derived). FY2006–08 from the 20-F cash-flow statements.',
    'r_pub': SRC + 'Adjusted EBITDA (company definition from FY2024; FY2023 as restated in the Q4 FY24 media release).',
    'r_pub_ex': SRC + '"Adjusted EBITDA excluding Asbestos" (FY2017–FY2020 Management\'s Analysis of Results).',
    'o_pub': SRC + '"EBIT excluding asbestos …" (FY2006–13) / "Adjusted EBIT" (FY2014–FY2025) reconciliation tables; FY2024–25 fiscal-year figures from the Q4 media release / earnings release.',
    'e_pub': SRC + ('"Net operating profit excluding asbestos (, asset impairments and tax adjustments)" FY2006–08; "Adjusted net operating profit" FY2009–21; "Adjusted net income" from FY2022. '
                    'FY2024 / Q4 FY24 and FY2025 / Q4 FY25: headline figures (FY25 items from the Q4 FY26 release comparatives).'),
    'cf_ni': 'Source: cash-flow statements (year to date; discrete quarters derived, Q4 = FY − 9M). Claims and handling costs paid — asbestos and cash paid to AICF per the statements and supplemental disclosures.',
    'bs_cash': 'Source: condensed consolidated balance sheets (quarter ends; FY2006–12 year ends from the 20-F / results packages). Shares outstanding from the 10-K / 10-Q covers and XBRL (dei).',
    'ppa_cons': 'Source: FY2026 Form 10-K Note 2 (Business Combination), final purchase-price allocation.',
    'sh_basic': SRC + 'statements of operations (weighted-average shares; James Hardie Industries N.V. to Jun-2010, SE to Jan-2020, plc since).',
    'ds_total': 'Source: balance sheets (short-term + long-term debt); Q2 FY27 10-Q Note 8 (Debt).',
    'as_liab': 'Source: balance sheets (current + non-current asbestos liability) and the asbestos notes (FY2026 10-K Note 12; Q2 FY27 10-Q Note 9).',
}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('FY2006–09: no EBITDA measure published (model bridge: EBIT + D&A + asbestos adjustments + AICF SG&A + other items)', None),
        A[2010]: ('FY2010–20: company "EBITDA" / "Adjusted EBITDA" = EBIT + D&A (asbestos included); "Adjusted EBITDA excluding Asbestos" published FY2017–20', 'Checked on the FY2010–20 rows below; the model row adds back the asbestos and other items for comparability.'),
        A[2021]: ('FY2021–22: not published (model bridge, same items as the FY2024 definition)', None),
        A[2023]: ('FY2023 (as restated in the FY24 release) – FY2026: Adjusted EBITDA = net income + tax + interest + other + D&A + asbestos adjustments, AICF SG&A, restructuring, acquisition / step-up items', None),
        q(2027, 1): ('FY2027+: also excludes share-based compensation; continuing operations (Europe discontinued). FY26 comparatives recast in the FY27 releases (data keys *_rc; not used in the as-reported columns)',
                     'Q1 FY27 = six months (Q2 FY27 release, 5-Nov-2026) less Q2 FY27, so the FY27 build is on one basis.'),
    }
    DEFS['o_def'] = {
        'C': ('FY2006–08: "EBIT excluding asbestos" (FY2008: and asset impairments; SCI costs not excluded)', None),
        A[2009]: ('FY2009–13: "EBIT excluding asbestos, ASIC expenses and asset impairments" (+ AICF SG&A)', None),
        A[2014]: ('FY2014–20: "Adjusted EBIT" — asbestos adjustments, AICF SG&A, NZ weathertightness / product liability, non-recurring stamp duty, Fermacell acquisition costs, product line discontinuation, asset impairments',
                  'Q1–Q3 FY13 and FY18 as originally reported differ from the Q4 packages (reclassification of NZ product liability expenses and Fermacell acquisition costs): the sum-of-quarters differences are documented in the README.'),
        A[2021]: ('FY2021–25: Adjusted EBIT — asbestos adjustments, AICF SG&A, restructuring, merger / acquisition costs', None),
        A[2026]: ('FY2026+: not published (model continuation: EBIT + asbestos + AICF + restructuring + acquisition / divestiture + step-up + impairments)', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006–08: "Net operating profit excluding asbestos (, asset impairments and tax adjustments)" — published items after tax; model rebuilds pre-tax from the statement of operations with the tax row as the balance', None),
        A[2009]: ('FY2009–21: "Adjusted net operating profit" — asbestos adjustments, AICF SG&A and interest income, ASIC / NZ / stamp duty items, impairments, debt extinguishment, Fermacell costs, tax adjustments', None),
        A[2022]: ('FY2022–25: "Adjusted net income" (same items; restructuring, merger costs FY2025)', 'FY2024 and Q4 FY24: headline only (no itemised bridge in the media release) — the tax / other row carries the whole adjustment.'),
        q(2026, 2): ('FY2026: + inventory fair-value step-up, pre-close financing costs, amortization of AZEK intangible assets', None),
        q(2027, 1): ('FY2027+: + share-based compensation; continuing operations; Q1 FY27 = six months (Q2 FY27 release) − Q2', None),
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
            _, _, lab, hi, mid_, lo, note, nf = spec_
            ws[f'{SL}{r}'] = lab
            for col, v in zip([SBULL, SBASE, SBEAR], [hi, mid_, lo]):
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
            _, _, lab, db, mid_, de, note, nf = spec_
            ws[f'{SL}{r}'] = lab; ws[f'{SBULL}{r}'] = db; ws[f'{SBASE}{r}'] = mid_; ws[f'{SBEAR}{r}'] = de; ws[f'{SNOTE}{r}'] = note
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY27 planning-assumption end-points (high / mid / low: Q3 FY27 and FY27 net sales and Adjusted EBITDA by segment), '
            'Q3–Q4/27E buybacks, 2028E–2031E segment net sales growth, segment Adjusted EBITDA margins, M&A spend and the leverage target for 2028E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'James Hardie Industries plc (NYSE / ASX: JHX) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 31 March (2027 = Apr-2026 – Mar-2027) · '
                'Source: SEC EDGAR, CIK 1159152 (James Hardie Industries N.V. / SE / plc) — Forms 20-F and 6-K results packages to Q3 FY26, Forms 10-K / 10-Q and 8-K Ex. 99.1 earnings releases from Q4 FY26; '
                'investor-relations and ASX releases are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: FY2006–FY2026 as originally reported in each results package (Q4 FY21–FY24 quarters = FY − 9M); FY2027 continuing operations — Europe (fermacell sale to Holcim, announced 20-Aug-2026) discontinued '
                'from the Q2 FY27 release, Q1 FY27 recast from the six-month columns. Segments: Siding & Trim (North America Fiber Cement + AZEK Exteriors), Deck, Rail & Accessories (AZEK, from 1-Jul-2025), '
                'Australia & New Zealand (Asia Pacific), Europe (to FY26); legacy International (FY17–18), Other Businesses and R&D segments as memo. Q3–Q4/27E set to the FY27 planning assumptions.')
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
    defs_setup()
    write_header(ws)
    for row in fw.SPEC: write_row(ws, row)
    write_scen(ws)
    set_columns(ws)
    ws.freeze_panes = 'C8'
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
        p = os.path.join(BASE, f'JHX_{scen}.xlsx')
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

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv:
        res = recalc(OUT); print('recalc', res.get('status'), res.get('total_errors'))
        import other_sheets as osh
        osh.inject_charts(OUT)
