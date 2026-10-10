"""Flatten data/<period>.json into model keys per model column period ('2019', '2020', 'Q1-21' ... 'Q2-26', '2021' ... '2025').

* Income statement / balance sheet / reconciliations: as originally reported (comparatives only where no original exists).
* Cash flow: discrete quarters from the year-to-date statements (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
* Sales splits: Q4 = FY - 9M where the release does not print the fourth quarter (2021-23).
* Shares: Class A-equivalent = Class A + Class B / 10 (Class B voting shares carry 1/10 of the Class A nominal value and
  economic rights); Class A EPS = net income / Class A-equivalent shares.
* Adjusted net income = Class A + Class B as published.
Expenses are returned as positive amounts (cost of sales, SG&A, financial expenses, income tax expense).
"""
import json, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(HERE, 'manual_items.json')))
RAW = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, 'data', '*.json'))}

def sec(per, s):
    r = RAW.get(per, {})
    out = dict((r.get('cmp') or {}).get(s) or {})
    out.update(r.get(s) or {})
    return out

def orig(per, s): return dict((RAW.get(per) or {}).get(s) or {})

QS = [f'Q{q}-{y:02d}' for y in range(21, 27) for q in (1, 2, 3, 4)]
QS = [q for q in QS if q not in ('Q3-26', 'Q4-26')]
YRS = [str(y) for y in range(2019, 2026)]

def yy(per): return per[-2:]
def fy_of(per): return '20' + per[-2:]
def n(x): return 0.0 if x is None else x

def cf_disc(per):
    """discrete-quarter or annual cash flow dict"""
    if not per.startswith('Q'):
        return sec(per, 'cf')
    q = int(per[1]); y = yy(per)
    ytd = {1: f'Q1-{y}', 2: f'H1-{y}', 3: f'9M-{y}', 4: fy_of(per)}
    cur = sec(ytd[q], 'cf')
    if q == 1: return cur
    prv = sec(ytd[q - 1], 'cf')
    if not cur or not prv: return {}
    out = {}
    for k in set(cur) | set(prv):
        if k in ('beg', 'end'): continue
        out[k] = n(cur.get(k)) - n(prv.get(k))
    out['end'] = cur.get('end'); out['beg'] = prv.get('end')
    return out

def split_disc(per, s):
    """sales split for a quarter (Q4 derived as FY - 9M when not printed)"""
    d = sec(per, s)
    if per.startswith('Q4'):
        o = orig(per, s)
        fy = sec(fy_of(per), s); nine = sec(f'9M-{yy(per)}', s)
        for k, v in fy.items():
            if k.endswith('_g') or k.endswith('_ccg'): continue
            if k not in o and k in nine: d[k] = v - nine[k]
    return d

def run():
    X = {}
    for per in YRS + QS:
        i = sec(per, 'is'); ng = sec(per, 'ng'); a = sec(per, 'ani_A'); b = sec(per, 'ani_B')
        bs = orig(per, 'bs') or ((RAW.get(per) or {}).get('cmp') or {}).get('bs') or {}   # whole statement: original, else comparative
        x = {}
        if not i and per not in YRS: continue
        if i:
            x.update(rev=i.get('rev'), cogs=-n(i.get('cogs')), gp=i.get('gp'), sga=-n(i.get('sga')), op=i.get('op'),
                     fin_inc=i.get('fin_inc'), fin_exp=-n(i.get('fin_exp')), fx=i.get('fx'), ebt=i.get('ebt'), tax=-n(i.get('tax')),
                     ni=i.get('ni'), eps_a=i.get('eps_a'), eps_dil_a=i.get('eps_dil_a'))
        if ng:
            x.update(dna=ng.get('dna'), sbc=ng.get('sbc'), etc=n(ng.get('etc')), adj_pub=ng.get('adj_ebitda'))
        if a:
            x['adj_ni_pub'] = n(a.get('adj_ni')) + n(b.get('adj_ni'))
            x['ani_sbc'] = n(a.get('sbc')) + n(b.get('sbc'))
            x['ani_etc'] = n(a.get('etc')) + n(b.get('etc'))
            x['ani_tax'] = n(a.get('tax_eff')) + n(b.get('tax_eff'))
            x['ani_ni'] = n(a.get('ni')) + n(b.get('ni'))
            x['sh_basic'] = (n(a.get('wsh')) + n(b.get('wsh')) / 10) / 1e6
            x['sh_dil'] = (n(a.get('wsh_dil')) + n(b.get('wsh_dil')) / 10) / 1e6
            x['adj_eps_pub'] = a.get('adj_eps_dil'); x['adj_eps_basic_pub'] = a.get('adj_eps')
            x['sh_a'] = n(a.get('wsh')) / 1e6; x['sh_b'] = n(b.get('wsh')) / 1e6
        # sales splits
        ch = split_disc(per, 'ch') if per.startswith('Q') else sec(per, 'ch')
        rg = split_disc(per, 'rg') if per.startswith('Q') else sec(per, 'rg')
        pr = split_disc(per, 'pr') if per.startswith('Q') else sec(per, 'pr')
        rev = x.get('rev')
        if ch.get('whs') is not None and rev is not None:
            x['ch_whs'] = ch['whs']; x['ch_dtc'] = rev - ch['whs']
            for k in ('whs', 'dtc', 'total'):
                if f'{k}_ccg' in ch: x[f'ccg_{k}'] = ch[f'{k}_ccg']
        for k in ('emea', 'am', 'apac'):
            if rg.get(k) is not None: x[f'rg_{k}'] = rg[k]
            if f'{k}_ccg' in rg: x[f'ccg_{k}'] = rg[f'{k}_ccg']
        if 'total_ccg' in rg and 'ccg_total' not in x: x['ccg_total'] = rg['total_ccg']
        for k in ('eu', 'na', 'apac_o'):
            if rg.get(k) is not None: x[f'ro_{k}'] = rg[k]
        if rg.get('eu') is not None and rev is not None:
            x['ro_row'] = rev - rg['eu'] - rg['na'] - rg['apac_o']
        for k in ('shoes', 'apparel', 'acc'):
            if pr.get(k) is not None: x[f'pr_{k}'] = pr[k]
            if f'{k}_ccg' in pr: x[f'ccg_{k}'] = pr[f'{k}_ccg']
        # balance sheet
        if bs and bs.get('ar') is not None:
            g = lambda k: n(bs.get(k))
            x.update(bs_cash=bs.get('cash'), bs_ar=bs.get('ar'), bs_inv=bs.get('inv'), bs_oca=g('ocfa') + g('ocoa'),
                     bs_ppe=bs.get('ppe'), bs_fa=g('ppe') + g('intang'), bs_rou=bs.get('rou'), bs_int=bs.get('intang'), bs_dta=bs.get('dta'),
                     bs_ap=bs.get('ap'), bs_cfl=g('cll') + g('ocfl'), bs_ocl=g('ocol') + g('cprov') + g('itl'),
                     bs_ncfl=g('ncll') + g('oncfl'), bs_oncl=g('ebo') + g('ncprov') + g('dtl'),
                     bs_cap=g('sh_cap') + g('cap_res') + g('treas'), bs_ores=bs.get('oth_res'), bs_re=bs.get('re'),
                     bs_ta=bs.get('ta'), bs_teq=bs.get('teq'), bs_tle=bs.get('tle'), bs_tca=bs.get('tca'), bs_tcl=bs.get('tcl'))
        elif bs and per in YRS:
            x.update(bs_cash_memo=bs.get('cash'), bs_ta_memo=bs.get('ta'), bs_teq_memo=bs.get('teq'))
        # cash flow (discrete)
        cf = cf_disc(per)
        if cf and cf.get('cfo') is not None:
            g = lambda k: n(cf.get(k))
            x.update(cf_ni=cf.get('ni'), cf_dna=cf.get('dna'), cf_sbc=cf.get('sbc'),
                     cf_wc=g('d_ar') + g('d_inv') + g('d_ap') + g('d_oth'), cf_taxp=g('tax_paid') + g('int_rec'),
                     cf_cfo=cf.get('cfo'), cf_capex=g('capex_ppe') + g('capex_int'), cf_cfi=cf.get('cfi'),
                     cf_lease=g('lease_pay'), cf_eq=g('sh_iss') + g('etc_cf') + g('treas_sale'), cf_intp=g('int_paid'),
                     cf_cff=cf.get('cff'), cf_fx=g('fx_cash'), cf_beg=cf.get('beg'), cf_end=cf.get('end'))
            x['cf_oth'] = x['cf_cfo'] - n(x['cf_ni']) - n(x['cf_dna']) - n(x['cf_sbc']) - x['cf_wc'] - x['cf_taxp']
            x['cf_oinv'] = x['cf_cfi'] - x['cf_capex']
            x['cf_ofin'] = x['cf_cff'] - x['cf_lease'] - x['cf_eq'] - x['cf_intp']
            x['cf_net'] = x['cf_cfo'] + x['cf_cfi'] + x['cf_cff']
        X[per] = {'x': {k: v for k, v in x.items() if v is not None}}
    for per, ov in MAN.get('overrides', {}).items():
        for k, v in ov.items():
            if not k.startswith('_'): X[per]['x'][k] = v
    for per, v in MAN.get('overdraft', {}).items():
        if not per.startswith('_'): X[per]['x']['overdraft'] = v
    return X

DATA = None
def get():
    global DATA
    if DATA is None: DATA = run()
    return DATA

if __name__ == '__main__':
    D = run()
    for p in YRS + QS:
        x = D.get(p, {}).get('x', {})
        print(p, {k: round(v, 2) for k, v in x.items() if k in ('rev', 'op', 'ni', 'adj_pub', 'adj_ni_pub', 'sh_dil', 'cf_cfo', 'bs_cash', 'ch_whs', 'rg_am', 'pr_shoes', 'ro_eu')})
