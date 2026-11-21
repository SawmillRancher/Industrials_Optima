"""Supplement data/<period>.json with items the releases omit, from the 10-K / 10-Q text and XBRL company facts:
  seg   Domestic / International revenue and the segment profit measure (net income to FY2025; income from operations from FY2026),
        from the business-segment note (quarters: three-month column of the 10-Q; Q4 = fiscal year (10-K) - nine months (Q3 10-Q)).
  x     XBRL company facts, as first filed: amortization of intangible assets (year to date; discrete quarters derived), goodwill,
        intangible assets, shares issued less treasury shares, cover-page shares outstanding.
  k10   10-K text: employees, intangible amortization (FY2006-FY2010), goodwill (FY2006-FY2008), organic growth where stated.
Run after extract.py:  CACI_SRC=<dir> python3 -I supp.py"""
import json, os, re, sys, glob, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_release import pnum
S = os.environ.get('CACI_SRC', '/tmp/caci_src')
BASE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(BASE, 'data')
ARCH = 'https://www.sec.gov/Archives/edgar/data/16058/'

def vals(line): return [pnum(c) for c in line.split(' | ')[1:]]
def m(v): return None if v is None else round(v / 1000.0, 6)

def seg_note(lines, annual):
    """-> dict(rev_dom, rev_intl, p_dom, p_intl, measure) for the current period (first column block) or None."""
    idx = [i for i, l in enumerate(lines) if re.match(r'^Domestic( Operations)? \| International|^Revenues?:$|^Revenues? from external customers \|', l)]
    for i0 in idx:
        seg = lines[max(0, i0 - 2):i0 + 30]
        out = {}
        for j, l in enumerate(seg):
            L = l.lower()
            if re.match(r'^revenues? from external customers', L) and 'rev_dom' not in out:
                v = vals(l)
                if len(v) >= 3: out['rev_dom'], out['rev_intl'] = m(v[0]), m(v[1])
            elif re.match(r'^net income( attributable to caci)? \|', L) and 'rev_dom' in out and 'p_dom' not in out and len(vals(l)) >= 3:
                v = vals(l); out['p_dom'], out['p_intl'], out['measure'] = m(v[0]), m(v[1]), 'net income'
            elif re.match(r'^revenues?:$', L) and 'rev_dom' not in out:
                a, b = vals(seg[j + 1]), vals(seg[j + 2])
                if a and b and seg[j + 1].lower().startswith('domestic'): out['rev_dom'], out['rev_intl'] = m(a[0]), m(b[0])
            elif re.match(r'^net income( attributable to caci)?:$', L) and 'p_dom' not in out:
                a, b = vals(seg[j + 1]), vals(seg[j + 2])
                if a and b: out['p_dom'], out['p_intl'], out['measure'] = m(a[0]), m(b[0]), 'net income'
            elif re.match(r'^revenues? \|', L) and 'rev_dom' not in out and len(vals(l)) >= 6:
                v = vals(l); out['rev_dom'], out['rev_intl'] = m(v[0]), m(v[1])
            elif L.startswith('income from operations |') and 'rev_dom' in out and 'p_dom' not in out and len(vals(l)) >= 6:
                v = vals(l); out['p_dom'], out['p_intl'], out['measure'] = m(v[0]), m(v[1]), 'income from operations'
        if 'rev_dom' in out and 'p_dom' in out: return out
    return None

# ------------------------------------------------------------------ XBRL
_F = None
def facts():
    global _F
    if _F is None:
        d = json.load(open(os.path.join(S, 'cf_16058.json')))['facts']
        _F = {}
        for ns in ('us-gaap', 'dei'):
            for k, v in d.get(ns, {}).items():
                for u, fs in v['units'].items(): _F.setdefault(k, []).extend(fs)
    return _F
def fyq(end):
    e = dt.date.fromisoformat(end)
    q = {9: 1, 10: 1, 12: 2, 1: 2, 3: 3, 4: 3, 6: 4, 7: 4}.get(e.month)
    return e.year + (1 if e.month >= 7 else 0), q
def xval(concepts, fy, q, months=None):
    """first-filed 10-K / 10-Q fact for the period ending at quarter q of fy; months None = instant, else duration in months."""
    best = None
    for c in concepts:
        for f in facts().get(c, []):
            if f.get('form') not in ('10-K', '10-Q', '10-K/A', '10-Q/A'): continue
            if fyq(f['end']) != (fy, q): continue
            if months is None:
                if 'start' in f: continue
            else:
                if 'start' not in f: continue
                dd = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
                if abs(dd - months * 30.4) > 20: continue
            if best is None or f['filed'] < best[0]: best = (f['filed'], f['val'])
        if best: break
    return None if best is None else best[1]

def k10(lines, fy):
    t = ' '.join(lines)
    out = {}
    mm = re.search(r'approximately ([\d,]{5,7}) (?:talented )?employees|employed approximately ([\d,]{5,7})|we had approximately ([\d,]{5,7})', t)
    if mm: out['employees'] = int(next(g for g in mm.groups() if g).replace(',', ''))
    mm = re.search(r'[Aa]mortization expense (?:for these intangible assets |related to (?:the above )?(?:intangible assets|intangibles) )?(?:was|of|for the year ended June 30, %d(?: was| of)?) \$([\d.]+) million' % fy, t)
    if mm: out['amort_text'] = float(mm.group(1)); out['amort_quote'] = t[max(0, mm.start() - 60):mm.end() + 80]
    mm = re.search(r'organic (?:revenue )?growth of ([\d.]+)%', t)
    if mm: out['organic_pct'] = float(mm.group(1)); out['organic_quote'] = t[max(0, mm.start() - 120):mm.end() + 40]
    for l in lines:
        if re.match(r'^Goodwill \| [\d,]+ \| [\d,]+$', l) and 'gw' not in out: out['gw'] = m(vals(l)[0])
        if re.match(r'^Intangible assets, net \| [\d,]+ \| [\d,]+$', l) and 'intang' not in out: out['intang'] = m(vals(l)[0])
    return out

def main():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    F = {}
    for o in fl:
        if o['form'] in ('10-K', '10-Q'):
            F[fyq(o['report'])] = o
    segs = {}
    for (fy, q), o in sorted(F.items()):
        p = os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{o['primary'].rsplit('.', 1)[0]}.txt")
        lines = [l.rstrip('\n') for l in open(p, encoding='utf-8', errors='replace')]
        sg = seg_note(lines, q == 4)
        segs[(fy, q)] = sg
        url = ARCH + o['acc'].replace('-', '') + '/' + o['primary']
        keys = [str(fy)] if q == 4 else []
        if fy >= 2013 and q < 4: keys.append(f'Q{q}-{str(fy)[2:]}')
        for key in keys:
            fp = os.path.join(OUT, key + '.json')
            if not os.path.exists(fp): continue
            d = json.load(open(fp))
            d['sources']['filing'] = url
            if sg: d['seg'] = dict(sg)
            if q == 4: d['k10'] = k10(lines, fy)
            json.dump(d, open(fp, 'w'), indent=1, ensure_ascii=False)
    # Q4 segments = FY - 9M (Q1 + Q2 + Q3 as reported in the 10-Qs)
    for fy in range(2013, 2027):
        fp = os.path.join(OUT, f'Q4-{str(fy)[2:]}.json')
        if not os.path.exists(fp): continue
        d = json.load(open(fp)); a = segs.get((fy, 4)); qs = [segs.get((fy, k)) for k in (1, 2, 3)]
        if a and all(qs) and len({x['measure'] for x in qs + [a]}) == 1:
            d['seg'] = {k: round(a[k] - sum(x[k] for x in qs), 6) for k in ('rev_dom', 'rev_intl', 'p_dom', 'p_intl')}
            d['seg']['measure'] = a['measure']
            d['notes'].append('Segment data for Q4 = fiscal year (10-K) less Q1-Q3 (10-Qs).')
        elif a: d['notes'].append('Q4 segment data not derived (segment profit measure changed during the year or a quarter is missing).')
        json.dump(d, open(fp, 'w'), indent=1, ensure_ascii=False)
    # XBRL
    for fp in glob.glob(os.path.join(OUT, '*.json')):
        if os.path.basename(fp).startswith('_'): continue
        d = json.load(open(fp)); fy, q = d['fy'], d['q']
        qq = q or 4
        x = {}
        ytd = xval(['AmortizationOfIntangibleAssets', 'FiniteLivedIntangibleAssetsAmortizationExpense'], fy, qq, qq * 3)
        if q is None or q == 1:
            if ytd is not None: x['amort'] = round(ytd / 1e6, 6)
        else:
            dq = xval(['AmortizationOfIntangibleAssets'], fy, q, 3)
            prev = xval(['AmortizationOfIntangibleAssets', 'FiniteLivedIntangibleAssetsAmortizationExpense'], fy, q - 1, (q - 1) * 3)
            if dq is not None: x['amort'] = round(dq / 1e6, 6)
            elif ytd is not None and prev is not None: x['amort'] = round((ytd - prev) / 1e6, 6); x['amort_note'] = 'year to date less prior year to date'
        g = xval(['Goodwill'], fy, qq)
        if g is not None: x['gw'] = round(g / 1e6, 6)
        it = xval(['FiniteLivedIntangibleAssetsNet', 'IntangibleAssetsNetExcludingGoodwill'], fy, qq)
        if it is not None: x['intang'] = round(it / 1e6, 6)
        so = xval(['CommonStockSharesOutstanding'], fy, qq)
        iss, tr = xval(['CommonStockSharesIssued'], fy, qq), xval(['TreasuryStockCommonShares', 'TreasuryStockShares'], fy, qq)
        if so is not None: x['sh_out'] = round(so / 1e6 * (1000 if so < 1e6 else 1), 6)
        elif iss is not None and tr is not None: x['sh_out'] = round((iss - tr) / 1e6, 6)
        d['x'] = x
        json.dump(d, open(fp, 'w'), indent=1, ensure_ascii=False)
    print('done')

if __name__ == '__main__':
    main()
