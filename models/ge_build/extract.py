"""Per-period extraction for GE Aerospace (General Electric Company, CIK 40545) -> data/<period>.json.

Sources (SEC EDGAR text conversions in $GE_SRC/txt, see fetch.py):
  - Face statements (statement of earnings / operations, financial position, cash flows) and the EPS note: Forms 10-Q / 10-K.
  - Segment tables (CES / DPT revenue by equipment / services and sub-segment, segment profit, units, RPO, Corporate & Other):
    10-Q / 10-K MD&A.
  - Non-GAAP reconciliations (adjusted revenue, operating profit, adjusted Corporate & Other costs, adjusted earnings / EPS,
    free cash flow) and orders: Form 8-K Item 2.02 earnings releases (Ex. 99.1).
Basis: GE Aerospace continuing operations after the GE Vernova spin (2-Apr-2024). Each period is taken from the first filing
that presents it on that basis:
  - FY2022-23 and the 2023 quarters: recast comparatives in the 2024 Forms 10-Q / 10-K and 2024 releases (Q1-23 = H1-23 - Q2-23;
    Q4-23 = FY2023 - 9M-23; GE Vernova reported in discontinued operations).
  - Q1-24: comparatives in the Q1-25 Form 10-Q / release (the Q1-24 10-Q still consolidated GE Vernova).
  - Q2-24 onward: as originally reported. Q4 = FY (10-K) - 9M (Q3 10-Q) for the face statements and segment tables; non-GAAP
    and orders from the Q4 release three-month columns.
Signs: costs positive; other income, gains and tax benefit signed by their effect on income; cash flows as presented."""
import json, os, re
import tables as T

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
URL = 'https://www.sec.gov/Archives/edgar/data/40545/{acc}/{doc}'
FIL = {o['date'] + o['form'] + o['primary']: o for o in json.load(open(os.path.join(T.S, 'filings.json')))}

def url_of(path):
    b = os.path.basename(path)
    date, form, acc, rest = b.split('_', 3)
    return URL.format(acc=acc.replace('-', ''), doc=rest[:-4] + '.htm')

# ------------------------------------------------------------------ documents
Q = {   # 10-Q / 10-K by fiscal period end
    'Q2-24': '2024-07-23', 'Q3-24': '2024-10-22', 'FY24': '2025-02-03', 'Q1-25': '2025-04-22', 'Q2-25': '2025-07-21',
    'Q3-25': '2025-10-21', 'FY25': '2026-01-29', 'Q1-26': '2026-04-21', 'Q2-26': '2026-07-16'}
REL = {  # earnings releases by quarter reported
    'Q2-24': '2024-07-23', 'Q3-24': '2024-10-22', 'Q4-24': '2025-01-23', 'Q1-25': '2025-04-22', 'Q2-25': '2025-07-17',
    'Q3-25': '2025-10-21', 'Q4-25': '2026-01-22', 'Q1-26': '2026-04-21', 'Q2-26': '2026-07-16'}
def qdoc(k): return T.doc(Q[k], '10-K' if k.startswith('FY') else '10-Q')
def rdoc(k): return T.doc(REL[k], 'release')

# ------------------------------------------------------------------ statement of earnings
IS = [  # key, regex on normalised label (earnings / income wording both accepted)
    ('rev_eq', r'^sales of equipment$'), ('rev_sv', r'^sales of services$'), ('rev_ins', r'^insurance revenues?$'), ('rev', r'^total revenues?$'),
    ('cogs_eq', r'^cost of equipment sold$'), ('cogs_sv', r'^cost of services sold$'), ('sga', r'^selling, general and administrative'),
    ('sep', r'^separation costs$'), ('gw_imp', r'^goodwill impairments?$'), ('debt_ext', r'^debt extinguishment costs$'),
    ('rd', r'^research and development$'), ('int', r'^interest and other financial charges$'), ('ins_cost', r'^insurance losses, annuity benefits'),
    ('nonop', r'^non-operating benefit'), ('tcost', r'^total costs and expenses$'), ('oth', r'^other income \(loss\)$'),
    ('ebt', r'from continuing operations before income taxes$'), ('tax', r'^benefit \(provision\) for income taxes$'),
    ('ni_cont', r'^(net )?(earnings|income) \(loss\) from continuing operations$'),
    ('disc', r'^(net )?(earnings|income) \(loss\) from discontinued operations, net of taxes$'),
    ('ni', r'^net (earnings|income) \(loss\)$'), ('nci', r'^less net (earnings|income) \(loss\) attributable to noncontrolling interests$'),
    ('ni_co', r'^net (earnings|income) \(loss\) attributable to the company$'), ('pref', r'^preferred stock dividends'),
    ('ni_common', r'^net (earnings|income) \(loss\) attributable to common shareholders$'),
    ('nci_cont', r'attributable to noncontrolling interests, continuing operations$'),
    ('ni_cont_common', r'from continuing operations attributable to common shareholders$')]

def is_raw(path, ci):
    sec = T.stmt(path, r'^STATEMENT OF (EARNINGS|OPERATIONS)', r'^Sales of equipment', r'^cash, cash equivalents and restricted cash$|^current receivables')
    o = {}
    for k, pat in IS:
        r = T.find(sec, pat, need=False)
        if r is None: continue
        v = r[3][ci] if ci < len(r[3]) else None
        if v is not None: o[k] = v
    eps = [r for r in sec if re.search(r'^(diluted|basic) (earnings|income) \(loss\) per share$', r[2])]
    if len(eps) >= 4:
        o['eps_cont_d'], o['eps_cont_b'], o['eps_d'], o['eps_b'] = (eps[i][3][ci] for i in range(4))
    for k in ('tax',):
        if k in o: o[k] = -o[k]            # provision positive (cost)
    if 'nonop' in o: o['nonop'] = o['nonop']   # cost (income): income negative
    return o

# ------------------------------------------------------------------ EPS note (10-Q / 10-K): shares in millions
def eps_note(path):
    """EPS note blocks -> list of dicts {sh_d, sh_b, ni_cc_d} per column pair (10-Q: [3M cur, 3M py] then [YTD cur, YTD py];
    10-K: one block with three years)."""
    a = T.anchor(path, r'^EARNINGS PER SHARE (\(EPS\) )?INFORMATION', r'.', 2)
    sec = T.section(path, '.', None, after=a, nmax=40, confirm=None)
    out = []
    for i, r in enumerate(sec):
        if not re.search(r'^total average equivalent shares$', r[2]): continue
        ni = T.find(sec[max(0, i - 7):i], r'from continuing operations attributable to common shareholders')
        t, n = r[3], ni[3]
        out.append([{'sh_d': t[j], 'sh_b': t[j + 1], 'ni_cc_d': n[j]} for j in range(0, len(t) - 1, 2)])
    return out

# ------------------------------------------------------------------ balance sheet
BS = [('cash', r'^cash, cash equivalents and restricted cash$'), ('inv_sec_cur', r'^investment securities$'),
      ('ar', r'^current receivables$'), ('inv', r'^inventories, including deferred inventory costs$'), ('ca_ctr', r'^current contract assets$'),
      ('oca', r'^all other current assets$'), ('hfs_a', r'^assets of businesses held for sale$'), ('tca', r'^current assets$'),
      ('inv_sec', r'^investment securities$'), ('ppe', r'^property, plant and equipment . net$'), ('gw', r'^goodwill$'),
      ('intang', r'^other intangible assets . net$'), ('ctr_def', r'^contract and other deferred assets$'), ('oa', r'^all other assets$'),
      ('dta', r'^deferred income taxes$'), ('disc_a', r'^assets of discontinued operations$'), ('ta', r'^total assets$'),
      ('std', r'^short-term borrowings$'), ('ap', r'^accounts payable$'), ('prog', r'^progress collections$'),
      ('ctr_liab', r'^contract liabilities and (current )?deferred income$'), ('sda', r'^sales discounts and allowances$'),
      ('ocl', r'^all other current liabilities$'), ('hfs_l', r'^liabilities of businesses held for sale$'), ('tcl', r'^current liabilities$'),
      ('def_inc', r'^deferred income$'), ('ltd', r'^long-term borrowings$'), ('ins_liab', r'^insurance liabilities and annuity benefits$'),
      ('comp', r'^non-current compensation and benefits$'), ('ol', r'^all other liabilities$'), ('disc_l', r'^liabilities of discontinued operations$'),
      ('tl', r'^total liabilities$'), ('cs', r'^common stock'), ('aoci', r'^accumulated other comprehensive'), ('oc', r'^other capital$'),
      ('re', r'^retained earnings$'), ('treas', r'^less common stock held in treasury$'), ('eq', r"^total shareholders. equity$"),
      ('nci', r'^noncontrolling interests$'), ('te', r'^total equity$'), ('tle', r'^total liabilities and equity$')]

def bs_raw(path, ci):
    a = T.anchor(path, r'^STATEMENT OF FINANCIAL POSITION', r'^Cash, cash equivalents and restricted cash \|', 6)
    sec = T.section(path, '.', r'^statement of cash flows|^net (earnings|income) \(loss\)$', after=a, nmax=60, confirm=None)
    o = {}; seen_tca = False
    for r in sec:
        for k, pat in BS:
            if re.search(pat, r[2]):
                if k == 'inv_sec_cur' and seen_tca: continue
                if k == 'inv_sec' and not seen_tca: continue
                if k in o: continue
                o[k] = r[3][ci]
                if k == 'tca': seen_tca = True
                break
    m = re.search(r'\(\s*([\d,]+) and ([\d,]+) shares outstanding', T.find(sec, r'^common stock')[1])
    if m: o['shares_out'] = float(m.group(1 + ci).replace(',', '')) / 1e6
    return o

# ------------------------------------------------------------------ cash flows (year to date)
CF = [('ni', r'^net (earnings|income) \(loss\)$'), ('disc', r'^\(?(net )?\(?(earnings|income)\)? (\(loss\) )?(loss )?from discontinued operations'),
      ('dep', r'^depreciation and amortization of property'), ('amort', r'^amortization of intangible assets'),
      ('gw_imp', r'^goodwill impairments?$'), ('g_eq', r'^\(gains\) losses on (retained and sold interests|equity securities|retained)'),
      ('pens_cost', r'^principal pension plans (\(benefit\) )?cost'), ('pens_contr', r'^principal pension plans employer contributions'),
      ('opeb', r'^other postretirement benefit plans'), ('tax_prov', r'^provision \(benefit\) for income taxes$'),
      ('tax_paid', r'^cash recovered \(paid\) during the year for income taxes'),
      ('wc_ar', r'^decrease \(increase\) in current receivables'), ('wc_inv', r'^decrease \(increase\) in inventories'),
      ('wc_ca', r'^decrease \(increase\) in current contract assets'), ('wc_cl', r'^increase \(decrease\) in contract liabilities'),
      ('wc_prog', r'^increase \(decrease\) in progress collections'), ('wc_ap', r'^increase \(decrease\) in accounts payable'),
      ('wc_sda', r'^increase \(decrease\) in sales discount'), ('oth_op', r'^all other operating activities'),
      ('cfo', r'^cash from \(used for\) operating activities . continuing operations$'), ('cfo_disc', r'^cash from \(used for\) operating activities . discontinued'),
      ('capex', r'^additions to property, plant and equipment'), ('ppe_disp', r'^dispositions of property, plant and equipment'),
      ('biz_disp', r'^proceeds from principal business dispositions'), ('acq', r'^net cash from \(payments for\) principal businesses purchased'),
      ('ret_int', r'^(sales|dispositions) of retained ownership interests'), ('ins_sec', r'^net \(purchases\) dispositions of insurance investment securities'),
      ('oth_inv', r'^all other investing activities'), ('cfi', r'^cash from \(used for\) investing activities . continuing operations$'),
      ('cfi_disc', r'^cash from \(used for\) investing activities . discontinued'),
      ('st_debt', r'^net increase \(decrease\) in borrowings \(maturities of 90 days or less\)'), ('new_debt', r'^newly issued debt'),
      ('repay', r'^repayments and other debt reductions'), ('div', r'^dividends paid to shareholders'), ('pref_red', r'^redemption of preferred stock'),
      ('bb', r'^purchases of common stock for treasury'), ('oth_fin', r'^all other financing activities'),
      ('cff', r'^cash from \(used for\) financing activities . continuing operations$'), ('cff_disc', r'^cash from \(used for\) financing activities . discontinued'),
      ('fx', r'^effect of currency exchange rate changes'), ('net', r'^increase \(decrease\) in cash, cash equivalents and restricted cash$'),
      ('beg', r'^cash, cash equivalents and restricted cash at beginning of'), ('end', r'^cash, cash equivalents and restricted cash at (june|september|december|march)'),
      ('disc_cash', r'^less cash, cash equivalents and restricted cash of discontinued operations'),
      ('end_cont', r'^cash, cash equivalents and restricted cash of continuing operations')]

def cf_raw(path, ci):
    a = T.anchor(path, r'^STATEMENT OF CASH FLOWS', r'^Net (earnings|income) \(loss\) \|', 6)
    sec = T.section(path, '.', r'^statement of comprehensive|^supplemental disclosure|^cash paid during', after=a, nmax=80, confirm=None)
    o = {}
    for r in sec:
        for k, pat in CF:
            if k not in o and re.search(pat, r[2]):
                o[k] = r[3][ci] if ci < len(r[3]) else None
                break
    return o

# ------------------------------------------------------------------ MD&A segment tables
def seg_raw(path, ci):
    """CES / DPT / Corporate & Other tables, units and RPO (MD&A). ci = column (10-Q: 0 3M, 1 3M py, 2 YTD, 3 YTD py; 10-K: years)."""
    rs = T.rows(path)
    o = {}
    heads = [i for i, r in enumerate(rs) if re.search(r'^segment revenues? and profit$', r[2]) or (re.search(r'^\d{4}$', r[2]) and i > 0 and
             re.search(r'^segment revenues? and profit$', rs[i - 1][2]))]
    # segment revenue tables: locate rows by content
    def block(start, n=12): return rs[start:start + n]
    ces = dpt = None
    for i, r in enumerate(rs):
        if re.search(r'^segment revenues? and profit', r[2]):
            b = block(i, 4)
            if any(re.search(r'^defense & systems', x[2]) for x in b[1:4]): dpt = dpt or i
            elif any(re.search(r'^equipment$', x[2]) for x in b[1:4]): ces = ces or i
    if ces is None or dpt is None: raise KeyError('segment tables not found ' + os.path.basename(path))
    def get(b, pat, nth=0):
        h = [x for x in b if re.search(pat, x[2])]
        return h[nth][3][ci] if len(h) > nth and ci < len(h[nth][3]) else None
    b = block(ces, 8)
    o['ces_eq'], o['ces_sv'], o['ces'], o['ces_op'] = get(b, r'^equipment$'), get(b, r'^services$'), get(b, r'^total segment revenues?$'), get(b, r'^segment profit$')
    b = block(dpt, 12)
    o['ds'], o['pat'] = get(b, r'^defense & systems'), get(b, r'^propulsion & additive')
    o['dpt'], o['dpt_eq'], o['dpt_sv'], o['dpt_op'] = get(b, r'^total segment revenues?$'), get(b, r'^equipment$'), get(b, r'^services$'), get(b, r'^segment profit$')
    # units
    u = [i for i, r in enumerate(rs) if re.search(r'^sales in units', r[2])]
    if u:
        b = block(u[0], 6)
        o['u_ce'], o['u_leap'], o['u_isv'] = get(b, r'^commercial engines'), get(b, r'^leap engines'), get(b, r'^internal shop visit')
    if len(u) > 1:
        b = block(u[1], 4)
        o['u_def'] = get(b, r'^(defense|defense & systems) engines')
    # corporate & other
    for i, r in enumerate(rs):
        if re.search(r'^revenues? and operating profit \(cost\)', r[2]):
            b = block(i, 22)
            for k, pat in (('c_ins_rev', r'^insurance revenues?'), ('c_elim', r'^eliminations and other$'), ('c_rev', r'^corporate & other revenues?$'),
                           ('c_g_biz', r'^gains \(losses\) on purchases and sales of business'), ('c_g_eq', r'^gains \(losses\) on retained and sold'),
                           ('c_restr', r'^restructuring and other charges'), ('c_sep', r'^separation costs'), ('c_ins_op', r'^insurance profit'),
                           ('c_te_op', r'^u\.s\. tax equity profit'), ('c_imp', r'^(goodwill )?impairments?'),
                           ('c_ru', r'^russia (&|and) ukraine charges'),
                           ('c_op_gaap', r'^corporate & other operating profit \(cost\) \(gaap\)'), ('c_adj', r'^adjusted (total )?corporate & other operating costs'),
                           ('c_costs', r'^corporate & other (profit \(costs\)|costs)$'), ('c_elim_op', r'^eliminations$')):
                v = get(b, pat)
                if v is not None: o[k] = v
            break
    # RPO (instants: ci 0 = current period end; RPO tables only have current / prior year end) -> take only for ci in (0, 1)
    r_ = [i for i, r in enumerate(rs) if re.search(r'^rpo$', r[2])]
    if ci in (0, 1) and len(r_) >= 2:
        def rpo(i):
            b = block(i, 5)
            return get(b, r'^equipment$'), get(b, r'^services$'), get(b, r'^total rpo$')
        tot = rpo(r_[0]); c1 = rpo(r_[1]); c2 = rpo(r_[2]) if len(r_) > 2 else (None,) * 3
        o['rpo_tot'], o['rpo_ces'], o['rpo_dpt'] = tot[2], c1[2], c2[2]
        o['rpo_ces_eq'], o['rpo_ces_sv'] = c1[0], c1[1]
    return o

# ------------------------------------------------------------------ release non-GAAP tables
def rel_raw(path, w):
    """w: 0 = 3M current, 1 = 3M prior year, 2 = YTD current, 3 = YTD prior year."""
    rs = T.rows(path); o = {}
    def sec(head, n=40):
        try: return T.section(path, head, None, nmax=n)[1:]      # drop the title row (its label repeats the total's)
        except KeyError: return None
    def val(s, pat, nth=0):
        if s is None: return None
        r = T.find(s, pat, nth, need=False)
        if r is None: return None
        try: c = T.cols(r)
        except ValueError: return None
        return c[w]
    s = sec(r'^(operating profit and profit margin|adjusted revenues?, operating profit and profit margin) \(non-gaap\)', 30)
    for k, pat in (('rev', r'^total revenues? \(gaap\)'), ('ins_rev', r'^less: insurance revenues?'), ('adj_rev', r'^adjusted revenues? \(non-gaap\)'),
                   ('tcost', r'^total costs and expenses \(gaap\)'), ('ins_cost', r'^less: insurance cost'), ('te_cost', r'^less: u\.s\. tax equity cost'),
                   ('int', r'^less: interest and other financial'), ('nonop', r'^less: non-operating benefit'), ('restr', r'^less: restructuring'),
                   ('sep', r'^less: separation costs'), ('gw', r'^less: goodwill impairments$'), ('nci_add', r'^add: noncontrolling interests'), ('adj_cost', r'^adjusted costs \(non-gaap\)'),
                   ('oth', r'^other income \(loss\) \(gaap\)'), ('te_oi', r'^less: u\.s\. tax equity$'), ('g_eq', r'^less: gains \(losses\) on retained'),
                   ('g_biz', r'^less: gains \(losses\) on purchases and sales'), ('adj_oi', r'^adjusted other income'), ('ebt', r'^profit \(loss\) \(gaap\)$'),
                   ('op', r'^operating profit \(loss\) \(non-gaap\)$')):
        v = val(s, pat)
        if v is not None: o['op_' + k] = v
    s = sec(r'^adjusted (total )?corporate & other operating costs \(non-gaap\)', 24)
    for k, pat in (('c_costs', r'^corporate & other (profit \(costs\)|costs)$'), ('c_elim', r'^eliminations$'),
                   ('c_adj', r'^adjusted (total )?corporate & other operating costs \(non-gaap\)$')):
        v = val(s, pat, 1 if k == 'c_adj' else 0)
        if v is not None: o[k] = v
    # adjusted earnings / net income: Income | EPS pairs
    s = sec(r'^adjusted (earnings|net income) \(loss\) \(non-gaap\)', 40)
    if s is not None:
        def pair(pat, nth=0):
            r = T.find(s, pat, nth, need=False)
            if r is None: return None, None
            t = r[3]
            return (t[2 * w] if 2 * w < len(t) else None), (t[2 * w + 1] if 2 * w + 1 < len(t) else None)
        items = []
        for k, pat in (('start', r'^(earnings|net income) \(loss\) from continuing operations \(gaap\)'),
                       ('ins_pre', r'^insurance (earnings|net income) \(loss\) \(pre-tax\)'), ('ins_tax', r'^tax effect on insurance'),
                       ('te_pre', r'^u\.s\. tax equity (earnings|net income) \(loss\) \(pre-tax\)'), ('te_tax', r'^tax effect on u\.s\. tax equity'),
                       ('nonop_pre', r'^non-operating benefit \(cost\) income \(pre-tax\)'), ('nonop_tax', r'^tax effect on non-operating'),
                       ('gbiz_pre', r'^gains \(losses\) on purchases and sales of business interests \(pre-tax\)'), ('gbiz_tax', r'^tax effect on gains \(losses\) on purchases'),
                       ('geq_pre', r'^gains \(losses\) on retained and sold ownership interests and other equity securities \(pre-tax\)'),
                       ('geq_tax', r'^tax effect on gains \(losses\) on retained'),
                       ('restr_pre', r'^restructuring & other \(pre-tax\)'), ('restr_tax', r'^tax effect on restructuring'),
                       ('sep_pre', r'^separation costs \(pre-tax\)'), ('sep_tax', r'^tax effect on separation'),
                       ('gw_pre', r'^goodwill impairments \(pre-tax\)'), ('gw_tax', r'^tax effect on goodwill impairments'),
                       ('ru_pre', r'^russia and ukraine charges \(pre-tax\)'), ('ru_tax', r'^tax effect on russia'),
                       ('pref', r'^less: excise tax and accretion of preferred'),
                       ('adj', r'^adjusted (earnings|net income) \(loss\) \(non-gaap\)')):
            a, e = pair(pat)
            if a is not None: o['ae_' + k] = a; o['ae_' + k + '_eps'] = e
    s = sec(r'^free cash flows? \(fcf\) \(non-gaap\)', 14)
    for k, pat in (('cfoa', r'^(cash flows from operating activities \(cfoa\)|cfoa) \(gaap\)'), ('ins_cfoa', r'^less: insurance cfoa'),
                   ('capex', r'^add: gross additions'), ('ppe_disp', r'^add: dispositions of property'), ('sep', r'^less: separation cash'),
                   ('restr', r'^less: corporate (& other )?restructuring cash'), ('tax_sale', r'^less: taxes related to business sales'),
                   ('fcf', r'^free cash flows? (\(fcf\) )?\(non-gaap\)$')):
        v = val(s, pat)
        if v is not None: o['fcf_' + k] = v
    # headline table: orders, continuing EPS
    for name, pat in (('ces', r'^commercial engines'), ('dpt', r'^defense & propulsion')):
        pass
    orders = [r for r in rs if re.search(r'^orders$', r[2])]
    if len(orders) >= 2:
        o['ord_ces'] = T.cols(orders[0])[w]; o['ord_dpt'] = T.cols(orders[1])[w]
    seg_rev = [r for r in rs if re.search(r'^revenues?$', r[2])]
    seg_op = [r for r in rs if re.search(r'^(segment|operating) profit/\(loss\)$', r[2])]
    if len(seg_rev) >= 2 and len(seg_op) >= 2:
        o['r_ces'], o['r_dpt'] = T.cols(seg_rev[0])[w], T.cols(seg_rev[1])[w]
        o['r_ces_op'], o['r_dpt_op'] = T.cols(seg_op[0])[w], T.cols(seg_op[1])[w]
    ce = [r for r in rs if re.search(r'^continuing eps$', r[2])]
    if ce: o['eps_cont'] = T.cols(ce[0])[w]
    return o

# ------------------------------------------------------------------ assembly helpers
def sub(a, b):
    """a - b for every key present in both (derived periods: H1 - Q2, FY - 9M)."""
    return {k: round(a[k] - b[k], 6) for k in a if k in b and isinstance(a[k], (int, float)) and isinstance(b[k], (int, float))}

def run():
    os.makedirs(OUT, exist_ok=True)
    recs = {}
    def rec(p):
        return recs.setdefault(p, {'period': p, 'sources': [], 'notes': [], 'is': {}, 'seg': {}, 'ng': {}, 'cf_ytd': None, 'bs': None, 'x': {}})
    def src(p, path):
        u = url_of(path)
        if u not in recs[p]['sources']: recs[p]['sources'].append(u)

    # ---------------- statements of earnings + segments
    plan = {  # period: list of (sign, doc key, column)
        '2022': [(1, 'FY24', 2)], '2023': [(1, 'FY24', 1)], '2024': [(1, 'FY24', 0)], '2025': [(1, 'FY25', 0)],
        'Q1-23': [(1, 'Q2-24', 3), (-1, 'Q2-24', 1)], 'Q2-23': [(1, 'Q2-24', 1)], 'Q3-23': [(1, 'Q3-24', 1)], 'Q4-23': [(1, 'FY24', 1), (-1, 'Q3-24', 3)],
        'Q1-24': [(1, 'Q1-25', 1)], 'Q2-24': [(1, 'Q2-24', 0)], 'Q3-24': [(1, 'Q3-24', 0)], 'Q4-24': [(1, 'FY24', 0), (-1, 'Q3-24', 2)],
        'Q1-25': [(1, 'Q1-25', 0)], 'Q2-25': [(1, 'Q2-25', 0)], 'Q3-25': [(1, 'Q3-25', 0)], 'Q4-25': [(1, 'FY25', 0), (-1, 'Q3-25', 2)],
        'Q1-26': [(1, 'Q1-26', 0)], 'Q2-26': [(1, 'Q2-26', 0)]}
    for p, parts in plan.items():
        r = rec(p)
        for name, fn in (('is', is_raw), ('seg', seg_raw)):
            acc = None
            for sg, dk, ci in parts:
                d = fn(qdoc(dk), ci); src(p, qdoc(dk))
                if sg < 0:
                    d = {k: v for k, v in d.items() if not k.startswith(('eps', 'rpo', 'u_isv'))}
                    acc = sub(acc, d)
                else:
                    acc = d if acc is None else acc
            r[name] = acc
        if len(parts) > 1:
            r['notes'].append(f'{p}: statement of earnings and segment tables derived as ' + ' − '.join(f'{dk} col {ci}' for _, dk, ci in parts) +
                              ' (per-share data, internal shop visit growth % and RPO not derivable).')
    # Jan-2026 segment recast (Aeroderivative CES -> DPT; T&O site revenue / cost from Corporate to the segments): the 2026 Forms 10-Q
    # present Q1-25 / H1-25 on the new structure; FY2025 revised ($bn, unaudited estimates) in the Q4-25 release guidance table
    for p, dk, ci in (('Q1-25', 'Q1-26', 1), ('Q2-25', 'Q2-26', 1)):
        recs[p]['seg_rc'] = {k: v for k, v in seg_raw(qdoc(dk), ci).items() if not k.startswith(('rpo', 'u_isv'))}
        recs[p]['ng_rc'] = rel_raw(rdoc(dk), 1); src(p, qdoc(dk))
        recs[p]['notes'].append(f'{p}: Jan-2026 segment structure (recast) from the {dk} Form 10-Q / release prior-year columns (seg_rc / ng_rc).')
    # 2023 cross-check: FY2023 in the FY2025 10-K (latest presentation)
    recs['2023']['x']['is_fy25k'] = is_raw(qdoc('FY25'), 2)
    # EPS-note share counts (10-Q three-month columns; FY from 10-K)
    shares = {}
    for k in ('Q2-24', 'Q3-24', 'Q1-25', 'Q2-25', 'Q3-25', 'Q1-26', 'Q2-26'):
        e = eps_note(qdoc(k))[0]
        y = int('20' + k[-2:]); q = int(k[1])
        shares[k] = (e[0]['sh_d'], e[0]['sh_b'], e[0]['ni_cc_d'])
        shares[f'Q{q}-{str(y - 1)[2:]}'] = (e[1]['sh_d'], e[1]['sh_b'], e[1]['ni_cc_d'])
    # 10-K EPS note: one block per year
    for p, (d, b, n) in shares.items():
        if p in recs: recs[p]['is'].update({'sh_d': d, 'sh_b': b, 'ni_cc_eps': n})
    for fy, blocks in (('FY24', eps_note(qdoc('FY24'))[0]), ('FY25', eps_note(qdoc('FY25'))[0])):
        yrs = {'FY24': ['2024', '2023', '2022'], 'FY25': ['2025', '2024', '2023']}[fy]
        for p, bl in zip(yrs, blocks):
            if 'sh_d' not in recs[p]['is']:
                recs[p]['is'].update({'sh_d': bl['sh_d'], 'sh_b': bl['sh_b'], 'ni_cc_eps': bl['ni_cc_d']})

    # ---------------- release non-GAAP + orders
    rplan = {'Q2-23': ('Q2-24', 1), 'Q3-23': ('Q3-24', 1), 'Q4-23': ('Q4-24', 1), '2023': ('Q4-24', 3), 'Q1-24': ('Q1-25', 1),
             'Q2-24': ('Q2-24', 0), 'Q3-24': ('Q3-24', 0), 'Q4-24': ('Q4-24', 0), '2024': ('Q4-24', 2), 'Q1-25': ('Q1-25', 0), 'Q2-25': ('Q2-25', 0),
             'Q3-25': ('Q3-25', 0), 'Q4-25': ('Q4-25', 0), '2025': ('Q4-25', 2), 'Q1-26': ('Q1-26', 0), 'Q2-26': ('Q2-26', 0)}
    for p, (rk, w) in rplan.items():
        recs[p]['ng'] = rel_raw(rdoc(rk), w); src(p, rdoc(rk))
    # Q1-23 = H1-23 - Q2-23 (Q2-24 release); per-share from the 11-Apr-2024 8-K (Ex. 99.1, revised)
    h1 = rel_raw(rdoc('Q2-24'), 3); q2 = rel_raw(rdoc('Q2-24'), 1)
    recs['Q1-23']['ng'] = sub(h1, {k: v for k, v in q2.items() if not k.endswith('_eps') and k != 'eps_cont'})
    recs['Q1-23']['notes'].append('Q1-23 non-GAAP and orders = H1-23 − Q2-23 (Q2-24 release comparatives). Adjusted EPS $0.63 and continuing EPS $5.98 '
                                  '(revised, GE Aerospace basis) from the 11-Apr-2024 Form 8-K Ex. 99.1 (supplemental financial information).')
    recs['Q1-23']['ng']['ae_adj_eps'] = 0.63; recs['Q1-23']['ng']['eps_cont'] = 5.98
    src('Q1-23', rdoc('Q2-24')); src('Q1-23', T.doc('2024-04-11', 'gevoluntary'))

    # ---------------- cash flow (YTD) and balance sheets
    cplan = {'2022': ('FY24', 2), '2023': ('FY24', 1), 'H1-23': ('Q2-24', 1), '9M-23': ('Q3-24', 1),
             'Q1-24': ('Q1-25', 1), 'H1-24': ('Q2-24', 0), '9M-24': ('Q3-24', 0), '2024': ('FY24', 0),
             'Q1-25': ('Q1-25', 0), 'H1-25': ('Q2-25', 0), '9M-25': ('Q3-25', 0), '2025': ('FY25', 0), 'Q1-26': ('Q1-26', 0), 'H1-26': ('Q2-26', 0)}
    ytd = {}
    for k, (dk, ci) in cplan.items():
        ytd[k] = cf_raw(qdoc(dk), ci); ytd[k]['_src'] = url_of(qdoc(dk))
    json.dump(ytd, open(os.path.join(OUT, '_cf_ytd.json'), 'w'), indent=1)
    bplan = {'2023': ('FY24', 1), 'Q4-23': ('FY24', 1), 'Q2-24': ('Q2-24', 0), 'Q3-24': ('Q3-24', 0), '2024': ('FY24', 0), 'Q4-24': ('FY24', 0),
             'Q1-25': ('Q1-25', 0), 'Q2-25': ('Q2-25', 0), 'Q3-25': ('Q3-25', 0), '2025': ('FY25', 0), 'Q4-25': ('FY25', 0), 'Q1-26': ('Q1-26', 0),
             'Q2-26': ('Q2-26', 0)}
    for p, (dk, ci) in bplan.items():
        recs[p]['bs'] = bs_raw(qdoc(dk), ci); src(p, qdoc(dk))
    # FY2024 10-K presents Dec-2023 as the first GE Aerospace balance sheet (GE Vernova in discontinued operations)
    for p in recs:
        json.dump(recs[p], open(os.path.join(OUT, f'{p}.json'), 'w'), indent=1)
    return recs

if __name__ == '__main__':
    R = run()
    for p in sorted(R, key=lambda s: (s[-2:] if '-' in s else s[2:], s)):
        r = R[p]
        print(p, 'IS', len(r['is']), 'SEG', len(r['seg']), 'NG', len(r['ng']), 'BS', len(r['bs'] or {}),
              {k: r['is'].get(k) for k in ('rev', 'ebt', 'ni_cont', 'sh_d')}, {k: r['ng'].get(k) for k in ('op_op', 'ae_adj', 'ae_adj_eps', 'fcf_fcf')})
