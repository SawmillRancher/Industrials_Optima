"""Harmonise the extraction JSON into the model's data keys and run cross-checks (ODFL).

- Shares / per-share already restated to the current basis in extract.py (3-for-2 Aug-2010, Sep-2012, Mar-2020; 2-for-1 Mar-2024).
- Operating statistics: tons / shipments on the published basis (total tons & shipments to 2013, LTL from 2014); tons per day
  derived from tons ÷ work days where not published; work days from the ODFL calendar (workdays.py) where not published (to 2011).
- Cash flow: quarterly records carry year-to-date statements; discrete quarters derived (Q4 = FY − 9M); derived 'other'
  lines keep each section summing to its published subtotal.
- Bridges: company-identified one-off items (manual_items.json) + net (gain) loss on disposal of property & equipment (cash-flow
  statement) feed the model-defined Adjusted EBITDA / adjusted EPS bridges; XBRL values are attached for check rows.
"""
import json
import workdays
from fw import DATA, num, load_data

def N(x): return num(x) or 0.0
def r6(x): return None if x is None else round(x, 6)
LOG = []
CF_CORE = ['net_income', 'dda', 'gain_loss', 'cfo', 'capex', 'proceeds_disp', 'cfi', 'debt_proceeds', 'debt_repay', 'buyback',
           'dividends', 'cff', 'net_change']
CF_OPT = ['deferred_tax', 'sbc', 'wc_change', 'sti_net', 'acquisitions']
PERIODS = lambda: [k for k, d in DATA.items() if isinstance(d, dict) and 'period' in d]

def qkeys(y): return [f'Q{q}-{str(y)[2:]}' for q in (1, 2, 3, 4)]
def pinfo(k):
    if k.startswith('Q'): return int('20' + k[3:]), int(k[1])
    return int(k), None

def stats():
    for k in PERIODS():
        d = DATA[k]; s = d.get('stats') or {}
        if not s: continue
        y, q = pinfo(k)
        st = {}
        days = num(s.get('work_days'))
        if days is not None and days < (55 if q else 240): days = None   # '—%' change cell mis-read as 0
        st['days_calc'] = days is None
        if days is None: days = workdays.quarter(y, q) if q else workdays.year(y)
        st['days'] = days
        ltl = num(s.get('ltl_tons')) is not None
        st['basis_ltl'] = ltl
        st['tons'] = num(s.get('ltl_tons')) if ltl else num(s.get('total_tons'))
        st['ship'] = num(s.get('ltl_ship')) if ltl else num(s.get('total_ship'))
        tpd, spd = num(s.get('tons_day')), num(s.get('ship_day'))
        if tpd is not None and tpd < 1000: tpd *= 1000   # some releases show tons / shipments per day in thousands
        if spd is not None and spd < 1000: spd *= 1000
        st['tpd'] = tpd or (round(st['tons'] * 1000 / days, 3) if st['tons'] else None)
        st['spd'] = spd or (round(st['ship'] * 1000 / days, 3) if st['ship'] else None)
        for a in ('rev_cwt', 'rev_cwt_xf', 'rev_shp', 'rev_shp_xf', 'wps', 'loh', 'miles', 'emp_avg', 'or_pub'):
            st[a] = num(s.get(a))
        d['st'] = st

def cf_derived(cf):
    o = {k: num(cf.get(k)) for k in CF_CORE + CF_OPT}
    if o['cfo'] is not None:
        o['oth'] = N(o['cfo']) - N(o['net_income']) - N(o['dda']) - N(o['gain_loss']) - N(o['deferred_tax']) - N(o['sbc']) - N(o['wc_change'])
    if o['cfi'] is not None:
        o['oinv'] = N(o['cfi']) - N(o['capex']) - N(o['proceeds_disp']) - N(o['sti_net']) - N(o['acquisitions'])
    if o['cff'] is not None:
        o['ofin'] = N(o['cff']) - N(o['debt_proceeds']) - N(o['debt_repay']) - N(o['buyback']) - N(o['dividends'])
    o['cash_begin'] = num(cf.get('cash_begin')); o['cash_end'] = num(cf.get('cash_end'))
    o['ytd'] = num(cf.get('ytd_months'))
    return o

def build_cfq():
    for k in PERIODS():
        if not k.startswith('Q') and DATA[k].get('cf'):
            DATA[k]['cfq'] = {a: r6(b) for a, b in cf_derived(DATA[k]['cf']).items() if a != 'ytd'}
    for y in range(2013, 2027):
        prev = None
        for qi, k in enumerate(qkeys(y), start=1):
            d = DATA.get(k)
            if not d or not d.get('cf'): prev = None; continue
            cur = cf_derived(d['cf'])
            if cur['ytd'] != 3 * qi: LOG.append(f'{k}: cf ytd_months {cur["ytd"]}')
            if qi == 1:
                q = dict(cur)
            elif prev is None:
                LOG.append(f'{k}: no prior YTD cash flow'); prev = cur; continue
            else:
                q = {}
                for a in CF_CORE + CF_OPT + ['oth', 'oinv', 'ofin']:
                    q[a] = None if cur.get(a) is None and prev.get(a) is None else N(cur.get(a)) - N(prev.get(a))
                q['cash_begin'], q['cash_end'] = prev['cash_end'], cur['cash_end']
            q.pop('ytd', None)
            d['cfq'] = {a: r6(b) for a, b in q.items()}
            prev = cur

def build_bsx():
    for k in PERIODS():
        bs = DATA[k].get('bs')
        if not bs: continue
        g = lambda f: num(bs.get(f))
        x = {}
        x['oca'] = g('total_current_assets') - N(g('cash')) - N(g('sti')) - N(g('receivables'))
        x['onca'] = g('total_assets') - g('total_current_assets') - N(g('ppe'))
        x['ocl'] = g('total_current_liab') - N(g('ap')) - N(g('accrued_comp')) - N(g('claims_cur')) - N(g('current_debt'))
        x['oncl'] = g('total_liabilities') - g('total_current_liab') - N(g('ltd')) - N(g('deferred_tax'))
        x['cap'] = N(g('common')) + N(g('apic'))
        x['eq_chk'] = round(g('total_equity') - x['cap'] - N(g('retained')), 6)
        if abs(x['eq_chk']) > 0.002: LOG.append(f'{k}: equity components residual {x["eq_chk"]}')
        x['debt'] = N(g('current_debt')) + N(g('ltd'))
        x['gwi'] = (N(g('goodwill')) + N(g('intangibles'))) if (g('goodwill') is not None or g('intangibles') is not None) else None
        DATA[k]['bsx'] = {a: r6(b) for a, b in x.items()}

def build_bridges():
    man = DATA.get('manual_items', {}).get('items', [])
    xb = DATA.get('xbrl', {})
    for k in PERIODS():
        d = DATA[k]; x = d.setdefault('x', {})
        its = [m for m in man if m['period'] == k]
        x['op_items'] = sum(N(m.get('op')) for m in its) if any('op' in m for m in its) else None
        x['op_labels'] = ' | '.join(f'{m["label"]}: {m["op"]:+.1f}' for m in its if 'op' in m) or None
        x['disc_tax'] = sum(N(m.get('disc_tax')) for m in its) if any('disc_tax' in m for m in its) else None
        x['disc_labels'] = ' | '.join(f'{m["label"]}: {m["disc_tax"]:+.1f}' for m in its if 'disc_tax' in m) or None
        cq = d.get('cfq') or {}
        x['gain'] = cq.get('gain_loss')
        xv = xb.get(k) or {}
        x['xb_ni'], x['xb_op'], x['xb_dda'], x['xb_rev'], x['xb_ta'] = (xv.get('ni'), xv.get('op'), xv.get('dda'), xv.get('rev'), xv.get('ta'))
        # XBRL sign convention for GainLossOnSaleOfPropertyPlantEquipment flips between filings (loss-positive 2012-18, gain-positive
        # from 2019): compare on absolute values; Q4-18 (FY − 9M across the change) is not comparable.
        x['xb_gain'] = None if (xv.get('gain') is None or k == 'Q4-18') else abs(xv['gain'])
        i = d.get('is') or {}
        x['int_net'] = i.get('int_net')
        if i and i.get('dps') is None and xv.get('dps') is not None:
            i['dps'] = round(xv['dps'], 6); i['dps_src'] = 'XBRL CommonStockDividendsPerShareDeclared (10-Q / 10-K)'

def checks():
    for k in sorted(PERIODS()):
        d = DATA[k]; i = d.get('is') or {}; x = d.get('x') or {}; cq = d.get('cfq') or {}
        for a, b in (('net_income', 'xb_ni'), ('op_income', 'xb_op'), ('revenue', 'xb_rev')):
            if i.get(a) is not None and x.get(b) is not None and abs(i[a] - x[b]) > 0.002:
                LOG.append(f'{k}: {a} {i[a]} vs XBRL {x[b]:.3f}')
        if x.get('xb_gain') is not None and x.get('gain') is not None and abs(abs(x['gain']) - x['xb_gain']) > 0.002:
            LOG.append(f'{k}: gain {x["gain"]} vs XBRL {x["xb_gain"]:.3f}')
        if i.get('dda') is not None and cq.get('dda') is not None and abs(i['dda'] - cq['dda']) > 0.05:
            LOG.append(f'{k}: IS D&A {i["dda"]} vs CF D&A {cq["dda"]:.3f}')
        if cq.get('cfo') is not None:
            t = N(cq['cfo']) + N(cq['cfi']) + N(cq['cff']) - N(cq['net_change'])
            if abs(t) > 0.002: LOG.append(f'{k}: CF sections {t:+.3f}')

def run():
    load_data()
    stats(); build_cfq(); build_bsx(); build_bridges(); checks()

if __name__ == '__main__':
    run()
    print('\n'.join(LOG) or 'no issues')
