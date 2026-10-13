"""Per-period extraction for Meta Platforms -> data/<period>.json (schema: EXTRACTION_SCHEMA.md).

Sources (SEC EDGAR, CIK 1326801; text from fetch.py / h2t.py in $META_SRC/txt):
  - 8-K Item 2.02 earnings releases (Ex. 99.1), Q2-2012 .. Q2-2026: statements of income, balance sheets and cash flows (three-month
    columns for quarters; the Q4 release's year columns for fiscal years 2012-2025), segment information (Q4-2021+), the GAAP to
    non-GAAP reconciliation (FX-neutral revenue; non-GAAP costs / operating income / net income / EPS 2012-16; free cash flow 2013+),
    and KPIs from the release text (DAUs / MAUs to Q4-2023, DAP / MAP from Q4-2019, ad impressions and price per ad from Q4-2021,
    headcount).
  - IPO prospectus (424B4, 18-May-2012): FY2009-2011 statements of income and cash flows; balance sheets at 31-Dec-2010 / 2011.
  - 10-Q / 10-K: ad impressions ("number of ads delivered") and average price per ad y/y % from MD&A (2014-2021; quarters from the 10-Qs,
    years from the 10-Ks); revenue by geography (billing address, from 2018); Class A + Class B shares issued and outstanding at the
    balance-sheet date (balance-sheet caption).
Each record keeps the source URLs; values in USD millions as published (per share in USD; shares and people in millions)."""
import json, os, re, glob
from parse_release import parse, find, num

S = os.environ.get('META_SRC', '/tmp/meta_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
FL = json.load(open(os.path.join(S, 'filings.json')))
def url(o, f): return f"https://www.sec.gov/Archives/edgar/data/1326801/{o['acc'].replace('-', '')}/{f}"
def pk(y, q): return f'Q{q}-{str(y)[2:]}'
def clean(lab): return re.sub(r'\s*(\(\d\)|\*|\d)\s*$', '', lab.replace('’', "'")).strip()

def rel_period(date):
    y, m = int(date[:4]), int(date[5:7])
    if m <= 3: return y - 1, 4
    return y, {4: 1, 5: 1, 7: 2, 8: 2, 10: 3, 11: 3}[m]

# ------------------------------------------------------------------ label maps: (key, regex, nth match, only after row matching)
IS = [('rev', r'^(Total )?revenue$', 0, None), ('cogs', r'^Cost of revenue$', 0, None), ('rd', r'^Research and development$', 0, None),
      ('mm', r'^Marketing and sales$', 0, None), ('ga', r'^General and administrative$', 0, None), ('costs', r'^Total costs and expenses$', 0, None),
      ('oi', r'^Income (\(loss\) )?from operations$', 0, None), ('int_exp', r'^Interest expense$', 0, None),
      ('oth', r'^Other (income|\(expense\)|\(income\)|expense)', 0, None), ('io_net', r'^Interest and other income', 0, None),
      ('ebt', r'^Income (\(loss\) )?before', 0, None), ('tax', r'^\(?Provision', 0, None), ('ni', r'^Net income( \(loss\))?$', 0, None),
      ('ni_part', r'participating securities', 0, None), ('ni_common', r'attributable to Class A and Class B', 0, None),
      ('eps_b', r'^Basic$', 0, None), ('eps_d', r'^Diluted$', 0, None), ('sh_b', r'^Basic$', 1, None), ('sh_d', r'^Diluted$', 1, None),
      ('sbc_is', r'^Total share-based compensation expense$', 0, None)]
BS = [('cash', r'^Cash and cash equivalents$', 0, None), ('ms', r'^Marketable securities$', 0, None), ('ar', r'^Accounts receivable', 0, None),
      ('itr', r'^Income tax refundable', 0, None), ('prepaid', r'^Prepaid expenses', 0, None), ('tca', r'^Total current assets$', 0, None),
      ('nme', r'^(Non-marketable equity|Equity investments)', 0, None), ('ppe', r'^Property and equipment, net', 0, None),
      ('rou', r'^Operating lease right-of-use', 0, None), ('gw', r'^Goodwill', 0, None), ('intang', r'^Intangible assets', 0, None),
      ('oa', r'^Other assets$', 0, None), ('ta', r'^Total assets$', 0, None),
      ('ap', r'^Accounts payable$', 0, None), ('pp', r'partners payable$', 0, None), ('olc', r'^Operating lease liabilities, current', 0, None),
      ('accr', r'^Accrued expenses', 0, None), ('defrev', r'^Deferred revenue', 0, None), ('clc', r'^Current portion of capital lease', 0, None),
      ('tcl', r'^Total current liabilities$', 0, None), ('oln', r'^Operating lease liabilities, non-current', 0, None),
      ('cll', r'^Capital lease obligations, less', 0, None), ('ltd', r'^Long-term debt$', 0, None), ('ltt', r'^Long-term income taxes', 0, None),
      ('ol', r'^Other liabilities$', 0, None), ('tl', r'^Total liabilities$', 0, None), ('pref', r'^Convertible preferred', 0, None),
      ('apic', r'^(Common stock and additional|Additional paid-in)', 0, None), ('aoci', r'^Accumulated other', 0, None),
      ('re', r'^Retained earnings', 0, None), ('te', r"^Total stockholders' equity$", 0, None), ('tle', r"^Total liabilities and stockholders' equity$", 0, None)]
CF = [('ni', r'^Net income( \(loss\))?$', 0, None), ('dda', r'^Depreciation and amortization$', 0, None), ('sbc', r'^Share-based compensation$', 0, None),
      ('def', r'^Deferred income taxes$', 0, None), ('cfo', r'^Net cash provided by( \(used in\))? operating', 0, None),
      ('capex', r'^Purchases? of property and equipment', 0, None), ('ppe_proc', r'^Proceeds relating to property and equipment', 0, None), ('ms_buy', r'^Purchases? of marketable', 0, None),
      ('ms_sale', r'^Sales of marketable', 0, None), ('ms_mat', r'^Maturities of marketable', 0, None),
      ('ms_sm', r'^(Sales and maturities|Maturities and sales) of marketable', 0, None),
      ('nme', r'(non-marketable equity|^Purchases of equity investments)', 0, None), ('acq', r'^Acquisitions? of business', 0, None),
      ('cfi', r'^Net cash .*investing', 0, None),
      ('eq_iss', r'^Net proceeds from (the )?issuance of (common|convertible)', 0, None), ('netshare', r'^Taxes paid related to net share settlement', 0, None),
      ('bb', r'^Repurchases of Class A common stock$', 0, None), ('div', r'^(Payments for dividends|Dividends? payments)', 0, None),
      ('debt_iss', r'^Proceeds from (issuance of )?(long-term )?debt', 0, None), ('debt_rep', r'^Repayment of long-term debt', 0, None),
      ('lease', r'^Principal payments on (capital lease|finance lease)', 0, None), ('cff', r'^Net cash .*financing', 0, None),
      ('fx', r'^Effect of exchange rate', 0, None),
      ('net', r'^Net (increase|decrease|\(decrease\)|\(increase\))[^,]*in cash', 0, None),
      ('beg', r'at beginning of', 0, None), ('end', r'at end of', 0, None)]
REC = [('adv', r'^GAAP advertising revenue$', 0, None), ('adv_exfx', r'^Advertising revenue excluding', 0, None),
       ('rev_exfx', r'^Revenue excluding', 0, None), ('ng_costs', r'^Non-GAAP costs and expenses', 0, None),
       ('sbc_ng', r'^Share-based compensation expense$', 0, r'^GAAP income .*from operations'),
       ('payroll', r'^Payroll tax', 0, r'^GAAP income .*from operations'), ('amort', r'^Amortization of intangible', 0, r'^GAAP income .*from operations'),
       ('ng_oi', r'^Non-GAAP income from operations', 0, None), ('tax_adj', r'^Income tax adjustments', 0, None),
       ('ng_ni', r'^Non-GAAP net income', 0, None), ('ng_sh', r'^(Non-GAAP diluted shares|GAAP and Non-GAAP diluted shares)', 0, None),
       ('ng_eps', r'^Non-GAAP diluted earnings per share', 0, None),
       ('fcf_cfo', r'^Net cash provided by operating', 0, None), ('fcf_capex', r'^Purchases of property and equipment', 0, r'^Net cash provided by operating'),
       ('fcf_cl', r'^Property and equipment acquired under capital leases', 0, None), ('fcf_flp', r'^Principal payments on finance leases', 0, None),
       ('fcf', r'^Free cash flow$', 0, None)]

def grab(rows, spec, col):
    rows = [(clean(l), d) for l, d in rows]
    out = {}
    for k, rx, nth, after in spec:
        v = find(rows, rx, col, nth, after)
        if v is not None: out[k] = v
    return out

def cf_ms(c):
    """net marketable-securities flows (purchases + sales + maturities)."""
    if not any(k in c for k in ('ms_buy', 'ms_sale', 'ms_mat', 'ms_sm')): return
    c['ms_net'] = sum(c.pop(k, 0.0) for k in ('ms_buy', 'ms_sale', 'ms_mat', 'ms_sm'))

def seg_vals(rows, col):
    rows = [(clean(l), d) for l, d in rows]
    o, sec = {}, 'rev'
    for lab, d in rows:
        if re.match(r'^Income \(loss\) from operations', lab): sec = 'oi'; continue
        if col not in d: continue
        k = {'Advertising': 'foa_adv', 'Other revenue': 'foa_oth', 'Family of Apps': 'foa', 'Reality Labs': 'rl',
             'Total revenue': 'rev', 'Total income from operations': 'oi'}.get(lab)
        if not k: continue
        key = k if k in ('foa_adv', 'foa_oth', 'rev', 'oi') else f'{k}_{sec}'
        o.setdefault(key, d[col])
    return o

REC_ = {}
def rec(p):
    return REC_.setdefault(p, {'period': p, 'sources': [], 'notes': []})

# ------------------------------------------------------------------ earnings releases
def releases():
    for o in FL:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        fs = [f for f in glob.glob(f"{S}/txt/{o['date']}_8-K_{o['acc']}_*.txt") if 'Revenue |' in open(f).read()]
        if len(fs) != 1: raise RuntimeError(f'{o["date"]}: {fs}')
        yield o, fs[0]

def do_release(o, f):
    y, q = rel_period(o['date'])
    text = open(f).read()
    pr = parse(text, y)
    u = url(o, os.path.basename(f).split('_', 3)[3].replace('.txt', '.htm'))
    p = pk(y, q); r = rec(p); r['sources'].append(u); r['release_date'] = o['date']
    neg = any(re.match(r'^\(Provision for\) benefit', clean(l)) for l, d in pr['is'] if d)     # "(Provision for) benefit": benefit +
    r['is'] = grab(pr['is'], IS, 'cur3'); r['bs'] = grab(pr['bs'], BS, 'cur'); r['cf'] = grab(pr['cf'], CF, 'cur3'); cf_ms(r['cf'])
    r['ngaap'] = grab(pr['rec'], REC, 'cur3'); r['kpi'] = {k: v for k, v in pr['kpi'].items() if not k.endswith('_fy')}
    r['py'] = {'is': grab(pr['is'], IS, 'py3')}
    if neg:
        for blk in (r['is'], r['py']['is']):
            if 'tax' in blk: blk['tax'] = -blk['tax']
    if pr['seg']:
        if p == 'Q4-21': do_q421_seg(text, u)
        else:
            r['seg'] = seg_vals(pr['seg'], 'cur3')
            if q < 4: rec(pk(y - 1, q)).setdefault('seg_py', seg_vals(pr['seg'], 'py3'))
    # fiscal-year record from the Q4 release (year columns); the prior year as presented is kept for restatement notes
    if q == 4:
        a = rec(str(y)); a['sources'].append(u); a['release_date'] = o['date']
        a['is'] = grab(pr['is'], IS, 'cury'); a['bs'] = r['bs']; a['cf'] = grab(pr['cf'], CF, 'cury'); cf_ms(a['cf'])
        a['ngaap'] = grab(pr['rec'], REC, 'cury')
        a['kpi'] = {k[:-3]: v for k, v in pr['kpi'].items() if k.endswith('_fy')}
        for k in ('dau', 'mau', 'dap', 'map', 'headcount'):
            if k in r['kpi']: a['kpi'][k] = r['kpi'][k]
        a['py'] = {'is': grab(pr['is'], IS, 'pyy')}
        if neg:
            for blk in (a['is'], a['py']['is']):
                if 'tax' in blk: blk['tax'] = -blk['tax']
        if pr['seg'] and p != 'Q4-21': a['seg'] = seg_vals(pr['seg'], 'cury')
    return r

def do_q421_seg(text, u):
    """Q4-2021 release: segment table with Q4/Q3/Q2/Q1-2021, Q4-2020 and FY2021 / 2020 / 2019 columns (first presentation of the segments)."""
    lines = text.split('\n')
    i = next(k for k, l in enumerate(lines) if l.strip() == 'Segment Information')
    cols = ['Q4-21', 'Q3-21', 'Q2-21', 'Q1-21', 'Q4-20', '2021', '2020', '2019']
    rows = []
    for l in lines[i + 4:i + 16]:
        c = [x.strip() for x in l.split(' | ')]
        vals = [num(x) for x in c[1:]]
        rows.append((c[0], dict(zip(cols, vals)) if len(vals) == 8 and None not in vals else {}))
    for p in cols:
        r = rec(p); r['seg'] = seg_vals(rows, p)
        if u not in r['sources']: r['sources'].append(u)
        r['notes'].append('Segment data (FoA / RL) from the Q4-2021 release, which first presented the segments (2019-21 recast).')

# ------------------------------------------------------------------ IPO prospectus (FY2009-2011)
def do_424b4():
    o = next(o for o in FL if o['form'] == '424B4')
    f = glob.glob(f"{S}/txt/{o['date']}_424B4_*.txt")[0]
    u = url(o, o['primary']); lines = open(f).read().split('\n')
    def block(title, start):
        i = next(k for k in range(start, len(lines)) if lines[k].strip().startswith(title))
        return i
    i_bs = block('CONSOLIDATED BALANCE SHEETS', 5000); i_is = block('CONSOLIDATED STATEMENTS OF INCOME', i_bs); i_cf = block('CONSOLIDATED STATEMENTS OF CASH FLOWS', i_is)
    def rows(s, e, n):
        out = []
        for l in lines[s:e]:
            c = [x.strip() for x in l.split(' | ')]
            if c[0].startswith('2011 and March 31, 2012'): c[0] = 'Accounts receivable'          # caption wrapped over two lines
            if 'no shares authorized, issued and outstanding, pro forma' in c[0]: c[0] = 'Convertible preferred stock'
            vals = [num(x) for x in c[1:]]
            out.append((c[0], vals[:n] if len(vals) >= n and None not in vals[:n] else []))
        return out
    isr = rows(i_is, i_is + 60, 3); cfr = rows(i_cf, i_cf + 70, 3); bsr = rows(i_bs, i_bs + 50, 2)
    for j, y in enumerate((2009, 2010, 2011)):
        r = rec(str(y)); r['sources'].append(u)
        conv = lambda rr: [(lab, {'v': v[j]}) for lab, v in rr if v]
        r['is'] = grab(conv(isr), IS, 'v'); r['cf'] = grab(conv(cfr), CF, 'v'); cf_ms(r['cf'])
        r['notes'].append('FY2009-2011 statements from the IPO prospectus (424B4, 18-May-2012), as originally reported.')
        if y >= 2010:
            r['bs'] = grab([(lab, {'v': v[j - 1]}) for lab, v in bsr if v], BS, 'v')
        else:
            r['notes'].append('No balance sheet at 31-Dec-2009 in the prospectus financial statements.')
    # advertising revenue (MD&A revenue table: Advertising / Payments and other fees)
    for l in lines:
        c = [x.strip() for x in l.split(' | ')]
        if c[0] == 'Advertising' and len(c) == 6:
            for j, y in enumerate((2009, 2010, 2011)): rec(str(y)).setdefault('ngaap', {})['adv'] = num(c[1 + j])
            break
    return u

# ------------------------------------------------------------------ 10-Q / 10-K text extras
ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4}
def sents(text):
    t = re.sub(r'\s+', ' ', text)
    return re.split(r'(?<=[.])\s+(?=[A-Z•])', t)

def growth_10q(text, y, q, annual):
    """(impressions y/y, price per ad y/y) for the period: the first number after 'number of ads delivered' / 'ad impressions' and
    'average price per ad' in the MD&A sentence that names the period."""
    out = {}
    for s in sents(text):
        if annual:
            if not re.search(rf'\b(In|During) {y}\b|\bin {y}\b|year-over-year in {y}|in {y} increased|{y} compared to {y - 1}', s): continue
        else:
            qw = [k for k, v in ORD.items() if v == q][0]
            mon = {1: 'March 31', 2: 'June 30', 3: 'September 30'}[q]
            if not (re.search(rf'{qw} quarter( and (the )?first \w+ months)? of {y}', s, re.I) or re.search(rf'months ended {mon}, {y}', s)): continue
        for k, rx in (('impr_g', r'(?:number of ads delivered|ad impressions(?: delivered)?(?: across our Family of Apps)?(?: in the \w+ quarter of \d{4})?)\s+(increased|decreased)(?: by)?\s+(\d+)%'),
                      ('price_g', r'average price per ad(?: in the \w+ quarter of \d{4})?\s+(increased|decreased)(?: by)?\s+(\d+)%'),
                      ('price_g', r'(\d+)% year-over-year (increase|decrease) in our average price per ad')):
            if k in out: continue
            m = re.search(rx, s, re.I)
            if not m: continue
            if m.group(1).isdigit(): v, d = float(m.group(1)), m.group(2).lower().startswith('inc')
            else: v, d = float(m.group(2)), m.group(1).lower().startswith('inc')
            out[k] = (1 if d else -1) * v / 100
    return out

GEO = [('geo_usc', r'^(US & Canada|United States and Canada|United States & Canada)$'), ('geo_eu', r'^Europe$'),
       ('geo_ap', r'^Asia-Pacific$'), ('geo_row', r'^Rest of World$')]
def geo_10q(text):
    lines = text.split('\n'); out = {}
    for i, l in enumerate(lines):
        if not re.match(r'^Revenue:?\s*(\|.*)?$', l.strip()): continue
        blk = {}
        for l2 in lines[i + 1:i + 8]:
            c = [x.strip() for x in l2.split(' | ')]
            lab = clean(c[0]); v = num(c[1]) if len(c) > 1 else None
            for k, rx in GEO:
                if re.match(rx, lab) and v is not None: blk[k] = v
        if len(blk) == 4: return blk
    for i, l in enumerate(lines):                       # newer filings: no "Revenue:" caption above the table
        lab = clean(l.split(' | ')[0])
        if re.match(GEO[0][1], lab):
            blk = {}
            for l2 in lines[i:i + 6]:
                c = [x.strip() for x in l2.split(' | ')]
                for k, rx in GEO:
                    if re.match(rx, clean(c[0])) and len(c) > 1 and num(c[1]) is not None: blk[k] = num(c[1])
            if len(blk) == 4: return blk
    return out

def shares_10q(text):
    t = re.sub(r'\s+', ' ', text)
    m = re.search(r'Class A shares authorized, ([\d,]+) million and [\d,]+ million shares issued and outstanding.*?Class B shares authorized, ([\d,]+) million( and [\d,]+ million)? shares issued', t)
    if m: return float(m.group(1).replace(',', '')) + float(m.group(2).replace(',', ''))
    return None

def do_10q():
    for o in FL:
        if o['form'] not in ('10-Q', '10-K'): continue
        f = glob.glob(f"{S}/txt/{o['date']}_{o['form']}_{o['acc']}_*.txt")
        if not f: continue
        text = open(f[0]).read()
        e = o['report']; y, mo = int(e[:4]), int(e[5:7])
        annual = o['form'] == '10-K'
        p = str(y) if annual else pk(y, {3: 1, 6: 2, 9: 3}[mo])
        r = rec(p); u = url(o, o['primary'])
        x = {}
        x.update(growth_10q(text, y, 4 if annual else {3: 1, 6: 2, 9: 3}[mo], annual))
        g = geo_10q(text)
        if g: x.update(g)
        sh = shares_10q(text)
        if sh: x['sh_out'] = sh
        if x:
            r['q10'] = x; r['sources'].append(u)

def main():
    os.makedirs(OUT, exist_ok=True)
    do_424b4()
    for o, f in releases(): do_release(o, f)
    do_10q()
    keep = [k for k in REC_ if k[0] == 'Q' and int('20' + k[-2:]) >= 2012 or k.isdigit()]
    for p in keep:
        json.dump(REC_[p], open(os.path.join(OUT, f'{p}.json'), 'w'), indent=1)
    print(len(keep), 'records')

if __name__ == '__main__':
    main()
