"""Harmonise the extracted JSON (data/<period>.json) into flat model keys (DATA[period]['x'][key]).

- Income statement: FY2012-2021 from the prospectus bridge (net sales / operating income / interest / tax / net income only);
  non-operating items other than interest (loss on extinguishment, FX & insurance gains, 2024 refinancing costs) in 'refi'.
- Cash flow: releases give year-to-date statements; discrete quarters derived (Q4 = FY - 9M). 2022 quarters: the
  prospectus "Other data" (CFO / CFI / CFF / capex / acquisitions / D&A) only.
- Derived 'other' lines so each statement section sums to its published subtotal.
- End markets: Q1-23 = H1-23 - Q2-23 (Q1-23 never published on its own).
- Adjusted EPS (current definition, adds back amortization of acquired intangibles): the tax adjustment is the published
  current-definition figure where published (Q1-25, Q2-25 restated; Q1-26, Q2-26); otherwise the published prior-definition
  tax adjustment plus tax on the amortization add-back at AMORT_TAX (manual_items.json).
- Balance sheet: Q4 columns carry the year-end balance sheet.
"""
import json, glob, os
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = {}
LOG = []

def N(x): return x or 0.0
def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        DATA[os.path.basename(f)[:-5]] = json.load(open(f))
    return DATA

MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def g(p, s, k=None):
    d = DATA.get(p, {}).get(s)
    if d is None: return None
    return d if k is None else d.get(k)

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(y) for y in range(2012, 2026)]
    for y in range(2022, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q > 2)]
    return out

# ---------------------------------------------------------------- income statement & EBITDA bridge
def do_is(p):
    i = g(p, 'is') or {}
    ng = g(p, 'ng') or {}
    if not i: return
    put(p, 'rev', i.get('net_sales')); put(p, 'cogs', i.get('cogs')); put(p, 'sga', i.get('sga')); put(p, 'trans', i.get('trans', ng.get('trans')))
    put(p, 'othinc', i.get('other_inc')); put(p, 'op', i.get('op_income')); put(p, 'int', i.get('interest'))
    if p.isdigit() and int(p) <= 2021:
        refi = N(ng.get('loss_ext')) + N(ng.get('fx_gain')) + N(ng.get('ins_gain'))   # as presented (gains negative)
        put(p, 'refi', refi)
        put(p, 'ebt', i['op_income'] - i['interest'] - refi)
    else:
        put(p, 'refi', i.get('refi', 0.0))
        put(p, 'ebt', i.get('ebt'))
    put(p, 'tax', i.get('tax')); put(p, 'ni', i.get('ni'))
    for k_src, k in (('dep', 'dep'), ('amort', 'amort'), ('ebitda', 'ebitda_pub'), ('inv_stepup', 'stepup'), ('other_adj', 'othadj'),
                     ('trans', 'trans_adj'), ('sbc', 'sbc'), ('integ', 'integ'), ('covid', 'covid'), ('msa', 'msa'), ('adj_ebitda', 'adj_pub')):
        put(p, k, ng.get(k_src))

def do_eps(p):
    old, new, i = g(p, 'eps_old') or {}, g(p, 'eps_new') or {}, g(p, 'is') or {}
    src = new or old
    if not src: return
    put(p, 'sh_basic', src.get('sh_basic')); put(p, 'sh_dil', src.get('sh_dil'))
    put(p, 'eps_basic', i.get('eps_basic', src.get('eps_basic'))); put(p, 'eps_dil', i.get('eps_dil', src.get('eps_dil_pub')))
    amort = g(p, 'ng', 'amort')
    put(p, 'e_refi', src.get('refi', 0.0)); put(p, 'e_gross', src.get('gross_adj'))
    if old:
        put(p, 'e_tax_old', old.get('tax_adj')); put(p, 'e_pub_old', old.get('adj_eps')); put(p, 'e_adjni_old', old.get('adj_ni'))
    if new:
        put(p, 'e_tax', new.get('tax_adj')); put(p, 'e_pub', new.get('adj_eps'))
        if old and amort:
            put(p, 'e_amort_rate', -(new['tax_adj'] - old['tax_adj']) / amort)
    elif old and amort is not None:
        r = MAN['amort_tax_rate'][p[-2:]]
        put(p, 'e_amort_rate_in', r)
        put(p, 'e_tax', old['tax_adj'] - amort * r)
    put(p, 'e_def', 'new' if new else 'old')

# ---------------------------------------------------------------- end markets / organic
EMK = ['com_oem', 'com_am', 'bj_oem', 'bj_am', 'def_oem', 'def_am', 'oth_oem', 'oth_am']
def do_em(p):
    em = g(p, 'em')
    if not em and p == 'Q1-23':
        h, q2 = g('H1-23', 'em'), g('Q2-23', 'em')
        em = {k: round(h[k] - q2[k], 4) for k in EMK}
        LOG.append('Q1-23 end markets = H1-23 - Q2-23')
    if not em: return
    for k in EMK: put(p, 'em_' + k, em.get(k))
    if em.get('oth_label'): put(p, 'em_oth_label', em['oth_label'])

def do_org(p):
    o = g(p, 'org')
    if not o: return
    put(p, 'org_sales', o['organic_sales']); put(p, 'org_g', o['growth'])
    put(p, 'acq_sales', round(g(p, 'is', 'net_sales') - o['organic_sales'], 3))

# ---------------------------------------------------------------- cash flow
CFK = ['ni', 'dep', 'amort', 'dcost', 'stepup', 'sbc', 'deferred_tax', 'lease', 'contingent', 'refi', 'otherinc', 'cfo', 'capex',
       'acquisitions', 'proceeds_fa', 'ppa_adj', 'cfi', 'equity', 'options', 'debt_in', 'debt_out', 'finlease', 'fincost', 'defpurch',
       'cff', 'fx', 'net_change']
def cf_ytd(p):
    cf = g(p, 'cf')
    if not cf: return None
    return {k: N(cf.get(k)) for k in CFK} | {'cash_begin': cf.get('cash_begin'), 'cash_end': cf.get('cash_end'), 'ytd': cf.get('ytd_months')}

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dep'] + c['amort'], 'cf_sbc': c['sbc'], 'cf_def': c['deferred_tax'], 'cf_cfo': c['cfo'],
         'cf_capex': c['capex'], 'cf_acq': c['acquisitions'], 'cf_cfi': c['cfi'], 'cf_eq': c['equity'] + c['options'],
         'cf_dbin': c['debt_in'], 'cf_dbout': c['debt_out'], 'cf_cff': c['cff'], 'cf_fx': c['fx']}
    o['cf_oth'] = c['dcost'] + c['stepup'] + c['lease'] + c['contingent'] + c['refi'] + c['otherinc']
    o['cf_wc'] = c['cfo'] - o['cf_ni'] - o['cf_dda'] - o['cf_sbc'] - o['cf_def'] - o['cf_oth']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acquisitions']
    o['cf_ofin'] = c['cff'] - o['cf_eq'] - c['debt_in'] - c['debt_out']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in range(2022, 2026):
        a = cf_ytd(str(y))
        if a:
            for k, v in cf_lines(a).items(): put(str(y), k, v)
            put(str(y), 'cf_beg', a['cash_begin']); put(str(y), 'cf_end', a['cash_end'])
    for y in range(2023, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            p = qk(y, q)
            cur = cf_ytd(str(y)) if q == 4 else cf_ytd(p)
            if cur is None: prev = None; continue
            lc = cf_lines(cur)
            if q == 1:
                d = lc; beg = cur['cash_begin']
            else:
                if prev is None: LOG.append(f'{p}: no prior YTD'); continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['cash_end'])
            prev = (lc, cur['cash_end'])
    for q in (1, 2, 3, 4):
        p = qk(2022, q); c = g(p, 'cfd')
        if not c: continue
        put(p, 'cf_cfo', c['cfo']); put(p, 'cf_cfi', c['cfi']); put(p, 'cf_cff', c['cff']); put(p, 'cf_capex', c['capex'])
        put(p, 'cf_acq', c['acquisitions']); put(p, 'cf_dda', c['dep'] + c['amort'])
        put(p, 'cf_oinv', c['cfi'] - c['capex'] - c['acquisitions'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p, src=None):
    b = g(src or p, 'bs')
    if not b: return
    ta = b['ta']; teq = b.get('teq') if b.get('teq') else (b.get('member') or 0.0)
    if not teq: teq = N(b.get('common')) + N(b.get('apic')) + N(b.get('re')) + N(b.get('aoci'))
    put(p, 'bs_cash', b['cash']); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', b['inv']); put(p, 'bs_oca', N(b.get('oca1')) + N(b.get('taxrec')))
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', ta - b['tca'] - b['ppe'] - b['gw'] - b['intang']); put(p, 'bs_ta', ta)
    put(p, 'bs_ap', b['ap']); put(p, 'bs_cdebt', b.get('cdebt', 0.0))
    put(p, 'bs_ocl', b['tcl'] - b['ap'] - N(b.get('cdebt')))
    put(p, 'bs_ltd', b['ltd']); put(p, 'bs_dtl', b['dtl'])
    tl = ta - teq
    put(p, 'bs_oncl', tl - b['tcl'] - b['ltd'] - b['dtl'])
    if b.get('member') and not b.get('apic'):
        put(p, 'bs_cap', b['member']); put(p, 'bs_re', 0.0); put(p, 'bs_aoci', 0.0)
    else:
        put(p, 'bs_cap', N(b.get('common')) + N(b.get('apic'))); put(p, 'bs_re', N(b.get('re'))); put(p, 'bs_aoci', N(b.get('aoci')))
    put(p, 'bs_teq', teq); put(p, 'bs_tle', b['tle'])
    put(p, 'bs_fl', N(b.get('cfl')) + N(b.get('fl')))
    put(p, 'bs_contingent', None)
    if b.get('shares_out'): put(p, 'bs_shares', b['shares_out'])

def run():
    load()
    for p in periods():
        do_is(p); do_eps(p); do_em(p); do_org(p)
    do_cf()
    for p in periods():
        if p.startswith('Q4-'): do_bs(p, '20' + p[-2:])
        else: do_bs(p)
    for p in ('Q4-24', 'Q4-25'):            # Q4 shares outstanding = year end
        if g('20' + p[-2:], 'bs', 'shares_out'): put(p, 'bs_shares', g('20' + p[-2:], 'bs', 'shares_out'))
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, len(x), {k: x[k] for k in ('rev', 'op', 'ni', 'adj_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'e_tax', 'e_pub', 'e_pub_old') if k in x})
    print('\n'.join(LOG))
