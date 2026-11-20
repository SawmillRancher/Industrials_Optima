"""Harmonise the extracted Lockheed Martin data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis policy (hybrid, documented per period in x['basis'] and in cell comments):
  - Default: every period as originally reported in its own earnings release.
  - Company re-presentations applied where the following year's filings re-present the whole period:
      * FY2006 segments on the four-segment structure (Aeronautics / Electronic Systems / IS&GS / Space Systems) as re-presented in the
        FY2007 release; FY2011-12 segments on the five-segment structure introduced in 2013 (FY2011 from the FY2013 10-K, FY2012 from the
        Q4-2013 release comparatives). Consolidated figures are unchanged by these realignments.
      * FY2014-15 (years and quarters) segments on the Q4-2015 program realignment basis (pro forma tables in the Q4-2015 release);
        consolidated figures unchanged.
      * Q1-16 and Q2-16 on the continuing-operations basis (IS&GS in discontinued operations) from the 2017 release comparatives, so
        that every 2016 column is on the same basis as the Q3/Q4-16 releases and the 2016 10-K. 2015 and earlier include IS&GS
        (a memo series carries the 2016 10-K continuing-operations re-presentation of 2015 where published).
      * 2017 (year and quarters) on the 2018 adjusted basis (ASC 606 full retrospective + ASU 2017-07 pension presentation) from the
        2018 release comparatives, so that 2018 y/y is like-for-like; 2016 and earlier remain pre-ASC 606 (flagged). The 2017
        non-service pension reclassification by quarter comes from the Q1-2018 release table (manual_items.json).
  - Balance sheet and cash flow: as originally reported throughout. Cash flow quarters are derived from year-to-date statements.
  - Unallocated items keep the company's own lines (FAS/CAS pension adjustment, severance / impairment, stock-based compensation,
    intangible amortization, other, unusual items).
"""
import json, glob, os
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SEGPF = json.load(open(os.path.join(BASE, 'data', '_segpf_2015.json'))) if os.path.exists(os.path.join(BASE, 'data', '_segpf_2015.json')) else {}
TENK = json.load(open(os.path.join(BASE, 'data', '_10k_segments.json'))) if os.path.exists(os.path.join(BASE, 'data', '_10k_segments.json')) else {}
SEGS = ['aero', 'mfc', 'rms', 'space', 'isgs', 'es']

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

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

# ---------------------------------------------------------------- income statement
IS_KEYS = ['rev', 'cos', 'gp', 'othinc', 'op', 'int', 'nonsvc', 'othnonop', 'ebt', 'tax', 'cont', 'disc', 'ni', 'etr', 'eps_b', 'eps_d', 'eps_d_cont', 'sh_b', 'sh_d', 'sh_end']

def is_source(p):
    r = REC[p]
    fy, q = fyq(p)
    if p == '2006' and r.get('py', {}).get('is'):
        return r['py']['is'], r['is'], 'as re-presented in the FY2007 release (%s): interest income and other non-operating items moved below operating profit' % r['py']['release_date']
    if p in ('Q1-16', 'Q2-16') and r.get('py', {}).get('is'):
        return r['py']['is'], r['is'], 'continuing operations (IS&GS in discontinued operations) as re-presented in the %s release' % r['py']['release_date']
    if fy == 2017 and r.get('py', {}).get('is'):
        return r['py']['is'], r['is'], 'ASC 606 / ASU 2017-07 adjusted basis as re-presented in the %s release' % r['py']['release_date']
    return r['is'], None, None

def do_is(p):
    i, orig, basis = is_source(p)
    fy, q = fyq(p)
    i = dict(i)
    if fy == 2017:          # split the non-service pension cost (ASU 2017-07 reclassification) out of other non-operating
        rc = MAN['asu_2017_07_reclass_2017'].get(p)
        if rc is not None and i.get('othnonop') is not None:
            i['nonsvc'] = -rc; i['othnonop'] = i['othnonop'] + rc
    # presentation-only: the separate non-service FAS pension line (from Q3-2021) applied to earlier quarters where the following
    # year's release re-presents them (EBT unchanged)
    py = (REC[p].get('py') or {}).get('is') or {}
    if i.get('nonsvc') is None and py.get('nonsvc') is not None and py.get('ebt') == i.get('ebt') and py.get('othnonop') is not None:
        i['nonsvc'] = py['nonsvc']; i['othnonop'] = py['othnonop']; put(p, 'nonsvc_src', 'following year release (presentation only)')
    for k in IS_KEYS: put(p, k, i.get(k))
    if 'cont' not in i and i.get('ni') is not None:
        put(p, 'cont', i['ni'] - N(i.get('disc')))
    if 'disc' not in i and i.get('ni') is not None:
        put(p, 'disc', (i['ni'] - i['cont']) if i.get('cont') is not None else 0.0)
    if orig:
        put(p, 'is_orig', {k: orig.get(k) for k in ('rev', 'cos', 'gp', 'othinc', 'op', 'int', 'othnonop', 'ebt', 'tax', 'cont', 'disc', 'ni', 'eps_d', 'eps_d_cont', 'sh_d') if orig.get(k) is not None})
        put(p, 'is_basis', basis)
    # EPS basis for the company's "excluding" quotes: continuing-operations diluted EPS as originally reported
    base = (orig or i)
    put(p, 'eps_co_base', base.get('eps_d_cont') if base.get('eps_d_cont') is not None else base.get('eps_d'))
    # dividends per share (paid rate in the quarter; annual = declared per XBRL / 10-K)
    if q is None:
        v = xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY') if fy >= 2009 else MAN['dps_pre_xbrl'].get(str(fy))
        put(p, 'dps', v)
    else:
        q1 = xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'Q', 1)
        if q in (1, 2, 3): put(p, 'dps', q1)
        else:
            fyv = xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY')
            if fyv is not None and q1 is not None: put(p, 'dps', round(fyv - 3 * q1, 4))
    put(p, 'fcf_pub', (REC[p].get('summary') or {}).get('fcf_pub'))

# ---------------------------------------------------------------- segments and unallocated items
UA_MAP = {'fascas': 'ua_fascas', 'fascas_op': 'ua_fascas', 'sev': 'ua_sev', 'impair': 'ua_sev', 'sbc': 'ua_sbc', 'amort': 'ua_amort', 'other': 'ua_other', 'special': 'ua_special'}
UA_KEYS = ['ua_fascas', 'ua_sev', 'ua_sbc', 'ua_amort', 'ua_other', 'ua_special']

def seg_source(p):
    r = REC[p]
    fy, q = fyq(p)
    if p == '2006' and r.get('py', {}).get('seg'):
        return r['py']['seg'], r['seg'], 'four-segment structure (Aeronautics / Electronic Systems / IS&GS / Space Systems) as re-presented in the FY2007 release (%s); originally reported with the Systems & IT Group' % r['py']['release_date']
    if p == '2011' and TENK.get('2013', {}).get('seg', {}).get('2011'):
        s = TENK['2013']['seg']['2011']
        return {'sales': s['sales'], 'op': s['op'], 'unalloc': r['seg']['unalloc'], 'unalloc_tot': r['seg'].get('unalloc_tot'), 'op_cons': r['seg'].get('op_cons')}, r['seg'], \
            'five-segment structure (Aeronautics / IS&GS / MFC / MST / Space Systems) as re-presented in the FY2013 Form 10-K; originally reported with Electronic Systems'
    if p == '2012' and r.get('py', {}).get('seg') and 'mfc' in r['py']['seg']['sales']:
        s = r['py']['seg']
        return {'sales': s['sales'], 'op': s['op'], 'unalloc': r['seg']['unalloc'], 'unalloc_tot': r['seg'].get('unalloc_tot'), 'op_cons': r['seg'].get('op_cons'), 'op_tot': s.get('op_tot')}, r['seg'], \
            'five-segment structure as re-presented in the Q4-2013 release (%s); originally reported with Electronic Systems' % r['py']['release_date']
    if p in SEGPF:
        s = SEGPF[p]
        return {'sales': s['sales'], 'op': s['op'], 'unalloc': r['seg']['unalloc'], 'unalloc_tot': s.get('unalloc_tot', r['seg'].get('unalloc_tot')), 'op_cons': s.get('op_cons', r['seg'].get('op_cons')), 'op_tot': s.get('op_tot')}, r['seg'], \
            'Q4-2015 program realignment basis (pro forma tables, Q4-2015 release of 26-Jan-2016); consolidated figures unchanged'
    if (p in ('Q1-16', 'Q2-16') or fy == 2017) and r.get('py', {}).get('seg'):
        return r['py']['seg'], r['seg'], ('continuing operations as re-presented in the %s release' if fy == 2016 else 'ASC 606 adjusted basis as re-presented in the %s release') % r['py']['release_date']
    return r['seg'], None, None

def do_seg(p):
    s, orig, basis = seg_source(p)
    if not s: LOG.append(f'{p}: no segment data'); return
    for k in SEGS:
        put(p, f'sr_{k}', s['sales'].get(k)); put(p, f'so_{k}', s['op'].get(k))
    put(p, 'seg_sales_tot', s.get('sales_tot', sum(v for k, v in s['sales'].items() if k != 'sitg')))
    put(p, 'segop_pub', s.get('op_tot', sum(s['op'].values()) if s['op'] else None))
    tot = {k: 0.0 for k in UA_KEYS}; labs = {k: [] for k in UA_KEYS}
    for lab, cat, v in s.get('unalloc', []):
        k = UA_MAP.get(cat)
        if not k: continue
        tot[k] += v
        if v: labs[k].append(f'{lab.strip()} {v:,.0f}')
    for k in UA_KEYS: put(p, k, tot[k]); put(p, k + '_lab', '; '.join(labs[k]))
    put(p, 'ua_tot', s.get('unalloc_tot', sum(tot.values())))
    put(p, 'op_cons', s.get('op_cons'))
    if orig:
        put(p, 'seg_orig', {'sales': orig['sales'], 'op': orig['op']}); put(p, 'seg_basis', basis)
    # continuing-operations re-presentation of 2015 (2016 filings): memo
    r = REC[p]; fy, q = fyq(p)
    py = r.get('py') or {}
    if fy == 2015 and py.get('seg') and 'isgs' not in py['seg']['sales'] and py.get('is'):
        put(p, 'co_rev', py['is'].get('rev')); put(p, 'co_op', py['is'].get('op')); put(p, 'co_segop', py['seg'].get('op_tot'))
        put(p, 'co_cont', py['is'].get('cont')); put(p, 'co_eps', py['is'].get('eps_d_cont'))
    # backlog, deliveries
    bk = r.get('backlog') or {}
    for k in SEGS: put(p, f'bk_{k}', bk.get(k))
    put(p, 'bk_tot', bk.get('total'))
    dl = r.get('deliv') or {}
    for k, src in (('dl_f35', 'f35'), ('dl_f16', 'f16'), ('dl_f22', 'f22'), ('dl_c130j', 'c130j'), ('dl_heli', 'governmenthelicopterprograms')):
        put(p, k, dl.get(src))

# ---------------------------------------------------------------- pension (FAS / CAS)
def do_pension(p):
    r = REC[p]; fy, q = fyq(p)
    pe = dict(r.get('pension') or {})
    if fy == 2017 and (r.get('py') or {}).get('pension'):
        pe.update(r['py']['pension'])
    if pe.get('fas_exp') is None and pe.get('fascas') is not None and pe.get('cas') is not None and pe['cas'] > 0: pe['fas_exp'] = pe['fascas'] - pe['cas']
    if pe.get('nonsvc') is None and pe.get('fascas') is not None and pe.get('fascas_op') is not None: pe['nonsvc'] = pe['fascas'] - pe['fascas_op']
    put(p, 'p_fas_exp', pe.get('fas_exp')); put(p, 'p_svc', pe.get('fas_svc')); put(p, 'p_fascas_op', pe.get('fascas_op'))
    put(p, 'p_nonsvc', pe.get('nonsvc')); put(p, 'p_settle', abs(pe['settle']) if pe.get('settle') is not None else None)
    fascas = pe.get('fascas')
    if fascas is None and pe.get('fascas_op') is not None and pe.get('nonsvc') is not None: fascas = pe['fascas_op'] + pe['nonsvc']
    put(p, 'p_fascas', fascas)
    cas = None
    if pe.get('cas') is not None and pe['cas'] > 0: cas = pe['cas']
    elif fascas is not None and pe.get('fas_exp') is not None: cas = fascas - pe['fas_exp']
    elif pe.get('fascas_op') is not None and pe.get('fas_svc') is not None: cas = pe['fascas_op'] - pe['fas_svc']
    put(p, 'p_cas', cas)

# ---------------------------------------------------------------- cash flow
CF_DIRECT = ['ni', 'dda', 'sbc', 'deftax', 'sev', 'settle', 'rfl', 'pens', 'wc_ar', 'wc_ca', 'wc_inv', 'wc_ap', 'wc_cl', 'wc_tax', 'cfo',
             'capex', 'acq', 'divest', 'cfi', 'debt_iss', 'debt_rep', 'bb', 'div', 'stock_iss', 'cff', 'fx']

def cf_ytd(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in CF_DIRECT}
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    o['net'] = c.get('net')
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['dda'], 'cf_sbc': c['sbc'], 'cf_def': c['deftax'], 'cf_chg': c['sev'] + c['settle'] + c['rfl'], 'cf_pens': c['pens'],
         'cf_ar': c['wc_ar'], 'cf_ca': c['wc_ca'], 'cf_inv': c['wc_inv'], 'cf_ap': c['wc_ap'], 'cf_cl': c['wc_cl'], 'cf_tax': c['wc_tax']}
    o['cf_oth'] = c['cfo'] - sum(o.values())
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq'] - c['divest']; o['cf_cfi'] = c['cfi']
    o['cf_debt_iss'] = c['debt_iss']; o['cf_debt_rep'] = c['debt_rep']; o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_stock'] = c['stock_iss']
    o['cf_ofin'] = c['cff'] - c['debt_iss'] - c['debt_rep'] - c['bb'] - c['div'] - c['stock_iss']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(p)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q == 4: break
            p = qk(y, q); cur = cf_ytd(p)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end'])
            prev = (lc, cur['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): LOG.append(f'{p}: no BS'); return
    b = r['bs']
    ta, tca = b['ta'], b['tca']
    cash, ar, ca, inv = b['cash'], N(b.get('ar')), N(b.get('ca')), N(b.get('inv'))
    put(p, 'bs_cash', cash); put(p, 'bs_ar', ar); put(p, 'bs_ca', ca); put(p, 'bs_inv', inv)
    put(p, 'bs_oca', tca - cash - ar - ca - inv); put(p, 'bs_tca', tca)
    ppe, gw, intang, dta = N(b.get('ppe')), N(b.get('gw')), N(b.get('intang')), N(b.get('dta'))
    put(p, 'bs_ppe', ppe); put(p, 'bs_gw', gw); put(p, 'bs_int', intang); put(p, 'bs_dta', dta)
    put(p, 'bs_onca', ta - tca - ppe - gw - intang - dta); put(p, 'bs_ta', ta)
    ap, sal, cl, std, tcl = N(b.get('ap')), N(b.get('sal')), N(b.get('cl')), N(b.get('std')), b['tcl']
    put(p, 'bs_ap', ap); put(p, 'bs_sal', sal); put(p, 'bs_cl', cl); put(p, 'bs_std', std); put(p, 'bs_ocl', tcl - ap - sal - cl - std); put(p, 'bs_tcl', tcl)
    ltd, pens = N(b.get('ltd')), N(b.get('pens'))
    tle = b['tle']; tl = b.get('tl')
    te = tle - tl if tl is not None else N(b.get('te') or b.get('eq'))
    if tl is None: tl = tle - te
    put(p, 'bs_ltd', ltd); put(p, 'bs_pens', pens); put(p, 'bs_oncl', tl - tcl - ltd - pens); put(p, 'bs_tl', tl)
    eq = b.get('eq') if b.get('eq') is not None else te
    nci = te - eq if abs(te - eq) > 0.5 else 0.0
    put(p, 'bs_eq', te - nci); put(p, 'bs_nci', nci); put(p, 'bs_teq', te); put(p, 'bs_tle', tle)
    put(p, 'debt_tot', std + ltd)

# ---------------------------------------------------------------- company-quantified special items (manual_items.json)
def do_special():
    items = MAN['special_items']['items']
    for p in periods():
        its = [i for i in items if i['period'] == p]
        if not its:
            if p in REC: 
                for k in ('sp_pl', 'sp_pens', 'sp_tax', 'sp_taxact', 'sp_ps'): put(p, k, 0.0)
            continue
        pl = -sum(i['pretax'] for i in its if i['cat'] == 'OTHER')
        pens = -sum(i['pretax'] for i in its if i['cat'] == 'PENSION')
        tax = sum(i['pretax'] - i['aftertax'] for i in its if i['cat'] in ('OTHER', 'PENSION'))      # negative: tax benefit removed with the item
        taxact = -sum(i['aftertax'] for i in its if i['cat'] == 'TAXD')
        put(p, 'sp_pl', pl); put(p, 'sp_pens', pens); put(p, 'sp_tax', tax); put(p, 'sp_taxact', taxact)
        put(p, 'sp_ps', sum(i['ps'] for i in its))
        put(p, 'sp_lab', ' | '.join(f"{i['label']}: pre-tax {i['pretax']:,.0f}, after-tax {i['aftertax']:,.1f}, {i['ps']:+.2f}/sh ({i['src']})" for i in its))
        x = DATA[p]['x']
        if p in ('Q4-17', '2017'): put(p, 'sp_eps_pub', 4.30 if p == 'Q4-17' else 13.33)
        else:
            base = x.get('eps_d_cont') if x.get('eps_d_cont') is not None else x.get('eps_d')
            if base is not None: put(p, 'sp_eps_pub', round(base - sum(i['ps'] for i in its), 2))

def run():
    load()
    for p in periods():
        if p not in REC: LOG.append(f'{p}: missing record'); continue
        do_is(p); do_seg(p); do_pension(p); do_bs(p)
    do_cf(); do_special()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'op', 'ni', 'eps_d', 'dps', 'sr_aero', 'sr_rms', 'ua_fascas', 'ua_tot', 'p_cas', 'cf_cfo', 'cf_oth', 'bs_ta', 'debt_tot', 'bk_tot')})
    print('\n'.join(LOG))
