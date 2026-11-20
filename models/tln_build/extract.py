"""Per-period extraction of the Talen statements from the EDGAR text files ($TLN_SRC/txt, see fetch.py) into data/<tag>.json.

Sources, in filing order (the first filing that presents a period wins = as originally reported):
  S-1 (20-Jun-2024): FY2021, FY2022, 1-Jan..17-May-2023 (Predecessor, tag P23), 18-May..31-Dec-2023 (Successor, tag S23),
      Q1-23 (Predecessor), Q1-24; balance sheets 31-Dec-2022, 31-Dec-2023, 31-Mar-2024.
  10-Q Q2-24: Q2-24, H1-24 and the 2023 comparatives split at Emergence: 18-May..30-Jun-2023 (S23a), 1-Apr..17-May-2023 (P23b).
  10-Q Q3-24: Q3-24, 9M-24, Q3-23 (Successor), 18-May..30-Sep-2023 (S23c).
  10-K FY2024 / FY2025 and the 2025-26 10-Qs: regular columns.
  8-K Ex. 99.1 earnings releases: net income -> Adjusted EBITDA -> Adjusted Free Cash Flow reconciliations, total generation.
Raw tags: fiscal years '2021'..; quarters 'Q1-24'; year-to-date 'H1-24', '9M-24'; partial 2023 periods P23, S23, S23a, P23b, S23c.
Each record: {'is':{}, 'bs':{}, 'cf':{}, 'ng':{}, 'seg':{}, 'ops':{}, 'sources':[], 'notes':[]}. Units USD m as published; costs are
stored positive; income items signed by their effect on income; cash flow as presented. normalize.py combines the tags."""
import os, re, glob, json
from parse_release import num, clean, find, block
S = os.environ.get('TLN_SRC', '/tmp/tln_src'); T = os.path.join(S, 'txt')
HERE = os.path.dirname(os.path.abspath(__file__))
REC = {}
def rec(tag): return REC.setdefault(tag, {'is': {}, 'bs': {}, 'cf': {}, 'ng': {}, 'seg': {}, 'ops': {}, 'sources': [], 'notes': []})
FIL = {}
import csv
for r in csv.DictReader(open(os.path.join(HERE, 'filings.csv'))): FIL[r['accession']] = r
def url_of(path):
    b = os.path.basename(path); m = re.match(r'(\d{4}-\d\d-\d\d)_([^_]+)_(\d{10}-\d\d-\d{6})_(.+)\.txt', b)
    return f"https://www.sec.gov/Archives/edgar/data/1622536/{m.group(3).replace('-', '')}/{m.group(4)}.htm"
def src(tag, sec, u):
    s = f'{sec}: {u}'
    if s not in rec(tag)['sources']: rec(tag)['sources'].append(s)

IS_MAP = [(r'^Capacity revenues', 'cap_rev', 1), (r'^Energy and other revenues', 'en_rev', 1), (r'^Operating Revenues', 'rev', 1),
          (r'^Fuel and energy purchases', 'fuel', -1), (r'^Nuclear fuel amortization', 'nfa', -1), (r'^(Total )?Energy Expenses', 'en_exp', -1),
          (r'^Operation, maintenance and development', 'om', -1), (r'^General and administrative', 'ga', -1),
          (r'^Depreciation, amortization and accretion', 'dda', -1), (r'^Impairments', 'impair', -1), (r'^Operational restructuring', 'restr_op', -1),
          (r'^Other operating income \(expense\), net', 'oth_op', 1), (r'^Operating Income \(Loss\)', 'oi', 1),
          (r'^Nuclear decommissioning trust funds gain \(loss\), net', 'ndt', 1), (r'^Interest expense and other finance charges', 'int', -1),
          (r'^Reorganization income \(expense\), net', 'reorg', 1), (r'^Consolidation of subsidiary gain \(loss\)', 'consol', 1),
          (r'^Gain \(loss\) on sale of assets, net', 'gain_sale', 1), (r'^Other non-operating income \(expense\), net', 'oth_nonop', 1),
          (r'^Income \(Loss\) Before Income Taxes', 'ebt', 1), (r'^Income tax benefit \(expense\)', 'tax', -1), (r'^Net Income \(Loss\)$', 'ni_tot', 1),
          (r'^Less: Net income \(loss\) attributable to noncontrolling interest', 'nci', 1), (r'^Net Income \(Loss\) Attributable to Stockholders( \(Successor\).*)?$', 'ni', 1),
          (r'Attributable to Stockholders - Basic', 'eps_b', 1), (r'Attributable to Stockholders - Diluted', 'eps_d', 1),
          (r'^Weighted-Average Number of Common Shares Outstanding - Basic', 'sh_b', 0.001), (r'^Weighted-Average Number of Common Shares Outstanding - Diluted', 'sh_d', 0.001)]
BS_MAP = [(r'^Cash and cash equivalents', 'cash'), (r'^Restricted cash', 'rcash'), (r'^Accounts receivable', 'ar'), (r'^Inventory', 'inv'),
          (r'^Assets held for sale', 'ahs'), (r'^Other current assets', 'oca'), (r'^Total current assets', 'tca'), (r'^Property, plant and equipment', 'ppe'),
          (r'^Nuclear decommissioning trust funds', 'ndt'), (r'^Other noncurrent assets', 'onca'), (r'^Total Assets', 'ta'),
          (r'^Revolving credit facilities', 'rcf'), (r'^Long-term debt, due within one year', 'cpltd'), (r'^Accrued interest', 'accint'),
          (r'^Accounts payable and other accrued liabilities', 'ap'), (r'^Liabilities held for sale', 'lhs'), (r'^Stock-based compensation liabilities', 'sbc_liab'),
          (r'^Other current liabilities', 'ocl'), (r'^Total current liabilities', 'tcl'), (r'^Long-term debt$', 'ltd'), (r'^Liabilities subject to compromise', 'lstc'),
          (r'^Postretirement benefit obligations', 'pension'), (r'^Asset retirement obligations', 'aro'), (r'^Deferred income taxes', 'dtl'),
          (r'^Acquired (fuel supply )?contract liabilities', 'acl'), (r'^Other noncurrent liabilities', 'oncl'), (r'^Total Liabilities$', 'tl'),
          (r'^Additional paid-in capital', 'apic'), (r'^Accumulated retained earnings', 're'), (r'^Accumulated other comprehensive', 'aoci'),
          (r'^Treasury stock', 'treas'), (r'^Member.s equity', 'member'), (r'^Total Stockholders', 'eq'), (r'^Noncontrolling interests', 'nci'), (r'^Total Equity', 'teq'),
          (r'^Total Liabilities and', 'tle')]
CF_MAP = [(r'^Net [Ii]ncome \(loss\)|^Net Income \(Loss\)', 'ni'), (r'^Unrealized \(gains\) losses on derivative', 'unr'), (r'^Nuclear fuel amortization', 'nfa'),
          (r'^Depreciation, amortization and accretion', 'dda'), (r'^(NDT|Nuclear decommissioning trust) funds \(gain\) loss', 'ndt'), (r'^Deferred income taxes', 'def'),
          (r'^Stock-based compensation', 'sbc'), (r'^\(Gain\) loss on (sales of assets|Cumulus|AWS|consolidation)|^Consolidation of subsidiary \(gain\)', 'gain'),
          (r'^Impairments', 'impair'), (r'^Operational restructuring', 'restr'), (r'^Reorganization \(income\) expense', 'reorg'),
          (r'^Net cash provided by \(used in\) operating', 'cfo'), (r'^Property, plant and equipment expenditures', 'capex'), (r'^Nuclear fuel expenditures', 'nfuel'),
          (r'^(NDT|Nuclear decommissioning trust) funds investment (sale proceeds|purchases)', 'ndt_inv'),
          (r'^(Freedom and Guernsey Acquisitions|Cornerstone Acquisition), net', 'acq'), (r'^Proceeds from', 'proceeds'),
          (r'^Net cash provided by \(used in\) investing', 'cfi'), (r'^Share repurchases', 'bb'), (r'^Repurchase of noncontrolling interest|^Repurchase of Riverstone', 'nci_rep'),
          (r'^(Repurchase of warrants|Exercise or repurchase of warrants)', 'warr'), (r'^(Cash settlement of restricted stock units|Tax payments related to net-settled)', 'sbc_fin'),
          (r'^Net cash provided by \(used in\) financing', 'cff'), (r'^Net [Ii]ncrease \(Decrease\) in Cash|^Net increase \(decrease\) in cash', 'net'),
          (r'^Beginning of period cash', 'beg'), (r'^End of period cash', 'end'), (r'^Cash settlement of stock-based awards', 'sbc_cash'),
          (r'^Collateral received', 'collat')]
ADD = {'gain', 'ndt_inv', 'proceeds', 'acq', 'sbc_fin'}

def apply(rows, mp, cols, sec, u, sign=True, only=None):
    seen = {}
    for label, vals in rows:
        for pat in mp:
            if re.search(pat[0], label):
                key = pat[1]; mult = pat[2] if len(pat) > 2 else 1
                if sec == 'is' and key == 'ga':
                    m = re.search(r'stock-based compensation of (.*)\)$', label)
                    if m: seen['__sbc'] = [num(x) for x in re.findall(r'\$\s*\(?\s*[\d,]+\s*\)?', m.group(1))]
                for j, tag in enumerate(cols):
                    if tag is None or j >= len(vals) or vals[j] is None: continue
                    if only and tag not in only: continue
                    d = rec(tag)[sec]
                    if (tag, sec) in DONE: continue
                    v = vals[j] * mult
                    if sec == 'is' and key == 'unr': pass
                    if key in ADD and (tag, key) in seen: d[key] = round(d[key] + v, 6)
                    else: d[key] = v if key not in d or (tag, key) not in seen else d[key]
                    seen[(tag, key)] = 1
                break
    return seen
DONE = set()
def close(cols, sec, u):
    for tag in cols:
        if tag and (tag, sec) not in DONE and rec(tag)[sec]:
            DONE.add((tag, sec)); src(tag, sec, u)

def statements(path, n, is_cols, bs_cols, cf_cols):
    L = open(path).read().split('\n'); u = url_of(path) if '_' in os.path.basename(path) else 'https://www.sec.gov/Archives/edgar/data/1622536/000162828024029107/talen-sx1.htm'
    i = find(L, r'^(CONDENSED )?CONSOLIDATED STATEMENTS OF OPERATIONS', nth=n)
    rows = block(L, i, r'^Weighted-Average Number of Common Shares Outstanding - Diluted')
    seen = apply(rows, IS_MAP, is_cols, 'is', u)
    # unrealized derivative lines: first = revenues, second = energy expenses
    un = [v for l, v in rows if l.startswith('Unrealized gain (loss) on derivative instruments')]
    for j, tag in enumerate(is_cols):
        if tag and (tag, 'is') not in DONE and len(un) == 2:
            rec(tag)['is']['unr_rev'] = un[0][j]; rec(tag)['is']['unr_exp'] = un[1][j]
    if '__sbc' in seen:
        for j, tag in enumerate(is_cols):
            if tag and (tag, 'is') not in DONE and j < len(seen['__sbc']): rec(tag)['is']['ga_sbc'] = -seen['__sbc'][j]
    close(is_cols, 'is', u)
    j = find(L, r'^(CONDENSED )?CONSOLIDATED BALANCE SHEETS', start=i)
    rows = block(L, j, r'^Total Liabilities and (Stockholders. )?Equity')
    apply(rows, BS_MAP, bs_cols, 'bs', u)
    dv = [v for l, v in rows if l.startswith('Derivative instruments')]
    for k, tag in enumerate(bs_cols):
        if tag and (tag, 'bs') not in DONE and len(dv) == 4:
            for nm, row in zip(('der_ca', 'der_nca', 'der_cl', 'der_ncl'), dv): rec(tag)['bs'][nm] = row[k]
    sh = re.findall(r'([\d,]{9,}) (?:and ([\d,]{9,}) )?shares issued and outstanding', ' '.join(L[j:j + 70]).replace('\n', ' '))
    if not sh: sh = re.findall(r'([\d,]{9,}) (?:and ([\d,]{9,}) )?shares (?:of common stock )?issued and outstanding', ' '.join(L[j:j + 70]))
    if sh:
        for k, tag in enumerate(bs_cols):
            if tag and (tag, 'bs') not in DONE and k < len([x for x in sh[0] if x]): rec(tag)['bs']['shares'] = num([x for x in sh[0] if x][k]) / 1e6
    close(bs_cols, 'bs', u)
    j = find(L, r'^(CONDENSED )?CONSOLIDATED STATEMENTS OF CASH FLOWS', start=i)
    rows = block(L, j, r'^End of period cash', 160)
    apply(rows, CF_MAP, cf_cols, 'cf', u)
    close(cf_cols, 'cf', u)

def F(pat):
    g = sorted(glob.glob(os.path.join(T, pat)))
    assert len(g) == 1, (pat, g)
    return g[0]

DOCS = [
    ('s1.txt', 2, ['S23', 'P23', '2022', '2021'], ['2023', '2022'], ['S23', 'P23', '2022', '2021']),
    ('s1.txt', 1, ['Q1-24', 'Q1-23'], ['Q1-24', None], ['Q1-24', 'Q1-23']),
    ('2024-08-13_10-Q*', 1, ['Q2-24', 'S23a', 'P23b', 'H1-24', None, None], ['Q2-24', None], ['H1-24', 'S23a', None]),
    ('2024-11-14_10-Q*', 1, ['Q3-24', 'Q3-23', '9M-24', 'S23c', None], ['Q3-24', None], ['9M-24', 'S23c', None]),
    ('2025-02-28_10-K*', 1, ['2024', None, None, None], ['2024', None], ['2024', None, None, None]),
    ('2025-05-08_10-Q*', 1, ['Q1-25', None], ['Q1-25', None], ['Q1-25', None]),
    ('2025-08-07_10-Q*', 1, ['Q2-25', None, 'H1-25', None], ['Q2-25', None], ['H1-25', None]),
    ('2025-11-05_10-Q*', 1, ['Q3-25', None, '9M-25', None], ['Q3-25', None], ['9M-25', None]),
    ('2026-02-26_10-K*', 1, ['2025', None, None, None], ['2025', None], ['2025', None, None, None]),
    ('2026-05-05_10-Q*', 1, ['Q1-26', None], ['Q1-26', None], ['Q1-26', None]),
    ('2026-08-05_10-Q*', 1, ['Q2-26', None, 'H1-26', None], ['Q2-26', None], ['H1-26', None]),
    ('2026-11-03_10-Q*', 1, ['Q3-26', None, '9M-26', None], ['Q3-26', None], ['9M-26', None]),
]
for pat, n, a, b, c in DOCS:
    statements(os.path.join(T, pat) if pat == 's1.txt' else F(pat), n, a, b, c)

# ---------------------------------------------------------------- non-GAAP reconciliations (net income -> Adjusted EBITDA -> Adjusted FCF)
NG_CAT = [(r'^Net Income \(Loss\)', 'ni'), (r'^Interest expense and other finance charges', 'int'), (r'^Income tax \(benefit\) expense', 'tax'),
          (r'^Depreciation, amortization and accretion', 'dda'), (r'^Nuclear fuel amortization', 'nfa'),
          (r'^Unrealized \(gain\) loss on commodity derivative', 'MTM'), (r'^Nuclear decommissioning trust funds \(gain\) loss', 'NDT'),
          (r'^Stock-based|^Long-term incentive compensation', 'SBC'), (r'^\(Gain\) loss on (non-core )?asset sales', 'GAIN'),
          (r'^Non-cash impairments|^Non-cash inventory|^Environmental and ARO', 'IMPAIR'),
          (r'^Reorganization|^Hedge termination|^Operational and other restructuring|^Liability management|^Consolidation of subsidiary', 'RESTR'),
          (r'^Acquisition and divestiture', 'ACQ'),
          (r'^Legal settlements|^Unusual market events|^Net periodic defined benefit|^Development expenses|^Cumulus Digital|^Noncontrolling interest|^Other$', 'OTHER'),
          (r'^Total Adjusted EBITDA', 'adj_ebitda'), (r'^Capital expenditures, net', 'f_capex'), (r'^Interest and finance charge payments', 'f_int'),
          (r'^(Tax payments|Income taxes)', 'f_tax'), (r'^Pension contributions', 'f_pension'), (r'^Total Adjusted Free Cash Flow', 'adj_fcf')]
CATS = ['MTM', 'NDT', 'SBC', 'GAIN', 'IMPAIR', 'RESTR', 'ACQ', 'OTHER']
def recon(path, cols, start_pat=r'^Net Income \(Loss\) \| ', nth=1, s1=False):
    L = open(path).read().split('\n'); u = url_of(path) if not s1 else 'https://www.sec.gov/Archives/edgar/data/1622536/000162828024029107/talen-sx1.htm'
    i0 = find(L, r'Adjusted EBITDA( / Adjusted Free Cash Flow)? Reconciliation|reconciliation of the GAAP financial measure of .Net Income \(Loss\). presented') if not s1 else 341
    i = find(L, start_pat, start=i0, nth=nth)
    rows = block(L, i, r'^Total Adjusted Free Cash Flow|^Total Adjusted EBITDA \|' if s1 else r'^Total Adjusted Free Cash Flow')
    for j, tag in enumerate(cols):
        if tag is None or (tag, 'ng') in DONE: continue
        d = rec(tag)['ng']; labs = {}
        for label, vals in rows:
            if j >= len(vals) or vals[j] is None: continue
            for pat, key in NG_CAT:
                if re.search(pat, label):
                    d[key] = round(d.get(key, 0.0) + vals[j], 6) if key in CATS else vals[j]
                    if key in CATS and abs(vals[j]) > 1e-9: labs.setdefault(key, []).append(f'{label} {vals[j]:,.0f}')
                    break
            else: raise SystemExit(f'unmapped non-GAAP label {label!r} in {path}')
        for k, v in labs.items(): d[k + '_lab'] = '; '.join(v)
    close(cols, 'ng', u)
REL = [('s1.txt', ['Q1-24', 'Q1-23', 'S23', 'P23', '2022', '2021']),
       ('2024-08-13_8-K*earn*', ['Q2-24', 'S23a', 'P23b', 'H1-24', None, None]),
       ('2024-11-14_8-K*earn*', ['Q3-24', 'Q3-23', '9M-24', 'S23c', None]),
       ('2025-02-27_8-K*earn*', ['2024', 'S23x', 'P23x']),
       ('2025-05-08_8-K*earn*', ['Q1-25', None]), ('2025-08-07_8-K*earn*', ['Q2-25', None, 'H1-25', None]),
       ('2025-11-05_8-K*earn*', ['Q3-25', None, '9M-25', None]), ('2026-02-26_8-K*earn*', ['Q4-25', 'Q4-24', '2025', None]),
       ('2026-05-05_8-K*earn*', ['Q1-26', None]), ('2026-08-05_8-K*earn*', ['Q2-26', None, 'H1-26', None]),
       ('2026-11-03_8-K*earn*', ['Q3-26', None, '9M-26', None])]
for pat, cols in REL:
    recon(os.path.join(T, pat) if pat == 's1.txt' else F(pat), cols, s1=(pat == 's1.txt'))

# ---------------------------------------------------------------- operating statistics (release summary table)
OPS = [('2024-08-13_8-K*earn*', ['Q2-24', 'H1-24']), ('2024-11-14_8-K*earn*', ['Q3-24', 'Q3-23', '9M-24']), ('2025-02-27_8-K*earn*', ['2024', '2023']),
       ('2025-05-08_8-K*earn*', ['Q1-25', 'Q1-24']), ('2025-08-07_8-K*earn*', ['Q2-25', None, 'H1-25', None]), ('2025-11-05_8-K*earn*', ['Q3-25', None, '9M-25', None]),
       ('2026-02-26_8-K*earn*', ['Q4-25', 'Q4-24', '2025', None]), ('2026-05-05_8-K*earn*', ['Q1-26', None]),
       ('2026-08-05_8-K*earn*', ['Q2-26', 'Q2-25', 'H1-26', 'H1-25']), ('2026-11-03_8-K*earn*', ['Q3-26', 'Q3-25', '9M-26', '9M-25'])]
for pat, cols in OPS:
    p = F(pat); L = open(p).read().split('\n'); u = url_of(p)
    for ln in L:
        c = [x.strip() for x in ln.split(' | ')]
        key = 'gen_twh' if c[0].startswith('Total Generation') else 'carbon_free' if c[0].startswith('Carbon-Free Generation') else 'cap_factor' if c[0].startswith('Capacity Factor') else None
        if not key or len(c) < 2: continue
        for j, tag in enumerate(cols):
            if tag is None or j + 1 >= len(c): continue
            v = num(c[j + 1].replace('TWh', ''))
            if v is None: continue
            if key != 'gen_twh': v = v / 100
            if key not in rec(tag)['ops']: rec(tag)['ops'][key] = v; src(tag, 'ops', u)

# ---------------------------------------------------------------- segments (10-K / 10-Q segment note: reconciliation of segment Adjusted EBITDA)
SEG = [('2025-02-28_10-K*', ['2024', 'S23', 'P23', '2022']), ('2025-05-08_10-Q*', ['Q1-25', 'Q1-24']), ('2025-08-07_10-Q*', ['Q2-25', 'Q2-24', 'H1-25', 'H1-24']),
       ('2025-11-05_10-Q*', ['Q3-25', 'Q3-24', '9M-25', '9M-24']), ('2026-02-26_10-K*', ['2025', None, None, None]), ('2026-05-05_10-Q*', ['Q1-26', None]),
       ('2026-08-05_10-Q*', ['Q2-26', None, 'H1-26', None]), ('2026-11-03_10-Q*', ['Q3-26', None, '9M-26', None])]
SEG_MAP = [(r'^(PJM Segment Adjusted EBITDA|PJM$|Total Segment Adjusted EBITDA)', 'pjm'), (r'^.Other. operating segment|^Other operating segment', 'other'),
           (r'^Corporate and Eliminations', 'corp'), (r'^Other items', 'other_items'), (r'^Noncontrolling interest', 'nci')]
for pat, cols in SEG:
    p = F(pat); L = open(p).read().split('\n'); u = url_of(p)
    i = find(L, r'^Reconciliation of [Ss]egment Adjusted EBITDA')
    rows = block(L, i, r'^(Income \(Loss\) Before Income Taxes|Net Income \(Loss\)) \|', 60)
    for label, vals in rows:
        for rx, key in SEG_MAP:
            if re.search(rx, label):
                for j, tag in enumerate(cols):
                    if tag and j < len(vals) and vals[j] is not None and key not in rec(tag)['seg']:
                        rec(tag)['seg'][key] = vals[j]; src(tag, 'seg', u)
                break

os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
for tag, r in sorted(REC.items()):
    json.dump(r, open(os.path.join(HERE, 'data', tag + '.json'), 'w'), indent=1, ensure_ascii=False)
print(len(REC), 'records:', ' '.join(sorted(REC)))
