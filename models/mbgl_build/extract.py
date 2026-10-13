"""Extract per-period source data for Mobility Global (data/<period>.json) from the text versions of the EDGAR documents in
$MBGL_SRC/txt (fetch.py). Every value is as published (USD millions, whole millions; per-share in USD; shares in millions);
nothing is estimated. Each record carries `sources` (URLs) and `notes`.

Documents (registrant_filingdate_form_document):
  F10   Form 10 information statement (10-12B/A Ex. 99.1, 27-May-2026): FY2023-25 audited combined statements, Q1-26 / Q1-25
        interim statements, MD&A (revenue mix, segment results) and non-GAAP reconciliations.
  DRS   First confidential draft (DRS, 23-Oct-2025, made public): the 31-Dec-2023 combined balance sheet.
  Q10   Form 10-Q for Q2-26 (7-Aug-2026): Q2 / 1H statements (prior-year Q2 / 1H comparatives), MD&A revenue mix.
  REL   Q2-26 earnings release (8-K Ex. 99.1, 7-Aug-2026): segment results, Adjusted EBITDA reconciliation, free cash flow.
  EX992 FY2025 quarterly financial data (8-K Ex. 99.2, 7-Aug-2026): Q1-Q4 2025 income statement, segment revenue, operating
        profit and Adjusted EBITDA reconciliation. The exhibit is slide images (EX992 table below transcribed from the images;
        every segment column re-adds to its published Adjusted EBITDA - checked in check_data.py). Q3 / Q4 2025 are labelled
        "unaudited and preliminary" by the company.
  SPGI  S&P Global earnings releases (8-K Ex. 99.1): Mobility segment revenue, expenses, operating profit, non-GAAP adjustments,
        deal-related amortization, adjusted operating profit and subscription / non-subscription revenue (memo series).
"""
import csv, json, os, re, glob

S = os.environ.get('MBGL_SRC', '/tmp/mbgl_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
URL = {}
for o in csv.DictReader(open(os.path.join(HERE, 'filings.csv'))):
    URL[f"{o['registrant']}_{o['filing_date']}_{o['form'].replace('/', '')}_{o['document'].rsplit('.', 1)[0]}"] = o['url']

def doc(prefix):
    fs = sorted(glob.glob(os.path.join(S, 'txt', prefix + '*.txt')))
    if not fs: raise FileNotFoundError(prefix)
    key = os.path.basename(fs[-1])[:-4]
    return key, clean(open(fs[-1], encoding='utf-8'))

def clean(lines):
    """drop zero-width / non-breaking spaces and empty table cells, so rows read 'Label | v1 | v2 | ...'"""
    out = []
    for l in lines:
        l = re.sub(r'\s+', ' ', l.replace('\u200b', '').replace('\u00a0', ' ')).strip()
        if '|' in l: l = ' | '.join(c.strip() for c in l.split('|') if c.strip())
        out.append(l)
    return out

F10 = doc('MBGL_2026-05-27_10-12BA')
DRS = doc('MBGL_2025-10-23_DRS_filename2')
Q10 = doc('MBGL_2026-08-07_10-Q')
REL = doc('MBGL_2026-08-07_8-K_mbgl-20260807xexx991')
EX992_URL = 'https://www.sec.gov/Archives/edgar/data/2090312/000209031226000013/exhibit992.htm'

def nums(line):
    """numeric cells of a ' | ' row (first cell = label): '(25 )' -> -25, '—' / '-' -> 0, '%' cells dropped"""
    out = []
    for c in line.split('|')[1:]:
        c = c.replace('$', '').replace(',', '').replace(' ', '')
        if c in ('', ')', '%'): continue
        if c.endswith('%'): continue
        if c in ('—', '-', '–'): out.append(0.0); continue
        m = re.fullmatch(r'\(?(-?\d+(?:\.\d+)?)\)?', c)
        if m: out.append(-float(m.group(1)) if c.startswith('(') else float(m.group(1)))
    return out

def find(d, pat, start=0, nth=0):
    k = -1
    for i in range(start, len(d[1])):
        if re.search(pat, d[1][i]):
            k += 1
            if k == nth: return i
    raise KeyError(f'{d[0]}: {pat} (from {start}, #{nth})')

def row(d, label, start, end=None, col=None, nth=0):
    """numbers of the first row whose label matches `label` between start and end"""
    end = end or start + 80
    k = -1
    for i in range(start, min(end, len(d[1]))):
        line = d[1][i]
        if re.match(label, line.split('|')[0].strip()) and '|' in line:
            k += 1
            if k < nth: continue
            v = nums(line)
            return v if col is None else v[col]
    raise KeyError(f'{d[0]}: row {label} after line {start}')

REC = {}
def rec(p):
    return REC.setdefault(p, {'period': p, 'sources': [], 'notes': []})
def src(p, d):
    u = URL.get(d[0]) if isinstance(d, tuple) else d
    if u and u not in rec(p)['sources']: rec(p)['sources'].append(u)

# ============================================================== income statements
def is_from(d, a, col, p, other=True, eps=False):
    r = rec(p).setdefault('is', {})
    for k, lab in (('rev', r'Revenue$'), ('opex', r'Operating ?[–-] ?related expenses'), ('sga', r'Selling and general expenses'),
                   ('dep', r'Depreciation$'), ('amort', r'Amortization of intangibles'), ('op', r'Operating profit'),
                   ('int', r'Interest expense, net'), ('ebt', r'Income before'), ('tax', r'Provision for'), ('ni', r'Net income$')):
        r[k] = row(d, lab, a, a + 40, col)
    if other:
        try: r['othinc_exp'] = row(d, r'Other income, net', a, a + 40, col)
        except KeyError: pass
    if eps:
        r['eps_basic'] = row(d, r'Basic', a, a + 40, col); r['eps_dil'] = row(d, r'Diluted', a, a + 40, col)
    src(p, d)

a = find(F10, r'^COMBINED STATEMENTS OF INCOME$')
for col, y in enumerate((2025, 2024, 2023)): is_from(F10, a, col, str(y))
a = find(F10, r'^Condensed Combined Statements of Income$')
for col, p in enumerate(('Q1-26', 'Q1-25')): is_from(F10, a, col, p, other=False)
a = find(Q10, r'^OPERATIONS$')
for col, p in ((0, 'Q2-26'), (1, 'Q2-25')): is_from(Q10, a, col, p, other=False, eps=True)
# 10-Q: shares (basic = diluted, 294,821,320: distribution share count applied to all periods presented)
for p in ('Q2-26', 'Q2-25'):
    rec(p)['is']['sh_basic'] = rec(p)['is']['sh_dil'] = 294.82132
    rec(p)['notes'].append('Weighted shares 294,821,320 basic and diluted: the 10-Q (Note 3) computes EPS for all periods presented on the shares '
                           'distributed on 1-Jul-2026 (one MBGL share per SPGI share held on 15-Jun-2026).')

# ============================================================== EX992 (FY2025 quarters; slide images, transcribed)
EX992 = {   # Q1, Q2, Q3, Q4, FY — consolidated income statement
    'rev': (420, 439, 445, 446, 1750), 'opex': (127, 132, 129, 128, 516), 'sga': (131, 134, 135, 185, 585), 'da': (78, 77, 77, 78, 310),
    'op': (84, 96, 104, 55, 339), 'int': (3, 4, 4, 2, 13), 'ebt': (81, 92, 100, 53, 326), 'tax': (23, 27, 29, 27, 106), 'ni': (58, 65, 71, 26, 220)}
EX992_SEG = {   # (CARFAX, B2B, Corporate) per quarter Q1..Q4 and FY
    'rev':   [(275, 145, 0), (289, 150, 0), (291, 154, 0), (287, 159, 0), (1142, 608, 0)],
    'sub':   [(225, 118, 0), (234, 124, 0), (235, 127, 0), (233, 130, 0), (927, 499, 0)],
    'nsub':  [(50, 27, 0), (55, 26, 0), (56, 27, 0), (54, 29, 0), (215, 109, 0)],
    'texp':  [(198, 131, 7), (200, 134, 9), (199, 131, 11), (223, 150, 18), (820, 546, 45)],
    'op':    [(77, 14, -7), (89, 16, -9), (92, 23, -11), (64, 9, -18), (322, 62, -45)],
    'da':    [(50, 28, 0), (50, 27, 0), (50, 27, 0), (48, 30, 0), (198, 112, 0)],
    'sbc':   [(3, 2, 0), (2, 2, 0), (4, 3, 0), (4, 2, 0), (13, 9, 0)],
    'trans': [(0, 0, 0), (0, 0, 2), (0, 3, 0), (0, 6, 10), (0, 9, 12)],
    'sev':   [(0, 0, 1), (1, 4, 2), (0, 6, 0), (1, 3, 2), (2, 13, 5)],
    'legal': [(0, 0, 0), (0, 0, 0), (0, -3, 0), (0, 0, 0), (0, -3, 0)],
    'other': [(0, 0, 1), (0, 0, 2), (0, -4, 1), (1, -1, 2), (1, -5, 6)],
    'adj':   [(130, 44, -5), (142, 49, -3), (146, 55, -10), (118, 49, -4), (536, 197, -22)]}
SEGS = ('cfx', 'b2b', 'corp')
for i, p in enumerate(('Q1-25', 'Q2-25', 'Q3-25', 'Q4-25', '2025')):
    r = rec(p); src(p, EX992_URL)
    x = r.setdefault('ex992', {})
    for k, v in EX992.items(): x[k] = float(v[i])
    sg = r.setdefault('seg', {})
    for k, v in EX992_SEG.items():
        for s, val in zip(SEGS, v[i]):
            if k in ('rev', 'sub', 'nsub') and s == 'corp': continue
            if p not in ('Q3-25', 'Q4-25') and k not in ('rev', 'sub', 'nsub'): continue   # filed detail wins where it exists
            sg.setdefault(s, {}).setdefault(k, float(val))
    if p in ('Q3-25', 'Q4-25'):
        r['is'] = {k: float(v[i]) for k, v in EX992.items()}
        r['notes'].append('Q3-25 / Q4-25: FY2025 quarterly financial data (8-K Ex. 99.2, 7-Aug-2026), "unaudited and preliminary", carve-out basis '
                          '(depreciation and amortization shown combined).')

# ============================================================== balance sheets
def bs_from(d, a, col, p):
    b = rec(p).setdefault('bs', {})
    L = lambda pat: row(d, pat, a, a + 60, col)
    for k, pat in (('cash', r'Cash and cash equivalents'), ('due_from_c', r'Due from related parties.{0,3}current'), ('ar', r'Accounts receivable'),
                   ('prepaid', r'Prepaid and other current assets'), ('tca', r'Total current assets'), ('ppe', r'Property and equipment, net'),
                   ('rou', r'Right of use assets'), ('gw', r'Goodwill'), ('intang', r'Other intangible assets'), ('onca', r'Other non-current assets'),
                   ('ta', r'Total assets'), ('ap', r'Accounts payable'), ('due_to_c', r'Due to related parties.{0,3}current'),
                   ('accr', r'Accrued compensation'), ('unearned', r'Unearned revenue'), ('ocl', r'Other current liabilities'),
                   ('tcl', r'Total current liabilities'), ('lease', r'(Lease|Operating lease) liabilities'), ('dtl', r'Deferred tax liability'),
                   ('due_to_nc', r'Due to related parties.{0,3}non-current'), ('oncl', r'Other non-current liabilities'), ('tl', r'Total liabilities$'),
                   ('pci', r'Parent company investment'), ('aoci', r'Accumulated other comprehensive'), ('teq', r'Total [Ee]quity'),
                   ('tle', r'Total liabilities and equity')):
        try: b[k] = L(pat)
        except KeyError: pass
    for k, pat in (('due_from_nc', r'Due from related parties.{0,3}non-current'), ('ltd', r'Long-term debt')):
        try: b[k] = L(pat)
        except KeyError: b[k] = 0.0
    src(p, d)

a = find(F10, r'^COMBINED BALANCE SHEETS$')
bs_from(F10, a, 0, '2025'); bs_from(F10, a, 1, '2024')
a = find(DRS, r'ombined Balance Sheets$', nth=0)
bs_from(DRS, a, 1, '2023')
rec('2023')['notes'].append('31-Dec-2023 balance sheet from the first Form 10 draft (DRS, 23-Oct-2025, FY2024 / FY2023 audited statements).')
a = find(F10, r'^Condensed Combined Balance Sheets$')
bs_from(F10, a, 0, 'Q1-26')
a = find(Q10, r'^CONDENSED COMBINED BALANCE SHEETS$')
bs_from(Q10, a, 0, 'Q2-26')

# ============================================================== cash flows (year to date)
def cf_from(d, a, col, p, ytd):
    c = rec(p).setdefault('cf', {'ytd_months': ytd})
    def L(pat, default=None):
        try: return row(d, pat, a, a + 60, col)
        except (KeyError, IndexError):
            if default is None: raise
            return default
    c.update(ni=L(r'Net income'), dep=L(r'Depreciation'), amort=L(r'Amortization of intangibles'), prov=L(r'Provision for losses', 0.0),
             def_tax=L(r'Deferred income taxes'), sbc=L(r'Stock-based compensation'), restr=L(r'(Restructuring and other|Other)$', 0.0),
             cfo=L(r'Cash provided by operating'), capex=L(r'Capital expenditures'), acq=L(r'Acquisitions, net', 0.0),
             eqinv=L(r'Purchases of equity investments', 0.0), loan_in=L(r'Proceeds from loan to related', 0.0), disp=L(r'Proceeds from dispositions', 0.0),
             cfi=L(r'Cash (used for|provided by) investing|Cash used for investing'), notes=L(r'Proceeds from issuance of Senior Notes', 0.0),
             transfers=L(r'Net transfers to Parent'), loan_out=L(r'Payments related to loan', 0.0), contingent=L(r'Contingent consideration', 0.0),
             cff=L(r'Cash (used for|provided by)( \(used for\))? financing'), fx=L(r'Effect of exchange rate'),
             net=L(r'Net change in cash'), cash_begin=L(r'Cash.*(beginning)'), cash_end=L(r'Cash.*(end of)'))
    src(p, d)

a = find(F10, r'^COMBINED STATEMENTS OF CASH FLOWS$')
for col, y in enumerate((2025, 2024, 2023)): cf_from(F10, a, col, str(y), 12)
a = find(F10, r'^Condensed Combined Statements of Cash Flows$')
cf_from(F10, a, 0, 'Q1-26', 3); cf_from(F10, a, 1, 'Q1-25', 3)
a = find(Q10, r'^CONDENSED COMBINED STATEMENTS OF CASH FLOWS$')
cf_from(Q10, a, 0, 'Q2-26', 6); cf_from(Q10, a, 1, 'Q2-25', 6)
for p in ('Q2-26', 'Q2-25'):
    rec(p)['notes'].append('Cash flow is six months year to date (10-Q); the discrete quarter is derived in normalize.py (Q2 = 1H − Q1).')

# ============================================================== revenue mix (MD&A)
def mix(d, a, col, p, seg=None):
    m = rec(p).setdefault('seg', {}).setdefault(seg, {}) if seg else rec(p).setdefault('mix', {})
    for k, pat in (('rev', r'Revenue$'), ('sub', r'Subscription revenue'), ('nsub', r'Non-subscription revenue'), ('us', r'U\.S\. revenue'),
                   ('intl', r'International revenue')):
        m[k] = row(d, pat, a, a + 25, col)
    src(p, d)

# Form 10: Q1 consolidated / FY consolidated / CARFAX Q1 / B2B Q1 / CARFAX FY / B2B FY (MD&A order)
a = find(F10, r'^Revenue \| 455 \| 420', find(F10, r'Three Months Ended March 31, 2026 Compared to Three Months Ended March 31, 2025'), nth=1)
mix(F10, a, 0, 'Q1-26'); mix(F10, a, 1, 'Q1-25')
a = find(F10, r'^Revenue \| 1,750 \| 1,613', a, nth=1)
for col, y in enumerate((2025, 2024, 2023)): mix(F10, a, col, str(y))
sr = find(F10, r'^Segment Results of Operations$')
a = find(F10, r'^Revenue \|', sr); mix(F10, a, 0, 'Q1-26', 'cfx'); mix(F10, a, 1, 'Q1-25', 'cfx')
a = find(F10, r'^Revenue \|', a + 1); mix(F10, a, 0, 'Q1-26', 'b2b'); mix(F10, a, 1, 'Q1-25', 'b2b')
a = find(F10, r'^Revenue \|', a + 1)
for col, y in enumerate((2025, 2024, 2023)): mix(F10, a, col, str(y), 'cfx')
a = find(F10, r'^Revenue \|', a + 1)
for col, y in enumerate((2025, 2024, 2023)): mix(F10, a, col, str(y), 'b2b')
# 10-Q: consolidated / CARFAX / B2B (three months current, prior)
a = find(Q10, r'^Revenue \| \$ 468 \| \$ 439 \| \$ 29')
a = find(Q10, r'^Revenue \|', a + 1)
mix(Q10, a, 0, 'Q2-26'); mix(Q10, a, 1, 'Q2-25')
a = find(Q10, r'^Revenue \| \$ 312 \| \$ 289 \| \$ 23'); mix(Q10, a, 0, 'Q2-26', 'cfx'); mix(Q10, a, 1, 'Q2-25', 'cfx')
a = find(Q10, r'^Revenue \| \$ 156 \| \$ 150 \| \$ 6'); mix(Q10, a, 0, 'Q2-26', 'b2b'); mix(Q10, a, 1, 'Q2-25', 'b2b')

# ============================================================== segment OP -> Adjusted OP -> Segment Adjusted EBITDA (Form 10)
ITEM_KEYS = {r'Amortization of intangibles': 'amort', r'Transaction costs': 'trans', r'Employee severance charges$': 'sev',
             r'Employee severance charges and other': 'sev_oth', r'Acquisition integration costs': 'integ',
             r'Acquisition and disposition-related costs': 'acqdisp', r'Legal settlement recovery': 'legal', r'ELT transition costs': 'elt',
             r'Other( \(\d\))?': 'other', r'Depreciation$': 'dep', r'Stock-based compensation': 'sbc', r'Adjusted operating profit': 'adjop',
             r'Segment Adjusted EBITDA|Adjusted EBITDA$': 'adj', r'Operating profit( \(GAAP\))?$': 'op'}
def seg_table(d, a, p, stop):
    sg = rec(p).setdefault('seg', {}); labels = []
    for i in range(a + 1, a + 30):
        line = d[1][i]
        if re.match(stop, line): break
        lab = line.split('|')[0].strip()
        for pat, k in ITEM_KEYS.items():
            if re.fullmatch(pat, lab):
                v = nums(line)
                if len(v) < 4: continue
                for s, val in zip(SEGS, v[:3]): sg.setdefault(s, {})[k] = val
                if k in ('adjop', 'adj', 'op'): rec(p).setdefault('ng', {})[f'{k}_total'] = v[3]
                if k not in ('amort', 'dep', 'sbc', 'adjop', 'adj', 'op') and v[3]:
                    labels.append(f'{lab} {v[3]:+.0f}')
                break
    rec(p).setdefault('ng', {})['labels'] = '; '.join(labels)
    src(p, d)

for hdr, p in (('Three months ended March 31, 2026', 'Q1-26'), ('Three months ended March 31, 2025', 'Q1-25'),
               ('Year ended December 31, 2025', '2025'), ('Year ended December 31, 2024', '2024'), ('Year ended December 31, 2023', '2023')):
    a = find(F10, r'^' + hdr + '$', find(F10, r'^Adjusted Operating Profit, Adjusted Operating Profit Margin'))
    seg_table(F10, a, p, r'^% ')
for hdr, p in (('Three months ended June 30, 2026', 'Q2-26'), ('Three months ended June 30, 2025', 'Q2-25')):
    a = find(REL, r'\| ' + hdr + '$', find(REL, r'^Non-GAAP Financial Information$'))
    seg_table(REL, a, p, r'^% ')
# release Exhibit 4: segment revenue / expenses (Q2)
for hdr, p in (('Three months ended June 30, 2026', 'Q2-26'), ('Three months ended June 30, 2025', 'Q2-25')):
    a = find(REL, r'\| ' + hdr + '$', find(REL, r'^Operating Results by Segment$'))
    sg = rec(p)['seg']
    for k, pat in (('rev', r'Revenue'), ('opex', r'Operating-related expenses'), ('sga', r'Selling and general expenses'),
                   ('da', r'Depreciation and amortization'), ('texp', r'Total expenses')):
        for s, val in zip(SEGS, row(REL, pat, a, a + 15)[:3]):
            if k == 'rev' and s == 'corp': continue
            sg.setdefault(s, {})[k] = val
# Form 10 segment operating-related / selling & general expenses (Q1-26, Q1-25, FY2023-25)
def seg_exp(a, p_cols):
    for lab, s in ((r'CARFAX', 'cfx'), (r'B2B', 'b2b'), (r'Corporate Unallocated expense', 'corp')):
        v = row(F10, lab, a, a + 12)
        for j, p in enumerate(p_cols):
            sg = rec(p)['seg'].setdefault(s, {}); sg['opex'], sg['sga'] = v[2 * j], v[2 * j + 1]
a = find(F10, r'^CARFAX \| 68 \| 91'); seg_exp(a - 1, ('Q1-26', 'Q1-25'))
a = find(F10, r'^CARFAX \(1\) \| 258'); seg_exp(a - 1, ('2025', '2024'))
a = find(F10, r'^CARFAX \(1\) \| 243 \| 339 \| 221'); seg_exp(a - 1, ('2024', '2023'))

# ============================================================== consolidated non-GAAP (Adjusted EBITDA reconciliation, FCF)
a = find(F10, r'^Net income \| 55 \| 58 \| 220', find(F10, r'presents a reconciliation of our net income to Adjusted EBITDA'))
for col, p in enumerate(('Q1-26', 'Q1-25', '2025', '2024', '2023')):
    ng = rec(p).setdefault('ng', {})
    ng['adj_ebitda'] = row(F10, r'Adjusted EBITDA', a, a + 20, col)
    ng['ebitda_da'] = row(F10, r'Depreciation and amortization', a, a + 20, col)
    ng['ebitda_int'] = row(F10, r'Interest, net', a, a + 20, col)
a = find(F10, r'^Cash provided by operating activities \|', find(F10, r'reconciliation of our cash provided by operating activities to Free cash flow'))
for col, p in enumerate(('Q1-26', 'Q1-25', '2025', '2024', '2023')):
    rec(p)['ng']['fcf'] = row(F10, r'Free cash flow', a, a + 6, col)
a = find(REL, r'^Computation of Free Cash Flow$')
rec('Q2-26')['ng']['fcf'] = row(REL, r'Free cash flow', a, a + 8, 0); rec('Q2-25')['ng']['fcf'] = row(REL, r'Free cash flow', a, a + 8, 1)
rec('Q2-26')['ng']['fcf_h1'] = row(REL, r'Free cash flow', a, a + 8, 2); rec('Q2-25')['ng']['fcf_h1'] = row(REL, r'Free cash flow', a, a + 8, 3)
for p in ('Q2-26', 'Q2-25'):
    rec(p)['ng']['adj_ebitda'] = rec(p)['seg']['cfx']['adj'] + rec(p)['seg']['b2b']['adj'] + rec(p)['seg']['corp']['adj']
for i, p in enumerate(('Q1-25', 'Q2-25', 'Q3-25', 'Q4-25', '2025')):
    rec(p).setdefault('ng', {}).setdefault('adj_ebitda_ex992', float(EX992_SEG['adj'][i][0] + EX992_SEG['adj'][i][1] + EX992_SEG['adj'][i][2]))
    rec(p)['ng'].setdefault('adj_ebitda', rec(p)['ng']['adj_ebitda_ex992'])
for i, p in enumerate(('Q3-25', 'Q4-25')):
    lab = []
    for k in ('trans', 'sev', 'legal', 'other'):
        t = sum(EX992_SEG[k][2 + i])
        if t: lab.append(f'{ {"trans": "Transaction costs", "sev": "Employee severance charges", "legal": "Legal settlement recovery", "other": "Other"}[k]} {t:+.0f}')
    rec(p)['ng']['labels'] = '; '.join(lab)

# ============================================================== guidance (Q2-26 release outlook)
a = find(REL, r'^Outlook$')
g = rec('Q2-26').setdefault('guidance', {})
g['rev'] = [float(x.replace(',', '')) for x in re.findall(r'[\d,]+', REL[1][a + 2].split('|')[1])]
g['rev_growth'] = [float(x) / 100 for x in re.findall(r'[\d.]+', REL[1][a + 3].split('|')[1])]
g['adj_ebitda'] = [float(x) for x in re.findall(r'\d+', REL[1][a + 4].split('|')[1])]
g['date'] = '2026-08-07'
g['dps_q'] = 0.06

# ============================================================== S&P Global Mobility segment (memo)
SP = sorted(glob.glob(os.path.join(S, 'txt', 'SPGI_*.txt')))
def spgi_q(path):
    d = (os.path.basename(path)[:-4], clean(open(path, encoding='utf-8')))
    dt = d[0].split('_')[1]
    y, m = int(dt[:4]), int(dt[5:7])
    q = {2: 4, 4: 1, 5: 1, 7: 2, 8: 2, 10: 3, 11: 3}[m]
    fy = y - 1 if q == 4 else y
    return d, fy, q

def spgi_lines(d):
    L = d[1]
    mob = [i for i, l in enumerate(L) if re.match(r'^Mobility( \([a-z]\))? \| -?[\d(]', l)]
    return L, mob

for path in SP:
    d, fy, q = spgi_q(path)
    if (fy, q) < (2023, 1) and not (fy, q) == (2022, 4): continue
    L, mob = spgi_lines(d)
    rev_i, exp_i, op_i = mob[0], mob[1], mob[2]
    subs = [i for i in mob[3:] if len(nums(L[i])) >= 6]
    p = f'Q{q}-{str(fy)[2:]}'
    out = {}
    v = nums(L[rev_i]); out['rev'] = v[0]
    out['exp'] = nums(L[exp_i])[0]; out['op'] = nums(L[op_i])[0]
    try:
        a = find(d, r'^Mobility \| Operating profit')
    except KeyError:    # 2026 releases: no Mobility non-GAAP schedule (S&P Global reports pro forma ex Mobility)
        a = None
    if a is not None:
        v = nums(L[a]); out['op_ng'] = v[0]
        out['ng_adj'] = nums(L[a + 1])[0]; out['amort'] = nums(L[a + 2])[0]
        k = a + 3
        while not re.match(r'^(Adjusted operating profit|Adjusted operating profit/)', L[k]): k += 1
        out['adj_op'] = nums(L[k])[0]
    sv = nums(L[subs[0]]); out['sub'], out['nsub'] = sv[0], sv[2]
    if fy == 2022:   # Q4-22 release: twelve-month pro forma columns only used for FY2022
        r = rec('2022'); r.setdefault('spgi', {})
        v = nums(L[a]); r['spgi']['op_pf'] = v[2]
        ra = find(d, r'^Mobility \| Revenue/Pro forma revenue')
        r['spgi']['rev_pf'] = nums(L[ra])[2]
        ka = find(d, r'^Adjusted operating profit/Non-GAAP pro forma adjusted operating profit', a)
        r['spgi']['adj_op_pf'] = nums(L[ka])[2]
        r['spgi']['rev_reported'] = nums(L[rev_i])[2]
        r['notes'].append('FY2022: S&P Global Mobility segment only (IHS Markit merger 28-Feb-2022). Reported revenue covers 1-Mar–31-Dec-2022; '
                          'pro forma revenue / operating profit / adjusted operating profit are S&P Global\'s non-GAAP pro forma figures for the full year.')
        src('2022', URL.get(d[0]))
        continue
    r = rec(p); r['spgi'] = out; src(p, URL.get(d[0]))
    if q == 4:      # twelve-month columns of the Q4 release -> annual memo
        A = {}
        A['rev'] = nums(L[rev_i])[2]; A['exp'] = nums(L[exp_i])[2]; A['op'] = nums(L[op_i])[2]
        v = nums(L[a]); A['op_ng'] = v[2]
        A['ng_adj'] = nums(L[a + 1])[1 if len(nums(L[a + 1])) == 2 else 2]
        A['amort'] = nums(L[a + 2])[1 if len(nums(L[a + 2])) == 2 else 2]
        A['adj_op'] = nums(L[k])[2]
        sv = nums(L[subs[1]]); A['sub'], A['nsub'] = sv[0], sv[2]
        rec(str(fy))['spgi'] = A; src(str(fy), URL.get(d[0]))
    if (fy, q) >= (2026, 1):
        r['notes'].append('S&P Global 2026 releases: Mobility segment shown until the 1-Jul-2026 spin (discontinued operations from Q3-26).')

# ============================================================== write
os.makedirs(OUT, exist_ok=True)
for p, r in sorted(REC.items()):
    json.dump(r, open(os.path.join(OUT, f'{p}.json'), 'w'), indent=1, sort_keys=False)
print(len(REC), 'periods:', ' '.join(sorted(REC)))
