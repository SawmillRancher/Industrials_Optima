"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the TLN Model rows /
columns; keep the template chart XML. The template's DCF_old tab is not carried.

Column mapping: the template's 2025A base column becomes TLN 2026E (nine months actual + Q4 calibrated to guidance; the year ends
about six weeks after the valuation date and carries the Cornerstone acquisition, the capacity monetization and the ASR) and the
template's 2026E-2030E become TLN 2027E-2031E, so the DCF's explicit years start in 2027E and net debt is taken at 31-Dec-2026E
(no double counting of 2026 cash flows)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE, MAN

# template Model row -> TLN row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_ebit', 182: 'r_ddap', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'r_adj',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_aero', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_nfuel',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
CMAP = {'BV': ANN[2026].c, 'CA': ANN[2027].c, 'CB': ANN[2028].c, 'CC': ANN[2029].c, 'CD': ANN[2030].c, 'CE': ANN[2031].c, 'CF': NOTE}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")
HIST = [ANN[y].c for y in range(2021, 2026)]
NCH = 11                                                    # chart years 2021-2031E -> Charts!C:M

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        c2 = CMAP.get(c, c)
        r2 = R[MAP[r]] if r in MAP else r
        if c == 'CF' and r == 2: r2 = 2
        return f'Model!{m.group(1)}{c2}{m.group(3)}{r2}'
    return REF.sub(rep, f)

def hist_stat(f):
    """LT historical AVERAGE / MIN / MAX over the template's annual columns -> TLN FY2021-FY2025 annual columns."""
    m = re.match(r'=IFERROR\((AVERAGE|MIN|MAX)\(Model!C(\d+),', f)
    if not m: return None
    fn, r = m.group(1), int(m.group(2))
    rr = R[MAP[r]]
    return f'=IFERROR({fn}({",".join(f"Model!{c}{rr}" for c in HIST)}),"")'

def fy_dates(f):
    f = re.sub(r'DATE\((\d{4}),12,31\)', lambda m: f'DATE({int(m.group(1)) + 1},12,31)', f)
    f = re.sub(r'DATE\((\d{4})-1,12,31\)', lambda m: f'DATE({int(m.group(1)) + 1}-1,12,31)', f)
    return f

PX = MAN['price']['px']
TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Talen Energy Corporation (TLN) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (Adjusted EBITDA and Adjusted Free Cash Flow = company definitions; adjusted net income / EPS = model definition, Talen publishes none) · USD millions · '
               f'Live panel linked to Model — toggle scenario via Model!{NOTE}2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               '2026E = nine months actual + Q4 calibrated to the FY26 Adjusted EBITDA guidance ($2,050–2,200m); 2027E solved to the FY27 guidance ($2,500–2,850m).'),
        'G26': 13, 'H26': 13, 'S26': 15, 'T26': 15, 'AD26': 10, 'AE26': 10, 'AF26': 10,
    },
    'DCF': {
        'B2': 'DCF VALUATION — TALEN ENERGY CORPORATION (TLN)',
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield, Nov-2026; government rate sources are not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.2, 'D7': 'Assumption: merchant power producers (VST, CEG, NRG) ~1.0–1.4; commodity-exposed gross margin partly offset by hedges, capacity revenues and the long-term AWS PPA; high financial leverage',
        'C9': 0.0625, 'D9': 'Unsecured notes issued Apr-2026 at 6.125% (2031) and 6.375% (2033); 2034 / 2036 notes 6.25% / 6.50%; term loans SOFR + 1.75% (~5.4%) — Q3-26 10-Q Note 10',
        'C10': 0.25, 'D10': 'Model tax rate (21% federal + state); cash taxes are lower in the first years (NOLs, nuclear PTC) — not credited here',
        'C12': 0.40, 'D12': f'Net debt incl. the deferred capacity obligation ~$11bn at YE2026E vs ~$16bn market cap (${PX:,.2f} × ~44m diluted shares); company net leverage target 3.5x',
        'D15': 'Periods = (31-Dec of the year − today) / 365.25; cash flows assumed at year end; 2026E (nine months actual) is the base year, the first explicit year is 2027E',
        'B18': 'Adj. EBIT (model) less stock compensation, restructuring & acquisition costs',
        'B21': 'plus D&A (reconciliation basis) and nuclear fuel amortization',
        'B22': '− Capex (PP&E incl. growth / conversion) and nuclear fuel expenditures',
        'B26': 'Fade-period growth (2032E–36E; 4.0% → 2.5% linear)', 'I26': 0.04, 'M26': 0.025, 'C27': 0.02,
        'D32': ("Talen's Adjusted EBITDA excludes stock-based compensation and nuclear fuel amortization: the model's adjusted EBIT charges D&A and nuclear fuel amortization (both added back in row 21, "
                'with nuclear fuel purchases inside capex in row 22) and row 18 also deducts stock compensation, restructuring and acquisition costs. Unrealized derivative results and '
                'nuclear decommissioning trust gains are excluded. The capacity revenues sold in the Oct-2026 monetization stay in UFCF; the related deferred capacity obligation is counted '
                'as debt in row 48. No acquisitions are assumed. The trust fund (~$2.0bn) is treated as covering the nuclear decommissioning obligation; neither is in net debt.'),
        'D25': 'Depreciation of the acquired plants (recorded at fair value) exceeds sustaining capex in the explicit and fade years; in perpetuity plants are replaced, so the terminal year assumes capex = D&A.',
        'D43': 'Opening IC = Model 2026E book IC (equity + net debt incl. the deferred capacity obligation at 31-Dec-2026E), rolled forward with capex − D&A + ΔWC.',
        'B48': 'Less: Net debt incl. deferred capacity obligation + NCI (Model 2026E year end)',
        'D48': 'TLN: noncontrolling interests ~$23m; net debt at the base-year end (31-Dec-2026E, after Cornerstone, the capacity monetization and the ASR), so 2027E+ cash flows are not double counted.',
        'B50': 'Diluted shares (m, Model 2026E period end)',
        'D76': 'Rationale (Talen Energy characteristics)',
        'C78': 0.06, 'D78': 'Model adjusted EBIT growth 2027–31E: AWS PPA ramp and PJM energy margins vs capacity prices normalising below the 2026–29 cap-level clears → mid-single-digit NOPAT growth',
        'C79': 0.12, 'D79': 'Returns on incremental capital come from contracting existing nuclear output at premium prices (little new capital) and from acquired gas plants bought at ~7–8x EBITDA; merchant exposure caps the assumption',
        'C80': 10, 'D80': 'Susquehanna licence to 2042 / 2044 and the AWS PPA through 2042 give long-dated cash flows; PJM capacity and energy prices are cyclical and policy-sensitive, so a shorter advantage period than regulated assets',
        'B90': 'VALUATION  —  Applied to 2029E NOPAT',
        'B91': '2029E Adj. EBIT less stock compensation, restructuring & acquisition costs',
        'B93': '2029E NOPAT',
        'B95': 'Implied Enterprise Value (2029E basis)',
        'B96': 'Less: YE2028E net debt + NCI (Model)',
        'B98': 'Diluted shares 2029E (m, Model)',
        'B99': 'Implied share price 2029 ($)',
        'B106': 'Plus: YE2026E net debt + NCI',
        'B108': 'TLN market-implied EV/NOPAT (on 2029E NOPAT)',
    },
    'Charts': {
        'B2': 'Talen Energy Corporation — Operating Performance (2021–2025) and Model Forecast (2026E–2031E)',
        'B3': ('USDm · Linked to Model. Bars = y/y growth of total generation (published from 2023) and of capacity revenues. Adjusted EBITDA = company definition; 2021–22 and 1-Jan to '
               '17-May-2023 are the Predecessor (Talen Energy Supply) and are not comparable with the Successor. ROIC / RONTA on adjusted EBIT (model) after stock compensation; no balance sheet for 2021.'),
        'B8': 'Generation y/y %', 'B9': 'Capacity revenues y/y %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating income (GAAP)',
        'B14': 'Adj. EBITDA % of energy & capacity revenues', 'B15': 'GAAP Op. Margin %', 'B20': 'Adj. EBITDA % of energy & capacity revenues', 'B21': 'Adjusted FCF % of energy & capacity revenues',
    },
}
BBB_ROWS = {9: 'Operating revenues', 10: '   Operating revenues y/y %', 11: '   Generation y/y %', 12: 'Adjusted EBITDA (company definition)',
            13: '   Adjusted EBITDA % of operating revenues', 15: 'Operating income (GAAP)', 16: '   Operating income y/y %', 17: '   Operating margin (GAAP) %',
            19: 'Adjusted net income (model definition, attributable)', 23: 'Adjusted EPS — Diluted ($, model definition)',
            26: 'P / E (x) — assumed (adjusted EPS, model definition)', 31: 'Adjusted Free Cash Flow (company definition)', 32: '   Adjusted FCF % of operating revenues',
            33: '   Adjusted FCF / share ($)', 34: '   Adjusted FCF yield (on PT)',
            35: 'Adjusted EBITDA (leverage basis)', 36: '   Adjusted EBITDA % of operating revenues', 38: 'Net Debt (incl. deferred capacity obligation)'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Growth Drivers: Generation vs. Capacity Revenues, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Income (USDm)',
}

def build_charts(ws):
    for row in ws.iter_rows(min_row=7, max_row=21, min_col=3, max_col=22):
        for c in row: c.value = None
    for i, y in enumerate(range(2021, 2032)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["gm_aero"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["gm_cap"]}+0,0)'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_ebit"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}17'] = f'={c}7'
        if y >= 2022:                                           # no balance sheet for 2021: cells left empty (chart gap)
            ws[f'{c}18'] = f'=IFERROR(Model!{mc}{R["ra_roic"]}+0,NA())'
            ws[f'{c}19'] = f'=IFERROR(Model!{mc}{R["rn_ronta"]}+0,NA())'
        ws[f'{c}20'] = f'=IFERROR(Model!{mc}{R["gm_ebitda_m"]}+0,NA())'
        if y >= 2023:                                           # Adjusted FCF published from 2023
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
    for ws in (b, wb['DCF'], wb['Charts']):
        for row in ws.iter_rows():
            for c in row:
                if c.comment: c.comment = None
    cm = Comment(f'P/E on the model-defined adjusted EPS (net income + the Adjusted EBITDA adjusting items after 25% tax; Talen publishes no adjusted EPS). At ${PX:,.2f} (Form 4, 17-Nov-2026) '
                 'the shares trade on the multiples shown in the Model valuation block. Exit multiples are assumptions: Base 13x, Bull 15x, Bear 10x applied to 2030E–31E '
                 '(2029E–31E for Bear); EV / Adjusted EBITDA and Adjusted FCF yield are shown alongside because power producers are usually valued on them.', 'TLN model')
    cm.width, cm.height = 420, 130; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with Model!{NOTE}2 = Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'TLN model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    b['J2'] = 'Share price ($):'
    for c in ('B', 'N', 'Z'): b[f'{c}29'] = 'IRR (to 31-Dec of Y-1)'
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4 incl. the ASR)'
    d = wb['DCF']
    for i, col in enumerate('DEFGHIJKLM'):
        d[f'{col}17'] = f'{2027 + i}E'
    a26, a27 = ANN[2026].c, ANN[2027].c
    d['D22'] = f'=Model!{a27}{R["cf_capex"]}+Model!{a27}{R["cf_nfuel"]}'
    d['D34'] = f'=Model!{a26}{R["ra_ic"]}'
    d['C48'] = f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_nci"]}'
    d['C50'] = f'=Model!{a26}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
    d['P17'] = 'CAGR 27–31E'; d['Q17'] = 'CAGR 27–36E'
    d['I22'] = '=H22*(1+I$26)'                                # fade capex grows from 2031E PP&E + nuclear fuel expenditures
    d['N24'] = '=(M20+M23)*(1+$C$27)'                         # terminal year: capex = D&A (plant replacement), so UFCF = NOPAT - change in working capital
    d['N42'] = 'n/m'
    d['B25'] = 'Terminal Value (Gordon Growth; terminal-year capex set equal to D&A)'
    for panel in ('F', 'R'):                                  # no price target in the 2029E column of the Base / Bull panels
        for r in (34, 47, 48, 49, 50): b[f'{panel}{r}'] = None
    a26 = ANN[2026].c
    import copy
    for r, k in ((40, 'bb_cash'), (41, 'bb_px'), (42, 'bb_sh')):
        b[f'C{r}'] = f'=Model!{a26}{R[k]}'
        for dst, srcc in (('C', 'D'), ('O', 'P'), ('AA', 'AB')): b[f'{dst}{r}']._style = copy.copy(b[f'{srcc}{r}']._style)
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
    """Replace openpyxl-rewritten chart parts with the template chart XML (combo charts, colours, layout), retitled, re-ranged to
    Charts!C:M (2021-2031E) and with cached values removed so Excel redraws from the TLN cells."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    last = L(2 + NCH)
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                t = re.sub(r'<c:numCache>.*?</c:numCache>', '', t, flags=re.S)
                t = re.sub(r'<c:strCache>.*?</c:strCache>', '', t, flags=re.S)
                t = re.sub(r'(Charts!\$C\$\d+:)\$[A-Z]+(\$\d+)', lambda m: f'{m.group(1)}${last}{m.group(2)}', t)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
