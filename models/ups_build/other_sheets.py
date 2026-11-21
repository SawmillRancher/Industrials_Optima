"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the UPS Model rows;
keep the template chart XML. The template's DCF_old tab is not carried.

UPS uses the template's own column layout (2025A base = BV, 2026E-2030E = CA-CE, switch = CF2), so only rows are remapped.
The valuation date falls in the last weeks of 2026 and the EV bridge takes net debt at YE2026E, so the 2026E unlevered cash flow
is switched off with an inclusion flag (DCF!C28 = 0) to avoid double counting."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE, MAN

# template Model row -> UPS row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_ebit', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_adv', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2006, 2026)]
PXV = MAN['price']['px']


def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        if r == 2 or r not in MAP: return m.group(0)      # scenario switch cell (Model!CF2); cells overwritten in do_all (DCF!D34)
        return f'Model!{m.group(1)}{c}{m.group(3)}{R[MAP[r]]}'
    return REF.sub(rep, f)


def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> UPS FY2006-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'


TEXT = {
    'Bull-Base-Bear': {
        'B2': 'United Parcel Service, Inc. (UPS) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company non-GAAP adjusted operating profit and EPS; adjusted EBITDA = model definition: adjusted operating profit + D&A) · USD millions · calendar years · '
               'Live panel linked to Model — toggle scenario via Model!CF2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               '2026E = Q1–Q3 actual + Q4 calibrated to the FY26 guidance (revenue ~$92.6bn, adjusted operating profit ~$8.75bn; High / Low end-points are model assumptions).'),
        'F26': 15, 'G26': 15, 'H26': 15, 'R26': 17, 'S26': 17, 'T26': 17, 'AD26': 12, 'AE26': 12, 'AF26': 12,
    },
    'DCF': {
        'B2': 'DCF VALUATION — UNITED PARCEL SERVICE, INC. (UPS)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources are not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied equity risk premium ~4.5–5.5%',
        'C7': 1.0, 'D7': 'Assumption: integrated parcel / logistics peers (FDX, DHL Group) ~0.9–1.1; cyclical B2B and trade volumes vs a dividend-paying, investment-grade profile',
        'C9': 0.05, 'D9': 'Aug-2026 issue: $1.0bn 4.850% senior notes due 2031 (Q3-2026 10-Q); long-dated notes at 5.05–6.05%; model rate on existing debt ~4.6%',
        'C10': 0.23, 'D10': 'Model 2027E+ effective tax rate (FY26 guidance ~23%)',
        'C12': 0.18, 'D12': f'Net debt ~$19bn at 30-Sep-2026 vs ~$90bn market cap (${PXV:.2f} × ~852m diluted shares); ~1.6x model adjusted EBITDA (pensions and operating leases excluded)',
        'D15': 'Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end. 2026E is switched off (C28 = 0) because net debt is taken at YE2026E',
        'B18': 'Adj. EBIT (non-GAAP adjusted operating profit) less transformation strategy & other excluded costs',
        'B21': 'plus D&A (depreciation and amortization, total)',
        'B22': '− Capex (PP&E, software) and acquisitions (M&A lever 2027E–30E)',
        'B26': 'Fade-period growth (2031E–35E; 4.0% → 3.0% linear)', 'I26': 0.04, 'M26': 0.03, 'C27': 0.025,
        'B28': '2026E unlevered FCF inclusion flag (0 = excluded: net debt is taken at YE2026E)', 'C28': 0,
        'D28': 'Valuation date in Q4-2026: the 2026E cash flow is already in the YE2026E net debt of the EV bridge (row 48). Set to 1 only if row 48 is moved to YE2025.',
        'D32': ("UPS's non-GAAP adjusted operating profit already deducts amortization of intangibles and stock compensation (neither is adjusted out); total D&A is added back in row 21. "
                'Transformation strategy costs (cash separation and consulting costs excluded by the company) are deducted inside row 18. Row 22 includes bolt-on acquisitions in 2027E–30E; '
                'the fade period and terminal value assume none. Operating leases are treated as operating costs (not in net debt). Pension contributions in excess of expense '
                '(Model cash-flow row) are not in UFCF; the pension and postretirement obligation is deducted in the EV bridge instead (row 48).'),
        'D43': 'Opening IC = Model 2025A book IC (equity + net debt), rolled forward with capex + M&A − D&A + ΔWC.',
        'B48': 'Less: Net debt + NCI + pension & postretirement obligations (Model 2026E year end)',
        'D48': ('UPS-specific: net debt (debt − cash − marketable securities) and noncontrolling interests (~$32m) at YE2026E, plus the balance-sheet pension and postretirement benefit '
                'obligations (~$5.6bn, gross of tax; debt-like). Operating lease liabilities (~$4.2bn) are not deducted (rent stays in operating costs).'),
        'B50': 'Diluted shares (m, Model 2026E period end; class A + class B)',
        'D76': 'Rationale (UPS characteristics)',
        'C78': 0.06, 'D78': 'Model adjusted EBIT CAGR 2026–30E: low-single-digit volume, ~3% revenue per piece and margin recovery from the 2026 trough (network reconfiguration savings) → ~6% NOPAT growth in Stage 1',
        'C79': 0.12, 'D79': 'Integrated air / ground network with high fixed cost: returns on incremental capital depend on density and yield (model ROIC low-to-mid teens); automation capex earns above WACC, volume lost to insourcing does not',
        'C80': 10, 'D80': 'Scale, brand and a global integrated network are hard to replicate, but customers insource (largest customer), postal and regional carriers compete on price and labour is unionised — a medium competitive-advantage period',
        'B90': 'VALUATION  —  Applied to 2028E NOPAT',
        'B91': '2028E Adj. EBIT less transformation strategy & other excluded costs',
        'B96': 'Less: YE2027 net debt + NCI + pension obligations (Model)',
        'B106': 'Plus: YE2026 net debt + NCI + pension obligations',
        'B108': 'UPS market-implied EV/NOPAT (on 2028E NOPAT)',
    },
    'Charts': {
        'B2': 'United Parcel Service, Inc. — Historical Operating Performance (2006–2025)',
        'B3': ('All historicals · USDm · Linked to Model. Volume / price = U.S. Domestic Package average daily volume and average revenue per piece, y/y %. Adjusted EBITDA = model definition '
               '(non-GAAP adjusted operating profit + D&A; adjusted = GAAP where the company published no adjusted measures). ROIC / RONTA on adjusted operating profit.'),
        'B8': 'U.S. Domestic average daily volume %', 'B9': 'U.S. Domestic revenue per piece %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating Profit (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Revenue', 10: '   Revenue y/y %', 11: '   Average daily package volume y/y %', 12: 'Adjusted EBITDA (model: adjusted operating profit + D&A)',
            15: 'Operating Profit (GAAP)', 16: '   Operating profit y/y %', 17: '   Operating margin (GAAP) %', 19: 'Non-GAAP Adjusted Net Income',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of revenue'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'U.S. Domestic Package Revenue Drivers: Average Daily Volume vs. Revenue per Piece, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Profit (USDm)',
}


def build_charts(ws):
    for i, y in enumerate(range(2006, 2026)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["us_adv_g"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["us_rpp_g"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_ebit"]}'
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
                if isinstance(c.value, str) and 'Model!' in c.value and name != 'Charts':
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
    cm = Comment(f'P/E on non-GAAP adjusted EPS (company definition). UPS at ${PXV:.2f} trades at ~14.5x FY2026E adjusted EPS guidance ($7.28). Exit multiples are assumptions: '
                 'Base 15x, Bull 17x, Bear 12x applied to 2028E–2030E.', 'UPS model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'UPS model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    for c in ('F', 'R'):          # price target for 2028E in the live and Bull panels too (the template has it for the Bear panel only)
        b[f'{c}27'] = f'={c}26*{c}23'
        b[f'{c}28'] = f'=IFERROR({c}27/$K$2-1,"")'
        b[f'{c}29'] = f'=IFERROR(({c}27/$K$2)^(1/((DATE(2028-1,12,31)-$K$3)/365.25))-1,"")'
    d = wb['DCF']
    for row in d.iter_rows():
        for c in row: c.comment = None
    a25, a26, a27, a28 = (ANN[y].c for y in (2025, 2026, 2027, 2028))
    d['D34'] = f'=Model!{a25}{R["ra_ic"]}'
    d['D31'] = '=D24*D30*$C$28'
    pen = R['bs_pension']
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_nci"]}+Model!{a26}{pen}'
    d['C96'] = f'=Model!{a27}{R["lv_nd"]}+Model!{a27}{R["bs_nci"]}+Model!{a27}{pen}'
    for r_ in (28,):
        d[f'B{r_}']._style = d['B27']._style; d[f'C{r_}']._style = d['C55']._style if False else d['C27']._style
    d['C28'].number_format = '0'
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
    (Charts!C:V = 2006-2025) and cached values removed so Excel redraws from the UPS cells."""
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
