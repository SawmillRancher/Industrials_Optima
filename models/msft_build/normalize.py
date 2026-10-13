"""Harmonise the extracted Microsoft data (data/<period>.json, data/_recast27.json, ngaap.json, XBRL subset) into flat model keys:
DATA[period]['x'][key] (USD m).

Basis: each period as originally reported in its own earnings release (quarters, FY2013+) or 10-K (FY2006-FY2012). Exceptions:
  - Segments: the main build uses the FY27 structure (Agents and Infra / Devices and Consumer, eight product and service lines), which
    exists only as restated in the 8-K of 2-Sep-2026 (Q1 FY25 - Q4 FY26). Earlier structures are memo keys, as originally reported:
    five divisions FY2006-FY2013 (l1_*), Devices & Consumer / Commercial FY2014-FY2015 (l2_*, revenue and gross margin only),
    Productivity & Business Processes / Intelligent Cloud / More Personal Computing FY2016-FY2026 (s3_*).
  - Non-GAAP: ngaap.json (company "As Adjusted" reconciliations, as first published; periods first given adjusted figures by a later
    release take that presentation - Q1-Q3 FY15, FY2025 quarters).
  - Q1 FY26 cash flow: D&A and investment gains restated from the Q2 FY26 year-to-date statement (manual_items.json corrections).
  - Depreciation, amortization of intangibles (annual), dividends declared per share and finance-lease data: XBRL company facts
    (10-K / 10-Q, as first filed).
Cash flow: quarters are the releases' three-month columns (MSFT releases present them directly; Q1 = year to date)."""
import json, glob, os
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
NG = json.load(open(os.path.join(BASE, 'ngaap.json')))
RC = None

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), None
    return int('20' + p[-2:]), int(p[1])

def periods():
    out = [str(y) for y in range(2006, 2027)]
    for y in range(2013, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4)]
    return out

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v

def load():
    global RC
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))
    RC = json.load(open(os.path.join(BASE, 'data', '_recast27.json')))

# ---------------------------------------------------------------- segment name maps
L1 = {'win': ('Client', 'Windows & Windows Live Division', 'Windows Division'), 'st': ('Server and Tools',),
      'osd': ('MSN', 'Online Services Business', 'Online Services Division'),
      'mbd': ('Information Worker', 'Microsoft Business Solutions', 'Microsoft Business Division'),
      'edd': ('Mobile and Embedded Devices', 'Home and Entertainment', 'Entertainment and Devices Division'),
      'unal': ('Reconciling amounts', 'Unallocated and other', 'Corporate-level activity')}
L2 = {'dcl': ('Devices and Consumer Licensing',), 'cgh': ('Computing and Gaming Hardware', 'Devices and Consumer Hardware'),
      'ph': ('Phone Hardware',), 'dco': ('Devices and Consumer Other',), 'cl': ('Commercial Licensing',), 'co': ('Commercial Other',),
      'corp': ('Corporate and Other',)}
S3 = {'pbp': ('Productivity and Business Processes',), 'ic': ('Intelligent Cloud',), 'mpc': ('More Personal Computing',), 'corp': ('Corporate and Other',)}
LINES = {'az': 'Azure', 'm365': 'Microsoft 365 cloud', 'psl': 'Productivity and server licensing', 'ind': 'Industry solutions',
         'fss': 'Frontier and support services', 'sa': 'Search and advertising', 'xbox': 'XBOX', 'win': 'Windows OEM and devices'}

def seg_map(seg, names, metric, prefix, p, suffix):
    for k, nm in names.items():
        vals = [v for kk, v in seg.items() if kk.split('||')[0] == metric and kk.split('||')[1] in nm]
        if vals: put(p, f'{prefix}_{k}_{suffix}', sum(vals))

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i = r['is']
    rev, cogs = i['rev'], i['cogs']
    put(p, 'rev', rev); put(p, 'rev_prod', i.get('rev_prod')); put(p, 'rev_serv', i.get('rev_serv'))
    put(p, 'cogs', cogs); put(p, 'gp', rev - cogs)
    put(p, 'rd', i['rd']); put(p, 'sm', i['sm']); put(p, 'ga', i['ga']); put(p, 'impair', N(i.get('impair')))
    put(p, 'oi', i['oi']); put(p, 'oth', i['oth']); put(p, 'ebt', i['ebt']); put(p, 'tax', i['tax']); put(p, 'ni', i['ni'])
    for k in ('eps_b', 'eps_d', 'sh_b', 'sh_d'): put(p, k, i.get(k))
    # dividends declared per share: XBRL (FY2008+), else the income statement
    if q is None: d = xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY')
    elif q < 4: d = xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'Q', q)
    else:
        fyd = xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY')
        qs = [xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'Q', k) for k in (1, 2, 3)]
        d = round(fyd - sum(qs), 4) if fyd is not None and None not in qs else None
    put(p, 'dps', d if d is not None else i.get('dps'))
    # segments
    seg = r.get('seg') or {}
    if fy <= 2013: seg_map(seg, L1, 'rev', 'l1', p, 'r'); seg_map(seg, L1, 'oi', 'l1', p, 'o')
    elif fy <= 2015: seg_map(seg, L2, 'rev', 'l2', p, 'r'); seg_map(seg, L2, 'gm', 'l2', p, 'g')
    else: seg_map(seg, S3, 'rev', 's3', p, 'r'); seg_map(seg, S3, 'oi', 's3', p, 'o')
    # FY27 basis (restated, 8-K 2-Sep-2026)
    if p in RC['prod']['Total']:
        for k, nm in LINES.items(): put(p, f'pl_{k}', RC['prod'][nm][p])
        for sk, nm in (('ai', 'Agents and Infra'), ('dc', 'Devices and Consumer')):
            for m in ('rev', 'cogs', 'opex', 'oi'): put(p, f'sg_{sk}_{m}', RC['seg'][f'{m}||{nm}'][p])
    # non-GAAP
    n = NG.get(p)
    if n:
        cat = lambda c, col: sum(N(it[col]) for it in n['items'] if it['cat'] in c)
        put(p, 'oa_revdef', cat(('REVDEF',), 'oi')); put(p, 'oa_restr', cat(('RESTR', 'IMPAIR'), 'oi')); put(p, 'oa_legal', cat(('LEGAL',), 'oi'))
        put(p, 'oa_rev', cat(('REVDEF',), 'rev'))
        ops = [it for it in n['items'] if it['cat'] in ('REVDEF', 'RESTR', 'IMPAIR', 'LEGAL')]
        if n['gaap'][2] is not None:
            put(p, 'na_op', sum(N(it['ni']) for it in ops)); put(p, 'na_tax', cat(('TAX',), 'ni')); put(p, 'na_openai', cat(('OPENAI',), 'ni'))
            put(p, 'adj_ni_pub', n['adj'][2])
        else:
            put(p, 'na_op_ps', sum(N(it['eps']) for it in ops)); put(p, 'na_tax', 0.0); put(p, 'na_openai', 0.0)
        put(p, 'adj_rev_pub', n['adj'][0]); put(p, 'adj_oi_pub', n['adj'][1]); put(p, 'adj_eps_pub', n['adj'][3])
        put(p, 'ng_lab', '; '.join(f"{it['label']} ({it['cat']}: OI {it['oi']:+,.0f}" + (f", NI {it['ni']:+,.0f}" if it['ni'] is not None else '') + f", EPS {it['eps']:+.2f})"
                                    for it in n['items']) + f" — {n['basis']}")
        put(p, 'ng_basis', 'published')
    elif fy >= 2012 and not (fy == 2012 and q is not None):
        for k in ('oa_revdef', 'oa_restr', 'oa_legal', 'oa_rev', 'na_op', 'na_tax', 'na_openai'): put(p, k, 0.0)
        put(p, 'adj_ni_pub', i['ni']); put(p, 'adj_oi_pub', i['oi']); put(p, 'adj_rev_pub', rev); put(p, 'adj_eps_pub', i['eps_d'])
        put(p, 'ng_basis', 'none')                  # framework exists, no items this period: adjusted = GAAP
    else:
        for k in ('oa_revdef', 'oa_restr', 'oa_legal', 'oa_rev', 'na_op', 'na_tax', 'na_openai'): put(p, k, 0.0)
        put(p, 'ng_basis', 'n/p')                   # no adjusted measures published (FY2006-FY2011)
    # XBRL annual memo items
    if q is None:
        put(p, 'x_dep', xbrl.value('Depreciation', fy, 'FY')); put(p, 'x_amort', xbrl.value('AmortizationOfIntangibleAssets', fy, 'FY'))
        put(p, 'x_fl', xbrl.value('FinanceLeaseLiability', fy, 'I', 4)); put(p, 'x_fl_add', xbrl.value('RightOfUseAssetObtainedInExchangeForFinanceLeaseLiability', fy, 'FY'))
        put(p, 'x_fl_prin', xbrl.value('FinanceLeasePrincipalPayments', fy, 'FY'))
        put(p, 'x_fl_int', xbrl.value('FinanceLeaseInterestExpense', fy, 'FY'))
    put(p, 'ppa_names', MAN['ppa'].get(p, {}).get('deal'))

# ---------------------------------------------------------------- cash flow
def do_cf(p):
    r = REC.get(p)
    if not r: return
    c = dict(r['cf'])
    cor = MAN['corrections'].get(f'{p}_cf')
    gains_adj = 0.0
    if cor:
        gains_adj = c['dda'] - cor['dda']; c['dda'] = cor['dda']; LOG.append(f'{p}: CF correction applied ({gains_adj:+,.0f} D&A to gains)')
    ni = r['is']['ni']
    put(p, 'cf_ni', c.get('ni', ni)); put(p, 'cf_dda', c['dda']); put(p, 'cf_sbc', c['sbc']); put(p, 'cf_def', c['def'])
    put(p, 'cf_wc', c['cfo'] - c.get('ni', ni) - c['dda'] - c['sbc'] - c['def'])
    put(p, 'cf_cfo', c['cfo']); put(p, 'cf_capex', c['capex']); put(p, 'cf_acq', c['acq'])
    put(p, 'cf_oinv', c['cfi'] - c['capex'] - c['acq']); put(p, 'cf_cfi', c['cfi'])
    debt = N(c.get('debt_iss')) + N(c.get('debt_rep')) + N(c.get('debt_st'))
    put(p, 'cf_bb', c['bb']); put(p, 'cf_div', c['div']); put(p, 'cf_iss', c['iss']); put(p, 'cf_debt', debt)
    put(p, 'cf_ofin', c['cff'] - c['bb'] - c['div'] - c['iss'] - debt); put(p, 'cf_cff', c['cff'])
    put(p, 'cf_fx', N(c.get('fx'))); put(p, 'cf_net', c['cfo'] + c['cfi'] + c['cff'] + N(c.get('fx')))
    put(p, 'cf_beg', c['beg']); put(p, 'cf_end', c['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']
    ta, tca, tcl = b['ta'], b['tca'], b['tcl']
    sti = N(b.get('sti')); inv = N(b.get('inv'))
    put(p, 'bs_cash', b['cash']); put(p, 'bs_sti', sti); put(p, 'bs_ar', b['ar']); put(p, 'bs_inv', inv)
    put(p, 'bs_oca', tca - b['cash'] - sti - b['ar'] - inv); put(p, 'bs_tca', tca)
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_eqinv', N(b.get('eqinv'))); put(p, 'bs_gw', b['gw']); put(p, 'bs_int', N(b.get('intang')))
    put(p, 'bs_onca', ta - tca - b['ppe'] - N(b.get('eqinv')) - b['gw'] - N(b.get('intang'))); put(p, 'bs_ta', ta)
    cdebt = N(b.get('std')) + N(b.get('cltd'))
    put(p, 'bs_ap', b['ap']); put(p, 'bs_cdebt', cdebt); put(p, 'bs_ucr', b['ucr'])
    put(p, 'bs_ocl', tcl - b['ap'] - cdebt - b['ucr']); put(p, 'bs_tcl', tcl)
    put(p, 'bs_ltd', N(b.get('ltd'))); put(p, 'bs_ol', b['tl'] - tcl - N(b.get('ltd'))); put(p, 'bs_tl', b['tl'])
    put(p, 'bs_eq', b['eq']); put(p, 'bs_tle', b['tle']); put(p, 'bs_shares', b.get('sh_out'))
    put(p, 'debt_tot', cdebt + N(b.get('ltd')))

def run():
    load()
    for p in periods():
        do_pl(p); do_bs(p); do_cf(p)
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'dps', 'adj_eps_pub', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'sg_ai_rev', 's3_pbp_r', 'l2_cl_r', 'l1_win_r', 'x_dep')})
    print('\n'.join(LOG))
