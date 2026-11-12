"""Build RTX_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
import normalize
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'RTX_Model.xlsx')
G26 = MAN['guidance_fy26']
AM = MAN['amort_sched']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = DATA['2025']['x']
    rev, cogs = q['rev'], q['cogs']
    return {'dso': round(q['bs_ar'] / rev * 365), 'cad': round(q['bs_cac'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365),
            'dpo': round(q['bs_ap'] / cogs * 365), 'clp': round(q['bs_clc'] / rev, 3), 'acp': round(q['bs_accr'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at fiscal-year-end (31-Dec-2025) levels on 2025 net sales / cost of sales (receivables {WC["dso"]}d, contract assets {WC["cad"]}d, '
              f'inventory {WC["dio"]}d, payables {WC["dpo"]}d, contract liabilities {WC["clp"]:.1%} and accrued {WC["acp"]:.1%} of sales); year ends are compared with year ends '
              '(contract assets and inventory build during the year and unwind in Q4).')
UNV = 'Assumption — not guided in any SEC-filed document (segment, tax, interest and pension outlooks were given on calls only; rtx.com is not reachable)'

V0 = {
    'out_hdr': '2026 outlook — Q3-26 release (20-Oct-2026)',
    'out_note': ('Adjusted sales $97.0–97.5bn (raised from $95.0–96.0bn), organic growth 10–11%, adjusted EPS $7.65–7.75 (raised from $7.10–7.25), FCF $9.0–9.2bn. '
                 'The SEC-filed releases print company-level ranges only.'),
    'outlook': [
        ('out_sales', '  2026 adjusted sales ($m)', tuple(G26['adj_sales']), 'm', 'Outlook $97.0–97.5bn. Drives the Q4/26E sales calibration.'),
        ('out_eps', '  2026 adjusted EPS ($)', tuple(G26['adj_eps']), 'ps', 'Outlook $7.65–7.75. Drives the Q4/26E segment-margin calibration.'),
        ('out_org', '  2026 organic sales growth — memo', tuple(G26['organic_growth']), 'pct', 'Outlook +10–11% (information row).'),
        ('out_fcf', '  2026 free cash flow ($m)', tuple(G26['fcf']), 'm', 'Outlook $9.0–9.2bn. Drives the 2026E contract-asset (working-capital) calibration.'),
        ('bb26', '  Q4/26E share repurchases ($m)', (600.0, 0.0, 0.0), 'm', 'None in 9M-26; ~$0.6bn left on the Oct-2023 $11bn authorization. Bull uses it up; Base / Bear nil (assumption).'),
    ],
    'points': [
        ('pt_int', '  Q4/26E interest expense, net ($m)', 375.0, 'm', UNV + '. Q3-26 $381m; $2.9bn of notes / term loan mature in Q4-26.'),
        ('pt_nsp', '  Q4/26E non-service pension income ($m)', 345.0, 'm', UNV + '. Q3-26 $345m (9M-26 $1,048m).'),
        ('pt_fascas', '  Q4/26E FAS/CAS operating adjustment ($m)', 170.0, 'm', UNV + '. Q3-26 $171m (9M-26 $514m).'),
        ('pt_acqadj', '  Q4/26E acquisition accounting adjustments ($m)', AM['2026_rem'], 'm', 'Q3-26 10-Q schedule: $460m of intangible amortization remaining in 2026 (Q3-26 adjustments $448m).'),
        ('pt_dda', '  Q4/26E depreciation & amortization ($m)', 1070.0, 'm', UNV + '. Q3-26 $1,068m.'),
        ('pt_restr', '  Q4/26E restructuring costs ($m)', 50.0, 'm', UNV + '. 9M-26 $65m net; Q4-25 $44m.'),
        ('pt_etr', '  Q4/26E adjusted effective tax rate', 0.19, 'pct', UNV + '. 9M-26 adjusted rate 17.7%; 2025 19.6% (Q4-25 23.9%).'),
        ('pt_nci', '  Q4/26E noncontrolling interest ($m)', 120.0, 'm', UNV + '. Q3-26 $125m.'),
        ('pt_elim', '  Q4/26E eliminations and other — adjusted OP ($m)', -20.0, 'm', UNV + '. 9M-26 $17m; Q4-25 $32m.'),
        ('pt_corp', '  Q4/26E adjusted corporate expenses ($m)', -45.0, 'm', UNV + '. 9M-26 $(59)m; Q4-25 $(132)m.'),
        ('pt_othinc', '  Q4/26E other income, net ($m)', 40.0, 'm', UNV + '. 9M-26 $287m incl. $229m of investment gains (adjusted out).'),
    ],
    'lev': (1.75, 1.25, 0.75),
    'lev_note': ('Net debt $28.2bn at 30-Sep-26 ≈ 1.8x LTM adjusted EBITDA (model definition); 2023 ASR left 3.4x at YE23, deleveraged to 2.2x at YE25 with buybacks of only $0.4bn (2024) and $0.05bn (2025). '
                 'No leverage target is published in the SEC filings: the target is an assumption up to which surplus cash is returned via buybacks; below it free cash flow repays maturing notes. '
                 'Bull = more buybacks (higher target). The Q3-26 10-Q flags an executive order that could limit buybacks for underperforming defense contractors.'),
    'blocks': [
        ('COL_COMM', 'COL_COMM (Collins commercial aerospace sales y/y)', 0.03, -0.05, [0.08, 0.07, 0.06, 0.05, 0.05],
         '9M-26 +11.5% (commercial OE +23% and aftermarket +9% in Q3-26, after the 2025 actuation divestiture); narrowbody / widebody rate increases, aftermarket mid-to-high single digits.', 'pct', False),
        ('COL_DEF', 'COL_DEF (Collins defense sales y/y)', 0.02, -0.04, [0.05, 0.05, 0.04, 0.04, 0.04], '9M-26 +1% (actuation divestiture); Q3-26 organic defense +7%.', 'pct', False),
        ('PW_COMM', 'PW_COMM (Pratt & Whitney commercial sales y/y)', 0.03, -0.05, [0.09, 0.08, 0.07, 0.06, 0.05],
         '9M-26 +13% (commercial aftermarket +21% in Q3-26, GTF shop visits; OE −5% on engine mix); GTF fleet MRO and powder-metal inspections sustain aftermarket demand.', 'pct', False),
        ('PW_MIL', 'PW_MIL (Pratt & Whitney military sales y/y)', 0.02, -0.04, [0.06, 0.05, 0.05, 0.04, 0.04], '9M-26 +10% (F135 production and sustainment; F119 / F117 sustainment).', 'pct', False),
        ('RTN_USG', 'RTN_USG (Raytheon U.S. government & commercial sales y/y)', 0.03, -0.04, [0.08, 0.07, 0.06, 0.05, 0.04],
         '9M-26 +10%; record $130bn Raytheon backlog incl. multi-year Tomahawk (~$23bn) and AMRAAM (~$14.3bn) awards (Q3-26).', 'pct', False),
        ('RTN_INTL', 'RTN_INTL (Raytheon international sales y/y; FMS + direct commercial)', 0.04, -0.06, [0.10, 0.08, 0.07, 0.06, 0.05],
         '9M-26 +21% (Patriot, NASAMS, GEM-T for European customers).', 'pct', False),
        ('COL_M', 'COL_M (Collins adjusted segment margin)', 0.01, -0.02, [0.185, 0.188, 0.191, 0.193, 0.195],
         '9M-26 18.4% incl. ~$250m of Q3 IEEPA tariff recovery (Q3-26 21.3%); 2025 16.2%, 2024 15.9%. IEEPA recovery is one-off, so 2027E starts near the 9M rate ex-recovery.', 'pct', False),
        ('PW_M', 'PW_M (Pratt & Whitney adjusted segment margin)', 0.01, -0.02, [0.095, 0.100, 0.105, 0.110, 0.115],
         '9M-26 9.2% incl. ~$160m of Q3 IEEPA recovery; 2025 8.3%, 2024 8.1%; aftermarket mix vs. GTF OE losses.', 'pct', False),
        ('RTN_M', 'RTN_M (Raytheon adjusted segment margin)', 0.01, -0.02, [0.132, 0.135, 0.137, 0.139, 0.140],
         '9M-26 13.0% (2025 11.5%, 2024 10.2%); productivity, higher-margin international mix; new multi-year awards start at lower margins.', 'pct', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 500.0, 0.0, [0.0, 0.0, 0.0, 0.0, 0.0],
         'No acquisitions since the Raytheon merger (Apr-2020); portfolio actions have been divestitures. Base nil; Bull $500m p.a. of bolt-ons (assumption).', 'm', True),
    ],
    'inter_p': {'col': 0.09, 'pw': 0.001, 'rtn': 0.005},
    'elim_p': -0.027, 'elim_aop': -40.0, 'corp_aop': -150.0,
    'fascas': {2027: 620.0, 2028: 570.0, 2029: 520.0, 2030: 470.0, 2031: 420.0},
    'nsp': {2027: 1350.0, 2028: 1300.0, 2029: 1250.0, 2030: 1200.0, 2031: 1150.0},
    'restr_mix': {'col': 0.45, 'pw': 0.20, 'rtn': 0.15, 'corp': 0.20},
    'dep_pct': {2027: 0.025, 2028: 0.025, 2029: 0.026, 2030: 0.026, 2031: 0.026},
    'sga_pct': {2027: 0.070, 2028: 0.069, 2029: 0.068, 2030: 0.068, 2031: 0.068},
    'rd_pct': 0.029, 'sbc_pct': 0.0065, 'othinc': 100.0, 'nci_pct': 0.045, 'adj_etr': 0.19, 'mrate': 0.21, 'stat_rate_hist': 0.35,
    'capex_pct': {2027: 0.030, 2028: 0.030, 2029: 0.029, 2030: 0.028, 2031: 0.028},
    'dps_q': MAN['dividends']['q4_26e'], 'dps_paid_q4': 0.73, 'dps_g': 0.07,
    'def_q4': 0.0, 'def_ae': 0.0, 'oth_op': -150.0, 'svc_q4': 43.0, 'svc_ae': 170.0, 'k401_pct': 0.0065, 'contrib': -250.0, 'oinv_pct': 0.006,
    'iss_q4': 2.4, 'iss_ae': 9.0, 'dil': 15.9,
    'ae_restr': {2027: 200.0, 2028: 200.0, 2029: 150.0, 2030: 150.0, 2031: 150.0},
    'acq_sched': {2027: AM['2027'], 2028: AM['2028'], 2029: AM['2029'], 2030: AM['2030'], 2031: AM['2031']},
    'acq_sched_note': (AM['src'] + ': 2027 $1,884m, 2028 $1,795m, 2029 $1,638m, 2030 $1,606m, 2031 $1,593m. Acquisition accounting adjustments also include PP&E fair-value and '
                       'contractual-obligation amortization, which net to roughly nil (9M-26 adjustments $1,393m vs ~$1.5bn of intangible amortization); the schedule is used as the forecast.'),
    'repay': {2026: 2869.0, 2027: 2917.0, 2028: 3470.0, 2029: 914.0, 2030: 1570.0, 2031: 2000.0},
    'mat': {2026: 2917.0, 2027: 3470.0, 2028: 914.0, 2029: 1570.0, 2030: 2000.0, 2031: 1000.0},
    'refi': 0.5, 'min_cash': 6000.0,
    'r_notes': {2027: 0.044, 2028: 0.045, 2029: 0.046, 2030: 0.046, 2031: 0.047},
    'r_notes_note': ('Weighted coupon of the notes outstanding at 30-Sep-2026 ~4.4% (Q3-26 10-Q debt table); drifting up as low-coupon 2030–32 notes mature and maturities are '
                     'refinanced at ~5–5.5% (assumption).'),
    'int_other': 150.0, 'r_cash': 0.03,
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $201.70 (Form 4 filed 3-Nov-2026: open-market sale on 30-Oct-2026 at a weighted average $201.6951 — the latest share price in an '
                'SEC filing; ~$274bn market cap); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base nil; Bull $500m p.a.). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': 'Company 2026 adjusted-sales outlook $97.0–97.5bn (raised 20-Oct-2026 from $95.0–96.0bn). Drives the sales calibration.',
    'eps_guid_note': 'Company 2026 adjusted-EPS outlook $7.65–7.75 (raised 20-Oct-2026 from $7.10–7.25). Drives the segment-margin calibration.',
}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw; path = kw.get('data')
    if not path: return None
    if kw.get('ppa'):
        v = MAN.get('ppa', {}).get(pkey(col), {}).get(path.split('_', 1)[1])
        return v if kw.get('textdata') else num(v)
    v = xget(pkey(col), path)
    if kw.get('pctdata') and num(v) is not None: return v / 100.0
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
CAGR_G = {'is_rev', 'g_rev', 'col_rev', 'pw_rev', 'rtn_rev', 'col_comm', 'col_def', 'pw_comm', 'pw_mil', 'rtn_usg', 'rtn_intl', 'o_adj', 'g_adj', 'r_adj',
          'is_op', 'd_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_gp', 'is_sga', 'd_acq', 'd_dep', 'col_aop', 'pw_aop',
          'rtn_aop', 'is_ni', 'eps_dil', 'dps', 'g_segaop'}
CAGR_A = {'col_m', 'pw_m', 'rtn_m', 'g_adjm', 'o_adj_m', 'r_adj_m', 'is_gm', 'is_op_m', 'r_ebit_m', 'gm_rev', 'gm_col', 'gm_pw', 'gm_rtn', 'gm_gm', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_sga', 'gm_rd', 'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_sga', 'd_dep_pct',
          'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'g_segaop_m'}
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
                if t: comment(cell, f'Company items ({pkey(col)}): {t}', 420, 160)
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

REL = 'Source: RTX / United Technologies earnings releases (Form 8-K Item 2.02, Ex. 99) — '
LABEL_SOURCES = {
    'col_comm': ('Source: Forms 10-Q / 10-K revenue note ("Segment sales disaggregated by type of customer", ASC 606, from 2018; external sales). Defense = sales to the U.S. government + '
                 'foreign military sales through the U.S. government + foreign government direct commercial sales. Before 2018 the build falls back to segment net sales as reported.'),
    'rtn_usg': ('Source: Forms 10-Q / 10-K revenue note. Raytheon = Raytheon Intelligence & Space + Raytheon Missiles & Defense for Q2-20 to Q4-22 (summed); one segment from 1-Jul-2023 '
                '(2022 recast in the 2023 filings; 2023 recast for the 2024 Collins / Raytheon realignment in the 2024 filings).'),
    'col_op': REL + 'segment net sales and operating profit schedule and the reconciliation of adjusted (non-GAAP) results (restructuring and significant items by segment).',
    'otis_rev': REL + 'segment schedule as originally reported (UTC conglomerate segments to Q4-19; Sikorsky to Q2-15).',
    'fc_adj': REL + 'segment schedule ("FAS/CAS operating adjustment", from Q2-20) and the 10-Q / 10-K FAS/CAS components table (CAS expense − FAS service cost).',
    'aa_adj': REL + 'segment schedule ("Acquisition accounting adjustments", from Q2-20).',
    'is_rev': (REL + 'condensed consolidated statements of operations. Basis: hybrid recast — years whose four quarters were all re-presented in the following year\'s releases take '
               'those comparatives (cell comments); 2006–12 take the latest 10-K presentation; balance sheet and cash flow as originally reported.'),
    'd_dda': REL + 'cash-flow statement ("Depreciation and amortization").',
    'o_pub': REL + 'Reconciliation of Reported (GAAP) to Adjusted (Non-GAAP) Results — adjusted operating profit (published from Q4-13 / FY2013).',
    'e_pub': REL + 'Reconciliation of adjusted net income, EPS and effective tax rate (adjusted EPS first printed for Q3-14).',
    'cf_ni': (REL + 'condensed cash-flow statements (year to date; discrete quarters derived, Q4 = FY − 9M); 10-K / Exhibit 13 statements for annual records. Restricted cash '
              'included from 2018 (ASU 2016-18).'),
    'bs_cash': REL + 'condensed consolidated balance sheets (period ends); shares outstanding from the 10-Q / 10-K cover pages.',
    'sh_basic': REL + 'statements of operations (weighted average shares). No stock splits in the window; the Otis / Carrier separations (3-Apr-2020) were pro-rata distributions with no share consolidation, and the all-stock Raytheon Company merger (same date) issued RTX shares to Raytheon shareholders, so share counts step up from Q2-20.',
    'ds_total': 'Source: release balance sheets; Q3-26 10-Q Note 9 (long-term debt by note) and MD&A Liquidity (revolver, commercial paper).',
    'ppa_cons': 'Source: FY2012 10-K (Goodrich), FY2018 10-K (Rockwell Collins), FY2020 10-K (Raytheon Company merger) purchase-price allocation notes.',
    'gm_bl': REL + 'release text and 10-Q / 10-K MD&A ("Backlog and Bookings"; total backlog from 2020, segment backlog from 10-K Item 1 before).',
}
CELL_COMMENTS = {}
def comments_setup():
    for p, (b, reason) in normalize.REC_LOG.items():
        y, q = (int(p), None) if p.isdigit() else (int('20' + p[-2:]), int(p[1]))
        col = ANN[y].c if q is None else QC[(y, q)].c
        src = {'py': 'the following year\'s release / 10-K', 'py2': 'the 10-K two years later'}[b]
        CELL_COMMENTS.setdefault('is_rev', {})[col] = f'Recast period ({p}): income statement, segments and adjusted figures as re-presented in {src}. Reason: {reason}'

    for y, t in ((2006, 'Revenues as originally reported include other income, net ($711m in 2006); no later filing re-presents 2006 without it.'),
                 (2007, 'As presented in the FY2009 10-K (SFAS 160; collaboration gross-up). Revenues still include other income, net; the FY2010 presentation moved it out from 2008.')):
        CELL_COMMENTS.setdefault('is_rev', {})[A[y]] = t + (' ' + CELL_COMMENTS['is_rev'][A[y]] if A[y] in CELL_COMMENTS.get('is_rev', {}) else '')

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('2006–12: no adjusted operating profit published — releases list restructuring and non-recurring items (bullet text, approximate amounts); model adjusted = OP + restructuring − items',
              'UTC releases in 2006–2012 reconcile nothing to an adjusted measure; restructuring by segment and "non-recurring items" are listed with approximate pre-tax amounts.'),
        A[2013]: ('2013–19 (UTC): adjusted operating profit = operating profit excl. restructuring and significant non-recurring / non-operational items; acquired-intangible amortization NOT excluded', None),
        q(2020, 2): ('Q2-20+ (Raytheon Technologies / RTX): adjusted operating profit also excludes acquisition accounting adjustments (acquired intangibles, PP&E fair-value step-ups, contractual obligations, goodwill impairment)',
                     'Definition introduced with the Raytheon merger (3-Apr-2020); 2019 comparatives were not restated to exclude amortization.'),
        q(2023, 3): ('Q3-23: powder metal matter ($2.9bn charge, incl. a $0.5bn sales reduction) adjusted out; adjusted net sales = net sales − significant sales items', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–Q2/14: no adjusted EPS published — model: GAAP continuing EPS + items less the tax effect stated by the company (35% statutory where none stated; flag)', None),
        q(2014, 3): ('Q3-14+: adjusted EPS = diluted EPS from continuing operations excl. restructuring and significant non-recurring / non-operational items (incl. discrete tax items)', None),
        q(2020, 2): ('Q2-20+: adjusted EPS also excludes acquisition accounting adjustments (tax-effected) and items in non-service pension income and interest', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: 2026 adjusted-sales, adjusted-EPS and FCF outlook end-points (high / mid / low), '
            'Q4/26E buybacks, 2027E–2031E customer-type sales growth, adjusted segment margins, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'RTX Corporation (NYSE: RTX) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP · USD millions (per-share data in USD; shares in millions) · Calendar fiscal years · Source: RTX (United Technologies Corporation to Apr-2020, Raytheon Technologies to Jul-2023) '
                'Forms 10-K (Exhibit 13 to FY2018) / 10-Q, Form 8-K earnings releases (Ex. 99) and Form 4, SEC EDGAR (CIK 0000101829); XBRL company facts; investor-relations releases at rtx.com '
                'are the same documents as filed on EDGAR. 2026 outlook: SEC-filed company-level ranges only; segment / tax / interest / pension items not in an SEC filing are labelled assumptions.')
    ws['B4'] = ('Basis notes: hybrid recast — income statement, segments and adjusted figures of a year take the following year\'s re-presented comparatives when all four quarters were re-presented '
                '(2015 Sikorsky discontinued; 2016 ASU 2016-09; 2017 ASU 2017-07; 2019 Otis & Carrier discontinued; 2020 RIS / RMD reorganization; 2023 Collins / Raytheon realignment); '
                '2007–11 on the latest 10-K presentation (2006–07 revenues include other income); BS and CF as originally reported. Raytheon = RIS + RMD in 2020–22. '
                'Acquisitions: Goodrich Jul-12, Rockwell Collins Nov-18, Raytheon Company merger 3-Apr-20; separations: Sikorsky Nov-15, Otis & Carrier 3-Apr-20; divestitures 2020–25 '
                '(Collins / Raytheon businesses). Q4/26E calibrated to the 2026 outlook (20-Oct-2026).')
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
        p = os.path.join(BASE, f'RTX_{scen}.xlsx')
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
    viewer; fullCalcOnLoad stays set so Excel recalculates on open. Same approach as the LECO / ESAB / WWD finishing step."""
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
    p = os.path.join(BASE, 'RTX_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
