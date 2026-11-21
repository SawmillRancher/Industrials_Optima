"""Harmonise the extracted L3Harris data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release / 10-K / 10-KT, with one documented exception:
  - Segments on the three-segment structure effective Q1-26 (Space & Mission Systems, Communications & Spectrum Dominance,
    Missile Solutions) and the unallocated corporate items on that basis are taken for 2025 (quarters and year) from the Q3-26
    earnings appendix (latest filing presenting the period; manual_items.json 'recast_appendix'). The segments as originally
    reported in 2025 and earlier stay in the legacy memo keys (lr_* / lo_*). 2024 and earlier were not recast by the company.
Periods: '2013'..'2019' Harris fiscal years (Friday nearest 30-Jun); 'Q3-19', 'Q4-19', 'TP19' the six-month transition period
to 3-Jan-2020; 'Q1-20'.. calendar-fiscal quarters; '2020'..'2025' fiscal years (Friday nearest 31-Dec).
Cash flow: year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M; Q4-19 = TP - Q3-19).
Share-based compensation and deferred income taxes come from the cash-flow statement where printed, otherwise from XBRL company
facts (data/_xbrl.json), otherwise they stay inside the derived working-capital line (noted in LOG).
Non-GAAP EPS: published per share; $m = per share x diluted shares (pre-tax $ amounts where the release gives them), with a
labelled rounding line so that the bridge reproduces the published figure.
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
RA = MAN['recast_appendix']

def N(x): return x or 0.0
def qk(y, q): return f'Q{q}-{str(y)[2:]}'
HARRIS = [str(y) for y in range(2013, 2020)]
def periods():
    out = HARRIS + ['Q3-19', 'Q4-19', 'TP19']
    for y in range(2020, 2027):
        out += [qk(y, q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
        if y < 2026: out.append(str(y))
    return out
def is_annual(p): return p.isdigit() or p == 'TP19'

def put(p, k, v):
    if v is None: return
    DATA.setdefault(p, {}).setdefault('x', {})[k] = round(v, 6) if isinstance(v, float) else v
def x_(p, k): return DATA.get(p, {}).get('x', {}).get(k)

def load():
    for f in glob.glob(os.path.join(BASE, 'data', '*.json')):
        k = os.path.basename(f)[:-5]
        if not k.startswith('_'): REC[k] = json.load(open(f))

def num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

# ---------------------------------------------------------------- label classifiers
def corp_cat(lab):
    l = lab.lower()
    if 'amortization' in l and ('intangible' in l or 'acquisition' in l): return 'amort'
    if 'fas/cas' in l or 'pension adjustment' in l or 'fas pension' in l: return 'fascas'
    if 'impairment' in l: return 'impair'
    if 'divestiture-related' in l and 'expense' not in l: return 'gain'
    if re.search(r'\b(gain|loss)(es)? on (the )?sales?\b', l) or 'gain on sale' in l or 'loss on sale' in l: return 'gain'
    if 'integration' in l or 'lhx next' in l or 'restructuring' in l or 'merger' in l: return 'restr'
    if 'transaction' in l or 'acquisition' in l or 'divestiture' in l: return 'acq'
    return 'other'

LEGMAP = [('rf communications', 'rf'), ('integrated network', 'ins'), ('government communications', 'gcs'), ('critical networks', 'cn'), ('exelis', 'ex'),
          ('communication systems', 'cs'), ('space and intelligence', 'sis'), ('electronic systems', 'es'), ('integrated mission', 'ims'),
          ('space and airborne', 'sas'), ('space & airborne', 'sas'), ('aviation systems', 'avs'), ('aerojet', 'ar')]
CURMAP = [('space & mission', 'sms'), ('space and mission', 'sms'), ('spectrum dominance', 'csd'), ('missile solutions', 'ms')]
def seg_code(name, table):
    l = name.lower()
    for k, c in table:
        if k in l: return c
    return None

def item_cat(lab, loc, cat):
    l = lab.lower()
    if cat in ('TAX', 'TAXD') or loc == 'tax': return 'tax'
    if cat == 'NCI' or 'noncontrolling' in l: return 'nci'
    if cat == 'AMORT' or ('amortization' in l and 'intangible' in l): return 'amort'
    if loc in ('nonop', 'below_ni', 'discops') or cat == 'DEBT': return 'nonop'
    if 'integration' in l or 'lhx next' in l or 'restructuring' in l or cat == 'RESTR': return 'restr'
    if cat == 'IMPAIR' or 'impairment' in l: return 'impair'
    if cat == 'GAIN' or 'divestiture-related' in l: return 'gain'
    if cat == 'ACQ': return 'acq'
    return 'oth'
def bridge_kind(lab):
    l = lab.lower()
    if re.search(r'net of (income )?tax', l) or 'after-tax' in l or 'after tax' in l: return 'skip'          # single after-tax total line
    if l.startswith(('adjustments', 'total')) or 'per share amount' in l or 'non-gaap' in l: return 'skip'
    if 'noncontrolling' in l: return 'nci'
    if 'tax' in l: return 'tax'
    return 'item'

# ---------------------------------------------------------------- P&L, segments, non-GAAP
def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    i, s, n = r['is'], r.get('seg') or {}, r.get('ngaap') or {}
    rev = num(i.get('sales'))
    put(p, 'rev', rev); put(p, 'cogs', num(i.get('cogs'))); put(p, 'sga', num(i.get('sga')))
    ool = [(l, num(v)) for l, v in (i.get('other_op_lines') or []) if num(v) is not None]
    put(p, 'oth_op', sum(v for _, v in ool))
    put(p, 'oth_op_labels', '; '.join(f'{l} {v:,.0f}' for l, v in ool if v))
    oi = num(i.get('op_income'))
    put(p, 'oi', oi)
    pens = oth = 0.0; labs = []
    for l, v in (i.get('nonop_lines') or []):
        v = num(v)
        if v is None: continue
        if 'pension' in l.lower() and 'other' not in l.lower(): pens += v
        else: oth += v; labs.append(f'{l} {v:,.0f}')
    # split a combined "Non-service FAS pension income and other, net" / "Non-operating income" line with the disclosed pension income
    pi = RA['nonop_pens'].get(p)
    if pi is None: pi = num(((r.get('extra') or {}).get('pension') or {}).get('non_service_fas_pension_income'))
    if pens == 0.0 and pi is not None and oth:
        pens, oth = float(pi), oth - float(pi)
        labs.append(f'split: non-service FAS pension income {pi:,.0f} per the 10-Q / 10-K / earnings appendix')
    put(p, 'nonop_pens', pens); put(p, 'nonop_oth', oth); put(p, 'nonop_labels', '; '.join(labs))
    if num(i.get('interest_net')) is not None: put(p, 'int_net', num(i['interest_net']))
    else: put(p, 'int_net', N(num(i.get('interest_exp'))) - N(num(i.get('interest_inc'))))
    put(p, 'ebt', num(i.get('ebt'))); put(p, 'tax', num(i.get('tax')))
    cont = num(i.get('cont_ops'))
    if cont is None and num(i.get('net_income')) is not None: cont = num(i['net_income']) - N(num(i.get('disc_ops')))
    put(p, 'cont', cont); put(p, 'disc', N(num(i.get('disc_ops')))); put(p, 'ni_tot', num(i.get('net_income')))
    put(p, 'nci', N(num(i.get('nci')))); put(p, 'ni', num(i.get('ni_parent')) if num(i.get('ni_parent')) is not None else num(i.get('net_income')))
    put(p, 'pref_div', N(num(i.get('pref_div'))))
    put(p, 'sh_b', num(i.get('shares_basic'))); put(p, 'sh_d', num(i.get('shares_diluted')))
    put(p, 'eps_d', num(i.get('eps_dil'))); put(p, 'eps_cont', num(i.get('eps_dil_cont'))); put(p, 'dps', num(i.get('dps')))
    # ---- segments
    segs = s.get('segments') or []
    current = p in RA['sr_sms']
    lsum = lo = 0.0; found = False
    for g in segs:
        c = seg_code(g['name'], LEGMAP)
        cc = seg_code(g['name'], CURMAP)
        if cc and not current: LOG.append(f'{p}: current segment {g["name"]} outside recast range')
        if c and not cc:
            put(p, f'lr_{c}', N(x_(p, f'lr_{c}')) + N(num(g.get('sales')))); put(p, f'lo_{c}', N(x_(p, f'lo_{c}')) + N(num(g.get('op_income'))))
            lsum += N(num(g.get('sales'))); lo += N(num(g.get('op_income'))); found = True
        elif not cc:
            LOG.append(f'{p}: unmapped segment {g["name"]!r} ({g.get("sales")}, {g.get("op_income")}) -> other')
    other_rev = N(num(s.get('other_rev')))
    unm = [g for g in segs if not seg_code(g['name'], LEGMAP) and not seg_code(g['name'], CURMAP)]
    for g in unm: other_rev += N(num(g.get('sales')))
    unm_oi = sum(N(num(g.get('op_income'))) for g in unm)
    if found: put(p, 'lr_elim', N(num(s.get('intersegment'))))
    put(p, 'sr_other_orig', other_rev)
    corp = {c: 0.0 for c in ('amort', 'fascas', 'restr', 'acq', 'gain', 'impair', 'other')}
    clabs = []
    for l, v in (s.get('corp_lines') or []):
        v = num(v)
        if v is None: continue
        c = corp_cat(l); corp[c] -= v
        if v and c == 'other': clabs.append(f'{l} {-v:,.0f}')
    corp['other'] -= unm_oi
    if unm_oi: clabs.append(f'non-reportable / other businesses {-unm_oi:,.0f}')
    if current and p == '2024':     # FY2024 annual recast (Q4-25 release Table 9); unallocated items as originally reported, with the divested non-reportable businesses' operating income moved out of the segments
        for k in ('sr_sms', 'so_sms', 'sr_csd', 'so_csd', 'sr_ms', 'so_ms', 'sr_inter', 'sr_other', 'seg_oi_pub'): put(p, k, float(RA[k][p]))
        nr = RA['recast_2024']['nonrep_oi']
        corp['other'] -= nr; clabs.append(f'operating income of divested non-reportable businesses (recast) {-nr:,.0f}')
        for c, v in corp.items(): put(p, f'c_{c}', v)
        put(p, 'c_labels', '; '.join(clabs)); put(p, 'seg_recast', 1)
        put(p, 'seg_orig', f"As originally reported: segment operating income {N(num(s.get('seg_op_total_pub'))):,.0f} (four segments incl. the divested businesses)")
    elif current:
        for k in ('sr_sms', 'so_sms', 'sr_csd', 'so_csd', 'sr_ms', 'so_ms', 'sr_inter', 'sr_other', 'seg_oi_pub', 'c_amort', 'c_restr', 'c_gain', 'c_acq'):
            put(p, k, float(RA[k][p]))
        put(p, 'c_fascas', 0.0); put(p, 'c_impair', 0.0)
        co = RA['c_defcomp'][p] + RA['c_seginv'][p] + RA['c_otheritems'][p]
        put(p, 'c_other', float(co))
        put(p, 'c_labels', f"Change in fair value of deferred compensation plan liabilities {RA['c_defcomp'][p]:,.0f}; segment investment offset {RA['c_seginv'][p]:,.0f}; other items {RA['c_otheritems'][p]:,.0f}"
            + (' (Q3-26 earnings appendix, recast basis)' if p[-2:] == '25' else ''))
        for k in ('bk_sms', 'bk_csd', 'bk_ms'): put(p, k, RA[k][p] * 1000.0)
        for k in ('b2b_sms', 'b2b_csd', 'b2b_ms'): put(p, k, float(RA[k][p]))
        if p[-2:] == '25':
            put(p, 'seg_recast', 1)
            put(p, 'seg_orig', f"As originally reported: segment operating income {N(num(s.get('adj_seg_op_pub')) or num(s.get('seg_op_total_pub'))):,.0f}"
                + '; unallocated: ' + '; '.join(f'{k} {v:,.0f}' for k, v in corp.items() if v))
    else:
        put(p, 'sr_other', other_rev)
        for c, v in corp.items(): put(p, f'c_{c}', v)
        put(p, 'c_labels', '; '.join(clabs))
        tot = num(s.get('seg_op_total_pub'))
        put(p, 'seg_oi_pub', tot if tot is not None else (lo if found else None))
    # ---- KPIs
    k = s.get('kpis') or {}
    for key, src in (('k_orders', 'orders'), ('k_backlog', 'backlog'), ('k_funded', 'funded_backlog')):
        v = RA[key].get(p) if key in RA else None
        put(p, key, v * 1000.0 if v is not None else num(k.get(src)))
    og = RA['k_org'].get(p); og = og if og is not None else num(k.get('organic_growth'))
    if og is not None: put(p, 'k_org', og / 100.0)
    ex = r.get('extra') or {}
    put(p, 'rd', float(RA['rd'][p]) if p in RA['rd'] else num(ex.get('rd_company_funded')))
    put(p, 'employees', num(ex.get('employees')))
    # ---- non-GAAP
    if p in ('2019', 'Q3-19', 'Q4-19', 'TP19') or p[-2:] in ('20', '21'): put(p, 'adj_ebit_pub', num(n.get('adj_ebit_pub')))   # 'adjusted EBIT' was published FY2019-2021 only
    put(p, 'ebitda_pub', num(MAN['ebitda_pub'].get(p)))
    put(p, 'fcf_pub', num(n.get('adj_fcf_pub')) if num(n.get('adj_fcf_pub')) is not None else num(n.get('fcf_pub')))
    put(p, 'fcf_basis', 'adjusted free cash flow' if num(n.get('adj_fcf_pub')) is not None else ('free cash flow' if num(n.get('fcf_pub')) is not None else None))
    put(p, 'e_pub_pa', num(n.get('pension_adj_eps_pub')))
    cats = {c: 0.0 for c in ('amort', 'restr', 'acq', 'gain', 'impair', 'oth', 'nonop')}
    alabs = []
    epub, shd = num(n.get('adj_eps_pub')), num(i.get('shares_diluted'))
    if epub is not None and shd:
        ia = [(it[0], num(it[1]), it[2] if len(it) > 2 else None, it[3] if len(it) > 3 else None) for it in (n.get('item_amounts') or []) if len(it) >= 2 and num(it[1]) is not None]
        br = [(l, num(v), bridge_kind(l)) for l, v in (n.get('eps_bridge') or []) if num(v) is not None]
        br_items = [(l, v) for l, v, k in br if k == 'item']
        tax = nci = 0.0; has_tax = False
        for l, v, k in br:
            if k == 'tax': tax += v * shd; has_tax = True
            elif k == 'nci': nci += v * shd
        def addc(l, d, loc, cat, ps):
            nonlocal tax, nci, has_tax
            c = item_cat(l, loc, cat)
            if c == 'tax':
                if not any(k == 'tax' for _, _, k in br): tax += d; has_tax = True
                return
            if c == 'nci':
                if not any(k == 'nci' for _, _, k in br): nci += d
                return
            cats[c] += d
            if d: alabs.append(f'{l} {d:,.0f}' + (' (per share × diluted shares)' if ps else ''))
        if ia and len([1 for x in ia if item_cat(x[0], x[2], x[3]) not in ('tax', 'nci')]) >= len(br_items):
            for l, d, loc, cat in ia: addc(l, d, loc, cat, False)
        else:
            amt = {l.strip().lower(): (d, loc, cat) for l, d, loc, cat in ia}
            for l, v in br_items:
                a = amt.get(l.strip().lower())
                if a: addc(l, a[0], a[1], a[2], False)
                else: addc(l, v * shd, None, None, True)
        if num(n.get('items_tax_effect')) is not None: tax = num(n['items_tax_effect']); has_tax = True
        if num(n.get('items_nci')) is not None: nci = num(n['items_nci'])
        start = N(x_(p, 'cont')) - N(num(i.get('nci'))) - N(num(i.get('pref_div')))
        resid = epub * shd - (start + sum(cats.values()) + tax + nci)
        if not has_tax:      # only a total after-tax adjustment is published: the tax effect is the balance to the published figure
            tax, resid = resid, 0.0; put(p, 'a_tax_derived', 1)
        for c, v in cats.items(): put(p, f'a_{c}', v)
        put(p, 'a_tax', tax); put(p, 'a_nci', nci)
        put(p, 'a_round', resid)
        put(p, 'e_pub', epub); put(p, 'a_labels', '; '.join(alabs)); put(p, 'adj_basis', 'published')
    elif p in ('Q1-26', 'Q2-26', 'Q3-26'):
        # model rebuild of the FY2025 definition (not published from Q1-26; no amortization add-back since Q1-25): divestiture / transaction items; fair-value change of the preferred-stock derivatives
        put(p, 'a_amort', 0.0); put(p, 'a_restr', x_(p, 'c_restr')); put(p, 'a_acq', x_(p, 'c_acq')); put(p, 'a_gain', x_(p, 'c_gain'))
        put(p, 'a_impair', 0.0); put(p, 'a_oth', 0.0); put(p, 'a_nonop', -float(RA['pref_fv'].get(p, 0.0)))
        put(p, 'a_nci', 0.0); put(p, 'a_round', 0.0); put(p, 'adj_basis', 'model')
    else:
        for c in cats: put(p, f'a_{c}', 0.0)
        put(p, 'a_tax', 0.0); put(p, 'a_nci', 0.0); put(p, 'a_round', 0.0); put(p, 'adj_basis', 'none')

# ---------------------------------------------------------------- cash flow
def _lab(lines, pats, excl=()):
    tot, hit = 0.0, False
    for l, v in lines:
        ll = l.lower()
        if any(re.search(pt, ll) for pt in pats) and not any(re.search(e, ll) for e in excl) and num(v) is not None:
            tot += num(v); hit = True
    return tot if hit else None

def cf_ytd(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']; L = [(l, v) for l, v in (c.get('lines_raw') or [])]
    # operating section only (up to the net cash from operations line)
    op = []
    for l, v in L:
        if re.match(r'net cash (provided by|used in|\(used in\)|provided by \(used in\)).*operating', l.lower()): break
        op.append((l, v))
    o = {'ni': num(c.get('net_income')), 'cfo': num(c.get('cfo')), 'capex': N(num(c.get('capex'))), 'acq': N(num(c.get('acquisitions'))), 'divest': N(num(c.get('divest'))),
         'cfi': num(c.get('cfi')), 'bb': N(num(c.get('buyback'))), 'div': N(num(c.get('dividends'))), 'cff': num(c.get('cff')), 'fx': N(num(c.get('fx'))),
         'beg': num(c.get('cash_begin')), 'end': num(c.get('cash_end')), 'months': c.get('ytd_months')}
    da = _lab(op, [r'depreciation', r'^amortization of (acquisition|intangible)'])
    o['da'] = da if da is not None else N(num(c.get('da')))
    end = r['period_end']; m = c.get('ytd_months') or 12
    sbc = _lab(op, [r'^share-based compensation$', r'share-based matching', r'^share-based compensation and'])
    lump = _lab(op, [r'(pension|benefit).*share-based compensation', r'share-based compensation.*(pension|benefit)'])
    xs = xbrl.xv(['ShareBasedCompensation'], end, m)
    if sbc is None:
        sbc = xs
        if sbc is None: LOG.append(f'{p}: share-based compensation not printed / not in XBRL (inside derived working capital)'); sbc = 0.0
    pens = N(_lab(op, [r'pension', r'net periodic benefit', r'postretirement', r'defined benefit'], excl=[r'share-based compensation']))
    if lump is not None: pens += lump - (xs if xs is not None else 0.0)
    de = _lab(op, [r'^deferred income taxes'])
    if de is None:
        de = xbrl.xv(['DeferredIncomeTaxExpenseBenefit', 'DeferredIncomeTaxesAndTaxCredits'], end, m)
        if de is None: de = 0.0
    o['sbc'], o['pens'], o['def'] = sbc, pens, de
    debt = _lab(L, [r'proceeds from borrowings', r'repayments? of (borrowings|long-term debt)', r'commercial paper', r'issuances? of long-term debt', r'short-term debt', r'proceeds from .*notes',
                    r'net (proceeds from|payment of) .*(borrowings|debt)', r'term loan'])
    o['debt'] = N(debt)
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni'], 'cf_da': c['da'], 'cf_sbc': c['sbc'], 'cf_def': c['def'], 'cf_pens': c['pens']}
    o['cf_wc'] = c['cfo'] - c['ni'] - c['da'] - c['sbc'] - c['def'] - c['pens']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acq']; o['cf_divest'] = c['divest']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acq'] - c['divest']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['bb']; o['cf_div'] = c['div']; o['cf_debt'] = c['debt']
    o['cf_ofin'] = c['cff'] - c['bb'] - c['div'] - c['debt']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['cfo'] + c['cfi'] + c['cff'] + c['fx']
    return o

def do_cf():
    for p in periods():
        if is_annual(p):
            a = cf_ytd(p)
            if not a: LOG.append(f'{p}: no annual CF'); continue
            for k, v in cf_lines(a).items(): put(p, k, v)
            put(p, 'cf_beg', a['beg']); put(p, 'cf_end', a['end'])
    chains = [[('Q3-19', 3), ('Q4-19', 6)]] + [[(qk(y, q), 3 * q) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)] for y in range(2020, 2027)]
    for ch in chains:
        prev = None
        for p, m in ch:
            cur = cf_ytd(p)
            if cur is None and p[1] == '4':            # Q4: year-to-date = the annual record
                cur = cf_ytd('TP19' if p == 'Q4-19' else '20' + p[-2:])
            if cur is None: LOG.append(f'{p}: no YTD CF'); prev = None; continue
            lc = cf_lines(cur)
            if prev is None and ch.index((p, m)) > 0: LOG.append(f'{p}: previous YTD CF missing'); prev = (lc, cur['end']); continue
            if prev is None: d, beg = lc, cur['beg']
            else: d, beg = {k: lc[k] - prev[0][k] for k in lc}, prev[1]
            for k, v in d.items(): put(p, k, v)
            put(p, 'cf_beg', beg); put(p, 'cf_end', cur['end'])
            prev = (lc, cur['end'])

# ---------------------------------------------------------------- balance sheet
def do_bs(p):
    r = REC.get(p)
    if not r or not r.get('bs'): return
    b = r['bs']; g = lambda k: num(b.get(k))
    L = b.get('lines_raw') or []
    ta = g('ta')
    if ta is None: return
    cash = g('cash'); stinv = N(g('st_inv')) or N(_lab(L, [r'^short-term investments']))
    ar, ca, inv = N(g('ar')), N(g('contract_assets')), N(g('inventories'))
    tca = g('tca')
    if tca is None:      # unclassified balance sheet (Harris releases): current assets = the lines printed before PP&E
        tca = cash + stinv + ar + ca + inv; LOG.append(f'{p}: balance sheet not classified (no total current assets); other current assets inside other assets')
    put(p, 'bs_cash', cash); put(p, 'bs_stinv', stinv); put(p, 'bs_ar', ar); put(p, 'bs_ca', ca); put(p, 'bs_inv', inv)
    put(p, 'bs_oca', tca - cash - stinv - ar - ca - inv); put(p, 'bs_tca', tca)
    ppe, gw, it = N(g('ppe')), N(g('goodwill')), N(g('intangibles'))
    put(p, 'bs_ppe', ppe); put(p, 'bs_gw', gw); put(p, 'bs_int', it); put(p, 'bs_onca', ta - tca - ppe - gw - it); put(p, 'bs_ta', ta)
    std, ap, cl = N(g('st_debt')), N(g('ap')), N(g('contract_liab'))
    tcl = g('tcl')
    if tcl is None: tcl = std + ap + cl + N(g('comp_benefits'))
    ltd = N(g('ltd'))
    mezz = N(g('mezz'))
    te = g('te'); nci = N(g('nci'))
    if te is None: te = N(g('equity_parent')) + nci
    tle = g('tle') if g('tle') is not None else ta
    put(p, 'bs_std', std); put(p, 'bs_ap', ap); put(p, 'bs_cl', cl); put(p, 'bs_ocl', tcl - std - ap - cl); put(p, 'bs_tcl', tcl)
    put(p, 'bs_ltd', ltd); put(p, 'bs_ol', tle - te - mezz - tcl - ltd); put(p, 'bs_mezz', mezz)
    put(p, 'bs_eq', te - nci); put(p, 'bs_nci', nci); put(p, 'bs_teq', te); put(p, 'bs_tle', tle)
    put(p, 'bs_prefd', N(g('pref_deriv')))
    put(p, 'bs_shares', g('shares_out'))
    cur_ltd = _lab(L, [r'^current portion of long-term debt'])
    put(p, 'debt_st', std - N(cur_ltd)); put(p, 'debt_lt', N(cur_ltd) + ltd)

def run():
    load()
    for p in periods():
        do_pl(p); do_bs(p)
    for y in range(2020, 2026):   # Q4 non-service pension income where the Q4 release does not split it: fiscal year - nine months (derived, noted)
        q4 = qk(y, 4); fy = x_(str(y), 'nonop_pens'); q = [x_(qk(y, k), 'nonop_pens') for k in (1, 2, 3)]
        if x_(q4, 'rev') is not None and not x_(q4, 'nonop_pens') and fy and all(v for v in q):
            d = fy - sum(q)
            put(q4, 'nonop_oth', x_(q4, 'nonop_oth') - d); put(q4, 'nonop_pens', d)
            put(q4, 'nonop_labels', (x_(q4, 'nonop_labels') or '') + f'; non-service FAS pension income {d:,.0f} = fiscal year − nine months (not split in the Q4 release)')
    do_cf()
    for p in periods():           # cash in the cash-flow statement outside balance-sheet cash (held for sale / restricted)
        if x_(p, 'cf_end') is not None and x_(p, 'bs_cash') is not None:
            put(p, 'bs_cash_adj', x_(p, 'cf_end') - x_(p, 'bs_cash'))
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'seg_oi_pub', 'e_pub', 'a_round', 'cf_cfo', 'cf_wc', 'cf_sbc', 'bs_ta', 'bs_shares', 'bs_cash_adj')})
    print('\n'.join(LOG))
