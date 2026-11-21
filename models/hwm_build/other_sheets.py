"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the HWM Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: template 2025A -> HWM 2025A; template 2026E-2030E -> HWM 2026E-2030E (same calendar years as the template).
DCF: valuation net debt is taken at the end of 2026E, so the 2026E unlevered free cash flow is excluded by a flag (row 28)
to avoid double counting (playbook 5.7)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> HWM row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'd_da', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_ep', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2025].c, 'CA': ANN[2026].c, 'CB': ANN[2027].c, 'CC': ANN[2028].c, 'CD': ANN[2029].c, 'CE': ANN[2030].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2019, 2026)]
Y0C, YLC = 2020, 2030                      # Charts: years shown

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> HWM FY2019-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Howmet Aerospace Inc. (HWM) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA, adjusted net income, adjusted EPS) · USD millions · Live panel linked to Model — toggle scenario via '
               f'Model!{NOTE}2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the '
               'FY26 guidance of 29-Oct-2026 (revenue $10.29–10.31bn, Adjusted EBITDA $3.325–3.335bn).'),
        'G26': 30, 'H26': 30, 'S26': 34, 'T26': 34, 'AD26': 24, 'AE26': 24, 'AF26': 24,
    },
    'DCF': {
        'B2': 'DCF VALUATION — HOWMET AEROSPACE INC. (HWM)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources are not reachable from the build environment); update to market',
        'C6': 0.05, 'D6': 'Assumption: US implied equity risk premium ~4.5–5.5%',
        'C7': 1.10, 'D7': 'Assumption: aerospace engine and structures suppliers (GE Aerospace, TransDigm, HEICO, Safran, ATI, Carpenter) ~1.0–1.3; ~15% of sales in cyclical commercial transportation',
        'C9': 0.0475, 'D9': 'Investment grade; Mar-2026 issue: 3.750% Notes 2028, 3.900% Notes 2029 and 4.750% Notes 2036 (Q3-26 10-Q Note O); commercial paper 4.2%',
        'C10': 0.21, 'D10': 'Model 2027E+ effective tax rate (operational tax rate 20.3% in nine months 2026)',
        'C12': 0.04, 'D12': 'Net debt ~$3.9bn at 30-Sep-2026 vs ~$88bn market cap ($220 × ~400m diluted shares); ~1.3x LTM Adjusted EBITDA',
        'D15': 'Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end',
        'B18': 'Adj. EBIT (full-cost) less operating special items',
        'B21': 'plus D&A (depreciation + amortization of intangibles)',
        'B22': '− Capex (PP&E) and acquisitions (2026E incl. CAM / Brunner; M&A lever 2027E–30E)',
        'B26': 'Fade-period growth (2031E–35E; 8.0% → 5.0% linear)', 'I26': 0.08, 'M26': 0.05, 'C27': 0.035,
        'B28': '2026E UFCF inclusion flag (0 = excluded: year-end 2026E net debt in row 48 already reflects the 2026 cash flows)', 'D28': 0,
        'D32': ("Howmet's adjusted operating income already deducts amortization of acquired intangibles and stock-based compensation (neither is adjusted out), so NOPAT is on "
                'full-cost EBIT and total D&A is added back in row 21. Operating special items (acquisition and restructuring cash costs; nil in the forecast unless the M&A lever '
                'is used) are deducted inside row 18. The 2026E column is shown for the invested-capital roll-forward but is excluded from the valuation by the flag in row 28, '
                'because net debt is taken at the end of 2026E (after the CAM acquisition and 2026 buybacks). The fade period and terminal value assume no acquisitions.'),
        'D43': 'Opening IC = Model 2025A book IC (equity + net debt), rolled forward with capex + acquisitions (CAM / Brunner $1.9bn in 2026E) − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end)',
        'D48': 'HWM: no noncontrolling interests and no preferred stock (redeemed Q4-25). Pension and other postretirement liabilities (~$0.5bn) and the $250m off-balance-sheet receivables program are not deducted.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (Howmet Aerospace characteristics)',
        'C78': 0.12, 'D78': 'Model adjusted EBIT CAGR 2026–30E: ~10% sales growth (commercial aerospace build rates, engine spares, gas turbines) with segment-margin expansion → ~12% NOPAT growth',
        'C79': 0.30, 'D79': 'Proprietary airfoil casting and coating technology on sole- or dual-sourced engine positions with long-term agreements; capacity additions are underwritten by customer demand, so incremental returns are high; acquired growth (CAM at ~13x EBITDA) earns far less',
        'C80': 15, 'D80': 'Engine programs run for decades with a growing spares annuity (LEAP, GTF, F135, gas turbines); qualification barriers and a concentrated industry; exposure to aircraft build rates and truck cycles',
        'B90': 'VALUATION  —  Applied to 2028E NOPAT',
        'B91': '2028E Adj. EBIT less operating special items',
        'B108': 'HWM market-implied EV/NOPAT (on 2028E NOPAT)',
    },
    'Charts': {
        'B2': 'Howmet Aerospace — Operating Performance (2020–2025) and Model Forecast (2026E–2030E)',
        'B3': ('USDm · Linked to Model. Bars = contribution of Engine Products and of the other three segments to total sales growth (pp). Adjusted EBITDA = company definition; '
               'operating income = GAAP. ROIC / RONTA on adjusted EBIT (full-cost). The charts start in 2020, the first year with a post-separation balance sheet.'),
        'B8': 'Engine Products contribution to growth (pp)', 'B9': 'Other segments contribution to growth (pp)', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Sales', 10: '   Sales y/y %', 11: '   Engine Products sales y/y %', 12: 'Adjusted EBITDA',
            15: 'Operating Income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted Net Income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of sales'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Sales Growth: Engine Products vs. Other Segments Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for row in ws['C7:V21']:
        for c in row: c.value = None
    for i, y in enumerate(range(Y0C, YLC + 1)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_ep"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_oth"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_oi"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}17'] = f'={c}7'
        ws[f'{c}18'] = f'=IFERROR(Model!{mc}{R["ra_roic"]}+0,NA())'
        ws[f'{c}19'] = f'=IFERROR(Model!{mc}{R["rn_ronta"]}+0,NA())'
        ws[f'{c}20'] = f'=IFERROR(Model!{mc}{R["gm_ebitda_m"]}+0,NA())'
        ws[f'{c}21'] = f'=IFERROR(Model!{mc}{R["fcf_m"]}+0,NA())'

def do_all(wb):
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and 'Model!' in c.value:
                    h = hist_stat(c.value) if name == 'Bull-Base-Bear' else None
                    c.value = h or remap(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    from openpyxl.comments import Comment
    for row in b.iter_rows():
        for c in row: c.comment = None
    cm = Comment('P/E on adjusted EPS (company definition). HWM at $220.00 (user price, 20-Nov-2026) trades at ~40x 2026E adjusted EPS ($5.50 guided baseline) and ~33x the Base 2027E. '
                 'Exit multiples are assumptions: Base 30x, Bull 34x, Bear 24x applied to 2029E–2030E (2028E–2030E for Bear), converging toward aerospace-supplier peers as growth normalises.', 'HWM model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'HWM model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    for c in ('F', 'R'):                 # no price target in 2028E for Base / Bull: blank the implied-value rows instead of showing 0
        for r in range(47, 51): b[f'{c}{r}'] = None
    d = wb['DCF']
    a25, a26 = ANN[2025].c, ANN[2026].c
    d['D22'] = f'=Model!{a26}{R["cf_capex"]}+Model!{a26}{R["cf_acq"]}'
    d['D24'] = '=(D20+D21+D22+D23)*$D$28'
    d['D28'].number_format = '0'
    d['D34'] = f'=Model!{a25}{R["ra_ic"]}'
    d['P24'] = '=(H24/E24)^(1/(COLUMNS(E24:H24)-1))-1'; d['Q24'] = '=(M24/E24)^(1/(COLUMNS(E24:M24)-1))-1'      # UFCF CAGRs from 2027E (2026E excluded)
    d['P17'] = 'CAGR 26–30E (UFCF: 27–30E)'; d['Q17'] = 'CAGR 26–35E (UFCF: 27–35E)'
    build_charts(wb['Charts'])

def snapshot_values(wb, bull, bear):
    ws = wb['Bull-Base-Bear']
    cols = 'CDEFGHIJKL'
    for snap, off in ((bull, 'OPQRSTUVWX'), (bear, ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ'])):
        for (r, c), v in snap.items():
            tgt = f'{off[cols.index(c)]}{r}'
            cur = ws[tgt].value
            if isinstance(cur, str) and cur.startswith('='): continue
            if r in (7, 26): continue
            ws[tgt] = v

def inject_charts(path):
    """Replace openpyxl-rewritten chart parts with the template chart XML (combo charts, colours, layout), retitled, ranges kept
    (template Charts!C:V re-pointed to C:N = 2019-2030E) and cached values removed so Excel redraws from the HWM cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = t.replace('$V$', f'${L(2 + YLC - Y0C + 1)}$')
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
