"""Build NOC_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC, SEG
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'NOC_Model.xlsx')
G26 = MAN['guidance_fy26']
GS = G26['segments']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    rev, cos = q['rev'], q['cos']
    return {'dso': round(q['bs_ar'] / rev * 365), 'dunb': round(q['bs_unb'] / rev * 365), 'dio': round(q['bs_inv'] / cos * 365), 'dpo': round(q['bs_ap'] / cos * 365),
            'accr': round(q['bs_accr'] / rev, 3), 'adv': round(q['bs_adv'] / rev, 3), 'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at year-end (31-Dec-2025) levels on 2025 sales / cost of sales (DSO {WC["dso"]}d, unbilled {WC["dunb"]}d, inventoried costs {WC["dio"]}d, '
              f'payables {WC["dpo"]}d, accrued compensation {WC["accr"]:.1%}, advances {WC["adv"]:.1%}, other current liabilities {WC["ocl"]:.1%} of sales); year ends are compared with year ends.')
AM = MAN['amort_sched']

V0 = {
    'out_hdr': '2026 guidance — Q3 2026 release (20-Oct-2026)',
    'out_note': ('Sales $43,750–44,250m (raised 21-Jul-2026), segment operating income $4,940–5,040m (raised 20-Oct-2026 from $4,850–5,000m), MTM-adjusted EPS $29.35–29.75 (raised from $28.60–29.10), '
                 'adjusted free cash flow $3,100–3,500m. Segment guidance: Aeronautics ~$14bn / high 9%, Defense mid-to-high $8bn / ~10%, Mission high $12bn / mid 15%, Space ~$11bn / low 10%, eliminations ~($2.7bn) / mid 13%.'),
    'outlook': [
        ('out_sales', '  2026 sales ($m)', tuple(G26['sales']), 'm', 'Guided $43,750–44,250m. Drives the Q4/26E sales calibration.'),
        ('out_soi', '  2026 segment operating income ($m)', tuple(G26['segment_oi']), 'm', 'Guided $4,940–5,040m. Drives the Q4/26E segment-margin calibration.'),
        ('out_eps', '  2026 MTM-adjusted EPS ($) — memo', tuple(G26['mtm_adj_eps']), 'ps', 'Guided $29.35–29.75 (information row; the model result depends on the Q4 tax rate and pension inputs).'),
        ('out_fcf', '  2026 adjusted free cash flow ($m) — memo', tuple(G26['adj_fcf']), 'm', 'Guided $3,100–3,500m (information row).'),
        ('bb26', '  Q4/26E share repurchases ($m)', (600.0, 300.0, 0.0), 'm', 'No repurchases in Q3 2026; $68m in 9M 2026; $2.5bn remaining on the authorization at 30-Sep-2026 (10-Q). Assumption.'),
    ],
    'points': [
        ('pt_elim_p', '  Q4/26E intersegment eliminations % of gross segment sales', 0.060, 'pct', '9M 2026 6.0% (Q3 5.6%); 2026 guidance ~($2.7bn) on ~$46bn gross.'),
        ('pt_elim_m', '  Eliminations margin rate (all forecast periods)', GS['elim']['om_mid'], 'pct', '2026 guidance "mid 13%"; 9M 2026 13.5%.'),
        ('pt_fascas', '  Q4/26E FAS/CAS operating adjustment ($m)', 10.0, 'm', '9M 2026 $29m (Q3 $15m); no guidance on EDGAR. Run-rate point estimate.'),
        ('pt_unalloc', '  Q4/26E unallocated corporate expense ($m; negative)', -90.0, 'm', '9M 2026 −$250m (Q3 −$91m) incl. −$51m of intangible amortization / step-up depreciation.'),
        ('pt_nonop', '  Q4/26E non-operating FAS pension benefit ($m)', 167.0, 'm', 'Q3 2026 $167m; 9M $499m.'),
        ('pt_oth', '  Q4/26E other, net incl. interest income ($m)', 35.0, 'm', '9M 2026 $124m (Q3 $20m; Q2 included marketable-securities gains). Assumption.'),
        ('pt_int', '  Q4/26E interest expense ($m)', 158.0, 'm', 'Q3 2026 $158m; no new debt; $527m repaid Mar-2026.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.18, 'pct', '9M 2026 11.5% (Q3 13.4%, higher research credits); 2025 full year 17.5%; Q4 2025 ~17%. Assumption: set so that the 2026E MTM-adjusted EPS lands inside the guided $29.35–29.75 range (tax guidance is not on EDGAR).'),
        ('pt_dda', '  Q4/26E depreciation & amortization ($m)', 385.0, 'm', '9M 2026 $1,118m (~$373m a quarter), rising with capex.'),
        ('pt_sbc', '  Q4/26E stock-based compensation ($m)', 25.0, 'm', '9M 2026 $75m.'),
        ('pt_def', '  Q4/26E deferred income taxes ($m)', 100.0, 'm', '9M 2026 $651m (2025 full year $548m, Q4 2025 $204m) — assumption.'),
        ('pt_contrib', '  Q4/26E pension & OPB cash contributions ($m)', 35.0, 'm', '9M 2026 $92m (~$30m a quarter); 2025 ~$130m.'),
        ('pt_capex', '  2026E capital expenditures ($m)', 1250.0, 'm', '9M 2026 $775m; 2025 $1,450m (Q4 2025 $662m). No capex guidance in the release (assumption).'),
        ('pt_b2b', '  Q4/26E book-to-bill (x)', 1.0, 'x2', 'Q4 2025 1.3x; 9M 2026 ~1.4x (record $110bn backlog). Assumption.'),
        ('pt_g_as_s', '  Memo: 2026 Aeronautics sales guidance mid-point ($m)', GS['as']['sales_mid'], 'm', GS['as']['sales_bn'] + ' bn'),
        ('pt_g_as_m', '  Memo: 2026 Aeronautics margin guidance', GS['as']['om_mid'], 'pct', GS['as']['om']),
        ('pt_g_ds_s', '  Memo: 2026 Defense sales guidance mid-point ($m)', GS['ds']['sales_mid'], 'm', GS['ds']['sales_bn'] + ' bn'),
        ('pt_g_ds_m', '  Memo: 2026 Defense margin guidance', GS['ds']['om_mid'], 'pct', GS['ds']['om']),
        ('pt_g_ms_s', '  Memo: 2026 Mission sales guidance mid-point ($m)', GS['ms']['sales_mid'], 'm', GS['ms']['sales_bn'] + ' bn'),
        ('pt_g_ms_m', '  Memo: 2026 Mission margin guidance', GS['ms']['om_mid'], 'pct', GS['ms']['om']),
        ('pt_g_ss_s', '  Memo: 2026 Space sales guidance mid-point ($m)', GS['ss']['sales_mid'], 'm', GS['ss']['sales_bn'] + ' bn'),
        ('pt_g_ss_m', '  Memo: 2026 Space margin guidance', GS['ss']['om_mid'], 'pct', GS['ss']['om']),
    ],
    'lev': (1.75, 1.50, 1.25),
    'lev_note': ('Net debt $11.5bn at 30-Sep-2026 ≈ 1.9x 2026E adjusted EBITDA (model; 1.6–2.3x in 2021–25). Target = leverage up to which surplus cash is returned via buybacks; '
                 'below it free cash flow repays commercial paper. The company states no leverage target (assumption).'),
    'blocks': [
        ('AS_G', 'AS_G (Aeronautics Systems sales y/y)', 0.03, -0.04, [0.07, 0.06, 0.05, 0.05, 0.04],
         '9M 2026 +14% (F-35 lot timing, B-21 production ramp, B-2 sustainment); backlog $26.8bn (1.9x sales); 2025 +5%. Normalising toward mid single digits as F-35 fuselage volumes plateau.', 'pct', False),
        ('DS_G', 'DS_G (Defense Systems sales y/y)', 0.03, -0.04, [0.09, 0.08, 0.07, 0.06, 0.05],
         '9M 2026 +8% (Sentinel ramp, GMLRS ER, solid rocket motors; training services sold Q2 2025); backlog $36.5bn (4.2x sales, Sentinel). Highest growth of the four sectors.', 'pct', False),
        ('MS_G', 'MS_G (Mission Systems sales y/y)', 0.03, -0.04, [0.05, 0.05, 0.04, 0.04, 0.04],
         '9M 2026 +2% (restricted airborne radar and marine systems vs lower advanced microelectronics); 2025 +10%; backlog $20.0bn (1.6x sales).', 'pct', False),
        ('SS_G', 'SS_G (Space Systems sales y/y)', 0.03, -0.04, [0.04, 0.05, 0.05, 0.04, 0.04],
         '9M 2026 +1% (restricted space ramp vs lower Commercial Resupply Services and the 2024 NGI / restricted program wind-downs); 2025 −8%; backlog $26.3bn (2.4x sales).', 'pct', False),
        ('AS_M', 'AS_M (Aeronautics operating margin rate)', 0.005, -0.010, [0.100, 0.102, 0.105, 0.107, 0.108],
         '2026 guided "high 9%" (9M 2026 10.1%; 2025 6.3% after the $477m B-21 loss provision; 2024 10.3%). B-21 LRIP lots are at zero / low margin, so the rate recovers only gradually.', 'pct', False),
        ('DS_M', 'DS_M (Defense operating margin rate)', 0.005, -0.010, [0.102, 0.104, 0.106, 0.108, 0.108],
         '2026 guided ~10% (9M 2026 9.4%; 2025 10.9% incl. divested training services; 2024 (recast) 9.7%). Sentinel cost-type mix dilutes the rate as it ramps.', 'pct', False),
        ('MS_M', 'MS_M (Mission operating margin rate)', 0.005, -0.010, [0.153, 0.153, 0.153, 0.152, 0.152],
         '2026 guided "mid 15%" (9M 2026 15.5%; 2025 14.6%; 2024 14.0%); favourable EAC adjustments on mature production programs.', 'pct', False),
        ('SS_M', 'SS_M (Space operating margin rate)', 0.005, -0.010, [0.104, 0.106, 0.108, 0.108, 0.108],
         '2026 guided "low 10%" (9M 2026 9.8%; 2025 11.0%; 2024 10.7%); mix shifting to fixed-price restricted work.', 'pct', False),
        ('ELIM_P', 'ELIM_P (intersegment eliminations % of gross segment sales)', -0.003, 0.003, [0.060, 0.060, 0.060, 0.060, 0.060],
         '9M 2026 6.0%; 2025 5.2%; 2024 (recast) 4.4% — intersegment content (Mission Systems sensors on Aeronautics / Space platforms) is rising. Bull = fewer eliminations (more external sales).', 'pct', False),
        ('B2B', 'B2B (book-to-bill, x)', 0.10, -0.10, [1.05, 1.05, 1.03, 1.02, 1.00],
         '2021–25 book-to-bill 0.9–1.3x (2025 1.1x; 9M 2026 ~1.4x on Sentinel / restricted awards). Base 1.05x keeps backlog growing roughly in line with sales; memo only (no sales linkage).', 'x2', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 500.0, -500.0, [500.0, 500.0, 500.0, 500.0, 500.0],
         'No acquisitions since Orbital ATK (2018); the company has been a net divestor (IT services 2021, training services 2025). Base $500m p.a. of bolt-ons (assumption).', 'm', True),
        ('BBMIN', 'BB_min (minimum share repurchases, $m)', 500.0, -500.0, [1500.0, 1500.0, 1500.0, 1500.0, 1500.0],
         'Repurchases: 2021 $3.7bn, 2022 $1.5bn, 2023 $1.5bn, 2024 $2.6bn, 2025 $1.2bn; $2.5bn authorization remaining at 30-Sep-2026. Floor for the leverage plug (assumption).', 'm', True),
    ],
    'cas_26': 240.0, 'cas_ae': 240.0, 'svc_26': 200.0, 'svc_ae': 200.0,
    'unalloc_pct': {2027: 0.0060, 2028: 0.0060, 2029: 0.0060, 2030: 0.0060, 2031: 0.0060},
    'amort': {2026: AM['2026'], 2027: AM['2027'], 2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: 31.0},
    'ga_pct': {2027: 0.096, 2028: 0.096, 2029: 0.095, 2030: 0.095, 2031: 0.095},
    'dda_pct': {2027: 0.035, 2028: 0.035, 2029: 0.034, 2030: 0.034, 2031: 0.033},
    'sbc_pct': 0.0025, 'nonop_ae': {2027: 650.0, 2028: 650.0, 2029: 650.0, 2030: 650.0, 2031: 650.0}, 'oth_ae': 40.0, 'etr': 0.16,
    'dps_q': 2.47, 'dps_g': 0.08, 'def_ae': {2027: 150.0, 2028: 100.0, 2029: 50.0, 2030: 0.0, 2031: 0.0}, 'contrib_ae': 125.0,
    'eq_q4': -5.0, 'eq_ae': -70.0, 'iss_q4': 0.02, 'iss_ae': 0.20, 'dil': 0.3,
    'capex_pct': {2027: 0.032, 2028: 0.031, 2029: 0.030, 2030: 0.030, 2031: 0.030},
    'refi': {2027: 1.0, 2028: 1.0, 2029: 1.0, 2030: 1.0, 2031: 1.0},
    'repay': {2026: 0.0, 2027: 755.0, 2028: 2044.0, 2029: 592.0, 2030: 1252.0, 2031: 0.0},
    'mat': {2026: 755.0, 2027: 2044.0, 2028: 592.0, 2029: 1252.0, 2030: 0.0, 2031: 0.0},
    'repay_note': ('FY2025 10-K maturity table: 2026 $534m (of which $527m of 7.875% / 7.75% notes repaid Mar-2026), 2027 $755m, 2028 $2,044m, 2029 $592m, 2030 $1,252m, thereafter $10,621m. '
                   '2031 maturities are not itemised in the five-year table (input 0). Q4/26E: no further maturities.'),
    'min_cash': 2000.0,
    'r_notes': {2027: 0.0435, 2028: 0.0440, 2029: 0.0450, 2030: 0.0455, 2031: 0.0460},
    'r_notes_note': ('2025 interest expense $665m on ~$15.9bn average debt (~4.2%, after ~$100m of capitalized interest); 9M 2026 $481m on $15.2bn (~4.2%). '
                     'Drifting up as maturities (3.2–4.4% coupons) are refinanced at an assumed ~5.25% (May-2025 issues 4.65–5.25%).'),
    'wc': WC,
    'px': MAN['share_price']['px'],
    'px_note': ('VALUATION — share price input $555.32 (Form 4 of 2-Nov-2026: shares withheld at $555.32; open-market sales the same day at $553.39–557.47 — the latest share price in an SEC filing; '
                '~$79bn market cap); no repurchases in Q3 2026, so the 10-Q carries no average repurchase price. Update to market.'),
    'mna_note': 'Scenario lever M&A_spend (Base $500m p.a. of bolt-ons; assumption). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': 'Company 2026 sales guidance $43,750–44,250m (raised 21-Jul-2026; unchanged 20-Oct-2026). Drives the sales calibration.',
    'soi_guid_note': 'Company 2026 segment operating income guidance $4,940–5,040m (raised 20-Oct-2026). Drives the segment-margin calibration.',
    'eps_guid_note': 'Company 2026 MTM-adjusted EPS guidance $29.35–29.75 (raised 20-Oct-2026). Information row: not forced (the Q4 tax rate and pension inputs are run-rate point estimates).',
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
    if k in FCK and 'fc_in' in kw: return kw['fc_in'], True
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
        if kw.get('bs') and not row.spec2 and ('qe' in kw or 'qe_in' in kw): return f'={QE}{row.r}', False
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
CAGR_G = {'is_rev', 'g_rev', 'g_gross', 'as_s', 'ds_s', 'ms_s', 'ss_s', 'as_oi', 'ds_oi', 'ms_oi', 'ss_oi', 'g_soi', 'is_oi', 'r_adj', 'r_ebitda', 'r_aebit', 'd_dda',
          'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'afcf', 'bs_ta', 'bs_eq', 'sh_dil', 'is_gp', 'is_ga', 'is_ni', 'eps_dil', 'dps', 'bl_tot', 'rc_fascas', 'is_svc', 'is_prod'}
CAGR_A = {'as_m', 'ds_m', 'ms_m', 'ss_m', 'g_som', 'r_adj_m', 'r_aebit_m', 'is_gm', 'is_oim', 'gm_rev', 'gm_as', 'gm_ds', 'gm_ms', 'gm_ss', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m',
          'gm_ga', 'gm_som', 'gm_fascas', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_ga', 'd_dda_p', 'd_sbc_p', 'wc_nwc_p', 'is_etr', 'el_p', 'el_m',
          'bl_b2b', 'bl_cov', 'rc_unalloc_p', 'd_svc_p', 'as_mix', 'ds_mix', 'ms_mix', 'ss_mix'}
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

REL = 'Source: Northrop Grumman earnings releases (Form 8-K Item 2.02, Ex. 99 / 99.1) — '
LABEL_SOURCES = {
    'as_s': (REL + 'consolidated segment table (sales and operating income by segment, intersegment eliminations). Current four-sector structure (from 1-Jan-2020): 2019 from the 2020 releases\' comparatives; '
             '2018–19 annual from the FY2020 10-K segment note; 2024 as recast for the 1-Jan-2025 realignment (2025 releases); 2023 as reported (the 2024 releases recast only Q3–Q4 for the 1-Jan-2024 realignment, so all four quarters are kept as reported). '
             'Earlier structures in the legacy memo block.'),
    'el_s': REL + 'segment table ("Intersegment eliminations").',
    'g_soi_pub': REL + 'segment table ("Segment operating income", non-GAAP; "Total segment operating margin" 2006–08).',
    'bl_tot': REL + 'backlog schedule ("Total backlog"; funded / unfunded from 2011) or release narrative ($bn); 2016–17 quarters where the release gives no backlog are blank. 10-K segment notes for 2006–08 are not used.',
    'rc_fascas': REL + 'reconciliation of segment operating income to operating income. FY2006–08 from the 10-K segment note / MD&A table.',
    'rc_cas': 'Source: Forms 10-K, MD&A "Segment operating income" reconciliation table (CAS pension expense, FAS pension service expense) — FY2012–25 annual.',
    'is_rev': REL + 'condensed consolidated statements of earnings (FY2006–08: Form 10-K statements of income). Quarters as originally reported; Q1–Q3 2018 as recast in the Q4 2018 release (MTM accounting change). Q4 lines from the release\'s consolidated table (the fourth-quarter releases print only full-year statements).',
    'is_prod': REL + 'statements of earnings ("Product" / "Service" sales and costs). Q4 = year − nine months (derived).',
    'd_dda': 'Source: release cash-flow statements (2009–15: XBRL DepreciationDepletionAndAmortization, as first filed; FY2006–08: 10-K reconciliation of net income to cash from operations).',
    'e_pub': REL + 'pension-adjusted diluted EPS (Q4 2009 – Q1 2017 releases; continuing operations 2009–12), "EPS excluding tax reform" (Q4 2017), MTM-adjusted EPS (Q4 2018 onward; 2021 and 2023 from the following year\'s comparatives).',
    'cf_ni': REL + 'condensed consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = FY − 9M). 2009–15 direct-method statements: D&A, stock-based compensation, deferred taxes and retiree benefits from XBRL (10-K / 10-Q, as first filed).',
    'bs_cash': REL + 'condensed consolidated statements of financial position (period ends). Current portion of long-term debt (inside other current liabilities from 2013) from XBRL LongTermDebtCurrent; shares outstanding from XBRL CommonStockSharesOutstanding.',
    'sh_basic': REL + 'statements of earnings (weighted-average shares). No stock splits in the period.',
    'ds_total': 'Source: release balance sheets; FY2025 10-K Note 9 (maturities); Q3 2026 10-Q Note 8 (repayments Mar-2026, $3.0bn credit facility).',
    'dps': 'Source: XBRL CommonStockDividendsPerShareDeclared (10-Q / 10-K).',
}
CELL_COMMENTS = {}
def comments_setup():
    def rec_cmt(key, orig_key, lab):
        d = {}
        for col in COLS:
            if col.kind not in HISTK: continue
            p = pkey(col); x = DATA.get(p, {}).get('x', {})
            if x.get('cur_recast') and x.get(orig_key) is not None:
                d[col.c] = f'{lab} {p}: {x["cur_basis"]}. As originally reported: {x[orig_key]:,.0f}.'
        return d
    for s, title, code in SEG:
        CELL_COMMENTS[f'{s}_s'] = rec_cmt(f'{s}_s', f'orig_{s}_s', title + ' sales')
        CELL_COMMENTS[f'{s}_oi'] = rec_cmt(f'{s}_oi', f'orig_{s}_oi', title + ' operating income')
    for key, okey, lab in (('is_oi', 'orig_oi', 'Operating income'), ('is_ni', 'orig_ni', 'Net earnings'), ('is_nonop', 'orig_nonop_fas', 'Non-operating FAS pension benefit'), ('eps_pub', 'orig_eps_d', 'Diluted EPS')):
        d = {}
        for col in COLS:
            p = pkey(col) if col.kind in HISTK else None
            x = DATA.get(p, {}).get('x', {}) if p else {}
            if x.get('recast_mtm_2018') and x.get(okey) is not None:
                d[col.c] = f'{lab} {p} as recast in the Q4 2018 release (Schedule 6) for the mark-to-market pension accounting change adopted in Q4 2018. As originally reported: {x[okey]:,.2f}.'
        CELL_COMMENTS[key] = d
    CELL_COMMENTS['is_rev_py'] = {A[2008]: '2008 recast in the FY2009 10-K for the TASC sale (discontinued operations): $32,315m vs $33,887m as reported.',
                                  A[2010]: '2010 recast in the FY2011 10-K for the Shipbuilding spin-off (discontinued operations): $28,143m vs $34,757m as reported; 2009 $27,650m.',
                                  A[2017]: '2017 recast in the 2018 releases (ASC 606 full retrospective; ASU 2017-07; MTM): $26,004m vs $25,803m as reported.'}
    CELL_COMMENTS['is_othop'] = {A[2008]: 'Q4 2008 goodwill impairment $3,060m pre-tax (Aerospace $570m, Shipbuilding $2,490m), FY2008 10-K.'}
    CELL_COMMENTS['is_oth'] = {A[2010]: 'Includes a $231m charge on debt redemption (2010 10-K / Q4 2010 release).', A[2011]: 'Includes a $229m charge on debt redemption? — no: the 2011 figure contains no redemption charge; the Q4 2011 release row "(229" is the 2010 comparative (identity-closed).'}
    CELL_COMMENTS['is_oth'].pop(A[2011])
    CELL_COMMENTS['is_oth'][A[2010]] = 'Includes the $231m charge on debt redemption (Q4 2010 release; the Q4 2011 release restates it as $229m).'

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['rc_def'] = {
        'C': ('2006–08: Information & Services / Aerospace / Electronics / Ships (Shipbuilding from 2008); net pension adjustment = total FAS pension expense − CAS cost; royalty reversal',
              'Form 10-K segment notes. The 2008 goodwill impairment ($3,060m) sits in Aerospace ($570m) and Shipbuilding ($2,490m) segment operating income.'),
        A[2009]: ('2009–15: Aerospace / Electronic / Information / Shipbuilding (to Q1 2011) / Technical Services; TASC in discontinued operations from 2009', 'Realignment effective 1-Jan-2009; 2008 and 2007 recast in the FY2009 10-K (memo block as reported).'),
        A[2011]: ('2011: Shipbuilding spun off 31-Mar-2011 (discontinued operations); 2010 not recast in this column (memo row)', None),
        q(2013, 1): ('Quarterly columns begin; segment operating income and "Net FAS/CAS pension adjustment" as published in each release', None),
        A[2016]: ('2016–17: Aerospace / Mission / Technology Services (realignment 1-Jan-2016; 2015 recast in the FY2016 10-K)', None),
        q(2018, 1): ('2018: Innovation Systems from 6-Jun-2018; ASU 2017-07 → FAS/CAS service-cost only, non-service FAS below operating income; ASC 606; MTM adopted Q4 2018 (Q1–Q3 recast)',
                     'Q1–Q3 2018 figures are the recast of the Q4 2018 release Schedule 6 (MTM accounting change); the as-reported figures are in the cell comments.'),
        q(2019, 1): ('2019 on the 2020 four-sector structure (Aeronautics / Defense / Mission / Space; intangible amortization moved to unallocated) — recast in the 2020 releases',
                     'As reported, 2019 segments were Aerospace / Innovation / Mission / Technology Services (legacy memo block); segment operating income $3,909m as reported vs $3,978m recast.'),
        q(2020, 1): ('2020+: Aeronautics / Defense / Mission / Space Systems as reported; IT services sold 30-Jan-2021 (gain $1,980m in unallocated)', None),
        q(2023, 1): ('2023 as reported (the 2024 releases recast only Q3–Q4 for the 1-Jan-2024 Defense / Space realignment; FY2023 on later structures in the 10-K memo rows)', None),
        q(2024, 1): ('2024 as recast for the 1-Jan-2025 realignment (SSAS to Aeronautics) in the 2025 releases', 'As reported 2024: Aeronautics $12,030m, Defense $8,560m (memo rows).'),
        q(2025, 1): ('2025–26 as reported (1-Jan-2025 structure); training services sold Q2 2025 (gain $231m in unallocated)', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–08: no adjusted EPS published — adjusted = GAAP (flag)', None),
        A[2009]: ('2009–12: "pension-adjusted diluted EPS from continuing operations" (excludes the net FAS/CAS pension adjustment after tax at 35%)', 'Published in the fourth-quarter releases (2009 and 2011 from the following year\'s comparatives).'),
        q(2013, 1): ('2013–Q1 2017: "pension-adjusted diluted EPS" (net earnings basis)', None),
        q(2017, 2): ('Q2–Q3 2017: not published — adjusted = GAAP (flag); Q4 / FY2017: EPS excluding the impact of tax reform and the related discretionary pension contribution', None),
        q(2018, 1): ('2018+: "MTM-adjusted EPS" (excludes the Q4 MTM (benefit) expense net of federal and deferred state tax); interim quarters have no MTM → = diluted EPS', None),
        A[2021]: ('2021: MTM-adjusted EPS $32.59 (comparative in the Q4 2022 release); the Q4 2021 release headlined "transaction-adjusted EPS" $25.63 (also excl. the IT services gain)', None),
    }
    DEFS['r_def'] = {
        'C': ('Model definition throughout: EBITDA = operating income + D&A; adjusted EBITDA adds back the 2008 goodwill impairment, gains / costs on business sales (2021, 2025) and the B-21 loss provisions (Q4 2023, Q1 2025)', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: 2026 sales and segment-operating-income guidance end-points (high / mid / low), '
            'Q4/26E buybacks, 2027E–2031E segment sales growth and margins, eliminations %, book-to-bill, M&A spend, the minimum buyback and the leverage target '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'Northrop Grumman Corporation (NYSE: NOC) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Calendar fiscal year · Source: Northrop Grumman Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99 / 99.1), '
                'SEC EDGAR (CIK 0001133421); XBRL company facts; the investor-relations releases at northropgrumman.com are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: consolidated statements as originally reported (Q1–Q3 2018 as recast in the Q4 2018 release for the MTM pension accounting change; 2008 / 2010 / 2017 restatements in memo rows). '
                'Segments: current four-sector structure on the latest consistent presentation (2019 and 2024 recast; 2023 as reported), legacy structures as memo. '
                'Shipbuilding spun off 31-Mar-2011 (HII); Orbital ATK acquired 6-Jun-2018; IT services sold 30-Jan-2021; training services sold Q2 2025. Q4/26E calibrated to the 2026 sales and segment-operating-income guidance (20-Oct-2026).')
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
        p = os.path.join(BASE, f'NOC_{scen}.xlsx')
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
    p = os.path.join(BASE, 'NOC_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
