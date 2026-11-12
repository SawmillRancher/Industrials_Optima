"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the TDG Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes TDG FY2026A (fiscal year ended 30-Sep-2026, about six weeks before the
valuation date) and the template's 2026E-2030E become TDG FY2027E-FY2031E, so the DCF's explicit years start in FY2027E and
net debt is taken at 30-Sep-2026."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from openpyxl.comments import Comment
from fw import R, TEMPLATE, ANN, NOTE, AUTHOR, MAN

# template Model row -> TDG row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_oi', 182: 'is_dda', 186: 'sh_d', 211: 'r_ad', 212: 'r_ad_m', 219: 'r_ebit', 221: 'r_ad',
       229: 'e_adjni', 231: 'e_eps', 238: 'mx_caft_g', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_ncit', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2027)]
PX = MAN['price']['px']

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> TDG FY2006-FY2026 annual columns."""
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
        'B2': 'TransDigm Group Incorporated (TDG) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: EBITDA As Defined, adjusted EPS) · USD millions · fiscal years ended 30 September · Live panel linked to Model — '
               'toggle scenario via Model!CK2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. FY2026A = actual; FY2027E '
               'calibrated to the FY27 guidance (net sales $11,950–12,150m, EBITDA As Defined $6,195–6,345m).'),
        'F26': 26, 'G26': 26, 'H26': 26, 'R26': 30, 'S26': 30, 'T26': 30, 'AD26': 20, 'AE26': 20, 'AF26': 20,
    },
    'DCF': {
        'B2': 'DCF VALUATION — TRANSDIGM GROUP INCORPORATED (TDG)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.10, 'D7': ('Assumption: aerospace components peers (HEI, HWM, CW, PH aerospace) ~0.9–1.2, raised for TransDigm\'s high financial leverage '
                           '(net debt ~5.8x EBITDA As Defined; ~32% of EV)'),
        'C9': 0.0675, 'D9': '2035 senior secured notes issued 28-Sep-2026 at 6.750% (8-K 29-Sep-2026); weighted note coupon 6.36%; term loans SOFR + 2.25–2.50% (B / Ba credit ratings)',
        'C10': 0.23, 'D10': 'Model FY2028E+ effective tax rate (FY27 guidance midpoint 23.1%)',
        'C12': 0.32, 'D12': f'Net debt ~$32.5bn at 30-Sep-2026 vs ~$68bn market cap (${PX:,.2f} × ~56.2m shares incl. participating options); ~5.8x EBITDA As Defined',
        'D15': 'Periods = (30-Sep of fiscal year − today) / 365.25; cash flows assumed at fiscal year-end (30 September); FY2026A (ended 30-Sep-2026) is the base year',
        'B18': 'Adj. EBIT (EBITDA As Defined − D&A) less stock compensation, acquisition & integration costs',
        'B21': 'plus D&A (depreciation + intangible amortization)',
        'B22': '− Capex and acquisitions (Extant FY2027E; M&A lever 2028E–31E)',
        'B26': 'Fade-period growth (2032E–36E; 6.0% → 4.5% linear)', 'I26': 0.06, 'M26': 0.045, 'C27': 0.035,
        'D32': ("TransDigm's EBITDA As Defined excludes non-cash stock & deferred compensation and acquisition / integration costs; row 18 deducts both again (stock compensation "
                'is a real cost to shareholders). Row 18 is full-cost: it charges all D&A including acquired-intangible amortization, which is added back in row 21. Row 22 includes '
                'the Extant asset purchase (FY2027E) and the M&A lever (2028E–31E); the fade period and terminal value assume no new acquisitions. Acquired intangibles are largely '
                'tax-deductible over 15 years (FY2026 deals, 10-K Note 2), so NOPAT broadly reflects the cash tax shield. The FY2026 deals (Simmonds, JPE / VSA, P&I) are in the '
                '30-Sep-2026 balance sheet and net debt, not in UFCF.'),
        'D43': 'Opening IC = Model FY2026A book IC (equity deficit + net debt + NCI incl. redeemable at 30-Sep-2026), rolled forward with capex + M&A − D&A + ΔWC. IC is small because of the accumulated deficit from debt-funded special dividends.',
        'B48': 'Less: Net debt + NCI incl. redeemable (Model FY2026A year end, 30-Sep-2026)',
        'D48': 'TDG: redeemable NCI (JPE / VSA / P&I, $85m) and NCI ($8m) deducted with net debt at the base-year end (≈ valuation date) so FY2027E+ cash flows are not double counted.',
        'B50': 'Shares (m, Model FY2026A period end; common + participating options)',
        'D76': 'Rationale (TransDigm characteristics)',
        'C78': 0.10, 'D78': 'Model adjusted EBIT CAGR FY2026–31E: ~8–9% sales growth (aftermarket, defense, OEM build rates, M&A) with modest margin recovery as FY2026 deals are integrated',
        'C79': 0.30, 'D79': ('Proprietary, sole-source aerospace content (~90% of sales) with aftermarket pricing power; acquisitions are bought at 2–8x sales and re-priced under the '
                             'value-driver model, earning high returns on acquired capital'),
        'C80': 15, 'D80': 'Certification barriers and a 30-year aftermarket tail on the installed base sustain a long competitive-advantage period; risks are pricing scrutiny (DoD audits) and leverage',
        'B90': 'VALUATION  —  Applied to FY2029E NOPAT',
        'B91': 'FY2029E Adj. EBIT less stock compensation, acquisition & integration costs',
        'B93': 'FY2029E NOPAT',
        'B95': 'Implied Enterprise Value (FY2029E basis)',
        'B96': 'Less: FY2028E year-end net debt + NCI (Model)',
        'B98': 'Shares FY2029E (m, Model)',
        'B99': 'Implied share price FY2029 ($)',
        'B106': 'Plus: FY2026A year-end net debt + NCI',
        'B108': 'TDG market-implied EV/NOPAT (on FY2029E NOPAT)',
    },
    'Charts': {
        'B2': 'TransDigm Group — Operating Performance (FY2012–FY2026) and Model Forecast (FY2027E–FY2031E)',
        'B3': ('USDm · fiscal years ended 30 September · Linked to Model. Bars = contribution of each segment to total net-sales growth (pp; segments from FY2011). '
               'EBITDA As Defined = company definition; income from operations = GAAP. ROIC / RONTA on adjusted EBIT (full-cost).'),
        'B8': 'Power & Control contribution to growth (pp)', 'B9': 'Airframe contribution to growth (pp)', 'B12': 'EBITDA As Defined', 'B13': 'Income from operations (GAAP)',
        'B14': 'EBITDA As Defined margin %', 'B15': 'Operating margin %', 'B18': 'ROIC', 'B19': 'RONTA', 'B20': 'EBITDA As Defined margin %', 'B21': 'FCF margin %',
    },
}
BBB_ROWS = {9: 'Net sales', 10: '   Net sales y/y %', 11: '   Commercial aftermarket net sales y/y %', 12: 'EBITDA As Defined', 13: '   EBITDA As Defined margin %',
            15: 'Income from operations (GAAP)', 16: '   Income from operations y/y %', 17: '   Operating margin (GAAP) %', 19: 'Adjusted net income',
            21: 'Shares (two-class, m)', 23: 'Adjusted EPS ($)', 35: 'EBITDA As Defined (leverage basis)', 36: '   EBITDA As Defined % of net sales',
            39: '   Net debt / EBITDA As Defined (x)', 50: 'Implied EV / EBITDA As Defined (x)'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Net Sales Growth: Power &amp; Control vs. Airframe Contribution, pp',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'EBITDA As Defined &amp; Income from Operations (USDm)',
    'Adjusted EBITDA': 'EBITDA As Defined',
}

def build_charts(ws):
    for i, y in enumerate(range(2012, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2026 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gc_pc"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gc_af"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_ad"]}'
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
                if c.comment is not None: c.comment = None
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    for c0 in ('C', 'O', 'AA'):
        i = b[f'{c0}7'].column
        b.cell(7, i).value = '2026A'
        for k in range(1, 6): b.cell(7, i + k).value = f'{2026 + k}E'
        b.cell(7, i + 6).value = "26-'31 CAGR"
    cm = Comment(f'P/E on adjusted EPS (company definition). TDG at ${PX:,.2f} trades at ~25x FY2027E adjusted EPS guidance ($47.51 midpoint) and ~29x FY2026A ($41.35). '
                 'Exit multiples are assumptions: Base 26x, Bull 30x, Bear 20x applied to FY2029E–31E; leverage-funded capital returns raise EPS growth '
                 'but also equity risk.', AUTHOR)
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', AUTHOR)
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 30-Sep of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2028E+ = buyback share of the leverage plug)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_acq"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_ncit"]}'
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
    (Charts!C:V = FY2012-FY2031E) and cached values removed so Excel redraws from the TDG cells."""
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
