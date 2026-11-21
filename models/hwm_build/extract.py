"""Per-period extraction from the Howmet Aerospace EDGAR sources into data/<period>.json (schema: EXTRACTION_SCHEMA.md).

Periods: quarters Q1-20 .. Q3-26 and years 2019 .. 2025. Each period is taken from its own earnings release (8-K Item 2.02,
Ex. 99.1: current-quarter column; full-year statement of the fourth-quarter release) = as originally reported, except the
periods before the 1-Apr-2020 separation of Arconic Corporation, which exist on the Howmet (continuing-operations) basis only
as recast comparatives: Q1-20 from the Q1-21 release (prior-year quarter column) and FY2019 from the Q4-20 release (prior-year
column). Segment data come from the release 'Segment Information' panels (every release prints 5-10 quarters / years).
Nothing is estimated: a line a release does not show is omitted; '—' is 0. USD millions, per share in USD, shares in millions.
"""
import json, os, re, glob
import parse_release as P
import xbrl

S = os.environ.get('HWM_SRC', '/tmp/hwm_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
ARCH = 'https://www.sec.gov/Archives/edgar/data/4281/'
SEGS = [('ep', 'Engine Products'), ('fs', 'Fastening Systems'), ('es', 'Engineered Structures'), ('fw', 'Forged Wheels')]

def qk(y, q): return f'Q{q}-{str(y)[2:]}'

# ------------------------------------------------------------------ release index
def release_index():
    """(year, quarter) -> {'date', 'url', 'secs'}: the earnings release that first reported the quarter."""
    rel = {}
    for o in json.load(open(os.path.join(S, 'filings.json'))):
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        for doc in o['files']:
            if doc == o['primary']: continue
            p = os.path.join(S, 'txt', f"{o['date']}_8-K_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
            if not os.path.exists(p): continue
            secs = P.sections(open(p).read())
            if not {'is', 'bs', 'cf', 'seg'} <= {s[0] for s in secs}: continue
            y, mth = int(o['date'][:4]), int(o['date'][5:7])
            key = (y - 1, 4) if mth <= 3 else (y, 1) if mth <= 6 else (y, 2) if mth <= 9 else (y, 3)
            rel.setdefault(key, dict(date=o['date'], url=ARCH + o['acc'].replace('-', '') + '/' + doc, secs=secs))
    return rel

# ------------------------------------------------------------------ statements
IS_MAP = [('rev', r'^sales$'), ('cogs', r'^cost of goods sold'), ('sga', r'^selling, general'), ('rd', r'^research and development'),
          ('da', r'^provision for depreciation'), ('restr', r'^restructuring and other'), ('oi', r'^operating income'),
          ('loss_debt', r'^loss on debt redemption'), ('int', r'^interest expense'), ('oth', r'^other (expense|\(income\)|income)'),
          ('ebt', r'^income (\(loss\) )?(from continuing operations )?before income taxes'), ('tax', r'^\(?(provision|benefit)\)? .*income taxes'),
          ('cont', r'^(income|loss)( \(loss\))? from continuing operations after income taxes'),
          ('disc', r'^(income|loss)( \(loss\))? from discontinued operations after income taxes'), ('ni', r'^net income( \(loss\))?$')]

def ext_is(rows, col):
    out = {}
    for k, rx in IS_MAP:
        v = P.find(rows, rx, col)
        if v is not None: out[k] = v
    ib = P.index(rows, r'basic')
    idl = P.index(rows, r'diluted', (ib or 0) + 1) if ib is not None else None
    def blk(start, end):
        sub = rows[start:end] if start is not None else []
        e = P.find(sub, r'^net income( \(loss\))? per share', col)
        c = P.find(sub, r'^continuing operations', col)
        sh = P.find(sub, r'^average (number of shares|shares outstanding)', col)
        d = P.find(sub, r'^discontinued operations', col)
        if e is None and c is not None and d is not None:        # full-year statements of 2019-20 print continuing and discontinued per-share lines only
            e = round(c + d, 2); out['eps_total_computed'] = 1
        return (e if e is not None else c), c, sh
    if ib is not None and idl is not None:
        out['eps_b'], cb, out['sh_b'] = blk(ib, idl)
        out['eps_d'], cd, out['sh_d'] = blk(idl, len(rows))
        if cd is not None: out['eps_d_cont'] = cd
        if cb is not None: out['eps_b_cont'] = cb
    so = P.find(rows, r'^common stock outstanding at the end', col)
    if so is not None: out['sh_out'] = so
    if out.get('sh_b') is None:           # full-year statements of 2020-21 list average shares after the per-share lines
        out['sh_b'] = P.find(rows, r'^average shares outstanding - basic', col); out['sh_d'] = P.find(rows, r'^average shares outstanding - diluted', col)
    for k in ('sh_b', 'sh_d', 'sh_out'):
        if out.get(k) is not None and out[k] > 1e5: out[k] = round(out[k] / 1e6, 6)
    return {k: v for k, v in out.items() if v is not None}

BS_MAP = [('cash', r'^cash and cash equivalents'), ('ar', r'^receivables from customers'), ('oth_rec', r'^other receivables'), ('inv', r'^inventories'),
          ('prepaid', r'^prepaid expenses'), ('disc_ca', r'^current assets of discontinued'), ('tca', r'^total current assets'),
          ('ppe', r'^properties, plants'), ('gw', r'^goodwill'), ('dta', r'^deferred income taxes'), ('intang', r'^intangibles'),
          ('onca', r'^other noncurrent assets'), ('disc_nca', r'^non ?current assets of discontinued'), ('ta', r'^total assets'),
          ('ap', r'^accounts payable'), ('accr_comp', r'^accrued compensation'), ('taxes', r'^taxes, including'), ('accr_int', r'^accrued interest'),
          ('defrev', r'^deferred revenue'), ('ocl', r'^other current liabilities'), ('std', r'^short-term (debt|borrowings)'),
          ('cltd', r'^long-term debt due within one year'), ('disc_cl', r'^current liabilities of discontinued'), ('tcl', r'^total current liabilities'),
          ('ltd', r'^long-term debt(, less amount due within one year)?$'), ('pension', r'^accrued pension'), ('opeb', r'^accrued other postretirement'),
          ('oncl', r'^other noncurrent liabilities'), ('disc_ncl', r'^non ?current liabilities of discontinued'), ('tl', r'^total liabilities$'),
          ('pref', r'^preferred stock'), ('common', r'^common stock$'), ('apic', r'^additional capital'), ('re', r'^retained earnings'),
          ('aoci', r'^accumulated other comprehensive'), ('nci', r'^noncontrolling interests'), ('teq', r'^total equity'), ('tle', r'^total liabilities and equity')]
CF_MAP = [('ni', r'^net income'), ('da', r'^depreciation and amortization'), ('deftax', r'^deferred income taxes'), ('restr', r'^restructuring and other'),
          ('sbc', r'^stock-based compensation'), ('pension_cost', r'^net periodic pension'), ('pension_contrib', r'^pension contributions'),
          ('cfo', r'^cash (provided|\(?used).*operations$'), ('st_change', r'^net change in (short-term borrowings|commercial paper)'),
          ('debt_add', r'^additions to debt'), ('debt_pay', r'^(payments on debt|repurchases and payments on debt)'), ('debt_costs', r'^debt issuance costs'),
          ('debt_prem', r'^premiums paid'), ('options', r'^proceeds from exercise'), ('div', r'^dividends paid'), ('bb', r'^repurchases? of common stock'),
          ('tax_withheld', r'^taxes paid for net share settlement'), ('pref_red', r'^redemption of preferred'), ('arconic', r'^net cash transferred'),
          ('cff', r'^cash (provided|\(?used).*financing activities$'), ('capex', r'^capital expenditures'), ('acq', r'^acquisitions, net'),
          ('divest', r'^proceeds from the sale of assets'), ('sold_rec', r'^cash receipts from sold receivables'),
          ('cfi', r'^cash (provided|\(?used).*investing activities$'), ('fx', r'^effect of exchange rate'), ('net', r'^net change in cash'),
          ('beg', r'^cash, cash equivalents and restricted cash at beginning'), ('end', r'^cash, cash equivalents and restricted cash at end')]

def ext_map(rows, mp, col):
    out = {}
    for k, rx in mp:
        v = P.find(rows, rx, col)
        if v is not None: out[k] = v
    return out

# ------------------------------------------------------------------ segment panels
def ext_panel(secs):
    """-> {period: {key: value}} from the Segment Information panel and the segment-to-consolidated reconciliation of one release."""
    out, per, seg = {}, None, None
    for ty, title, rows in secs:
        if ty not in ('seg', 'calc'): continue
        if ty == 'calc' and not re.search(r'total segment', title, re.I): continue
        seg = None
        for lab, vals, cells in rows:
            h = P.panel_header(cells)
            if h: per = h; continue
            if per is None: continue
            name = next((k for k, n in SEGS if lab.strip() == n), None)
            if name and len(cells) == 1: seg = name; continue
            nums = [v for v in vals if v is not None]
            if len(nums) != len(per): continue
            L = lab.lower()
            key = None
            if seg and ty == 'seg':
                key = ('tps' if L.startswith('third-party sales') else 'inter' if L.startswith('inter-segment') else
                       'da' if L.startswith('provision for depreciation') else 'op' if L == 'segment operating profit' else
                       'ebitda' if L == 'segment adjusted ebitda' else 'restr' if L.startswith('restructuring') else
                       'capex' if L.startswith('capital expenditures') else None)
                if key: key = f'{seg}_{key}'
            elif ty == 'calc':
                key = ('tot_op' if L.startswith('total segment operating profit') else 'tot_ebitda' if L.startswith('total segment adjusted ebitda') else
                       'corp' if L.startswith('corporate expense') else 'seg_da' if L.startswith('segment provision for depreciation') else
                       'unalloc_restr' if L.startswith('restructuring') else 'oi' if re.match(r'(consolidated )?operating income', L) else None)
            if key:
                for p, v in zip(per, nums): out.setdefault(p, {}).setdefault(key, v)
    return out

# ------------------------------------------------------------------ non-GAAP reconciliations
def numcols(rows, i): return [v for v in rows[i][1] if v is not None]

def pick_col(rows, rx, target, prefer):
    """column whose anchor-row value equals the period's own figure (prefer: 'q' -> third column of a quarter block, 'last')."""
    i = P.index(rows, rx)
    while i is not None:
        nums = numcols(rows, i)
        hits = [j for j, v in enumerate(nums) if target is not None and abs(v - target) < 0.51]
        if hits:
            if prefer == 'q': return i, (2 if 2 in hits else hits[-1] if len(nums) <= 3 else hits[0])
            return i, (hits[-1] if prefer == 'last' else hits[0])
        i = P.index(rows, rx, i + 1)
    return None, None

ADJ_NI = r'^(adjusted net income|net income excluding special items|income( \(loss\))? from continuing operations,? excluding special items)'
ADJ_EPS = r'^(adjusted eps|diluted eps excluding special items)'
def ext_ngaap(secs, isd, cfo_q, prefer):
    n = {}
    target = isd.get('cont', isd.get('ni'))
    for ty, title, rows in secs:
        if ty != 'calc' or re.search(r'total segment', title, re.I): continue
        labs = ' || '.join(l.lower() for l, _, _ in rows)
        if re.search(r'\|\| (adjusted net income|net income excluding special items|income( \(loss\))? from continuing operations,? excluding special items)( \|\||$)', labs) and 'adj_ni' not in n:
            i, j = pick_col(rows, r'^(net (income|loss)( \(loss\))?|(\(loss\) income|income \(loss\)|income|loss) from continuing operations)$', target, prefer)
            if i is None: continue
            end = P.index(rows, ADJ_NI, i + 1)
            items = []
            for lab, vals, cells in rows[i + 1:end]:
                nums = [v for v in vals if v is not None]
                if len(nums) > j and not re.match(r'(diluted |)(earnings|eps)|average number|special items:?$|(continuing|discontinued) operations', lab, re.I):
                    items.append([re.sub(r'\s*\(\d\)', '', lab).strip(), nums[j]])
            n['items'] = items
            n['adj_ni'] = numcols(rows, end)[j]
            e = P.index(rows, ADJ_EPS, end)
            if e is not None and len(numcols(rows, e)) > j: n['adj_eps'] = numcols(rows, e)[j]
            sh = P.index(rows, r'^average number of (diluted )?shares', i)
            if sh is not None and len(numcols(rows, sh)) > j:
                v = numcols(rows, sh)[j]; n['adj_sh'] = round(v / 1e6, 6) if v > 1e5 else v
        if re.search(r'\|\| (adjusted operating income|operating income excluding special items)( excluding special items)?( \|\||$)', labs) and 'adj_oi' not in n:
            i, j = pick_col(rows, r'^operating income( \(loss\))?$', isd.get('oi'), prefer)
            if i is not None:
                e = P.index(rows, r'^(adjusted operating income|operating income excluding special items)( excluding special items)?$', i)
                n['adj_oi'] = numcols(rows, e)[j]
                n['oi_items'] = [[re.sub(r'\s*\(\d\)', '', l).strip(), [v for v in vs if v is not None][j]] for l, vs, _ in rows[i + 1:e]
                                 if len([v for v in vs if v is not None]) > j and not re.match(r'add:?$|operating income|sales', l, re.I)]
        if re.search(r'\|\| adjusted ebitda', labs) and 'adj_ebitda' not in n and 'pass through' not in title.lower():
            i, j = pick_col(rows, r'^(operating income( \(loss\))?|net income|income( \(loss\))? from continuing operations after income taxes)$',
                            None, prefer)
            for rx, tg in ((r'^operating income( \(loss\))?$', isd.get('oi')), (r'^(net income|income( \(loss\))? from continuing operations after income taxes)$', target),
                           (r'^(third-party )?sales$', isd.get('rev'))):
                i, j = pick_col(rows, rx, tg, prefer)
                if i is not None: break
            if i is not None:
                e = P.index(rows, r'^adjusted ebitda,? excluding special items', 0)
                if e is None: e = P.index(rows, r'^adjusted ebitda$', 0)
                if len(numcols(rows, e)) > j: n['adj_ebitda'] = numcols(rows, e)[j]
                b = P.index(rows, r'^adjusted ebitda$', 0)
                if b is not None and b != e and len(numcols(rows, b)) > j: n['ebitda_pre_special'] = numcols(rows, b)[j]
        if re.search(r'(^|\|\| )(adjusted )?free cash flow( \(a\))?( \|\||$)', labs) and 'fcf' not in n and cfo_q is not None:
            i, j = pick_col(rows, r'^cash (provided|\(?used).*operations$', cfo_q, 'first' if prefer == 'q' else 'last')
            if i is not None:
                e = P.index(rows, r'^(adjusted )?free cash flow( \(a\))?$', i)
                n['fcf'] = numcols(rows, e)[j]; n['fcf_label'] = rows[e][0]
                n['fcf_lines'] = [[l, [v for v in vs if v is not None][j]] for l, vs, _ in rows[i:e] if len([v for v in vs if v is not None]) > j]
        if re.search(r'organic revenue', title, re.I) and 'organic' not in n and prefer == 'q':
            org = {}
            for lab, vals, cells in rows:
                nums = [v for v in vals if v is not None]
                k = next((k for k, nm in SEGS if lab.strip() == nm), 'tot' if lab.strip() == 'Total' else None)
                if k and len(nums) == 8:
                    org[k] = dict(py_sales=nums[0], py_ad=nums[1], py_org=nums[2], sales=nums[3], ad=nums[4], org=nums[5], g=nums[6] / 100, g_org=nums[7] / 100)
            if org: n['organic'] = org
    return n


# ------------------------------------------------------------------ end-market revenue (10-Q / 10-K revenue note)
EM_LAB = [('ca', r'^aerospace - commercial'), ('df', r'^aerospace - defense'), ('aero', r'^aerospace$'), ('ct', r'^commercial transportation'),
          ('io', r'^industrial and other$'), ('gt', r'^(industrial gas turbines?|gas turbines)$'), ('og', r'^oil and gas'), ('gi', r'^general industrial'),
          ('oth', r'^other$'), ('tot', r'^total end-market revenue')]
def em_blocks(path):
    """-> list of {market: consolidated total} in document order (10-Q: quarter, prior-year quarter, year to date, prior year to date;
    10-K: year, prior year, two years ago). The last numeric cell of each row is the consolidated total."""
    out, cur = [], {}
    for line in open(path).read().split('\n'):
        cells = [c.strip() for c in line.split(' | ')]
        nums = [P.pnum(c) for c in cells[1:]]
        nums = [v for v in nums if v is not None]
        k = next((k for k, rx in EM_LAB if re.match(rx, cells[0].lower())), None)
        if not k or not nums: continue
        cur[k] = nums[-1]
        if k == 'tot': out.append(cur); cur = {}
    for b in out:
        if 'io' not in b and 'gt' in b: b['io'] = b['gt'] + b.get('og', 0.0) + b.get('gi', 0.0) + b.get('oth', 0.0)
        if 'aero' not in b and 'ca' in b: b['aero'] = b['ca'] + b['df']
    return out

def filing_index():
    fi = {}
    for o in json.load(open(os.path.join(S, 'filings.json'))):
        if o['form'] not in ('10-Q', '10-K'): continue
        y, mth = int(o['report'][:4]), int(o['report'][5:7])
        p = os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{o['primary'].rsplit('.', 1)[0]}.txt")
        fi[(y, mth // 3)] = dict(path=p, url=ARCH + o['acc'].replace('-', '') + '/' + o['primary'], form=o['form'], date=o['date'])
    return fi

def add_em(recs):
    fi = filing_index()
    def sub(a, b): return {k: round(a[k] - b[k], 6) for k in a if k in b}
    for p, r in recs.items():
        y, q = r['year'], r['q']
        em, src, note = None, None, None
        if q is None:
            f = fi.get((y, 4)) if y >= 2020 else fi.get((2020, 4))
            b = em_blocks(f['path']); em = b[0] if y >= 2020 else b[1]; src = f['url']
            if y == 2019: note = 'End-market revenue for 2019 from the prior-year column of the 2020 Form 10-K (continuing operations).'
        elif (y, q) in ((2020, 1), (2020, 2)):
            f = fi[(2021, q)]; b = em_blocks(f['path']); em = b[1]; src = f['url']
            note = f'End-market revenue for Q{q}-20 from the prior-year column of the Q{q}-21 Form 10-Q (commercial / defense aerospace split first shown in Q3-20).'
        elif q in (1, 2, 3):
            f = fi[(y, q)]; em = em_blocks(f['path'])[0]; src = f['url']
        else:
            fk, f9 = fi[(y, 4)], fi[(y, 3)]
            em = sub(em_blocks(fk['path'])[0], em_blocks(f9['path'])[2]); src = fk['url']
            note = 'End-market revenue for Q4 = year (Form 10-K) − nine months (Q3 Form 10-Q).'
        if em and y == 2025 and q:          # gas turbines / other basis (FY2025 Form 10-K): 2025 quarters from the 2026 Form 10-Q comparatives
            if q < 4: b = em_blocks(fi[(2026, q)]['path'])[1]
            else: b = sub(em_blocks(fi[(2025, 4)]['path'])[0], em_blocks(fi[(2026, 3)]['path'])[3])
            em = dict(em); em.pop('og', None); em.pop('gi', None)
            em['gt'], em['oth'] = b['gt'], b['oth']; em['io'] = b['gt'] + b['oth']
            r['notes'].append('Gas turbines / other end markets (basis introduced in the FY2025 Form 10-K): 2025 quarter from the prior-year column of the 2026 Form 10-Q'
                              + (' (Q4 = year − nine months).' if q == 4 else '.'))
        if em:
            r['em'] = em; r['sources']['filing'] = src
            if note: r['notes'].append(note)

# ------------------------------------------------------------------ records
def note_text(secs, rx):
    for ty, title, rows in secs:
        for lab, vals, cells in rows:
            t = ' '.join(cells)
            if re.search(rx, t, re.I): return t
    return None

def build():
    rel = release_index()
    os.makedirs(OUT, exist_ok=True)
    panels = {k: ext_panel(v['secs']) for k, v in rel.items()}
    recs, prev_cfo = {}, {}
    def panel_for(p, own, later):
        """own-release panel values + '_rc' values from the later release that re-presents the period (recast detection)."""
        d = dict(panels.get(own, {}).get(p, {}))
        for k in later:
            for kk, v in panels.get(k, {}).get(p, {}).items():
                if kk not in d: d[kk] = v; d.setdefault('_from_later', []).append(kk)
                elif d[kk] != v and (kk + '_rc') not in d and kk not in d.get('_from_later', []): d[kk + '_rc'] = v
        return d
    for y in range(2020, 2027):
        ytd_prev = None
        for q in (1, 2, 3, 4):
            if (y, q) > (2026, 3): break
            p = qk(y, q); notes = []
            own = (y, q)
            if (y, q) == (2020, 1):
                src = rel[(2021, 1)]; col = 2
                notes.append('Q1-20 is the prior-year column of the Q1-21 release (continuing operations after the 1-Apr-2020 Arconic Corporation separation); '
                             'the Q1-20 release itself reported consolidated Arconic Inc. Balance sheet at 31-Mar-2020 not shown (pre-separation). '
                             'Cash flow includes Arconic Corporation (not segregated by the company).')
            else:
                src = rel[own]; col = 0
            secs = src['secs']
            isd = ext_is(P.rows_of(secs, 'is', 0), col)
            r = dict(period=p, year=y, q=q, sources=dict(release=src['url'], release_date=src['date']), notes=notes)
            r['is'] = isd
            if (y, q) != (2020, 1): r['bs'] = ext_map(P.rows_of(secs, 'bs'), BS_MAP, 0)
            cf = ext_map(P.rows_of(secs, 'cf'), CF_MAP, 1 if (y, q) == (2020, 1) else 0)
            if (y, q) == (2020, 2):      # H1-20 cash flow as revised in the Q3-20 10-Q (accounts payable / capital expenditures misclassification)
                cf = ext_map(P.rows_of(rel[(2021, 2)]['secs'], 'cf'), CF_MAP, 1)
                notes.append('Cash flow for the six months ended 30-Jun-2020 is the prior-year column of the Q2-21 release: the company revised the classification of '
                             'changes in accounts payable and capital expenditures in Q3-20, so the originally reported H1-20 statement is not comparable with 9M / FY2020.')
            cf['ytd_months'] = 3 * q; r['cf'] = cf
            cfo_q = cf.get('cfo') - (ytd_prev or 0.0) if cf.get('cfo') is not None else None
            ytd_prev = cf.get('cfo')
            later = [(y, qq) for qq in range(q + 1, 5)] + [(y + 1, qq) for qq in (1, 2, 3, 4)] + [(y + 2, qq) for qq in (1, 2, 3, 4)]
            r['seg'] = panel_for(p, own if (y, q) != (2020, 1) else (2020, 2), [k for k in later if k in rel])
            if (y, q) == (2020, 1):
                r['ngaap'] = {}
                pr = ext_ngaap(secs, dict(isd, ni=isd.get('ni')), None, 'first')      # prior-year column of the Q1-21 reconciliations
                r['ngaap'] = {k: v for k, v in pr.items() if k in ('adj_ni', 'adj_eps', 'items', 'adj_oi', 'oi_items', 'adj_ebitda', 'adj_sh')}
            else:
                r['ngaap'] = ext_ngaap(secs, isd, cfo_q, 'q')
            recs[p] = r
        if y <= 2025:
            src = rel[(y, 4)]; secs = src['secs']
            p = str(y)
            r = dict(period=p, year=y, q=None, sources=dict(release=src['url'], release_date=src['date']), notes=[])
            r['is'] = ext_is(P.rows_of(secs, 'is', 1), 0)
            r['bs'] = ext_map(P.rows_of(secs, 'bs'), BS_MAP, 0)
            cf = ext_map(P.rows_of(secs, 'cf'), CF_MAP, 0); cf['ytd_months'] = 12; r['cf'] = cf
            later = [(y + 1, qq) for qq in (1, 2, 3, 4)] + [(y + 2, qq) for qq in (1, 2, 3, 4)]
            r['seg'] = panel_for(p, (y, 4), [k for k in later if k in rel])
            r['ngaap'] = ext_ngaap(secs, r['is'], cf.get('cfo'), 'last')
            recs[p] = r
    # FY2019: prior-year column of the Q4-20 release (recast to continuing operations)
    src = rel[(2020, 4)]; secs = src['secs']
    r = dict(period='2019', year=2019, q=None, sources=dict(release=src['url'], release_date=src['date']),
             notes=['FY2019 is the prior-year column of the Q4-20 release (Arconic Corporation in discontinued operations). Balance sheet and cash flow at / for 2019 are '
                    'not used: the cash flow was not segregated and the balance sheet carries the assets of discontinued operations.'])
    r['is'] = ext_is(P.rows_of(secs, 'is', 1), 1)
    r['seg'] = dict(panels[(2020, 4)].get('2019', {}))
    r['ngaap'] = {k: v for k, v in ext_ngaap(secs, r['is'], None, 'first').items() if k in ('adj_ni', 'adj_eps', 'items', 'adj_oi', 'oi_items', 'adj_ebitda', 'adj_sh')}
    recs['2019'] = r
    # XBRL extras (10-K / 10-Q as first filed): dividends declared per share
    for p, r in recs.items():
        y, q = r['year'], r['q']
        x = {}
        v = xbrl.value('CommonStockDividendsPerShareDeclared', y, 'Q' if q else 'FY', q, pick='first')
        if v is not None and p not in ('2019', 'Q1-20'): x['dps_decl'] = v
        if x: r['x'] = x
    add_em(recs)
    for f in glob.glob(os.path.join(OUT, '*.json')):
        if not os.path.basename(f).startswith('_'): os.remove(f)
    for p, r in recs.items():
        json.dump(r, open(os.path.join(OUT, p + '.json'), 'w'), indent=1, ensure_ascii=False)
    json.dump({f'{k[0]}Q{k[1]}': dict(date=v['date'], url=v['url']) for k, v in sorted(rel.items())}, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    xbrl.dump_subset(xbrl.USED | set(XCHECK))
    return recs

XCHECK = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'OperatingIncomeLoss', 'NetIncomeLoss', 'EarningsPerShareDiluted',
          'NetCashProvidedByUsedInOperatingActivities', 'Assets', 'CashAndCashEquivalentsAtCarryingValue', 'ShareBasedCompensation',
          'CommonStockSharesOutstanding', 'PaymentsForRepurchaseOfCommonStock', 'StockRepurchasedAndRetiredDuringPeriodShares']

if __name__ == '__main__':
    recs = build()
    print(len(recs), 'records')
    for p, r in recs.items():
        i, n, s = r['is'], r['ngaap'], r['seg']
        print(p, i.get('rev'), i.get('oi'), i.get('ni'), i.get('eps_d'), i.get('sh_d'), '| adj', n.get('adj_oi'), n.get('adj_ebitda'), n.get('adj_ni'), n.get('adj_eps'),
              n.get('fcf'), '| seg', s.get('ep_tps'), s.get('ep_ebitda', s.get('ep_op')), s.get('corp'), s.get('tot_ebitda', s.get('tot_op')),
              '| bs', (r.get('bs') or {}).get('ta'), 'cf', r.get('cf', {}).get('cfo'))
