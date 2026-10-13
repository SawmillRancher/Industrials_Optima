"""Per-period extraction from the Mastercard earnings releases (8-K Item 2.02, Ex. 99.1) into data/<period>.json.

Periods: annual FY2006-FY2025 (Q4 release, twelve-month columns; balance sheet at 31-Dec; cash flow for the year) and quarters
Q1-13 - Q2-26 (three-month column of each quarter's own release; Q4 from the Q4 release's three-month column). Cash flow is
year to date (cf.ytd_months); normalize.py derives discrete quarters. Each record keeps the raw statement rows (label, value)
in USD millions so every mapped key can be traced, plus the prior-year comparative columns ('py') for restatement checks.
Statement keys are mapped by label (MAP_IS / MAP_BS / MAP_CF); lines a period does not present are omitted, never estimated.

Non-GAAP reconciliations, revenue by category (10-Q / 10-K notes) and release-narrative KPIs (cross-border volume and switched
transaction growth, currency-neutral growth) are transcribed into data/_ngaap.json, data/_revcat.json and data/_kpi.json
(see EXTRACTION_SCHEMA.md) and merged in normalize.py."""
import json, os, re, glob
from parse_release import parse

S = os.environ.get('MA_SRC', '/tmp/ma_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '1141391'

MAP_IS = [('rev', r'^(net revenue|revenues?, ?ne ?t|revenue, net)'), ('ga', r'^general and administrative'),
          ('am', r'^advertising and (marketing|market development)'), ('lit', r'^(provision for litigation|litigation settlements)'),
          ('char', r'^charitable contributions'), ('da', r'^depreciation and amortization'), ('dep', r'^depreciation$'), ('amo', r'^amortization$'),
          ('opex', r'^total operating expenses'), ('oi', r'^operating income'), ('inv_inc', r'^investment income'),
          ('eq_gl', r'^gains \(losses\) on equity'), ('int_exp', r'^interest expense'), ('oth', r'^other income ?(\(expense\)|/\(expense\))?, net|^other income \(expense\)$'),
          ('oth_tot', r'^total other income'), ('ebt', r'^income (\(loss\) )?before income taxes'), ('tax', r'^income tax expense'),
          ('ni_tot', r'^net income( \(loss\))?$'), ('nci', r'attributable to non-?controlling'), ('ni_ma', r'^net income( \(loss\))? att+ributable to mastercard'),
          ('eps_b', r'^basic (earnings|net income)( \(loss\))? per share'), ('sh_b', r'^basic weighted'),
          ('eps_d', r'^diluted (earnings|net income)( \(loss\))? per share'), ('sh_d', r'^diluted weighted')]
MAP_BS = [('cash', r'^cash and cash equivalents$'), ('rcash_lit', r'^restricted cash.*(litigation|escrow)'),
          ('rcash', r'^restricted cash( and restricted cash equivalents)?$'), ('rsd_a', r'^restricted security deposits held for'),
          ('inv_cur', r'^investments?$|^investment securities|^trading$|^available-for-sale$|^held-to-maturity'),
          ('ar', r'^accounts receivable'), ('settle_a', r'^settlement (assets|due from)'),
          ('tca', r'^total current assets'), ('ppe', r'^property'), ('dta', r'^deferred income taxes'), ('gw', r'^goodwill'),
          ('intang', r'^other intangible assets'), ('ta', r'^total assets'), ('ap', r'^accounts payable'),
          ('settle_l', r'^settlement (obligations|due to)'), ('lit_l', r'^(accrued litigation|obligations under)'),
          ('accr', r'^accrued expenses'), ('std', r'^short-term debt|^current portion of long-term debt'),
          ('tcl', r'^total current liabilities'), ('ltd', r'^long-term debt'), ('tl', r'^total liabilities$'),
          ('rnci', r'^redeemable non-?controlling'), ('minority', r'^minority interest'),
          ('eq_ma', r"^(total )?mastercard incorporated stockholders|^total stockholders. equity$"),
          ('nci', r'^non-?controlling interests?$'), ('teq', r'^total equity'), ('tle', r'^total liabilities(,| and)')]
MAP_CF = [('ni', r'^net income'), ('da', r'^depreciation and amortization'), ('sbc', r'^share[- ]based (payments|compensation)'),
          ('deftax', r'^deferred income taxes'), ('eq_gl', r'^\(gains?\) losses? on equity|^gains? on equity'),
          ('cust_inc', r'^amortization of customer incentives'),
          ('cfo', r'^net cash (provided by|used in|\(used in\)|provided by \(used in\)) operating'),
          ('capex', r'^purchases? of (property|property and equipment|property, plant)'), ('capsw', r'^capitalized software'),
          ('acq', r'^acquisition of businesses|^acquisitions of businesses|^acquisition of business'),
          ('cfi', r'^net cash.*investing activities'), ('bb', r'^purchases? of treasury stock'), ('div', r'^dividends paid'),
          ('cff', r'^net cash.*financing activities'), ('fx', r'^effect of exchange rate'),
          ('net', r'^net (increase|decrease|\(decrease\) increase|increase \(decrease\)|change)'),
          ('beg', r'beginning of (period|year)'), ('end', r'end of (period|year)')]

def mapped(rows, mp, col, first_only=True):
    out = {}
    for lab, vals in rows:
        l = lab.lower().strip()
        for k, rx in mp:
            if re.search(rx, l):
                if len(vals) <= col: break
                if k in out and first_only:
                    if k in ('inv_cur', 'lit_l', 'dta', 'std', 'rsd_a'): out[k + '_2'] = vals[col]     # noncurrent / liability duplicates
                    break
                out[k] = vals[col]
                break
    return out

def releases():
    F = json.load(open(os.path.join(S, 'filings.json')))
    rel = {}
    for o in F:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        ex = [x for x in o['files'] if re.search(r'99[_.-]?1|991|ex-?99', x.lower()) and '992' not in x.lower()]
        if not ex: continue
        t = os.path.join(S, 'txt', f"{o['date']}_8-K_{o['acc']}_{ex[0].rsplit('.', 1)[0]}.txt")
        if not os.path.exists(t): continue
        r = parse(open(t).read())
        if not r.get('is'): continue
        m, y = int(o['date'][5:7]), int(o['date'][:4])
        q = 4 if m <= 3 else 1 if m <= 6 else 2 if m <= 9 else 3
        fy = y - 1 if q == 4 else y
        url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{ex[0]}"
        rel[(fy, q)] = dict(r=r, date=o['date'], url=url)
    return rel

def scale_fix(r, date):
    """releases filed before Apr-2010 are in USD thousands (amounts and share counts); later ones in USD millions."""
    if r.get('_scaled'): return
    r['_scaled'] = True
    if date < '2010-04-01':
        for key in ('is', 'bs', 'cf'):
            new = []
            for lab, vals in r.get(key, []):
                ps = re.search(r'per share', lab, re.I) and not re.search(r'outstanding', lab, re.I)
                new.append((lab, vals if ps else [round(v / 1000, 6) for v in vals]))
            r[key] = new

def record(period, fy, q, rl, annual):
    r = rl['r']; scale_fix(r, rl['date'])
    ncols = max(len(v) for _, v in r['is'])
    ic = 2 if annual else 0
    isd = mapped(r['is'], MAP_IS, ic); isp = mapped(r['is'], MAP_IS, ic + 1)
    rec = {'period': period, 'fy': fy, 'q': None if annual else q,
           'sources': {'release': rl['url'], 'release_date': rl['date']}, 'notes': [],
           'is': isd, 'py': {'is': isp},
           'is_raw': [[l, v] for l, v in r['is']]}
    if not annual or q == 4:
        rec['bs'] = mapped(r.get('bs', []), MAP_BS, 0)
        rec['bs_py_yearend'] = mapped(r.get('bs', []), MAP_BS, 1)
        rec['bs_raw'] = [[l, v] for l, v in r.get('bs', [])]
    if True:
        rec['cf'] = mapped(r.get('cf', []), MAP_CF, 0); rec['cf']['ytd_months'] = 12 if annual else 3 * q
        rec['cf_py'] = mapped(r.get('cf', []), MAP_CF, 1)
        rec['cf_raw'] = [[l, v] for l, v in r.get('cf', [])]
    op = r.get('op')
    if op:
        rec['op_hdr'] = op['hdr']; rec['op_q'] = op['worldwide']; rec['op_rows'] = op.get('all_rows')
    if annual and ncols < 4: rec['notes'].append('release has no twelve-month column')
    return rec

def main():
    rel = releases()
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for (fy, q), rl in sorted(rel.items()):
        if q == 4 and 2006 <= fy <= 2025:
            rec = record(str(fy), fy, 4, rl, True)
            json.dump(rec, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
        if fy >= 2013:
            p = f'Q{q}-{str(fy)[2:]}'
            rec = record(p, fy, q, rl, False)
            json.dump(rec, open(os.path.join(OUT, f'{p}.json'), 'w'), indent=1); n += 1
    print(n, 'records')

if __name__ == '__main__':
    main()

def dps_from_filings():
    """dividends declared per share from each 10-Q / 10-K ('Dividends declared per share | 3M | 3M py | YTD | YTD py' table; earlier
    filings: the equity statement's 'dividends declared on Class A and Class B common stock, $x per share' (year to date)).
    Writes data/_dps.json: {period: {'q': three-month, 'ytd': year to date, 'url': ...}} as published (pre-split for filings
    before 22-Jan-2014)."""
    idx = json.load(open(os.path.join(S, 'period_index.json')))
    out = {}
    for k, v in idx.items():
        f = v.get('filing')
        if not f or not f.get('txt') or k.startswith('Q4'): continue
        t = open(f['txt']).read().replace('\xa0', ' ')
        rec = {'url': f['url'], 'filed': f['date']}
        if f['form'] == '10-K':
            m = re.search(r'\n(?:Cash )?[Dd]ividends declared per share(?: \d)? \| ([\d.]+)', t)
            if m: rec['ytd'] = float(m.group(1)); rec['basis'] = 'dividends declared per share (10-K)'
        else:
            m = re.search(r'\nDividends declared per share \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+)', t)
            m2 = re.search(r'\nDividends declared per share \| ([\d.]+) \| ([\d.]+)\n', t)
            if m:
                rec['q'] = float(m.group(1)); rec['ytd'] = float(m.group(3)); rec['basis'] = 'dividends declared per share table'
            elif m2 and k.startswith('Q1'):
                rec['q'] = rec['ytd'] = float(m2.group(1)); rec['basis'] = 'dividends declared per share table'
            else:
                vals = re.findall(r'dividends declared on Class A and Class B common stock, \$\s?([\d.]+) per share', t, re.I)
                if vals and f['date'] >= '2019-01-01':
                    rec['q'] = float(vals[0]); rec['basis'] = 'equity statement (three months)'
                elif vals:
                    rec['ytd'] = float(vals[0]); rec['basis'] = 'equity statement (year to date)'
        if 'ytd' in rec or 'q' in rec: out[k] = rec
    json.dump(out, open(os.path.join(OUT, '_dps.json'), 'w'), indent=1)
    print(len(out), 'DPS records')

if __name__ == '__main__' and os.environ.get('MA_DPS', '1') == '1':
    dps_from_filings()
