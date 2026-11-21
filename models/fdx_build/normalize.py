"""Map the extracted FedEx rows (data/<period>.json: [group, label, value]) to flat model keys: DATA[period]['x'][key] (USD m).

Two bases sit side by side in the model and are never mixed in one series:
  legacy   L<fy> (annual, FY2006-FY2026) and LQ<q>-<yy> (Q1 FY2013 - Q4 FY2026): fiscal years ended 31 May, FedEx Freight
           consolidated, every period as originally reported in its own earnings release (no recasts: the FY2015 change to
           mark-to-market pension accounting, ASU 2017-07 in FY2019 and ASC 842 in FY2020 are not applied backwards).
  calendar CY<yyyy> (2024, 2025) and CQ<q>-<yy> (Q1/24 - Q3/26): years ended 31 December, FedEx Freight in discontinued operations,
           Express U.S. Domestic / Express International segments, from the recast exhibits (21-Jul-2026, 28-Oct-2026) and the
           release of 28-Oct-2026. C9M-25 / C9M-26 carry the nine-month cash flow (not recast for discontinued operations).
Derived values (all noted in the model): legacy Q4 dividends declared and basic shares from XBRL; diluted shares of the recast
calendar periods = net income / diluted EPS (the recast exhibits print no share count); discrete quarterly cash flow from year to date;
'other' balance-sheet and cash-flow lines as residuals to the reported totals."""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json'))) if os.path.exists(os.path.join(BASE, 'manual_items.json')) else {}

def N(x): return x or 0.0
def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

LEG_A = [str(y) for y in range(2006, 2013)] + [f'FY{str(y)[2:]}' for y in range(2013, 2027)]
def lkey(p):                     # extraction key -> model key
    if p.isdigit(): return 'L' + p
    if p.startswith('FY'): return 'L20' + p[2:]
    if p.startswith('Q'): return 'L' + p
    return p
def periods():
    out = [lkey(p) for p in LEG_A] + [f'LQ{q}-{str(y)[2:]}' for y in range(2013, 2027) for q in (1, 2, 3, 4)]
    out += ['CY2024', 'CY2025'] + [f'CQ{q}-{yy}' for yy in ('24', '25', '26') for q in (1, 2, 3, 4) if not (yy == '26' and q == 4)]
    return out

# ---------------------------------------------------------------- income statement
SEGN = [(r'u\.s\. domestic', 'usd'), (r'express international', 'intl'), (r'federal express', 'fec'), (r'tnt express', 'tnt'),
        (r'fedex express', 'exp'), (r'fedex ground', 'gnd'), (r'fedex freight', 'frt'), (r'kinko', 'kin'), (r'fedex services', 'svc')]
def segname(l):
    l = l.lower()
    for pat, k in SEGN:
        if re.search(pat, l): return k
    return 'oth'
STD = [(r'^salaries', 'sal'), (r'^purchased transp', 'pt'), (r'^rentals', 'rent'), (r'^depreciation', 'da'), (r'^fuel', 'fuel'), (r'^maintenance', 'maint')]

def do_is(p, rows):
    st = 'rev'; sr, so, spec, nonop = {}, {}, [], []
    o = {}
    eps_seen = []
    for g, l, v in rows:
        full = (g + ' ' + l).lower(); ll = l.lower().strip()
        if st == 'rev':
            if re.search(r'total revenue', full): o['rev'] = v; st = 'opex'
            else: k = segname(l); sr[k] = sr.get(k, 0.0) + v
            continue
        if st == 'opex':
            if re.search(r'total operating\s+expenses', full): o['opex_tot'] = v; st = 'oi'; continue
            for pat, k in STD:
                if re.search(pat, ll): o[k] = v; break
            else:
                if re.fullmatch(r'other(, net)?', ll): o['oth'] = v
                else: spec.append((l, v))
            continue
        if st == 'oi':
            if re.search(r'total operating', full) or re.match(r'operating (income|loss|\(loss\))', ll):
                o['oi'] = v; st = 'nonop'
            else: k = segname(l); so[k] = so.get(k, 0.0) + v
            continue
        if re.search(r'pretax|before income taxes', full): o['ebt'] = v; st = 'bot'; continue
        if re.search(r'provision for income\s+taxes', full): o['tax'] = v; st = 'bot'; continue
        if re.search(r'from continuing operations', ll) and 'eps' not in o and abs(v) > 50: o['ni_cont'] = v; continue
        if re.search(r'from discontinued operations', ll) and abs(v) >= 0 and 'ni' not in o: o['disc'] = v; continue
        if re.match(r'net \(?(income|loss)', ll) and 'per' not in ll and 'from' not in ll: o['ni'] = v; st = 'bot'; continue
        if re.search(r'^basic earnings', ll): o['eps_b'] = v; eps_seen = []; continue
        if re.search(r'diluted .*per (common )?share', full): o['eps_d'] = v; st = 'bot'; continue
        if ll in ('continuing operations', 'discontinued operations'): eps_seen.append((ll, v)); o['_eps_parts'] = list(eps_seen); continue
        if re.search(r'common equivalent shares', full): o['sh_d'] = v; continue
        if re.search(r'dividends declared', ll): o['dps'] = v; continue
        if re.search(r'^capital expenditures', ll): o['capex_is'] = v; continue
        if re.search(r'full-time equivalents', ll): continue
        if st == 'nonop':
            if re.search(r'total other', full) or re.match(r'total expense', ll): o['nonop_tot'] = v; st = 'bot'
            elif re.search(r'^interest', ll): o['int_net'] = v
            elif re.search(r'retirement plans', ll): o['ret'] = N(o.get('ret')) + v
            elif re.search(r'short-term investment|investment in fedex freight|retained (interest|investment)', ll): o['inv_gain'] = v
            else: nonop.append((l, v))
    # EPS from continuing operations: the diluted block is the 'continuing operations' row directly above the diluted total
    parts = o.pop('_eps_parts', [])
    if parts:
        cont = [v for k, v in parts if k == 'continuing operations']
        if cont: o['eps_cont'] = cont[-1]
    for k, v in o.items(): put(p, k, v)
    put(p, 'spec', sum(v for _, v in spec)); put(p, 'spec_lab', '; '.join(f'{l} {v:,.0f}' for l, v in spec if v))
    put(p, 'oth_nonop', sum(v for _, v in nonop)); put(p, 'oth_nonop_lab', '; '.join(f'{l} {v:,.0f}' for l, v in nonop if v))
    for k in ('ret', 'inv_gain', 'int_net'):
        if k not in o: put(p, k, 0.0)
    for k, v in sr.items(): put(p, 'sr_' + k, v)
    for k, v in so.items(): put(p, 'so_' + k, v)
    if 'ni_cont' not in o and 'ni' in o: put(p, 'ni_cont', o['ni']); put(p, 'disc', 0.0)
    if 'ni' not in o and 'ni_cont' in o: put(p, 'ni', o['ni_cont'] + N(o.get('disc')))
    if 'eps_cont' not in o and 'eps_d' in o: put(p, 'eps_cont', o['eps_d'])

# ---------------------------------------------------------------- segment tables / operating statistics
def find(rows, lab, grp=None, nth=0):
    hits = [v for g, l, v in rows if re.search(lab, l.lower()) and (grp is None or re.search(grp, g.lower()))]
    return hits[nth] if len(hits) > nth else None

G_ADV, G_YLD, G_LB, G_YLB = r'daily package|package volume|adv', r'yield \(rev|revenue per package|yield \(revenue per', r'freight pounds', r'per (freight )?pound'
def do_express(p, rows, fec=False):
    """FedEx Express (to FY2024) / Federal Express (FY2025-26) / Express U.S. Domestic + International segment tables."""
    def stat(key, lab, grp): put(p, key, find(rows, lab, grp))
    stat('adv_pri', r'^(total )?u\.s\. (overnight package|priority)$|^total u\.s\. overnight$', G_ADV)
    if x_(p, 'adv_pri') is None:                      # releases to FY2012 print box and envelope without a total: sum (noted in the model)
        bx, en = find(rows, r'^u\.s\. overnight box', G_ADV), find(rows, r'^u\.s\. overnight envelope', G_ADV)
        if bx is not None and en is not None: put(p, 'adv_pri', bx + en); put(p, 'adv_pri_sum', 1)
    stat('adv_def', r'^u\.s\. deferred', G_ADV)
    stat('adv_gc', r'ground commercial', G_ADV); stat('adv_ghd', r'home delivery', G_ADV)
    stat('adv_us', r'total u\.s\. domestic', G_ADV)
    stat('adv_ip', r'^international priority', G_ADV); stat('adv_ie', r'^international economy', G_ADV)
    stat('adv_ex', r'total international export', G_ADV); stat('adv_id', r'^international domestic', G_ADV)
    stat('adv_tot', r'^total (average daily packages|adv)$', G_ADV)
    stat('y_pri', r'^u\.s\. (overnight composite|priority)$', G_YLD); stat('y_def', r'^u\.s\. deferred', G_YLD)
    stat('y_gnd', r'^u\.s\. ground$', G_YLD); stat('y_us', r'u\.s\. domestic composite', G_YLD)
    stat('y_ip', r'^international priority', G_YLD); stat('y_ie', r'^international economy', G_YLD)
    stat('y_ex', r'international export composite', G_YLD); stat('y_id', r'^international domestic', G_YLD)
    stat('y_tot', r'^composite package yield', G_YLD)
    stat('lb_us', r'^u\.s\.( freight)?$', G_LB); stat('lb_ip', r'^international priority', G_LB)
    stat('lb_ie', r'^international (economy|airfreight)', G_LB); stat('lb_tot', r'^total (avg|average) daily freight pounds', G_LB)
    stat('ylb_us', r'^u\.s\.( freight)?$', G_YLB); stat('ylb_ip', r'^international priority', G_YLB)
    stat('ylb_ie', r'^international (economy|airfreight)', G_YLB); stat('ylb_tot', r'^composite freight yield', G_YLB)
    put(p, 'days', find(rows, r'^operating (weekdays|days)', None))
    # revenue by service: only the package-revenue rows of the segment income statement (above 'Total package revenue')
    cut = [i for i, (g, l, v) in enumerate(rows) if re.search(r'^total package revenue', l.lower())]
    fin = rows[:cut[0]] if cut else []
    put(p, 'r_pri', find(fin, r'^(total u\.s\. overnight|u\.s\. priority)$', None))
    put(p, 'r_def', find(fin, r'^u\.s\. deferred$', None)); put(p, 'r_gnd', find(fin, r'^u\.s\. ground$', None))
    put(p, 'r_ip', find(fin, r'^international priority$', None)); put(p, 'r_ie', find(fin, r'^international economy$', None))
    put(p, 'r_id', find(fin, r'^international domestic$', None))

def do_usd(p, rows):
    do_express(p, rows)
    put(p, 'r_pkg_us', find(rows, r'^total package revenue', None)); put(p, 'r_ufrt', find(rows, r'^u\.s\. freight$', None))
    put(p, 'r_uoth', find(rows, r'^other$', r'package|revenue|freight'))
    put(p, 'usd_rev', find(rows, r'^total revenue', None)); put(p, 'usd_oi', find(rows, r'^operating income', None))
    for pat, k in STD: put(p, 'usd_' + k, find(rows, pat, r'operating expenses'))
    if x_(p, 'adv_gc') is not None: put(p, 'adv_gnd', x_(p, 'adv_gc') + N(x_(p, 'adv_ghd')))

def do_intl(p, rows):
    def stat(key, lab, grp, nth=0): put(p, key, find(rows, lab, grp, nth))
    stat('adv_ip', r'^international priority', G_ADV); stat('adv_ie', r'^international economy', G_ADV)
    stat('adv_id', r'^international domestic', G_ADV); stat('adv_intl', r'^total adv', G_ADV)
    stat('y_ip', r'^international priority', G_YLD); stat('y_ie', r'^international economy', G_YLD)
    stat('y_id', r'^international domestic', G_YLD); stat('y_intl', r'^composite package yield', G_YLD)
    stat('lb_ip', r'^international priority', G_LB); stat('lb_ie', r'^international economy', G_LB); stat('lb_intl', r'^total average daily freight pounds', G_LB)
    stat('ylb_ip', r'^international priority', G_YLB); stat('ylb_ie', r'^international economy', G_YLB); stat('ylb_intl', r'^composite freight yield', G_YLB)
    put(p, 'days_i', find(rows, r'^operating (weekdays|days)', None))
    fin = [r for r in rows if not re.search(G_ADV + '|' + G_YLD + '|' + G_LB + '|' + G_YLB, r[0].lower())]
    put(p, 'r_ip', find(fin, r'^international priority$', None, 0)); put(p, 'r_ie', find(fin, r'^international economy$', None, 0))
    put(p, 'r_id', find(fin, r'^international domestic', None)); put(p, 'r_pkg_i', find(fin, r'^total package revenue', None))
    put(p, 'r_fip', find(fin, r'^international priority$', None, 1)); put(p, 'r_fie', find(fin, r'^international economy$', None, 1))
    put(p, 'r_ifrt', find(fin, r'^total freight revenue', None)); put(p, 'r_ioth', find(fin, r'^other$', None))
    put(p, 'intl_rev', find(fin, r'^total revenue', None)); put(p, 'intl_oi', find(fin, r'^operating income', None))

def do_ground(p, rows):
    G = r'package volume'; Y = r'yield|package volume'
    tot = find(rows, r'^total average daily package volume', None)
    if tot is None:
        a = find(rows, r'^fedex ground$', G); b = find(rows, r'smartpost', G)
        if a is not None: tot = a + N(b); put(p, 'adv_gnd_note', 'FedEx Ground + FedEx SmartPost (sum)' if b is not None else None)
        else: tot = find(rows, r'^average daily package volume', None)
    put(p, 'adv_gnd', tot)
    gc = find(rows, r'^ground commercial$', G)
    if gc is not None:
        put(p, 'adv_gc', gc); put(p, 'adv_ghd', N(find(rows, r'^home delivery$', G)) + N(find(rows, r'^economy$', G)))
    y = find(rows, r'^yield \(revenue per package\)$', None)
    put(p, 'y_gnd', y)

def do_freight(p, rows):
    put(p, 'lf_ship', find(rows, r'^total average daily (ltl )?shipments|^ltl shipments per day|shipments per day', None))
    put(p, 'lf_wt', find(rows, r'^composite weight per (ltl )?shipment|^weight per ltl shipment|shipment \(lbs\)', None))
    put(p, 'lf_cwt', find(rows, r'^composite (ltl )?(revenue/cwt|yield|revenue per hundredweight)|^ltl revenue/cwt', None))
    put(p, 'lf_rps', find(rows, r'^composite (ltl )?revenue(/| per )shipment', None))
    put(p, 'lf_days', find(rows, r'operating weekdays|weekdays', None))

# ---------------------------------------------------------------- balance sheet
def do_bs(p, rows):
    st = 'ca'; o = {}
    def add(k, v): o[k] = o.get(k, 0.0) + v
    for g, l, v in rows:
        full = (g + ' ' + l).lower(); ll = l.lower()
        if st == 'ca':
            if re.search(r'total current assets', full): o['tca'] = v; st = 'lta'
            elif re.search(r'^restricted cash', ll): add('rcash', v)
            elif re.search(r'^cash and cash|^cash and cash equivalents|equivalents$', ll) or full.strip().endswith('cash equivalents'): add('cash', v)
            elif re.search(r'^receivables', ll): add('ar', v)
            elif re.search(r'short-term investment', ll): add('sti', v)
            elif re.search(r'discontinued', ll): add('disc_ca', v)
            else: add('oca_named', v)
            continue
        if st == 'lta':
            if re.search(r'^property and equipment, at cost|less accumulated', ll): continue
            if re.search(r'net property and\s+equipment|property and equipment, net', ll) or (ll == 'equipment' and 'net property' in g.lower()): o['ppe'] = v
            elif re.search(r'right-of-use', ll): add('rou', v)
            elif re.search(r'^goodwill$', ll): add('gw', v)
            elif re.search(r'^goodwill and other assets', ll): add('gw_oth', v)
            elif re.search(r'equity method', ll): add('eqm', v)
            elif re.search(r'discontinued', ll): add('disc_nca', v)
            elif re.search(r'total other long-term assets', ll) or (ll == 'assets' and 'other long-term' in g.lower()) or ll == 'other long-term assets': o['tolta'] = v
            elif re.search(r'^total assets', ll): o['ta_pub'] = v
            elif re.search(r'current portion of long-term debt|short-term borrowings', full): st = 'cl'
            elif re.search(r'accrued|accounts', ll): st = 'cl'
            else: add('olta_named', v)
            if st != 'cl': continue
        if st == 'cl':
            if re.search(r'total current liabilities', full): o['tcl'] = v; st = 'ltl'
            elif re.search(r'current portion of long-term debt', full): add('cltd', v)
            elif re.search(r'short-term borrowings', ll): add('stb', v)
            elif re.search(r'accrued salaries', ll): add('acc_sal', v)
            elif re.search(r'^accounts( and notes)? payable', ll): add('ap', v)
            elif re.search(r'operating lease', ll): add('lease_c', v)
            elif re.search(r'discontinued', ll): add('disc_cl', v)
            else: add('ocl_named', v)
            continue
        if st == 'ltl':
            if re.search(r'long-term debt,\s+less current portion', ll) or (ll == 'less current portion' and 'long-term debt' in g.lower()): o['ltd'] = v
            elif re.search(r'total other long-term liabilities', ll) or (ll == 'liabilities' and 'other long-term' in g.lower()) or ll == 'other long-term liabilities': o['toltl'] = v
            elif re.search(r'^total liabilities and', ll): o['tle_pub'] = v
            elif re.search(r'total common\s+stockholders', full): o['eq'] = v
            elif re.search(r'^common stock|paid-in|retained earnings|comprehensive|treasury stock', ll): o[{'c': 'eq_cs', 'p': 'eq_apic', 'r': 'eq_re', 'o': 'eq_aoci', 't': 'eq_ts'}['c' if ll.startswith('common') else 'p' if 'paid' in ll else 'r' if 'retained' in ll else 't' if 'treasury' in ll else 'o']] = v
            elif re.search(r'operating lease', ll): add('lease_nc', v)
            elif re.search(r'^deferred income taxes', ll): add('dtl', v)
            elif re.search(r'^pension', ll): add('pens', v)
            elif re.search(r'self-insurance', ll): add('selfins', v)
            elif re.search(r'discontinued', ll): add('disc_ncl', v)
            else: add('oltl_named', v)
    if 'tca' not in o: LOG.append(f'{p}: balance sheet not parsed'); return
    ta = o['tca'] + o['ppe'] + o['tolta']
    tle = o['tcl'] + o['ltd'] + o['toltl'] + o['eq']
    put(p, 'bs_cash', o['cash']); put(p, 'bs_ar', o.get('ar')); put(p, 'bs_sti', o.get('sti')); put(p, 'bs_rcash', o.get('rcash'))
    put(p, 'bs_oca', o['tca'] - o['cash'] - N(o.get('ar')) - N(o.get('sti')))
    put(p, 'bs_tca', o['tca']); put(p, 'bs_ppe', o['ppe']); put(p, 'bs_rou', o.get('rou'))
    put(p, 'bs_gw', o.get('gw')); put(p, 'bs_eqm', o.get('eqm'))
    put(p, 'bs_onca', o['tolta'] - N(o.get('rou')) - N(o.get('gw')) - N(o.get('eqm')))
    put(p, 'bs_ta', ta)
    det = MAN.get('bs_detail', {}).get(p, {})              # current debt / leases shown only in the 10-Q notes
    for k in ('cltd', 'lease_c'):
        if k in det and k not in o: o[k] = det[k]
    put(p, 'bs_std', N(o.get('cltd')) + N(o.get('stb'))); put(p, 'bs_ap', o.get('ap')); put(p, 'bs_accsal', o.get('acc_sal'))
    put(p, 'bs_lease_c', o.get('lease_c'))
    put(p, 'bs_ocl', o['tcl'] - N(o.get('cltd')) - N(o.get('stb')) - N(o.get('ap')) - N(o.get('acc_sal')))
    put(p, 'bs_tcl', o['tcl']); put(p, 'bs_ltd', o['ltd']); put(p, 'bs_lease_nc', o.get('lease_nc')); put(p, 'bs_dtl', o.get('dtl'))
    put(p, 'bs_pens', o.get('pens')); put(p, 'bs_selfins', o.get('selfins'))
    put(p, 'bs_oltl', o['toltl'] - N(o.get('lease_nc')) - N(o.get('dtl')) - N(o.get('pens')) - N(o.get('selfins')))
    put(p, 'bs_eq', o['eq']); put(p, 'bs_tle', tle)
    for k in ('eq_cs', 'eq_apic', 'eq_re', 'eq_aoci', 'eq_ts', 'disc_ca', 'disc_nca', 'disc_cl', 'disc_ncl'): put(p, 'bs_' + k, o.get(k))
    put(p, 'debt_tot', N(o.get('cltd')) + N(o.get('stb')) + o['ltd'])

# ---------------------------------------------------------------- cash flow (year to date)
def cf_ytd(rows, src=None):
    for c in MAN.get('corrections', []):                   # documented data corrections (manual_items.json)
        if c['period'] == src and c['table'] == 'cf':
            rows = [[g, l, (c['used'] if re.search(c['label'], l.lower()) and abs(v - c['release']) < 0.01 else v)] for g, l, v in rows]
    st = 'op'; o = {'noncash': 0.0}
    def add(k, v): o[k] = o.get(k, 0.0) + v
    for g, l, v in rows:
        full = (g + ' ' + l).lower(); ll = l.lower()
        if re.search(r'effect of exchange', ll): o['fx'] = v; continue
        if re.search(r'^net (increase|decrease|\(decrease\)|\(increase\))', ll) or 'increase (decrease) in cash' in full: o['net'] = v; continue
        if re.search(r'at beginning of period|at\s+beginning', full):
            add('beg', v); continue
        if re.search(r'at end of period', full): o['end'] = v; continue
        if st == 'op':
            if re.search(r'cash provided by operating', ll): o['cfo'] = v; st = 'inv'
            elif re.fullmatch(r'net income', ll): o['ni'] = v
            elif re.search(r'^depreciation', ll) or ll == 'amortization': o['da'] = v
            elif re.search(r'changes in (operating )?assets|operating assets and liabilities', ll): o['wc'] = v
            elif re.search(r'changes in (operating )?assets and liabilities', g.lower()): add('wc', v)      # 10-K detail lines
            else: add('noncash', v)
        elif st == 'inv':
            if re.search(r'cash (used in|provided by|\(used in\) provided by|provided by \(used in\)) investing', ll): o['cfi'] = v; st = 'fin'
            elif re.search(r'^capital expenditures|^expenditures', ll): o['capex'] = v
            elif re.search(r'acquisition|equity method investment', ll): add('acq', v)
            elif re.search(r'sale of business', ll): add('divest', v)
            else: add('oinv', v)
        elif st == 'fin':
            if re.search(r'cash \(?(used in|provided by)\)?.* financing', ll): o['cff'] = v; st = 'end'
            elif re.search(r'debt|borrowings', full): add('debt', v)
            elif re.search(r'dividends paid', ll): o['div'] = v
            elif re.search(r'treasury stock|purchases? of common stock', ll): add('bb', v)
            elif re.search(r'stock issuances', ll): add('iss', v)
            else: add('ofin', v)
    return o

CFK = ['cf_ni', 'cf_da', 'cf_noncash', 'cf_wc', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_oinv', 'cf_cfi', 'cf_debt', 'cf_div', 'cf_bb', 'cf_iss', 'cf_ofin',
       'cf_cff', 'cf_fx', 'cf_net']
def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_da': c['da'], 'cf_wc': N(c.get('wc')), 'cf_cfo': c['cfo']}
    o['cf_noncash'] = c['cfo'] - c['ni'] - c['da'] - N(c.get('wc'))
    o['cf_capex'] = c['capex']; o['cf_acq'] = N(c.get('acq')); o['cf_cfi'] = c['cfi']
    o['cf_oinv'] = c['cfi'] - c['capex'] - N(c.get('acq'))
    o['cf_debt'] = N(c.get('debt')); o['cf_div'] = N(c.get('div')); o['cf_bb'] = N(c.get('bb')); o['cf_iss'] = N(c.get('iss'))
    o['cf_cff'] = c['cff']; o['cf_ofin'] = c['cff'] - o['cf_debt'] - o['cf_div'] - o['cf_bb'] - o['cf_iss']
    o['cf_fx'] = N(c.get('fx')); o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + N(c.get('fx'))
    return o

# ---------------------------------------------------------------- non-GAAP reconciliations
CATS = [(r'mtm|mark-to-market', 'mtm'), (r'tnt|integration|genco', 'acq'),
        (r'impairment', 'impair'), (r'legal|regulatory|reserve|settlement', 'legal'),
        (r'realignment|optimization|restructuring|severance|buyout|spin-off|separation|fiscal year change|exit', 'restr'),
        (r'tax|tcja|deferred', 'taxitem'), (r'short-term investment|extinguishment|sale of|gain', 'gain')]
OCATS = ['restr', 'acq', 'impair', 'legal', 'mtm', 'other']
def cat(l):
    l = l.lower()
    for pat, k in CATS:
        if re.search(pat, l): return k
    return 'other'

def recon_pick(blocks, oi, eps, ni):
    """the consolidated reconciliation whose GAAP side ties to this period's operating income, net income and diluted EPS."""
    for b in blocks:
        rws = [(l, [v for v in vals if v is not None]) for l, vals in b['rows']]
        ng = [r for r in rws if r[0].lower().startswith('non-gaap')]
        if not ng or len(ng[0][1]) not in (4, 5): continue
        n = len(ng[0][1])
        top_down = rws[0][0].lower().startswith('non-gaap')
        items = [(l, v) for l, v in rws if not re.match(r'(non-)?gaap measure', l.lower()) and len(v) == n]
        if len(items) != len(rws) - 2: continue
        sgn = -1.0 if top_down else 1.0          # top-down tables list charges as negatives (non-GAAP - charges = GAAP)
        its = [(l, [sgn * t for t in v]) for l, v in items]
        adj = ng[0][1]
        g_oi = adj[0] - sum(v[0] for _, v in its); g_ni = adj[-2] - sum(v[-2] for _, v in its); g_eps = adj[-1] - sum(v[-1] for _, v in its)
        if abs(g_oi - oi) <= 2.5 and abs(g_eps - eps) <= (0.085 if ni < 0 else 0.035) and abs(g_ni - ni) <= 2.5:
            return n, adj, its, b['head']
    return None

def do_recon(p, blocks):
    oi, eps, ni = x_(p, 'oi'), x_(p, 'eps_cont'), x_(p, 'ni_cont')
    if oi is None or eps is None: return
    blocks = [b for b in (blocks or []) if b.get('entity', 'corp') == 'corp']
    r = recon_pick(blocks, oi, eps, ni)
    if not r:
        put(p, 'adj_basis', 'none'); return
    n, adj, its, head = r
    tot = {c: 0.0 for c in OCATS}; labs = {c: [] for c in OCATS}; nonop = 0.0; taxeff = 0.0; nlab = []
    for l, v in its:
        o_i, ni_i = v[0], v[-2]
        tax_i = v[2] if n == 5 else (o_i - ni_i)           # 4-column tables (to FY2015): all items operating, tax = pre-tax - after-tax
        c = cat(l)
        if c in ('taxitem', 'gain'): c = 'other'
        if abs(o_i) > 1e-9:
            tot[c] += o_i; labs[c].append(f'{l} {o_i:,.0f}')
        pre = ni_i + tax_i
        if abs(pre - o_i) > 0.51:
            nonop += pre - o_i; nlab.append(f'{l} {pre - o_i:,.0f} pre-tax')
        taxeff += tax_i
        if abs(pre) < 0.51 and abs(tax_i) > 0.51: nlab.append(f'{l} (tax item) {-tax_i:,.0f}')
    for c in OCATS:
        put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(labs[c]))
    put(p, 'oa_nonop', nonop); put(p, 'oa_nonop_lab', '; '.join(nlab)); put(p, 'oa_tax', taxeff); put(p, 'e_tax_in', -taxeff)
    put(p, 'adj_oi_pub', adj[0]); put(p, 'adj_ni_pub', adj[-2]); put(p, 'adj_eps_pub', adj[-1])
    if n == 5: put(p, 'adj_tax_pub', adj[2])
    put(p, 'adj_basis', 'published'); put(p, 'adj_head', head[-70:])

def do_seg_recon(p, blocks):
    for b in blocks or []:
        e = b.get('entity')
        if e in ('usd', 'intl'):
            ng = [v for l, v in b['rows'] if l.lower().startswith('non-gaap')]
            if ng: put(p, f'{e}_adj_oi', [t for t in ng[0] if t is not None][0])

# ---------------------------------------------------------------- drivers
def legacy_period(p, src):
    r = REC.get(src)
    if not r: LOG.append(f'{p}: no record {src}'); return
    do_is(p, r['is'])
    if r.get('exp'): do_express(p, r['exp'])
    if r.get('fec'):
        do_express(p, r['fec'])
        if x_(p, 'adv_gc') is not None: put(p, 'adv_gnd', x_(p, 'adv_gc') + N(x_(p, 'adv_ghd')))
    if r.get('gnd'): do_ground(p, r['gnd'])
    if r.get('frt'): do_freight(p, r['frt'])
    if r.get('bs'): do_bs(p, r['bs'])
    do_recon(p, r.get('recon'))

def legacy_xbrl(p, fy, q):
    V = xbrl.value
    if q is None:
        put(p, 'sbc', V('ShareBasedCompensation', fy, 'FY') or V('AllocatedShareBasedCompensationExpense', fy, 'FY'))
        put(p, 'dps', V('CommonStockDividendsPerShareDeclared', fy, 'FY') or MAN.get('dps_legacy', {}).get(str(fy)))
        put(p, 'sh_b', V('WeightedAverageNumberOfSharesOutstandingBasic', fy, 'FY')); put(p, 'eps_b', V('EarningsPerShareBasic', fy, 'FY'))
    else:
        put(p, 'sbc', V('AllocatedShareBasedCompensationExpense', fy, 'Q', q))
        if q < 4:
            put(p, 'dps', V('CommonStockDividendsPerShareDeclared', fy, 'Q', q))
            put(p, 'sh_b', V('WeightedAverageNumberOfSharesOutstandingBasic', fy, 'Q', q))
        else:
            fyv = V('CommonStockDividendsPerShareDeclared', fy, 'FY'); qs = [x_(f'LQ{i}-{str(fy)[2:]}', 'dps') for i in (1, 2, 3)]
            if fyv is not None and all(v is not None for v in qs): put(p, 'dps', round(fyv - sum(qs), 4))
    lo = {None: f'{fy}-06-01', 1: f'{fy - 1}-09-01', 2: f'{fy - 1}-12-01', 3: f'{fy}-03-01', 4: f'{fy}-06-01'}[q]
    hi = {None: f'{fy}-08-15', 1: f'{fy - 1}-11-15', 2: f'{fy}-02-15', 3: f'{fy}-05-15', 4: f'{fy}-08-15'}[q]
    sh, asof = xbrl.cover_shares(lo, hi)
    put(p, 'bs_shares', sh); put(p, 'bs_shares_asof', asof)

def run():
    load()
    for src in LEG_A:
        p = lkey(src); fy = int(p[1:])
        legacy_period(p, src); legacy_xbrl(p, fy, None)
        r = REC.get(src)
        if r and r.get('cf'):
            c = cf_ytd(r['cf'], src)
            try:
                for k, v in cf_lines(c).items(): put(p, k, v)
                put(p, 'cf_beg', c.get('beg')); put(p, 'cf_end', c.get('end'))
            except KeyError as e: LOG.append(f'{p}: cash flow key {e}')
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            src = f'Q{q}-{str(y)[2:]}'; p = 'L' + src
            legacy_period(p, src); legacy_xbrl(p, y, q)
            r = REC.get(src)
            if not r or not r.get('cf'): prev = None; continue
            c = cf_ytd(r['cf'], src)
            try: lc = cf_lines(c)
            except KeyError as e:
                LOG.append(f'{p}: cash flow key {e}'); prev = None; continue
            if q == 1: d, beg = lc, c.get('beg')
            elif prev is None: continue
            else: d, beg = {k: lc[k] - prev[0][k] for k in lc}, prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', c.get('end'))
            prev = (lc, c.get('end'))
    # calendar basis
    for p in ['CY2024', 'CY2025'] + [f'CQ{q}-{yy}' for yy in ('24', '25', '26') for q in (1, 2, 3, 4)] + ['C9M-25', 'C9M-26']:
        r = REC.get(p)
        if not r: continue
        if r.get('is'): do_is(p, r['is'])
        if r.get('usd'): do_usd(p, r['usd'])
        if r.get('intl'): do_intl(p, r['intl'])
        if r.get('bs'): do_bs(p, r['bs'])
        if r.get('capex'): put(p, 'capex_is', find(r['capex'], r'^total', None))
        if r.get('is'):
            do_recon(p, r.get('recon')); do_seg_recon(p, r.get('recon'))
            if x_(p, 'sh_d') is None and x_(p, 'eps_d'):
                put(p, 'sh_d', round(x_(p, 'ni') / x_(p, 'eps_d'), 1)); put(p, 'sh_d_derived', 1)
        if r.get('cf'):
            c = cf_ytd(r['cf'])
            for k, v in cf_lines(c).items(): put(p, k, v)
            put(p, 'cf_beg', c.get('beg')); put(p, 'cf_end', c.get('end'))
    for p in list(DATA):
        if p.startswith('C') and 'x' in DATA[p]:
            put(p, 'corp_rev', x_(p, 'sr_oth')); put(p, 'corp_oi', x_(p, 'so_oth'))
            if x_(p, 'adj_oi_pub') is not None and x_(p, 'usd_adj_oi') is not None:
                put(p, 'corp_adj_oi', x_(p, 'adj_oi_pub') - x_(p, 'usd_adj_oi') - x_(p, 'intl_adj_oi'))
    # nine-month cash flow (the only calendar-basis cash flow published) is carried in the third-quarter columns, flagged
    for src, dst in (('C9M-25', 'CQ3-25'), ('C9M-26', 'CQ3-26')):
        for k, v in DATA.get(src, {}).get('x', {}).items():
            if k.startswith('cf_'): put(dst, k, v)
        put(dst, 'cf_is_9m', 1)
        put(dst, 'capex_9m', x_(src, 'capex_is'))
    # calendar Q3/26: XBRL extras (10-Q for the quarter ended 30-Sep-2026)
    put('CQ3-26', 'sbc', xbrl.span('AllocatedShareBasedCompensationExpense', '2026-07-01', '2026-09-30'))
    put('CQ3-26', 'dps', xbrl.span('CommonStockDividendsPerShareDeclared', '2026-07-01', '2026-09-30'))
    put('CQ3-26', 'sh_b', xbrl.span('WeightedAverageNumberOfSharesOutstandingBasic', '2026-07-01', '2026-09-30'))
    sh, asof = xbrl.cover_shares('2026-09-01', '2026-11-15'); put('CQ3-26', 'bs_shares', sh); put('CQ3-26', 'bs_shares_asof', asof)
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: (round(x[k], 2) if isinstance(x.get(k), float) else x.get(k)) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'adj_oi_pub', 'adj_eps_pub', 'cf_cfo', 'bs_ta', 'adv_gnd', 'lf_ship', 'dps')})
    print('\n'.join(LOG))
