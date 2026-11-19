"""Per-period extraction from the CSX EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2025 (fourth-quarter release, twelve-month column) and quarters Q1/13 - Q3/26 (that quarter's
release, three-month column; Q4 from the fourth-quarter release three-month column). Each record carries:
  is     consolidated income statement (USD m; per share in $; diluted shares in m - converted from thousands where published so)
  mkt    volume (thousands of units), revenue (USD m) and revenue per unit ($) by market, labels as published (quarter / twelve-month table)
  seg    Rail / Intermodal segment detail (2006-2008 releases only)
  fuel   locomotive gallons (m), price per gallon ($), locomotive / non-locomotive / total fuel expense
  fsc    fuel surcharge revenue and fuel lag (where the release prints them)
  coal   coal tonnage (domestic / export, m tons)
  emp    average employees
  stats  revenue ton-miles (total), gross ton-miles, train velocity, dwell
  adj    special-item ("comparable" / "adjusted") reconciliation rows as printed (raw; categorised in manual_items.json / normalize.py)
  cf     condensed cash flow, year to date (cf.ytd_months)
  bs     condensed balance sheet at period end (raw lines kept)
  x      XBRL company facts (share-based compensation, D&A, cover-page shares, goodwill, receivables)
  py     prior-year comparative as presented in this release (income statement, markets) for restatement checks
  sources / notes
Release units: USD millions (shares in thousands to 2008, millions after). Everything is stored as published (no split adjustment;
normalize.py restates for the 3-for-1 split of 28-Jun-2021 by filing date).
"""
import json, os, re, datetime as dt
import parse_release as P
import xbrl

S = os.environ.get('CSX_SRC', '/tmp/csx_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '277948'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc

# ------------------------------------------------------------------ release index: (fy, q) -> release
def fyq_of_release(date):
    d = dt.date.fromisoformat(date)
    if d.month <= 2: return d.year - 1, 4
    if d.month <= 5: return d.year, 1
    if d.month <= 8: return d.year, 2
    return d.year, 3

_PCACHE = {}
def parsed(path):
    if path not in _PCACHE: _PCACHE[path] = P.parse(open(path, 'rb').read())
    return _PCACHE[path]

def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings = {}, {}
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            for doc in o['files']:
                if doc == o['primary'] or doc.lower().endswith('.txt'): continue
                p = os.path.join(S, 'docs', f"{o['date']}_8-K_{o['acc']}_{doc}")
                if not os.path.exists(p): continue
                tabs = parsed(p)
                types = {t['type'] for t in tabs}
                if not {'is', 'bs', 'cf', 'vol'} <= types: continue
                fy, q = fyq_of_release(o['date'])
                if (fy, q) not in rel:               # first full release for the quarter = as originally reported
                    rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), path=p, acc=o['acc'])
        if o['form'] in ('10-Q', '10-K'):
            e = dt.date.fromisoformat(o['report'])
            fy = e.year; q = {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3, 12: 4}[e.month]
            filings[(fy, q)] = dict(date=o['date'], url=url(o, o['primary']), form=o['form'])
    return rel, filings

# ------------------------------------------------------------------ helpers
def split_blocks(t):
    """a release table can hold the quarter and the year-to-date schedule: split at in-table year / caption rows."""
    blocks, cur = [], {'hdr': list(t['hdr']), 'rows': []}
    for lab, vals in t['rows']:
        if not vals and (re.search(r'(19|20)\d\d', lab) or re.search(r'months ended|quarters? ended|years? ended|six months|nine months|full year', lab, re.I)) and cur['rows']:
            blocks.append(cur); cur = {'hdr': [lab], 'rows': []}
        elif not vals and cur['rows'] and re.search(r'^(volume \| revenue|rail|csx corporation)', lab, re.I):
            continue
        else:
            cur['rows'].append((lab, vals))
    blocks.append(cur)
    return blocks

def pick(vals, n_blocks, which):
    """which: 'cur' | 'py' | 'ytd' | 'ytd_py' from a row whose columns are [cur, py, (changes...)] x n_blocks."""
    if not vals: return None
    if n_blocks == 1:
        return {'cur': vals[0], 'py': vals[1] if len(vals) > 1 else None}.get(which)
    L = len(vals)
    if L in (2,): return {'cur': vals[0], 'py': vals[1]}.get(which)
    if L == 4: return {'cur': vals[0], 'py': vals[1], 'ytd': vals[2], 'ytd_py': vals[3]}[which]
    b = L // 2
    return {'cur': vals[0], 'py': vals[1], 'ytd': vals[b], 'ytd_py': vals[b + 1]}[which]

IS_MAP = [('rev', r'revenue$'), ('labor', r'labor and fringe'), ('mso', r'materials, supplies and other|purchased services and other'),
          ('fuel', r'^fuel'), ('dep', r'^depreciation'), ('rents', r'equipment and other rents'), ('inland', r'inland transportation'),
          ('conrail', r'conrail rents'), ('restr', r'restructuring'), ('impair', r'goodwill impairment'), ('gain_disp', r'gain on property disposition'),
          ('tot_exp', r'total expense'), ('st_oi', r'surface transportation operating income'), ('oth_oi', r'other operating income'),
          ('oi', r'^operating income$'), ('oth_inc', r'^other (\(expense\) ?/?|\(expense\) )?income|^other income'), ('debt_rep', r'debt repurchase expense'), ('int_exp', r'^interest expense'),
          ('ebt', r'before income taxes'), ('tax', r'^income tax'), ('cont_ops', r'^earnings from continuing operations$'),
          ('disc_ops', r'^discontinued operations'), ('ni', r'^net earnings$'), ('op_margin', r'^operating margin'),
          ('sh_d', r'average (diluted )?(common )?shares outstanding'), ('dps', r'cash dividends')]
SKIP_IS = r'per share|per common share|assuming dilution'

def ext_is(t, which):
    yrs = P.years_in(t); nb = 2 if len(yrs) >= 4 else 1
    out, other, eps, state, pend = {}, [], {}, 'pre', ''
    for lab, vals in t['rows']:
        L = re.sub(r'\(note [a-z]\)|\([a-z]\)', '', lab.lower()).strip(' :*')
        L = re.sub(r'^(transportation|consolidated)\s+', '', L); L = re.sub(r'^consolidated\s+', '', L)
        L = re.sub(r'^surface (?!transportation)', '', L)
        if pend and state == 'eps': L = pend + ' ' + L; pend = ''
        if not vals:
            if 'per share' in L or 'per common share' in L or 'per share data' in L: state = 'eps'
            if state == 'eps' and not re.search(r'per share|dilution', L): pend = L
            continue
        if state == 'eps' or re.search(r'per share|assuming dilution', L):
            if re.search(r'average|shares outstanding|^outstanding', L):
                out['sh_d'] = pick(vals, nb, which); out['sh_unit'] = 'thousands' if 'thousand' in L else 'millions'; continue
            if re.search(r'dividend', L): out['dps'] = pick(vals, nb, which); continue
            k = 'eps_cont' if 'continuing' in L else ('eps_disc' if 'discontinued' in L else 'eps_d')
            if k not in eps: eps[k] = pick(vals, nb, which)
            continue
        key = next((k for k, p in IS_MAP if re.search(p, L)), None)
        if key == 'rev' and state == 'pre': state = 'costs'
        if key == 'tot_exp': state = 'post'
        if key and key not in out:
            out[key] = pick(vals, nb, which)
            if key == 'sh_d': out['sh_unit'] = 'thousands' if 'thousand' in L else 'millions'
        elif state == 'costs' and not key:
            other.append([lab, pick(vals, nb, which)])
    out.update(eps)
    out['other_exp_lines'] = other
    return out

def ext_rows(t, which, nb=None):
    yrs = P.years_in(t); nb = nb or (2 if len(yrs) >= 4 else 1)
    return [[lab, pick(vals, nb, which)] for lab, vals in t['rows'] if vals]

def ext_vol(block, which):
    """market rows -> [label, vol, rev, rpu] for cur / py (columns: vol cur, vol py, %, rev cur, rev py, %, rpu cur, rpu py, %)."""
    out = []
    for lab, vals in block['rows']:
        if not vals: continue
        if len(vals) == 9:
            i = 0 if which == 'cur' else 1
            out.append([lab, vals[i], vals[3 + i], vals[6 + i]])
        elif len(vals) == 6:          # no revenue-per-unit columns (older "Other" lines)
            i = 0 if which == 'cur' else 1
            out.append([lab, vals[i], vals[3 + i], None])
    return out

CF_MAP = [('ni', r'^net earnings'), ('dep', r'^depreciation'), ('deftax', r'deferred income tax'), ('impair', r'goodwill impairment'),
          ('cfo', r'^net cash provided by operating'), ('capex', r'^property additions'), ('sti_buy', r'purchases? of short-term investments'),
          ('sti_sell', r'proceeds from sales of short-term investments'), ('disp', r'proceeds (and advances )?from property dispositions'),
          ('acq', r'business acquisitions?|acquisition'), ('cfi', r'^net cash .*investing'),
          ('bb', r'^shares repurchased'), ('div', r'^dividends paid'), ('debt_iss', r'long-term debt issued'), ('debt_rep', r'long-term debt repaid'),
          ('std_net', r'short-term debt - net|commercial paper'), ('options', r'stock options exercised'),
          ('cff', r'^net cash .*financing'),
          ('net', r'^net .*in cash'), ('beg', r'beginning of'), ('end', r'end of')]

def ext_cf(t, mo):
    out, raw = {'ytd_months': mo}, []
    for lab, vals in t['rows']:
        if not vals: continue
        v = vals[0]; raw.append([lab, v])
        L = re.sub(r'\([a-z]\)', '', lab.lower()).strip()
        L = re.sub(r'^(operating activities|investing activities|financing activities|cash and cash equivalents|cash and cash)\s+', '', L)
        for k, p in CF_MAP:
            if re.search(p, L):
                if k == 'acq' and 'minority' in L: break
                if k in out: break
                out[k] = v; break
    out['lines_raw'] = raw
    return out

BS_MAP = [('cash_sti', r'^cash, cash equivalents and short-term investments'), ('cash', r'^cash and cash equivalents'), ('sti', r'^short-term investments'), ('ar', r'^accounts receivable'), ('tca', r'^total current assets'),
          ('ppe_gross', r'^properties$'), ('accdep', r'^accumulated depreciation'), ('ppe', r'^properties - net'), ('conrail', r'^investment in conrail'),
          ('affil', r'^(investment in )?affiliates and other'), ('olta', r'^other long-term assets'), ('ta', r'^total assets'),
          ('cmltd', r'^current maturities of long-term debt'), ('std', r'^short-term debt'), ('tcl', r'^total current liabilities'),
          ('ltd', r'^long-term debt'), ('dit', r'^deferred income taxes( - net)?$'), ('oltl', r'^other long-term liabilities'), ('tl', r'^total liabilities$'),
          ('nci', r'noncontrolling'), ('te', r"^total shareholders['’] equity"), ('tle', r"^total liabilities and shareholders")]

def ext_bs(t):
    out, raw, section = {}, [], 'a'
    for lab, vals in t['rows']:
        L = re.sub(r"^(assets|liabilities and|shareholders['’] equity|liabilities)\s+", '', lab.lower()).strip(' :')
        if not vals:
            if 'liabilit' in L: section = 'l'
            continue
        v = vals[0]; raw.append([lab, v])
        if re.search(r'^total current liabilities|^liabilities and', L): section = 'l'
        for k, p in BS_MAP:
            if re.search(p, L):
                if k == 'dit' and section == 'a': k = 'dta_cur'
                if k not in out: out[k] = v
                break
        if re.search(r'^total assets', L): section = 'l'
    out['lines_raw'] = raw
    return out

def ext_misc(tabs, which, nb_default):
    o = {}
    for t in tabs:
        ty = t['type']
        if ty == 'fuel':
            o['fuel'] = {}
            for k, rx in (('gallons', r'gallons'), ('ppg', r'price per gallon'), ('loco', r'^(total )?locomotive fuel expense'),
                          ('nonloco', r'non-locomotive'), ('total', r'^total fuel expense')):
                lab, vals = P.row(t, rx)
                if vals: o['fuel'][k] = pick(vals, 2 if len(P.years_in(t)) >= 4 else 1, which)
        elif ty == 'fsc':
            o['fsc'] = {}
            for k, rx in (('fsc', r'fuel surcharge revenue'), ('lag', r'fuel lag')):
                lab, vals = P.row(t, rx)
                if vals: o['fsc'][k] = pick(vals, 2 if len(P.years_in(t)) >= 4 else 1, which)
        elif ty == 'coal' and 'coal' not in o:
            o['coal'] = {}
            for k, rx in (('domestic', r'^(total )?domestic'), ('export', r'^export'), ('total', r'^total coal')):
                lab, vals = P.row(t, rx)
                if vals: o['coal'][k] = pick(vals, 2 if len(P.years_in(t)) >= 4 else 1, which)
        elif ty == 'emp' and 'emp' not in o:
            lab, vals = P.row(t, r'^total')
            if vals: o['emp'] = {'avg_total': pick(vals, 2 if len(P.years_in(t)) >= 4 else 1, which)}
        elif ty == 'stats':
            s = o.setdefault('stats', {})
            for k, rx in (('rtm', r'^total revenue ton-miles|^total$'), ('gtm', r'gross ton-miles'), ('velocity', r'train velocity'), ('dwell', r'^dwell'),
                          ('cars_online', r'cars.online'), ('fuel_eff', r'fuel efficiency'), ('fra_inj', r'personal injur'), ('fra_acc', r'train accident')):
                lab, vals = P.row(t, rx)
                if vals and k not in s: s[k] = pick(vals, 2 if len(P.years_in(t)) >= 4 else 1, which)
    return o

# ------------------------------------------------------------------ build records
def rec_period(rel, filings, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    tabs = parsed(r['path'])
    which = 'ytd' if annual else 'cur'
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'sources': {'release': r['url'], 'release_date': r['date']}, 'notes': []}
    is_t = next(t for t in tabs if t['type'] == 'is')
    if annual and len(P.years_in(is_t)) < 4:
        rec['notes'].append('Fourth-quarter release shows no twelve-month column'); return None
    rec['is'] = ext_is(is_t, which)
    rec['is']['other_exp_lines'] = [[l, v] for l, v in rec['is']['other_exp_lines'] if v is not None]
    # markets: quarter block first, year-to-date block second
    vol = [b for t in tabs if t['type'] == 'vol' for b in split_blocks(t)]
    vol = [b for b in vol if any(len(v) >= 6 for _, v in b['rows'])]
    def vtot(b):
        for l, v in b['rows']:
            if re.match(r'^total( surface transportation)?( \([a-z]\))?$', l.strip().lower()) and len(v) >= 6: return v[3]
    rv = rec['is'].get('rev')
    match = [b for b in vol if rv is not None and vtot(b) is not None and abs(vtot(b) - rv) < 0.5]
    vb = match[0] if match else (vol[-1] if annual else vol[0])
    if not match: rec['notes'].append('Volume table total does not match revenue; block chosen by position')
    if annual and len(vol) < 2: rec['notes'].append('Only one volume table in the fourth-quarter release (quarter)'); vb = None
    if vb: rec['mkt'] = ext_vol(vb, 'cur'); rec['mkt_hdr'] = vb['hdr'][:3]
    segs = [b for t in tabs if t['type'] == 'seg' for b in split_blocks(t)]
    if segs:
        sb = segs[-1] if annual else segs[0]
        rec['seg'] = {}
        for k, rx in (('rev', r'^revenue'), ('oi', r'operating income$'), ('or', r'operating ratio')):
            lab, vals = P.row(sb, rx)
            if vals and len(vals) >= 6: rec['seg'][k] = {'rail': vals[0], 'intermodal': vals[2], 'total': vals[4]}
    rec.update(ext_misc(tabs, which, None))
    cf_t = next(t for t in tabs if t['type'] == 'cf')
    rec['cf'] = ext_cf(cf_t, 12 if annual else 3 * q)
    rec['bs'] = ext_bs(next(t for t in tabs if t['type'] == 'bs'))
    adj = [t for t in tabs if t['type'] == 'adj']
    if adj: rec['adj_raw'] = [{'hdr': t['hdr'][:4], 'rows': [[l, v] for l, v in t['rows'] if v]} for t in adj]
    fcf = next((t for t in tabs if t['type'] == 'fcf'), None)
    if fcf:
        lab, vals = P.row(fcf, r'^free cash flow')
        if vals: rec['fcf_pub'] = vals[0]
    f = filings.get((fy, 4 if annual else q))
    if f: rec['sources']['filing'] = f['url']
    # prior-year comparative as presented in this release
    rec['py'] = {'is': ext_is(is_t, 'ytd_py' if annual else 'py')}
    rec['py']['is']['other_exp_lines'] = [[l, v] for l, v in rec['py']['is']['other_exp_lines'] if v is not None]
    if vb: rec['py']['mkt'] = ext_vol(vb, 'py')
    # XBRL extras (10-K / 10-Q, as first filed)
    kind = 'FY' if annual else 'Q'
    cs = xbrl.cover_shares(fy, 4 if annual else q)
    rec['x'] = {'sbc': xbrl.first_of(['AllocatedShareBasedCompensationExpense'], fy, kind, q),
                'dda': xbrl.first_of(['DepreciationDepletionAndAmortization', 'Depreciation'], fy, kind, q),
                'deftax_ytd': xbrl.first_of(['DeferredIncomeTaxExpenseBenefit'], fy, 'FY' if annual else 'YTD', q),
                'goodwill': xbrl.value('Goodwill', fy, 'I', 4 if annual else q),
                'intang_gw': xbrl.first_of(['IntangibleAssetsNetIncludingGoodwill'], fy, 'I', 4 if annual else q),
                'ar': xbrl.value('AccountsReceivableNetCurrent', fy, 'I', 4 if annual else q),
                'sh_out_cover': cs[0] if cs else None, 'sh_out_cover_date': cs[1] if cs else None,
                'sh_out': xbrl.value('CommonStockSharesOutstanding', fy, 'I', 4 if annual else q),
                'oi': xbrl.value('OperatingIncomeLoss', fy, kind, q), 'ni': xbrl.value('NetIncomeLoss', fy, kind, q),
                'rev': xbrl.first_of(['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, kind, q),
                'eps_d': xbrl.value('EarningsPerShareDiluted', fy, kind, q), 'ta': xbrl.value('Assets', fy, 'I', 4 if annual else q),
                'cfo_ytd': xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, 'FY' if annual else 'YTD', q),
                'employees': xbrl.value('EntityNumberOfEmployees', fy, 'I', 4) if annual else None}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings = release_index()
    idx = [{'fy': fy, 'q': q, 'date': r['date'], 'url': r['url']} for (fy, q), r in sorted(rel.items())]
    json.dump(idx, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    n = 0
    for fy in range(2006, 2026):
        r = rec_period(rel, filings, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
        else: print('missing annual', fy)
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if (fy, q) > (2026, 3): break
            r = rec_period(rel, filings, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
            else: print('missing quarter', fy, q)
    xbrl.dump_subset()
    print(n, 'period files;', len(rel), 'releases indexed')

if __name__ == '__main__':
    main()
