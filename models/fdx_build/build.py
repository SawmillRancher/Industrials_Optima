"""Build FDX_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'FDX_Model.xlsx')
G26 = MAN['guidance_cy26']
X25, X26 = DATA['CY2025']['x'], DATA['CQ3-26']['x']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = X25; rev = q['rev']
    return {'dso': round(q['bs_ar'] / rev * 365), 'ap': round(q['bs_ap'] / rev, 3), 'sal': round(q['bs_accsal'] / rev, 3),
            'ocl': round((q['bs_ocl'] - q['bs_disc_cl']) / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at calendar year-end (31-Dec-2025) levels on 2025 revenue (DSO {WC["dso"]}d; payables {WC["ap"]:.1%}, accrued salaries {WC["sal"]:.1%}, '
              f'accrued & other current liabilities {WC["ocl"]:.1%} of revenue, excl. liabilities of discontinued operations); year ends are compared with year ends '
              '(December receivables are seasonally high).')
HFS = MAN['supply_chain_sale']['held_for_sale_2026_09_30']

V0 = {
    'out_hdr': 'Calendar-2026 guidance — release of 28-Oct-2026 (SEC EDGAR, Form 8-K Ex. 99.1)',
    'out_note': ('Revenue growth ~12% (raised from ~11%); adjusted diluted EPS from continuing operations $18.00–18.60 (from $16.90–18.10); GAAP EPS $35.30–35.90; '
                 'effective tax rate ~22.5%; capital spending $3.9bn; pension contributions $475m. Verified on EDGAR. The "calendar 2029 financial targets" '
                 'mentioned in the filings are not quantified in any EDGAR exhibit and are not used.'),
    'outlook': [
        ('out_g', '  2026 revenue growth', (0.125, 0.12, 0.115), 'pct', 'Guided "~12%" (a point, not a range): Mid = 12.0%; High / Low ±0.5 pt are model bounds. Drives the Q4/26E volume calibration.'),
        ('out_eps', '  2026 adjusted EPS, continuing operations ($)', (G26['adj_eps'][1], round(sum(G26['adj_eps']) / 2, 2), G26['adj_eps'][0]), 'ps',
         'Guided $18.00–18.60. Drives the Q4/26E segment-margin calibration.'),
        ('out_geps', '  2026 GAAP EPS, continuing operations ($) — memo', (G26['gaap_eps_cont'][1], round(sum(G26['gaap_eps_cont']) / 2, 2), G26['gaap_eps_cont'][0]), 'ps',
         'Guided $35.30–35.90 before further MTM adjustments (information row; compare the model).'),
        ('bb26', '  Q4/26E share repurchases ($m)', (750.0, 500.0, 250.0), 'm',
         'ASSUMPTION. $2.0bn repurchased June–September 2026 (6.3m shares); $4.3bn left on the 2026 program; "will continue to be opportunistic".'),
    ],
    'points': [
        ('pt_int', '  Q4/26E interest, net ($m; expense −)', -75.0, 'm', 'Not guided. Q3/26 $(66)m after the July tender offers ($4.9bn repurchased) and the 14-Sep-2026 notes ($1.1bn + €2.0bn) — a full quarter of the new notes.'),
        ('pt_ret', '  Q4/26E other retirement plans income ($m)', 55.0, 'm', 'Q1/26 $56m, Q3/25 $52m, Q4/25 $55m (ex mark-to-market adjustments). No MTM adjustment is forecast (the company excludes it from guidance).'),
        ('pt_onop', '  Q4/26E other non-operating, net ($m)', -15.0, 'm', 'Assumption: Q1/26 $(14)m, Q4/25 $(10)m.'),
        ('pt_da', '  Q4/26E depreciation & amortization ($m)', 975.0, 'm', 'Q3/26 $967m, Q2/26 $978m.'),
        ('pt_etr', '  Q4/26E tax rate (adjusted)', G26['etr'], 'pct', 'Calendar-2026 effective tax rate guided ~22.5% (before MTM adjustments and the $263m FedEx Supply Chain deferred-tax benefit).'),
        ('pt_capex', '  2026 capital spending ($m, continuing operations)', G26['capex'], 'm', 'Guided $3.9bn (nine months $2,859m).'),
        ('pt_restr', '  2026 restructuring, exit and other costs ($m, full year)', G26['eps_bridge_usd_m']['restructuring_exit_other'], 'm',
         'Company outlook table: $579m for calendar 2026 (nine months $507m in the reconciliations) → Q4/26E = remainder.'),
    ],
    'lev': (1.25, 1.0, 0.75),
    'lev_note': ('Net debt ~$10.8bn at 30-Sep-2026 (debt $19.4bn − cash $8.0bn − FedEx Freight stake $3.3bn + $2.7bn tariff refunds held) ≈ 1.2x 2026E adjusted EBITDA; '
                 'company debt / adjusted EBITDA 1.9x (covenant 3.5x). Target = leverage up to which surplus cash is returned via buybacks ($4.3bn left on the 2026 program; '
                 'more assumes new authorizations). No leverage target is published — assumption. Bull = more buybacks (higher target).'),
    'blocks': [
        ('US_VOL', 'US_VOL (U.S. package average daily volume y/y)', 0.01, -0.02, [0.02, 0.02, 0.015, 0.015, 0.015],
         'Nine months 2026: U.S. priority and deferred ADV up low-to-mid single digits, ground up ~4–6% (see the build rows); 2025 +5.0% total U.S. domestic ADV. Applied to priority, deferred and ground.', 'pct', False),
        ('US_YLD', 'US_YLD (U.S. revenue per package y/y)', 0.005, -0.015, [0.035, 0.03, 0.025, 0.025, 0.025],
         'General rate increase 5.9% effective 4-Jan-2027 (release 28-Oct-2026); realised yield growth is lower after mix and discounts (2025 composite +2.8%; nine months 2026 higher with fuel surcharges).', 'pct', False),
        ('INTL_VOL', 'INTL_VOL (international package average daily volume y/y)', 0.01, -0.025, [0.015, 0.015, 0.015, 0.015, 0.015],
         'International export ADV roughly flat in 2025 (+0.4%) with a shift from priority to economy; international domestic −1.8%. Trade-policy sensitivity → wider Bear Δ.', 'pct', False),
        ('INTL_YLD', 'INTL_YLD (international revenue per package y/y)', 0.005, -0.015, [0.025, 0.02, 0.02, 0.02, 0.02],
         'Composite international package yield +2.6% in 2025; nine months 2026 higher on base yields, fuel surcharges and currency.', 'pct', False),
        ('US_M', 'US_M (Express U.S. Domestic adjusted operating margin)', 0.0075, -0.015, [0.090, 0.094, 0.097, 0.099, 0.100],
         'Adjusted margin 6.9% in 2024, 8.4% in 2025, ~8.7% in 2026E; Network 2.0 / one FedEx cost reductions. Base assumes continued expansion at a slowing pace (assumption; no company target is used).', 'pct', False),
        ('INTL_M', 'INTL_M (Express International adjusted operating margin)', 0.005, -0.015, [0.034, 0.038, 0.041, 0.043, 0.045],
         'Adjusted margin 2.9% in 2025 (Europe restructuring, trade-policy headwinds); nine months 2026 ~3.1%. Base assumes gradual recovery (assumption).', 'pct', False),
    ],
    'days_q4': G26['operating_days']['2026'][3], 'days': {2027: sum(G26['operating_days']['2027']), 2028: 255, 2029: 255, 2030: 255, 2031: 255},
    'ufrt_g': 0.02, 'uoth_g': 0.03, 'ifrt_g': 0.03, 'ioth_g': 0.03, 'corp_g': 0.02,
    'sc_share': 0.50,
    'sc_note': ('FedEx Supply Chain revenue is not disclosed (Corporate, other, and eliminations also holds FedEx Office, FedEx Dataworks and eliminations). 50% is an ASSUMPTION; '
                'it only shifts Q4/26E revenue between corporate and the segments, because total 2026 revenue is calibrated to the guidance.'),
    'corp_pct': -0.0035, 'da_pct': {2027: 0.0415, 2028: 0.041, 2029: 0.0405, 2030: 0.040, 2031: 0.040},
    'sbc_q4': 37.0, 'sbc_h1': 74.0, 'sbc_pct': 0.0017,
    'ret_ae': 220.0, 'onop_ae': -60.0, 'etr': 0.23, 'dps_q': MAN['dividend']['declared_2026_08_21'], 'dps_g': 0.05,
    'ae_restr': {2027: 300.0, 2028: 150.0, 2029: 0.0, 2030: 0.0, 2031: 0.0},
    'restr_note': ('Q4/26E = calendar-2026 outlook ($579m of restructuring, exit and other costs) − nine months. 2027E $300m and 2028E $150m are ASSUMPTIONS (Network 2.0, '
                   'Europe workforce plan, transition after the FedEx Freight spin-off); no multi-year amount is disclosed.'),
    'rev_guid_note': 'Company calendar-2026 revenue growth guidance ~12% (28-Oct-2026; previously ~11%). Drives the volume calibration.',
    'eps_guid_note': 'Company calendar-2026 adjusted diluted EPS guidance (continuing operations) $18.00–18.60 (28-Oct-2026). Drives the segment-margin calibration.',
    'iss_q4': 50.0, 'iss_ae': 300.0, 'ish_q4': 0.2, 'ish_ae': 1.2, 'dil': 2.8,
    'capex_pct': {2027: 0.042, 2028: 0.041, 2029: 0.040, 2030: 0.040, 2031: 0.040},
    'wc': WC, 'sc': {'proc': MAN['supply_chain_sale']['proceeds'], 'ca': HFS['current_assets'], 'nca': HFS['noncurrent_assets'], 'cl': HFS['current_liabilities'], 'ncl': HFS['noncurrent_liabilities']},
    'def_ae': 150.0, 'pens_q4': 75.0, 'pens_ae': 300.0,
    'tariff': {2026: MAN['tariff_refunds']['held_for_customers_2026_09_30'], 2027: 0.0},
    'iss_notes': {2027: 2051.0, 2028: 499.0, 2029: 2087.0, 2030: 2340.0, 2031: 1477.0},
    'repay': {2027: 2051.0, 2028: 499.0, 2029: 2087.0, 2030: 2340.0, 2031: 1477.0},
    'mat': {2026: 2051.0, 2027: 499.0, 2028: 2087.0, 2029: 2340.0, 2030: 1477.0, 2031: 168.0},
    'repay_note': ('2027E: current portion of long-term debt at 30-Sep-2026 ($2,051m, incl. the €1.25bn 1.625% notes due January 2027 and current finance leases). 2028E–2031E: '
                   'FY2026 Form 10-K debt table by (old) fiscal year of maturity — 2028 $499m, 2029 $2,087m, 2030 $2,340m, 2031 $1,985m less $508m of 2.40% notes due 2031 '
                   'repurchased in the July-2026 tender. ASSUMPTION: each fiscal-year bucket is repaid in the same-numbered calendar year and refinanced (input row above).'),
    'min_cash': 4000.0,
    'r_notes': {2027: 0.039, 2028: 0.040, 2029: 0.041, 2030: 0.042, 2031: 0.043},
    'r_notes_note': ('Weighted-average rate on long-term debt 3.75% at 30-Sep-2026 (Form 10-Q); drifting up as low-coupon euro notes (0.45–1.625%) are refinanced near 5% '
                     '(14-Sep-2026 issues: 5.75% USD 2036, 4.00% / 4.625% EUR).'),
    'r_cash': 0.04,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $300.00, provided by the user on 20-Nov-2026 (~$70bn market cap). Latest SEC-filed reference: $293.07 average price paid for '
                'shares repurchased in September 2026 (Form 10-Q, Part II Item 2). Update to market.'),
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
    if kw.get('basis') and k in HISTK and col.basis != kw['basis']: return None, False
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
CAGR_G = {'is_rev', 'g_rev', 'usd_rev', 'intl_rev', 'r_pri', 'r_def', 'r_gnd', 'r_ip', 'r_ie', 'r_id', 'adv_pri', 'adv_def', 'adv_gnd', 'adv_ip', 'adv_ie', 'adv_id',
          'y_pri', 'y_def', 'y_gnd', 'y_ip', 'y_ie', 'y_id', 'usd_adj', 'intl_adj', 'g_adj', 'o_adj', 'r_adj', 'r_ebitda', 'is_oi', 'is_da', 'e_adjni', 'e_eps',
          'cf_cfo', 'fcf', 'bs_ta', 'bs_eq', 'sh_dil', 'is_ni', 'is_nic', 'eps_dil', 'eps_cont', 'dps', 'is_sal', 'is_pt', 'is_fuel'}
CAGR_A = {'usd_m', 'intl_m', 'g_adjm', 'o_adj_m', 'r_adj_m', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_usd', 'gm_intl', 'gm_ebitda_m', 'gm_op_m', 'gm_net_m', 'gm_adjop_m',
          'gm_sal', 'gm_pt', 'gm_fuel', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'c_sal', 'c_pt', 'c_rent', 'c_fuel', 'c_maint', 'c_da',
          'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'e_rate', 'corp_pct'}
A = {y: ANN[y].c for y in ANN}
LA = {y: LANN[y].c for y in LANN}

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
                if t: comment(cell, f'Company items ({col.label}): {t}', 380, 110)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    rc = CELL_COMMENTS.get(row.key, {})
    for c, t in rc.items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2031]}{r}/{A[2026]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({LA[2026]}{r}/{LA[2021]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({LA[2026]}{r}/{LA[2016]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({LA[2026]}{r}/{LA[2006]}{r})^(1/20)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{LA[y]}{r}" for y in range(2022, 2027))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{LA[y]}{r}" for y in range(2017, 2027))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{LA[y]}{r}" for y in range(2007, 2027))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: FedEx earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
RECAST = ('Calendar basis: recast exhibits "Supplemental Historical Financial Information" (Form 8-K Ex. 99.1 of 21-Jul-2026 for 2024–2025 and of 28-Oct-2026 for Q1–Q2/26) '
          'and the release of 28-Oct-2026 (Q3/26).')
LABEL_SOURCES = {
    'adv_pri': (REL + 'segment operating statistics. Legacy columns: FedEx Express "Total U.S. Overnight Package" to FY2024 (box + envelope summed for FY2006–FY2012, where no '
                'total is printed) and Federal Express "U.S. priority" in FY2025–26, as originally reported. ' + RECAST),
    'adv_gnd': ('Legacy columns: FedEx Ground segment average daily package volume as published (FedEx Ground + FedEx SmartPost summed where shown separately, FY2008–FY2015; '
                'ground commercial + home delivery + economy from FY2022, with home delivery / economy on a 7-day basis) — definitions changed over time; Federal Express '
                '"U.S. ground commercial + home delivery / economy" in FY2025–26. ' + RECAST),
    'y_gnd': 'Legacy columns: FedEx Ground composite yield only where one figure was published (FY2007, FY2016–FY2026); blank where FedEx Ground and SmartPost yields were shown separately.',
    'usd_adj': 'Source: non-GAAP reconciliation tables of the recast exhibits and the 28-Oct-2026 release (segment "Non-GAAP measure").',
    'corp_rev': RECAST + ' "Corporate, other, and eliminations" = FedEx Office, FedEx Dataworks, FedEx Supply Chain (sold 1-Oct-2026) and eliminations.',
    'ls_exp': REL + 'consolidated financial highlights (revenue and operating income by segment), fiscal years ended 31 May, as originally reported.',
    'lf_ship': REL + 'FedEx Freight segment operating statistics (LTL shipments per day; composite weight, revenue per hundredweight and per shipment).',
    'is_rev': (REL + 'condensed consolidated statements of income. Legacy columns as originally reported (not recast for the FY2015 change to mark-to-market pension accounting, '
               'ASU 2017-07 in FY2019 or ASC 842 in FY2020). ' + RECAST),
    'o_pub': REL + '"Reconciliations of non-GAAP financial measures to GAAP financial measures" (consolidated table for the period).',
    'e_pub': REL + 'reconciliations of non-GAAP financial measures (net income and diluted EPS columns).',
    'cf_ni': (REL + 'condensed consolidated statements of cash flows (year to date; legacy quarters derived, Q4 = FY − nine months). FY2023 from the Form 10-K (operating cash flow '
              '$8,848m vs $8,815m in the release). Q3 FY2015 effect of exchange rates corrected to $(104)m per the Form 10-Q (release typo +104).'),
    'bs_cash': (REL + 'condensed consolidated balance sheets. FY2016 from the Form 10-K (the Q4 FY16 release printed no balance sheet); FY2023 and FY2025 from the Form 10-K '
                '(differ from the release). Calendar basis: 31-Dec-2024 / 2025 recast (21-Jul-2026 exhibit) and 30-Sep-2026 (release; current debt and leases from the Form 10-Q).'),
    'sh_basic': 'Source: XBRL company facts (weighted average basic shares, as first filed in the Form 10-K / 10-Q).',
    'd_sbc': 'Source: XBRL company facts (ShareBasedCompensation, fiscal years; AllocatedShareBasedCompensationExpense for quarters where tagged).',
    'dps': 'Source: XBRL company facts (CommonStockDividendsPerShareDeclared; fiscal Q4 = year − nine months); FY2006–FY2010 from the Form 10-K statements of changes in stockholders\' investment; calendar basis: dividends declared per share in the recast income statements.',
    'ds_total': 'Source: balance sheets; FY2026 Form 10-K debt note (maturities); Form 10-Q for the quarter ended 30-Sep-2026, Note 5 (tender offers of 14-Jul-2026, notes of 14-Sep-2026, credit agreements).',
    'sc_proc': 'Source: Form 10-Q for the quarter ended 30-Sep-2026, Note 1 (held for sale) and Note 14 (subsequent events).',
}
CELL_COMMENTS = {}
def comments_setup():
    der = 'Derived: net income ÷ diluted EPS (the recast exhibit prints no share count).'
    CELL_COMMENTS['sh_dil'] = {c.c: der for c in COLS if c.basis == 'C' and c.kind in HISTK and xget(pkey(c), 'sh_d_derived')}
    n9 = ('Nine months ended 30 September (year to date) — the only calendar-basis cash-flow statement published; not recast for discontinued operations '
          '(includes FedEx Freight to 31-May-2026). Not a discrete quarter.')
    for k in ('cf_ni', 'cf_cfo', 'cf_cfi', 'cf_cff', 'fcf'):
        CELL_COMMENTS[k] = {QC[(2025, 3)].c: n9, QC[(2026, 3)].c: n9}
    CELL_COMMENTS['cf_fx'] = {LQC[(2015, 3)].c: 'Correction: the Q3 FY2015 release prints +104 for the nine months; the arithmetic of the statement and the Form 10-Q give (104). Discrete Q3 derived from the corrected figure.'}
    CELL_COMMENTS['bs_cash'] = {LANN[2016].c: 'FY2016 Form 10-K (the Q4 FY16 release printed no balance sheet).', LQC[(2016, 4)].c: 'FY2016 Form 10-K (the Q4 FY16 release printed no balance sheet).',
                                LANN[2023].c: 'FY2023 Form 10-K: $6,856m (the Q4 FY23 release showed $6,823m; the 10-K wins).'}
    CELL_COMMENTS['bs_ta_pub'] = {LANN[2025].c: 'FY2025 Form 10-K: $87,627m (the Q4 FY25 release showed $87,663m; the 10-K wins).'}
    CELL_COMMENTS['bs_std'] = {QC[(2026, 3)].c: MAN['bs_detail']['CQ3-26']['note']}
    CELL_COMMENTS['is_oi'] = {LANN[2015].c: 'FY2015 as reported in the Q4 FY15 release, after the change to mark-to-market pension accounting ($2.19bn MTM loss in Q4). Q1–Q3 FY15 are as originally '
                                            'reported on the previous basis, so the quarters do not sum to the year (documented exception).'}
    CELL_COMMENTS['is_sal'] = {LANN[2013].c: 'FY2013 total per the Q4 FY13 release; the quarters as first reported sum to $8m more (reclassification between cost lines).'}
    CELL_COMMENTS['is_onop'] = {QC[(2026, 2)].c: 'Includes the ~$4.5bn fair-value gain on the retained FedEx Freight stake in June 2026 (shown inside "Other nonoperating, net" in the recast exhibit).',
                                QC[(2026, 3)].c: 'Includes the $627m gain on extinguishment of debt (July-2026 tender offers) and other retirement plans income (one line in the release).'}
    CELL_COMMENTS['adv_gnd'] = {LQC[(2022, 1)].c: 'From Q1 FY22: ground commercial + home delivery + economy, with home delivery / economy average daily volume on a 7-day-per-week basis (definition change).'}

DEFS = {}
def defs_setup():
    lq = lambda y, n: LQC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2006–FY2011: no reconciliation tables in the releases — adjusted = GAAP (n/p)', 'Items such as the FY2008–FY2009 impairment charges were discussed in the release text only.'),
        LANN[2012].c: ('FY2012–FY2014: aircraft impairment, business realignment (voluntary buyout), legal reserve — tables in Q4 releases only; quarters n/p', None),
        lq(2015, 4): ('Q4 FY15+: MTM pension adjustment (in operating income to FY2018), aircraft impairment, legal matters; segment reporting change', None),
        lq(2016, 2): ('FY2016–FY2022: TNT Express / GENCO acquisition & integration expenses, legal matters, MTM adjustment, business realignment (FY2019+)', None),
        lq(2019, 1): ('FY2019+: MTM adjustment moves below operating income (ASU 2017-07) — non-operating item in the EPS bridge', None),
        lq(2023, 1): ('FY2023+: business optimization (DRIVE, Network 2.0), FedEx Ground legal matters, impairments', None),
        lq(2026, 1): ('FY2026: FedEx Freight spin-off costs, fiscal-year-change costs', None),
        QC[(2024, 1)].c: ('Calendar basis (continuing operations): business optimization and realignment, fiscal-year change, impairments, legal / regulatory matters', None),
        QC[(2026, 1)].c: ('2026: "Restructuring, exit and other costs" (one line; incl. spin-off and fiscal-year-change costs)', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2006–FY2011: no adjusted EPS tables — adjusted = GAAP (n/p); legacy EPS includes FedEx Freight', None),
        LANN[2012].c: ('FY2012–FY2015: items net of tax (4-column tables) — tax effect = pre-tax − after-tax', None),
        lq(2016, 4): ('Q4 FY16+: income-tax column published; discrete tax items (TNT restructuring, TCJA FY2018–19) adjusted', None),
        QC[(2024, 1)].c: ('Calendar basis: adjusted EPS from continuing operations; MTM retirement plans, state deferred-tax remeasurement', None),
        QC[(2026, 2)].c: ('Q2/26+: gain / loss on the retained FedEx Freight stake and (Q3/26) gain on extinguishment of debt adjusted out', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: calendar-2026 revenue-growth and adjusted-EPS guidance end-points (high / mid / low), '
            'Q4/26E buybacks, 2027E–2031E package volume and yield growth, segment margins and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'FedEx Corporation (NYSE: FDX) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions; package volumes in thousands per day) · TWO BASES: columns C–CA fiscal years ended 31 May '
                '(FY2006–FY2026, FedEx Freight consolidated, as originally reported); columns CB onward calendar years (2024–2031E, continuing operations after the FedEx Freight '
                'spin-off of 1-Jun-2026 and the change of year end to 31 December) · Source: FedEx Forms 10-K / 10-Q, Form 8-K earnings releases and recast exhibits (Ex. 99.1), '
                'SEC EDGAR (CIK 1048911); XBRL company facts; investor-relations material is the same as filed on EDGAR')
    ws['B4'] = ('Basis notes: the two bases are never mixed in one growth rate (calendar 2024 has no prior year). Calendar 2024–Q2/26 from the recast exhibits of 21-Jul-2026 and '
                '28-Oct-2026 (unaudited; segments Express U.S. Domestic / Express International); cash flow on the calendar basis exists only for nine months (Q3 columns). '
                'Deals: TNT Express May-2016; FedEx Freight spun off 1-Jun-2026 (19.9% retained); InPost consortium stake (37%) 2026; FedEx Supply Chain sold 1-Oct-2026. '
                'Q4/26E calibrated to the calendar-2026 revenue and adjusted-EPS guidance of 28-Oct-2026 (EDGAR). Share price $300 provided by the user (20-Nov-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical (fiscal)'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{LANN[2006].c}5'] = 'Fiscal years ended 31 May — as originally reported (incl. FedEx Freight)'
    ws[f'{QC[(2024, 1)].c}5'] = 'Calendar years — continuing operations (recast)'
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '20Y CAGR'], ["26-'31", "FY21-'26", "FY16-'26", "FY06-'26"]):
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
        p = os.path.join(BASE, f'FDX_{scen}.xlsx')
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
    p = os.path.join(BASE, 'FDX_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
