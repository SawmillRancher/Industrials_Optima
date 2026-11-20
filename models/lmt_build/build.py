"""Build LMT_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'LMT_Model.xlsx')
G26 = MAN['guidance_2026']
PN = MAN['pension_2026']
AM = MAN['amort_sched']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    rev, cos = q['rev'], q['cos']
    return {'dso': round(q['bs_ar'] / rev * 365), 'ca': round(q['bs_ca'] / rev, 3), 'inv': round(q['bs_inv'] / rev, 3), 'oca': round(q['bs_oca'] / rev, 3),
            'dpo': round(q['bs_ap'] / cos * 365), 'sal': round(q['bs_sal'] / rev, 3), 'cl': round(q['bs_cl'] / rev, 3), 'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end 2025 levels on 2025 net sales / cost of sales (DSO {WC["dso"]}d, contract assets {WC["ca"]:.1%}, inventories {WC["inv"]:.1%}, '
              f'payables {WC["dpo"]}d, salaries {WC["sal"]:.1%}, contract liabilities {WC["cl"]:.1%}, other CL {WC["ocl"]:.1%} of sales); year ends are compared with year ends.')
YRS = list(range(FYC + 1, FYL + 1))
def flat(v): return {y: v for y in YRS}
A9 = lambda k: sum(DATA[f'Q{q}-26']['x'][k] for q in (1, 2, 3))         # 9M 2026 actual

V0 = {
    'out_hdr': '2026 outlook — Q3 2026 release (22-Oct-2026); excludes the pending Ultra Maritime acquisition',
    'out_note': ('Sales ~$80.0-82.0bn (raised from $79.75-81.75bn), business segment operating profit ~$8,575-8,675m, total FAS/CAS pension adjustment ~$1,365m, diluted EPS ~$30.35-30.75, '
                 'cash from operations ~$10.0-10.2bn, capex ~$2.1-2.3bn, free cash flow ~$7.8-8.0bn. Company bridge: FAS/CAS operating adjustment ~$1,685m, intangible amortization ~$(200)m, '
                 'other, net ~$(540)m → consolidated operating profit ~$9,520-9,620m.'),
    'outlook': [
        ('out_sales', '  2026 net sales ($m)', tuple(G26['sales']), 'm', 'Guided ~$80,000-82,000m. Drives the Q4/26E sales calibration (four segments, ex Ultra Maritime).'),
        ('out_segop', '  2026 business segment operating profit ($m)', tuple(G26['seg_op']), 'm', 'Guided ~$8,575-8,675m. Drives the Q4/26E segment-margin calibration.'),
        ('out_cop', '  2026 consolidated operating profit ($m) — memo', tuple(G26['bridge']['cons_op']), 'm', 'Company bridge ~$9,520-9,620m (information row).'),
        ('out_eps', '  2026 diluted EPS ($) — memo', tuple(G26['eps']), 'ps', 'Guided ~$30.35-30.75 (information row; the model EPS follows from the point estimates).'),
        ('out_cfo', '  2026 cash from operations ($m)', tuple(G26['cfo']), 'm', 'Guided ~$10,000-10,200m. Drives the Q4/26E contract-asset calibration plug.'),
        ('out_fcf', '  2026 free cash flow ($m) — memo', tuple(G26['fcf']), 'm', 'Guided ~$7,800-8,000m (information row; = CFO − capex point estimate).'),
        ('bb26', '  Q4/26E share repurchases ($m)', (0.0, 0.0, 0.0), 'm', 'None in 9M 2026 (cash preserved for the $3.45bn Ultra Maritime payment); none assumed for Q4 in all cases.'),
    ],
    'points': [
        ('pt_fascas', '  Q4/26E FAS/CAS pension operating adjustment ($m)', round(G26['bridge']['fascas_op'] - A9('ua_fascas'), 1), 'm', 'Outlook $1,685m less 9M actual $1,264m.'),
        ('pt_amort', '  Q4/26E intangible asset amortization ($m)', round(-G26['bridge']['amort'] - (-A9('ua_amort')), 1), 'm', 'Outlook ~$200m less 9M actual $149m.'),
        ('pt_other', '  Q4/26E unallocated other, net ($m, expense)', round(-G26['bridge']['other_net'] - (-A9('ua_other')), 1), 'm', 'Outlook ~$540m less 9M actual $344m (incl. stock-based compensation).'),
        ('pt_sev', '  Q4/26E severance / impairment charges ($m)', 0.0, 'm', 'None assumed.'),
        ('pt_nonsvc', '  Q4/26E non-service FAS pension expense ($m)', round(-PN['nonsvc'] - (-A9('nonsvc')), 1), 'm', 'Outlook $(320)m less 9M actual $(241)m.'),
        ('pt_int', '  Q4/26E interest expense ($m)', 265.0, 'm', 'Q3/26 $264m; no 2026 issuance; $1,168m repaid in 9M.'),
        ('pt_othnonop', '  Q4/26E other non-operating income, net ($m)', 60.0, 'm', '9M 2026 $179m (interest income on ~$5-6bn cash); Q3 $74m. Cash falls after the Ultra Maritime payment (assumed 31-Dec).'),
        ('pt_othinc', '  Q4/26E other income, net in operating profit ($m)', 10.0, 'm', '9M 2026 $25m.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.165, 'pct', '9M 2026 15.6%; Q3 15.1%; 2025 15.3%. 16.5% puts 2026E EPS near the mid-point of the guided range (information row).'),
        ('pt_dep', '  Q4/26E depreciation & other amortization ($m)', 380.0, 'm', '9M 2026 D&A $1,223m incl. $149m intangible amortization (~$358m a quarter of other D&A); Q4 is a 14-week quarter.'),
        ('pt_sbc', '  Q4/26E stock-based compensation ($m)', 90.0, 'm', '9M 2026 $269m.'),
        ('pt_def', '  Q4/26E deferred income taxes ($m)', 100.0, 'm', '9M 2026 $1,114m (tax-law changes); assumed to normalise.'),
        ('pt_wc_ar', '  Q4/26E change in receivables ($m; cash inflow +)', 300.0, 'm', 'Q4 collections (Q4/25 +$57m; Q4/24 +$0.6bn); assumption.'),
        ('pt_wc_inv', '  Q4/26E change in inventories ($m)', 0.0, 'm', 'Assumption.'),
        ('pt_wc_ap', '  Q4/26E change in accounts payable ($m)', 0.0, 'm', 'Assumption.'),
        ('pt_wc_cl', '  Q4/26E change in contract liabilities ($m)', 0.0, 'm', 'Assumption (Q4/25 −$0.3bn; Q4/24 +$1.3bn).'),
        ('pt_wc_tax', '  Q4/26E income taxes (working capital, $m)', 0.0, 'm', 'Assumption.'),
        ('pt_wc_oth', '  Q4/26E other operating, net ($m)', 0.0, 'm', 'Assumption; contract assets are the calibration plug to the guided cash from operations.'),
        ('pt_capex', '  2026 capital expenditures ($m)', G26['capex'][1], 'm', 'Guided ~$2,100-2,300m (9M $1,268m).'),
        ('pt_ofin', '  Q4/26E other financing, net ($m)', -10.0, 'm', '9M 2026 $(118)m (tax withholding on awards, mostly Q1).'),
    ],
    'lev': (1.50, 1.25, 1.00),
    'lev_note': ('Net debt $14.5bn at 27-Sep-2026 (~1.3x 2026E adjusted EBITDA) before the $3.45bn Ultra Maritime payment (~1.5x at YE2026E). Repurchases resume from 2027E up to the leverage '
                 'target (A-/Baa1 ratings; 2018-25 net debt / adjusted EBITDA 1.0-1.8x; buybacks $1.1-7.9bn a year). Base 1.25x gives ~$4-5bn a year, near the 2023-25 pace; below the target free cash flow repays commercial paper. Bull = more buybacks (higher target).'),
    'blocks': [
        ('AERO_G', 'AERO_G (Aeronautics sales y/y)', 0.02, -0.03, [0.05, 0.04, 0.04, 0.03, 0.03],
         '9M 2026 +7% (F-35 production / sustainment, C-130 award); backlog $57bn (1.8x sales); F-35 Lot 20+ not yet definitized (contractual authorization exceeded in Q3/26). Assumption.', 'pct', False),
        ('MFC_G', 'MFC_G (Missiles and Fire Control sales y/y)', 0.04, -0.05, [0.15, 0.12, 0.10, 0.07, 0.05],
         '9M 2026 +17% (PAC-3, THAAD, GMLRS, PrSM ramps); backlog $143bn (8.9x sales) incl. the $52.5bn PAC-3 MSE multi-year award (Q3/26). Assumption.', 'pct', False),
        ('RMS_G', 'RMS_G (Rotary and Mission Systems sales y/y, excl. Ultra Maritime)', 0.02, -0.03, [0.05, 0.04, 0.04, 0.03, 0.03],
         '9M 2026 +1% (radars up; CMHP / Seahawk down); backlog $49bn (2.9x sales). Ultra Maritime is added in its own block. Assumption.', 'pct', False),
        ('SPACE_G', 'SPACE_G (Space sales y/y)', 0.02, -0.03, [0.05, 0.04, 0.04, 0.03, 0.03],
         '9M 2026 +5% (FBM, NGI, hypersonics; OPIR lifecycle decline); backlog $43bn (3.1x sales). Assumption.', 'pct', False),
        ('AERO_M', 'AERO_M (Aeronautics segment margin)', 0.005, -0.010, [0.095, 0.097, 0.100, 0.100, 0.100],
         '9M 2026 9.1% (2025 6.0% after the Q2/25 $950m classified-program loss; 2019-23 10.3-10.9%). Assumption.', 'pct', False),
        ('MFC_M', 'MFC_M (MFC segment margin)', 0.005, -0.010, [0.140, 0.142, 0.145, 0.145, 0.145],
         '9M 2026 14.1% (2024 2.6% after the $1.4bn classified-program loss; 2019-23 13.5-14.4%). Assumption.', 'pct', False),
        ('RMS_M', 'RMS_M (RMS segment margin)', 0.005, -0.010, [0.115, 0.117, 0.120, 0.120, 0.120],
         '9M 2026 10.8% (Q3 11.6%; 2025 6.7% after the CMHP / TUHP losses; 2019-23 10.4-11.7%). Assumption.', 'pct', False),
        ('SPACE_M', 'SPACE_M (Space segment margin)', 0.005, -0.010, [0.095, 0.097, 0.100, 0.100, 0.100],
         '9M 2026 9.4% (2021-25 9.9-10.9% incl. ULA equity earnings). Assumption.', 'pct', False),
        ('B2B', 'B2B (book-to-bill, all segments, x)', 0.05, -0.05, [1.05, 1.03, 1.02, 1.00, 1.00],
         '9M 2026 2.1x (PAC-3 MSE award); 2021-25 1.0-1.2x. Record $292bn backlog = 3.6x sales. Assumption.', 'x2', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions beyond Ultra Maritime, $m)', 500.0, -500.0, [500.0, 500.0, 500.0, 500.0, 500.0],
         'Lockheed Martin spent $9.0bn on Sikorsky (2015) and $3.45bn on Ultra Maritime (2026; separate block); otherwise small. Base $500m p.a. (assumption).', 'm', True),
    ],
    'b2b_q4': {'aero': 1.0, 'mfc': 1.0, 'rms': 1.0, 'space': 1.0},
    'ae_sev': flat(0.0),
    'ua_other_pct': 0.0065,
    'pn': {'cas': {2026: PN['cas'], **flat(PN['cas'])}, 'svc': {2026: PN['fas_svc'], **flat(PN['fas_svc'])}, 'nonsvc': {2026: PN['nonsvc'], **flat(-300.0)},
           'contrib': {2026: 0.0, **flat(0.0)}},
    'um': {'sales': 900.0, 'g': 0.05, 'm': 0.12, 'intp': 0.40, 'life': 12, 'ppe': 0.10},
    'mna_note': 'Scenario lever M&A_spend (Base $500m p.a. of bolt-ons). Funded from cash / commercial paper (debt schedule).',
    'm_mult': 3.5,
    'rev_guid_note': 'Company 2026 sales outlook ~$80.0-82.0bn (raised 22-Oct-2026 from $79.75-81.75bn). Drives the sales calibration.',
    'segop_guid_note': 'Company 2026 business segment operating profit outlook ~$8,575-8,675m (22-Oct-2026). Drives the segment-margin calibration.',
    'eps_guid_note': 'Company 2026 diluted EPS outlook ~$30.35-30.75 (22-Oct-2026). Information row: the model EPS results from the segment calibration plus the unallocated / interest / tax point estimates.',
    'cfo_guid_note': 'Company 2026 cash from operations outlook ~$10.0-10.2bn (raised 22-Oct-2026 from $9.2-9.4bn). The Q4/26E contract-asset change is solved so that 2026E CFO = the end-point.',
    'amort_sched': {2027: AM['2027'], 2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: 100.0},
    'dep_pct': {2027: 0.019, 2028: 0.0195, 2029: 0.020, 2030: 0.020, 2031: 0.020},
    'sbc_pct': 0.0042, 'etr': 0.16, 'othinc': 40.0, 'othnonop_x': 20.0,
    'capex_pct': flat(0.026),
    'dps_q': 3.60, 'dps_g': 0.045, 'def_ae': 200.0, 'ofin_ae': -150.0, 'iss_q4': 0.25, 'iss_ae': 1.0, 'dil': 1.0,
    'mat': {2026: 750.0, 2027: 1000.0, 2028: 650.0, 2029: 1150.0, 2030: 600.0, 2031: 800.0},
    'repay': {2026: 0.0}, 'iss_notes': {2026: 0.0}, 'refi': 1.0,
    'min_cash': 2500.0, 'bb_min': 1000.0,
    'r_notes': 0.052,
    'wc': dict(WC, ca={2027: 0.190, 2028: 0.180, 2029: 0.175, 2030: WC['ca'], 2031: WC['ca']}),
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $601.50 (mid-point of the 23-Oct-2026 open-market sales on the Form 4 of F. A. St John, filed 27-Oct-2026 — the latest '
                'share price observable on EDGAR; ~$139bn market cap); update to market'),
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
        if row.spec2 and not kw.get('qe_ok'): return None, False
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
CAGR_G = {'is_rev', 'g_rev', 'aero_rev', 'mfc_rev', 'rms_rev', 'space_rev', 'aero_oi', 'mfc_oi', 'rms_oi', 'space_oi', 'aero_bk', 'mfc_bk', 'rms_bk', 'space_bk', 'bk_tot',
          'g_segop', 'o_adj', 'g_op', 'r_adj', 'r_ebitda', 'r_ebit', 'is_op', 'd_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_gp',
          'is_ni', 'eps_dil', 'dps', 'ua_fascas', 'pn_cas', 'is_cont'}
CAGR_A = {'aero_m', 'mfc_m', 'rms_m', 'space_m', 'g_segm', 'g_opm', 'o_adj_m', 'r_adj_m', 'r_ebit_m', 'is_gm', 'is_opm', 'gm_rev', 'gm_aero', 'gm_mfc', 'gm_rms', 'gm_space',
          'gm_gm', 'gm_segm', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_fascas_p', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x',
          'd_dep_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'd_etr', 'fcf_eb', 'ua_other_pct', 'aero_mix', 'mfc_mix', 'rms_mix', 'space_mix', 'aero_b2b', 'mfc_b2b', 'rms_b2b', 'space_b2b',
          'bk_cov', 'wc_ca', 'wc_cl'}
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

REL = 'Source: Lockheed Martin earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'aero_rev': REL + ('business segment net sales / operating profit schedules, as originally reported, except: 2006 on the four-segment basis of the FY2007 release; 2011-12 on the 2013 five-segment '
                       'basis (FY2013 Form 10-K; Q4-13 release); 2014-15 on the Q4/15 program realignment basis (pro forma tables, Q4-15 release of 26-Jan-2016); Q1/Q2-16 continuing operations '
                       '(2017 release comparatives); 2017 on the ASC 606 adjusted basis (2018 release comparatives). Space Systems renamed Space in 2019; MST renamed RMS in 2016.'),
    'aero_bk': REL + 'operating-data tables (backlog by segment at period end; 2006 total only). 2014-15 segment backlog on the Q4/15 realignment basis (Jan-2016 pro forma backlog table).',
    'ua_fascas': REL + 'unallocated items (segment schedules; 2006-12 "Selected Financial Data"). FAS/CAS pension adjustment: total adjustment to 2017 (2017 re-presented under ASU 2017-07 in the 2018 releases); operating adjustment from 2018.',
    'pn_cas': REL + 'FAS/CAS pension tables (annual: fourth-quarter releases and the following year\'s "Outlook / Actual" tables; 2006-08 "FAS 87 expense" / "CAS costs"); FY2025 Form 10-K Note 11.',
    'is_rev': REL + ('consolidated statements of earnings, as originally reported, except the re-presented periods (2006: FY2007 release presentation of non-operating items; Q1/Q2-16: continuing operations per the 2017 releases; '
                     '2017: ASC 606 / ASU 2017-07 adjusted per the 2018 releases, with the non-service pension reclassification by quarter from the Q1-18 release). Cell comments on the re-presented cells give the originally reported figures.'),
    'd_dda': 'Source: consolidated statements of cash flows (releases; year to date, quarters derived). Intangible amortization from the unallocated-items line (2023+).',
    'o_pub': REL + 'business segment operating profit (segment schedules; the company\'s non-GAAP measure, reconciled to consolidated operating profit in every release).',
    'cf_ni': ('Source: release condensed statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M); as originally reported (incl. IS&GS cash flows to Aug-2016). '
              'Lines not separately presented in a period are inside "other, net" (derived).'),
    'bs_cash': REL + 'consolidated balance sheets (period ends), as originally reported (pre-ASC 606 presentation to 2017: unbilled receivables in receivables; customer advances line).',
    'sh_basic': REL + 'statements of earnings (weighted average shares; common shares outstanding at period end). No stock splits in the period.',
    'ds_total': 'Source: release balance sheets; FY2025 Form 10-K Note 10 (notes ladder); Q3 2026 Form 10-Q (principal $21.7bn at 27-Sep-2026; $6.0bn of undrawn revolving credit facilities).',
    'um_hdr': MAN['ultra_maritime']['src'],
    'e_co_ps': 'Source: release text / supplemental tables for each item (see manual_items.json special_items): Q4-17 Tax Act; Q3-21 and Q2-22 and Q4-25 pension settlement charges; Q4-24 and Q2-25 program losses.',
    'dps': 'Source: XBRL CommonStockDividendsPerShareDeclared (10-K / 10-Q); FY2006-08 from the FY2008 Form 10-K selected financial data; Q4-26 rate per the Q3-26 10-Q (October 2026 declaration).',
    'dl_f35': REL + 'operating-data tables (aircraft deliveries).',
}
CELL_COMMENTS = {}
def comments_setup():
    for p, x in DATA.items():
        x = x.get('x', {})
        col = next((c for c in COLS if pkey(c) == p), None)
        if not col: continue
        if x.get('seg_orig'):
            o = x['seg_orig']
            CELL_COMMENTS.setdefault('aero_rev', {})[col.c] = (f'Segments {p}: {x.get("seg_basis")}. Originally reported segment net sales / operating profit: ' +
                '; '.join(f'{k} {v:,.0f} / {o["op"].get(k, float("nan")):,.0f}' for k, v in o['sales'].items()))
        if x.get('is_orig'):
            o = x['is_orig']
            CELL_COMMENTS.setdefault('is_rev', {})[col.c] = (f'Income statement {p}: {x.get("is_basis")}. Originally reported: ' +
                ', '.join(f'{k} {v:,.2f}' if k == 'eps_d' else f'{k} {v:,.0f}' for k, v in o.items()))
        if x.get('sp_lab'):
            CELL_COMMENTS.setdefault('e_co_ps', {})[col.c] = f'Company-quantified items {p}: {x["sp_lab"]}'
    CELL_COMMENTS['cf_bb'] = {A[2006]: '2006: "Common stock activity, net" (repurchases net of issuances) as presented in the FY2006 release cash-flow statement.'}
    CELL_COMMENTS['rms_rev'] = {QC[(2015, 4)].c: 'Q4/15 includes Sikorsky from 6-Nov-2015 (acquired for $9.0bn; MST renamed Rotary and Mission Systems in 2016).'}
    CELL_COMMENTS['is_disc'] = {A[2016]: '2016: IS&GS (divested to Leidos 16-Aug-2016) — net earnings from discontinued operations $1,549m incl. the gain on the transaction.',
                                A[2010]: '2010: EIG and PAE businesses sold (discontinued operations $281m incl. gains).'}
    CELL_COMMENTS['is_tax'] = {QC[(2017, 4)].c: 'Q4/17: income tax expense includes the ~$1.9bn net one-time charge for the Tax Cuts and Jobs Act ($6.80 per share; adjusted EPS from continuing operations $4.30 per the release).'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('2006-10: four segments (Aeronautics / Electronic Systems / IS&GS / Space Systems; 2006 re-presented in the FY2007 release). Unallocated: total FAS/CAS adjustment, stock compensation, unusual items, other',
              'The FY2006 release still showed the Systems & IT Group (Electronic Systems, IT&GS, IS&S); the FY2007 release re-presented 2006 on the four-segment basis used here.'),
        A[2011]: ('2011-12: five segments (Aeronautics / IS&GS / MFC / MST / Space Systems) as re-presented in the FY2013 Form 10-K (2011) and the Q4-13 release (2012); Electronic Systems split into MFC / MST / IS&GS',
                  'Realignment effective 31-Dec-2012; consolidated figures unchanged.'),
        q(2013, 1): ('2013-15: five segments as reported; 2014-15 on the Q4/15 program realignment basis (Jan-2016 pro forma tables); severance / goodwill impairment shown as special items', None),
        q(2016, 1): ('2016+: four segments (IS&GS in discontinued operations; Q1/Q2-16 re-presented per the 2017 releases); MST renamed Rotary and Mission Systems; Sikorsky in RMS', None),
        q(2017, 1): ('2017: ASC 606 adjusted basis and FAS/CAS *operating* adjustment (ASU 2017-07) as re-presented in the 2018 releases', 'Historical 2017 as first reported: net sales $51,048m, operating profit $5,921m, unallocated $806m (total FAS/CAS adjustment $876m).'),
        q(2018, 1): ('2018+: as reported (ASC 606; non-service FAS pension cost below operating profit); Space Systems renamed Space (2019); intangible amortization shown separately from 2023', None),
    }
    DEFS['e_def'] = {
        'C': ('Model definition throughout: + severance / impairment / unusual items (tax-effected at 35%) — the company published no adjusted EPS', None),
        q(2017, 4): ('Q4/17: + Tax Act one-time charge ($6.80 per share; company-quoted adjusted EPS from continuing operations $4.30)', None),
        q(2018, 1): ('2018+: items tax-effected at 21%; pension settlement charges (Q3/21, Q2/22, Q4/25) and quantified program losses (Q4/24, Q2/25) at the company-disclosed after-tax amounts', None),
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
                ws[f'{col}{r}'].number_format = '\\+#,##0;\\-#,##0' if nf == 'm' else ('\\+0.00;\\-0.00' if nf == 'x2' else '\\+0.0%;\\-0.0%')
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: 2026 sales, segment-operating-profit and cash-from-operations guidance end-points (high / mid / low), '
            '2027E–2031E segment sales growth, segment margins, book-to-bill, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Lockheed Martin Corporation (NYSE: LMT) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 31 December (quarters close on the last Sunday of March / June / September) · '
                'Source: Lockheed Martin Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1), SEC EDGAR (CIK 936468); XBRL company facts; '
                'investor-relations releases at lockheedmartin.com are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: as originally reported, with company re-presentations applied where the following year\'s filings re-present the whole period (2006 segments / non-operating items; 2011-12 five-segment '
                'realignment; 2014-15 Q4/15 program realignment; Q1/Q2-16 continuing operations ex IS&GS; 2017 ASC 606 + ASU 2017-07). IS&GS divested Aug-2016 (disc. ops); Sikorsky acquired 6-Nov-2015; '
                'Ultra Maritime ($3.45bn) pending, expected Q4-26. Q4/26E calibrated to the 22-Oct-2026 outlook (sales, business segment operating profit, cash from operations).')
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
    wid = {'A': 11.0, 'Q': 9.5703125, 'QE': 11.42578125, 'E26': 12.5, 'AE': 11.5}
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
        p = os.path.join(BASE, f'LMT_{scen}.xlsx')
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
    p = os.path.join(BASE, 'LMT_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
