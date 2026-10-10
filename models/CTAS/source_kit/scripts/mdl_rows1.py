"""Row definitions part 1: segment build, UniFirst, future M&A, group total & guidance calibration."""
from mdl_core import Row, BYNAME, prior_year, A27
import curated as C

def build_part1(S, H, X):
    """S: Sheet registry; H: hist dict; X: helpers dict (scenario refs etc.)."""
    def hv(*keys, scale=1.0):
        def f(p):
            h = H.get(p.name, {})
            for k in keys:
                v = h.get(k)
                if isinstance(v, (int, float)):
                    return v * scale
            return None
        return f
    def yoy(k):
        def f(p):
            if prior_year(p) is None: return None
            return '=IF(AND(ISNUMBER({%s}),ISNUMBER({%s@py})),IFERROR({%s}/{%s@py}-1,""),"")' % (k, k, k, k)
        return f
    def ratio(n, d):
        return '=IF(AND(ISNUMBER({%s}),ISNUMBER({%s})),IFERROR({%s}/{%s},""),"")' % (n, d, n, d)
    SUMQ = lambda k: '=SUM({%s@q1},{%s@q2},{%s@q3},{%s@q4})' % (k, k, k, k)
    SC = X['scn']          # function(lever_key) -> CHOOSE formula fragment for the period's year
    PT = X['pt']           # function(name) -> absolute ref to point-estimate cell (base col)
    add = S.add

    add(Row(None, 'SEGMENT P&L — UNIFORM RENTAL & FACILITY SERVICES · FIRST AID & SAFETY · ALL OTHER · UNIFIRST (organic growth + M&A build)', 'sec',
            note='SEGMENT BUILD — modelling logic (organic growth → revenues → gross margin → S&A → segment operating income)'))
    S.blank()

    segs = [
        ('urfs', 'Uniform Rental & Facility Services (UR&FS) — reportable segment: uniform & garment rental, mats, mops, shop towels, restroom & hygiene, water, Clean Room; legacy "Rental Uniforms & Ancillary Products" segment to FY2014 (FY2015 recast incl. storage)',
         ('seg_urfs_rev', 'seg_l_rental_rev', 'rev_urfs_line'), ('seg_urfs_gm', 'seg_l_rental_gm', 'gm_urfs_line'), ('seg_urfs_sga', 'seg_l_rental_sga'),
         ('seg_urfs_oi', 'seg_urfs_pbt', 'seg_l_rental_pbt'), C.ORG_URFS, 'URFS'),
        ('fas', 'First Aid & Safety Services (FA&S) — reportable segment from FY2016 (FY2015 recast); first aid cabinets, safety products & training, eyewash, AEDs',
         ('seg_fas_rev',), ('seg_fas_gm',), ('seg_fas_sga',), ('seg_fas_oi', 'seg_fas_pbt'), C.ORG_FAS, 'FAS'),
        ('oth', 'All Other — Fire Protection Services + Uniform Direct Sale (from FY2016; FY2015 recast)',
         ('seg_oth_rev',), ('seg_oth_gm',), ('seg_oth_sga',), ('seg_oth_oi', 'seg_oth_pbt'), {}, 'OTH'),
    ]
    for s, title, krev, kgm, ksga, koi, org, lev in segs:
        add(Row(None, title, 'sub', note={'urfs': 'UR&FS — modelling logic', 'fas': 'FIRST AID & SAFETY — modelling logic', 'oth': 'ALL OTHER (FIRE + UNIFORM DIRECT SALE) — modelling logic'}[s]))
        add(Row(f'{s}_rev', '  Revenues', 'key', 'n1', h=hv(*krev),
                fq='={%s_rev@py}*(1+{%s_g})' % (s, s), f27=SUMQ(f'{s}_rev'), fa='={%s_rev@pa}*(1+{%s_g})' % (s, s), cagr=True,
                note='Q2–Q4/27E: prior-year quarter × (1 + Q1/27 y/y growth ex-workday effect + revenue-outlook calibration Δ). FY28E+: prior year × (1 + scenario organic growth %s_org); bolt-on M&A modelled separately (Future acquisitions block).' % lev))
        add(Row(f'{s}_g', '  Revenues y/y %', 'yoy', 'p1', h=yoy(f'{s}_rev'),
                fq='={%s_g@$P:FY2027Q1}-{wd_q1@$P:FY2027Q1}+{cal_g}' % s, f27='=IFERROR({%s_rev}/{%s_rev@pa}-1,"")' % (s, s),
                fa=lambda p, lev=lev: '=' + SC(f'{lev}_org', p),
                note='Q2–Q4/27E: Q1/27 y/y less the Q1 extra-workday effect (row "Workday effect") + calibration Δ (Group block). FY28E+: scenario lever.'))
        add(Row(f'{s}_org', '  Organic growth % (company-disclosed, segment)', 'yoy', 'p1',
                h=(lambda p, org=org: org[p.name] / 100 if p.name in org else None),
                fq='={%s_g}' % s, f27='={%s_g}' % s, fa='={%s_g}' % s, level=1,
                note='Segment organic growth as disclosed in releases (FY2016–21) and 10-Q MD&A (FY2022+); blank where not disclosed. Forecast: no acquisition/FX/workday effect assumed inside segments.' if s != 'oth' else 'Cintas does not disclose All Other organic growth.'))
        add(Row(f'{s}_inorg', '  Acquisitions, FX & workday effects % (derived = y/y − organic)', 'yoy', 'p1',
                h=lambda p, s=s: '=IF(AND(ISNUMBER({%s_g}),ISNUMBER({%s_org})),{%s_g}-{%s_org},"")' % (s, s, s, s), level=1))
        add(Row(f'{s}_gm', '  Gross margin (GAAP)', 'line', 'n1', h=hv(*kgm),
                fq='={%s_rev}*{%s_gmp}' % (s, s), f27=SUMQ(f'{s}_gm'), fa='={%s_rev}*{%s_gmp}' % (s, s), cagr=True))
        add(Row(f'{s}_gmp_pre', '  Gross margin % before outlook calibration (Q2–Q4/27E helper)', 'pct', 'p1',
                fq='={%s_gmp@py}+({%s_gmp@$P:FY2027Q1}-{%s_gmp@$P:FY2026Q1})' % (s, s, s), level=1,
                note='Prior-year quarter margin + (Q1/27 − Q1/26 margin drift).'))
        add(Row(f'{s}_gmp', '  Gross margin %', 'pct', 'p1', h=ratio(f'{s}_gm', f'{s}_rev'),
                fq='={%s_gmp_pre}+{cal_m}' % s, f27=ratio(f'{s}_gm', f'{s}_rev'), fa=lambda p, lev=lev: '=' + SC(f'{lev}_GM', p),
                note='Q2–Q4/27E: helper + uniform margin calibration Δ (solved to the FY27 adjusted EPS guidance). FY28E+: scenario lever %s_GM (level).' % lev))
        add(Row(f'{s}_sga', '  Selling & administrative expenses (segment)', 'line', 'n1', h=hv(*ksga),
                fq='={%s_rev}*{%s_sgap}' % (s, s), f27=SUMQ(f'{s}_sga'), fa='={%s_rev}*{%s_sgap}' % (s, s)))
        add(Row(f'{s}_sgap', '  S&A % of revenues', 'pct', 'p1', h=ratio(f'{s}_sga', f'{s}_rev'),
                fq='={%s_sgap@py}+({%s_sgap@$P:FY2027Q1}-{%s_sgap@$P:FY2026Q1})' % (s, s, s),
                f27=ratio(f'{s}_sga', f'{s}_rev'), fa='={%s_sgap@$P:FY2027}+({leg_sgap_tgt}-{leg_sgap@$P:FY2027})' % s,
                note='Q2–Q4/27E: prior-year quarter + Q1 drift. FY28E+: FY27E segment ratio + Δ of the consolidated legacy S&A lever SA_pct vs FY27E.'))
        add(Row(f'{s}_oi', '  Segment operating income (before special items)', 'key', 'n1',
                h=lambda p, s=s: '=IF(AND(ISNUMBER({%s_gm}),ISNUMBER({%s_sga})),{%s_gm}-{%s_sga},"")' % (s, s, s, s),
                fq='={%s_gm}-{%s_sga}' % (s, s), f27='={%s_gm}-{%s_sga}' % (s, s), fa='={%s_gm}-{%s_sga}' % (s, s), cagr=True))
        add(Row(f'{s}_oim', '  Segment operating margin %', 'pct', 'p1', h=ratio(f'{s}_oi', f'{s}_rev'),
                fq=ratio(f'{s}_oi', f'{s}_rev'), f27=ratio(f'{s}_oi', f'{s}_rev'), fa=ratio(f'{s}_oi', f'{s}_rev')))
        add(Row(f'{s}_oi_rep', '  Memo: segment operating income / income before taxes as reported (incl. segment special items)', 'memo', 'n1',
                h=hv(*koi), level=1))
        S.blank()

    # legacy segments memo
    add(Row(None, 'Legacy reportable segments to FY2015 (as originally reported; memo — not forecast)', 'sub', note='LEGACY SEGMENTS — historical disclosure only'))
    for k, lab in (('l_uds', 'Uniform Direct Sales'), ('l_fasfp', 'First Aid, Safety & Fire Protection'), ('l_doc', 'Document Management (shredding & storage; Shred-it JV Apr-2014, storage sold FY2015–16)')):
        add(Row(f'{k}_rev', f'  Memo: {lab} — revenues', 'memo', 'n1', h=hv(f'seg_{k}_rev'), level=1))
        add(Row(f'{k}_pbt', f'  Memo: {lab} — income before income taxes', 'memo', 'n1', h=hv(f'seg_{k}_pbt'), level=1))
    add(Row('leg_other_rev', '  Other services — legacy segments (UDS + FAS&FP + Document Mgmt; IS "other services" line where no segment data)', 'line', 'n1',
            h=lambda p: (None if p.fy >= 2015 else ('=SUM({l_uds_rev},{l_fasfp_rev},{l_doc_rev})' if H.get(p.name, {}).get('seg_l_uds_rev') is not None else H.get(p.name, {}).get('rev_other_line')))))
    add(Row('leg_other_gm', '  Other services — legacy gross margin', 'line', 'n1',
            h=lambda p: (None if p.fy >= 2015 else (
                sum(H[p.name].get(f'seg_{k}_gm', 0) for k in ('l_uds', 'l_fasfp', 'l_doc')) if H.get(p.name, {}).get('seg_l_uds_gm') is not None
                else (H[p.name]['rev_other_line'] - H[p.name]['cogs_other'] if H.get(p.name, {}).get('rev_other_line') is not None else None)))))
    S.blank()

    # ---------------- UniFirst
    add(Row(None, 'UniFirst Corporation (NYSE: UNF) — pending acquisition (merger agreement 10-Mar-2026; $155.00 cash + 0.7720 CTAS shares per UNF share; FTC Second Request 11-Jun-2026)', 'sub',
            note='UNIFIRST — modelling logic (toggle & closing date in the scenario table; NOT in company FY27 guidance)'))
    add(Row('unf_on', '  Transaction included (1 = consolidate from closing; 0 = standalone Cintas)', 'line', 'gen',
            fq='={unf_toggle@abs}', f27='={unf_toggle@abs}', fa='={unf_toggle@abs}',
            note='Switch in the scenario table (point estimates). 0 removes UniFirst revenues, earnings, financing, share issuance and PPA from all statements.'))
    pdays = {'FY2027Q2': ('DATE(2026,9,1)', 'DATE(2026,11,30)'), 'FY2027Q3': ('DATE(2026,12,1)', 'DATE(2027,2,28)'), 'FY2027Q4': ('DATE(2027,3,1)', 'DATE(2027,5,31)')}
    add(Row('unf_days', '  Days consolidated in period (assumed closing date → scenario table)', 'line', 'n0',
            fq=lambda p: '=MAX(0,%s-MAX(%s,{unf_close@abs})+1)*{unf_on}' % (pdays[p.name][1], pdays[p.name][0]),
            f27=SUMQ('unf_days'), fa='=365*{unf_on}',
            note='Base: closing assumed 31-Dec-2026 (company: "prior to the end of calendar 2026"; outside date 10-Jan-2027, extendable to Sep-2027). Q3/27E = 31-Dec to 28-Feb.'))
    add(Row('unf_rr', '  UniFirst revenue run-rate, annualised (standalone; UNF fiscal year ends Aug)', 'line', 'n1',
            h=lambda p: {'FY2026': 2492.672}.get(p.name),
            fq='={unf_rr@$P:FY2027}', f27='={unf_rr@pa}*(1+{unf_g})', fa='={unf_rr@pa}*(1+{unf_g})',
            note='FY2026 column = UNF LTM to 30-May-2026 ($2,492.7m: Q4/FY25 614.4 + Q1–Q3/FY26 1,878.2; 8-K Ex.99 earnings releases). UNF FY26 (ended 29-Aug-26) not yet reported on EDGAR.'))
    add(Row('unf_g', '  UniFirst standalone revenue growth %', 'yoy', 'p1',
            h=lambda p: {'FY2026': 0.033}.get(p.name), f27=lambda p: '=' + SC('UNF_g', p, fy27=True), fa=lambda p: '=' + SC('UNF_g', p),
            note='FY2026 column: UNF 9M/FY26 y/y +3.3% (1,878.2 vs 1,817.9). Forecast: scenario lever UNF_g.'))
    add(Row('unf_rev', '  Revenues (consolidated from closing)', 'key', 'n1',
            fq='={unf_rr}*{unf_days}/365', f27=SUMQ('unf_rev'), fa='={unf_rr}*{unf_on}'))
    add(Row('unf_gmp', '  Standalone gross margin % (Cintas presentation: cost of sales incl. production D&A; before synergies)', 'pct', 'p1',
            fq='={unf_gmp@$P:FY2027}', f27='={unf_gm_in@abs}', fa='={unf_gmp@pa}',
            note='UNF LTM: cost of revenues ex-D&A 63.3% of revenue + ~85% of D&A (5.7%) in cost of sales → ~31.8% gross margin on Cintas presentation.'))
    add(Row('unf_syn_pct', '  Cost synergies realised — % of $375m run-rate (scenario)', 'pct', 'p1',
            fq='={unf_syn_pct@$P:FY2027}', f27=lambda p: '=' + SC('UNF_syn', p, fy27=True), fa=lambda p: '=MIN(1,' + SC('UNF_syn', p) + ')',
            note='~$375m run-rate operating cost synergies "within four years" (deal 8-K 11-Mar-2026): material cost, production, delivery & G&A. No annual phasing disclosed → scenario lever UNF_syn.'))
    add(Row('unf_syn', '  (+) Cost synergies realised (USDm)', 'line', 'n1',
            fq='={unf_syn_tgt@abs}*{unf_syn_pct}*{unf_days}/365', f27=SUMQ('unf_syn'), fa='={unf_syn_tgt@abs}*{unf_syn_pct}*{unf_on}'))
    add(Row('unf_gm', '  Gross margin (GAAP; incl. cost-of-sales share of synergies & PP&E step-up depreciation)', 'line', 'n1',
            fq='={unf_rev}*{unf_gmp}+{unf_syn}*{unf_syn_cogs@abs}-{unf_ppe_dep@abs}*{unf_days}/365',
            f27=SUMQ('unf_gm'), fa='={unf_rev}*{unf_gmp}+{unf_syn}*{unf_syn_cogs@abs}-{unf_ppe_dep@abs}*{unf_on}',
            note='Synergy split input: 65% cost of sales (material, production, delivery) / 35% S&A. Net PP&E step-up depreciation: buildings FV $558.7m / 20y = $27.9m vs $27.5m eliminated (424B3 pro forma note) → +$0.4m p.a.'))
    add(Row('unf_sgap', '  Standalone S&A % of revenues (before synergies & PPA amortization)', 'pct', 'p1',
            fq='={unf_sgap@$P:FY2027}', f27='={unf_sga_in@abs}', fa='={unf_sgap@pa}',
            note='UNF LTM SG&A ex merger costs $605.4m (24.3%) + non-production D&A (~0.8%).'))
    add(Row('unf_amort', '  (+) Amortization of acquired intangibles (PPA; within S&A)', 'line', 'n1',
            fq='={unf_amort_y@abs}*{unf_days}/365', f27=SUMQ('unf_amort'),
            fa=lambda p: '=(%s)*{unf_on}' % ('{unf_amort_y@abs}' if p.fy <= 2029 else '{unf_amort_y2@abs}'),
            note='Customer relationships $1,241m / 15y ($82.7m) + trade names $50m / 3y ($16.7m) = $98.3m p.a. for three years, then $82.7m (424B3 pro forma note). Not adjusted out (company adjusted EPS excludes only transaction & integration costs).'))
    add(Row('unf_sga', '  S&A (USDm; consolidated in the S&A line)', 'line', 'n1',
            fq='={unf_rev}*{unf_sgap}-{unf_syn}*(1-{unf_syn_cogs@abs})+{unf_amort}', f27=SUMQ('unf_sga'),
            fa='={unf_rev}*{unf_sgap}-{unf_syn}*(1-{unf_syn_cogs@abs})+{unf_amort}'))
    add(Row('unf_oi', '  Operating income contribution (before transaction & integration costs)', 'key', 'n1',
            fq='={unf_gm}-{unf_sga}', f27='={unf_gm}-{unf_sga}', fa='={unf_gm}-{unf_sga}'))
    add(Row('unf_da_pct', '  Standalone D&A % of revenues (excl. UNF acquired-intangible amortization)', 'pct', 'p1',
            fq='={unf_da_pct@$P:FY2027}', f27='={unf_da_in@abs}', fa='={unf_da_pct@pa}',
            note='UNF LTM D&A $142.2m less ~$17m acquired-intangible amortization (eliminated in PPA) ≈ 5.0% of revenue.'))
    add(Row('unf_da', '  D&A of UniFirst (standalone D&A + PP&E step-up + PPA amortization)', 'line', 'n1',
            fq='={unf_rev}*{unf_da_pct}+{unf_ppe_dep@abs}*{unf_days}/365+{unf_amort}', f27=SUMQ('unf_da'),
            fa='={unf_rev}*{unf_da_pct}+{unf_ppe_dep@abs}*{unf_on}+{unf_amort}'))
    add(Row('unf_ebitda', '  Memo: UniFirst Adjusted EBITDA contribution (OI + D&A)', 'memo', 'n1',
            fq='={unf_oi}+{unf_da}', f27='={unf_oi}+{unf_da}', fa='={unf_oi}+{unf_da}',
            note='Cross-check: UNF LTM Adjusted EBITDA $320.3m (12.8%) incl. $12.8m SBC add-back; Cintas basis (no SBC add-back) ≈ $307m. Deal: EV $5.5bn ≈ 8.0x TTM EBITDA incl. $375m synergies.'))
    add(Row('unf_ebitda_m', '  Memo: UniFirst Adjusted EBITDA margin %', 'pct', 'p1', fq=ratio('unf_ebitda', 'unf_rev'), f27=ratio('unf_ebitda', 'unf_rev'), fa=ratio('unf_ebitda', 'unf_rev')))
    add(Row('unf_cost', '  Transaction, retention & integration costs (one-time; excluded from adjusted results)', 'line', 'n1',
            h=lambda p: {'FY2026': 15.136, 'FY2026Q4': 14.024, 'FY2027Q1': 14.412}.get(p.name),
            fq=lambda p: {'FY2027Q2': '={unf_pre_q@abs}', 'FY2027Q3': '={unf_pre_q@abs}+({unf_close_costs@abs}+{unf_int_tot@abs}*{unf_int_y1@abs}*0.4)*IF({unf_days}>0,1,0)',
                          'FY2027Q4': '={unf_pre_q@abs}*IF({unf_days@P:FY2027Q3}>0,0,1)+{unf_int_tot@abs}*{unf_int_y1@abs}*0.6*{unf_on}'}[p.name],
            f27=SUMQ('unf_cost'), fa=lambda p: '={unf_int_tot@abs}*%s*{unf_on}' % {2028: '{unf_int_y2@abs}', 2029: '{unf_int_y3@abs}', 2030: '{unf_int_y4@abs}', 2031: '0'}[p.fy],
            note='Pre-close: ~$15m per quarter of transaction costs (Q1/27 $14.4m). At close: Cintas transaction costs $34.0m + retention bonuses $38.7m (424B3). Integration (severance, retention, lease exits): not quantified on EDGAR — CFO: "in line on a proportional basis with G&K" (~$138m on a $2.2bn deal) → $350m input phased 15/45/30/10%.'))
    S.blank()

    # ---------------- future acquisitions
    add(Row(None, 'Future acquisitions (M&A lever — tuck-in uniform, first-aid & fire businesses; unallocated; deals closed from FY2028E)', 'sub',
            note='M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention'))
    add(Row('ma_spend', '  Acquisition spend (USDm, scenario)', 'line', 'n1', h=lambda p: (-H[p.name]['cf_acq'] if p.fy >= 2013 and not p.is_q and 'cf_acq' in H.get(p.name, {}) else None),
            fa=lambda p: '=' + SC('MA_spend', p),
            note='Historical: cash paid for acquisitions (CF statement; FY2017 incl. G&K $2.1bn). Cintas spends ~$100–400m p.a. on tuck-ins outside large deals. FY27E bolt-ons inside legacy run-rate (guidance excludes future acquisitions).'))
    add(Row('ma_mult', '  Purchase multiple — EV / sales (x)', 'line', 'x1', fa='={ma_mult_in@abs}'))
    add(Row('ma_sales', '  Annualised sales acquired in the year', 'line', 'n1', fa='=IFERROR({ma_spend}/{ma_mult},0)'))
    add(Row('ma_g', '  Growth of acquired businesses after acquisition %', 'pct', 'p1', fa='={urfs_g}'))
    add(Row('ma_rr', '  Run-rate sales of businesses acquired (year end)', 'line', 'n1',
            fa=lambda p: '={ma_sales}' if p.fy == 2028 else '={ma_rr@pa}*(1+{ma_g})+{ma_sales}'))
    add(Row('ma_rev', '  Revenues from future acquisitions', 'key', 'n1',
            fa=lambda p: '={ma_sales}*0.5' if p.fy == 2028 else '={ma_rr@pa}*(1+{ma_g})+{ma_sales}*0.5',
            note='Mid-year convention: deals close evenly through the year (half a year of sales in year 1).'))
    add(Row('ma_oim', '  Operating margin of acquired businesses % (after intangible amortization)', 'pct', 'p1', fa='={ma_oim_in@abs}'))
    add(Row('ma_gmp', '  Gross margin of acquired businesses %', 'pct', 'p1', fa='={ma_gmp_in@abs}'))
    add(Row('ma_gm', '  Gross margin from future acquisitions', 'line', 'n1', fa='={ma_rev}*{ma_gmp}'))
    add(Row('ma_sga', '  S&A of future acquisitions (incl. amortization)', 'line', 'n1', fa='={ma_gm}-{ma_rev}*{ma_oim}'))
    add(Row('ma_gw_pct', '  Goodwill % of spend (balance: acquired intangibles; tangible assets negligible)', 'pct', 'p1', fa='={ma_gw_in@abs}'))
    add(Row('ma_life', '  Intangible amortization life (years)', 'line', 'n1', fa='={ma_life_in@abs}'))
    add(Row('ma_int_cum', '  Cumulative acquired intangibles (gross)', 'line', 'n1',
            fa=lambda p: '={ma_spend}*(1-{ma_gw_pct})' if p.fy == 2028 else '={ma_int_cum@pa}+{ma_spend}*(1-{ma_gw_pct})'))
    add(Row('ma_amort', '  Amortization of future-acquisition intangibles (within S&A)', 'line', 'n1',
            fa=lambda p: '=IFERROR({ma_spend}*(1-{ma_gw_pct})/{ma_life}*0.5,0)' if p.fy == 2028 else '=IFERROR({ma_int_cum@pa}/{ma_life}+{ma_spend}*(1-{ma_gw_pct})/{ma_life}*0.5,0)'))
    add(Row('ma_da', '  D&A of acquired businesses (amortization + 1.5% of sales depreciation)', 'line', 'n1', fa='={ma_amort}+{ma_rev}*0.015'))
    S.blank()

    # ---------------- group total & calibration
    add(Row(None, "Group Total — revenues & gross margin (segment build) → adjusted operating income (Cintas' guided profit metric: adjusted diluted EPS)", 'sub',
            note='GROUP TOTAL (CONSOLIDATED) — modelling logic'))
    seg_rev = '=SUM({urfs_rev},{fas_rev},{oth_rev})'
    add(Row('grp_rev', 'Revenues (segment build)', 'total', 'n1',
            h=lambda p: ('=SUM({urfs_rev},{fas_rev},{oth_rev})' if p.fy >= 2015 else '=SUM({urfs_rev},{leg_other_rev})'),
            fq='=SUM({urfs_rev},{fas_rev},{oth_rev},{unf_rev})', f27='=SUM({urfs_rev},{fas_rev},{oth_rev},{unf_rev})',
            fa='=SUM({urfs_rev},{fas_rev},{oth_rev},{unf_rev},{ma_rev})', cagr=True,
            note='Σ UR&FS + FA&S + All Other (legacy: Rental + other services) + UniFirst + future M&A. Historical rows tie to consolidated revenues (check below).'))
    add(Row('grp_gm', 'Gross margin (segment build)', 'total', 'n1',
            h=lambda p: ('=SUM({urfs_gm},{fas_gm},{oth_gm})' if p.fy >= 2015 else '=SUM({urfs_gm},{leg_other_gm})') if H.get(p.name, {}).get('rev') is not None else None,
            fq='=SUM({urfs_gm},{fas_gm},{oth_gm},{unf_gm})', f27='=SUM({urfs_gm},{fas_gm},{oth_gm},{unf_gm})',
            fa='=SUM({urfs_gm},{fas_gm},{oth_gm},{unf_gm},{ma_gm})', cagr=True,
            note='FY2009 legacy gross margin includes the $27.5m inventory valuation charge recorded in cost of sales (segment GM as reported).'))
    add(Row('grp_gmp', '  Gross margin %', 'pct', 'p1', h=ratio('grp_gm', 'grp_rev'), fq=ratio('grp_gm', 'grp_rev'), f27=ratio('grp_gm', 'grp_rev'), fa=ratio('grp_gm', 'grp_rev')))
    add(Row('grp_g', '  Revenues y/y %', 'yoy', 'p1', h=yoy('grp_rev'), fq='=IFERROR({grp_rev}/{grp_rev@py}-1,"")', f27='=IFERROR({grp_rev}/{grp_rev@pa}-1,"")', fa='=IFERROR({grp_rev}/{grp_rev@pa}-1,"")'))
    add(Row('chk_rev', '  Check: segment build vs consolidated revenues (should be 0)', 'check', 'n1',
            h=lambda p: '=ROUND({grp_rev}-{is_rev},1)' if H.get(p.name, {}).get('rev') is not None else None,
            fq='=ROUND({grp_rev}-{is_rev},1)', f27='=ROUND({grp_rev}-{is_rev},1)', fa='=ROUND({grp_rev}-{is_rev},1)'))
    add(Row('chk_gm', '  Check: segment build vs consolidated gross margin (should be 0)', 'check', 'n1',
            h=lambda p: '=ROUND({grp_gm}-{is_gm},1)' if H.get(p.name, {}).get('rev') is not None else None,
            fq='=ROUND({grp_gm}-{is_gm},1)', f27='=ROUND({grp_gm}-{is_gm},1)', fa='=ROUND({grp_gm}-{is_gm},1)'))
    # organic growth bridge (company non-GAAP)
    add(Row('og_rep', '  Organic growth bridge: reported revenue growth y/y %', 'yoy', 'p1', h=yoy('is_rev'), level=1,
            note='ORGANIC GROWTH (company non-GAAP): reported growth adjusted for acquisitions, divestitures (incl. Shred-it FY2015), FX and workday differences.'))
    add(Row('og_adj', '  (−) Acquisitions, divestitures, FX & workday differences, net (derived)', 'yoy', 'p1',
            h=lambda p: '=IF(AND(ISNUMBER({og_rep}),ISNUMBER({og_org})),{og_rep}-{og_org},"")', level=1))
    add(Row('og_org', '  = Organic revenue growth % (company-published)', 'memo', 'p1', h=lambda p: C.ORG[p.name] / 100 if p.name in C.ORG else None, level=1))
    add(Row('wd_q1', '  Workday effect on Q1/27 y/y growth (66 vs 65 workdays; Q1/27 release)', 'pct', 'p1', h=lambda p: {'FY2027Q1': 66 / 65 - 1}.get(p.name), level=1,
            note='FY2027 has 261 workdays vs 260 in FY2026; the extra day fell in Q1/27 (release workday table), so Q2–Q4/27E carry no workday benefit.'))
    add(Row('leg_rev', '  Memo: revenues — legacy Cintas ex-UniFirst & future M&A', 'memo', 'n1',
            h=lambda p: ('=SUM({urfs_rev},{fas_rev},{oth_rev})' if p.fy >= 2015 else '=SUM({urfs_rev},{leg_other_rev})') if H.get(p.name, {}).get('rev') is not None else None,
            fq=seg_rev, f27=seg_rev, fa=seg_rev))
    add(Row('guid_rev', '  Memo: FY27 revenue guidance — legacy ex-UniFirst (scenario end-point)', 'memo', 'n1',
            f27='=' + X['outlook']('rev'), note='Company FY27 revenue guidance $12.15–12.27bn (raised in the Q1/27 release, 23-Sep-2026; excludes UniFirst and future acquisitions; constant FX). Bull = high, Base = mid, Bear = low end.'))
    pre_q = '=({urfs_rev@py}*(1+{urfs_g@$P:FY2027Q1}-{wd_q1@$P:FY2027Q1})+{fas_rev@py}*(1+{fas_g@$P:FY2027Q1}-{wd_q1@$P:FY2027Q1})+{oth_rev@py}*(1+{oth_g@$P:FY2027Q1}-{wd_q1@$P:FY2027Q1}))'
    add(Row('leg_rev_pre', '  Legacy revenues before revenue calibration (Q2–Q4/27E helper)', 'line', 'n1',
            fq=pre_q, f27='={leg_rev@P:FY2027Q1}+SUM({leg_rev_pre@q2},{leg_rev_pre@q3},{leg_rev_pre@q4})', level=1,
            note='Σ segments: prior-year quarter × (1 + Q1/27 y/y − workday effect). FY27E = Q1/27 actual + Σ Q2–Q4 helper.'))
    add(Row('rev_sens', '  Revenue sensitivity to +1.00 of growth (Q2–Q4/27E helper)', 'line', 'n1',
            fq='={leg_rev@py}', f27='=SUM({rev_sens@q2},{rev_sens@q3},{rev_sens@q4})', level=1))
    add(Row('cal_g', '  Outlook calibration: Δ y/y growth applied to legacy segments (Q2–Q4/27E)', 'pct', 'p1',
            fq='={cal_g@$P:FY2027}', f27='=IFERROR(({guid_rev}-{leg_rev_pre})/{rev_sens},0)',
            note='Solves the uniform growth shift (vs Q1/27 trend ex-workday) so that legacy FY27E revenues = the guidance end-point for the active scenario.'))
    add(Row('chk_guid_rev', '  Check: legacy FY27E revenues vs guidance end-point (should be 0)', 'check', 'n1', f27='=ROUND({leg_rev}-{guid_rev},1)'))
    add(Row('leg_oi_pre', '  Legacy adjusted operating income before margin calibration (Q2–Q4/27E helper)', 'line', 'n1',
            fq='={urfs_rev}*{urfs_gmp_pre}-{urfs_sga}+{fas_rev}*{fas_gmp_pre}-{fas_sga}+{oth_rev}*{oth_gmp_pre}-{oth_sga}',
            f27='=SUM({urfs_oi@P:FY2027Q1},{fas_oi@P:FY2027Q1},{oth_oi@P:FY2027Q1})+SUM({leg_oi_pre@q2},{leg_oi_pre@q3},{leg_oi_pre@q4})', level=1))
    add(Row('m_sens', '  Margin sensitivity: Σ legacy revenues Q2–Q4/27E (helper)', 'line', 'n1',
            fq='={leg_rev}', f27='=SUM({m_sens@q2},{m_sens@q3},{m_sens@q4})', level=1))
    add(Row('guid_eps', '  Memo: FY27 adjusted diluted EPS guidance — ex-UniFirst (scenario end-point, $)', 'memo', 'n2',
            f27='=' + X['outlook']('eps'), note='Company FY27 adjusted diluted EPS guidance $5.45–5.54 (Q1/27 release; excludes UniFirst transaction costs & impact, future buybacks; interest, net ≈ $103.0m; ETR 20.4%).'))
    add(Row('tgt_oi', '  Memo: FY27 adjusted operating income implied by the EPS guidance (legacy)', 'memo', 'n1',
            f27='={guid_eps}*{g_shares@abs}/(1-{g_etr@abs})+{g_int@abs}',
            note='EPS end-point × guidance diluted shares (Q1/27 404.3m; guidance excludes future buybacks) ÷ (1 − 20.4% ETR) + interest, net $103.0m.'))
    add(Row('cal_m', '  Outlook calibration: Δ gross margin applied to legacy segments (Q2–Q4/27E)', 'pct', 'p1',
            fq='={cal_m@$P:FY2027}', f27='=IFERROR(({tgt_oi}-{leg_oi_pre})/{m_sens},0)',
            note='Solves the uniform gross-margin shift (vs prior-year quarter + Q1 drift) so that legacy FY27E adjusted operating income = the guidance-implied level.'))
    add(Row('leg_adj_oi', '  Memo: model legacy adjusted operating income (ex-UniFirst & future M&A)', 'memo', 'n1',
            h=lambda p: '=SUM({urfs_oi},{fas_oi},{oth_oi})' if p.fy >= 2015 else None,
            fq='=SUM({urfs_oi},{fas_oi},{oth_oi})', f27='=SUM({urfs_oi},{fas_oi},{oth_oi})', fa='=SUM({urfs_oi},{fas_oi},{oth_oi})'))
    add(Row('chk_guid_oi', '  Check: legacy FY27E adjusted operating income vs guidance-implied (should be 0)', 'check', 'n1', f27='=ROUND({leg_adj_oi}-{tgt_oi},1)'))
    add(Row('leg_sgap', '  Memo: legacy S&A % of legacy revenues', 'memo', 'p1',
            h=lambda p: '=IFERROR(SUM({urfs_sga},{fas_sga},{oth_sga})/{leg_rev},"")' if p.fy >= 2015 else None,
            fq='=IFERROR(SUM({urfs_sga},{fas_sga},{oth_sga})/{leg_rev},"")', f27='=IFERROR(SUM({urfs_sga},{fas_sga},{oth_sga})/{leg_rev},"")',
            fa='=IFERROR(SUM({urfs_sga},{fas_sga},{oth_sga})/{leg_rev},"")'))
    add(Row('leg_sgap_tgt', '  Legacy S&A % of revenues — scenario lever SA_pct (FY28E+)', 'pct', 'p1', fa=lambda p: '=' + SC('SA_pct', p),
            note='Operating leverage on S&A (technology, route density, SAP/AI tools). Segment S&A ratios move by the same Δ.'))
    S.blank()
