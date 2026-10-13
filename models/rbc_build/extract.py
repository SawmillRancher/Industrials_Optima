"""Per-period extraction for RBC Bearings (CIK 1324948) from the EDGAR text files -> data/<period>.json.

Sources per period (period_index.py):
  - quarters: the earnings release (8-K Item 2.02, Ex. 99.1) three-month column for the statement of operations, non-GAAP
    reconciliations, selected financial data and segment sales; the 10-Q / 10-K for the balance sheet, the year-to-date cash flow
    statement and the segment note (segment sales, gross margin, SG&A, operating income; Q4 = fiscal year - nine months).
  - fiscal years: the 10-K statement of operations, balance sheet, cash flow statement and segment note; the Q4 release
    twelve-month columns for the non-GAAP reconciliations and selected data.
  - prior-year comparatives ('py'): the same tables one year later (segment recast to Aerospace & Defense / Industrial).
Units: USD millions (thousands / 1,000 where the document is in thousands); shares in millions; per share as published.
Signs: costs positive; adjusting items as added back (charges +, gains -); cash flow as presented.
Nothing is estimated: a line not presented is omitted; computed values are stated in 'notes'."""
import json, os, re, sys
from parse import lines, rows, row, find, get, scale_of
import period_index

S = os.environ.get('RBC_SRC', '/tmp/rbc_src')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def sc(L, i):
    """unit factor to USD millions. Set per document from the magnitude of a reference figure (statement net sales or total assets),
    because the unit captions are not reliable near every table (FY2023-24 documents mix 'in thousands' captions with millions)."""
    if DOC[0] is not None: return DOC[0]
    s = scale_of(L, i, 60)
    return 0.001 if s == 'k' else 1.0

def doc_scale(L):
    a, b = is_window(L)
    if a is not None:
        rv = row(L[a])[1][0]
        return 0.001 if rv > 10000 else 1.0
    i = find(L, r'^Total assets$', n=2)
    if i is not None:
        return 0.001 if row(L[i])[1][0] > 50000 else 1.0
    return None

# ------------------------------------------------------------------ statement of operations
def is_window(L):
    for i in range(len(L)):
        lab, v = row(L[i])
        if re.match(r'^Net sales$', lab, re.I) and len(v) >= 2 and all(abs(x - 100.0) > 1e-9 for x in v[:2]):
            j = find(L, r'.', i + 1, i + 3)
            if j is not None and re.match(r'^Cost of sales', row(L[j])[0], re.I):
                k = find(L, r'^Diluted$', i, i + 60)
                k = find(L, r'^Diluted$', k + 1, i + 70) if k is not None else None
                return i, (k or i + 50) + 1
    return None, None

IS_PATS = [('rev', r'^Net sales$'), ('cogs', r'^Cost of sales'), ('gp', r'^Gross margin$'), ('sga', r'^Selling, general'),
           ('oth', r'^Other, net'), ('opex', r'^Total operating expenses'), ('oi', r'^Operating income( \(loss\))?$'),
           ('int', r'^Interest expense'), ('loe', r'^Loss on (early )?extinguishment'), ('onop', r'^Other non-?operating'),
           ('ebt', r'^Income (\(loss\) )?before income taxes'), ('tax', r'^(Provision for|Benefit from|\(Benefit\)|Income tax)'),
           ('ni', r'^Net (income|\(loss\) income|loss)( ?/? ?\(loss\))?$'),
           ('pref', r'^Preferred stock dividends'), ('pref_part', r'^Participation rights of preferred'),
           ('ni_c', r'available to common|attributable to common')]

def ex_is(L, col):
    a, b = is_window(L)
    if a is None: return None
    f = doc_scale(L); o = {}
    for k, p in IS_PATS:
        h = get(L, p, a, b, col)
        if h: o[k] = round(h[1] * f, 6)
    eps, sh = [], []
    for i in range(a, b):
        lab, v = row(L[i])
        if re.match(r'^(Basic|Diluted)', lab) and len(v) > col:
            (eps if abs(v[col]) < 1000 else sh).append((lab.split()[0], v[col]))
    for lab, v in eps:
        o.setdefault('eps_b' if lab == 'Basic' else 'eps_d', v)
    for lab, v in sh:
        o.setdefault('sh_b' if lab == 'Basic' else 'sh_d', v / 1e6 if v > 1e5 else (v / 1e3 if v > 1e3 else v))
    h = get(L, r'^(Cash )?Dividends (declared )?per (common )?share', a, b + 25, col)
    if h: o['dps'] = h[1]
    o['_scale'] = f
    return o

# ------------------------------------------------------------------ release non-GAAP
CATS = [('STEPUP', r'inventory (purchase accounting|step|fair value)|purchase accounting'),
        ('ACQ', r'transaction|acquisition|due diligence|transition services|deal'),
        ('RESTR', r'restructur|consolidation|moving|relocat|integration|facility|plant|closure|severance|reorgani'),
        ('LEGAL', r'litigation|legal|settlement|lawsuit'),
        ('DEBT', r'extinguishment|deferred financ|refinanc|finance fee'),
        ('FX', r'foreign (exchange|currency)'),
        ('AMORT', r'amortization'), ('SBC', r'stock compensation|stock-based'),
        ('GAIN', r'disposal|sale of|gain|disposition|divest'),
        ('IMPAIR', r'impairment|write-?(off|down)'),
        ('PREF', r'preferred'),
        ('TAX', r'tax')]
def cat(label):
    l = label.lower()
    for c, p in CATS:
        if re.search(p, l): return c
    return 'OTHER'

def block(L, start_pat, end_pat, col, a=0, b=None, maxn=30):
    """rows from a 'Reported ...' line to the closing 'Adjusted ...' line. h2t drops blank cells, so a 4-column row with 2 values is
    ambiguous (current-period columns or prior-year columns): it is resolved by the choice that makes the reconciliation close."""
    i = find(L, start_pat, a, b, n=col + 1)
    if i is None: return None
    f = sc(L, i)
    items, amb = [], []
    nc = len(row(L[i])[1])
    for j in range(i + 1, min(i + maxn, len(L))):
        lab, v = row(L[j])
        lab0 = re.sub(r'\s*(\(\d\)|\*+)\s*$', '', lab).strip()
        if re.search(end_pat, lab0, re.I) and len(v) > col:
            start, end = round(row(L[i])[1][col] * f, 6), round(v[col] * f, 6)
            if amb:
                gap = end - start - sum(x[1] for x in items)
                for k, cand in amb:
                    if abs(cand - gap) < 0.0015: items[k][1] = cand; gap -= cand
            return dict(start=start, items=items, end=end, end_label=lab0, i=i, j=j, f=f)
        if lab and v and len(v) < nc and len(v) * 2 == nc:
            cur = v[0] if col < nc // 2 else v[1]
            items.append([lab0, 0.0, cat(lab0)]); amb.append((len(items) - 1, round(cur * f, 6)))
            continue
        if lab and len(v) > col:
            items.append([lab0, round(v[col] * f, 6), cat(lab0)])
    return None

def per_share_after(L, j, col, maxn=14):
    o = {}
    for k in range(j + 1, min(j + maxn, len(L))):
        lab, v = row(L[k])
        if re.match(r'^(Basic|Diluted)', lab) and len(v) > col:
            key = lab.split()[0].lower()
            if abs(v[col]) < 1000: o.setdefault('eps_' + key[0], v[col])
            else: o.setdefault('sh_' + key[0], v[col] / 1e6 if v[col] > 1e5 else v[col] / 1e3)
        if 'sh_d' in o: break
    return o

DOC = [None]
def ex_release(L, col):
    n = {}
    DOC[0] = doc_scale(L)
    gm = block(L, r'^Reported gross margin', r'^Adjusted gross margin', col)
    if gm: n['gm'] = dict(rep=gm['start'], items=gm['items'], adj=gm['end'])
    # operating income -> adjusted operating income (first block that closes on 'Adjusted operating income')
    a = 0
    while True:
        oi = block(L, r'^Reported operating income', r'^Adjusted operating income$|^Adjusted EBITDA$|^EBITDA$', col, a)
        if not oi: break
        if re.match(r'^Adjusted operating income', oi['end_label'], re.I):
            n['oi'] = dict(rep=oi['start'], items=oi['items'], adj=oi['end']); break
        a = oi['i'] + 1
    # net income -> adjusted net income
    ni = block(L, r'^Reported net income', r'^Adjusted net income$|^Adjusted net income \(loss\)$|^Adjusted net income attributable|^Adjusted net income available|^Net income$', col, maxn=40)
    if ni:
        d = dict(rep=ni['start'], items=ni['items'], adj=ni['end'], end_label=ni['end_label'])
        j = ni['j']
        h = get(L, r'^Preferred stock dividends', j + 1, j + 3, col)
        if h:
            d['pref'] = round(h[1] * ni['f'], 6)
            h2 = get(L, r'^Adjusted net income (available|attributable)', j + 1, j + 4, col)
            if h2: d['adj_c'] = round(h2[1] * ni['f'], 6); j = h2[0]
        d.update(per_share_after(L, j, col))
        n['ni'] = d
    for key, pat in (('new', r'^New adjusted net income'), ('cash', r'^Adjusted cash net income')):
        i = find(L, pat + r'.*(stockholders|income)$', n=col + 1)
        if i is not None:
            f = sc(L, i); st = find(L, r'^Adjusted net income (available|attributable)', i - 12, i, n=col + 1)
            items = []
            if st is not None:
                for k in range(st + 1, i):
                    lab, v = row(L[k])
                    if lab and len(v) > col: items.append([lab, round(v[col] * f, 6), cat(lab)])
            d = dict(adj_c=round(row(L[i])[1][col] * f, 6), items=items); d.update(per_share_after(L, i, col)); n[key] = d
    # EBITDA
    for key, pat in (('ebitda', r'^EBITDA$'), ('adj_ebitda', r'^Adjusted EBITDA$')):
        i = find(L, pat, n=col + 1)
        if i is not None: n[key] = round(row(L[i])[1][col] * sc(L, i), 6)
    i = find(L, r'Adjusted EBITDA:?$|to EBITDA to Adjusted EBITDA|Net Income to Adjusted EBITDA')
    if 'adj_ebitda' in n and i is not None:
        e = find(L, r'^Adjusted EBITDA$', i, n=col + 1) or i
        f = sc(L, e); comp = []
        for k in range(i + 1, e):
            lab, v = row(L[k])
            if lab and len(v) > col: comp.append([lab, round(v[col] * f, 6), cat(lab)])
        n['ebitda_rec'] = comp
    i = find(L, r'plus incentive stock compensation|operating income plus depreciation.*stock', n=col + 1)
    if i is not None: n['proxy_ebitda'] = round(row(L[i])[1][col] * sc(L, i), 6)
    # selected financial data
    i = find(L, r'^Selected Financial Data')
    if i is not None:
        f = sc(L, i); sel = {}
        for k, p in (('dda', r'^Depreciation and amortization'), ('sbc', r'stock compensation'), ('cfo', r'^Cash provided by operating'),
                     ('capex', r'^Capital expenditures')):
            h = get(L, p, i, i + 25, col)
            if h: sel[k] = round(h[1] * f, 6)
        for k, p in (('debt', r'^Total debt$'), ('backlog', r'^Backlog'), ('bb', r'^Repurchase of common stock')):
            h = get(L, p, i, i + 25, 0)
            if h: sel[k] = round(h[1] * f, 6)
        n['sel'] = sel
    i = find(L, r'^Backlog', n=1)
    m = re.search(r'Backlog[^.]*?as of [A-Za-z]+ \d+, \d{4},? (was|of) \$([\d.,]+) (million|billion)', ' '.join(L))
    if m: n['backlog_text'] = float(m.group(2).replace(',', '')) * (1000 if m.group(3) == 'billion' else 1)
    # segment external sales
    i = find(L, r'^Segment Data')
    seg = {}
    if i is not None:
        for k in range(i, min(i + 14, len(L))):
            lab, v = row(L[k])
            if re.search(r'segment$', lab, re.I) and len(v) > col:
                seg[segname(lab)] = round(v[col] * sc(L, i), 6)
    n['seg_sales'] = seg
    # guidance
    t = ' '.join(x.strip() for x in L)
    m = re.search(r'(Outlook for the [^.]{0,80}?(Quarter|Year)[^.]{0,40}?)\s+(The Company expects.{0,700}?)(Live Webcast|Conference Call|Webcast)', t, re.I)
    if m: n['outlook'] = (m.group(1) + ': ' + m.group(3)).strip()
    return n

def segname(lab):
    l = lab.lower()
    for k, p in (('aero', r'aerospace'), ('ind', r'^industrial'), ('plain', r'^plain'), ('roller', r'^roller'), ('ball', r'^ball'),
                 ('eng', r'^engineered'), ('other', r'^other'), ('corp', r'^corporate')):
        if re.search(p, l): return k
    return None

# ------------------------------------------------------------------ segment note (10-Q / 10-K)
HEADS = [('sales', r'^Net External Sales'), ('cogs', r'^Cost of Sales'), ('gm', r'^Gross Margin'), ('sga', r'^Selling, General'),
         ('oi', r'^Operating Income'), ('stop', r'^(Geographic|Total Assets|Intersegment|Capital Expenditures|Depreciation|Reconciliation)')]
def ex_segnote(L, col):
    a = None
    for i in range(len(L)):
        lab, v = row(L[i])
        if re.match(r'^Net External Sales:?$', lab, re.I) and len(v) == 0:
            a = i; break
    if a is None: return None
    f = sc(L, a, ) if scale_of(L, a, 60) else None
    out, head, pend = {}, None, None
    for k in range(a, a + 60):
        lab, v = row(L[k])
        h = next((hk for hk, hp in HEADS if re.match(hp, lab, re.I)), None)
        if h == 'stop': break
        if h:
            head = h
            if v: pend = v                         # header line carrying the first segment's numbers (2013 10-K layout)
            continue
        s = segname(lab) if lab else None
        if head and s:
            vals = v if v else pend
            pend = None
            if vals and len(vals) > col: out.setdefault(head, {})[s] = vals[col]
    if not out: return None
    tot = sum(out.get('sales', {}).values())
    unit = 0.001 if tot > 20000 else 1.0
    return {h: {s: round(x * unit, 6) for s, x in d.items()} for h, d in out.items()}

# ------------------------------------------------------------------ balance sheet
BS_PATS = [('cash', r'^Cash( and cash equivalents)?$'), ('sti', r'^(Short-term investments|Marketable securities)'),
           ('ar', r'^Accounts receivable'), ('inv', r'^Inventor'), ('tca', r'^Total current assets'),
           ('ppe', r'^Property, plant and equipment'), ('rou', r'^Operating lease assets'), ('gw', r'^Goodwill'),
           ('intang', r'^Intangible assets|^Intangibles'), ('ta', r'^Total assets'),
           ('ap', r'^Accounts payable'), ('accr', r'^Accrued expenses'), ('cltd', r'^Current portion of long[- ]term debt'),
           ('std', r'^(Notes payable|Short[- ]term (debt|borrowings)|Revolving credit facility)'), ('tcl', r'^Total current liabilities'),
           ('ltd', r'^Long[- ]term debt'), ('tl', r'^Total liabilities$'),
           ('pref', r'preferred stock'), ('teq', r"^Total (stockholders|shareholders)['’]? equity"), ('tle', r'^Total liabilities and')]
def ex_bs(L):
    for i in range(len(L)):
        lab, v = row(L[i])
        if re.match(r'^Total assets$', lab, re.I) and len(v) >= 2:
            tca = find(L, r'^Total current assets$', max(0, i - 40), i, n=2)
            if tca is None: continue
            a = find(L, r'^Cash', max(0, tca - 15), tca, n=2)
            b = find(L, r'^Total liabilities and', i, i + 70, n=2)
            if a is None or b is None: continue
            f = sc(L, a); o = {}
            for k, p in BS_PATS:
                h = get(L, p, a, b + 1, 0, flags=re.I)
                if h and not (k == 'ltd' and h[0] < i) : o[k] = round(h[1] * f, 6)
            o['lines_raw'] = [[lab2, round(v2[0] * f, 6)] for _, lab2, v2 in rows(L, a, b + 1) if v2]
            return o
    return None

# ------------------------------------------------------------------ cash flow
CF_PATS = [('ni', r'^Net (income|\(loss\) income|loss)'), ('dda', r'^Depreciation and amortization$'), ('dep', r'^Depreciation$'),
           ('amort', r'^Amortization of intangible'), ('sbc', r'^(Stock[- ]based compensation|Stock compensation|Amortization of deferred stock compensation|Share-based compensation|Equity-based compensation)'),
           ('deftax', r'^Deferred income tax'), ('cfo', r'^Net cash (provided by|\(used in\)|used in|from)[^|]*operating'),
           ('capex', r'^(Capital expenditures|Purchases? of property|Property, plant and equipment additions)'),
           ('acq', r'^(Acquisitions?|Purchase of business|Business acquisition)'), ('cfi', r'^Net cash[^|]*investing'),
           ('div', r'^(Cash )?[Dd]ividends paid( on common stock)?$|^Dividends paid to'), ('prefdiv', r'^(Preferred stock dividends|Dividends paid on preferred)'),
           ('bb', r'^(Repurchase of common stock|Purchase of treasury stock|Repurchases? of common)'),
           ('cff', r'^Net cash[^|]*financing'), ('fx', r'^Effect of exchange'),
           ('net', r'^(Increase|Decrease|\(Decrease\)|Net (increase|decrease|change))[^|]*(cash|during|period|year)|^(Increase|Decrease|\(Decrease\))[^|]*$'), ('beg', r'beginning of'), ('end', r'end of (period|year)')]
def ex_cf(L):
    for i in range(len(L)):
        lab, v = row(L[i])
        if re.match(r'^Cash flows from operating activities', lab, re.I):
            a = find(L, r'^Net (income|\(loss\)|loss)', i, i + 4, n=1)
            if a is None: continue
            b = find(L, r'end of (period|year)', a, a + 90, n=1)
            if b is None: continue
            f = sc(L, a); o = {}
            c = find(L, r'^Net cash[^|]*operating', a, b, n=1) or b
            OPK = ('ni', 'dda', 'dep', 'amort', 'sbc', 'deftax')
            for k, p in CF_PATS:
                d = find(L, r'^Net cash[^|]*financing', c, b, n=1) or c
                lo = a if k in OPK or k == 'cfo' else (d if k in ('fx', 'net', 'beg', 'end') else c)
                h = get(L, p, lo, c if k in OPK else b + 1, 0)
                if h: o[k] = round(h[1] * f, 6)
            o['lines_raw'] = [[lab2, round(v2[0] * f, 6)] for _, lab2, v2 in rows(L, a, b + 1) if v2]
            return o
    return None

# ------------------------------------------------------------------ driver
def run(only=None):
    idx = period_index.run()
    os.makedirs(OUT, exist_ok=True)
    keys = [str(y) for y in range(2006, 2027)] + [f'Q{q}-{str(y)[2:]}' for y in range(2007, 2028) for q in (1, 2, 3, 4) if (y, q) <= (2027, 1)]
    for k in keys:
        if only and k not in only: continue
        v = idx.get(k)
        if not v: print('missing', k); continue
        ann = k.isdigit(); q = 4 if ann else v['q']
        rec = dict(period=k, fy=v['fy'], q=None if ann else q, period_end=v['period_end'],
                   sources=dict(release=(v['release'] or {}).get('url'), release_date=(v['release'] or {}).get('date'),
                                filing=v['filing']['url'], filing_form=v['filing']['form'], filing_date=v['filing']['date']), notes=[])
        F = lines(v['filing']['txt'])
        R = lines(v['release']['txt']) if v.get('release') and v['release'].get('txt') else None
        rcol = 2 if ann else 0
        # statement of operations
        if ann:
            rec['is'] = ex_is(F, 0)
        else:
            rec['is'] = ex_is(R, 0) if R else None
            if not rec['is'] or 'rev' not in rec['is']:
                rec['is'] = ex_is(F, 0) if q < 4 else None
                rec['notes'].append('statement of operations from the 10-Q (release table not parsed)')
        # release
        DOC[0] = None
        if R:
            rr = ex_release(R, rcol)
            if ann and not rr.get('ni') and not rr.get('oi'):
                rr = ex_release(R, 1) if False else rr
            rec['ng'] = rr
        # balance sheet, cash flow (year to date), segment note
        DOC[0] = doc_scale(F)
        rec['bs'] = ex_bs(F)
        cf = ex_cf(F)
        if cf: cf['ytd_months'] = 3 * q
        rec['cf'] = cf
        rec['segn'] = ex_segnote(F, 0)
        rv = (rec['is'] or {}).get('rev') if ann else None
        if rv and rec['segn'] and abs(sum(rec['segn'].get('sales', {}).values()) - rv) > 0.2:
            for c in (1, 2):                      # FY2006 10-K: segment table columns run oldest-first
                alt = ex_segnote(F, c)
                if alt and abs(sum(alt.get('sales', {}).values()) - rv) <= 0.2:
                    rec['segn'] = alt; rec['notes'].append(f'segment note: fiscal-year column is column {c + 1} (oldest-first layout)'); break
        if not ann and q == 3:
            rec['segn_ytd'] = ex_segnote(F, 2)
        if v.get('next'):
            nf = v['next']['filing']; nr = v['next']['release']
            py = {}
            NF = lines(nf['txt'])
            DOC[0] = doc_scale(NF)
            py['segn'] = ex_segnote(NF, 1)
            if not ann and q == 3: py['segn_ytd'] = ex_segnote(NF, 3)
            if nr and nr.get('txt'):
                NR = lines(nr['txt'])
                rp = ex_release(NR, 3 if ann else 1)
                py['seg_sales'] = rp.get('seg_sales'); py['ng'] = {kk: rp.get(kk) for kk in ('oi', 'ni', 'adj_ebitda', 'ebitda', 'new', 'gm')}
                py['is'] = ex_is(NR, 3 if ann else 1) if not ann else ex_is(NF, 1)
            py['source'] = dict(filing=nf['url'], release=(nr or {}).get('url'))
            rec['py'] = py
        json.dump(rec, open(os.path.join(OUT, f'{k}.json'), 'w'), indent=1)
    return idx

if __name__ == '__main__':
    run(sys.argv[1:] or None)
