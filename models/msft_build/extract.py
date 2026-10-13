"""Per-period extraction of the Microsoft statements from EDGAR (see EXTRACTION_SCHEMA.md).

Sources (all in $MSFT_SRC/docs, indexed by make_index.py / fetch.py):
  - Annual FY2006-FY2012: the 10-K for the year (Item 8 income statements, balance sheets, cash-flow statements; segment note).
  - Quarters Q1 FY2013 - Q4 FY2026 and annual FY2013-FY2026: the quarter's earnings release (8-K Item 2.02, Ex. 99.1): three-month
    columns for the quarter (income statement, cash flow, segments), the quarter-end balance sheet, and the twelve-month columns of the
    Q4 release for the year. Each period is therefore as originally reported.
  - Prior-year comparatives (py): the prior-year columns of the same documents (used to flag restatements).
Values are USD millions as published; shares in millions; per share as published. Costs positive as presented; cash flow as presented.
Raw label rows are kept under lines_raw so every mapped value is traceable to the exact label."""
import json, os, re, datetime as dt
from tables import tables, split_row

S = os.environ.get('MSFT_SRC', '/tmp/msft_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
CIK = '789019'
F = json.load(open(os.path.join(S, 'filings.json')))

def url(o, doc): return f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{doc}"
def path(o, doc): return os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{doc}")

def qend(d):
    """latest calendar quarter end strictly before date d (release dates follow the quarter end by 3-5 weeks)."""
    d = dt.date.fromisoformat(d)
    for m in (12, 9, 6, 3):
        y = d.year
        e = dt.date(y, m, {12: 31, 9: 30, 6: 30, 3: 31}[m])
        if e < d: return e
    return dt.date(d.year - 1, 12, 31)

def fyq(e):
    return (e.year + 1, {9: 1, 12: 2}[e.month]) if e.month in (9, 12) else (e.year, {3: 3, 6: 4}[e.month])

def pk(fy, q): return f'Q{q}-{str(fy)[2:]}'

# ------------------------------------------------------------------ statement identification
def kind(t):
    head = (t.get('prev', '') + ' ' + t['ctx'][-200:] + ' ' + ' '.join(' '.join(r) for r in t['rows'][:2])).upper()
    labs = [r[0].lower() for r in t['rows'][:80]]
    has = lambda p: any(re.match(p, l) for l in labs)
    if has(r'comprehensive income') or has(r'^\d{4} as reported') or has(r'percentage change'): return None
    if has(r'^net income') and has(r'^diluted') and has(r'^(total )?revenue') and has(r'^income (\(loss\) )?before income taxes') and not has(r'^total assets'): return 'is'
    if has(r'^total assets') and has(r'^total current assets'): return 'bs'
    if has(r'^net cash (from|provided by|used in) operations'): return 'cf'
    if 'SEGMENT' in head and has(r'^(revenue|total revenue)') and (has(r'^operating income') or has(r'^gross margin')): return 'seg'
    return None

def raw_rows(t):
    """[(section, label, values)]: section = the last label-only row (e.g. 'Operations', 'Current assets:', 'Revenue')."""
    out, sec = [], ''
    for r in t['rows']:
        lab, vals = split_row(r)
        if not vals:
            if lab and not re.match(r'^(\d{4}|Three|Six|Nine|Twelve|Year|June|September|December|March|\(In)', lab): sec = lab
            continue
        if not lab or re.match(r'^(19|20)\d\d$', lab): continue
        out.append((sec, lab, vals))
    return out

# ------------------------------------------------------------------ label maps (first match wins; order matters)
IS_MAP = [('rev_prod', r'^Product$', 'rev'), ('rev_serv', r'^Service and other$', 'rev'), ('rev', r'^(Total revenue|Revenue)$', None),
          ('cogs_prod', r'^Product$', 'cogs'), ('cogs_serv', r'^Service and other$', 'cogs'),
          ('cogs', r'^(Total cost of revenue|Cost of revenue)$', None), ('gp', r'^Gross (margin|profit)$', None),
          ('rd', r'^Research and development$', None), ('sm', r'^Sales and marketing$', None), ('ga', r'^General and administrative$', None),
          ('impair', r'^(Impairment|Integration|Goodwill impairment|Employee severance)', None), ('opex', r'^Total operating expenses$', None),
          ('oi', r'^Operating income', None), ('oth', r'^(Other income|Other expense|Investment income)', None),
          ('ebt', r'^Income (\(loss\) )?before income taxes$', None), ('tax', r'^Provision for (\(benefit from\) )?income taxes$', None), ('ni', r'^Net income', None),
          ('eps_b', r'^Basic$', 'eps'), ('eps_d', r'^Diluted$', 'eps'), ('sh_b', r'^Basic$', 'sh'), ('sh_d', r'^Diluted$', 'sh'),
          ('dps', r'^Cash dividends declared per common share$', None)]

def map_is(rows, col):
    o, seen = {}, set()
    for sec, lab, vals in rows:
        s = sec.lower()
        ctx = 'rev' if s.startswith('revenue') else 'cogs' if s.startswith('cost of revenue') else 'eps' if s.startswith(('earnings', 'net income per share', 'earnings (loss)')) else 'sh' if s.startswith('weighted average') else None
        for k, pat, need in IS_MAP:
            if k in seen or not re.search(pat, lab, re.I): continue
            if need and need != ctx: continue
            if need is None and ctx in ('eps', 'sh') and k not in ('dps',): continue
            if col < len(vals): o[k] = vals[col]; seen.add(k)
            break
    return o

BS_MAP = [('cash', r'^Cash and (cash )?equivalents'), ('sti', r'^Short-term investments'), ('ar', r'^Accounts receivable'), ('inv', r'^Inventories'),
          ('tca', r'^Total current assets'), ('ppe', r'^Property and equipment'), ('rou', r'^Operating lease right-of-use'),
          ('eqinv', r'^Equity (and other )?investments'), ('gw', r'^Goodwill'), ('intang', r'^Intangible assets'), ('ta', r'^Total assets'),
          ('ap', r'^Accounts payable'), ('std', r'^(Short-term debt|Commercial paper)'), ('cltd', r'^Current portion of long-term debt'),
          ('ucr', r'^Short-term unearned revenue'), ('tcl', r'^Total current liabilities'), ('ltd', r'^Long-term debt'),
          ('lucr', r'^Long-term unearned revenue'), ('lease_ltl', r'^Operating lease liabilities'), ('tl', r'^Total liabilities$'),
          ('eq', r"^Total (stockholders|shareholders)[’'] equity"), ('tle', r'^Total liabilities and (stockholders|shareholders)')]

def map_bs(rows, col):
    o = {}
    for sec, lab, vals in rows:
        for k, pat in BS_MAP:
            if k in o or not re.search(pat, lab, re.I): continue
            if col < len(vals): o[k] = vals[col]
            break
        m = re.search(r'outstanding\s+([\d,]+)', lab)
        if m and 'sh_out' not in o and re.search(r'paid-in capital', lab, re.I): o['sh_out'] = float(m.group(1).replace(',', ''))
    if 'tl' not in o and 'tle' in o and 'eq' in o: o['tl'] = round(o['tle'] - o['eq'], 6); o['tl_derived'] = True
    return o

CF_MAP = [('ni', r'^Net income', 'op'), ('dda', r'^Depreciation, amortization', 'op'), ('sbc', r'^Stock-based compensation', 'op'),
          ('def', r'^Deferred income taxes', 'op'), ('cfo', r'^Net cash (from|used in|provided by) operations', None),
          ('debt_st', r'maturities (of|less than) 90 days', 'fin'),
          ('debt_iss', r'^Proceeds from issuance of debt(, maturities longer than 90 days)?$', 'fin'),
          ('debt_rep', r'^Repayments of debt(, maturities longer than 90 days)?$', 'fin'),
          ('iss', r'^Common stock issued', 'fin'), ('bb', r'^Common stock repurchased', 'fin'), ('div', r'^Common stock cash dividends', 'fin'),
          ('cff', r'^Net cash (from|used in|provided by)( \(used in\))? financing', None),
          ('capex', r'^Additions to property and equipment', 'inv'), ('acq', r'^Acquisitions? of companies', 'inv'),
          ('cfi', r'^Net cash (from|used in|provided by|from \(used in\)) investing', None),
          ('fx', r'^Effect of (foreign )?exchange rates', None), ('net', r'^Net (change|increase|decrease) in cash', None),
          ('beg', r'^Cash and (cash )?equivalents, beginning', None), ('end', r'^Cash and (cash )?equivalents, end', None)]

def map_cf(rows, col):
    o, sk = {}, None
    for sec, lab, vals in rows:
        s = sec.lower()
        if s:   # continuation tables (page breaks) carry no section header: keep the last one
            sk = 'op' if s.startswith(('operations', 'adjustments', 'changes in operating')) else 'fin' if s.startswith('financing') else 'inv' if s.startswith('investing') else sk
        for k, pat, need in CF_MAP:
            if k in o or not re.search(pat, lab, re.I): continue
            if need and need != sk: continue
            if col < len(vals): o[k] = vals[col]
            break
    return o

def seg_rows(rows, col):
    """{'metric||segment': value} for both layouts (metric-major: section = 'Revenue' / 'Operating income (loss)', rows = segments;
    segment-major: section = segment, rows = Revenue / Cost of revenue / Operating expenses / Operating income)."""
    o = {}
    for sec, lab, vals in rows:
        if col >= len(vals): continue
        if re.match(r'^(Revenue|Operating income|Cost of revenue|Operating expenses|Gross margin)', lab) and sec and not re.match(r'^(Revenue|Operating income|Gross margin)', sec):
            metric, seg = lab, sec
        else:
            metric, seg = sec, lab
        ml = metric.lower()
        metric = 'rev' if ml.startswith(('revenue', 'total revenue')) else 'oi' if ml.startswith(('operating income', 'total operating income')) else \
                 'cogs' if ml.startswith('cost of revenue') else 'opex' if ml.startswith('operating expenses') else \
                 'gm' if ml.startswith(('gross margin', 'total gross margin')) else metric
        o[f'{metric}||{seg}'] = vals[col]
    return o

# ------------------------------------------------------------------ non-GAAP reconciliation tables (vertical layout)
NG_LAB = re.compile(r'^(\d{4})\s+As\s+(Reported|Adjusted)(?: for [A-Za-z]+)?\s*\((GAAP|non-GAAP)\)', re.I)
def ngaap_tables(tbs):
    """Vertical layout: header (Revenue / Operating Income / Net Income / EPS), rows 'YYYY As Reported (GAAP)', item rows,
    'YYYY As Adjusted (non-GAAP)'. Returns [(ctx, header, [(label, values)])]."""
    out = []
    for t in tbs:
        labs = [r[0] for r in t['rows']]
        if not any(NG_LAB.match(l) for l in labs): continue
        hdr = None
        for r in t['rows']:
            if any(re.search(r'(Revenue|Net Income|Earnings per Share|Operating Income|Gross Margin)', c, re.I) for c in r) and not NG_LAB.match(r[0]):
                hdr = [c for c in r if re.search(r'(Revenue|Income|Share|Margin|Expense)', c, re.I)]
                break
        rows = [split_row(r) for r in t['rows']]
        out.append((t['ctx'][-200:], hdr, [(l, v) for l, v in rows if v and l]))
    return out

def parse_ngaap(nts, year):
    """Pick the GAAP -> non-GAAP bridge for the given label year from the first matching table: GAAP row, items, adjusted row."""
    for ctx, hdr, rows in nts:
        if not hdr: continue
        i0 = next((i for i, (l, v) in enumerate(rows) if re.match(rf'^{year}\s+As\s+Reported\s*\(GAAP\)', l, re.I)), None)
        if i0 is None: continue
        items, adj = [], None
        for l, v in rows[i0 + 1:]:
            if NG_LAB.match(l) and re.search(r'non-GAAP', l, re.I) and l.startswith(str(year)): adj = v; break
            if NG_LAB.match(l) or l.lower().startswith('percentage'): break
            items.append([l, v])
        if adj is None: continue
        return {'ctx': ctx, 'cols': hdr, 'gaap': rows[i0][1], 'items': items, 'adj': adj}
    return None

# ------------------------------------------------------------------ horizontal layout (FY2026 releases: columns As Reported / Impact / As Adjusted)
def parse_ngaap_h(tbs, year, which):
    for t in tbs:
        rows = t['rows']
        hi = next((i for i, r in enumerate(rows) if any('As Adjusted' in c for c in r) and any('As Reported' in c for c in r)), None)
        if hi is None or hi == 0: continue
        if 'Twelve' in t['ctx'][-120:] and which == 'q': continue
        if which == 'fy' and 'Twelve' not in t['ctx'][-200:]: continue
        hdr = rows[hi]
        # first year block: As Reported, [impacts...], As Adjusted
        try:
            a = hdr.index(next(c for c in hdr if 'As Reported' in c)); b = hdr.index(next(c for c in hdr if 'As Adjusted' in c))
        except StopIteration:
            continue
        if not str(year) in ' '.join(rows[hi - 1]): continue
        names = hdr[a + 1:b]
        out = {'ctx': t['ctx'][-200:], 'cols': [], 'gaap': [], 'adj': [], 'items': [[n, []] for n in names], 'layout': 'h'}
        for r in rows[hi + 1:]:
            lab, vals = split_row(r)
            if not vals or lab.lower().startswith('percentage'): continue
            out['cols'].append(lab)
            k = b - a + 1
            blk = vals[:k]
            if len(blk) < k: continue
            out['gaap'].append(blk[0]); out['adj'].append(blk[-1])
            for j, n in enumerate(names): out['items'][j][1].append(blk[1 + j])
        if out['cols']: return out
    return None

# ------------------------------------------------------------------ documents
def doc_tables(o, doc):
    p = path(o, doc)
    return tables(open(p, 'rb').read())

CF_CONT = re.compile(r'^(Investing|Financing|Additions to property|Net cash (from|used in)|Cash and (cash )?equivalents, (beginning|end)|Effect of|Net (change|increase|decrease) in cash|Purchases of investments|Common stock)', re.I)
def statements(tbs):
    st = {}
    for i, t in enumerate(tbs):
        k = kind(t)
        if k and k not in st:
            st[k] = raw_rows(t)
            if k == 'cf':         # page breaks split the cash-flow statement into continuation tables
                labs = [l for _, l, _ in st[k]]
                for t2 in tbs[i + 1:i + 6]:
                    if kind(t2): break
                    r2 = raw_rows(t2)
                    if r2 and any(CF_CONT.match(l) for _, l, _ in r2) and not any(l in labs for _, l, _ in r2 if l.startswith('Cash and')):
                        st[k] += r2; labs += [l for _, l, _ in r2]
    return st

def tenk_for(fy):
    return next(o for o in F if o['form'] == '10-K' and o['report'].startswith(f'{fy}-06'))

def tenq_for(fy, q):
    e = {1: f'{fy - 1}-09', 2: f'{fy - 1}-12', 3: f'{fy}-03'}[q]
    return next((o for o in F if o['form'] == '10-Q' and o['report'].startswith(e)), None)

def releases():
    out = {}
    for o in F:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        ex = [w for w in o['files'] if w != o['primary'] and re.search(r'99[_.]?1|dex991|ex99_1|ex991', w.lower())]
        if not ex: continue
        e = qend(o['date']); fy, q = fyq(e)
        out[(fy, q)] = (o, ex[0], e.isoformat())
    return out

REL = releases()

def lines(rows, col):
    return [[f'{s} / {l}' if s else l, v[col]] for s, l, v in rows if col < len(v)]

def annual_from_10k(fy):
    o = tenk_for(fy); doc = o['primary']
    tbs = doc_tables(o, doc)
    # Item 8 statements: first statement tables after the 'ITEM 8' heading
    st = {}
    TITLE = {'is': 'INCOME STATEMENTS', 'bs': 'BALANCE SHEETS', 'cf': 'CASH FLOW'}
    for t in tbs:
        k = kind(t)
        head = (t['ctx'][-200:] + ' ' + ' '.join(' '.join(r) for r in t['rows'][:2])).upper()
        if k in TITLE and k not in st and TITLE[k] in head and 'COMPREHENSIVE' not in head:
            st[k] = raw_rows(t)
    rec = {'period': str(fy), 'fy': fy, 'q': None, 'period_end': f'{fy}-06-30',
           'sources': {'filing': url(o, doc), 'filing_date': o['date']}, 'notes': ['Annual statements from the 10-K (Item 8).']}
    rec['is'] = map_is(st['is'], 0); rec['bs'] = map_bs(st['bs'], 0); rec['cf'] = map_cf(st['cf'], 0); rec['cf']['ytd_months'] = 12
    rec['is']['lines_raw'] = lines(st['is'], 0); rec['bs']['lines_raw'] = lines(st['bs'], 0); rec['cf']['lines_raw'] = lines(st['cf'], 0)
    rec['seg'] = seg_from_10k(tbs, fy)
    return rec

def seg_from_10k(tbs, fy):
    """10-K Item 8 segment note: the 'Revenue' and 'Operating income (loss)' tables by segment, fiscal-year columns (current year
    first). The last matching pair in the document is the audited note (the MD&A has quarterly tables)."""
    found = {}
    for t in tbs:
        hdr = ' '.join(' '.join(r) for r in t['rows'][:3])
        if not re.search(rf'Year Ended June 30,?\s*\|?\s*{fy}', ' | '.join(' | '.join(r) for r in t['rows'][:3])) and not re.search(rf'Year Ended June 30,? {fy}', hdr):
            continue
        rows = raw_rows(t)
        secs = {sec.lower() for sec, _, _ in rows}
        labs = ' '.join(l for _, l, _ in rows)
        if not re.search(r'(Server and Tools|Client|Windows)', labs) or not re.search(r'(Consolidated|Total)', labs): continue
        for sec in secs:
            if sec.startswith('revenue'): found['rev'] = rows
            if sec.startswith('operating income'): found['oi'] = rows
    out = {}
    for k in ('rev', 'oi'):
        for sec, lab, vals in found.get(k, []):
            out[f'{k}||{lab}'] = vals[0]
    return out

def quarter_from_release(fy, q):
    o, ex, e = REL[(fy, q)]
    tbs = doc_tables(o, ex)
    st = statements(tbs)
    rec = {'period': pk(fy, q), 'fy': fy, 'q': q, 'period_end': e,
           'sources': {'release': url(o, ex), 'release_date': o['date']}, 'notes': []}
    fq = tenk_for(fy) if q == 4 else tenq_for(fy, q)
    if fq: rec['sources']['filing'] = url(fq, fq['primary'])
    rec['is'] = map_is(st['is'], 0); rec['is']['lines_raw'] = lines(st['is'], 0)
    rec['bs'] = map_bs(st['bs'], 0); rec['bs']['lines_raw'] = lines(st['bs'], 0)
    ncf = max(len(v) for _, _, v in st['cf'])
    rec['cf'] = map_cf(st['cf'], 0); rec['cf']['months'] = 3 if (ncf >= 4 or q == 1) else None
    rec['cf']['lines_raw'] = lines(st['cf'], 0)
    if ncf >= 4: rec['cf_ytd'] = map_cf(st['cf'], 2); rec['cf_ytd']['ytd_months'] = 3 * q
    elif q == 1: rec['cf_ytd'] = dict(rec['cf']); rec['cf_ytd'].pop('lines_raw', None); rec['cf_ytd']['ytd_months'] = 3
    if 'seg' in st:
        rec['seg'] = seg_rows(st['seg'], 0); rec['seg_py'] = seg_rows(st['seg'], 1)
    rec['py'] = {'is': map_is(st['is'], 1)}
    nts = ngaap_tables(tbs)
    cy = int(e[:4])
    ng = parse_ngaap(nts, cy) or parse_ngaap_h(tbs, cy, 'q')
    if ng: rec['ngaap'] = ng
    ngp = parse_ngaap(nts, cy - 1)
    if ngp: rec['ngaap_py'] = ngp
    return rec, st, tbs, o

def annual_from_q4(fy, st, tbs, o):
    rec = {'period': str(fy), 'fy': fy, 'q': None, 'period_end': f'{fy}-06-30',
           'sources': {'release': url(o, [w for w in o['files'] if w != o['primary']][0]), 'release_date': o['date'],
                       'filing': url(tenk_for(fy), tenk_for(fy)['primary'])},
           'notes': ['Annual figures from the Q4 release twelve-month columns (cross-checked to the 10-K XBRL facts in check_data.py).']}
    rec['is'] = map_is(st['is'], 2); rec['is']['lines_raw'] = lines(st['is'], 2)
    rec['bs'] = map_bs(st['bs'], 0)
    rec['cf'] = map_cf(st['cf'], 2); rec['cf']['ytd_months'] = 12; rec['cf']['lines_raw'] = lines(st['cf'], 2)
    if 'seg' in st: rec['seg'] = seg_rows(st['seg'], 2); rec['seg_py'] = seg_rows(st['seg'], 3)
    rec['py'] = {'is': map_is(st['is'], 3)}
    nts = ngaap_tables(tbs)
    # the annual reconciliation is the table whose context mentions twelve months / year ended
    fy_t = [x for x in nts if re.search(r'(Twelve Months|Year Ended|Fiscal Year)', x[0], re.I)]
    ng = parse_ngaap(fy_t, fy) or parse_ngaap_h(tbs, fy, 'fy')
    if ng: rec['ngaap'] = ng
    return rec

def save(rec):
    json.dump(rec, open(os.path.join(OUT, rec['period'] + '.json'), 'w'), indent=1)

if __name__ == '__main__':
    import sys
    os.makedirs(OUT, exist_ok=True)
    for fy in range(2006, 2013):
        save(annual_from_10k(fy)); print(fy, 'ok')
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            rec, st, tbs, o = quarter_from_release(fy, q)
            save(rec)
            if q == 4: save(annual_from_q4(fy, st, tbs, o))
        print(fy, 'ok')
