"""Harmonise the extracted Federal Signal data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy: as originally reported in each period's own 10-K / 10-Q, with one rule for discontinued-operations recasts: when the
following year's 10-Q re-presents a quarter (the Fire Rescue Group / Bronto was moved to discontinued operations in the FY2015
10-K, so Q1-Q3/15 were re-presented in the 2016 10-Qs), the quarter takes that restated comparative, so the quarters of a year are on
the same basis as its annual column. Annual columns stay as originally reported (Tool Group, FSTech and Fire Rescue are included in
the years before each was discontinued); y/y growth uses the prior-year comparative as presented in the current period's filing.
Q4 = the fourth-quarter earnings release three-month column (Ex. 99.1 of the 10-K; Form 8-K for FY2008), else fiscal year - nine months.
Cash flow: as originally reported, year to date; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
Derived lines (stated in the cell comments): tax = earnings before tax - continuing income; discontinued = net income - continuing
income; other operating items = gross profit - SEG&A - amortization - acquisition costs - restructuring - operating income; non-operating
items = operating income - interest - earnings before tax; corporate = operating income - segment operating income; BS / CF 'other'
lines close to the reported subtotals.
"""
import json, glob, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SEGS = ['esg', 'ssg', 'frg', 'tool', 'fst']

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), None
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
def note(p, t): DATA.setdefault(p, {}).setdefault('notes', []).append(t)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def g(d, *ks):
    for k in ks:
        if d is None: return None
        d = d.get(k)
    return d

# ---------------------------------------------------------------- adjusting-item categories
def icat(lab):
    L = lab.lower()
    if re.search(r'interest', L): return 'INT'
    if re.search(r'income tax|tax expense|tax benefit', L) and not re.search(r'special|planning|discrete', L): return 'TAXL'
    if re.search(r'depreciation|amortization', L) and not re.search(r'purchase', L): return 'DA'
    if re.search(r'^other (\(income\) )?(expense|income)', L): return 'NONOP'
    if re.search(r'pension', L): return 'PENSION'
    if re.search(r'debt settlement', L): return 'DEBT'
    if re.search(r'from discontinued operations|loss on discontinued|gain on discontinued|discontinued operations and disposal', L) and 'charges associated' not in L: return 'DISCOPS'
    if re.search(r'special (income )?tax|tax planning|discrete', L): return 'TAXD'
    if re.search(r'acquisition|integration|contingent', L): return 'ACQ'
    if re.search(r'restructuring|severance', L): return 'RESTR'
    if re.search(r'purchase accounting', L): return 'STEPUP'
    return 'OTHER'          # coronavirus, environmental remediation, hearing loss, charges associated with previously discontinued operations
OPCATS = ['ACQ', 'RESTR', 'STEPUP', 'OTHER']
NOPCATS = ['PENSION', 'DEBT']

# ---------------------------------------------------------------- income statement
def is_lines(i):
    """flat IS dict from an extracted IS block (as presented)."""
    if not i or i.get('rev') is None: return None
    o = {}
    rev = i['rev']; o['rev'] = rev
    cogs = i.get('cogs')
    if cogs is not None and cogs < 0: cogs = -cogs
    o['cogs'] = cogs
    o['gp'] = rev - cogs if cogs is not None else i.get('gp')
    for k in ('sga', 'amort', 'acq', 'restr'):
        v = i.get(k)
        o[k] = abs(v) if (v is not None and k == 'sga') else N(v)
    o['oi'] = i.get('oi')
    o['int'] = abs(N(i.get('int_exp')))
    ebt, ni = i.get('ebt'), i.get('ni')
    cont = i.get('cont')
    disc = i.get('disc')
    if cont is None: cont = ni if disc is None else ni - disc
    o['ebt'], o['cont'], o['ni'] = ebt, cont, ni
    if ebt is not None and cont is not None: o['tax'] = ebt - cont
    if ni is not None and cont is not None: o['disc'] = ni - cont
    if o['oi'] is not None and o['gp'] is not None:
        o['opx_oth'] = o['gp'] - o['sga'] - o['amort'] - o['acq'] - o['restr'] - o['oi']
        ps = N(i.get('pension_settle'))
        o['pension_in_oi'] = 1 if (ps > 0.05 and abs(o['opx_oth'] - ps) < 0.15) else 0
    if o['oi'] is not None and ebt is not None:
        o['nonop'] = o['oi'] - o['int'] - ebt
    o['opx_lab'] = '; '.join(f'{l} {v:,.1f}' for l, v in (i.get('other_lines') or []) if abs(v) > 1e-9)
    if o.get('pension_in_oi'): o['opx_lab'] = ('Pension settlement charges (in operating income) %.1f' % i['pension_settle']) + ('; ' + o['opx_lab'] if o['opx_lab'] else '')
    for k in ('eps_d', 'eps_b', 'sh_b', 'sh_d', 'dps'):
        o[k] = i.get(k)
    o['eps_dc'] = i.get('eps_d_cont') if i.get('eps_d_cont') is not None else (i.get('eps_d') if abs(N(o.get('disc'))) < 0.05 else None)
    return o

ISK = ['rev', 'cogs', 'gp', 'sga', 'amort', 'acq', 'restr', 'opx_oth', 'oi', 'int', 'nonop', 'ebt', 'tax', 'cont', 'disc', 'ni']

def do_is(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    src = r['k'].get('is'); basis = 'own filing'
    k1 = g(r, 'k1', 'is')
    if q and k1 and src and k1.get('rev') is not None and abs(k1['rev'] - src['rev']) > 0.5:
        src = k1; basis = 'restated comparative (next-year 10-Q)'
        note(p, f'Income statement and segments from the following year\'s 10-Q prior-year column (re-presented for discontinued operations): '
                f'net sales {r["k"]["is"]["rev"]:,.1f} as first reported -> {k1["rev"]:,.1f}.')
        put(p, 'recast', 1); put(p, 'rev_orig', r['k']['is']['rev'])
    elif q and k1 and src and src.get('amort') is None and N(k1.get('amort')) > 0:
        # amortization shown as its own line from the FY2021 10-K; the 2021 quarters take the 2022 10-Q comparatives (reclassified from SEG&A)
        src = dict(src); src['sga'] = k1['sga']; src['amort'] = k1['amort']
        basis = 'own filing; amortization reclassified out of SEG&A per the next-year 10-Q'
        note(p, f'Amortization expense ({k1["amort"]:,.1f}) shown separately as re-presented in the following year\'s 10-Q (it sat inside SEG&A as first reported).')
        put(p, 'amort_reclass', 1)
    o = is_lines(src)
    if not o: LOG.append(f'{p}: no IS'); return
    for k, v in o.items(): put(p, k, v)
    put(p, 'is_basis', basis)

def do_q4(y):
    """Q4 from the Q4 release three-month column; lines it lacks = FY - 9M."""
    p, a = qk(y, 4), str(y)
    r = REC.get(a)
    rel = is_lines(g(r, 'rel_q4', 'is'))
    used = []
    for k in ISK + ['eps_d', 'eps_dc', 'sh_b', 'sh_d', 'dps']:
        v = rel.get(k) if rel else None
        if v is None and k in ISK:
            fyv = x_(a, k); qs = [x_(qk(y, q), k) for q in (1, 2, 3)]
            if fyv is not None and all(qq is not None for qq in qs):
                v = fyv - sum(qs); used.append(k)
        put(p, k, v)
    if rel:
        put(p, 'opx_lab', rel.get('opx_lab')); put(p, 'pension_in_oi', rel.get('pension_in_oi'))
    note(p, 'Q4 from the fourth-quarter earnings release three-month column (Ex. 99.1 of the 10-K)' + (f'; FY - 9M for: {", ".join(used)}' if used else '') + '.')
    put(p, 'is_basis', 'Q4 release')

# ---------------------------------------------------------------- segments
def seg_src(p):
    r = REC.get(p)
    fy, q = fyq(p)
    if x_(p, 'recast'):
        return g(r, 'k1', 'seg') or {}, g(r, 'k1', 'grp') or {}
    return g(r, 'k', 'seg') or {}, (g(r, 'k', 'grp') or g(r, 'rel', 'grp') or {})

def do_seg(p):
    r = REC.get(p)
    s, gr = seg_src(p)
    rg = g(r, 'rel', 'grp') or {}
    for sg in SEGS:
        put(p, f'sales_{sg}', s.get(f'sales_{sg}', gr.get(f'sales_{sg}')))
        put(p, f'oi_{sg}', s.get(f'oi_{sg}', gr.get(f'oi_{sg}')))
        put(p, f'da_{sg}', s.get(f'da_{sg}', gr.get(f'dda_{sg}', rg.get(f'dda_{sg}'))))
        for kk in ('orders', 'backlog', 'adj_ebitda'):
            v = gr.get(f'{kk}_{sg}', rg.get(f'{kk}_{sg}'))
            if kk == 'adj_ebitda' and v is None: v = g(r, 'rel', 'ebitda', f'adj_ebitda_{sg}')
            put(p, f'{kk}_{sg}', v)
    if s.get('oi_corp') is not None: put(p, 'corp_pub', s['oi_corp'])
    ct = g(r, 'rel', 'corp_text', 'cur')
    if ct is not None: put(p, 'corp_opex_pub', -ct)

def do_seg_q4(y):
    p, a = qk(y, 4), str(y)
    r = REC.get(a)
    rg = g(r, 'rel_q4', 'grp') or {}
    for sg in SEGS:
        for kk, src in (('sales', 'sales'), ('oi', 'oi'), ('orders', 'orders'), ('da', 'dda'), ('adj_ebitda', 'adj_ebitda')):
            v = rg.get(f'{src}_{sg}')
            if kk == 'adj_ebitda' and v is None: v = g(r, 'rel_q4', 'ebitda', f'adj_ebitda_{sg}')
            if v is None and kk in ('sales', 'oi', 'orders', 'da'):
                fyv = x_(a, f'{kk}_{sg}'); qs = [x_(qk(y, q), f'{kk}_{sg}') for q in (1, 2, 3)]
                if fyv is not None and all(qq is not None for qq in qs): v = fyv - sum(qs)
            put(p, f'{kk}_{sg}', v)
        put(p, f'backlog_{sg}', x_(a, f'backlog_{sg}'))
    ct = g(r, 'rel_q4', 'corp_text', 'cur')
    if ct is not None: put(p, 'corp_opex_pub', -ct)

def seg_derived(p):
    oi = x_(p, 'oi')
    if oi is None: return
    s = sum(N(x_(p, f'oi_{sg}')) for sg in SEGS)
    if x_(p, 'oi_esg') is not None: put(p, 'corp', oi - s)
    srev = sum(N(x_(p, f'sales_{sg}')) for sg in SEGS)
    if x_(p, 'sales_esg') is not None: put(p, 'seg_rev_resid', x_(p, 'rev') - srev)

# ---------------------------------------------------------------- comparatives (y/y on the basis of the current filing)
def do_cmp(p):
    fy, q = fyq(p)
    prev = str(fy - 1) if q is None else qk(fy - 1, q)
    r = REC.get(prev)
    if not r: return
    if q == 4:
        c = is_lines(g(REC.get(str(fy)), 'rel_q4', 'is')) if False else None
        cmp_ = is_lines(g(REC.get(str(fy - 1)), 'rel1_q4', 'is'))
    else:
        cmp_ = is_lines(g(r, 'k1', 'is'))
    if cmp_ and cmp_.get('rev') is not None:
        put(p, 'rev_cmp', cmp_['rev'])
        if x_(prev, 'rev') is not None and abs(cmp_['rev'] - x_(prev, 'rev')) > 0.5:
            put(p, 'rev_cmp_flag', 1)

# ---------------------------------------------------------------- non-GAAP
def do_ngaap(p, block='rel'):
    """block: 'rel' (the period's own release) or 'rel_q4' (annual record's Q4 three-month column)."""
    fy, q = fyq(p)
    r = REC.get(str(fy)) if block == 'rel_q4' else REC.get(p)
    if x_(p, 'recast'):
        # restated quarters: the following year's release prior-year column (same basis as the restated statements)
        b = g(r, 'rel1') or {}
    else:
        b = g(r, block) or {}
    e = b.get('ebitda') or {}
    a = b.get('adjeps') or {}
    # Adjusted EBITDA (company) and its adjusting items in operating income
    if e.get('adj_ebitda') is not None and (q is not None or block == 'rel' or True):
        put(p, 'ebitda_pub', e['adj_ebitda'])
        tot = {c: 0.0 for c in OPCATS}; labs = {c: [] for c in OPCATS}
        for it in e.get('adj_ebitda_items') or []:
            c = icat(it['label'])
            if c == 'PENSION' and x_(p, 'pension_in_oi'): c = 'OTHER'
            if c in OPCATS:
                tot[c] += it['v']
                if abs(it['v']) > 1e-9: labs[c].append(f"{it['label']} {it['v']:,.1f}")
        for c in OPCATS:
            put(p, f'ea_{c.lower()}', tot[c]); put(p, f'ea_{c.lower()}_lab', '; '.join(labs[c]))
        put(p, 'ebitda_start', e.get('adj_ebitda_start')); put(p, 'ebitda_start_label', e.get('adj_ebitda_start_label'))
    # adjusted EPS bridge
    if a.get('adj_eps') is not None or a.get('adj_ni') is not None:
        put(p, 'e_pub', a.get('adj_eps'))
        adj_ni = a.get('adj_ni')
        fmt = a.get('fmt')
        if fmt == 'ps' or adj_ni is None or (adj_ni is not None and a.get('adj_eps') is not None and abs(adj_ni) < 5 and abs(adj_ni - a['adj_eps']) < 0.02):
            sh = x_(p, 'sh_d')
            if a.get('adj_eps') is not None and sh:
                adj_ni = a['adj_eps'] * sh; put(p, 'adj_ni_from_ps', 1)
                note(p, 'Adjusted net income = published adjusted EPS x diluted shares (the release gives a per-share reconciliation only).')
            else: adj_ni = None
        put(p, 'adj_ni_pub', adj_ni)
        tot = {c: 0.0 for c in OPCATS + NOPCATS + ['TAXD']}; labs = {c: [] for c in tot}
        items = a.get('items') or []
        ps_only = fmt == 'ps' or bool(x_(p, 'adj_ni_from_ps'))
        for it in items:
            c = icat(it['label'])
            if c in ('INT', 'TAXL', 'DA', 'NONOP', 'DISCOPS'): continue
            if c == 'PENSION' and x_(p, 'pension_in_oi'): c = 'OTHER'
            v = it['v']
            if ps_only:
                sh = x_(p, 'sh_d'); v = v * sh if sh else 0.0
            if c not in tot: c = 'OTHER'
            tot[c] += v
            if abs(v) > 1e-9: labs[c].append(f"{it['label']} {it['v']:,.2f}" + (' per share' if ps_only else ''))
        net = fmt == 'net' or ps_only
        put(p, 'e_items_net', 1 if net else 0)
        for c in tot:
            put(p, f'ei_{c.lower()}', tot[c]); put(p, f'ei_{c.lower()}_lab', '; '.join(labs[c]))
        put(p, 'e_start_label', a.get('start_label'))

def op_items(p):
    """adjusting items inside operating income used by the model bridges: the adjusted EBITDA reconciliation items where the company
    published adjusted EBITDA, else the pre-tax items of the adjusted EPS reconciliation, else none (adjusted = GAAP)."""
    src = 'none'
    if x_(p, 'ebitda_pub') is not None: src = 'ea'
    elif x_(p, 'e_pub') is not None and not x_(p, 'e_items_net'): src = 'ei'
    for c in ('acq', 'restr', 'stepup', 'other'):
        put(p, f'oa_{c}', x_(p, f'{src}_{c}') if src != 'none' else 0.0)
        put(p, f'oa_{c}_lab', x_(p, f'{src}_{c}_lab') if src != 'none' else '')
    put(p, 'oa_src', src)
    if x_(p, 'e_pub') is not None and not x_(p, 'e_items_net'):
        put(p, 'e_preitems', sum(N(x_(p, f'ei_{c}')) for c in ('acq', 'restr', 'stepup', 'other', 'pension', 'debt')))
        put(p, 'e_preitems_lab', '; '.join(x for x in (x_(p, f'ei_{c}_lab') for c in ('acq', 'restr', 'stepup', 'other', 'pension', 'debt')) if x))
        put(p, 'ea_nonop', N(x_(p, 'ei_pension')) + N(x_(p, 'ei_debt')) if not x_(p, 'pension_in_oi') else N(x_(p, 'ei_debt')))
        labs = '; '.join(x for x in (x_(p, 'ei_pension_lab') if not x_(p, 'pension_in_oi') else '', x_(p, 'ei_debt_lab')) if x)
        put(p, 'ea_nonop_lab', labs)
        put(p, 'e_taxd', N(x_(p, 'ei_taxd')))
    elif x_(p, 'e_items_net'):
        put(p, 'e_preitems', 0.0)
        tot = sum(N(x_(p, f'ei_{c}')) for c in ('acq', 'restr', 'stepup', 'other', 'pension', 'debt', 'taxd'))
        put(p, 'e_netitems', tot)
        put(p, 'e_netitems_lab', '; '.join(x for x in (x_(p, f'ei_{c}_lab') for c in ('acq', 'restr', 'stepup', 'other', 'pension', 'debt', 'taxd')) if x))
    else:
        put(p, 'e_preitems', 0.0)

def adj_basis(p):
    """flags which adjusted measures the company published for the period."""
    fy, q = fyq(p)
    put(p, 'adj_ebitda_basis', 'published' if x_(p, 'ebitda_pub') is not None else 'none')
    put(p, 'adj_eps_basis', 'published' if x_(p, 'e_pub') is not None else 'none')

# ---------------------------------------------------------------- cash flow
CFK = ['ni', 'dda', 'sbc', 'deftax', 'cfo', 'capex', 'acq', 'cfi', 'debt', 'bb', 'withhold', 'div', 'stock_iss', 'cff', 'fx', 'net']

def cf_ytd(p):
    r = REC.get(p)
    c = g(r, 'k', 'cf')
    if not c: return None
    x = r.get('x') or {}
    o = {}
    o['cfo'] = c.get('cfo'); o['capex'] = N(c.get('capex')) + 0.0; o['capex_disp'] = N(c.get('capex_disp'))
    o['acq'] = N(c.get('acq')); o['cfi'] = c.get('cfi')
    o['debt'] = N(c.get('rev_net')) + N(c.get('debt_proc')) + N(c.get('debt_repay'))
    o['bb'] = N(c.get('bb')); o['withhold'] = N(c.get('withhold')); o['div'] = N(c.get('div')); o['stock_iss'] = N(c.get('stock_iss'))
    o['cff'] = c.get('cff'); o['fx'] = N(c.get('fx')); o['net'] = c.get('net')
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    o['dda'] = c.get('dda') if c.get('dda') is not None else x.get('dda_ytd')
    o['sbc'] = c.get('sbc') if c.get('sbc') is not None else N(x.get('sbc_ytd'))
    o['deftax'] = c.get('deftax') if c.get('deftax') is not None else N(x.get('deftax_ytd'))
    if o['net'] is None and o['beg'] is not None and o['end'] is not None: o['net'] = o['end'] - o['beg']
    return o

def cf_lines(c, ni):
    o = {k: c[k] for k in ('cfo', 'capex', 'acq', 'cfi', 'debt', 'bb', 'withhold', 'div', 'stock_iss', 'cff', 'fx', 'net', 'dda', 'sbc', 'deftax')}
    o['ni'] = ni
    o['wc'] = c['cfo'] - ni - N(c['dda']) - c['sbc'] - c['deftax']
    o['cfi_oth'] = c['cfi'] - c['capex'] - c['acq']
    o['cff_oth'] = c['cff'] - c['debt'] - c['bb'] - c['withhold'] - c['div'] - c['stock_iss']
    o['disc_cf'] = c['net'] - c['cfo'] - c['cfi'] - c['cff'] - c['fx']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); c = cf_ytd(p)
        if not c or c['cfo'] is None: LOG.append(f'{p}: no annual CF'); continue
        cni = g(REC[p], 'k', 'is', 'ni')
        for k, v in cf_lines(c, cni).items(): put(p, 'cf_' + k, v)
        put(p, 'cf_beg', c['beg']); put(p, 'cf_end', c['end']); put(p, 'cf_cashadj', 0.0)
        if x_(p, 'bs_cash') is not None and c['end'] is not None and abs(c['end'] - x_(p, 'bs_cash')) > 0.05:
            put(p, 'cf_cash_disc', c['end'] - x_(p, 'bs_cash'))
            if y >= 2013: put(qk(y, 4), 'cf_cash_disc', c['end'] - x_(p, 'bs_cash'))
            note(p, f'Cash-flow cash {c["end"]:,.1f} includes {c["end"] - x_(p, "bs_cash"):,.1f} of cash held by discontinued operations (balance sheet cash {x_(p, "bs_cash"):,.1f}).')
    for y in range(2013, 2027):
        prev = None; ni_c = 0.0
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q)
            if q == 4:
                c = cf_ytd(str(y)); ni_y = g(REC[str(y)], 'k', 'is', 'ni')
            else:
                c = cf_ytd(p); ni_y = None
            # CF net income = net income as originally reported (incl. discontinued operations)
            ni_q = g(REC.get(p), 'k', 'is', 'ni') if q < 4 else (ni_y - ni_c if ni_y is not None else None)
            if q < 4 and ni_q is not None: ni_c += ni_q
            if c is None or c['cfo'] is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(c, ni_c if q < 4 else ni_y)
            if q == 1: d = lc; beg = c['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, 'cf_' + k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', c['end'])
            if beg is not None and c['end'] is not None:
                adj = c['end'] - beg - d['net']
                put(p, 'cf_cashadj', adj if abs(adj) > 0.05 else 0.0)
                if abs(adj) > 0.05: note(p, f'Cash basis difference {adj:,.1f}: the year-to-date statements start from a different opening cash (cash of discontinued operations).')
            prev = (lc, c['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    b = g(r, 'k', 'bs')
    if not b: return
    ta, tca = b['ta'], b.get('tca')
    cash = b.get('cash')
    put(p, 'bs_cash', cash); put(p, 'bs_ar', b.get('ar')); put(p, 'bs_inv', b.get('inv'))
    put(p, 'bs_oca', tca - cash - N(b.get('ar')) - N(b.get('inv')))
    put(p, 'bs_tca', tca); put(p, 'bs_ppe', b.get('ppe')); put(p, 'bs_rental', N(b.get('rental')))
    put(p, 'bs_gw', b.get('gw')); put(p, 'bs_int', N(b.get('intang')))
    put(p, 'bs_onca', ta - tca - N(b.get('ppe')) - N(b.get('rental')) - N(b.get('gw')) - N(b.get('intang'))); put(p, 'bs_ta', ta)
    std = N(b.get('std'))
    put(p, 'bs_std', std); put(p, 'bs_ap', b.get('ap')); put(p, 'bs_dep', N(b.get('cust_dep')))
    put(p, 'bs_ocl', b['tcl'] - std - N(b.get('ap')) - N(b.get('cust_dep'))); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', N(b.get('ltd')))
    eq = b.get('eq')
    tl = b.get('tl') if b.get('tl') is not None else b['tle'] - eq
    put(p, 'bs_oncl', tl - b['tcl'] - N(b.get('ltd')))
    put(p, 'bs_eq', eq); put(p, 'bs_tle', b['tle'])
    if b.get('sh_issued') is not None and b.get('sh_treasury') is not None: put(p, 'bs_shares', b['sh_issued'] - b['sh_treasury'])
    elif (r.get('x') or {}).get('sh_out') is not None: put(p, 'bs_shares', r['x']['sh_out'])
    put(p, 'debt_tot', std + N(b.get('ltd')))
    put(p, 'bs_ppex', N(b.get('ppe')) + N(b.get('rental')))
    d = MAN['debt']
    if p == 'Q3-26':      # split of the 30-Sep-2026 debt (Q3-26 10-Q Note 5): term loan; revolver + finance leases net of issuance costs
        put(p, 'debt_tl', d['tl']); put(p, 'debt_rev', std + N(b.get('ltd')) - d['tl'])

def do_misc(p):
    r = REC.get(p)
    x = r.get('x') or {}
    fy, q = fyq(p)
    if x_(p, 'dps') is None and x.get('dps_declared') is not None: put(p, 'dps', x['dps_declared'])
    for k in ('rev', 'oi', 'ni', 'eps_d', 'ta', 'cont'):
        if x.get(k) is not None: put(p, f'xb_{k}', x[k])

def run():
    load()
    for p in periods():
        fy, q = fyq(p)
        if q == 4: continue
        do_is(p); do_seg(p); do_bs(p); do_misc(p); do_cmp(p)
    for y in range(2013, 2026):
        do_q4(y); do_seg_q4(y); do_bs(qk(y, 4)) if False else None
        p4 = qk(y, 4)
        # Q4 balance sheet = year-end balance sheet
        for k, v in list(DATA.get(str(y), {}).get('x', {}).items()):
            if k.startswith('bs_') or k in ('debt_tot', 'cf_cash_disc'): put(p4, k, v)
        do_cmp(p4)
        dps = g(REC.get(str(y)), 'x', 'dps_declared')
        dq = [x_(qk(y, q), 'dps') for q in (1, 2, 3)]
        if x_(p4, 'dps') is None and dps is not None and all(v is not None for v in dq): put(p4, 'dps', dps - sum(dq)) if dps > sum(dq) + 0.001 else None
    for p in periods():
        fy, q = fyq(p)
        seg_derived(p)
        if q == 4: do_ngaap(p, 'rel_q4')
        else: do_ngaap(p, 'rel')
        op_items(p)
        adj_basis(p)
    do_cf()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'sales_esg', 'oi_esg', 'corp', 'ebitda_pub', 'e_pub', 'adj_ni_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'debt_tot')})
    print('\n'.join(LOG))
