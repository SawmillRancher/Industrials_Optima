"""Per-period extraction from the Woodward EDGAR sources into data/<period>.json.

Periods: annual FY2011-FY2025 (fourth-quarter release, twelve-month column) and quarters Q1 FY21 - Q3 FY26 (that quarter's
release, three-month column; Q4 from the fourth-quarter release three-month column). Each record carries:
  is     statement of earnings (USD m; per share in $; shares in m)
  seg    segment net sales / earnings, nonsegment expenses, EBIT (segment schedule)
  em     sales by primary market (10-Q / 10-K revenue-disaggregation note; Q4 = FY - 9M, noted)
  ngaap  EBIT / EBITDA / adjusted measures, adjusting items (company labels, category), free cash flow
  cf     cash flow, year to date (cf.ytd_months)
  bs     balance sheet at period end
  x      XBRL company facts (share-based compensation, deferred income taxes, shares issued less treasury shares)
  py     prior-year comparative as presented in this release (for restatement checks)
  sources / notes
Release units are thousands; everything is stored in millions (per share as published). Woodward's fiscal year ends
30 September (FY2026 = Oct-2025 - Sep-2026).
"""
import json, glob, os, re, datetime as dt
import parse_release as P
import xbrl

S = os.environ.get('WWD_SRC', '/tmp/wwd_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '108312'
ARCH = 'https://www.sec.gov/Archives/edgar/data/108312/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc
def m(v): return None if v is None else round(v / 1000.0, 6)

# ------------------------------------------------------------------ release index: (fy, q) -> release
def fyq_of_release(date):
    d = dt.date.fromisoformat(date)
    if d.month >= 10: return d.year, 4
    if d.month <= 3: return d.year, 1
    if d.month <= 6: return d.year, 2
    return d.year, 3

def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings = {}, {}
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            for doc in o['files']:
                if doc == o['primary']: continue
                p = os.path.join(S, 'docs', f"{o['date']}_8-K_{o['acc']}_{doc}")
                if not os.path.exists(p): continue
                tabs = P.parse(open(p, 'rb').read())
                types = {t['type'] for t in tabs}
                if not {'is', 'bs', 'seg'} <= types: continue
                fy, q = fyq_of_release(o['date'])
                if (fy, q) not in rel:               # first full release for the quarter = as originally reported
                    rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), tabs=tabs)
        if o['form'] in ('10-Q', '10-K'):
            e = dt.date.fromisoformat(o['report'])
            fy = e.year + (1 if e.month >= 10 else 0)
            q = {12: 1, 3: 2, 6: 3, 9: 4}[e.month]
            filings[(fy, q)] = dict(date=o['date'], url=url(o, o['primary']), path=os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{o['primary']}"), form=o['form'])
    return rel, filings

# ------------------------------------------------------------------ section extractors
IS_MAP = [('rev', r'^net sales$'), ('cogs', r'^cost of goods sold'), ('sga', r'^selling, general'), ('rd', r'^research and development'),
          ('amort', r'^amortization of intangible'), ('restr', r'^restructuring'), ('int_exp', r'^interest expense'), ('int_inc', r'^interest income'),
          ('oth', r'^other (\(income\) expense|income|expense|\(income\)),? ?(\(income\))?,? ?net'), ('tot_costs', r'^total costs and expenses'),
          ('ebt', r'^(consolidated )?earnings before income taxes'), ('tax', r'^income tax(es| expense)'),
          ('ni_tot', r'^net earnings( \(loss\))?$|^net earnings including'), ('nci', r'noncontrolling interests'),
          ('ni', r'^net earnings attributable to woodward|^net earnings$'),
          ('eps_b', r'^basic earnings per share'), ('eps_d', r'^diluted earnings per share'),
          ('sh_b', r'^basic$'), ('sh_d', r'^diluted$'), ('dps', r'^cash dividends.*per share')]
PS = {'eps_b', 'eps_d', 'dps'}

def ext_is(tabs, mo, cp):
    t = next((t for t in tabs if t['type'] == 'is' and any(c[0] == mo and c[1] == cp for c in t['cols'])), None)
    if not t: return None
    ci = next(i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp)
    out, other, state = {}, [], 'pre'
    for lab, vals in t['rows']:
        if not vals or ci >= len(vals): continue
        L = lab.lower().strip(' :*')
        v = vals[ci]
        key = next((k for k, p in IS_MAP if re.search(p, L)), None)
        if key == 'ni' and 'ni' in out and L == 'net earnings': continue
        if key and key not in out:
            out[key] = v if key in PS else round(v / 1000.0, 6)
            if key == 'rev': state = 'costs'
            if key == 'tot_costs': state = 'post'
        elif state == 'costs' and not key:
            other.append([lab, round(v / 1000.0, 6)])
    if 'ni' not in out and 'ni_tot' in out: out['ni'] = out['ni_tot']
    out['other_lines'] = other
    return out

def ext_seg(tabs, mo, cp):
    t = next((t for t in tabs if t['type'] == 'seg' and any(c[0] == mo and c[1] == cp for c in t['cols'])), None)
    if not t: return None
    ci = next(i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp)
    out, seen = {}, {}
    for lab, vals in t['rows']:
        if not vals or ci >= len(vals): continue
        L = lab.lower().strip(' :*')
        v = vals[ci] / 1000.0
        mm = re.match(r'^(aerospace|energy|industrial)( segment)?$', L)
        if mm:
            s = 'ind' if mm.group(1) in ('energy', 'industrial') else 'aero'
            n = seen.get(s, 0); seen[s] = n + 1
            out[('sales_' if n == 0 else 'earn_') + s] = round(v, 6)
            if s == 'ind': out['ind_name'] = mm.group(1).title()
        elif L.startswith('total consolidated net sales') or L == 'total net sales': out['sales_tot'] = round(v, 6)
        elif L.startswith('total segment earnings'): out['earn_tot'] = round(v, 6)
        elif L.startswith('nonsegment'): out['nonseg'] = round(v, 6)
        elif L == 'ebit' or L.startswith('ebit '): out['ebit'] = round(v, 6)
        elif L.startswith('interest expense, net'): out['int_net'] = round(v, 6)
        elif L.startswith('payments for property'): out['capex'] = round(v, 6)
        elif L.startswith('depreciation'): out['dep'] = round(v, 6)
    return out

def val(tabs, ty, rx, mo, cp, meas='v', exclude=None):
    v = P.get(tabs, ty, rx, mo, cp, meas, exclude=exclude)
    return None if v is None else round(v / 1000.0, 6)

CAT = [('TAXD', r'corporate tax rate|tax legislation|tax reform|discrete tax|tax law|valuation allowance|tax (benefit|charge|item)s? (related|associated)|change in tax'),
       ('TAX', r'tax effect'),
       ('RESTR', r'restructur|workforce|facility rationali|special charge'),
       ('AMORT', r'backlog amortization|amortization'),
       ('STEPUP', r'step[- ]up|inventory fair value|purchase accounting'),
       ('IMPAIR', r'impairment|senvion'),
       ('GAIN', r'gain|loss on sale|sale of|product rationali|divestiture of|business divest'),
       ('SWAP', r'cross[- ]currency|swap'),
       ('PENSION', r'pension'),
       ('ACQ', r'merger|acquisition|transaction|integration|business development|warranty and indemnity|real estate transfer|duarte|move related|other charges|separation|strategic'),
       ('LEGAL', r'legal|litigation|settlement')]
def cat(lab):
    L = lab.lower()
    return next((c for c, p in CAT if re.search(p, L)), 'OTHER')

def ext_adj(tabs, mo, cp):
    """adjusted-earnings reconciliation for one period column block -> dict (USD m; per share $)."""
    for t in tabs:
        if t['type'] != 'adj': continue
        cols = [(i, c[2]) for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not cols: continue
        ms = {mm: i for i, mm in cols}
        fmt = 'a' if 'pre' in ms else ('b' if 'ps' in ms else 'v')
        rows = [(l, v) for l, v in t['rows'] if v]
        if not rows or not re.search(r'earnings \(u\.s\. gaap\)|^net earnings', rows[0][0], re.I): continue
        def g(vals, mm):
            i = ms.get(mm)
            return vals[i] if i is not None and i < len(vals) else None
        out = {'fmt': fmt, 'items': []}
        st = rows[0][1]
        out['gaap_ni'] = m(g(st, 'net') if fmt != 'v' else g(st, 'v'))
        if fmt == 'a': out['gaap_ebt'] = m(g(st, 'pre'))
        out['gaap_eps'] = g(st, 'ps')
        for lab, vals in rows[1:]:
            L = lab.lower()
            if re.match(r'adjusted (net )?earnings', L):
                out['adj_ni'] = m(g(vals, 'net') if fmt != 'v' else g(vals, 'v')); out['adj_eps'] = g(vals, 'ps')
                if fmt == 'a': out['adj_ebt'] = m(g(vals, 'pre'))
                break
            if re.match(r'(sub[- ]?total|total) non', L):
                key = 'subtotal' if 'sub' in L else 'total'
                out[key] = {'pre': m(g(vals, 'pre')), 'net': m(g(vals, 'net') if fmt != 'v' else g(vals, 'v')), 'ps': g(vals, 'ps')}
                continue
            if L.startswith('non-u.s. gaap adjustments') and fmt == 'a':
                out['subtotal'] = {'pre': m(g(vals, 'pre')), 'net': m(g(vals, 'net')), 'ps': g(vals, 'ps')}; continue
            c = cat(lab)
            if fmt == 'a': it = {'label': lab, 'pre': m(g(vals, 'pre')), 'net': m(g(vals, 'net')), 'ps': g(vals, 'ps'), 'cat': c}
            else:
                amt = m(g(vals, 'net') if fmt == 'b' else g(vals, 'v'))
                if c in ('TAX', 'TAXD'): it = {'label': lab, 'pre': 0.0, 'net': amt, 'ps': g(vals, 'ps'), 'cat': c}
                else: it = {'label': lab, 'pre': amt, 'net': None, 'ps': g(vals, 'ps'), 'cat': c}
            out['items'].append(it)
        if 'adj_ni' in out: return out
    return None

def ext_ngaap(tabs, mo, cp):
    o = {}
    for ty in ('ebit', 'ebitda'):
        for k, rx in (('ebit_pub', r'^ebit\b(?!da)'), ('adj_ebit_pub', r'^adjusted ebit\b(?!da)')):
            if o.get(k) is None: o[k] = val(tabs, ty, rx, mo, cp)
    o['ebitda_pub'] = val(tabs, 'ebitda', r'^ebitda', mo, cp)
    o['adj_ebitda_pub'] = val(tabs, 'ebitda', r'^adjusted ebitda', mo, cp)
    o['dep'] = val(tabs, 'ebitda', r'^depreciation', mo, cp)
    o['amort'] = val(tabs, 'ebitda', r'^amortization', mo, cp)
    o['ebitda_adj_tot'] = val(tabs, 'ebitda', r'non-u\.s\. gaap adjustments', mo, cp)
    o['ebit_adj_tot'] = val(tabs, 'ebit', r'non-u\.s\. gaap adjustments', mo, cp)
    o['fcf_pub'] = val(tabs, 'fcf', r'^free cash (flow|inflow)(?! excluding)', mo, cp)
    o['adj_fcf_pub'] = val(tabs, 'fcf', r'^adjusted free cash flow', mo, cp)
    o['nonseg_pub'] = val(tabs, 'nonseg', r'^nonsegment expenses', mo, cp)
    o['adj_nonseg_pub'] = val(tabs, 'nonseg', r'^adjusted nonsegment', mo, cp)
    for s, nm in (('ind', r'industrial'), ('aero', r'aerospace')):
        g_ = val(tabs, 'adjseg', rf'^{nm} segment earnings', mo, cp)
        a_ = val(tabs, 'adjseg', rf'^adjusted {nm} segment earnings(?! excluding)', mo, cp)
        if a_ is not None: o[f'adj_seg_{s}'] = a_; o[f'gaap_seg_{s}'] = g_
    o['adj_tax_pub'] = val(tabs, 'tax', r'^adjusted income tax expense', mo, cp)
    a = ext_adj(tabs, mo, cp)
    if a: o['adj'] = a
    return {k: v for k, v in o.items() if v is not None}

CF_MAP = [('cfo', r'^net cash .*operating'), ('capex', r'^payments for (purchase of )?property'),
          ('acq', r'^(business )?acquisitions?|^payments for (business )?acquisitions'), ('divest', r'divestiture|sale of business|sale of the renewable|proceeds from (the )?sale of businesses'),
          ('cfi', r'^net cash .*investing'),
          ('div', r'^cash dividends paid'), ('stock_iss', r'^proceeds from sales of treasury|^proceeds from exercise'), ('bb', r'^payments for repurchases'),
          ('cff', r'^net cash .*financing'),
          ('fx', r'^effect of exchange rate'), ('net', r'^net (change|increase|decrease|\(decrease\) increase|increase \(decrease\)) in cash'),
          ('beg', r'beginning of'), ('end', r'end of')]

def ext_cf(tabs, mo, cp):
    t = next((t for t in tabs if t['type'] == 'cf' and any(c[0] == mo and c[1] == cp for c in t['cols'])), None)
    if not t: return None
    ci = next(i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp)
    out, raw = {'ytd_months': mo}, []
    for lab, vals in t['rows']:
        if not vals or ci >= len(vals): continue
        v = round(vals[ci] / 1000.0, 6); raw.append([lab, v])
        L = lab.lower()
        for k, p in CF_MAP:
            if re.search(p, L):
                if k in ('acq', 'divest'): out[k] = round(out.get(k, 0.0) + v, 6)
                elif k not in out: out[k] = v
                break
    out['lines_raw'] = raw
    return out

BS_MAP = [('cash', r'^cash and cash equivalents'), ('ar', r'^accounts receivable'), ('inv', r'^inventories'), ('tca', r'^total current assets'),
          ('ppe', r'^property, plant,? and equipment'), ('gw', r'^goodwill'), ('intang', r'^intangible assets'), ('ta', r'^total assets'),
          ('std', r'^short-term (borrowings|debt)'), ('cltd', r'^current portion of long-term debt'), ('ap', r'^accounts payable'),
          ('tcl', r'^total current liabilities'), ('ltd', r'^long-term debt'), ('tl', r'^total liabilities$'),
          ('nci', r'noncontrolling interests?$'), ('eq', r"^(total )?stockholders['’] equity|^total woodward stockholders"), ('te', r'^total equity'),
          ('tle', r"^total liabilities and (stockholders['’] )?equity")]

def ext_bs(tabs, cp='cur'):
    t = next((t for t in tabs if t['type'] == 'bs'), None)
    if not t: return None
    ci = 0 if cp == 'cur' else 1
    out, raw = {}, []
    for lab, vals in t['rows']:
        if not vals or ci >= len(vals): continue
        v = round(vals[ci] / 1000.0, 6); raw.append([lab, v])
        L = lab.lower().strip(' :')
        for k, p in BS_MAP:
            if re.search(p, L):
                if k not in out: out[k] = v
                break
    if 'te' in out and 'eq' not in out: out['eq'] = out['te']
    out['lines_raw'] = raw
    return out

# ------------------------------------------------------------------ end markets (10-Q / 10-K revenue disaggregation note)
EM = [('com_oem', r'^commercial oem'), ('com_aft', r'^commercial (aftermarket|services)'), ('def_oem', r'^defense oem'),
      ('def_aft', r'^defense (aftermarket|services)'), ('aero_tot', r'^total aerospace'),
      ('pg', r'^power generation'), ('trans', r'^transportation'), ('og', r'^oil and gas'),
      ('recip', r'^reciprocating engines'), ('ind_turb', r'^industrial turbines'), ('renew', r'^renewables'),
      ('ind_tot', r'^total industrial')]
_EMCACHE = {}
def em_tables(path):
    if path not in _EMCACHE:
        tabs = []
        if os.path.exists(path):
            for t in P.html_tables(open(path, 'rb').read()):
                labs = ' '.join(l.lower() for l, _ in t['rows'])
                if 'commercial oem' in labs or 'total industrial segment net sales' in labs:
                    cols = P.columns(t)
                    if cols: tabs.append(dict(t, cols=cols))
        _EMCACHE[path] = tabs
    return _EMCACHE[path]

def ext_em(path, mo, cp='cur'):
    out = {}
    for t in em_tables(path):
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        for lab, vals in t['rows']:
            if not vals or idx[0] >= len(vals): continue
            L = lab.lower()
            for k, p in EM:
                if re.search(p, L) and k not in out:
                    out[k] = round(vals[idx[0]] / 1000.0, 6); break
    return out

# ------------------------------------------------------------------ build records
def rec_period(rel, filings, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    tabs = r['tabs']
    mo = 12 if annual else 3
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'sources': {'release': r['url'], 'release_date': r['date']}, 'notes': []}
    rec['is'] = ext_is(tabs, mo, 'cur')
    rec['seg'] = ext_seg(tabs, mo, 'cur')
    rec['ngaap'] = ext_ngaap(tabs, mo, 'cur')
    ytd = 12 if annual else 3 * q
    rec['cf'] = ext_cf(tabs, ytd, 'cur')
    rec['bs'] = ext_bs(tabs, 'cur')
    f = filings.get((fy, 4 if annual else q))
    if f:
        rec['sources']['filing'] = f['url']
        if annual or q == 4:
            fa = ext_em(f['path'], 12)
            if annual: rec['em'] = fa
            else:
                f9 = filings.get((fy, 3))
                n9 = ext_em(f9['path'], 9) if f9 else {}
                rec['em'] = {k: round(v - n9[k], 6) for k, v in fa.items() if k in n9}
                if rec['em']: rec['notes'].append('Sales by primary market: Q4 = fiscal year (10-K) less nine months (Q3 10-Q).')
        else:
            rec['em'] = ext_em(f['path'], 3)
    # sales by primary market as recast in the following year's filings (Industrial markets re-cut in the FY2023 10-K)
    fn = filings.get((fy + 1, 4 if annual else q))
    if fn:
        if annual or q != 4: rec['em_py'] = ext_em(fn['path'], 12 if annual else 3, 'py')
        else:
            f9n = filings.get((fy + 1, 3))
            a_, n_ = ext_em(fn['path'], 12, 'py'), (ext_em(f9n['path'], 9, 'py') if f9n else {})
            rec['em_py'] = {k: round(v - n_[k], 6) for k, v in a_.items() if k in n_}
    if annual:
        fn2 = filings.get((fy + 2, 4))
        if fn2: rec['em_py2'] = ext_em(fn2['path'], 12, 'py2')
    # prior-year comparative as presented in the following year's release
    nxt = rel.get((fy + 1, 4 if annual else q))
    if nxt:
        rec['py'] = {'release': nxt['url'], 'is': ext_is(nxt['tabs'], mo, 'py'), 'seg': ext_seg(nxt['tabs'], mo, 'py'),
                     'ngaap': ext_ngaap(nxt['tabs'], mo, 'py')}
    # XBRL extras
    kind = 'FY' if annual or q == 4 else 'YTD'
    rec['x'] = {'sbc_ytd': xbrl.first_of(['ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense'], fy, kind, 4 if annual else q),
                'deftax_ytd': xbrl.first_of(['DeferredIncomeTaxExpenseBenefit'], fy, kind, 4 if annual else q),
                'dda_ytd': xbrl.first_of(['DepreciationDepletionAndAmortization'], fy, kind, 4 if annual else q),
                'sh_issued': xbrl.value('CommonStockSharesIssued', fy, 'I', 4 if annual else q),
                'sh_treasury': xbrl.first_of(['TreasuryStockCommonShares', 'TreasuryStockShares'], fy, 'I', 4 if annual else q)}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings = release_index()
    idx = []
    for (fy, q), r in sorted(rel.items()):
        idx.append({'fy': fy, 'q': q, 'date': r['date'], 'url': r['url']})
    json.dump(idx, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    n = 0
    for fy in range(2011, 2026):
        r = rec_period(rel, filings, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
    for fy in range(2021, 2027):
        for q in (1, 2, 3, 4):
            r = rec_period(rel, filings, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
    xbrl.dump_subset()
    print(n, 'period files')

if __name__ == '__main__':
    main()
