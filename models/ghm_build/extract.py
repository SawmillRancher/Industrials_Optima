"""Per-period extraction from the Graham Corporation EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2026 (fourth-quarter release, twelve-month column) and quarters Q1 FY13 - Q1 FY27 (that quarter's
release, three-month column; Q4 from the fourth-quarter release three-month column). Each record carries:
  is     statement of operations (USD m; per share in $ as published; shares in m)
  ngaap  EBITDA / adjusted EBITDA, adjusted net income / EPS and adjusted operating profit reconciliations with their items
         (company labels, category), as published in that release
  kpi    orders, backlog, sales / orders / backlog by market and sales by region from the release grids (USD m) or the
         Ex. 99.2 supplemental exhibit (USD thousands, from FY2023), plus the 10-K / 10-Q revenue-note market table
  cf     cash flow, year to date (cf.ytd_months)
  bs     balance sheet at period end
  x      XBRL company facts (cover-page shares outstanding, shares issued / treasury)
  py     prior-year comparative as presented in the following year's release (restatement checks)
  sources / notes
Release units are thousands (statements) or millions (grids); everything is stored in millions. Graham's fiscal year ends
31 March (FY2027 = Apr-2026 - Mar-2027). Stock splits are NOT applied here (normalize.py applies them by release date).
"""
import json, os, re, datetime as dt
import parse_release as P
import xbrl

S = os.environ.get('GHM_SRC', '/tmp/ghm_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '716314'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc
def r6(v): return None if v is None else round(v, 6)
def k2m(v): return None if v is None else round(v / 1000.0, 6)

# ------------------------------------------------------------------ release index: (fy, q) -> release (all exhibits of the 8-K)
MONTHQ = {'june': 1, 'september': 2, 'december': 3, 'march': 4}

def fyq_of_is(tabs):
    t = next((t for t in tabs if t['type'] == 'is' and t['cols']), None)
    if not t: return None
    h = (t['raw'].get('hdr_text') or '').lower()
    m = re.search(r'(june|september|december|march)', h)
    yrs = [int(x) for r in t['hdr'] for x in r if P.YEAR.match(x)]
    if not m or not yrs: return None
    q = MONTHQ[m.group(1)]; y = max(yrs)
    return (y if q == 4 else y + 1), q

def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings = {}, {}
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            tabs_all, main = [], None
            for doc in o['files']:
                if doc == o['primary']: continue
                p = os.path.join(S, 'docs', f"{o['date']}_8-K_{o['acc']}_{doc}")
                if not os.path.exists(p): continue
                tabs = P.parse(open(p, 'rb').read())
                for t in tabs: t['doc'] = doc
                types = {t['type'] for t in tabs}
                if {'is', 'bs', 'cf'} <= types and main is None: main = doc
                tabs_all += tabs
            if main is None: continue
            key = fyq_of_is(tabs_all)
            if key is None: continue
            if key not in rel:               # first full release for the quarter = as originally reported
                rel[key] = dict(date=o['date'], url=url(o, main), acc=o['acc'], tabs=tabs_all, docs=[d for d in o['files'] if d != o['primary']])
        if o['form'] in ('10-Q', '10-K'):
            e = dt.date.fromisoformat(o['report'])
            fy = e.year + (1 if e.month >= 4 else 0)
            q = {6: 1, 9: 2, 12: 3, 3: 4}[e.month]
            filings[(fy, q)] = dict(date=o['date'], url=url(o, o['primary']), path=os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{o['primary']}"), form=o['form'])
    return rel, filings

def colval(t, ci, vals):
    """value of row `vals` in column ci (values are aligned on the table's grid columns)."""
    return vals[ci] if ci < len(vals) else None

# ------------------------------------------------------------------ income statement
IS_MAP = [('rev', r'^net sales$'), ('cogs', r'^cost of (products|goods) sold$'), ('cogs_amort', r'^cost of (products|goods) sold.*amortization'),
          ('gp', r'^gross profit$'), ('sga', r'^selling, general and administrative( expenses?)?$'),
          ('sga_amort', r'^(selling, general and administrative\s*[–\-—]\s*)?amortization( of intangible assets)?$'),
          ('restr', r'^restructuring'), ('impair', r'impairment'), ('oth_op', r'^other operating (expense|income|\(income\) expense|expense \(income\)|income expense)'),
          ('op_profit', r'^operating (profit|income|loss|\(loss\) profit|profit \(loss\)|income \(loss\)|\(loss\) income)$'),
          ('int_inc', r'^interest income$'), ('int_exp', r'^interest expense$'), ('int_net', r'^(net (other )?interest|interest.*,? ?net$|interest \(income\) expense|interest expense \(income\))'),
          ('oth_nonop', r'^other (expense|income|\(income\) expense|expense \(income\)|\(income\)|income \(expense\)),? ?(net)?$'),
          ('ebt', r'before .*income tax'), ('tax', r'^(provision|\(benefit\) provision|provision \(benefit\)|benefit|income tax)'),
          ('cont_ops', r'from continuing operations$'), ('disc_ops', r'discontinued operations'),
          ('ni', r'^net (income|loss|\(loss\) income|income \(loss\)|\(loss\))$'),
          ('dps', r'^(cash )?dividends (declared|paid)? ?per share')]

def ext_is(tabs, mo, cp):
    t = next((t for t in tabs if t['type'] == 'is' and t['cols'] and any(c and c[0] == mo and c[1] == cp for c in t['cols'])), None)
    if not t: return None
    ci = next(i for i, c in enumerate(t['cols']) if c and c[0] == mo and c[1] == cp)
    out, oth_op, nonop, state, eps_state = {}, [], [], 'pre', None
    has_op = any(vals and re.search(IS_MAP[9][1], lab.lower().strip(' :*.…')) for lab, vals in t['rows'])
    for lab, vals in t['rows']:
        L = lab.lower().strip(' :*.…')
        if not vals:
            if L.startswith('basic'): eps_state = 'b'
            elif L.startswith('diluted'): eps_state = 'd'
            elif L.startswith('weighted average'): eps_state = 'sh'
            elif L.startswith('per share'): eps_state = None
            continue
        v = colval(t, ci, vals)
        if v is None: continue
        if eps_state in ('b', 'd') and re.match(r'^net (income|loss|\(loss\) income|income \(loss\))', L):
            out['eps_' + eps_state] = v; continue
        if eps_state in ('b', 'd') and 'continuing' in L:
            out['eps_' + eps_state + '_cont'] = v; continue
        if eps_state in ('b', 'd') and 'discontinued' in L: continue
        if re.search(r'dividends?.*per share', L): out['dps'] = v; continue
        if eps_state == 'sh' or (eps_state is None and L in ('basic', 'diluted')):
            if L.startswith('basic'): out['sh_b'] = v / 1e6 if v > 1e6 else v / 1e3
            elif L.startswith('diluted'): out['sh_d'] = v / 1e6 if v > 1e6 else v / 1e3
            continue
        if re.search(r'margin', L) and 'net' not in L: continue
        if re.search(r'^gross (profit )?margin|^operating (profit )?margin|^net income margin', L): continue
        key = next((k for k, p in IS_MAP if re.search(p, L)), None)
        if key == 'oth_nonop' and state == 'op' and has_op: key = 'oth_op'
        if key in ('int_inc', 'int_exp', 'int_net') and state == 'op': state = 'nonop'
        if key == 'dps': out['dps'] = v; continue
        if key == 'ni' and state == 'post_ni': continue
        if key and key not in out:
            out[key] = k2m(v)
            if key == 'rev': state = 'op'
            if key == 'op_profit': state = 'nonop'
            if key == 'ni': state = 'post_ni'
            continue
        if L.startswith('total'): continue
        if state == 'op' and key is None: oth_op.append([lab, k2m(v)])
        elif state == 'nonop' and key is None: nonop.append([lab, k2m(v)])
        elif key in out and key not in ('rev',): oth_op.append([lab, k2m(v)]) if state == 'op' else nonop.append([lab, k2m(v)])
    out['other_op_lines'] = oth_op; out['nonop_lines'] = nonop
    return out

# ------------------------------------------------------------------ non-GAAP
CAT = [('TAXD', r'valuation allowance|tax act|tax reform|discrete|tax legislation|federal tax rate|tax law'),
       ('TAX', r'tax effect|tax impact|normaliz|income tax effect|tax on adjust'),
       ('AMORT', r'amortization of intangible|intangible amortization'),
       ('STEPUP', r'step[- ]up'),
       ('ERP', r'\berp\b'),
       ('SBC', r'equity-based|stock-based|share-based'),
       ('RESTR', r'restructur|severance'),
       ('IMPAIR', r'impairment'),
       ('ACQ', r'acquisition|integration|transaction|contingent consideration|earn-?out|business development'),
       ('LEGAL', r'legal|settlement|litigation'),
       ('TRANS', r'transition'), ('BNBONUS', r'performance bonus'), ('DEBT', r'debt amendment|extinguishment'), ('ERC', r'erc tax credit'),
       ('BADDEBT', r'bad debt'),
       ('GAIN', r'gain|loss on sale|sale of')]
STRUCT = re.compile(r'^(\+|-|−)?\s*(net interest|interest|income tax(es)?( expense| provision| \(benefit\))?|provision|depreciation|net income|net \(loss\)|net loss|ebitda|adjusted|diluted weighted|gaap net income|net sales|net income margin|adjusted ebitda margin|operating (profit|loss|\(loss\))|income tax provision)', re.I)

def cat(lab):
    L = lab.lower()
    return next((c for c, p in CAT if re.search(p, L)), 'OTHER')

def ext_recon(t, ci, unit):
    """one reconciliation table / column -> {'start', 'items': [[label, amount, cat]], totals}"""
    f = (lambda v: k2m(v)) if unit == 'k' else (lambda v: r6(v))
    out = {'items': []}
    for lab, vals in t['rows']:
        if not vals: continue
        v = colval(t, ci, vals)
        if v is None: continue
        L = re.sub(r'\s*\(\d\)$', '', lab.lower().strip(' :*.'))
        if 'per share' in L or 'per diluted' in L:
            if L.startswith('adjusted'): out['adj_eps'] = v
            elif L.startswith(('gaap', 'net')): out['gaap_eps'] = v
            continue
        if re.match(r'^(net (income|loss|\(loss\)( income)?|income \(loss\)))', L) and 'start' not in out and 'per' not in L and 'margin' not in L:
            out['start'] = f(v); out['start_label'] = lab; continue
        if re.match(r'^operating', L) and 'start' not in out and 'margin' not in L:
            out['start'] = f(v); out['start_label'] = lab; continue
        if re.match(r'^adjusted ebitda$', L): out['adj_ebitda'] = f(v); continue
        if re.match(r'^ebitda$', L): out['ebitda'] = f(v); continue
        if re.match(r'^adjusted net (income|loss|\(loss\) income|income \(loss\))( \(loss\))?$', L): out['adj_ni'] = f(v); continue
        if re.match(r'^adjusted net (income|loss).*per diluted share', L): out['adj_eps'] = v; continue
        if re.match(r'^adjusted operating', L) and 'margin' not in L: out['adj_op'] = f(v); continue
        if re.match(r'^(gaap )?net (income|loss).*per diluted share', L): out['gaap_eps'] = v; continue
        if re.match(r'^diluted weighted', L): out['sh_d'] = v / 1e3; continue
        if re.search(r'margin|^net sales', L): continue
        if re.match(r'^(\+|-|−)?\s*(net interest|interest (expense|income))', L): out['int'] = f(v); continue
        if re.match(r'^(\+|-|−)?\s*(income tax|provision|tax provision)', L) and not re.search(r'effect|impact|normaliz', L): out['tax'] = f(v); continue
        if re.match(r'^(\+|-|−)?\s*depreciation', L): out['dda'] = f(v); continue
        it = [lab, f(v), cat(lab)]
        if 'net of tax' in L: it.append('net_of_tax')
        out['items'].append(it)
    return out

def ext_ngaap(tabs, mo, cp, ref_ni_k):
    o = {}
    for ty, key in (('ebitda', 'ebitda'), ('adjni', 'adjni'), ('adjop', 'adjop')):
        for t in tabs:
            if t['type'] != ty or not t['cols']: continue
            idx = [i for i, c in enumerate(t['cols']) if c and c[0] == mo and c[1] == cp and c[2] == 'v']
            if not idx: continue
            u = P.unit(t['raw'], ty, ref_ni_k if ty != 'adjop' else None)
            r = ext_recon(t, idx[0], u)
            if ty == 'adjni':
                ps = [i for i, c in enumerate(t['cols']) if c and c[0] == mo and c[1] == cp and c[2] == 'ps']
                if ps:
                    rr = ext_recon(t, ps[0], 'm')
                    r['adj_eps'] = rr.get('adj_ni'); r['gaap_eps'] = rr.get('start')
                    r['items_ps'] = [[it[0], it[1]] for it in rr['items']]
            if 'start' not in r: continue
            r['unit'] = u; r['doc'] = t.get('doc')
            if key in o:         # keep the richer table (more items)
                if len(r['items']) <= len(o[key]['items']): continue
            o[key] = r
    return o

# ------------------------------------------------------------------ cash flow / balance sheet
CF_MAP = [('cfo', r'^net cash .*operating'), ('ni', r'^net (income|loss|\(loss\) income|income \(loss\))$|from continuing operations$'),
          ('dep', r'^depreciation( and amortization)?$'), ('amort', r'^amortization$|^amortization of intangible'),
          ('pens_amort', r'amortization of (unrecognized|actuarial)'), ('sbc', r'^(equity|stock|share)-based compensation'),
          ('deftax', r'^deferred income tax'), ('gain_ppe', r'disposal or sale of property'), ('cont_cons', r'contingent consideration'),
          ('capex', r'^purchase of property'), ('capex_proc', r'^proceeds from (sale|disposal) of property'),
          ('acq', r'^acquisition(s)?(, net of cash acquired| of)'), ('inv_purch', r'^purchase of investments'), ('inv_red', r'^redemption of investments'),
          ('cfi', r'^net cash .*investing'),
          ('debt_borrow', r'^borrowings|^proceeds from (the )?(issuance of )?(long-term )?debt|^increase in short-term'),
          ('debt_repay', r'^principal repayments|^repayments? (on|of) (debt|long-term)|^\(decrease\) increase in short|^decrease in short'),
          ('fin_lease', r'^repayments? on (finance|capital) lease'), ('div', r'^dividends paid'),
          ('stock_iss', r'^issuance of common stock$|^proceeds from (issuance|exercise)|^sale of treasury'), ('stock_cost', r'^common stock issuance costs'),
          ('withhold', r'^tax withholding|^purchase of treasury stock.*(withholding|net share)'), ('bb', r'^(purchase|acquisition|repurchase) of (treasury|common) stock$|^repurchase of'),
          ('cff', r'^net cash .*financing'), ('fx', r'^effect of exchange'),
          ('net', r'^net (\(?(increase|decrease)\)? ?)+in cash'),
          ('beg', r'beginning of'), ('end', r'end of (period|year)')]

def ext_cf(tabs, mo, cp):
    t = next((t for t in tabs if t['type'] == 'cf' and t['cols'] and any(c and c[0] == mo and c[1] == cp for c in t['cols'])), None)
    if not t: return None
    ci = next(i for i, c in enumerate(t['cols']) if c and c[0] == mo and c[1] == cp)
    out, raw = {'ytd_months': mo}, []
    for lab, vals in t['rows']:
        if not vals or ci >= len(vals) or vals[ci] is None: continue
        v = k2m(vals[ci]); raw.append([lab, v])
        L = lab.lower().strip(' :')
        for k, p in CF_MAP:
            if re.search(p, L):
                if k in ('acq', 'withhold', 'bb', 'inv_purch', 'inv_red', 'debt_borrow', 'debt_repay', 'stock_iss'): out[k] = round(out.get(k, 0.0) + v, 6)
                elif k == 'net': out[k] = v
                elif k not in out: out[k] = v
                break
    out['lines_raw'] = raw
    return out

BS_MAP = [('cash', r'^cash and cash equivalents'), ('invest', r'^investments'), ('ar', r'^trade accounts receivable|^accounts receivable'),
          ('unbilled', r'^unbilled revenue'), ('inv', r'^inventories'), ('tca', r'^total current assets'),
          ('ppe', r'^property, plant and equipment'), ('pension_asset', r'^prepaid pension'), ('rou', r'^operating lease assets'),
          ('gw', r'^goodwill'), ('intang', r'^customer relationships|^technology|^tradenames?|^backlog|^permits|^other intangible|^intangible assets'),
          ('ta', r'^total assets'),
          ('std', r'^short-term debt|^current portion of (long-term debt|finance lease|capital lease)'), ('ap', r'^accounts payable'),
          ('accr_comp', r'^accrued compensation'), ('accr_oth', r'^accrued expenses'), ('deposits', r'^customer deposits'),
          ('oplease_cl', r'^operating lease liabilities'), ('tax_pay', r'^income taxes payable|^domestic and foreign income taxes payable'),
          ('tcl', r'^total current liabilities'), ('ltd', r'^long-term debt$|^finance lease obligations$|^capital lease obligations$'),
          ('tl', r'^total liabilities$'), ('eq', r"^total stockholders['’] equity"), ('tle', r"^total liabilities and")]

def ext_bs(tabs, cp='cur'):
    t = next((t for t in tabs if t['type'] == 'bs' and t['cols']), None)
    if not t: return None
    ci = 0 if cp == 'cur' else 1
    out, raw, seen_tcl = {}, [], False
    for lab, vals in t['rows']:
        if not vals or ci >= len(vals) or vals[ci] is None: continue
        v = k2m(vals[ci]); raw.append([lab, v])
        L = lab.lower().strip(' :')
        for k, p in BS_MAP:
            if re.search(p, L):
                if k == 'oplease_cl' and seen_tcl: k = 'oplease_ncl'
                if k == 'accr_comp' and seen_tcl: k = 'accr_comp_lt'
                if k in ('intang', 'std', 'ltd'): out[k] = round(out.get(k, 0.0) + v, 6)
                elif k not in out: out[k] = v
                if k == 'tcl': seen_tcl = True
                break
    out['lines_raw'] = raw
    return out

# ------------------------------------------------------------------ grids: orders / backlog / markets / regions
MK = [('refining', r'^refin'), ('chem', r'^chem'), ('power', r'^power|^energy & new energy|^new energy'), ('defense', r'^defense'),
      ('space', r'^space'), ('ep', r'^energy & process'), ('other', r'^other')]
RG = [('us', r'^united states|^north america|^u\.s'), ('mideast', r'^middle east'), ('asia', r'^asia'), ('other', r'^other|^all other'), ('intl', r'^international')]

def grid_vals(tabs, ty, key):
    """-> {label_key: value (USD m)} for period key (fy, q) from the grids of type ty."""
    out = {}
    MAP = RG if ty.endswith('_reg') else MK
    for t in tabs:
        if t['type'] != ty or not t['cols']: continue
        idx = [i for i, c in enumerate(t['cols']) if c == key]
        if not idx: continue
        u = P.unit(t['raw'], ty)
        f = (lambda v: k2m(v)) if u == 'k' else (lambda v: r6(v))
        for lab, vals in t['rows']:
            if not vals or idx[0] >= len(vals) or vals[idx[0]] is None: continue
            L = lab.lower().strip(' :*')
            if L.startswith('total') or re.match(r'^[\d,]+$', L):
                out.setdefault('total', f(vals[idx[0]])); continue
            k = next((k for k, p in MAP if re.search(p, L)), None)
            if ty == 'orders':
                if L.startswith('orders'): out.setdefault('orders', f(vals[idx[0]]))
                elif L.startswith('backlog'): out.setdefault('backlog', f(vals[idx[0]]))
                continue
            if k and k not in out: out[k] = f(vals[idx[0]]); out.setdefault('_labels', {})[k] = lab
        if out: out['_unit'] = u
    return out

def ext_kpi(tabs, fy, q):
    key = (fy, q if q else 'FY')
    o = {}
    g = grid_vals(tabs, 'orders', key)
    if g: o['orders'] = g.get('orders'); o['backlog'] = g.get('backlog')
    if q == 4:
        gq = grid_vals(tabs, 'orders', (fy, 4))
        if gq: o['orders_q4'] = gq.get('orders')
    for ty, k in (('sales_mkt', 'sales_mkt'), ('orders_mkt', 'orders_mkt'), ('backlog_mkt', 'backlog_mkt'), ('sales_reg', 'sales_reg'), ('orders_reg', 'orders_reg')):
        g = grid_vals(tabs, ty, key)
        if g: o[k] = {kk: v for kk, v in g.items() if not kk.startswith('_')}; o[k + '_labels'] = g.get('_labels', {}); o[k + '_unit'] = g.get('_unit')
    return o

# ------------------------------------------------------------------ 10-K / 10-Q revenue note (market table, USD thousands, FY2019+)
_FCACHE = {}
def filing_tables(path):
    if path not in _FCACHE:
        tabs = []
        if os.path.exists(path):
            for t in P.html_tables(open(path, 'rb').read()):
                labs = ' || '.join(l.lower() for l, _ in t['rows'])
                if re.search(r'(^|\|\| )(refining|defense|energy & process)', labs) and re.search(r'(^|\|\| )net sales', labs):
                    cols = P.columns(t, 'is')
                    if cols and all(c is not None for c in cols) and not re.search(r'change', t.get('hdr_text') or '', re.I): tabs.append(dict(t, cols=cols))
        _FCACHE[path] = tabs
    return _FCACHE[path]

def ext_note_mkt(path, mo, cp='cur'):
    out = {}
    for t in filing_tables(path):
        idx = [i for i, c in enumerate(t['cols']) if c and c[0] == mo and c[1] == cp]
        if not idx: continue
        for lab, vals in t['rows']:
            if not vals or idx[0] >= len(vals) or vals[idx[0]] is None: continue
            L = lab.lower().strip()
            if L.startswith('net sales'): out.setdefault('total', k2m(vals[idx[0]])); continue
            k = next((k for k, p in MK if re.search(p, L)), None)
            if k and k not in out: out[k] = k2m(vals[idx[0]])
        if out: break
    return out

# ------------------------------------------------------------------ build records
def rec_period(rel, filings, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    tabs = r['tabs']
    mo = 12 if annual else 3
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'sources': {'release': r['url'], 'release_date': r['date'], 'exhibits': r['docs']}, 'notes': []}
    rec['is'] = ext_is(tabs, mo, 'cur')
    ni_k = (rec['is'] or {}).get('ni'); ni_k = ni_k * 1000 if ni_k is not None else None
    rec['ngaap'] = ext_ngaap(tabs, mo, 'cur', ni_k)
    ytd = 12 if annual else 3 * q
    rec['cf'] = ext_cf(tabs, ytd, 'cur')
    rec['bs'] = ext_bs(tabs, 'cur')
    rec['kpi'] = ext_kpi(tabs, fy, None if annual else q)
    f = filings.get((fy, 4 if annual else q))
    if f:
        rec['sources']['filing'] = f['url']
        if annual: rec['mkt_note'] = ext_note_mkt(f['path'], 12)
        elif q == 4:
            fa = ext_note_mkt(f['path'], 12); f9 = filings.get((fy, 3))
            n9 = ext_note_mkt(f9['path'], 9) if f9 else {}
            if fa and n9 and set(fa) == set(n9):
                rec['mkt_note'] = {k: round(v - n9[k], 6) for k, v in fa.items() if k in n9}
                rec['notes'].append('mkt_note: Q4 = fiscal year (10-K) less nine months (Q3 10-Q revenue note).')
        else: rec['mkt_note'] = ext_note_mkt(f['path'], 3)
        fn = filings.get((fy + 1, 4 if annual else q))
        if fn and (annual or q != 4): rec['mkt_note_py'] = ext_note_mkt(fn['path'], 12 if annual else 3, 'py')
    nxt = rel.get((fy + 1, q))
    if nxt:
        ni_py = ext_is(nxt['tabs'], mo, 'py')
        rec['py'] = {'release': nxt['url'], 'is': ni_py,
                     'ngaap': ext_ngaap(nxt['tabs'], mo, 'py', (ni_py or {}).get('ni', 0) * 1000 if ni_py else None),
                     'kpi': ext_kpi(nxt['tabs'], fy, None if annual else q)}
    qq = 4 if annual else q
    rec['x'] = {'sh_cover': xbrl.dei_shares(fy, qq), 'sh_issued': xbrl.value('CommonStockSharesIssued', fy, 'I', qq),
                'sh_treasury': xbrl.first_of(['TreasuryStockCommonShares', 'TreasuryStockShares'], fy, 'I', qq),
                'sh_out': xbrl.value('CommonStockSharesOutstanding', fy, 'I', qq),
                'rev': xbrl.first_of(['RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet', 'Revenues'], fy, 'FY' if annual else 'Q', qq),
                'ni': xbrl.value('NetIncomeLoss', fy, 'FY' if annual else 'Q', qq), 'eps_d': xbrl.value('EarningsPerShareDiluted', fy, 'FY' if annual else 'Q', qq),
                'ta': xbrl.value('Assets', fy, 'I', qq), 'cfo_ytd': xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, 'FY' if annual else 'YTD', qq)}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings = release_index()
    idx = [{'fy': fy, 'q': q, 'date': r['date'], 'url': r['url'], 'exhibits': r['docs']} for (fy, q), r in sorted(rel.items())]
    json.dump(idx, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    n = 0
    for fy in range(2006, 2027):
        r = rec_period(rel, filings, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
    for fy in range(2013, 2028):
        for q in (1, 2, 3, 4):
            if fy == 2027 and q > 1: break
            r = rec_period(rel, filings, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
    xbrl.dump_subset()
    print(n, 'period files;', len(rel), 'releases')

if __name__ == '__main__':
    main()
