"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the LHX Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes LHX 2026E (fiscal year ending 1-Jan-2027, six weeks after the valuation
date; Q1-Q3 actual, Q4 calibrated to guidance) and the template's 2026E-2030E become LHX 2027E-2031E, so the DCF's explicit years
start in 2027E and net debt is taken at the 2026E year end (no double counting of 2026E cash flow)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE, TP

# template Model row -> LHX row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'd_dep', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'o_adj', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_sms', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_ncipref', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2013, 2026)]

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> LHX FY2013-FY2019 and 2020-2025 annual columns."""
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
        'B2': 'L3Harris Technologies, Inc. (LHX) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (model definitions: adjusted EBITDA; non-GAAP EPS = model rebuild of the company\'s FY2025 definition, which is no longer published) · USD millions · fiscal years ended the Friday '
               f'nearest 31 December · Live panel linked to Model — toggle scenario via Model!{NOTE}2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               '2026E = Q1–Q3 actual + Q4 calibrated to the FY26 guidance (revenue $23.5–23.7bn, GAAP diluted EPS $12.25–12.35).'),
        'G26': 21, 'H26': 21, 'S26': 24, 'T26': 24, 'AD26': 17, 'AE26': 17, 'AF26': 17,
    },
    'DCF': {
        'B2': 'DCF VALUATION — L3HARRIS TECHNOLOGIES (LHX)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 0.8, 'D7': 'Assumption: US defense primes (LMT, NOC, GD, RTX) ~0.5–0.9 (budget-driven, low cyclicality); ~23% international revenue; fixed-price development exposure',
        'C9': 0.053, 'D9': 'Nov-2026 senior notes at 5.200% (2029) and 5.400% (2032) (8-K 5-Nov-2026)',
        'C10': 0.16, 'D10': 'Model 2027E+ effective tax rate (FY2025 16.9%; 9M 2026 14.6%)',
        'C12': 0.15, 'D12': 'Net debt ~$8.0bn at 2-Oct-2026 (after cash and short-term investments) vs ~$48bn market cap ($255 × ~187m diluted shares); 1.9x company TTM EBITDA',
        'D15': 'Periods = (Dec-31 of fiscal year − today) / 365.25; cash flows assumed at fiscal year-end (Friday nearest 31 December); 2026E (ending 1-Jan-2027) is the base year',
        'B18': 'Adj. operating income (EBITA) less integration, restructuring & transaction costs',
        'B21': 'plus Depreciation & other amortization (acquisition-related amortization is not deducted in row 18)',
        'B22': '− Capex (PP&E) and acquisitions (M&A lever 2027E–31E; Base none)',
        'B26': 'Fade-period growth (2032E–36E; 6.0% → 4.0% linear)', 'I26': 0.06, 'M26': 0.04, 'C27': 0.03,
        'D32': ('NOPAT basis: adjusted operating income before acquisition-related amortization (tax on pre-amortization profit; only depreciation & other amortization is added back in row 21). '
                'Share-based compensation is expensed in adjusted operating income (not adjusted out). Cash integration / transaction costs adjusted out by the company are deducted inside row 18. '
                'Non-service FAS pension income (non-cash, below operating income) is excluded from UFCF; the net pension asset (~$1.4bn) is not added to equity value. '
                '2026E cash flow is excluded: net debt is taken at the 2026E year end.'),
        'D43': 'Opening IC = Model 2026E book IC (equity + subsidiary preferred + net debt at the 2026E year end), rolled forward with capex + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI + subsidiary preferred (Model 2026E year end)',
        'D48': ('LHX: net debt after cash and short-term investments; plus the DoW subsidiary preferred stock (mezzanine ~$1.0bn + conversion-feature and warrant liabilities $366m), which converts into '
                'Missile Solutions equity on a Qualified IPO. Taken at the 2026E year end so that 2027E+ cash flows are not double counted.'),
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (L3Harris characteristics)',
        'C78': 0.07, 'D78': 'Model adjusted operating income CAGR 2026–31E (~7%): mid-to-high single-digit revenue growth (record $53bn backlog; missile-propulsion ramps) with modest margin expansion → ~7% NOPAT growth',
        'C79': 0.15, 'D79': 'Incremental returns on organic growth are high (customer-funded development, progress payments), but goodwill-heavy capital from the L3 and Aerojet deals depresses reported ROIC (~7–9%); 15% on incremental capital (assumption)',
        'C80': 12, 'D80': 'Sole-source / franchise positions (tactical radios, EW, solid rocket motors, space payloads) on multi-decade programmes; exposure to US defense budgets and fixed-price development risk',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. operating income (EBITA) less integration & transaction costs',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: YE2028E net debt + NCI + subsidiary preferred (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: YE2026E net debt + NCI + subsidiary preferred',
        'B108': 'LHX market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'L3Harris Technologies — Operating Performance (FY2013–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · FY2013–FY2019 = Harris Corporation fiscal years ended ~30 June; 2H19 TP = six-month transition period after the L3 merger (not annualised); 2020+ fiscal years ended ~31 December · Linked to Model. '
               'Growth chart: 2H19 TP and 2020 have no comparable prior year (shown as 0). Adjusted EBITDA and adjusted operating income = model definitions. ROIC / RONTA on adjusted EBIT (full-cost).'),
        'B8': 'Revenue y/y %', 'B9': 'Adjusted operating income y/y %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   Space & Mission Systems revenue y/y %', 12: 'Adjusted EBITDA (model)',
            15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %', 19: 'Non-GAAP net income (model rebuild, attributable to common)',
            23: 'Non-GAAP EPS — Diluted ($; model rebuild)', 26: 'P / E (x) — assumed (non-GAAP EPS)',
            48: '(+) Net debt, NCI & subsidiary preferred', 35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenue'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue vs. Adjusted Operating Income Growth, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}
CH_COLS = [ANN[y] for y in range(2013, 2020)] + [TP] + [ANN[y] for y in range(2020, 2032)]

def build_charts(ws):
    for i, col in enumerate(CH_COLS):
        c = L(3 + i); mc = col.c
        ws[f'{c}7'] = col.label
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gm_rev"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gm_adjop"]}+0,0)'
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
    cm = Comment('P/E on non-GAAP EPS (model rebuild of the FY2025 company definition; ≈ GAAP EPS + adjusting items). LHX at $255 trades at ~21x 2026E GAAP EPS guidance ($12.30) and ~19x 2027E. '
                 'Exit multiples are assumptions: Base 21x, Bull 24x, Bear 17x applied to 2030E–31E (2029E–31E for Bear), within the range of US defense primes.', 'LHX model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'LHX model')
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
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_ncipref"]}'
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
    (Charts!C:V = FY2013-2031E incl. the 2H19 transition period) and cached values removed so Excel redraws from the LHX cells."""
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
