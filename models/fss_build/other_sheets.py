"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the FSS Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes FSS 2026E (Q1-Q3 actual, Q4 calibrated to the outlook; the year ends about
two months after the valuation date) and the template's 2026E-2030E become FSS 2027E-2031E, so the DCF's explicit years start in 2027E
and net debt is taken at 31-Dec-2026 (no double counting of 2026 cash flow)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> FSS row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_esg', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
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
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> FSS 2006-2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def yr_shift(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},12,31)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,12,31)', f)
    return f

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Federal Signal Corporation (FSS) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: adjusted EBITDA, adjusted EPS) · USD millions · Live panel linked to Model — toggle scenario via Model!CG2. '
               'Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the FY26 outlook '
               '(net sales $2.61–2.64bn, adjusted EPS $5.20–5.32).'),
        'G26': 25, 'H26': 25, 'S26': 29, 'T26': 29, 'AD26': 19, 'AE26': 19, 'AF26': 19,
    },
    'DCF': {
        'B2': 'DCF VALUATION — FEDERAL SIGNAL CORPORATION (FSS)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.10, 'D7': 'Assumption: specialty-vehicle and municipal-equipment peers (Oshkosh, REV Group, Alamo Group, Terex) ~1.0–1.3; ~45% municipal demand dampens cyclicality',
        'C9': 0.055, 'D9': 'Senior secured credit facility at adjusted RFR + 1.00–1.75% (2025 Credit Agreement); marginal pre-tax cost ~5.5% (assumption)',
        'C10': 0.24, 'D10': 'Model 2027E+ effective tax rate (9M 2026 GAAP 23.5%)',
        'C12': 0.05, 'D12': 'Net debt ~$0.35bn at 30-Sep-2026 vs ~$7.0bn market cap ($114.00 × ~61.6m diluted shares); ~0.65x LTM adjusted EBITDA',
        'D15': 'Periods = (31-Dec of the year − today) / 365.25; cash flows assumed at year-end; 2026E (ends ~2 months after the valuation date) is the base year',
        'B18': 'Adj. EBIT (full-cost) less acquisition, restructuring & other cash items',
        'B21': 'plus D&A (depreciation incl. rental fleet + amortization of intangibles)',
        'B22': '− Capex, rental fleet investment and acquisitions (M&A lever 2027E–31E)',
        'B26': 'Fade-period growth (2032E–36E; 6.0% → 4.5% linear)', 'I26': 0.06, 'M26': 0.045, 'C27': 0.035,
        'D32': ("Federal Signal's adjusted EBIT (operating income + acquisition / integration, restructuring, purchase-accounting and other items) is after amortization of acquired "
                'intangibles and after stock-based compensation; total D&A is added back in row 21 because the recent intangibles and goodwill are tax-deductible (New Way, Hog, Mega). '
                'The adjusting items are deducted again as cash costs (row 18). Row 22 includes the rental fleet (inside operating cash flow in the filings) and the M&A lever in '
                '2027E–31E; the fade period and terminal value assume no new acquisitions.'),
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt at 31-Dec-2026), rolled forward with capex + rental fleet + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end, 31-Dec-2026)',
        'D48': 'FSS: no noncontrolling interests; net debt at the base-year end so that 2027E+ cash flows are not double counted.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (Federal Signal characteristics)',
        'C78': 0.09, 'D78': 'Model adjusted EBIT CAGR 2026–31E: mid-to-high-single-digit sales growth (municipal replacement demand, aftermarket, bolt-on acquisitions) and modest margin gains → ~9% NOPAT growth',
        'C79': 0.16, 'D79': 'Niche specialty-vehicle franchises (Vactor, Elgin, Guzzler, TBEI, Joe Johnson dealer network) with aftermarket and rental annuities; acquired growth earns ~10–14% pre-synergy on 1.1–1.7x sales',
        'C80': 12, 'D80': 'Leading positions in street sweepers, sewer cleaners and hydro-excavators sold to municipalities through dealer networks; acquisitive 80/20 operating model; exposure to municipal budgets and industrial cycles',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. EBIT less acquisition, restructuring & other cash items',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: 2028E year-end net debt + NCI (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: 2026E year-end net debt + NCI',
        'B108': 'FSS market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'Federal Signal Corporation — Operating Performance (2012–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · Linked to Model. Bars = contribution of each group to net-sales growth (pp; 2012–15 as originally reported, including Fire Rescue in the totals). '
               'Adjusted EBITDA = company definition (published from FY2013; model EBITDA before). ROIC / RONTA on adjusted EBIT (full-cost).'),
        'B8': 'Environmental Solutions contribution (pp)', 'B9': 'Safety and Security Systems contribution (pp)', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Net sales', 10: '   Net sales y/y %', 11: '   Environmental Solutions net sales y/y %', 12: 'Adjusted EBITDA',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted net income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of net sales'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Net Sales Growth: Environmental Solutions vs. Safety and Security Systems Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_esg"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_ssg"]}+0,0)'
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
                    c.value = yr_shift(c.value)
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
    cm = Comment('P/E on adjusted EPS (company definition). FSS at $114.00 trades at ~22x 2026E adjusted EPS (guided $5.20–5.32) and ~20x 2027E. Exit multiples are '
                 'assumptions: Base 25x, Bull 29x, Bear 19x applied to 2030E–31E (2029E–31E for Bear); the stock has traded at a premium to diversified industrials since 2021.', 'FSS model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'FSS model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 31-Dec of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    for col, y in zip('DEFGH', range(2027, 2032)):
        ay = ANN[y].c
        d[f'{col}22'] = f'=Model!{ay}{R["cf_capex"]}+Model!{ay}{R["cf_acq"]}+Model!{ay}{R["cf_rent"]}'
    d['I22'] = f'=(Model!{ANN[2031].c}{R["cf_capex"]}+Model!{ANN[2031].c}{R["cf_rent"]})*(1+I$26)'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_nci"]}'
    d['C50'] = f'=Model!{a26}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
    d['P17'] = 'CAGR 27–31E'; d['Q17'] = 'CAGR 27–36E'
    b['K2'] = f'=Model!${a26}${R["v_px"]}'
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
    (Charts!C:V = 2012-2031E) and cached values removed so Excel redraws from the FSS cells."""
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
