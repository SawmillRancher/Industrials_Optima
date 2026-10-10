"""Rewire the Bull-Base-Bear, DCF and Charts tabs of the MLM template to the WAB Model rows; keep the template chart XML."""
import re, zipfile, shutil, os
from fw import R, TEMPLATE

MAP = {158: 'is_rev', 166: 'is_op', 164: 'o_trans', 182: 'is_dda', 186: 'sh_dil', 211: 'r_adj', 212: 'r_adj_m', 219: 'r_ebit',
       221: 'r_adj', 229: 'e_adjni', 231: 'e_eps', 238: 'gm_org', 245: 'gm_ebitda_m', 247: 'gm_op_m', 260: 'cf_wc', 262: 'cf_capex',
       263: 'cf_acq', 280: 'fcf', 282: 'fcf_m', 331: 'bs_nci', 408: 'ra_ic', 411: 'ra_roic', 422: 'rn_ronta', 428: 'lv_nd',
       433: 'v_px', 434: 'v_sh', 12: 'f_rev_g', 30: 'f_rev_g', 14: 't_rev_g', 31: 't_rev_g'}
REF = re.compile(r"Model!(\$?)([A-Z]{1,3})(\$?)(\d+)")

def remap(f):
    def rep(m):
        r = int(m.group(4))
        if r in MAP: return f'Model!{m.group(1)}{m.group(2)}{m.group(3)}{R[MAP[r]]}'
        return m.group(0)
    return REF.sub(rep, f)

TEXT = {
    'Bull-Base-Bear': {
        'B2': 'Westinghouse Air Brake Technologies (WAB) — Bull / Base / Bear Case P&L Summary',
        'B3': ('Adjusted figures (company definitions: Adjusted EBITDA; adjusted EPS incl. add-back of non-cash amortization) · USD millions · '
               'Live panel linked to Model — toggle scenario via Model!CF2. Bull and Bear panels are value snapshots generated from the Model with the switch set to each case. '
               '2026E includes Dellner Couplers from 10-Feb-2026.'),
        'B9': 'Net Sales', 'N9': 'Net Sales', 'Z9': 'Net Sales',
        'B10': '   Net sales y/y %', 'N10': '   Net sales y/y %', 'Z10': '   Net sales y/y %',
        'B11': '   Organic sales growth %', 'N11': '   Organic sales growth %', 'Z11': '   Organic sales growth %',
        'B12': 'Adjusted EBITDA', 'N12': 'Adjusted EBITDA', 'Z12': 'Adjusted EBITDA',
        'B15': 'Income from Operations (GAAP)', 'N15': 'Income from Operations (GAAP)', 'Z15': 'Income from Operations (GAAP)',
        'B16': '   Income from operations y/y %', 'N16': '   Income from operations y/y %', 'Z16': '   Income from operations y/y %',
        'B19': 'Adjusted Net Income (attributable to Wabtec)', 'N19': 'Adjusted Net Income (attributable to Wabtec)', 'Z19': 'Adjusted Net Income (attributable to Wabtec)',
        'B35': 'Adjusted EBITDA (leverage basis)', 'N35': 'Adjusted EBITDA (leverage basis)', 'Z35': 'Adjusted EBITDA (leverage basis)',
        'B36': '   Adjusted EBITDA % of net sales', 'N36': '   Adjusted EBITDA % of net sales', 'Z36': '   Adjusted EBITDA % of net sales',
    },
    'DCF': {
        'B2': 'DCF VALUATION — WESTINGHOUSE AIR BRAKE TECHNOLOGIES (WAB)',
        'D7': 'Rail equipment / transportation-technology peers (Knorr-Bremse, Alstom, Siemens Mobility, Trinity, Greenbrier) ~0.9–1.2; 25,000+ locomotive installed base and multi-year backlog ($30.9bn) dampen cyclicality',
        'D9': 'Investment grade (BBB / Baa2); 5.50% 2035 and 4.90% 2030 notes issued 2025; marginal cost ~5.0–5.5%',
        'D12': 'Net debt ~$5.9bn at 30-Jun-26 vs ~$47bn market cap ($280 × ~169m shares); ~2.0x Adjusted EBITDA, targeted 2.0–2.5x',
        'B20': '(−) Restructuring & transaction costs (cash; added back in Adjusted EBITDA)',
        'B22': 'NOPAT  =  (Adjusted EBIT − restructuring & transaction costs) × (1 − t)',
        'B23': 'plus depreciation & amortization (total, incl. acquired-intangible amortization)',
        'B24': '− Capex (PP&E) and acquisitions (M&A lever, 2027E+)',
        'D37': ("Wabtec's Adjusted EBITDA expenses stock-based compensation; Adjusted EBIT deducts all D&A incl. ~$350m p.a. of acquired-intangible amortization "
                '(non-cash, added back in row 23). The 1H/26 Dellner cash consideration (~$1.06bn) is excluded from 2026E UFCF and added to opening invested capital.'),
        'D48': ('Opening IC = Model 2025A book IC (equity + net debt) + 2026 acquisitions (Dellner, ~$1.06bn cash), rolled forward with DCF net investment '
                '(capex + M&A − D&A + ΔWC). Terminal incremental ROIC = g / reinvestment rate.'),
        'D82': 'Rationale (Wabtec characteristics)',
        'D84': 'Model Adjusted EBIT CAGR 2026–30E: mid-single-digit organic growth (locomotive & digital backlog), 50–100 bps p.a. margin expansion, bolt-on M&A → ~9–10% NOPAT growth',
        'D85': 'Installed-base aftermarket (services ~25% of sales) and proprietary locomotive / brake / PTC technology earn high returns on organic investment (capex ~2% of sales); acquired growth earns ~7–9% after tax on purchase price',
        'D86': 'Duopoly in N.A. freight locomotives with ~25,000-unit installed base, 20–30-year asset lives and multi-year backlog; disciplined Integration 3.0 / portfolio optimization',
        'B98': '(−) 2028E restructuring & transaction costs',
        'B100': '2028E NOPAT  =  (Adj. EBIT − restructuring & transaction costs) × (1 − t)',
        'B115': "WAB's market-implied EV/NOPAT (on 2028E NOPAT)",
        'B53': 'Less: net debt (Model 2026E YE)', 'B56': 'Diluted shares (m, Model 2026E period end)',
        'D5': 'Assumption (~US 10Y Treasury yield); update to market',
        'B76': ('To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C57 (implied price) to the current price (C58) by changing C32 '
                '(terminal growth) or the Model scenario levers (product-line growth, segment adjusted margins).'),
    },
    'Charts': {
        'B2': 'Westinghouse Air Brake Technologies (Wabtec) — Historical Operating Performance (2006–2025)',
        'B3': ('All historicals · USDm · Linked to Model. Bars = Freight and Transit segment net sales y/y (as originally reported; 2019 includes GE Transportation from 25-Feb-2019). '
               'Adjusted EBITDA as reconciled by Wabtec in each period (published from 2019; EBITDA definition per Model). ROIC / RONTA on Adjusted EBIT.'),
        'B8': 'Freight segment sales y/y %', 'B9': 'Transit segment sales y/y %', 'B13': 'Income from Operations (GAAP)',
    },
}
CHART_TITLES = {
    'Aggregates Revenue Drivers: Shipment Volume vs. Price (ASP), y/y %': 'Segment Sales Growth: Freight vs. Transit, y/y %',
    'Adjusted EBITDA &amp; Earnings from Operations (USDm)': 'Adjusted EBITDA &amp; Income from Operations (USDm)',
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
    d['D42'] = f'=Model!BV{R["ra_ic"]}-Model!CA{R["cf_acq"]}'
    d['C7'] = 1.05
    d['C9'] = 0.055
    d['C10'] = 0.245
    d['C12'] = 0.15
    d['D10'] = 'Model 2027E+ effective tax rate (FY26 guidance ~24.5%)'
    d['C84'] = 0.09; d['C85'] = 0.14; d['C86'] = 12
    b = wb['Bull-Base-Bear']
    b['J2'] = 'Share price ($):'

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
