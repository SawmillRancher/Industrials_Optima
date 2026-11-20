"""Build TLN_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'TLN_Model.xlsx')
G26, G27 = MAN['guidance']['fy26'], MAN['guidance']['fy27']
CAPC = MAN['capacity']; ECR = CAPC['expected_capacity_revenues']; MON = CAPC['monetization']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['Q4-25']['x']
    rev = 4 * (q['en_rev'] + q['cap_rev'])
    return {'dso': round(q['bs_ar'] / rev * 365), 'inv': round(q['bs_inv'] / rev, 3), 'ap': round(q['bs_ap'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end (31-Dec-2025) levels on annualised Q4/25 energy and capacity revenues, the first quarter with Freedom and Guernsey '
              f'(DSO {WC["dso"]}d, inventory {WC["inv"]:.1%}, payables {WC["ap"]:.1%} of revenues); year ends are compared with year ends.')
Y5 = list(range(FYC + 1, FYL + 1))
def yd(vals): return dict(zip(Y5, vals))

V0 = {
    'out_hdr': 'Company guidance — Q3-26 release (3-Nov-2026)',
    'out_note': ('FY26 Adjusted EBITDA $2,050–2,200m and Adjusted FCF $1,225–1,325m (narrowed, mid-point reaffirmed); FY27 Adjusted EBITDA $2,500–2,850m and Adjusted FCF $1,500–1,750m '
                 '(introduced). Net leverage target 3.5x. All guidance is from the Form 8-K Ex. 99.1 filed on EDGAR.'),
    'outlook': [
        ('out_eb26', '  FY26 Adjusted EBITDA ($m)', tuple(G26['adj_ebitda']), 'm', 'Guided $2,050–2,200m. Drives the Q4/26E energy-margin calibration.'),
        ('out_eb27', '  FY27 Adjusted EBITDA ($m)', tuple(G27['adj_ebitda']), 'm', 'Guided $2,500–2,850m. Drives the 2027E energy-margin solve.'),
        ('out_fcf26', '  FY26 Adjusted Free Cash Flow ($m) — memo', tuple(G26['adj_fcf']), 'm', 'Guided $1,225–1,325m (information row; compare the model).'),
        ('out_fcf27', '  FY27 Adjusted Free Cash Flow ($m) — memo', tuple(G27['adj_fcf']), 'm', 'Guided $1,500–1,750m (information row).'),
    ],
    'points': [
        ('pt_cap', '  Q4/26E capacity revenues ($m)', float(ECR['2026_q4']), 'm1', 'Expected capacity revenues for 1-Oct to 31-Dec-2026 (Q3-26 10-Q Note 3, fixed-fee performance obligations).'),
        ('pt_opx', '  Q4/26E adjusted operating costs, net ($m)', -190.0, 'm1', 'Q3/26 −$180m with the full acquired fleet; fall maintenance outages in Q4 (assumption).'),
        ('pt_gax', '  Q4/26E G&A excluding stock compensation ($m)', 25.0, 'm1', 'Q3/26 $22m (G&A $76m less $54m of stock-based and long-term incentive compensation).'),
        ('pt_sbc', '  Q4/26E stock-based & long-term incentive compensation ($m)', 50.0, 'm1', 'Q3/26 $54m; nine months $127m (higher grant-date values of RSUs / PSUs).'),
        ('pt_acl', '  Q4/26E amortization of acquired contract liabilities ($m)', 25.0, 'm1', 'Nine months $79m (income-statement D&A $352m less $273m in the Adjusted EBITDA reconciliation); FY2025 10-K schedule $93m for 2026.'),
        ('pt_nfa', '  Q4/26E nuclear fuel amortization ($m)', 27.0, 'm1', 'FY26 guidance reconciliation $100m less nine months $73m.'),
        ('pt_dda', '  Q4/26E depreciation, amortization & accretion ($m)', 163.0, 'm1', 'FY26 guidance reconciliation $515m less nine months $352m (Q3 $157m).'),
        ('pt_dda27', '  FY27 depreciation, amortization & accretion ($m)', 650.0, 'm1', 'FY27 guidance reconciliation (full year of Cornerstone).'),
        ('pt_int', '  Q4/26E interest expense & other finance charges ($m)', 169.0, 'm1', 'Q3/26 $148m + ~$21m accretion of the capacity-monetization discount from 1-Oct-2026 (assumption). The FY26 guidance line ($460–480m) is below the nine-month figure of $481m, which carries $78m of one-off refinancing charges.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.259, 'pct', 'Nine months 2026: 25.9%.'),
        ('pt_fcapex', '  FY26 capital expenditures, net — Adjusted FCF definition ($m)', 330.0, 'm1', 'Guided $325–335m (nine months $200m).'),
        ('pt_fint', '  Q4/26E interest and finance charge payments ($m)', 167.0, 'm1', 'FY26 guidance mid-point $470m less nine months $303m.'),
        ('pt_ftax', '  FY26 income taxes paid — Adjusted FCF definition ($m)', 20.0, 'm1', 'Guided $15–25m (nine months: $5m net refund).'),
        ('pt_fpen', '  FY26 pension contributions ($m)', 30.0, 'm1', 'Guided $25–35m (nine months $23m).'),
        ('pt_nfuel', '  Q4/26E nuclear fuel expenditures ($m)', 25.0, 'm1', 'Nine months $101m; FY2025 $126m (assumption).'),
        ('pt_gcapex', '  Q4/26E growth, development & conversion capex ($m)', 60.0, 'm1', 'Outside the Adjusted FCF definition; nine months $249m (PP&E + nuclear fuel expenditures $449m less $200m). Assumption.'),
        ('pt_accint', '  Accrued interest at 31-Dec-2026 ($m)', 150.0, 'm1', '$169m at 30-Sep-2026 + Q4 cash-basis interest expense ($148m) − Q4 interest payments ($167m).'),
        ('pt_asr', '  Q4/26E accelerated share repurchase — cash paid 1-Oct-2026 ($m)', 1500.0, 'm', MAN['equity']['asr'] + '. Funded by the $1.3bn net capacity-monetization proceeds and cash.'),
        ('pt_asr_sh', '  ASR shares received and retired on 1-Oct-2026 (m)', MAN['equity']['asr_initial_shares'], 'm2', '3,811,460 shares = 80% of $1.5bn at $314.84 (Q3-26 10-Q Note 15).'),
        ('pt_bb', '  Q4/26E other share repurchases ($m)', 0.0, 'm', 'None assumed besides the ASR ($1.5bn left on the program to Dec-2028).'),
    ],
    'lev': (3.5, 3.5, 3.0),
    'lev_note': ('Company net leverage target: 3.5x net debt / Adjusted EBITDA (Q3-26 release). Applied to net debt excluding the deferred capacity obligation by default (switch in the leverage block; '
                 'assumption — the company does not define it). Surplus cash beyond the target is returned via buybacks; Bear = lower target (deleveraging first).'),
    'blocks': [
        ('GEN_G', 'GEN_G (generation y/y; 2027E vs the 2026E pro forma base)', 0.01, -0.01, [0.0, 0.01, 0.01, 0.005, 0.005],
         'Fleet ~15.5 GW after Cornerstone; Q3/26 capacity factor 75.4% (nine months 64.3%). Base: flat on the pro forma base, then modest growth as PJM load (data centres) lifts dispatch of the gas fleet.', 'pct', False),
        ('EM_G', 'EM_G (adjusted energy margin per MWh y/y; from 2028E — 2027E is solved to guidance)', 0.02, -0.03, [0.0, 0.04, 0.04, 0.03, 0.03],
         ('2027E margin per MWh is solved to the FY27 Adjusted EBITDA guidance (the 2027E entry is not used). 2028E+: AWS PPA ramp to 1,920 MW at premium prices, the nuclear PTC floor and '
          'tighter PJM spark spreads vs lower hedge cover (~35% of 2028 hedged at 30-Sep-2026). Bear: lower power prices / spark spreads.'), 'pct', False),
        ('CAP_PX', 'CAP_PX (PJM clearing price for capacity years from 2029/2030, $/MW-day)', 25.0, -75.0, [300.0, 300.0, 300.0, 300.0, 300.0],
         ('Cleared: 2025/26 $269.92, 2026/27 $329.17, 2027/28 $333.44, 2028/29 $325.00 (the last three at the temporary price cap). Base $300; Bull = cap-level pricing persists; '
          'Bear = new supply / market reform. Applies to the days after 31-May-2029 only.'), 'm', True),
        ('OPX_G', 'OPX_G (adjusted operating costs y/y; 2027E vs the 2026E pro forma run-rate)', -0.01, 0.01, [0.03, 0.03, 0.03, 0.03, 0.03],
         'Inflation-like growth on the pro forma cost base (O&M, G&A excluding stock compensation). Bull = lower cost growth.', 'pct', False),
    ],
    'gen_pf': 81.0,
    'gen_pf_note': ('Analyst estimate (assumption): Q3/26 23.9 TWh and Q4/26E ~20 TWh with the full fleet; Q1/26 15.6 and Q2/26 14.1 TWh plus ~3–4 TWh a quarter for the 2.6 GW Cornerstone '
                    'plants before the 15-Jun-2026 closing (≈65% capacity factor). Not company-disclosed.'),
    'cap_con': yd([float(ECR['2027']), float(ECR['2028']), float(ECR['2029']), float(ECR['2030']), 22.0]),
    'cap_con_note': ECR['src'] + '. 2027 $1,270m, 2028 $1,248m, 2029 $529m (auctions cleared to 31-May-2029 + contracts), 2030 $36m; 2031 $22m assumed ($109m "thereafter" through 2035).',
    'cap_mw': yd([0.0, 0.0, 10180.0, 10180.0, 10180.0]),
    'cap_mw_note': ('Assumption: the 10,180 MW cleared for 2028/2029 (8-K 14-Jul-2026) is held for later auctions (2026/27: 6,702 MW; 2027/28: 8,745 MW before Cornerstone). '
                    + CAPC['guernsey_sale'] + ' — bilateral sales are not modelled separately.'),
    'cap_days': yd([0.0, 0.0, 214.0, 365.0, 365.0]),
    'eb26_note': 'Company FY26 Adjusted EBITDA guidance $2,050–2,200m (3-Nov-2026; $1,750–2,050m before Cornerstone on 26-Feb-2026). Drives the Q4/26E calibration.',
    'eb27_note': 'Company FY27 Adjusted EBITDA guidance $2,500–2,850m (introduced 3-Nov-2026). The 2027E energy margin per MWh is solved to it.',
    'acl': yd([101.0, 120.0, 112.0, 113.0, 115.0]),
    'acl_note': (MAN['contracts']['fuel_contract_amort']['src'] + ': 2027 $101m, 2028 $102m, 2029 $83m, 2030 $84m; plus the acquired capacity-contract liability ('
                 + 'Q3-26 10-Q Note 17: 2028 $18m, 2029 $29m, 2030 $29m, 2031 $24m, booked in capacity revenues — shown here in one line, simplification); 2031 fuel-contract amortization $91m assumed.'),
    'sbc': yd([160.0, 168.0, 176.0, 185.0, 194.0]),
    'sbc_note': 'Nine months 2026 $127m (Q3 $54m). Q4/25 included a $501m charge on the change in accounting for existing awards. 2027E+ input (assumption).',
    'ndt_r': 0.05, 'etr': 0.25, 'adj_rate': 0.25,
    'nfa': yd([110.0, 112.0, 114.0, 117.0, 119.0]),
    'fcapex': yd([-370.0, -380.0, -390.0, -400.0, -410.0]),
    'ftax': yd([-60.0, -150.0, -250.0, -300.0, -330.0]),
    'ftax_note': ('Q4/26E = FY26 guidance mid-point ($20m) − nine months. 2027E $60m (guidance mid-point). 2028E+: input rising toward the book tax charge as tax attributes are used (assumption; '
                  'the company definition excludes taxes paid from the NDT and benefits of the nuclear PTC).'),
    'fpen': yd([-20.0, -20.0, -20.0, -20.0, -20.0]),
    'nfuel': yd([-130.0, -130.0, -135.0, -135.0, -140.0]),
    'gcapex': yd([120.0, 80.0, 50.0, 50.0, 50.0]),
    'gcapex_note': ('History = PP&E and nuclear fuel expenditures less capital expenditures, net of the Adjusted FCF reconciliation (development, growth and conversion capex the company excludes). '
                    'Not guided; 2027E+ input (assumption).'),
    'iss_ae': 0.3, 'dil': 0.4,
    'iss_notes': yd([0.0, 0.0, 0.0, 0.0, 2300.0]),
    'repay': {2026: 7.0, 2027: 29.0, 2028: 29.0, 2029: 29.0, 2030: 29.0, 2031: 2329.0},
    'mat': {2026: 29.0, 2027: 29.0, 2028: 29.0, 2029: 29.0, 2030: 2329.0, 2031: 29.0},
    'repay_note': ('Term loans amortize ~1% a year ($29m current portion). 2031E: $1.5bn 6.125% notes due 2031 and the TLB-2 (Dec-2031, ~$800m) repaid and refinanced. '
                   'TLB-1 Nov-2032, TLB-3 2032, notes 2033 / 2034 / 2036 mature after the forecast period.'),
    'min_cash': 350.0, 'ds_fixed': 6701.0,
    'min_cash_note': 'Cash and restricted cash $349m at 30-Sep-2026; $220m unrestricted and $1.4bn of revolver capacity at 30-Oct-2026 (Q3-26 release). Assumption.',
    'r_notes': 0.0612,
    'r_notes_note': ('Weighted rate on carrying value: term loans $2,868m at ~5.4%, unsecured notes $6,690m at ~6.33% (6.125% 2031, 6.375% 2033, 6.25% 2034, 6.50% 2036), PEDFA $131m at 5.25% '
                     '= ~$586m on $9,569m. FY27 guidance interest $585–615m.'),
    'fees': 15.0, 'fees_note': 'Letter-of-credit facility ($1.5bn LCF, $482m issued), commitment fees and amortization of deferred financing costs (assumption).',
    'dco_acc': {2026: 21.0, 2027: 80.0, 2028: 48.0, 2029: 8.0},
    'dco_rep': yd([float(MON['repay']['2027']), float(MON['repay']['2028']), float(MON['repay']['2029']), 0.0, 0.0]),
    'dco_note': 'The $157m discount is amortized to interest expense through May-2029 (10-Q). Allocation by year is a model assumption (≈6.4% effective rate on the outstanding balance): $21m Q4/26, $80m 2027, $48m 2028, $8m 2029.',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $354.52 (Form 4 open-market sale on 17-Nov-2026, filed 19-Nov-2026 — the latest share price in an SEC filing; ASR reference price '
                '$314.84 on 1-Oct-2026); update to market'),
}
V0['dco_acc'].update({2030: 0.0, 2031: 0.0})

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
CAGR_G = {'gen', 'em', 'cap', 'g_adj', 'r_adj', 'r_ebit', 'is_rev', 'is_en', 'is_cap', 'is_ebit', 'is_ni', 'e_adjni', 'e_eps', 'eps_dil', 'f_fcf', 'fcf', 'fcf_ps', 'f_ps',
          'cf_cfo', 'bs_ta', 'bs_teq', 'sh_dil', 'is_dda', 'is_int', 'sg_pjm', 'em_mwh'}
CAGR_A = {'gen_g', 'em_g', 'g_adj_mwh', 'opx_mwh', 'r_adj_m', 'r_ebit_m', 'is_ebit_m', 'is_etr', 'f_conv', 'gm_rev', 'gm_aero', 'gm_ebitda', 'gm_ebitda_m', 'gm_op_m',
          'gm_net_m', 'gm_capshare', 'fcf_m', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'wc_nwc_p', 'sg_pjm_p', 'd_dda_p', 'hr_dda', 'hr_int'}
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
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2023]}{r})^(1/2)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2022]}{r})^(1/3)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2021]}{r})^(1/4)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2024, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2023, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2022, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct'] if NF[row.nf] == NF['pct'] else nf
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: Talen earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
FS = ('Source: Talen Form S-1 (20-Jun-2024: FY2021, FY2022, the two 2023 periods, Q1/23, Q1/24), Forms 10-Q and 10-K (CIK 1622536), as originally reported. '
      'FY2023 = Predecessor (1-Jan to 17-May-2023) + Successor (18-May to 31-Dec-2023). Q2/23 = 1-Apr to 17-May + 18-May to 30-Jun (Q2-24 10-Q). Q4 = fiscal year − nine months.')
LABEL_SOURCES = {
    'gen': REL + 'summary table "Total Generation (TWh)", net of station use; acquired and sold plants for the periods owned. FY2023 and Q3/23 from the 2024 releases\' comparatives.',
    'cap': FS + ' Capacity revenues line of the statements of operations.',
    'cap_con': 'Source: Q3-26 Form 10-Q Note 3, "Future Performance Obligations" (expected capacity revenues at 30-Sep-2026); PJM auction results in the 8-Ks of 31-Jul-2024, 22-Jul-2025, 17-Dec-2025 and 14-Jul-2026.',
    'sg_pjm': ('Source: segment note of the FY2024 10-K (FY2022–24 on the current basis: PJM / Other / Corporate and Eliminations), the 2025–26 Forms 10-Q (with 2024 comparatives) and the FY2025 10-K; '
               'Q4 = fiscal year − nine months. Not published for 2021 and the 2023 quarters on this basis (the S-1 used PJM / ERCOT and WECC).'),
    'is_en': FS,
    'r_int': ('Source: reconciliations of net income (loss) to Adjusted EBITDA — Form S-1 (FY2021, FY2022, the 2023 periods, Q1/23, Q1/24) and the earnings releases (8-K Ex. 99.1) from Q2/24. '
              'Q2/23 and Q3/23 from the 2024 releases\' comparatives; Q4/23 and Q4/24 = fiscal year − nine months; Q4/25 as published (three-month column).'),
    'r_adj_pub': REL + '"Total Adjusted EBITDA" (Form S-1 before Q2/24).',
    'f_capex': REL + 'Adjusted EBITDA / Adjusted Free Cash Flow reconciliation (from Q2/24). FY2023 from the Q4-24 release; Q1/23 = Predecessor period − (1-Apr to 17-May); Q1/24 = six months − Q2/24; Q4 = fiscal year − nine months (Q4/25 as published).',
    'cf_ni': FS + ' Cash flow statements are year to date; discrete quarters are derived.',
    'bs_cash': FS + ' Balance sheets: 31-Dec-2022 and 31-Dec-2023 (S-1), then each period end; none published for 31-Mar, 30-Jun and 30-Sep-2023.',
    'bs_shares': 'Source: ' + MAN['shares_out']['src'] + '.',
    'ppa_cons': 'Source: FY2025 10-K Note 17 (Freedom and Guernsey, provisional) and Q3-26 10-Q Note 17 (Cornerstone, provisional as revised).',
    'sh_basic': FS + ' Per-share data exist for the Successor only (from 18-May-2023); FY2023 shows the Successor period; Q4 weighted shares = 4 × FY − Σ Q1–Q3 (derived).',
    'ds_total': 'Source: balance sheets; Q3-26 10-Q Note 10 (long-term debt and credit facilities); 8-Ks on the 2025–26 financings.',
    'dco_h': 'Source: ' + MON['src'] + '.',
}
CELL_COMMENTS = {}
def comments_setup():
    a23 = A[2023]; q = lambda y, n: QC[(y, n)].c
    pre = 'FY2023 = Predecessor (1-Jan to 17-May-2023, Talen Energy Supply) + Successor (18-May to 31-Dec-2023, after fresh-start accounting), summed as presented; the two periods are not comparable.'
    CELL_COMMENTS['is_en'] = {a23: pre, q(2023, 2): 'Q2/23 = Predecessor 1-Apr to 17-May + Successor 18-May to 30-Jun-2023 (Q2-24 10-Q comparatives).',
                              q(2023, 4): 'Q4/23 = FY2023 − Q1 − Q2 − Q3 (derived).'}
    CELL_COMMENTS['is_reorg'] = {a23: 'Predecessor: $799m reorganization income, net, on Emergence (gain on settlement of liabilities subject to compromise, fresh-start adjustments).',
                                 A[2022]: 'Reorganization expense $(812)m and loss on the consolidation of Cumulus Digital $(170)m.'}
    CELL_COMMENTS['is_imp'] = {A[2022]: 'Operational restructuring $488m (2022).', a23: 'Impairments: Predecessor $381m, Successor $3m.'}
    CELL_COMMENTS['is_gain'] = {A[2024]: 'Gains on the sale of the Cumulus data campus to AWS (Mar-2024) and of the ERCOT fleet (May-2024): ~$885m in aggregate.',
                                q(2026, 3): 'Sale of the 12.34% Keystone interest (Sep-2026): gain $66m.'}
    CELL_COMMENTS['is_ga'] = {q(2025, 4): 'Includes the $501m charge on the change in accounting for existing stock-based awards (stock-based compensation $526m in FY2025).'}
    CELL_COMMENTS['is_int'] = {q(2026, 2): MAN['debt']['one_offs_2026']}
    CELL_COMMENTS['sh_basic'] = {a23: 'Successor period only (18-May to 31-Dec-2023): 59.029m basic / 59.399m diluted; EPS $2.27 / $2.26 on net income attributable of $134m.'}
    CELL_COMMENTS['eps_dil'] = {a23: 'Not meaningful: FY2023 net income (Predecessor + Successor) over Successor shares. Published Successor EPS: $2.26 diluted.',
                                q(2025, 3): 'Reported diluted EPS $4.25 vs $4.26 computed (rounding of the dilution adjustments).'}
    CELL_COMMENTS['cf_wc'] = {q(2026, 2): 'Includes the $500m cash settlement of stock-based awards (liability recorded in Q4/25).'}
    CELL_COMMENTS['bs_oncl'] = {A[2022]: 'Includes $2,825m of liabilities subject to compromise (Chapter 11, filed May-2022).'}
    CELL_COMMENTS['bs_eq'] = {A[2022]: "Member's deficit of the Predecessor (Talen Energy Supply, LLC)."}
    CELL_COMMENTS['f_capex'] = {q(2023, 1): 'Derived: Predecessor period (Q4-24 release) − 1-Apr to 17-May-2023 (Q2-24 release).', q(2024, 1): 'Derived: six months − Q2/24 (Q2-24 release).'}
    CELL_COMMENTS['r_adj_pub'] = {a23: 'Predecessor $695m + Successor $426m (Form S-1).'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('FY2021–Q1/24: Form S-1 definition (Predecessor Talen Energy Supply to 17-May-2023) — hedge termination, reorganization, liability-management, Cumulus Digital / noncontrolling-interest lines shown separately',
              'Form S-1 (20-Jun-2024), "Non-GAAP Financial Measures". Adjusted EBITDA is computed consistently with the provisions of the company\'s indebtedness. Interest in the reconciliation '
              'includes other finance charges (FY2022: $365m vs $359m in the statement of operations).'),
        q(2024, 2): ('Q2/24+: earnings-release definition; Adjusted Free Cash Flow added (capex net, cash interest, taxes, pension)', 'Q2-24 release (13-Aug-2024), the first release after the Nasdaq listing.'),
        q(2025, 1): ('2025+: "Acquisition and divestiture activities" line added; stock-based and other long-term incentive compensation combined', None),
        q(2025, 4): ('Q4/25+: D&A line shown net of the amortization of acquired fuel-supply contract fair values (Freedom & Guernsey); $501m stock-award charge excluded', 'FY2025 10-K / Q4-25 release, footnote (a) of the reconciliation.'),
    }
    DEFS['f_def'] = {
        q(2023, 1): ('2023: Adjusted FCF first published in the 2024 releases (comparatives); Q1/23 derived', None),
        q(2024, 2): ('Q2/24+: Adjusted EBITDA − capex net (incl. nuclear fuel; excl. development, growth, conversion) − interest paid − taxes paid − pension contributions', None),
        q(2026, 1): ('2026: "Income taxes" line excludes NDT taxes, taxes on strategic asset sales and nuclear PTC benefits', None),
    }
    DEFS['e_def'] = {
        'C': ('Model definition for all periods: net income attributable + Adjusted EBITDA adjusting items × (1 − 25%); no company-published adjusted EPS; per-share data from the Successor period (18-May-2023)', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 and FY27 Adjusted EBITDA guidance end-points (high / mid / low), 2027E–2031E generation growth, '
            'energy margin per MWh from 2028E, PJM capacity prices from the 2029/2030 capacity year, operating-cost growth and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Talen Energy Corporation (NASDAQ: TLN) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as originally reported · USD millions (per-share data in USD; shares in millions; generation in TWh) · Calendar fiscal year · '
                'Source: Talen Form S-1 (20-Jun-2024), Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1) and deal / financing / PJM auction 8-Ks, SEC EDGAR (CIK 1622536); '
                'investor-relations releases at talenenergy.com are the same documents as filed on EDGAR. Guidance: Form 8-K of 3-Nov-2026 (EDGAR); no guidance from outside EDGAR is used')
    ws['B4'] = ('Basis notes: Talen Energy Corporation emerged from Chapter 11 on 17-May-2023 with fresh-start accounting — FY2021, FY2022 and 1-Jan to 17-May-2023 are the Predecessor '
                '(Talen Energy Supply, LLC) and are not comparable with the Successor; FY2023 = Predecessor + Successor as presented; no balance sheet for 2021 or the 2023 quarters; '
                'per-share data from 18-May-2023. Cumulus data campus sold to AWS Mar-2024, ERCOT fleet sold May-2024; Freedom & Guernsey acquired 25-Nov-2025; Cornerstone acquired '
                '15-Jun-2026; Keystone interest sold Sep-2026; PJM capacity monetization and $1.5bn ASR on 1-Oct-2026. Q4/26E calibrated to FY26 Adjusted EBITDA guidance; 2027E to FY27 guidance.')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '2Y CAGR', '3Y CAGR', '4Y CAGR'], ["26-'31", "23-'25", "22-'25", "21-'25"]):
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
        p = os.path.join(BASE, f'TLN_{scen}.xlsx')
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
    p = os.path.join(BASE, 'TLN_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
