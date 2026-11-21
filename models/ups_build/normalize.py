"""Normalise the per-period extraction (data/<period>.json) into flat model keys: DATA[period]['x'][key].

Basis policy: AS ORIGINALLY REPORTED. Each period comes from its own earnings release (segments, operating data, adjusted
measures) and its own Form 10-K / 10-Q (operating-expense detail, balance sheet, cash flow). Nothing is recast:
  * FY2006-FY2010 are on the pre-2011 pension accounting (UPS adopted mark-to-market pension accounting in Q4-2011 and recast
    2007-2011 in the 8-K of 27-Jan-2012; the recast figures are not used);
  * FY2017 and earlier are before ASU 2017-07 (non-service pension cost inside operating expenses; adopted Q1-2018);
  * Supply Chain & Freight was renamed Supply Chain Solutions in Q2-2021 (UPS Freight sold 30-Apr-2021).
Derivations (all stated in the workbook notes): discrete quarterly cash flow = year-to-date differences; Q4 operating-expense
detail = fiscal year (10-K) - nine months (Q3 10-Q) where the release has no detail table; quarterly dividends per share =
year-to-date declared differences; 'other' balance-sheet / cash-flow lines are residuals so that reported totals tie."""
import json, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(BASE, 'manual_items.json')))
SEG = ('us', 'intl', 'scs')
YEARS = list(range(2006, 2026))
QUARTERS = [(y, q) for y in range(2013, 2027) for q in (1, 2, 3, 4) if (y, q) <= (2026, 3)]


def qk(y, q): return f'Q{q}-{str(y)[2:]}'


def load():
    return {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(BASE, 'data', '*.json')) if not os.path.basename(f).startswith('_')}


def n0(v): return 0.0 if v is None else v


def base_x(rec):
    """Release data of one record -> flat keys."""
    x = {}
    i = rec.get('is', {}); o = rec.get('ops', {})
    for k in ('rev', 'op', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d', 'sh_b', 'sh_d', 'int_exp', 'opex'):
        if k in i: x[k] = i[k]
    for s in SEG:
        for k in ('rev', 'op'):
            if f'{k}_{s}' in i: x[f'{k}_{s}'] = i[f'{k}_{s}']
    # other income: other pension income (expense) (separate from Q1-2018, ASU 2017-07) + investment income and other
    if 'inv_inc' in i:
        x['inv_inc'] = i['inv_inc']
        if 'pen_inc' in i: x['pen_inc'] = i['pen_inc']
        x['oth_inc'] = i['inv_inc'] + n0(i.get('pen_inc'))
    # company adjusted measures: published only in periods with adjusting items; otherwise adjusted = GAAP (flag adj_pub = 0)
    pub = 'a_op' in i or 'a_ni' in i
    x['adj_pub'] = 1 if pub else 0
    for s in SEG:
        x[f'aop_{s}'] = i.get(f'a_op_{s}', i.get(f'op_{s}')) if pub else i.get(f'op_{s}')
    if pub:
        x['aop_pub'] = i.get('a_op', i.get('op'))
        x['a_ebt'] = i.get('a_ebt', i.get('ebt'))
        x['a_ni_pub'] = i.get('a_ni', i.get('ni'))
        x['a_eps_pub'] = i.get('a_eps_d', i.get('eps_d'))
        x['oa_nonop'] = round((x['a_ebt'] - i['ebt']) - (x['aop_pub'] - i['op']), 4)   # items below operating profit (pension mark-to-market from 2018)
    else:
        x['oa_nonop'] = 0.0
    for s in SEG:
        x[f'oa_{s}'] = round(x[f'aop_{s}'] - i[f'op_{s}'], 4)              # adjusting items in segment operating profit (added back)
    # company wording of the adjustments: verbatim release footnotes only (reconciliation schedule footnotes, else the Selected Financial Data footnotes)
    lab = rec.get('adj_notes') or i.get('a_footnotes')
    if lab and pub: x['oa_lab'] = lab[:1800]
    # operating data
    for k, v in o.items(): x['o_' + k] = v
    if 'o_rev_scs_fwdlog' in x and 'o_rev_scs_fwd' not in x:
        pass
    return x


def cf_lines(c):
    """Year-to-date cash-flow record -> model lines (others derived so that the subtotals tie to reported)."""
    d = {}
    d['cf_ni'] = c.get('ni'); d['cf_da'] = c.get('da')
    d['cf_pen'] = n0(c.get('pen_exp')) + n0(c.get('pen_contrib')) if ('pen_exp' in c or 'pen_contrib' in c) else None
    d['cf_pen_contrib'] = c.get('pen_contrib')
    d['cf_def'] = c.get('def_tax'); d['cf_sbc'] = c.get('sbc')
    d['cf_cfo'] = c.get('cfo')
    d['cf_wc'] = c['cfo'] - sum(n0(d[k]) for k in ('cf_ni', 'cf_da', 'cf_pen', 'cf_def', 'cf_sbc'))
    d['cf_capex'] = c.get('capex'); d['cf_disp'] = n0(c.get('disp'))
    d['cf_acq'] = n0(c.get('acq'))
    d['cf_ms'] = n0(c.get('ms_buy')) + n0(c.get('ms_sell'))
    d['cf_finrec'] = n0(c.get('fin_rec'))
    d['cf_cfi'] = c.get('cfi')
    d['cf_oinv'] = c['cfi'] - (c['capex'] + d['cf_disp'] + d['cf_acq'] + d['cf_ms'] + d['cf_finrec'])
    d['cf_oinv_pub'] = c.get('oth_inv')
    d['cf_debt'] = n0(c.get('st_debt')) + n0(c.get('debt_in')) + n0(c.get('debt_out'))
    d['cf_bb'] = n0(c.get('bb')); d['cf_iss'] = n0(c.get('iss')); d['cf_div'] = c.get('div')
    cff = c.get('cff')
    if cff is None: cff = c['net'] - c['cfo'] - c['cfi'] - n0(c.get('fx'))
    d['cf_cff'] = cff
    d['cf_ofin'] = cff - (d['cf_debt'] + d['cf_bb'] + d['cf_iss'] + n0(d['cf_div']))
    d['cf_fx'] = n0(c.get('fx')); d['cf_net'] = c.get('net')
    return d


FLOW = ('cf_ni', 'cf_da', 'cf_pen', 'cf_pen_contrib', 'cf_def', 'cf_sbc', 'cf_cfo', 'cf_wc', 'cf_capex', 'cf_disp', 'cf_acq', 'cf_ms', 'cf_finrec', 'cf_cfi',
        'cf_oinv', 'cf_oinv_pub', 'cf_debt', 'cf_bb', 'cf_iss', 'cf_div', 'cf_cff', 'cf_ofin', 'cf_fx', 'cf_net')
OPX = ('comp', 'rm', 'da', 'pt', 'fuel', 'occ', 'othx')


def bs_lines(b):
    d = {}
    d['bs_cash'] = b['cash']; d['bs_ms'] = n0(b.get('ms')); d['bs_ar'] = b['ar']
    d['bs_oca'] = b['tca'] - b['cash'] - d['bs_ms'] - b['ar']
    d['bs_ppe'] = b['ppe']; d['bs_rou'] = n0(b.get('rou')); d['bs_gw'] = b['gw']; d['bs_int'] = b['intang']
    d['bs_onca'] = b['ta'] - b['tca'] - b['ppe'] - d['bs_rou'] - b['gw'] - b['intang']
    d['bs_ta'] = b['ta']
    d['bs_cdebt'] = b['cur_debt']; d['bs_clease'] = n0(b.get('cur_lease')); d['bs_ap'] = b['ap']; d['bs_wages'] = b['wages']
    d['bs_ocl'] = b['tcl'] - b['cur_debt'] - d['bs_clease'] - b['ap'] - b['wages']
    d['bs_ltd'] = b['ltd']; d['bs_nclease'] = n0(b.get('nc_lease')); d['bs_pension'] = b['pension']
    teq = b['teq']
    d['bs_nci'] = n0(b.get('nci')); d['bs_eq'] = b.get('eq', teq - d['bs_nci'])
    d['bs_dtl'] = n0(b.get('dtl'))
    d['bs_ol'] = b['tle'] - teq - b['tcl'] - b['ltd'] - d['bs_nclease'] - b['pension'] - d['bs_dtl']
    d['bs_tle'] = b['tle']
    d['bs_shares'] = n0(b.get('sh_a')) + n0(b.get('sh_b'))
    d['bs_sh_a'] = b.get('sh_a'); d['bs_sh_b'] = b.get('sh_b')
    d['debt'] = b['cur_debt'] + b['ltd']
    return d


def run():
    raw = load()
    D = {}
    # ---- annual
    for y in YEARS:
        r = raw[str(y)]; x = base_x(r)
        f = r.get('face_is', {})
        for k in OPX:
            if k in f: x['x_' + k] = f[k]
        c = r['cf']
        x.update({k: v for k, v in cf_lines(c).items() if v is not None})
        x['cf_beg'] = c['beg']; x['cf_end'] = c['end']
        x.update(bs_lines(r['bs']))
        x['dps'] = r.get('dps_declared_ytd')
        if r.get('ngaap', {}).get('fcf_pub_ytd') is not None: x['fcf_pub'] = r['ngaap']['fcf_pub_ytd']
        D[str(y)] = {'x': x, 'sources': r['sources'], 'notes': r.get('notes', [])}
    # ---- quarters
    for y, q in QUARTERS:
        r = raw[qk(y, q)]; x = base_x(r)
        prev = raw.get(qk(y, q - 1)) if q > 1 else None
        # operating-expense detail: release table (2021+) or the 10-Q three-month column; Q4 = FY (10-K) - nine months (Q3 10-Q)
        if q < 4:
            f = r.get('opex') or {}
            g = r.get('face_is', {})
            for k in OPX:
                v = f.get(k, g.get(k))
                if v is not None: x['x_' + k] = v
        else:
            f = r.get('opex') or {}
            fy = r.get('face_is', {}); n9 = prev.get('face_is_ytd', {}) if prev else {}
            for k in OPX:
                if k in f: x['x_' + k] = f[k]
                elif k in fy and k in n9: x['x_' + k] = fy[k] - n9[k]
        # cash flow: discrete = year to date - prior year to date
        cur = cf_lines(r['cf']); pc = cf_lines(prev['cf']) if prev else None
        for k in FLOW:
            if cur.get(k) is None: continue
            x[k] = cur[k] - (n0(pc.get(k)) if pc else 0.0)
        x['cf_beg'] = prev['cf']['end'] if prev else r['cf']['beg']
        x['cf_end'] = r['cf']['end']
        x.update(bs_lines(r['bs']))
        dy = r.get('dps_declared_ytd'); dp = prev.get('dps_declared_ytd') if prev else 0.0
        if dy is not None and dp is not None: x['dps'] = round(dy - dp, 4)
        fp = r.get('ngaap', {}).get('fcf_pub_ytd'); fpp = (prev.get('ngaap', {}).get('fcf_pub_ytd') if prev else 0.0)
        if fp is not None and fpp is not None: x['fcf_pub'] = fp - fpp
        D[qk(y, q)] = {'x': x, 'sources': r['sources'], 'notes': r.get('notes', [])}
    # ---- FY2020 / Q4-20: the 10-K wins. The release (2-Feb-2021) recorded a $556m UPS Freight held-for-sale impairment; the 10-K
    #      (22-Feb-2021) recorded $686m. Operating profit, tax, net income and EPS take the 10-K values; adjusted measures are unchanged.
    r20 = raw['2020']; f = r20['face_is']; x = D['2020']['x']; old = dict(x)
    for k in ('op', 'opex', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d'): x[k] = f[k]
    x['op_scs'] = x['op'] - x['op_us'] - x['op_intl']; x['oa_scs'] = round(x['aop_scs'] - x['op_scs'], 4)
    q4 = D['Q4-20']['x']
    for k in ('op', 'opex', 'ebt', 'tax', 'ni', 'op_scs'):
        q4[k] = round(q4[k] + (x[k] - old[k]), 4)
    q4['oa_scs'] = round(q4['aop_scs'] - q4['op_scs'], 4)
    q4['eps_d'] = q4['eps_b'] = round(q4['ni'] / q4['sh_d'], 2)
    D['2020']['corr'] = D['Q4-20']['corr'] = ('The 10-K wins: the Q4-2020 release (2-Feb-2021) recorded a $556m UPS Freight held-for-sale impairment; the 2020 Form 10-K '
        f'(22-Feb-2021) recorded $686m. Release values: FY operating profit {old["op"]:,.0f}, net income {old["ni"]:,.0f}, diluted EPS {old["eps_d"]:.2f}; '
        '10-K: 7,684 / 1,343 / 1.54. Q4-2020 = 10-K fiscal year less nine months as reported (Q4 EPS = net loss / weighted shares). Adjusted measures are unchanged.')
    # ---- Q1-Q3 2024 segments: recast basis from the 2025 releases' prior-year columns. The Q4-2024 release moved air cargo (U.S. Domestic
    #      'Cargo and Other') from Supply Chain Solutions to U.S. Domestic Package and presented FY2024 on that basis.
    for q in (1, 2, 3):
        py = raw[qk(2025, q)].get('py', {}); x = D[qk(2024, q)]['x']; orig = {k: x.get(k) for k in ('rev_us', 'rev_scs', 'op_us', 'op_scs')}
        pi = py.get('is', {})
        for s in ('us', 'scs'):
            x[f'rev_{s}'] = pi[f'rev_{s}']; x[f'op_{s}'] = pi[f'op_{s}']
            if f'a_op_{s}' in pi: x[f'aop_{s}'] = pi[f'a_op_{s}']
            x[f'oa_{s}'] = round(x.get(f'aop_{s}', x[f'op_{s}']) - x[f'op_{s}'], 4)
        for k, v in py.get('ops', {}).items():
            if k.startswith(('rev_us', 'rev_scs')): x['o_' + k] = v
        D[qk(2024, q)]['recast'] = ('Recast basis (prior-year column of the 2025 release): air cargo moved from Supply Chain Solutions to U.S. Domestic Package in the Q4-2024 '
            f'release. As originally reported: U.S. Domestic revenue {orig["rev_us"]:,.0f} / operating profit {orig["op_us"]:,.0f}; Supply Chain Solutions '
            f'{orig["rev_scs"]:,.0f} / {orig["op_scs"]:,.0f}.')
    # ---- business-divestiture proceeds: the cash-flow line 'proceeds from disposal of businesses, PP&E' less the PP&E disposals in the
    #      company's free-cash-flow reconciliation (UPS Freight Q2-2021 $848m; Coyote Q3-2024 $1,002m). Year to date -> discrete.
    def divest_ytd(r):
        d_ = r.get('ngaap', {}).get('fcf_disp_ytd'); c_ = r['cf'].get('disp')
        return (c_ - d_) if (d_ is not None and c_ is not None and abs(c_ - d_) > 100) else 0.0
    for y in YEARS:
        v = divest_ytd(raw[str(y)]); x = D[str(y)]['x']; x['cf_divest'] = v; x['cf_disp'] -= v
    for y, q in QUARTERS:
        v = divest_ytd(raw[qk(y, q)]) - (divest_ytd(raw[qk(y, q - 1)]) if q > 1 else 0.0)
        x = D[qk(y, q)]['x']; x['cf_divest'] = v; x['cf_disp'] -= v
    # ---- adjusted diluted shares: the company's own count where it says so (GAAP-loss quarters), else GAAP diluted shares
    import re
    for p, d in D.items():
        x = d['x']; r = raw[p]
        t = (r.get('is', {}).get('a_footnotes') or '') + ' ' + (r.get('adj_notes') or '')
        m = re.search(r'weighted-average shares outstanding of ([\d,]+) million', t)
        if m and x.get('ni', 0) < 0: x['a_sh'] = float(m.group(1).replace(',', ''))
        # cash held for sale: beginning + change - ending cash (Coyote held for sale at 30-Jun-2024)
        x['cf_hfs'] = round(x['cf_end'] - x['cf_beg'] - x['cf_net'], 4)
        if abs(x['cf_hfs']) < 1.5: x['cf_hfs'] = 0.0
    # ---- Q4-2018 release typo: the 'Logistics' row of the three-month table is labelled 'Forwarding and Logistics' (878; the twelve-month
    #      table shows Forwarding 6,580 / Logistics 3,234)
    for p, d in D.items():
        x = d['x']
        if 'o_rev_scs_fwdlog' in x and 'o_rev_scs_fwd' in x and 'o_rev_scs_log' not in x:
            x['o_rev_scs_log'] = x.pop('o_rev_scs_fwdlog'); d['corr_ops'] = "Release row label typo: 'Forwarding and Logistics' 878 is Logistics."
    # ---- derived operating keys common to all periods
    import xbrl
    for p, d in D.items():
        x = d['x']
        x['cf_oinv2'] = x['cf_finrec'] + x['cf_oinv']
        x['fcf_oth'] = x['cf_finrec'] + (x.get('cf_oinv_pub') or 0.0)
        x['bs_restr'] = round(x['cf_end'] - x['bs_cash'], 4) if abs(x['cf_end'] - x['bs_cash']) > 1.5 else 0.0
        x['debt_x'] = x['debt']
        if p == 'Q3-26': x['debt_cp'] = 0.0          # 10-Q: no commercial paper outstanding at 30-Sep-2026
        if len(p) == 4:
            a = xbrl.value('AmortizationOfIntangibleAssets', int(p), 'FY')
            if a is not None: x['amort'] = a
        # Supply Chain revenue lines: Forwarding and Logistics were one line to 2017 (split from the Q4-2018 release); Freight to Q2-2021
        if 'o_rev_scs_fwdlog' in x and 'o_rev_scs_fwd' not in x: x['o_rev_scs_fl'] = x['o_rev_scs_fwdlog']
        elif 'o_rev_scs_fwd' in x: x['o_rev_scs_fl'] = x['o_rev_scs_fwd'] + n0(x.get('o_rev_scs_log'))
        for s in ('us', 'intl'):
            if f'o_rev_{s}_cargo' not in x and s == 'us': x['o_rev_us_cargo'] = None
        x.pop('o_rev_us_cargo', None) if x.get('o_rev_us_cargo') is None else None
    return D


if __name__ == '__main__':
    D = run()
    for p in ('2006', '2012', '2025', 'Q1-13', 'Q4-20', 'Q3-26'):
        print(p, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in D[p]['x'].items() if k != 'oa_lab'})
