"""Harmonise the extracted Moody's data (data/<period>.json) into flat model keys: DATA[period]['x'][key] (USD m).

Basis: every period as originally reported in its own earnings release / 10-Q / 10-K (the 10-K wins over the Q4 release for
annual records). Exceptions, by source priority:
  - MA revenue lines on the current structure (Decision Solutions / Research & Insights / Data & Information, introduced in
    the 2022 releases; Decision Solutions split into Banking / Insurance / KYC in the 2024 releases): for the year before each
    re-presentation the lines come from the following year's restated comparatives ("latest filing presenting the period"),
    but only where the restated lines sum to the originally reported MA revenue (a re-presentation inside MA). Earlier
    structures (Subscriptions / Software / Professional Services 2006-08; RD&A / Risk Management Software / PS 2009-10;
    RD&A / ERS / PS 2011-21) are kept as legacy memo keys.
  - Acquired-intangible amortization: XBRL AmortizationOfIntangibleAssets (10-Q / 10-K as first filed; Q4 = FY - 9M).
Cash flow: year-to-date statements; discrete quarters derived (Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M). Q4 balance sheets
are the 10-K year-end balance sheets. Segment items missing from a Q4 release are derived as FY - 9M (logged).
Adjusted EPS: the company's non-GAAP / adjusted diluted EPS as published in each period (definition flags in the workbook);
where only the per-share bridge is published, adjusted net income = adjusted EPS x diluted shares and item $ = per-share x
diluted shares (logged).
"""
import json, glob, os, re
import xbrl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA, LOG, REC = {}, [], {}
_MP = os.path.join(BASE, 'manual_items.json')
MAN = json.load(open(_MP)) if os.path.exists(_MP) else {}

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

# ---------------------------------------------------------------- revenue-line label maps
def _n(s): return re.sub(r'[^a-z]', '', s.lower().replace('&', 'and'))
MIS_MAP = [('corporatefinance', 'cfg'), ('structuredfinance', 'sfg'), ('financialinstitutions', 'fig'), ('publicprojectandinfrastructure', 'ppif'),
           ('publicfinance', 'ppif'), ('misother', 'moth'), ('other', 'moth')]
MA_MAP = [('banking', 'bank'), ('insurance', 'ins'), ('kyc', 'kyc'), ('researchandinsights', 'ri'), ('dataandinformation', 'di'),
          ('decisionsolutions', 'l_ds'), ('researchdataandanalytics', 'l_rda'), ('enterpriserisksolutions', 'l_ers'), ('professionalservices', 'l_ps'),
          ('riskmanagementsoftware', 'l_rms'), ('subscription', 'l_sub'), ('software', 'l_sw'), ('consulting', 'l_ps')]
def map_lines(d, mp, p, seg):
    out = {}
    for lab, v in (d or {}).items():
        if v is None: continue
        n = _n(lab)
        if n.startswith('total') and 'decisionsolutions' not in n: continue
        if 'recurring' in n or 'transaction' in n or 'intersegment' in n or 'subtotal' in n or 'eliminat' in n: continue
        k = next((k for pat, k in mp if n.startswith(pat) or n == pat or (pat in n and len(pat) > 8)), None)
        if k is None: LOG.append(f'{p}: unmapped {seg} line {lab!r}'); continue
        out[k] = out.get(k, 0.0) + v
    return out

MA_CUR = ('bank', 'ins', 'kyc', 'ri', 'di')
SEG_RECAST = {'2006': '2007', '2007': '2008'}

# adjusting-item categories -> model lines
def bridge_items(p, n, sh_d):
    """returns dict of pre-tax items by model line and labels; uses item_amounts, else per-share bridge x diluted shares."""
    tot = {'amort': 0.0, 'restr': 0.0, 'op': 0.0, 'nonop': 0.0}; lab = {'op': [], 'nonop': []}
    items = n.get('item_amounts') or []
    def cls(cat, loc, label):
        cat = (cat or '').upper(); loc = (loc or '').lower(); l = label.lower()
        if cat in ('TAX', 'TAXD', 'NCI') or loc in ('tax', 'below_ni'): return None
        if cat == 'AMORT' or 'amortization' in l: return 'amort'
        if cat == 'RESTR' or 'restructuring' in l or 'abandonment' in l: return 'restr' if 'restructuring' in l else 'op'
        if loc == 'nonop' or cat == 'GAIN': return 'nonop'
        return 'op'
    used = False
    for it in items:
        if len(it) < 5: continue
        label, pre, net, loc, cat = it[:5]
        c = cls(cat, loc, str(label))
        if c is None or pre is None: continue
        if str(label).lower().startswith(('tax on', 'net ')): continue
        tot[c] += pre; used = True
        if c in lab and pre: lab[c].append(f'{label} {pre:,.1f}')
    if not used and n.get('eps_bridge') and sh_d:
        for label, v in n['eps_bridge']:
            if v is None: continue
            l = str(label).lower()
            if 'tax' in l and 'pre-tax' not in l and 'pretax' not in l: continue
            if l.startswith('net ') and any(str(a).lower().startswith('pre') for a, _ in n['eps_bridge']): continue
            c = cls(None, 'nonop' if any(w in l for w in ('gain', 'legacy', 'icra', 'ccxi', 'hedge', 'fx', 'interest')) else 'op', str(label))
            if c is None: continue
            tot[c] += v * sh_d; used = True
            if c in lab and v: lab[c].append(f'{label} ${v:.2f}/sh')
        if used: LOG.append(f'{p}: adjusting items from the per-share bridge × diluted shares')
    return tot, lab, used

def do_pl(p):
    r = REC.get(p)
    if not r: LOG.append(f'{p}: no record'); return
    fy, q = fyq(p)
    i, s, n = r['is'], r.get('seg') or {}, r.get('ngaap') or {}
    put(p, 'rev', i['rev']); put(p, 'opr', i.get('opex_operating')); put(p, 'sga', i.get('sga')); put(p, 'dna', i.get('dna'))
    put(p, 'restr', N(i.get('restr')))
    ol = [(l, v) for l, v in (i.get('other_op_lines') or []) if v is not None]
    put(p, 'othop', sum(v for _, v in ol)); put(p, 'othop_lab', '; '.join(f'{l} {v:,.1f}' for l, v in ol if v))
    put(p, 'oi', i.get('oi')); put(p, 'int_net', i.get('int_net')); put(p, 'onop', i.get('oth_nonop'))
    nl = [(l, v) for l, v in (i.get('nonop_lines') or []) if v is not None]
    put(p, 'gain', sum(v for _, v in nl)); put(p, 'gain_lab', '; '.join(f'{l} {v:,.1f}' for l, v in nl if v))
    put(p, 'ebt', i.get('ebt')); put(p, 'tax', i.get('tax')); put(p, 'ni_tot', i.get('ni_tot')); put(p, 'nci', N(i.get('nci'))); put(p, 'ni', i.get('ni'))
    for k in ('eps_b', 'eps_d', 'sh_b', 'sh_d'): put(p, k, i.get(k))
    put(p, 'dps', i.get('dps_decl'))
    # revenue lines (2006-07: old MIS / Moody's KMV segments -> 2008-basis recast from the following year's comparatives)
    if p in SEG_RECAST:
        src = REC[SEG_RECAST[p]]['py']
        s = dict(s, mis_lines=src['mis_lines'], ma_lines=src['ma_lines'], mis_ext=sum(src['mis_lines'].values()), ma_ext=sum(src['ma_lines'].values()),
                 mis_interseg=None, ma_interseg=None)
        put(p, 'seg_recast', SEG_RECAST[p]); LOG.append(f'{p}: MIS / MA revenue lines on the 2008 basis from the {SEG_RECAST[p]} restated comparatives')
    ml = map_lines(s.get('mis_lines'), MIS_MAP, p, 'MIS')
    for k, v in ml.items(): put(p, f'r_{k}', v)
    al = map_lines(s.get('ma_lines'), MA_MAP, p, 'MA')
    # Decision Solutions sub-lines (Banking / Insurance / KYC): release / 10-Q revenue note, stored apart from ma_lines in 2023-25 records
    ds = s.get('ma_ds_lines') or {k[3:].strip(): v for k, v in (s.get('legacy') or {}).items() if k.startswith('DS:') and isinstance(v, (int, float))}
    dl = {k: v for k, v in map_lines(ds, MA_MAP, p, 'MA-DS').items() if k in ('bank', 'ins', 'kyc')}
    if len(dl) == 3 and 'bank' not in al:
        if al.get('l_ds') is not None and abs(sum(dl.values()) - al['l_ds']) > 1.5: LOG.append(f'{p}: DS sub-lines {sum(dl.values()):.1f} vs DS {al["l_ds"]:.1f} — not used')
        else: al.update(dl)
    for k, v in al.items(): put(p, f'r_{k}', v)
    if 'bank' in al and 'l_ds' in al: DATA[p]['x'].pop('r_l_ds', None)
    put(p, 'mis_ext', s.get('mis_ext')); put(p, 'ma_ext', s.get('ma_ext'))
    put(p, 'mis_isr', s.get('mis_interseg')); put(p, 'ma_isr', s.get('ma_interseg'))
    put(p, 'mis_rec', s.get('mis_recurring')); put(p, 'ma_rec', s.get('ma_recurring'))
    put(p, 'ma_arr', s.get('ma_arr'))
    put(p, 'mis_aoi', s.get('mis_adj_oi')); put(p, 'ma_aoi', s.get('ma_adj_oi'))
    for k in ('mis', 'ma'):
        v = s.get(f'{k}_adj_om')
        put(p, f'{k}_m_pub', v / 100 if isinstance(v, (int, float)) else None)
    occ = n.get('occ') or {}
    for k in ('mco', 'ma', 'mis'):
        v = occ.get(k)
        put(p, f'occ_{k}', v / 100 if isinstance(v, (int, float)) else None)
    # adjusted operating income: company definition only where it excludes D&A (the "Adjusted Operating Income" framework);
    # earlier "non-GAAP operating income" measures (before D&A) are kept as a memo and the model applies the current
    # definition (operating income + D&A + restructuring + IS-face other operating items)
    items = [(lab, v) for lab, v in (n.get('adj_oi_items') or []) if v is not None]
    if n.get('adj_oi_pub') is not None and any('depreciation' in lab.lower() for lab, _ in items):
        put(p, 'adj_oi_pub', n['adj_oi_pub'])
        oth, rs, labs = 0.0, 0.0, []
        for lab, v in items:
            l = lab.lower()
            if 'depreciation' in l: continue
            if 'restructuring' in l and 'abandon' not in l: rs += v; continue
            oth += v; labs.append(f'{lab} {v:,.1f}')
        put(p, 'oa_other', oth); put(p, 'oa_restr', rs); put(p, 'oa_other_lab', '; '.join(labs))
    else:
        if n.get('adj_oi_pub') is not None:
            put(p, 'adj_oi_old', n['adj_oi_pub']); put(p, 'adj_oi_old_lab', '; '.join(f'{l} {v:,.1f}' for l, v in items))
        put(p, 'oa_other', sum(v for _, v in ol)); put(p, 'oa_restr', N(i.get('restr'))); put(p, 'oa_model', 1)
        put(p, 'oa_other_lab', '; '.join(f'{l} {v:,.1f}' for l, v in ol if v) + ' (model definition)')
    # adjusted EPS bridge
    sh_d = i.get('sh_d')
    tot, lab, used = bridge_items(p, n, sh_d)
    if n.get('adj_eps_pub') is not None:
        put(p, 'e_pub', n['adj_eps_pub'])
        for c in tot: put(p, f'ea_{c}', tot[c])
        put(p, 'ea_op_lab', '; '.join(lab['op'])); put(p, 'ea_nonop_lab', '; '.join(lab['nonop']))
        if n.get('adj_ni_pub') is not None:
            put(p, 'adj_ni_pub', n['adj_ni_pub'])
        elif sh_d:
            put(p, 'adj_ni_pub', n['adj_eps_pub'] * sh_d); put(p, 'adj_ni_derived', 1)
    else:
        for c in tot: put(p, f'ea_{c}', 0.0)
        put(p, 'adj_none', 1)
    fcf = n.get('fcf_pub')
    if fcf is not None:
        ym = n.get('fcf_pub_ytd_months')
        if ym is None:
            c = r.get('cf') or {}
            if p.isdigit(): ym = 12
            elif c.get('cfo') is not None and c.get('capex') is not None and abs(fcf - (c['cfo'] + c['capex'])) <= 1.5: ym = c.get('ytd_months') or 3 * q
            elif q == 4:
                fyr = (REC.get(str(fy)) or {}).get('ngaap', {}).get('fcf_pub')
                ym = 12 if fyr is not None and abs(fcf - fyr) <= 1.5 else 3
            else: ym = 3
        put(p, 'fcf_pub_ytd', fcf); put(p, 'fcf_pub_ytdm', ym)

def ytd_to_q():
    """discrete quarterly published FCF from year-to-date publications."""
    for y in range(2013, 2027):
        for q in (1, 2, 3, 4):
            p = qk(y, q)
            v, m = x_(p, 'fcf_pub_ytd'), x_(p, 'fcf_pub_ytdm')
            if v is None:
                if q == 4 and x_(str(y), 'fcf_pub_ytd') is not None:
                    s3 = [x_(qk(y, k), 'fcf_pub') for k in (1, 2, 3)]
                    if all(t is not None for t in s3): put(p, 'fcf_pub', x_(str(y), 'fcf_pub_ytd') - sum(s3)); LOG.append(f'{p}: published FCF = FY − 9M')
                continue
            if m == 3: put(p, 'fcf_pub', v)
            else:
                prev = qk(y, q - 1) if q > 1 else None
                pv = x_(prev, 'fcf_pub_ytd') if prev else None
                if pv is not None and x_(prev, 'fcf_pub_ytdm') == m - 3: put(p, 'fcf_pub', v - pv)
                elif q == 4 and m == 12:
                    s3 = [x_(qk(y, k), 'fcf_pub') for k in (1, 2, 3)]
                    if all(t is not None for t in s3): put(p, 'fcf_pub', v - sum(s3))
    for y in range(2006, 2026):
        p = str(y)
        if x_(p, 'fcf_pub_ytd') is not None: put(p, 'fcf_pub', x_(p, 'fcf_pub_ytd'))

def ma_recast_fill():
    """current MA lines for the year before a re-presentation, from the following year's restated comparatives."""
    for p, r in REC.items():
        py = (r.get('py') or {}).get('ma_lines') or {}
        if not py: continue
        fy, q = fyq(p)
        tgt = str(fy - 1) if p.isdigit() else qk(fy - 1, q)
        if tgt not in DATA: continue
        al = map_lines(py, MA_MAP, p + ' py', 'MA')
        cur = {k: v for k, v in al.items() if k in MA_CUR + ('l_ds',)}
        if 'bank' in cur: cur.pop('l_ds', None)
        if not any(k in cur for k in MA_CUR): continue
        def has(k): return x_(tgt, f'r_{k}') is not None or (k == 'l_ds' and x_(tgt, 'r_bank') is not None)
        if all(has(k) for k in cur): continue      # already on this structure (or a finer one) as reported
        tot = x_(tgt, 'ma_ext')
        if tot is None or abs(sum(cur.values()) - tot) > 1.5:
            LOG.append(f'{tgt}: restated MA lines from {p} not used (sum {sum(cur.values()):.1f} vs reported {tot})'); continue
        for k in MA_CUR + ('l_ds',): DATA[tgt]['x'].pop(f'r_{k}', None)
        for k, v in cur.items(): put(tgt, f'r_{k}', v)
        put(tgt, 'ma_recast_from', p); LOG.append(f'{tgt}: current MA lines from the {p} restated comparatives')

def q4_derive():
    keys = ['mis_aoi', 'ma_aoi', 'mis_isr', 'ma_isr', 'mis_rec', 'ma_rec', 'dps', 'r_bank', 'r_ins', 'r_kyc']
    for y in range(2013, 2026):
        p4 = qk(y, 4)
        for k in keys:
            if x_(p4, k) is not None: continue
            fyv = x_(str(y), k); qs = [x_(qk(y, q), k) for q in (1, 2, 3)]
            if fyv is not None and all(v is not None for v in qs):
                put(p4, k, fyv - sum(qs)); LOG.append(f'{p4}: {k} = FY − 9M')

def amort():
    for p in periods():
        fy, q = fyq(p)
        if p.isdigit():
            v = xbrl.value('AmortizationOfIntangibleAssets', fy, 'FY')
        elif q < 4:
            v = xbrl.value('AmortizationOfIntangibleAssets', fy, 'Q', q)
        else:
            f = xbrl.value('AmortizationOfIntangibleAssets', fy, 'FY'); s9 = xbrl.value('AmortizationOfIntangibleAssets', fy, 'YTD', 3)
            v = f - s9 if f is not None and s9 is not None else None
        put(p, 'amort', v)

# ---------------------------------------------------------------- cash flow
def cf_ytd(p):
    r = REC.get(p)
    if not r or not r.get('cf'): return None
    c = r['cf']
    o = {k: N(c.get(k)) for k in ('ni_tot', 'dna', 'sbc', 'deferred_tax', 'cfo', 'capex', 'acquisitions', 'divest', 'cfi', 'buyback', 'dividends', 'cff', 'fx')}
    o['stock'] = N(c.get('stock_plan_proceeds')) + N(c.get('sbc_tax_withholding'))
    o['debt'] = N(c.get('debt_proceeds')) + N(c.get('debt_repay')) + N(c.get('cp_net'))
    o['beg'], o['end'] = c.get('cash_begin'), c.get('cash_end')
    net = o['cfo'] + o['cfi'] + o['cff'] + o['fx']
    if o['beg'] is not None and o['end'] is not None and abs(o['end'] - o['beg'] - net) > 0.6:
        # e.g. 2019 "Reclassification of cash to assets held for sale" (MAKS): carried in the FX & other line
        LOG.append(f'{p}: cash movement outside CFO/CFI/CFF/FX {o["end"] - o["beg"] - net:+.1f} carried in the FX & other line')
        o['fx'] += o['end'] - o['beg'] - net
    o['net'] = o['cfo'] + o['cfi'] + o['cff'] + o['fx']
    return o

def cf_lines(c):
    o = {'cf_ni': c['ni_tot'], 'cf_dna': c['dna'], 'cf_sbc': c['sbc'], 'cf_def': c['deferred_tax']}
    o['cf_wc'] = c['cfo'] - c['ni_tot'] - c['dna'] - c['sbc'] - c['deferred_tax']
    o['cf_cfo'] = c['cfo']; o['cf_capex'] = c['capex']; o['cf_acq'] = c['acquisitions']; o['cf_divest'] = c['divest']
    o['cf_oinv'] = c['cfi'] - c['capex'] - c['acquisitions'] - c['divest']; o['cf_cfi'] = c['cfi']
    o['cf_bb'] = c['buyback']; o['cf_div'] = c['dividends']; o['cf_stock'] = c['stock']; o['cf_debt'] = c['debt']
    o['cf_ofin'] = c['cff'] - c['buyback'] - c['dividends'] - c['stock'] - c['debt']; o['cf_cff'] = c['cff']; o['cf_fx'] = c['fx']
    o['cf_net'] = c['net']
    return o

def do_cf():
    for y in range(2006, 2026):
        a = cf_ytd(str(y))
        if not a: LOG.append(f'{y}: no annual CF'); continue
        for k, v in cf_lines(a).items(): put(str(y), k, v)
        put(str(y), 'cf_beg', a['beg']); put(str(y), 'cf_end', a['end'])
    for y in range(2013, 2027):
        prev = None
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 2: break
            p = qk(y, q)
            cur = cf_ytd(str(y)) if q == 4 else cf_ytd(p)
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
def do_bs(p, src=None):
    r = REC.get(src or p)
    if not r or not r.get('bs'): return
    b = r['bs']
    ta, tca = b['ta'], b['tca']
    cash, sti, ar = b['cash'], N(b.get('sti')), b['ar']
    put(p, 'bs_cash', cash); put(p, 'bs_sti', sti); put(p, 'bs_ar', ar); put(p, 'bs_oca', tca - cash - sti - ar)
    put(p, 'bs_ppe', b['ppe']); put(p, 'bs_gw', b['goodwill']); put(p, 'bs_int', b['intang'])
    put(p, 'bs_onca', ta - tca - b['ppe'] - b['goodwill'] - b['intang']); put(p, 'bs_ta', ta)
    std = N(b.get('cp')) + N(b.get('cltd'))
    put(p, 'bs_ap', b['ap_accr']); put(p, 'bs_std', std); put(p, 'bs_dr', N(b.get('defrev')))
    put(p, 'bs_ocl', b['tcl'] - b['ap_accr'] - std - N(b.get('defrev')))
    put(p, 'bs_ltd', N(b.get('ltd')))
    te = b['te'] if b.get('te') is not None else N(b.get('eq')) + N(b.get('nci'))
    eq = b['eq'] if b.get('eq') is not None else te - N(b.get('nci'))
    put(p, 'bs_ol', b['tle'] - te - b['tcl'] - N(b.get('ltd')))
    put(p, 'bs_eq', eq); put(p, 'bs_nci', te - eq); put(p, 'bs_tle', b['tle'])
    put(p, 'bs_shares', b.get('shares_out'))
    put(p, 'debt_st', N(b.get('cp'))); put(p, 'debt_lt', N(b.get('cltd')) + N(b.get('ltd')))

def rcash():
    for p in periods():
        c, e = x_(p, 'bs_cash'), x_(p, 'cf_end')
        if c is not None and e is not None and abs(e - c) > 0.05:
            put(p, 'bs_rcash', e - c); LOG.append(f'{p}: CF cash − BS cash = {e - c:.1f}')

def run():
    load()
    for p in periods():
        do_pl(p)
        fy, q = fyq(p)
        do_bs(p, str(fy) if (q == 4 and not p.isdigit()) else None)
    ma_recast_fill(); ytd_to_q(); q4_derive(); amort(); do_cf(); rcash()
    for p, v in MAN.get('ppa', {}).items():
        if isinstance(v, dict) and p in DATA: DATA[p]['x']['ppa'] = v
    return DATA

if __name__ == '__main__':
    run()
    for p in periods():
        x = DATA.get(p, {}).get('x', {})
        print(p, {k: round(x[k], 1) if isinstance(x.get(k), float) else x.get(k) for k in
                  ('rev', 'oi', 'ni', 'adj_oi_pub', 'e_pub', 'sh_d', 'mis_aoi', 'ma_aoi', 'amort', 'cf_cfo', 'bs_ta', 'bs_shares')})
    print('\n'.join(LOG))
