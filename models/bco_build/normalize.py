"""Normalise the per-period extraction (data/<period>.json) to flat model keys: DATA[period]['x'][key].

Basis policy (one policy, documented in the README):
  * statements: as originally reported (XBRL value first filed for the period; FY2006-08 from the FY2008 10-K, continuing operations);
  * segments / non-GAAP: as presented in the quarterly tables of the year's fourth-quarter release (2013 and 2019: following
    year's release; 2026: third-quarter 2026 release);
  * Q4 income statement and cash flow = full year - nine months (first-filed values); Q4 diluted shares = 4 x FY - sum(Q1..Q3);
  * cash flow quarters = differences of the year-to-date statements;
  * cash in the cash-flow statement: cash and cash equivalents to 2017; cash, cash equivalents and restricted cash from 2018
    (ASU 2016-18), which is the basis the statements were first filed on.
Signs: costs positive; adjusting items = add-backs (GAAP + items = non-GAAP); cash flow lines signed by their effect on cash."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(HERE, 'manual_items.json'))) if os.path.exists(os.path.join(HERE, 'manual_items.json')) else {}
Y0, YQ, YL, QL = 2006, 2013, 2026, 3            # first annual year, first quarterly year, current year, last actual quarter

def load():
    raw = {}
    for f in os.listdir(os.path.join(HERE, 'data')):
        if f.endswith('.json') and not f.startswith('_'):
            raw[f[:-5]] = json.load(open(os.path.join(HERE, 'data', f)))
    return raw

CAT = [('ven', r'venezuela|ven\.'), ('restr', r'reorganization|restructuring'), ('acq', r'acquisitions and dispositions'), ('arg', r'argentina highly'),
       ('transf', r'transformation'), ('ret', r'retirement plans')]
def cat_of(lab):
    l = lab.lower()
    for k, pat in CAT:
        if re.search(pat, l): return k
    return 'oth'
ITK = ('restr', 'acq', 'arg', 'ven', 'transf', 'ret', 'oth')

def rows_between(rows, starts, ends):
    """rows after the last row whose label is in `starts` and before the first later row whose label is in `ends`"""
    i0 = max((i for i, (l, _) in enumerate(rows) if l in starts), default=None)
    if i0 is None: return None, None, []
    i1 = next((i for i in range(i0 + 1, len(rows)) if rows[i][0] in ends), None)
    if i1 is None: return rows[i0][1], None, []
    return rows[i0][1], rows[i1][1], rows[i0 + 1:i1]

def get(rows, *labels):
    for l, v in rows or []:
        if l in labels: return v
    return None

def seg_keys(x, d, notes):
    for s in d.get('seg', []):
        b = s['basis']; rev = dict(s['rev']); op = s['op']; opd = dict(op)
        if b == 'intl2':
            x.update(i_intl_rev=rev['International'], i_na_rev=rev['North America'], i_intl_op=opd['International'], i_na_op=opd['North America'], i_nonseg=opd['Non-segment'])
            continue
        if b == 'cur4':
            for k, n in (('na', 'North America'), ('la', 'Latin America'), ('eu', 'Europe'), ('row', 'Rest of World')):
                x[k + '_rev'] = rev[n]; x[k + '_op'] = opd.get(n)
            corp = get(op, 'Corporate', 'Corporate expenses')
        elif b == 'three':
            for k, n in (('l3_na', 'North America'), ('l3_sa', 'South America'), ('l3_row', 'Rest of World')):
                x[k + '_rev'] = rev[n]; x[k + '_op'] = opd.get(n)
            corp = get(op, 'Corporate')
        elif b == 'mkts':
            for k, n in (('m_l5', 'Largest 5 Markets'), ('m_gm', 'Global Markets'), ('m_ps', 'Payment Services')):
                x[k + '_rev'] = rev[n]; x[k + '_op'] = opd.get(n)
            for k, n in (('m_us', 'U.S.'), ('m_fr', 'France'), ('m_mx', 'Mexico'), ('m_br', 'Brazil'), ('m_ca', 'Canada')):
                x[k + '_rev'] = rev.get(n); x[k + '_op'] = opd.get(n)
            corp = get(op, 'Corporate items')
        x['seg_basis'] = b
        x['corp'] = corp
        if b == 'cur4': x['corp4'] = corp
        if b == 'three': x['l3_corp'] = corp
        if b == 'mkts': x['m_corp'] = corp
        x['seg_rev'] = get(s['rev'], 'Segment revenues - GAAP and Non-GAAP', 'Segment revenues', 'Revenue - non-GAAP', 'Total revenues', 'Non-GAAP and GAAP')
        segop = get(op, 'Segment operating profit')
        ng = get(op, 'Non-GAAP', 'Operating profit - non-GAAP')
        if ng is None and segop is not None and corp is not None: ng = round(segop + corp, 1)
        x['ng_op_seg'] = ng
        if b == 'cur4': x['seg_rev4'] = x['seg_rev']
        if b == 'three': x['l3_seg_rev'] = x['seg_rev']; x['l3_ng'] = ng
        if b == 'mkts': x['m_seg_rev'] = x['seg_rev']; x['m_ng'] = ng
        # adjusting items: rows between the non-GAAP total (or corporate) and the GAAP total, signed by their effect on GAAP profit
        st = ('Non-GAAP', 'Operating profit - non-GAAP') if get(op, 'Non-GAAP', 'Operating profit - non-GAAP') is not None else ('Corporate expenses',)
        _, gaap, items = rows_between(op, st, ('GAAP', 'Operating profit (loss) - GAAP', 'Operating profit (loss) -GAAP', 'Operating profit'))
        det = d.get('ngaap', {}).get('op_items')
        if det and len(items) <= 1: items = [r for r in det if r[0] not in ('Operating profit',)]
        x['op_seg_tbl'] = gaap
        labs = {k: [] for k in ITK}
        for l, v in items:
            if v is None: continue
            k = cat_of(l) if l != 'Other items not allocated to segments' else 'oth'
            x['it_' + k] = round(x.get('it_' + k, 0.0) - v, 1)
            if abs(v) > 1e-9: labs[k].append(f'{l} {-v:,.1f}')
        for k in ITK:
            if labs[k]: x[f'it_{k}_lab'] = '; '.join(labs[k])
        if items:
            for k in ITK: x.setdefault('it_' + k, 0.0)

def ngaap_keys(x, d):
    ng = d.get('ngaap') or {}
    t = d.get('ngaap_tot')
    gt = d.get('gaap_tbl')
    if gt: x['op_tbl'] = gt['op']; x['inc_tbl'] = gt['inc']; x['eps_cont_tbl'] = gt['eps']
    if t:
        for a, b in (('rev', 'rev_ng_pub'), ('op', 'op_ng_pub'), ('inc', 'inc_ng_pub'), ('eps', 'eps_ng_pub')):
            if t.get(a) is not None: x[b] = t[a]
    if 'rev' in ng:
        x['rev_ng_pub'] = get(ng['rev'], 'Non-GAAP', 'Adjusted non-GAAP') if d['year'] != 2014 and d['year'] != 2013 else get(ng['rev'], 'Non-GAAP and GAAP', 'Non-GAAP')
    if 'op' in ng:
        x['op_ng_pub'] = get(ng['op'], 'Non-GAAP'); x['op_tbl'] = get(ng['op'], 'GAAP')
    if 'eps' in ng:
        x['eps_ng_pub'] = get(ng['eps'], 'Non-GAAP'); x['eps_cont_tbl'] = get(ng['eps'], 'GAAP')
        x['eps_share_adj'] = get(ng['eps'], 'Share adjustment')
        items = [f'{l} {v:+.2f}' for l, v in ng['eps'] if l not in ('GAAP', 'Non-GAAP', 'Non-GAAP margin', 'Adjusted non-GAAP', 'Adjusted non-GAAP margin') and v]
        if items: x['eps_items_lab'] = '; '.join(items)
    if 'inc' in ng:
        x['inc_ng_pub'] = get(ng['inc'], 'Non-GAAP'); x['inc_tbl'] = get(ng['inc'], 'GAAP')
    elif 'recni' in ng:
        x['inc_ng_pub'] = get(ng['recni'], "Income (loss) from continuing operations attributable to Brink's - Non-GAAP")
        x['inc_tbl'] = get(ng['recni'], "Income (loss) from continuing operations attributable to Brink's - GAAP")
        if x['inc_ng_pub'] is None:
            v = [v for l, v in ng['recni'] if l.startswith('Income (loss) from continuing operations attributable')]
            if len(v) == 2: x['inc_tbl'], x['inc_ng_pub'] = v
    if 'ebitda' in ng:
        e = ng['ebitda']
        x['adj_ebitda_pub'] = get(e, 'Adjusted EBITDA')
        eb = get(e, 'EBITDA')
        if eb is not None:
            x['ebitda_pub'] = eb
            x['eb_sbc'] = get(e, 'Share-based compensation'); x['eb_mkt'] = get(e, 'Marketable securities (gain) loss')
            x['eb_disc'] = get(e, 'Discontinued operations - GAAP', 'Discontinued operations')
            i0 = next(i for i, (l, _) in enumerate(e) if l == 'EBITDA')
            its = [(l, v) for l, v in e[i0 + 1:] if l not in ('Adjusted EBITDA', 'Share-based compensation', 'Marketable securities (gain) loss', 'Discontinued operations - GAAP', 'Discontinued operations') and v is not None]
            x['eb_items'] = round(sum(v for _, v in its), 1)
            x['eb_items_lab'] = '; '.join(f'{l} {v:,.1f}' for l, v in its if abs(v) > 1e-9)
            x['eb_da_tbl'] = get(e, 'Depreciation and amortization - GAAP', 'Depreciation and amortization')
            x['eb_int_tbl'] = get(e, 'Interest expense - GAAP', 'Interest expense')
        else:
            x['eb_sbc'] = get(e, 'Share-based compensation - Non-GAAP')
            x['eb_ng_da'] = get(e, 'Depreciation and amortization - Non-GAAP'); x['eb_ng_int'] = get(e, 'Interest expense - Non-GAAP'); x['eb_ng_tax'] = get(e, 'Income tax provision - Non-GAAP')
    if 'da' in ng: x['da_ng_pub'] = get(ng['da'], 'Non-GAAP')

SEGN = {'North America': 'na', 'Latin America': 'la', 'Europe': 'eu', 'Rest of World': 'row'}
def growth_keys(x, d):
    g = d.get('growth')
    if not g: return
    rows = [r for t in g[:1] for r in t]
    cur4 = x.get('seg_basis') == 'cur4' and any(r[1] == 'Europe' for r in rows)
    for sec, lab, v in rows:
        if not sec.lower().startswith('revenue'): continue
        if cur4 and lab in SEGN:
            k = SEGN[lab]; x[f'g_{k}_base'], x[f'g_{k}_org'], x[f'g_{k}_acq'], x[f'g_{k}_fx'], x[f'g_{k}_cur'] = v
        if lab in ('Revenues - GAAP', 'Revenues', 'Total', 'Total revenues') and 'g_ng' not in x:
            x['g_base'], x['g_org'], x['g_acq'], x['g_fx'], x['g_cur'] = v
        if re.match(r'(?i)^(segment revenues|revenues? (- )?non-gaap)', lab):
            x['g_base'], x['g_org'], x['g_acq'], x['g_fx'], x['g_cur'] = v; x['g_ng'] = True
    for k in ('na', 'la', 'eu', 'row', ''):
        p = f'g_{k}_' if k else 'g_'
        if x.get(p + 'base'):
            b = x[p + 'base']
            x[p + 'orgp'] = round(x[p + 'org'] / b, 4); x[p + 'acqp'] = round(x[p + 'acq'] / b, 4); x[p + 'fxp'] = round(x[p + 'fx'] / b, 4); x[p + 'totp'] = round(x[p + 'cur'] / b - 1, 4)
    for sec, lab, v in rows:
        if sec.lower().startswith('operating profit') and lab in ('Operating profit - non-GAAP', 'Non-GAAP operating profit'):
            x['go_base'], x['go_org'], x['go_acq'], x['go_fx'], x['go_cur'] = v

ISF = ('rev', 'cor', 'sga', 'ooi', 'op', 'int', 'ven_decon', 'oth', 'ebt', 'tax', 'cont', 'nci', 'cont_att', 'disc_att', 'ni', 'dps')
CFF = ('ni', 'da', 'sbc', 'def_tax', 'cfo', 'capex', 'acq', 'ppe_sale', 'cfi', 'buyback', 'div', 'div_nci', 'cff', 'fx', 'amort')

def is_keys(x, i):
    for k in ISF + ('eps_d', 'eps_cont_d', 'sh_d', 'sh_b', 'sh_ng'):
        if i.get(k) is not None: x[k] = i[k]
    if 'disc_att' not in x and i.get('disc') is not None: x['disc_att'] = i['disc']
    if 'cont_att' not in x and 'ni' in x: x['cont_att'] = round(x['ni'] - x.get('disc_att', 0.0), 1)

def bs_keys(x, b, year):
    if not b: return
    g = lambda k: b.get(k)
    x['bs_cash'] = g('cash'); x['bs_rcash'] = g('rcash') if year >= 2018 else None
    x['bs_ar'] = g('ar'); x['bs_tca'] = g('tca')
    if g('tca') is not None: x['bs_oca'] = round(g('tca') - g('cash') - (x['bs_rcash'] or 0) - g('ar'), 1)
    x['bs_rou'] = g('rou'); x['bs_ppe'] = g('ppe'); x['bs_gw'] = g('gw'); x['bs_int'] = g('intang'); x['bs_ta'] = g('ta')
    if g('ta') is not None and g('tca') is not None:
        x['bs_onca'] = round(g('ta') - g('tca') - (g('rou') or 0) - g('ppe') - g('gw') - (g('intang') or 0), 1)
    x['bs_stb'] = g('stb'); x['bs_cltd'] = g('cltd')
    x['bs_std'] = round((g('stb') or 0) + (g('cltd') or 0), 1) if g('tcl') is not None else None
    x['bs_ap'] = g('ap'); x['bs_tcl'] = g('tcl')
    if g('tcl') is not None: x['bs_ocl'] = round(g('tcl') - x['bs_std'] - g('ap'), 1)
    x['bs_ltd'] = g('ltd'); x['bs_ret'] = round((g('pension') or 0) + (g('opeb') or 0), 1) if g('tl') is not None else None
    x['bs_lease'] = g('lease'); x['bs_tl'] = g('tl')
    if g('tl') is not None: x['bs_ol'] = round(g('tl') - g('tcl') - g('ltd') - x['bs_ret'] - (g('lease') or 0), 1)
    x['bs_eq'] = g('eq'); x['bs_nci'] = g('nci'); x['bs_teq'] = g('teq'); x['bs_tle'] = g('tle'); x['bs_shares'] = g('shares')
    x['bs_cash_cf'] = g('cash_cf')
    for k in [k for k, v in x.items() if k.startswith('bs_') and v is None]: del x[k]

def cf_model(x, c):
    """flat cash-flow keys from a discrete-period dict c (XBRL signs: payments positive)"""
    if not c or c.get('cfo') is None: return
    n = lambda k: c.get(k) or 0.0
    x['cf_ni'] = c.get('ni'); x['cf_da'] = c.get('da'); x['cf_sbc'] = c.get('sbc'); x['cf_def'] = c.get('def_tax'); x['cf_cfo'] = c['cfo']
    x['cf_oop'] = round(c['cfo'] - n('ni') - n('da') - n('sbc') - n('def_tax'), 1)
    x['cf_capex'] = -n('capex'); x['cf_acq'] = -n('acq'); x['cf_ppe'] = n('ppe_sale'); x['cf_cfi'] = c.get('cfi')
    if c.get('cfi') is not None: x['cf_oinv'] = round(c['cfi'] + n('capex') + n('acq') - n('ppe_sale'), 1)
    x['cf_bb'] = -n('buyback'); x['cf_div'] = -n('div'); x['cf_divnci'] = -n('div_nci'); x['cf_cff'] = c.get('cff')
    if c.get('cff') is not None: x['cf_ofin'] = round(c['cff'] + n('buyback') + n('div') + n('div_nci'), 1)
    x['cf_fx'] = n('fx')
    if c.get('amort') is not None: x['cf_amort'] = c['amort']
    for k in [k for k, v in x.items() if k.startswith('cf_') and v is None]: del x[k]

def diff(a, b, keys):
    out = {}
    for k in keys:
        if a.get(k) is None: continue
        out[k] = round(a[k] - (b.get(k) or 0.0), 2 if k == 'dps' else 1) if b is not None else a[k]
    return out

def run():
    raw = load(); DATA = {}
    def cash_cf(per, year):
        b = raw.get(per, {}).get('bs') or {}
        return b.get('cash_cf') if year >= 2018 else b.get('cash')
    for per, d in raw.items():
        y, q = d['year'], d['quarter']
        x = {}; notes = list(d.get('notes', []))
        seg_keys(x, d, notes); ngaap_keys(x, d); growth_keys(x, d)
        if q is None:
            is_keys(x, d.get('is') or {})
            c = d.get('cf') or {}
            cf_model(x, c)
            if d.get('extra'):
                x['cf_da'] = d['extra'].get('da'); x['capex_memo'] = d['extra'].get('capex')
            bs_keys(x, d.get('bs'), y)
            if c.get('cash_end') is not None: x['cf_beg'], x['cf_end'] = c.get('cash_beg'), c['cash_end']
            if y == 2009: x['cf_beg'] = raw['2008']['bs']['cash']
            f = d.get('fcf')
            if f: x['fcf_pub'] = f['rows'][-1][1]
        elif q < 4:
            is_keys(x, d.get('is') or {})
            c = d.get('cf') or {}
            prev = raw.get(f'Q{q - 1}-{str(y)[2:]}', {}).get('cf') if q > 1 else None
            cf_model(x, diff(c, prev, CFF) if q > 1 else c)
            bs_keys(x, d.get('bs'), y)
            if 'cf_cfo' in x:
                x['cf_end'] = c.get('cash_end'); x['cf_beg'] = c.get('cash_beg') if q == 1 else (prev or {}).get('cash_end')
            f = d.get('fcf'); pf = raw.get(f'Q{q - 1}-{str(y)[2:]}', {}).get('fcf') if q > 1 else None
            if f and (q == 1 or pf): x['fcf_pub'] = round(f['rows'][-1][1] - (pf['rows'][-1][1] if q > 1 else 0.0), 1)
        else:
            fy = raw[str(y)]; q3 = raw[f'Q3-{str(y)[2:]}']
            qs = [raw[f'Q{k}-{str(y)[2:]}'] for k in (1, 2, 3)]
            i = {}
            for k in ISF:
                if fy['is'].get(k) is None: continue
                i[k] = round(fy['is'][k] - sum((qq['is'].get(k) or 0.0) for qq in qs), 2 if k == 'dps' else 1)
            if fy['is'].get('sh_d') is not None and all(qq['is'].get('sh_d') for qq in qs):
                i['sh_d'] = round(4 * fy['is']['sh_d'] - sum(qq['is']['sh_d'] for qq in qs), 1); i['sh_b'] = round(4 * fy['is']['sh_b'] - sum(qq['is']['sh_b'] for qq in qs), 1)
            is_keys(x, i)
            x['disc_att'] = round((fy['is'].get('disc_att') if fy['is'].get('disc_att') is not None else fy['is'].get('disc') or 0.0) - sum((qq['is'].get('disc_att') if qq['is'].get('disc_att') is not None else qq['is'].get('disc') or 0.0) for qq in qs), 1)
            x['cont_att'] = round(fy['is']['cont_att'] - sum(qq['is']['cont_att'] for qq in qs), 1) if all(qq['is'].get('cont_att') is not None for qq in qs) and fy['is'].get('cont_att') is not None else x.get('cont_att')
            if x.get('eps_cont_tbl') is not None: x['eps_cont_d'] = x['eps_cont_tbl']
            cf_model(x, diff(fy['cf'], q3['cf'], CFF))
            bs_keys(x, fy.get('bs'), y)
            x['cf_end'] = fy['cf'].get('cash_end'); x['cf_beg'] = q3['cf'].get('cash_end')
            if fy['is'].get('sh_ng') is not None and all(qq['is'].get('sh_ng') for qq in qs): x['sh_ng'] = round(4 * fy['is']['sh_ng'] - sum(qq['is']['sh_ng'] for qq in qs), 1)
            f = fy.get('fcf'); pf = q3.get('fcf')
            if f and pf: x['fcf_pub'] = round(f['rows'][-1][1] - pf['rows'][-1][1], 1)
            notes.append('Q4 income statement and cash flow = full year − nine months; Q4 weighted shares = 4 × FY − Σ Q1–Q3.')
        # diluted shares used by the company for non-GAAP EPS: GAAP diluted shares, except in GAAP-loss periods (dilutive awards included)
        if x.get('eps_ng_pub') and x.get('inc_ng_pub') is not None and x.get('sh_d'):
            if abs(x['inc_ng_pub'] / x['sh_d'] - x['eps_ng_pub']) > 0.0149 and (x.get('cont_att', 1) < 0 or q == 4 or (q is None and x.get('cont_att', 1) < 0)):
                x['sh_ng'] = round(x['inc_ng_pub'] / x['eps_ng_pub'], 1)
                x['sh_ng_note'] = 'GAAP loss period (or derived Q4): diluted shares implied by published non-GAAP income ÷ published non-GAAP EPS (the company includes dilutive awards that GAAP excludes in a loss period).'
            else: x['sh_ng'] = x['sh_d']
        if q and all(x.get(k) is not None for k in ('cf_beg', 'cf_end', 'cf_cfo', 'cf_cfi', 'cf_cff')):
            dd = round(x['cf_end'] - x['cf_beg'] - x['cf_cfo'] - x['cf_cfi'] - x['cf_cff'] - x.get('cf_fx', 0.0), 1)
            if abs(dd) > 0.3:
                x['cf_repr'] = dd
                notes.append(f'Opening cash re-presented between filings: {dd} (the year-to-date statement of this quarter opens from a different balance than the previous quarter\'s statement closed on).')
        if x.get('bs_cash') is not None and x.get('cf_end') is not None:
            dd = round(x['bs_cash'] + (x.get('bs_rcash') or 0.0) - x['cf_end'], 1)
            if abs(dd) > 0.25: x['bs_cash_diff'] = dd
        if d.get('recast'): x['recast_note'] = d['recast']['reason'] + ' Originally reported: revenues {rev}, operating profit {op}.'.format(**d['recast']['original'])
        if x.get('adj_ebitda_pub') is not None and x.get('ebitda_pub') is None and all(k in x for k in ('ni', 'int', 'tax', 'cf_da')):
            x['eb_items'] = round(x['adj_ebitda_pub'] - (x['ni'] + x['int'] + x['tax'] + x['cf_da']) - (x.get('eb_sbc') or 0.0) + x.get('disc_att', 0.0), 1)
            x['eb_items_lab'] = ('Derived: published adjusted EBITDA − (net income attributable to Brink\'s + interest expense + income taxes + D&A) − share-based compensation − loss from discontinued operations. '
                                 'In 2016–17 the company built adjusted EBITDA from non-GAAP income from continuing operations + non-GAAP interest, taxes and D&A (+ share-based compensation from 2017).')
        if 'op' in x and 'ng_op_seg' in x and 'it_restr' not in x and x.get('op_ng_pub') is None: pass
        if 'op' in x and x.get('op_ng_pub') is not None and 'it_restr' not in x:      # totals-only periods (2009-2013): one total, shown in "other"
            x['it_oth'] = round(x['op_ng_pub'] - x['op'], 1)
            for k in ITK: x.setdefault('it_' + k, 0.0)
            x['it_oth_lab'] = 'Total of the company\'s adjusting items (published non-GAAP operating profit − GAAP operating profit); the item detail is in the column-format reconciliation of the release.'
        x = {k: v for k, v in x.items() if v is not None}
        DATA[per] = {'x': x, 'notes': notes, 'sources': d.get('sources', [])}
    # full-year growth decomposition = sum of the four quarterly tables (whole $m), where all four exist
    for y in range(YQ, YL):
        qs = [DATA.get(f'Q{q}-{str(y)[2:]}', {}).get('x', {}) for q in (1, 2, 3, 4)]
        fx_ = DATA[str(y)]['x']
        for k in ('na', 'la', 'eu', 'row', ''):
            p = f'g_{k}_' if k else 'g_'
            if all(q.get(p + 'base') for q in qs):
                b = sum(q[p + 'base'] for q in qs)
                for a in ('org', 'acq', 'fx'): fx_[p + a + 'p'] = round(sum(q[p + a] for q in qs) / b, 4)
                fx_[p + 'totp'] = round(sum(q[p + 'cur'] for q in qs) / b - 1, 4)
                fx_['g_sumq'] = True
    return DATA

if __name__ == '__main__':
    D = run()
    for p in ('2008', '2012', 'Q4-25', 'Q3-26'): print(p, json.dumps(D[p]['x'])[:1500])
