"""Harmonise the extracted Alphabet / Google data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy (documented in README.md and the workbook header):
  * Consolidated statements: AS ORIGINALLY REPORTED in each period's own 10-K / 10-Q (FY2006-08 from the 10-K text; XBRL from
    FY2009). Quarters Q1-Q3 = 10-Q three-month facts; Q4 = fiscal year (10-K) - nine months (Q3 10-Q), stated in the notes.
  * Revenue by type and segment revenue / operating income: from the LATEST filing that presents the period on the current
    taxonomy (revenue types: Search & other, YouTube ads, Network, Subscriptions/platforms/devices, Cloud - annual from FY2017,
    quarterly from Q1-19; segments Google Services / Google Cloud / Other Bets / Alphabet-level - annual from FY2018, quarterly
    from Q1-20). Q4 = FY - (Q1 + Q2 + Q3). Earlier structures as first reported are legacy memo keys (Google websites /
    Network members / other / Motorola, 2006-2017; Google segment / Other Bets 2015-2020; Google / Motorola Mobile 2012-2013).
  * Per-share data and share counts are split-adjusted by the filing date of the source document: x40 before 3-Apr-2014 (2-for-1
    Class C dividend x 20-for-1), x20 before 15-Jul-2022 (20-for-1). EPS / DPS divided, shares multiplied.
  * Cash flow: year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M). Cash includes
    restricted cash from 2018 (ASU 2016-18), so BS cash differs from cash-flow cash by restricted cash (memo).
"""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def periods():
    out = [str(y) for y in range(2006, 2026)]
    for y in range(2013, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q > 2)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def X(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def split_factor(filed):
    f = 1
    if filed < '2014-04-03': f *= 2
    if filed < '2022-07-15': f *= 20
    return f

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# ---------------------------------------------------------------- income statement
IS_KEYS = ['rev', 'cor', 'rd', 'sm', 'ga', 'opex_tot', 'oi', 'oie', 'ebt', 'tax', 'ni', 'pref_div', 'sbc_is', 'int_inc', 'int_exp', 'eq_gain', 'amort_int', 'dps']

def is_raw(p):
    """raw (unsplit) income-statement dict for an annual or Q1-Q3 period; None if not available."""
    r = REC.get(p)
    if not r: return None
    if 'pre09' in r:
        a = r['pre09']
        return {'rev': a['rev'], 'cor': a['cor'], 'rd': a['rd'], 'sm': a['sm'], 'ga': a['ga'], 'opex_tot': a['opex_tot'], 'oi': a['oi'], 'oie': a['oie'],
                'ebt': a['ebt'], 'tax': a['tax'], 'ni': a['ni'], 'eps_b': a['eps_b'], 'eps_d': a['eps_d'], 'sh_b': a['sh_b'], 'sh_d': a['sh_d'],
                'sbc_is': a.get('sbc'), '_filed': r['filed']}
    x = r.get('xbrl')
    if not x: return None
    src = x['ytd'] if p.isdigit() else x['q']
    d = {k: src.get(k) for k in IS_KEYS + ['eps_b', 'eps_d', 'sh_b', 'sh_d']}
    d['_filed'] = r['filed']
    return d

def do_is(p):
    if p.startswith('Q4'):
        y = 2000 + int(p[-2:]); fy, q3 = REC.get(str(y)), REC.get(qk(y, 3))
        if not fy or not q3: LOG.append(f'{p}: no FY / Q3'); return
        a, b = fy['xbrl']['ytd'], q3['xbrl']['ytd']
        d = {k: (a[k] - N(b.get(k)) if a.get(k) is not None else None) for k in IS_KEYS}
        f_fy, f_q3 = split_factor(fy['filed']), split_factor(q3['filed'])
        sh = {}
        for k in ('sh_b', 'sh_d'):
            qs = [X(qk(y, q), k) for q in (1, 2, 3)]
            if a.get(k) is not None and all(v is not None for v in qs):
                sh[k] = 4 * a[k] * f_fy - sum(qs)              # Q4 weighted shares = 4 x FY - sum(Q1-Q3), split-adjusted
        rel = REC.get(p, {}).get('release') or {}
        rf = split_factor(rel.get('filed', '9999'))
        eps_d = rel.get('eps_d_q') / rf if rel.get('eps_d_q') is not None else None
        eps_b = rel.get('eps_b_q') / rf if rel.get('eps_b_q') is not None else None
        for k, v in d.items(): put(p, k, v)
        put(p, 'sh_b', sh.get('sh_b')); put(p, 'sh_d', sh.get('sh_d')); put(p, 'eps_d', eps_d); put(p, 'eps_b', eps_b)
        put(p, 'q4_derived', 1)
    else:
        d = is_raw(p)
        if not d: LOG.append(f'{p}: no IS'); return
        f = split_factor(d.pop('_filed'))
        for k in IS_KEYS: put(p, k, d.get(k))
        for k in ('sh_b', 'sh_d'): put(p, k, d[k] * f if d.get(k) is not None else None)
        for k in ('eps_b', 'eps_d'): put(p, k, d[k] / f if d.get(k) is not None else None)
    x = DATA[p]['x']
    if x.get('cor') is None and x.get('opex_tot') is not None:     # 2012-13: cost of revenues tagged by segment only (Google / Motorola)
        put(p, 'cor', x['opex_tot'] - x['rd'] - x['sm'] - x['ga']); put(p, 'cor_derived', 1)
    if x.get('oie') is None:                                       # FY2009: other income, net not tagged -> EBT - OI (noted)
        put(p, 'oie', x['ebt'] - x['oi']); put(p, 'oie_derived', 1)
    put(p, 'oth_op', x['opex_tot'] - x['cor'] - x['rd'] - x['sm'] - x['ga'])
    put(p, 'disc', x['ni'] - (x['ebt'] - x['tax']))
    put(p, 'pref_div', N(x.get('pref_div')))
    put(p, 'dps', N(x.get('dps')))

# ---------------------------------------------------------------- cash flow
CF_KEYS = ['cf_dep', 'cf_amort', 'cf_sbc', 'cf_def', 'cf_gain', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_divest', 'cf_cfi', 'cf_bb', 'cf_div', 'cf_div_pref',
           'cf_sbcnet', 'cf_eq_iss', 'cf_pref_iss', 'cf_minority', 'cf_debt_iss', 'cf_debt_rep', 'cf_cff', 'cf_fx']

def cf_ytd(p):
    r = REC.get(p)
    if not r: return None
    if 'pre09' in r:
        a = r['pre09']
        return {'cf_dep': a['dep'], 'cf_amort': a['amort'], 'cf_sbc': a['sbc'], 'cf_def': N(a.get('deftax')), 'cf_gain': -N(a.get('impair_cf')),
                'cf_cfo': a['cfo'], 'cf_capex': a['capex'], 'cf_acq': a['acq'], 'cf_cfi': a['cfi'], 'cf_cff': a['cff'], 'cf_fx': a['fx'],
                'cf_eq_iss': N(a.get('eq_iss')), '_end': a['end'], '_beg': a['beg']}
    x = r.get('xbrl')
    if not x: return None
    d = {k: x['ytd'].get(k) for k in CF_KEYS}
    d['_end'] = x['q'].get('cf_cash'); d['_beg'] = x['q'].get('cf_cash_beg'); d['_concepts'] = x.get('concepts', {})
    return d

def cf_lines(c, ni, amort_is):
    """model cash-flow lines from a YTD dict (signs as presented: inflow +)."""
    dep = N(c.get('cf_dep'))
    amort = c.get('cf_amort')
    gain_tag = (c.get('_concepts') or {}).get('cf_gain', '')
    gain = c.get('cf_gain')
    # securities (gain) / loss adjustment as presented in CFO: gains are tagged positive and deducted (impairment add-back in 2008 already signed)
    gl = (-gain if gain_tag else N(gain)) if gain is not None else 0.0
    sbcnet = c.get('cf_sbcnet')
    sbcnet = -abs(sbcnet) if sbcnet is not None else 0.0
    o = {'cf_ni': ni, 'cf_dep': dep, 'cf_amort': N(amort), 'cf_sbc': N(c.get('cf_sbc')), 'cf_def': N(c.get('cf_def')), 'cf_gl': gl}
    o['cf_wc'] = c['cf_cfo'] - ni - dep - N(amort) - o['cf_sbc'] - o['cf_def'] - gl
    o['cf_cfo'] = c['cf_cfo']; o['cf_capex'] = c['cf_capex']; o['cf_acq'] = N(c.get('cf_acq')); o['cf_divest'] = N(c.get('cf_divest'))
    o['cf_oinv'] = c['cf_cfi'] - o['cf_capex'] - o['cf_acq'] - o['cf_divest']; o['cf_cfi'] = c['cf_cfi']
    o['cf_bb'] = N(c.get('cf_bb')); o['cf_div'] = N(c.get('cf_div')) + N(c.get('cf_div_pref')); o['cf_sbcnet'] = sbcnet
    o['cf_eqiss'] = N(c.get('cf_eq_iss')) + N(c.get('cf_pref_iss')) + N(c.get('cf_minority'))
    o['cf_debt'] = N(c.get('cf_debt_iss')) + N(c.get('cf_debt_rep'))
    o['cf_ofin'] = c['cf_cff'] - o['cf_bb'] - o['cf_div'] - o['cf_sbcnet'] - o['cf_eqiss'] - o['cf_debt']; o['cf_cff'] = c['cf_cff']
    o['cf_fx'] = N(c.get('cf_fx')); o['cf_net'] = c['cf_cfo'] + c['cf_cfi'] + c['cf_cff'] + o['cf_fx']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(p)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a, X(p, 'ni'), X(p, 'amort_int')).items(): put(p, k, v)
        put(p, 'cf_beg', a['_beg']); put(p, 'cf_end', a['_end'])
        if a['_beg'] is not None and abs(a['_beg'] + X(p, 'cf_net') - a['_end']) > 1: put(p, 'cf_end', a['_beg'] + X(p, 'cf_net'))
    for y in range(2013, 2027):
        prev = None; ni_c = 0.0
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 2: break
            p = qk(y, q)
            ni_c += X(p, 'ni')
            cur = cf_ytd(str(y) if q == 4 else p)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur, ni_c, None)
            if q == 1: d = lc; beg = cur['_beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            end = cur['_end']
            y0 = cur['_beg'] if q == 1 else None
            fy_beg = (cf_ytd(qk(y, 1)) or {}).get('_beg')
            if fy_beg is not None and abs(fy_beg + lc['cf_net'] - end) > 1:      # CF-statement cash incl. held-for-sale cash (Q1-Q3 2014)
                end = fy_beg + lc['cf_net']
            put(p, 'cf_beg', beg); put(p, 'cf_end', end)
            prev = (lc, end)

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r: return
    if 'pre09' in r:
        a = r['pre09']
        b = {'bs_cash': a['cash'], 'bs_msec': a['msec'], 'bs_ar': a['ar'], 'bs_tca': a['tca'], 'bs_nmsec': a['nmsec'], 'bs_ppe': a['ppe'], 'bs_gw': a['gw'],
             'bs_int': a['intang'], 'bs_ta': a['ta'], 'bs_ap': a['ap'], 'bs_tcl': a['tcl'], 'bs_eq': a['eq'], 'bs_tle': a['tle'], 'bs_ltd': 0.0}
        f = 40
    else:
        x = r.get('xbrl')
        if not x: return
        b = dict(x['q']); f = split_factor(r['filed'])
    ta, tca = b['bs_ta'], b['bs_tca']
    put(p, 'bs_cash', b['bs_cash']); put(p, 'bs_msec', N(b.get('bs_msec'))); put(p, 'bs_ar', b['bs_ar'])
    put(p, 'bs_oca', tca - b['bs_cash'] - N(b.get('bs_msec')) - b['bs_ar']); put(p, 'bs_tca', tca)
    put(p, 'bs_nmsec', N(b.get('bs_nmsec'))); put(p, 'bs_ppe', b['bs_ppe']); put(p, 'bs_gw', b['bs_gw'])
    put(p, 'bs_int_memo', b.get('bs_int'))
    put(p, 'bs_onca', ta - tca - N(b.get('bs_nmsec')) - b['bs_ppe'] - b['bs_gw']); put(p, 'bs_ta', ta)
    std = N(b.get('bs_cp')) + N(b.get('bs_cltd'))
    put(p, 'bs_ap', b['bs_ap']); put(p, 'bs_std', std); put(p, 'bs_ocl', b['bs_tcl'] - b['bs_ap'] - std); put(p, 'bs_tcl', b['bs_tcl'])
    put(p, 'bs_ltd', N(b.get('bs_ltd')))
    teq = b['bs_eq']; pref = N(b.get('bs_pref'))
    put(p, 'bs_ol', ta - teq - b['bs_tcl'] - N(b.get('bs_ltd')))
    put(p, 'bs_pref', pref); put(p, 'bs_eq', teq - pref); put(p, 'bs_teq', teq); put(p, 'bs_tle', b['bs_tle'])
    put(p, 'debt_tot', std + N(b.get('bs_ltd')))
    if b.get('bs_sh') is not None: put(p, 'bs_shares', b['bs_sh'] * f)

# ---------------------------------------------------------------- segments and revenue types
def dims(p, blk):
    d = (REC.get(p, {}).get('dims') or {}).get(blk)
    return (d or {}).get('values')

def seg_period(p, out):
    st, srn, son = dims(p, 'streams'), dims(p, 'segrev_new'), dims(p, 'segoi_new')
    sro, soo = dims(p, 'segrev_old'), dims(p, 'segoi_old')
    if st:
        for k in ('search', 'youtube', 'network', 'subs'): out[f'st_{k}'] = st.get(k)
        out['st_cloud'] = st.get('cloud', (srn or {}).get('cloud'))
    if srn:
        out['sr_svc'] = srn.get('svc'); out['sr_cloud'] = srn.get('cloud'); out['sr_ob'] = srn.get('ob')
        if out.get('st_cloud') is None: out['st_cloud'] = srn.get('cloud')
    if son:
        for k in ('svc', 'cloud', 'ob', 'alpha'): out[f'so_{k}'] = son.get(k)
    if sro:
        out['lsr_google'] = sro.get('google'); out['lsr_ob'] = sro.get('ob'); out['lsr_moto'] = sro.get('moto'); out['lsr_home'] = sro.get('home')
    if soo:
        out['lso_google'] = soo.get('google'); out['lso_ob'] = soo.get('ob'); out['lso_alpha'] = soo.get('alpha'); out['lso_moto'] = soo.get('moto'); out['lso_home'] = soo.get('home')
    return out

SEGK = ['st_search', 'st_youtube', 'st_network', 'st_subs', 'st_cloud', 'sr_svc', 'sr_cloud', 'sr_ob', 'so_svc', 'so_cloud', 'so_ob', 'so_alpha',
        'lsr_google', 'lsr_ob', 'lsr_moto', 'lso_google', 'lso_ob', 'lso_alpha', 'lso_moto']
LEGK = ['leg_web', 'leg_net', 'leg_oth', 'leg_moto', 'leg_ob']

def do_seg():
    raw = {p: seg_period(p, {}) for p in periods() if not p.startswith('Q4')}
    for p in periods():
        if p.startswith('Q4'):
            y = 2000 + int(p[-2:]); fy = raw.get(str(y), {}); qs = [raw.get(qk(y, q), {}) for q in (1, 2, 3)]
            v = {k: fy[k] - sum(q[k] for q in qs) for k in SEGK if fy.get(k) is not None and all(q.get(k) is not None for q in qs)}
        else:
            v = raw[p]
        for k, val in v.items(): put(p, k, val)
        x = DATA.get(p, {}).get('x', {})
        if x.get('sr_svc') is not None and x.get('rev') is not None:
            put(p, 'st_hedge', x['rev'] - x['sr_svc'] - x['sr_cloud'] - N(x.get('sr_ob')))
    # legacy revenue split (own filing; 10-K / pre-2009 text)
    for p in periods():
        r = REC.get(p, {})
        if p.isdigit() and 'pre09' in r:
            a = r['pre09']; put(p, 'leg_web', a.get('rs_web')); put(p, 'leg_net', a.get('rs_net')); put(p, 'leg_oth', a.get('rs_lic'))
        elif p.startswith('Q4'):
            y = 2000 + int(p[-2:])
            for k in LEGK:
                fy = X(str(y), k); qs = [X(qk(y, q), k) for q in (1, 2, 3)]
                if fy is not None and all(v is not None for v in qs): put(p, k, fy - sum(qs))
        else:
            for k, v in (r.get('legacy') or {}).items(): put(p, k, v)

# ---------------------------------------------------------------- release data, manual items
def do_release():
    for p in periods():
        if p.isdigit(): continue
        rel = REC.get(p, {}).get('release') or {}
        put(p, 'fcf_pub', rel.get('fcf_q')); put(p, 'tac', rel.get('tac_q')); put(p, 'employees', rel.get('employees'))
        rf = split_factor(rel.get('filed', '9999'))
        if rel.get('ng_ni_q') is not None and int(p[-2:]) <= 16:
            put(p, 'ng_oi_pub', rel.get('ng_oi_q')); put(p, 'ng_ni_pub', rel['ng_ni_q']); put(p, 'ng_sbc', rel.get('ng_sbc_q'))
            if rel.get('ng_eps_q') is not None: put(p, 'ng_eps_pub', rel['ng_eps_q'] / rf)
    for y in range(2013, 2026):
        qs = [X(qk(y, q), 'tac') for q in (1, 2, 3, 4)]
        if all(v is not None for v in qs): put(str(y), 'tac', sum(qs))
        put(str(y), 'employees', X(qk(y, 4), 'employees'))
    it = MAN['items']
    for p in periods():
        put(p, 'i_fine', 0.0); put(p, 'i_restr', 0.0); put(p, 'i_taxd', 0.0); put(p, 'i_eqimp', 0.0)
    for p in periods(): put(p, 'c_alloc', 0.0)
    for cat, key in (('fine', 'i_fine'), ('restr', 'i_restr'), ('taxd', 'i_taxd'), ('eq_impair', 'i_eqimp'), ('c_alloc', 'c_alloc')):
        for p, d in it[cat].items():
            if p.startswith('_'): continue
            put(p, key, d['v']); put(p, key + '_lab', d['label'])
            if not p.isdigit():
                y = str(2000 + int(p[-2:])); put(y, key, N(X(y, key)) + d['v']); put(y, key + '_lab', d['label'])
    for p, d in MAN['company_adjusted'].items():
        if p.startswith('_'): continue
        put(p, 'ca_oi', d.get('oi')); put(p, 'ca_ni', d.get('ni')); put(p, 'ca_eps', d.get('eps')); put(p, 'ca_def', d['def'])

def run():
    load()
    for p in periods():
        if not p.startswith('Q4'): do_is(p)
    for p in periods():
        if p.startswith('Q4'): do_is(p)
    for p in periods(): do_bs(p)
    for y in range(2013, 2026):                      # Q4 balance sheet = fiscal year end
        for k, v in list(DATA.get(str(y), {}).get('x', {}).items()):
            if k.startswith('bs_') or k == 'debt_tot': put(qk(y, 4), k, v)
    do_cf(); do_seg(); do_release()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 2) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'cf_cfo', 'cf_wc', 'bs_ta', 'debt_tot', 'st_search', 'so_cloud', 'leg_web')})
    print('\n'.join(LOG))
