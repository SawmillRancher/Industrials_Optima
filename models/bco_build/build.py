"""Build BCO_Model.xlsx from the MLM template (same layout, formatting and process as the prior models).

    python3 build.py [--snap] [--recalc]

--snap fills the Bull / Bear snapshot panels of the Bull-Base-Bear tab (rebuild with the switch on each case, recalculate,
paste values); --recalc stores the calculated values in the workbook (LibreOffice Calc via the xlsx skill's recalc.py)."""
import sys, copy, os, json
from openpyxl.styles import Font
from fw import *
import fw
from spec import build_spec, scen_layout, SCEN_ROWS, SC, SEG, SEGK
from spec2 import build_spec2, PPA

OUT = os.path.join(os.path.dirname(BASE), 'BCO_Model.xlsx')
G = MAN['guidance']; NC = MAN['ncr_atleos']; SP = MAN['standalone_projections']
YRS = range(FYC + 1, FYL + 1)
def yd(*v): return dict(zip(YRS, v))
def only27(v): return {y: (v if y == 2027 else 0.0) for y in YRS}
Q3X = DATA['Q3-26']['x']

# ====================================================================== inputs (V0)
ppa = {k: only27(v) for k, v in NC['ppa'].items() if k not in ('net_assets', 'pf_goodwill')}
ppa.update(cashcons=only27(NC['cash_consideration']), shares=only27(NC['shares_issued']), awards=only27(NC['equity_awards']))
V0 = {
    'out_hdr': 'Q4 2026 guidance — third-quarter 2026 release (4-Nov-2026)',
    'out_note': G['text'],
    'outlook': [
        ('out_rev', '  Q4 2026 revenues ($m)', tuple(G['q4_rev']), 'm', 'Guided $1,365–1,415m. Drives the Q4/26E organic-growth calibration.'),
        ('out_eb', '  Q4 2026 non-GAAP adjusted EBITDA ($m)', tuple(G['q4_ebitda']), 'm', 'Guided $275–295m. Drives the Q4/26E segment-margin calibration.'),
        ('out_eps', '  Q4 2026 non-GAAP EPS ($) — memo', tuple(G['q4_eps']), 'ps', 'Guided $2.45–2.80 (information row; compare the model).'),
        ('out_fcf', '  2026 free cash flow conversion (FCF before dividends ÷ adjusted EBITDA)', tuple(G['fw_fcf_conv']), 'pct', '2026 non-GAAP framework: 40–45%. Drives the Q4/26E working-capital calibration.'),
        ('bb26', '  Q4/26E share repurchases ($m)', (50.0, 0.0, 0.0), 'm', '9M 2026 $30.2m (average $125.12); $720m left on the 2025 Repurchase Program; NCR Atleos closing pending (assumption).'),
    ],
    'points': [
        ('pt_dda', '  Q4/26E depreciation and amortization ($m)', 78.0, 'm1', 'Q1–Q3/26: $79.7m / $79.1m / $76.0m.'),
        ('pt_amort', '  Q4/26E amortization of acquisition-related intangibles ($m)', 13.0, 'm1', '9M 2026 $43.3m (~$14m a quarter); 10-K schedule for 2026 $53.6m.'),
        ('pt_sbc', '  Q4/26E share-based compensation ($m)', 7.0, 'm1', 'Non-GAAP basis 9M 2026 $20.2m.'),
        ('pt_int', '  Q4/26E interest expense ($m)', 66.0, 'm1', 'Q3/26 $66.0m.'),
        ('pt_oth', '  Q4/26E interest and other nonoperating income ($m; non-GAAP basis)', 0.5, 'm1', '9M 2026 non-GAAP: pre-tax income $375.9m − (non-GAAP operating profit $566.3m − interest $192.4m) ≈ +$2.0m.'),
        ('pt_nci', '  Q4/26E net income attributable to noncontrolling interests ($m)', 2.5, 'm1', 'Q1–Q3/26: $2.7m / $2.9m / $2.0m.'),
        ('pt_etr', '  Non-GAAP effective tax rate', 0.272, 'pct', 'Company estimate of the full-year 2026 non-GAAP effective tax rate (third-quarter release).'),
        ('pt_itax', '  Tax rate on adjusting items', 0.20, 'pct', '9M 2026: $47.0m of tax on $221.9m of adjusting items (21%).'),
        ('pt_transf', '  Q4/26E NCR Atleos acquisition and transformation costs ($m)', 40.0, 'm1', 'Q1–Q3/26: $38.9m / $36.4m / $45.7m (assumption for Q4).'),
        ('pt_capex', '  Q4/26E capital expenditures ($m)', 50.0, 'm1', '9M 2026 $112.1m; Q4/25 $47.7m (assumption; not guided).'),
        ('pt_corp', '  Q4/26E corporate expenses — factor on (prior-year quarter × 9M y/y)', 0.75, 'x2',
         '9M 2026 corporate expenses are up 33% y/y (currency losses, incentive accruals); Q3/26 was $36.2m. Factor 0.75 → ~$42m in Q4 (assumption).'),
    ],
    'lev': (2.5, 2.0, 1.5),
    'lev_note': ('Company target: net leverage 2.0–3.0x by the end of 2027 after the NCR Atleos closing (deal release, 26-Feb-2026). Threshold = leverage below which surplus cash goes to buybacks '
                 '(Bull = higher, more buybacks); above it free cash flow repays the prepayable bank debt. Model net debt = total debt − cash and cash equivalents, which is lower than the company\'s own measure (the company also deducts cash held by cash-management operations), so the thresholds sit at and below the low end of the company range.'),
    'blocks': [
        ('NA_ORG', 'NA_ORG (North America organic growth)', 0.015, -0.02, [0.03, 0.035, 0.035, 0.035], '9M 2026 +3% (Q3 +1%); 2025 +3–4%. AMS / DRS growth vs flat-to-declining traditional cash-in-transit.', 'pct', False),
        ('LA_ORG', 'LA_ORG (Latin America organic growth)', 0.02, -0.03, [0.04, 0.045, 0.045, 0.045], '9M 2026 +3% (Q3 +2%); inflation-driven pricing in Argentina is offset in the currency line.', 'pct', False),
        ('EU_ORG', 'EU_ORG (Europe organic growth)', 0.015, -0.02, [0.03, 0.03, 0.03, 0.03], '9M 2026 +3% (Q3 +2%).', 'pct', False),
        ('ROW_ORG', 'ROW_ORG (Rest of World organic growth)', 0.02, -0.04, [0.09, 0.08, 0.07, 0.06], '9M 2026 +12% (Q3 +14%): Brink\'s Global Services and AMS / DRS in the Middle East and Asia.', 'pct', False),
        ('NA_M', 'NA_M (North America segment margin)', 0.008, -0.015, [0.154, 0.158, 0.162, 0.165], '9M 2026 14.5% (FY2025 14.2%, FY2023 ~12%): mix shift to AMS / DRS and productivity.', 'pct', False),
        ('LA_M', 'LA_M (Latin America segment margin)', 0.008, -0.015, [0.180, 0.183, 0.185, 0.185], '9M 2026 17.4% (FY2025 18.9%).', 'pct', False),
        ('EU_M', 'EU_M (Europe segment margin)', 0.008, -0.015, [0.150, 0.154, 0.157, 0.160], '9M 2026 13.9% (Q3 17.1%; FY2025 12.4%).', 'pct', False),
        ('ROW_M', 'ROW_M (Rest of World segment margin)', 0.008, -0.02, [0.250, 0.250, 0.250, 0.250], '9M 2026 24.8% (FY2025 22.3%).', 'pct', False),
        ('NCR_REV', 'NCR_REV (NCR Atleos revenue vs its management projections)', 0.02, -0.04, [0.0, 0.0, 0.0, 0.0],
         'Base = NCR Atleos February 2026 Standalone Projections (424B3): revenue $4,607m in 2027E to $4,774m in 2030E (+1–2% a year). 9M 2026 operating income $423m vs $322m in 9M 2025.', 'pct', False),
        ('NCR_M', 'NCR_M (NCR Atleos adjusted EBITDA margin vs projections, pp)', 0.005, -0.015, [0.0, 0.0, 0.0, 0.0],
         'Base = projections: 21.1% in 2027E rising to 22.0% in 2030E (2026E 20.4%).', 'pct', False),
        ('SYN', 'SYN (cost-synergy realisation, % of the $200m run-rate target)', 0.15, -0.30, [1.0, 1.0, 1.0, 1.0],
         'Company target: $200m annual run-rate cost synergies within three years of closing (network / field-service insourcing, SG&A, procurement).', 'pct', True),
    ],
    'acq_q4': {s: Q3X.get(f'g_{s}_acqp', 0.0) for s in SEGK}, 'fx_q4': {s: Q3X.get(f'g_{s}_fxp', 0.0) for s in SEGK},
    'acq_ae': {'na': 0.0, 'la': 0.0, 'eu': 0.0, 'row': yd(-0.06, 0.0, 0.0, 0.0)},
    'fx_ae': {s: 0.0 for s in SEGK},
    'acq_note': ('Q4/26E = Q3/26 effect (Malaysia subsidiaries deconsolidated in Q3/26: −$24m, −12% of Rest of World). 2027E −6%: analyst estimate (two more quarters of the disposition effect, '
                 '~$48m on ~$845m).'),
    'fx_note': 'Q4/26E = Q3/26 currency effect by segment (assumption: rates held). 2027E+: 0 (no currency forecast).',
    'corp_pct': -0.029,
    'nc_tgl': 1, 'nc_frac': yd(round(362 / 365, 4), 1.0, 1.0, 1.0),
    'nc_rev': {int(k): v for k, v in NC['proj_rev'].items()}, 'nc_eb': {int(k): v for k, v in NC['proj_ebitda'].items()},
    'syn_phase': yd(0.25, 0.60, 0.90, 1.0), 'nc_dep_pct': 0.042, 'nc_sbc_pct': 0.008, 'nc_capex_pct': 0.035,
    'nc_integ': yd(150.0, 100.0, 50.0, 0.0),
    'sp_rev': {int(k): v for k, v in SP['rev'].items()}, 'sp_eb': {int(k): v for k, v in SP['ebitda'].items()},
    'amort_sched': yd(*[MAN['amort_sched'][str(y)] for y in YRS]),
    'dep_pct': 0.044, 'sga_pct': 0.168, 'sbc_pct': 0.005, 'etr': 0.272, 'itax': 0.20,
    'oth_ae': 5.0, 'nci_ae': yd(11.0, 11.5, 12.0, 12.5), 'transf_in': yd(20.0, 10.0, 0.0, 0.0),
    'dps_q': Q3X['dps'], 'dps_g': 0.05, 'cover_sh': round(MAN['buyback']['cover_shares'], 3),
    'def_q4': 0.0, 'def_ae': 0.0, 'ppe_sale': 10.0, 'divnci': -5.0, 'ofin': -25.0, 'iss_ae': 0.25, 'dil': yd(0.7, 0.7, 0.7, 0.7),
    'capex_pct': 0.035,
    'ppa': ppa, 'bridge': NC['bridge'], 'refinanced': NC['refinanced'],
    'prepayable_q3': round(MAN['debt']['revolver'] + MAN['debt']['term_loans'], 1),
    'iss_notes': yd(600.0, 0.0, 400.0, 0.0), 'repay': yd(600.0, 0.0, 400.0, 0.0),
    'cur': {2026: 957.0, 2027: 445.0, 2028: 845.0, 2029: 445.0, 2030: 445.0},
    'min_cash': {2026: 2000.0, 2027: 2580.0, 2028: 2580.0, 2029: 2580.0, 2030: 2580.0},
    'r_fixed': yd(0.065, 0.077, 0.077, 0.077), 'r_rev': 0.060, 'r_deal': 0.095, 'fees': yd(12.0, 8.0, 8.0, 8.0),
    'r_note': ('Q3/26 interest expense $66.0m ≈ 6.4% annualised on $4.16bn of debt: scheduled debt ($2,477m: 4.625% 2027, 6.5% 2029 and 6.75% 2032 senior notes, other facilities, leases, '
               'local short-term borrowings) ~6.5%; prepayable bank debt ~6.0% (SOFR + margin). From 2028E the scheduled-debt rate blends in the NCR Atleos notes (assumption 9.5%) and the '
               'refinancing of the 4.625% notes.'),
    'px': MAN['price']['px'],
    'px_note': ('VALUATION — share price input $114.00 (provided by the user on 20-Nov-2026; not an SEC-filed price — update to market). EDGAR reference points: $125.12 average repurchase price '
                'in 9M 2026 (Q3-26 10-Q), $104.79 close on 21-May-2026 (424B3)'),
    'rev_guid_note': 'Company Q4 2026 revenue guidance $1,365–1,415m (third-quarter release, 4-Nov-2026). Drives the organic-growth calibration.',
    'eb_guid_note': 'Company Q4 2026 non-GAAP adjusted EBITDA guidance $275–295m (third-quarter release). Drives the segment-margin calibration.',
}

# ====================================================================== compute engine
def hist_value(row, col):
    kw = row.kw
    if 'hval' in kw:
        v = kw['hval'](col)
        if v is not None: return v
    path = kw.get('data')
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
CAGR_G = {'is_rev', 'g_rev', 'seg_rev', 'na_rev', 'la_rev', 'eu_rev', 'row_rev', 'na_op', 'la_op', 'eu_op', 'row_op', 'seg_op', 'o_adj', 'g_adj', 'r_adj', 'r_ebitda', 'is_op',
          'd_dda', 'e_adjni', 'e_eps', 'cf_cfo', 'fcf', 'bs_ta', 'bs_teq', 'sh_dil', 'is_sga', 'is_cor', 'is_cont_att', 'is_ni', 'eps_cont', 'dps', 'r_ebit'}
CAGR_A = {'na_m', 'la_m', 'eu_m', 'row_m', 'seg_m', 'g_adjm', 'o_adj_m', 'r_adj_m', 'is_op_m', 'r_ebit_m', 'gm_rev', 'gm_org', 'gm_na', 'gm_la', 'gm_eu', 'gm_row', 'gm_ebitda_m',
          'gm_op_m', 'gm_net_m', 'gm_sga', 'gm_cor', 'gm_adjop_m', 'fcf_m', 'fcf_conv', 'capex_pct', 'ra_roic', 'rn_ronta', 'roe', 'lv_x', 'd_sga', 'd_sbc_pct',
          'wc_nwc_p', 'is_etr', 'fcf_eb', 'corp_pct', 'na_org', 'la_org', 'eu_org', 'row_org', 'g_org', 'na_g', 'la_g', 'eu_g', 'row_g', 'g_rev_g', 'hr_dda'}
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
                if t: comment(cell, f'Company items ({pkey(col)}): {t}', 420, 130)
            if row.kw.get('shnote') and col.kind in HISTK:
                t = xget(pkey(col), 'sh_ng_note')
                if t: comment(cell, t, 380, 100)
        elif row.arch == 'growth' and col.kind in HISTK:
            set_color(cell, GRAY)
        else:
            set_color(cell, BLACK)
            lk = row.kw.get('labkey')
            if lk and row.key == 'e_tax' and col.kind in HISTK:
                t = xget(pkey(col), lk)
                if t and xget(pkey(col), 'eps_ng_pub') is not None: comment(cell, f'Company per-share reconciliation ({pkey(col)}), $ per share: {t}', 440, 150)
    rc = CELL_COMMENTS.get(row.key, {})
    for c, t in rc.items(): comment(ws[f'{c}{r}'], t)
    if row.key in CAGR_G:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(({A[2030]}{r}/{A[2025]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2020]}{r})^(1/5)-1,"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2015]}{r})^(1/10)-1,"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(({A[2025]}{r}/{A[2006]}{r})^(1/19)-1,"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = '0%;\\(0%\\);"n/m"'
    elif row.key in CAGR_A:
        ws[f'{CAGR[0]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2026, 2031))}),"n/m")'
        ws[f'{CAGR[1]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2021, 2026))}),"n/m")'
        ws[f'{CAGR[2]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2016, 2026))}),"n/m")'
        ws[f'{CAGR[3]}{r}'] = f'=IFERROR(AVERAGE({",".join(f"{A[y]}{r}" for y in range(2006, 2026))}),"n/m")'
        for c in CAGR: ws[f'{c}{r}'].number_format = NF['pct']
    t = LABEL_SOURCES.get(row.key)
    if t: comment(ws.cell(r, 2), t)

REL = "Source: Brink's earnings releases (Form 8-K, Ex. 99.1) — "
XB = ("Source: Brink's Forms 10-K / 10-Q via XBRL company facts (value as first filed for the period = as originally reported); FY2006–08 from the FY2008 Form 10-K "
      "(continuing operations after the Brink's Home Security spin-off of 31-Oct-2008). ")
LABEL_SOURCES = {
    'na_rev': REL + '"Segment Results" quarterly tables of each year\'s fourth-quarter release (2019 from the fourth-quarter 2020 release, recast to the current four segments; 2026 from the third-quarter 2026 release).',
    'na_org': REL + '"nQ\'YY vs" table of each quarterly release: organic change, acquisitions / dispositions and currency effect in whole $m, divided by the prior-year quarter of the same table. Annual columns = Σ of the four quarterly tables.',
    'corp': REL + 'segment tables ("Corporate" to 2023, "Corporate expenses" from 2024).',
    'l3_na_rev': REL + 'fourth-quarter 2017 and 2018 releases (three-segment basis).',
    'm_us_rev': REL + 'fourth-quarter 2014, 2015 and 2016 releases (nine reporting units; 2013 comparatives exist only on a recast basis and are not used).',
    'i_intl_rev': ("Source: Forms 10-K segment notes, each year as originally reported (FY2006–08 from the FY2008 10-K); 2013 quarters from the fourth-quarter 2013 release (GAAP block)."),
    'nc_sa_rev': 'Source: joint proxy statement / prospectus (424B3, 27-May-2026): unaudited pro forma information and "Certain Unaudited Prospective Financial Information"; NCR Atleos XBRL company facts (CIK 1974138).',
    'is_rev': XB + 'Quarters 2013–Q3/14 recast: comparatives as filed in the following year\'s 10-Q (discontinued operations re-presented at year end), consistent with the release tables (cell comments). Q4 = full year − nine months.',
    'd_dda': XB + 'Cash-flow statement (year to date; discrete quarters derived).',
    'd_restr': REL + '"Segment Results" tables: other items not allocated to segments, grouped; the company\'s labels and amounts per period are in the cell comments.',
    'o_pub': REL + '"Non-GAAP Results Reconciled to GAAP" (2014+); column-format reconciliations 2009–13 (2009–12 annual: each year\'s fourth-quarter release, as first published).',
    'r_ebitda_pub': REL + '"Non-GAAP Results Reconciled to GAAP — Adjusted EBITDA" (EBITDA shown from 2018).',
    'e_pub': REL + '"Non-GAAP Results Reconciled to GAAP — EPS" (2014+); earlier years as first published.',
    'cf_ni': XB + 'Cash flow extracted year to date; discrete quarters = differences. Cash = cash and cash equivalents to 2017; cash, cash equivalents and restricted cash from 2018 (ASU 2016-18).',
    'bs_cash': XB + 'Derived lines (other current assets, other assets, other current liabilities, other liabilities) = reported subtotals − the lines shown.',
    'fcf_pub': REL + 'free cash flow before dividends reconciliation (published by quarter from 2021; annual 2020).',
    'sh_basic': XB + 'No stock splits in the period.',
    'ds_total': 'Source: balance sheets; Q3-26 Form 10-Q debt note; 8-K of 6-Apr-2026 (amended and restated credit agreement); 424B3 (NCR Atleos financing).',
    'ppa_cashcons': 'Source: 424B3 (27-May-2026), unaudited pro forma condensed combined financial information, notes 3 and 5 (preliminary; balance sheet at 31-Mar-2026).',
}
CELL_COMMENTS = {}
def comments_setup():
    for col in COLS:
        per = pkey(col)
        if per and xget(per, 'recast_note'):
            CELL_COMMENTS.setdefault('is_rev', {})[col.c] = 'Recast basis. ' + xget(per, 'recast_note')
    CELL_COMMENTS['o_pub'] = {A[2010]: 'As first published in the fourth-quarter 2010 release ($166.6m; EPS $1.71). Re-presented as $188.3m / $1.99 in the 2011 release (U.S. retirement-plan costs also excluded).',
                              A[2011]: 'As first published in the fourth-quarter 2011 release ($205.9m; EPS $1.90). Re-presented as $226.6m / $2.32 in the 2012 release (discontinued operations).'}
    CELL_COMMENTS['eu_rev'] = {QC[(2025, 1)].c: 'Q1–Q3/25 as re-presented in the fourth-quarter 2025 release (about $20m a quarter moved from Rest of World to Europe); the growth decomposition rows are as first published.'}

DEFS = {}
def defs_setup():
    DEFS['o_def'] = {
        'C': ('2006–08: no non-GAAP measures published — n/p', None),
        A[2009]: ('2009–13: "adjusted" / non-GAAP results, column-format reconciliations — total of the items only (in "other")',
                  'Items in those years: Venezuela currency / remeasurement items, acquisition gains and losses, restructuring, employee-benefit settlements, U.S. retirement plans (from the 2011 release), tax items.'),
        A[2014]: ('2014: non-GAAP excludes "other items not allocated to segments" (FX devaluation in Venezuela, 2014 reorganization and restructuring, acquisitions / dispositions, Mexican settlement losses, U.S. retirement plans) — total only',
                  'The fourth-quarter 2014 release also showed an "adjusted non-GAAP" variant (Venezuela at 50 VEF/USD); the model uses "non-GAAP".'),
        A[2015]: ('2015+: Venezuela operations excluded in full; retirement plans excluded from operating profit (to 2016)', None),
        A[2017]: ('2017: retirement plans now below operating profit (ASU 2017-07 presentation); three-segment basis', None),
        A[2018]: ('2018: Argentina highly inflationary impact excluded from Q3/18; Venezuela deconsolidated 30-Jun-2018; reporting compliance', None),
        A[2019]: ('2019–22: internal loss; Chile antitrust matter (2021+); change in allowance estimate and ship loss matter (2022)', None),
        A[2023]: ('2023+: transformation initiatives; non-routine auto loss matter', None),
        A[2024]: ('2024+: DOJ / FinCEN investigations; corporate expenses shown separately; non-GAAP revenues = GAAP', None),
        A[2026]: ('2026: NCR Atleos acquisition costs (with transformation initiatives), incident-related losses, non-routine legal matters', None),
    }
    DEFS['r_def'] = {
        'C': ('to 2015: adjusted EBITDA not published — model measure (EBITDA + other items not allocated to segments)', None),
        A[2016]: ('2016–17: company adjusted EBITDA = non-GAAP income from continuing operations + non-GAAP interest, taxes, D&A (+ share-based compensation from 2017); items derived',
                  'First published in the second-quarter 2016 release. The model rebuilds it from net income; the adjusting-items row is derived from the published total in 2016–17.'),
        A[2018]: ('2018+: reconciled from net income attributable to Brink\'s; EBITDA published; share-based compensation added back', None),
        A[2020]: ('2020+: marketable securities (gain) loss added back', None),
    }
    DEFS['e_def'] = {
        'C': ('2006–08: no non-GAAP EPS published — n/p', None),
        A[2009]: ('2009–13: adjusted / non-GAAP EPS as first published (column-format reconciliations)', None),
        A[2014]: ('2014+: non-GAAP EPS excl. other items not allocated to segments; interim tax-rate adjustment to the full-year non-GAAP rate', None),
        A[2017]: ('2017+: retirement plans, prepayment penalties, U.S. tax reform items excluded; "share adjustment" in GAAP-loss periods', None),
        A[2022]: ('2022+: valuation allowance on tax credits excluded', None),
        A[2025]: ('2025: tax on return of capital (Argentina) and Argentina debt-securities impairment excluded', None),
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
    comment(ws[f'{NOTE}2'], 'Scenario toggle. Choose Bull / Base / Bear. Drives: Q4 2026 revenue and adjusted-EBITDA guidance end-points (high / mid / low), the 2026 free-cash-flow conversion, '
            'Q4/26E buybacks, 2027E–2030E segment organic growth and margins, the NCR Atleos revenue / margin / synergy levers and the leverage threshold for 2027E+ buybacks '
            f'(scenario table {SL}:{SNOTE}).')
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(f'{NOTE}2')
    ws['B2'] = "The Brink's Company (NYSE: BCO) — 3-Statement Financial Model"
    ws['B3'] = ("US GAAP · USD millions (per-share data in USD; shares in millions) · calendar fiscal year · Source: Brink's Forms 10-K / 10-Q (XBRL company facts, values as first filed), "
                'Form 8-K earnings releases (Ex. 99.1), deal and financing 8-Ks and the NCR Atleos joint proxy statement / prospectus (424B3), SEC EDGAR (CIK 78890; The Pittston Company to May-2003); '
                "investor-relations releases at investors.brinks.com are the same documents as filed on EDGAR · Q4 2026 guidance and the 2026 framework are from the 8-K release (verified on EDGAR); "
                'management projections in the 424B3 are not guidance')
    ws['B4'] = ("Basis notes: statements as originally reported (quarters of 2013–Q3/14 recast for discontinued operations, as re-presented at year end; cell comments). FY2006–08: continuing operations per the "
                "FY2008 10-K after the Brink's Home Security spin-off (31-Oct-2008); FY2006–07 income statement only. Segments: four segments from 2019 (North America, Latin America, Europe, Rest of World); "
                'earlier structures as memo rows. Venezuela deconsolidated 30-Jun-2018; Argentina highly inflationary from Q3/18. Acquisitions: Dunbar (Aug-18), G4S cash businesses (2020), PAI (Apr-21), '
                'NoteMachine (Oct-22); NCR Atleos pending (closing expected early January 2027; own block, outside the 2026 guidance). Q4/26E calibrated to the Q4 2026 guidance (4-Nov-2026).')
    ws[f'{CAGR[0]}5'] = 'Forecast'
    for c in CAGR[1:]: ws[f'{c}5'] = 'Historical'
    ws['B6'] = '(USDm)'
    for col in COLS: ws[f'{col.c}6'] = col.label
    ws[f'{NOTE}6'] = 'Modelling Notes'
    for c, a, b in zip(CAGR, ['5Y CAGR', '5Y CAGR', '10Y CAGR', '19Y CAGR'], ["25-'30", "20-'25", "15-'25", "06-'25"]):
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

def main(with_other=True):
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
    if with_other:
        import other_sheets as osh
        osh.do_all(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(OUT)
    if with_other:
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
        p = os.path.join(BASE, f'BCO_{scen}.xlsx')
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
    p = os.path.join(BASE, 'BCO_recalc.xlsx')
    shutil.copy(OUT, p)
    res = recalc(p); print('recalc', res.get('status'), res.get('total_errors'))
    inject_values(OUT, p)
    os.remove(p)

if __name__ == '__main__':
    main(with_other='--model-only' not in sys.argv)
    if '--snap' in sys.argv: scenario_snapshots()
    if '--recalc' in sys.argv: store_values()
