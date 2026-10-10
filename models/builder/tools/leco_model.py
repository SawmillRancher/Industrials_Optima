"""Build the Lincoln Electric (LECO) model in the MLM template format."""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl
from openpyxl.utils import get_column_letter as L
from openpyxl.comments import Comment
from mbuild import Model, Layout, NF
import leco_data as D

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, '..', 'MLM_template.xlsx')
REF = json.load(open(os.path.join(HERE, '..', 'leco', 'extract', 'REFERENCE_2026.json'))) if os.path.exists(
    os.path.join(HERE, '..', 'leco', 'extract', 'REFERENCE_2026.json')) else {}
CFG = json.load(open(os.path.join(HERE, 'leco_cfg.json')))

P, S, NOTES = D.build()
CF = D.cf_discrete(S)
for k, v in CF.items():
    S['cf_' + k] = v
import leco_prep
leco_prep.prep(S, None)

lay = Layout(range(2006, 2013), range(2013, 2026), 2026, 2, range(2027, 2031))
SEGS = [('AW', 'Americas Welding', 'Americas Welding (arc-welding equipment, consumables, automation & cutting — North and South America)'),
        ('IW', 'International Welding', 'International Welding (welding & cutting — Europe, Middle East, Africa, Asia Pacific)'),
        ('HPG', 'Harris Products Group', 'The Harris Products Group (brazing & soldering alloys, oxy-fuel cutting, gas regulators; US retail channel)')]


def H(key, scale=1.0, cols=None):
    d = S.get(key, {})

    def f(c):
        v = d.get(c.label)
        if v is None:
            return None
        if cols and not cols(c):
            return None
        return v * scale
    return f


def has(key):
    d = S.get(key, {})
    return lambda c: c.label in d and d[c.label] is not None


def yoy(key, guard=None):
    def f(c):
        p = lay.py(c)
        if p is None:
            return None
        if guard and not (guard(c) and guard(p)):
            return None
        return f'=IF(AND(ISNUMBER([{key}]),ISNUMBER([{key}@py])),IFERROR([{key}]/[{key}@py]-1,""),"")'
    return f


def ratio(a, b, guard=None):
    def f(c):
        if guard and not guard(c):
            return None
        return f'=IF(AND(ISNUMBER([{a}]),ISNUMBER([{b}])),IFERROR([{a}]/[{b}],""),"")'
    return f


def when(cond, a, b=None):
    return lambda c: (a(c) if callable(a) else a) if cond(c) else ((b(c) if callable(b) else b) if b is not None else None)


Y26 = lambda c: c.year == 2026
SUMQ = lambda k: f'=SUMQ[{k}]'


def afc_26(sum_formula, later):
    return lambda c: sum_formula if c.year == 2026 else (later(c) if callable(later) else later)


def build(out_path, scenario='Base'):
    wb = openpyxl.load_workbook(TEMPLATE)
    t = wb['Model']
    ws = wb.create_sheet('Model_new')
    M = Model(wb, t, ws, lay)
    sc = CFG['scenario']

    # ------------------------------------------------------------------ scenario table first (row numbers)
    blocks = [
        dict(kind='hdr', label='FY26 outlook — Q2-26 earnings call (30-Jul-26); company assumptions', note='Lincoln Electric gives qualitative / range outlook on its earnings call (not in the 8-K). Captured from call coverage; IR site & slides not reachable from this environment — verify against the Q2-26 presentation.'),
        dict(kind='pt', key='G26', label='  FY26 net sales growth — "low double-digit %"', bull=sc['G26'][0], base=sc['G26'][1], bear=sc['G26'][2], fmt='pct', note='Raised on the Q2-26 call to low double-digit (from mid-to-high single digit). 1H/26 +11.9%. Drives the Q3/Q4-26E volume calibration.'),
        dict(kind='pt', key='ORG26', label='  FY26 organic sales growth — "high single-digit to low double-digit" (memo)', bull=sc['ORG26'][0], base=sc['ORG26'][1], bear=sc['ORG26'][2], fmt='pct', note='~1/3 volume, ~2/3 price per management. Memo / cross-check only.'),
        dict(kind='pt', key='INC26', label='  2H/26 incremental adjusted operating income margin — "mid-20%"', bull=sc['INC26'][0], base=sc['INC26'][1], bear=sc['INC26'][2], fmt='pct', note='Q2-26 call: adjusted operating margin to improve y/y at mid-20% incrementals in 2H; price/cost neutral in 2H. Drives the Q3/Q4-26E margin calibration.'),
        dict(kind='pt', key='INT26', label='  FY26 interest expense, net ($m)', bull=sc['INT26'][0], base=sc['INT26'][1], bear=sc['INT26'][2], fmt='num1', note='Company assumption $50–55m (maintained on the Q2-26 call).'),
        dict(kind='pt', key='TAX26', label='  FY26 effective tax rate — "low-to-mid 20%"', bull=sc['TAX26'][0], base=sc['TAX26'][1], bear=sc['TAX26'][2], fmt='pct', note='Company assumption (adjusted ETR). 1H/26 22.7% adjusted.'),
        dict(kind='pt', key='CAPEX26', label='  FY26 capital expenditures ($m)', bull=sc['CAPEX26'][0], base=sc['CAPEX26'][1], bear=sc['CAPEX26'][2], fmt='num', note='Company assumption $110–130m.'),
        dict(kind='pt', key='CONV26', label='  FY26 cash conversion (FCF / adjusted net income; memo)', bull=1.0, base=1.0, bear=1.0, fmt='pct', note='Company target ~100% cash conversion.'),
        dict(kind='hdr', label='Capital returns', cols=('Bull', 'Base', 'Bear'), note=None),
        dict(kind='pt', key='BB26', label='  2H/26 share repurchases ($m)', bull=sc['BB26'][0], base=sc['BB26'][1], bear=sc['BB26'][2], fmt='num', note='1H/26 repurchases $133m (Q1 $57m, Q2 $76m). Base keeps the 1H pace.'),
        dict(kind='pt', key='LEV', label='  Minimum net debt / Adjusted EBITDA (x) — buyback floor 2027E+', bull=sc['LEV'][0], base=sc['LEV'][1], bear=sc['LEV'][2], fmt='x2', note='LECO runs ~0.5–1.0x net leverage; surplus cash above the floor is returned through repurchases.'),
    ]
    for lk, lbl, note in CFG['levers']:
        lv = CFG['lever_values'][lk]
        blocks.append(dict(kind='lever', key=lk, label=lbl, dbull=lv['d'][0], dbear=lv['d'][1],
                           base={y: v for y, v in zip(range(2027, 2031), lv['base'])}, note=note,
                           fmt=lv.get('fmt', 'pct')))
    M.scen_table(9, 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', blocks)

    def SC(k):
        return f'SCEN({k})'

    def lever(k):
        return lambda c: f'=SCEN({k}_{c.year})'

    # ------------------------------------------------------------------ SEGMENT BUILD
    M.add(style='section', label='SEGMENT P&L — AMERICAS WELDING · INTERNATIONAL WELDING · THE HARRIS PRODUCTS GROUP (volume × price × acquisitions × FX build)',
          note='SEGMENT BUILD — modelling logic (prior-year net sales × (1 + volume + price + acquisitions + FX) → total segment sales × adjusted EBIT margin → group adjusted EBIT)')
    M.blank()
    acq_q = CFG['acq_q']   # per segment Q3/Q4-26E acquisition contribution inputs
    for s, short, long in SEGS:
        segsales = S.get(f'seg_{s}_net_sales', {})
        hseg = lambda c, d=segsales: c.label in d
        sc_has = S.get(f'sc_{s}_volume_pct', {})
        hsc = lambda c, d=sc_has: c.label in d
        M.add(style='block', label=long, note=f'{short.upper()} — modelling logic')
        M.add(f'{s}_sales', '  Net sales (external customers)', 'sub', 'num',
              hist=H(f'seg_{s}_net_sales'),
              qfc=f'=[{s}_sales@py]*(1+[{s}_g])',
              afc=lambda c, s=s: f'=SUMQ[{s}_sales]' if c.year == 2026 else f'=[{s}_sales@py]*(1+[{s}_g])',
              cagr='growth', outline=0,
              note=f'Historical: segment table of the earnings release (current 3-segment basis from FY2013 / Q1-14, per the Feb-2016 recast 8-K). Q3/Q4-26E: prior-year quarter × (1 + volume + price + acquisitions + FX). 2027E+: prior year × (1 + scenario levers {s}_vol + {s}_price (+ FX)).',
              comment=f'Source: Lincoln Electric earnings releases (Form 8-K Ex. 99.1) "Segment Highlights" — Net sales (external). 2013–Q3/15 on the recast 3-segment basis (8-K 10-Feb-2016 Ex. 99.1; no 2013 quarters recast — FY2013 only).')
        M.add(f'{s}_g', '  Net sales y/y %', 'pct', 'pct', hist=yoy(f'{s}_sales', hseg),
              qfc=f'=[{s}_vol]+[{s}_price]+[{s}_acq]+[{s}_fx]',
              afc=lambda c, s=s: f'=IFERROR([{s}_sales]/[{s}_sales@py]-1,"")' if c.year == 2026 else f'=[{s}_vol]+[{s}_price]+[{s}_acq]+[{s}_fx]')
        M.add(f'{s}_vol', '  Volume % (company "change in net sales due to volume")', 'pctline', 'pct',
              hist=H(f'sc_{s}_volume_pct'),
              qfc=f'=[{s}_vol@$Q2/26]+[cal_g]',
              afc=lambda c, s=s: f'=IFERROR([{s}_dvol]/[{s}_sales@py],"")' if c.year == 2026 else f'=SCEN({s}_vol_{c.year})',
              note=f'Q3/Q4-26E: Q2/26 y/y volume + outlook calibration Δ (Group block). 2027E–2030E: scenario lever {s}_vol (Bull/Base/Bear table →).',
              comment='Source: earnings-release table "Change in Net Sales by Segment" (volume, price, acquisitions, foreign exchange). Segment-level split published from Q1/16 (3-segment basis); consolidated split back to 2006.')
        M.add(f'{s}_price', '  Price %', 'pctline', 'pct', hist=H(f'sc_{s}_price_pct'),
              qfc=f'=[{s}_price@$Q2/26]',
              afc=lambda c, s=s: f'=IFERROR([{s}_dprice]/[{s}_sales@py],"")' if c.year == 2026 else f'=SCEN({s}_price_{c.year})',
              note='Q3/Q4-26E: Q2/26 y/y price held (carry-over of the 2025–26 increases; HPG includes metals pass-through). 2027E+: scenario lever. Note: 2016 Americas Welding as published includes Venezuela hyperinflationary price (+15.4%) offset by FX (−17.7%); ex-Venezuela price −0.5%, FX −1.0%.')
        M.add(f'{s}_acq', '  Acquisitions %', 'pctline', 'pct', hist=H(f'sc_{s}_acquisitions_pct'),
              qfc=lambda c, s=s: acq_q[s][c.label],
              afc=lambda c, s=s: f'=IFERROR([{s}_dacq]/[{s}_sales@py],"")' if c.year == 2026 else 0,
              note=CFG['acq_note'][s])
        M.add(f'{s}_fx', '  Foreign exchange %', 'pctline', 'pct', hist=H(f'sc_{s}_fx_pct'),
              qfc=lambda c, s=s: CFG['fx_q'][s][c.label],
              afc=lambda c, s=s: f'=IFERROR([{s}_dfx]/[{s}_sales@py],"")' if c.year == 2026 else (f'=SCEN(IW_fx_{c.year})' if s == 'IW' else 0),
              note='Q3/Q4-26E: FX input (spot-rate translation vs prior-year quarter). 2027E+: International Welding FX lever; Americas & Harris 0%.')
        M.add(f'{s}_org', '  Organic growth % (volume + price)', 'pctline', 'pct',
              hist=lambda c, s=s, h=hsc: f'=[{s}_vol]+[{s}_price]' if h(c) else None,
              fc=f'=[{s}_vol]+[{s}_price]')
        M.add(f'{s}_dvol', '  Δ Net sales — volume ($)', 'line', 'num', hist=H(f'sc_{s}_volume'),
              qfc=f'=[{s}_sales@py]*[{s}_vol]', afc=lambda c, s=s: f'=SUMQ[{s}_dvol]' if c.year == 2026 else f'=[{s}_sales@py]*[{s}_vol]', outline=2)
        M.add(f'{s}_dprice', '  Δ Net sales — price ($)', 'line', 'num', hist=H(f'sc_{s}_price'),
              qfc=f'=[{s}_sales@py]*[{s}_price]', afc=lambda c, s=s: f'=SUMQ[{s}_dprice]' if c.year == 2026 else f'=[{s}_sales@py]*[{s}_price]', outline=2)
        M.add(f'{s}_dacq', '  Δ Net sales — acquisitions ($)', 'line', 'num', hist=H(f'sc_{s}_acquisitions'),
              qfc=f'=[{s}_sales@py]*[{s}_acq]', afc=lambda c, s=s: f'=SUMQ[{s}_dacq]' if c.year == 2026 else f'=[{s}_sales@py]*[{s}_acq]', outline=2)
        M.add(f'{s}_dfx', '  Δ Net sales — foreign exchange ($)', 'line', 'num', hist=H(f'sc_{s}_fx'),
              qfc=f'=[{s}_sales@py]*[{s}_fx]', afc=lambda c, s=s: f'=SUMQ[{s}_dfx]' if c.year == 2026 else f'=[{s}_sales@py]*[{s}_fx]', outline=2)
        M.add(f'{s}_inter', '  Inter-segment sales', 'line', 'num', hist=H(f'seg_{s}_inter_segment'),
              qfc=f'=[{s}_sales]*[{s}_inter@py]/[{s}_sales@py]',
              afc=lambda c, s=s: f'=SUMQ[{s}_inter]' if c.year == 2026 else f'=[{s}_sales]*[{s}_inter@py]/[{s}_sales@py]',
              note='Forecast: prior-year inter-segment sales ratio to external net sales.', outline=2)
        M.add(f'{s}_tot', '  Total segment sales (incl. inter-segment)', 'line', 'num',
              hist=lambda c, s=s, h=hseg: f'=[{s}_sales]+N([{s}_inter])' if h(c) else None,
              fc=f'=[{s}_sales]+[{s}_inter]')
        M.add(f'{s}_aebit', '  Adjusted EBIT (segment profit, company definition)', 'sub', 'num', hist=H(f'seg_{s}_adj_ebit'),
              qfc=f'=[{s}_tot]*[{s}_m]',
              afc=lambda c, s=s: f'=SUMQ[{s}_aebit]' if c.year == 2026 else f'=[{s}_aebit@py]+[{s}_dbridge]',
              cagr='growth',
              note='2027E+: prior-year adjusted EBIT + Δ bridge (price $ × fall-through + volume $ × incremental margin + (acquisitions + FX) $ × prior-year margin). 2026E = sum of quarters.',
              comment='Source: earnings-release segment table — "EBIT, as adjusted" (to 2019) / "Adjusted EBIT" (2020+). EBIT = operating income + other income (+ equity earnings in affiliates while reported), adjusted for special items.')
        M.add(f'{s}_m0', '  Adjusted EBIT margin before outlook calibration % (Q3/Q4-26E helper)', 'pctline', 'pct',
              qfc=f'=[{s}_m@py]+([{s}_aebit@$Q1/26]+[{s}_aebit@$Q2/26])/([{s}_tot@$Q1/26]+[{s}_tot@$Q2/26])-([{s}_aebit@$Q1/25]+[{s}_aebit@$Q2/25])/([{s}_tot@$Q1/25]+[{s}_tot@$Q2/25])',
              note='Q3/Q4-26E: prior-year quarter margin + (1H/26 − 1H/25 margin drift).')
        M.add(f'{s}_m', '  Adjusted EBIT margin % (on total segment sales)', 'pctline', 'pct',
              hist=ratio(f'{s}_aebit', f'{s}_tot', hseg), qfc=f'=[{s}_m0]+[cal_m]',
              afc=f'=IFERROR([{s}_aebit]/[{s}_tot],"")', cagr='avg',
              note='Q3/Q4-26E: margin before calibration + outlook calibration Δ. 2027E+: output of the Δ adjusted EBIT bridge.')
        M.add(f'{s}_inc', '  Incremental adjusted EBIT margin (Δ adj. EBIT / Δ total sales)', 'pct', 'pct',
              hist=lambda c, s=s, h=hseg: (f'=IFERROR(([{s}_aebit]-[{s}_aebit@py])/([{s}_tot]-[{s}_tot@py]),"")' if (lay.py(c) and h(c) and h(lay.py(c))) else None),
              fc=f'=IFERROR(([{s}_aebit]-[{s}_aebit@py])/([{s}_tot]-[{s}_tot@py]),"")', outline=2)
        ft, vi = CFG['bridge'][s]
        M.add(f'{s}_ft', '  Price fall-through to adjusted EBIT %', 'pct', 'pct',
              afc=lambda c, v=ft: None if c.year == 2026 else v, outline=2,
              note='Input: share of price-driven sales growth that falls through to adjusted EBIT (price/cost broadly neutral — LECO prices to offset inflation; HPG price is largely metals pass-through).')
        M.add(f'{s}_vi', '  Volume incremental adjusted EBIT margin %', 'pct', 'pct',
              afc=lambda c, v=vi: None if c.year == 2026 else v, outline=2,
              note='Input: incremental margin on volume-driven sales (company targets mid-20s–30s% incrementals through the cycle).')
        M.add(f'{s}_dbridge', '  Δ Adjusted EBIT (price × fall-through + volume × incremental + (acq. + FX) × prior margin)', 'line', 'num',
              afc=lambda c, s=s: None if c.year == 2026 else f'=[{s}_dprice]*[{s}_ft]+[{s}_dvol]*[{s}_vi]+([{s}_dacq]+[{s}_dfx])*[{s}_m@py]', outline=2)
        M.add(f'{s}_sp', '  Special items (pre-tax, charged to the segment)', 'line', 'num', hist=H(f'seg_{s}_special_items'), outline=2,
              note='Historical disclosure only; forecast special items are modelled at the consolidated level.')
        M.add(f'{s}_ebit', '  EBIT (GAAP, as reported in the segment table)', 'line', 'num', hist=H(f'seg_{s}_ebit'), outline=2)
        M.blank()

    M.add(style='block', label='Corporate / eliminations', note='CORPORATE & ELIMINATIONS')
    hcorp = has('seg_CORP_adj_ebit')
    M.add('corp_inter', '  Inter-segment eliminations', 'line', 'num', hist=H('seg_CORP_inter_segment'),
          fc='=-([AW_inter]+[IW_inter]+[HPG_inter])')
    M.add('corp_aebit', '  Corporate / eliminations adjusted EBIT', 'line', 'num', hist=H('seg_CORP_adj_ebit'),
          qfc='=([corp_aebit@$Q1/26]+[corp_aebit@$Q2/26])/2',
          afc=lambda c: '=SUMQ[corp_aebit]' if c.year == 2026 else CFG['corp_aebit'],
          note=f'Q3/Q4-26E: 1H/26 run-rate. 2027E+: {CFG["corp_aebit"]:.0f} p.a. input (unallocated corporate costs net of inter-segment profit eliminations).')
    M.add('corp_sp', '  Corporate special items (pre-tax)', 'line', 'num', hist=H('seg_CORP_special_items'), outline=2)
    M.add('corp_ebit', '  Corporate / eliminations EBIT (GAAP)', 'line', 'num', hist=H('seg_CORP_ebit'), outline=2)
    M.blank()

    # legacy segments
    M.add(style='block', label='Legacy segments (memo; as originally reported — North America / Europe / Other Countries to 2008; five welding & Harris segments 2009–Q4/15)',
          note='LEGACY SEGMENTS — historical disclosure only (not forecast)')
    for lk, names, lbl in CFG['legacy']:
        for f, fl in (('net_sales', 'net sales'), ('adj_ebit', 'EBIT as adjusted')):
            vals = {}
            for nm in names:
                for colk, v in S.get(f'legacy::{nm}::{f}', {}).items():
                    vals[colk] = v
            M.add(f'leg_{lk}_{f}', f'  {lbl} — {fl}', 'line', 'num',
                  hist=lambda c, vals=vals: vals.get(c.label), outline=2)
    M.blank()

    # consolidated sales change
    M.add(style='block', label='Consolidated change in net sales (company table: volume · price · acquisitions · FX)',
          note='CONSOLIDATED SALES BRIDGE — historical as published; forecast = Σ segment $ effects ÷ prior-year net sales')
    for k, lbl in (('volume', 'Volume %'), ('price', 'Price %'), ('acquisitions', 'Acquisitions %'), ('fx', 'Foreign exchange %')):
        sk = {'volume': 'dvol', 'price': 'dprice', 'acquisitions': 'dacq', 'fx': 'dfx'}[k]
        extra = '+N([ma_rev])-N([ma_rev@py])' if k == 'acquisitions' else ''
        M.add(f'cons_{k}', f'  {lbl}', 'pctline', 'pct', hist=H(f'sc_CONS_{k}_pct'),
              fc=f'=IFERROR(([AW_{sk}]+[IW_{sk}]+[HPG_{sk}]{extra})/[is_sales@py],"")', cagr='avg' if k in ('volume', 'price') else None,
              comment='Source: earnings-release "Change in Net Sales" table (consolidated); 2006–2008 from the 10-K MD&A net-sales variance discussion.' if k == 'volume' else None)
    M.add('cons_org', '  Organic sales growth % (volume + price)', 'pctline', 'pct',
          hist=lambda c: '=[cons_volume]+[cons_price]' if c.label in S.get('sc_CONS_volume_pct', {}) else None,
          fc='=[cons_volume]+[cons_price]', cagr='avg')
    M.blank()

    # future M&A
    M.add(style='block', label='Future acquisitions (M&A lever — bolt-ons, unallocated; deals closed from 2027E)',
          note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention')
    mc = CFG['ma']
    M.add('ma_spend', '  Acquisition spend (USDm, scenario)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else f'=MAX(0,SCEN(MA_spend_{c.year}))',
          note='Scenario lever MA_spend. LECO deployed ~$50–400m p.a. on bolt-ons in 2016–25 (Air Liquide Welding, Baker, Kestra, Fori, RedViking, Vanair, Alloy Steel …).')
    M.add('ma_mult', '  Purchase multiple — EV / sales (x)', 'line', 'x', afc=lambda c: None if c.year == 2026 else mc['mult'])
    M.add('ma_acq_sales', '  Annualised sales acquired in the year', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=IFERROR([ma_spend]/[ma_mult],0)')
    M.add('ma_growth', '  Growth of acquired businesses after acquisition %', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['growth'])
    M.add('ma_rr', '  Run-rate sales of businesses acquired (year end)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rr@py]*(1+[ma_growth])+[ma_acq_sales]')
    M.add('ma_rev', '  Net sales from future acquisitions', 'sub', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rr@py]*(1+[ma_growth])+[ma_acq_sales]*0.5',
          note='Mid-year convention: deals close evenly through the year (half a year of sales in year 1).')
    M.add('ma_m', '  Adjusted EBIT margin of acquired businesses % (after D&A)', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['margin'])
    M.add('ma_aebit', '  Adjusted EBIT from future acquisitions', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rev]*[ma_m]')
    M.add('ma_da_pct', '  D&A of acquired businesses % of sales (incl. intangible amortization)', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['da_pct'])
    M.add('ma_da', '  D&A from future acquisitions', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_rev]*[ma_da_pct]')
    M.add('ma_ppe_pct', '  PP&E % of spend', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['ppe_pct'],
          note='Automation / welding bolt-ons: consideration mostly allocated to customer relationships, technology and goodwill; PP&E a minor share.')
    M.add('ma_int_pct', '  Acquired intangibles % of spend', 'pct', 'pct', afc=lambda c: None if c.year == 2026 else mc['int_pct'])
    M.add('ma_life', '  Intangible amortization life (years)', 'line', 'num1', afc=lambda c: None if c.year == 2026 else mc['life'])
    M.add('ma_cum_int', '  Cumulative acquired intangibles (gross)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=[ma_cum_int@py]+[ma_spend]*[ma_int_pct]')
    M.add('ma_amort', '  Amortization of future-acquisition intangibles (within D&A)', 'line', 'num', afc=lambda c: 0 if c.year == 2026 else '=([ma_cum_int@py]+[ma_spend]*[ma_int_pct]*0.5)/[ma_life]')
    M.blank()

    # ------------------------------------------------------------------ GROUP TOTAL
    M.add(style='block', label="Group Total — net sales & adjusted EBIT (segment build) → adjusted operating income / adjusted EBIT (LECO's primary profit KPIs)",
          note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    hseg_any = has('seg_AW_net_sales')
    M.add('g_sales', 'Net sales (segment build)', 'total', 'num',
          hist=lambda c: '=N([AW_sales])+N([IW_sales])+N([HPG_sales])' if hseg_any(c) else None,
          fc='=N([AW_sales])+N([IW_sales])+N([HPG_sales])+N([ma_rev])', cagr='growth',
          note='Σ Americas Welding + International Welding + Harris Products (external net sales) + future M&A. Inter-segment sales eliminate in consolidation.')
    M.add('g_aebit', 'Adjusted EBIT (segment build)', 'total', 'num',
          hist=lambda c: '=N([AW_aebit])+N([IW_aebit])+N([HPG_aebit])+N([corp_aebit])' if hseg_any(c) else None,
          fc='=N([AW_aebit])+N([IW_aebit])+N([HPG_aebit])+N([corp_aebit])+N([ma_aebit])', cagr='growth')
    M.add('g_m', '  Adjusted EBIT margin %', 'pctline', 'pct', hist=ratio('g_aebit', 'g_sales', hseg_any), fc='=IFERROR([g_aebit]/[g_sales],"")')
    M.add('g_g', '  Net sales y/y %', 'pct', 'pct', hist=yoy('g_sales', hseg_any), fc='=IFERROR([g_sales]/[g_sales@py]-1,"")')
    M.add('chk_gsales', '  Check: segment build vs consolidated net sales (should be 0)', 'check', 'num',
          hist=lambda c: '=ROUND([g_sales]-[is_sales],1)' if hseg_any(c) else None, fc='=ROUND([g_sales]-[is_sales],1)')
    M.add('chk_gaebit', '  Check: segment build vs adjusted EBIT bridge (should be 0)', 'check', 'num',
          hist=lambda c: '=ROUND([g_aebit]-[aebit],1)' if hseg_any(c) else None, fc='=ROUND([g_aebit]-[aebit],1)')
    M.add('out_g', '  Memo: FY26 net sales growth outlook — "low double-digit" (scenario end-point)', 'pctline', 'pct',
          afc=lambda c: '=SCEN(G26)' if c.year == 2026 else None,
          note='Q2-26 call (30-Jul-2026): FY26 net sales growth raised to a low double-digit %; organic high single- to low double-digit (~1/3 volume, ~2/3 price). Scenario end-points: Bull / Base / Bear (table →).')
    M.add('out_sales', '  Memo: FY26 net sales implied by the outlook end-point', 'line', 'num',
          afc=lambda c: '=[is_sales@py]*(1+[out_g])' if c.year == 2026 else None)
    M.add('pre_sales', '  Net sales before outlook calibration (Q3/Q4-26E helper)', 'line', 'num',
          qfc='=' + '+'.join(f'[{s}_sales@py]*(1+[{s}_vol@$Q2/26]+[{s}_price]+[{s}_acq]+[{s}_fx])' for s, _, _ in SEGS),
          note='Σ segments: prior-year quarter × (1 + Q2/26 volume + price + acquisitions + FX).')
    M.add('sens_sales', '  Net sales sensitivity to +1.00 of volume growth (Q3/Q4-26E helper)', 'line', 'num',
          qfc='=' + '+'.join(f'[{s}_sales@py]' for s, _, _ in SEGS))
    M.add('cal_g', '  Outlook calibration: Δ volume growth applied uniformly to the segments (Q3/Q4-26E)', 'pctline', 'pct',
          qfc='=([out_sales@$2026E]-[is_sales@$Q1/26]-[is_sales@$Q2/26]-[pre_sales@$Q3/26E]-[pre_sales@$Q4/26E])/([sens_sales@$Q3/26E]+[sens_sales@$Q4/26E])',
          note='Solves the uniform volume shift (vs the Q2/26 y/y trend) so that FY26 net sales = the outlook end-point of the active scenario.')
    M.add('chk_out_sales', '  Check: FY26 net sales vs outlook end-point (should be 0)', 'check', 'num',
          afc=lambda c: '=ROUND([is_sales]-[out_sales],1)' if c.year == 2026 else None)
    M.add('out_inc', '  Memo: 2H/26 incremental adjusted operating income margin — "mid-20%" (scenario end-point)', 'pctline', 'pct',
          afc=lambda c: '=SCEN(INC26)' if c.year == 2026 else None,
          note='Q2-26 call: adjusted operating income margin to improve on mid-20% incremental margins in 2H/26; price/cost neutral.')
    M.add('out_aoi', '  Memo: 2H/26 adjusted operating income implied by the incremental-margin outlook', 'line', 'num',
          afc=lambda c: '=[adj_oi@$Q3/25]+[adj_oi@$Q4/25]+[out_inc]*([is_sales@$Q3/26E]+[is_sales@$Q4/26E]-[is_sales@$Q3/25]-[is_sales@$Q4/25])' if c.year == 2026 else None)
    M.add('pre_aebit', '  Adjusted EBIT before margin calibration (Q3/Q4-26E helper)', 'line', 'num',
          qfc='=' + '+'.join(f'[{s}_tot]*[{s}_m0]' for s, _, _ in SEGS) + '+[corp_aebit]')
    M.add('cal_m', '  Outlook calibration: Δ adjusted EBIT margin applied to the segments (Q3/Q4-26E)', 'pctline', 'pct',
          qfc='=([out_aoi@$2026E]+[nonop_adj@$Q3/26E]+[nonop_adj@$Q4/26E]-[pre_aebit@$Q3/26E]-[pre_aebit@$Q4/26E])/(' +
              '+'.join(f'[{s}_tot@$Q3/26E]+[{s}_tot@$Q4/26E]' for s, _, _ in SEGS) + ')',
          note='Solves the uniform margin shift (vs prior-year quarter + 1H drift) so that 2H/26 adjusted operating income = 2H/25 + incremental margin × Δ net sales for the active scenario.')
    M.add('chk_out_aoi', '  Check: 2H/26 adjusted operating income vs outlook end-point (should be 0)', 'check', 'num',
          afc=lambda c: '=ROUND([adj_oi@$Q3/26E]+[adj_oi@$Q4/26E]-[out_aoi],1)' if c.year == 2026 else None)
    M.blank()

    # ------------------------------------------------------------------ COST DRIVERS
    M.add(style='block', label='Cost drivers & D&A', note='COST DRIVERS — inputs that drive forecast cost lines')
    M.add('da', '  Depreciation & amortization (total; cash-flow statement)', 'line', 'num', hist=H('cf_da'),
          qfc='=([da@$Q1/26]+[da@$Q2/26])/2',
          afc=lambda c: '=SUMQ[da]' if c.year == 2026 else '=([is_sales]-[ma_rev])*[da_pct]+[ma_da]',
          note='Q3/Q4-26E: 1H/26 run-rate. 2027E+: legacy net sales × D&A % + future-M&A D&A. Historical quarters derived from year-to-date cash-flow statements.')
    M.add('da_pct', '  D&A (legacy) % of net sales', 'pctline', 'pct', hist=ratio('da', 'is_sales'),
          afc=lambda c: '=IFERROR([da]/[is_sales],"")' if c.year == 2026 else CFG['da_pct'], cagr='avg',
          note=f'2027E+: {CFG["da_pct"]:.1%} input (FY25 level; capex runs ~1.2–1.4x D&A).')
    M.add('sga_pct', '  SG&A % of net sales', 'pctline', 'pct', hist=ratio('is_sga', 'is_sales'),
          qfc='=[sga_pct@py]+([is_sga@$Q1/26]+[is_sga@$Q2/26])/([is_sales@$Q1/26]+[is_sales@$Q2/26])-([is_sga@$Q1/25]+[is_sga@$Q2/25])/([is_sales@$Q1/25]+[is_sales@$Q2/25])',
          afc=lambda c: '=IFERROR([is_sga]/[is_sales],"")' if c.year == 2026 else CFG['sga_pct'], cagr='avg',
          note='Q3/Q4-26E: prior-year quarter ratio + 1H drift. 2027E+: input. SG&A only splits gross profit vs opex — operating income is driven by the adjusted EBIT build.')
    M.add('sbc_pct', '  Stock-based compensation % of net sales', 'pctline', 'pct', hist=ratio('is_sbc', 'is_sales'),
          qfc='=([is_sbc@$Q1/26]+[is_sbc@$Q2/26])/([is_sales@$Q1/26]+[is_sales@$Q2/26])',
          afc=lambda c: '=IFERROR([is_sbc]/[is_sales],"")' if c.year == 2026 else CFG['sbc_pct'])
    M.blank()

    # ------------------------------------------------------------------ INCOME STATEMENT
    M.add(style='section', label='CONSOLIDATED STATEMENT OF INCOME (US GAAP, as reported)', note='CONSOLIDATED IS — forecast logic')
    M.add('is_sales', 'Net sales', 'total', 'num', hist=H('is_sales'), fc='=[g_sales]', cagr='growth',
          note='Forecast linked to the segment build.',
          comment='Source: Lincoln Electric Forms 10-K / 10-Q and earnings releases (Form 8-K Ex. 99.1), SEC EDGAR CIK 0000059527. Q4 = fourth-quarter columns of the Q4 earnings release.')
    M.add('is_sales_g', '  Net sales y/y %', 'pct', 'pct', hist=yoy('is_sales'), fc='=IFERROR([is_sales]/[is_sales@py]-1,"")')
    M.add('is_cogs', 'Cost of goods sold', 'line', 'num', hist=H('is_cogs'), fc='=[is_sales]-[is_gp]',
          note='Forecast = net sales − gross profit.')
    M.add('is_gp', 'Gross profit', 'sub', 'num', hist='=[is_sales]-[is_cogs]', fc='=[is_oi]+[is_sga]+[is_rat]+[is_othop]', cagr='growth',
          note='Forecast = operating income + SG&A + rationalization + other operating items (backed out of the adjusted EBIT build).')
    M.add('is_gm', '  Gross margin %', 'pctline', 'pct', hist=ratio('is_gp', 'is_sales'), fc='=IFERROR([is_gp]/[is_sales],"")', cagr='avg')
    M.add('is_sga', 'Selling, general & administrative expenses', 'line', 'num', hist=H('is_sga'),
          qfc='=[is_sales]*[sga_pct]', afc=lambda c: '=SUMQ[is_sga]' if c.year == 2026 else '=[is_sales]*[sga_pct]')
    M.add('is_rat', 'Rationalization & asset impairment net charges', 'line', 'num', hist=H('is_rat'),
          qfc='=([is_rat@$Q1/26]+[is_rat@$Q2/26])/2', afc=lambda c: '=SUMQ[is_rat]' if c.year == 2026 else CFG['rat_fc'],
          note=f'Q3/Q4-26E: 1H/26 run-rate. 2027E+: ${CFG["rat_fc"]:.0f}m p.a. (LECO runs rolling rationalization programmes; excluded from adjusted results).')
    M.add('is_othop', 'Other operating (income) charges — bargain purchase gains, Venezuela, other (charge = +)', 'line', 'num', hist=H('is_othop'), fc=0,
          note='Items printed on the face of the income statement between gross profit and operating income other than SG&A and rationalization (e.g. 2015 Venezuela deconsolidation, bargain purchase gains).')
    M.add('is_oi', 'Operating income', 'total', 'num', hist='=[is_gp]-[is_sga]-[is_rat]-[is_othop]',
          qfc='=[g_aebit]-[nonop_adj]-[oi_sp]', afc=lambda c: '=SUMQ[is_oi]' if c.year == 2026 else '=[g_aebit]-[nonop_adj]-[oi_sp]', cagr='growth',
          note='Forecast = adjusted EBIT (segment build) − adjusted non-operating income − special items in operating income.')
    M.add('chk_oi', '  Check: operating income vs reported (should be 0)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([is_oi_rep]),ROUND([is_oi]-[is_oi_rep],1),"")')
    M.add('is_oi_rep', '  Memo: operating income as reported', 'pub', 'num', hist=H('is_oi_rep'), outline=2)
    M.add('is_int_gross', '  Memo: interest expense (gross; separately reported to 2022)', 'line', 'num', hist=H('is_int_gross'), outline=2)
    M.add('is_int_inc', '  Memo: interest income (separately reported to 2022; within interest expense, net from 2023)', 'line', 'num', hist=H('is_int_inc'), outline=2)
    M.add('is_int_net', 'Interest expense, net of interest income', 'line', 'num', hist=H('is_int_net'),
          qfc='=(SCEN(INT26)-[is_int_net@$Q1/26]-[is_int_net@$Q2/26])/2',
          afc=lambda c: '=SUMQ[is_int_net]' if c.year == 2026 else '=[dsch_notes@py]*[r_notes]+[dsch_fac@py]*[r_fac]-[bs_cash@py]*[r_cash]',
          note='Q3/Q4-26E: (FY26 assumption $50–55m − 1H actual) ÷ 2 for the active scenario. 2027E+: rate × opening balances (no circularity).')
    M.add('is_eq', 'Equity earnings in affiliates', 'line', 'num', hist=H('is_eq'), fc=0,
          note='Reported separately to 2019 (Turkey / Chile JVs); none forecast.')
    M.add('is_oth', 'Other income (expense)', 'line', 'num', hist=H('is_oth'),
          qfc='=([is_oth@$Q1/26]+[is_oth@$Q2/26])/2', afc=lambda c: '=SUMQ[is_oth]' if c.year == 2026 else CFG['oth_fc'],
          note=f'Pension non-service income/cost (from 2018), FX, other. Q3/Q4-26E: 1H run-rate; 2027E+: ${CFG["oth_fc"]:.0f}m p.a. input.')
    M.add('is_pretax', 'Income before income taxes', 'sub', 'num', hist='=[is_oi]-[is_int_net]+[is_eq]+[is_oth]', fc='=[is_oi]-[is_int_net]+[is_eq]+[is_oth]', cagr='growth')
    M.add('is_tax', 'Income taxes', 'line', 'num', hist=H('is_tax'), qfc='=[is_pretax]*[is_etr]',
          afc=lambda c: '=SUMQ[is_tax]' if c.year == 2026 else '=[is_pretax]*[is_etr]')
    M.add('is_etr', '  Effective tax rate', 'pctline', 'pct', hist=ratio('is_tax', 'is_pretax'),
          qfc='=SCEN(TAX26)', afc=lambda c: '=IFERROR([is_tax]/[is_pretax],"")' if c.year == 2026 else CFG['etr'], cagr='avg',
          note=f'Q3/Q4-26E: FY26 "low-to-mid 20%" assumption for the active scenario. 2027E+: {CFG["etr"]:.1%} input.')
    M.add('is_nici', 'Net income (incl. noncontrolling interests)', 'sub', 'num', hist='=[is_pretax]-[is_tax]', fc='=[is_pretax]-[is_tax]')
    M.add('is_nci', '  Less: net income (loss) attributable to noncontrolling interests', 'line', 'num', hist=H('is_nci'), fc=0)
    M.add('is_ni', 'Net income attributable to Lincoln Electric', 'total', 'num', hist='=[is_nici]-[is_nci]', fc='=[is_nici]-[is_nci]', cagr='growth')
    M.add('chk_ni', '  Check: net income vs reported (should be 0; ±0.1 rounding tolerated)', 'check', 'num',
          hist=lambda c: '=IF(ISNUMBER([is_ni_rep]),ROUND([is_ni]-[is_ni_rep],1),"")')
    M.add('is_ni_rep', '  Memo: net income attributable as reported', 'pub', 'num', hist=H('is_ni_rep'), outline=2)
    M.add('is_da', '  Memo: depreciation & amortization (cash-flow statement)', 'line', 'num', hist='=[da]', fc='=[da]', outline=2)
    M.add('is_sbc', '  Memo: stock-based compensation', 'line', 'num', hist=H('cf_sbc'),
          qfc='=[is_sales]*[sbc_pct]', afc=lambda c: '=SUMQ[is_sbc]' if c.year == 2026 else '=[is_sales]*[sbc_pct]', outline=2)
    M.add(None, '(Earnings per share — 2006–2010 restated for the 2-for-1 stock split of 27-May-2011)', 'label')
    M.add('sh_b', '  Weighted-average basic shares (m)', 'line', 'num1', hist=H('sh_b'),
          qfc=lambda c: f'=[sh_b@$Q2/26]-[bb_sh@$2026E]*{0.25 if c.q == 3 else 0.75}',
          afc=lambda c: '=AVERAGE([sh_b@-4],[sh_b@-3],[sh_b@-2],[sh_b@-1])' if c.year == 2026 else '=AVERAGE([sh_beg],[sh_end])',
          note='Q3/Q4-26E: Q2/26 less 2H buybacks (time-weighted). 2027E+: average of beginning and ending shares outstanding.')
    M.add('sh_d', '  Weighted-average diluted shares (m)', 'line', 'num1', hist=H('sh_d'),
          qfc='=[sh_b]+([sh_d@$Q2/26]-[sh_b@$Q2/26])',
          afc=lambda c: '=AVERAGE([sh_d@-4],[sh_d@-3],[sh_d@-2],[sh_d@-1])' if c.year == 2026 else '=[sh_b]+[dil]')
    M.add('eps_b', 'EPS – basic, attributable to Lincoln Electric ($)', 'line', 'eps', hist=ratio('is_ni', 'sh_b'), fc='=IFERROR([is_ni]/[sh_b],"")')
    M.add('eps_d', 'EPS – diluted, attributable to Lincoln Electric ($)', 'sub', 'eps', hist=ratio('is_ni', 'sh_d'),
          qfc='=IFERROR([is_ni]/[sh_d],"")', afc=lambda c: '=SUMQ[eps_d]' if c.year == 2026 else '=IFERROR([is_ni]/[sh_d],"")', cagr='growth',
          note='EPS computed as net income / weighted diluted shares (may differ by ±$0.01–0.02 vs reported because of share rounding). 2026E = sum of quarters.')
    M.add('eps_d_g', '  EPS – diluted y/y %', 'pct', 'pct', hist=yoy('eps_d'), fc='=IFERROR([eps_d]/[eps_d@py]-1,"")')
    M.add('eps_d_rep', '  Memo: EPS – diluted as reported ($)', 'pub', 'eps', hist=H('eps_d_rep'), outline=2)
    M.add('dps', '  Dividends declared per share ($)', 'line', 'eps', hist=H('dps'),
          qfc=lambda c: '=[dps@$Q2/26]' if c.q == 3 else f'=[dps@$Q2/26]*(1+{CFG["dps_g"]})',
          afc=lambda c: '=SUMQ[dps]' if c.year == 2026 else '=[dps@py]*(1+[dps_g])', cagr='growth',
          note=f'Q3/26E: $0.79 declared (payable 15-Oct-2026). Q4/26E: +{CFG["dps_g"]:.0%} (LECO raises its dividend with the Q4 declaration; 31 consecutive annual increases). 2027E+: +{CFG["dps_g"]:.0%} p.a.')
    M.add('dps_g', '  Dividend per share growth %', 'pct', 'pct', hist=yoy('dps'),
          afc=lambda c: '=IFERROR([dps]/[dps@py]-1,"")' if c.year == 2026 else CFG['dps_g'])
    M.blank()
    return M, wb, ws, t


if __name__ == '__main__':
    pass
