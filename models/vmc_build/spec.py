"""Row specification of the VMC Model sheet (adapted from the TDY template)."""
from fw import *

SCN = '$CT$2'
def CH(row):  # scenario lookup on the Bull/Base/Bear table row
    return f'CHOOSE(MATCH({SCN},{{"Bull","Base","Bear"}},0),$DC${row},$DD${row},$DE${row})'
SC = {}   # scenario table rows: SC[name][year] or SC[name] -> row (filled by scen.py layout)

def ifn(x, expr, alt='""'):
    return f'IF(ISNUMBER({x}),{expr},{alt})'

def growth_formula():
    c = CTX.col
    k = CTX.key_base
    if c.prior is None: return None
    return f'=IF(AND(ISNUMBER({V(k)}),ISNUMBER({P(k)})),IFERROR({V(k)}/{P(k)}-1,""),"")'

def ratio(num, den):
    return lambda: f'=IFERROR({V(num)}/{V(den)},"")'

def build_spec():
    S = add
    # ================================================================== SEGMENT BUILD
    S('sec_seg', 'SEGMENT P&L — BY SEGMENT (Aggregates, Asphalt, Concrete; legacy Cement / Calcium as memo) · tons in millions, prices in $', 'section',
      note='SEGMENT BUILD — modelling logic (volume × price → segment revenues → gross profit → cash gross profit → Adjusted EBITDA)')
    blank()
    # ---------------- Aggregates
    S('agg_hdr', 'Aggregates (crushed stone, sand & gravel; ~75% of total revenues, ~90% of segment gross profit)', 'block', note='AGGREGATES — modelling logic')
    S('agg_tons', '  Shipments (million tons)', 'line_b', 'm1', data='seg.agg_tons', flow=True,
      qe=lambda: (f'={P("agg_tons")}*($CI${R["agg_tons"]}*(1+{CH(SC["out_vol"])})-$CL${R["agg_tons"]})'
                  f'/($CG${R["agg_tons"]}+$CH${R["agg_tons"]})'),
      ae=lambda: f'={PV("agg_tons")}*(1+{V("agg_tons_g")})',
      note='Q3/26E–Q4/26E: FY26 shipments guide (+1–3%; scenario high / mid / low) less 1H/26, split on prior-year quarter weights. 2027E+: prior year × (1 + scenario volume growth).')
    S('agg_tons_g', '  Shipments y/y %', 'growth', 'pct', growth='agg_tons',
      ae=lambda: '=' + CH(SC['AGG_vol'][CTX.col.year]),
      note='2027E–2030E: scenario lever (AGG_volumeGrowth, Bull/Base/Bear table →).')
    S('agg_price', '  Freight-adjusted average sales price ($/ton)', 'line', 'ps', data='seg.agg_price',
      h1=lambda: f'=IFERROR({V("agg_fa_rev")}/{V("agg_tons")},"")',
      qe=lambda: (f'={P("agg_price")}*(($CI${R["agg_tons"]}*(1+{CH(SC["out_vol"])})*$CI${R["agg_price"]}*(1+{CH(SC["out_px"])})'
                  f'-$CL${R["agg_fa_rev"]})/($CM${R["agg_tons"]}+$CN${R["agg_tons"]}))'
                  f'/(($CG${R["agg_fa_rev"]}+$CH${R["agg_fa_rev"]})/($CG${R["agg_tons"]}+$CH${R["agg_tons"]}))'),
      e26=lambda: f'=IFERROR({V("agg_fa_rev")}/{V("agg_tons")},"")',
      ae=lambda: f'={PV("agg_price")}*(1+{V("agg_price_g")})',
      note='Q3/26E–Q4/26E: 2H/26 price implied by the FY26 freight-adjusted price guide (+4–6%; scenario) on the guided volumes, applied to prior-year quarters. 2027E+: scenario price growth.')
    S('agg_price_g', '  Freight-adjusted price y/y %', 'growth', 'pct', growth='agg_price',
      ae=lambda: '=' + CH(SC['AGG_price'][CTX.col.year]), note='2027E–2030E: scenario lever (AGG_priceGrowth).')
    S('agg_fa_rev', '  Freight-adjusted revenues', 'line', 'm', data='seg.agg_fa_rev', flow=True,
      qe=lambda: f'={V("agg_tons")}*{V("agg_price")}', ae=lambda: f'={V("agg_tons")}*{V("agg_price")}',
      note='Company non-GAAP measure: segment revenues less freight & delivery and other (service) revenues. Forecast = tons × price.')
    S('agg_fdo', '  Freight & delivery and other revenues (segment)', 'line', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("agg_rev")}),ISNUMBER({V("agg_fa_rev")})),{V("agg_rev")}-{V("agg_fa_rev")},"")',
      qe=lambda: f'={V("agg_fa_rev")}*{P("agg_fdo")}/{P("agg_fa_rev")}',
      ae=lambda: f'={V("agg_fa_rev")}*{PV("agg_fdo")}/{PV("agg_fa_rev")}',
      note='Pass-through freight (post-ASC 606, 2018+) and service revenues; forecast at the prior-year ratio to freight-adjusted revenues.')
    S('agg_rev', '  Segment total revenues (incl. intersegment)', 'line_b', 'm', data='seg.agg_rev', flow=True,
      qe=lambda: f'={V("agg_fa_rev")}+{V("agg_fdo")}', ae=lambda: f'={V("agg_fa_rev")}+{V("agg_fdo")}',
      note='Pre-2018 segment net sales exclude delivery revenues (shown outside segments below); ASC 606 from 2018 puts freight inside segment revenues.')
    S('agg_rev_g', '  Segment revenues y/y %', 'growth', 'pct', growth='agg_rev')
    S('agg_gp', '  Segment gross profit (GAAP)', 'line', 'm', data='seg.agg_gp', flow=True,
      qe=lambda: f'={V("agg_cgp")}-{V("agg_dda")}', ae=lambda: f'={V("agg_cgp")}-{V("agg_dda")}',
      note='Forecast GAAP gross profit = cash gross profit − DDA&A.')
    S('agg_dda', '  (+) Segment depreciation, depletion, accretion & amortization', 'line', 'm', data='seg.agg_dda', flow=True,
      qe=lambda: f'=($DD${SC["pt_dda"]}-$CL${R["is_dda"]})/2*$CL${R["agg_dda"]}/$CL${R["is_dda"]}',
      ae=lambda: f'={V("agg_tons")}*{V("agg_dda_t")}',
      note='Q3/Q4-26E: FY26 projected DDA&A (outlook bridge) less 1H/26, split by 1H/26 segment mix. 2027E+: tons × DDA&A per ton.')
    S('agg_cgp', '  Cash gross profit (non-GAAP)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("agg_dda")}),{V("agg_gp")}+{V("agg_dda")},"")',
      qe=lambda: f'={V("agg_tons")}*({V("agg_price")}-{V("agg_cost")})',
      e26=lambda: f'=SUM({V("agg_cgp","CJ")},{V("agg_cgp","CK")},{V("agg_cgp","CM")},{V("agg_cgp","CN")})',
      ae=lambda: f'={V("agg_tons")}*({V("agg_price")}-{V("agg_cost")})',
      note='Company non-GAAP measure: segment gross profit + DDA&A. Forecast = tons × (freight-adjusted price − unit cash cost).')
    S('agg_cgp_pub', '  Memo: cash gross profit as published', 'memo', 'm', data='seg.agg_cgp', flow=True)
    S('agg_cgp_chk', '  Check: build vs published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("agg_cgp_pub")}),ROUND({V("agg_cgp")}-{V("agg_cgp_pub")},1),"n/p")')
    S('agg_gp_t', '  Gross profit per ton ($)', 'line', 'ps', all=ratio('agg_gp', 'agg_tons'))
    S('agg_cgp_t', '  Cash gross profit per ton ($)', 'line_b', 'ps', all=ratio('agg_cgp', 'agg_tons'))
    S('agg_cost_pre', '  Unit cash cost before outlook calibration ($/ton)', 'line', 'ps',
      qe=lambda: (f'={P("agg_cost")}*(($CI${R["agg_tons"]}*(1+{CH(SC["out_vol"])})*$CI${R["agg_cost"]}*(1+$DD${SC["pt_cost_g"]})'
                  f'-($CL${R["agg_fa_rev"]}-$CL${R["agg_cgp"]}))/($CM${R["agg_tons"]}+$CN${R["agg_tons"]}))'
                  f'/(($CG${R["agg_fa_rev"]}-$CG${R["agg_cgp"]}+$CH${R["agg_fa_rev"]}-$CH${R["agg_cgp"]})/($CG${R["agg_tons"]}+$CH${R["agg_tons"]}))'),
      note='Q3/Q4-26E: 2H/26 unit cash cost implied by the FY26 guide (low-single-digit increase; point estimate) after 1H/26 actuals, applied to prior-year quarters.')
    S('agg_cost', '  Freight-adjusted unit cash cost of sales ($/ton)', 'line', 'ps',
      hist=lambda: f'=IFERROR({V("agg_price")}-{V("agg_cgp_t")},"")',
      qe=lambda: f'={V("agg_cost_pre")}+{V("calib")}',
      e26=lambda: f'=IFERROR({V("agg_price")}-{V("agg_cgp_t")},"")',
      ae=lambda: f'={PV("agg_cost")}*(1+{V("agg_cost_g")})',
      note='Freight-adjusted price − cash gross profit per ton (company definition). Q3/Q4-26E = pre-calibration cost + outlook calibration Δ. 2027E+: scenario unit cash cost inflation.')
    S('agg_cost_g', '  Unit cash cost y/y %', 'growth', 'pct', growth='agg_cost',
      ae=lambda: '=' + CH(SC['AGG_cost'][CTX.col.year]), note='2027E–2030E: scenario lever (AGG_unitCashCostGrowth).')
    S('agg_cgp_m', '  Cash gross profit % of freight-adjusted revenues', 'pct', 'pct', all=ratio('agg_cgp', 'agg_fa_rev'))
    S('agg_gp_m', '  Gross margin % of segment revenues', 'pct', 'pct', all=ratio('agg_gp', 'agg_rev'))
    S('agg_inc', '  Incremental cash gross profit (ΔCGP / Δ freight-adjusted revenues)', 'pct', 'pct',
      prior_ratio=('agg_cgp', 'agg_fa_rev'))
    S('agg_dda_t', '  DDA&A per ton ($)', 'driver', 'ps',
      all=ratio('agg_dda', 'agg_tons'),
      ae=lambda: f'={PV("agg_dda_t")}*(1+$DD${SC["pt_ddat_g"]})',
      note='2027E+: prior year × (1 + DDA&A per ton growth, point estimate in scenario table).')
    S('agg_capex', '  Memo: segment capital expenditures (annual, 10-K segment note)', 'memo', 'm', data='extra.capex_by_segment.aggregates', annual_only=True)
    blank()
    # ---------------- Asphalt
    S('asph_hdr', 'Asphalt (asphalt mix & paving; Arizona, California, Texas, Tennessee)', 'block', note='ASPHALT — modelling logic')
    S('asph_tons', '  Asphalt mix shipments (million tons)', 'line', 'm1', data='seg.asph_tons', flow=True)
    S('asph_price', '  Asphalt mix average sales price ($/ton)', 'line', 'ps', data='seg.asph_price')
    S('asph_rev', '  Segment total revenues', 'line_b', 'm', data='seg.asph_rev', flow=True,
      qe=lambda: f'={P("asph_rev")}*(1-{V("asph_div")})*(1+$DD${SC["pt_down_g"]})',
      ae=lambda: f'={PV("asph_rev")}*(1+{V("asph_rev_g")})',
      note='Q3/Q4-26E: prior-year quarter × (1 − divested share) × (1 + underlying growth point estimate). 2027E+: scenario growth.')
    S('asph_rev_g', '  Segment revenues y/y %', 'growth', 'pct', growth='asph_rev',
      ae=lambda: '=' + CH(SC['ASPH_g'][CTX.col.year]), note='2027E–2030E: scenario lever (ASPH_growth).')
    S('asph_gp', '  Segment gross profit (GAAP)', 'line', 'm', data='seg.asph_gp', flow=True,
      qe=lambda: f'={V("asph_cgp")}-{V("asph_dda")}', ae=lambda: f'={V("asph_cgp")}-{V("asph_dda")}')
    S('asph_dda', '  (+) Segment DDA&A', 'line', 'm', data='seg.asph_dda', flow=True,
      qe=lambda: f'=($DD${SC["pt_dda"]}-$CL${R["is_dda"]})/2*$CL${R["asph_dda"]}/$CL${R["is_dda"]}',
      ae=lambda: f'={V("asph_rev")}*{PV("asph_dda")}/{PV("asph_rev")}')
    S('asph_cgp', '  Cash gross profit (non-GAAP)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("asph_dda")}),{V("asph_gp")}+{V("asph_dda")},"")',
      qe=lambda: f'={V("asph_rev")}*{V("asph_cgp_m")}',
      e26=lambda: f'=SUM({V("asph_cgp","CJ")},{V("asph_cgp","CK")},{V("asph_cgp","CM")},{V("asph_cgp","CN")})',
      ae=lambda: f'={V("asph_rev")}*{V("asph_cgp_m")}')
    S('asph_cgp_pub', '  Memo: cash gross profit as published', 'memo', 'm', data='seg.asph_cgp', flow=True)
    S('asph_cgp_chk', '  Check: build vs published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("asph_cgp_pub")}),ROUND({V("asph_cgp")}-{V("asph_cgp_pub")},1),"n/p")')
    S('asph_gp_m', '  Gross margin %', 'pct', 'pct', all=ratio('asph_gp', 'asph_rev'))
    S('asph_cgp_m', '  Cash gross profit margin %', 'pct', 'pct', all=ratio('asph_cgp', 'asph_rev'),
      qe=lambda: f'={P("asph_cgp_m")}+$CL${R["asph_cgp_m"]}-$CF${R["asph_cgp_m"]}',
      ae=lambda: '=' + CH(SC['ASPH_m'][CTX.col.year]),
      note='Q3/Q4-26E: prior-year quarter margin + 1H/26 vs 1H/25 change. 2027E+: scenario lever (ASPH_cashMargin).')
    S('asph_div', '  Divested operations share of prior-year quarter revenues (input)', 'driver', 'pct',
      qe_input={3: 0.05, 4: 0.05}, note='Houston asphalt & construction business (sold Q4/25): Q2/26 10-Q attributes the $16m y/y fall in service revenues to the sale (~4–5% of the prior-year quarter) — analyst estimate.')
    blank()
    # ---------------- Concrete
    S('conc_hdr', 'Concrete (ready-mixed concrete; Virginia / Maryland / DC; California sold Jun-2026)', 'block', note='CONCRETE — modelling logic')
    S('conc_cy', '  Ready-mixed concrete shipments (million cubic yards)', 'line', 'm1', data='seg.conc_cy', flow=True)
    S('conc_price', '  Ready-mixed concrete average sales price ($/cubic yard)', 'line', 'ps', data='seg.conc_price')
    S('conc_rev', '  Segment total revenues', 'line_b', 'm', data='seg.conc_rev', flow=True,
      qe=lambda: f'={P("conc_rev")}*(1-{V("conc_div")})*(1+$DD${SC["pt_down_g"]})',
      ae=lambda: f'={PV("conc_rev")}*(1+{V("conc_rev_g")})',
      note='Q3/Q4-26E: prior-year quarter × (1 − divested California share) × (1 + underlying growth). 2027E+: scenario growth.')
    S('conc_rev_g', '  Segment revenues y/y %', 'growth', 'pct', growth='conc_rev',
      ae=lambda: '=' + CH(SC['CONC_g'][CTX.col.year]), note='2027E–2030E: scenario lever (CONC_growth).')
    S('conc_gp', '  Segment gross profit (GAAP)', 'line', 'm', data='seg.conc_gp', flow=True,
      qe=lambda: f'={V("conc_cgp")}-{V("conc_dda")}', ae=lambda: f'={V("conc_cgp")}-{V("conc_dda")}')
    S('conc_dda', '  (+) Segment DDA&A', 'line', 'm', data='seg.conc_dda', flow=True,
      qe=lambda: f'={V("conc_rev")}*$CK${R["conc_dda"]}/$CK${R["conc_rev"]}',
      ae=lambda: f'={V("conc_rev")}*{PV("conc_dda")}/{PV("conc_rev")}',
      note='Q3/Q4-26E at the Q2/26 DDA&A-to-revenue ratio (California depreciation ceased when held for sale).')
    S('conc_cgp', '  Cash gross profit (non-GAAP)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("conc_dda")}),{V("conc_gp")}+{V("conc_dda")},"")',
      qe=lambda: f'={V("conc_rev")}*{V("conc_cgp_m")}',
      e26=lambda: f'=SUM({V("conc_cgp","CJ")},{V("conc_cgp","CK")},{V("conc_cgp","CM")},{V("conc_cgp","CN")})',
      ae=lambda: f'={V("conc_rev")}*{V("conc_cgp_m")}')
    S('conc_cgp_pub', '  Memo: cash gross profit as published', 'memo', 'm', data='seg.conc_cgp', flow=True)
    S('conc_cgp_chk', '  Check: build vs published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("conc_cgp_pub")}),ROUND({V("conc_cgp")}-{V("conc_cgp_pub")},1),"n/p")')
    S('conc_gp_m', '  Gross margin %', 'pct', 'pct', all=ratio('conc_gp', 'conc_rev'))
    S('conc_cgp_m', '  Cash gross profit margin %', 'pct', 'pct', all=ratio('conc_cgp', 'conc_rev'),
      qe=lambda: f'=$CK${R["conc_cgp_m"]}',
      ae=lambda: '=' + CH(SC['CONC_m'][CTX.col.year]),
      note='Q3/Q4-26E at the Q2/26 margin (mostly the retained East-coast business). 2027E+: scenario lever (CONC_cashMargin).')
    S('conc_div', '  Divested operations share of prior-year quarter revenues (input)', 'driver', 'pct',
      qe_input={3: 0.46, 4: 0.46}, note='California ready-mixed concrete (sold Jun-26; revenues not disclosed). Analyst estimate: Q2/26 concrete revenues −15% y/y with two of three months of California ownership ⇒ ~46% share.')
    blank()
    # ---------------- Legacy segments
    S('leg_hdr', 'Legacy segments (memo; Cement 2007–Q1/14 sold to Cementos Argos; Calcium; included in group totals)', 'block',
      note='LEGACY SEGMENTS — included in the group build historically; not forecast', group=True)
    S('cem_rev', '  Cement — segment revenues', 'line', 'm', data='seg.cem_rev', flow=True, group=True, h1_partial=True)
    S('cem_gp', '  Cement — gross profit', 'line', 'm', data='seg.cem_gp', flow=True, group=True, h1_partial=True)
    S('cem_dda', '  Cement — DDA&A', 'line', 'm', data='seg.cem_dda', flow=True, group=True, h1_partial=True)
    S('calc_rev', '  Calcium — segment revenues', 'line', 'm', data='seg.calc_rev', flow=True, group=True, h1_partial=True)
    S('calc_gp', '  Calcium — gross profit', 'line', 'm', data='seg.calc_gp', flow=True, group=True, h1_partial=True)
    S('calc_dda', '  Calcium — DDA&A', 'line', 'm', data='seg.calc_dda', flow=True, group=True, h1_partial=True)
    S('oseg_rev', '  Other segment / product line — revenues', 'line', 'm', data='seg.other_seg_rev', flow=True, group=True, h1_partial=True)
    S('oseg_gp', '  Other segment / product line — gross profit', 'line', 'm', data='seg.other_seg_gp', flow=True, group=True, h1_partial=True)
    S('oseg_dda', '  Other segment / product line — DDA&A', 'line', 'm', data='seg.other_seg_dda', flow=True, group=True, h1_partial=True)
    blank()
    # ---------------- Corporate & reconciling
    S('corp_hdr', 'Corporate & reconciling items (segment cash gross profit → Adjusted EBITDA)', 'block', note='CORPORATE — modelling logic')
    S('interseg', '  Intersegment eliminations (total)', 'line', 'm', data='seg.interseg_total', flow=True, h1_partial=True,
      qe=lambda: f'={V("agg_rev")}*{P("interseg")}/{P("agg_rev")}',
      ae=lambda: f'={V("agg_rev")}*{PV("interseg")}/{PV("agg_rev")}',
      note='Mostly aggregates sold to the downstream segments; forecast at the prior-year ratio to aggregates revenues.')
    S('deliv', '  Delivery revenues outside segments (pre-2018 presentation)', 'line', 'm', data='seg.delivery_rev', flow=True, h1_partial=True)
    S('sag', '  Selling, administrative & general (SAG) expense', 'line_b', 'm',
      hist=lambda: f'={V("is_sag")}' ,
      qe=lambda: f'=($DD${SC["pt_sag"]}-$CL${R["sag"]})/2', ae=lambda: f'={V("g_rev")}*{V("sag_pct")}',
      note='Historical = income statement. Q3/Q4-26E: FY26 SAG outlook ($580–590m) less 1H/26, split evenly; 2027E+: % of revenues input.')
    S('sag_pct', '  SAG % of total revenues', 'pct', 'pct', all=ratio('sag', 'g_rev'), ae_input=0.068)
    S('oth_dda', '  Corporate / other DDA&A (not allocated to segments)', 'line', 'm', data='seg.other_dda', flow=True,
      qe=lambda: f'=($DD${SC["pt_dda"]}-$CL${R["is_dda"]})/2*$CL${R["oth_dda"]}/$CL${R["is_dda"]}',
      ae=lambda: f'={PV("oth_dda")}*(1+$DD${SC["pt_ddat_g"]})',
      note='Charged within SAG / other operating; added back in Adjusted EBITDA.')
    S('oth_op', '  Other operating income (expense) incl. gain on sale, net (GAAP, signed)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("is_op")}),N({V("is_gain")})+N({V("is_othop")}),"")',
      qe=lambda: f'=($CL${R["oth_op"]}+$CL${R["adj_ex"]})/2',
      ae=lambda: f'={V("g_rev")}*{V("oth_op_pct")}',
      note='Q3/Q4-26E: 1H/26 recurring run-rate (excluding adjusting items). 2027E+: % of revenues input (recurring idle-facility, environmental and other costs).')
    S('oth_op_pct', '  Recurring other operating items % of revenues', 'pct', 'pct',
      all=lambda: f'=IFERROR(({V("oth_op")}+{V("adj_ex")})/{V("g_rev")},"")', ae_input=-0.002)
    S('nonop', '  Other nonoperating income (expense), net', 'line', 'm',
      hist=lambda: f'={V("is_nonop")}', qe=lambda: f'=$CL${R["nonop"]}/2', ae_input=0.0,
      note='Includes non-service pension cost from 2018 (ASU 2017-07).')
    S('nci_c', '  (−) Earnings attributable to noncontrolling interests', 'line', 'm',
      hist=lambda: f'=-N({V("is_nci")})', qe=lambda: f'=$CL${R["nci_c"]}/2', ae_input=-3.0)
    S('adj_ex', '  (+) Adjusting items excluded from Adjusted EBITDA (ex discontinued operations)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),{V("r_adj_tot")}-N({V("r_disc")}),"")', qe_input={3: 0.0, 4: 0.0}, ae_input=0.0,
      note='Company bridge items that sit in operating / nonoperating lines. Forecast none (2H/26 items not guided).')
    S('oth_sum', '  Other items to Adjusted EBITDA, net', 'line_b', 'm',
      all=lambda: f'=N({V("oth_op")})+N({V("nonop")})+N({V("nci_c")})+N({V("adj_ex")})')
    S('calib', '  Outlook calibration: Δ aggregates unit cash cost ($/ton), Q3/Q4-26E', 'driver', 'ps',
      qe=lambda: (f'=({V("agg_tons")}*({V("agg_price")}-{V("agg_cost_pre")})+{V("asph_cgp")}+{V("conc_cgp")}'
                  f'-{V("sag")}+{V("oth_dda")}+{V("oth_sum")}-{V("target")})/{V("agg_tons")}'),
      note='Solves the residual unit cash cost shift (after guided volume / price / cost) so that FY26 Adjusted EBITDA equals the FY26 outlook (scenario: high / mid / low), allocated to Q3/Q4 by prior-year quarter weights.')
    S('target', '  Memo: Adjusted EBITDA target (FY26 outlook × prior-year quarter weight)', 'memo', 'm',
      qe=lambda: (f'=({CH(SC["out_ebitda"])}-$CL${R["g_ebitda"]})*{P("g_ebitda")}/($CG${R["g_ebitda"]}+$CH${R["g_ebitda"]})'),
      e26=lambda: '=' + CH(SC['out_ebitda']),
      note='Q3/Q4-26E: (FY26 Adjusted EBITDA outlook − 1H/26 actual) × prior-year quarter share of 2H/25.')
    blank()
    # ---------------- M&A lever
    S('mna_hdr', 'Future acquisitions (M&A lever — aggregates bolt-ons; deals closed from 2027E)', 'block',
      note='M&A LEVER — acquired EBITDA = spend ÷ EV/EBITDA; mid-year convention')
    S('mna_spend', '  Acquisition spend (USDm, scenario)', 'line', 'm', e26_input=0.0,
      ae=lambda: '=' + CH(SC['MNA'][CTX.col.year]), note='Scenario lever (M&A_spend, Bull/Base/Bear table →).')
    S('mna_mult', '  Purchase multiple — EV / Adjusted EBITDA (x)', 'driver', 'x2', ae_input=14.0)
    S('mna_ebitda_acq', '  Annualised Adjusted EBITDA acquired in the year', 'line', 'm',
      e26_input=0.0, ae=lambda: f'=IFERROR({V("mna_spend")}/{V("mna_mult")},0)')
    S('mna_margin', '  Adjusted EBITDA margin of acquired businesses %', 'driver', 'pct', ae_input=0.30)
    S('mna_rev_acq', '  Annualised revenues acquired in the year', 'line', 'm',
      e26_input=0.0, ae=lambda: f'=IFERROR({V("mna_ebitda_acq")}/{V("mna_margin")},0)')
    S('mna_g', '  Growth of acquired businesses after acquisition %', 'driver', 'pct', ae_input=0.06)
    S('mna_runrate', '  Run-rate revenues of businesses acquired (year end)', 'line', 'm',
      e26_input=0.0, ae=lambda: f'={PV("mna_runrate")}*(1+{V("mna_g")})+{V("mna_rev_acq")}')
    S('mna_rev', '  Revenues from future acquisitions', 'line_b', 'm', e26_input=0.0,
      ae=lambda: f'={PV("mna_runrate")}*(1+{V("mna_g")})+0.5*{V("mna_rev_acq")}',
      note='Mid-year convention: deals close evenly through the year (half a year of acquired revenues in year 1).')
    S('mna_cgp', '  Adjusted EBITDA (cash gross profit) from future acquisitions', 'line', 'm', e26_input=0.0,
      ae=lambda: f'={V("mna_rev")}*{V("mna_margin")}')
    S('mna_ppe_pct', '  Purchase price allocated to PP&E (incl. mineral reserves) %', 'driver', 'pct', ae_input=0.55)
    S('mna_int_pct', '  Purchase price allocated to intangibles %', 'driver', 'pct', ae_input=0.15)
    S('mna_gw_pct', '  Purchase price allocated to goodwill %', 'driver', 'pct',
      ae=lambda: f'=1-{V("mna_ppe_pct")}-{V("mna_int_pct")}')
    S('mna_life', '  Depreciation / depletion life of acquired assets (years)', 'driver', 'gen', ae_input=25)
    S('mna_base', '  Cumulative depreciable acquired assets (gross)', 'line', 'm', e26_input=0.0,
      ae=lambda: f'={PV("mna_base")}+{V("mna_spend")}*({V("mna_ppe_pct")}+{V("mna_int_pct")})')
    S('mna_dda', '  DDA&A of future acquisitions', 'line', 'm', e26_input=0.0,
      ae=lambda: f'=({PV("mna_base")}+0.5*{V("mna_spend")}*({V("mna_ppe_pct")}+{V("mna_int_pct")}))/{V("mna_life")}')
    S('mna_inc', '  Incremental acquisition revenues (first 12 months of ownership)', 'line', 'm', e26_input=0.0,
      ae=lambda: f'=0.5*{V("mna_rev_acq")}+0.5*{PV("mna_rev_acq")}')
    blank()
    # ---------------- Group total
    S('grp_hdr', "Group Total — Adjusted EBITDA (Vulcan's primary profit KPI; company definition)", 'block',
      note='GROUP TOTAL (CONSOLIDATED) — modelling logic')
    segrev = ['agg_rev', 'asph_rev', 'conc_rev', 'cem_rev', 'calc_rev', 'oseg_rev', 'interseg', 'deliv']
    S('g_rev', '  Total revenues (segment build)', 'line_b', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("agg_rev")}),' + '+'.join(f'N({V(k)})' for k in segrev) + ',"")',
      fc=lambda: '=' + '+'.join(f'N({V(k)})' for k in segrev + ['mna_rev']),
      note='Σ segment revenues + intersegment eliminations + delivery revenues (pre-2018) (+ future acquisitions from 2027E).')
    seggp = ['agg_gp', 'asph_gp', 'conc_gp', 'cem_gp', 'calc_gp', 'oseg_gp']
    S('g_gp', '  Gross profit (Σ segments)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("agg_gp")}),' + '+'.join(f'N({V(k)})' for k in seggp) + ',"")',
      fc=lambda: '=' + '+'.join(f'N({V(k)})' for k in seggp) + f'+N({V("mna_cgp")})-N({V("mna_dda")})')
    segdda = ['agg_dda', 'asph_dda', 'conc_dda', 'cem_dda', 'calc_dda', 'oseg_dda']
    S('g_dda', '  Segment DDA&A (Σ)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("agg_dda")}),' + '+'.join(f'N({V(k)})' for k in segdda) + ',"")',
      fc=lambda: '=' + '+'.join(f'N({V(k)})' for k in segdda) + f'+N({V("mna_dda")})')
    S('g_cgp', '  Cash gross profit (Σ segments, non-GAAP)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_dda")}),{V("g_gp")}+{V("g_dda")},"")')
    S('g_cgp_m', '  Cash gross profit margin %', 'pct', 'pct', all=ratio('g_cgp', 'g_rev'))
    S('g_ebitda', '  Adjusted EBITDA (Σ segment cash GP − SAG + corporate DDA&A + other items)', 'total', 'm',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_cgp")}),ISNUMBER({V("oth_dda")}),ISNUMBER({V("r_adj_pub")})),{V("g_cgp")}-{V("sag")}+{V("oth_dda")}+{V("oth_sum")},"")',
      fc=lambda: f'={V("g_cgp")}-{V("sag")}+{V("oth_dda")}+{V("oth_sum")}')
    S('g_ebitda_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('g_ebitda', 'g_rev'))
    S('g_ebitda_g', '  Adjusted EBITDA y/y %', 'growth', 'pct', growth='g_ebitda')
    S('g_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔRevenues)', 'pct', 'pct', prior_ratio=('g_ebitda', 'g_rev'))
    S('g_dda_tot', '  Total DDA&A (segments + corporate)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_dda")}),{V("g_dda")}+N({V("oth_dda")}),"")')
    S('g_ebit', '  Adjusted EBIT (Adjusted EBITDA − DDA&A)', 'line_b', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("g_ebitda")}),ISNUMBER({V("g_dda_tot")})),{V("g_ebitda")}-{V("g_dda_tot")},"")')
    S('g_op', '  Operating earnings (GAAP; Σ segment GP − SAG + other operating)', 'line', 'm',
      all=lambda: f'=IF(ISNUMBER({V("g_gp")}),{V("g_gp")}-{V("sag")}+N({V("oth_op")}),"")')
    S('g_rev_g', '  Total revenues y/y %', 'growth', 'pct', growth='g_rev')
    S('g_acq', '  Incremental revenues from acquisitions (disclosed / model)', 'line', 'm', data='extra.acquisition_revenue_contribution',
      annual_only=True, e26_input=0.0, ae=lambda: f'={V("mna_inc")}',
      note='10-K / releases where Vulcan quantified acquired revenues; otherwise blank (organic growth = total growth).')
    S('g_chk_rev', '  Check: segment build vs consolidated total revenues (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_rev")}),ROUND({V("g_rev")}-{V("is_rev")},1),"")')
    S('g_chk_gp', '  Check: segment build vs consolidated gross profit (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_gp")}),ROUND({V("g_gp")}-{V("is_gp")},1),"")')
    S('g_chk_op', '  Check: segment build vs consolidated operating earnings (should be 0)', 'check', 'm1',
      all=lambda: f'=IF(ISNUMBER({V("g_op")}),ROUND({V("g_op")}-{V("is_op")},1),"")')
    S('g_chk_eb', '  Check: segment build vs company-published Adjusted EBITDA (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("g_ebitda")}),ISNUMBER({V("r_adj_pub")})),ROUND({V("g_ebitda")}-{V("r_adj_pub")},1),"n/p")',
      fc=lambda: f'=ROUND({V("g_ebitda")}-{V("r_adj")},1)')
    blank()
    # ---------------- cost drivers
    S('drv_hdr', 'Cost drivers (% of revenues)', 'block', note='% OF REVENUE drivers — reference')
    S('drv_cogs', '  Cost of revenues % of total revenues', 'pct', 'pct', all=ratio('is_cogs', 'is_rev'))
    S('drv_dda', '  Total DDA&A % of total revenues', 'pct', 'pct', all=ratio('is_dda', 'is_rev'))
    S('drv_sbc', '  Share-based compensation % of total revenues', 'pct', 'pct', all=ratio('is_sbc', 'is_rev'), ae_input=0.0065,
      e26_input=0.0065)
    blank()
    S('ann_hdr', 'Annual disclosures (10-K)', 'block', note='ANNUAL DISCLOSURES — historical only (not forecast)')
    S('reserves', '  Aggregates reserves (billion tons, year end)', 'line', 'ps', data='extra.reserves_bn_tons', annual_only=True)
    S('res_life', '  Reserve life at current shipments (years)', 'line', 'yrs',
      hist=lambda: f'=IF(ISNUMBER({V("reserves")}),{V("reserves")}*1000/{V("agg_tons")},"")')
    S('employees', '  Employees (year end)', 'line', 'm', data='extra.employees', annual_only=True)
    blank()

    # ================================================================== INCOME STATEMENT
    S('sec_is', 'CONSOLIDATED INCOME STATEMENT (US GAAP)', 'section', note='CONSOLIDATED IS — forecast logic')
    S('is_rev', 'Total revenues', 'total', 'm', data='is.total_rev', flow=True, fc=lambda: f'={V("g_rev")}',
      note='Forecast linked to the segment build.')
    S('is_deliv', '  of which: delivery revenues (separate line pre-2018)', 'line', 'm', data='is.delivery_rev', flow=True)
    S('is_cogs', 'Cost of revenues', 'line', 'm', data='is.cost_of_rev', flow=True,
      fc=lambda: f'={V("is_rev")}-{V("g_gp")}', note='Forecast = revenues − segment-build gross profit.')
    S('is_gp', 'Gross profit', 'line_b', 'm', all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_rev")}-{V("is_cogs")},"")')
    S('is_sag', 'Selling, administrative and general expenses', 'line', 'm', data='is.sag', flow=True, fc=lambda: f'={V("sag")}')
    S('is_gain', 'Gain (loss) on sale of property, plant & equipment and businesses', 'line', 'm', data='is.gain_sale', flow=True,
      qe_input={3: 0.0, 4: 0.0}, ae_input=0.0)
    S('is_othop', 'Other operating income (expense), net (incl. impairments, settlements, restructuring)', 'line', 'm',
      data='is.other_op', flow=True, qe=lambda: f'={V("oth_op")}', ae=lambda: f'={V("oth_op")}',
      note='Historical: all remaining operating lines combined (cell comments give the company wording).')
    S('is_op', 'Operating earnings', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_rev")}),{V("is_gp")}-{V("is_sag")}+N({V("is_gain")})+N({V("is_othop")}),"")')
    S('is_nonop', 'Other nonoperating income (expense), net', 'line', 'm', data='is.nonop', flow=True, fc=lambda: f'={V("nonop")}')
    S('is_int', 'Interest expense, net', 'line', 'm', data='is.interest', flow=True,
      qe=lambda: f'=($DD${SC["pt_int"]}-$CL${R["is_int"]})/2',
      ae=lambda: (f'={V("d_r_leg")}*({PV("d_total")}-{PV("d_refi")}-{PV("d_rev")})+{V("d_r_refi")}*{PV("d_refi")}'
                  f'+{V("d_r_rev")}*{PV("d_rev")}-{V("d_r_cash")}*{PV("cf_end")}'),
      note='Q3/Q4-26E: FY26 projected interest expense (outlook bridge) less 1H/26. 2027E+ = rate × opening debt − yield × opening cash (no circularity).')
    S('is_ebt', 'Earnings from continuing operations before income taxes', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_op")}),{V("is_op")}+N({V("is_nonop")})-{V("is_int")},"")')
    S('is_tax', 'Income tax expense', 'line', 'm', data='is.tax', flow=True,
      qe=lambda: f'={V("is_ebt")}*$DD${SC["pt_etr"]}', ae=lambda: f'={V("is_ebt")}*{V("is_etr")}',
      note='Q3/Q4-26E at the tax rate implied by the FY26 outlook bridge; 2027E+ input ETR.')
    S('is_etr', '  Effective tax rate', 'pct', 'pct', all=ratio('is_tax', 'is_ebt'), ae_input=0.22)
    S('is_cont', 'Earnings from continuing operations', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_ebt")}),{V("is_ebt")}-{V("is_tax")},"")')
    S('is_disc', 'Earnings (loss) on discontinued operations, net of tax', 'line', 'm', data='is.disc_ops', flow=True,
      qe_input={3: 0.0, 4: 0.0}, ae_input=0.0, note='Legacy Chemicals (sold 2005) indemnities / Hewitt, Lower Passaic litigation, etc.')
    S('is_ne', 'Net earnings (incl. noncontrolling interests)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_cont")}),{V("is_cont")}+N({V("is_disc")}),"")')
    S('is_nci', '  Earnings attributable to noncontrolling interests', 'line', 'm', data='is.nci', flow=True,
      fc=lambda: f'=-{V("nci_c")}')
    S('is_ni', 'Net earnings attributable to Vulcan', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("is_ne")}),{V("is_ne")}-N({V("is_nci")}),"")')
    S('is_ni_chk', '  Check: net earnings attributable to Vulcan vs reported (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("is_ni_pub")}),ROUND({V("is_ni")}-{V("is_ni_pub")},1),"")')
    S('is_ni_pub', '  Memo: net earnings attributable to Vulcan as reported', 'memo', 'm', data='is.ni_vulcan', flow=True)
    S('is_dda', '  Memo: depreciation, depletion, accretion & amortization (total)', 'memo', 'm', data='seg.total_dda', flow=True,
      fc=lambda: f'={V("g_dda_tot")}')
    S('is_dda_chk', '  Check: Σ segment + corporate DDA&A vs total (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("is_dda")}),ISNUMBER({V("g_dda_tot")})),ROUND({V("g_dda_tot")}-{V("is_dda")},1),"")')
    S('is_sbc', '  Memo: share-based compensation expense', 'memo', 'm', data='cf.sbc', annual_only=True,
      e26=lambda: f'={V("is_rev")}*{V("drv_sbc")}', ae=lambda: f'={V("is_rev")}*{V("drv_sbc")}')
    S('eps_hdr', '(Earnings per share)', 'line', 'gen')
    S('sh_basic', '  Weighted-average basic shares (m)', 'line', 'm1', data='is.shares_basic', avg=True,
      qe=lambda: f'=$CK${R["sh_basic"]}-$CO${R["bb_shares"]}*{0.25 if CTX.col.q == 3 else 0.75}',
      e26=lambda: f'=AVERAGE({V("sh_basic","CJ")},{V("sh_basic","CK")},{V("sh_basic","CM")},{V("sh_basic","CN")})',
      ae=lambda: f'=AVERAGE({V("bb_begin")},{V("bb_end")})',
      note='Q3/Q4-26E: Q2/26 less the 2H/26 buyback phased in (¼ in Q3, ¾ in Q4). 2027E+ = average of opening and closing shares.')
    S('sh_dil', '  Weighted-average diluted shares (m)', 'line', 'm1', data='is.shares_diluted', avg=True,
      qe=lambda: f'={V("sh_basic")}+($CK${R["sh_dil"]}-$CK${R["sh_basic"]})',
      e26=lambda: f'=AVERAGE({V("sh_dil","CJ")},{V("sh_dil","CK")},{V("sh_dil","CM")},{V("sh_dil","CN")})',
      ae=lambda: f'={V("sh_basic")}+{V("d_dilutive")}')
    S('eps_basic', 'EPS – basic, net earnings attributable to Vulcan ($)', 'eps_total', 'ps', all=ratio('is_ni', 'sh_basic'))
    S('eps_dil', 'EPS – diluted, net earnings attributable to Vulcan ($)', 'eps_total', 'ps', all=ratio('is_ni', 'sh_dil'))
    S('eps_cont', '  EPS – diluted, continuing operations ($)', 'line', 'ps',
      all=lambda: f'=IFERROR(({V("is_cont")}-N({V("is_nci")}))/{V("sh_dil")},"")')
    S('eps_dil_pub', '  Memo: EPS – diluted (net earnings) as reported ($)', 'eps_memo', 'ps', data='is.eps_dil')
    S('eps_cont_pub', '  Memo: EPS – diluted, continuing operations as reported ($)', 'eps_memo', 'ps', data='is.eps_cont_dil')
    S('eps_out', '  Memo: FY26 GAAP net earnings outlook (projected bridge mid-point, $m)', 'eps_memo', 'm',
      e26=lambda: f'=$DD${SC["out_ni"]}', note='Compare with the model 2026E net earnings attributable to Vulcan above.')
    S('dps', 'Dividends declared per share ($)', 'line', 'ps', data='is.dps', flow=True,
      qe=lambda: f'=$CK${R["dps"]}', ae=lambda: f'={PV("dps")}*(1+$DD${SC["pt_dps_g"]})',
      note='Q3/Q4-26E at the current quarterly rate; 2027E+ grows with the DPS growth point estimate.')
    S('payout', '  Dividend payout (DPS / diluted EPS) %', 'pct', 'pct', all=ratio('dps', 'eps_dil'))
    blank()

    # ================================================================== RECON 1
    S('sec_r1', 'RECONCILIATION: GAAP NET EARNINGS → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'section',
      note='ADJUSTED EBITDA — per Vulcan earnings-release reconciliation (Appendix: EBITDA and Adjusted EBITDA)')
    S('r_ni', 'Net earnings attributable to Vulcan (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('r_tax', '  (+) Income tax expense (incl. discontinued operations where presented)', 'line', 'm', data='ngaap.ebitda_bridge_tax', flow=True,
      fc=lambda: f'={V("is_tax")}')
    S('r_int', '  (+) Interest expense, net', 'line', 'm', all=lambda: f'={V("is_int")}')
    S('r_dda', '  (+) Depreciation, depletion, accretion & amortization', 'line', 'm', all=lambda: f'={V("is_dda")}')
    S('r_discat', '  (+) Discontinued operations, after tax (inside EBITDA build, 2022–Q1/23 presentation)', 'line', 'm',
      data='ngaap.ebitda_disc_at', flow=True, h1_partial=True)
    S('r_ebitda', '  = EBITDA (model)', 'line_b', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("r_ni")}),ISNUMBER({V("r_dda")})),{V("r_ni")}+N({V("r_tax")})+N({V("r_int")})+{V("r_dda")}+N({V("r_discat")}),"")')
    S('r_ebitda_pub', '  Memo: EBITDA as published', 'memo', 'm', data='ngaap.ebitda_pub', flow=True)
    S('r_ebitda_chk', '  Check: model EBITDA vs published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_ebitda_pub")}),ROUND({V("r_ebitda")}-{V("r_ebitda_pub")},1),"n/p")')
    ADJ = [('r_disc', 'disc_ops', '(Gain) loss on discontinued operations (pre-tax)'),
           ('r_gain', 'gain_sale', '(Gain) loss on sale of real estate and businesses, net'),
           ('r_imp', 'impairment', 'Loss on impairments / asset write-downs'),
           ('r_divest', 'divested_ops', 'Charges associated with divested operations'),
           ('r_acq', 'acquisition', 'Acquisition / business-development related charges (incl. inventory step-up)'),
           ('r_restr', 'restructuring', 'Restructuring, reorganization & CEO transition charges'),
           ('r_legal', 'legal_env', 'Legal & environmental settlements / recoveries, net'),
           ('r_pens', 'pension', 'Pension settlement / curtailment charges'),
           ('r_other', 'other', 'Other adjusting items (COVID-19, exchange-offer costs, property donation, etc.)')]
    for k, f, lab in ADJ:
        S(k, f'  (+) {lab}', 'line', 'm', data=f'ngaap.adj_items.{f}', flow=True, adj=True, h1_partial=True,
          qe_input={3: 0.0, 4: 0.0}, ae_input=0.0)
    S('r_adj_tot', '  Total adjusting items', 'line', 'm', all=lambda: f'=SUM({V("r_disc")}:{V("r_other")})')
    S('r_adj', '  = Adjusted EBITDA (model bridge)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),{V("r_ebitda")}+{V("r_adj_tot")},"")',
      fc=lambda: f'={V("r_ebitda")}+{V("r_adj_tot")}',
      note='Historical shown only where Vulcan published Adjusted EBITDA (EBITDA only before the adjusted measure).')
    S('r_adj_m', '  Adjusted EBITDA margin %', 'pct', 'pct', all=ratio('r_adj', 'is_rev'))
    S('r_adj_pub', '  Company-published Adjusted EBITDA', 'memo', 'm', data='ngaap.adj_ebitda_pub', flow=True)
    S('r_adj_chk', '  Check: model bridge vs company-published (should be 0)', 'check', 'm1',
      hist=lambda: f'=IF(ISNUMBER({V("r_adj_pub")}),ROUND({V("r_adj")}-{V("r_adj_pub")},1),"n/p")')
    S('r_def', '  Definition basis (company Adjusted EBITDA definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('r_cur_hdr', 'Memo — current definition applied to all periods (model):', 'sub', 'gen')
    S('r_cur', '  Adjusted EBITDA — current definition (EBITDA + company adjusting items; EBITDA where none published)', 'line_b', 'm',
      all=lambda: f'=IF(ISNUMBER({V("r_ebitda")}),IF(ISNUMBER({V("r_adj_pub")}),{V("r_adj")},{V("r_ebitda")}+N({V("r_adj_tot")})),"")',
      fc=lambda: f'={V("r_adj")}',
      note='Consistent series: where Vulcan did not publish Adjusted EBITDA, EBITDA (model) + any disclosed one-off items.')
    S('r_cur_m', '  Adjusted EBITDA — current definition margin %', 'pct', 'pct', all=ratio('r_cur', 'is_rev'))
    blank()

    # ================================================================== RECON 2
    S('sec_r2', 'RECONCILIATION: GAAP OPERATING EARNINGS → ADJUSTED EBIT → ADJUSTED EBITDA (model; ties the segment build to the company bridge)', 'section',
      note='ADJUSTED EBIT — model measure (Vulcan publishes Adjusted EBITDA, not adjusted operating earnings)')
    S('o_op', 'Operating earnings (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_op")}')
    S('o_nonop', '  (+) Other nonoperating income (expense), net', 'line', 'm', all=lambda: f'=N({V("is_nonop")})')
    S('o_nci', '  (−) Earnings attributable to noncontrolling interests', 'line', 'm', all=lambda: f'=-N({V("is_nci")})')
    S('o_adj', '  (+) Adjusting items excl. discontinued operations (company bridge)', 'line', 'm',
      all=lambda: f'=N({V("r_adj_tot")})-N({V("r_disc")})')
    S('o_ebit', '  = Adjusted EBIT (model)', 'total', 'm',
      all=lambda: f'=IF(ISNUMBER({V("o_op")}),{V("o_op")}+{V("o_nonop")}+{V("o_nci")}+{V("o_adj")},"")')
    S('o_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_ebit', 'is_rev'))
    S('o_dda', '  (+) Depreciation, depletion, accretion & amortization', 'line', 'm', all=lambda: f'={V("is_dda")}')
    S('o_ebitda', '  = Adjusted EBITDA (via operating earnings)', 'line_b', 'm',
      all=lambda: f'=IF(AND(ISNUMBER({V("o_ebit")}),ISNUMBER({V("o_dda")})),{V("o_ebit")}+{V("o_dda")},"")')
    S('o_chk', '  Check: vs company bridge (should be 0; differences = tax on discontinued ops in the company bridge)', 'check', 'm1',
      hist=lambda: f'=IF(AND(ISNUMBER({V("o_ebitda")}),ISNUMBER({V("r_adj_pub")})),ROUND({V("o_ebitda")}-{V("r_adj")},1),"n/p")',
      fc=lambda: f'=ROUND({V("o_ebitda")}-{V("r_adj")},1)')
    S('o_ebit_g', '  Adjusted EBIT y/y %', 'growth', 'pct', growth='o_ebit')
    blank()

    # ================================================================== RECON 3
    S('sec_r3', 'RECONCILIATION: GAAP NET EARNINGS → ADJUSTED NET EARNINGS → ADJUSTED DILUTED EPS (continuing operations)', 'section',
      note='ADJUSTED EPS — company definition in force in each period (Vulcan reconciles in per-share amounts)')
    S('e_ni', 'Net earnings attributable to Vulcan (GAAP)', 'line_b', 'm', all=lambda: f'={V("is_ni")}')
    S('e_disc', '  (−) Discontinued operations, net of tax', 'line', 'm', all=lambda: f'=-N({V("is_disc")})')
    S('e_adj', '  (+) Adjusting items excl. discontinued operations, pre-tax', 'line', 'm', all=lambda: f'={V("o_adj")}')
    S('e_tax', '  (−) Income tax effect of adjusting items', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_items_ps")}),{V("e_items_ps")}*{V("sh_dil")}-{V("e_disc")}-{V("e_adj")},"")',
      fc=lambda: f'=-{V("e_adj")}*{V("e_rate")}',
      note='Historical = company per-share items net of tax × diluted shares − pre-tax items − discontinued operations (company reconciles per share).')
    S('e_disc_tax', '  (+/−) Discrete tax items (NOL valuation allowance, tax reform, etc.)', 'line', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_disc_ps")}),{V("e_disc_ps")}*{V("sh_dil")},"")', qe_input={3: 0.0, 4: 0.0}, ae_input=0.0)
    S('e_adjni', '  = Adjusted net earnings attributable to Vulcan (model bridge)', 'total', 'm',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),SUM({V("e_ni")}:{V("e_disc_tax")}),"")',
      fc=lambda: f'=SUM({V("e_ni")}:{V("e_disc_tax")})',
      note='Historical shown only where Vulcan published Adjusted EPS.')
    S('e_rate', '  Tax rate applied to adjustments (forecast input; historical = implied)', 'pct', 'pct',
      hist=lambda: f'=IFERROR(-{V("e_tax")}/{V("e_adj")},"")', qe=lambda: f'=$DD${SC["pt_etr"]}', e26=lambda: f'=$DD${SC["pt_etr"]}',
      ae=lambda: f'={V("is_etr")}')
    S('e_sh', '  Weighted-average diluted shares (m)', 'line', 'm1', all=lambda: f'={V("sh_dil")}')
    S('e_eps', 'Adjusted EPS – diluted, continuing operations ($) (model bridge)', 'eps_total', 'ps', all=ratio('e_adjni', 'e_sh'))
    S('e_pub', '  Company-published Adjusted diluted EPS ($)', 'eps_memo', 'ps', data='ngaap.adj_eps_pub')
    S('e_chk', '  Check: model bridge vs company-published Adjusted EPS ($, should be 0.00 ± rounding)', 'check', 'ps',
      hist=lambda: f'=IF(ISNUMBER({V("e_pub")}),ROUND({V("e_eps")}-{V("e_pub")},2),"n/p")')
    S('e_items_ps', '  Input: items included in Adjusted EBITDA, net of tax ($/share, incl. disc. ops, as published)', 'memo', 'ps',
      data='ngaap.e_items_incl')
    S('e_disc_ps', '  Input: discrete tax items ($/share, as published)', 'memo', 'ps', data='ngaap.eps_discrete_tax_ps')
    S('e_def', '  Definition basis (company Adjusted EPS definition in force)', 'text', 'gen',
      note='Definition changes are flagged in the column where they take effect (cell comment gives the detail).')
    S('e_cur_hdr', 'Memo — current definition applied to all periods (model):', 'sub', 'gen')
    S('e_cur', '  Adjusted net earnings — current definition', 'line_b', 'm',
      all=lambda: (f'=IF(ISNUMBER({V("e_adjni")}),{V("e_adjni")},IF(ISNUMBER({V("is_ni")}),{V("is_ni")}-N({V("is_disc")})'
                   f'+N({V("o_adj")})*(1-MAX(0.15,MIN(0.4,N({V("is_etr")})))),""))'),
      fc=lambda: f'={V("e_adjni")}',
      note='Periods without a published Adjusted EPS: net earnings from continuing operations + company adjusting items × (1 − period ETR, bounded 15–40%).')
    S('e_cur_eps', '  Adjusted EPS — current definition, diluted ($)', 'line_b', 'ps', all=ratio('e_cur', 'sh_dil'))
    blank()

    # ================================================================== GROWTH & MARGINS
    S('sec_gm', 'GROWTH & MARGINS', 'section', note='GROWTH & MARGINS (consolidated) — forecast outputs')
    S('gm_rev', '  Total revenues y/y %', 'growth', 'pct', growth='is_rev')
    S('gm_org', '  Total revenues — organic y/y %', 'growth', 'pct',
      all=lambda: f'=IFERROR({V("gm_rev")}-{V("gm_acq")},"")', need_prior=True,
      note='Organic = total growth less disclosed incremental acquisition revenues (annual only).')
    S('gm_acq', '  Total revenues — acquisition y/y %', 'growth', 'pct',
      all=lambda: f'=IFERROR(N({V("g_acq")})/{P("is_rev")},"")', need_prior=True)
    S('gm_vol', '  Aggregates shipments y/y %', 'growth', 'pct', all=lambda: f'={V("agg_tons_g")}', need_prior=True)
    S('gm_price', '  Aggregates freight-adjusted price y/y %', 'growth', 'pct', all=lambda: f'={V("agg_price_g")}', need_prior=True)
    S('gm_ebitda', '  Adjusted EBITDA (current definition) y/y %', 'growth', 'pct', growth='r_cur')
    S('gm_op', '  Operating earnings (GAAP) y/y %', 'growth', 'pct', growth='is_op')
    S('gm_ni', '  Net earnings attributable to Vulcan y/y %', 'growth', 'pct', growth='is_ni')
    S('gm_eps', '  Adjusted EPS (current definition) y/y %', 'growth', 'pct', growth='e_cur_eps')
    S('gm_gm', '  Gross margin %', 'pct', 'pct', all=ratio('is_gp', 'is_rev'))
    S('gm_cgp_t', '  Aggregates cash gross profit per ton ($)', 'line', 'ps', all=lambda: f'={V("agg_cgp_t")}')
    S('gm_ebitda_m', '  Adjusted EBITDA margin (current definition) %', 'pct', 'pct', all=ratio('r_cur', 'is_rev'))
    S('gm_inc', '  Incremental Adjusted EBITDA margin (ΔEBITDA / ΔRevenues)', 'pct', 'pct', prior_ratio=('r_cur', 'is_rev'))
    S('gm_ebit_m', '  Adjusted EBIT margin %', 'pct', 'pct', all=ratio('o_ebit', 'is_rev'))
    S('gm_op_m', '  Operating margin (GAAP) %', 'pct', 'pct', all=ratio('is_op', 'is_rev'))
    S('gm_net_m', '  Net margin %', 'pct', 'pct', all=ratio('is_ni', 'is_rev'))
    S('gm_sag', '  SAG % of revenues', 'pct', 'pct', all=ratio('is_sag', 'is_rev'))
    blank()
