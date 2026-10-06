"""Harmonise the extraction JSON (data/<period>.json) into the model's data keys and run cross-checks.

- 2-for-1 split (June 2010): pre-split share counts / per-share data restated to the post-split basis.
- Hybrid recast: income statement, segments and adjusted EPS of a period are taken from the prior-year comparative column
  of the filing one year later when that filing restated the period (discontinued operations: Fortive 2016, Envista 2019,
  Veralto 2023, others; segment recasts). Balance sheet and cash flow stay as originally reported.
- Cash flow: quarterly records carry year-to-date statements; discrete quarters derived (Q4 = FY − 9M).
- Derived 'other' lines so each statement section sums to its published subtotal.
- Adjusted-results bridges: operating-level items (company 'other operating profit adjustments' + amortization),
  non-operating items, tax effect and discrete tax, from the release notes ($m) or per-share lines × diluted shares.
"""
import json, os, glob, re, copy

BASE = os.path.dirname(os.path.abspath(__file__))
RAW, DATA, LOG, BASIS = {}, {}, [], {}

def num(x):
    if isinstance(x, bool) or x is None: return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip().replace(',', '').replace('$', '').replace('~', '').replace('%', '')
    neg = s.startswith('(')
    s = s.strip('()').strip()
    if s in ('—', '-', '–', ''): return 0.0 if s else None
    try:
        v = float(s); return -v if neg else v
    except ValueError:
        return None
def N(x): return num(x) or 0.0

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        try: RAW[k] = json.load(open(f))
        except Exception as e: LOG.append(f'{k}: bad JSON {e}')

def is_period(k): return bool(re.fullmatch(r'(20\d\d|Q[1-4]-\d\d)', k))
def prior_key(k):
    if k.isdigit(): return str(int(k) - 1)
    return f'{k[:3]}{int(k[3:]) - 1:02d}'
def next_key(k):
    if k.isdigit(): return str(int(k) + 1)
    return f'{k[:3]}{int(k[3:]) + 1:02d}'

# ---------------------------------------------------------------- segment name mapping
SEGMAP = [(r'biotech', 'bio'), (r'life sciences\s*(&|and)\s*diagnostics', 'lsd'), (r'life sciences', 'ls'), (r'diagnostics', 'dx'),
          (r'environmental\s*(&|and)\s*applied', 'eas'), (r'environmental', 'env'), (r'dental', 'dental'),
          (r'test\s*(&|and)\s*measurement', 'tm'), (r'industrial technologies', 'it'), (r'professional instrumentation', 'pi'),
          (r'medical technologies', 'mt'), (r'tools\s*(&|and)\s*components', 'tc'), (r'apex', 'apex'), (r'other|corporate', 'other')]
def segkey(name):
    n = (name or '').lower()
    for pat, k in SEGMAP:
        if re.search(pat, n): return k
    LOG.append(f'unmapped segment name {name!r}'); return None

# ---------------------------------------------------------------- split
def split_factor(d):
    return 2.0 if str((d.get('is') or {}).get('per_share_basis', '')).startswith('pre') else 1.0

def flat(k, d, src='orig'):
    """Flatten one period record (current-period columns) to model keys."""
    i, s, ng = d.get('is') or {}, d.get('seg') or {}, d.get('ngaap') or {}
    f = split_factor(d)
    x = {}
    for a in ('sales', 'cogs', 'gp', 'sga', 'rnd', 'op_profit', 'interest_exp', 'interest_inc', 'ebt', 'tax', 'cont_ops', 'disc_ops',
              'net_income', 'nci', 'pref_div', 'ni_common'):
        x['is_' + a] = num(i.get(a))
    x['is_other_op'] = sum(N(b) for _, b in (i.get('other_op_lines') or [])) if i.get('other_op_lines') else 0.0
    x['is_nonop'] = sum(N(b) for _, b in (i.get('nonop_lines') or [])) if i.get('nonop_lines') else 0.0
    for a in ('shares_basic', 'shares_diluted'):
        v = num(i.get(a)); x['is_' + a] = None if v is None else v * f
    for a in ('eps_basic_cont', 'eps_dil_cont', 'eps_dil', 'dps'):
        v = num(i.get(a)); x['is_' + a] = None if v is None else v / f
    if x['is_gp'] is None and x['is_sales'] is not None and x['is_cogs'] is not None: x['is_gp'] = x['is_sales'] - x['is_cogs']
    # segments
    for sg in s.get('segments') or []:
        sk = segkey(sg.get('name'))
        if not sk: continue
        for a in ('sales', 'op_profit', 'amort', 'dep', 'adj_op', 'other_adj', 'growth_total', 'growth_acq', 'growth_fx', 'growth_core'):
            v = num(sg.get(a))
            if v is not None: x[f'sg_{sk}_{a}'] = v
    x['sg_other_op_profit'] = num(s.get('other_op_profit'))
    tg = s.get('total_growth') or {}
    for a in ('total', 'acq', 'fx', 'core', 'other'): x['g_' + a] = num(tg.get(a))
    x['resp_sales'] = num(s.get('respiratory_sales')); x['core_ex_resp'] = num(s.get('core_ex_resp'))
    # non-GAAP
    x['adj_eps_pub'] = None if num(ng.get('adj_eps_pub')) is None else num(ng['adj_eps_pub']) / f
    x['adj_op_pub'] = num(ng.get('adj_op_pub'))
    x['fcf_pub'] = num(ng.get('fcf_pub'))
    x['amort_pretax'] = num(ng.get('amort_pretax'))
    x['_bridge'] = ng.get('eps_bridge') or []
    x['_items'] = ng.get('item_amounts') or []
    x['_eps_start'] = None if num(ng.get('eps_bridge_start')) is None else num(ng['eps_bridge_start']) / f
    x['_f'] = f
    return x

def flat_py(d):
    """Flatten the prior-year comparative columns of a record (used for the recast basis)."""
    p = d.get('py') or {}
    if not p: return None
    f = split_factor(d)
    i = p.get('is') or {}
    x = {}
    for a in ('sales', 'cogs', 'sga', 'rnd', 'op_profit', 'interest_exp', 'interest_inc', 'ebt', 'tax', 'cont_ops', 'disc_ops', 'net_income', 'pref_div'):
        x['is_' + a] = num(i.get(a))
    x['is_other_op'] = num(i.get('other_op')) or 0.0
    x['is_nonop'] = num(i.get('nonop')) or 0.0
    for a in ('shares_basic', 'shares_diluted'):
        v = num(i.get(a)); x['is_' + a] = None if v is None else v * f
    for a in ('eps_dil_cont', 'eps_dil'):
        v = num(i.get(a)); x['is_' + a] = None if v is None else v / f
    if x['is_sales'] is not None and x['is_cogs'] is not None: x['is_gp'] = x['is_sales'] - x['is_cogs']
    for sg in p.get('segments') or []:
        sk = segkey(sg.get('name'))
        if sk and num(sg.get('sales')) is not None:
            x[f'sg_{sk}_sales'] = num(sg['sales'])
            if num(sg.get('op_profit')) is not None: x[f'sg_{sk}_op_profit'] = num(sg['op_profit'])
    x['sg_other_op_profit'] = num(p.get('other_op_profit'))
    x['adj_eps_pub'] = None if num(p.get('adj_eps_pub')) is None else num(p['adj_eps_pub']) / f
    x['amort_pretax'] = num(p.get('amort_pretax'))
    x['_restated'] = bool(p.get('restated'))
    x['_notes'] = p.get('notes')
    return x

# ---------------------------------------------------------------- hybrid recast
RECAST_KEYS = ('is_sales', 'is_cogs', 'is_gp', 'is_sga', 'is_rnd', 'is_other_op', 'is_op_profit', 'is_nonop', 'is_interest_exp', 'is_interest_inc',
               'is_ebt', 'is_tax', 'is_cont_ops', 'is_disc_ops', 'is_net_income', 'is_pref_div', 'is_shares_basic', 'is_shares_diluted',
               'is_eps_dil_cont', 'is_eps_dil')
def apply_recast(k, x):
    n = next_key(k)
    if n not in RAW: return x
    py = flat_py(RAW[n])
    if not py or py.get('is_sales') is None or x.get('is_sales') is None: return x
    diff = abs(py['is_sales'] - x['is_sales']) / max(1.0, abs(x['is_sales']))
    seg_changed = any(kk.startswith('sg_') and kk.endswith('_sales') and abs(N(py[kk]) - N(x.get(kk))) > 1.0 for kk in py)
    seg_changed = seg_changed or any(kk.startswith('sg_') and kk.endswith('_sales') and kk not in py and N(x.get(kk)) for kk in x)
    opd = abs(N(py.get('is_op_profit')) - N(x.get('is_op_profit'))) if py.get('is_op_profit') is not None else 0.0
    cod = abs(N(py.get('is_cont_ops')) - N(x.get('is_cont_ops'))) if py.get('is_cont_ops') is not None else 0.0
    if diff > 0.003 or opd > 1.0 or cod > 1.0:
        BASIS[k] = f'recast: prior-year comparatives in the {n} filing ({py.get("_notes") or "discontinued operations"})'
        for kk in RECAST_KEYS:
            if py.get(kk) is not None: x[kk] = py[kk]
        # earnings after the recast: disc ops picks up the moved earnings, so net income is unchanged
        for kk in [kk for kk in x if kk.startswith('sg_') and (kk.endswith('_sales') or kk.endswith('_op_profit'))]:
            x.pop(kk)
        for kk, v in py.items():
            if kk.startswith('sg_'): x[kk] = v
        for kk in ('sg_other_op_profit',):
            x[kk] = py.get(kk)
        if py.get('adj_eps_pub') is not None and x.get('adj_eps_pub') is not None:
            x['adj_eps_orig'] = x.get('adj_eps_pub'); x['adj_eps_pub'] = py['adj_eps_pub']
        if py.get('amort_pretax') is not None: x['amort_pretax'] = py['amort_pretax']
        x['_recast'] = n
        x['_recast_ni'] = cod > 1.0
    elif seg_changed and all(py.get(kk) is not None for kk in py if kk.startswith('sg_')):
        BASIS[k] = f'segments recast: prior-year comparatives in the {n} filing'
        for kk in [kk for kk in x if kk.startswith('sg_') and (kk.endswith('_sales') or kk.endswith('_op_profit'))]:
            x.pop(kk)
        for kk, v in py.items():
            if kk.startswith('sg_'): x[kk] = v
        x['_recast_seg'] = n
    return x

def harmonise_seg_recast():
    """a segment-only recast is applied to a year's quarters only if every quarter of that year has it (keeps quarters on one basis)."""
    for y in range(2013, 2027):
        ks = [f'Q{q}-{str(y)[2:]}' for q in (1, 2, 3, 4)]
        flags = [bool(DATA.get(k, {}).get('_recast_seg')) for k in ks if k in DATA]
        if any(flags) and not all(flags):
            for k in ks:
                if DATA.get(k, {}).get('_recast_seg'):
                    orig = flat(k, RAW[k])
                    for kk in [kk for kk in DATA[k] if kk.startswith('sg_')]: DATA[k].pop(kk)
                    for kk, v in orig.items():
                        if kk.startswith('sg_'): DATA[k][kk] = v
                    DATA[k].pop('_recast_seg'); BASIS.pop(k, None)

# ---------------------------------------------------------------- cash flow
CF_CORE = ['net_income', 'disc_ops_ni', 'dep', 'amort', 'sbc', 'deferred_tax', 'impair', 'gains', 'wc_change', 'cfo_cont', 'cfo_disc', 'cfo',
           'capex', 'capex_disposals', 'acquisitions', 'divest', 'invest_purch', 'invest_sales', 'cfi_disc', 'cfi',
           'stock_iss', 'pref_iss', 'dividends', 'buyback', 'debt_net_short', 'debt_proceeds', 'debt_repay', 'spin_cash', 'cff_disc', 'cff',
           'fx', 'net_change']
def cf_ytd(cf):
    o = {k: num(cf.get(k)) for k in CF_CORE}
    o['cash_begin'] = num(cf.get('cash_begin')); o['cash_end'] = num(cf.get('cash_end')); o['ytd'] = num(cf.get('ytd_months'))
    if o['cfo'] is None and o['cfo_cont'] is not None: o['cfo'] = o['cfo_cont'] + N(o['cfo_disc'])
    return o
def cf_derive(o):
    """model cash-flow lines: CFO on a total basis (continuing + discontinued) so the cash roll ties."""
    q = {}
    q['cf_ni'] = o['net_income']; q['cf_dep'] = o['dep']; q['cf_amort'] = o['amort']; q['cf_sbc'] = o['sbc']
    q['cf_def'] = o['deferred_tax']; q['cf_wc'] = o['wc_change']; q['cf_cfo'] = o['cfo']
    if o['cfo'] is not None:
        q['cf_oth'] = o['cfo'] - N(o['net_income']) - N(o['dep']) - N(o['amort']) - N(o['sbc']) - N(o['deferred_tax']) - N(o['wc_change'])
    q['cf_capex'] = o['capex']; q['cf_disp'] = o['capex_disposals']; q['cf_acq'] = o['acquisitions']; q['cf_div_bus'] = o['divest']
    q['cf_cfi'] = o['cfi']
    if o['cfi'] is not None:
        q['cf_oinv'] = o['cfi'] - N(o['capex']) - N(o['capex_disposals']) - N(o['acquisitions']) - N(o['divest'])
    q['cf_stock'] = o['stock_iss']; q['cf_divs'] = o['dividends']; q['cf_bb'] = o['buyback']
    q['cf_debt'] = (N(o['debt_net_short']) + N(o['debt_proceeds']) + N(o['debt_repay'])) if any(
        o[k] is not None for k in ('debt_net_short', 'debt_proceeds', 'debt_repay')) else None
    q['cf_cff'] = o['cff']
    if o['cff'] is not None:
        q['cf_ofin'] = o['cff'] - N(o['stock_iss']) - N(o['dividends']) - N(o['buyback']) - N(q['cf_debt'])
    q['cf_fx'] = o['fx']; q['cf_net'] = o['net_change']
    q['cf_beg'] = o['cash_begin']; q['cf_end'] = o['cash_end']
    q['cfo_cont'] = o['cfo_cont']
    return q

def build_cf():
    for k, d in RAW.items():
        if not is_period(k) or not d.get('cf'): continue
        DATA[k]['_cfytd'] = cf_ytd(d['cf'])
    for k in [k for k in DATA if k.isdigit()]:
        o = DATA[k].get('_cfytd')
        if o: DATA[k].update(cf_derive(o))
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            k = f'Q{q}-{str(y)[2:]}'
            if k not in DATA: prev = None; continue
            cur = DATA[k].get('_cfytd')
            if q == 4 and str(y) in DATA and DATA[str(y)].get('_cfytd'): cur = DATA[str(y)]['_cfytd']
            if not cur: prev = None; continue
            if q == 1: disc = dict(cur)
            elif prev is None: LOG.append(f'{k}: no prior YTD cash flow'); prev = cur; continue
            else:
                disc = {}
                for kk in CF_CORE:
                    disc[kk] = None if cur[kk] is None else cur[kk] - N(prev[kk])
                disc['cash_begin'] = prev['cash_end']; disc['cash_end'] = cur['cash_end']
            DATA[k].update(cf_derive(disc))
            prev = cur

# ---------------------------------------------------------------- balance sheet
def build_bs():
    for k, d in RAW.items():
        if not is_period(k) or not d.get('bs'): continue
        b = d['bs']; g = lambda a: num(b.get(a)); x = DATA[k]
        for a in ('cash', 'ar', 'inventories', 'tca', 'ppe', 'goodwill', 'intangibles', 'ta', 'st_debt', 'ap', 'accrued', 'tcl', 'ltd',
                  'other_ltl', 'other_lta', 'pref', 'retained', 'aoci', 'dhr_equity', 'nci', 'te', 'tle', 'treasury'):
            x['bs_' + a] = g(a)
        f = split_factor(d)
        so = g('shares_out'); x['bs_shares'] = None if so is None else so * (f if (f > 1 and so < 400) else 1)
        if x['bs_tca'] is not None:
            x['bs_oca'] = x['bs_tca'] - N(g('cash')) - N(g('ar')) - N(g('inventories'))     # prepaid & other (+ held for sale)
        if x['bs_ta'] is not None and x['bs_tca'] is not None:
            x['bs_onca'] = x['bs_ta'] - x['bs_tca'] - N(g('ppe')) - N(g('goodwill')) - N(g('intangibles'))
        if x['bs_tcl'] is not None:
            x['bs_ocl'] = x['bs_tcl'] - N(g('st_debt')) - N(g('ap')) - N(g('accrued'))
        tl = None
        if g('tle') is not None and g('te') is not None: tl = g('tle') - g('te')
        if tl is not None and x['bs_tcl'] is not None:
            x['bs_oncl'] = tl - x['bs_tcl'] - N(g('ltd'))                               # other LT liabilities (+ disc ops)
        cap = None
        if g('dhr_equity') is not None:
            cap = g('dhr_equity') - N(g('retained')) - N(g('aoci')) - N(g('treasury')) - N(g('pref'))
        x['bs_cap'] = cap
        if g('ta') is not None and g('tle') is not None and abs(g('ta') - g('tle')) > 1.0: LOG.append(f'{k}: BS TA {g("ta")} vs TL&E {g("tle")}')

# ---------------------------------------------------------------- bridges
def classify(label):
    l = (label or '').lower()
    if 'amortization' in l and 'intangible' in l: return 'amort'
    if 'tax effect' in l: return 'taxeff'
    if 'discrete tax' in l or 'tax-related' in l or 'tax related' in l or 'tax law' in l or 'tax reform' in l or 'tax cuts' in l: return 'disc'
    if 'rounding' in l: return 'round'
    if re.search(r'\btax(es)?\b', l) and not any(w in l for w in ('pre-tax', 'pretax', 'after-tax', 'after tax')): return 'disc'
    if 'preferred' in l or 'mcps' in l: return 'pref'
    if any(w in l for w in ('investment', 'extinguishment', 'debt', 'interest', 'pension', 'nonoperating', 'non-operating', 'bond')): return 'nonop'
    if 'discontinued' in l: return 'discops'
    return 'op'

def build_bridges():
    """$m bridge lines from the release footnotes (item amounts, located by the extraction 'where' field), falling back to
    per-share lines × diluted shares. Narrative bridges without a tax-effect line are after-tax (no separate tax effect)."""
    for k, x in DATA.items():
        if x.get('adj_eps_pub') is None: continue
        sh = x.get('is_shares_diluted') or 0.0
        bridge = [r for r in (x.get('_bridge') or []) if isinstance(r, list) and len(r) >= 2 and num(r[1]) is not None]
        has_tax_line = any(classify(r[0]) == 'taxeff' for r in bridge)
        ps = {'amort': 0.0, 'op': 0.0, 'nonop': 0.0, 'taxeff': 0.0, 'disc': 0.0, 'pref': 0.0, 'round': 0.0, 'other': 0.0}
        for r in bridge:
            c = classify(r[0]); c = 'other' if c == 'discops' else c
            ps[c] += num(r[1]) / x['_f']
        rows = []
        for row in x.get('_items') or []:
            if not isinstance(row, list) or len(row) < 2: continue
            lab, pre = row[0], num(row[1]); aft = num(row[2]) if len(row) > 2 else None
            where = str((row[3] if len(row) > 3 else '') or '').lower()
            if where not in ('op', 'nonop'): continue
            cat = 'amort' if classify(lab) == 'amort' else where
            if pre is None and aft is None: continue
            rows.append((cat, pre, aft))
        b = {'amort': 0.0, 'op': 0.0, 'nonop': 0.0}
        if rows:
            all_aft = all(a is not None for _, _, a in rows)
            for cat, pre, aft in rows:
                if has_tax_line: b[cat] += pre if pre is not None else aft
                else: b[cat] += aft if aft is not None else pre
            if has_tax_line:
                if x.get('amort_pretax') is not None and not any(c == 'amort' for c, _, _ in rows): b['amort'] += x['amort_pretax']; all_aft = False
                taxeff = sum((a - p) for _, p, a in rows if p is not None and a is not None) if all_aft else ps['taxeff'] * sh
            else:
                taxeff = 0.0
        else:
            for c in b: b[c] = ps[c] * sh
            taxeff = ps['taxeff'] * sh
        x['br_amort'], x['br_op'], x['br_nonop'] = b['amort'], b['op'], b['nonop']
        x['br_taxeff'] = taxeff
        x['br_disc'] = ps['disc'] * sh
        # MCPS: preferred dividends added back where GAAP diluted EPS (and adjusted EPS) use the if-converted method
        ni = N(x.get('is_cont_ops')) - N(x.get('is_nci')) - N(x.get('is_pref_div'))
        ifc = 0.0
        if N(x.get('is_pref_div')) > 0 and x.get('is_eps_dil_cont') is not None and abs(x['is_eps_dil_cont'] * sh - ni) > 0.006 * sh:
            ifc = x['is_eps_dil_cont'] * sh - ni
        base = ni + b['amort'] + b['op'] + b['nonop'] + taxeff + x['br_disc'] + ps['pref'] * sh + (ps['round'] + ps['other']) * sh
        if ifc and abs((base + ifc) / sh - x['adj_eps_pub']) >= abs(base / sh - x['adj_eps_pub']): ifc = 0.0   # company EPS not on the if-converted basis
        x['br_pref'] = ps['pref'] * sh + ifc
        x['br_resid'] = (ps['round'] + ps['other']) * sh
        if x.get('_recast_ni'):
            tot = ni + b['amort'] + b['op'] + b['nonop'] + taxeff + x['br_disc'] + x['br_pref']
            x['br_resid'] = x['adj_eps_pub'] * sh - tot
            x['_resid_recast'] = True

def contrib(total, acq, fx, core):
    """growth bridge → (acq, fx, core) contributions in fractions, whatever sign convention the record used:
    deduction convention (company table: total + acq + fx = core) or contribution convention (core + acq + fx = total)."""
    if core is None: return None, None, None
    a, f = N(acq), N(fx)
    if total is not None:
        if abs(total + a + f - core) <= 0.06 and not abs(core + a + f - total) <= 0.06: a, f = -a, -f
        elif abs(core + a + f - total) <= 0.06: pass
        elif abs(total + a + f - core) <= 0.06: a, f = -a, -f      # both fit (a = f = 0)
    return a / 100, f / 100, core / 100

def load_json(name):
    p = os.path.join(BASE, 'data', name)
    return json.load(open(p)) if os.path.exists(p) else {}

MAN = {}
def build_misc():
    global MAN
    MAN = load_json('manual_items.json')
    deals = load_json('deals.json')
    for k, x in DATA.items():
        ni = x.get('is_net_income')
        if ni is not None:
            x['is_ni_common_calc'] = ni - N(x.get('is_nci')) - N(x.get('is_pref_div'))
        x['dps'] = x.get('is_dps')
        # amortization: release footnote (pretax, continuing ops) when published, else cash-flow statement
        x['amort'] = x.get('amort_pretax') if x.get('amort_pretax') is not None else x.get('cf_amort')
        # growth contributions
        for sk in ('bio', 'ls', 'dx', 'lsd', 'eas', 'env', 'dental', 'tm', 'it', 'pi', 'mt', 'tc', 'apex'):
            a, f, c = contrib(x.get(f'sg_{sk}_growth_total'), x.get(f'sg_{sk}_growth_acq'), x.get(f'sg_{sk}_growth_fx'), x.get(f'sg_{sk}_growth_core'))
            if c is not None: x[f'sg_{sk}_acqc'], x[f'sg_{sk}_fxc'], x[f'sg_{sk}_core'] = a, f, c
        a, f, c = contrib(x.get('g_total'), x.get('g_acq'), x.get('g_fx'), x.get('g_core'))
        if c is not None: x['g_acqc'], x['g_fxc'], x['g_corec'] = a, f, c
        if x.get('core_ex_resp') is not None: x['core_ex_resp_c'] = x['core_ex_resp'] / 100
        r = num(((RAW.get(k) or {}).get('seg') or {}).get('recurring_pct'))
        if r is not None: x['recurring'] = r / 100
        e = num(((RAW.get(k) or {}).get('extra') or {}).get('employees'))
        if e is not None: x['employees'] = e
        # free cash flow on the company's basis: components of the release FCF table where published, else the cash-flow statement
        ngr = (RAW.get(k) or {}).get('ngaap') or {}
        pub = x.get('fcf_pub') is not None
        x['fcf_cfo'] = num(ngr.get('cfo_pub_period')) if (pub and num(ngr.get('cfo_pub_period')) is not None) else (x.get('cfo_cont') if x.get('cfo_cont') is not None else x.get('cf_cfo'))
        x['fcf_capex'] = num(ngr.get('capex_pub')) if (pub and num(ngr.get('capex_pub')) is not None) else x.get('cf_capex')
        if pub: x['fcf_disp'] = num(ngr.get('capex_disposals_pub')) or 0.0      # 2010–12 definition excluded PP&E disposals
        else: x['fcf_disp'] = x.get('cf_disp')
        # other operating profit adjustments (op-level items excl. amortization) from the adjusted-EPS bridge
        if x.get('br_op') is not None: x['o_oth'] = x['br_op']
        # segment legacy keys (Diagnostics ex Masimo set below)
        for kk in [kk for kk in x if re.fullmatch(r'sg_[a-z]+_(sales|op_profit)', kk)]:
            x[kk + '_l'] = x[kk]
    # manual overrides / allocations (segment other operating profit adjustments by quarter, etc.)
    for k, items in (MAN.get('period_overrides') or {}).items():
        if k in DATA:
            for kk, v in items.items():
                if not kk.startswith('_'): DATA[k][kk] = v
    # ---- Masimo
    ms = load_json('masimo_standalone.json').get('periods', {})
    qmap = {}
    for key, v in ms.items():
        kind, end = key.split(':')
        y, m = int(end[:4]), int(end[5:7])
        if kind == 'FY':
            fy = y if m >= 6 else y - 1
            qmap[str(fy)] = v
        else:
            q = {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3, 12: 4, 1: 4}[m]
            fy = y if not (m == 1) else y - 1
            qmap[f'Q{q}-{str(fy)[2:]}'] = v
    for y in (2024, 2025):
        fyv = qmap.get(str(y))
        qs = [qmap.get(f'Q{q}-{str(y)[2:]}') for q in (1, 2, 3)]
        if fyv and all(qs):
            qmap[f'Q4-{str(y)[2:]}'] = {kk: round(fyv[kk] - sum(q[kk] for q in qs), 1) for kk in ('sales', 'op') if kk in fyv and all(kk in q for q in qs)}
    for k, v in qmap.items():
        if k.startswith(('Q1-23', 'Q2-23', 'Q3-23', '2023', '2022')): continue
        DATA.setdefault(k, {})
        if 'sales' in v: DATA[k]['ms_sa_rev'] = v['sales']
        if 'op' in v: DATA[k]['ms_sa_op'] = v['op']
    M = (MAN.get('masimo') or {})
    q = DATA.get('Q2-26')
    if q is not None and M:
        q['ms_days'] = M['days_q2']
        q['ms_rev'] = M['sales_q2']
        q['ms_amort'] = M['amort_q2']
        q['ms_inv'] = M['items_q2']
        q['ms_adjop'] = round(M['sales_q2'] * M['adj_margin_q2'], 1)
        q['ms_op_l'] = round(q['ms_adjop'] - q['ms_amort'] - M.get('items_in_dx_q2', 0.0), 1)
        # legacy Diagnostics = reported − Masimo
        if q.get('sg_dx_sales') is not None:
            q['sg_dx_sales_l'] = q['sg_dx_sales'] - q['ms_rev']
            q['sg_dx_op_profit_l'] = q['sg_dx_op_profit'] - q['ms_op_l']
            if q.get('sg_dx_amort') is not None: q['sg_dx_amort'] = q['sg_dx_amort'] - q['ms_amort']
            if q.get('sg_dx_other_adj') is not None: q['sg_dx_other_adj'] = q['sg_dx_other_adj'] - M.get('items_in_dx_q2', 0.0)
        p = M['ppa']
        for kk in ('cons', 'stock', 'ar', 'inv', 'ppe', 'int', 'gw', 'ap', 'dtl', 'oth', 'life'):
            q['ppa_' + kk] = p.get(kk)
        q['ds_fac'] = M['cp_q2']; q['ds_notes'] = round(N(q.get('bs_st_debt')) + N(q.get('bs_ltd')) - M['cp_q2'], 1)

def checks():
    for k, x in sorted(DATA.items()):
        s = x.get('is_sales')
        if s is None: LOG.append(f'{k}: no sales'); continue
        op = N(x.get('is_gp')) - N(x.get('is_sga')) - N(x.get('is_rnd')) - N(x.get('is_other_op'))
        if x.get('is_op_profit') is not None and abs(op - x['is_op_profit']) > 1.0: LOG.append(f'{k}: IS op {op:.1f} vs {x["is_op_profit"]}')
        ebt = N(x.get('is_op_profit')) + N(x.get('is_nonop')) - N(x.get('is_interest_exp')) + N(x.get('is_interest_inc'))
        if x.get('is_ebt') is not None and abs(ebt - x['is_ebt']) > 1.0: LOG.append(f'{k}: IS ebt {ebt:.1f} vs {x["is_ebt"]}')
        segs = [kk for kk in x if re.fullmatch(r'sg_[a-z]+_sales', kk) and kk != 'sg_other_sales']
        if segs:
            t = sum(N(x[kk]) for kk in segs)
            if abs(t - s) > 1.5: LOG.append(f'{k}: segment sales {t:.1f} vs sales {s:.1f} ({",".join(segs)})')
        if x.get('cf_cfo') is not None and x.get('cf_net') is not None:
            t = N(x['cf_cfo']) + N(x['cf_cfi']) + N(x['cf_cff']) + N(x['cf_fx']) - N(x['cf_net'])
            if abs(t) > 1.0: LOG.append(f'{k}: CF sections vs net change {t:+.1f}')

def run():
    load()
    for k in sorted(RAW):
        if not is_period(k): continue
        x = flat(k, RAW[k])
        x['_orig_sales'] = x.get('is_sales')
        DATA[k] = apply_recast(k, x)
    harmonise_seg_recast()
    build_cf(); build_bs(); build_bridges(); build_misc(); checks()
    return DATA

if __name__ == '__main__':
    run()
    print('\n'.join(LOG) or 'no issues')
    for k, v in sorted(BASIS.items()): print(k, v)
