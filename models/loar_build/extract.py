"""Extract Loar Holdings (LOAR) historical data from SEC EDGAR documents into data/<period>.json.

Sources (text form, produced by h2t.py from the EDGAR HTML downloaded by fetch.py into $LOAR_SRC/txt):
  - IPO prospectus (424B4, 26-Apr-2024): FY2012-2021 net income -> Adjusted EBITDA bridge, FY2022-23 audited statements,
    Q1/22-Q4/23 quarterly results and quarterly Adjusted EBITDA bridge, FY2022-23 end-market sales.
  - Earnings releases (8-K Item 2.02, Ex. 99.1) Q1-24 .. Q2-26: Table 1 balance sheet, 2 income statement, 3 cash flow (YTD),
    4 net income -> EBITDA -> Adjusted EBITDA, 5 sales by end market, 6 EPS -> Adjusted EPS; organic sales narrative.
Priority: the release in which a period is first reported as the current period ("as originally reported"); comparatives
only fill periods never reported as current (2023 quarters / pre-IPO).
"""
import json, os, re, glob
from parse_release import parse_tables, organic, pnum

SRC = os.environ.get('LOAR_SRC', '/tmp/loar_src')
TXT = os.path.join(SRC, 'txt')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
EDGAR = 'https://www.sec.gov/Archives/edgar/data/2000178/'

def k1000(v): return None if v is None else round(v / 1000.0, 4)

# ---------------------------------------------------------------- release registry
# cols: IS / Table 4 column -> period ; cf: CF column -> (period, ytd months) ; bs: BS column -> period
# t6: Table 6 column -> period ; em: end-market (block keyword or list column) -> period ; org: organic sentences -> periods
REL = [
    ('2024-05-14', 'd759018dex991', 'Q1-24', dict(cols=['Q1-24', 'Q1-23'], cf=[('Q1-24', 3), ('Q1-23', 3)], bs=['Q1-24', '2023'],
                                                  t6=[], em={}, org=['Q1-24'])),
    ('2024-08-13', 'ck0002000178-ex99_1', 'Q2-24', dict(cols=['Q2-24', 'Q2-23', 'H1-24', 'H1-23'], cf=[('Q2-24', 6), ('Q2-23', 6)], bs=['Q2-24', '2023'],
                                                  t6=['Q2-24', 'H1-24'], em={'Three': ('Q2-24', 'Q2-23'), 'Six': ('H1-24', 'H1-23')}, org=['Q2-24', 'H1-24'])),
    ('2024-11-13', 'ck0002000178-ex99_1', 'Q3-24', dict(cols=['Q3-24', 'Q3-23', '9M-24', '9M-23'], cf=[('Q3-24', 9), ('Q3-23', 9)], bs=['Q3-24', '2023'],
                                                  t6=['Q3-24', '9M-24'], em={'Three': ('Q3-24', 'Q3-23'), 'Nine': ('9M-24', '9M-23')}, org=['Q3-24', '9M-24'])),
    ('2025-03-31', 'ck0002000178-ex99_1', 'Q4-24', dict(cols=['Q4-24', 'Q4-23', '2024', '2023'], cf=[('2024', 12), ('2023', 12)], bs=['2024', '2023'],
                                                  t6=['Q4-24', '2024'], em={'Year': ('2024', '2023'), 'Three': ('Q4-24', 'Q4-23')}, org=['Q4-24', '2024'])),
    ('2025-05-13', 'ck0002000178-ex99_1', 'Q1-25', dict(cols=['Q1-25', 'Q1-24'], cf=[('Q1-25', 3), ('Q1-24', 3)], bs=['Q1-25', '2024'],
                                                  t6=['Q1-25'], em={'Three': ('Q1-25', 'Q1-24')}, org=['Q1-25'])),
    ('2025-08-13', 'ck0002000178-ex99_1', 'Q2-25', dict(cols=['Q2-25', 'Q2-24', 'H1-25', 'H1-24'], cf=[('Q2-25', 6), ('Q2-24', 6)], bs=['Q2-25', '2024'],
                                                  t6=['Q2-25', 'Q2-24', 'H1-25', 'H1-24'], em={'Three': ('Q2-25', 'Q2-24'), 'Six': ('H1-25', 'H1-24')}, org=['Q2-25', 'H1-25'])),
    ('2025-11-12', 'ck0002000178-ex99_1', 'Q3-25', dict(cols=['Q3-25', 'Q3-24', '9M-25', '9M-24'], cf=[('Q3-25', 9), ('Q3-24', 9)], bs=['Q3-25', '2024'],
                                                  t6=['Q3-25', 'Q3-24', '9M-25', '9M-24'], em={'Three': ('Q3-25', 'Q3-24'), 'Nine': ('9M-25', '9M-24')}, org=['Q3-25', '9M-25'])),
    ('2026-02-26', 'ck0002000178-ex99_1', 'Q4-25', dict(cols=['Q4-25', 'Q4-24', '2025', '2024'], cf=[('2025', 12), ('2024', 12)], bs=['2025', '2024'],
                                                  t6=['Q4-25', 'Q4-24', '2025', '2024'], em=['Q4-25', 'Q4-24', '2025', '2024'], org=['Q4-25', '2025'])),
    ('2026-05-07', 'ck0002000178-ex99_1', 'Q1-26', dict(cols=['Q1-26', 'Q1-25'], cf=[('Q1-26', 3), ('Q1-25', 3)], bs=['Q1-26', '2025'],
                                                  t6=['Q1-26', 'Q1-25'], em=['Q1-26', 'Q1-25'], org=['Q1-26'])),
    ('2026-08-06', 'ck0002000178-ex99_1', 'Q2-26', dict(cols=['Q2-26', 'Q2-25', 'H1-26', 'H1-25'], cf=[('Q2-26', 6), ('Q2-25', 6)], bs=['Q2-26', '2025'],
                                                  t6=['Q2-26', 'Q2-25', 'H1-26', 'H1-25'], em=['Q2-26', 'Q2-25', 'H1-26', 'H1-25'], org=['Q2-26', 'H1-26'])),
]
PROSPECTUS = '2024-04-26_424B4_0001193125-24-118106_d551112d424b4'

def find_txt(tag, date='*'):
    m = sorted(glob.glob(os.path.join(TXT, f'{date}_*{tag}.txt')))
    assert len(m) == 1, (tag, date, m)
    return m[0]

def url_of(path):
    b = os.path.basename(path)[:-4]
    parts = b.split('_')
    acc = parts[2]; doc = '_'.join(parts[3:]) + '.htm'
    return EDGAR + acc.replace('-', '') + '/' + doc

# ---------------------------------------------------------------- store
P = {}       # period -> dict
SRCS = {}    # period -> {section: url}
OWN = {}     # (period, section) -> source that first populated it; later documents never merge into it
def put(per, sec, key, val, src, override=False):
    if val is None: return
    if OWN.setdefault((per, sec), src) != src and not override: return
    d = P.setdefault(per, {}).setdefault(sec, {})
    if key in d and not override: return
    d[key] = val
    SRCS.setdefault(per, {}).setdefault(sec, src)

def row(rows, pats, block=None, excl=None):
    for p in pats:
        for lab, vals, blk in rows:
            if block and block.lower() not in blk.lower(): continue
            if re.search(p, lab, re.I) and not (excl and re.search(excl, lab, re.I)):
                return vals
    return None

# ---------------------------------------------------------------- mappings
IS_MAP = [('net_sales', [r'^Net sales']), ('cogs', [r'^Cost of sales']), ('gp', [r'^Gross profit']), ('sga', [r'^Selling, general']),
          ('trans', [r'^Transaction expenses']), ('op_income', [r'^Operating income']), ('interest', [r'^Interest expense, net']),
          ('refi', [r'^Refinancing costs']), ('ebt', [r'before income taxes']), ('ni', [r'^Net income', r'^Net loss', r'^Net \(loss\) income'])]
T4_MAP = [('interest', [r'^Interest expense']), ('refi', [r'^Refinancing']), ('op_income', [r'^Operating income']), ('dep', [r'^Depreciation']),
          ('amort', [r'^Amortization']), ('ebitda', [r'^EBITDA']), ('inv_stepup', [r'inventory step-up']),
          ('other_adj', [r'^Other ']), ('trans', [r'^Transaction expenses']), ('sbc', [r'^Stock-based']),
          ('integ', [r'integration costs']), ('covid', [r'COVID']), ('adj_ebitda', [r'^Adjusted EBITDA$', r'^Adjusted EBITDA \(?1?\)?$'])]
CF_MAP = [('ni', [r'^Net income', r'^Net loss']), ('dep', [r'^Depreciation']), ('amort', [r'^Amortization of intangible']),
          ('dcost', [r'^Amortization of debt issuance']), ('stepup', [r'inventory step-up']), ('sbc', [r'^Stock-based']),
          ('deferred_tax', [r'^Deferred income taxes']), ('lease', [r'^Non-cash lease']), ('contingent', [r'^Adjustment to contingent']),
          ('refi', [r'^Refinancing costs']), ('otherinc', [r'^Other income']),
          ('cfo', [r'^Net cash provided by.*operating', r'^Net cash \(used in\).*operating', r'^Net cash provided by \(used in\) operating']),
          ('capex', [r'^Capital expenditures']), ('acquisitions', [r'^Payments? for acquisitions']),
          ('proceeds_fa', [r'^Proceeds from sale of fixed']), ('ppa_adj', [r'^Proceeds from acquisition purchase price']),
          ('cfi', [r'^Net cash used in investing', r'^Net cash provided by.*investing']),
          ('equity', [r'^Net proceeds from issuance of common stock']), ('options', [r'^Proceeds from exercise']),
          ('debt_in', [r'^Proceeds from issuance of long-term debt']), ('debt_out', [r'^Payments of long-term debt']),
          ('finlease', [r'^Payments of finance lease']), ('fincost', [r'^Financing costs', r'^Debt issuance costs']),
          ('defpurch', [r'^Payment of deferred purchase']),
          ('cff', [r'^Net cash .*financing']), ('fx', [r'^Effect of translation']),
          ('net_change', [r'^Net (increase|decrease)']), ('cash_begin', [r'beginning of period']), ('cash_end', [r'end of period']),
          ('int_paid', [r'^Interest paid']), ('tax_paid', [r'^Income taxes paid'])]
BS_MAP = [('cash', [r'^Cash and cash equivalents']), ('ar', [r'^Accounts receivable']), ('inv', [r'^Inventories']),
          ('oca1', [r'^Other current assets']), ('taxrec', [r'^Income taxes receivable']), ('tca', [r'^Total current assets']),
          ('ppe', [r'^Property, plant']), ('finla', [r'^Finance lease assets']), ('opla', [r'^Operating lease assets']),
          ('olta', [r'^Other long-term assets']), ('intang', [r'^Intangible assets']), ('gw', [r'^Goodwill']), ('ta', [r'^Total assets']),
          ('ap', [r'^Accounts payable']), ('cdebt', [r'^Current portion of long-term debt']), ('cfl', [r'^Current portion of finance']),
          ('col', [r'^Current portion of operating']), ('taxpay', [r'^Income taxes payable']), ('accrued', [r'^Accrued expenses']),
          ('tcl', [r'^Total current liabilities']), ('dtl', [r'^Deferred income taxes']), ('ltd', [r'^Long-term debt']),
          ('fl', [r'^Finance lease liabilities']), ('ol', [r'^Operating lease liabilities']), ('env', [r'^Environmental']),
          ('oltl', [r'^Other long-term liabilities']), ('common', [r'^Common stock']), ('apic', [r'^Additional paid-in']),
          ('re', [r'^Retained earnings', r'^Accumulated deficit']), ('aoci', [r'^Accumulated other comprehensive']),
          ('member', [r'^Member.s equity$']),
          ('teq', [r"^Total stockholders. equity", r'^Total equity', r'^Member.s equity$']), ('tle', [r'^Total liabilities and'])]
EM = [('com', r'^Commercial Aerospace$'), ('bj', r'^Business Jet (and|&) General Aviation$'), ('def', r'^Defense$'), ('oth', r'^(Other|Non-Aerospace)$')]
EM_LIST = [('com_oem', r'^Commercial aerospace OEM'), ('com_am', r'^Commercial aerospace aftermarket'), ('bj_oem', r'^Business jet & general aviation OEM'),
           ('bj_am', r'^Business jet & general aviation aftermarket'), ('def_oem', r'^Total defense OEM'), ('def_am', r'^Total defense aftermarket'),
           ('oth_oem', r'^Total other OEM'), ('oth_am', r'^Total other aftermarket'), ('total', r'^Net Sales$')]

def shares_from_label(rows):
    for lab, _, _ in rows:
        m = re.search(r'authorized;\s*([\d,]+)\s+and\s+([\d,]+)', lab)
        if m: return float(m.group(1).replace(',', '')) / 1e6, float(m.group(2).replace(',', '')) / 1e6
    return None

# ---------------------------------------------------------------- releases
def do_release(date, tag, cur, meta):
    path = find_txt(tag, date); txt = open(path).read().replace('\xa0', ' '); src = url_of(path)
    T = parse_tables(txt)
    # income statement
    t2 = T[2]['rows']
    for key, pats in IS_MAP:
        v = row(t2, pats, excl=r'per common|margin')
        if v:
            for i, per in enumerate(meta['cols']):
                if i < len(v): put(per, 'is', key, k1000(v[i]), src)
    for i, per in enumerate(meta['cols']):
        d = P.get(per, {}).get('is', {})
        if 'op_income' in d and 'gp' in d:
            put(per, 'is', 'other_inc', round(d['op_income'] - d['gp'] + d['sga'] + d['trans'], 4), src)
        if 'ebt' in d and 'ni' in d:
            put(per, 'is', 'tax', round(d['ebt'] - d['ni'], 4), src)
    b = row(t2, [r'^Basic$']); dl = row(t2, [r'^Diluted$'])
    for i, per in enumerate(meta['cols']):
        if b and i < len(b): put(per, 'is', 'eps_basic', b[i], src)
        if dl and i < len(dl): put(per, 'is', 'eps_dil', dl[i], src)
    # EBITDA bridge
    t4 = T[4]['rows']
    for key, pats in T4_MAP:
        v = row(t4, pats, excl=r'margin')
        if v:
            for i, per in enumerate(meta['cols']):
                if i < len(v): put(per, 'ng', key, k1000(v[i]), src)
    # cash flow (YTD)
    t3 = T[3]['rows']
    for key, pats in CF_MAP:
        v = row(t3, pats)
        if v:
            for i, (per, ytd) in enumerate(meta['cf']):
                put(per, 'cf', key, k1000(v[i]), src)
    for per, ytd in meta['cf']:
        put(per, 'cf', 'ytd_months', ytd, src)
    # balance sheet
    t1 = T[1]['rows']
    for key, pats in BS_MAP:
        v = row(t1, pats)
        if v:
            for i, per in enumerate(meta['bs']):
                put(per, 'bs', key, k1000(v[i]), src)
    sh = shares_from_label(t1)
    if sh:
        for i, per in enumerate(meta['bs']): put(per, 'bs', 'shares_out', sh[i], src)
    # end markets
    if 5 in T:
        t5 = T[5]['rows']
        if isinstance(meta['em'], dict):
            for kw, (pc, pp) in meta['em'].items():
                for k, pat in EM:
                    v = row(t5, [pat], block=kw)
                    if v:
                        put(pc, 'em', k + '_oem', k1000(v[0]), src); put(pc, 'em', k + '_am', k1000(v[1]), src)
                        put(pp, 'em', k + '_oem', k1000(v[3]), src); put(pp, 'em', k + '_am', k1000(v[4]), src)
                v = row(t5, [r'^Total$'], block=kw)
                if v: put(pc, 'em', 'total', k1000(v[2]), src); put(pp, 'em', 'total', k1000(v[5]), src)
                lab = [l for l, _, bl in t5 if kw.lower() in bl.lower() and re.match(r'^(Other|Non-Aerospace)$', l)]
                if lab: put(pc, 'em', 'oth_label', lab[0], src)
        else:
            for k, pat in EM_LIST:
                v = row(t5, [pat])
                if v:
                    for i, per in enumerate(meta['em']): put(per, 'em', k, k1000(v[i]), src)
    # EPS bridge
    if 6 in T and meta['t6']:
        t6 = T[6]['rows']
        new = any(re.search(r'Amortization of acquired intangible', l) for l, _, _ in t6)
        sec = 'eps_new' if new else 'eps_old'
        def first_block(pats):
            return row(t6, pats)
        items = [('ni', [r'^Net income$']), ('sh_basic', [r'outstanding.*basic']), ('sh_dil', [r'outstanding.*diluted']),
                 ('eps_basic', [r'^(Net income per common shares?|Earnings per share)\W*basic$']), ('eps_dil_pub', [r'(per common shares?|Earnings per share)\W*diluted$']),
                 ('refi', [r'^Refinancing costs']), ('gross_adj', [r'^Gross adjustments to EBITDA']),
                 ('amort', [r'^Amortization of acquired']), ('tax_adj', [r'^Tax adjustment']),
                 ('adj_ni', [r'^Adjusted net income']), ('adj_eps', [r'^Adjusted (diluted )?earnings per share'])]
        for key, pats in items:
            v = first_block(pats)
            if v is None: continue
            for i, per in enumerate(meta['t6']):
                if i >= len(v): continue
                val = v[i]
                if key in ('ni', 'refi', 'gross_adj', 'amort', 'tax_adj', 'adj_ni'): val = k1000(val)
                elif key in ('sh_basic', 'sh_dil'): val = round(val / 1000.0, 3)
                put(per, sec, key, val, src)
        # per-share bridge lines (second block of refinancing / tax rows): keep raw rows as text for comments
        for i, per in enumerate(meta['t6']):
            lines = []
            on = False
            for lab, vals, _ in t6:
                if re.search(r'diluted$', lab) and re.search(r'per common|per share', lab, re.I) and on is False and lines == [] and any(re.search(r'Adjusted', l) for l, _, _ in t6):
                    pass
                if re.search(r'^Adjustments to diluted', lab): on = True
            put(per, sec, 'definition', 'current (adds back amortization of acquired intangibles, tax-effected)' if new else
                'prior (EBITDA adjustments + refinancing costs, tax-effected; amortization not added back)', src)
        if 'eps_new' == sec:
            for i, per in enumerate(meta['t6']): pass
    # organic
    orgs = organic(txt)
    for per, o in zip(meta['org'], orgs):
        put(per, 'org', 'growth', o[0], src); put(per, 'org', 'incr', o[1], src); put(per, 'org', 'organic_sales', o[2], src)

# ---------------------------------------------------------------- prospectus
def lines_after(lines, anchor, start=0, exact=False):
    for i in range(start, len(lines)):
        if (lines[i].strip() == anchor) if exact else (anchor in lines[i]): return i
    raise KeyError(anchor)

def rows_between(lines, i0, stop_pat, n=None):
    out = []
    for ln in lines[i0:]:
        if re.search(stop_pat, ln): break
        if '|' not in ln: continue
        cells = [c.strip() for c in ln.split('|')]
        vals = [pnum(c) for c in cells[1:]]
        if not vals or any(v is None for v in vals): continue
        if n and len(vals) != n: continue
        out.append((cells[0], vals, ''))
    return out

def do_prospectus():
    path = find_txt('d551112d424b4', '2024-04-26'); L = open(path).read().replace('\xa0', ' ').splitlines(); src = url_of(path)
    # annual bridge FY2012-2021 (12 columns; TTM-2017 combined column used for 2017)
    i = lines_after(L, 'for the time periods indicated')
    R = rows_between(L, i, r'^\(1\) \|', n=12)
    cols = ['2021', '2020', '2019', '2018', '2017', '2017S', '2017P', '2016', '2015', '2014', '2013', '2012']
    amap = [('ni', [r'^Net \(loss\) income']), ('tax', [r'^Income tax']), ('interest', [r'^Interest expense']), ('loss_ext', [r'^Loss on extinguishment']),
            ('fx_gain', [r'^Foreign exchange']), ('ins_gain', [r'^Gain on insurance']), ('op_income', [r'^Operating income']),
            ('dep', [r'^Depreciation']), ('amort', [r'^Amortization']), ('ebitda', [r'^EBITDA']), ('inv_stepup', [r'inventory step-up']),
            ('other_adj', [r'^Other \(income\) loss']), ('trans', [r'^Transaction expenses']), ('sbc', [r'^Stock-based']),
            ('integ', [r'integration costs']), ('covid', [r'^COVID']), ('msa', [r'^Management service']), ('adj_ebitda', [r'^Adjusted EBITDA$']),
            ('net_sales', [r'^Net sales'])]
    for key, pats in amap:
        v = row(R, pats)
        for j, per in enumerate(cols):
            if per in ('2017S', '2017P'): continue
            sec = 'is' if key in ('ni', 'tax', 'interest', 'op_income', 'net_sales') else 'ng'
            put(per, sec, key, k1000(v[j]) if v else None, src)
            if key in ('dep', 'amort', 'interest', 'op_income'): put(per, 'ng', key, k1000(v[j]), src)
    # quarterly results Q1/22-Q4/23 (8 columns, newest first)
    qcols = ['Q4-23', 'Q3-23', 'Q2-23', 'Q1-23', 'Q4-22', 'Q3-22', 'Q2-22', 'Q1-22']
    i = lines_after(L, 'Quarterly Results of Operations and Other Financial Data')
    R = rows_between(L, i, r'^Non-GAAP', n=8)
    qmap = [('net_sales', [r'^Net sales']), ('cogs', [r'^Cost of sales']), ('gp', [r'^Gross profit']), ('sga', [r'^Selling']),
            ('trans', [r'^Transaction expenses']), ('other_inc', [r'^Other income']), ('op_income', [r'^Operating income']),
            ('interest', [r'^Interest expense']), ('ebt', [r'before income taxes']), ('ni', [r'^Net \(loss\) income$'])]
    for key, pats in qmap:
        v = row(R, pats)
        for j, per in enumerate(qcols): put(per, 'is', key, k1000(v[j]), src)
    v = row(R, [r'^Income tax'])
    for j, per in enumerate(qcols): put(per, 'is', 'tax', -k1000(v[j]), src)
    for key, pats in [('cfo', [r'^Operating activities']), ('cfi', [r'^Investing activities']), ('cff', [r'^Financing activities']),
                      ('dep', [r'^Depreciation']), ('amort', [r'^Amortization of intangible']), ('capex', [r'^Capital expenditures']),
                      ('acquisitions', [r'^Payment for acquisitions'])]:
        v = row(R, pats)
        for j, per in enumerate(qcols):
            if per.endswith('22'): put(per, 'cfd', key, k1000(v[j]), src)   # discrete quarter (2022 only; 2023 from release YTD)
    i = lines_after(L, 'Margin for each of the quarters indicated', i)
    R = rows_between(L, i, r'^\(1\) \|', n=8)
    for key, pats in [('interest', [r'^Interest expense']), ('op_income', [r'^Operating income']), ('dep', [r'^Depreciation']),
                      ('amort', [r'^Amortization']), ('ebitda', [r'^EBITDA']), ('inv_stepup', [r'inventory step-up']),
                      ('other_adj', [r'^Other income']), ('trans', [r'^Transaction expenses']), ('sbc', [r'^Stock-based']),
                      ('integ', [r'^Acquisition integration', r'^costs \(5\)']), ('covid', [r'^COVID']), ('adj_ebitda', [r'^Adjusted EBITDA$'])]:
        v = row(R, pats)
        for j, per in enumerate(qcols): put(per, 'ng', key, k1000(v[j]) if v else None, src)
    # FY2022-23 statements and bridge
    i = lines_after(L, 'Consolidated Balance Sheets', exact=True)
    R = rows_between(L, i, r'accompanying notes', n=2)
    for key, pats in BS_MAP:
        v = row(R, pats)
        if v:
            put('2023', 'bs', key, k1000(v[0]), src); put('2022', 'bs', key, k1000(v[1]), src)
    i = lines_after(L, 'Consolidated Statements of Operations', i, exact=True)
    R = rows_between(L, i, r'accompanying notes', n=2)
    for key, pats in IS_MAP + [('other_inc', [r'^Other income'])]:
        v = row(R, pats, excl=r'per common')
        if v: put('2023', 'is', key, k1000(v[0]), src); put('2022', 'is', key, k1000(v[1]), src)
    v = row(R, [r'^Income tax'])
    put('2023', 'is', 'tax', -k1000(v[0]), src); put('2022', 'is', 'tax', -k1000(v[1]), src)
    i = lines_after(L, 'Consolidated Statements of Cash Flows', i, exact=True)
    R = rows_between(L, i, r'accompanying notes', n=2)
    for key, pats in CF_MAP:
        v = row(R, pats)
        if v: put('2023', 'cf', key, k1000(v[0]), src); put('2022', 'cf', key, k1000(v[1]), src)
    put('2023', 'cf', 'ytd_months', 12, src); put('2022', 'cf', 'ytd_months', 12, src)
    i = lines_after(L, 'follows (in thousands except percentages):')
    R = rows_between(L, i, r'^\(1\) \|', n=2)
    for key, pats in T4_MAP:
        v = row(R, pats, excl=r'margin')
        if v: put('2023', 'ng', key, k1000(v[0]), src); put('2022', 'ng', key, k1000(v[1]), src)
    # end markets FY2022-23
    i = lines_after(L, 'Net sales by end market were as follows')
    R = rows_between(L, i, r'^F-\d', n=6)
    for k, pat in EM:
        v = row(R, [pat])
        put('2023', 'em', k + '_oem', k1000(v[0]), src); put('2023', 'em', k + '_am', k1000(v[1]), src)
        put('2022', 'em', k + '_oem', k1000(v[3]), src); put('2022', 'em', k + '_am', k1000(v[4]), src)
    v = row(R, [r'^Total$']); put('2023', 'em', 'total', k1000(v[2]), src); put('2022', 'em', 'total', k1000(v[5]), src)
    # organic FY2023 (MD&A)
    t = re.sub(r'\s+', ' ', '\n'.join(L))
    m = re.search(r'Net organic sales for the year ended December 31, 2023 increased \$([\d.]+) million, or ([\d.]+)%, to \$([\d.]+) million', t)
    if m:
        put('2023', 'org', 'incr', float(m.group(1)), src); put('2023', 'org', 'growth', float(m.group(2)) / 100, src)
        put('2023', 'org', 'organic_sales', float(m.group(3)), src)

def main():
    do_prospectus()            # earliest document: 2022-23 as first published
    for date, tag, cur, meta in REL:
        do_release(date, tag, cur, meta)
    # Q1-24 organic (sentence split by footnote marker in the HTML)
    put('Q1-24', 'org', 'growth', 0.111, 'Q1-24 release'); put('Q1-24', 'org', 'incr', 8.3, 'Q1-24 release'); put('Q1-24', 'org', 'organic_sales', 82.5, 'Q1-24 release')
    os.makedirs(OUT, exist_ok=True)
    for per, d in P.items():
        d['period'] = per; d['sources'] = SRCS.get(per, {})
        json.dump(d, open(os.path.join(OUT, f'{per}.json'), 'w'), indent=1, sort_keys=True)
    print(len(P), 'periods:', sorted(P))

if __name__ == '__main__':
    main()
