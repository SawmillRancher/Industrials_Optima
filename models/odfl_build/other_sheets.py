"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template to the ODFL Model rows; keep the template chart XML."""
import re, zipfile, shutil
from fw import R, TEMPLATE

MAP = {158: 'is_rev', 166: 'is_op', 164: 'r_items', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit',
       221: 'r_adj', 229: 'e_adjni', 231: 'e_eps', 238: 'gm_tpd', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex',
       263: 'cf_acq', 280: 'fcf', 282: 'fcf_m', 331: 'v_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta', 428: 'lv_nd',
       433: 'v_px', 434: 'v_sh', 12: 'l_tpd_g', 30: 'l_tpd_g', 14: 'y_xf_g', 31: 'y_xf_g'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")

def remap(f):
    def rep(m):
        r = int(m.group(4))
        if r in MAP: return f'Model!{m.group(1)}{m.group(2)}{m.group(3)}{R[MAP[r]]}'
        return m.group(0)
    return REF.sub(rep, f)

def _three(lab):
    return {c: lab for c in ('B', 'N', 'Z')}

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Old Dominion Freight Line (ODFL) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures are model definitions (ODFL publishes no non-GAAP measures): Adjusted EBITDA / adjusted EPS exclude net gains on disposal of property & '
               'equipment and company-named one-offs · USD millions · Live panel linked to Model — toggle scenario via Model!CF2. Bull and Bear panels are value snapshots '
               'generated from the Model with the switch set to each case.'),
    },
    'DCF': {
        'B2': 'DCF VALUATION — OLD DOMINION FREIGHT LINE (ODFL)',
        'D7': 'LTL peers (SAIA, XPO, ArcBest, TFI) ~1.1–1.4; ODFL ~1.0–1.1 — union-free, net-cash balance sheet and best-in-class service dampen cyclicality',
        'D9': 'Minimal debt ($20m Series B 2.79% notes, final May-2027); $400m revolver at SOFR + 1.00%; marginal cost ~4.5–5.0%',
        'D12': 'Net cash (~$264m at 30-Jun-26) vs ~$41bn market cap ($198.39 × ~208m shares); capital structure effectively all equity',
        'B18': 'Adjusted EBIT (Model; Adjusted EBITDA − D&A)',
        'B20': '(−) Company-identified one-off items (pre-tax; nil in forecast)',
        'B22': 'NOPAT  =  (Adjusted EBIT − one-off items) × (1 − t)',
        'B23': 'plus depreciation & amortization',
        'B24': '− Capex (property & equipment) and acquisitions of business assets',
        'D37': ("ODFL's Adjusted EBITDA (model) expenses share-based compensation and excludes disposal gains on revenue equipment / real estate; capex is "
                'gross of ~0.6% of revenue disposal proceeds (conservative). ODFL capex runs well above D&A in growth phases (2021–24 ~13–15% of revenue).'),
        'D48': ('Opening IC = Model 2025A book IC (equity + net debt), rolled forward with DCF net investment (capex − D&A + ΔWC). '
                'Terminal incremental ROIC = g / reinvestment rate.'),
        'D82': 'Rationale (Old Dominion characteristics)',
        'D84': 'Model Adjusted EBIT CAGR 2026–30E: tons/day recovery (+4–5% p.a.), ex-fuel yield +4–5% and operating-ratio improvement toward 68.5% → ~12% NOPAT growth',
        'D85': 'Service-led share gains on a network with excess door capacity: incremental density earns very high returns (2016–25 ROIC 20–30% after tax on book IC)',
        'D86': 'Union-free, owned real estate (240 of 260 service centers), 99% on-time / 0.1% claims ratio and a decades-long record of LTL share gains; long runway in a consolidating industry',
        'B98': '(−) 2028E company-identified one-off items',
        'B100': '2028E NOPAT  =  (Adj. EBIT − one-off items) × (1 − t)',
        'B115': "ODFL's market-implied EV/NOPAT (on 2028E NOPAT)",
        'B53': 'Less: net debt (Model 2026E YE; negative = net cash)', 'B54': 'Less: non-controlling interests (none)',
        'B56': 'Diluted shares (m, Model 2026E period end)',
        'D5': 'Assumption (~US 10Y Treasury yield); update to market',
        'B76': ('To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C57 (implied price) to the current price (C58) by changing C32 '
                '(terminal growth) or the Model scenario levers (tons/day growth, ex-fuel yield, operating ratio).'),
    },
    'Charts': {
        'B2': 'Old Dominion Freight Line — Historical Operating Performance (2006–2025)',
        'B3': ('All historicals · USDm · Linked to Model. Volume / price = tons per day and revenue per hundredweight excluding fuel surcharges, y/y '
               '(total-tons basis to 2013, LTL from 2014). Adjusted EBITDA = model definition (ODFL publishes no non-GAAP measures). ROIC / RONTA on Adjusted EBIT.'),
        'B8': 'Tons per day y/y %', 'B9': 'Revenue/cwt ex fuel y/y %', 'B13': 'Operating Income (GAAP)',
    },
}
for lab_r, lab in ((9, 'Revenue'), (10, '   Revenue y/y %'), (11, '   LTL tons per day y/y %'), (12, 'Adjusted EBITDA (model)'),
                   (15, 'Operating Income (GAAP)'), (16, '   Operating income y/y %'), (17, '   Operating margin (1 − operating ratio) %'),
                   (19, 'Adjusted Net Income (model)'), (35, 'Adjusted EBITDA (leverage basis)'), (36, '   Adjusted EBITDA % of revenue'),
                   (38, 'Net Debt (negative = net cash)')):
    for c in ('B', 'N', 'Z'):
        TEXT['Bull-Base-Bear'][f'{c}{lab_r}'] = lab

CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'LTL Revenue Drivers: Tons per Day vs. Revenue/cwt ex Fuel, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA (model) &amp; Operating Income (USDm)',
}

def do_all(wb):
    for name in ('Bull-Base-Bear', 'DCF', 'Charts'):
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and 'Model!' in c.value:
                    c.value = remap(c.value)
        for addr, t in TEXT.get(name, {}).items():
            ws[addr] = t
    d = wb['DCF']
    d['D42'] = f'=Model!BV{R["ra_ic"]}'
    d['C7'] = 1.05
    d['C9'] = 0.048
    d['C10'] = 0.25
    d['C12'] = 0.02
    d['D10'] = 'Model 2027E+ effective tax rate (1H/26 25.0%)'
    d['C84'] = 0.11; d['C85'] = 0.25; d['C86'] = 15
    b = wb['Bull-Base-Bear']
    b['J2'] = 'Share price ($):'
    for c in ('G', 'H'): b[f'{c}26'] = 28      # ODFL 10-year average forward P/E ~27-30x
    for c in ('S', 'T'): b[f'{c}26'] = 32
    for c in ('AD', 'AE', 'AF'): b[f'{c}26'] = 22

def snapshot_values(wb, bull, bear):
    ws = wb['Bull-Base-Bear']
    cols = 'CDEFGHIJKL'
    for snap, off in ((bull, 'OPQRSTUVWX'), (bear, ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ'])):
        for (r, c), v in snap.items():
            tgt = f'{off[cols.index(c)]}{r}'
            cur = ws[tgt].value
            if isinstance(cur, str) and cur.startswith('='): continue
            if r in (26,): continue
            ws[tgt] = v

def inject_charts(path):
    """Replace openpyxl-rewritten chart parts with the template chart XML (keeps the combo chart, colours and layout), retitled."""
    tz = zipfile.ZipFile(TEMPLATE)
    tmpl = {n: tz.read(n) for n in tz.namelist() if n.startswith('xl/charts/chart')}
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in tmpl:
                t = tmpl[item.filename].decode('utf-8')
                for a, b2 in CHART_TITLES.items(): t = t.replace(a, b2)
                data = t.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, path)
