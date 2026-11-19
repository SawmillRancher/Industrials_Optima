"""Per-period extraction from the General Dynamics EDGAR sources into data/<period>.json.

Periods: annual 2006-2025 (fourth-quarter release, twelve-month columns) and quarters Q1-13 - Q3-26 (that quarter's release,
three-month columns; Q4 from the fourth-quarter release three-month columns, which every GD release prints). Each record carries:
  is       statement of earnings (USD m; per share in $; shares in m)
  seg      revenue / operating earnings by segment and corporate (segment structure in force in the period)
  backlog  funded / unfunded / total backlog, estimated potential contract value, total estimated contract value by segment
  deliv    Gulfstream aircraft deliveries (large / mid / total; green to 2016, outfitted from 2017), pre-owned, Aerospace orders
  fin      company non-GAAP free cash flow (quarter and year to date), shares outstanding, employment, R&D (where printed)
  cf       cash flow, year to date (cf.ytd_months), mapped lines plus lines_raw
  bs       balance sheet at period end
  x        XBRL company facts (share-based compensation, deferred tax, D&A, dividends per share, G&A, cover-page shares)
  py       prior-year comparative as presented in the following year's release (restatement checks)
  sources / notes
Release units are USD millions (per share in $; shares in millions, or units in the pre-2011 financial-information exhibit).
GD's fiscal year ends 31 December; quarters end on the Sunday nearest the calendar quarter end."""
import json, os, re, glob
import parse_release as P
import xbrl

S = os.environ.get('GD_SRC', '/tmp/claude-0/-home-user-Industrials-Optima/92a98ef9-0d7e-5c30-9fc1-50550455fc0b/scratchpad/gd_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '40533'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc
def lab_norm(l): return re.sub(r'\s+', ' ', re.sub(r'\s*(\([a-z]\)|\*)+\s*$', '', l.replace('\xa0', ' ').strip().rstrip(':').strip())).lower()

# ------------------------------------------------------------------ release index: (fy, q) -> parsed release
def fyq_of_release(date):
    y, m = int(date[:4]), int(date[5:7])
    return {1: (y - 1, 4), 2: (y - 1, 4), 4: (y, 1), 5: (y, 1), 7: (y, 2), 8: (y, 2), 10: (y, 3), 11: (y, 3)}[m]

def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings, dup = {}, {}, []
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            fy, q = fyq_of_release(o['date'])
            docs = [d for d in o['files'] if d != o['primary']] or [o['primary']]        # Q4-2009: release embedded in the 8-K body
            for doc in docs:
                p = os.path.join(S, 'txt', f"{o['date']}_8-K_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
                if not os.path.exists(p): continue
                tabs = P.parse(open(p).read(), {1: 3, 2: 6, 3: 9, 4: 12}[q])
                if not any(t['type'] == 'is' for t in tabs) or not any(t['type'] == 'seg' for t in tabs): continue
                if (fy, q) in rel: dup.append((fy, q, o['date'])); continue
                rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), tabs=tabs, path=p)
        if o['form'] in ('10-Q', '10-K'):
            y, m = int(o['report'][:4]), int(o['report'][5:7])
            q = {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3, 12: 4}[m]
            filings[(y, q)] = dict(date=o['date'], url=url(o, o['primary']), form=o['form'],
                                   path=os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{o['primary'].rsplit('.', 1)[0]}.txt"))
    if dup: print('duplicate releases skipped:', dup)
    return rel, filings

# ------------------------------------------------------------------ income statement
IS_MAP = [('rev', r'^(net sales|revenues?)$'), ('costs', r'^operating costs and expenses$'), ('oi', r'^operating earnings'),
          ('int', r'^interest, net$'), ('oth', r'^other'), ('ebt', r'^earnings.*before income tax'),
          ('tax', r'^provision for income tax'), ('cont', r'^earnings( \(loss\))? from continuing operations$'),
          ('disc', r'^discontinued operations, net of tax$'), ('ni', r'^net earnings'),
          ('sh_b', r'^basic weighted average shares'), ('sh_d', r'^diluted weighted average shares')]

def ext_is(tabs, mo, cp):
    for t in P.rows_of(tabs, 'is'):
        if not t['cols'] or not any(c[0] == mo and c[1] == cp for c in t['cols']): continue
        if any(c[0] == mo and c[1] == cp for c in t['cols']) and sum(1 for c in t['cols'] if c[1] == 'py') > 1: continue   # multi-year comparison table
        ci = next(i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp)
        out, eps_mode = {}, None
        for lab, vals in t['rows']:
            L = lab_norm(lab)
            if re.match(r'^earnings( \(loss\))? per share\s*[-—–]\s*basic', L): eps_mode = 'b'
            if re.match(r'^earnings( \(loss\))? per share\s*[-—–]\s*diluted', L): eps_mode = 'd'
            if re.match(r'^diluted earnings per share', L): eps_mode = 'd'
            if not vals or ci >= len(vals): continue
            v = vals[ci]
            if eps_mode and re.match(r'^(continuing operations|discontinued operations|net earnings( \(loss\))?)$', L):
                k = {'continuing operations': 'cont', 'discontinued operations': 'disc'}.get(L, 'ni')
                out[f'eps_{eps_mode}_{k}'] = v; continue
            if eps_mode and re.match(r'^earnings( \(loss\))? per share\s*[-—–]\s*(basic|diluted)', L):
                out[f'eps_{eps_mode}_ni'] = v; continue
            if re.match(r'^diluted earnings per share - continuing', L): out['eps_d_cont'] = v; continue
            if eps_mode is None and re.match(r'^discontinued operations$', L) and 'disc' not in out: out['disc'] = v; continue
            key = next((k for k, p in IS_MAP if re.search(p, L)), None)
            if key and key not in out:
                if key == 'sh_b' or key == 'sh_d': v = v / 1e6 if v > 1e6 else v
                out[key] = v
        if 'rev' not in out: continue
        # sign normalisation: costs and tax positive (modern releases print them negative); interest / other as income effect
        neg_costs = out.get('costs', 0) < 0
        for k in ('costs', 'tax'):
            if k in out: out[k] = -out[k] if neg_costs else out[k]
        if 'tax' in out and not neg_costs and out.get('ebt') is not None and out.get('cont', out.get('ni')) is not None:
            # a positive-presented table may still show a tax benefit as a negative number: trust the arithmetic
            if abs(out['ebt'] - out['tax'] - out.get('cont', out.get('ni'))) > 0.6 and abs(out['ebt'] + out['tax'] - out.get('cont', out.get('ni'))) <= 0.6:
                out['tax'] = -out['tax']
        if 'oth' not in out and all(k in out for k in ('oi', 'int', 'ebt')) and abs(out['oi'] + out['int'] - out['ebt']) <= 0.6: out['oth'] = 0.0
        if 'cont' not in out: out['cont'] = out['ni']; out['disc'] = 0.0 if 'disc' not in out else out['disc']
        if 'disc' not in out: out['disc'] = 0.0
        for k in ('eps_b_cont', 'eps_d_cont'):
            if k not in out and out.get(k.replace('cont', 'ni')) is not None: out[k] = out[k.replace('cont', 'ni')]
        return out
    return None

# ------------------------------------------------------------------ segments
SEGN = [('aero', r'^aerospace'), ('combat', r'^combat systems'), ('marine', r'^marine systems'), ('ist', r'^information systems and technology'),
        ('it', r'^information technology'), ('ms', r'^mission systems'), ('tech', r'^technologies'), ('corp', r'^(resources/ ?)?corporate'),
        ('resources', r'^resources$'), ('total', r'^total')]

def ext_seg(tabs, mo, cp):
    for t in P.rows_of(tabs, 'seg'):
        if not t['cols'] or not any(c[0] == mo and c[1] == cp for c in t['cols']): continue
        if sum(1 for c in t['cols'] if c[1] == 'cur') > 1: continue                 # sequential-quarter comparison table
        ci = next(i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp)
        seen, out = {}, {'rev': {}, 'oi': {}, 'margin': {}}
        for lab, vals in t['rows']:
            L = lab_norm(lab)
            name = next((k for k, p in SEGN if re.search(p, L)), None)
            if not name or not vals or ci >= len(vals): continue
            n = seen.get(name, 0); seen[name] = n + 1
            sec = ['rev', 'oi', 'margin'][min(n, 2)] if name != 'corp' else ['oi', 'margin'][min(n, 1)]
            out[sec][name] = vals[ci]
        if out['rev']: return out
    return None

# ------------------------------------------------------------------ backlog (first block = current quarter end)
def ext_backlog(tabs):
    for t in P.rows_of(tabs, 'backlog'):
        out, ntot = {}, 0
        for lab, vals in t['rows']:
            L = lab_norm(lab)
            name = next((k for k, p in SEGN if re.search(p, L)), None)
            if not name or len(vals) < 3: continue
            if name == 'total':
                ntot += 1
                if ntot > 1: break
            if name in out: break                                   # the next block (prior quarter) starts
            keys = ['funded', 'unfunded', 'total', 'pcv', 'tecv']
            out[name] = {k: vals[i] for i, k in enumerate(keys) if i < len(vals)}
        if out: return out
    return None

# ------------------------------------------------------------------ Gulfstream deliveries, Aerospace orders
def ext_deliv(tabs, mo, ytd):
    out, sec = {}, 'green'
    for t in tabs:
        if t['type'] not in ('deliv', 'fin'): continue
        if not any(re.search(r'large|green aircraft|outfitted aircraft', lab_norm(l)) for l, _ in t['rows']): continue
        cols = t['cols'] or []
        qi = next((i for i, c in enumerate(cols) if c[0] == mo and c[1] == 'cur'), None)
        yi = next((i for i, c in enumerate(cols) if c[0] == ytd and c[1] == 'cur'), None) if ytd != mo else qi
        if any('1Q | 2Q' in h for h in t['hdr']):                     # FY2016 release: 1Q | 2Q | 3Q | 4Q | Full Year table
            for lab, vals in t['rows']:
                L = lab_norm(lab)
                if L.startswith('green aircraft') and len(vals) == 5: out['green_total_q'] = vals[3]; out['green_total_ytd'] = vals[4]
                if L.startswith('outfitted aircraft') and len(vals) == 5: out['outfitted_total_q'] = vals[3]; out['outfitted_total_ytd'] = vals[4]
            out['basis'] = 'green deliveries 2016 (quarterly table); outfitted deliveries shown for the ASC 606 change'
            continue
        if qi is None: continue
        for lab, vals in t['rows']:
            L = lab_norm(lab)
            if re.match(r'^green \(units\)|^gulfstream aircraft deliveries', L): sec = 'green'; continue
            if re.match(r'^completions', L): sec = 'compl'; continue
            if re.match(r'^pre-owned$', L): sec = 'preowned'; continue
            if re.match(r'^aerospace book-to-bill', L): sec = 'b2b'; continue
            if not vals or qi >= len(vals): continue
            def put(k):
                out[k + '_q'] = vals[qi]
                if yi is not None and yi < len(vals): out[k + '_ytd'] = vals[yi]
            if sec == 'green' and re.match(r'^large', L): put('large')
            elif sec == 'green' and re.match(r'^mid', L): put('mid')
            elif sec == 'green' and re.match(r'^total$', L): put('total')
            elif sec == 'compl' and re.match(r'^total$', L): put('compl_total')
            elif re.match(r'^pre-owned (aircraft )?deliveries', L) or (sec == 'preowned' and L == 'units'): put('preowned')
            elif sec == 'preowned' and L.startswith('sales'): put('preowned_sales')
            elif sec == 'b2b' and re.match(r'^orders', L): put('aero_orders')
            elif sec == 'b2b' and re.match(r'^revenue', L): put('aero_b2b_rev')
        out['basis'] = 'outfitted' if any('cabin' in lab_norm(l) for l, _ in t['rows']) else 'green'
    return out or None

# ------------------------------------------------------------------ financial information / non-GAAP free cash flow
def ext_fin(tabs, mo, ytd):
    out = {}
    for t in P.rows_of(tabs, 'fin'):
        cols = t['cols'] or []
        for lab, vals in t['rows']:
            L = lab_norm(lab)
            if not vals:
                if re.search(r'quarter \| year-to-date \| quarter \| year-to-date', L):        # FY2006 release: sub-heading inside the exhibit
                    cols = [(3, 'cur'), (ytd, 'cur'), (3, 'py'), (ytd, 'py')]
                continue
            if re.match(r'^free cash flow', L):
                qi = next((i for i, c in enumerate(cols) if c[0] == mo and c[1] == 'cur'), None)
                yi = next((i for i, c in enumerate(cols) if c[0] == ytd and c[1] == 'cur'), None)
                if qi is not None and qi < len(vals): out['fcf_q'] = vals[qi]
                if yi is not None and yi < len(vals): out['fcf_ytd'] = vals[yi]
                if qi is None and yi is None and len(vals) >= 2 and 'fcf_q' not in out:
                    out['fcf_q'] = vals[0]; out['fcf_note'] = 'columns unresolved; first value taken'
            elif re.match(r'^shares outstanding$', L) and 'shares_out' not in out:
                v = vals[0]; out['shares_out'] = v / 1e6 if v > 1e6 else v
            elif re.match(r'^employment$', L): out['employment'] = vals[0]
            elif re.match(r'^company[- ]sponsored r', L): out['rnd_q'] = vals[0]
            elif re.match(r'^net debt$', L) and 'net_debt' not in out: out['net_debt'] = vals[0]
            elif re.match(r'^total debt$', L) and 'total_debt' not in out: out['total_debt'] = vals[0]
            elif re.match(r'^return on invested capital$', L) or re.match(r'^return on invested capital \(', lab_norm(lab) + ' ('): pass
    return out or None

# ------------------------------------------------------------------ cash flow (year to date)
CF_MAP = [('ni', r'^net earnings'), ('dep', r'^depreciation'), ('amort', r'^amortization'), ('sbc', r'^(stock|equity)-based compensation'),
          ('excess_tax', r'^excess tax benefit'), ('deferred_tax', r'^deferred income tax'), ('disc_adj', r'^discontinued operations'),
          ('impair', r'impairment'), ('wc_ar', r'^accounts receivable'), ('wc_unbilled', r'^(contracts in process|unbilled receivables)'),
          ('wc_inv', r'^inventories'), ('wc_ap', r'^accounts payable'), ('wc_adv', r'^customer advances'), ('wc_tax', r'^income taxes payable'),
          ('wc_ocl', r'^other current (and non-?current )?liabilities'), ('wc_oca', r'^other current assets'), ('wc_ol', r'^other liabilities'),
          ('cfo_cont', r'^net cash provided by operating activities from continuing'), ('cfo_disc', r'^net cash .*discontinued operations.*operating'),
          ('cfo', r'^net cash .*operating activities$'),
          ('capex', r'^capital expenditures'), ('acq', r'^business acquisitions'), ('disc_proceeds', r'^proceeds from sale of discontinued'),
          ('asset_sales', r'^proceeds from sales? of assets'), ('sec_buy', r'^purchases of (available|held)'), ('sec_sell', r'^(maturities|sales|sales/maturities) of (available|held)'),
          ('cfi', r'^net cash .*investing activities'),
          ('div', r'^dividends paid'), ('bb', r'^purchases of common stock'), ('options', r'^proceeds from (stock )?option'),
          ('notes_rep', r'^repayment of (fixed|floating)-rate notes|^repayment of senior notes|^repayment of csra'),
          ('notes_proc', r'^proceeds from (fixed|floating)-rate notes|^\(repayment of\) proceeds from fixed|^proceeds from fixed-rate notes, net'),
          ('cp', r'commercial paper|credit facility'), ('cff', r'^net cash .*financing activities'),
          ('disc_cash', r'^net cash .*discontinued operations'), ('net', r'^net (increase|decrease|\(decrease\)|\(increase\)).*cash'),
          ('beg', r'^cash and equivalents at beginning'), ('end', r'^cash and equivalents at end')]
ONCE = {'ni', 'cfo_cont', 'cfo_disc', 'cfo', 'cfi', 'cff', 'net', 'beg', 'end', 'capex'}

def ext_cf(tabs, mo, cp='cur'):
    for t in P.rows_of(tabs, 'cf'):
        if not t['cols'] or not any(c[0] == mo and c[1] == cp for c in t['cols']): continue
        ci = next(i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp)
        out, raw, sec = {'ytd_months': mo}, [], 'op'
        for lab, vals in t['rows']:
            L = lab_norm(lab)
            if re.match(r'^cash flows from investing', L): sec = 'inv'; continue
            if re.match(r'^cash flows from financing', L): sec = 'fin'; continue
            if re.match(r'^cash flows from operating', L): sec = 'op'; continue
            if not vals or ci >= len(vals): continue
            v = vals[ci]; raw.append([lab, v, sec])
            if re.match(r'^other, net$|^other$', L): out[f'other_{sec}'] = out.get(f'other_{sec}', 0.0) + v; continue
            key = next((k for k, p in CF_MAP if re.search(p, L)), None)
            if key is None: continue
            if key == 'cfo' and sec != 'op': key = None
            if key in ('cfi',) and sec == 'op': sec = 'inv'
            if key in ('cff',): sec = 'fin'
            if key == 'disc_cash' and sec == 'op': key = 'cfo_disc'
            if key in ONCE and key in out: continue
            out[key] = round(out.get(key, 0.0) + v, 6) if key not in ONCE else v
        if 'cfo' not in out and 'cfo_cont' in out: out['cfo'] = out['cfo_cont']
        out['lines_raw'] = raw
        if 'cfo' in out: return out
    return None

# ------------------------------------------------------------------ balance sheet
BS_MAP = [('cash', r'^cash and equivalents'), ('ar', r'^accounts receivable'), ('unbilled', r'^(contracts in process|unbilled receivables)'),
          ('inv', r'^inventories'), ('oca', r'^other current assets'), ('tca', r'^total current assets'), ('ppe', r'^property, plant and equipment'),
          ('intang', r'^intangible assets'), ('gw', r'^goodwill'), ('oa', r'^other assets'), ('tnca', r'^total noncurrent assets'), ('ta', r'^total assets'),
          ('std', r'^short-term debt'), ('ap', r'^accounts payable'), ('adv', r'^customer advances'), ('ocl', r'^other current liabilities'),
          ('tcl', r'^total current liabilities'), ('ltd', r'^long-term debt'), ('ol', r'^other liabilities'), ('tncl', r'^total noncurrent liabilities'),
          ('cs', r'^common stock'), ('surplus', r'^surplus'), ('re', r'^retained earnings'), ('ts', r'^treasury stock'), ('aoci', r'^accumulated other comprehensive'),
          ('te', r"^total shareholders['’] equity"), ('tle', r"^total liabilities and shareholders")]

def ext_bs(tabs):
    for t in P.rows_of(tabs, 'bs'):
        if not t['cols']: continue
        ci = next((i for i, c in enumerate(t['cols']) if c[1] == 'cur'), 0)
        out, raw = {}, []
        for lab, vals in t['rows']:
            if not vals or ci >= len(vals): continue
            v = vals[ci]; raw.append([lab, v])
            L = lab_norm(lab)
            if lab == '':
                if 'tnca' in out and 'ta' not in out: out['ta'] = v
                elif 'te' in out and 'tle' not in out: out['tle'] = v
                continue
            key = next((k for k, p in BS_MAP if re.search(p, L)), None)
            if key and key not in out: out[key] = v
        out['lines_raw'] = raw
        if 'ta' in out: return out
    return None

# ------------------------------------------------------------------ MD&A Gulfstream deliveries (10-Q / 10-K, 2010-2016: the releases dropped the exhibit)
def ext_deliv_mdna(path):
    """-> [{'green': (cur, py), 'outfitted': (cur, py), 'hdr': ...}] per "Gulfstream aircraft deliveries (in units)" table in document order
    (10-Q: quarter then year to date; 10-K: current year then prior year). Column order (current / prior year first) varies by filing and
    is resolved from the variance column (variance = current - prior)."""
    if not os.path.exists(path): return []
    lines = open(path).read().splitlines()
    out = []
    for i, ln in enumerate(lines):
        if not re.match(r'^\s*Gulfstream aircraft deliveries \(in units\)', ln, re.I): continue
        tab = {'hdr': ' / '.join(l.strip() for l in lines[max(0, i - 8):i] if re.search(r'Months Ended|Year Ended|20\d\d', l))[:200]}
        for l in lines[i + 1:i + 4]:
            row = P.split_row(l.strip())
            if not row or row[0] == '': continue
            L = lab_norm(row[0]); v = row[1]
            if L not in ('green', 'outfitted', 'completion', 'completions') or len(v) < 2: continue
            a, b = v[0], v[1]
            var = v[2] if len(v) > 2 else None
            if var is not None and abs((b - a) - var) < 0.5: cur, py = b, a
            elif var is not None and abs((a - b) - var) < 0.5: cur, py = a, b
            else: cur, py = b, a; tab['order_note'] = 'variance column missing; prior-first order assumed'
            tab[{'completion': 'outfitted', 'completions': 'outfitted'}.get(L, L)] = (cur, py)
        if len(tab) > 1: out.append(tab)
    return out

def ext_bs_10k(path, ta_ref=None):
    """balance sheet from the 10-K text (FY2006, whose release had no balance-sheet exhibit, and the annual 10-K-wins check). The value
    column is the one whose total assets match ta_ref (XBRL Assets); the 2011-14 10-Ks print the prior year first."""
    if not os.path.exists(path): return None
    lines = open(path).read().splitlines()
    idx = next((i for i, l in enumerate(lines) if re.match(r'^\s*total current assets', l, re.I)), None)
    if idx is None: return None
    rows = [P.split_row(l.strip()) for l in lines[max(0, idx - 12): idx + 45]]
    rows = [r for r in rows if r and len(r[1]) >= 2]
    ci = 0
    if ta_ref is not None:
        tas = [vals for lab, vals in rows if lab_norm(lab) == 'total assets' or lab == '']
        for cand in (0, 1):
            if any(len(v) > cand and abs(v[cand] - ta_ref) < 1.1 for v in tas): ci = cand; break
    out, raw = {}, []
    for lab, vals in rows:
        v = vals[ci]; raw.append([lab, v])
        L = lab_norm(lab)
        if lab == '':
            if 'tnca' in out and 'ta' not in out: out['ta'] = v
            elif 'te' in out and 'tle' not in out: out['tle'] = v
            continue
        key = next((k for k, p in BS_MAP if re.search(p, L)), None)
        if key and key not in out: out[key] = v
    out['lines_raw'] = raw
    return out if 'ta' in out or 'tnca' in out else None

# ------------------------------------------------------------------ build records
def rec_period(rel, filings, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    tabs, mo, ytd = r['tabs'], (12 if annual else 3), (12 if annual else 3 * q)
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'sources': {'release': r['url'], 'release_date': r['date']}, 'notes': []}
    rec['is'] = ext_is(tabs, mo, 'cur')
    rec['seg'] = ext_seg(tabs, mo, 'cur')
    rec['backlog'] = ext_backlog(tabs)
    rec['deliv'] = ext_deliv(tabs, 3, ytd)
    rec['fin'] = ext_fin(tabs, 3, ytd)
    rec['cf'] = ext_cf(tabs, ytd, 'cur')
    rec['bs'] = ext_bs(tabs)
    f = filings.get((fy, 4 if annual else q))
    if f:
        rec['sources']['filing'] = f['url']
        if rec['bs'] is None:
            rec['bs'] = ext_bs_10k(f['path'])
            if rec['bs']: rec['notes'].append('Balance sheet from the Form 10-K (the release had no balance-sheet exhibit).')
        elif annual or q == 4:
            ta_x = xbrl.value('Assets', fy, 'I', 4)
            b10 = ext_bs_10k(f['path'], ta_x) if ta_x else None
            if b10 and b10.get('ta') is not None and abs(b10['ta'] - rec['bs']['ta']) > 0.6:
                rec['bs_release'] = rec['bs']; rec['bs'] = b10
                rec['notes'].append(f"Balance sheet from the Form 10-K (total assets {b10['ta']:,.0f}); the release's preliminary balance sheet showed {rec['bs_release']['ta']:,.0f} (10-K wins).")
        if rec['deliv'] is None or rec['deliv'].get('total_q') is None:
            md = ext_deliv_mdna(f['path'])
            if md:
                rec['deliv_mdna'] = md
                rec['notes'].append(f"Gulfstream deliveries from the {f['form']} MD&A (the release had no deliveries exhibit).")
    nxt = rel.get((fy + 1, 4 if annual else q))
    if nxt:
        rec['py'] = {'release': nxt['url'], 'is': ext_is(nxt['tabs'], mo, 'py'), 'seg': ext_seg(nxt['tabs'], mo, 'py')}
    kind, qq = ('FY', 4) if annual else ('Q', q)
    ytdk = 'FY' if annual else 'YTD'
    rec['x'] = {'sbc_ytd': xbrl.value('ShareBasedCompensation', fy, ytdk, qq), 'deftax_ytd': xbrl.value('DeferredIncomeTaxExpenseBenefit', fy, ytdk, qq),
                'dep_ytd': xbrl.value('Depreciation', fy, ytdk, qq), 'amort_ytd': xbrl.value('AmortizationOfIntangibleAssets', fy, ytdk, qq),
                'dps': xbrl.first_of(['CommonStockDividendsPerShareDeclared', 'CommonStockDividendsPerShareCashPaid'], fy, kind, qq),
                'ga': xbrl.value('GeneralAndAdministrativeExpense', fy, kind, qq),
                'oi_xbrl': xbrl.value('OperatingIncomeLoss', fy, kind, qq), 'ni_xbrl': xbrl.value('NetIncomeLoss', fy, kind, qq),
                'rev_xbrl': xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, kind, qq),
                'ta_xbrl': xbrl.value('Assets', fy, 'I', qq), 'cfo_xbrl': xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, ytdk, qq),
                'shares_cover': xbrl.value('EntityCommonStockSharesOutstanding', fy, 'I', qq, pick='last'),
                'shares_out': xbrl.value('CommonStockSharesOutstanding', fy, 'I', qq)}
    if annual and f and os.path.exists(f['path']):
        txt = open(f['path']).read()
        ms = re.findall(r'(?:employed|approximately|community of)\s+(?:approximately\s+)?([\d,]{5,8})\s+(?:employees|people|individuals|full-time)', txt)
        ms = [v for v in ms if int(v.replace(',', '')) >= 50000]                   # company total; segment and site headcounts are smaller
        rec['extra'] = {'src': f['url']}
        if ms: rec['extra']['employees'] = max(int(v.replace(',', '')) for v in ms)
        m = re.search(r'dividends declared per (?:common )?share were \$([\d.]+) in (20\d\d)', txt, re.I) or \
            re.search(r'declared dividends per share of \$\s*([\d.]+)\s*in\s*(20\d\d)', txt, re.I | re.S)
        if m and int(m.group(2)) == fy: rec['extra']['dps_fy'] = float(m.group(1)); rec['extra']['dps_src'] = '10-K text: dividends declared per share'
        else:
            m = re.search(r'cash dividends declared per common share \| ([\d. |]+)', txt, re.I)
            if m:                                   # five-year selected-data table; year order varies (ascending 2011-14), DPS rose every year
                vals = [float(v) for v in m.group(1).split('|') if v.strip()]
                rec['extra']['dps_fy'] = max(vals); rec['extra']['dps_src'] = '10-K selected financial data (five-year table; current year = highest, DPS raised every year)'
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
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if fy == 2026 and q == 4: break
            r = rec_period(rel, filings, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
    xbrl.dump_subset()
    print(n, 'period files')

if __name__ == '__main__':
    main()
