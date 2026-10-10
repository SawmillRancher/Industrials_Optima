"""Harmonise the extracted Boeing data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m; costs positive).

Basis: every period as originally reported in its own earnings release (8-K Ex. 99.1). Restated comparatives in the following
year's release are kept as *_py memo keys where they differ (segment realignments 2017 / 2019 / 2021?, ASC 606 full-retrospective
restatement of 2016-17 in the 2018 releases, ASU 2017-07 pension reclassification).

Segments as reported:
  2006-2008  Commercial Airplanes (BCA); Integrated Defense Systems (IDS: PE&MS / N&SS / Support Systems to 2007; BMA / N&SS / GS&S
             from Q3-08 recast); Boeing Capital (BCC); Other; unallocated.
  2009-2016  BCA; IDS renamed Defense, Space & Security (BDS) in 2010 (BMA / N&SS / GS&S); BCC; Other segment; unallocated.
  2017+      BCA; BDS; Global Services (BGS, formed Q3-17 with Q1/Q2-17 recast); BCC (folded into unallocated from 2023);
             unallocated items, eliminations and other; FAS/CAS service cost adjustment (from Q1-18, ASU 2017-07).
Core (non-GAAP): published from the Q4-2012 release (FY2011 comparative). 2011-2017: core operating earnings = earnings from
operations + unallocated pension / postretirement expense; core EPS = GAAP EPS + its after-tax per-share effect (35%).
2018+: core operating earnings = earnings from operations - FAS/CAS service cost adjustment; core EPS = GAAP diluted EPS - FAS/CAS
service cost adjustment - non-operating pension / postretirement income + provision for deferred taxes on the adjustments.
Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
"""
import json, glob, os, re
import xbrl

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

def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def fyq(p):
    if p.isdigit(): return int(p), None
    return int('20' + p[-2:]), int(p[1])

# ---------------------------------------------------------------------------------------------------------------- P&L
def is_lines(p, i):
    rev = i['rev']
    put(p, 'rev', rev); put(p, 'rev_prod', i.get('rev_prod')); put(p, 'rev_serv', i.get('rev_serv'))
    cogs = -(N(i.get('cogs_prod')) + N(i.get('cogs_serv')))
    put(p, 'cogs', cogs); put(p, 'bcc_int', -N(i.get('bcc_int')))
    gp = rev - cogs + N(i.get('bcc_int'))
    put(p, 'gp', gp)
    put(p, 'opinv', N(i.get('opinv'))); put(p, 'ga', -N(i.get('ga'))); put(p, 'rd', -N(i.get('rd'))); put(p, 'gain', N(i.get('gain_disp')))
    efo = i['efo']
    put(p, 'efo', efo)
    # other operating lines shown separately (e.g. 2006 DOJ settlement): residual to the reported earnings from operations
    put(p, 'oth_op', round(gp + N(i.get('opinv')) + N(i.get('ga')) + N(i.get('rd')) + N(i.get('gain_disp')) - efo, 6))
    put(p, 'oth_inc', N(i.get('oth_inc'))); put(p, 'int_exp', -N(i.get('int_exp')))
    ebt = i.get('ebt'); put(p, 'ebt', ebt)
    put(p, 'tax', -N(i.get('tax')))
    ni = i.get('ni'); put(p, 'ni', ni)
    ni_cont = i.get('ni_cont', ebt + N(i.get('tax')) if ebt is not None else None)
    put(p, 'ni_cont', ni_cont)
    put(p, 'disc', (ni - ni_cont) if (ni is not None and ni_cont is not None) else 0.0)     # disc ops + cumulative effect of accounting change
    attr = i.get('ni_attr', ni)
    put(p, 'nci', round(ni - attr, 6)); put(p, 'ni_attr', attr)
    put(p, 'pref', N(i.get('pref')))
    put(p, 'ni_common', attr - N(i.get('pref')))
    put(p, 'eps_d', i.get('eps_d')); put(p, 'eps_b', i.get('eps_b')); put(p, 'dps', i.get('dps', 0.0 if p >= '2020' or p.startswith('Q') and fyq(p)[0] >= 2020 else None))

SEGK = ('bca', 'bds', 'bgs', 'bcc', 'oth', 'unal', 'doj')
def seg_lines(p, s, r):
    rv, ef = s.get('rev', {}), s.get('efo', {})
    for k in ('bca', 'bgs', 'bcc', 'oth'):
        put(p, f'sr_{k}', rv.get(k, 0.0 if k != 'bca' else None)); put(p, f'se_{k}', ef.get(k, 0.0 if k != 'bca' else None))
    # defense: total as reported, else the sum of the sub-segments (2010-11 releases print no total)
    for part, d in (('sr', rv), ('se', ef)):
        subs = [d[k] for k in ('bma', 'nss', 'gss', 'pems', 'ss') if k in d]
        bds = d.get('bds', sum(subs) if subs else None)
        if 'bds' not in d and subs: LOG.append(f'{p}: defense total = Σ sub-segments')
        put(p, f'{part}_bds', bds)
        for k in ('bma', 'nss', 'gss', 'pems', 'ss'): put(p, f'{part}_{k}', d.get(k))
    put(p, 'sr_unal', rv.get('unal', 0.0)); put(p, 'se_unal', N(ef.get('unal')) + N(ef.get('doj')))
    put(p, 'se_fascas', ef.get('fascas', 0.0))
    put(p, 'se_doj', ef.get('doj', 0.0))
    put(p, 'sr_tot', rv.get('tot')); put(p, 'se_tot', ef.get('tot'))

def core_lines(p, r):
    fy, q = fyq(p)
    rc, cp = r.get('core_recon') or {}, r.get('core_pub') or {}
    py = r.get('py') or {}
    def g(d, k, kind): return (d.get(k) or {}).get(kind)
    # unallocated pension / postretirement expense (pre-2018 core definition): reconciliation, else the unallocated detail table
    pen = [v for l, v in r.get('unal') or [] if re.match(r'^(pension|post-?retirement)$', l.strip().lower())]
    upp = -sum(pen) if (pen and fy < 2018) else g(rc, 'unal_pp', 'usd')
    if fy >= 2018:
        oe = g(rc, 'core_oe', 'usd'); eps = g(rc, 'core_eps', 'ps')
        if oe is None: oe = cp.get('core_oe')
        if eps is None: eps = cp.get('core_eps')
    elif fy == 2017:   # summary table: the Q4-17 release also carries a 2018-basis restated reconciliation
        oe = cp.get('core_oe', g(rc, 'core_oe', 'usd')); eps = cp.get('core_eps', g(rc, 'core_eps', 'ps'))
    else:
        oe = g(rc, 'core_oe', 'usd'); eps = g(rc, 'core_eps', 'ps')
        if oe is None: oe = cp.get('core_oe')
        if eps is None: eps = cp.get('core_eps')
    if eps is not None and abs(eps) > 60: eps = None
    basis = 'fascas' if fy >= 2018 else ('unal_pp' if eps is not None else 'none')
    if p == '2011':        # FY2011 core figures first published as comparatives in the Q4-2012 release (latest filing presenting the period)
        rc = (r.get('py') or {}).get('core_recon') or {}
        upp, oe, eps, basis = g(rc, 'unal_pp', 'usd'), g(rc, 'core_oe', 'usd'), g(rc, 'core_eps', 'ps'), 'unal_pp'
        LOG.append('2011: core figures from the Q4-2012 release comparative')
    put(p, 'core_basis', basis)
    put(p, 'unal_pp', upp)
    put(p, 'core_oe_pub', oe); put(p, 'core_eps_pub', eps)
    put(p, 'unal_pp_ps', g(rc, 'unal_pp', 'ps'))
    if fy < 2018: rc = {}
    put(p, 'nonop_pen', g(rc, 'nonop_pen', 'usd')); put(p, 'nonop_pr', g(rc, 'nonop_pr', 'usd'))
    put(p, 'core_dtax', g(rc, 'dtax', 'usd')); put(p, 'core_sub', g(rc, 'sub', 'usd')); put(p, 'core_sub_ps', g(rc, 'sub', 'ps'))
    put(p, 'sh_core', g(rc, 'sh', 'ps') or g(rc, 'sh', 'usd'))

# ---------------------------------------------------------------------------------------------------------------- KPIs
def kpi_lines(p, r):
    d = r.get('deliveries') or {}
    for k in ('737', '747', '767', '777', '787'): put(p, f'del_{k}', d.get(k, 0.0 if d else None))
    if d: put(p, 'del_717', round(d['tot'] - sum(N(d.get(k)) for k in ('737', '747', '767', '777', '787')), 6))
    put(p, 'del_tot', d.get('tot'))
    b = r.get('backlog') or {}
    for k in ('bca', 'bds', 'bgs', 'tot', 'contract', 'unob'): put(p, f'bl_{k}', b.get(k))

# ---------------------------------------------------------------------------------------------------------------- cash flow
WC = ('ar', 'unbilled', 'adv', 'inv', 'oca', 'ap', 'accr', 'itx', 'oltl', 'cfin')
def cf_from(r):
    c = r.get('cf') or {}
    if not c: return None
    o = {k: N(c.get(k)) for k in ('ni', 'sbc', 'cfo', 'capex', 'ppe_red', 'acq', 'inv_contrib', 'inv_proc', 'cfi', 'borrow', 'repay', 'bb', 'div',
                                   'pref_div', 'cff', 'fx', 'net')}
    o['dda'] = N(c.get('dda')) if c.get('dda') is not None else N(c.get('dep')) + N(c.get('amort_int'))
    o['pens'] = N(c.get('pens'))
    o['wc'] = sum(N(c.get(k)) for k in WC)
    raw = r.get('cf_raw') or []
    def rawv(pat):
        return sum(N(v) for l, v in raw if re.search(pat, l.lower()))
    o['divest'] = rawv(r'^proceeds from dispositions$|^proceeds from (the )?sale of business')
    o['eq_iss'] = rawv(r'stock issuance, net of issuance costs|^common stock issuance|preferred stock issuance')
    o['opt'] = rawv(r'^stock options exercised')
    o['div'] = rawv(r'^dividends paid$|^dividends paid on common')
    o['pref_div'] = rawv(r'dividends paid on mandatory convertible preferred')
    o['beg'] = c.get('beg'); o['end'] = c.get('end_r', c.get('end')); o['end_bs'] = c.get('end')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dda'], 'cf_sbc': c['sbc'], 'cf_pens': c['pens'], 'cf_wc': c['wc']}
    o['cf_onc'] = c['cfo'] - c['ni'] - c['dda'] - c['sbc'] - c['pens'] - c['wc']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest']
    o['cf_invnet'] = c['inv_contrib'] + c['inv_proc']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq'] - c['divest'] - o['cf_invnet']; o['cf_cfi'] = c['cfi']
    o['cf_debt'] = c['borrow'] + c['repay']; o['cf_bb'] = c['bb']; o['cf_div'] = c['div'] + c['pref_div']; o['cf_eq'] = c['eq_iss'] + c['opt']
    o['cf_ofin'] = c['cff'] - o['cf_debt'] - c['bb'] - o['cf_div'] - o['cf_eq']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); r = REC.get(p)
        a = cf_from(r) if r else None
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end']); put(p, 'cf_end_bs', a['end_bs'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 2: break
            p = qk(y, q)
            cur = cf_from(REC[p]) if REC.get(p) else None
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end']); put(p, 'cf_end_bs', cur['end_bs'])
            prev = (lc, cur['end'])

# ---------------------------------------------------------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']
    ta = b.get('ta', b.get('tle'))
    tca = b['tca']
    cash = b['cash']
    sti = N(b.get('sti'))
    ar = N(b.get('ar')) + N(b.get('unbilled'))
    put(p, 'bs_cash', cash); put(p, 'bs_sti', sti); put(p, 'bs_ar', ar); put(p, 'bs_inv', b['inv'])
    put(p, 'bs_oca', tca - cash - sti - ar - b['inv'])
    put(p, 'bs_tca', tca); put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', b.get('intang', 0.0))
    put(p, 'bs_onca', ta - tca - b['ppe'] - b['gw'] - N(b.get('intang'))); put(p, 'bs_ta', ta)
    std = N(b.get('std'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_adv', b.get('adv')); put(p, 'bs_std', std)
    put(p, 'bs_ocl', b['tcl'] - b['ap'] - N(b.get('adv')) - std); put(p, 'bs_tcl', b['tcl'])
    put(p, 'bs_ltd', N(b.get('ltd')))
    put(p, 'bs_pens', N(b.get('pens_l')) + N(b.get('rhc')))
    te = b.get('te', b.get('sh_eq'))
    nci = N(b.get('nci_eq'))
    if b.get('te') is None and b.get('sh_eq') is not None: te = b['sh_eq'] + nci
    tle = b.get('tle', ta)
    put(p, 'bs_ol', tle - te - b['tcl'] - N(b.get('ltd')) - N(b.get('pens_l')) - N(b.get('rhc')))
    put(p, 'bs_eq', te - nci); put(p, 'bs_nci', nci); put(p, 'bs_teq', te); put(p, 'bs_tle', tle)
    put(p, 'debt_tot', std + N(b.get('ltd')))
    # shares outstanding = issued (1,012,261,159) - treasury shares (balance-sheet caption)
    for l, v in r.get('bs_raw') or []:
        m = re.search(r'treasury (?:stock|shares), at cost\s*[–-]\s*([\d,]+)', l.lower())
        if m:
            put(p, 'bs_shares', round(1012.261159 - int(m.group(1).replace(',', '')) / 1e6, 6)); break
    if x_(p, 'bs_shares') is None:
        fy, q = fyq(p)
        t = xbrl.first_of(['TreasuryStockCommonShares', 'TreasuryStockShares'], fy, 'I', q or 4)
        if t is not None:
            put(p, 'bs_shares', round(1012.261159 - t, 6)); LOG.append(f'{p}: shares outstanding from XBRL treasury shares')

def run():
    load()
    for p in periods():
        r = REC.get(p)
        if not r: LOG.append(f'{p}: no record'); continue
        if r.get('is', {}).get('rev') is None: LOG.append(f'{p}: no IS'); continue
        is_lines(p, r['is'])
        sh = r['is'].get('sh_d')
        rc = r.get('core_recon') or {}
        if sh is None: sh = ((rc.get('sh') or {}).get('ps') or (rc.get('sh') or {}).get('usd'))
        put(p, 'sh_d', sh)
        seg_lines(p, r.get('seg') or {}, r)
        core_lines(p, r)
        kpi_lines(p, r)
        do_bs(p)
        put(p, 'fcf_pub', (r.get('core_pub') or {}).get('fcf'))
    do_cf()
    for p, v in MAN.get('overrides', {}).items():
        for k, val in v.items():
            if not k.startswith('_'): put(p, k, val)
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: (round(x[k], 1) if isinstance(x.get(k), float) else x.get(k)) for k in
                  ('rev', 'efo', 'ni_common', 'eps_d', 'sh_d', 'core_oe_pub', 'core_eps_pub', 'del_tot', 'cf_cfo', 'bs_ta', 'bs_shares')})
    print('\n'.join(LOG))
