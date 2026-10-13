"""Per-period extraction for Fair Isaac (FICO) from the EDGAR documents in $FICO_SRC (see EXTRACTION_SCHEMA.md).

Sources by period (period_index.json):
  - Quarters Q1-13 ... Q3-26: earnings release (8-K Item 2.02, Ex. 99.1) for the income statement (three-month column),
    balance sheet, year-to-date cash flow and the non-GAAP results table; the 10-Q for the segment operating-income summary
    (MD&A), segment revenues, the interest / other split (segment note) and the B2B / B2C Scores and platform / non-platform
    software revenue tables. Q4: release three-month column; 10-Q-only items are derived later as FY (10-K) - 9M (Q3 10-Q).
  - FY2006-FY2012: the 10-K (statements, segment summary); FY2013-FY2025: the Q4 release twelve-month column (statements,
    non-GAAP) plus the 10-K (segment summary, interest, KPIs).
All amounts USD thousands in the documents -> USD millions (3 dp); shares thousands -> millions; per-share as published.
Writes data/<period>.json."""
import json, os, re, sys
import ptab
from ptab import get, find_table, rowlist

S = os.environ.get('FICO_SRC', '/tmp/fico_src')
HERE = os.path.dirname(os.path.abspath(__file__))
_PI = os.path.join(S, 'period_index.json')
IDX = json.load(open(_PI)) if os.path.exists(_PI) else {}
K = 1000.0

def m(v): return None if v is None else round(v / K, 3)

def qkey(y, q): return f'Q{q}-{str(y)[2:]}'

def periods():
    out = [str(y) for y in range(2006, 2026)]
    for y in range(2013, 2027):
        out += [qkey(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
    return out

def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

# ------------------------------------------------------------------ income statement
IS_NEED = [r'^Operating income$', r'^Net income', r'before income taxes', r'^Cost of revenues', r'^(Basic|Diluted)']

def ext_is(T, col):
    t = find_table(T, IS_NEED)
    if t is None: return None, None
    rs = [(l, v[col] if col < len(v) else None) for l, v in t['rows'] if v]
    labs = [l for l, _ in rs]
    o = {'rev_lines': [], 'other_op': [], 'nonop': []}
    i_rev = next((k for k, l in enumerate(labs) if re.match(r'^(Total revenues|Revenues)$', l, re.I)), None)
    if i_rev is None: return None, t
    o['rev'] = m(rs[i_rev][1])
    for l, v in rs[:i_rev]:
        if l and not re.match(r'^(19|20)\d\d$', l): o['rev_lines'].append([l, m(v)])
    i_op = next(k for k, l in enumerate(labs) if re.match(r'^Operating income', l, re.I))
    for l, v in rs[i_rev + 1:i_op]:
        if not l or re.match(r'^Total (operating )?(costs and )?expenses', l, re.I): continue
        if re.match(r'^Cost of revenues', l, re.I): o['cogs'] = m(v)
        elif re.match(r'^Research', l, re.I): o['rd'] = m(v)
        elif re.match(r'^Selling, general', l, re.I): o['sga'] = m(v)
        elif re.match(r'^Amortization of intangible', l, re.I): o['amort'] = m(v)
        elif re.match(r'^Restructuring', l, re.I): o['restr'] = round(o.get('restr', 0.0) + m(v), 3)
        else: o['other_op'].append([l, m(v)])           # positive = expense; gains on product-line / business sales negative
    o['opinc'] = m(rs[i_op][1])
    i_ebt = next(k for k, l in enumerate(labs) if re.search(r'before income taxes', l, re.I))
    for l, v in rs[i_op + 1:i_ebt]:
        if l: o['nonop'].append([l, m(v)])               # signed as presented (income +)
    o['ebt'] = m(rs[i_ebt][1])
    i_ni = next(k for k, l in enumerate(labs) if re.match(r'^Net income( \(loss\))?$', l, re.I))
    for l, v in rs[i_ebt + 1:i_ni]:
        if re.search(r'income tax', l, re.I) and 'tax' not in o: o['tax'] = m(v)
        elif re.search(r'discontinued operations', l, re.I): o['disc'] = m(v)
        elif re.match(r'^Income from continuing operations', l, re.I): o['cont'] = m(v)
    o['ni'] = m(rs[i_ni][1])
    tail = rs[i_ni + 1:]
    eps = [(l, v) for l, v in tail if v is not None and abs(v) < 1000]
    shr = [(l, v) for l, v in tail if v is not None and abs(v) >= 1000]
    if any(re.match(r'^Continuing operations', l, re.I) for l, _ in eps):
        tots = [v for l, v in eps if re.match(r'^Total$', l, re.I)]
        conts = [v for l, v in eps if re.match(r'^Continuing operations', l, re.I)]
        if len(tots) >= 2: o['eps_b'], o['eps_d'] = tots[0], tots[1]
        if len(conts) >= 2: o['eps_b_cont'], o['eps_d_cont'] = conts[0], conts[1]
    else:
        b = [v for l, v in eps if re.search(r'basic', l, re.I)]
        d = [v for l, v in eps if re.search(r'diluted', l, re.I)]
        if b: o['eps_b'] = b[0]
        if d: o['eps_d'] = d[0]
    b = [v for l, v in shr if re.search(r'basic', l, re.I)]
    d = [v for l, v in shr if re.search(r'diluted', l, re.I)]
    if b: o['sh_b'] = round(b[0] / K, 3)
    if d: o['sh_d'] = round(d[0] / K, 3)
    dps = [v for l, v in eps if re.search(r'dividends', l, re.I)]
    if dps: o['dps'] = dps[0]
    return o, t

# ------------------------------------------------------------------ balance sheet
def ext_bs(T, col=0):
    t = find_table(T, [r'Total current assets', r'Total current liabilities', r'Cash and cash equivalents'])
    if t is None: return None
    rs = [(l, v[col] if col < len(v) else None) for l, v in t['rows'] if v]
    o, unl = {'lines': []}, []
    sect = 'a'
    for l, v in rs:
        if v is None: continue
        if re.match(r'^(19|20)\d\d$', l) or (not l and v and 1990 < v < 2100): continue
        lab = l.lower()
        if not l: unl.append(v); continue
        o['lines'].append([l, m(v)])
        if re.match(r'^cash and cash equivalents', lab): o['cash'] = m(v)
        elif re.match(r'^(accounts )?receivables?, net', lab): o['ar'] = m(v)
        elif re.match(r'^total current assets', lab): o['tca'] = m(v)
        elif re.match(r'^property and equipment', lab): o['ppe'] = m(v)
        elif re.match(r'^goodwill and intangible', lab): o['gw'] = m(v)
        elif re.match(r'^goodwill$', lab): o['gw'] = round(o.get('gw', 0.0) + m(v), 3)
        elif re.match(r'^intangible assets, net', lab): o['gw'] = round(o.get('gw', 0.0) + m(v), 3)
        elif re.match(r'^total assets', lab): o['ta'] = m(v)
        elif re.match(r'^accounts payable', lab): o['ap'] = round(o.get('ap', 0.0) + m(v), 3); sect = 'l'
        elif re.match(r'^other accrued liabilities', lab): o['ap'] = round(o.get('ap', 0.0) + m(v), 3)
        elif re.match(r'^accrued compensation', lab): o['accomp'] = m(v)
        elif re.match(r'^deferred revenue', lab) and 'tcl' not in o: o['defrev'] = round(o.get('defrev', 0.0) + m(v), 3)
        elif re.search(r'(current maturities|current portion|senior convertible notes|short-term)', lab) and 'tcl' not in o:
            o['std'] = round(o.get('std', 0.0) + m(v), 3)
        elif re.match(r'^total current liabilities', lab): o['tcl'] = m(v)
        elif 'tcl' in o and 'tl' not in o and re.search(r'(revolving line of credit|senior notes|long-term debt|senior convertible notes|term loan)', lab):
            o['ltd'] = round(o.get('ltd', 0.0) + m(v), 3)
        elif re.match(r'^total liabilities$', lab): o['tl'] = m(v)
        elif re.match(r"^total stockholders. (equity|deficit)$|^stockholders. (equity|deficit)$", lab): o['eq'] = m(v)
        elif re.match(r"^total liabilities and stockholders", lab): o['tle'] = m(v)
        elif re.match(r'^marketable securities', lab) and 'tca' not in o: o['mkt_cur'] = round(o.get('mkt_cur', 0.0) + m(v), 3)
        elif re.match(r'^marketable securities', lab): o['mkt_lt'] = round(o.get('mkt_lt', 0.0) + m(v), 3)
    if 'ta' not in o and unl: o['ta'] = m(unl[0])
    if 'tle' not in o and len(unl) >= 2: o['tle'] = m(unl[-1])
    return o

# ------------------------------------------------------------------ cash flow (year to date)
def ext_cf(T, col=0):
    t = find_table(T, [r'operating activities', r'investing activities', r'beginning of'])
    if t is None: return None
    rs = [(l, v[col] if col < len(v) else None) for l, v in t['rows'] if v]
    o = {'lines': [], 'debt': 0.0}
    sect = 'o'
    for l, v in rs:
        if v is None or not l or re.match(r'^(19|20)\d\d$', l): continue
        lab = l.lower(); mv = m(v)
        if re.match(r'^net cash .*operating', lab): o['cfo'] = mv; sect = 'i'; continue
        if re.match(r'^net cash .*investing', lab): o['cfi'] = mv; sect = 'f'; continue
        if re.match(r'^net cash .*financing', lab): o['cff'] = mv; sect = 'x'; continue
        o['lines'].append([sect, l, mv])
        if sect == 'o':
            if re.match(r'^net income', lab) and 'ni' not in o: o['ni'] = mv
            elif re.match(r'^depreciation and amortization', lab): o['dda'] = mv
            elif re.match(r'^(share|stock)-based compensation', lab): o['sbc'] = mv
            elif re.match(r'^deferred income taxes', lab): o['def'] = mv
        elif sect == 'i':
            if re.match(r'^purchases? of property and equipment', lab): o['capex'] = mv
            elif re.match(r'^capitalized internal-use software', lab): o['capsw'] = mv
            elif re.search(r'paid for acquisition', lab): o['acq'] = round(o.get('acq', 0.0) + mv, 3)
            elif re.search(r'(proceeds from (sale|product line|disposition)|cash transferred, net of proceeds|from sale of business|from product line)', lab):
                o['divest'] = round(o.get('divest', 0.0) + mv, 3)
        elif sect == 'f':
            if re.match(r'^repurchases of common stock', lab): o['bb'] = mv
            elif re.match(r'^dividends paid', lab): o['div'] = mv
            elif re.search(r'proceeds from (issuance|issuances) of (common|treasury) stock', lab): o['stock'] = round(o.get('stock', 0.0) + mv, 3)
            elif re.search(r'taxes paid related to net share', lab): o['taxw'] = mv
            elif re.search(r'(revolving line|term loan|senior (convertible )?notes|short-term loans|convertible)', lab): o['debt'] = round(o['debt'] + mv, 3)
        elif sect == 'x':
            if re.match(r'^effect of exchange rate', lab): o['fx'] = mv
            elif re.search(r'beginning of', lab): o['beg'] = mv
            elif re.search(r'end of', lab): o['end'] = mv
            elif re.search(r'(increase|decrease).*cash', lab): o['net'] = mv
    return o

# ------------------------------------------------------------------ non-GAAP results (releases FY2013+)
def ext_ng(T, col):
    need = [r'^GAAP net income', r'^Non[- ]GAAP net income', r'^GAAP diluted earnings per share']
    t = None
    for c in T:
        labs = [r[0] for r in c['rows']]
        if not all(any(re.search(p, l, re.I) for l in labs) for p in need): continue
        if re.search(r'GUIDANCE', c['ctx'][-160:] + ' ' + ' '.join(labs[:8]), re.I): continue
        t = c; break
    if t is None: return None
    if t['ncol'] < col + 1: col = 0
    o = {'items': [], 'eps_items': []}
    o['gaap_ni'] = m(get(t, r'^GAAP net income', col))
    o['ni_pub'] = m(get(t, r'^Non[- ]GAAP net income', col))
    o['items'] = [[l, m(v)] for l, v in rowlist(t, r'^GAAP net income', r'^Non[- ]GAAP net income', col)]
    o['gaap_eps'] = get(t, r'^GAAP diluted earnings per share', col)
    o['eps_pub'] = get(t, r'^Non[- ]GAAP diluted earnings per share', col)
    o['eps_items'] = [[l, v] for l, v in rowlist(t, r'^GAAP diluted earnings per share', r'^Non[- ]GAAP diluted earnings per share', col)]
    f = t if any(re.match(r'^Free cash flow', r[0], re.I) and r[1] for r in t['rows']) else next((c for c in T if any(re.match(r'^Free cash flow', r[0], re.I) and r[1] for r in c['rows']) and not re.search(r'GUIDANCE', c['ctx'][-160:], re.I)), None)
    if f is not None:
        o['fcf_pub'] = m(get(f, r'^Free cash flow', col))
        o['fcf_lines'] = [[l, m(v)] for l, v in rowlist(f, r'^Net cash provided by', r'^Free cash flow', col, incl_start=True)]
        if f['ncol'] < col + 1: o['fcf_pub'] = None
    return o

# ------------------------------------------------------------------ 10-Q / 10-K: segment summary, interest, KPIs
def seg_tables(T):
    """MD&A segment operating-income summaries, split into blocks at each 'Operating income' row (a 10-Q table may hold the
    quarter and the year-to-date blocks). Returns a list of row lists in document order."""
    out = []
    for t in T:
        labs = [r[0] for r in t['rows'] if r[1]]
        if any(re.match(r'^(Total )?segment operating income$', l, re.I) for l in labs) and any(re.match(r'^Operating income$', l, re.I) for l in labs) \
           and any(re.match(r'^Unallocated', l, re.I) for l in labs) and not any(re.match(r'^(Total segment revenues|Segment operating expense)', l, re.I) for l in labs):
            cur = []
            for row in t['rows']:
                cur.append(row)
                if row[1] and re.match(r'^Operating income$', row[0], re.I):
                    out.append(cur); cur = []
    return out

def seg_summary(rows, col=0):
    o = {'segs': [], 'items': []}
    after = False
    for lab, vals in rows:
        if not vals or not lab or col >= len(vals) or vals[col] is None: continue
        if re.match(r'^(Segment|Fiscal Year)$', lab) or re.match(r'^(19|20)\d\d$', lab): continue
        v = m(vals[col])
        if re.match(r'^(Total )?segment operating income$', lab, re.I): o['total'] = v; after = True; continue
        if re.match(r'^Operating income$', lab, re.I): o['opinc'] = v; break
        if re.search(r'corporate expenses', lab, re.I): o['corp'] = v; continue
        (o['items'] if after else o['segs']).append([lab, v])
    return o

def seg_revenue(T, names):
    """MD&A revenue summary table: rows = segment names + Total."""
    for t in T:
        labs = [r[0] for r in t['rows'] if r[1]]
        if all(any(l == n for l in labs) for n in names) and any(re.match(r'^Total( segment)? revenues?$', l, re.I) for l in labs) \
           and not any(re.search(r'operating income', l, re.I) for l in labs):
            return t
    return None

def seg_rev_by_oi(T, segs):
    """segment-note table: find the column of each segment by matching its operating income (from the MD&A summary), then
    read that column's total segment revenues."""
    for t in T:
        rows = {}
        for lab, vals in t['rows']:
            if vals and re.match(r'^(Total segment revenues|Segment revenues|Revenues)$', lab, re.I) and 'rev' not in rows: rows['rev'] = vals
            if vals and re.match(r'^Segment operating income( \(loss\))?$', lab, re.I): rows['oi'] = vals
        if 'rev' not in rows or 'oi' not in rows: continue
        out = []
        for name, v in segs:
            j = next((j for j, x in enumerate(rows['oi']) if x is not None and v is not None and abs(x / K - v) < 0.0015), None)
            if j is None or j >= len(rows['rev']) or rows['rev'][j] is None: break
            out.append([name, m(rows['rev'][j])])
        else:
            if out: return out
    return None

def interest(T, nth):
    ts = [t for t in T if any(re.match(r'^Unallocated interest', r[0], re.I) for r in t['rows'] if r[1])]
    if len(ts) <= nth: return None
    t = ts[nth]
    def last(pat):
        for lab, vals in t['rows']:
            if vals and re.match(pat, lab, re.I):
                vs = [v for v in vals if v is not None]
                return m(vs[-1]) if vs else None
        return None
    return {'int_inc': last(r'^Unallocated interest income'), 'int_exp': last(r'^Unallocated interest expense$'),
            'int_net': last(r'^Unallocated interest expense, net'), 'oth': last(r'^Unallocated other'),
            'opinc': last(r'^Operating income'), 'ebt': last(r'^Income before income taxes')}

KPI = {'b2b': r'^Business-to-business Scores', 'b2c': r'^Business-to-consumer Scores', 'plat': r'^Platform software', 'nonplat': r'^Non-platform software'}

def kpis(T, cols):
    t = find_table(T, [KPI['b2b'], KPI['b2c']])
    t2 = find_table(T, [KPI['plat'], KPI['nonplat']])
    o = {}
    for tt, ks in ((t, ('b2b', 'b2c')), (t2, ('plat', 'nonplat'))):
        if tt is None: continue
        for k in ks:
            for name, c in cols.items():
                v = get(tt, KPI[k], c)
                if v is not None: o[f'{k}_{name}'] = m(v)
    return o

# ------------------------------------------------------------------ period records
def url(p, kind): return IDX.get(p, {}).get(kind + '_url')

def do_period(p):
    fy, q = fyq(p)
    ent = IDX.get(p, {})
    rec = {'period': p, 'sources': {}, 'notes': []}
    rel = ent.get('release_html'); fil = ent.get('filing_html')
    TR = ptab.tables(rel) if rel else []
    TF = ptab.tables(fil) if fil else []
    if rel: rec['sources']['release'] = url(p, 'release')
    if fil: rec['sources']['filing'] = url(p, 'filing')
    annual = p.isdigit()
    if annual and fy <= 2012:
        rec['is'], _ = ext_is(TF, 0); rec['bs'] = ext_bs(TF, 0); rec['cf'] = ext_cf(TF, 0); rec['basis'] = '10-K'
    elif annual:
        rec['is'], _ = ext_is(TR, 2); rec['bs'] = ext_bs(TR, 0); rec['cf'] = ext_cf(TR, 0); rec['ng'] = ext_ng(TR, 2); rec['basis'] = 'Q4 release (twelve months)'
    else:
        rec['is'], _ = ext_is(TR, 0); rec['bs'] = ext_bs(TR, 0); rec['cf'] = ext_cf(TR, 0); rec['ng'] = ext_ng(TR, 0)
        rec['basis'] = 'release (three months)'
        if q > 1:
            ytd, _ = ext_is(TR, 2); rec['is_ytd'] = ytd
            rec['ng_ytd'] = ext_ng(TR, 2)
    if rec.get('cf'): rec['cf']['ytd_months'] = 12 if annual else 3 * q
    # 10-Q / 10-K items
    if TF and (annual or q < 4):
        st = seg_tables(TF)
        if st:
            rec['seg'] = seg_summary(st[0], 0)
            if annual and len(st) >= 1:
                rec['seg_py'] = seg_summary(st[0], 1)
            if not annual and q > 1 and len(st) >= 2:
                rec['seg_ytd'] = seg_summary(st[1], 0); rec['seg_ytd_py'] = seg_summary(st[1], 1)
            if not annual and q == 1:
                rec['seg_py'] = seg_summary(st[0], 1)
            for key in ('seg', 'seg_py', 'seg_ytd', 'seg_ytd_py'):
                if key in rec:
                    rv = seg_rev_by_oi(TF, rec[key]['segs'])
                    if rv: rec[key]['rev'] = rv
            if 'rev' not in rec['seg']:
                names = [n for n, _ in rec['seg']['segs']]
                rt = seg_revenue(TF, names)
                if rt is not None:
                    rec['seg']['rev'] = [[n, m(get(rt, '^' + re.escape(n) + '$', 0))] for n in names]
                    rec['seg']['rev_src'] = 'MD&A segment revenue summary'
        rec['int'] = interest(TF, 0)
        if not annual and q > 1:
            n_int = len([t for t in TF if any(re.match(r'^Unallocated interest', r[0], re.I) for r in t['rows'] if r[1])])
            if n_int >= 4: rec['int_ytd'] = interest(TF, 2)
        if annual: rec['kpi'] = kpis(TF, {'cur': 0, 'py': 1, 'py2': 2})
        else:
            first = find_table(TF, [KPI['b2b']])
            nc = first['ncol'] if first else 0
            rec['kpi'] = kpis(TF, {'cur': 0, 'py': 1, **({'ytd': 4, 'ytd_py': 5} if nc >= 8 else {})})
    return rec

def check(rec):
    i = rec.get('is') or {}
    n = rec['notes']
    if i:
        oc = sum(v for k, v in i.items() if k in ('cogs', 'rd', 'sga', 'amort', 'restr') and v) + sum(v for _, v in i['other_op'] if v)
        if abs(i['rev'] - oc - i['opinc']) > 0.01: n.append(f'CHECK IS: rev - costs - opinc = {i["rev"] - oc - i["opinc"]:.3f}')
        if abs(i['opinc'] + sum(v for _, v in i['nonop'] if v) - i['ebt']) > 0.01: n.append('CHECK IS: opinc + nonop != ebt')
        ni = i['ebt'] - i.get('tax', 0) + (i.get('disc') or 0)
        if abs(ni - i['ni']) > 0.01: n.append(f'CHECK IS: ebt - tax + disc != ni ({ni - i["ni"]:.3f})')
    b = rec.get('bs') or {}
    if b and b.get('ta') is not None and b.get('tle') is not None and abs(b['ta'] - b['tle']) > 0.01: n.append('CHECK BS: ta != tle')
    c = rec.get('cf') or {}
    if c and all(c.get(k) is not None for k in ('cfo', 'cfi', 'cff', 'beg', 'end')):
        if abs(c['cfo'] + c['cfi'] + c['cff'] + (c.get('fx') or 0) - (c['end'] - c['beg'])) > 0.01: n.append('CHECK CF: flows != change in cash')
    g = rec.get('ng') or {}
    if g and g.get('ni_pub') is not None and g.get('gaap_ni') is not None:
        if abs(g['gaap_ni'] + sum(v for _, v in g['items'] if v) - g['ni_pub']) > 0.01: n.append('CHECK NG: items do not sum')
    s = rec.get('seg') or {}
    if s and s.get('opinc') is not None:
        tot = sum(v for _, v in s['segs']) + (s.get('corp') or 0) + sum(v for _, v in s['items'])
        if abs(tot - s['opinc']) > 0.01: n.append(f'CHECK SEG: segments + corporate + items != opinc ({tot - s["opinc"]:.3f})')
        if i and abs(s['opinc'] - i['opinc']) > 0.01: n.append(f'CHECK SEG: opinc {s["opinc"]} vs IS {i["opinc"]}')
    return rec

if __name__ == '__main__':
    want = sys.argv[1:] or periods()
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    for p in want:
        try:
            rec = check(do_period(p))
        except Exception as e:
            print(p, 'ERROR', repr(e)); continue
        json.dump(rec, open(os.path.join(HERE, 'data', f'{p}.json'), 'w'), indent=1)
        i = rec.get('is') or {}
        print(p, i.get('rev'), i.get('opinc'), i.get('ni'), i.get('eps_d'), (rec.get('ng') or {}).get('eps_pub'), (rec.get('seg') or {}).get('opinc'), '|', '; '.join(rec['notes']))
