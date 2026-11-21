"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the FDX Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes FDX calendar 2026E (year ending 31-Dec-2026, six weeks after the valuation
date; Q1-Q3 actual, Q4 calibrated to guidance) and the template's 2026E-2030E become 2027E-2031E, so the DCF's explicit years start
in 2027E and net debt is taken at 31-Dec-2026 (the 2026E cash flow is in that net debt and is not counted again)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, LANN, NOTE

# template Model row -> FDX row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_da', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_usd', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'wc_dcf', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [LANN[y].c for y in range(2006, 2027)]            # legacy fiscal years FY2006-FY2026

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> FDX legacy fiscal years FY2006-FY2026."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},12,31)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,12,31)', f)
    return f

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'FedEx Corporation (FDX) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: adjusted operating income, adjusted EPS from continuing operations; adjusted EBITDA is a model definition) · USD millions · '
               'calendar years, continuing operations (after the FedEx Freight spin-off) · Live panel linked to Model — toggle scenario via Model!CV2. Bull and Bear panels are value '
               'snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the calendar-2026 guidance (revenue ~+12%, adjusted EPS $18.00–18.60).'),
        'G26': 15, 'H26': 15, 'S26': 17, 'T26': 17, 'AD26': 12, 'AE26': 12, 'AF26': 12,
    },
    'DCF': {
        'B2': 'DCF VALUATION — FEDEX CORPORATION (FDX)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.10, 'D7': 'Assumption: parcel / freight transportation peers (UPS, DHL Group, XPO, ODFL) ~1.0–1.3; cyclical volumes, high fixed costs, trade-policy exposure',
        'C9': 0.0525, 'D9': 'Sep-2026 notes: 5.75% USD notes due 2036, 4.00% / 4.625% EUR notes (Form 10-Q, Note 5); weighted-average rate on existing long-term debt 3.75%',
        'C10': 0.23, 'D10': 'Model 2027E+ effective tax rate (calendar-2026 guidance ~22.5%)',
        'C12': 0.15, 'D12': 'Net debt ~$11bn at 30-Sep-2026 (debt $19.4bn − cash − FedEx Freight stake + tariff refunds held) vs ~$70bn market cap ($300 × ~237m diluted shares); operating leases (~$15bn) are not treated as debt',
        'D15': 'Periods = (31-Dec of the year − today) / 365.25; cash flows assumed at year-end; calendar 2026E (ending 31-Dec-2026) is the base year',
        'B18': 'Adj. operating income less restructuring, integration & legal costs',
        'B21': 'plus D&A (depreciation and amortization)',
        'B22': '− Capex (capital expenditures) and acquisitions (none forecast)',
        'B26': 'Fade-period growth (2032E–36E; 4.0% → 3.0% linear)', 'I26': 0.04, 'M26': 0.03, 'C27': 0.025,
        'D32': ("FedEx's adjusted operating income already deducts depreciation, amortization, share-based compensation and operating lease rent (rent-as-opex basis: lease "
                'liabilities are not in net debt and right-of-use assets are not in invested capital flows); D&A is added back in row 21. Restructuring, exit, integration and '
                'legal costs (cash; adjusted out by the company) are deducted inside row 18. Non-operating retirement-plan income and mark-to-market adjustments are excluded. '
                'The change in working capital excludes the pass-through of customer tariff refunds (excluded from net debt). Proceeds from the retained FedEx Freight stake '
                '(in net debt at carrying value) and from FedEx Supply Chain (received in Q4/26) are not in UFCF.'),
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt − InPost stake at 31-Dec-2026), rolled forward with capex − D&A + ΔWC.',
        'B48': 'Less: Net debt − InPost stake at carrying value (Model 2026E year end, 31-Dec-2026)',
        'D48': 'FDX: no noncontrolling interests. Net debt = debt − cash − FedEx Freight stake (fair value at 30-Sep-2026) + tariff refunds held; the 37% InPost consortium stake ($2.5bn, equity method) is added at carrying value. Year-end 2026E basis, so 2027E+ cash flows are not double counted.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (FedEx characteristics)',
        'C78': 0.07, 'D78': 'Model adjusted operating income CAGR 2026–31E: mid-single-digit revenue growth (volume + yield) with margin expansion from Network 2.0 / one FedEx cost reductions → ~7% NOPAT growth (assumption)',
        'C79': 0.10, 'D79': 'Capital-intensive integrated air-ground network (capex ~4% of revenue); returns on incremental capital near the cost of capital historically (FY2006–FY2026 ROIC in the Model), improving with network consolidation',
        'C80': 10, 'D80': 'Scale network and brand in a three-player global market, offset by price competition, e-commerce mix and labour / purchased-transportation cost inflation',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. operating income less restructuring, integration & legal costs',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: 2028E year-end net debt − InPost stake (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: 2026E year-end net debt − InPost stake',
        'B108': 'FDX market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'FedEx Corporation — Operating Performance (fiscal years FY2012–FY2025) and Model Forecast (calendar 2026E–2031E)',
        'B3': ('USDm · Linked to Model. FY2012–FY2025: fiscal years ended 31 May incl. FedEx Freight, as originally reported; 2026E onward: calendar years, continuing operations '
               '(basis break between FY2025 and 2026E; 2026E growth is vs calendar 2025 on the same basis). Bars = contribution to revenue growth (pp). Adjusted EBITDA = model definition (adjusted operating income + D&A). '
               'ROIC / RONTA on adjusted operating income.'),
        'B8': 'U.S. Domestic / parcel segments contribution to growth (pp)', 'B9': 'International, freight & other contribution to growth (pp)', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   Express U.S. Domestic revenue y/y %', 12: 'Adjusted EBITDA (model)',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted Net Income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenue'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: U.S. Domestic / Parcel vs. International, Freight &amp; Other Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}
CHART_COLS = [(f'FY{y}', LANN[y].c) for y in range(2012, 2026)] + [(f'{y}E', ANN[y].c) for y in range(2026, 2032)]

def build_charts(ws):
    for i, (lab, mc) in enumerate(CHART_COLS):
        c = L(3 + i)
        ws[f'{c}7'] = lab
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_a"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_b"]}+0,0)'
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
    cm = Comment('P/E on adjusted EPS from continuing operations (company definition). FDX at $300 trades at ~16x 2026E adjusted EPS ($18.30 guidance mid-point). '
                 'Exit multiples are assumptions: Base 15x, Bull 17x, Bear 12x, in line with a cyclical, capital-intensive transportation network.', 'FDX model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'FDX model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 31-Dec of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
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
    (Charts!C:V = FY2012-2031E) and cached values removed so Excel redraws from the FDX cells."""
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
