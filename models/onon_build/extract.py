"""Per-period extraction from On Holding releases (6-K Ex. 99.1 / 99.3) and MD&A exhibits (6-K Ex. 99.2) -> data/<period>.json.

Periods: quarters 'Q1-22' (discrete three-month), year-to-date 'H1-22' / '9M-22', fiscal years '2022'. Each file holds the
as-originally-reported figures (sections is / ng / ani_A / ani_B / bs / cf / ch / rg / pr) and, under 'cmp', the prior-year
comparatives printed in the following year's release (used only where no original exists, e.g. 2021 quarters, or for
re-based disclosures such as the 2022 quarters on the EMEA / Americas / APAC basis). Values in CHF millions as published
(expenses negative as in the statements); per-share in CHF; share counts in units.
"""
import os, re, json, glob
from parse_release import tables, label, colmap, row_values

S = os.environ.get('ONON_SRC', '/tmp/onon_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')

IS = {'Net sales': 'rev', 'Cost of sales': 'cogs', 'Gross profit': 'gp', 'Selling, general and administrative expenses': 'sga',
      'Operating result': 'op', 'Financial income': 'fin_inc', 'Financial expenses': 'fin_exp', 'Foreign exchange result': 'fx',
      'Foreign exchange gain / (loss)': 'fx', 'Income / (Loss) before taxes': 'ebt', 'Income / (loss) before taxes': 'ebt',
      'Income before taxes': 'ebt', 'Income tax benefit / (expense)': 'tax', 'Income tax expense': 'tax', 'Income taxes': 'tax',
      'Net income': 'ni', 'Net income / (loss)': 'ni', 'Net loss': 'ni', 'Basic EPS Class A (CHF)': 'eps_a',
      'Diluted EPS Class A (CHF)': 'eps_dil_a', 'Basic EPS Class B (CHF)': 'eps_b', 'Diluted EPS Class B (CHF)': 'eps_dil_b'}
NG = {'Net income': 'ni', 'Net income / (loss)': 'ni', 'Net (loss)': 'ni', 'Net loss': 'ni', 'Depreciation and amortization': 'dna',
      'Share-based compensation': 'sbc', 'Equity transaction costs': 'etc', 'Adjusted EBITDA': 'adj_ebitda',
      'Income taxes': 'tax_rc', 'Financial income': 'fin_inc_rc', 'Financial expenses': 'fin_exp_rc', 'Foreign exchange result': 'fx_rc'}
ANI = {'Net income': 'ni', 'Net income / (loss)': 'ni', 'Share-based compensation': 'sbc', 'Equity transaction costs': 'etc',
       'Tax effect of adjustments': 'tax_eff', 'Adjusted Net income': 'adj_ni', 'Adjusted net income': 'adj_ni',
       'Adjusted net income / (loss)': 'adj_ni', 'Weighted number of outstanding shares': 'wsh',
       'Weighted number of shares with dilutive effects': 'wsh_dileff',
       'Weighted number of outstanding shares (diluted and undiluted)': 'wsh_dil', 'Adjusted EPS (CHF)': 'adj_eps',
       'Adjusted basic EPS (CHF)': 'adj_eps', 'Adjusted Basic EPS (CHF)': 'adj_eps', 'Adjusted diluted EPS (CHF)': 'adj_eps_dil',
       'Adjusted Diluted EPS (CHF)': 'adj_eps_dil'}
BS = {'Cash and cash equivalents': 'cash', 'Cash and cash equivalents  (excluding bank overdrafts)': 'cash', 'Trade receivables': 'ar',
      'Inventories': 'inv', 'Other current financial assets': 'ocfa', 'Other current operating assets': 'ocoa', 'Current assets': 'tca',
      'Property, plant and equipment': 'ppe', 'Right-of-use assets': 'rou', 'RoU assets': 'rou', 'Intangible assets': 'intang',
      'Deferred tax assets': 'dta', 'Non-current assets': 'tnca', 'Assets': 'ta', 'Trade payables': 'ap', 'Current lease liabilities': 'cll',
      'Other current financial liabilities': 'ocfl', 'Other current operating liabilities': 'ocol', 'Current provisions': 'cprov',
      'Income tax liabilities': 'itl', 'Current liabilities': 'tcl', 'Employee benefit obligations': 'ebo', 'Non-current provisions': 'ncprov',
      'Non-current lease liabilities': 'ncll', 'Other non-current financial liabilities': 'oncfl', 'Other non-current liabilities': 'oncfl',
      'Deferred tax liabilities': 'dtl', 'Non-current liabilities': 'tncl', 'Share capital': 'sh_cap', 'Treasury shares': 'treas',
      'Capital reserves': 'cap_res', 'Other reserves': 'oth_res', 'Accumulated losses': 're', 'Retained earnings': 're',
      'Retained earnings / (losses)': 're', 'Equity': 'teq', 'Equity and liabilities': 'tle', 'Liabilities and equity': 'tle'}
CF = {'Net income': 'ni', 'Net income / (loss)': 'ni', 'Net loss': 'ni', 'Net (loss)': 'ni', 'Share-based compensation': 'sbc',
      'Employee benefit expenses': 'ebe', 'Employee benefit expenses / (income)': 'ebe', 'Depreciation and amortization': 'dna',
      'Loss / (gain) on disposal of assets': 'disp', 'Loss on disposal of assets': 'disp', 'Loss on disposal of assets and impairment': 'disp',
      'Loss/(gain) on disposal of assets': 'disp', 'Loss/gain on disposal of assets': 'disp',
      'Interest income and expense': 'int', 'Interest income and expenses': 'int', 'Net exchange differences': 'fxd', 'Income taxes': 'tax',
      'Change in provision': 'prov', 'Change in provisions': 'prov', 'Trade receivables': 'd_ar', 'Inventories': 'd_inv', 'Trade payables': 'd_ap',
      'Change in other current assets / liabilities': 'd_oth', 'Change in other current operating assets and liabilities': 'd_oth',
      'Change in other current operating assets / liabilities': 'd_oth',
      'Interest received': 'int_rec', 'Interests received': 'int_rec', 'Income taxes paid': 'tax_paid',
      'Cash flow from operating activities': 'cfo', 'Cash inflow / (outflow) from operating activities': 'cfo',
      'Cash inflow from operating activities': 'cfo', 'Cash outflow from operating activities': 'cfo',
      'Purchase tangible assets': 'capex_ppe', 'Purchase of tangible assets': 'capex_ppe', 'Purchase of property, plant and equipment': 'capex_ppe',
      'Purchase of intangible assets': 'capex_int', 'Proceeds from disposal of tangible assets': 'disp_proc',
      'Payment of contingent considerations': 'contingent', 'Investment in subsidiary, net of cash acquired': 'acq',
      'Cash flow from investing activities': 'cfi', 'Cash inflow / (outflow) from investing activities': 'cfi',
      'Change in other operating assets / liabilities': 'd_oth', 'Cash (outflow) from investing activities': 'cfi', 'Cash outflow from investing activities': 'cfi',
      'Repayment of financial liabilities': 'debt_rep', 'Repayments of financial liabilities': 'debt_rep', 'Proceeds from financial liabilities': 'debt_iss',
      'Payments of lease liabilities': 'lease_pay', 'Proceeds from issue of shares': 'sh_iss', 'Proceeds from issuance of shares': 'sh_iss',
      'Net proceeds from the IPO': 'sh_iss', 'Equity transaction costs': 'etc_cf',
      'Proceeds on sale of treasury shares related to share-based compensation': 'treas_sale',
      'Sale of treasury shares related to share-based compensation': 'treas_sale', 'Interests paid': 'int_paid', 'Interest paid': 'int_paid',
      'Cash flow from financing activities': 'cff', 'Cash (outflow) from financing activities': 'cff',
      'Cash inflow / (outflow) from financing activities': 'cff', 'Cash inflow from financing activities': 'cff',
      'Change in cash and cash equivalents': 'chg', 'Change in net cash and cash equivalents': 'chg',
      'Net impact of foreign exchange rate differences': 'fx_cash'}
CF_BEG = ('at 1 January', 'at January 1', 'as of January 1', 'beginning of the year')
CF_END = ('at 30 September', 'at December 31', 'as of December 31', 'at June 30', 'at March 31', 'at September 30', 'end of the period')
SPLIT = {'Wholesale': ('ch', 'whs'), 'DTC': ('ch', 'dtc'), 'Direct-to-consumer': ('ch', 'dtc'), 'Direct-to-Consumer': ('ch', 'dtc'),
         'Europe': ('rg', 'eu'), 'North America': ('rg', 'na'), 'Rest of World': ('rg', 'row'),
         'Asia-Pacific': ('rg', 'apac'), 'Europe, Middle East and Africa': ('rg', 'emea'), 'EMEA': ('rg', 'emea'), 'Americas': ('rg', 'am'),
         'Shoes': ('pr', 'shoes'), 'Apparel': ('pr', 'apparel'), 'Accessories': ('pr', 'acc')}

def kind(t):
    s = ' '.join(r[0] for r in t['rows'])
    if 'Cost of sales' in s: return 'is'
    if 'Equity and liabilities' in s or 'Liabilities and equity' in s: return 'bs'
    if 'operating activities' in s: return 'cf'
    if re.search(r'Adjusted [Nn]et income', s): return 'ani'
    if 'Adjusted EBITDA' in s: return 'ng'
    if 'Net working capital' in s: return 'nwc'
    if 'Wholesale' in s: return 'ch'
    if 'Americas' in s or 'North America' in s: return 'rg'
    if 'Shoes' in s: return 'pr'
    return None

def rel_period(fname):
    d = os.path.basename(fname)[:10]; y, m = int(d[:4]), int(d[5:7])
    if m in (2, 3): return 'Q4', y - 1
    if m in (4, 5): return 'Q1', y
    if m in (7, 8, 9): return 'Q2', y
    return 'Q3', y

def key_for(group, q, fy):
    yy = str(fy)[2:]
    if group == '3M': return f'{q}-{yy}'
    if group == '6M': return f'H1-{yy}'
    if group == '9M': return f'9M-{yy}'
    if group == 'FY': return str(fy)
    return None

def ytd_key(q, fy):
    return {'Q1': f'Q1-{str(fy)[2:]}', 'Q2': f'H1-{str(fy)[2:]}', 'Q3': f'9M-{str(fy)[2:]}', 'Q4': str(fy)}[q]

D = {}
def put(per, sec, k, v, src, cmp=False):
    if v is None: return
    rec = D.setdefault(per, {'period': per})
    tgt = rec.setdefault('cmp', {}) if cmp else rec
    s = tgt.setdefault(sec, {})
    if k not in s:
        s[k] = round(v, 6)
        rec.setdefault('sources', {}).setdefault(sec if not cmp else 'cmp_' + sec, src)

def year_of(tok):
    m = re.search(r'(20\d\d)', tok or '')
    return int(m.group(1)) if m else None

def process(fname, splits_only=False):
    q, fy = rel_period(fname)
    src = os.path.basename(fname)
    for t in tables(open(fname).read()):
        k = kind(t)
        if k is None or k == 'nwc': continue
        if splits_only and k not in ('ch', 'rg', 'pr'): continue
        u = t['unit']
        groups = t['groups']
        if k in ('bs',):
            cm = colmap(t)
            for r in t['rows']:
                lab = label(r); f = BS.get(lab)
                if not f: continue
                vals = row_values(t, r)
                for i, ((g, tok, kd, cl), v) in enumerate(vals[:2]):
                    if kd != 'v' or v is None: continue
                    y = year_of(tok)
                    if i == 0:
                        put(f'{q}-{str(fy)[2:]}', 'bs', f, v * u, src)
                        if q == 'Q4': put(str(fy), 'bs', f, v * u, src)
                    elif y == fy - 1 and ('12/31' in tok or 'December' in tok):
                        put(str(fy - 1), 'bs', f, v * u, src, cmp=True); put(f'Q4-{str(fy - 1)[2:]}', 'bs', f, v * u, src, cmp=True)
            continue
        if k == 'cf':
            ytd = ytd_key(q, fy)
            for r in t['rows']:
                lab = label(r)
                f = CF.get(lab)
                if f is None:
                    if any(x in lab for x in CF_BEG): f = 'beg'
                    elif any(x in lab for x in CF_END): f = 'end'
                    elif 'thereof restricted' in lab or lab.startswith('Change in working capital'): continue
                    else:
                        put(ytd, 'cf_unmapped', lab, 0.0, src); continue
                vals = [(c, v) for c, v in row_values(t, r) if c[2] == 'v']
                if not vals: continue
                if vals[0][1] is not None: put(ytd, 'cf', f, vals[0][1] * u, src)
                if len(vals) > 1 and vals[1][1] is not None:
                    put(ytd_key(q, fy - 1), 'cf', f, vals[1][1] * u, src, cmp=True)
            continue
        if k == 'ani':
            g = groups[0] if groups else ('FY' if q == 'Q4' else '3M')
            for r in t['rows']:
                f = ANI.get(label(r).replace(' (3)', '').replace(' (4)', '').replace(' (5)', ''))
                if not f: continue
                for (gg, tok, kd, cl), v in row_values(t, r):
                    if kd != 'v' or v is None or cl is None: continue
                    y = year_of(tok); per = key_for(g, q, y if y else fy)
                    sc = 'ani_' + cl[-1]
                    unit = 1.0 if f.startswith('wsh') or f.startswith('adj_eps') else u
                    put(per, sc, f, v * unit, src, cmp=(y != fy))
            continue
        # is / ng / splits: grouped columns
        old_basis = any(label(r) in ('Europe', 'North America') for r in t['rows'])
        for r in t['rows']:
            lab = label(r)
            if k == 'is': sec, f = 'is', IS.get(lab)
            elif k == 'ng': sec, f = 'ng', NG.get(lab)
            else:
                if lab in ('Net sales', 'Net Sales'): sec, f = k, 'total'
                elif lab in SPLIT:
                    sec, f = SPLIT[lab]
                    if old_basis and f == 'apac': f = 'apac_o'
                else: continue
            if not f: continue
            vals = row_values(t, r)
            last_v = None
            for (g, tok, kd, cl), v in vals:
                if v is None: continue
                if kd == 'v':
                    y = year_of(tok); per = key_for(g, q, y)
                    if per is None: continue
                    unit = 1.0 if f.startswith('eps') else u
                    put(per, sec, f, v * unit, src, cmp=(y != fy)); last_v = (g, y)
                elif kd == 'cc' and last_v:
                    g0 = g or last_v[0]
                    per = key_for(g0, q, fy)
                    put(per, sec, f + '_ccg', v / 100.0, src)
                elif kd == 'pct' and last_v and sec in ('ch', 'rg', 'pr'):
                    per = key_for(g or last_v[0], q, fy)
                    put(per, sec, f + '_g', v / 100.0, src)

def main():
    T = os.path.join(S, 'txt')
    rel = sorted(f for f in glob.glob(T + '/*6-K*') if re.search(r'press|ex991press|a991press|ex993xpress|ex991xpress', os.path.basename(f))
                 and not re.search(r'investorday|2023-05-02|2026-01-28', f))
    mda = sorted(f for f in glob.glob(T + '/*6-K*') if re.search(r'mda|managementsdisc', os.path.basename(f)))
    for f in rel: process(f)
    for f in mda: process(f, splits_only=True)
    # releases FY24+ carry 3M and FY split tables: handled above. Manual annual / prospectus items
    man = json.load(open(os.path.join(HERE, 'manual_items.json')))
    for per, secs in man['periods'].items():
        for sec, kv in secs.items():
            if sec.startswith('_'): continue
            for k, v in kv.items(): put(per, sec, k, v, man['sources'].get(per, 'manual_items.json'))
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(OUT + '/*.json'): os.remove(old)
    for per, rec in D.items():
        json.dump(rec, open(os.path.join(OUT, f'{per}.json'), 'w'), indent=1, sort_keys=True)
    print(len(D), 'periods:', ' '.join(sorted(D)))

if __name__ == '__main__':
    main()
