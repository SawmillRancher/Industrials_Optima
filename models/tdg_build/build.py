"""Build TDG_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'TDG_Model.xlsx')
G27 = MAN['guidance_fy27']

# ====================================================================== inputs (V0)
P_I_REV = 390.0                      # P&I expected calendar-2026 revenue (8-K 28-Sep-2026), used for pro forma working-capital ratios
def wc_inputs():
    q = DATA['2026']['x']
    pf = (q['rev'] + P_I_REV) / q['rev']          # P&I closed 28-Sep-2026: its balances are in the 30-Sep-2026 BS but not its sales
    rev, cogs = q['rev'] * pf, q['cogs'] * pf
    return {'dso': round(q['bs_ar'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365), 'dpo': round(q['bs_ap'] / cogs * 365),
            'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at fiscal-year-end (30-Sep-2026) levels on FY2026 net sales / cost of sales grossed up for a full year of P&I (~$390m, closed 28-Sep-2026; '
              f'pro forma, so the acquired balances are not mistaken for working-capital growth): DSO {WC["dso"]}d, inventory {WC["dio"]}d, payables {WC["dpo"]}d, '
              f'accrued & other {WC["ocl"]:.1%} of net sales.')
AM = MAN['amort_sched']
DEBT = MAN['debt']

V0 = {
    'out_hdr': 'FY27 guidance — Q4 FY26 release (10-Nov-2026)',
    'out_note': ('Net sales $11,950–12,150m, EBITDA As Defined $6,195–6,345m (~52.0% margin), net income $2,442–2,490m, EPS $42.06–42.91 and adjusted EPS $47.09–47.94 on 56.7m shares; '
                 'commercial OEM growth high single to low double digits, commercial aftermarket and defense high single digits. Market growth ranges read as organic (model interpretation).'),
    'outlook': [
        ('out_sales', '  FY27 net sales ($m)', tuple(G27['sales']), 'm', 'Guided $11,950–12,150m (+14% at the midpoint). Drives the sales calibration.'),
        ('out_ebitda', '  FY27 EBITDA As Defined ($m)', tuple(G27['ebitda_ad']), 'm', 'Guided $6,195–6,345m. Drives the segment-margin calibration.'),
        ('out_coem', '  FY27 commercial OEM market growth', (0.12, 0.10, 0.08), 'pct', 'Guided "high single-digit to low double-digit percentage range" — model reading 8% / 10% / 12% (EDGAR text; numeric reading is an assumption).'),
        ('out_caft', '  FY27 commercial aftermarket market growth', (0.09, 0.08, 0.07), 'pct', 'Guided "high single-digit percentage range" — model reading 7% / 8% / 9%.'),
        ('out_def', '  FY27 defense market growth', (0.09, 0.08, 0.07), 'pct', 'Guided "high single-digit percentage range" — model reading 7% / 8% / 9%.'),
        ('out_adjeps', '  FY27 adjusted EPS ($) — memo', tuple(G27['adj_eps']), 'ps', 'Guided $47.09–47.94 (information row; compare the model).'),
        ('out_eps', '  FY27 GAAP EPS ($) — memo', tuple(G27['eps']), 'ps', 'Guided $42.06–42.91 on 56.7m weighted shares (information row).'),
        ('out_ni', '  FY27 net income ($m) — memo', tuple(G27['ni']), 'm', 'Guided $2,442–2,490m (information row).'),
        ('bb27', '  FY27E share repurchases ($m)', (3000.0, 2000.0, 1000.0), 'm', 'Not guided (guidance holds 56.7m shares). $3,038m remained on the program at 30-Sep-2026; FY2026 repurchases $2,750m. Scenario input, spread evenly by quarter.'),
    ],
    'points': [
        ('pt_int', '  Interest expense — net, per quarter ($m)', G27['mid_int'] / 4, 'm1', 'Guidance midpoint $2,255m ÷ 4 (Q4 FY26 $536m).'),
        ('pt_amort', '  Amortization of intangible assets, per quarter ($m)', AM['2027'] / 4, 'm1', 'FY2026 10-K estimated amortization FY27 $294m ÷ 4.'),
        ('pt_dep', '  Depreciation & other amortization, per quarter ($m)', (G27['mid_dda'] - AM['2027']) / 4, 'm1', 'Guided D&A $525m − $294m intangible amortization, ÷ 4.'),
        ('pt_acq', '  Acquisition & integration expenses, per quarter ($m)', G27['mid_acq'] / 4, 'm1', 'Guidance midpoint $42m ÷ 4.'),
        ('pt_sbc', '  Non-cash stock & deferred compensation, per quarter ($m)', G27['mid_sbc'] / 4, 'm1', 'Guidance midpoint $225m ÷ 4.'),
        ('pt_other', '  Other, net adjusting items, per quarter ($m)', G27['mid_other'] / 4, 'm1', 'Guidance midpoint $16m ÷ 4.'),
        ('pt_backlog', '  Purchase-accounting backlog amortization, per quarter ($m)', 4.0, 'm1', 'Not guided; P&I backlog $12m over one year + other recent deals (assumption, FY26 $27m).'),
        ('pt_etr', '  Effective tax rate', round(G27['mid_tax'] / (G27['ni'][1] + G27['mid_tax']), 4), 'pct',
         'Guidance midpoint tax $741m on pre-tax income $3,207m.'),
        ('pt_nci', '  Net income attributable to NCI, per quarter ($m)', 1.0, 'm1', 'FY2026 $1m; redeemable NCI in JPE / VSA / P&I (assumption).'),
        ('pt_na_g', '  Non-aviation net sales growth (y/y)', 0.05, 'pct', 'Not guided; FY2026 +13%, FY2022–25 −3% to +4% (assumption).'),
        ('pt_corp', '  Unallocated corporate % of net sales', 0.0105, 'pct', 'FY2026 1.07%.'),
    ],
    'acq27': {1: 197.5, 2: 192.5, 3: 112.5, 4: 107.5},
    'acq27_note': ('Assumption from EDGAR revenue disclosures: P&I ~$390m calendar-2026 revenue (8-K 28-Sep-2026; closed 28-Sep-2026) ≈ $97.5m a quarter in all four quarters; '
                   'JPE / VSA ~$280m calendar-2025 revenue (closed 7-Apr-2026) ≈ $75m a quarter in Q1–Q2/27E until the anniversary; FY2026 bolt-ons ($434m of spend) $25m / $20m / $15m / $10m. '
                   'Simmonds (closed 6-Oct-2025) has anniversaried. All in Power & Control (10-K Note 2).'),
    'acq27_al': {'coem': 0.15, 'caft': 0.65, 'def': 0.20},
    'divq1': 54.0,
    'lev': (6.25, 5.75, 5.0),
    'lev_note': ('Net debt $32.5bn at 30-Sep-2026 ≈ 5.8x FY2026 EBITDA As Defined (FY2020–26 range ~5.5–7.5x). TransDigm varies leverage "to optimize equity return"; '
                 'capacity up to the target is returned as special dividends / buybacks (2028E+). Bull = more capital returned (higher target).'),
    'blocks': [
        ('COEM', 'COEM (Commercial OEM y/y, both segments)', 0.03, -0.05, [0.09, 0.08, 0.07, 0.06],
         'FY2026 +16% (P&C +22%, Airframe +13%) with OEM build-rate increases; FY27 guide HSD–LDD. Normalising toward mid-single digits as 737 / A320 / 787 rates plateau (assumption).', 'pct', False),
        ('CAFT', 'CAFT (Commercial aftermarket y/y, both segments)', 0.02, -0.05, [0.07, 0.065, 0.06, 0.06],
         'FY2026 +23% incl. JPE / VSA; organic Q3–Q4 FY26 +17% / mid-teens; FY27 guide HSD. Long-run growth ~ revenue passenger miles + price (assumption).', 'pct', False),
        ('DEF', 'DEF (Defense y/y, both segments)', 0.02, -0.04, [0.06, 0.055, 0.05, 0.05],
         'FY2026 +20% incl. Simmonds; FY27 guide HSD; sizeable defense backlog built in FY2026 (Q3 FY26 release).', 'pct', False),
        ('NA_G', 'NA_G (Non-aviation net sales y/y)', 0.01, -0.03, [0.03, 0.03, 0.03, 0.03], 'FY2022–26 −3% to +13%; ~2% of sales.', 'pct', False),
        ('PC_M', 'PC_M (Power & Control EBITDA As Defined margin)', 0.01, -0.02, [0.540, 0.545, 0.550, 0.553],
         'FY2026 53.7% (FY2024–25 56.8–56.9% before the dilutive Simmonds / JPE / VSA / P&I deals); recovery as acquisitions are integrated (TransDigm value-driver playbook).', 'pct', False),
        ('AF_M', 'AF_M (Airframe EBITDA As Defined margin)', 0.01, -0.02, [0.550, 0.555, 0.560, 0.563],
         'FY2026 54.3% (FY2023 50.0%, FY2025 53.7%): steady expansion from price and mix.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 1000.0, -1000.0, [1500.0, 1500.0, 1500.0, 1500.0],
         'TransDigm spent $0.4–4.4bn a year on acquisitions in FY2023–26 ($4.4bn in FY2026). Base $1.5bn p.a. (assumption).', 'm', True),
    ],
    'na_m': 0.44, 'corp_pct': 0.0105,
    'dep_pct': {2028: 0.019, 2029: 0.019, 2030: 0.019, 2031: 0.019},
    'sga_pct': {2028: 0.110, 2029: 0.108, 2030: 0.107, 2031: 0.106},
    'sbc_pct': 0.019, 'etr': 0.23, 'nci_ae': 4.0,
    'backlog_ae': {2028: 4.0, 2029: 0.0, 2030: 0.0, 2031: 0.0},
    'amort_sched': {2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: AM['2031']},
    'amort_note': AM['src'] + ' FY27 $294m, FY28 $271m, FY29 $265m, FY30 $262m, FY31 $253m.',
    'capex_pct': 0.025, 'def_ae': 0.0, 'stock_ae': 150.0, 'iss_ae': 0.5, 'amdebt': 45.0,
    'part': 1.6, 'partp': 0.028, 'spd': 0.5,
    'mna27': 240.0, 'm_mult': 3.5, 'm_m': 0.40,
    'm_mult_note': ('FY2026 deals: Simmonds $757m on ~$350m revenue (2.2x), JPE / VSA $2,142m on ~$280m (7.7x), P&I $1,058m on ~$390m (2.7x); withdrawn Stellant $960m on ~$300m (3.2x). '
                    '3.5x input (assumption).'),
    'mna_note': ('Scenario lever M&A_spend 2028E+ (Base $1.5bn p.a.). FY2027E: Extant Aerospace asset purchase ~$240m (8-K 21-Sep-2026, close expected FY27; revenue not disclosed, '
                 'revenue modelled from FY2028E at the EV/sales input). Funded from cash / incremental borrowings (debt schedule).'),
    'refi': {2027: 0.0, 2028: 269.0, 2029: 4700.0, 2030: 3394.0, 2031: 4926.0},
    'repay': {2027: 130.0, 2028: 399.0, 2029: 4830.0, 2030: 3524.0, 2031: 5056.0},
    'mat': {2027: 399.0, 2028: 4830.0, 2029: 3524.0, 2030: 5056.0, 2031: 130.0},
    'min_cash': 1500.0,
    'r_notes': {2027: 0.069, 2028: 0.069, 2029: 0.070, 2030: 0.070, 2031: 0.070},
    'r_notes_note': ('Calibrated to FY27 guided interest expense — net ($2,255m) + ~$84m interest income on opening cash ⇒ ~6.9% of the $33.9bn opening carrying debt '
                     '(notes 6.36% weighted coupon; term loans SOFR + 2.25–2.50%, ~75% fixed via swaps / collars; includes amortization of issuance costs). '
                     'Rising to 7.0% as the 4.625% / 4.875% 2029 notes are refinanced at ~6.75% (assumption).'),
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $1,208.04 = exercise price of stock options granted 3-Nov-2026 at market (Forms 4 filed 5-Nov-2026) — the latest share price '
                'in an SEC filing (~$68bn market cap); update to market'),
    'rev_guid_note': 'Company FY27 net sales guidance $11,950–12,150m (issued 10-Nov-2026). Drives the sales calibration; the M&A lever is outside the guidance basis.',
    'eb_guid_note': 'Company FY27 EBITDA As Defined guidance $6,195–6,345m (~52.0% margin). Drives the segment-margin calibration.',
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
def pick_in(v, col):
    if isinstance(v, dict): return v.get(col.year) if col.q is None else v.get(col.q)
    return v

def compute(row, col):
    kw = row.kw; k = col.kind
    CTX.col = col
    if kw.get('ann') and col.q: return None, False
    if k in HISTK:
        if k == 'A' and col.year == FYA:
            if 'a26_in' in kw: return kw['a26_in'], True
            if 'a26' in kw: return kw['a26'](), False
        v = hist_value(row, col)
        if v is not None: return v, True
        for key in ('hist', 'all'):
            if key in kw: return kw[key](), False
        return None, False
    if k == 'QE':
        if row.spec2: return None, False
        if 'qe_in' in kw:
            v = pick_in(kw['qe_in'], col); return (v, True) if v is not None else (None, False)
        key = first(kw, ('qe', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'E27':
        if 'e27_in' in kw: return kw['e27_in'], True
        if 'e27' in kw: return kw['e27'](), False
        if row.spec2:
            if row.key.startswith('lev_'): return None, False
            if 'ae_in' in kw:
                v = pick_in(kw['ae_in'], col)
                if v is not None: return v, True
            if 'ae' in kw: return kw['ae'](), False
            if 'fc_in' in kw:
                v = pick_in(kw['fc_in'], col); return (v, True) if v is not None else (None, False)
            key = first(kw, ('fc', 'all'))
            return (kw[key](), False) if key else (None, False)
        if kw.get('avg') and ('qe' in kw or 'qe_in' in kw): return f'=AVERAGE({Q1}{row.r}:{QE4}{row.r})', False
        if kw.get('flow') and any(x in kw for x in ('qe', 'qe_in', 'fc')): return S27(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = pick_in(kw['ae_in'], col); return (v, True) if v is not None else (None, False)
        if 'ae' in kw: return kw['ae'](), False
        if 'fc_in' in kw:
            v = pick_in(kw['fc_in'], col); return (v, True) if v is not None else (None, False)
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'pc_rev', 'af_rev', 'na_rev', 'pc_coem', 'pc_caft', 'pc_def', 'af_coem', 'af_caft', 'af_def', 'mx_coem', 'mx_caft', 'mx_def', 'mx_aero',
          'g_eb', 'r_ad', 'r_ebitda', 'is_oi', 'd_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'sh_d', 'is_gp', 'is_sga',
          'd_amort', 'd_dep', 'pc_eb', 'af_eb', 'is_ni', 'eps_d', 'is_int', 'ds_total'}
CAGR_A = {'pc_m', 'af_m', 'na_m', 'g_ebm', 'r_ad_m', 'is_gm', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_pc', 'gm_af', 'gm_gm', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_sga', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'lv_x', 'org_g', 'acq_g',
          'd_sga', 'd_dep_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'corp_pct', 'pc_aft', 'af_aft', 'mx_coem_p', 'mx_caft_p', 'mx_def_p', 'gm_int'}
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

REL = 'Source: TransDigm earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'pc_coem': ('Source: TransDigm Forms 10-Q / 10-K segment note, "net sales to external customers" by end market (published from the FY2019 10-K with FY2017–18 comparatives and '
                'quarterly from Q1 FY2019; FY2018 quarters from the FY2019 10-Q comparatives). Each period from the latest filing presenting it (the following fiscal year\'s 10-Q / 10-K), '
                'so the FY2020 allocation of the FY2019 Esterline businesses to end markets is applied consistently. Labels "commercial OEM / aftermarket" became '
                '"commercial and non-aerospace OEM / aftermarket" in FY2025. Q4 = fiscal year (10-K) − three quarters.'),
    'pc_rev': ('Source: Forms 10-Q / 10-K segment note (three segments from Q3 FY2013; FY2011–12 annual from the FY2013 10-K and Q1–Q2 FY2013 from the FY2014 10-Q comparatives). '
               'FY2017 segment sales reflect the FY2018 reclassification of a business from Power & Control to Non-aviation (FY2018 10-K comparatives).'),
    'pc_eb': 'Source: Forms 10-Q / 10-K segment note, EBITDA As Defined by segment (latest filing presenting the period). In Q2–Q3 FY2019 Esterline was a separate fourth segment, allocated in the FY2020 comparatives used here.',
    'corp': 'Source: segment note, "unallocated corporate expenses" / "unallocated corporate EBITDA As Defined".',
    'org_sales': 'Source: 10-Q / 10-K MD&A, "net organic sales and acquisition sales" table (from FY2012).',
    'is_rev': REL + 'consolidated statements of income, as originally reported (later reclassifications to discontinued operations are not recast; see the Group basis row).',
    'd_dda': REL + 'Reconciliation of EBITDA, EBITDA As Defined to Net Income ("depreciation and amortization expense").',
    'r_ebitda_pub': REL + 'Reconciliation of EBITDA, EBITDA As Defined to Net Income (published throughout; labelled "EBITDA, excluding discontinued operations" in FY2011–12).',
    'r_ad_pub': REL + 'EBITDA As Defined (published throughout; FY2006–07 releases also showed an "Adjusted EBITDA As Defined" including IPO costs).',
    'e_pub': REL + 'Reconciliation of Reported Earnings per Share to Adjusted Earnings per Share (adjusted EPS under the two-class method).',
    'cf_ni': ('Source: 10-Q / 10-K consolidated statements of cash flows (year to date; discrete quarters derived, Q4 = fiscal year − nine months). '
              'Cash includes restricted cash from FY2019 (ASU 2016-18).'),
    'bs_cash': 'Source: 10-Q / 10-K consolidated balance sheets (period ends); common shares outstanding = shares issued − treasury shares (equity captions).',
    'ppa_cons': 'Source: FY2026 10-K Note 2 (acquisitions): consideration net of cash acquired, goodwill and other intangible assets by deal.',
    'sh_d': REL + 'statements of income / two-class EPS table (weighted average shares; vested options deemed participating securities). No stock splits since the March 2006 IPO.',
    'ds_total': 'Source: 10-Q / 10-K balance sheets; FY2026 10-K Note 10 (debt) and Liquidity section; 8-Ks of 13-Feb-2026, 17-Apr-2026 and 29-Sep-2026 (financings).',
    'e_cont': REL + 'Reconciliation of Reported EPS to Adjusted EPS (adjusted net income block).',
}
CELL_COMMENTS = {}
def comments_setup():
    CELL_COMMENTS['r_oadj'] = {A[2006]: 'FY2006: the release row "Non-Recurring IPO Costs (6)" prints three cells for four columns; the $2.650m belongs to the fifty-two-week 2006 column '
                                         '(Gross Adjustments $60.159m = other items $57.509m + $2.650m). Re-aligned in extraction (manual_items.json).'}
    CELL_COMMENTS['is_tax'] = {A[2016]: 'FY2016 as reported in the Q4 FY16 release: ASU 2016-09 early-adopted retroactive to 1-Oct-2015 (excess tax benefits through the tax provision); '
                                        'Q1–Q3 FY2016 as first reported are pre-adoption, so the quarters do not sum to the year ($37.6m).',
                               A[2018]: 'FY2018 includes the US tax reform (TCJA) remeasurement benefit (deferred tax liabilities).'}
    CELL_COMMENTS['is_rev'] = {A[2017]: 'FY2017 10-K / Q4 release present SCHROTH as discontinued operations; Q1–Q3 FY2017 as first reported include it (quarters sum to $14.5m more).',
                               A[2019]: 'FY2019 10-K presents Esterline businesses held for sale as discontinued operations; Q2–Q3 FY2019 as first reported include them (quarters sum to $165.7m more).'}
    CELL_COMMENTS['d_sbc'] = {A[2022]: 'FY2022 release: "Non-cash stock and deferred compensation expense" for the year includes deferred compensation previously in Other, net in the quarterly releases (Σ quarters $170m vs $184m; EBITDA As Defined itself sums).'}
    CELL_COMMENTS['org_sales'] = {QC[(2017, 4)].c: 'Not derived: the FY2017 10-K organic table is on the discontinued-operations basis, the quarters as first reported.',
                                  QC[(2019, 4)].c: 'Not derived: the FY2019 10-K organic table is on the discontinued-operations basis, the quarters as first reported.'}
    CELL_COMMENTS['g_basis'] = {QC[(2019, 3)].c: 'Q3 FY2019 segment data from the FY2020 10-Q comparatives exclude the Esterline businesses later presented as discontinued operations ($137m of sales).'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['r_def'] = {
        'C': ('FY2006–07: EBITDA As Defined = EBITDA + deferred / stock-option compensation, acquisition costs, refinancing costs, IPO-related option vesting, IPO costs, one-time special bonus',
              'FY2006–07 releases also show "Adjusted EBITDA As Defined"; the model ties to EBITDA As Defined (the measure in all later releases).'),
        A[2008]: ('FY2008–10: + write-down of PP&E held for sale, equity offering costs; integration and purchase-accounting adjustments added (FY2010)', None),
        A[2011]: ('FY2011–12: EBITDA excluding discontinued operations; acquisition-related expenses and adjustments; refinancing costs', None),
        A[2013]: ('FY2013+: acquisition-related costs, non-cash stock compensation, refinancing costs, other (non-recurring) items', None),
        q(2020, 2): ('Q2 FY2020–Q1 FY2022: COVID-19 / 737 MAX restructuring costs added back', None),
        A[2021]: ('FY2021–23: gain on sale of businesses adjusted out', None),
        q(2022, 1): ('FY2022+: "non-cash stock and deferred compensation expense" (deferred compensation moved from Other, net)', None),
        q(2026, 1): ('FY2026: acquisition transaction & integration expenses, non-cash stock & deferred compensation, refinancing costs, other, net', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006–09: adjusted net income = net income + gross adjustments to EBITDA (+ backlog amortization from FY2007) − tax adjustment; ÷ diluted shares', None),
        A[2010]: ('FY2010+: two-class method — adjusted EPS includes the dividend-equivalent payments deducted from GAAP EPS', None),
        A[2017]: ('FY2017–20: adjusted net income starts from income from continuing operations; excess tax benefits on option exercises excluded from the tax adjustment (from FY2017)', None),
        q(2021, 1): ('Q1 FY2021: adjusted EPS on the adjusted share basis (participating options included in a loss-to-common quarter)', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY27 net-sales, EBITDA As Defined and market-growth guidance end-points (high / mid / low), '
            'FY27E buybacks, 2028E–2031E end-market growth, segment margins, M&A spend and the leverage target for the 2028E+ capital return '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'TransDigm Group Incorporated (NYSE: TDG) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 30 September (2026 = Oct-2025 – Sep-2026; 13-week fiscal quarters) · '
                'Source: TransDigm Forms 10-K / 10-Q, Form 8-K earnings releases (Ex. 99.1) and deal / financing 8-Ks, SEC EDGAR (CIK 1260221); XBRL company facts; '
                'investor-relations releases at transdigm.com are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: income statement, bridges, BS and CF as originally reported; segments and end markets from the latest filing presenting the period (FY2017 Non-aviation '
                'reclassification, FY2019 Esterline allocation), basis difference shown in the Group block. Segments from FY2011, end markets from FY2017. Deals: Esterline Mar-19, '
                'Cobham Aero Connectivity Q2 FY21, CPI Electron Device Business Jun-24, Raptor Scientific Jul-24, Simmonds Oct-25, JPE / VSA Apr-26, P&I Sep-26; Extant asset purchase pending (FY27). '
                'FY27E quarters calibrated to the FY27 guidance (10-Nov-2026).')
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
    wid = {'A': 13.0, 'Q': 9.5703125, 'QE': 11.42578125, 'E27': 14.140625, 'AE': 13.0}
    for col in COLS:
        cd = ws.column_dimensions[col.c]; cd.width = wid[col.kind]
        if col.q and col.kind == 'Q':
            cd.outlineLevel = 1; cd.hidden = True
        elif col.q:
            cd.outlineLevel = 1
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
def recalc(path, timeout=900):
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
        p = os.path.join(BASE, f'TDG_{scen}.xlsx')
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
    p = os.path.join(BASE, 'TDG_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
