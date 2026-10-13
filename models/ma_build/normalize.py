"""Harmonise the extracted Mastercard data into flat model keys: DATA[period]['x'][key] (USD m; shares m; per share $).

Basis: every period as originally reported in its own earnings release (8-K Ex. 99.1): annual FY2006-FY2025 from the Q4
release twelve-month columns, quarters Q1-13 - Q2-26 from each quarter's three-month column. Prior-year columns that a later
release re-presented (e.g. the 2015 reclassification of 2014 net revenue, ASC 606 in 2018) are kept as *_py memo keys.
- Shares / per-share: 10-for-1 split effective 21-Jan-2014; documents filed before 22-Jan-2014 are restated (shares x 10,
  per share / 10). Class A and Class B shares are combined (same economics; EPS is reported for both classes together).
- Cash flow: releases give year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M).
  From 2018 (ASU 2016-18) the statement reconciles cash + restricted cash + restricted security deposits held for customers.
- Balance sheet: condensed to the model lines by section (current / noncurrent); 'other' lines are derived so totals tie.
- Non-GAAP items, release KPIs and revenue by category: transcribed records in data/_agent/*.json (EXTRACTION_SCHEMA.md).
- DPS: XBRL CommonStockDividendsPerShareDeclared (as first filed; Q4 = FY - 9M), split-adjusted by filing date.
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC, AG = {}, [], {}, {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json'))) if os.path.exists(os.path.join(BASE, 'manual_items.json')) else {}
SPLIT_DATE = '2014-01-22'

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def fyq(p):
    if p.isdigit(): return int(p), 4
    return int('20' + p[-2:]), int(p[1])

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
    for f in sorted(glob.glob(os.path.join(BASE, 'data', '_agent', '*.json'))):
        for r in json.load(open(f)):
            AG[r['period']] = r

def rsum(rows, rx, col=0, sect=None):
    t, hit = 0.0, False
    for l, v in rows:
        if re.search(rx, l.lower()) and len(v) > col:
            t += v[col]; hit = True
    return t if hit else None

# ---------------------------------------------------------------- income statement
def do_is(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i = r['is']
    pre = r['sources']['release_date'] < SPLIT_DATE
    sf = 10.0 if pre else 1.0
    da = i.get('da') if i.get('da') is not None else (N(i.get('dep')) + N(i.get('amo')) if i.get('dep') is not None else None)
    put(p, 'rev', i['rev']); put(p, 'ga', i['ga']); put(p, 'am', i['am']); put(p, 'da', da)
    put(p, 'lit', N(i.get('lit'))); put(p, 'char', N(i.get('char')))
    put(p, 'opex', i['opex']); put(p, 'oi', i['oi'])
    put(p, 'inv_inc', N(i.get('inv_inc'))); put(p, 'eq_gl', N(i.get('eq_gl'))); put(p, 'int_exp', -N(i.get('int_exp')))
    put(p, 'oth_inc', N(i.get('oth'))); put(p, 'oth_tot', i.get('oth_tot'))
    put(p, 'ebt', i['ebt']); put(p, 'tax', i['tax']); put(p, 'ni_tot', i['ni_tot'])
    ni = i.get('ni_ma') if i.get('ni_ma') is not None else i['ni_tot']
    put(p, 'ni', ni); put(p, 'nci', i['ni_tot'] - ni)
    put(p, 'sh_b', i['sh_b'] * sf); put(p, 'sh_d', i['sh_d'] * sf)
    put(p, 'eps_b', i['eps_b'] / sf); put(p, 'eps_d', i['eps_d'] / sf)
    put(p, 'eps_d_asrep', i['eps_d']); put(p, 'split_adj', 1 if pre else 0)
    # prior-year comparative as presented one year later (restatement memo)
    fy, q = fyq(p)
    nxt = REC.get(str(fy + 1) if p.isdigit() else qk(fy + 1, q))
    if nxt and nxt.get('py', {}).get('is', {}).get('rev') is not None:
        rv = nxt['py']['is']['rev']
        if abs(rv - i['rev']) > 0.6: put(p, 'rev_py', rv); LOG.append(f'{p}: net revenue re-presented in the next year ({i["rev"]} -> {rv})')
        oiv = nxt['py']['is'].get('oi')
        if oiv is not None and abs(oiv - i['oi']) > 0.6: put(p, 'oi_py', oiv)

# ---------------------------------------------------------------- balance sheet (section-aware)
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs_raw'): return
    rows = r['bs_raw']
    sect, A = 'ca', {}
    def add(k, v): A[k] = A.get(k, 0.0) + v
    for lab, vals in rows:
        l = lab.lower().strip()
        if not vals: continue
        v = vals[0]
        if re.match(r'total current assets', l): A['tca'] = v; sect = 'nca'; continue
        if re.match(r'total assets', l): A['ta'] = v; sect = 'cl'; continue
        if re.match(r'total current liabilities', l): A['tcl'] = v; sect = 'ncl'; continue
        if re.match(r'total liabilities$', l): A['tl'] = v; sect = 'mez'; continue
        if re.match(r'total liabilities(,| and)', l): A['tle'] = v; continue
        if sect == 'ca':
            if re.match(r'cash and cash equivalents', l): add('cash', v)
            elif re.match(r'restricted cash', l): add('rcash', v)
            elif re.match(r'restricted security deposits', l): add('rsd_a', v)
            elif re.match(r'investments?$|investment securities|trading$|available-for-sale$|auction rate', l): add('inv', v)
            elif re.match(r'accounts receivable', l): add('ar', v)
            elif re.match(r'settlement (assets|due from)', l): add('settle_a', v)
        elif sect == 'nca':
            if re.match(r'property', l): add('ppe', v)
            elif re.match(r'goodwill', l): add('gw', v)
            elif re.match(r'other intangible assets', l): add('intang', v)
        elif sect == 'cl':
            if re.match(r'accounts payable', l): add('ap', v)
            elif re.match(r'settlement (obligations|due to)', l): add('settle_l', v)
            elif re.match(r'restricted security deposits', l): add('rsd_l', v)
            elif re.match(r'accrued litigation|obligations under', l): add('lit_l', v)
            elif re.match(r'accrued expenses', l): add('accr', v)
            elif re.match(r'short-term debt|current portion of long-term debt', l): add('std', v)
        elif sect == 'ncl':
            if re.match(r'long-term debt', l): add('ltd', v)
            elif re.match(r'obligations under', l): add('lit_l_nc', v)
        elif sect == 'mez':
            if re.match(r'redeemable non-?controlling|minority interest', l): add('mez', v)
            elif re.match(r"(total )?mastercard incorporated stockholders|total stockholders. equity$", l) and 'eq_ma' not in A: A['eq_ma'] = v
            elif re.match(r'non-?controlling interests?$', l): A['nci'] = v
            elif re.match(r'total equity', l): A['teq'] = v
            elif re.match(r'class a common stock', l): A['_clA'] = lab
            elif re.match(r'class b common stock', l): A['_clB'] = lab
            elif re.match(r'.*outstanding.*respectively|^[\d,]+$|respectively', l) and '_clA' in A and '_clB' not in A: A['_clA'] += ' ' + lab
    if 'ta' not in A: LOG.append(f'{p}: BS incomplete'); return
    teq = A.get('teq', A.get('eq_ma'))
    put(p, 'bs_cash', A.get('cash')); put(p, 'bs_rcash', A.get('rcash', 0.0)); put(p, 'bs_rsd', A.get('rsd_a', 0.0))
    put(p, 'bs_inv', A.get('inv', 0.0)); put(p, 'bs_ar', A['ar']); put(p, 'bs_set_a', A.get('settle_a', 0.0))
    put(p, 'bs_oca', A['tca'] - A['cash'] - A.get('rcash', 0) - A.get('rsd_a', 0) - A.get('inv', 0) - A['ar'] - A.get('settle_a', 0))
    put(p, 'bs_tca', A['tca']); put(p, 'bs_ppe', A['ppe']); put(p, 'bs_gw', A['gw']); put(p, 'bs_int', A['intang'])
    put(p, 'bs_onca', A['ta'] - A['tca'] - A['ppe'] - A['gw'] - A['intang']); put(p, 'bs_ta', A['ta'])
    put(p, 'bs_ap', A['ap']); put(p, 'bs_set_l', A.get('settle_l', 0.0)); put(p, 'bs_rsdl', A.get('rsd_l', 0.0))
    put(p, 'bs_litl', A.get('lit_l', 0.0)); put(p, 'bs_accr', A['accr']); put(p, 'bs_std', A.get('std', 0.0))
    put(p, 'bs_ocl', A['tcl'] - A['ap'] - A.get('settle_l', 0) - A.get('rsd_l', 0) - A.get('lit_l', 0) - A['accr'] - A.get('std', 0))
    put(p, 'bs_tcl', A['tcl']); put(p, 'bs_ltd', A.get('ltd', 0.0))
    put(p, 'bs_ol', A['tl'] - A['tcl'] - A.get('ltd', 0)); put(p, 'bs_tl', A['tl'])
    put(p, 'bs_mez', A.get('mez', 0.0))
    nci = A.get('nci', 0.0)
    put(p, 'bs_eq', A.get('eq_ma', teq - nci)); put(p, 'bs_nci', nci); put(p, 'bs_teq', teq)
    put(p, 'bs_tle', A.get('tle', A['tl'] + A.get('mez', 0) + teq))
    put(p, 'debt_tot', A.get('std', 0.0) + A.get('ltd', 0.0))
    # shares outstanding (Class A + Class B), from the equity captions
    pre = r['sources']['release_date'] < SPLIT_DATE
    def outst(t):
        if not t: return None
        t = t.replace('\n', ' ')
        m = re.search(r'([\d,]+(?:\.\d+)?) and ([\d,]+(?:\.\d+)?) shares (?:issued and )?outstanding', t) or \
            re.search(r'([\d,]+(?:\.\d+)?) and ([\d,]+(?:\.\d+)?) (?:shares )?issued and outstanding', t) or \
            re.search(r'([\d,]+(?:\.\d+)?) shares issued and outstanding', t) or re.search(r'([\d,]+(?:\.\d+)?) and [\d,]+ outstanding', t)
        if not m: return None
        v = float(m.group(1).replace(',', ''))
        return v / 1e6 if v > 1e6 else v
    a, b = outst(A.get('_clA')), outst(A.get('_clB'))
    if a is not None and b is not None:
        put(p, 'bs_shares', (a + b) * (10 if pre else 1))
    else:
        LOG.append(f'{p}: shares outstanding not parsed')

# ---------------------------------------------------------------- cash flow
def cf_ytd(fy, q):
    r = REC.get(str(fy)) if q == 4 and REC.get(str(fy)) else REC.get(qk(fy, q))
    if not r or not r.get('cf_raw'): return None
    rows = r['cf_raw']; c = r['cf']
    o = {}
    o['ni'] = c.get('ni'); o['da'] = c.get('da'); o['sbc'] = N(c.get('sbc')); o['def'] = N(c.get('deftax'))
    o['eqgl'] = N(rsum(rows, r'^\(gains?\) losses? on equity|^gains? on equity|^impairment of (investments|available|assets)'))
    o['cfo'] = c['cfo']
    o['capex'] = N(rsum(rows, r'^purchases? of property')) + N(rsum(rows, r'^capitalized software'))
    o['acq'] = N(rsum(rows, r'^acquisitions? of business'))
    o['cfi'] = c['cfi']
    o['bb'] = N(rsum(rows, r'^purchases? of treasury stock'))
    o['div'] = N(rsum(rows, r'^dividends paid'))
    o['debt'] = N(rsum(rows, r'^proceeds from debt|^payment of debt|^proceeds from \(payment of\) debt'))
    o['cff'] = c['cff']; o['fx'] = N(c.get('fx'))
    o['net'] = c['cfo'] + c['cfi'] + c['cff'] + N(c.get('fx'))
    o['beg'], o['end'] = c.get('beg'), c.get('end')
    corr = MAN.get('corrections', {}).get(str(fy) if (q == 4 and REC.get(str(fy))) else qk(fy, q), {})
    if 'cf_end' in corr:
        o['end'] = corr['cf_end']; LOG.append(f'{qk(fy, q)}: ending cash corrected to {corr["cf_end"]} (release typo; 10-Q)')
    o['basis'] = 'restricted' if any(re.search(r'restricted cash.*end of', l.lower()) for l, _ in rows) else 'cash'
    return o

KEYS = ('cf_ni', 'cf_dda', 'cf_sbc', 'cf_def', 'cf_eqgl', 'cf_wc', 'cf_cfo', 'cf_capex', 'cf_acq', 'cf_oinv', 'cf_cfi', 'cf_bb', 'cf_div',
        'cf_debt', 'cf_ofin', 'cf_cff', 'cf_fx', 'cf_net')
def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_dda': c['da'], 'cf_sbc': c['sbc'], 'cf_def': c['def'], 'cf_eqgl': c['eqgl']}
    o['cf_wc'] = c['cfo'] - c['ni'] - c['da'] - c['sbc'] - c['def'] - c['eqgl']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_debt'] = c['debt']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['debt']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']; o['cf_net'] = c['net']
    return o

def do_cf():
    for y in range(2006, 2026):
        p = str(y); a = cf_ytd(y, 4)
        if not a: LOG.append(f'{p}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(p, k, v)
        put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end']); put(p, 'cf_basis', a['basis'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 2: break
            p = qk(y, q)
            cur = cf_ytd(y, q)
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if q == 1: d = lc; beg = cur['beg']
            else:
                if prev is None: continue
                d = {k: lc[k] - prev[0][k] for k in lc}; beg = prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end']); put(p, 'cf_basis', cur['basis'])
            prev = (lc, cur['end'])
    for p in periods():
        if x_(p, 'cf_basis') == 'restricted' and x_(p, 'bs_cash') is not None:
            put(p, 'bs_rc_oth', x_(p, 'cf_end') - x_(p, 'bs_cash') - x_(p, 'bs_rcash') - x_(p, 'bs_rsd'))

# ---------------------------------------------------------------- operating KPIs (GDV)
def do_op(p):
    r = REC.get(p)
    if not r: return
    rows = r.get('op_rows') or []
    fy, q = fyq(p)
    row = (rows[3] if len(rows) > 3 else None) if p.isdigit() else (rows[0] if rows else None)
    if p.isdigit() and fy == 2006 and len(rows) > 3: row = rows[3]
    if row and len(row) >= 3:
        put(p, 'gdv', row[0]); put(p, 'gdv_g_usd', row[1] / 100); put(p, 'gdv_g_loc', row[2] / 100)
        if len(row) >= 4: put(p, 'pv', row[3])

# ---------------------------------------------------------------- transcribed: non-GAAP, KPIs, revenue categories
CATS = {'LEGAL': 'lit', 'RESTR': 'restr', 'EQGL': 'eqgl', 'GAIN': 'gain', 'FOUNDATION': 'oth', 'IMPAIR': 'oth', 'ACQ': 'oth', 'OTHER': 'oth', 'TAXD': 'taxd'}
OCATS = ['lit', 'restr', 'oth']          # operating-expense parts of special items
NCATS = ['eqgl', 'gain']                 # other income (expense) parts: equity-investment (gains) losses; other non-operating items
def do_ag(p):
    a = AG.get(p)
    if not a: return
    n = a.get('ngaap') or {}
    tot = {c: 0.0 for c in OCATS + NCATS + ['rev']}
    taxd = 0.0; labels = {c: [] for c in OCATS + NCATS + ['rev', 'taxd']}
    if n.get('published'):
        for it in n.get('items') or []:
            c = CATS.get(it.get('cat'), 'oth')
            if c == 'taxd':
                taxd += N(it.get('ni')); labels['taxd'].append(f"{it['label']} ({N(it.get('ni')):+,.0f} net income)"); continue
            pre_o, pre_n, pre_r = N(it.get('opex_pre')), N(it.get('oth_pre')), N(it.get('rev_pre'))
            if pre_o:
                co = c if c in OCATS else 'oth'; tot[co] += pre_o; labels[co].append(f"{it['label']} {pre_o:,.0f}")
            if pre_n:
                cn = 'eqgl' if c == 'eqgl' else 'gain'; tot[cn] += pre_n; labels[cn].append(f"{it['label']} {pre_n:,.0f}")
            if pre_r:
                tot['rev'] += pre_r; labels['rev'].append(f"{it['label']} {pre_r:,.0f}")
        sf = 10.0 if (REC.get(p, {}).get('sources', {}).get('release_date', '9') < SPLIT_DATE) else 1.0
        adj = n.get('adj') or {}
        for c in OCATS + NCATS + ['rev']:
            put(p, f'oa_{c}', tot[c]); put(p, f'oa_{c}_lab', '; '.join(labels[c]))
        put(p, 'oa_taxd', taxd); put(p, 'oa_taxd_lab', '; '.join(labels['taxd']))
        put(p, 'adj_opex_pub', adj.get('opex')); put(p, 'adj_ni_pub', adj.get('ni')); put(p, 'adj_rev_pub', adj.get('rev'))
        put(p, 'e_pub', adj['eps_d'] / sf if adj.get('eps_d') is not None else None)
        put(p, 'adj_oth_pub', adj.get('oth_inc')); put(p, 'adj_om_pub', adj.get('op_margin') / 100 if adj.get('op_margin') is not None else None)
        put(p, 'adj_basis', 'published'); put(p, 'ngaap_def', n.get('def_note'))
    else:
        for c in OCATS + NCATS + ['rev']: put(p, f'oa_{c}', 0.0)
        put(p, 'oa_taxd', 0.0); put(p, 'adj_basis', 'none')
    k = a.get('kpi') or {}
    for src, dst in (('rev_g_cn', 'k_rev_g_cn'), ('gdv_g_local', 'k_gdv_g'), ('xb_g_local', 'k_xb_g'), ('sw_g', 'k_sw_g'), ('pn_g_cn', 'k_pn_g_cn'),
                     ('vas_g_cn', 'k_vas_g_cn'), ('rebates_g', 'k_reb_g'), ('rev_g', 'k_rev_g')):
        if k.get(src) is not None: put(p, dst, k[src] / 100)
    put(p, 'k_cards', k.get('cards_bn')); put(p, 'k_sw_label', k.get('sw_label')); put(p, 'k_xb_label', k.get('xb_label'))

RC_LEG = [('rc_dom', r'^domestic assessments'), ('rc_xb', r'^cross-border'), ('rc_tp', r'^transaction processing'),
          ('rc_oth', r'^other (revenues|network assessments)'), ('rc_reb', r'rebates and incentives')]
RC_CUR = [('rc_pn', r'^payment network'), ('rc_vas', r'^value-added services')]
def rc_map(lines, spec):
    o = {}
    for lab, v in lines or []:
        if v is None: continue
        for k, rx in spec:
            if re.search(rx, lab.lower().strip()):
                o[k] = o.get(k, 0.0) + v; break
    return o
def revcat(p, kind):
    """kind: 'q' / 'ytd' / 'fy'; returns {'cur': {...}, 'leg': {...}} for that period's filing."""
    a = AG.get(p)
    rc = (a or {}).get('revcat') or {}
    out = {'cur': {}, 'leg': {}}
    main = rc.get(kind) or []
    met = rc.get(f'{kind}_metrics') or []
    if rc.get('basis') == 'current':
        out['cur'] = rc_map(main, RC_CUR); out['leg'] = rc_map(met, RC_LEG)
    elif rc.get('basis') == 'legacy':
        out['leg'] = rc_map(main, RC_LEG)
    elif rc.get(f'{kind}_legacy_recast'):        # FY2007-08: five-category recast in the FY2009 10-K (2006: none published)
        lr = rc[f'{kind}_legacy_recast']
        out['leg'] = rc_map(lr.get(kind) if isinstance(lr, dict) else lr, RC_LEG)
    return out

def do_rc():
    for p in periods():
        fy, q = fyq(p)
        if p.isdigit(): src = revcat(p, 'fy')
        elif q in (1, 2, 3): src = revcat(p, 'q')
        else:
            fyr, nine = revcat(str(fy), 'fy'), revcat(qk(fy, 3), 'ytd')
            src = {}
            for b in ('cur', 'leg'):
                src[b] = {k: fyr[b][k] - nine[b][k] for k in fyr[b] if k in nine[b]}
            if src['cur'] or src['leg']: put(p, 'rc_q4_derived', 1)
        for b in ('cur', 'leg'):
            for k, v in src[b].items(): put(p, (k if b == 'cur' else k.replace('rc_', 'rcl_')), v)
    # current-basis history for periods filed on the legacy basis: the next year's filing comparatives (manual_items)
    for p, d in MAN.get('revcat_recast', {}).items():
        for k in ('rc_pn', 'rc_vas'):
            if d.get(k) is not None and x_(p, k) is None: put(p, k, d[k]); put(p, 'rc_recast', 1)

def do_dps():
    """dividends declared per share from the 10-Q / 10-K (data/_dps.json): quarters = three-month figure where the filing shows
    one, else year-to-date differences (Q1 = H1 YTD - Q2 when the Q1 filing has none); Q4 = FY (10-K) - 9M. Split-adjusted for
    filings dated before 22-Jan-2014."""
    D = json.load(open(os.path.join(BASE, 'data', '_dps.json')))
    def g(k, f):
        r = D.get(k)
        if not r or r.get(f) is None: return None
        return r[f] / (10 if r['filed'] < SPLIT_DATE else 1)
    for y in range(2006, 2026):
        v = g(str(y), 'ytd')
        if v is not None: put(str(y), 'dps', v)
    for y in range(2013, 2027):
        qv, ytd = {}, {}
        for q in (1, 2, 3):
            qv[q], ytd[q] = g(qk(y, q), 'q'), g(qk(y, q), 'ytd')
        if qv[1] is None: qv[1] = ytd[1]
        if qv[1] is None and ytd[2] is not None and qv[2] is not None: qv[1] = ytd[2] - qv[2]
        for q in (2, 3):
            if qv[q] is None and ytd[q] is not None and ytd[q - 1] is not None: qv[q] = ytd[q] - ytd[q - 1]
        for q in (1, 2, 3):
            if qv[q] is None and q > 1 and ytd[q] is not None:
                prev = sum(qv[i] for i in range(1, q) if qv[i] is not None)
                qv[q] = ytd[q] - prev
        fyv = g(str(y), 'ytd')
        if fyv is not None and all(qv[q] is not None for q in (1, 2, 3)): qv[4] = round(fyv - qv[1] - qv[2] - qv[3], 4)
        for q, v in qv.items():
            if y == 2026 and q > 2: continue
            if v is not None: put(qk(y, q), 'dps', round(v, 4))
            else: LOG.append(f'{qk(y, q)}: DPS not available')

def run():
    if DATA: return DATA
    load()
    for p in periods():
        do_is(p); do_bs(p); do_op(p); do_ag(p)
    do_cf(); do_rc(); do_dps()
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 2) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'eps_d', 'sh_d', 'gdv', 'cf_cfo', 'cf_wc', 'bs_ta', 'bs_shares', 'debt_tot', 'dps', 'e_pub', 'rc_pn', 'rcl_dom')})
    print('\n'.join(LOG))
