"""Per-period extraction of the FedEx earnings releases and recast exhibits (Form 8-K Item 2.02, Ex. 99.1) into data/<period>.json.

Legacy basis (fiscal years ended 31 May, FedEx Freight consolidated, as originally reported):
    data/<FY>.json      FY2006-FY2012 annual  (twelve-month columns of the fourth-quarter release; balance sheet at 31 May)
    data/Q<n>-<yy>.json Q1 FY2013 - Q4 FY2026 (three-month columns of each quarter's own release; cash flow year to date)
    data/FY<yy>.json    FY2013-FY2026 annual  (twelve-month columns of the fourth-quarter release)
Calendar basis (years ended 31 December, FedEx Freight in discontinued operations, Express U.S. Domestic / International segments):
    data/CQ<n>-<yy>.json, data/CY<yyyy>.json  from the recast exhibits of 21-Jul-2026 (2024-25) and 28-Oct-2026 (Q1-Q2/26) and the
    release of 28-Oct-2026 (Q3/26, nine months, balance sheet at 30-Sep-2026 and 31-Dec-2025).
Every table row is captured as [group, label, value] (group = the sub-heading above the row); normalize.py maps rows to model keys and
check_data.py runs the arithmetic checks. Nothing is estimated: a row that is not presented is absent."""
import json, os, re, glob, sys
import parse_release as pr

BASE = os.path.dirname(os.path.abspath(__file__))
S = os.environ.get('FDX_SRC', '/tmp/fdx_src')
FIL = json.load(open(os.path.join(S, 'filings.json')))
SEGSECS = ('exp', 'tnt', 'gnd', 'frt', 'kin', 'fec', 'usd', 'intl')

def url(o, w): return f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{o['acc'].replace('-', '')}/{w}"
def txt(o, w): return os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{w}".rsplit('.', 1)[0] + '.txt')

def releases():
    """(filing, exhibit, entries) of the quarterly earnings releases (those with a FedEx Freight segment table and a balance sheet)."""
    out = []
    for o in FIL:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        for w in o['files']:
            if w == o['primary'] or w.endswith('.txt') or not os.path.exists(txt(o, w)): continue
            e = pr.parse(open(txt(o, w)).read())
            secs = {x['sec'] for x in e}
            if 'frt' in secs and 'cf' in secs and ('is' in secs or 'fec' in secs):
                out.append((o, w, e))
    return out

def fiscal(date):
    y, m = int(date[:4]), int(date[5:7])
    q = {9: 1, 12: 2, 3: 3, 6: 4}[m]
    return (y + 1 if q in (1, 2) else y), q

def pick(v, single):
    """-> (quarter, prior-year quarter, year to date, prior year to date); quarterly releases print [cur, prior, % change] per period."""
    n = len(v)
    if single or n <= 3: return (v[0] if n else None, v[1] if n > 1 else None, None, None)
    if n >= 6: return v[0], v[1], v[3], v[4]
    if n == 4: return v[0], v[1], v[2], v[3]
    # five cells: one % change cell missing - take the layout whose year-to-date value is not smaller than the quarter
    a, b = (v[0], v[1], v[3], v[4]), (v[0], v[1], v[2], v[3])
    ok = lambda t: t[2] is not None and t[0] is not None and abs(t[2]) >= abs(t[0]) * 0.999
    return a if ok(a) and not ok(b) else b if ok(b) and not ok(a) else a

def rows(e, sec, single, two=False):
    out = []
    for x in e:
        if x['sec'] != sec or not x['label'] or not any(v is not None for v in x['vals']): continue
        g = x['ctx'][-1] if x['ctx'] else ''
        if two:
            v = [t for t in x['vals']]
            out.append([g, x['label'], v[0], v[1] if len(v) > 1 else None])
        else:
            out.append([g, x['label'], *pick(x['vals'], single)])
    return out

def recon_blocks(e):
    """Reconciliation tables: consecutive rows from 'GAAP measure' to 'Non-GAAP measure' (either order), with the heading above them."""
    out, cur = [], None
    for x in e:
        lab = x['label'].lower()
        if x['sec'] in SEGSECS or x['sec'] in ('bs', 'cf'):
            cur = None; continue
        isg = re.match(r'^(gaap|non-gaap) measure', lab)
        if isg and cur is None:
            cur = {'head': ' / '.join(x['ctx']), 'rows': []}; out.append(cur)
        if cur is not None:
            cur['rows'].append([x['label'], x['vals']])
            if isg and len(cur['rows']) > 1: cur = None
    return out

def tenk_bs(year):
    """Balance sheet at 31 May from the Form 10-K filed in <year> (used where the fourth-quarter release printed none: FY2016)."""
    o = [o for o in FIL if o['form'] == '10-K' and o['date'].startswith(str(year))][0]
    e = pr.parse(open(txt(o, o['primary'])).read())
    i = [k for k, x in enumerate(e[:-1]) if x['label'].lower() == 'cash and cash equivalents' and e[k + 1]['label'].lower().startswith('receivables')
         and len([v for v in x['vals'] if v is not None]) == 2][0]
    out = []
    for x in e[i:i + 60]:
        if x['label'] and x['vals'] and x['vals'][0] is not None:
            out.append([x['ctx'][-1] if x['ctx'] else '', x['label'], x['vals'][0], None])
        if x['label'].lower().startswith('total common stockholders'): break
    return out, url(o, o['primary'])

def tenk_cf(year):
    """Cash-flow statement of the fiscal year from the Form 10-K filed in <year> (first column)."""
    o = [o for o in FIL if o['form'] == '10-K' and o['date'].startswith(str(year))][0]
    e = pr.parse(open(txt(o, o['primary'])).read())
    i = [k for k, x in enumerate(e) if x['sec'] == 'cf' and x['label'].lower() == 'net income' and len(x['vals']) >= 3][0]
    out = []
    for x in e[i:i + 60]:
        if x['label'] and x['vals'] and x['vals'][0] is not None:
            out.append([x['ctx'][-1] if x['ctx'] else '', x['label'], x['vals'][0], None])
        if 'at end of period' in x['label'].lower(): break
    return out, url(o, o['primary'])

# fiscal years whose Form 10-K differs from the fourth-quarter release (the 10-K wins): FY2023 cash and operating cash flow
# (+$33m), FY2025 total assets (-$36m). Found by the XBRL cross-check in check_data.py.
TENK = {2023: ('bs', 'cf'), 2025: ('bs',)}

def save(key, rec):
    json.dump(rec, open(os.path.join(BASE, 'data', key + '.json'), 'w'), indent=0, ensure_ascii=False)

def legacy():
    n = 0
    for o, w, e in releases():
        if o['date'] > '2026-07-01': continue
        fy, q = fiscal(o['date'])
        single = q == 1
        src = [url(o, w)]
        tabs = {s: rows(e, s, single) for s in ('is',) + SEGSECS}
        bs = rows(e, 'bs', True, two=True)
        cf = rows(e, 'cf', True, two=True)
        rb = recon_blocks(e)
        bs_note = None
        if q == 4 and fy in TENK:
            notes = []
            if 'bs' in TENK[fy]:
                bs, u = tenk_bs(int(o['date'][:4])); notes.append('balance sheet')
            if 'cf' in TENK[fy]:
                cf, u = tenk_cf(int(o['date'][:4])); notes.append('cash-flow statement')
            src = src + [u]
            bs_note = f'FY{fy} {" and ".join(notes)} from the Form 10-K, which differs from the fourth-quarter release (the 10-K wins).'
        if not bs and q == 4:
            bs, u = tenk_bs(int(o['date'][:4])); src = src + [u]
            bs_note = f'The fourth-quarter release printed no balance sheet; balance sheet at 31-May-{fy} from the FY{fy} Form 10-K.'
        def mk(col, basis_note):
            rec = {'period': None, 'basis': 'legacy (fiscal year ended 31 May; FedEx Freight consolidated; as originally reported)',
                   'sources': src, 'filed': o['date'], 'notes': [basis_note]}
            for s, t in tabs.items():
                if t: rec[s] = [[g, l, r[col]] for g, l, *r in t if r[col] is not None]
                if t: rec.setdefault('py', {})[s] = [[g, l, r[col + 1]] for g, l, *r in t if r[col + 1] is not None]
            return rec
        if fy >= 2013:
            rec = mk(0, 'three-month columns of the release'); rec['period'] = f'Q{q}-{str(fy)[2:]}'
            rec['bs'] = [[g, l, a] for g, l, a, b in bs if a is not None]
            rec['cf'] = [[g, l, a] for g, l, a, b in cf if a is not None]; rec['cf_ytd_months'] = 3 * q
            rec['recon'] = rb
            if bs_note: rec['notes'].append(bs_note)
            save(rec['period'], rec); n += 1
        if q == 4:
            rec = mk(2, 'twelve-month columns of the fourth-quarter release'); rec['period'] = (str(fy) if fy <= 2012 else f'FY{str(fy)[2:]}')
            rec['bs'] = [[g, l, a] for g, l, a, b in bs if a is not None]
            rec['cf'] = [[g, l, a] for g, l, a, b in cf if a is not None]; rec['cf_ytd_months'] = 12
            rec['recon'] = rb
            if bs_note: rec['notes'].append(bs_note)
            save(rec['period'], rec); n += 1
    print('legacy records', n)

if __name__ == '__main__':
    os.makedirs(os.path.join(BASE, 'data'), exist_ok=True)
    legacy()
    import extract_cal; extract_cal.run()
