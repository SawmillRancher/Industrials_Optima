"""Harmonise the extracted Netflix data (data/<period>.json, raw statement rows in USD thousands) into flat model keys:
DATA[period]['x'][key] (USD millions; shares in millions; per-share in USD, split-adjusted).

Basis: every period as originally reported in its own Form 10-Q / 10-K (annual = 10-K, which wins over the Q4 letter where
they differ). Quarters Q1-Q3 = the 10-Q three-month column; Q4 flows = fiscal year (10-K) - nine months (Q3 10-Q year-to-date
column); Q4 EPS and weighted shares = the Q4 shareholder letter's three-month column (matched on revenue). Cash flow is filed
year to date: discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M). Balance sheets at each period end.
Stock splits (7-for-1 on 14-Jul-2015; 10-for-1 on 14-Nov-2025) are applied by the filing date of each source document:
filings before 15-Jul-2015 x70 (shares) / 70 (per share); before 14-Nov-2025 x10 / 10.
Regions (UCAN / EMEA / LATAM / APAC): FY2017-19 from the FY2019 10-K, Q1-Q3 2019 from the 2020 10-Q prior-year columns
(latest filing presenting the period), Q4 = FY - 9M; paid memberships at period end; ARM from the 10-Q / 10-K MD&A
(Q4 from the Q4 letter regional table). Legacy segments (Domestic / International streaming, Domestic DVD; 2011-2019): 10-Q / 10-K
segment note, Q4 = FY - 9M.
Published non-GAAP: free cash flow (every letter; the column is matched on net cash from operating activities); adjusted
EBITDA (letters Q2-15 - Q1-23, columns Q2-14 - Q1-23, matched on GAAP net income; first published value); non-GAAP net income
(2006 - Q2-10 excl. stock-based compensation; Q1-13 debt extinguishment; Q4-14 and Q4-15 tax-accrual releases; Q1-15 F/X)."""
import json, glob, os, re, datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
FY0, FYQ0 = 2006, 2013

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(y) for y in range(FY0, 2026)]
    for y in range(FYQ0, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q > 2)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def split_factor(filed):
    if filed < '2015-07-15': return 70.0
    if filed < '2025-11-14': return 10.0
    return 1.0

# ---------------------------------------------------------------- row lookup
def rows_get(rows, pat, col=0, nth=0, total=False):
    """value (column `col`) of the nth row whose label matches `pat`; total=True sums every matching row."""
    hits = [r for r in (rows or []) if re.match(pat, r[0], re.I) and r[2] and (len(r[2]) > col if col >= 0 else True)]
    if not hits: return None
    if total: return sum(r[2][col] for r in hits)
    return hits[nth][2][col] if len(hits) > nth else None

IS_MAP = {'rev': r'^(Total )?Revenues$', 'cor': r'^(Total cost of revenues|Cost of revenues)$', 'mkt': r'^(Marketing|Sales and marketing)$',
          'td': r'^Technology and development$', 'ga': r'^General and administrative$', 'gain_dvd': r'^Gain on disposal of DVDs$',
          'legal': r'^(Gain on legal settlement|Legal settlement)$', 'oi': r'^Operating (income|loss)', 'int': r'^Interest expense',
          'oth': r'^Interest and other (income|expense)', 'ext': r'^Loss on extinguishment', 'ebt': r'^Income.*before income taxes',
          'ni': r'^Net (income|loss)'}

def is_values(rows, col=0):
    o = {}
    for k, pat in IS_MAP.items():
        o[k] = rows_get(rows, pat, col, total=(k in ('oth', 'int')))
    o['int'] = abs(o['int']) if o['int'] is not None else 0.0
    o['eps_b'] = rows_get(rows, r'^Basic$', col, 0); o['eps_d'] = rows_get(rows, r'^Diluted$', col, 0)
    o['sh_b'] = rows_get(rows, r'^Basic$', col, 1); o['sh_d'] = rows_get(rows, r'^Diluted$', col, 1)
    return o

CF_MAP = {'cf_ni': r'^Net (income|loss)', 'cf_cadd': r'^Additions to (streaming )?content (assets|library)$',
          'cf_cliab': r'^(Change in|Increase in) (streaming )?content liabilities', 'cf_camort': r'^Amortization of (streaming )?content (assets|library)$',
          'cf_damort': r'^Amortization of DVD', 'cf_dep': r'^Depreciation', 'cf_sbc': r'^Stock-based compensation',
          'cf_fxdebt': r'^Foreign currency remeasurement', 'cf_def': r'^Deferred (income )?taxes$', 'cf_cfo': r'^Net cash.*operating',
          'cf_capex': r'^Purchases of property and equipment', 'cf_dvd': r'^Acquisitions? of (DVD |streaming )?(content )?(library|assets)|^Acquisitions? of DVD',
          'cf_acq': r'^(Acquisitions|Acquisitions? of intangible assets?|Investment in business)$',
          'cf_inv': r'^(Purchases of (short-term )?investments|Proceeds from (maturities|sale)s? (and sales )?of (short-term )?investments|Proceeds from maturities and sales of investments|Proceeds from sale of short-term investments|Proceeds from maturities of (short-term )?investments)',
          'cf_cfi': r'^Net cash.*investing', 'cf_diss': r'^(Proceeds from issuance of debt|Borrowings on line of credit)',
          'cf_drep': r'^(Repayments of debt|Redemption of debt|Payments on line of credit|Principal payments)',
          'cf_stock': r'^(Proceeds from issuance of common stock|Proceeds from public offering)', 'cf_bb': r'^(Repurchases of common stock|Taxes paid related to net share settlement)',
          'cf_cff': r'^Net cash.*financing', 'cf_fx': r'^Effect of exchange rate', 'cf_beg': r'.*beginning of', 'cf_end': r'.*end of'}
SUMK = ('cf_inv', 'cf_drep', 'cf_diss', 'cf_stock', 'cf_bb', 'cf_dvd', 'cf_acq', 'cf_camort', 'cf_damort', 'cf_dep')

def cf_values(rows, col=None):
    """year-to-date column: recent 10-Qs show three-month and year-to-date columns (4 values: YTD = third), older ones and
    10-Ks year to date first."""
    w = len(next(r[2] for r in rows if re.match(CF_MAP['cf_ni'], r[0], re.I) and r[2]))
    col = 2 if w == 4 else (col if col is not None else 0)
    o = {k: rows_get(rows, pat, col, total=(k in SUMK)) for k, pat in CF_MAP.items()}
    for k in o:
        if o[k] is None and k not in ('cf_beg', 'cf_end'): o[k] = 0.0
    op = ('cf_ni', 'cf_cadd', 'cf_cliab', 'cf_camort', 'cf_damort', 'cf_dep', 'cf_sbc', 'cf_fxdebt', 'cf_def')
    o['cf_oop'] = o['cf_cfo'] - sum(o[k] for k in op)
    o['cf_oinv'] = o['cf_cfi'] - o['cf_capex'] - o['cf_dvd'] - o['cf_acq'] - o['cf_inv']
    o['cf_ofin'] = o['cf_cff'] - o['cf_diss'] - o['cf_drep'] - o['cf_stock'] - o['cf_bb']
    o['cf_net'] = o['cf_cfo'] + o['cf_cfi'] + o['cf_cff'] + o['cf_fx']
    return o
CFK = ['cf_ni', 'cf_cadd', 'cf_cliab', 'cf_camort', 'cf_damort', 'cf_dep', 'cf_sbc', 'cf_fxdebt', 'cf_def', 'cf_oop', 'cf_cfo', 'cf_capex', 'cf_dvd',
       'cf_acq', 'cf_inv', 'cf_oinv', 'cf_cfi', 'cf_diss', 'cf_drep', 'cf_stock', 'cf_bb', 'cf_ofin', 'cf_cff', 'cf_fx', 'cf_net']

BS_MAP = {'cash': r'^Cash and cash equivalents$', 'sti': r'^Short-term investments$', 'ccont': r'^Current content (library|assets)',
          'tca': r'^Total current assets$', 'cont': r'^(Non-current content (library|assets)|Content (library|assets), net|DVD library, net)',
          'ppe': r'^Property and equipment, net$', 'ta': r'^Total assets$', 'ccl': r'^(Current content liabilities|Content accounts payable)',
          'ap': r'^(Accounts payable|Other accounts payable)$', 'accr': r'^Accrued expenses', 'defrev': r'^Deferred revenue$',
          'std': r'^(Short-term debt|Current portion of lease financing)', 'tcl': r'^Total current liabilities$',
          'nccl': r'^Non-current content liabilities', 'ltd': r'^(Long-term debt|Lease financing obligations, excluding)',
          'tl': r'^Total liabilities$', 'eq': r'^Total (stockholders|shareholders)', 'tle': r'^Total liabilities and'}

def do_bs(p, rows):
    b = {k: rows_get(rows, pat, COL0.get(p, 0), total=(k in ('ltd', 'ap'))) for k, pat in BS_MAP.items()}
    for k in ('sti', 'ccont', 'ccl', 'std', 'nccl', 'ltd', 'accr', 'defrev', 'ap'): b[k] = N(b[k])
    put(p, 'bs_cash', b['cash']); put(p, 'bs_sti', b['sti'] / 1e3); put(p, 'bs_ccont', b['ccont'] / 1e3)
    put(p, 'bs_oca', (b['tca'] - b['cash'] - b['sti'] - b['ccont']) / 1e3); put(p, 'bs_tca', b['tca'] / 1e3)
    put(p, 'bs_cont', N(b['cont']) / 1e3); put(p, 'bs_ppe', b['ppe'] / 1e3)
    put(p, 'bs_onca', (b['ta'] - b['tca'] - N(b['cont']) - b['ppe']) / 1e3); put(p, 'bs_ta', b['ta'] / 1e3)
    put(p, 'bs_ccl', b['ccl'] / 1e3); put(p, 'bs_ap', b['ap'] / 1e3); put(p, 'bs_accr', b['accr'] / 1e3); put(p, 'bs_defrev', b['defrev'] / 1e3)
    put(p, 'bs_std', b['std'] / 1e3); put(p, 'bs_ocl', (b['tcl'] - b['ccl'] - b['ap'] - b['accr'] - b['defrev'] - b['std']) / 1e3)
    put(p, 'bs_tcl', b['tcl'] / 1e3); put(p, 'bs_nccl', b['nccl'] / 1e3); put(p, 'bs_ltd', b['ltd'] / 1e3)
    tl = b['tl'] if b['tl'] is not None else b['tle'] - b['eq']
    put(p, 'bs_oncl', (tl - b['tcl'] - b['nccl'] - b['ltd']) / 1e3); put(p, 'bs_tl', tl / 1e3)
    put(p, 'bs_eq', b['eq'] / 1e3); put(p, 'bs_tle', b['tle'] / 1e3)
    DATA[p]['x']['bs_cash'] = b['cash'] / 1e3
    put(p, 'debt_tot', (b['std'] + b['ltd']) / 1e3)

def put_is(p, o, f):
    """o: income statement values in USD thousands as published; f: split factor of the source document."""
    rev = o['rev']
    put(p, 'rev', rev / 1e3); put(p, 'cor', o['cor'] / 1e3); put(p, 'mkt', o['mkt'] / 1e3); put(p, 'td', o['td'] / 1e3); put(p, 'ga', o['ga'] / 1e3)
    put(p, 'oth_op', (N(o.get('gain_dvd')) + N(o.get('legal'))) / 1e3)
    put(p, 'oi', o['oi'] / 1e3); put(p, 'int_exp', o['int'] / 1e3); put(p, 'oth_inc', N(o['oth']) / 1e3); put(p, 'ext', N(o.get('ext')) / 1e3)
    put(p, 'ebt', o['ebt'] / 1e3); put(p, 'ni', o['ni'] / 1e3); put(p, 'tax', (o['ebt'] - o['ni']) / 1e3)
    if o.get('eps_d') is not None:
        put(p, 'eps_b', o['eps_b'] / f); put(p, 'eps_d', o['eps_d'] / f)
        put(p, 'sh_b', o['sh_b'] * f / 1e3); put(p, 'sh_d', o['sh_d'] * f / 1e3)

def diff(a, b): return {k: a[k] - b[k] for k in a if isinstance(a.get(k), (int, float)) and isinstance(b.get(k), (int, float))}

# ---------------------------------------------------------------- per period
RECAST = {2018: ('Q1-Q3 2018 from the 2019 Form 10-Q prior-year columns: personnel costs reclassified effective Q4-2018 (8-K 3-Jan-2019, Ex. 99.1: '
                'content / marketing personnel from G&A to cost of revenues and marketing; streaming-delivery personnel from technology & development '
                'to cost of revenues), as presented in the FY2018 10-K; operating income unchanged. Q4 = FY2018 (10-K) - recast nine months.')}

COL0 = {'2006': -1}         # the FY2006 10-K presents its columns oldest first (2004, 2005, 2006)

def do_pl():
    for y in range(FY0, 2026):
        r = REC[str(y)]; f = split_factor(r['filed'])
        put_is(str(y), is_values(r['is_rows'], col=COL0.get(str(y), 0)), f)
        put(str(y), 'filed', r['filed'])
    for y in range(FYQ0, 2027):
        for q in (1, 2, 3):
            p = qk(y, q); r = REC.get(p)
            if not r: continue
            if y in RECAST:
                rn = REC[qk(y + 1, q)]
                put_is(p, is_values(rn['is_rows'], col=1), split_factor(rn['filed'])); put(p, 'recast', 1)
                o = is_values(r['is_rows'])
                for kk in ('cor', 'mkt', 'td', 'ga'): put(p, f'orig_{kk}', o[kk] / 1e3)
            else:
                put_is(p, is_values(r['is_rows']), split_factor(r['filed']))
        if y == 2026: continue
        r3, rf = REC[qk(y, 3)], REC[str(y)]
        nine = is_values(REC[qk(y + 1, 3)]['is_rows'], col=3) if y in RECAST else is_values(r3['is_rows'], col=2)     # nine-month column
        fy = is_values(rf['is_rows'])
        q4 = diff(fy, nine)
        for k in ('eps_b', 'eps_d', 'sh_b', 'sh_d'): q4.pop(k, None)
        q4['int'] = fy['int'] - nine['int']
        # Q4 EPS / shares from the Q4 letter three-month column (matched on derived Q4 revenue)
        ri = rf.get('release_is') or []
        revs = next((r_[2] for r_ in ri if re.match(IS_MAP['rev'], r_[0])), [])
        k = next((i for i, v in enumerate(revs) if abs(v - q4['rev']) <= 1.5), None)
        rel_filed = re.match(r'(\d{4}-\d\d-\d\d)', rf.get('_release_text_file', '')).group(1)
        if k is not None:
            lo = is_values(ri, col=k)
            for kk in ('eps_b', 'eps_d', 'sh_b', 'sh_d'): q4[kk] = lo[kk]
            for kk in ('cor', 'mkt', 'td', 'ga', 'oi', 'ni'):
                if lo.get(kk) is not None and q4.get(kk) is not None and abs(lo[kk] - q4[kk]) > 1.5:
                    LOG.append(f'{qk(y, 4)}: {kk} FY-9M {q4[kk]:,.0f} vs Q4 letter {lo[kk]:,.0f}')
                    put(qk(y, 4), f'q4diff_{kk}', (q4[kk] - lo[kk]) / 1e3)
        else:
            LOG.append(f'{qk(y, 4)}: Q4 revenue not matched in the letter')
        put_is(qk(y, 4), q4, split_factor(rel_filed))
        put(qk(y, 4), 'q4_derived', 1)

def do_bs_all():
    for p in periods():
        r = REC.get(p if not p.startswith('Q4') else '20' + p[-2:])
        if r and r.get('bs_rows'): do_bs(p, r['bs_rows'])

def do_cf():
    for y in range(FY0, 2026):
        r = REC[str(y)]; c = cf_values(r['cf_rows'], COL0.get(str(y)))
        for k in CFK: put(str(y), k, c[k] / 1e3)
        put(str(y), 'cf_beg', c['cf_beg'] / 1e3); put(str(y), 'cf_end', c['cf_end'] / 1e3)
    for y in range(FYQ0, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            p = qk(y, q)
            r = REC.get(str(y) if q == 4 else p)
            if not r or (y == 2026 and q > 2): break
            c = cf_values(r['cf_rows'])
            d = c if q == 1 else {k: c[k] - prev[k] for k in CFK}
            for k in CFK: put(p, k, d[k] / 1e3)
            put(p, 'cf_beg', (c['cf_beg'] if q == 1 else prev['cf_end']) / 1e3); put(p, 'cf_end', c['cf_end'] / 1e3)
            prev = c

# ---------------------------------------------------------------- segments, regions
SEGC = {'dom': 'Domestic Streaming', 'int': 'International Streaming', 'dvd': 'Domestic DVD'}
SEGR = {'rev': r'^Revenues', 'cor': r'^Cost of revenues', 'mkt': r'^Marketing', 'cp': r'^Contribution profit', 'mem': r'^(Paid memberships|Total memberships)'}
def seg_get(tab, row, col):
    for lab, d in (tab or {}).items():
        if re.match(SEGR[row], lab, re.I):
            for c, v in d.items():
                if c.lower() == SEGC[col].lower(): return v
    return None

def seg_tab(p, kind, year):
    r = REC.get(p) or {}
    return (r.get('seg_tables') or {}).get(f'{kind}-{year}')

def do_seg():
    for y in range(2011, 2020):
        fy = seg_tab(str(y), 'Y', y)
        for s_ in SEGC:
            for row in SEGR:
                v = seg_get(fy, row, s_)
                if v is not None: put(str(y), f'sg_{s_}_{row}', v / 1e3)
        if y < FYQ0: continue
        for q in (1, 2, 3):
            t = seg_tab(qk(y + 1, q), '3', y) if y in RECAST else seg_tab(qk(y, q), '3', y)
            for s_ in SEGC:
                for row in SEGR:
                    v = seg_get(t, row, s_)
                    if v is not None: put(qk(y, q), f'sg_{s_}_{row}', v / 1e3)
        t9 = seg_tab(qk(y + 1, 3), '9', y) if y in RECAST else seg_tab(qk(y, 3), '9', y)
        for s_ in SEGC:
            for row in SEGR:
                a, b = seg_get(fy, row, s_), seg_get(t9, row, s_)
                if row == 'mem': put(qk(y, 4), f'sg_{s_}_mem', a / 1e3 if a is not None else None)
                elif a is not None and b is not None: put(qk(y, 4), f'sg_{s_}_{row}', (a - b) / 1e3)

RG = ('UCAN', 'EMEA', 'LATAM', 'APAC')
def put_reg(p, d, keys=('rev', 'paid', 'netadds', 'arm')):
    for g in RG:
        for k in keys:
            v = (d.get(g) or {}).get(k)
            if v is None: continue
            put(p, f'rg_{g.lower()}_{k}', v / 1e3 if k in ('rev', 'paid', 'netadds') else v)

def do_reg():
    f19 = REC['2019']
    put_reg('2019', f19.get('reg') or {}); put_reg('2018', f19.get('reg_2018') or {}); put_reg('2017', f19.get('reg_2017') or {})
    for y in ('2017', '2018'): put(y, 'rg_recast', 1)
    for y in range(2020, 2026): put_reg(str(y), REC[str(y)].get('reg') or {})
    for q in (1, 2, 3):                                  # 2019 quarters from the 2020 10-Q prior-year columns
        put_reg(qk(2019, q), REC[qk(2020, q)].get('reg_py') or {}); put(qk(2019, q), 'rg_recast', 1)
    for y in range(2020, 2027):
        for q in (1, 2, 3):
            if REC.get(qk(y, q)): put_reg(qk(y, q), REC[qk(y, q)].get('reg') or {})
    for y in range(2019, 2026):                         # Q4 = FY - 9M; paid memberships at year end; ARM from the Q4 letter
        nine = (REC[qk(y + 1, 3)].get('reg_9m_py') if y == 2019 else REC[qk(y, 3)].get('reg_9m')) or {}
        fy = REC[str(y)].get('reg') or {}
        for g in RG:
            a, b = (fy.get(g) or {}).get('rev'), (nine.get(g) or {}).get('rev')
            if a is not None and b is not None: put(qk(y, 4), f'rg_{g.lower()}_rev', (a - b) / 1e3)
            if (fy.get(g) or {}).get('paid') is not None: put(qk(y, 4), f'rg_{g.lower()}_paid', fy[g]['paid'] / 1e3)
            a, b = (fy.get(g) or {}).get('netadds'), (nine.get(g) or {}).get('netadds')
            if a is not None and b is not None: put(qk(y, 4), f'rg_{g.lower()}_netadds', (a - b) / 1e3)
            lr = (REC[str(y)].get('letter_reg') or {}).get(g) or {}
            if lr.get('arm') is not None and y <= 2024: put(qk(y, 4), f'rg_{g.lower()}_arm', lr['arm'])

# ---------------------------------------------------------------- published non-GAAP
def tables(name):
    for p in sorted(REC, key=lambda k: REC[k].get('_release_text_file', 'z')):
        for t in REC[p].get(name) or []:
            yield REC[p].get('_release_text_file', '')[:10], t

def col_match(t, lab_re, value, tol=1.5, loose=None):
    """column whose value equals `value` (thousands, +-tol); else, with `loose`, the column within +-loose (a comparative the
    release restated, e.g. Q2-13 CFO after the Q1-13 restatement), logged."""
    vals = next((v for k, v in t.items() if re.match(lab_re, k, re.I)), None)
    if not vals: return None
    for k, v in enumerate(vals):
        if abs(v - value) <= tol: return k
    if loose:
        for k, v in enumerate(vals):
            if abs(v - value) <= loose: LOG.append(f'matched within {abs(v - value):,.0f}k on {lab_re[:20]}'); return k
    return None

def do_ngaap():
    for p in periods():
        cfo = x_(p, 'cf_cfo'); ni = x_(p, 'ni')
        if cfo is None: continue
        # free cash flow: the period's own release, column matched on CFO
        r = REC.get(p if not p.startswith('Q4') else '20' + p[-2:])
        if p.isdigit() or p.startswith('Q4'): r = REC.get('20' + p[-2:]) if not p.isdigit() else REC.get(p)
        for t in (r or {}).get('fcf_tables') or []:
            k = col_match(t, r'^Net cash (provided by|used in|\(used in\))', cfo * 1e3, loose=100)
            if k is None: continue
            fl = next(v for kk, v in t.items() if re.match(r'^(Non-GAAP )?free cash flow', kk, re.I))
            cap = next((v for kk, v in t.items() if re.match(r'^Purchases of property', kk, re.I)), None)
            items = {kk: v[k] for kk, v in t.items() if k < len(v) and not re.match(r'^(Net cash (provided by|used in|\(used in\)).*operating|Purchases of property|(Non-GAAP )?free cash flow)', kk, re.I)}
            oth = sum(items.values())
            if any(re.match(r'^Net cash.*investing', kk, re.I) for kk in items): oth -= x_(p, 'cf_capex') * 1e3     # 2019-20: FCF = CFO + investing ex investments
            put(p, 'fcf_pub', fl[k] / 1e3); put(p, 'fcf_oth', oth / 1e3)
            put(p, 'fcf_oth_lab', '; '.join(f'{kk} {v / 1e3:,.1f}' for kk, v in items.items()))
            if cap is not None and abs(cap[k] / 1e3 - x_(p, 'cf_capex')) > 0.05: LOG.append(f'{p}: release capex {cap[k] / 1e3:,.1f} vs filing {x_(p, "cf_capex"):,.1f}')
            break
        else:
            LOG.append(f'{p}: published FCF not matched (CFO {cfo:,.1f})')
        # adjusted EBITDA (first published column whose GAAP net income equals the period's)
        for d, t in tables('ebitda_tables'):
            k = col_match(t, r'^GAAP net income', ni * 1e3)
            if k is None: continue
            v = t.get('Adjusted EBITDA')
            if v and k < len(v):
                put(p, 'adj_ebitda_pub', v[k] / 1e3); put(p, 'adj_ebitda_src', d); break
        # non-GAAP net income
        for d, t in tables('ngni_tables'):
            k = col_match(t, r'^GAAP net income|^Net income', ni * 1e3)
            if k is None or 'Non-GAAP net income' not in t: continue
            items = {kk: v[k] for kk, v in t.items() if k < len(v) and not re.match(r'^(GAAP net income|Net income|Non-GAAP net income|Basic|Diluted|Add:?)$', kk, re.I)}
            for kk in list(items):     # Q4-14 letter prints the tax-accrual release as +38,612 but deducts it (later letters: "Less: ... (38,612)")
                if re.search(r'release of tax accrual', kk, re.I) and items[kk] > 0: items[kk] = -items[kk]; LOG.append(f'{p}: tax-accrual release sign corrected (deducted)')
            put(p, 'ng_ni_pub', t['Non-GAAP net income'][k] / 1e3)
            f = split_factor(d)
            if 'Diluted' in t and k < len(t['Diluted']): put(p, 'ng_eps_pub', t['Diluted'][k] / f)
            tax = sum(v for kk, v in items.items() if re.search(r'tax effect', kk, re.I))
            pre = sum(v for kk, v in items.items() if not re.search(r'tax effect', kk, re.I))
            put(p, 'ng_items_pre', pre / 1e3); put(p, 'ng_items_tax', tax / 1e3)
            for kk, v in items.items():
                if re.search(r'stock-based compensation', kk, re.I) and not re.search(r'tax effect', kk, re.I) and p.isdigit(): put(p, 'ng_sbc', v / 1e3)
                if re.search(r'foreign exchange impact', kk, re.I): put(p, 'na_fx', v / 1e3)
            put(p, 'ng_items_lab', '; '.join(f'{kk} {v / 1e3:,.1f}' for kk, v in items.items()))
            put(p, 'ng_src', d)
            break

def do_xbrl_shares():
    """shares outstanding at period end (XBRL CommonStockSharesOutstanding, as first filed; split-adjusted by filing date)."""
    import xbrl
    for p in periods():
        if p.isdigit(): y, q = int(p), 4
        else: y, q = int('20' + p[-2:]), int(p[1])
        f = xbrl.value_full('CommonStockSharesOutstanding', y, 'I', q)
        if f: put(p, 'bs_shares', f[1] / 1e6 * split_factor(f[0]))

def do_items():
    """content amortization (streaming + DVD) and the adjusting items the company quantified (model adjusted measures)."""
    for p in periods():
        if x_(p, 'cf_camort') is not None: put(p, 'camort', x_(p, 'cf_camort') + N(x_(p, 'cf_damort')))
        fy = int(p) if p.isdigit() else int('20' + p[-2:])
        if fy >= 2017 and x_(p, 'cf_fxdebt') is not None: put(p, 'na_fx', x_(p, 'cf_fxdebt'))     # (Q1-15 company item set in do_ngaap)
    one = MAN['one_offs']
    for k, key, ps in (('oa_restr', 'restructuring_q222', ('Q2-22', '2022')), ('oa_brazil', 'brazil_q325', ('Q3-25', '2025'))):
        for p in ps: put(p, k, one[key]['amount'])
    put('Q1-26', 'na_fee', -one['wbd_fee_q126']['amount'])
    put('2015', 'na_fx', x_('Q1-15', 'na_fx'))          # FY2015 = the Q1-15 company item (no FY non-GAAP published)

def run():
    load()
    for p in periods(): DATA.setdefault(p, {'x': {}})
    do_pl(); do_bs_all(); do_cf(); do_seg(); do_reg(); do_ngaap(); do_xbrl_shares(); do_items()
    for p in periods():                                   # cash-flow basis (restricted cash included from 2018) vs balance-sheet cash
        if x_(p, 'cf_end') is not None and x_(p, 'bs_cash') is not None: put(p, 'cf_restr', x_(p, 'cf_end') - x_(p, 'bs_cash'))
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'cf_cfo', 'fcf_pub', 'adj_ebitda_pub', 'bs_ta', 'bs_shares', 'rg_ucan_rev', 'sg_dom_rev')})
    print('\n'.join(LOG))
