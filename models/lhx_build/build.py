"""Build LHX_Model.xlsx from the MLM template (same layout, formatting and process as the prior models)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC
from spec2 import build_spec2

OUT = os.path.join(os.path.dirname(BASE), 'LHX_Model.xlsx')
G26 = MAN['guidance_fy26']
X25 = DATA['2025']['x']

# ====================================================================== inputs (V0)
def wc_inputs():
    q = X25
    rev, cogs = q['rev'], q['cogs']
    return {'dso': round(q['bs_ar'] / rev * 365), 'dio': round(q['bs_inv'] / cogs * 365), 'dpo': round(q['bs_ap'] / cogs * 365),
            'cl': round(q['bs_cl'] / rev, 3), 'ocl': round(q['bs_ocl'] / rev, 3)}
WC = wc_inputs()
WC['note'] = (f'Forecast inputs at fiscal-year-end (2-Jan-2026) levels on FY2025 revenue / cost of revenue (DSO {WC["dso"]}d, inventory {WC["dio"]}d, payables {WC["dpo"]}d, '
              f'contract liabilities {WC["cl"]:.1%} and other current liabilities {WC["ocl"]:.1%} of revenue); year ends are compared with year ends. Contract assets are solved in 2026E (cash-from-operations guidance).')
YRS = range(FYC + 1, FYL + 1)
def yr(*v): return dict(zip(YRS, v))

V0 = {
    'out_hdr': 'FY26 guidance — Q3-26 release (29-Oct-2026)',
    'out_note': ('Revenue $23.5–23.7bn (low end raised from $23.2bn), GAAP diluted EPS $12.25–12.35 (raised from $11.80–12.00), segment operating margin low 16%, cash from operations $3.6bn, '
                 'capital expenditures ~$600m, free cash flow $3.0bn; Space & Mission Systems ~$11.9bn at mid 10%, Communications & Spectrum Dominance ~$7.9bn at mid 25%, Missile Solutions ~$4.1bn at low 12%. '
                 'Source: Form 8-K Ex. 99.1 (EDGAR). The "2028 Financial Framework" mentioned in the Q1-26 release is not filed on EDGAR and is not used (unverified).'),
    'outlook': [
        ('out_rev', '  FY26 revenue ($m)', tuple(G26['revenue']), 'm', 'Guided $23.5–23.7bn (8-K 29-Oct-2026). Drives the Q4/26E revenue calibration.'),
        ('out_eps', '  FY26 GAAP diluted EPS ($)', tuple(G26['gaap_eps']), 'ps', 'Guided $12.25–12.35 (8-K 29-Oct-2026). Drives the Q4/26E segment-margin calibration.'),
        ('bb26', '  Q4/26E share repurchases ($m)', (300.0, 150.0, 75.0), 'm', '9M 2026 $598m ($73m in Q3; 259,000 shares at $282.50 in fiscal August); $1,629m left on the $3.0bn authorization at 2-Oct-2026. Not guided: assumption.'),
    ],
    'points': [
        ('pt_rev_sms', '  FY26 Space & Mission Systems revenue guidance ($m)', 11900.0, 'm', 'Guided ~$11.9bn (prior ~$11.7bn).'),
        ('pt_rev_csd', '  FY26 Communications & Spectrum Dominance revenue guidance ($m)', 7900.0, 'm', 'Guided ~$7.9bn (prior ~$8.0bn).'),
        ('pt_rev_ms', '  FY26 Missile Solutions revenue guidance ($m)', 4100.0, 'm', 'Guided ~$4.1bn (unchanged; Space Technology disposal group sold 3-Aug-2026).'),
        ('pt_m_sms', '  FY26 Space & Mission Systems margin guidance', 0.105, 'pct', 'Guided "mid 10%" — read as 10.5% (interpretation).'),
        ('pt_m_csd', '  FY26 Communications & Spectrum Dominance margin guidance', 0.255, 'pct', 'Guided "mid 25%" — read as 25.5% (interpretation).'),
        ('pt_m_ms', '  FY26 Missile Solutions margin guidance', 0.122, 'pct', 'Guided "low 12%" — read as 12.2% (interpretation).'),
        ('pt_m_tot', '  FY26 segment operating margin guidance', 0.162, 'pct', 'Guided "low 16%" — read as 16.2% (interpretation; information row).'),
        ('pt_inter', '  Q4/26E intersegment revenue ($m)', -85.0, 'm', 'Q1 −91, Q2 −82, Q3 −80.'),
        ('pt_other', '  Q4/26E other revenue outside the segments ($m)', -5.0, 'm', 'Amortization of the $386m program investment asset over 20 years as a reduction of revenue (−$5m in Q3-26).'),
        ('pt_amort', '  Q4/26E amortization of acquisition-related intangibles ($m)', 135.0, 'm', 'FY2025 10-K schedule: $632m for 2026; 9M actual $497m (Q3 $147m after the Space Technology sale).'),
        ('pt_acq', '  Q4/26E acquisition, divestiture & transaction-related expenses ($m)', 10.0, 'm', 'Q2 $10m, Q3 $9m (Missile Solutions carve-out / planned public offering costs). Assumption.'),
        ('pt_cother', '  Q4/26E other unallocated corporate items ($m)', 40.0, 'm', '9M 2026 $142m incl. deferred-compensation fair-value changes ($35m) and the Q2 segment investment offset ($39m). Assumption.'),
        ('pt_dep', '  Q4/26E depreciation & other amortization ($m)', 115.0, 'm', '9M 2026 $340m (total D&A $837m less acquisition-related amortization $497m).'),
        ('pt_pens', '  Q4/26E non-service FAS pension income ($m)', 74.0, 'm', 'Q1 $75m, Q2 $75m, Q3 $74m (earnings appendix).'),
        ('pt_othno', '  Q4/26E other non-operating income, net ($m)', 0.0, 'm', 'Investment gains and fair-value changes are not forecast.'),
        ('pt_int', '  Q4/26E interest expense, net ($m)', 118.0, 'm', 'Q3 $116m; $1.0bn notes issued 5-Nov-2026 ahead of the Dec-2026 / Jan-2027 maturities ($1.8bn). Assumption.'),
        ('pt_etr', '  Q4/26E effective tax rate', 0.15, 'pct', '9M 2026 14.6% (Q3 14.9%). Not guided in the release: assumption.'),
        ('pt_pref', '  Q4/26E subsidiary preferred stock deemed dividend ($m)', 19.0, 'm', 'Q3-26 $19m (accretion of the mezzanine balance toward the $1,422m redemption value at 17-Apr-2031).'),
        ('pt_cfo', '  FY26 cash from operations guidance ($m)', float(G26['cfo']), 'm', 'Guided ~$3.6bn (9M $2,223m). Drives the Q4/26E working-capital calibration.'),
        ('pt_capex', '  FY26 capital expenditures guidance ($m)', float(G26['capex']), 'm', 'Guided ~$600m (9M $386m).'),
        ('pt_fcf', '  FY26 free cash flow guidance ($m)', float(G26['fcf']), 'm', 'Guided $3.0bn (CFO − capital expenditures; information row).'),
    ],
    'lev': (1.75, 1.5, 1.25),
    'lev_note': ('Net debt (after cash and short-term investments) $7,975m at 2-Oct-2026 = 1.9x company TTM EBITDA (4.3x at FY2023 after Aerojet Rocketdyne, 3.3x FY2024, 2.7x FY2025). No leverage target is published in the filings: '
                 'the levels are assumptions. Target = leverage up to which surplus cash is returned via buybacks; below it free cash flow accumulates. Bull = more buybacks (higher target).'),
    'blocks': [
        ('SMS_G', 'SMS_G (Space & Mission Systems revenue y/y)', 0.02, -0.03, [0.06, 0.06, 0.05, 0.05, 0.04],
         '2026E ~+11% (9M +13%: missionized ISR aircraft, classified space, FAA mission networks, F-35); backlog $22.3bn at Q3-26 (1.9x revenue; book-to-bill 1.0–1.7x in 2026).', 'pct', False),
        ('CSD_G', 'CSD_G (Communications & Spectrum Dominance revenue y/y)', 0.02, -0.03, [0.05, 0.05, 0.04, 0.04, 0.04],
         '2026E ~+4% (9M +3%: international resilient communications, night vision, Next Generation Jammer); backlog $10.9bn after 1.9x book-to-bill in Q3-26 (NGJ-LB $876m).', 'pct', False),
        ('MS_G', 'MS_G (Missile Solutions revenue y/y)', 0.03, -0.05, [0.08, 0.16, 0.14, 0.12, 0.10],
         ('2026E ~+8% reported (Q3 organic +17%). 2027E reported growth is held back ~9pp by the Space Technology sale (3-Aug-2026; $350m of 9M 2026 revenue). Backlog doubled to $20.0bn in Q3-26 '
          '(THAAD $6.3bn and PAC-3 MSE $4.7bn seven-year undefinitized propulsion contracts; book-to-bill 11.8x); DoW $1bn investment funds capacity.'), 'pct', False),
        ('SMS_M', 'SMS_M (Space & Mission Systems segment margin)', 0.0075, -0.01, [0.106, 0.108, 0.110, 0.112, 0.113],
         'FY26 guided mid 10% (FY25 9.8%, FY24 10.3% recast; 9M 2026 10.4%). Fixed-price development EAC risk (2025 net unfavourable EACs $98m).', 'pct', False),
        ('CSD_M', 'CSD_M (Communications & Spectrum Dominance segment margin)', 0.0075, -0.015, [0.253, 0.253, 0.253, 0.253, 0.253],
         'FY26 guided mid 25% (FY25 25.4%, FY24 23.0% recast; 9M 2026 25.7% incl. investment and asset-sale gains). International mix supports margins; held near 25%.', 'pct', False),
        ('MS_M', 'MS_M (Missile Solutions segment margin)', 0.01, -0.015, [0.125, 0.130, 0.135, 0.138, 0.140],
         'FY26 guided low 12% (FY25 9.6% incl. $85m goodwill impairment; 9M 2026 12.3%). Volume leverage on solid-rocket-motor production ramps vs. start-up of new facilities.', 'pct', False),
        ('MNA', 'M&A_spend (acquisitions, $m)', 0.0, 0.0, [0.0, 0.0, 0.0, 0.0, 0.0],
         'No acquisition since Aerojet Rocketdyne (Jul-2023); the company has been a net seller (CAS, antenna, AOT, Space Technology). Base none; lever kept for scenarios (assumption).', 'm', True),
    ],
    'other_rev': -19.0,
    'other_rev_note': ('History: corporate / divested non-reportable businesses (Commercial Aviation Solutions to 28-Mar-2025). 2027E+: amortization of the $386m program investment asset '
                       '(DoW strategic investment) over 20 years as a reduction of revenue (~$19m a year).'),
    'ae_acq': yr(40.0, 20.0, 20.0, 20.0, 20.0),
    'cother_pct': 0.007,
    'cother_note': 'FY2025 0.7% of segment revenue on the recast basis ($158m); 9M 2026 0.8%. Input (assumption).',
    'b2b_q4': 1.0, 'b2b': 1.1,
    'b2b_note': 'Book-to-bill 1.3x in FY2025; 1.4x / 1.2x / 3.2x in Q1–Q3 2026 (Q3 incl. $11bn of THAAD / PAC-3 propulsion awards). Forecast input: 1.0x in Q4/26E, 1.1x thereafter (assumption).',
    'mna_note': 'Scenario lever M&A_spend (Base none). Funded from cash / commercial paper (debt schedule).',
    'mna_mult_note': 'Aerojet Rocketdyne (Jul-2023): $4.7bn net consideration on ~$2.3bn of revenue (~2.1x); Viasat Tactical Data Links (Jan-2023): $1.97bn. 2.0x input (assumption).',
    'mna_int_note': 'PPAs: Aerojet Rocketdyne intangibles $2.84bn of $4.7bn (60%); Tactical Data Links $755m of $1.97bn (38%).',
    'amort_sched': yr(532.0, 459.0, 403.0, 386.0, 370.0),
    'amort_note': ('FY2025 10-K (2-Jan-2026): 2026 $632m, 2027 $532m, 2028 $459m, 2029 $403m, 2030 $386m, thereafter $2.3bn; 2031 $370m is an assumption. The Space Technology intangibles ($372m) were held for sale '
                   'at year-end 2025 and sold 3-Aug-2026.'),
    'dep_pct': 0.020,
    'dep_note': 'FY2025 2.1% of revenue ($455m); 9M 2026 1.9%. Depreciation of PP&E plus amortization of capitalized software and other assets. Input.',
    'sbc_pct': 0.012,
    'pens': yr(280.0, 270.0, 260.0, 250.0, 240.0),
    'pens_note': ('Non-service component of FAS pension and OPEB income (expected return on plan assets less interest cost and amortization), below operating income; non-cash. FY2025 $356m, 9M 2026 $224m. '
                  'Q4/26E point estimate; 2027E+ input, drifting down with de-risking (assumption — the 2026 pension outlook is in the earnings presentation, not filed on EDGAR).'),
    'pens_cf_ratio': 0.93,
    'pens_cf_note': ('History: net periodic benefit income and pension contributions as shown in the cash-flow statement (2017–18 include voluntary contributions). '
                     'Forecast: −93% of the non-service FAS pension income (9M 2026: net periodic benefit income $209m vs $224m; service cost offsets), no contributions; accretes the net pension asset.'),
    'etr': 0.16,
    'etr_note': 'FY2025 16.9%; 9M 2026 14.6% (FY2024 5.3% with discrete benefits). Q4/26E point estimate; 2027E+ input 16% (assumption).',
    'pref_div': yr(90.0, 95.0, 100.0, 100.0, 31.0),
    'pref_note': ('Accretion of the redeemable subsidiary Series A preferred stock (DoW, $1bn, 17-Apr-2026) to its $1,422m redemption value at 17-Apr-2031, deducted from net income available to common shareholders '
                  '(Q2-26 $14m, Q3-26 $19m). 2027E+ phasing is an assumption. A Qualified IPO of the Missile Solutions business (expected by 31-Dec-2027) would convert the preferred into subsidiary common stock: not modelled (no terms filed).'),
    'mezz_note': ('$987m at 2-Oct-2026 (initial $1,070m − $89m deferred tax − $27m costs + $33m deemed dividends); + deemed dividends. Deducted in the EV bridge together with the conversion-feature ($203m) and warrant ($163m) liabilities.'),
    'dps_q': 1.25, 'dps_g': 0.04,
    'dps_note': 'Quarterly dividend $1.25 from Jan-2026 ($1.20 in 2025; 25th consecutive annual increase). 2027E+: prior year × (1 + growth).',
    'e_trate': 0.24,
    'e_trate_note': 'Published periods: implied by the company tax effect. Q1-26 onward (model rebuild): 24% (US federal 21% + state; assumption).',
    'def_q4': 20.0, 'def_ae': 50.0,
    'capex_note': '2026E: FY26 guidance ~$600m. 2027E+: revenue × capex %.',
    'capex_pct': yr(0.030, 0.030, 0.028, 0.026, 0.025),
    'capex_pct_note': ('FY2025 1.9%, FY26 guidance ~2.5%. Elevated in 2027E–28E: about 60 new facilities to expand munitions / solid-rocket-motor capacity (the $973m of DoW proceeds is earmarked for it). Input (assumption).'),
    'bb_note': ('2026E: 9M actual + Q4 scenario input ($3.0bn authorization of Oct-2022, no expiry; $1,629m remaining at 2-Oct-2026). 2027E+ = leverage plug (surplus cash returned until net debt / adjusted EBITDA reaches the target; '
                'assumes the authorization is renewed).'),
    'ofin_ae': 0.0,
    'iss_q4': 0.3, 'iss_ae': 1.3, 'dil': 1.0,
    'iss_note': '9M 2026: shares outstanding fell 0.7m with 1.8m repurchased → ~1.1m issued (equity awards, share-based matching contributions). Input.',
    'ppe_dep_share': 0.85,
    'ppe_note': 'Roll-forward: prior − capex (negative cash flow) − depreciation (85% of depreciation & other amortization: assumption; the rest amortizes capitalized software / other assets) + acquired PP&E.',
    'iss_notes': {2026: 1000.0, 2027: 0.0, 2028: 1880.0, 2029: 1655.0, 2030: 5.0, 2031: 0.0},
    'repay': {2026: 550.0, 2027: 1256.0, 2028: 1880.0, 2029: 1655.0, 2030: 5.0, 2031: 0.0},
    'mat': {2026: 1256.0, 2027: 1880.0, 2028: 1655.0, 2029: 5.0, 2030: 0.0, 2031: 0.0},
    'iss_notes_note': MAN['debt']['new_notes'] + ' 2027E: the Jan-2027 maturity is pre-funded by the Nov-2026 issue; 2028E+: maturities refinanced with new notes (assumption).',
    'repay_note': ('FY2025 10-K maturities: 2026 $660m, 2027 $1,256m, 2028 $1,880m, 2029 $1,155m, 2030 $5m, thereafter $5,973m. 2026E Q4: $550m 3.85% notes (Dec-2026); 2027E incl. $1,250m 5.40% notes (Jan-2027); '
                   '2029E incl. the new $500m 5.200% notes; 2031E maturities are inside "thereafter" (not disclosed by year; nil assumed).'),
    'debt_note': MAN['debt']['at_2026_10_02'],
    'min_cash': 1000.0,
    'min_cash_note': 'Cash $2,471m + short-term investments $550m at 2-Oct-2026 (FY2025 $1,069m; FY2024 $615m). Input (assumption).',
    'r_debt': 0.049,
    'r_debt_note': 'FY2025 net interest $597m on ~$11.7bn average debt (5.1%); fixed-rate notes 1.80%–7.00%+; new 2029 / 2032 notes at 5.2% / 5.4%. Input (assumption).',
    'r_cash': 0.04,
    'r_cash_note': 'Assumption (~short-term US rates); interest income is netted in "Interest expense, net".',
    'wc': WC,
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $255.00 (provided by the user, 20-Nov-2026; ~$48bn market cap). Latest SEC-filed reference prices: $282.50 average repurchase price in fiscal August 2026 and '
                '$260.56 tax-withholding price in fiscal September 2026 (Q3-26 10-Q Part II Item 2); update to market'),
    'rev_guid_note': 'Company FY26 revenue guidance $23.5–23.7bn (29-Oct-2026; initial $23.0–23.5bn on 29-Jan-2026). Drives the revenue calibration.',
    'eps_guid_note': 'Company FY26 GAAP diluted EPS guidance $12.25–12.35 (29-Oct-2026; initial $11.30–11.50). The company guides GAAP EPS from 2026 (non-GAAP EPS no longer published). Drives the segment-margin calibration.',
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
    if kw.get('ann') and (col.q or col.tp): return None, False        # ratio rows: annual columns only (the six-month transition period is not annualised)
    if k in HISTK:
        v = hist_value(row, col)
        if v is not None: return v, True
        if 'hist_in' in kw and xget(pkey(col), 'adj_basis') == 'model': return kw['hist_in'], True
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
        if kw.get('flow') and not row.spec2 and any(x in kw for x in ('qe', 'qe_in', 'fc', 'all')): return S26(row.key), False
        key = first(kw, ('fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    if k == 'AE':
        if 'ae_in' in kw:
            v = kw['ae_in']; return (v[col.year] if isinstance(v, dict) else v), True
        key = first(kw, ('ae', 'fc', 'all'))
        return (kw[key](), False) if key else (None, False)
    return None, False

# ====================================================================== writers
CAGR_G = {'is_rev', 'g_rev', 'seg_rev', 'sms_rev', 'csd_rev', 'ms_rev', 'seg_oi', 'sms_oi', 'csd_oi', 'ms_oi', 'g_oi', 'o_adj', 'r_adj', 'r_ebitda', 'is_oi', 'd_dda', 'e_adjni', 'e_eps',
          'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_gp', 'is_sga', 'd_amort', 'd_dep', 'is_ni', 'is_nic', 'eps_dil', 'dps', 'k_bk', 'k_orders'}
CAGR_A = {'sms_m', 'csd_m', 'ms_m', 'seg_m', 'g_oim', 'o_adj_m', 'r_adj_m', 'is_gm', 'is_oi_m', 'r_ebit_m', 'gm_rev', 'gm_sms', 'gm_csd', 'gm_ms', 'gm_gm', 'gm_ebitda_m', 'gm_seg_m',
          'gm_op_m', 'gm_net_m', 'gm_sga', 'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'k_b2b',
          'd_sga', 'd_dep_pct', 'd_sbc_pct', 'wc_nwc_p', 'is_etr', 'fcf_eb', 'c_other_p'}
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
                if t: comment(cell, f'Company lines ({pkey(col)}): {t}', 420, 130)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
    rc = CELL_COMMENTS.get(row.key, {})
    for c, t in rc.items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2031]}{r}/{A[2026]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2020]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2015]}{r})^(1/10.5)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2013]}{r})^(1/12.5)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2027, 2032))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in list(range(2016, 2020)) + list(range(2020, 2026)))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2013, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = 'Source: L3Harris / Harris earnings releases (Form 8-K Item 2.02, Ex. 99.1; 2022–Q3-23 quarterly investor letters) — '
LABEL_SOURCES = {
    'sms_rev': ('Source: 2026 earnings releases (summary financial results) and the Q3-26 earnings appendix (8-K 29-Oct-2026, Ex. 99.2) for the 2025 quarters; FY2024 from the Q4-25 release Table 9 (Segment Recast). '
                'The company did not recast 2024 quarters or earlier periods to the three-segment structure.'),
    'sms_bk': 'Source: Q3-26 earnings appendix (contractual backlog by segment, $bn to one decimal; 2025 quarters and 2026).',
    'seg_pub': REL + 'segment tables. 2025 and FY2024 on the recast three-segment basis (earnings appendix / Q4-25 Table 9); earlier periods as originally reported (legacy structures).',
    'lr_rf': REL + 'business segment information, as originally reported in each period (FY2013–FY2019 from the Form 10-K where it differs from the release).',
    'c_amort': REL + 'reconciling lines between segment operating income and operating income ("Unallocated corporate items" tables; segment notes of the 10-K / 10-Q). 2025 on the recast basis (earnings appendix).',
    'k_orders': REL + 'orders, book-to-bill and backlog as published (FY2013–15 total orders not published; funded book-to-bill only in 2020–Q3-23; total backlog from the 10-K / 10-Q in $bn). 2025–26 from the Q3-26 earnings appendix.',
    'is_rev': REL + 'condensed consolidated statements of income / operations, as originally reported; annual columns from the Form 10-K / 10-KT. Operating income is not printed on the face in most periods to 2023 (computed).',
    'is_pens': ('Source: 10-K / 10-Q retirement-benefit notes and releases ("Pension adjustment" 2019–21; "Non-service FAS pension income" from 2022); Q3-26 earnings appendix for 2025–26. '
                'Where the statement shows one combined non-operating line, it is split with the disclosed pension income; Q4 = fiscal year − nine months where not split (cell comments on the row below).'),
    'd_dda': REL + 'condensed consolidated statements of cash flows (year to date; discrete quarters derived). FY2013–18 include the separate "Amortization of intangible assets from Exelis Inc. acquisition" line.',
    'd_sbc': 'Source: cash-flow statements (share-based compensation and share-based matching contributions under defined contribution plans); XBRL company facts (ShareBasedCompensation) where the statement combines it with pension income.',
    'o_seg_pub': REL + 'segment operating income total as published (definition in force — see the definition row).',
    'o_pub': REL + '"Adjusted EBIT and Adjusted EBIT Margin" reconciliations (published FY2019 to 2021).',
    'r_ebitda_pub': 'Source: Q3-26 earnings appendix (8-K 29-Oct-2026, Ex. 99.2), net debt leverage ratio slide: EBITDA FY2023, FY2024, 4Q25, FY2025, 1Q26–3Q26.',
    'e_pub': REL + 'reconciliations of GAAP to non-GAAP EPS (income from continuing operations per diluted share to FY2021; diluted EPS from 2022). Not published in FY2014 and from Q1-26.',
    'cf_ni': REL + 'condensed consolidated statements of cash flows (year to date; discrete quarters derived: Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M; Q4/19 = transition period − Q3/19); annual columns from the 10-K / 10-KT.',
    'fcf_pub': REL + 'free cash flow / adjusted free cash flow reconciliations (company definition in force — definition row).',
    'bs_cash': REL + 'condensed consolidated balance sheets (period ends), with current / non-current totals and equity detail from the 10-Q / 10-K where the release statement is unclassified.',
    'bs_shares': 'Source: Forms 10-K / 10-Q (shares issued and outstanding at period end).',
    'ppa_cons': 'Source: FY2023 10-K business-combination note (Viasat Tactical Data Links, closed 3-Jan-2023; Aerojet Rocketdyne, closed 28-Jul-2023, preliminary allocation); 10-KT for the L3 merger (29-Jun-2019; all-stock).',
    'ds_total': 'Source: release balance sheets; FY2025 10-K debt note (maturities) and Q3-26 10-Q Note I; 8-K of 5-Nov-2026 (2029 / 2032 notes).',
    'bs_mezz': MAN['dow_investment']['text'],
    'cf_divest': MAN['space_tech_sale']['text'],
}
CELL_COMMENTS = {}
def comments_setup():
    for p in [k for k in DATA if xget(k, 'seg_recast')]:
        col = [c for c in COLS if pkey(c) == p]
        if not col: continue
        CELL_COMMENTS.setdefault('seg_oi', {})[col[0].c] = ('Recast to the three-segment structure effective Q1-26 (latest filing presenting the period). ' + (xget(p, 'seg_orig') or ''))[:900]
    CELL_COMMENTS.setdefault('sms_rev', {})[A[2024]] = MAN['recast_appendix']['recast_2024']['note']
    CELL_COMMENTS.setdefault('sms_rev', {})[QC[(2025, 1)].c] = MAN['recast_appendix']['note']
    CELL_COMMENTS['is_rev'] = {
        A[2016]: 'FY2016 as originally reported ($7,467m incl. CapRock and government IT services). Re-presented in the FY2017 10-K for discontinued operations: revenue $5,992m, continuing EPS $4.87, non-GAAP EPS $5.14.',
        A[2018]: 'FY2018 as originally reported ($6,182m). Re-presented in FY2019 for ASC 606 (full retrospective) and ASU 2017-07: revenue $6,168m, continuing EPS $5.78, non-GAAP EPS $6.39.',
        A[2015]: 'FY2015 (53 weeks) includes Exelis Inc. from 29-May-2015.',
        TP.c: 'Six-month fiscal transition period 29-Jun-2019 – 3-Jan-2020 (27 weeks; Form 10-KT), the first period after the L3 merger (29-Jun-2019). Not comparable with Harris FY2019.',
        A[2020]: 'First full fiscal year of L3Harris; no comparable prior-year column (the company\'s "four quarters ended 3-Jan-2020" and pro forma comparatives are not used).',
        A[2024]: 'FY2024 = 53 weeks (Q4 14 weeks). FY2025 quarters: 12 / 13 / 14 / 13 weeks.'}
    CELL_COMMENTS['eps_chk'] = {}
    CELL_COMMENTS['e_round'] = {A[2013]: 'FY2013: EPS under the two-class method (participating securities): published continuing EPS $4.16 vs $4.19 computed on diluted shares; the difference sits in this line.'}
    CELL_COMMENTS['fcf'] = {}

DEFS = {}
def defs_setup():
    q = lambda y, n: QC[(y, n)].c
    DEFS['o_def'] = {
        'C': ('FY2013–18 (Harris): segment operating income after pension costs; reconciling items = unallocated corporate expense, eliminations (FY2016: + Exelis amortization)',
              'Segments: RF Communications / Integrated Network Solutions / Government Communications Systems to FY2015; Communication Systems / Space and Intelligence Systems / Electronic Systems / Critical Networks FY2016; three segments FY2017–19.'),
        A[2019]: ('FY2019–2021: segment operating income includes FAS pension income; a "Pension adjustment" (non-service FAS pension income) is a reconciling line', 'FY2019 10-K (ASU 2017-07) and the L3Harris releases to Q4-21.'),
        q(2019, 3): ('2H19: four L3Harris segments (IMS, SAS, CS, AS); merger costs, acquisition-related amortization, divestiture gains unallocated', None),
        q(2022, 1): ('2022: three segments (Aviation Systems dissolved); segments bear CAS pension cost; FAS/CAS operating adjustment unallocated (2021 recast by the company, not in the model)',
                     'Q1-22 investor letter. The Q3-22 goodwill impairment ($802m) and 2023 impairments sit inside GAAP segment operating income.'),
        q(2023, 3): ('Q3-23: Aerojet Rocketdyne becomes the fourth segment (acquired 28-Jul-2023)', None),
        q(2023, 4): ('Q4-23: "segment operating income" / adjusted segment operating income becomes the company non-GAAP measure (excl. unallocated items and significant items)', None),
        q(2024, 4): ('Q4-24: adjusted segment operating income also excludes segment-level impairments ($24m CS)', None),
        A[2024]: ('FY2024 annual: recast to the three-segment structure (Q4-25 release Table 9); 2024 quarters as originally reported', None),
        q(2025, 1): ('2025: recast to the three-segment structure of 2026 (Q3-26 earnings appendix); as originally reported: adjusted segment operating income $3,451m for FY2025', None),
        q(2026, 1): ('Q1-26+: three segments (SMS, CSD, MS); segment operating income = operating income + unallocated corporate items and other, net; FAS/CAS adjustment no longer unallocated', None),
    }
    DEFS['r_def'] = {
        'C': ('FY2013–22: the company published no EBITDA — model figure on the company\'s later definition (net income + taxes + net interest + D&A)', None),
        A[2023]: ('FY2023+: company EBITDA published in the Q3-26 earnings appendix (FY2023, FY2024, 4Q25, FY2025, 1Q26–3Q26)', None),
    }
    DEFS['e_def'] = {
        'C': ('FY2013: non-GAAP EPS from continuing operations excl. restructuring and debt-prepayment charges', None),
        A[2014]: ('FY2014: no non-GAAP EPS published (adjusted = GAAP)', None),
        A[2015]: ('FY2015–19: excl. Exelis / L3 deal and integration costs, restructuring, impairments, debt refinancing, tax reform (acquisition amortization NOT added back)',
                  'FY2015 5.14; FY2016 5.70 (re-presented 5.14 for discontinued operations); FY2017 5.53; FY2018 6.50 (re-presented 6.39 for ASC 606); FY2019 8.29. The model keeps the figures as first published.'),
        q(2019, 3): ('Q3-19 to Q4-24: also adds back amortization of acquisition-related intangibles, inventory step-up, merger integration, divestiture items, impairments, LHX NeXt (from 2023)', None),
        q(2022, 1): ('2022+: bridge starts from diluted EPS (no discontinued operations)', 'Q3-22 non-GAAP EPS uses 192.8m diluted shares (GAAP loss: 191.3m) — difference in the rounding line.'),
        q(2025, 1): ('Q1-25: amortization of acquisition-related intangibles no longer added back (2024 recast by the company: FY24 $13.10 → $9.70); pension adjusted non-GAAP EPS also published',
                     'The model keeps FY2024 as originally published ($13.10; quarters 3.06 / 3.24 / 3.34 / 3.47).'),
        q(2026, 1): ('Q1-26+: not published (GAAP EPS guidance) — model rebuild of the FY2025 definition; tax effect at the input rate', None),
    }
    DEFS['fcf_def'] = {
        'C': ('FY2013–16: free cash flow = CFO − net additions of PP&E', None),
        A[2017]: ('FY2017–18: adjusted free cash flow (adds back voluntary pension contributions $400m / $300m)', None),
        A[2019]: ('FY2019–Q3-23: adjusted free cash flow (adds back cash merger transaction / integration costs; + PP&E sale proceeds from Q4-20; cash taxes on divestiture gains from Q3-21; LHX NeXt cash in Q3-23)', None),
        q(2023, 4): ('Q4-23: "free cash flow" (no LHX NeXt add-back); 2024–25 "adjusted free cash flow" incl. severance and, from Q4-24, PP&E disposal proceeds', None),
        q(2026, 1): ('2026: free cash flow = CFO − capex + PP&E disposal proceeds (Q1–Q2); from Q3-26 CFO − capex only (prior periods recast by the company)', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: FY26 revenue and GAAP EPS guidance end-points (high / mid / low), '
            'Q4/26E buybacks, 2027E–2031E segment revenue growth, segment margins, M&A spend and the leverage target for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = 'L3Harris Technologies, Inc. (NYSE: LHX) — 3-Statement Financial Model'
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD; shares in millions) · FY2013–FY2019 = Harris Corporation fiscal years ended the Friday nearest 30 June; '
                '2H19 TP = six-month transition period to 3-Jan-2020; from 2020 fiscal years ended the Friday nearest 31 December · Source: Forms 10-K / 10-KT / 10-Q, Form 8-K earnings releases '
                '(Ex. 99.1), investor letters and earnings appendix, deal / financing 8-Ks, SEC EDGAR (CIK 0000202058; Harris Corp until 25-Jun-2019); XBRL company facts; '
                'investor-relations releases at l3harris.com are the same documents as filed on EDGAR; guidance from EDGAR-filed releases only (the "2028 Financial Framework" is not filed — not used)')
    ws['B4'] = ('Basis notes: as originally reported, except the segments, which are on the three-segment structure of 2026 for 2025 (quarters) and FY2024 (annual) as recast by the company; earlier segment '
                'structures are memo rows. L3 Technologies merged 29-Jun-2019 (Harris = accounting acquirer; FY2019 is pre-merger Harris); Exelis from 29-May-2015; Viasat Tactical Data Links 3-Jan-2023; '
                'Aerojet Rocketdyne 28-Jul-2023; divestitures: airport security May-2020, military training / CPS Jul-2021, antennas May-2024, Commercial Aviation Solutions 28-Mar-2025, '
                'Space Technology (60%) 3-Aug-2026; $1bn DoW preferred investment in Missile Solutions 17-Apr-2026. 2020 has no comparable prior year. '
                'Q4/26E calibrated to the FY26 revenue, GAAP EPS and cash-from-operations guidance (29-Oct-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10.5Y CAGR', '12.5Y CAGR'], ["26-'31", "20-'25", "FY15-'25", "FY13-'25"]):
        ws[f'{c}6'] = a; ws[f'{c}7'] = b
    comment(ws[f'{CAGR[2]}6'], 'Harris FY2015 (June year-end) to L3Harris 2025: 10.5 years; includes the L3 merger (2019) — registrant growth, not organic.', 300, 80)

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
        p = os.path.join(BASE, f'LHX_{scen}.xlsx')
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
    p = os.path.join(BASE, 'LHX_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main()
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
