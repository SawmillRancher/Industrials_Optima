"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the GD Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes GD 2026E (Q1-Q3 actual, Q4 estimated; the year is ten and a half months
done at the 19-Nov-2026 valuation date) and the template's 2026E-2030E become GD 2027E-2031E, so the DCF's explicit years start in
2027E and net debt is taken at 31-Dec-2026."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> GD row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'g_bl_g', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh', 353: 'ppa_cons', 355: 'ppa_cons'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2026)]
UNMAPPED = set()

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        if r in MAP: r2 = R[MAP[r]]
        elif r == 2: r2 = 2
        else: UNMAPPED.add(r); r2 = r
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> GD FY2006-FY2025 annual columns."""
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
        'B2': 'General Dynamics Corporation (GD) — Bull / Base / Bear Case P&L Summary',
        'B3': ('GAAP figures (GD publishes no adjusted measures; model adjusted EBITDA = operating earnings + D&A, adjusted EPS = GAAP diluted EPS from continuing operations in every forecast period) · '
               'USD millions · calendar years · Live panel linked to Model — toggle scenario via Model!CG2. Bull and Bear panels are value snapshots generated from the Model with the switch set '
               'to each case. 2026E = Q1–Q3 actual + Q4 estimate (no company guidance on EDGAR; optional targets in the scenario table).'),
        'G26': 20, 'H26': 20, 'S26': 23, 'T26': 23, 'AD26': 16, 'AE26': 16, 'AF26': 16,
    },
    'DCF': {
        'B2': 'DCF VALUATION — GENERAL DYNAMICS CORPORATION (GD)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 0.85, 'D7': 'Assumption: defense primes (LMT, NOC, RTX, HII, LHX) ~0.5–0.9; Gulfstream business-jet cycle (~25% of revenue) adds cyclicality',
        'C9': 0.0475, 'D9': 'Aug-2035 4.950% notes issued May-2025 (8-K 7-May-2025); outstanding fixed-rate notes 2.25–4.95%; A-range credit',
        'C10': 0.175, 'D10': 'Model 2027E+ effective tax rate (FY2025 17.5%; 9M-26 17.6%)',
        'C12': 0.05, 'D12': 'Net debt ~$2.6bn at 4-Oct-2026 vs ~$99bn market cap ($362.97 × ~274m diluted shares); ~0.4x adjusted EBITDA',
        'D15': 'Periods = (Dec-31 of year − today) / 365.25; cash flows assumed at year-end; 2026E (ten and a half months done at the valuation date) is the base year',
        'B18': 'Adj. EBIT (= adjusted operating earnings, full-cost) less cash adjusting items',
        'B21': 'plus D&A (depreciation + amortization of intangibles and finance-lease ROU)',
        'B22': '− Capex and acquisitions (M&A lever 2027E–31E; Base nil)',
        'B26': 'Fade-period growth (2032E–36E; 5.0% → 3.5% linear)', 'I26': 0.05, 'M26': 0.035, 'C27': 0.03,
        'D32': ("GD's operating earnings already deduct amortization of intangibles and equity-based compensation (neither is adjusted out); D&A is added back in row 21. "
                'Adjusting items exist only in Q4-2012 (impairments, contract disputes, restructuring, inventory charges), so row 18 equals operating earnings in the forecast. '
                'Customer advances and deposits (progress payments, Gulfstream deposits) make working capital a source of cash as revenue grows (row 23 from the Model cash-flow statement). '
                'Row 22 includes the M&A lever (Base nil); the fade period and terminal value assume no acquisitions. Pension: non-service components sit in other, net (below EBIT); '
                'contributions are inside operating cash flow and are not separately modelled.'),
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt at 31-Dec-2026), rolled forward with capex + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end, 31-Dec-2026)',
        'D48': 'GD: no noncontrolling interests; net debt at the base-year end so that 2027E+ cash flows are not double counted. Operating leases (~$1.4bn) are not treated as debt.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (General Dynamics characteristics)',
        'C78': 0.08, 'D78': 'Model operating-earnings CAGR 2026–31E: record $220bn backlog (Columbia / Virginia submarines, Gulfstream G700 / G800) → high-single-digit revenue growth with modest margin expansion → ~8% NOPAT growth',
        'C79': 0.20, 'D79': 'Prime-contractor franchises (submarines, destroyers, Abrams, GDIT) with customer-funded working capital and ~2% capex intensity earn ~20%+ incremental returns; Gulfstream development is expensed',
        'C80': 15, 'D80': 'Sole- or dual-source positions on 30-year naval programs and a 7-year defense backlog support a long competitive-advantage period; business-jet demand and U.S. budget cycles are the risks',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. EBIT less cash adjusting items',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: 2028E year-end net debt + NCI (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: 2026E year-end net debt + NCI',
        'B108': 'GD market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'General Dynamics — Operating Performance (2012–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · calendar years · Linked to Model. Bars = contribution of Aerospace and of the three defense segments to total revenue growth (pp). Adjusted EBITDA = model definition '
               '(operating earnings + D&A + the Q4-2012 one-off items); operating earnings = GAAP. ROIC / RONTA on adjusted EBIT (full-cost).'),
        'B8': 'Aerospace contribution to growth (pp)', 'B9': 'Defense segments contribution to growth (pp)', 'B12': 'Adjusted EBITDA (model)', 'B13': 'Operating earnings (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   Total backlog y/y %', 12: 'Adjusted EBITDA (model: operating earnings + D&A)',
            15: 'Operating earnings (GAAP)', 16: '   Operating earnings y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted net earnings (continuing operations)',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenue'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: Aerospace vs. Defense Segments Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Earnings (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_aero"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_def"]}+0,0)'
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
    cm = Comment('P/E on diluted EPS (GAAP = adjusted in the forecast). GD at $362.97 trades at ~21x 2026E EPS and ~19x 2027E. Exit multiples are assumptions: Base 20x, Bull 23x, Bear 16x '
                 'applied to 2030E–31E (2029E–31E for Bear), in line with the 16–22x range of the defense primes.', 'GD model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'GD model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to Dec-Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_nci"]}'
    d['C50'] = f'=Model!{a26}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
    d['P17'] = 'CAGR 27–31E'; d['Q17'] = 'CAGR 27–36E'
    build_charts(wb['Charts'])
    if UNMAPPED: print('WARNING: template Model rows referenced but not mapped:', sorted(UNMAPPED))

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
    (Charts!C:V = 2012-2031E) and cached values removed so Excel redraws from the GD cells."""
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
