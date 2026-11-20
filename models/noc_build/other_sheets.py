"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the NOC Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes NOC 2026E (Q1-Q3 actual, Q4 calibrated to guidance; the year ends six
weeks after the valuation date) and the template's 2026E-2030E become NOC 2027E-2031E, so the DCF's explicit years start in 2027E
and net debt is taken at 31-Dec-2026 (2026E free cash flow is therefore not discounted separately)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE

# template Model row -> NOC row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_aebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_as', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
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
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> NOC FY2006-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    return f      # calendar year ends: the template's DATE(yyyy,12,31) convention is kept

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Northrop Grumman Corporation (NOC) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (model adjusted EBITDA; MTM-adjusted EPS, company definition) · USD millions · calendar years · Live panel linked to Model — toggle scenario via '
               f'Model!{NOTE}2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the 2026 guidance '
               '(sales $43.75–44.25bn, segment operating income $4.94–5.04bn).'),
        'G26': 18, 'H26': 18, 'S26': 20, 'T26': 20, 'AD26': 15, 'AE26': 15, 'AF26': 15,
    },
    'DCF': {
        'B2': 'DCF VALUATION — NORTHROP GRUMMAN CORPORATION (NOC)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 0.85, 'D7': 'Assumption: US defense primes (LMT, GD, RTX, LHX, HII) ~0.5–0.9; ~85% of sales to the US Government (FY2025 10-K)',
        'C9': 0.0500, 'D9': 'May-2025 senior notes 4.65% (2030) / 5.25% (2035) (Q3 2026 10-Q Note 8); 2025 effective rate ~4.2% on fixed-rate notes',
        'C10': 0.16, 'D10': 'Model 2027E+ effective tax rate (2025 17.5%; 9M 2026 11.5% with higher research credits)',
        'C12': 0.14, 'D12': 'Net debt ~$11.5bn at 30-Sep-2026 vs ~$79bn market cap ($555.32 × ~142m diluted shares); ~1.9x adjusted EBITDA',
        'D15': 'Periods = (31-Dec of fiscal year − today) / 365.25; cash flows assumed at year-end; 2026E (ends six weeks after the valuation date) is the base year, net debt at 31-Dec-2026E',
        'B18': 'Adj. EBIT (model, after D&A) less the FAS/CAS operating adjustment (non-cash pension accounting) and divestiture costs',
        'B21': 'plus D&A (depreciation + purchased-intangible amortization)',
        'B22': '− Capex and acquisitions (bolt-ons; M&A lever 2027E–31E)',
        'B26': 'Fade-period growth (2032E–36E; 5.0% → 3.0% linear)', 'I26': 0.05, 'M26': 0.03, 'C27': 0.03,
        'D32': ('Adjusted EBIT (model) is after purchased-intangible amortization and stock-based compensation (neither is added back) and includes the FAS/CAS operating adjustment, a non-cash '
                'pension-accounting item (CAS cost recovered through contracts less FAS service cost): row 18 deducts it so NOPAT is on a cash-pension basis, and the non-operating FAS pension '
                'benefit never enters UFCF. Divestiture costs (cash; added back in adjusted EBITDA) are deducted. Row 22 includes bolt-on acquisitions in 2027E–31E; the fade period and '
                'terminal value assume no new acquisitions. Pension contributions are inside operating cash flow in the Model but not in UFCF (plans overfunded; ~$125m p.a.).'),
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt at 31-Dec-2026E), rolled forward with capex + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI (Model 2026E year end, 31-Dec-2026)',
        'D48': 'NOC: no noncontrolling interests; net debt at the base-year end so that 2027E+ cash flows are not double counted. The overfunded pension (~$2.3bn net asset at 30-Sep-2026) is not added to equity value (CAS recovery mechanics).',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (Northrop Grumman characteristics)',
        'C78': 0.07, 'D78': 'Model adjusted EBIT CAGR 2026–31E: mid-single-digit sales growth (Sentinel, B-21, restricted space, F-35 sustainment) with ~50bp of segment-margin recovery as B-21 LRIP dilution fades → ~7% NOPAT growth',
        'C79': 0.14, 'D79': 'Sole-source franchise programs (B-21, Sentinel, strategic deterrence, restricted space) on multi-decade production and sustainment cycles earn mid-teens ROIC on invested capital that includes ~$17bn of goodwill; incremental returns are higher',
        'C80': 15, 'D80': 'Backlog of $110bn (2.5x sales) and sole-source positions sustain a long competitive-advantage period; exposure to US defense budgets, fixed-price development risk (B-21) and CAS pension recovery',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. EBIT less the FAS/CAS operating adjustment and divestiture costs',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: 2028E year-end net debt + NCI (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: 2026E year-end net debt + NCI',
        'B108': 'NOC market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'Northrop Grumman Corporation — Operating Performance (2012–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · calendar years · Linked to Model. Bars = contribution of each sector to total sales growth (pp; current four-sector structure from 2019, so 2019 is the first bar). '
               'Adjusted EBITDA = model definition (operating income + D&A, before business-sale gains, the 2008 goodwill impairment and the B-21 loss provisions). ROIC / RONTA on adjusted EBIT (after D&A).'),
        'B8': 'Aeronautics contribution to growth (pp)', 'B9': 'Defense + Mission + Space contribution to growth (pp)', 'B12': 'Adjusted EBITDA (model)', 'B13': 'Operating income',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'Operating Margin %',
    },
}
BBB_ROWS = {9: 'Sales', 10: '   Sales y/y %', 11: '   Aeronautics Systems sales y/y %', 12: 'Adjusted EBITDA (model)',
            15: 'Operating income', 16: '   Operating income y/y %', 17: '   Operating margin rate %', 19: 'Adjusted Net Earnings (MTM-adjusted)',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of sales'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Sales Growth: Aeronautics vs. Defense / Mission / Space Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA (model) &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR((Model!{mc}{R["as_s"]}-Model!{ANN[y - 1].c}{R["as_s"]})/Model!{ANN[y - 1].c}{R["is_rev"]}+0,0)' if y - 1 in ANN else 0
        ws[f'{c}9'] = (f'=IFERROR((Model!{mc}{R["g_rev"]}-Model!{ANN[y - 1].c}{R["g_rev"]}-(Model!{mc}{R["as_s"]}-Model!{ANN[y - 1].c}{R["as_s"]}))/Model!{ANN[y - 1].c}{R["is_rev"]}+0,0)'
                       if y - 1 in ANN else 0)
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
    for c0 in ('C', 'O', 'AA'):
        i = b[f'{c0}7'].column
        b.cell(7, i).value = '2026E'
        for k in range(1, 6): b.cell(7, i + k).value = f'{2026 + k}E'
        b.cell(7, i + 6).value = "26-'31 CAGR"
    from openpyxl.comments import Comment
    cm = Comment('P/E on MTM-adjusted EPS (company definition). NOC at $555.32 trades at ~19x 2026E MTM-adjusted EPS (~$29.6 guided mid-point) and ~17x 2027E. Exit multiples are '
                 'assumptions: Base 18x, Bull 20x, Bear 15x applied to 2030E–31E (2029E–31E for Bear), in line with the 2015–25 range of large-cap US defense primes.', 'NOC model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'NOC model')
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
    # NOPAT basis: adjusted EBIT less the FAS/CAS operating adjustment and divestiture costs (row 18 of the DCF references Model rows via MAP 219 / 164)
    for col, y in zip('DEFGH', range(2027, 2032)):
        d[f'{col}18'] = f'=Model!{ANN[y].c}{R["r_aebit"]}-Model!{ANN[y].c}{R["rc_fascas"]}+Model!{ANN[y].c}{R["r_cash"]}'
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
    (Charts!C:V = 2012-2031E) and cached values removed so Excel redraws from the NOC cells."""
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
