"""Per-period extraction from the J.B. Hunt EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2025 (fourth-quarter release, twelve-month column) and quarters Q1/13 - Q3/26 (that quarter's release,
three-month column). Each record carries:
  is     condensed statement of earnings (USD m; per share in $; shares in m)
  seg    segment revenue (gross, incl. fuel surcharge) and operating income, intersegment eliminations, corporate / other
  stat   operating statistics by segment (loads, revenue per load, average trucks, revenue per truck per week, stops ...)
  bs     condensed balance sheet at period end; shares outstanding (supplemental data)
  cf     cash flow, year to date (cf.ytd_months): XBRL company facts as first filed (10-Q / 10-K); net cash from operations and
         net capital expenditures also from the release supplemental data (cross-check)
  x      XBRL: basic shares, basic EPS, dividends per share, goodwill & intangibles, operating income / net earnings (cross-check)
  py     prior-year comparative as presented in this release (is / seg / stat) - used for the 2006 (ICS) and 2019 (Final Mile
         Services) segment recasts
  sources / notes
Release units are thousands; everything is stored in millions (per share as published; statistics as published).
"""
import json, os, re, pickle, sys
import parse_release as P
import xbrl

S = os.environ.get('JBHT_SRC', '/tmp/jbht_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
ARCH = 'https://www.sec.gov/Archives/edgar/data/728535/'
M = {1: 3, 2: 6, 3: 9, 4: 12}

def m(v): return None if v is None else round(v / 1000.0, 6)

def release_index():
    """(year, quarter) -> release: first-filed 8-K Item 2.02 exhibit containing the statements."""
    cache = os.path.join(S, 'rel.pkl')
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings = {}, {}
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            for doc in o['files']:
                if doc == o['primary']: continue
                p = os.path.join(S, 'docs', f"{o['date']}_8-K_{o['acc']}_{doc}")
                if not os.path.exists(p): continue
                secs = P.parse(open(p, 'rb').read())
                if not {'is', 'seg', 'bs'} <= {s['type'] for s in secs}: continue
                y, mo = int(o['date'][:4]), int(o['date'][5:7])
                yq = (y - 1, 4) if mo <= 2 else (y, 1) if mo <= 5 else (y, 2) if mo <= 8 else (y, 3)
                rel.setdefault(yq, dict(date=o['date'], url=ARCH + o['acc'].replace('-', '') + '/' + doc, secs=secs))
        if o['form'] in ('10-Q', '10-K') and o['report']:
            y, mo = int(o['report'][:4]), int(o['report'][5:7])
            filings[(y, mo // 3)] = dict(date=o['date'], form=o['form'], url=ARCH + o['acc'].replace('-', '') + '/' + o['primary'])
    return rel, filings

IS_MAP = [('rev_xfuel', r'^operating revenues, excluding fuel'), ('fuel_rev', r'^fuel surcharge revenues'), ('rev', r'^total operating revenues'),
          ('pt', r'^rents and purchased transportation'), ('sw', r'^salaries, wages'), ('fuel', r'^fuel and fuel taxes'),
          ('da', r'^depreciation and amortization'), ('supplies', r'^operating supplies'), ('ins', r'^insurance and claims'),
          ('ga', r'^general and administrative'), ('taxlic', r'^operating taxes and licenses'), ('comm', r'^communication and utilities'),
          ('opex', r'^total operating expenses'), ('oi', r'^operating income'), ('net_int', r'^net interest expense'),
          ('int_inc', r'^interest income'), ('int_exp', r'^interest expense'), ('equity_loss', r'^equity in (loss|operations)'),
          ('ebt', r'^earnings before income taxes'), ('tax', r'^income taxes'), ('ni', r'^net earnings'),
          ('sh_b', r'^average basic shares'), ('eps_b', r'^basic earnings per share'),
          ('sh_d', r'^(weighted )?average diluted shares'), ('eps_d', r'^diluted earnings per share')]
PS = {'eps_b', 'eps_d'}

def pick(nums, which): return P.cur(nums) if which == 'cur' else P.py(nums)

def ext_is(secs, mo, which):
    s = next((s for s in secs if s['type'] == 'is' and s['months'] == mo), None)
    if not s: return None
    out = {}
    for g, lab, nums in s['rows']:
        key = next((k for k, p in IS_MAP if re.search(p, lab.strip(), re.I)), None)
        if not key or key in out: continue
        v = pick(nums, which)
        if v is None: continue
        out[key] = v if key in PS else m(v)
    if 'net_int' not in out and 'int_exp' in out: out['net_int'] = round(out['int_exp'] - out.get('int_inc', 0.0), 6)
    return out

SEGN = [('jbi', r'^intermodal'), ('dcs', r'^dedicated'), ('ics', r'^integrated capacity'), ('fms', r'^final mile'), ('jbt', r'^truck')]
def segkey(name): return next((k for k, p in SEGN if re.search(p, name.strip(), re.I)), None)
SEGH = [('jbi', r'^intermodal( \(jbi\))?$'), ('dcs', r'^dedicated( contract services)?( \(dcs\))?$'), ('ics', r'^integrated capacity solutions( \(ics\))?$'),
        ('fms', r'^final mile services( \(fms\))?$'), ('jbt', r'^truck(load)?( \(jbt\))?$')]
def seghead(name): return next((k for k, p in SEGH if re.search(p, name.strip(' :*'), re.I)), None)

def ext_seg(secs, mo, which):
    s = next((s for s in secs if s['type'] == 'seg' and s['months'] == mo), None)
    if not s: return None
    out = {}
    for g, lab, nums in s['rows']:
        v = pick(nums, which)
        if v is None: continue
        kind = 'oi' if re.search(r'operating income', g, re.I) else 'rev'
        k = segkey(lab); L = lab.lower()
        if k: out[f'{kind}_{k}'] = m(v)
        elif L.startswith('subtotal'): out['rev_sub'] = m(v)
        elif L.startswith('intersegment'): out['rev_elim'] = m(v)
        elif L.startswith('consolidated revenue'): out['rev_tot'] = m(v)
        elif L.startswith('other'): out['oi_other'] = m(v)
        elif L.startswith('operating income'): out['oi_tot'] = m(v)
    return out

STAT = [('loads', r'^loads$'), ('stops', r'^stops$'), ('loh', r'^(average )?length of haul'), ('rpl', r'^revenue per load$'),
        ('rptw', r'^(net )?revenue.*per (truck|tractor) per week'), ('trucks_avg', r'^average (trucks|tractors) during the period'),
        ('trucks_eop', r'^(trucks|tractors) \(end of period\)|^total (trucks|tractors)$'), ('gpm', r'^gross profit margin'),
        ('emp', r'^employee count'), ('trailing_eop', r'^(trailing equipment|containers|trailers) \(end of period\)|^total trailers$'),
        ('trailing_avg', r'^average effective trailing equipment usage'), ('loaded_miles', r'^loaded miles'), ('or', r'^operating ratio')]

def ext_stat(secs, mo, which):
    s = next((s for s in secs if s['type'] == 'stat' and s['months'] == mo), None)
    if not s: return None
    out, seg = {}, None
    for g, lab, nums in s['rows']:
        k = seghead(g)
        if k: seg = k
        if not seg or '360' in g: continue
        key = next((kk for kk, p in STAT if re.search(p, lab.strip(' *'), re.I)), None)
        v = pick(nums, which)
        if key and v is not None and f'{seg}_{key}' not in out: out[f'{seg}_{key}'] = v
    return out

BS_MAP = [('cash', r'^cash and (cash )?equivalents'), ('ar', r'^(trade )?accounts receivable'), ('tca', r'^total current assets'),
          ('ppe_gross', r'^property and equipment'), ('accdep', r'^less accumulated depreciation'), ('ppe', r'^net property and equipment'),
          ('oa', r'^other assets'), ('debt_cur', r'^current debt|^current (portion|maturities) of long-term debt'), ('ap', r'^trade accounts payable'),
          ('claims', r'^claims accruals'), ('payroll', r'^accrued payroll'), ('oth_accr', r'^other accrued expenses'), ('tcl', r'^total current liabilities'),
          ('ltd', r'^long-term debt'), ('lt_claims', r'^long-term claims accruals'), ('oltl', r'^other long-term liabilities'), ('eq', r'^(stock|share)holders.? ?equity')]

def ext_bs(secs, which):
    s = next((s for s in secs if s['type'] == 'bs'), None)
    if not s: return None
    out, tot, after_tcl = {}, [], False
    for g, lab, nums in s['rows']:
        v = nums[0] if which == 'cur' else (nums[1] if len(nums) > 1 else None)
        if v is None: continue
        if lab == '__total__': tot.append(m(v)); continue
        L = lab.strip().lower()
        if L.startswith('deferred income taxes'):
            out['dit' if after_tcl else 'dit_cur'] = m(v); continue
        key = next((k for k, p in BS_MAP if re.search(p, L)), None)
        if key and key not in out: out[key] = m(v)
        if key == 'tcl': after_tcl = True
    if tot: out['ta'] = tot[0]
    if len(tot) > 1: out['tle'] = tot[1]
    for sec in secs:
        if sec['type'] != 'sup' and sec['type'] != 'bs': continue
        for g, lab, nums in sec['rows']:
            if lab.lower().startswith('actual shares outstanding') and 'shares' not in out:
                v = nums[0] if which == 'cur' else nums[1]
                out['shares'] = round(v / 1000.0, 6)
    return out

def ext_sup(secs, mo):
    out = {}
    for sec in secs:
        if sec['type'] != 'sup' or sec['months'] != mo: continue
        for g, lab, nums in sec['rows']:
            L = lab.lower()
            if L.startswith('net cash provided by operating'): out['cfo_rel'] = m(nums[0])
            if L.startswith('net capital expenditures'): out['netcapex_rel'] = m(nums[0])
    return out

XCF = [('ni', ['NetIncomeLoss']), ('da', ['DepreciationAndAmortization', 'DepreciationDepletionAndAmortization']), ('sbc', ['ShareBasedCompensation']),
       ('gain', ['GainLossOnSaleOfPropertyPlantEquipment', 'GainLossOnDispositionOfAssets1']), ('deftax', ['DeferredIncomeTaxExpenseBenefit']),
       ('cfo', ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations']),
       ('capex', ['PaymentsToAcquirePropertyPlantAndEquipment']), ('sale', ['ProceedsFromSaleOfMachineryAndEquipment']),
       ('acq', ['PaymentsToAcquireBusinessesNetOfCashAcquired']),
       ('cfi', ['NetCashProvidedByUsedInInvestingActivities', 'NetCashProvidedByUsedInInvestingActivitiesContinuingOperations']),
       ('bb', ['PaymentsForRepurchaseOfCommonStock']), ('div', ['PaymentsOfDividends']),
       ('cff', ['NetCashProvidedByUsedInFinancingActivities', 'NetCashProvidedByUsedInFinancingActivitiesContinuingOperations'])]

def ext_cf(y, q):
    out = {'ytd_months': M[q]}
    for k, cs in XCF:
        v = xbrl.first_of(cs, y, 'YTD', q)
        if v is not None: out[k] = round(v, 6)
    return out if 'cfo' in out else None

def ext_x(y, q, annual):
    kind, qq = ('FY', None) if annual else ('Q', q)
    out = {}
    for k, c in (('sh_b', 'WeightedAverageNumberOfSharesOutstandingBasic'), ('eps_b', 'EarningsPerShareBasic'), ('eps_d', 'EarningsPerShareDiluted'),
                 ('dps', 'CommonStockDividendsPerShareDeclared'), ('dps_paid', 'CommonStockDividendsPerShareCashPaid'), ('oi', 'OperatingIncomeLoss'), ('ni', 'NetIncomeLoss'),
                 ('amort', 'AmortizationOfIntangibleAssets')):
        v = xbrl.value(c, y, kind, qq)
        if v is None and not annual and q == 4:
            continue                                   # Q4 is not tagged separately (derived in normalize as FY - 9M)
        if v is not None: out[k] = round(v, 6)
    for k, c in (('gwint', 'IntangibleAssetsNetIncludingGoodwill'), ('gw', 'Goodwill'), ('rou', 'OperatingLeaseRightOfUseAsset')):
        v = xbrl.value(c, y, 'I', q)
        if v is not None: out[k] = round(v, 6)
    return out

def record(rel, filings, y, q, annual):
    r = rel.get((y, q))
    if not r: return None
    secs, mo = r['secs'], (12 if annual else 3)
    rec = {'period': str(y) if annual else f'Q{q}-{str(y)[2:]}', 'units': 'USD millions (per share in USD; shares in millions; statistics as published)',
           'sources': [r['url']], 'notes': []}
    for name, fn in (('is', ext_is), ('seg', ext_seg), ('stat', ext_stat)):
        rec[name] = fn(secs, mo, 'cur')
        if rec[name] is None and annual is False and q == 1: rec[name] = fn(secs, 3, 'cur')
    rec['py'] = {'is': ext_is(secs, mo, 'py'), 'seg': ext_seg(secs, mo, 'py'), 'stat': ext_stat(secs, mo, 'py')}
    rec['bs'] = ext_bs(secs, 'cur')
    cf = ext_cf(y, q)
    f = filings.get((y, q))
    if cf:
        cf.update(ext_sup(secs, M[q]))
        rec['cf'] = cf
        if f: rec['sources'].append(f['url'])
        rec['notes'].append('cash flow: XBRL company facts (10-Q / 10-K, value as first filed), year to date')
    else:
        rec['cf'] = dict(ytd_months=M[q], **ext_sup(secs, M[q])) if ext_sup(secs, M[q]) else None
    rec['x'] = ext_x(y, q, annual)
    # self-checks
    i, s, b = rec['is'], rec['seg'], rec['bs']
    def chk(name, a, bb, tol=0.011):
        if a is None or bb is None: return
        if abs(a - bb) > tol: rec['notes'].append(f'CHECK FAIL {name}: {a:.3f} vs {bb:.3f}')
    costs = sum(i.get(k, 0.0) for k in ('pt', 'sw', 'fuel', 'da', 'supplies', 'ins', 'ga', 'taxlic', 'comm'))
    chk('opex', costs, i.get('opex')); chk('oi', i['rev'] - i['opex'], i['oi'])
    chk('ebt', i['oi'] - i['net_int'] - i.get('equity_loss', 0.0), i['ebt']); chk('ni', i['ebt'] - i['tax'], i['ni'])
    chk('seg rev', sum(v for k, v in s.items() if k.startswith('rev_') and k[4:] in ('jbi', 'dcs', 'ics', 'fms', 'jbt')) + s.get('rev_elim', 0.0), i['rev'])
    chk('seg oi', sum(v for k, v in s.items() if k.startswith('oi_') and k != 'oi_tot'), i['oi'])
    chk('eps', i['ni'] / i['sh_d'], i['eps_d'], 0.0051)
    if b:
        chk('bs', b.get('ta'), b.get('tle'))
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings = release_index()
    n = 0
    for y in range(2006, 2026):
        rec = record(rel, filings, y, 4, True)
        if rec is None: print('missing', y); continue
        json.dump(rec, open(os.path.join(OUT, f'{y}.json'), 'w'), indent=1); n += 1
        for t in rec['notes']:
            if 'FAIL' in t: print(y, t)
    for y in range(2012, 2027):          # 2012 quarters: cash-flow / statistics base only (not shown in the model)
        for q in (1, 2, 3, 4):
            if (y, q) > (2026, 3): break
            rec = record(rel, filings, y, q, False)
            if rec is None: print('missing', y, q); continue
            json.dump(rec, open(os.path.join(OUT, f"Q{q}-{str(y)[2:]}.json"), 'w'), indent=1); n += 1
            for t in rec['notes']:
                if 'FAIL' in t: print(y, q, t)
    json.dump({f'{y}Q{q}': {'date': r['date'], 'url': r['url']} for (y, q), r in sorted(rel.items())}, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    xbrl.dump_subset()
    print(n, 'records')

if __name__ == '__main__':
    main()
