"""Per-period extraction of the Booz Allen sources into data/<period>.json (schema: EXTRACTION_SCHEMA.md).

Periods: fiscal years FY2012-FY2026 (fourth-quarter release, fiscal-year column) and quarters Q1 FY2022 - Q1 FY2027 (each quarter's
own release, three-month column; cash flow year to date). Each period is taken as originally reported in its own release.
Revenue by customer comes from the 10-Q / 10-K revenue note (from FY2017, the FY2019 10-K comparatives being the first filing that
presents it); Q4 = fiscal year (10-K) - nine months (Q3 10-Q). Shares and the two-class earnings for diluted EPS come from XBRL
(as first filed); Q4 = fiscal year - nine months where only the 10-K presents the year.
Run make_index.py and fetch.py first ($BAH_SRC)."""
import csv, glob, json, os, re
from parse_release import Release
import xbrl

S = os.environ.get('BAH_SRC', '/tmp/bah_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
T = os.path.join(S, 'txt')
FIL = list(csv.DictReader(open(os.path.join(BASE, 'filings.csv'))))
URL = 'https://www.sec.gov/Archives/edgar/data/1443646/{acc}/{doc}'

def qk(y, q): return f'Q{q}-{str(y)[2:]}'

# ---------------------------------------------------------------- source documents
def release_files():
    out = {}
    for r in FIL:
        if r['form'] != '8-K' or '2.02' not in r['items']: continue
        ex = r['exhibits'].split(';')[0]
        f = glob.glob(os.path.join(T, f"{r['filing_date']}_8-K_{r['accession']}_{ex.rsplit('.', 1)[0]}.txt"))
        out[r['filing_date']] = (f[0] if f else None, URL.format(acc=r['accession'].replace('-', ''), doc=ex))
    return out

def periodic_files():
    """10-Q / 10-K by (fiscal year, quarter of the period end)."""
    out = {}
    for r in FIL:
        if r['form'] not in ('10-Q', '10-K'): continue
        end = r['period']
        y, m = int(end[:4]), int(end[5:7])
        fy = y + (1 if m >= 4 else 0)
        q = {6: 1, 9: 2, 12: 3, 3: 4}[m]
        f = glob.glob(os.path.join(T, f"{r['filing_date']}_{r['form']}_{r['accession']}_{r['primary_document'].rsplit('.', 1)[0]}.txt"))
        out[(fy, q)] = (f[0] if f else None, URL.format(acc=r['accession'].replace('-', ''), doc=r['primary_document']), r['filing_date'])
    return out

REL = release_files()
PER = periodic_files()

def release_for(fy, q):
    """the earnings release for fiscal quarter q of fiscal year fy (Q1: Jul-Aug, Q2: Oct-Nov of fy-1; Q3: Jan-Feb, Q4: May-Jun of fy)."""
    y, months = {1: (fy - 1, ('07', '08')), 2: (fy - 1, ('10', '11')), 3: (fy, ('01', '02')), 4: (fy, ('05', '06'))}[q]
    c = [d for d in sorted(REL) if d[:4] == str(y) and d[5:7] in months]
    if not c: raise KeyError((fy, q))
    return c[0]

# ---------------------------------------------------------------- field maps (label regex at the end of the entry label)
IS_F = [('rev', r'Revenue'), ('cost_rev', r'Cost of revenue'), ('bill', r'Billable expenses'),
        ('ga', r'General and administrative expenses'), ('da', r'Depreciation and amortization'),
        ('restr', r'Restructuring charges?'), ('tot_costs', r'Total operating costs and expenses'),
        ('oi', r'Operating income(?: \(loss\))?'), ('int_exp', r'Interest expense(?:, net)?'),
        ('oth', r'Other,? net|Other income \(expense\),? net|Other \(expense\) income,? net|Other income \(expense\)|Other \(expense\) income|Other income, net'),
        ('ebt', r'Income (?:\(loss\) )?before income taxes'), ('tax', r'Income tax (?:\(benefit\) )?expense(?: \(benefit\))?'),
        ('ni', r'Net income(?: \(loss\))?'), ('nci', r'Net \(income\) loss attributable to non-?controlling interests?|Net loss \(income\) attributable to non-?controlling interests?|Net income attributable to non-?controlling interests?'),
        ('ni_common', r'Net income(?: \(loss\))? attributable to common stockholders'),
        ('eps_b', r'Basic'), ('eps_d', r'Diluted'), ('dps', r'Dividends declared per share')]

BS_F = [('cash', r'Cash and cash equivalents'), ('ar', r'Accounts receivable, net(?: of allowance)?'),
        ('tca', r'Total current assets'), ('ppe', r'Property and equipment, net(?: of accumulated depreciation)?'),
        ('rou', r'Operating lease right-of-use assets'), ('intang', r'Intangible assets, net(?: of accumulated amortization)?'),
        ('gw', r'Goodwill'), ('ta', r'Total assets'), ('cltd', r'Current portion of long-term debt'),
        ('ap', r'Accounts payable and other accrued expenses'), ('acc_comp', r'Accrued compensation and benefits'),
        ('tcl', r'Total current liabilities'), ('ltd', r'Long-term debt, net of current portion'),
        ('lease_lt', r'Operating lease liabilities, net of current portion'), ('tl', r'Total liabilities'),
        ('treas', r'Treasury stock, at cost .*'), ('apic', r'Additional paid-in capital'), ('re', r'Retained earnings'),
        ('aoci', r'Accumulated other comprehensive (?:loss|income \(loss\)|loss, net of tax)'),
        ('eq', r"Total stockholders['’] equity(?: attributable to common stockholders)?|Total Booz Allen Hamilton Holding Corporation stockholders['’] equity"),
        ('nci_bs', r'Non-?controlling interests?'), ('teq', r"Total stockholders['’] equity|Total equity"),
        ('tle', r"Total liabilities and stockholders['’] equity|Total liabilities and equity")]

CF_F = [('ni', r'Net income(?: \(loss\))?'), ('da', r'Depreciation and amortization'), ('sbc', r'Stock-based compensation expense'),
        ('deftax', r'Deferred income taxes'), ('cfo', r'Net cash (?:provided by|used in|provided by \(used in\)|\(used in\) provided by) operating activities'),
        ('capex', r'Purchases of property(?:,)? (?:and )?equipment(?:,? and software)?'),
        ('acq', r'(?:Payments? for|Cash paid for) business acquisitions?,? net of cash acquired|Payments? for business acquisitions?|Cash paid for acquisitions?, net of cash acquired|Payment for business acquisition, net of cash acquired|Payments for acquisitions?, net of cash acquired|Cash paid for business acquisitions?, net of cash acquired'),
        ('cfi', r'Net cash (?:used in|provided by|\(used in\) provided by|provided by \(used in\)) investing activities'),
        ('iss', r'(?:Net )?[Pp]roceeds from issuance of common stock'), ('opt', r'Stock option exercises'),
        ('bb', r'Repurchases of common stock'), ('div', r'Cash dividends paid'),
        ('cff', r'Net cash (?:used in|provided by|\(used in\) provided by|provided by \(used in\)|provided by \(used\) in) financing activities'),
        ('net', r'Net (?:increase|decrease|increase \(decrease\)|\(decrease\) increase|decrease \(increase\)) in cash(?:,)? (?:and )?cash equivalents(?:,? and restricted cash)?'),
        ('beg', r'Cash(?:,)? (?:and )?cash equivalents(?:,? and restricted cash)?\W*beginning of (?:period|year)'),
        ('end', r'Cash(?:,)? (?:and )?cash equivalents(?:,? and restricted cash)?\W*end of (?:period|year)')]

# adjusting-item categories (company labels -> model lines)
CATS = [('TAX', r'tax effect'),
        ('AMORT', r'amortization of intangible|acquisition amortization'),
        ('SBC', r'stock-based compensation'),
        ('ACQ', r'transaction expenses|acquisition costs|acquisition and divestiture|other corporate expenses|acquisition'),
        ('RESTR', r'restructuring'),
        ('LEGAL', r'legal matter|provision for claimed|insurance recoveries|dc tax assessment'),
        ('COVID', r'covid'),
        ('DEBT', r'debt issuance|debt discount|debt extinguishment|financing transaction|original issue discount'),
        ('GAIN', r'gain|valuation adjustments? to cost method|adjustments? to cost method'),
        ('TAXD', r'tax reserves|tax credits|re-?measurement of deferred|deferred tax')]

def cat(label):
    l = label.lower()
    for c, rx in CATS:
        if re.search(rx, l): return c
    return 'OTHER'

def clean(label):
    l = re.sub(r'\s*\([a-z]\)\s*$', '', label).strip()
    return re.sub(r'^.*?(?=[A-Z][^A-Z]*$)', '', l) if len(l) > 120 else l

def block(r, start_rx, end_rx, col, scale):
    """items between the entry matching start_rx (the bridge start) and the entry matching end_rx (the published total)."""
    rows = r.rows('ng')
    i0 = None
    for i, (lab, nums) in enumerate(rows):
        if re.search(start_rx, lab, re.I) and len(nums) > col: i0 = i; break
    if i0 is None: return None
    items, total = [], None
    for lab, nums in rows[i0 + 1:]:
        if re.search(rf'(?:^|\W)(?:{end_rx})\s*(?:\([a-z]\))?$', lab, re.I):
            total = nums[col] * scale if len(nums) > col else None
            break
        if len(nums) <= col: continue
        items.append((clean(lab), round(nums[col] * scale, 6)))
    return {'start': round(rows[i0][1][col] * scale, 6), 'items': items, 'total': total}

def val(r, sec, rx, col, scale, after=None, need=None):
    nums = r.find(sec, rx, after=after, need=need or col + 1)
    return None if nums is None else round(nums[col] * scale, 6)

def ncols(r):
    nums = r.find('is', r'Revenue', need=2)
    return 4 if nums and len(nums) >= 4 else 2

def extract_release(d, col, ytd_col):
    f, url = REL[d]
    r = Release(open(f).read())
    sc = r.units('is') or 1e-3
    scn = r.units('ng') or sc
    rec = {'is': {}, 'bs': {}, 'cf': {}, 'ngaap': {}, 'op': {}}
    for k, rx in IS_F:
        v = val(r, 'is', rx, col, 1.0 if k.startswith(('eps', 'dps')) else sc)
        if v is not None: rec['is'][k] = v
    for k in ('int_exp',):
        if k in rec['is']: rec['is'][k] = -rec['is'][k]               # release shows interest as a negative
    for k, rx in BS_F:
        v = val(r, 'bs', rx, 0, r.units('bs') or sc)
        if v is not None: rec['bs'][k] = v
    for k, rx in CF_F:
        v = val(r, 'cf', rx, ytd_col, r.units('cf') or sc)
        if v is not None: rec['cf'][k] = v
    # non-GAAP
    ng = rec['ngaap']
    ng['rev_xb_pub'] = val(r, 'ng', r'Revenue, Excluding Billable Expenses\*?', col, scn)
    eb = block(r, r'(?:^|\W)Net income(?: \(loss\))?(?: attributable to common stockholders)?$', r'EBITDA', col, scn)
    ng['ebitda_bridge'] = eb
    ng['ebitda_pub'] = eb and eb['total']
    ae = block(r, r'(?:^|\W)EBITDA$', r'Adjusted EBITDA', col, scn)
    if ae: ae['items'] = [(l, v, cat(l)) for l, v in ae['items']]
    ng['adj_ebitda'] = ae
    ng['adj_ebitda_pub'] = ae and ae['total']
    ao = block(r, r'Adjusted Operating Income Operating Income(?: \(loss\))?$', r'Adjusted Operating Income', col, scn)
    if ao: ao['items'] = [(l, v, cat(l)) for l, v in ao['items']]
    ng['adj_oi'] = ao
    an = block(r, r'Adjusted Net Income Net income(?: \(loss\))?(?: attributable to common stockholders)?$', r'Adjusted Net Income', col, scn)
    if an: an['items'] = [(l, v, cat(l)) for l, v in an['items']]
    ng['adj_ni'] = an
    ng['adj_ni_pub'] = an and an['total']
    sh = r.find('ng', r'Weighted-average number of diluted shares outstanding', need=col + 1)
    ng['adj_sh'] = sh and sh[col] / 1e6
    ng['adj_eps_pub'] = val(r, 'ng', r'Adjusted Net Income Per Diluted Share', col, 1.0)
    ng['fcf_pub'] = val(r, 'ng', r'Free Cash Flow', col, scn)
    m = re.search(r'Excludes adjustments? of approximately \$?([\d.]+) million', r.flat)
    if m: ng['twoclass_note'] = float(m.group(1))
    # operating data
    op = rec['op']
    for k, rx in (('bl_funded', r'Funded'), ('bl_unfunded', r'Unfunded(?: \(\d\))?'), ('bl_options', r'Priced [Oo]ptions(?: \(\d\))?'),
                  ('bl_total', r'Total [Bb]acklog')):
        v = val(r, 'op', rx, 0, 1.0)
        if v is not None: op[k] = v
    for k, rx in (('hc_total', r'Total Headcount'), ('hc_staff', r'(?:Consulting|Client|Customer) Staff Headcount\**')):
        v = val(r, 'op', rx, 0, 1.0)
        if v is not None: op[k] = v
    b = r.find('op', r'Book-to-Bill(?: \*| \(\d\))?:?(?: Three Months Ended .*)?', need=2)
    if b:
        b = [x for x in b if x < 100]                                   # drop the header years
        op['b2b_q'] = b[0] if b else None
        if len(b) >= 3: op['b2b_ytd'] = b[2]
    for k, rx in (('ct_cr', r'Cost-Reimbursable(?: \(\d\))?'), ('ct_tm', r'Time-and-Materials'), ('ct_fp', r'Fixed-Price(?: \(\d\))?')):
        v = val(r, 'op', rx, col, 0.01)
        if v is not None: op[k] = v
    rec['sources'] = {'release': url, 'release_date': d}
    rec['units'] = 'USD thousands (converted to millions)' if sc == 1e-3 else 'USD millions'
    return rec

# ---------------------------------------------------------------- revenue by customer (10-Q / 10-K revenue note)
CUST = [('def', r'Defense (?:Clients|Customers)'), ('intel', r'Intelligence (?:Clients|Customers)'), ('civ', r'Civil (?:Clients|Customers)(?: \(\d\))?'),
        ('com', r'Global Commercial (?:Clients|Customers)'), ('ns', r'National Security(?: Customers)?'), ('cc', r'Civil and Commercial(?: Customers)?')]

def customers(fy, q):
    """{key: [values...]} from the revenue-by-customer table of the filing for (fy, q): pairs of (value, %) per column."""
    f = PER.get((fy, q))
    if not f or not f[0]: return None, None
    txt = open(f[0]).read().split('\n')
    sc = None
    out = {}
    for i, line in enumerate(txt):
        for k, rx in CUST:
            if k in out: continue
            m = re.match(rf'^{rx} \| (.*)$', line)
            if not m: continue
            cells = [c.strip().replace('%', '').strip() for c in m.group(1).split('|')]
            vals = []
            for c in cells:
                c = c.replace(',', '')
                try: vals.append(float(c))
                except ValueError: pass
            out[k] = vals[0::2]
    if not out: return None, f[1]
    n = min(len(v) for v in out.values())
    if 'ns' not in out and 'def' in out and 'intel' in out:
        out['ns'] = [out['def'][i] + out['intel'][i] for i in range(n)]
    if 'cc' not in out and 'civ' in out:
        out['cc'] = [out['civ'][i] + (out['com'][i] if 'com' in out and len(out['com']) > i else 0.0) for i in range(n)]
    big = max(v[0] for v in out.values())
    sc = 1e-3 if big > 50000 else 1.0
    return {k: [x * sc for x in v] for k, v in out.items()}, f[1]

# ---------------------------------------------------------------- XBRL (as first filed)
def xq(concept, fy, q, kind='Q'):
    return xbrl.value(concept, fy, kind, q)

def shares(fy, q, annual):
    """weighted basic / diluted shares (m) and earnings for diluted EPS (two-class, $m)."""
    if annual:
        b = xbrl.value('WeightedAverageNumberOfSharesOutstandingBasic', fy, 'FY')
        dl = xbrl.value('WeightedAverageNumberOfDilutedSharesOutstanding', fy, 'FY')
        e = xbrl.first_of(['UndistributedEarningsDiluted'], fy, 'FY')
        return b, dl, e, 'XBRL 10-K'
    if q < 4:
        b = xbrl.value('WeightedAverageNumberOfSharesOutstandingBasic', fy, 'Q', q)
        dl = xbrl.value('WeightedAverageNumberOfDilutedSharesOutstanding', fy, 'Q', q)
        e = xbrl.value('UndistributedEarningsDiluted', fy, 'Q', q)
        if b is None or dl is None or e is None:      # quarter missing from the company facts: the following year's 10-Q comparative
            b = b if b is not None else xbrl.value('WeightedAverageNumberOfSharesOutstandingBasic', fy, 'Q', q, pick='last')
            dl = dl if dl is not None else xbrl.value('WeightedAverageNumberOfDilutedSharesOutstanding', fy, 'Q', q, pick='last')
            e = e if e is not None else xbrl.value('UndistributedEarningsDiluted', fy, 'Q', q, pick='last')
            return b, dl, e, 'XBRL (not in the company facts as first filed; prior-year comparative of the following year\'s 10-Q)'
        return b, dl, e, 'XBRL 10-Q'
    fyv = [xbrl.value(c, fy, 'FY') for c in ('WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'UndistributedEarningsDiluted')]
    nm = [xbrl.value(c, fy, 'YTD', 3) for c in ('WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding', 'UndistributedEarningsDiluted')]
    q3 = [[xbrl.value(c, fy, 'Q', k) for k in (1, 2, 3)] for c in ('WeightedAverageNumberOfSharesOutstandingBasic', 'WeightedAverageNumberOfDilutedSharesOutstanding')]
    b = 4 * fyv[0] - sum(q3[0]) if fyv[0] and all(q3[0]) else None
    e = fyv[2] - nm[2] if fyv[2] is not None and nm[2] is not None else None
    return b, None, e, ('Q4: diluted shares from the release (non-GAAP exhibit, weighted-average diluted shares); basic shares derived as '
                        '4 x FY - (Q1+Q2+Q3) (XBRL); earnings for diluted EPS = FY - nine months (XBRL)')

XB = [('x_rev', ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues', 'SalesRevenueServicesNet']), ('x_oi', ['OperatingIncomeLoss']),
      ('x_ni', ['NetIncomeLoss']), ('x_eps_d', ['EarningsPerShareDiluted']), ('x_cfo', ['NetCashProvidedByUsedInOperatingActivities']),
      ('x_ta', ['Assets']), ('x_sbc', ['ShareBasedCompensation']), ('x_deftax', ['DeferredIncomeTaxExpenseBenefit']), ('x_dps', ['CommonStockDividendsPerShareCashPaid', 'CommonStockDividendsPerShareDeclared']),
      ('x_sh_out', ['CommonStockSharesOutstanding'])]

def xbrl_block(fy, q, annual, ytd_q):
    o = {}
    for k, cs in XB:
        if k in ('x_ta', 'x_sh_out'):
            v = xbrl.first_of(cs, fy, 'I', 4 if annual else q)
        elif k in ('x_cfo', 'x_sbc', 'x_deftax'):
            v = xbrl.first_of(cs, fy, 'FY') if annual else (xbrl.first_of(cs, fy, 'YTD', ytd_q) if q < 4 else xbrl.first_of(cs, fy, 'FY'))
        elif annual:
            v = xbrl.first_of(cs, fy, 'FY')
        elif q < 4:
            v = xbrl.first_of(cs, fy, 'Q', q)
        else:
            a, n = xbrl.first_of(cs, fy, 'FY'), xbrl.first_of(cs, fy, 'YTD', 3)
            v = None if a is None or n is None or k in ('x_eps_d', 'x_dps') else a - n
        if v is not None: o[k] = v
    return o

# ---------------------------------------------------------------- driver
def period_record(fy, q=None):
    annual = q is None
    d = release_for(fy, 4 if annual else q)
    rel = Release(open(REL[d][0]).read())
    nc = ncols(rel)
    col = 2 if annual else 0
    ytd_col = 0
    rec = extract_release(d, col, ytd_col)
    if annual and nc < 4: raise ValueError(f'{fy}: Q4 release without fiscal-year columns')
    p = str(fy) if annual else qk(fy, q)
    rec.update(period=p, fy=fy, q=q, notes=[])
    rec['cf']['ytd_months'] = 12 if (annual or q == 4) else 3 * q
    b, dl, e, src = shares(fy, q, annual)
    if dl is None: dl = rec['ngaap'].get('adj_sh')
    rec['is'].update(sh_b=b, sh_d=dl, earn_dil=e)
    rec['notes'].append(f'Weighted shares and earnings for diluted EPS (two-class method): {src}.')
    rec['x'] = xbrl_block(fy, q or 4, annual, q or 4)
    # customers
    if annual:
        c, u = customers(fy, 4)
        if c is None and fy in (2017, 2018):                                # first presented as FY2019 10-K comparatives
            c0, u = customers(2019, 4)
            c = {k: [v[2019 - fy]] for k, v in c0.items()} if c0 else None
            if c: rec['notes'].append(f'Revenue by customer FY{fy}: comparative column of the FY2019 10-K (first filing that presents it).')
        if c: rec['cust'] = {k: v[0] for k, v in c.items()}; rec['sources']['cust'] = u
    elif q < 4:
        c, u = customers(fy, q)
        if c: rec['cust'] = {k: v[0] for k, v in c.items()}; rec['sources']['cust'] = u
    else:
        cf_, u1 = customers(fy, 4); c9, u2 = customers(fy, 3)
        if cf_ and c9:
            rec['cust'] = {k: round(cf_[k][0] - c9[k][2], 6) for k in cf_ if k in c9 and len(c9[k]) > 2}
            rec['sources']['cust'] = [u1, u2]
            rec['notes'].append('Revenue by customer Q4 = fiscal year (10-K) - nine months (Q3 10-Q).')
    # the 10-Q / 10-K for the period
    pf = PER.get((fy, 4 if annual else q))
    if pf: rec['sources']['filing'] = pf[1]
    return rec

def run():
    os.makedirs(OUT, exist_ok=True)
    recs = []
    for y in range(2012, 2027):
        recs.append(period_record(y))
    for y in range(2022, 2028):
        for q in (1, 2, 3, 4):
            if y == 2027 and q > 1: break
            recs.append(period_record(y, q))
    for rec in recs:
        json.dump(rec, open(os.path.join(OUT, rec['period'] + '.json'), 'w'), indent=1)
    xbrl.dump_subset()
    json.dump({d: {'file': os.path.basename(f) if f else None, 'url': u} for d, (f, u) in REL.items()},
              open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    print(len(recs), 'periods')

if __name__ == '__main__':
    run()
