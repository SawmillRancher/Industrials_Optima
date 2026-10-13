"""FY2006-FY2008 (before Google's XBRL filings, which start with the Q2-2009 10-Q): each year from its own Form 10-K
(as originally reported), parsed from the h2t text of the consolidated financial statements. Amounts in USD thousands in the
filings -> USD millions. Per-share data and share counts as filed (pre-split; split factors are applied in normalize.py)."""
import os, re, glob
S = os.environ.get('GOOG_SRC', '/tmp/goog_src')
TENK = {2006: '2007-03-01_10-K_0001193125-07-044494', 2007: '2008-02-15_10-K_0001193125-08-032690', 2008: '2009-02-13_10-K_0001193125-09-029448'}
URL = {2006: 'https://www.sec.gov/Archives/edgar/data/1288776/000119312507044494/d10k.htm',
       2007: 'https://www.sec.gov/Archives/edgar/data/1288776/000119312508032690/d10k.htm',
       2008: 'https://www.sec.gov/Archives/edgar/data/1288776/000119312509029448/d10k.htm'}

def nums(line):
    out = []
    for c in line.split(' | ')[1:]:
        c = c.strip()
        if c in ('—', '-'): out.append(0.0); continue
        m = re.fullmatch(r'\(?\$?\s*([\d,]+(?:\.\d+)?)\)?', c)
        if m: out.append((-1 if c.startswith('(') else 1) * float(m.group(1).replace(',', '')))
    return out

# (key, regex on the row label, statement section) ; last column = the filing's own year
IS = [('rev', r'^Revenues$'), ('cor', r'^Cost of revenues'), ('rd', r'^Research and development'), ('sm', r'^Sales and marketing'),
      ('ga', r'^General and administrative'), ('found', r'^Contribution to Google Foundation'), ('opex_tot', r'^Total costs and expenses'),
      ('oi', r'^Income from operations'), ('impair_eq', r'^Impairment of equity investments'), ('oie_int', r'^Interest income and other, net'),
      ('ebt', r'^Income before income taxes'), ('tax', r'^Provision for income taxes'), ('ni', r'^Net income$'),
      ('eps_b', r'^Basic$'), ('eps_d', r'^Diluted$')]
BS = [('cash', r'^Cash and cash equivalents$'), ('msec', r'^Marketable securities$'), ('ar', r'^Accounts receivable'), ('tca', r'^Total current assets'),
      ('nmsec', r'^Non-marketable equity securities'), ('ppe', r'^Property and equipment, net'), ('intang', r'^Intangible assets, net'),
      ('gw', r'^Goodwill$'), ('ta', r'^Total assets'), ('ap', r'^Accounts payable'), ('tcl', r'^Total current liabilities'),
      ('eq', r'^Total stockholders. equity'), ('tle', r'^Total liabilities and stockholders. equity')]
CF = [('cfo', r'^Net cash provided by operating activities'), ('dep', r'^Depreciation and amortization of property and equipment'),
      ('amort', r'^Amortization of intangibles and other'), ('sbc', r'^Stock-based compensation$'), ('deftax', r'^Deferred income taxes$'),
      ('capex', r'^Purchases of property and equipment'), ('acq', r'^Acquisitions'), ('cfi', r'^Net cash used in investing activities'),
      ('cff', r'^Net cash provided by financing activities'), ('fx', r'^Effect of exchange rate changes'), ('beg', r'^Cash and cash equivalents at beginning'),
      ('end', r'^Cash and cash equivalents at end'), ('eq_iss', r'^Net proceeds from a public offering'), ('sec_buy', r'^Purchases of marketable securities'),
      ('sec_sell', r'^Maturities and sales of marketable securities'), ('nm_inv', r'^Investments in non-marketable equity securities'),
      ('impair_cf', r'^Impairment of equity investments')]

def section(lines, title):
    idx = [i for i, l in enumerate(lines) if l.strip().startswith(title)]     # the statement page titles are upper case
    return idx[0] if idx else None

def grab(lines, start, spec, n=220):
    out = {}
    for l in lines[start:start + n]:
        lab = l.split(' | ')[0].strip()
        for k, rx in spec:
            if k in out: continue
            if re.search(rx, lab):
                v = nums(l)
                if v: out[k] = v[-1]
    return out

def extract(y):
    t = open(glob.glob(os.path.join(S, 'txt', TENK[y] + '*.txt'))[0]).read().split('\n')
    b = section(lines=t, title='CONSOLIDATED BALANCE SHEETS')
    i = section(t, 'CONSOLIDATED STATEMENTS OF INCOME')
    c = section(t, 'CONSOLIDATED STATEMENTS OF CASH FLOWS')
    r = {}
    r.update(grab(t, b, BS)); r.update(grab(t, i, IS)); r.update(grab(t, c, CF, 120))
    # revenue streams from MD&A (USD thousands in FY2006 10-K, USD millions to one decimal in FY2007 / FY2008)
    for k, rx in (('rs_web', r'^Google web sites$'), ('rs_net', r'^Google Network web sites$'), ('rs_lic', r'^Licensing and other revenues$')):
        for l in t:
            if re.search(rx, l.split(' | ')[0].strip()):
                v = nums(l)
                if len(v) >= 3: r[k] = v[2]; break
    sc = 1e-3
    for k in list(r):
        if k in ('eps_b', 'eps_d'): continue
        if k.startswith('rs_') and y >= 2007: continue
        r[k] = round(r[k] * sc, 3)
    # weighted shares (thousands -> millions) from the EPS note: Class A | Class B pairs per year, current year last.
    # Basic = Class A + Class B; diluted = the Class A diluted count, which assumes conversion of Class B.
    basic = [nums(l) for l in t if re.search(r'^Number of shares used in basic computation', l)]
    dil = [nums(l) for l in t if re.search(r'^Number of shares used in per share computations', l)]
    if basic: r['sh_b'] = round((basic[-1][-2] + basic[-1][-1]) / 1e3, 3)
    if dil: r['sh_d'] = round(dil[-1][-2] / 1e3, 3)
    r['oie'] = round(r.get('impair_eq', 0.0) + r['oie_int'], 3)
    r['src'] = URL[y]
    return r

if __name__ == '__main__':
    for y in TENK: print(y, extract(y))
