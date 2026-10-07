"""Build the ESAB Corporation model in the MLM template format."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl
from mbuild import Model, Layout
import esab_data as D

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, '..', 'MLM_template.xlsx')
CFG = json.load(open(os.path.join(HERE, 'esab_cfg.json')))

P, S = D.build()
for k, v in D.cf_discrete(S).items():
    S['cf_' + k] = v
CFX = D.colfax()

lay = Layout(range(2012, 2021), range(2021, 2026), 2026, 2, range(2027, 2031))
SEGS = [('AM', 'Americas', 'Americas (welding & cutting equipment, consumables, gas control, automation — North & South America)'),
        ('EA', 'EMEA & APAC', 'EMEA & APAC (Europe, Middle East, Africa, Asia Pacific; includes Russia)')]


def H(key, scale=1.0):
    d = S.get(key, {})
    return lambda c: (None if d.get(c.label) is None else d[c.label] * scale)


def has(key):
    d = S.get(key, {})
    return lambda c: d.get(c.label) is not None


def yoy(key, guard=None):
    def f(c):
        p = lay.py(c)
        if p is None or (guard and not (guard(c) and guard(p))):
            return None
        return f'=IF(AND(ISNUMBER([{key}]),ISNUMBER([{key}@py])),IFERROR([{key}]/[{key}@py]-1,""),"")'
    return f


def ratio(a, b, guard=None):
    return lambda c: None if (guard and not guard(c)) else f'=IF(AND(ISNUMBER([{a}]),ISNUMBER([{b}])),IFERROR([{a}]/[{b}],""),"")'


def prep():
    """derived historical series"""
    g = lambda k, l: S.get(k, {}).get(l)
    labels = set(S.get('is_net_sales', {}).keys())
    # Eddyfi in segments (Q2/26) — split of the acquisition contribution
    for s in ('AM', 'EA'):
        v = CFG['eddyfi']['in_segment_q2'][s]
        S.setdefault(f'{s}_edd', {})['Q2/26'] = v
        S.setdefault(f'{s}_edde', {})['Q2/26'] = v * CFG['eddyfi']['margin_2026']
    # adjusted EBITDA bridge categories (pre-tax): restr / txn / amort / perf / oth ; D&A other
    for l in labels:
        if g('pub_adj_ebitda', l) is None:
            continue
        txn, am = g('acq_txn', l), g('acq_amort', l)
        acq_total = g('ae_acq', l) or 0.0
        if txn is None and am is None:
            am, txn = acq_total, 0.0   # split not disclosed: treated as amortization
        elif txn is None:
            txn = acq_total - am
        elif am is None:
            am = acq_total - txn
        resid = acq_total - txn - am
        S.setdefault('br_txn', {})[l] = txn + resid
        S.setdefault('br_amort', {})[l] = am
        S.setdefault('br_restr', {})[l] = g('ae_restr', l) or 0.0
        S.setdefault('br_perf', {})[l] = g('ae_perf', l) or 0.0
        S.setdefault('br_oth', {})[l] = g('ae_oth', l) or 0.0
        S.setdefault('br_sep', {})[l] = g('ae_sep', l) or 0.0
        S.setdefault('br_da', {})[l] = g('ae_da', l) or 0.0
    # FY2019 / FY2020 (Form 10 basis): unexplained difference between the printed components and adjusted EBITDA -> definitional row
    for y in (2019, 2020):
        oi = g('is_operating_income', y)
        if oi is None or g('pub_adj_ebitda', y) is None:
            continue
        comp = oi + sum((g(k, y) or 0.0) for k in ('br_restr', 'br_txn', 'br_amort', 'br_perf', 'br_sep', 'br_oth', 'br_da'))
        S['br_oth'][y] = (g('br_oth', y) or 0.0) + g('pub_adj_ebitda', y) - comp
    # adjusted NI bridge: pre-tax items beyond the EBITDA bridge (e.g. bridge fees in interest)
    for l in labels:
        if g('pub_adj_ni', l) is None:
            continue
        pre_tot = sum((g('an_' + k, l) or 0.0) for k in ('restr', 'acq', 'perf', 'oth', 'pen', 'da', 'sep'))
        ebitda_items = sum((g(k, l) or 0.0) for k in ('br_restr', 'br_txn', 'br_amort', 'br_perf', 'br_sep'))
        S.setdefault('an_nonop', {})[l] = pre_tot - ebitda_items
    # BS derived lines
    for l in set(S.get('bs_total_assets', {}).keys()):
        tca = g('bs_total_current_assets', l); cash = g('bs_cash', l); ar = g('bs_ar', l); inv = g('bs_inventories', l)
        if None not in (tca, cash, ar, inv):
            S.setdefault('bs_oca', {})[l] = tca - cash - ar - inv
        ta = g('bs_total_assets', l)
        parts = [g(k, l) for k in ('bs_ppe_net', 'bs_goodwill', 'bs_intangibles_net')]
        if ta is not None and tca is not None and None not in parts:
            S.setdefault('bs_onca', {})[l] = ta - tca - sum(parts)
        tcl = g('bs_total_current_liabilities', l)
        if tcl is not None:
            S.setdefault('bs_ocl', {})[l] = tcl - (g('bs_current_debt', l) or 0) - (g('bs_ap', l) or 0) - (g('bs_accrued_liabilities', l) or 0)
        tl = g('bs_total_liabilities', l); tle = g('bs_total_liabilities_and_equity', l); te = g('bs_total_equity', l)
        if tl is None and tle is not None and te is not None:
            tl = tle - te; S.setdefault('bs_total_liabilities', {})[l] = tl
        if tl is not None and tcl is not None:
            S.setdefault('bs_oncl', {})[l] = tl - tcl - (g('bs_long_term_debt', l) or 0)
        le = g('bs_total_esab_equity', l)
        if le is None and te is not None:
            le = te - (g('bs_nci_equity', l) or 0); S.setdefault('bs_total_esab_equity', {})[l] = le
        if le is not None:
            known = sum((g(k, l) or 0.0) for k in ('bs_mcps', 'bs_common_stock_apic', 'bs_aoci'))
            S.setdefault('bs_re', {})[l] = le - known   # retained earnings / net parent investment (balance)
    # Q4 weighted shares (not disclosed): FY x 4 - (Q1+Q2+Q3)
    for y in range(2021, 2026):
        q4 = f'Q4/{str(y)[2:]}'
        for k in ('is_shares_basic', 'is_shares_diluted'):
            qs = [g(k, f'Q{q}/{str(y)[2:]}') for q in (1, 2, 3)]
            if g(k, q4) is None and g(k, y) is not None and None not in qs:
                S[k][q4] = 4 * g(k, y) - sum(qs)
    # Q4 BS = FY BS
    for y in range(2021, 2026):
        q4 = f'Q4/{str(y)[2:]}'
        for k in list(S.keys()):
            if k.startswith('bs_') and S[k].get(y) is not None and S[k].get(q4) is None:
                S[k][q4] = S[k][y]
    # CF derived
    for l in set(S.get('cf_cfo', {}).keys()):
        f = lambda k: S.get('cf_' + k, {}).get(l) or 0.0
        S.setdefault('cf_oth', {})[l] = f('cfo') - (f('net_income') + f('da') + f('sbc') + f('deferred_taxes') + f('noncash_restructuring_impairment_gains') + f('wc'))
        S.setdefault('cf_oinv', {})[l] = f('cfi') - (f('capex') + f('acquisitions') + f('proceeds_asset_sales'))
        S.setdefault('cf_ofin', {})[l] = f('cff') - (f('debt_proceeds') + f('debt_repayments') + f('revolver_net') + f('dividends_paid') + f('buybacks') + f('equity_issuance'))
    # Colfax Fabrication Technology memo
    yrs = (CFX or {}).get('years', {})
    for y, d in yrs.items():
        y = int(y)
        for k in ('net_sales', 'segment_operating_income', 'adjusted_ebita'):
            v = d.get(k)
            if v is None and k == 'adjusted_ebita':
                v = ((d.get('later_recasts') or {}).get('adjusted_ebita') if isinstance(d.get('later_recasts'), dict) else None)
            if isinstance(v, dict) and v:
                v = list(v.values())[0]
            if v is not None and not isinstance(v, (dict, list)):
                S.setdefault('cfx_' + k, {})[y] = float(v)
        sc = d.get('sales_change') or {}
        for k in ('organic_pct', 'acquisitions_pct', 'fx_pct'):
            if sc.get(k) is not None:
                S.setdefault('cfx_' + k, {})[y] = float(sc[k]) / 100.0
        if y <= 2020 and d.get('equipment_sales') is not None and y not in S.get('pl_equipment', {}):
            S.setdefault('cfx_eq', {})[y] = float(d['equipment_sales']); S.setdefault('cfx_cons', {})[y] = float(d['consumables_sales'])


prep()


def build(scenario='Base'):
    wb = openpyxl.load_workbook(TEMPLATE)
    t = wb['Model']
    ws = wb.create_sheet('Model_new')
    M = Model(wb, t, ws, lay)
    sc = CFG['scenario']
    E = CFG['eddyfi']
    blocks = [
        dict(kind='hdr', label='FY26 outlook — Q2-26 release (6-Aug-26); includes Eddyfi from 1-Jun-26', cols=('High', 'Mid', 'Low'),
             note='Updated outlook: total core sales growth 11.0–14.0% (core organic 2–4%, M&A ~9%, FX 0–1%); core adjusted EBITDA $615–625m; core adjusted EPS $5.40–5.50.'),
        dict(kind='pt', key='G26', label='  FY26 core sales growth (ex-Russia)', bull=sc['G26'][0], base=sc['G26'][1], bear=sc['G26'][2], fmt='pct',
             note='Raised from 6–9% (M&A contribution ~9% from ~4% after the Eddyfi close). Drives the Q3/Q4-26E organic calibration.'),
        dict(kind='pt', key='EB26', label='  FY26 core adjusted EBITDA ($m)', bull=sc['EB26'][0], base=sc['EB26'][1], bear=sc['EB26'][2], fmt='num',
             note='Raised to $615–625m (from $575–595m). Drives the Q3/Q4-26E margin calibration.'),
        dict(kind='pt', key='EPS26', label='  FY26 core adjusted EPS ($; memo)', bull=sc['EPS26'][0], base=sc['EPS26'][1], bear=sc['EPS26'][2], fmt='eps',
             note='$5.40–5.50 (memo; compare with model core adjusted EPS).'),
        dict(kind='hdr', label='FY26 point estimates / capital returns', cols=('Bull', 'Base', 'Bear')),
        dict(kind='pt', key='CAPEX26', label='  FY26 capital expenditures ($m)', bull=sc['CAPEX26'][0], base=sc['CAPEX26'][1], bear=sc['CAPEX26'][2], fmt='num', note=CFG['notes']['capex']),
        dict(kind='pt', key='TAX26', label='  2H/26 effective tax rate', bull=sc['TAX26'][0], base=sc['TAX26'][1], bear=sc['TAX26'][2], fmt='pct', note='ESAB adjusted tax rate ~22–23%.'),
        dict(kind='pt', key='BB26', label='  2H/26 share repurchases ($m)', bull=sc['BB26'][0], base=sc['BB26'][1], bear=sc['BB26'][2], fmt='num', note='Post-Eddyfi deleveraging: no 2H buybacks in Base.'),
        dict(kind='pt', key='LEV', label='  Minimum net debt / Adjusted EBITDA (x) — buyback floor 2027E+', bull=sc['LEV'][0], base=sc['LEV'][1], bear=sc['LEV'][2], fmt='x2',
             note='ESAB targets net leverage < 3.0x by YE2026 after Eddyfi and ~2x over time; buybacks resume once leverage reaches the floor.'),
    ]
    for lk, lbl, note in CFG['levers']:
        lv = CFG['lever_values'][lk]
        blocks.append(dict(kind='lever', key=lk, label=lbl, dbull=lv['d'][0], dbear=lv['d'][1],
                           base={y: v for y, v in zip(range(2027, 2031), lv['base'])}, note=note, fmt=lv.get('fmt', 'pct')))
    M.scen_table(9, 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', blocks)

    # ================================================================ SEGMENT BUILD
    M.add(style='section', label='SEGMENT P&L — AMERICAS · EMEA & APAC (organic × acquisitions × FX build) · EDDYFI (acquired 1-Jun-2026)',
          note='SEGMENT BUILD — modelling logic (prior-year net sales × (1 + organic + acquisitions + FX) → segment adjusted EBITDA; Eddyfi modelled separately from Q3/26E)')
    M.blank()
    acq_q, fx_q = CFG['acq_q'], CFG['fx_q']
    for s, short, long in SEGS:
        hs = has(f'seg_{s}_net_sales')
        M.add(style='block', label=long, note=f'{short.upper()} — modelling logic')
        M.add(f'{s}_sales', '  Net sales', 'sub', 'num', hist=H(f'seg_{s}_net_sales'),
              qfc=f'=[{s}_sales@py]*(1+[{s}_g])',
              afc=lambda c, s=s: f'=SUMQ[{s}_sales]' if c.year == 2026 else f'=([{s}_sales@py]-N([{s}_edd@py]))*(1+[{s}_g])',
              cagr='growth', comment='Source: ESAB earnings releases (Form 8-K Ex. 99.1) segment adjusted-EBITDA reconciliation and 10-K / 10-Q segment notes; 2019–21 from the Form 10 (carve-out) and 2022 comparatives.',
              note='Historical: as reported (Q2/26 includes one month of Eddyfi). Q3/Q4-26E: legacy business only = prior-year quarter × (1 + organic + acquisitions + FX); Eddyfi in its own block. 2027E+: legacy 2026E (ex-Eddyfi June) × (1 + organic lever + FX).')
        M.add(f'{s}_g', '  Net sales y/y %', 'pct', 'pct', hist=yoy(f'{s}_sales', hs), qfc=f'=[{s}_org]+[{s}_acq]+[{s}_fx]',
              afc=lambda c, s=s: f'=IFERROR([{s}_sales]/[{s}_sales@py]-1,"")' if c.year == 2026 else f'=[{s}_org]+[{s}_acq]+[{s}_fx]')
        M.add(f'{s}_org', '  Organic growth % (company; price, mix & volume)', 'pctline', 'pct', hist=H(f'sc_{s}_organic_pct'),
              qfc=f'=[{s}_org@$Q2/26]+[cal_g]',
              afc=lambda c, s=s: f'=IFERROR([{s}_dorg]/[{s}_sales@py],"")' if c.year == 2026 else f'=SCEN({s}_org_{c.year})',
              note='Q3/Q4-26E: Q2/26 y/y organic + outlook calibration Δ. 2027E+: scenario lever. ESAB does not split organic growth into price and volume.',
              comment='Source: earnings-release "Change in Net Sales" table (existing businesses / acquisitions / foreign currency translation).')
        M.add(f'{s}_acq', '  Acquisitions % (excl. Eddyfi in forecast)', 'pctline', 'pct', hist=H(f'sc_{s}_acquisitions_pct'),
              qfc=lambda c, s=s: acq_q[s][c.label],
              afc=lambda c, s=s: f'=IFERROR([{s}_dacq]/[{s}_sales@py],"")' if c.year == 2026 else 0, note=CFG['notes']['acq_' + s])
        M.add(f'{s}_fx', '  Foreign currency translation %', 'pctline', 'pct', hist=H(f'sc_{s}_fx_pct'),
              qfc=lambda c, s=s: fx_q[s][c.label],
              afc=lambda c, s=s: f'=IFERROR([{s}_dfx]/[{s}_sales@py],"")' if c.year == 2026 else (f'=SCEN(EA_fx_{c.year})' if s == 'EA' else 0),
              note='Q3/Q4-26E: FX input (spot vs prior-year rates). 2027E+: EMEA & APAC FX lever; Americas 0%.')
        M.add(f'{s}_dorg', '  Δ Net sales — organic ($)', 'line', 'num', hist=H(f'sc_{s}_organic'),
              qfc=f'=[{s}_sales@py]*[{s}_org]', afc=lambda c, s=s: f'=SUMQ[{s}_dorg]' if c.year == 2026 else f'=([{s}_sales@py]-N([{s}_edd@py]))*[{s}_org]', outline=2)
        M.add(f'{s}_dacq', '  Δ Net sales — acquisitions ($)', 'line', 'num', hist=H(f'sc_{s}_acquisitions'),
              qfc=f'=[{s}_sales@py]*[{s}_acq]', afc=lambda c, s=s: f'=SUMQ[{s}_dacq]' if c.year == 2026 else 0, outline=2)
        M.add(f'{s}_dfx', '  Δ Net sales — FX ($)', 'line', 'num', hist=H(f'sc_{s}_fx'),
              qfc=f'=[{s}_sales@py]*[{s}_fx]', afc=lambda c, s=s: f'=SUMQ[{s}_dfx]' if c.year == 2026 else f'=([{s}_sales@py]-N([{s}_edd@py]))*[{s}_fx]', outline=2)
        M.add(f'{s}_edd', '  Memo: Eddyfi net sales included in the segment (from 1-Jun-2026)', 'line', 'num', hist=H(f'{s}_edd'),
              qfc=0, afc=lambda c, s=s: f'=SUMQ[{s}_edd]' if c.year == 2026 else 0, outline=2,
              note=CFG['notes']['edd_seg'])
        M.add(f'{s}_aebitda', '  Adjusted EBITDA (segment, company definition)', 'sub', 'num', hist=H(f'seg_{s}_adj_ebitda'),
              qfc=f'=[{s}_sales]*[{s}_m]',
              afc=lambda c, s=s: f'=SUMQ[{s}_aebitda]' if c.year == 2026 else f'=[{s}_aebitda@py]-N([{s}_edde@py])+[{s}_dbridge]',
              cagr='growth', note='2027E+: legacy prior-year adjusted EBITDA + Δ bridge (organic $ × incremental margin + FX $ × prior margin).',
              comment='Segment adjusted EBITDA = segment operating income + restructuring + acquisition-amortization & other + depreciation & other amortization (+ performance option awards from 2026).')
        M.add(f'{s}_edde', '  Memo: Eddyfi adjusted EBITDA included in the segment (estimate)', 'line', 'num', hist=H(f'{s}_edde'),
              qfc=0, afc=lambda c, s=s: f'=SUMQ[{s}_edde]' if c.year == 2026 else 0, outline=2,
              note='June 2026 Eddyfi sales × 2026E standalone margin (not separately disclosed).')
        M.add(f'{s}_m0', '  Adjusted EBITDA margin before outlook calibration % (Q3/Q4-26E helper)', 'pctline', 'pct',
              qfc=f'=[{s}_m@py]+([{s}_aebitda@$Q1/26]+[{s}_aebitda@$Q2/26]-[{s}_edde@$Q2/26])/([{s}_sales@$Q1/26]+[{s}_sales@$Q2/26]-[{s}_edd@$Q2/26])-([{s}_aebitda@$Q1/25]+[{s}_aebitda@$Q2/25])/([{s}_sales@$Q1/25]+[{s}_sales@$Q2/25])',
              note='Prior-year quarter margin + (1H/26 legacy − 1H/25 margin drift).')
        M.add(f'{s}_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', hist=ratio(f'{s}_aebitda', f'{s}_sales', hs),
              qfc=f'=[{s}_m0]+[cal_m]', afc=f'=IFERROR([{s}_aebitda]/[{s}_sales],"")', cagr='avg')
        M.add(f'{s}_inc', '  Incremental adjusted EBITDA margin (Δ adj. EBITDA / Δ net sales)', 'pct', 'pct',
              hist=lambda c, s=s, h=hs: (f'=IFERROR(([{s}_aebitda]-[{s}_aebitda@py])/([{s}_sales]-[{s}_sales@py]),"")' if (lay.py(c) and h(c) and h(lay.py(c))) else None),
              fc=f'=IFERROR(([{s}_aebitda]-[{s}_aebitda@py])/([{s}_sales]-[{s}_sales@py]),"")', outline=2)
        M.add(f'{s}_vi', '  Organic incremental adjusted EBITDA margin % (input)', 'pct', 'pct',
              afc=lambda c, v=CFG['incr'][s]: None if c.year == 2026 else v, outline=2,
              note='Input: incremental margin on organic sales growth (EBXai productivity; ESAB delivered ~30–35% organic incrementals in 2023–25).')
        M.add(f'{s}_dbridge', '  Δ Adjusted EBITDA (organic × incremental + FX × prior margin)', 'line', 'num',
              afc=lambda c, s=s: None if c.year == 2026 else f'=[{s}_dorg]*[{s}_vi]+[{s}_dfx]*[{s}_m@py]', outline=2)
        M.add(f'{s}_oi', '  Operating income (GAAP, segment)', 'line', 'num', hist=H(f'seg_{s}_operating_income'), outline=2,
              note='Historical disclosure only.')
        M.add(f'{s}_restr', '  Restructuring & other related charges (segment)', 'line', 'num', hist=H(f'seg_{s}_restructuring'), outline=2)
        M.add(f'{s}_acqam', '  Acquisition-amortization & other related charges (segment)', 'line', 'num', hist=H(f'seg_{s}_acq_amort_other'), outline=2)
        M.add(f'{s}_da', '  Depreciation & other amortization (segment)', 'line', 'num', hist=H(f'seg_{s}_da_other'), outline=2)
        if s == 'EA':
            M.add('ru_sales', '  Memo: Russia net sales (excluded from "core")', 'line', 'num', hist=H('russia_sales'),
                  qfc='=([ru_sales@$Q1/26]+[ru_sales@$Q2/26])/2', afc=lambda c: '=SUMQ[ru_sales]' if c.year == 2026 else '=[ru_sales@py]*(1+SCEN(EA_fx_%d))' % c.year,
                  note='ESAB continues to operate in Russia (in-country for in-country); excluded from "core" metrics. Forecast: 1H/26 run-rate, then flat (FX only).')
            M.add('ru_ebitda', '  Memo: Russia adjusted EBITDA', 'line', 'num', hist=H('pub_russia_ebitda'),
                  qfc='=([ru_ebitda@$Q1/26]+[ru_ebitda@$Q2/26])/2', afc=lambda c: '=SUMQ[ru_ebitda]' if c.year == 2026 else '=[ru_sales]*[ru_ebitda@py]/[ru_sales@py]')
        M.blank()

    # product lines
    M.add(style='block', label='Product lines (memo; revenue disaggregation — 10-K / 10-Q)', note='PRODUCT LINES — historical disclosure only')
    M.add('pl_eq', '  Equipment net sales', 'line', 'num', hist=H('pl_equipment'), cagr='growth')
    M.add('pl_cons', '  Consumables net sales', 'line', 'num', hist=H('pl_consumables'), cagr='growth')
    M.add('pl_eq_pct', '  Equipment % of net sales', 'pctline', 'pct', hist=lambda c: '=IFERROR([pl_eq]/([pl_eq]+[pl_cons]),"")' if c.label in S.get('pl_equipment', {}) else None)
    M.blank()

    # Colfax memo
    M.add(style='block', label='Pre-spin history (memo): Colfax "Fabrication Technology" segment as reported by Colfax (2012–2021; Colfax 10-K filings)',
          note='COLFAX FABRICATION TECHNOLOGY — ESAB under Colfax ownership (not the carve-out basis); for long-run context only')
    for k, lbl in (('net_sales', 'net sales'), ('segment_operating_income', 'segment operating income (before restructuring & certain other charges)'), ('adjusted_ebita', 'adjusted EBITA (segment operating income + acquisition amortization; disclosed from FY2019 10-K)'),
                   ('organic_pct', 'organic growth % (existing businesses)'), ('acquisitions_pct', 'acquisitions %'), ('fx_pct', 'foreign currency %')):
        M.add(f'cfx_{k}', f'  Fabrication Technology — {lbl}', 'pctline' if k.endswith('pct') else 'line', 'pct' if k.endswith('pct') else 'num',
              hist=lambda c, k=k: S.get('cfx_' + k, {}).get(c.label) if c.kind == 'A' else None, outline=2,
              cagr='growth' if k == 'net_sales' else None)
    M.add('cfx_m', '  Fabrication Technology — segment operating margin %', 'pctline', 'pct',
          hist=lambda c: '=IFERROR([cfx_segment_operating_income]/[cfx_net_sales],"")' if c.label in S.get('cfx_net_sales', {}) else None, outline=2)
    M.blank()

    # Eddyfi
    M.add(style='block', label='EDDYFI TECHNOLOGIES — advanced inspection & monitoring (NDT); acquired 1-Jun-2026 for $1.45bn; reported across both segments',
          note='EDDYFI — modelling logic (closed 1-Jun-2026; in company FY26 guidance)')
    M.add('edd_sa_sales', '  Memo: Eddyfi standalone net sales (pre-acquisition; not consolidated)', 'line', 'num',
          hist=lambda c: E['standalone_sales'].get(str(c.label)), outline=0, note=E['note_standalone'])
    M.add('edd_sa_ebitda', '  Memo: Eddyfi standalone EBITDA (pre-acquisition)', 'line', 'num', hist=lambda c: E['standalone_ebitda'].get(str(c.label)))
    M.add('edd_days', '  Days consolidated in period (closing 1-Jun-2026)', 'line', 'num', hist=lambda c: E['days'].get(str(c.label)),
          qfc=lambda c: E['days'][str(c.label)], afc=lambda c: '=SUMQ[edd_days]' if c.year == 2026 else 365,
          note='Q2/26: 1-Jun to 3-Jul (33 days, inside the segment actuals). Q3/26E 91 days, Q4/26E 90 days.')
    M.add('edd_rr', '  Annual net sales run-rate (standalone basis)', 'line', 'num', afc=lambda c: E['rr_2026'] if c.year == 2026 else f'=[edd_rr@py]*(1+[edd_g])',
          note='2026E: company deal metric ~$270m 2026E revenue. 2027E+: × (1 + scenario lever EDD_g; company: high-single-digit organic growth).')
    M.add('edd_g', '  Sales growth y/y %', 'pctline', 'pct', afc=lambda c: None if c.year == 2026 else f'=SCEN(EDD_g_{c.year})')
    M.add('edd_rev', '  Net sales (consolidated from closing)', 'sub', 'num', hist=lambda c: E['in_segment_q2_total'] if c.label == 'Q2/26' else None,
          qfc='=[edd_rr@$2026E]*[edd_days]/365', afc=lambda c: '=SUMQ[edd_rev]' if c.year == 2026 else '=[edd_rr]',
          note='Q2/26 (memo) = June 2026 contribution already inside the segment actuals; Q3/26E onward added in the group build.')
    M.add('edd_m', '  Standalone adjusted EBITDA margin % (before synergies)', 'pctline', 'pct',
          afc=lambda c: E['margin_2026'] if c.year == 2026 else f'=SCEN(EDD_m_{c.year})', note='Deal metrics: ~$80m adjusted EBITDA on ~$270m 2026E revenue (29.6%); gross margin > 65%.')
    M.add('edd_syn', '  (+) Cost synergies realised ($20m run-rate target)', 'line', 'num', qfc=0,
          afc=lambda c: '=SUMQ[edd_syn]' if c.year == 2026 else f'={E["synergies"]}*SCEN(EDD_syn_{c.year})',
          note='Company: $20m annualized run-rate synergies ($100m adjusted EBITDA incl. synergies).')
    M.add('edd_ebitda', '  Adjusted EBITDA (consolidated)', 'sub', 'num', qfc='=[edd_rev]*[edd_m@$2026E]+[edd_syn]',
          afc=lambda c: '=SUMQ[edd_ebitda]' if c.year == 2026 else '=[edd_rev]*[edd_m]+[edd_syn]')
    M.add('edd_ebitda_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', fc='=IFERROR([edd_ebitda]/[edd_rev],"")')
    M.add('edd_amort', '  (−) Purchase-accounting amortization of acquired intangibles (added back in adjusted EBITDA / adjusted EPS)', 'line', 'num',
          qfc=f'={E["ppa_amort"]["2026"]}*[edd_days]/365', afc=lambda c: '=SUMQ[edd_amort]' if c.year == 2026 else E['ppa_amort'][str(c.year)],
          note=E['note_amort'])
    M.add('edd_step', '  (−) Inventory fair-value step-up expensed', 'line', 'num', qfc=lambda c: E['stepup_q'][c.label],
          afc=lambda c: '=SUMQ[edd_step]' if c.year == 2026 else 0, note=E['note_step'])
    M.add('edd_da_pct', '  Standalone D&A (depreciation & other amortization) % of sales', 'pctline', 'pct', fc=E['da_pct'])
    M.add('edd_da', '  Standalone D&A (in depreciation & other amortization)', 'line', 'num', fc='=[edd_rev]*[edd_da_pct]')
    M.blank()

    # future M&A
    mc = CFG['ma']
    M.add(style='block', label='Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)', note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention')
    M.add('ma_spend', '  Acquisition spend (USDm, scenario)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else f'=MAX(0,SCEN(MA_spend_{c.year}))',
          note='ESAB deployed ~$50–300m p.a. on bolt-ons in 2022–25 (gas control, automation, cutting; e.g. Ohio Medical, SUMIG, Bavaria, DeltaP, Aktiv); Base pauses in 2027E to delever after Eddyfi.')
    M.add('ma_mult', '  Purchase multiple — EV / sales (x)', 'line', 'x', afc=lambda c: None if c.year == 2026 else mc['mult'])
    M.add('ma_acq_sales', '  Annualised sales acquired in the year', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=IFERROR([ma_spend]/[ma_mult],0)')
    M.add('ma_growth', '  Growth of acquired businesses after acquisition %', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['growth'])
    M.add('ma_rr', '  Run-rate sales of businesses acquired (year end)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rr@py]*(1+[ma_growth])+[ma_acq_sales]')
    M.add('ma_rev', '  Net sales from future acquisitions', 'sub', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rr@py]*(1+[ma_growth])+[ma_acq_sales]*0.5')
    M.add('ma_m', '  Adjusted EBITDA margin of acquired businesses %', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['margin'])
    M.add('ma_ebitda', '  Adjusted EBITDA from future acquisitions', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rev]*[ma_m]')
    M.add('ma_da_pct', '  Depreciation & other amortization % of acquired sales', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['da_pct'])
    M.add('ma_da', '  Depreciation & other amortization from future acquisitions', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rev]*[ma_da_pct]')
    M.add('ma_ppe_pct', '  PP&E % of spend', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['ppe_pct'])
    M.add('ma_int_pct', '  Acquired intangibles % of spend', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['int_pct'])
    M.add('ma_life', '  Intangible amortization life (years)', 'line', 'num1', afc=lambda c: None if c.year == 2026 else mc['life'])
    M.add('ma_cum_int', '  Cumulative acquired intangibles (gross)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_cum_int@py]+[ma_spend]*[ma_int_pct]')
    M.add('ma_amort', '  Amortization of future-acquisition intangibles (adjusted out)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=([ma_cum_int@py]+[ma_spend]*[ma_int_pct]*0.5)/[ma_life]')
    M.blank()

    # ================================================================ GROUP
    M.add(style='block', label="Group Total — net sales & adjusted EBITDA (segment build + Eddyfi) → core (ex-Russia) metrics (ESAB's primary KPIs)",
          note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    hseg = has('seg_AM_net_sales')
    M.add('g_sales', 'Net sales (segment build)', 'total', 'num', hist=lambda c: '=N([AM_sales])+N([EA_sales])' if hseg(c) else None,
          qfc='=N([AM_sales])+N([EA_sales])+N([edd_rev])', afc=lambda c: '=SUMQ[g_sales]' if c.year == 2026 else '=N([AM_sales])+N([EA_sales])+N([edd_rev])+N([ma_rev])',
          cagr='growth', note='Σ Americas + EMEA & APAC (+ Eddyfi from Q3/26E + future M&A). 2026E = sum of quarters.')
    M.add('g_aebitda', 'Adjusted EBITDA (segment build)', 'total', 'num', hist=lambda c: '=N([AM_aebitda])+N([EA_aebitda])' if has('seg_AM_adj_ebitda')(c) else None,
          qfc='=N([AM_aebitda])+N([EA_aebitda])+N([edd_ebitda])', afc=lambda c: '=SUMQ[g_aebitda]' if c.year == 2026 else '=N([AM_aebitda])+N([EA_aebitda])+N([edd_ebitda])+N([ma_ebitda])', cagr='growth')
    M.add('g_m', '  Adjusted EBITDA margin %', 'pctline', 'pct', hist=ratio('g_aebitda', 'g_sales', hseg), fc='=IFERROR([g_aebitda]/[g_sales],"")')
    M.add('chk_gsales', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'num',
          hist=lambda c: '=ROUND([g_sales]-[is_sales],1)' if hseg(c) else None, fc='=ROUND([g_sales]-[is_sales],1)')
    M.add('chk_gaebitda', '  Check: segment build vs adjusted EBITDA bridge (should be 0)', 'check', 'num',
          hist=lambda c: '=ROUND([g_aebitda]-[aebitda],1)' if has('seg_AM_adj_ebitda')(c) else None, fc='=ROUND([g_aebitda]-[aebitda],1)')
    hru = has('russia_sales')
    M.add('core_sales', 'Core net sales (ex-Russia)', 'sub', 'num', hist=lambda c: '=[g_sales]-[ru_sales]' if hru(c) and hseg(c) else None,
          fc='=[g_sales]-[ru_sales]', cagr='growth')
    M.add('core_g', '  Core net sales y/y %', 'pct', 'pct', hist=yoy('core_sales', lambda c: hru(c) and hseg(c)), fc='=IFERROR([core_sales]/[core_sales@py]-1,"")')
    M.add('core_org', '  Core organic growth % (company)', 'pctline', 'pct', hist=H('csc_TOT_organic_pct'),
          fc='=IFERROR(([AM_dorg]+[EA_dorg])/[core_sales@py],"")', note='Forecast approximation: Σ segment organic $ ÷ prior-year core sales.')
    M.add('core_ebitda', 'Core adjusted EBITDA (ex-Russia)', 'sub', 'num', hist=lambda c: '=[g_aebitda]-[ru_ebitda]' if hru(c) and hseg(c) else None,
          fc='=[g_aebitda]-[ru_ebitda]', cagr='growth')
    M.add('core_m', '  Core adjusted EBITDA margin %', 'pctline', 'pct', hist=lambda c: '=IFERROR([core_ebitda]/[core_sales],"")' if hru(c) and hseg(c) else None,
          fc='=IFERROR([core_ebitda]/[core_sales],"")')
    M.add('out_g', '  Memo: FY26 core sales growth outlook — 11–14% (scenario end-point)', 'pctline', 'pct', afc=lambda c: '=SCEN(G26)' if c.year == 2026 else None)
    M.add('out_core_sales', '  Memo: FY26 core net sales implied by the outlook end-point', 'line', 'num', afc=lambda c: '=[core_sales@py]*(1+[out_g])' if c.year == 2026 else None)
    M.add('pre_sales', '  Legacy net sales before outlook calibration (Q3/Q4-26E helper)', 'line', 'num',
          qfc='=' + '+'.join(f'[{s}_sales@py]*(1+[{s}_org@$Q2/26]+[{s}_acq]+[{s}_fx])' for s, _, _ in SEGS))
    M.add('sens_sales', '  Net sales sensitivity to +1.00 of organic growth (Q3/Q4-26E helper)', 'line', 'num', qfc='=' + '+'.join(f'[{s}_sales@py]' for s, _, _ in SEGS))
    M.add('cal_g', '  Outlook calibration: Δ organic growth applied uniformly to the segments (Q3/Q4-26E)', 'pctline', 'pct',
          qfc='=([out_core_sales@$2026E]+[ru_sales@$2026E]-[is_sales@$Q1/26]-[is_sales@$Q2/26]-[edd_rev@$Q3/26E]-[edd_rev@$Q4/26E]-[pre_sales@$Q3/26E]-[pre_sales@$Q4/26E])/([sens_sales@$Q3/26E]+[sens_sales@$Q4/26E])',
          note='Solves the uniform organic shift so that FY26 core net sales = outlook end-point (core = ex-Russia; Russia at 1H run-rate).')
    M.add('chk_out_sales', '  Check: FY26 core net sales vs outlook end-point (should be 0)', 'check', 'num', afc=lambda c: '=ROUND([core_sales]-[out_core_sales],1)' if c.year == 2026 else None)
    M.add('out_eb', '  Memo: FY26 core adjusted EBITDA outlook — $615–625m (scenario end-point)', 'line', 'num', afc=lambda c: '=SCEN(EB26)' if c.year == 2026 else None)
    M.add('pre_aebitda', '  Adjusted EBITDA before margin calibration (Q3/Q4-26E helper)', 'line', 'num',
          qfc='=' + '+'.join(f'[{s}_sales]*[{s}_m0]' for s, _, _ in SEGS) + '+[edd_ebitda]')
    M.add('cal_m', '  Outlook calibration: Δ adjusted EBITDA margin applied to the legacy segments (Q3/Q4-26E)', 'pctline', 'pct',
          qfc='=([out_eb@$2026E]+[ru_ebitda@$2026E]-[g_aebitda@$Q1/26]-[g_aebitda@$Q2/26]-[pre_aebitda@$Q3/26E]-[pre_aebitda@$Q4/26E])/(' + '+'.join(f'[{s}_sales@$Q3/26E]+[{s}_sales@$Q4/26E]' for s, _, _ in SEGS) + ')',
          note='Solves the uniform margin shift so that FY26 core adjusted EBITDA = outlook end-point (Eddyfi at deal-metric margin).')
    M.add('chk_out_eb', '  Check: FY26 core adjusted EBITDA vs outlook end-point (should be 0)', 'check', 'num', afc=lambda c: '=ROUND([core_ebitda]-[out_eb],1)' if c.year == 2026 else None)
    M.add('out_eps', '  Memo: FY26 core adjusted EPS outlook — $5.40–5.50 (scenario end-point; compare with the model)', 'line', 'eps', afc=lambda c: '=SCEN(EPS26)' if c.year == 2026 else None)
    M.blank()

    # ================================================================ COST DRIVERS
    M.add(style='block', label='Cost drivers, D&A & adjusting items', note='COST DRIVERS — inputs that drive forecast cost lines')
    M.add('da_oth', '  Depreciation & other amortization (excl. acquired-intangible amortization)', 'line', 'num', hist=H('br_da'),
          qfc='=([da_oth@$Q1/26]+[da_oth@$Q2/26])/2+[edd_da]', afc=lambda c: '=SUMQ[da_oth]' if c.year == 2026 else '=([is_sales]-[edd_rev]-[ma_rev])*[da_pct]+[edd_da]+[ma_da]',
          note='Q3/Q4-26E: 1H/26 run-rate + Eddyfi standalone D&A. 2027E+: legacy sales × % + Eddyfi + future M&A.')
    M.add('da_pct', '  Depreciation & other amortization (legacy) % of net sales', 'pctline', 'pct', hist=ratio('da_oth', 'is_sales', has('br_da')),
          afc=lambda c: '=IFERROR([da_oth]/[is_sales],"")' if c.year == 2026 else CFG['da_pct'])
    M.add('amort', '  Amortization of acquired intangibles & inventory step-up (adjusted out)', 'line', 'num', hist=H('br_amort'),
          qfc=f'={CFG["legacy_amort_q"]}+[edd_amort]+[edd_step]', afc=lambda c: '=SUMQ[amort]' if c.year == 2026 else f'={CFG["legacy_amort"][str(c.year)]}+[edd_amort]+[ma_amort]',
          note=CFG['notes']['amort'])
    M.add('txn', '  Acquisition transaction, diligence & integration costs (adjusted out)', 'line', 'num', hist=H('br_txn'),
          qfc=lambda c: CFG['txn_q'][c.label], afc=lambda c: '=SUMQ[txn]' if c.year == 2026 else CFG['txn_fc'][str(c.year)], note=CFG['notes']['txn'])
    M.add('perf', '  Performance option awards compensation (adjusted out; granted Jun/Jul-2026)', 'line', 'num', hist=H('br_perf'),
          qfc=lambda c: CFG['perf_q'][c.label], afc=lambda c: '=SUMQ[perf]' if c.year == 2026 else CFG['perf_fc'][str(c.year)], note=CFG['notes']['perf'])
    M.add('sga_pct', '  SG&A % of net sales', 'pctline', 'pct', hist=ratio('is_sga', 'is_sales'),
          qfc='=[sga_pct@py]+([is_sga@$Q1/26]+[is_sga@$Q2/26])/([is_sales@$Q1/26]+[is_sales@$Q2/26])-([is_sga@$Q1/25]+[is_sga@$Q2/25])/([is_sales@$Q1/25]+[is_sales@$Q2/25])',
          afc=lambda c: '=IFERROR([is_sga]/[is_sales],"")' if c.year == 2026 else CFG['sga_pct'], cagr='avg',
          note='Splits gross profit vs SG&A only (operating income is driven by the adjusted EBITDA build).')
    M.add('sbc_pct', '  Stock-based compensation % of net sales', 'pctline', 'pct', hist=ratio('cf_sbc', 'is_sales', has('cf_sbc')),
          qfc='=([cf_sbc@$Q1/26]+[cf_sbc@$Q2/26])/([is_sales@$Q1/26]+[is_sales@$Q2/26])', afc=lambda c: '=IFERROR([is_sbc]/[is_sales],"")' if c.year == 2026 else CFG['sbc_pct'])
    M.blank()
    return M, wb, ws, t
