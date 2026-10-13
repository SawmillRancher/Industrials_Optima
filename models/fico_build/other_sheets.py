"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the FICO Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes FICO FY2026E (fiscal year ended 30-Sep-2026, two weeks before the valuation
date; Q1-Q3 actual, Q4 calibrated to guidance) and the template's 2026E-2030E become FICO FY2027E-FY2031E, so the DCF's explicit years
start in FY2027E and net debt is taken at 30-Sep-2026."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> FICO row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_op', 182: 'd_dep', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_sc', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'capex_tot', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2026)]

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> FICO FY2006-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},9,30)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,9,30)', f)
    return f

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Fair Isaac Corporation (FICO) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Non-GAAP figures (company definition: non-GAAP net income / EPS; model non-GAAP operating income and adjusted EBITDA) · USD millions · fiscal years ended 30 September · '
               'Live panel linked to Model — toggle scenario via Model!CG2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               'FY2026E = Q1–Q3 actual + Q4 calibrated to the FY26 guidance (revenue $2.53bn, non-GAAP EPS $42.43).'),
        'G26': 30, 'H26': 30, 'S26': 38, 'T26': 38, 'AD26': 20, 'AE26': 20, 'AF26': 20,
    },
    'DCF': {
        'B2': 'DCF VALUATION — FAIR ISAAC CORPORATION (FICO)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Oct-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.10, 'D7': 'Assumption: credit-data and analytics peers (EFX, TRU, MCO, SPGI, VRSK) ~0.9–1.2; higher financial leverage (net debt ~3.5x EBITDA) and mortgage-score pricing risk',
        'C9': 0.06, 'D9': '2025 Senior Notes 6.00% (due 2033) and 2026 Senior Notes 6.25% (due 2034); term loan 5.86% and revolver 5.64% at 30-Jun-2026 (Q3 FY26 10-Q)',
        'C10': 0.25, 'D10': 'Model non-GAAP effective tax rate FY2027E+ (9M FY26 25.4%; FY2025 24.3%)',
        'C12': 0.25, 'D12': 'Debt ~$5.6bn at 30-Jun-2026 vs ~$16bn market cap ($740 × ~21.8m diluted shares)',
        'D15': 'Periods = (30-Sep of fiscal year − today) / 365.25; cash flows assumed at fiscal year-end (30 September); FY2026E (ended 30-Sep-2026) is the base year',
        'B18': 'Adj. EBITA after SBC less restructuring & acquisition costs',
        'B21': 'plus depreciation & software amortization',
        'B22': '− Capex (PP&E + capitalized software) and acquisitions (M&A lever 2027E–31E)',
        'B26': 'Fade-period growth (2032E–36E; 8.0% → 5.0% linear)', 'I26': 0.08, 'M26': 0.05, 'C27': 0.04,
        'D32': ("FICO's non-GAAP measures exclude share-based compensation (~7% of revenue); the model NOPAT deducts it (row 18 = adjusted EBITDA − depreciation − SBC − restructuring) "
                'and taxes the result at the non-GAAP rate. Acquired-intangible amortization is nil. Restructuring (the Oct-2026 workforce reduction, mostly in FY2026) is a cash cost. '
                'Row 22 includes capitalized internal-use software and any M&A from the lever (Base $0); the fade period and terminal value assume no acquisitions. Operating leases '
                '(~$17m) are left in operating costs and excluded from net debt.'),
        'D43': 'Opening IC = Model FY2026E book IC (stockholders\' deficit + net debt at 30-Sep-2026), rolled forward with capex + M&A − depreciation + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model FY2026E year end, 30-Sep-2026)',
        'D48': 'FICO: no noncontrolling interests; net debt (debt − cash − marketable securities) at the base-year end (≈ valuation date) so that FY2027E+ cash flows are not double counted.',
        'B50': 'Diluted shares (m, Model FY2026E period end)',
        'D76': 'Rationale (Fair Isaac characteristics)',
        'C78': 0.11, 'D78': 'Model non-GAAP operating income CAGR FY2026–31E: B2B Scores pricing and platform software growth with stable Scores margins → ~10–12% NOPAT growth',
        'C79': 0.60, 'D79': 'Capital-light model: the FICO Score is embedded in US lending (90% of top lenders, release boilerplate) and Scores earn ~90% segment margins; book invested capital is small because of buybacks',
        'C80': 15, 'D80': 'Long competitive-advantage period from the score\'s entrenchment with lenders and the GSEs; risks: FHFA approval of alternative scores and bureau competition (VantageScore) — 10-K risk factors',
        'B90': 'VALUATION  —  Applied to FY2029E NOPAT',
        'B91': 'FY2029E Adj. EBITA after SBC less restructuring & acquisition costs',
        'B93': 'FY2029E NOPAT',
        'B95': 'Implied Enterprise Value (FY2029E basis)',
        'B96': 'Less: FY2028E year-end net debt + NCI (Model)',
        'B98': 'Diluted shares FY2029E (m, Model)',
        'B99': 'Implied share price FY2029 ($)',
        'B106': 'Plus: FY2026E year-end net debt + NCI',
        'B108': 'FICO market-implied EV/NOPAT (on FY2029E NOPAT)',
    },
    'Charts': {
        'B2': 'Fair Isaac Corporation — Operating Performance (FY2012–FY2025) and Model Forecast (FY2026E–FY2031E)',
        'B3': ('USDm · fiscal years ended 30 September · Linked to Model. Bars = contribution of each segment to total revenue growth (pp). Adjusted EBITDA = model definition '
               '(FICO publishes no EBITDA; excludes SBC). ROIC / RONTA on adjusted EBITA after SBC.'),
        'B8': 'Scores contribution to growth (pp)', 'B9': 'Software contribution to growth (pp)', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   Scores segment revenue y/y %', 12: 'Adjusted EBITDA (model)',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Non-GAAP Net Income',
            21: 'FDSO (m)', 23: 'Non-GAAP EPS — Diluted ($)', 26: 'P / E (x) — assumed (non-GAAP EPS)',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenue'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: Scores vs. Software Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_sc"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_sw"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_op"]}'
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
                if isinstance(c.value, str) and 'DATE(' in c.value:
                    c.value = fy_dates(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    for c0 in ('C', 'O', 'AA'):
        i = b[f'{c0}7'].column
        b.cell(7, i).value = '2026E'
        for k in range(1, 6): b.cell(7, i + k).value = f'{2026 + k}E'
        b.cell(7, i + 6).value = "26-'31 CAGR"
    from openpyxl.comments import Comment
    cm = Comment('P/E on non-GAAP EPS (company definition). At the $740 input price FICO trades at ~17x FY2026E non-GAAP EPS ($42.43 guided). Exit multiples are assumptions: '
                 'Base 30x, Bull 38x, Bear 20x, below FICO\'s FY2021–25 range given pricing and regulatory risk on mortgage scores.', 'FICO model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'FICO model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 30-Sep of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; FY2026E = Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["capex_tot"]}+Model!{a27}{R["cf_acq"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["v_nci"]}'
    d['C50'] = f'=Model!{a26}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
    d['P17'] = 'CAGR 27–31E'; d['Q17'] = 'CAGR 27–36E'
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
    (Charts!C:V = FY2012-FY2031E) and cached values removed so Excel redraws from the FICO cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
