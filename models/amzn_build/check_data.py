"""Consistency checks on the normalised Amazon data: statement arithmetic, segment / product-group / legacy-segment sums, EPS,
cash-flow and balance-sheet tie-outs, published TTM free cash flow vs the model definition, quarters vs fiscal years, and
cross-checks to XBRL company facts (revenue, operating income, net income, total assets; as first filed)."""
import normalize
D = normalize.run()
def x(p): return D.get(p, {}).get('x', {})
def n(v): return v or 0.0
bad, ok = [], [0]
def chk(name, a, b, tol=1.01):
    if a is None or b is None: return
    ok[0] += 1
    if abs(a - b) > tol: bad.append(f'{name}: {a:.3f} vs {b:.3f} ({a - b:+.3f})')

def qk(y, q): return f'Q{q}-{str(y)[2:]}'
def prevq(p):
    y, q = normalize.fyq(p)
    return qk(y, q - 1) if q > 1 else qk(y - 1, 4)

for p in normalize.periods():
    v = x(p)
    if not v: bad.append(f'{p}: no data'); continue
    ops = v['cogs'] + v['ful'] + v['mkt'] + v['tech'] + v['ga'] + v['othop']
    chk(f'{p} oi', v['rev'] - ops, v['oi'])
    chk(f'{p} ebt', v['oi'] + v['int_inc'] - v['int_exp'] + v['oth_inc'], v['ebt'])
    chk(f'{p} ni', v['ebt'] - v['tax'] + v['equity'], v['ni'])
    if v.get('rev_prod') is not None: chk(f'{p} product+service', v['rev_prod'] + v['rev_serv'], v['rev'])
    if v.get('sh_d'): chk(f'{p} eps', v['ni'] / v['sh_d'], v['eps_d'], 0.0101 if v['split_f'] == 1 else 0.0026)
    if v.get('aws_rev') is not None:
        chk(f'{p} seg rev', v['na_rev'] + v['intl_rev'] + v['aws_rev'], v['rev'])
        chk(f'{p} seg oi', v['na_oi'] + v['intl_oi'] + v['aws_oi'] + n(v.get('seg_unalloc')), v['oi'])
    if v.get('leg_na_rev') is not None:
        chk(f'{p} legacy seg rev', v['leg_na_rev'] + v['leg_intl_rev'], v['rev'])
        chk(f'{p} legacy seg oi', v['leg_na_oi'] + v['leg_intl_oi'] + n(v.get('leg_unalloc')), v['oi'])
    if v.get('orig_na_oi') is not None:
        chk(f'{p} 2015 original seg oi', v['orig_na_oi'] + v['orig_intl_oi'] + v['orig_aws_oi'] + v['orig_unalloc'], v['oi'])
    if v.get('mx_media') is not None:
        chk(f'{p} media/EGM/other (+ AWS from 2015)', v['mx_media'] + v['mx_egm'] + v['mx_other'] + (n(v.get('aws_rev')) if normalize.fyq(p)[0] >= 2015 else 0), v['rev'])
    if v.get('grp_online') is not None:
        chk(f'{p} product groups', sum(n(v.get(f'grp_{k}')) for k in normalize.GRP), v['rev'])
        chk(f'{p} AWS group vs segment', v['grp_aws'], v.get('aws_rev'))
    if v.get('cf_cfo') is not None:
        chk(f'{p} cfo lines', v['cf_ni'] + v['cf_dda'] + v['cf_sbc'] + v['cf_def'] + v['cf_othnc'] + v['cf_wc'], v['cf_cfo'])
        chk(f'{p} cf ni = is ni', v['cf_ni'], v['ni'])
        chk(f'{p} cash roll', v['cf_beg'] + v['cf_net'], v['cf_end'])
        chk(f'{p} net = cfo+cfi+cff+fx', v['cf_cfo'] + v['cf_cfi'] + v['cf_cff'] + v['cf_fx'], v['cf_net'])
        y, q = normalize.fyq(p)
        if y < 2018: chk(f'{p} cf end = bs cash', v['cf_end'], v.get('bs_cash'))
        else:
            if v.get('bs_cash') is not None and v['cf_end'] < v['bs_cash'] - 1: bad.append(f'{p}: CF cash (incl. restricted) below BS cash')
    if v.get('fcf_ttm') is not None:
        if p.isdigit(): chk(f'{p} fcf FY', v['fcf_mod'], v['fcf_ttm'])
        else:
            ps = [p]
            for _ in range(3): ps.append(prevq(ps[-1]))
            if all(x(k).get('fcf_mod') is not None for k in ps):
                chk(f'{p} fcf TTM (±3 rounding)', sum(x(k)['fcf_mod'] for k in ps) + n(v.get('fcf_basis')), v['fcf_ttm'], 3.01)
                if v.get('fcf_lease_ttm') is not None and normalize.fyq(p) >= (2015, 3):
                    chk(f'{p} fcf less lease principal TTM (±3)', sum(x(k)['fcf_mod'] + x(k)['cf_lease'] for k in ps) + n(v.get('fcf_lease_basis')), v['fcf_lease_ttm'], 3.01)
    if v.get('bs_ta') is not None:
        chk(f'{p} bs', v['bs_ta'], v['bs_tle'])
        chk(f'{p} tca', v['bs_cash'] + v['bs_msec'] + v['bs_inv'] + v['bs_ar'] + v['bs_oca'], v['bs_tca'])
    # XBRL cross-checks (as first filed; XBRL starts 2009)
    if not p.startswith('Q4'):          # XBRL has no reliable three-month Q4 facts (10-K duration facts are annual)
        chk(f'{p} xbrl rev', v['rev'], v.get('xb_rev')); chk(f'{p} xbrl oi', v['oi'], v.get('xb_oi')); chk(f'{p} xbrl ni', v['ni'], v.get('xb_ni'))
    chk(f'{p} xbrl ta', v.get('bs_ta'), v.get('xb_ta'))

for y in range(2013, 2026):
    xs = lambda p, ks: None if any(x(p).get(k) is None for k in ks) else sum(x(p)[k] for k in ks)
    for ks in (('cf_debt', 'cf_lease'), ('cf_capex', 'cf_capex_proc')):      # 2014 / 2017 presentation changes within the year
        qs = [xs(qk(y, q), ks) for q in (1, 2, 3, 4)]
        if None not in qs: chk(f'FY{y} {"+".join(ks)} sum-q', sum(qs), xs(str(y), ks), 2.51)
    KNOWN = {(2022, 'cf_dda'): 'FY2022 D&A in the Q4-22 release includes the 9M-22 "other operating expense (income), net" ($460m), shown separately in the Q1-Q3/22 releases'}
    for k in ('rev', 'cogs', 'ful', 'mkt', 'tech', 'ga', 'othop', 'oi', 'int_inc', 'int_exp', 'oth_inc', 'tax', 'equity', 'ni', 'na_rev', 'intl_rev', 'aws_rev',
              'na_oi', 'intl_oi', 'aws_oi', 'cf_cfo', 'cf_acq', 'cf_cfi', 'cf_cff', 'cf_bb', 'cf_dda', 'cf_sbc',
              'grp_online', 'grp_tp', 'grp_subs', 'grp_ads', 'grp_aws'):
        qs = [x(qk(y, q)).get(k) for q in (1, 2, 3, 4)]
        if (y, k) in KNOWN: continue
        if all(q is not None for q in qs): chk(f'FY{y} {k} sum-q (±2.5 rounding)', sum(qs), x(str(y)).get(k), 2.51)
    chk(f'FY{y} sh_d vs avg q', sum(x(qk(y, q))['sh_d'] for q in (1, 2, 3, 4)) / 4, x(str(y))['sh_d'], 100)
print('\n'.join(bad) or 'all checks pass')
print('Known, documented exceptions (not checked):', '; '.join(KNOWN.values()))
print(f'{ok[0]} checks, {len(bad)} issues')
