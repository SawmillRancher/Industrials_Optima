"""Harmonise the extracted Northrop Grumman data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy
- Consolidated statements, cash flow and balance sheet: every period as originally reported in its own earnings release (FY2006-08
  from each year's Form 10-K). Later restatements are not applied; where the next year's release restated a period (TASC
  discontinued operations in 2009, the Shipbuilding spin-off in 2011, ASC 606 / ASU 2017-07 in 2018) the restated sales,
  operating income and net earnings are kept as *_py memo keys and flagged.
- Segments, current four-sector structure (Aeronautics / Defense / Mission / Space Systems, in force from 1-Jan-2020): each period
  on the LATEST filing that presents it on this structure (2018-19 from the FY2020 10-K segment note; 2019 quarters from the 2020
  releases' comparatives; 2023 and 2024 as recast for the 1-Jan-2024 and 1-Jan-2025 realignments in the 2024 / 2025 releases and
  the FY2024 / FY2025 10-K notes). The originally reported figures of recast periods are kept as seg_orig_* memo keys. Periods the
  company never presented on the current structure (2018 quarters and everything before 2018) are blank in this block.
- Legacy structures as originally reported: 2016-19 (Aerospace / Innovation / Mission / Technology Services), 2009-15
  (Aerospace / Electronic / Information / Shipbuilding / Technical Services), 2006-08 (Information & Services / Aerospace /
  Electronics / Ships).
- Reconciliation of segment operating income to operating income: FAS/CAS adjustment (net total FAS/CAS pension adjustment through
  2017; service-cost-only FAS/CAS operating adjustment from 2018 under ASU 2017-07), unallocated corporate expense, divestiture
  items, royalty reversal (2006-13) and a derived residual.
- Cash flow: releases give year-to-date statements; discrete quarters are derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
  2009-15 releases use the direct method, so D&A, stock-based compensation, deferred taxes and the retiree-benefit line come from
  XBRL (10-K / 10-Q, as first filed); working capital & other items are the derived residual in every period.
- Pension accounting: the mark-to-market (MTM) method was adopted in Q4 2018; the Q4 2018 release (Schedule 6) recast 2016, 2017 and
  Q1-Q3 2018. Q1-Q3 2018 take that recast (so that the 2018 quarters sum to the year as reported) with the originally reported
  figures kept as orig_* memo keys; 2016-17 stay as originally reported with the recast totals as memo (rev_py / oi_py / ni_py).
- Adjusted EPS: pension-adjusted diluted EPS (Q4 2009-2017 releases; excludes the net FAS/CAS pension adjustment after tax; on a
  continuing-operations basis in the 2009-12 releases) and MTM-adjusted EPS (Q4 2018 onward; excludes the fourth-quarter MTM pension /
  OPB (benefit) expense and related tax; nil in interim quarters). 2006-08: none published.
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json'))) if os.path.exists(os.path.join(BASE, 'manual_items.json')) else {}
SEG10K = json.load(open(os.path.join(BASE, 'data', '_seg_10k.json'))) if os.path.exists(os.path.join(BASE, 'data', '_seg_10k.json')) else {}
FASCAS10K = json.load(open(os.path.join(BASE, 'data', '_fascas_10k.json'))) if os.path.exists(os.path.join(BASE, 'data', '_fascas_10k.json')) else {}
RECAST18 = json.load(open(os.path.join(BASE, 'data', '_recast_2018.json'))) if os.path.exists(os.path.join(BASE, 'data', '_recast_2018.json')) else {}

CUR = ['Aeronautics Systems', 'Defense Systems', 'Mission Systems', 'Space Systems']
CURK = {'Aeronautics Systems': 'as', 'Defense Systems': 'ds', 'Mission Systems': 'ms', 'Space Systems': 'ss'}
L16 = {'Aerospace Systems': 'aer', 'Innovation Systems': 'inn', 'Mission Systems': 'mis', 'Technology Services': 'tsv'}
L09 = {'Aerospace Systems': 'aer', 'Electronic Systems': 'ele', 'Information Systems': 'inf', 'Shipbuilding': 'shp', 'Technical Services': 'tec'}
L06 = {'Information & Services': 'ins', 'Aerospace': 'aer', 'Electronics': 'ele', 'Ships': 'shp', 'Other': 'oth'}
L06_SUB = {'Information & Services': ('Mission Systems', 'Information Technology', 'Technical Services'), 'Aerospace': ('Integrated Systems', 'Space Technology'),
           'Electronics': ('Electronics',), 'Ships': ('Ships', 'Shipbuilding', 'Newport News', 'Ship Systems'), 'Other': ('Other',)}

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2006, 2026)]
    for y in range(2013, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# ------------------------------------------------------------------ helpers
def rec_find(rows, rx, idx=1, exclude=None, min_nv=2):
    """first ng row whose label matches -> value at idx (1 = quarter, 2 = year to date); rows printed as a single value
    (guidance tables) are skipped"""
    for row in rows or []:
        lab = row[0]
        if len(row) > 3 and row[3] < min_nv: continue
        if re.search(rx, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)) and row[idx] is not None:
            return row[idx]
    return None

def recon_items(recon):
    """-> dict of reconciliation items (signed as printed: income +) and the list of unmatched labels"""
    o = {'fascas': 0.0, 'unalloc': None, 'gain': 0.0, 'divest': 0.0, 'royalty': 0.0, 'intang': None, 'mtm_state': None, 'other_unalloc': None, 'other': 0.0, 'labels': []}
    has_total = any(re.match(r'^unallocated corporate', l.strip(), re.I) and not re.match(r'^other unallocated', l.strip(), re.I) for l, v in recon)
    has_sub = any(re.match(r'^intangible asset amort|^other unallocated', l.strip(), re.I) for l, v in recon)
    for lab, v in recon:
        L = lab.strip().lower(); v = N(v)
        if re.match(r'^net (fas|fas/cas|fas \(service\)/cas)?.*pension|^fas/cas operating|^net pension|^pension expense|^reversal of cas pension', L): o['fascas'] += v
        elif re.match(r'^unallocated corporate', L) or re.match(r'^unallocated (&|and other )?expenses', L) or re.match(r'^unallocated expenses', L): o['unalloc'] = N(o['unalloc']) + v
        elif re.match(r'^other unallocated', L): o['other_unalloc'] = v
        elif re.match(r'^intangible asset amort', L): o['intang'] = v
        elif re.match(r'^mtm-related deferred state|^deferred state tax', L): o['mtm_state'] = v
        elif re.match(r'^gain on sale', L): o['gain'] += v
        elif re.search(r'divestiture', L): o['divest'] += v
        elif re.match(r'^reversal of royalty|^royalty', L): o['royalty'] += v
        elif re.match(r'^other\s*\d?$', L):
            if has_total and has_sub: o['other_unalloc'] = N(o['other_unalloc']) + v
            else: o['other'] += v; o['labels'].append(lab)
        else: o['other'] += v; o['labels'].append(lab)
    # the 2018+ unallocated total already contains its components (intangibles, MTM state tax, other unallocated; gain / divestiture
    # items are shown inside the unallocated block from 2021); components that were summed separately are not added again
    if has_total and has_sub:
        if o['gain'] or o['divest']:
            o['gain_in_total'] = True
    return o

def ebt_below(below):
    o = {'int_exp': None, 'int_inc': None, 'nonop_fas': None, 'mtm': None, 'other_net': None, 'other_items': [], 'ebt': None, 'tax': None, 'cont': None, 'disc': None, 'ni': None}
    for lab, v in below:
        L = lab.strip().lower()
        if re.match(r'^(net )?interest expense', L): o['int_exp'] = -N(v)
        elif re.match(r'^interest income', L): o['int_inc'] = N(v)
        elif re.match(r'^mark-to-market|^mtm', L): o['mtm'] = N(v)
        elif re.search(r'pension', L) and 'ebt' not in o: o['nonop_fas'] = N(v)
        elif re.match(r'^other,? ?net|^other income|^other,? ?income|^other \(expense\)|^other$', L): o['other_net'] = N(v)
        elif re.search(r'before (income )?tax', L): o['ebt'] = v
        elif re.match(r'^federal and foreign income tax|^income tax', L): o['tax'] = v
        elif re.match(r'^(earnings|income)( \(loss\))? from continuing operations$|^\(loss\) earnings from continuing', L): o['cont'] = v
        elif re.search(r'discontinued', L): o['disc'] = v
        elif re.match(r'^net (\(loss\) )?(earnings|income)|^net loss', L): o['ni'] = v
        elif o['ebt'] is None and v is not None: o['other_items'].append([lab, v])
    return o

# ------------------------------------------------------------------ P&L
def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    annual = p.isdigit()
    i = r.get('is') or {}
    s = r.get('seg') or {}
    bl = ebt_below(s.get('below') or [])
    q4 = (not annual) and q == 4
    if q4:
        # fourth-quarter releases print only full-year statements: the quarter's P&L lines come from the release's consolidated table
        rev = s.get('total_sales'); oi = s.get('oi_total')
        put(p, 'rev', rev); put(p, 'oi', oi)
        put(p, 'int_exp', bl['int_exp']); put(p, 'int_inc', bl['int_inc'] if bl['int_inc'] is not None else 0.0)
        put(p, 'nonop_fas', bl['nonop_fas'] if fy >= 2018 else 0.0); put(p, 'mtm', bl['mtm'] if fy >= 2018 else 0.0)
        put(p, 'oth_nonop', N(bl['other_net']) + sum(v for _, v in bl['other_items']))
        put(p, 'ebt', bl['ebt']); put(p, 'tax', -N(bl['tax']) if N(bl['tax']) < 0 and bl['ebt'] and bl['ebt'] > 0 else N(bl['tax']))
        # the consolidated table shows tax as an expense (positive) from 2018 and as a negative line before
        tax = bl['tax']
        if tax is not None and bl['ebt'] is not None and bl['ni'] is not None:
            tax_exp = bl['ebt'] - (bl['cont'] if bl['cont'] is not None else bl['ni'] - N(bl['disc']))
            put(p, 'tax', tax_exp)
        put(p, 'cont_ops', bl['cont'] if bl['cont'] is not None else (bl['ni'] - N(bl['disc']) if bl['ni'] is not None else None))
        put(p, 'disc_ops', N(bl['disc'])); put(p, 'ni', bl['ni'])
        ng = r.get('ng') or []
        put(p, 'eps_d', rec_find(ng, r'^diluted (\(loss\) )?(eps|earnings( \(loss\))? per share)', 1, exclude=r'adjusted|excluding'))
        put(p, 'sh_d', rec_find(ng, r'weighted[- ]average (diluted )?shares outstanding.*diluted|weighted[- ]average diluted shares', 1))
        put(p, 'sh_b', rec_find(ng, r'weighted[- ]average (common )?shares outstanding.*basic|weighted[- ]average common shares', 1))
        put(p, 'eps_b', rec_find(ng, r'^basic (\(loss\) )?(eps|earnings( \(loss\))? per share)', 1, exclude=r'adjusted'))
        # product / service split and costs: fiscal year less nine months
        y = REC.get(str(fy), {}).get('is') or {}
        qs = [REC.get(qk(fy, qq), {}).get('is') or {} for qq in (1, 2, 3)]
        for k in ('prod_sales', 'svc_sales', 'cost_prod', 'cost_svc', 'ga'):
            if y.get(k) is not None and all(qq.get(k) is not None for qq in qs): put(p, k, y[k] - sum(qq[k] for qq in qs))
        put(p, 'q4_derived', 1)
    else:
        put(p, 'rev', i.get('sales')); put(p, 'oi', i.get('oi'))
        for k in ('prod_sales', 'svc_sales', 'cost_prod', 'cost_svc', 'ga', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d', 'eps_d_cont'):
            put(p, k, i.get(k))
        put(p, 'int_exp', -N(i.get('int_exp'))); put(p, 'int_inc', N(i.get('int_inc')))
        put(p, 'nonop_fas', N(i.get('nonop_fas')) if fy >= 2018 else 0.0); put(p, 'mtm', N(i.get('mtm')) if fy >= 2018 else 0.0)
        put(p, 'oth_nonop', N(i.get('other_net')) + sum(N(v) for _, v in i.get('other_nonop', [])))
        put(p, 'cont_ops', i.get('cont_ops') if i.get('cont_ops') is not None else (i['ni'] - N(i.get('disc_ops')) if i.get('ni') is not None else None))
        put(p, 'disc_ops', N(i.get('disc_ops')))
    # cost of sales total and other operating items, closed on the operating-income identity (single-value rows in three-year
    # schedules cannot be placed by position, e.g. the 2008 goodwill impairment printed in the FY2010 release)
    rev, oi = x_(p, 'rev'), x_(p, 'oi')
    if rev is not None and oi is not None and x_(p, 'cost_prod') is not None and x_(p, 'ga') is not None:
        cos = N(x_(p, 'cost_prod')) + N(x_(p, 'cost_svc'))
        put(p, 'cos', cos)
        oth = rev - cos - x_(p, 'ga') - oi          # other operating items as an expense (+); gains negative
        put(p, 'oth_op', round(oth, 6))
        labs = [l for l, v in (i.get('other_op') or []) if v is not None and abs(abs(v) - abs(oth)) < 0.6]
        put(p, 'oth_op_lab', '; '.join(labs))
    if x_(p, 'ebt') is not None and oi is not None:
        res = x_(p, 'ebt') - oi + N(x_(p, 'int_exp')) - N(x_(p, 'int_inc')) - N(x_(p, 'nonop_fas')) - N(x_(p, 'mtm')) - N(x_(p, 'oth_nonop'))
        if abs(res) > 0.6:
            put(p, 'oth_nonop', round(N(x_(p, 'oth_nonop')) + res, 6)); LOG.append(f'{p}: other non-operating closed on the pre-tax identity ({res:+.1f})')
    if p in ('Q1-18', 'Q2-18', 'Q3-18') and RECAST18:
        col = RECAST18['_cols'].index(p)
        def rc(rx):
            for lab, vals in RECAST18.items():
                if not lab.startswith('_') and re.match(rx, lab, re.I): return vals[col]
            return None
        for k in ('oi', 'rc_unalloc', 'nonop_fas', 'oth_nonop', 'ebt', 'tax', 'ni', 'cont_ops', 'eps_d', 'sh_d'):
            if x_(p, k) is not None: put(p, 'orig_' + k, x_(p, k))
        put(p, 'oi', rc(r'^operating income')); put(p, 'nonop_fas', rc(r'^net fas \(non-service\)')); put(p, 'oth_nonop', rc(r'^other, net'))
        put(p, 'ebt', rc(r'^earnings before')); put(p, 'tax', -N(rc(r'^federal and foreign income tax'))); put(p, 'ni', rc(r'^net earnings')); put(p, 'cont_ops', rc(r'^net earnings'))
        put(p, 'eps_d', rc(r'^diluted eps')); put(p, 'sh_d', rc(r'^weighted average shares outstanding'))
        put(p, 'unalloc_recast', rc(r'^unallocated corporate'))
        put(p, 'recast_mtm_2018', 1)
        if x_(p, 'cos') is not None:        # operating costs were not recast line by line: the difference sits in other operating items
            put(p, 'oth_op', round(x_(p, 'rev') - x_(p, 'cos') - x_(p, 'ga') - x_(p, 'oi'), 6)); put(p, 'oth_op_lab', 'MTM accounting-change recast of operating costs (Q4 2018 release Schedule 6)')
        LOG.append(f'{p}: Q1-Q3 2018 taken as recast in the Q4 2018 release (MTM accounting change; original figures in orig_* keys)')
    if x_(p, 'ebt') is not None and x_(p, 'tax') is not None and x_(p, 'cont_ops') is None: put(p, 'cont_ops', x_(p, 'ebt') - x_(p, 'tax'))
    put(p, 'etr', (x_(p, 'tax') / x_(p, 'ebt')) if x_(p, 'ebt') else None)
    if x_(p, 'eps_d') is not None and x_(p, 'sh_d') and x_(p, 'ni') is not None and fy <= 2008:
        adj = x_(p, 'eps_d') * x_(p, 'sh_d') - x_(p, 'ni')
        if abs(adj) > 5: put(p, 'eps_num_adj', round(adj, 1))     # dividends on mandatorily redeemable convertible preferred added back (if-converted); redeemed Apr-2008
    x = r.get('x') or {}
    put(p, 'dps', x.get('dps'))
    # ---- segments
    do_seg(p, r, fy, q, annual)
    # ---- published non-GAAP, backlog, FCF
    ng = r.get('ng') or []
    ngpy = (r.get('py') or {}).get('ng') or []
    idx = 2 if annual else 1
    pens_eps = rec_find(ng, r'^pension-adjusted diluted eps', idx)

    mtm_eps = rec_find(ng, r'^mtm-adjusted (diluted )?eps', idx)
    src = 'release'
    tr_eps = None
    if mtm_eps is None and pens_eps is None:
        tr_eps = rec_find(ng, r'^earnings per share excluding the impact of tax reform', idx)
        if tr_eps is not None and annual:          # Q4 release table prints (fourth quarter, total year): take the year
            for row in ng:
                if re.search(r'^earnings per share excluding the impact of tax reform', row[0], re.I) and len(row) > 4 and row[3] == 2: tr_eps = row[4][1]; break
        if tr_eps is not None: src = 'release (EPS excluding the impact of tax reform and the related discretionary pension contribution)'
    if mtm_eps is None and pens_eps is None and tr_eps is None and ngpy:
        mtm_eps = rec_find(ngpy, r'^mtm-adjusted (diluted )?eps', idx); src = "following year's release (comparative)"
        if mtm_eps is None: pens_eps = rec_find(ngpy, r'^pension-adjusted diluted eps', idx)
    if mtm_eps is None and pens_eps is None and fy >= 2018 and not annual and q != 4:
        mtm_eps = x_(p, 'eps_d'); src = 'MTM nil in interim quarters: MTM-adjusted EPS = diluted EPS'
    put(p, 'adj_eps_pub', mtm_eps if mtm_eps is not None else (pens_eps if pens_eps is not None else tr_eps))
    put(p, 'adj_eps_src', src if (mtm_eps is not None or pens_eps is not None or tr_eps is not None) else None)
    if tr_eps is not None and mtm_eps is None and pens_eps is None:
        put(p, 'adj_def', 'TAXREFORM'); put(p, 'taxreform_ni_pub', rec_find(ng, r'^net earnings excluding tax reform', idx))

    if annual:            # FAS / CAS components (10-K MD&A table; own 10-K first, else the latest 10-K presenting the year)
        for fyk in sorted(FASCAS10K, key=lambda s: (s != str(fy), s)):
            t = FASCAS10K[fyk].get(str(fy))
            if t and t.get('cas') is not None:
                put(p, 'cas_cost', abs(t['cas'])); put(p, 'fas_svc', abs(t['fas_svc']) if t.get('fas_svc') is not None else None); put(p, 'fas_total_10k', t.get('fas_total')); put(p, 'fascas_10k_src', fyk); break
    if pens_eps is not None:
        cont = rec_find(ng, r'^pension-adjusted (diluted )?eps from continuing', idx) is not None or rec_find(ngpy, r'^pension-adjusted (diluted )?eps from continuing', idx) is not None
        put(p, 'adj_eps_basis', 'continuing operations' if cont else 'net earnings')
    put(p, 'adj_def', 'MTM' if mtm_eps is not None else ('PENSION' if pens_eps is not None else ('TAXREFORM' if tr_eps is not None else None)))
    put(p, 'e_def_flag', {'PENSION': 1, 'MTM': 2, 'TAXREFORM': 3}.get(x_(p, 'adj_def'), 0) if x_(p, 'adj_eps_pub') is not None else 0)
    put(p, 'e_cont_flag', 1 if x_(p, 'adj_eps_basis') == 'continuing operations' else 0)
    ps = rec_find(ng, r'^after-tax net pension adjustment per share', idx)
    if ps is None: ps = rec_find(ng, r'^(after-tax mtm (adjustment|expense|benefit) per share|mtm (adjustment|expense|benefit), net of tax, per share)', idx)
    if ps is None and ngpy and x_(p, 'adj_def') == 'MTM': ps = rec_find(ngpy, r'^(after-tax mtm (adjustment|expense|benefit) per share|mtm (adjustment|expense|benefit), net of tax, per share)', idx)
    put(p, 'e_ps_pub', ps)
    put(p, 'pens_adj_ps', rec_find(ng, r'^after-tax net pension adjustment per share', idx))
    put(p, 'pens_adj_pre_ps', rec_find(ng, r'^pre-tax net pension adjustment per share', idx))
    put(p, 'pens_adj_tax_ps', rec_find(ng, r'^tax effect on net pension adjustment per share', idx))
    put(p, 'fascas_tot_pub', rec_find(ng, r'^net fas/cas pension adjustment|^net pension adjustment|^total net fas/cas pension adjustment', idx, exclude=r'per share'))
    put(p, 'mtm_adj_ni_pub', rec_find(ng, r'^mtm-adjusted net earnings', idx) if rec_find(ng, r'^mtm-adjusted net earnings', idx) is not None else rec_find(ngpy, r'^mtm-adjusted net earnings', idx))
    put(p, 'mtm_item_pub', rec_find(ng, r'^mtm (\(benefit\) expense|expense \(benefit\)|\(expense\) benefit|benefit \(expense\)|expense|benefit|\(benefit\))\s*\d?$', idx))
    put(p, 'mtm_state_pub', rec_find(ng, r'^mtm-related deferred state tax', idx, exclude=r'per share'))
    put(p, 'mtm_fed_pub', rec_find(ng, r'^federal tax (benefit|expense|\(benefit\) expense|benefit \(expense\)|expense \(benefit\)|impact).* of (line )?items above', idx, exclude=r'per share'))
    put(p, 'mtm_net_pub', rec_find(ng, r'^(after-tax mtm (adjustment|expense|benefit)|mtm (adjustment|expense|benefit), net of tax|mtm \(benefit\) expense, net of tax)\s*\d?$', idx, exclude=r'per share'))
    put(p, 'trans_adj_eps_pub', rec_find(ng, r'^transaction-adjusted eps', idx))
    put(p, 'fcf_pub', rec_find(ng, r'^free cash flow( provided by continuing operations)?\s*\d?$', idx))
    put(p, 'adj_fcf_pub', rec_find(ng, r'^adjusted free cash flow|^free cash flow( provided by continuing operations)? before (after-tax )?discretionary|^transaction-adjusted free cash flow', idx))
    put(p, 'disc_pension_pub', rec_find(ng, r'^after-tax discretionary pension', idx))
    b = r.get('backlog') or {}
    tr = b.get('total_row')
    if tr and len(tr) >= 3:
        put(p, 'backlog', tr[2]); put(p, 'backlog_funded', tr[0]); put(p, 'backlog_unfunded', tr[1])
    elif tr and len(tr) == 1: put(p, 'backlog', tr[0])
    elif b.get('total_bn_text') is not None: put(p, 'backlog', b['total_bn_text'] * 1000.0); put(p, 'backlog_text', 1)
    if b.get('awards_bn_text') is not None: put(p, 'awards', b['awards_bn_text'] * 1000.0)
    put(p, 'rpo', x.get('rpo'))

# ------------------------------------------------------------------ segments
YEAR_RECAST = {}      # fy -> 'py' (all four quarters recast in the following year's releases), 'orig' (none or only some recast)
def _differs(a, b):
    return any(abs(N((a.get('sales') or {}).get(nm)) - N((b.get('sales') or {}).get(nm))) > 0.6 for nm in CUR)
def year_recast_decisions():
    for fy in range(2013, 2027):
        cnt, have = 0, 0
        for q in (1, 2, 3, 4):
            r = REC.get(qk(fy, q))
            if not r: continue
            s = r.get('seg') or {}; py = (r.get('py') or {}).get('seg')
            if not py or not all(nm in (py.get('sales') or {}) for nm in CUR): continue
            have += 1
            if _differs(py, s): cnt += 1
        YEAR_RECAST[fy] = 'py' if (have == 4 and cnt == 4) else ('mixed' if 0 < cnt < 4 else 'orig')
        if YEAR_RECAST[fy] == 'orig' and have == 4:
            # same-structure restatement of a quarter's operating-income allocation in a later release (Q1 2020 in the Q4 2020 release):
            # use the comparatives when they, and not the originals, sum to the year as reported
            fyr = REC.get(str(fy)) or {}
            fy_oi = (fyr.get('seg') or {}).get('seg_oi')
            own = [((REC[qk(fy, q)].get('seg') or {}).get('seg_oi')) for q in (1, 2, 3, 4)]
            pys = [(((REC[qk(fy, q)].get('py') or {}).get('seg') or {}).get('seg_oi')) for q in (1, 2, 3, 4)]
            if fy_oi is not None and all(v is not None for v in own) and all(v is not None for v in pys):
                if abs(sum(pys) - fy_oi) < 0.6 and abs(sum(own) - fy_oi) > 0.6: YEAR_RECAST[fy] = 'py'

def latest_current_basis(p, r, fy, q, annual):
    """(values dict with 'sales' / 'oi' / 'elim_sales' / 'elim_oi' / 'seg_oi' / 'total_sales', source note) on the current structure"""
    cands = []
    s = r.get('seg') or {}
    if all(n in (s.get('sales') or {}) for n in CUR): cands.append((r['sources'].get('release_date', '0'), s, 'as reported'))
    py = (r.get('py') or {}).get('seg')
    if py and all(n in (py.get('sales') or {}) for n in CUR): cands.append((r['py'].get('release_date', '1'), py, f"as recast in the following year's release ({r['py'].get('release_date')})"))
    if annual:
        for fyk, t in SEG10K.items():
            if fy in t['years'] and all(n in t['sales'] for n in CUR):
                k = t['years'].index(fy)
                d = {'sales': {n: v[k] for n, v in t['sales'].items()}, 'oi': {n: v[k] for n, v in t['oi'].items()},
                     'elim_sales': t['elim_sales'][k] if t['elim_sales'] else None, 'elim_oi': t['elim_oi'][k] if t['elim_oi'] else None,
                     'seg_oi': t['seg_oi'][k] if t['seg_oi'] else None, 'total_sales': t['total_sales'][k] if t['total_sales'] else None,
                     'recon': [(l, v[k]) for l, v in t.get('recon', [])], 'oi_total': t['oi_total'][k] if t.get('oi_total') else None}
                cands.append((t['date'], d, f"as presented in the FY{fyk} Form 10-K segment note ({t['date']})"))
    if not cands: return None, None, None
    cands.sort(key=lambda c: c[0])
    rel = [c for c in cands if not c[2].startswith('as presented in the FY')]
    if fy >= 2013 and rel:
        dec = YEAR_RECAST.get(fy, 'orig')
        own = [c for c in rel if c[2] == 'as reported']
        pyc = [c for c in rel if c[2] != 'as reported']
        if dec == 'py' and pyc: chosen = pyc[-1]
        elif own: chosen = own[-1]
        else: chosen = rel[-1]
        if dec == 'mixed' and chosen[2] == 'as reported': chosen = (chosen[0], chosen[1], 'as reported (the following year\'s releases recast only some quarters of this year; all four kept as reported)')
    else:
        chosen = cands[-1]
    memo = cands[-1] if cands[-1] is not chosen and cands[-1][0] > chosen[0] else None
    return chosen[1], chosen[2], memo

def do_seg(p, r, fy, q, annual):
    s = r.get('seg') or {}
    sales, oi = s.get('sales') or {}, s.get('oi') or {}
    put(p, 'seg_total_sales', s.get('total_sales')); put(p, 'seg_oi_pub', s.get('seg_oi')); put(p, 'seg_oi_total_pub', s.get('oi_total'))
    # current structure
    d, note, memo = latest_current_basis(p, r, fy, q, annual)
    if memo:
        for nme in CUR:
            put(p, f'c10k_{CURK[nme]}_s', memo[1]['sales'].get(nme)); put(p, f'c10k_{CURK[nme]}_oi', memo[1]['oi'].get(nme))
        put(p, 'c10k_elim_s', memo[1].get('elim_sales')); put(p, 'c10k_elim_oi', memo[1].get('elim_oi')); put(p, 'c10k_basis', memo[2])
    if d:
        for n in CUR:
            put(p, f'cur_{CURK[n]}_s', d['sales'].get(n)); put(p, f'cur_{CURK[n]}_oi', d['oi'].get(n))
        put(p, 'cur_elim_s', d.get('elim_sales')); put(p, 'cur_elim_oi', d.get('elim_oi')); put(p, 'cur_seg_oi', d.get('seg_oi'))
        put(p, 'cur_basis', note)
        if note != 'as reported' and all(n in sales for n in CUR):
            for n in CUR:
                put(p, f'orig_{CURK[n]}_s', sales.get(n)); put(p, f'orig_{CURK[n]}_oi', oi.get(n))
            put(p, 'orig_elim_s', s.get('elim_sales')); put(p, 'orig_elim_oi', s.get('elim_oi'))
            put(p, 'cur_recast', 1)
    # legacy structures, as originally reported
    if fy <= 2019 and any(n in sales for n in L16) and 'Technology Services' in sales:
        for n, k in L16.items(): put(p, f'l16_{k}_s', sales.get(n)); put(p, f'l16_{k}_oi', oi.get(n))
        put(p, 'l16_elim_s', s.get('elim_sales')); put(p, 'l16_elim_oi', s.get('elim_oi')); put(p, 'l16_seg_oi', s.get('seg_oi'))
    if fy <= 2015 and 'Electronic Systems' in sales:
        for n, k in L09.items(): put(p, f'l09_{k}_s', sales.get(n)); put(p, f'l09_{k}_oi', oi.get(n))
        put(p, 'l09_elim_s', s.get('elim_sales')); put(p, 'l09_elim_oi', s.get('elim_oi')); put(p, 'l09_seg_oi', s.get('seg_oi'))
    if fy <= 2008:
        for n, k in L06.items():
            subs = [x for x in L06_SUB[n] if x in sales or ('Total ' + x) in sales]
            if not subs: continue
            put(p, f'l06_{k}_s', sum(N(sales.get('Total ' + x, sales.get(x))) for x in subs))
            put(p, f'l06_{k}_oi', sum(N(oi.get('Total ' + x, oi.get(x))) for x in subs))
        put(p, 'l06_elim_s', s.get('elim_sales')); put(p, 'l06_elim_oi', s.get('elim_oi')); put(p, 'l06_seg_oi', s.get('seg_oi'))
        if s.get('total_sales') is not None and s.get('seg_oi') is not None:
            main = ['ins', 'aer', 'ele', 'shp']
            put(p, 'l06_oth_s', round(s['total_sales'] - sum(N(x_(p, f'l06_{k}_s')) for k in main) - N(s.get('elim_sales')), 6))
            put(p, 'l06_oth_oi', round(s['seg_oi'] - sum(N(x_(p, f'l06_{k}_oi')) for k in main) - N(s.get('elim_oi')), 6))
            put(p, 'l06_oth_derived', 1)
    # reconciliation
    rsrc = s
    if d and note and note != 'as reported' and d.get('recon') and d.get('seg_oi') is not None:
        rsrc = d; put(p, 'rc_basis', note)
        for k, kk in (('seg_oi', 'orig_seg_oi_pub'),): put(p, kk, s.get('seg_oi'))
        put(p, 'seg_oi_pub', d.get('seg_oi'))
    rc = recon_items(rsrc.get('recon') or [])
    if rc['unalloc'] is None and rc['labels'] and rsrc.get('recon'):
        rc['unalloc'] = rc['other']; rc['other'] = 0.0; rc['unalloc_lab'] = '; '.join(rc['labels'])
        put(p, 'rc_unalloc_lab', rc['unalloc_lab'])
    if x_(p, 'unalloc_recast') is not None:
        put(p, 'orig_rc_unalloc', rc['unalloc']); rc['unalloc'] = x_(p, 'unalloc_recast')
    put(p, 'rc_fascas', rc['fascas']); put(p, 'rc_unalloc', rc['unalloc']); put(p, 'rc_gain', rc['gain']); put(p, 'rc_divest', rc['divest'])
    put(p, 'rc_royalty', rc['royalty']); put(p, 'rc_intang', rc['intang']); put(p, 'rc_mtm_state', rc['mtm_state']); put(p, 'rc_other_unalloc', rc['other_unalloc'])
    put(p, 'rc_other_lab', '; '.join(rc['labels']))
    seg_oi, oi_t = rsrc.get('seg_oi'), x_(p, 'oi') if x_(p, 'oi') is not None else rsrc.get('oi_total')
    if seg_oi is not None and oi_t is not None:
        gain_sep = 0.0 if rc.get('gain_in_total') else rc['gain'] + rc['divest']
        known = rc['fascas'] + N(rc['unalloc']) + gain_sep + rc['royalty']
        put(p, 'rc_other', round(oi_t - seg_oi - known, 6))
        if abs(oi_t - seg_oi - known - rc['other']) > 0.6 and rc['other']:
            LOG.append(f"{p}: reconciliation residual {oi_t - seg_oi - known - rc['other']:+.1f} beyond labelled other items {rc['labels']}")
    # restated comparatives of consolidated totals (next year's release / 10-K)
    py = r.get('py') or {}
    pis = py.get('is') or {}
    pseg = py.get('seg') or {}
    if pis.get('sales') is not None and x_(p, 'rev') is not None and abs(pis['sales'] - x_(p, 'rev')) > 0.6:
        put(p, 'rev_py', pis['sales']); put(p, 'oi_py', pis.get('oi')); put(p, 'ni_py', pis.get('ni')); put(p, 'restated', 1)
    elif pseg.get('total_sales') is not None and x_(p, 'rev') is not None and abs(pseg['total_sales'] - x_(p, 'rev')) > 0.6:
        put(p, 'rev_py', pseg['total_sales']); put(p, 'oi_py', pseg.get('oi_total')); put(p, 'restated', 1)

# ------------------------------------------------------------------ cash flow
def cf_ytd(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c, x = r['cf'], r.get('x') or {}
    fy, q = fyq(p)
    o = {k: N(c.get(k)) for k in ('capex', 'acq', 'divest', 'equip', 'sale_inv', 'cfi', 'debt_iss', 'debt_rep', 'credit', 'div', 'bb', 'tax_withheld', 'stock_iss', 'cff', 'net')}
    o['cfo'] = c.get('cfo'); o['beg'], o['end'] = c.get('beg'), c.get('end')
    o['dda'] = c.get('dda') if c.get('dda') is not None else x.get('dda_ytd')
    o['sbc'] = c.get('sbc') if c.get('sbc') is not None else x.get('sbc_ytd')
    o['deftax'] = c.get('deftax') if c.get('deftax') is not None else x.get('deftax_ytd')
    pens = [c.get(k) for k in ('mtm', 'pension_inc', 'pension_contrib', 'retiree', 'pension_noncash')]
    if any(v is not None for v in pens): o['pens'] = sum(N(v) for v in pens)
    else: o['pens'] = N(x.get('retiree_ytd')) if fy <= 2015 else 0.0
    o['gain'] = N(c.get('gain_sale')) + N(c.get('b21')) + N(c.get('impairment'))
    o['b21'] = N(c.get('b21'))
    o['src'] = 'release' if c.get('dda') is not None else ('10-K' if p.isdigit() and fy <= 2008 else 'XBRL')
    return o

def cf_lines(c, ni):
    o = {'cf_ni': ni, 'cf_dda': N(c['dda']), 'cf_sbc': N(c['sbc']), 'cf_def': N(c['deftax']), 'cf_pens': c['pens'], 'cf_gain': c['gain'], 'b21': c['b21']}
    o['cf_wc'] = N(c['cfo']) - ni - o['cf_dda'] - o['cf_sbc'] - o['cf_def'] - o['cf_pens'] - o['cf_gain']
    o['cf_cfo'] = N(c['cfo']); o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest'] + c['equip'] + c['sale_inv']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq'] - o['cf_divest']; o['cf_cfi'] = c['cfi']
    o['cf_debt'] = c['debt_iss'] + c['debt_rep'] + c['credit']; o['cf_div'] = c['div']; o['cf_bb'] = c['bb']; o['cf_eq'] = c['stock_iss'] + c['tax_withheld']
    o['cf_ofin'] = c['cff'] - o['cf_debt'] - c['div'] - c['bb'] - o['cf_eq']; o['cf_cff'] = c['cff']
    o['cf_net'] = N(c['cfo']) + c['cfi'] + c['cff']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(p)
        if not a or a['cfo'] is None: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a, N(x_(p, 'ni'))).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end']); put(p, 'cf_src', a['src'])
        if abs(N(a['net']) - (N(a['cfo']) + a['cfi'] + a['cff'])) > 0.6: put(p, 'cf_fx', round(N(a['net']) - (N(a['cfo']) + a['cfi'] + a['cff']), 6))
    for y in range(2013, 2027):
        prev, ni_c = None, 0.0
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q)
            cur = cf_ytd(p)
            ni_c += N(x_(p, 'ni'))
            if cur is None or cur['cfo'] is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur, ni_c)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end']); put(p, 'cf_src', cur['src'])
            fx = N(cur['net']) - (N(cur['cfo']) + cur['cfi'] + cur['cff']) - (prev[2] if prev else 0.0)
            if abs(fx) > 0.6: put(p, 'cf_fx', round(fx, 6))
            prev = (lc, cur['end'], N(cur['net']) - (N(cur['cfo']) + cur['cfi'] + cur['cff']))

# ------------------------------------------------------------------ balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b, x = r['bs'], r.get('x') or {}
    fy, q = fyq(p)
    ta, tca, tcl = b.get('ta'), b.get('tca'), b.get('tcl')
    if ta is None or tca is None or tcl is None: LOG.append(f'{p}: balance sheet totals missing'); return
    cash, ar, unb, inv = N(b.get('cash')), N(b.get('ar')), N(b.get('unbilled')), N(b.get('inv'))
    put(p, 'bs_cash', cash); put(p, 'bs_ar', ar); put(p, 'bs_unb', unb); put(p, 'bs_inv', inv)
    put(p, 'bs_oca', tca - cash - ar - unb - inv); put(p, 'bs_tca', tca)
    ppe, rou, gw = N(b.get('ppe')), N(b.get('rou')), N(b.get('gw'))
    intang = b.get('intang') if b.get('intang') is not None else x.get('intang_bs')
    pens_a = N(b.get('pension_asset'))
    put(p, 'bs_ppe', ppe); put(p, 'bs_rou', rou); put(p, 'bs_gw', gw); put(p, 'bs_int', N(intang)); put(p, 'bs_int_src', 'printed' if b.get('intang') is not None else ('XBRL' if intang is not None else 'n/d'))
    put(p, 'bs_pens_a', pens_a)
    put(p, 'bs_onca', ta - tca - ppe - rou - gw - N(intang) - pens_a); put(p, 'bs_ta', ta)
    ap, accr, adv = N(b.get('ap')), N(b.get('accrued_comp')), N(b.get('advances'))
    std = (N(b.get('notes_pay')) + N(b.get('cur_debt'))) if (b.get('notes_pay') is not None or b.get('cur_debt') is not None) else N(x.get('ltd_cur'))
    put(p, 'bs_ap', ap); put(p, 'bs_accr', accr); put(p, 'bs_adv', adv); put(p, 'bs_std', std)
    put(p, 'bs_std_src', 'printed' if (b.get('notes_pay') is not None or b.get('cur_debt') is not None) else 'XBRL')
    put(p, 'bs_ocl', tcl - ap - accr - adv - std); put(p, 'bs_tcl', tcl)
    ltd, pens_l, lease = N(b.get('ltd')), N(b.get('pension_liab')), N(b.get('lease_liab'))
    tl = b.get('tl') if b.get('tl') is not None else (b['tle'] - b['equity'] if b.get('equity') is not None else None)
    put(p, 'bs_ltd', ltd); put(p, 'bs_pens_l', pens_l); put(p, 'bs_lease', lease)
    put(p, 'bs_oncl', N(tl) - tcl - ltd - pens_l - lease); put(p, 'bs_tl', tl)
    eq = b.get('equity') if b.get('equity') is not None else (b['tle'] - N(tl))
    put(p, 'bs_eq', eq); put(p, 'bs_tle', b.get('tle'))
    put(p, 'bs_shares', x.get('sh_out')); put(p, 'debt_tot', std + ltd)

def run():
    load()
    year_recast_decisions()
    for p in periods():
        do_pl(p); do_bs(p)
    do_cf()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: (round(x[k], 1) if isinstance(x.get(k), float) else x.get(k)) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'cur_as_s', 'cur_seg_oi', 'rc_fascas', 'rc_unalloc', 'rc_other', 'adj_eps_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'debt_tot', 'backlog')})
    print('\n'.join(LOG))
