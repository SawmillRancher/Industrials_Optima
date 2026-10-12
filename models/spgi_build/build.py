"""Build SPGI_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'SPGI_Model.xlsx')
G26 = MAN['guidance_fy26']
SP = MAN['mobility_spin']; PFB = SP['pf_bs_2026_03_31']

# ====================================================================== inputs (V0)
def wc_inputs():
    """FY2025 year-end balances excluding Mobility (31-Mar-2026 pro forma Mobility balances as proxy) and the assets / liabilities held for
    sale, on FY2025 pro forma revenue."""
    q = DATA['2025']['x']; rev = q['rev']
    return {'dso': round((q['bs_ar'] - PFB['ar']) / rev * 365), 'unr': round((q['bs_unr'] - PFB['unearned']) / rev, 3), 'ap': round((q['bs_ap'] - PFB['ap']) / rev, 3),
            'acc': round((q['bs_acc'] - PFB['accrued']) / rev, 3), 'taxp': round((q['bs_taxp'] - PFB['tax_pay']) / rev, 3),
            'ocl': round((q['bs_ocl'] - PFB['ocl'] - 43) / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at 31-Dec-2025 levels excluding Mobility (31-Mar-2026 pro forma balances as proxy) and held-for-sale liabilities, on FY2025 pro forma revenue: '
              f'DSO {WC["dso"]}d, unearned revenue {WC["unr"]:.1%}, payables {WC["ap"]:.1%}, accrued compensation {WC["acc"]:.1%}, taxes payable {WC["taxp"]:.1%}, '
              f'other current liabilities {WC["ocl"]:.1%} of revenue. Year ends are compared with year ends (unearned revenue peaks at year end on annual billing).')
AM = MAN['amort_sched']
DEBT = MAN['debt_2026_06_30']
COUP = {'2027': (500 * 2.95 + 1250 * 2.45) / 1750, '2028': 4.75, '2029': (921 * 4.25 + 500 * 2.5 + 1227 * 3.20) / 2648, '2030': 1.25, '2031': 4.25}
MOB = {'ta': float(PFB['ta']), 'tl': float(PFB['tl']), 'notes': SP['mobility_notes_carrying_2026_06_30'], 'cash': PFB['cash'], 'ar': PFB['ar'], 'oca': PFB['oca'],
       'ppe': PFB['ppe'], 'rou': PFB['rou'], 'gw': PFB['gw'], 'int': PFB['int'], 'onca': PFB['onca'], 'ap': PFB['ap'], 'accrued': PFB['accrued'],
       'tax_pay': PFB['tax_pay'], 'unearned': PFB['unearned'], 'ocl': PFB['ocl'], 'lease': PFB['lease'], 'pension': PFB['pension'], 'dtl': PFB['dtl'], 'onl': PFB['onl']}

V0 = {
    'out_hdr': 'FY26 guidance — Q2-26 release (28-Jul-2026), continuing operations excl. Mobility',
    'out_note': ('Revenue +5.9–7.9% (organic cc +6–8%) on FY2025 pro forma revenue $13,589m; adjusted EPS $17.50–17.75; GAAP EPS $16.35–16.60; adjusted margin +35–60 bp '
                 '(+75–100 bp ex OSTTRA); deal amortization ~$785m; corporate unallocated $185–195m adjusted; interest $365–385m GAAP / $390–410m adjusted; tax 22–23%; capex $190–210m; '
                 '>$7bn of 2026 buybacks. Source: SEC EDGAR 8-K Ex. 99.1 (no unverified guidance used).'),
    'outlook': [
        ('out_g', '  FY26 revenue growth (vs FY2025 pro forma)', (G26['rev_growth'][1], round(sum(G26['rev_growth']) / 2, 4), G26['rev_growth'][0]), 'pct',
         'Guided +5.9–7.9%. Drives the Q3–Q4/26E revenue calibration.'),
        ('out_eps', '  FY26 adjusted diluted EPS ($)', (G26['adj_eps'][1], round(sum(G26['adj_eps']) / 2, 3), G26['adj_eps'][0]), 'ps', 'Guided $17.50–17.75. Drives the margin calibration.'),
        ('out_geps', '  FY26 GAAP diluted EPS, continuing ($) — memo', (G26['gaap_eps'][1], round(sum(G26['gaap_eps']) / 2, 3), G26['gaap_eps'][0]), 'ps', 'Guided $16.35–16.60 (information row).'),
        ('out_m', '  FY26 adjusted margin expansion (bp) — memo', (60, 47.5, 35), 'm', 'Guided +35–60 bp vs FY2025 pro forma 51.3% (information row).'),
        ('out_og', '  FY26 organic constant-currency growth — memo', (0.08, 0.07, 0.06), 'pct', 'Guided +6–8% (information row).'),
        ('bb26', '  2H-26 share repurchases ($m)', (6000.0, 5750.0, 5500.0), 'm', '1H-26 $1,500m (ASRs at $426.70 and $414.76); company expects >$7bn for 2026 → 2H ≥ $5.5bn (assumption by case).'),
    ],
    'points': [
        ('pt_corp', '  Adjusted corporate unallocated expense ($m / quarter)', 54.0, 'm', 'FY26 guided $185–195m adjusted; 1H $82m → (190 − 82) ÷ 2.'),
        ('pt_amort', '  Deal-related amortization ($m / quarter)', 193.0, 'm', 'FY26 guided ~$785m; 1H $399m → (785 − 399) ÷ 2.'),
        ('pt_int', '  Interest expense, net — GAAP ($m / quarter)', 98.0, 'm', 'FY26 guided $365–385m GAAP; 1H $179m → (375 − 179) ÷ 2.'),
        ('pt_prem', '  Premium amortization benefit in interest ($m / quarter)', 6.0, 'm', 'IHS Markit notes fair-value premium: $6m a quarter (adjusted interest = GAAP + $6m).'),
        ('pt_oth', '  Other income, net ($m / quarter)', 3.0, 'm', '1H-26 $6m (pension income).'),
        ('pt_dep', '  Depreciation ($m / quarter)', 29.0, 'm', '1H-26 $56m continuing.'),
        ('pt_sev', '  Severance & restructuring ($m / quarter)', 15.0, 'm', 'Assumption (1H-26 continuing ~$45m).'),
        ('pt_disp', '  Disposition / separation costs ($m / quarter)', 10.0, 'm', 'Assumption: residual Mobility separation and geoscience / EDM disposition costs.'),
        ('pt_gain', '  Gain on geoscience portfolio sale (Q4/26E; negative = gain)', -250.0, 'm',
         'Assumption implied by the guidance: GAAP vs adjusted margin guidance leaves ~$210m of net 2H gains after amortization, and the EPS bridge includes −$1.20 of divestiture gains ($0.60 booked in 1H).'),
        ('pt_etr', '  Tax rate (GAAP & adjusted)', 0.225, 'pct', 'FY26 guided 22–23%.'),
        ('pt_capex2h', '  2H-26 capital expenditures ($m)', 135.0, 'm', 'FY26 guided $190–210m; 1H $65m.'),
    ],
    'lev': (1.75, 1.5, 1.25),
    'lev_note': ('Assumption: net debt / adjusted EBITDA target for 2027E+ buybacks. Model YE2026E ~1.4x after the $7bn+ 2026 buybacks; S&P Global has historically returned ~85% of '
                 'adjusted FCF and kept leverage near 2x gross. Bull = more buybacks (higher target).'),
    'blocks': [
        ('RAT_TR', 'RAT_TR (Ratings transaction revenue y/y)', 0.04, -0.08, [0.03, 0.06, 0.06, 0.05, 0.05],
         '1H-26 +20% (record issuance, refinancing walls); FY2020–25 range −27% to +25% (cyclical). 2027E normalisation after two strong years.', 'pct', False),
        ('RAT_NT', 'RAT_NT (Ratings non-transaction revenue y/y)', 0.02, -0.03, [0.07, 0.07, 0.06, 0.06, 0.06], '1H-26 +10%; surveillance and frequent-issuer fees, Crisil; price.', 'pct', False),
        ('IDX_ALF', 'IDX_ALF (Indices asset-linked fees y/y)', 0.05, -0.12, [0.10, 0.09, 0.09, 0.08, 0.08],
         '1H-26 +20% (equity-market levels and ETF inflows); market-driven (Bear = equity drawdown).', 'pct', False),
        ('IDX_ETD', 'IDX_ETD (Indices exchange-traded derivatives y/y)', 0.04, -0.08, [0.05, 0.05, 0.05, 0.05, 0.05], '1H-26 +20%; volatility-driven volumes.', 'pct', False),
        ('IDX_SUB', 'IDX_SUB (Indices data & custom subscriptions y/y)', 0.02, -0.03, [0.08, 0.08, 0.07, 0.07, 0.07], '1H-26 +10%; FY2023–25 +7–10%.', 'pct', False),
        ('EN', 'EN (Energy revenue y/y, all types)', 0.02, -0.04, [0.06, 0.06, 0.06, 0.06, 0.06],
         '1H-26 +5% recast (2026 includes the geoscience sale in 2H); Platts / CERA, CERAWeek; subscription growth ~4–7%.', 'pct', False),
        ('MI', 'MI (Market Intelligence revenue y/y, all types)', 0.02, -0.04, [0.06, 0.065, 0.065, 0.065, 0.065],
         '1H-26 +7% recast (+6% organic cc); With Intelligence (Nov-2025) in the base; EDM / thinkFolio sold Q1-26.', 'pct', False),
        ('RAT_M', 'RAT_M (Ratings adjusted margin)', 0.01, -0.03, [0.665, 0.67, 0.67, 0.67, 0.67], 'FY2025 65.1%, 1H-26 68.0%; operating leverage on issuance.', 'pct', False),
        ('IDX_M', 'IDX_M (Indices adjusted margin)', 0.005, -0.02, [0.715, 0.72, 0.72, 0.725, 0.725], 'FY2025 70.3%, 1H-26 72.2%.', 'pct', False),
        ('CI_M', 'CI_M (Energy adjusted margin)', 0.01, -0.02, [0.475, 0.48, 0.485, 0.49, 0.49], 'FY2025 recast 45.9%, 1H-26 47.8%.', 'pct', False),
        ('MI_M', 'MI_M (Market Intelligence adjusted margin)', 0.01, -0.02, [0.35, 0.355, 0.36, 0.365, 0.37], 'FY2025 recast 33.0%, 1H-26 34.4%; new operating model (Jul-2026).', 'pct', False),
        ('MNA', 'M&A_spend (bolt-on acquisitions, $m)', 500.0, -500.0, [500.0, 500.0, 500.0, 500.0, 500.0],
         'Assumption: bolt-ons (With Intelligence ~$1.8bn in 2025, Visible Alpha 2024, small deals 2026). Base $500m p.a.', 'm', True),
    ],
    'corp_pct': 0.013,
    'dep_pct': 0.008, 'opr_pct': 0.285, 'sbc_pct': 0.012, 'etr': 0.225, 'oth_ae': 12.0,
    'capex_pct': 0.014,
    'dps_q': 0.97, 'dps_g': 0.05, 'def_2h': -100.0, 'def_ae': -180.0, 'iss_2h': 0.5, 'iss_ae': 1.0, 'dil': 0.3,
    'ae_sev': {2027: 40.0, 2028: 40.0, 2029: 40.0, 2030: 40.0, 2031: 40.0},
    'amort_sched': {2027: AM['2027'] - AM['mobility_2025'], 2028: AM['2028'] - AM['mobility_2025'], 2029: AM['2029'] - AM['mobility_2025'],
                    2030: AM['2030'] - AM['mobility_2025'], 2031: AM['2030'] - AM['mobility_2025'] - 25},
    'amort_note': ('FY2025 10-K expected amortization (incl. Mobility): 2027 $1,094m, 2028 $1,076m, 2029 $1,050m, 2030 $1,024m; less Mobility $303m (FY2025 pro forma, held flat — assumption); '
                   '2031 = 2030 − $25m (assumption). FY2026 continuing guidance ~$785m vs the ex-Mobility schedule $807m (EDM / thinkFolio / geoscience disposals).'),
    'gain_note': 'Q4/26E: gain on the geoscience portfolio sale to SLB (assumption implied by the guidance; terms undisclosed). 2027E+: nil.',
    'acq_2h': 100.0,
    'iss_notes': {2026: 0.0, 2027: 1750.0, 2028: 700.0, 2029: 2650.0, 2030: 600.0, 2031: 600.0},
    'repay': {2026: 0.0, 2027: 1750.0, 2028: 700.0, 2029: 2650.0, 2030: 600.0, 2031: 600.0},
    'mat': {2026: 1750.0, 2027: 700.0, 2028: 2650.0, 2029: 600.0, 2030: 600.0, 2031: 1500.0},
    'repay_note': ('Face amounts (10-Q Note 4 / 10-K): 2027 $500m 2.95% (Jan) + $1,250m 2.45% (Mar); 2028 $700m 4.75%; 2029 $921m 4.25% + $500m 2.5% + $1,227m 2.95% SLB; '
                   '2030 $600m 1.25%; 2031 $600m 4.25%; 2032 $1,500m 2.90%. Assumed refinanced in full (input row above).'),
    'min_cash': 1500.0,
    'r_notes': {2027: 0.0335, 2028: 0.0345, 2029: 0.0365, 2030: 0.0375, 2031: 0.0380},
    'r_notes_note': ('Weighted coupon on the 30-Jun-2026 notes ex-Mobility ~3.3% (2.45–6.55%; IHS Markit notes carried above face); maturities refinanced at ~5% (assumption) lift the '
                     'average over time.'),
    'wc': WC,
    'mob': MOB,
    'geo': {'assets': 120.0, 'liab': 28.0, 'nav': 92.0},
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $415.00 (user-provided, 12-Oct-2026; cross-check: Q2-26 average repurchase price $414.85, 10-Q Part II Item 2); update to market'),
    'mna_note': 'Scenario lever M&A_spend (Base $500m p.a. of bolt-ons). Funded from cash / commercial paper (debt schedule).',
    'rev_guid_note': 'Company FY26 revenue growth guidance +5.9–7.9% excluding Mobility (Q2-26 release, 28-Jul-2026). Drives the revenue calibration.',
    'eps_guid_note': 'Company FY26 adjusted diluted EPS guidance $17.50–17.75 excluding Mobility (Q2-26 release). Drives the margin calibration.',
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
CAGR_G = {'is_rev', 'g_rev', 'rat_rev', 'idx_rev', 'en_rev', 'mi_rev', 'rat_tr', 'rat_nt', 'idx_alf', 'idx_etd', 'idx_sub', 'o_adj', 'g_adj', 'r_adj', 'is_op',
          'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'sh_dil', 'rat_oi', 'idx_oi', 'en_oi', 'mi_oi', 'is_nicattr', 'eps_cont', 'dps', 'd_amort', 'd_dep', 'is_sga', 'is_opr'}
CAGR_A = {'rat_m', 'idx_m', 'en_m', 'mi_m', 'g_adjm', 'o_adj_m', 'r_adj_m', 'is_op_m', 'r_ebit_m', 'gm_rev', 'gm_rat', 'gm_idx', 'gm_en', 'gm_mi', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_opr', 'gm_sga', 'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'roe', 'lv_x', 'd_opr', 'd_dep_pct', 'd_sbc_pct',
          'wc_nwc_p', 'is_etr', 'e_rate', 'fcf_eb', 'corp_pct', 'mx_tr', 'mx_alf', 'mx_rec', 'rat_mix', 'idx_mix', 'en_mix', 'mi_mix'}
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
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2010]}{r})^(1/15)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2016, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2010, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: S&P Global (McGraw Hill Financial / McGraw-Hill) earnings releases (Form 8-K Item 2.02, Ex. 99.1) — '
LABEL_SOURCES = {
    'rat_tr': (REL + 'revenue-information exhibit (revenue by type; 2016–17 MCI and 2013–15 C&C / Capital IQ types mapped to Energy / Market Intelligence lines). '
               '2025–1H26 Energy / MI types: recast tables in the 8-K/A of 6-Jul-2026 (Ex. 99.1) and the Q2-26 release Exhibit 7.'),
    'rat_oi': (REL + 'Operating Results by Segment / Reported vs Adjusted exhibits (adjusted segment OP as published; FY2010 from the FY2012 10-K segment note, GAAP only). '
               '2025–1H26: pro forma non-GAAP adjusted OP on the July-2026 recast basis (8-K/A 6-Jul-2026 recast tables; Q2-26 release Exhibit 6).'),
    'mob_rev': REL + 'segment exhibits (Mobility and Engineering Solutions from the IHS Markit merger, 28-Feb-2022; Engineering Solutions sold 2-May-2023; Mobility spun off 1-Jul-2026).',
    'corp': REL + 'Corporate Unallocated expense (reported and adjusted); 2025–1H26 pro forma recast (derived where the recast table rounds: Q1-25, Q3-25, FY2025).',
    'is_rev': (REL + 'condensed consolidated statements of income, as originally reported; FY2010–11 continuing operations recast in the FY2012 10-K / Q4-12 release; '
               '2025 quarters, FY2025 and 1H-26 = Article 11 pro forma continuing operations excluding Mobility (8-K/A 6-Jul-2026 Ex. 99.1–99.2; Q2-26 release Exhibit 5). '
               'Expense lines not in the condensed release statement from XBRL (10-Q / 10-K as first filed; Q4 = FY − 9M).'),
    'd_amort': REL + 'reconciliation exhibits ("deal-related amortization"); added back from the 2016 releases (FY2013–15 adjusted measures included amortization).',
    'o_pub': REL + 'Reported vs Adjusted exhibits (adjusted operating profit); 2025–1H26 pro forma non-GAAP adjusted.',
    'e_pub': REL + 'Adjusted Net Income / Adjusted Diluted EPS reconciliations; 2025–1H26 pro forma non-GAAP adjusted (as originally published incl. Mobility in the memo row).',
    'cf_ni': ('Source: XBRL company facts (Forms 10-K / 10-Q cash-flow statements, as first filed; 2013–15 10-Qs tagged continuing + discontinued separately) — year to date, discrete quarters '
              'derived (Q4 = FY − 9M); 1H-26 from the Q2-26 10-Q. As reported (incl. Mobility to 30-Jun-2026).'),
    'bs_cash': ('Source: XBRL company facts (10-K / 10-Q balance sheets as first filed), 30-Jun-2026 from the Q2-26 10-Q; derived "other" lines close to reported totals. '
                'Shares outstanding: release "actual shares outstanding" / XBRL / 10-Q cover.'),
    'ppa_cons': MAN['ppa']['Q1-22']['source'],
    'sh_basic': REL + 'statements of income (weighted-average shares). No stock splits since the 2-for-1 split of May-2005.',
    'ds_total': 'Source: balance sheets; Q2-26 10-Q Note 4 (Debt) — notes by tranche, $825m commercial paper, Mobility notes ($1,981m) transferred with Mobility Global on 1-Jul-2026.',
    'pf_hdr': MAN['recast_2025_26']['note'],
    'sp_h': MAN['mobility_spin']['source'],
}
CELL_COMMENTS = {}
def comments_setup():
    CELL_COMMENTS['is_rev'] = {A[2011]: 'FY2011 = continuing-operations comparative in the Q4-2012 release (McGraw-Hill Education classified as discontinued operations); not as first reported.',
                               A[2014]: 'FY2014 excludes McGraw Hill Construction (discontinued from Q3-14); Q1–Q2/14 as originally reported include it, so Σ quarters ≠ FY (check_data known exception).',
                               A[2025]: 'FY2025 pro forma continuing operations excluding Mobility (Article 11); as reported $15,336m.',
                               QC[(2026, 2)].c: 'Q2-26 pro forma excluding Mobility (Q2-26 release Exhibit 5); as reported $4,146m.'}
    CELL_COMMENTS['e_pub'] = {QC[(2014, 4)].c: 'Q4-14 GAAP loss quarter: the company computed adjusted EPS on 276.2m diluted shares (GAAP 271.7m).',
                              QC[(2022, 1)].c: 'Q1-22: adjusted EPS published only pro forma for IHS Markit ($2.89); the model rebuilds the actual-scope figure (memo row).'}
    CELL_COMMENTS['corp'] = {QC[(2025, 3)].c: 'Q3-25 pro forma adjusted corporate derived as Σ adjusted divisions + equity income − adjusted OP ($55m); the recast table prints $52m (company rounding).'}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2010: continuing operations recast (FY2012 10-K); no adjusted measures on this basis', None),
        A[2011]: ('FY2011–15: adjusted OP excludes restructuring / Growth & Value Plan items, legal settlements and gains; deal amortization NOT added back',
                  'McGraw-Hill / McGraw Hill Financial adjusted operating profit (Q4-12 to Q4-15 releases).'),
        q(2016, 1): ('2016+: deal-related amortization added back (the Q4-15 release recast FY2015 adjusted EPS to $4.69; the model keeps 2013–15 as first published)', None),
        q(2022, 1): ('Q1-22 / FY2022: adjusted published only pro forma for IHS Markit — model = actual-scope rebuild (check n/p); Q2–Q4-22 actual scope, net of divestitures', None),
        q(2023, 1): ('Q1-23+: premium amortization benefit on assumed IHS Markit notes removed from adjusted interest', None),
        q(2025, 1): ('2025–1H26: pro forma continuing operations excluding Mobility (Article 11; recast 6-Jul-2026; incl. Transition Services Agreement income)', None),
    }
    DEFS['e_def'] = {
        A[2011]: ('FY2011–13: adjusted diluted EPS from continuing operations; FY2014–24 adjusted diluted EPS (start: total net income attributable)', None),
        q(2016, 1): ('2016+: deal-related amortization excluded (after tax)', None),
        q(2025, 1): ('2025–1H26: pro forma non-GAAP adjusted diluted EPS from continuing operations excluding Mobility (originally published figures in the memo row)', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 revenue-growth and adjusted-EPS guidance end-points (high / mid / low), '
            '2H-26 buybacks, 2027E–2031E revenue growth by type, division adjusted margins, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'S&P Global Inc. (NYSE: SPGI) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP · USD millions (per-share data in USD; shares in millions) · Fiscal years ended 31 December · Source: S&P Global Forms 10-K / 10-Q, Form 8-K earnings releases '
                '(Ex. 99.1), the 8-K / 8-K/A of 2 / 6-Jul-2026 (Mobility spin-off, pro forma and recast) and deal / financing 8-Ks, SEC EDGAR (CIK 64040; McGraw Hill Financial 2013–16, '
                'The McGraw-Hill Companies before); XBRL company facts; investor-relations releases are the same documents as filed on EDGAR')
    ws['B4'] = ('Basis notes: hybrid recast — FY2010–11 continuing operations (McGraw-Hill Education sold Mar-2013); FY2012–2024 as originally reported; 2025 and 1H-26 pro forma excluding Mobility '
                '(spun off 1-Jul-2026 as Mobility Global, NYSE: MBGL). Divisions: Ratings, Indices (S&P DJI JV with CME 73/27 from Jul-2012), Energy (C&C / Platts / Commodity Insights), Market '
                'Intelligence (Capital IQ; SNL Sep-2015). IHS Markit merger 28-Feb-2022; Engineering Solutions sold May-2023; OSTTRA stake sold Q4-2025. Q3–Q4/26E calibrated to FY26 guidance (28-Jul-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '15Y CAGR'], ["26-'31", "20-'25", "15-'25", "10-'25"]):
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
        p = os.path.join(BASE, f'SPGI_{scen}.xlsx')
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
    p = os.path.join(BASE, 'SPGI_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
