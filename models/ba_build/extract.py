"""Extract Boeing per-period records (data/<period>.json) from the 8-K Item 2.02 earnings releases (Ex. 99.1) on EDGAR.

Each release is read with tables.py (positional, colspan-aware), so every value is assigned to the period header it sits under.
Tables are classified by content: statement of operations, balance sheet, cash flows, segment revenues / earnings from operations,
unallocated items detail, deliveries, backlog, summary (Table 1) and the core-earnings reconciliation.

Periods: FY2006-FY2012 (Q4 release twelve-month columns) and Q1-13 ... Q2-26 (three-month columns; Q4 from the Q4 release),
plus FY2013-FY2025. Cash flow is year to date (cf.ytd_months). As originally reported: each period comes from its own release; the
prior-year columns of the following year's release are kept under `py` (restatement detection). Values in USD millions as
published (signs as presented: costs negative in the statement of operations)."""
import json, os, re, glob, sys
import tables as T

S = os.environ.get('BA_SRC', '/tmp/claude-0/-home-user-Industrials-Optima/705e6389-b409-5ea3-a1e9-50d700f2aedd/scratchpad/ba_src')
HERE = os.path.dirname(os.path.abspath(__file__))
CIK = '12927'

# ---------------------------------------------------------------------------------------------------------------- release index
def releases():
    """Earnings releases: 8-K Item 2.02 exhibits that contain a statement of operations and a balance sheet. One per quarter
    (the regular release; preliminary / charge pre-announcements without full statements are skipped)."""
    fl = json.load(open(os.path.join(S, 'filings.json')))
    out = {}
    for o in fl:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        for f in o['files']:
            if f == o['primary'] and len(o['files']) > 1: continue
            p = os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{f}")
            if not os.path.exists(p): continue
            tp = os.path.join(S, 'txt', os.path.basename(p).rsplit('.', 1)[0] + '.txt')
            low = re.sub(r'\s+', ' ', open(tp, encoding='utf-8', errors='ignore').read().lower()) if os.path.exists(tp) else ''
            if 'balance sheet' not in low and 'statements of financial position' not in low: continue
            if 'cost of products' not in low: continue
            d = o['date']; y, m = int(d[:4]), int(d[5:7])
            fy, q = (y - 1, 4) if m <= 2 else (y, (m - 1) // 3)
            url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{f}"
            out[(fy, q)] = dict(path=p, url=url, date=d, acc=o['acc'])
    return out

def filings_10():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    out = {}
    for o in fl:
        if o['form'] not in ('10-K', '10-Q'): continue
        r = o['report']; y, m = int(r[:4]), int(r[5:7])
        out[(y, m // 3)] = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{o['primary']}"
    return out

# ---------------------------------------------------------------------------------------------------------------- label maps
def norm(l):
    l = l.lower().replace('’', "'").replace('‘', "'").replace('&amp;', '&')
    l = re.sub(r'\(\d\)|\b\d\b$', '', l)
    l = re.sub(r'[*¹²³]', '', l)
    return re.sub(r'\s+', ' ', l).strip(' :')

IS_MAP = [
    ('rev_prod', r'^sales of products'), ('rev_serv', r'^sales of services'), ('rev', r'^total revenues'),
    ('cogs_prod', r'^cost of products'), ('cogs_serv', r'^cost of services'), ('bcc_int', r'boeing capital.*interest expense'),
    ('tot_costs', r'^total costs and expenses'), ('opinv', r'from operating investments'), ('ga', r'^general and administrative'),
    ('rd', r'^research and development'), ('gain_disp', r'(gain|loss).*on dispositions'),
    ('efo', r'(earnings|loss).*from operations$'), ('oth_inc', r'^other (income|\(loss\)|expense|income/\(loss\)|\(expense\)|income/\(expense\))'),
    ('int_exp', r'^interest and debt expense'), ('ebt', r'before income taxes'), ('tax', r'^income tax'),
    ('ni_cont', r'from continuing operations$'), ('disc', r'discontinued operations, net'),
    ('ni', r'^net (earnings|\(loss\)|loss)(/\(loss\)|/earnings)?$'),
    ('nci', r'attributable to noncontrolling'), ('ni_attr', r'attributable to (the )?boeing (company )?(shareholders)?$|attributable to boeing'),
    ('pref', r'preferred stock dividend|mandatory convertible preferred'), ('ni_common', r'(attributable|available) to common'),
    ('eps_b', r'^basic (earnings|\(loss\)|loss).*per share$'), ('eps_d', r'^diluted (earnings|\(loss\)|loss).*per share$'),
    ('eps_b_cont', r'^basic (earnings|\(loss\)|loss).*per share from continuing'), ('eps_d_cont', r'^diluted (earnings|\(loss\)|loss).*per share from continuing'),
    ('dps', r'dividends (paid|declared) per share'), ('sh_d', r'weighted average diluted shares|diluted weighted average (common )?shares'), ('sh_b', r'weighted average basic shares'),
]
BS_MAP = [
    ('cash', r'^cash and cash equivalents$'), ('sti', r'^short-term (and other )?investments'), ('ar', r'^accounts receivable'),
    ('unbilled', r'^unbilled receivables'), ('cfin_cur', r'^current portion of customer financing'), ('dta_cur', r'^deferred income taxes$'),
    ('inv', r'^inventories'), ('oca_l', r'^other current assets'), ('hfs_a', r'assets held for sale'), ('tca', r'^total current assets'),
    ('cfin', r'^customer financing'), ('ppe', r'^property, plant and equipment'), ('gw', r'^goodwill'), ('intang', r'acquired intangible'),
    ('invest', r'^investments'), ('pens_a', r'^pension plan assets'), ('ota_l', r'^other assets'), ('ta', r'^total assets'),
    ('ap', r'^accounts payable'), ('accr', r'^(other )?accrued liabilities'), ('adv', r'^advances and (billings|progress)'),
    ('itp', r'income taxes payable'), ('std', r'^short-term debt'), ('hfs_l', r'liabilities held for sale'), ('tcl', r'^total current liabilities'),
    ('rhc', r'^accrued retiree health'), ('pens_l', r'^accrued pension plan liability'), ('nc_itp', r'^non-current income taxes'),
    ('oltl', r'^other long-term liabilities'), ('ltd', r'^long-term debt'), ('tl', r'^total liabilities$'),
    ('pref_eq', r'preferred stock'), ('sh_eq', r"^total (boeing )?shareholders' (equity|deficit)|^total shareholders' (equity|deficit)"),
    ('nci_eq', r'^noncontrolling interest'), ('te', r'^total (equity|\(deficit\)|deficit|equity/\(deficit\)|equity \(deficit\))'),
    ('tle', r'^total liabilities and (shareholders\' )?(equity|deficit|\(deficit\))|^total liabilities and equity'),
    ('treas_sh', r'^treasury (stock|shares), at cost'),
]
CF_MAP = [
    ('ni', r'^net (earnings|\(loss\)|loss)(/\(loss\)|/earnings)?$'), ('sbc', r'^share-based plans expense'),
    ('dda', r'^depreciation and amortization'), ('dep', r'^depreciation$'), ('amort_int', r'^amortization of (other )?acquired intangibles'),
    ('ar', r'^accounts receivable$'), ('unbilled', r'^unbilled receivables$'), ('adv', r'^advances and (billings|progress)'),
    ('inv', r'^inventories'), ('oca', r'^other current assets'), ('ap', r'^accounts payable$'), ('accr', r'^(other )?accrued liabilities$'),
    ('itx', r'^income taxes receivable'), ('oltl', r'^other long-term liabilities$'), ('pens', r'^pension and other postretirement'),
    ('cfin', r'^customer financing, net'), ('cfo', r'(provided|used).*by operating activities'),
    ('capex', r'^property, plant and equipment,? additions|^payments to acquire property, plant'), ('ppe_red', r'^property, plant and equipment,? reductions|^proceeds from disposals of property'),
    ('acq', r'^acquisitions, net of cash'), ('divest', r'^(proceeds from )?(business|businesses) (dispositions|divest)|proceeds from (sale|dispositions) of business|^proceeds from divest'),
    ('inv_contrib', r'^contributions to investments'), ('inv_proc', r'^proceeds from investments'), ('cfi', r'by investing activities'),
    ('borrow', r'^new borrowings'), ('repay', r'^debt repayments'), ('opt', r'^stock options exercised'),
    ('bb', r'^common shares? repurchased'), ('div', r'^dividends paid'), ('pref_div', r'preferred.*dividends|dividends.*preferred'),
    ('eq_iss', r'proceeds from (the )?issuance of (common|preferred|stock)|issuance of (common|preferred)'), ('cff', r'by financing activities'),
    ('fx', r'^effect of exchange rate'), ('net', r'^net (increase|decrease|\(decrease\)|change).*cash'),
    ('beg', r'at beginning of (year|period)'), ('end_r', r'including restricted, at end of (period|year)'), ('end', r'^cash and cash equivalents at end of'),
]
SEG_KEYS = [('bca', r'^commercial airplanes$'), ('bds', r'^(total )?(defense, space (&|and) security|integrated defense systems)$'),
            ('bma', r'^boeing military aircraft'), ('nss', r'^network (&|and) space systems'), ('gss', r'^global services (&|and) support'),
            ('bgs', r'^global services$'), ('bcc', r'^boeing capital'), ('oth', r'^other segment|^other$'),
            ('segop', r'^segment operating profit'), ('unal', r'^unallocated items|^unallocated expense|^accounting differences/eliminations'), ('fascas', r'fas/cas service cost adjustment$'),
            ('tot_rev', r'^total revenues|^sales and other operating revenues$'), ('pems', r'^precision engagement'), ('ss', r'^support systems'),
            ('doj', r'settlement with u.s. department of justice'), ('efo', r'(earnings|loss).*from operations$')]

def match(label, maps):
    n = norm(label)
    for k, pat in maps:
        if re.search(pat, n): return k
    return None

# ---------------------------------------------------------------------------------------------------------------- table helpers
def tbl_text(rows):
    return ' '.join(norm(r[0]) for r in rows)

def colsel(cols, months, year):
    for j, (c0, c1, m, y, d) in enumerate(cols):
        if m == months and y == year: return j
    return None

def read_rows(rows, maps, cols, first=True):
    """{key: {col_index: value}}; first occurrence of each key unless first=False (list of occurrences)."""
    out = {}
    for lab, vals, cells in rows:
        if not vals or not lab: continue
        k = match(lab, maps)
        if not k: continue
        a = T.assign(cols, vals)
        if first and k in out: continue
        out[k] = a
    return out

def classify(tbs):
    kinds = {}
    for i, rows in enumerate(tbs):
        t = tbl_text(rows)
        if 'cost of products' in t and ('diluted' in t) and 'is' not in kinds: kinds['is'] = i
        elif 'accounts payable' in t and 'total current assets' in t and 'bs' not in kinds: kinds['bs'] = i
        elif 'by operating activities' in t and 'by financing activities' in t and 'cf' not in kinds: kinds['cf'] = i
        elif 'commercial airplanes' in t and ('total revenues' in t or 'sales and other operating revenues' in t) and 'from operations' in t and 'cost of products' not in t and 'seg' not in kinds:
            cols, h = T.columns(rows)
            if cols and all(c[2] is not None for c in cols): kinds['seg'] = i
        elif ('sub-total' in t or 'subtotal' in t or 'total unallocated' in t) and ('deferred compensation' in t or 'share-based plans' in t) and 'unal' not in kinds:
            kinds['unal'] = i
        elif any(norm(r[0]).startswith('deliveries') for r in rows[:2]) and any(re.match(r'^7\d7', r[0]) for r in rows) and 'del' not in kinds: kinds['del'] = i
        elif 'backlog' in t and 'commercial airplanes' in t and 'blog' not in kinds: kinds['blog'] = i
    return kinds

# ---------------------------------------------------------------------------------------------------------------- per release
def parse_release(fy, q, rel):
    tbs = T.tables(open(rel['path'], 'rb').read())
    K = classify(tbs)
    ytd = q * 3
    res = {'_kinds': K}
    # statement of operations: 3-month and YTD (current and prior year)
    if 'is' in K:
        rows = tbs[K['is']]; cols, h = T.columns(rows)
        d = read_rows(rows, IS_MAP, cols)
        # unlabeled gross line ("19,637 | 17,393 ...") after total costs
        for m, yr, tag in ((3, fy, 'q'), (ytd, fy, 'ytd'), (3, fy - 1, 'q_py'), (ytd, fy - 1, 'ytd_py')):
            j = colsel(cols, m, yr)
            if j is None: continue
            res.setdefault('is_' + tag, {k: v[j] for k, v in d.items() if j in v})
        # rows not mapped between total costs and earnings from operations (other operating lines)
        others, on = [], False
        for lab, vals, cells in rows:
            k = match(lab, IS_MAP) if lab else None
            if k == 'tot_costs': on = True; continue
            if k == 'efo': break
            if on and lab and k is None and vals:
                a = T.assign(cols, vals); j = colsel(cols, 3, fy)
                if j in a: others.append([lab, a[j]])
        res['is_other_lines'] = others
        res['is_cols'] = [c[2:4] for c in cols]
    if 'bs' in K:
        rows = tbs[K['bs']]; cols, h = T.columns(rows)
        d = read_rows(rows, BS_MAP, cols)
        unl = [T.assign(cols, vals) for lab, vals, cells in rows if not lab and vals]
        if 'ta' not in d and len(unl) >= 2: d['ta'] = unl[0]
        if 'tle' not in d and len(unl) >= 2: d['tle'] = unl[-1]
        if cols:
            res['bs'] = {k: v[0] for k, v in d.items() if 0 in v}
            if len(cols) > 1: res['bs_prior'] = {k: v[1] for k, v in d.items() if 1 in v}
            res['bs_date'] = cols[0][4]
        res['bs_raw'] = [[lab, T.assign(cols, vals).get(0)] for lab, vals, cells in rows if vals and lab]
    if 'cf' in K:
        rows = tbs[K['cf']]; cols, h = T.columns(rows)
        d = read_rows(rows, CF_MAP, cols)
        j = colsel(cols, ytd, fy)
        if j is None and cols: j = 0
        res['cf'] = {k: v[j] for k, v in d.items() if j in v}
        res['cf']['ytd_months'] = ytd
        res['cf_raw'] = [[lab, T.assign(cols, vals).get(j)] for lab, vals, cells in rows if vals and lab]
        jp = colsel(cols, ytd, fy - 1)
        if jp is not None: res['cf_py'] = {k: v[jp] for k, v in d.items() if jp in v}
    if 'seg' in K:
        rows = tbs[K['seg']]; cols, h = T.columns(rows)
        part, rev, efo = 'rev', {}, {}
        for lab, vals, cells in rows:
            if not lab: continue
            n = norm(lab)
            if n.startswith('research and development') or n.startswith('total research'): break
            if not vals:
                if 'from operations' in n or 'operating profit' in n or n.startswith('earnings') or n.startswith('loss'): part = 'efo'
                continue
            k = match(lab, SEG_KEYS)
            if k is None: continue
            a = T.assign(cols, vals)
            tgt = rev if part == 'rev' else efo
            if k == 'tot_rev': rev['tot'] = a; part = 'efo'; continue
            if k == 'efo' and part == 'efo': efo['tot'] = a; part = 'done'; continue
            if part in ('rev', 'efo') and k not in tgt: tgt[k] = a
        for m, yr, tag in ((3, fy, 'q'), (ytd, fy, 'ytd'), (3, fy - 1, 'q_py'), (ytd, fy - 1, 'ytd_py')):
            j = colsel(cols, m, yr)
            if j is None: continue
            res['seg_' + tag] = {'rev': {k: v[j] for k, v in rev.items() if j in v}, 'efo': {k: v[j] for k, v in efo.items() if j in v}}
    if 'unal' not in K and 'seg' in K and 'deferred compensation' in tbl_text(tbs[K['seg']]): K['unal'] = K['seg']
    if 'unal' in K:
        rows = tbs[K['unal']]
        cols, h = T.columns(rows)
        if not cols and 'seg' in K: cols, h = T.columns(tbs[K['seg']])
        # the detail is often the tail of the segment table: locate it inside the table
        for m, yr, tag in ((3, fy, 'q'), (ytd, fy, 'ytd'), (3, fy - 1, 'q_py'), (ytd, fy - 1, 'ytd_py')):
            j = colsel(cols, m, yr)
            if j is None: continue
            items, on = [], False
            for lab, vals, cells in rows:
                n = norm(lab)
                if n.startswith('share-based plans') and vals: on = True
                if on and vals:
                    a = T.assign(cols, vals)
                    if j in a: items.append([lab, a[j]])
                if on and n.startswith('total') and vals: break
            res['unal_' + tag] = items
    if 'del' in K:
        rows = tbs[K['del']]; cols, h = T.columns(rows)
        for m, yr, tag in ((3, fy, 'q'), (ytd, fy, 'ytd'), (3, fy - 1, 'q_py'), (ytd, fy - 1, 'ytd_py')):
            j = colsel(cols, m, yr)
            if j is None: continue
            dl = {}
            for lab, vals, cells in rows:
                n = norm(lab)
                mm = re.match(r'^(7\d7)\b', n)
                if mm or n == 'total':
                    # footnote markers like "(1)" sit in their own cells; keep only cells that align with the column
                    vv = [(c0, c1, t) for c0, c1, t in vals if not re.fullmatch(r'\(\d\)?', t.strip())]
                    a = T.assign(cols, vv)
                    if j in a:
                        key = mm.group(1) if mm else 'tot'
                        if key not in dl: dl[key] = a[j]
                    if n == 'total': break
            res['del_' + tag] = dl
    if 'blog' in K:
        rows = tbs[K['blog']]; cols, h = T.columns(rows)
        bl = {}
        for lab, vals, cells in rows:
            k = match(lab, [('bca', r'^commercial airplanes'), ('bds', r'^(total )?defense, space|^total integrated defense'), ('bgs', r'^global services$'),
                            ('contract', r'^total contractual backlog|^contractual backlog'), ('unob', r'^unobligated backlog'), ('tot', r'^total backlog')])
            if k and vals:
                a = T.assign(cols, vals)
                if 0 in a and k not in bl: bl[k] = a[0]
        unit = 'bn' if 'billions' in tbl_text(rows) else 'm'
        res['backlog'] = {k: (v * 1000 if unit == 'bn' else v) for k, v in bl.items()}
    # summary table 1 and core reconciliation: published core figures
    res['core'] = core_published(tbs, fy, q)
    return res

def core_published(tbs, fy, q):
    """Published core operating earnings / core EPS (and pre-2018 'unallocated pension / postretirement' per-share item) from the
    summary table (Table 1: quarter and year-to-date columns)."""
    out = {}
    for rows in tbs:
        t = tbl_text(rows)
        if 'core' not in t and 'free cash flow' not in t: continue
        cols, h = T.columns(rows)
        if not cols: continue
        ytd = q * 3
        for lab, vals, cells in rows:
            n = norm(lab)
            k = None
            if re.match(r'^core operating earnings( \(non-gaap\))?$', n): k = 'core_oe'
            elif re.match(r'^core (earnings|\(loss\)|loss).*per share( \(non-gaap\))?$', n): k = 'core_eps'
            elif re.match(r'^core operating (\(loss\)|loss|earnings)', n) and 'margin' not in n: k = 'core_oe'
            elif re.match(r'^core (\(loss\)|loss|earnings)(/\(loss\)|/earnings)? per share', n): k = 'core_eps'
            elif re.match(r'^(diluted weighted average|weighted average diluted)', n): k = 'sh_d'
            elif re.match(r'^free cash flow( \(non-gaap\))?$', n): k = 'fcf'
            if not k or not vals: continue
            a = T.assign(cols, vals)
            for m, yr, tag in ((3, fy, 'q'), (ytd, fy, 'ytd'), (3, fy - 1, 'q_py'), (ytd, fy - 1, 'ytd_py')):
                j = colsel(cols, m, yr)
                if j is None or j not in a: continue
                out.setdefault(tag, {}).setdefault(k, a[j])
    return out

# ---------------------------------------------------------------------------------------------------------------- core reconciliation
RC_MAP = [('fascas_pen', r'^pension fas/cas service cost adjustment'), ('fascas_pr', r'^postretirement fas/cas service cost adjustment'),
          ('fascas', r'^fas/cas service cost adjustment$'), ('nonop_pen', r'^non-operating pension'), ('nonop_pr', r'^non-operating postretirement'),
          ('dtax', r'^provision for deferred income taxes on adjustments'), ('sub', r'^subtotal of adjustments'),
          ('unal_pp', r'^unallocated pension/postretirement expense'), ('gaap_eps', r'^(gaap )?diluted (earnings|\(loss\)|loss).*per share'),
          ('core_eps', r'^core (earnings|\(loss\)|loss).*per share'), ('core_oe', r'^core operating (earnings|\(loss\)|loss)(?!.*margin)'),
          ('efo', r'^(gaap )?(earnings|\(loss\)|loss).*from operations'), ('sh', r'weighted average')]
PER = [(r'fourth quarter|third quarter|second quarter|first quarter', 3), (r'first half|six months', 6), (r'nine months|first nine', 9),
       (r'full year|twelve months|year ended', 12)]

def _grp_months(t):
    t = t.lower()
    if 'guidance' in t or 'outlook' in t: return None
    for pat, m in PER:
        if re.search(pat, t): return m
    return None

def core_recon(tbs, fy, q):
    """{tag: {item: {'usd': x, 'ps': y}}} from the reconciliation tables. tag: q / ytd / q_py / ytd_py."""
    out = {}
    ytd = q * 3
    for rows in tbs:
        t = tbl_text(rows)
        if 'core' not in t or not ('fas/cas' in t or 'pension/postretirement' in t): continue
        # header: group cells with (months, year) — either 'Second Quarter 2026' cells, or group row + year row
        hdr, grp_i = [], None
        for i, (lab, vals, cells) in enumerate(rows[:6]):
            g = []
            for c0, c1, txt in cells:
                ym = T.YEAR.search(txt); m = _grp_months(txt)
                if m and ym: g.append((c0, c1, m, int(ym.group(0))))
            if g: hdr, grp_i = g, i; break
        if not hdr:
            cols, h = T.columns(rows)
            if not cols: continue
            hdr = [(c0, c1, m, y) for c0, c1, m, y, d in cols if m]
            grp_i = h
            sub = None
        # sub-columns ($ millions | Per Share)
        sub = None
        if grp_i is not None and grp_i + 1 < len(rows):
            cells = rows[grp_i + 1][2]
            if any('per share' in c[2].lower() for c in cells):
                sub = [(c0, c1, 'ps' if 'per share' in txt.lower() else 'usd') for c0, c1, txt in cells if 'million' in txt.lower() or 'per share' in txt.lower()]
        seen = {}
        for lab, vals, cells in rows:
            if not lab or not vals: continue
            k = match(lab, RC_MAP)
            if not k: continue
            seen[k] = seen.get(k, 0) + 1
            for c0, c1, txt in vals:
                v = T.parse_num(txt)
                if v is None: continue
                # group: overlap, else nearest group start to the left
                g = [h for h in hdr if h[0] <= c1 and c0 <= h[1]]
                if not g:
                    left = [h for h in hdr if h[0] <= c0]
                    g = [max(left, key=lambda h: h[0])] if left else []
                if not g: continue
                m, y = g[0][2], g[0][3]
                tags = [t_ for (mm, yy), t_ in (((3, fy), 'q'), ((ytd, fy), 'ytd'), ((3, fy - 1), 'q_py'), ((ytd, fy - 1), 'ytd_py')) if (mm, yy) == (m, y)]
                if not tags: continue
                if sub:
                    s = [x for x in sub if x[0] <= c1 and c0 <= x[1] and g[0][0] <= x[0] <= g[0][1] + 6]
                    kind = s[0][2] if s else ('ps' if abs(v) < 100 and '.' in txt else 'usd')
                else:
                    kind = 'ps' if k in ('gaap_eps', 'core_eps') else ('usd' if seen[k] == 1 else 'ps')
                if k == 'unal_pp' and not sub: kind = 'usd' if seen[k] == 1 else 'ps'
                for tag in tags:
                    out.setdefault(tag, {}).setdefault(k, {}).setdefault(kind, v)
    return out


# ---------------------------------------------------------------------------------------------------------------- period records
def pk(fy, q): return str(fy) if q == 4 and fy is not None and q is None else f'Q{q}-{str(fy)[2:]}'

def record(fy, q, R, F, ann=False):
    """One period. ann=True: fiscal year fy from the Q4 release twelve-month columns; else quarter q of fy (three-month columns)."""
    rq = (fy, 4) if ann else (fy, q)
    rel = R.get(rq)
    if not rel: return None
    r = parse_release(*rq, rel)
    rc = core_recon(T.tables(open(rel['path'], 'rb').read()), *rq)
    tag = 'ytd' if ann else 'q'
    key = str(fy) if ann else f'Q{q}-{str(fy)[2:]}'
    out = {'period': key, 'fy': fy, 'q': None if ann else q,
           'sources': {'release': rel['url'], 'release_date': rel['date'], 'filing': F.get((fy, 4 if ann else q))},
           'notes': [],
           'is': r.get('is_' + tag, {}), 'is_other_lines': r.get('is_other_lines', []) if not ann else [],
           'seg': r.get('seg_' + tag, {}), 'unal': r.get('unal_' + tag, []), 'deliveries': r.get('del_' + tag, {}),
           'core_pub': (r.get('core') or {}).get(tag, {}), 'core_recon': rc.get(tag, {}),
           'cf': r.get('cf', {}) if (ann or q) else {}, 'cf_raw': r.get('cf_raw', []),
           'bs': r.get('bs', {}), 'bs_date': r.get('bs_date'), 'bs_raw': r.get('bs_raw', []), 'backlog': r.get('backlog', {})}
    if ann and out['cf'].get('ytd_months') != 12: out['notes'].append('cash flow not twelve months')
    # prior-year comparatives as presented one year later (restatement detection)
    nxt = R.get((fy + 1, 4 if ann else q))
    if nxt:
        rn = parse_release(*((fy + 1, 4) if ann else (fy + 1, q)), nxt)
        rcn = core_recon(T.tables(open(nxt['path'], 'rb').read()), *((fy + 1, 4) if ann else (fy + 1, q)))
        out['py'] = {'release': nxt['url'], 'is': rn.get('is_' + tag + '_py', {}), 'seg': rn.get('seg_' + tag + '_py', {}),
                     'deliveries': rn.get('del_' + tag + '_py', {}), 'core_pub': (rn.get('core') or {}).get(tag + '_py', {}),
                     'core_recon': rcn.get(tag + '_py', {}), 'cf': rn.get('cf_py', {}) if ann else {}}
    return out

def periods():
    out = [(y, None) for y in range(2006, 2026)]
    out += [(y, q) for y in range(2013, 2027) for q in (1, 2, 3, 4) if not (y == 2026 and q > 2)]
    return out

if __name__ == '__main__':
    R, F = releases(), filings_10()
    want = sys.argv[1:]
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    for fy, q in periods():
        key = str(fy) if q is None else f'Q{q}-{str(fy)[2:]}'
        if want and key not in want: continue
        rec = record(fy, q, R, F, ann=q is None)
        if rec is None: print(key, 'no release'); continue
        # cash flow of quarters is year to date: the record keeps the YTD statement
        json.dump(rec, open(os.path.join(HERE, 'data', key + '.json'), 'w'), indent=1)
        print(key, rec['sources']['release_date'], rec['is'].get('rev'), rec['is'].get('efo'), rec['seg'].get('efo', {}).get('bca'),
              rec['deliveries'].get('tot'), rec['core_pub'].get('core_eps'), rec['cf'].get('cfo'), rec['bs'].get('ta'))
