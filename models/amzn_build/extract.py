"""Per-period extraction of the Amazon earnings releases (8-K Item 2.02, Ex. 99.1) into data/<period>.json (EXTRACTION_SCHEMA.md).

Quarters: the three-month columns of each quarter's own release (as originally reported). Annual records FY2006-FY2025: the
twelve-month columns of the Q4 release. Prior-year comparatives (py) are the prior-year columns as presented in the same release.
Recast segment schedules (8-K Ex. 99.3 of 23-Apr-2015: AWS split out of North America for Q1-Q4 2014 and FY2013) are stored in
data/_recast.json. Every record lists its source URLs; computed values are stated in notes. Run after make_index.py / fetch.py.
"""
import csv, glob, json, os, re
from parse_release import tables, classify, col_index, bs_index, supp_index, rowmap

S = os.environ.get('AMZN_SRC', '/tmp/amzn_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
CIK = '1018724'
MON = {'March': 1, 'June': 2, 'September': 3, 'December': 4}


def url(acc, doc): return f'https://www.sec.gov/Archives/edgar/data/{CIK}/{acc.replace("-", "")}/{doc}'


def releases():
    out = []
    for r in csv.DictReader(open(os.path.join(HERE, 'filings.csv'))):
        if r['form'] != '8-K' or '2.02' not in r['items']: continue
        for ex in r['exhibits'].split(';'):
            if re.search(r'ex-?99[._-]?1|ex991|dex991', ex.lower()) and not re.search(r'99[._-]?1\d', ex.lower()):
                out.append((r['filing_date'], r['accession'], ex))
    return out


def txt_path(date, acc, doc):
    return os.path.join(S, 'txt', f'{date}_8-K_{acc}_{doc.rsplit(".", 1)[0]}.txt')


def first(m, *pats, exclude=None):
    for p in pats:
        for k, v in m.items():
            if re.search(p, k, re.I) and not (exclude and re.search(exclude, k, re.I)):
                return v, k
    return None, None


def g(m, *pats, exclude=None):
    return first(m, *pats, exclude=exclude)[0]


# ------------------------------------------------------------------ income statement
def parse_is(t, ci):
    m = rowmap(t, ci)
    o = {}
    o['rev_prod'] = g(m, r'^Net product sales')
    o['rev_serv'] = g(m, r'^Net services? sales')
    o['rev'] = g(m, r'^Total net sales$', r'^Net sales$')
    o['cogs'] = g(m, r'^Cost of sales')
    o['ful'] = g(m, r'^Fulfillment')
    o['mkt'] = g(m, r'^(Sales and )?marketing$')
    o['tech'] = g(m, r'^Technology and (content|infrastructure)$')
    o['ga'] = g(m, r'^General and administrative')
    o['othop'] = g(m, r'^Other operating expense')
    o['opex_tot'] = g(m, r'^Total operating expenses')
    o['oi'] = g(m, r'^(Income \(loss\) from operations|Income from operations|Operating income)')
    o['int_inc'] = g(m, r'^Interest income')
    ie = g(m, r'^Interest expense')
    o['int_exp'] = -ie if ie is not None else None                    # releases print interest expense negative
    o['oth_inc'] = g(m, r'^Other income \(expense\)', r'^Other income(,|$)', r'^Other expense', r'^Other income \(loss\)')
    o['remeas'] = g(m, r'^Remeasurements and other')
    o['nonop_tot'] = g(m, r'^Total non-operating')
    o['ebt'] = g(m, r'before income taxes')
    tv, tk = first(m, r'^(Benefit \(provision\)|Provision \(benefit\)|Provision for|Benefit for|Provision|Benefit)')
    o['tax_printed'] = tv
    o['equity'] = g(m, r'^Equity-method investment')
    o['cum_eff'] = g(m, r'^Cumulative effect of change')
    o['ni'] = g(m, r'^Net income')
    o['eps_b'] = g(m, r'^Basic earnings per share')
    o['eps_d'] = g(m, r'^Diluted earnings per share')
    o['sh_b'] = g(m, r'^Basic$')
    o['sh_d'] = g(m, r'^Diluted$')
    if tv is not None and None not in (o['ebt'], o['ni']):
        # the printed signs of the tax and equity-method lines vary by era (2008 prints an equity-method loss unsigned):
        # take the sign combination that ties EBT - tax + equity-method + cumulative effect = net income
        eq = o['equity'] or 0.0
        best = min(((abs(o['ebt'] - st * tv + se * eq + (o['cum_eff'] or 0) - o['ni']), st != 1, se != 1, st, se)
                    for st in (1, -1) for se in (1, -1)))
        o['tax'] = best[3] * tv
        if o['equity'] is not None: o['equity'] = best[4] * eq
    o['gp'] = g(m, r'^Gross profit')
    if o['eps_b'] is None:                       # 2006-08 releases: EPS rows are unlabeled totals (basic first, then diluted)
        unl = [v[ci] for s, l, v in t['rows'] if l == '' and ci < len(v)]
        if len(unl) >= 2: o['eps_b'], o['eps_d'] = unl[0], unl[1]
        elif o.get('cum_eff') in (None, 0.0):
            o['eps_b'] = g(m, r'^Prior to cumulative effect')
    return {k: v for k, v in o.items() if v is not None}


# ------------------------------------------------------------------ segments
SEGS = ('North America', 'International', 'AWS', 'Consolidated')


def parse_seg(t, ci):
    m = rowmap(t, ci, sections=True)
    o = {}
    for s in SEGS:
        sec = {l: v for (ss, l), v in m.items() if ss == s}
        if not sec: continue
        k = {'North America': 'na', 'International': 'intl', 'AWS': 'aws', 'Consolidated': 'tot'}[s]
        o[f'{k}_rev'] = g(sec, r'^Net sales$')
        o[f'{k}_oi'] = g(sec, r'^(Segment )?operating (income|loss)( \(loss\))?$', r'^(Segment )?operating (income|loss)', exclude=r'before')
        o[f'{k}_opex'] = g(sec, r'operating expenses')
        if s == 'Consolidated':
            o['unalloc_sbc'] = g(sec, r'^Stock-based compensation$')
            o['unalloc_oth'] = g(sec, r'^Other operating (income \(expense\)|expense)')
    return {k: v for k, v in o.items() if v is not None}


def parse_media(t, ci):
    m = rowmap(t, ci, sections=True)
    o = {}
    for s, k in (('North America', 'na'), ('International', 'intl')):
        sec = {l: v for (ss, l), v in m.items() if ss == s}
        o[f'{k}_media'] = g(sec, r'^Media$'); o[f'{k}_egm'] = g(sec, r'^Electronics'); o[f'{k}_other'] = g(sec, r'^Other')
    return {k: v for k, v in o.items() if v is not None}


GRP = [('online', r'^Online stores'), ('physical', r'^Physical stores'), ('tp', r'^Third-party seller services'),
       ('subs', r'^Subscription services'), ('ads', r'^Advertising services'), ('aws', r'^AWS'), ('other', r'^Other')]


def parse_grp(t, ci):
    m = rowmap(t, ci)
    m = {k: v for k, v in m.items() if not re.search(r'Y/Y|TTM|growth', k)}
    return {f'grp_{k}': g(m, p) for k, p in GRP if g(m, p) is not None}


# ------------------------------------------------------------------ cash flow
def parse_cf(t, ci):
    m = rowmap(t, ci)
    o = {'lines_raw': [[l, v[ci]] for s, l, v in t['rows'] if ci < len(v)]}
    o['beg'] = g(m, r'BEGINNING OF PERIOD'); o['end'] = g(m, r'END OF PERIOD')
    o['ni'] = g(m, r'^Net income')
    o['dda'] = g(m, r'^Depreciation')
    if o['dda'] is None: o['dda'] = g(m, r'^amortization$')          # Q4-12-Q2-13: the D&A label wraps onto a second line
    o['sbc'] = g(m, r'^Stock-based compensation')
    o['deftax'] = g(m, r'^Deferred income taxes')
    o['cfo'] = g(m, r'operating activities$')
    o['capex'] = g(m, r'^Purchases of (property and equipment|fixed assets)')
    o['capex_proc'] = g(m, r'^Proceeds from property and equipment')
    o['acq'] = g(m, r'^Acquisitions')
    o['sec_sales'] = g(m, r'^Sales and maturities of marketable securities')
    o['sec_purch'] = g(m, r'^Purchases of marketable securities')
    o['cfi'] = g(m, r'investing activities$')
    o['bb'] = g(m, r'^Common stock repurchased')
    debt = 0.0
    for l, v in m.items():
        if re.search(r'^(Proceeds from|Repayments of) (short-term|long-term) debt', l, re.I): debt += v
    o['debt_net'] = debt
    lease = 0.0
    for l, v in m.items():
        if re.search(r'^Principal repayments of (finance|capital)', l, re.I) or re.search(r'^Principal repayments of financing obligations', l, re.I):
            lease += v
        elif re.search(r'^Repayments of long-term debt.*(capital|finance) lease', l, re.I):
            pass                                  # 2006-2013: combined repayment line (kept in debt_net)
    o['lease_prin'] = lease
    o['fin_oblig'] = g(m, r'^Principal repayments of financing obligations') or 0.0
    o['cff'] = g(m, r'financing activities$')
    o['fx'] = g(m, r'^Foreign.currency effect')
    o['net'] = g(m, r'^Net (increase|decrease)')
    return {k: v for k, v in o.items() if v is not None}


# ------------------------------------------------------------------ balance sheet
def parse_bs(t, ci):
    m = rowmap(t, ci)
    o = {'lines_raw': [[l, v[ci]] for s, l, v in t['rows'] if ci < len(v)]}
    o['cash'] = g(m, r'^Cash and cash equivalents'); o['msec'] = g(m, r'^Marketable securities')
    o['inv'] = g(m, r'^Inventories'); o['ar'] = g(m, r'^Accounts receivable')
    o['tca'] = g(m, r'^Total current assets'); o['ppe'] = g(m, r'^(Property and equipment|Fixed assets), net')
    o['oplease'] = g(m, r'^Operating leases'); o['gw'] = g(m, r'^Goodwill'); o['ta'] = g(m, r'^Total assets')
    o['ap'] = g(m, r'^Accounts payable'); o['accr'] = g(m, r'^Accrued expenses'); o['unearned'] = g(m, r'^Unearned revenue')
    o['tcl'] = g(m, r'^Total current liabilities'); o['ltlease'] = g(m, r'^Long-term lease liabilities')
    o['cltd'] = g(m, r'^Current portion of long-term debt')                 # shown on the face only in 2008
    o['ltcap'] = g(m, r'^Long-term capital lease')
    o['ltfin'] = g(m, r'^Long-term finance lease')
    o['ltd'] = g(m, r'^Long-term debt'); o['oltl'] = g(m, r'^Other long-term liabilities')
    o['te'] = g(m, r"^Total stockholders['’] equity"); o['tle'] = g(m, r'^Total liabilities and stockholders')
    return {k: v for k, v in o.items() if v is not None}


# ------------------------------------------------------------------ supplemental (TTM FCF, shares, ex-F/X growth)
SUPP = [('fcf_ttm', r'^Free cash flow( \(operating cash flow less purchases of (fixed assets|property and equipment)\))? - TTM$'),
        ('fcf_lease_ttm', r'^Free cash flow less (lease principal repayments|principal repayments of finance leases and financing obligations)'),
        ('fcf_eq_ttm', r'^Free cash flow less (finance (principal )?lease principal repayments|equipment finance leases)'),
        ('ocf_ttm', r'^Operating cash flow'), ('sh_out', r'^Common shares outstanding'),
        ('sh_awards', r'^Common shares and stock-based awards outstanding'),
        ('fx_ww', r'^WW net sales - Y/Y growth,? excluding F/X'),
        ('employees', r'^Employees')]


def parse_supp(tabs, q, y):
    o = {}
    for t in tabs:
        ci = supp_index(t, q, y)
        if ci is None: continue
        for sec, lab, v in t['rows']:
            lab2 = re.sub(r'\s*(--|—|–)\s*', ' - ', lab)
            for k, p in SUPP:
                if k not in o and re.search(p, lab2, re.I) and ci < len(v):
                    o[k] = v[ci]
            # segment ex-F/X growth (sections North America / International / AWS)
            if re.search(r'^Net sales - Y/Y growth,? excluding F/X', lab2, re.I) and ci < len(v):
                kk = {'North America Segment': 'fx_na', 'North America': 'fx_na', 'International Segment': 'fx_intl', 'International': 'fx_intl',
                      'AWS Segment': 'fx_aws', 'AWS': 'fx_aws'}.get(sec)
                if kk and kk not in o: o[kk] = v[ci]
    return o


def period_of(is_t, date):
    """quarter from the filing month (releases: Jan/Feb = Q4 of the prior year, Apr = Q1, Jul = Q2, Oct = Q3), checked against the header."""
    y, mth = int(date[:4]), int(date[5:7])
    q, y = {1: (4, y - 1), 2: (4, y - 1), 4: (1, y), 5: (1, y), 7: (2, y), 8: (2, y), 10: (3, y), 11: (3, y)}[mth]
    h = ' '.join(is_t['hdr'])
    mo = re.search(r'Months Ended (March|June|September|December)', h)
    yrs = [int(x) for x in re.findall(r'\b(20\d\d)\b', h)]
    assert (mo is None or MON[mo.group(1)] == q) and (not yrs or max(yrs) == y), (date, h)
    return q, y


def checks(r):
    n = []
    i = r.get('is', {})
    def c(name, a, b, tol=1.01):
        if a is None or b is None: return
        if abs(a - b) > tol: n.append(f'CHECK {name}: {a:.1f} vs {b:.1f}')
    if i:
        ops = sum(i.get(k, 0) for k in ('cogs', 'ful', 'mkt', 'tech', 'ga', 'othop'))
        c('opex', ops - (i.get('cogs', 0) if i.get('gp') is not None else 0), i.get('opex_tot')); c('oi', i.get('rev', 0) - ops, i.get('oi'))
        c('ebt', i.get('oi', 0) + i.get('int_inc', 0) - i.get('int_exp', 0) + i.get('oth_inc', 0) + i.get('remeas', 0), i.get('ebt'))
        c('ni', i.get('ebt', 0) - i.get('tax', 0) + i.get('equity', 0) + i.get('cum_eff', 0), i.get('ni'))
        if i.get('rev_prod') is not None: c('rev', i['rev_prod'] + i['rev_serv'], i.get('rev'))
    s = r.get('seg', {})
    if s and i:
        c('seg rev', sum(s.get(k, 0) for k in ('na_rev', 'intl_rev', 'aws_rev')), i.get('rev'))
        c('seg oi', sum(s.get(k, 0) for k in ('na_oi', 'intl_oi', 'aws_oi', 'unalloc_sbc', 'unalloc_oth')), i.get('oi'))
    gp = r.get('grp', {})
    if gp and i: c('groups', sum(gp.values()), i.get('rev'))
    f = r.get('cf', {})
    if f:
        c('cf', f.get('cfo', 0) + f.get('cfi', 0) + f.get('cff', 0) + f.get('fx', 0), f.get('net'))
        c('cash', f.get('beg', 0) + f.get('net', 0), f.get('end'))
    b = r.get('bs', {})
    if b: c('bs', b.get('ta'), b.get('tle'))
    return n


def extract_release(date, acc, doc):
    p = txt_path(date, acc, doc)
    if not os.path.exists(p): return []
    tabs = tables(open(p).read()); d = classify(tabs)
    if not d['is']: return []
    q, y = period_of(d['is'], date)
    src = url(acc, doc)
    recs = []
    for kind in ('Q', 'A') if q == 4 else ('Q',):
        months = 3 if kind == 'Q' else 12
        key = f'Q{q}-{str(y)[2:]}' if kind == 'Q' else str(y)
        r = {'period': key, 'sources': {'release': src}, 'filed': date}
        ci = col_index(d['is'], months)
        if ci is None: continue
        r['is'] = parse_is(d['is'], ci)
        cpy = col_index(d['is'], months, 'py')
        r['py'] = {'is': parse_is(d['is'], cpy)} if cpy is not None else {}
        if d['seg']:
            cs = col_index(d['seg'], months)
            r['seg'] = parse_seg(d['seg'], cs)
            cps = col_index(d['seg'], months, 'py')
            if cps is not None: r['py']['seg'] = parse_seg(d['seg'], cps)
        if d['media']:
            r['media'] = parse_media(d['media'], col_index(d['media'], months))
        if d['grp'] and re.match(r'^Q[1-4] \d{4}', d['grp']['hdr'][0]):
            if kind == 'Q':
                cg = supp_index(d['grp'], q, y)
                if cg is not None: r['grp'] = parse_grp(d['grp'], cg)
                cp = supp_index(d['grp'], q, y - 1)
                if cp is not None: r['py']['grp'] = parse_grp(d['grp'], cp)
            else:
                cols = [supp_index(d['grp'], qq, y) for qq in (1, 2, 3, 4)]
                if None not in cols:
                    gs = [parse_grp(d['grp'], c) for c in cols]
                    r['grp'] = {k: round(sum(x.get(k) or 0.0 for x in gs), 6) for k in gs[3]}
                    r['grp_note'] = 'FY = sum of the four quarters in the Q4 release supplemental table (computed; blank = 0, e.g. physical stores before Aug-2017)'
        elif d['grp']:
            cg = col_index(d['grp'], months)
            if cg is not None:
                r['grp'] = parse_grp(d['grp'], cg)
                cpg = col_index(d['grp'], months, 'py')
                if cpg is not None: r['py']['grp'] = parse_grp(d['grp'], cpg)
        if d['cf']:
            cc = col_index(d['cf'], months)
            if cc is not None: r['cf'] = parse_cf(d['cf'], cc); r['cf']['months'] = months
        if d['bs'] and kind == 'Q' or (d['bs'] and kind == 'A'):
            r['bs'] = parse_bs(d['bs'], bs_index(d['bs']))
        r['supp'] = parse_supp(d['supp'] + d['fcf'], q, y)
        r['notes'] = '; '.join(checks(r))
        recs.append(r)
    return recs


def recast_2015():
    """8-K 23-Apr-2015 Ex. 99.3: segment information recast for the AWS segment (Q1-Q4 2014, FY2014, FY2013)."""
    for p in glob.glob(os.path.join(S, 'txt', '2015-04-23_8-K_*ex993*.txt')):
        tabs = tables(open(p).read()); d = classify(tabs)
        t = d['seg']
        hdr = [h.strip() for h in t['hdr'][0].split('|')]
        keys = []
        seen = set()
        for h in hdr:
            mo, yy = re.match(r'(\w+) \d+, (\d{4})', h).groups()
            k = f'Q{MON[mo]}-{yy[2:]}'
            if mo == 'December' and (yy, 'FY') not in seen and (yy == '2013' or k in [kk for kk, _ in keys]):
                k = yy
            if mo == 'December' and yy == '2014' and not any(kk == '2014' for kk, _ in keys): k = '2014'
            seen.add((yy, 'FY') if k.isdigit() else k)
            keys.append((k, h))
        out = {}
        for i, (k, h) in enumerate(keys):
            out[k] = parse_seg(t, i)
        acc = os.path.basename(p).split('_')[2]; doc = os.path.basename(p).split('_', 3)[3].replace('.txt', '.htm')
        return {'source': url(acc, doc), 'periods': out,
                'note': 'Segment information recast for the AWS segment (8-K 23-Apr-2015, Ex. 99.3); columns FY2014, Q4/Q3/Q2/Q1 2014, FY2013.'}


def groups_latest():
    """net sales by groups of similar products: every quarter column of every release's supplemental table, the latest release presenting
    the quarter wins (Amazon re-presents the groups, e.g. advertising services split out of Other from the Q4-21 release)."""
    out = {}
    for date, acc, doc in releases():
        p = txt_path(date, acc, doc)
        if not os.path.exists(p): continue
        d = classify(tables(open(p).read()))
        t = d['grp']
        if not t or not re.match(r'^Q[1-4] \d{4}', t['hdr'][0]): continue
        for i, h in enumerate(c.strip() for c in t['hdr'][0].split('|')):
            m = re.match(r'Q([1-4]) (\d{4})', h)
            if not m: continue
            k = f'Q{m.group(1)}-{m.group(2)[2:]}'
            vals = {kk: v for kk, v in parse_grp(t, i).items() if v is not None}
            if vals: out[k] = {'v': vals, 'source': url(acc, doc), 'filed': date}
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump(groups_latest(), open(os.path.join(OUT, '_groups.json'), 'w'), indent=1)
    allr = {}
    for date, acc, doc in releases():
        for r in extract_release(date, acc, doc):
            k = r['period']
            if k in allr: continue
            allr[k] = r
    for k, r in allr.items():
        json.dump(r, open(os.path.join(OUT, f'{k}.json'), 'w'), indent=1)
    rc = recast_2015()
    if rc: json.dump(rc, open(os.path.join(OUT, '_recast.json'), 'w'), indent=1)
    bad = {k: r['notes'] for k, r in allr.items() if r['notes']}
    print(len(allr), 'periods;', len(bad), 'with check notes')
    for k in sorted(bad): print(k, bad[k])


if __name__ == '__main__':
    main()
