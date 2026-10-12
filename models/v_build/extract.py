"""Per-period extraction of Visa's statements and operating KPIs from the 10-K / 10-Q (and Q4 earnings releases) text into
data/<period>.json (schema: EXTRACTION_SCHEMA.md). Non-GAAP reconciliations are in data/ngaap/<period>.json (extracted from the
earnings releases, as originally published).

Basis: Q1-Q3 = 10-Q three-month column (identical to the release as originally reported); Q4 three-month = Q4 release column
where the release tables are text (FY2013-17, FY2021+), otherwise fiscal year (10-K) - nine months (Q3 10-Q); annual = 10-K.
Balance sheet = period-end column; cash flow = year to date. KPIs: nominal payments volume (the quarter whose volume drives the
period's service revenue, i.e. the prior calendar quarter; 10-Q / 10-K MD&A), processed transactions (current period).
Shares / EPS / DPS exactly as published (pre-split before Mar-2015); normalize.py adjusts."""
import json, os, re, sys
from parse_doc import rows, norm, block

S = os.environ.get('V_SRC', '/tmp/v_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
P = json.load(open(os.path.join(S, 'period_index.json')))
FY0, FYQ0 = 2008, 2013
END_IS = r'^Net (income|\(loss\) income|income \(loss\))( \(loss\))?( including non-controlling interest)?( attributable to Visa Inc\.)?$'

IS_MAP = [('rev_svc', r'^Service (revenues?|fees)$'), ('rev_dp', r'^Data processing (revenues?|fees)$'), ('rev_itr', r'^International transaction (revenues?|fees)$'),
          ('rev_oth', r'^Other revenues?$'), ('rev_ci', r'^(Client incentives|Volume and support incentives)$'),
          ('rev_net', r'^(Total operating revenues|Net operating revenues|Net revenues?|Operating revenues)$'),
          ('personnel', r'^Personnel$'), ('marketing', r'^(Marketing|Advertising, marketing and promotions?)$'),
          ('network', r'^(Network and processing|Network, EDP and communications)$'), ('prof', r'^(Professional fees|Professional and consulting fees)$'),
          ('dna', r'^Depreciation and amortization$'), ('ga', r'^(General and administrative|Administrative and other)$'),
          ('litig', r'^Litigation provision$'), ('opex', r'^Total operating expenses$'),
          ('opinc', r'^Operating (income|\(loss\) income|income \(loss\))$'),
          ('int_exp', r'^Interest expense(, net)?$'), ('nonop', r'^(Total other income( \(expense\))?|(Total )?[Nn]on-operating (income \(expense\)|\(expense\) income|income|expense|income, net|\(expense\) income, net))$'),
          ('ebt', r'^(Income|\(Loss\) income|Income \(loss\)) before (income taxes|income taxes and minority interest)$'),
          ('tax', r'^Income tax (provision|\(benefit\) provision|provision \(benefit\)|expense)'),
          ('ni_tot', r'^Net (income|\(loss\) income|income \(loss\))( \(loss\))?( including non-controlling interest)?$'),
          ('nci', r'^((Loss|Income|\(Loss\) income) attributable to non-controlling interest|Minority interest)'),
          ('ni', r'attributable to Visa Inc\.$')]
REV_KEYS = ('rev_svc', 'rev_dp', 'rev_itr', 'rev_oth', 'rev_ci')
OPEX_KEYS = ('personnel', 'marketing', 'network', 'prof', 'dna', 'ga', 'litig')

def pick(vals, col):
    return vals[col] if len(vals) > col else None

def parse_is(R, ncols, col, after=0):
    """statement of operations rows -> dict (col = column index: 0 current three months / fiscal year, 2 = year to date)."""
    nv = {3: (3,), 2: (2,), 4: (4,)}[ncols]
    B = block(R, r'^(Service revenues?|Operating revenues|Total operating revenues|Net revenues?|Net operating revenues?)$', r'^Personnel$', END_IS, nvals=nv, after=after)
    if not B: return None, []
    k0 = R.index(B[-1])
    for j in range(k0 + 1, min(k0 + 4, len(R))):        # include NCI / attributable rows
        if re.search(r'non-controlling|attributable to Visa', norm(R[j][1]), re.I) and R[j][2]: B.append(R[j])
    out, other_op, other_nonop, raw = {}, [], [], []
    stage = 'rev'
    for i, lab, vals, *_ in B:
        L = norm(lab)
        if not vals: continue
        v = pick(vals, col); raw.append([L, v])
        hit = None
        for k, p in IS_MAP:
            if re.search(p, L, re.I) and k not in out:
                hit = k; break
        if hit == 'personnel': stage = 'opex'
        if hit == 'opinc': stage = 'nonop'
        if hit == 'ebt': stage = 'post'
        if hit:
            out[hit] = v
        elif stage == 'opex' and L:
            other_op.append([L, v])
        elif stage == 'nonop' and L:
            other_nonop.append([L, v])
    out['other_op'] = other_op; out['other_nonop'] = other_nonop
    # EPS / shares: 'Class A common stock' rows after net income: basic EPS, basic shares, diluted EPS, diluted shares
    k0 = R.index(B[-1]); ca = []
    for j in range(k0 + 1, min(k0 + 45, len(R))):
        if re.match(r'^Class A common stock$', norm(R[j][1])) and R[j][2]: ca.append(pick(R[j][2], col))
        if len(ca) == 4: break
    if len(ca) == 4:
        out['eps_b'], out['sh_b'], out['eps_d'], out['sh_d'] = ca
    return out, raw

def parse_revcat(R, ncols, col):
    """revenue by category (statement of operations to FY2018; revenue note / MD&A from FY2019)."""
    nv = {3: (3,), 2: (2,), 4: (4,)}[ncols]
    B = block(R, r'^Service (revenues?|fees)$', r'^(Client incentives|Volume and support incentives)$', r'^(Net revenues?|Net operating revenues|Total operating revenues|Operating revenues)$', within=8, nvals=nv)
    if not B: B = block(R, r'^Service (revenues?|fees)$', r'^(Client incentives|Volume and support incentives)$', r'^(Net revenues?|Net operating revenues|Total operating revenues|Operating revenues)$', within=8)
    out = {}
    for _, lab, vals, *_ in B:
        L = norm(lab)
        for k, p in IS_MAP[:6]:
            if re.search(p, L, re.I) and k not in out: out[k] = pick(vals, col)
    return out

BS_A = [('cash', r'^Cash and cash equivalents$'), ('escrow', r'^Restricted cash( equivalents)?\s*[-—–]+\s*(U\.S\. )?litigation escrow$'),
        ('settle_rec', r'^Settlement receivable$'), ('ar', r'^Accounts receivable$'), ('collat_a', r'^Customer collateral$'),
        ('tca', r'^Total current assets$'), ('ppe', r'^Property, equipment and technology, net$'), ('gw', r'^Goodwill$'),
        ('intang', r'^Intangible assets(, net)?$'), ('ta', r'^Total assets$')]
BS_L = [('ap', r'^Accounts payable$'), ('settle_pay', r'^Settlement payable$'), ('collat_l', r'^Customer collateral$'),
        ('accomp', r'^Accrued compensation and benefits$'), ('ci_l', r'^Client incentives$'), ('accrued', r'^Accrued liabilities$'),
        ('std', r'^(Current maturities of (long-term )?debt|Short-term debt|Commercial paper|Current portion of long-term debt)$'),
        ('litig_acc', r'^Accrued litigation'), ('tcl', r'^Total current liabilities$'), ('ltd', r'^Long-term debt$'),
        ('dtl', r'^Deferred tax liabilities$'), ('oth_l', r'^Other liabilities$'), ('tl', r'^Total liabilities$'),
        ('pref', r'^(Preferred stock|Series [AB]|UK&I|Europe).*preferred|^Preferred stock'), ('temp', r'^Total temporary equity'), ('te', r'^Total (stockholders. )?equity( \(deficit\)| and accumulated income)?$'),
        ('tle', r'^Total liabilities.*equity$')]

def parse_bs(R):
    B = block(R, r'^Cash and cash equivalents$', r'^Total assets$', r'^Total liabilities.*equity$', within=35, nvals=(2,))
    out, raw, side, inv_cur, inv_nc, tca_seen = {}, [], 'A', 0.0, 0.0, False
    for _, lab, vals, *_ in B:
        L = norm(lab)
        if not vals: continue
        v = vals[0]; raw.append([L, v])
        if side == 'A':
            hit = next((k for k, p in BS_A if re.search(p, L, re.I) and k not in out), None)
            if hit: out[hit] = v
            elif re.search(r'^(Investment securities|Trading|Available-for-sale|Investment securities, available-for-sale)', L, re.I):
                if tca_seen: inv_nc += v
                else: inv_cur += v
            if hit == 'tca': tca_seen = True
            if hit == 'ta': side = 'L'
        else:
            hit = next((k for k, p in BS_L if re.search(p, L, re.I) and k not in out), None)
            if hit == 'litig_acc' and 'tcl' in out: hit = None          # long-term accrued litigation (FY2008-09) stays in other liabilities
            if hit: out[hit] = v
    out['inv_cur'], out['inv_nc'] = inv_cur, inv_nc
    if 'tle' in out and 'tl' in out: out['te'] = out['tle'] - out['tl']        # total equity incl. temporary equity / minority interest
    return out, raw

CF_MAP = [('ni', r'^Net (income|\(loss\) income|income \(loss\))'), ('ci_amort', r'^(Client incentives|Amortization of client incentives|Amortization of volume and support incentives)$'),
          ('sbc', r'^Share-based compensation( expense)?$'), ('dna', r'^Depreciation and amortization'), ('deftax', r'^Deferred income taxes$'),
          ('cfo', r'^Net cash.*operating activities$'), ('capex', r'^Purchases of property, equipment'), ('acq', r'^(Acquisitions?|Acquisition of)'),
          ('cfi', r'^Net cash.*investing activities$'), ('bb', r'^Repurchases? of class A common stock'), ('div', r'^Dividends paid'),
          ('debt_iss', r'^Proceeds from issuance of (senior notes|long-term debt|debt)'), ('debt_rep', r'^Repayments? of (senior notes|long-term debt|debt|term loan)'),
          ('cp', r'commercial paper'), ('cff', r'^Net cash.*financing activities$'), ('fx', r'^Effect of exchange rate'),
          ('net', r'^(Increase|Decrease|\(Decrease\) increase|Increase \(decrease\)|Net (increase|decrease)).*in cash'),
          ('beg', r'beginning of (period|year)$'), ('end', r'(end of (period|year)|as of end of period)$')]

def parse_cf(R, ncols):
    B = []
    for k, (i, lab, vals, *_) in enumerate(R):
        if not re.match(r'^Net (income|\(loss\) income|income \(loss\))', norm(lab)) or len(vals) != ncols: continue
        nxt = [norm(x[1]) for x in R[k:k + 30]]
        if not any(re.match(r'^Depreciation and amortization', x) for x in nxt[:9]): continue
        if not any(re.search(r'operating activities$', x) for x in nxt): continue
        for j in range(k, len(R)):
            B.append(R[j])
            if re.search(r'(end of (period|year)|as of end of period)$', norm(R[j][1])) and R[j][2]: break
        break
    out, raw, esc = {}, [], 0.0
    for _, lab, vals, *_ in B:
        L = norm(lab)
        if not vals: continue
        v = vals[0]; raw.append([L, v])
        if re.search(r'litigation escrow', L, re.I) and 'cfo' in out:
            esc += v; continue
        hit = next((k for k, p in CF_MAP if re.search(p, L, re.I) and k not in out), None)
        if hit == 'ci_amort' and 'cfo' in out: hit = None
        if hit in ('capex', 'acq') and 'cfo' not in out: hit = None
        if hit: out[hit] = v
    out['escrow_fin'] = esc
    return out, raw

def kpis(R, is10k, q):
    """nominal payments volume ($bn; Visa / U.S. / international) and processed transactions (millions):
    first table = three months (10-Q) or twelve months (10-K); for Q3 10-Qs also the nine-month figures (for Q4 = FY - 9M)."""
    out = {}
    pv = [(x[0], x[1], x[4]) for x in R if re.match(r'^Total nominal payments volume$', norm(x[1]), re.I) and len(x[4]) in (6, 9)]
    def tot(v): return (v[6], v[0], v[3]) if len(v) == 9 else (v[4], v[0], v[2])
    if pv:
        out['pv'], out['pv_us'], out['pv_intl'] = tot(pv[0][2])
        if q == 3 and len(pv) > 1: out['pv_9m'], out['pv_us_9m'], out['pv_intl_9m'] = tot(pv[1][2])
    pt = [x for x in R if re.match(r'^(Visa processed transactions|Total processed transactions|Processed transactions)$', norm(x[1]), re.I) and x[2]]
    if pt:
        v = pt[0][2]; out['ptx'] = v[0]
        if q == 3 and len(v) >= 4: out['ptx_9m'] = v[3] if len(v) >= 6 else v[2]
    return out

def load(name): return rows(open(os.path.join(S, 'txt', name)).read())

def period(key):
    e = P[key]; annual = not key.startswith('Q')
    q = None if annual else int(key[1])
    rec = {'period': key, 'sources': {'filing': e.get('filing'), 'release': e.get('release'), 'release_date': e.get('release_date')}, 'notes': []}
    if annual or q < 4:
        R = load(e['filing_txt'])
        ncols = 3 if annual else (2 if q == 1 else 4)
        IS, raw = parse_is(R, ncols, 0)
        rec['is'] = IS; rec['is_raw'] = raw
        rc = parse_revcat(R, ncols, 0)
        for k, v in rc.items():
            if IS.get(k) is None or k == 'rev_net': IS.setdefault(k, v)
        rec['bs'], rec['bs_raw'] = parse_bs(R)
        rec['cf'], rec['cf_raw'] = parse_cf(R, 3 if annual else 2)
        rec['cf']['ytd_months'] = 12 if annual else 3 * q
        rec['kpi'] = kpis(R, annual, q)
        if annual:          # selected financial data: 'Dividend declared and paid per common share' (current year = first value)
            d = [x for x in R if re.match(r'^(Cash )?[Dd]ividends? declared (and paid )?per (common|class A common) share', norm(x[1])) and x[2]]
            if d: rec['dps_10k'] = d[0][2][0]
        if not annual and q > 1:      # year-to-date P&L (for Q4 = FY - 9M)
            ytd, _ = parse_is(R, 4, 2)
            rc = parse_revcat(R, 4, 2)
            for k, v in rc.items(): ytd.setdefault(k, v)
            rec['is_ytd'] = ytd
    else:
        rec['is'] = None; rec['notes'].append('Q4: see normalize.py (release three-month column, else FY - 9M)')
        rel = e.get('release_txt')
        if rel and os.path.exists(os.path.join(S, 'txt', rel)):
            R = load(rel)
            txt = open(os.path.join(S, 'txt', rel)).read().split('\n')
            h = next((i for i, l in enumerate(txt) if re.search(r'statements? of operations', l, re.I) and '|' not in l and i > 20), 0)
            IS, raw = parse_is(R, 4, 0, after=h)
            if IS and IS.get('opex') is not None:
                rc = parse_revcat(R, 4, 0)
                for k, v in rc.items(): IS.setdefault(k, v)
                rec['is_rel'] = IS; rec['is_raw'] = raw
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    keys = [str(y) for y in range(FY0, 2026)] + [f'Q{q}-{y % 100:02d}' for y in range(FYQ0, 2027) for q in (1, 2, 3, 4) if not (y == 2026 and q == 4)]
    for k in keys:
        rec = period(k)
        json.dump(rec, open(os.path.join(OUT, f'{k}.json'), 'w'), indent=1)
        i = rec.get('is') or rec.get('is_rel') or {}
        print(k, i.get('rev_net'), i.get('opex'), i.get('ni'), i.get('eps_d'), i.get('sh_d'), (rec.get('bs') or {}).get('ta'), (rec.get('cf') or {}).get('cfo'), rec.get('kpi'))

if __name__ == '__main__':
    main()
