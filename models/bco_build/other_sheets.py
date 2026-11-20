"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template (current layout: DCF with live valuation date, fade period,
implied ROIC, target-IRR entry price, reverse DCF and Mauboussin EV/NOPAT; Bull-Base-Bear with buyback rows) to the BCO Model rows;
keep the template chart XML. The template's DCF_old tab is not carried.

Columns are identical to the template (2025A in BV, 2026E in CA, 2027E-2030E in CB-CE, switch in CF2), so only rows are remapped.
DCF basis: valuation net debt is taken at 31-Dec-2026 (before the NCR Atleos closing), so the 2026E cash flow is excluded from the
sum of present values, and the NCR Atleos debt assumed is added to the EV bridge (the cash consideration is inside 2027E UFCF and
the consideration shares are in the 2027E share count)."""
import re, zipfile, shutil
from openpyxl.utils import get_column_letter as L
from fw import R, TEMPLATE, ANN, NOTE, MAN

# template Model row -> BCO row key
MAP = {158: 'is_rev', 164: 'r_cash', 166: 'is_op', 182: 'r_dep', 186: 'e_sh', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit', 221: 'lv_eb',
       229: 'e_adjni', 231: 'e_eps', 238: 'gm_org', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex', 263: 'cf_acq',
       280: 'fcf', 282: 'fcf_m', 290: 'bb_px', 291: 'bb_cash', 292: 'bb_sh', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta',
       428: 'lv_nd', 433: 'v_px', 434: 'v_sh'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")

def remap(f):
    def rep(m):
        c, r = m.group(2), int(m.group(4))
        if c == 'CF' and r == 2: return m.group(0)
        if r not in MAP: raise KeyError(f'unmapped template row {r} in {f}')
        return f'Model!{m.group(1)}{c}{m.group(3)}{R[MAP[r]]}'
    return REF.sub(rep, f)

PX = MAN['price']['px']
TEXT = {
    'Bull-Base-Bear': {
        'B2': "The Brink's Company (BCO) — Bull / Base / Bear Case P&L Summary",
        'B3': ('Non-GAAP figures (company definitions: non-GAAP operating profit, adjusted EBITDA, non-GAAP EPS) · USD millions · Live panel linked to Model — toggle the scenario with the switch on the Model tab (cell CF2). '
               'Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. 2026E = Q1–Q3 actual + Q4 calibrated to the Q4 2026 guidance '
               '(revenue $1,365–1,415m, adjusted EBITDA $275–295m). 2027E+ includes NCR Atleos from the assumed closing in early January 2027 (Model toggle).'),
        'G26': 12, 'H26': 12, 'S26': 14, 'T26': 14, 'AD26': 9, 'AE26': 9, 'AF26': 9,
    },
    'DCF': {
        'B2': "DCF VALUATION — THE BRINK'S COMPANY (BCO)",
        'C5': 0.0425, 'D5': 'Assumption (~US 10Y Treasury yield; government rate sources are not reachable from the build environment); update to market',
        'D6': 'Assumption: US implied ERP ~4.5–5.5%',
        'C7': 1.3, 'D7': 'Assumption: security / cash-logistics and ATM-services peers ~1.0–1.3 unlevered-to-relevered at ~3x net debt / adjusted EBITDA after NCR Atleos; emerging-market exposure (Latin America ~25% of revenues)',
        'C9': 0.065, 'D9': '6.5% senior notes due 2029 and 6.75% due 2032; Q3/26 interest expense ≈ 6.4% of total debt; NCR Atleos notes carry a higher coupon (assumption 9.5%)',
        'C10': 0.272, 'D10': 'Company estimate of the 2026 non-GAAP effective tax rate (27.2%; 2025: 27.5%)',
        'C12': 0.40, 'D12': f'Net debt ~$2.3bn at YE2026E vs ~$4.7bn market cap (${PX:.2f} × ~41m diluted shares); ~$6.4bn of net debt vs ~$6.1bn of equity after NCR Atleos (53.8m shares) — target ~40% debt',
        'D15': 'Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end. 2026E is shown but excluded from the sum of present values (see the note in row 32)',
        'B18': 'Adj. EBIT (non-GAAP operating profit) less cash adjusting costs',
        'B21': 'plus D&A (excl. amortization of acquisition-related intangibles)',
        'B22': '− Capex and acquisitions (2027E: NCR Atleos cash consideration, net of cash acquired)',
        'B26': 'Fade-period growth (2031E–35E; 3.0% → 2.0% linear)', 'I26': 0.03, 'M26': 0.02, 'C27': 0.02,
        'D32': ("Brink's non-GAAP operating profit is after depreciation and share-based compensation and before amortization of acquisition-related intangibles, so NOPAT is taxed on pre-amortization profit and row 21 adds back "
                'D&A excluding that amortization. Restructuring, transformation, NCR Atleos integration and other cash items the company adjusts out are deducted inside row 18. Valuation net debt is taken at 31-Dec-2026, so the 2026E '
                'cash flow is excluded from the sum of present values (row 31, column D = 0). The NCR Atleos cash consideration (net of cash acquired) is in 2027E row 22; the debt assumed is added in row 48 and the consideration shares '
                'are in the row 50 share count. If the Model toggle is set to 0 the deal drops out of all three.'),
        'D43': 'Opening IC = Model 2025A book IC (equity + net debt); the 2027E opening adds the NCR Atleos stock consideration, converted awards and debt assumed (the cash consideration enters through row 35).',
        'B48': 'Less: net debt + NCI + pension / retiree liabilities (Model YE2026E) + NCR Atleos debt and pension assumed',
        'D48': ("Net debt = total debt incl. financing leases − cash and cash equivalents (restricted cash and cash held for customers are not netted); NCI ~$87m. NCR Atleos debt assumed $2,866m (424B3 pro forma) × the Model toggle. "
                'Accrued pension and retiree-benefit liabilities are treated as debt-like (~$265m; + ~$319m with NCR Atleos), pre-tax.'),
        'B50': 'Diluted shares (m, Model 2027E period end incl. NCR Atleos consideration shares)',
        'D76': "Rationale (Brink's characteristics)",
        'C78': 0.06, 'D78': 'Model adjusted EBIT growth 2027E–30E after the NCR Atleos step-up: mid-single-digit organic growth (AMS / DRS mix), margin expansion and $200m of cost synergies → ~6–8% NOPAT growth',
        'C79': 0.12, 'D79': 'Route-density businesses with heavy vehicle, vault and ATM fleets; AMS / DRS and ATM-as-a-service contracts earn higher returns on recurring revenue, but cash usage declines structurally in developed markets',
        'C80': 10, 'D80': 'Scale and security-network barriers in cash logistics and the largest independent ATM estate; competitive-advantage period limited by the secular shift to digital payments',
        'B90': 'VALUATION  —  Applied to 2028E NOPAT',
        'B91': '2028E Adj. EBIT less cash adjusting costs',
        'B108': 'BCO market-implied EV/NOPAT (on 2028E NOPAT)',
    },
    'Charts': {
        'B2': "The Brink's Company — Operating Performance (2011–2025) and Model Forecast (2026E–2030E)",
        'B3': ('USDm · Linked to Model. Bars = organic revenue growth and the acquisitions / dispositions + currency effect (company growth tables, 2015+; 0 where not published; forecast = legacy segments, '
               'excluding the NCR Atleos consolidation). Adjusted EBITDA = company definition (published from 2016; earlier a model measure). 2027E+ includes NCR Atleos. ROIC / RONTA on non-GAAP operating profit.'),
        'B8': 'Organic growth %', 'B9': 'Acquisitions / dispositions + currency %', 'B12': 'Adjusted EBITDA', 'B13': 'Operating profit (GAAP)',
        'B14': 'Adj. EBITDA Margin %', 'B15': 'GAAP Op. Margin %',
    },
}
BBB_ROWS = {9: 'Revenues', 10: '   Revenues y/y %', 11: '   Organic revenue growth % (company definition)', 12: 'Adjusted EBITDA',
            15: 'Operating profit (GAAP)', 16: '   Operating profit y/y %', 17: '   Operating margin (GAAP) %', 19: "Non-GAAP income (continuing ops, attributable to Brink's)",
            23: 'Non-GAAP EPS — Diluted ($)', 26: 'P / E (x) — assumed (non-GAAP EPS)',
            35: 'Adjusted EBITDA — pro forma (2027E incl. NCR Atleos pre-closing days)', 36: '   Adjusted EBITDA (pro forma) % of revenues'}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Revenue Growth: Organic vs. Acquisitions / Dispositions &amp; Currency, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Operating Profit (USDm)',
}

def build_charts(ws):
    """Charts window: 2011-2025 actual and 2026E-2030E forecast (20 columns C:V), so that every series has data in every year
    (the balance sheet starts at 31-Dec-2008; no error cells)."""
    for i, y in enumerate(range(2011, 2031)):
        c = L(3 + i); mc = ANN[y].c
        ws[f'{c}7'] = y if y <= 2025 else f'{y}E'
        ws[f'{c}8'] = f'=IFERROR(Model!{mc}{R["g_org"]}+0,0)'
        ws[f'{c}9'] = f'=IFERROR(Model!{mc}{R["g_acq"]}+Model!{mc}{R["g_fx"]},IFERROR(Model!{mc}{R["seg_g"]}-Model!{mc}{R["g_org"]},0))'
        ws[f'{c}11'] = f'={c}7'
        ws[f'{c}12'] = f'=Model!{mc}{R["r_adj"]}'
        ws[f'{c}13'] = f'=Model!{mc}{R["is_op"]}'
        ws[f'{c}14'] = f'=Model!{mc}{R["gm_ebitda_m"]}'
        ws[f'{c}15'] = f'=Model!{mc}{R["gm_op_m"]}'
        ws[f'{c}17'] = f'={c}7'
        ws[f'{c}18'] = f'=Model!{mc}{R["ra_roic"]}+0'
        ws[f'{c}19'] = f'=Model!{mc}{R["rn_ronta"]}+0'
        ws[f'{c}20'] = f'=Model!{mc}{R["gm_ebitda_m"]}+0'
        ws[f'{c}21'] = f'=Model!{mc}{R["fcf_m"]}+0'

def do_all(wb):
    from openpyxl.worksheet.formula import ArrayFormula
    wb['DCF']['D34'] = None                 # template: opening IC + LNA consideration rows; rewritten below
    for col in range(3, 23):                # the Charts data rows are rewritten below (window 2011-2030E)
        for r_ in range(7, 22): wb['Charts'].cell(r_, col).value = None
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, ArrayFormula):
                    if 'Model!' in (v.text or ''): v.text = remap(v.text)
                elif isinstance(v, str) and 'Model!' in v:
                    c.value = remap(v)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    b = wb['Bull-Base-Bear']
    for r, t in BBB_ROWS.items():
        for c in ('B', 'N', 'Z'): b[f'{c}{r}'] = t
    from openpyxl.comments import Comment
    cm = Comment(f'P/E on non-GAAP EPS (company definition). BCO at ${PX:.2f} trades at ~12.7x 2026E non-GAAP EPS (~$9.0) and ~10x 2027E including NCR Atleos. Exit multiples are assumptions: '
                 'Base 12x, Bull 14x, Bear 9x, applied to the last two forecast years (last three for Bear) — a levered, low-growth cash-logistics and ATM-services profile; update with market data.', 'BCO model')
    cm.width, cm.height = 420, 120; b['N26'].comment = cm
    cm2 = Comment(f'Snapshot (values) of Model rows {R["bb_cash"]}, {R["bb_px"]} and {R["bb_sh"]} (Share Buyback Schedule) with the Model-tab switch (cell {NOTE}2) set to Bull / Bear. '
                  'Base panel (D40:H42) is live-linked.', 'BCO model')
    cm2.width, cm2.height = 420, 90; b['P40'].comment = cm2
    for c in ('B', 'N', 'Z'):
        if b[f'{c}40'].value: b[f'{c}40'] = '   Share repurchases ($m; 2026E = Q4)'
    d = wb['DCF']
    a25, a26, a27 = ANN[2025].c, ANN[2026].c, ANN[2027].c
    d['D31'] = '=0*D24*D30'
    d['D34'] = f'=Model!{a25}{R["ra_ic"]}'
    d['E34'] = f'=D38+Model!{a27}{R["nc_tgl"]}*(Model!{a27}{R["ppa_stock"]}+Model!{a27}{R["ppa_awards"]}+Model!{a27}{R["ppa_debt"]})'
    d['C48'] = (f'=Model!{a26}{R["lv_nd"]}+Model!{a26}{R["bs_nci"]}+Model!{a26}{R["bs_ret"]}'
                f'+Model!{a27}{R["nc_tgl"]}*(Model!{a27}{R["ppa_debt"]}+Model!{a27}{R["ppa_ret"]})')
    d['C50'] = f'=Model!{a27}{R["v_sh"]}'
    d['C52'] = f'=Model!{a26}{R["v_px"]}'
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
    (Charts!C:V = 2011-2030E) and cached values removed so Excel redraws from the BCO cells."""
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
