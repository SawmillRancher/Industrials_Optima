"""Flatten data/<period>.json into model keys per model column ('2021', '2022', 'Q1-23' ... 'Q2-26', '2023' ... '2025').

Basis policy (documented in the README and header row 4):
* FY2021: P&L as first reported (AR2021; no restated 2021 P&L exists); balance sheet = restated 1-Jan-2022 column of AR2023.
* FY2022: restated comparatives in AR2023 (correction of errors, note 37); the original AR2022 print is kept for comments.
* 2023 quarters: comparatives in the 2024 Q1 / H1 / 9M documents (Theon listed in Feb-2024); FY2023 from AR2023.
* 2024 onwards: each period as first reported in its own document. The share of profit of equity-accounted investees is
  shown as its own line inside operating profit in every period (current presentation, adopted Q2-25 with 2024 restated);
  where a document presented it below operating profit, operating profit is rebuilt as printed operating profit + that line.
* Discrete quarters: Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M (income statement, reconciliation, revenue splits, cash flow,
  KPIs). Published adjusted EBIT / EBITDA are differenced only on a consistent definition (Q2-25 uses the restated Q1-25).
Values: EUR m; expenses as positive amounts (cost of sales, opex, finance costs, tax); cash flows as signed in the statement.
"""
import json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(HERE, 'manual_items.json')))
RAW = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, 'data', '*.json'))}

YRS = ['2021', '2022', '2023', '2024', '2025']
QS = [f'Q{q}-{y}' for y in ('23', '24', '25', '26') for q in (1, 2, 3, 4)]
QS = [q for q in QS if q not in ('Q3-26', 'Q4-26')]

def n(x): return 0.0 if x is None else x

def section(per, s):
    """statement section for a YTD/annual period on the chosen basis"""
    r = RAW.get(per, {})
    if per == '2022':
        return dict((r.get('cmp') or {}).get('AR23', {}).get(s) or {})
    if per == '2021' and s == 'bs':
        return dict((r.get('cmp') or {}).get('AR23', {}).get('bs') or {})
    if per in ('Q1-23', 'H1-23', '9M-23'):
        doc = {'Q1-23': 'Q1-24', 'H1-23': 'H1-24', '9M-23': '9M-24'}[per]
        return dict((r.get('cmp') or {}).get(doc, {}).get(s) or {})
    return dict(r.get(s) or {})

def flow_is(per):
    i = section(per, 'is')
    if not i: return {}
    assoc = n(i.get('assoc'))
    op = i.get('op')
    if op is not None and i.get('assoc_pos') == 'below_op': op = op + assoc
    out = dict(rev=i.get('rev'), cogs=-n(i.get('cogs')), gp=i.get('gp'), oinc=n(i.get('oinc')) + n(i.get('ogain')),
               admin=-n(i.get('admin')), sell=-n(i.get('sell')), rnd=-n(i.get('rnd')), oexp=-n(i.get('imp')) - n(i.get('oexp')),
               assoc=assoc, op=op, finc=n(i.get('finc')), fcost=-n(i.get('fcost')), ebt=i.get('ebt'),
               tax=-(n(i.get('taxc')) + n(i.get('taxd'))), ni=i.get('ni'), assoc_below=1.0 if i.get('assoc_pos') == 'below_op' else 0.0)
    return out

def flow_ng(per):
    g = section(per, 'ng')
    if not g: return {}
    i = section(per, 'is')
    out = {'adj_ebit_pub': g.get('adj_ebit'), 'adj_ebitda_pub': g.get('adj_ebitda'), 'nri': n(g.get('nri')),
           'adj_def': 0.0 if i.get('assoc_pos') == 'below_op' else 1.0}
    if g.get('adj_ebit') is not None and g.get('adj_ebitda') is not None:
        out['dna'] = g['adj_ebitda'] - g['adj_ebit']
    return out

def flow_rev(per):
    r = section(per, 'rev')
    i = section(per, 'is')
    if not r or not r.get('product') or i.get('rev') is None: return {}
    p, g = r['product'], r.get('region', {})
    out = {'pr_night': p.get('night'), 'pr_thermal': p.get('thermal')}
    out['pr_other'] = i['rev'] - n(p.get('night')) - n(p.get('thermal'))
    if g:
        out.update(rg_eu=g.get('europe'), rg_asia=g.get('asia'), rg_am=g.get('americas'))
        out['rg_row'] = i['rev'] - n(g.get('europe')) - n(g.get('asia')) - n(g.get('americas'))
    return out

def flow_cf(per):
    c = section(per, 'cf')
    if not c or c.get('cfo') is None: return {}
    nonc = c.get('noncash', c.get('noncash_derived'))
    out = dict(cf_ni=c.get('start'), cf_nonc=nonc, cf_wc=n(c.get('wc')), cf_tax=n(c.get('taxp')), cf_int=n(c.get('intp')), cf_cfo=c.get('cfo'),
               cf_capex=n(c.get('capex')), cf_acq=n(c.get('acq')), cf_cfi=c.get('cfi'),
               cf_debt=n(c.get('debt_pro')) + n(c.get('debt_rep')), cf_lease=n(c.get('lease_cf')), cf_eq=n(c.get('eq_iss')),
               cf_bb=n(c.get('buyback')), cf_div=n(c.get('div')), cf_cff=c.get('cff'),
               cf_fx=n(c.get('fx')), cf_beg=c.get('beg'), cf_end=c.get('end'))
    out['cf_oinv'] = out['cf_cfi'] - out['cf_capex'] - out['cf_acq']
    out['cf_ofin'] = out['cf_cff'] - out['cf_debt'] - out['cf_lease'] - out['cf_eq'] - out['cf_bb'] - out['cf_div']
    out['cf_net'] = out['cf_cfo'] + out['cf_cfi'] + out['cf_cff']
    return out

def bal(per):
    b = section(per, 'bs')
    if not b or b.get('ta') is None: return {}
    g = lambda k: n(b.get(k))
    eqp = b.get('eqp'); nci = g('nci_bs')
    te = b.get('te') if b.get('te') is not None else (eqp + nci if eqp is not None else None)
    tl = b.get('tl') if b.get('tl') is not None else g('tncl') + g('tcl')
    x = dict(bs_cash=g('cash'), bs_td=g('td'), bs_ar=g('ar'), bs_inv=g('inv'), bs_tca=b.get('tca'),
             bs_ppe=g('ppe') + g('invprop'), bs_rou=g('rou'), bs_intang=g('intang'), bs_fin=g('assoc_bs') + g('ofa') + g('ltloan') + g('ofa_c'),
             bs_ta=b.get('ta'), bs_debt_c=g('debt_c'), bs_lease_c=g('lease_c'), bs_bbl=g('bbl') + g('bbl_c'), bs_ap=g('ap'), bs_tcl=b.get('tcl'),
             bs_debt_nc=g('debt'), bs_lease_nc=g('lease'), bs_tl=tl, bs_eqp=eqp, bs_nci=nci, bs_teq=te, bs_tle=b.get('tle'),
             bs_assoc=g('assoc_bs'), bs_fvtpl=g('ofa') + g('ofa_c'))
    x['bs_oca'] = x['bs_tca'] - x['bs_cash'] - x['bs_td'] - x['bs_ar'] - x['bs_inv'] - g('ofa_c')
    x['bs_onca'] = x['bs_ta'] - x['bs_tca'] - x['bs_ppe'] - x['bs_rou'] - x['bs_intang'] - (x['bs_fin'] - g('ofa_c'))
    x['bs_ocl'] = x['bs_tcl'] - x['bs_ap'] - x['bs_debt_c'] - x['bs_lease_c'] - g('bbl_c')
    x['bs_oncl'] = x['bs_tl'] - x['bs_tcl'] - x['bs_debt_nc'] - x['bs_lease_nc'] - g('bbl')
    return x

def ytd_keys(q, yy):
    return {1: f'Q1-{yy}', 2: f'H1-{yy}', 3: f'9M-{yy}', 4: f'20{yy}'}[q]

def diff(cur, prv, skip=()):
    if not cur or not prv: return {}
    out = {}
    for k in set(cur) | set(prv):
        if k in skip: continue
        a, b = cur.get(k), prv.get(k)
        if a is None or b is None: continue
        out[k] = a - b
    return out

def disc(per, fn, skip=()):
    q, yy = int(per[1]), per[-2:]
    cur = fn(ytd_keys(q, yy))
    if q == 1: return cur
    return diff(cur, fn(ytd_keys(q - 1, yy)), skip)

def kpi(per):
    K = MAN['kpi_ytd']
    def ytd(p): return (K.get(p) or {})
    if per in YRS:
        return {k: v for k, v in ytd(per).items() if k in ('order_intake', 'soft_backlog', 'options')}
    q, yy = int(per[1]), per[-2:]
    cur = ytd(ytd_keys(q, yy)); out = {}
    if 'soft_backlog' in cur: out['soft_backlog'] = cur['soft_backlog']
    if 'options' in cur: out['options'] = cur['options']
    if 'order_intake' in cur:
        if q == 1: out['order_intake'] = cur['order_intake']
        else:
            prv = ytd(ytd_keys(q - 1, yy))
            if 'order_intake' in prv: out['order_intake'] = cur['order_intake'] - prv['order_intake']
    return out

def run():
    X = {}
    for per in YRS + QS:
        x = {}
        if per in YRS:
            x.update(flow_is(per)); x.update(flow_ng(per)); x.update(flow_rev(per)); x.update(flow_cf(per))
            sh = MAN['shares'].get(per)
            if sh: x['sh_w'] = sh
            nci = MAN['nci_profit'].get(per)
            x['nci'] = nci if nci is not None else (0.0 if per in ('2021', '2022', '2023') else None)
            fv = MAN['fv_gains'].get(per)
            if fv is not None: x['fv_gain'] = fv
            r = RAW.get('2021' if per == '2021' else per, {})
            ip = (r.get('is') or {}) if per not in ('2022',) else ((r.get('cmp') or {}).get('AR23', {}).get('is') or {})
            if ip.get('eps_b') is not None: x['eps_pub'] = ip['eps_b']
        else:
            x.update(disc(per, flow_is, skip=('assoc_below',)))
            if x: x['assoc_below'] = flow_is(ytd_keys(int(per[1]), per[-2:])).get('assoc_below', 0.0)
            # reconciliation: difference only on a consistent definition
            def ng_basis(p):
                g = flow_ng(p)
                if p == 'Q1-25' and per == 'Q2-25':
                    rs = MAN['adj_restated']['Q1-25']
                    g = dict(g, adj_ebit_pub=rs['adj_ebit'], adj_ebitda_pub=rs['adj_ebitda'], adj_def=1.0)
                return g
            q, yy = int(per[1]), per[-2:]
            cur = flow_ng(ytd_keys(q, yy))
            if q == 1: g = cur
            else:
                prv = ng_basis(ytd_keys(q - 1, yy))
                g = diff(cur, prv, skip=('adj_def',)) if cur and prv and cur.get('adj_def') == prv.get('adj_def') else {}
                if g: g['adj_def'] = cur['adj_def']
                if g and 'adj_ebit_pub' in g and 'adj_ebitda_pub' in g: g['dna'] = g['adj_ebitda_pub'] - g['adj_ebit_pub']
            x.update(g)
            x.update(disc(per, flow_rev))
            cf = disc(per, flow_cf, skip=('cf_beg', 'cf_end'))
            if cf:
                cur_cf = flow_cf(ytd_keys(q, yy))
                cf['cf_end'] = cur_cf.get('cf_end')
                cf['cf_beg'] = cur_cf.get('cf_beg') if q == 1 else flow_cf(ytd_keys(q - 1, yy)).get('cf_end')
                x.update(cf)
            if per in MAN['eps_q1_release']: x['eps_q1'] = MAN['eps_q1_release'][per]
        # balance sheet at the period end
        bkey = per if per in YRS else ytd_keys(int(per[1]), per[-2:])
        x.update(bal(bkey))
        x.update(kpi(per))
        X[per] = {'x': {k: v for k, v in x.items() if v is not None}}
    return X

DATA = None
def get():
    global DATA
    if DATA is None: DATA = run()
    return DATA

if __name__ == '__main__':
    D = run()
    keys = ('rev', 'op', 'adj_ebit_pub', 'adj_def', 'dna', 'ni', 'cf_cfo', 'cf_end', 'bs_cash', 'bs_ta', 'pr_night', 'order_intake', 'soft_backlog')
    for p in YRS + QS:
        x = D.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 2) for k in keys if k in x})
