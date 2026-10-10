"""Row specification for the Karman Model sheet (mirrors the TDY template layout)."""
from lib import Row

SRC_ER = 'Source: Karman earnings releases (Form 8-K Ex. 99.1) — end-market revenue tables; FY2022–23 from the IPO prospectus (424B4, 13-Feb-2025) MD&A. 2024 quarters on the recast basis shown as prior-year comparatives in the 2025 releases (FY2024 = $114.6m / $115.0m / $115.6m, unchanged vs the FY2024 release).'
SRC_XBRL = 'Source: SEC EDGAR XBRL company facts, CIK 0002040127 (Forms 10-K / 10-Q); Q4 = FY − 9M; 1H = Q1 + Q2.'
SRC_REC = 'Source: Reconciliation of GAAP to non-GAAP measures in each earnings release (8-K Ex. 99.1); FY2022–23 and 9M from the IPO prospectus (424B4) “Summary Consolidated Financial Data”.'

# scenario-table rows (columns AG:AK)
SCN = dict(rev=12, ebitda=13, tax=16, capex=17, sbc=18, tic=19, hsmd=22, sl=28, tmids=34, mds=40, margin=46, ma=52, bb=58, lev=63)


def build_rows(S):
    A = S.add
    # =====================================================================================================
    A(Row('sec_em', 'END-MARKET REVENUE BUILD — one reportable segment (revenue disaggregated by end market; no segment profit is disclosed)', 'SEC',
          note='END-MARKET BUILD — Karman reports a single operating / reportable segment (ASC 280; CODM = CEO). Revenue is disaggregated by end market in every release; profitability is managed and guided at the consolidated level (Adj. EBITDA), so margins are modelled at group level below.'))
    S.blank()
    ems = [
        ('hsmd', 'Hypersonics & Strategic Missile Defense (interceptors — THAAD, SM-3, GMD/NGI; hypersonic test & strategic deterrent programs)', 'em_hsmd', SCN['hsmd']),
        ('sl', 'Space & Launch (payload fairings / separation systems, interstage & propulsion components for legacy and new-space launch providers)', 'em_sl', SCN['sl']),
        ('tmids', 'Tactical Missiles & Integrated Defense Systems (tactical SRMs, PrSM / GMLRS content, UAS / counter-UAS launchers; “Missile & Integrated Defense Systems” in the S-1)', 'em_tmids', SCN['tmids']),
        ('mds', 'Maritime Defense Systems (Columbia / Virginia-class submarine content — Seemann Composites & Materials Sciences, acquired Q1-26; separately disclosed from Q1-26)', 'em_mds', SCN['mds']),
    ]
    for k, name, dk, scn in ems:
        A(Row('blk_' + k, name, 'BLK', note=name.split(' (')[0].upper() + ' — modelling logic'))
        A(Row('rev_' + k, '  Revenue', 'TOPV', hist=dk, h='sum', ae='sum', cagr='g', comment=SRC_ER,
              qe='=IFERROR($S[@]/$S[org_rev],0)*<c>[org_rev]',
              f='=<pa>[@]*(1+<c>[g_%s])' % k,
              note='Q3/26E–Q4/26E: end-market share of 1H/26 revenue × the outlook-implied 2H/26 quarterly revenue (group block). 2027E–2030E: prior year × (1 + scenario growth lever).'))
        A(Row('g_' + k, '  Revenue y/y %', 'PCT', histf='=IFERROR(<c>[rev_%s]/<y>[rev_%s]-1,"")' % (k, k),
              fc={'QE': '=IFERROR(<c>[rev_%s]/<y>[rev_%s]-1,"")' % (k, k), 'AE': '=IFERROR(<c>[rev_%s]/<y>[rev_%s]-1,"")' % (k, k),
                  'F': '={SC:%d}' % scn},
              cells={'C': None, 'E': None, 'F': None, 'G': None, 'H': None, 'I': None}, cagr='avg',
              note='2027E–2030E: scenario lever (%s_growth, Bull / Base / Bear table →). Q1-26 onward includes acquisitions (no end-market organic split disclosed).' % k.upper()))
        A(Row('mix_' + k, '  Mix — % of total revenue', 'RATIO', all='=IFERROR(<c>[rev_%s]/<c>[rev],"")' % k, cagr='avg'))
        if k == 'tmids':
            A(Row('memo_tm_s1', '  Memo: as originally reported in the IPO prospectus (9M/24 basis before the 2025 recast)', 'MEMO',
                  cells={'C': 74.351, 'D': 85.969}, note='The 2025 recast moved c.$7m of 9M/24 revenue from Space & Launch into Hypersonics; FY2022–23 were not restated.'))
        S.blank()

    # ---------------- M&A lever ----------------
    A(Row('blk_ma', 'Acquisitions after the FY26 outlook & future acquisitions (M&A lever — Walker Precision Engineering closed 28-Aug-26; scenario spend 2027E+)', 'BLK',
          note='M&A LEVER — Walker (closed 28-Aug-26, ~$95m / £70m cash, funded by a $100m term-loan add-on) is excluded from the FY26 outlook (“excluding the impact of any future acquisitions”). Acquired sales = spend ÷ EV/sales; mid-year convention 2027E+.'))
    A(Row('ma_spend', '  Acquisition spend (USDm; 2026E = Walker, scenario 2027E+)', 'INROW', cells={'V': 95}, f='={SC:%d}' % SCN['ma'],
          note='2026E: Walker ~$95m (8-K 28-Aug-26). 2027E+: scenario lever (M&A_spend). Since IPO Karman has closed ~2.5 deals p.a. at ~10x EBITDA (Investor Update 16-Sep-26).'))
    A(Row('ma_mult', '  Purchase multiple — EV / sales (x)', 'MULT', cells={'V': 2.6}, f=2.8,
          note='~10x EBITDA × ~27% acquired EBITDA margin ≈ 2.6–2.8x sales (Investor Update 16-Sep-26: average ~10x, ~27% margin).'))
    A(Row('ma_acqs', '  Annualised sales acquired in the year', 'VAL', fc={'AE': '=IFERROR(<c>[ma_spend]/<c>[ma_mult],0)', 'F': '=IFERROR(<c>[ma_spend]/<c>[ma_mult],0)'}))
    A(Row('ma_g', '  Growth of acquired businesses after acquisition %', 'DRV', f=0.12, note='Acquired businesses grew ~25% under Karman ownership (Investor Update); 12% assumed post-integration.'))
    A(Row('ma_rr', '  Run-rate sales of businesses acquired (year end)', 'VAL', fc={'AE': '=<c>[ma_acqs]', 'F': '=<pa>[@]*(1+<c>[ma_g])+<c>[ma_acqs]'}))
    A(Row('ma_rev', '  Net sales from post-outlook / future acquisitions', 'VAL', cells={'T': 3.0, 'U': 9.0}, ae='sum',
          f='=<pa>[ma_rr]*(1+<c>[ma_g])+0.5*<c>[ma_acqs]',
          note='Q3/26E: ~1 month of Walker (~$36m annual run-rate est. = $95m ÷ 2.6x); Q4/26E full quarter. 2027E+: opening run-rate × (1+g) + ½ of sales acquired in the year.'))
    A(Row('ma_margin', '  Adjusted EBITDA margin of acquired businesses %', 'DRV', cells={'V': 0.27}, f=0.27))
    A(Row('ma_ebitda', '  Adjusted EBITDA from post-outlook / future acquisitions', 'VAL', qe='=<c>[ma_rev]*$V[ma_margin]', ae='sum', f='=<c>[ma_rev]*<c>[ma_margin]'))
    A(Row('ma_intpct', '  Acquired intangibles % of spend', 'DRV', cells={'V': 0.45}, f=0.45, note='Karman acquisitions 2024–26: identified intangibles ≈ 30–55% of consideration (customer relationships, backlog, know-how).'))
    A(Row('ma_life', '  Amortization life (years)', 'MULT', cells={'V': 12}, f=12, fmt='0.0'))
    A(Row('ma_cum', '  Cumulative acquired intangibles (gross)', 'VAL', fc={'AE': '=<c>[ma_spend]*<c>[ma_intpct]', 'F': '=<pa>[@]+<c>[ma_spend]*<c>[ma_intpct]'}))
    A(Row('ma_amort', '  Amortization of post-outlook / future-acquisition intangibles', 'VAL',
          cells={'T': '=$V[ma_cum]/$V[ma_life]/12', 'U': '=$V[ma_cum]/$V[ma_life]/4'}, ae='sum',
          f='=(<pa>[ma_cum]+0.5*<c>[ma_spend]*<c>[ma_intpct])/<c>[ma_life]'))
    A(Row('ma_ebita', '  Adjusted EBITA from post-outlook / future acquisitions', 'VAL', qe='=<c>[ma_ebitda]-<c>[ma_amort]', ae='sum', f='=<c>[ma_ebitda]-<c>[ma_amort]'))
    A(Row('ma_first12', '  Incremental acquisition sales (first 12 months of ownership)', 'VAL', qe='=<c>[ma_rev]', ae='sum', f='=0.5*<c>[ma_acqs]+0.5*<pa>[ma_acqs]'))
    S.blank()

    # ---------------- Group total ----------------
    A(Row('blk_grp', "Group Total — Adjusted EBITDA (Karman's primary profit measure and guidance metric)", 'BLK',
          note='GROUP TOTAL — Q3/26E–Q4/26E are calibrated to the FY26 outlook (scenario end-point: High / Mid / Low) less 1H/26 actuals; 2H split by the prior-year Q3:Q4 revenue pattern. 2027E+: end-market revenue × Adj. EBITDA margin lever + M&A lever.'))
    A(Row('org_rev', '  Net sales — end-market build (outlook basis)', 'KEY', histf='=N(<c>[rev_hsmd])+N(<c>[rev_sl])+N(<c>[rev_tmids])+N(<c>[rev_mds])', h='sum',
          cells={'T': '=($V[guide_rev]-$S[@])*N[rev]/(N[rev]+O[rev])', 'U': '=($V[guide_rev]-$S[@])*O[rev]/(N[rev]+O[rev])'},
          ae='sum', f='=N(<c>[rev_hsmd])+N(<c>[rev_sl])+N(<c>[rev_tmids])+N(<c>[rev_mds])', cagr='g'))
    A(Row('rev_build', '  Net sales (end-market build + post-outlook / future acquisitions)', 'KEY', histf='=<c>[org_rev]', h='sum',
          qe='=<c>[org_rev]+<c>[ma_rev]', ae='sum', f='=<c>[org_rev]+<c>[ma_rev]', cagr='g'))
    A(Row('g_rev_build', '  Net sales y/y %', 'PCT', all='=IFERROR(<c>[rev_build]/<y>[rev_build]-1,"")', cells={'C': None, 'E': None, 'F': None, 'G': None, 'H': None, 'I': None}, cagr='avg'))
    A(Row('ebitda_org', '  Adjusted EBITDA — outlook basis', 'VAL', histf='=<c>[adjebitda]', h='sum',
          cells={'T': '=($V[guide_ebitda]-$S[@])*T[org_rev]/($V[guide_rev]-$S[org_rev])', 'U': '=($V[guide_ebitda]-$S[@])*U[org_rev]/($V[guide_rev]-$S[org_rev])'},
          ae='sum', f='=<c>[org_rev]*<c>[m_org]', cagr='g',
          note='Historical = company-published Adj. EBITDA. 2H/26E = FY26 Adj. EBITDA outlook − 1H/26 actual, split pro rata to quarterly revenue.'))
    A(Row('m_org', '  Adjusted EBITDA margin — outlook basis %', 'RATIO', all='=IFERROR(<c>[ebitda_org]/<c>[org_rev],"")', f='={SC:%d}' % SCN['margin'], cagr='avg',
          note='2027E–2030E: scenario lever (ADJ_EBITDA_margin). FY25 30.8%; 1H/26 29.8%; FY26 outlook mid-point 29.7% (incl. Seemann / MSC dilution).'))
    A(Row('ebitda_acq', '  Adjusted EBITDA — post-outlook / future acquisitions', 'VAL', qe='=<c>[ma_ebitda]', ae='sum', f='=<c>[ma_ebitda]'))
    A(Row('adjebitda_grp', '  Adjusted EBITDA (group build)', 'KEY', histf='=<c>[adjebitda]', h='sum', qe='=<c>[ebitda_org]+<c>[ebitda_acq]', ae='sum',
          f='=<c>[ebitda_org]+<c>[ebitda_acq]', cagr='g'))
    A(Row('m_grp', '  Adjusted EBITDA margin %', 'RATIO', all='=IFERROR(<c>[adjebitda_grp]/<c>[rev_build],"")', cagr='avg'))
    A(Row('g_grp', '  Adjusted EBITDA y/y %', 'PCT', all='=IFERROR(<c>[adjebitda_grp]/<y>[adjebitda_grp]-1,"")', cells={'C': None, 'E': None, 'F': None, 'G': None, 'H': None, 'I': None}, cagr='avg'))
    A(Row('inc_m', '  Incremental Adj. EBITDA margin (ΔAdj. EBITDA / ΔSales)', 'RATIO', all='=IFERROR((<c>[adjebitda_grp]-<y>[adjebitda_grp])/(<c>[rev_build]-<y>[rev_build]),"")',
          cells={'C': None, 'E': None, 'F': None, 'G': None, 'H': None, 'I': None}, cagr='avg'))
    A(Row('sbc', '  (−) Share-based compensation (excluded from Adj. EBITDA)', 'VAL', hist='adj_sbc', h='sum', cells={'T': '=$AI$%d' % SCN['sbc'], 'U': '=$AI$%d' % SCN['sbc']},
          ae='sum', f='=<c>[rev_build]*<c>[sbc_pct]', comment=SRC_REC,
          note='Pre-IPO P / Phantom Units (fully vested at IPO — $8.1m in Q1-25); RSU / PSU expense from Q2-26. 2H/26E per quarter from the point-estimate table; 2027E+ % of sales.'))
    A(Row('trans', '  (−) Transaction-related expenses', 'VAL', hist='adj_trans', h='sum', cells={'T': '=$AI$%d/4' % SCN['tic'], 'U': '=$AI$%d/4' % SCN['tic']}, ae='sum',
          f='=<c>[ma_spend]*<c>[trans_pct]', comment=SRC_REC + ' Called “Acquisition related expenses” before Q1-25.'))
    A(Row('integ', '  (−) Integration expenses and non-recurring restructuring costs', 'VAL', hist='adj_integ', h='sum', cells={'T': '=$AI$%d/4' % SCN['tic'], 'U': '=$AI$%d/4' % SCN['tic']}, ae='sum',
          f=2.0, comment=SRC_REC))
    A(Row('lender', '  (−) Lender and administrative agent fees', 'VAL', hist='adj_lender', h='sum', cells={'T': 0.5, 'U': 0}, ae='sum', f=0, comment=SRC_REC,
          note='Q3/26E: Fifth / Sixth credit-agreement amendments (repricing 3-Aug-26; $100m incremental 26-Aug-26).'))
    A(Row('othnr', '  (−) Other non-recurring costs (included in Adj. EBITDA bridge)', 'VAL', hist='adj_other', h='sum', qe=0, ae='sum', f=0, comment=SRC_REC + ' 2023: non-cash impairment; 2025–26: estimated legal settlements & related professional fees.'))
    A(Row('ebitda_grp', '  EBITDA (company definition: NI + tax + D&A + interest)', 'TOT', histf='=<c>[ebitda]', h='sum',
          qe='=<c>[adjebitda_grp]-<c>[sbc]-<c>[trans]-<c>[integ]-<c>[lender]-<c>[othnr]', ae='sum',
          f='=<c>[adjebitda_grp]-<c>[sbc]-<c>[trans]-<c>[integ]-<c>[lender]-<c>[othnr]', cagr='g'))
    A(Row('dep', '  (−) Depreciation of PP&E (total D&A − ROU − acquired-intangible amortization)', 'VAL', histf='=<c>[da]-<c>[rou]-<c>[amort]', h='sum',
          cells={'T': '=R[@]*1.04', 'U': '=T[@]*1.04'}, ae='sum', f='=<c>[rev_build]*<c>[dep_pct]',
          note='Q3/Q4-26E: Q2/26 run-rate +4% q/q (capacity additions — capex ~$35–38m in 2026 per the Investor Update); 2027E+ % of sales.'))
    A(Row('rou', '  (−) Amortization of finance-lease right-of-use assets', 'VAL', hist='rou', h='sum', qe='=$R[@]', ae='sum', f='=<pa>[@]*(1+<c>[rou_g])',
          comment=SRC_XBRL + ' (FinanceLeaseRightOfUseAssetAmortization). Most facilities are finance leases; ROU amortization sits in the D&A line, lease interest in interest expense.'))
    A(Row('amort', '  (−) Amortization of acquired intangible assets', 'VAL', hist='amort', h='sum',
          qe='=($V[amort_ex]-$S[@])/2+<c>[ma_amort]', ae='sum', f='=<c>[amort_ex]+<c>[ma_amort]',
          comment='Source: intangible-asset notes in each 10-Q / 10-K (“Amortization expense was $x million for the three months ended …”); Q4 = FY − 9M. FY2022–23 per the IPO prospectus.',
          note='Existing intangibles: FY2025 10-K schedule ($29.3m 2026E) + Seemann / MSC (Q2-26 run-rate $9.2m / qtr) — see schedule row; plus post-outlook / future acquisitions.'))
    A(Row('da_grp', '  Total depreciation & amortization', 'VAL', all='=<c>[dep]+<c>[rou]+<c>[amort]', cagr='g'))
    A(Row('oth_grp', '  (−) Other income (expense) — inside company EBITDA', 'VAL', histf='=<c>[oth]', h='sum', qe='=<c>[oth]', ae='sum', f='=<c>[oth]'))
    A(Row('oi_grp', '  Operating income (GAAP; EBITDA − D&A − other income)', 'KEY', all='=<c>[ebitda_grp]-<c>[da_grp]-<c>[oth_grp]', cagr='g'))
    A(Row('ebita_grp', '  Adjusted EBITA (model: Adj. EBITDA − depreciation − ROU amortization − other income)', 'TOT', all='=<c>[adjebitda_grp]-<c>[dep]-<c>[rou]-<c>[oth_grp]', cagr='g',
          note='Model measure analogous to TDY non-GAAP operating income: operating income before acquired-intangible amortization and the company’s Adj. EBITDA add-backs (incl. SBC).'))
    A(Row('m_ebita', '  Adjusted EBITA margin %', 'RATIO', all='=IFERROR(<c>[ebita_grp]/<c>[rev_build],"")', cagr='avg'))
    A(Row('acq_inc', '  Incremental sales from acquisitions (disclosed / derived)', 'VAL', hist='acq_rev', cells={'T': 38.0, 'U': 30.0}, fc={'V': '=SUM(Q[@],R[@],T[@],U[@])'},
          f='=<c>[ma_first12]',
          comment='FY2024: RMS revenue since acquisition (16-Feb-24) $11.7m (FY2024 10-K). Q2/26: derived from the release — total growth 58.2% vs organic growth 24.4% on Q2/25 revenue of $115.1m ⇒ $38.9m. Other periods: not disclosed (“impact … not significant” per 10-Q acquisition notes).',
          note='Q3/26E: Five Axis, Seemann / MSC (not in the Q3/25 base) ≈ Q2/26 level; Q4/26E lower as Five Axis (closed 28-Oct-25) laps. Excludes Walker (in M&A lever). 2027E+: M&A lever first-12-month sales.'))
    A(Row('backlog', '  Backlog (period end; “funded backlog” to Q3-25 — same definition)', 'MEMO', hist='backlog', h='stock',
          comment='Source: earnings releases / 10-Q KPI tables (Q1/26 $1,026.9m; Q2/26 $1,322.1m); FY2022–23 and 30-Sep-24 per the IPO prospectus. Backlog = firm contractual commitments (POs, task orders, binding ATPs); excludes options, IDIQ ceilings.'))
    A(Row('btb', '  Implied book-to-bill ((revenue + Δ backlog) / revenue; incl. acquired backlog)', 'RATIO',
          cells={c: '=IFERROR((%s[rev]+%s[backlog]-%s[backlog])/%s[rev],"")' % (c, c, p, c) for c, p in
                 {'D': 'C', 'J': 'D', 'K': 'I', 'L': 'K', 'N': 'L', 'O': 'N', 'P': 'J', 'Q': 'O', 'R': 'Q', 'S': 'O', 'M': 'I'}.items()},
          fmt='0.00\\x', note='Q2/26 includes ~$345m of acquired backlog (Seemann / MSC); Investor Update: ~1.6x organic book-to-bill over the last 18 months.'))
    A(Row('memo_guide', '  Memo: FY26 outlook (scenario end-point; Q2-26 release 6-Aug-26 — revenue / Adj. EBITDA)', 'MEMO'))
    A(Row('guide_rev', '    FY26 revenue outlook ($m)', 'MEMO', cells={'V': '={SC0:%d}' % SCN['rev']}))
    A(Row('guide_ebitda', '    FY26 Adjusted EBITDA outlook ($m)', 'MEMO', cells={'V': '={SC0:%d}' % SCN['ebitda']}))
    A(Row('chk_em', '  Check: end-market build vs consolidated revenue (should be 0)', 'CHK', all='=ROUND(<c>[org_rev]+N(<c>[ma_rev])-<c>[rev],1)'))
    A(Row('chk_grp', '  Check: group Adj. EBITDA vs company-definition bridge (should be 0)', 'CHK', all='=ROUND(<c>[adjebitda_grp]-<c>[adjebitda],1)'))
    A(Row('chk_oi', '  Check: group operating income vs income statement (should be 0)', 'CHK', all='=ROUND(<c>[oi_grp]-<c>[oi],1)'))
    S.blank()

    # ---------------- Cost drivers ----------------
    A(Row('blk_cost', 'Cost drivers (% of sales)', 'BLK', note='% OF SALES drivers — inputs that drive the forecast cost lines (blue = input).'))
    A(Row('cogs_pct', '  Cost of goods sold % of revenue', 'DRV', all='=IFERROR(<c>[cogs]/<c>[rev],"")', qe='=$S[@]', f=0.575, cagr='avg',
          note='COGS includes allocated depreciation (~$3m / qtr). Q3/Q4-26E at the 1H/26 ratio; 2027E+ input (FY25 59.7%, 1H/26 57.4%).'))
    A(Row('dacogs_pct', '  D&A allocated to cost of goods sold % of revenue', 'DRV', all='=IFERROR(<c>[da_cogs]/<c>[rev],"")', qe='=$S[@]', f=0.016, cagr='avg'))
    A(Row('dep_pct', '  Depreciation of PP&E % of revenue', 'DRV', all='=IFERROR(<c>[dep]/<c>[rev],"")', fc={'W': 0.024, 'X': 0.026, 'Y': 0.027, 'Z': 0.028}, cagr='avg',
          note='Rising with the 2026 capacity build (capex 5%+ of sales vs depreciation ~2%).'))
    A(Row('rou_g', '  Finance-lease ROU amortization growth %', 'DRV', f=0.05))
    A(Row('sbc_pct', '  Share-based compensation % of revenue', 'DRV', all='=IFERROR(<c>[sbc]/<c>[rev],"")', f=0.008, cagr='avg', note='Q2/26 RSU / PSU run-rate 0.8% of sales.'))
    A(Row('trans_pct', '  Transaction-related expenses % of acquisition spend', 'DRV', f=0.03))
    A(Row('ga_pct', '  G&A % of revenue (incl. adjusting items & SBC)', 'RATIO', all='=IFERROR(<c>[ga]/<c>[rev],"")', cagr='avg'))
    S.blank()

    # =====================================================================================================
    A(Row('sec_is', 'CONSOLIDATED INCOME STATEMENT (US GAAP)', 'SEC', note='CONSOLIDATED IS — forecast logic'))
    A(Row('rev', 'Revenue', 'KEY', hist='rev', h='sum', fc={'QE': '=<c>[rev_build]', 'AE': '=SUM(<q1>[@],<q2>[@],<q3>[@],<q4>[@])', 'F': '=<c>[rev_build]'}, cagr='g',
          comment=SRC_XBRL + ' Q1/25 = $100.124m per the income statement (the Q1-25 end-market table printed $100.128m).', note='Forecast linked to the end-market build.'))
    A(Row('cogs', 'Cost of goods sold (incl. allocated D&A)', 'VAL', hist='cogs', h='sum', qe='=<c>[rev]*<c>[cogs_pct]', ae='sum', f='=<c>[rev]*<c>[cogs_pct]', cagr='g', comment=SRC_XBRL))
    A(Row('gp', 'Gross profit', 'GP', all='=<c>[rev]-<c>[cogs]', cagr='g'))
    A(Row('ga', 'General and administrative expenses (incl. transaction, integration, SBC)', 'VAL', hist='ga', h='sum', qe='=<c>[gp]-<c>[da_opex]-<c>[oi_grp]', ae='sum',
          f='=<c>[gp]-<c>[da_opex]-<c>[oi_grp]', cagr='g', comment=SRC_XBRL, note='Forecast G&A is the balancing line so that operating income equals the group build (Adj. EBITDA − add-backs − D&A − other income).'))
    A(Row('da_opex', 'Depreciation and amortization expense (opex line; excl. D&A in COGS)', 'VAL', hist='da_opex', h='sum', qe='=<c>[da_grp]-<c>[rev]*<c>[dacogs_pct]', ae='sum',
          f='=<c>[da_grp]-<c>[rev]*<c>[dacogs_pct]', cagr='g', comment=SRC_XBRL + ' (OperatingExpenses − GeneralAndAdministrativeExpense). Includes acquired-intangible and ROU amortization.'))
    A(Row('oi', 'Net operating income', 'KEY', all='=<c>[gp]-<c>[ga]-<c>[da_opex]', cagr='g'))
    A(Row('int', 'Interest expense, net (incl. finance-lease interest & debt-cost amortization)', 'VAL', hist='int', h='sum',
          cells={'T': '=(R[tl_prin]*2/3+(R[tl_prin]+100)*1/3)*T[r_tl]/4+R[fll]*$V[r_fl]/4+$V[dic_am]/4',
                 'U': '=V[tl_prin]*U[r_tl]/4+R[fll]*$V[r_fl]/4+$V[dic_am]/4'},
          ae='sum', f='=<c>[r_tl]*(<pa>[tl_prin]+0.5*(<c>[tl_inc]+<c>[tl_sched]))+<c>[r_fl]*<pa>[fll]+<c>[r_rev]*<pa>[revolver]+<c>[dic_am]-<c>[r_cash]*<pa>[bs_cash]',
          comment=SRC_XBRL, cagr='g',
          note='Q3/26E: term loan $764m (30-Jun) + $100m add-on from 26-Aug; SOFR + 2.75% to 3-Aug, SOFR + 2.25% after (Fifth Amendment). 2027E+: rate × average principal + finance-lease rate × opening lease liability + revolver − interest income on opening cash.'))
    A(Row('oth', 'Other income (expense), net', 'VAL', hist='oth', h='sum', qe=0, ae='sum', f=0, comment=SRC_XBRL))
    A(Row('pbt', 'Income before provision for income taxes', 'KEY', all='=<c>[oi]-<c>[int]+<c>[oth]', cagr='g'))
    A(Row('tax', 'Provision for income taxes', 'VAL', hist='tax', h='sum', qe='=<c>[pbt]*$AI$%d' % SCN['tax'], ae='sum', f='=<c>[pbt]*<c>[etr]', comment=SRC_XBRL,
          note='Q3/Q4-26E at the point-estimate rate (1H/26 ETR 21.8%; Q2-26 27.2% incl. §162(m)); 2027E+ input.'))
    A(Row('etr', '  Effective tax rate', 'DRV', all='=IFERROR(<c>[tax]/<c>[pbt],"")', f=0.245, cagr='avg'))
    A(Row('ni', 'Net income', 'KEY', all='=<c>[pbt]-<c>[tax]', cagr='g'))
    A(Row('chk_ni', '  Check: net income vs reported (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[ni_rep]),ROUND(<c>[ni]-<c>[ni_rep],1),"")', h=None))
    A(Row('ni_rep', '  Memo: net income as reported', 'MEMO', hist='ni', h='sum', comment=SRC_XBRL))
    A(Row('da', '  Memo: depreciation and amortization (total; Adj. EBITDA reconciliation)', 'VAL', hist='da', h='sum', qe='=<c>[da_grp]', ae='sum', f='=<c>[da_grp]', comment=SRC_REC))
    A(Row('da_cogs', '  Memo: D&A allocated to cost of goods sold', 'VAL', hist='da_cogs', h='sum', qe='=<c>[rev]*<c>[dacogs_pct]', ae='sum', f='=<c>[rev]*<c>[dacogs_pct]',
          comment='Source: footnote 1 to the Adj. EBITDA reconciliation in each release / 10-K MD&A (e.g. $3.1m in Q2-26).'))
    A(Row('lbl_eps', '(Earnings per share — per unit before the Feb-2025 IPO)', 'VAL'))
    A(Row('sh_b', '  Weighted-average basic shares / units (m)', 'SH', hist='sh_b', h='avg', qe='=$R[@]+0.03',
          fc={'U': '=T[@]+0.03', 'AE': '=AVERAGE(<q1>[@],<q2>[@],<q3>[@],<q4>[@])', 'F': '=AVERAGE(<pa>[sh_end],<c>[sh_end])'}, comment=SRC_XBRL + ' Q4: three-month column of the FY25 release.',
          note='Pre-IPO: LLC common units (159–167m). Corporate Conversion at the IPO (14-Feb-25) → 132.3m shares. 2027E+: average of opening / closing shares (buyback schedule).'))
    A(Row('sh_d', '  Weighted-average diluted shares / units (m)', 'SH', hist='sh_d', h='avg', qe='=<c>[sh_b]+($R[sh_d]-$R[sh_b])',
          fc={'AE': '=AVERAGE(<q1>[@],<q2>[@],<q3>[@],<q4>[@])', 'F': '=<c>[sh_b]+<c>[dil]'}, comment=SRC_XBRL))
    A(Row('eps_b', 'EPS – basic ($)', 'EPSK', all='=IFERROR(<c>[ni]/<c>[sh_b],"")', cagr='g'))
    A(Row('eps_d', 'EPS – diluted ($)', 'EPSK', all='=IFERROR(<c>[ni]/<c>[sh_d],"")', cagr='g', note='EPS computed as NI / weighted diluted shares (units pre-IPO).'))
    A(Row('eps_rep', '  Memo: EPS – diluted as reported ($)', 'EPSM', hist='eps', comment=SRC_XBRL))
    S.blank()

    # =====================================================================================================
    A(Row('sec_b1', 'RECONCILIATION: GAAP OPERATING INCOME → ADJUSTED EBITA (model) → ADJUSTED EBITDA (company)', 'SEC',
          note='ADJUSTED EBITA BRIDGE — Karman does not publish an adjusted operating income. The model measure adds back acquired-intangible amortization plus the company’s Adj. EBITDA adjusting items; adding depreciation, ROU amortization and other income must land on company-published Adj. EBITDA (check row).'))
    A(Row('b1_oi', 'Operating income (GAAP)', 'GP', all='=<c>[oi]', cagr='g'))
    A(Row('b1_amort', '  (+) Amortization of acquired intangible assets', 'VAL', all='=<c>[amort]'))
    A(Row('b1_trans', '  (+) Transaction-related expenses', 'VAL', all='=<c>[trans]'))
    A(Row('b1_integ', '  (+) Integration expenses and non-recurring restructuring costs', 'VAL', all='=<c>[integ]'))
    A(Row('b1_lender', '  (+) Lender and administrative agent fees', 'VAL', all='=<c>[lender]'))
    A(Row('b1_sbc', '  (+) Share-based compensation', 'VAL', all='=<c>[sbc]'))
    A(Row('b1_oth', '  (+) Other non-recurring costs (impairment, legal settlements)', 'VAL', all='=<c>[othnr]'))
    A(Row('b1_tot', '  Total adjusting items', 'GP', all='=SUM(<c>[b1_amort]:<c>[b1_oth])'))
    A(Row('ebita', '  = Adjusted EBITA (model bridge)', 'KEY', all='=<c>[b1_oi]+<c>[b1_tot]', cagr='g'))
    A(Row('m_ebita2', '  Adjusted EBITA margin %', 'RATIO', all='=IFERROR(<c>[ebita]/<c>[rev],"")', cagr='avg'))
    A(Row('b1_dep', '  (+) Depreciation of PP&E and finance-lease ROU amortization', 'VAL', all='=<c>[dep]+<c>[rou]'))
    A(Row('b1_othinc', '  (+) Other income (expense), net (inside company EBITDA)', 'VAL', all='=<c>[oth]'))
    A(Row('b1_adj', '  = Adjusted EBITDA (via EBITA bridge)', 'GP', all='=<c>[ebita]+<c>[b1_dep]+<c>[b1_othinc]', cagr='g'))
    A(Row('adjebitda_pub', '  Company-published Adjusted EBITDA', 'MEMO', hist='adjebitda_pub', h='sum', comment=SRC_REC))
    A(Row('chk_b1', '  Check: EBITA bridge vs company-published Adj. EBITDA (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[adjebitda_pub]),ROUND(<c>[b1_adj]-<c>[adjebitda_pub],1),"n/p")', h=None,
          cells={'G': '=IF(ISNUMBER(G[adjebitda_pub]),ROUND(G[b1_adj]-G[adjebitda_pub],1),"n/p")', 'M': '=IF(ISNUMBER(M[adjebitda_pub]),ROUND(M[b1_adj]-M[adjebitda_pub],1),"n/p")',
                 'S': '=IF(ISNUMBER(S[adjebitda_pub]),ROUND(S[b1_adj]-S[adjebitda_pub],1),"n/p")'}))
    A(Row('chk_b1b', '  Check: EBITA bridge vs group build Adj. EBITA (should be 0)', 'CHK', all='=ROUND(<c>[ebita]-<c>[ebita_grp],1)'))
    S.blank()

    A(Row('sec_b2', 'RECONCILIATION: GAAP NET INCOME → EBITDA → ADJUSTED EBITDA (company definition, as published)', 'SEC',
          note='ADJ. EBITDA BRIDGE — line items and order exactly as in Karman’s releases. EBITDA = NI + income-tax provision + D&A + interest expense, net (other income stays inside EBITDA).'))
    A(Row('b2_ni', 'Net income (GAAP)', 'GP', all='=<c>[ni]', cagr='g'))
    A(Row('b2_tax', '  (+) Income tax provision (benefit)', 'VAL', all='=<c>[tax]'))
    A(Row('b2_da', '  (+) Depreciation and amortization', 'VAL', all='=<c>[da]'))
    A(Row('b2_int', '  (+) Interest expense, net', 'VAL', all='=<c>[int]'))
    A(Row('ebitda', '  = EBITDA', 'KEY', all='=SUM(<c>[b2_ni]:<c>[b2_int])', cagr='g'))
    A(Row('ebitda_pub', '  Company-published EBITDA', 'MEMO', hist='ebitda_pub', h='sum', comment=SRC_REC))
    A(Row('chk_e', '  Check: model EBITDA vs company-published (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[ebitda_pub]),ROUND(<c>[ebitda]-<c>[ebitda_pub],1),"n/p")', h=None,
          cells={k: '=IF(ISNUMBER(%s[ebitda_pub]),ROUND(%s[ebitda]-%s[ebitda_pub],1),"n/p")' % (k, k, k) for k in 'GMS'}))
    A(Row('b2_trans', '  (+) Transaction-related expenses', 'VAL', all='=<c>[trans]'))
    A(Row('b2_integ', '  (+) Integration expenses and non-recurring restructuring costs', 'VAL', all='=<c>[integ]'))
    A(Row('b2_lender', '  (+) Lender and administrative agent fees', 'VAL', all='=<c>[lender]'))
    A(Row('b2_sbc', '  (+) Share-based compensation', 'VAL', all='=<c>[sbc]'))
    A(Row('b2_oth', '  (+) Other non-recurring costs', 'VAL', all='=<c>[othnr]'))
    A(Row('adjebitda', '  = Adjusted EBITDA (model bridge)', 'KEY', all='=<c>[ebitda]+SUM(<c>[b2_trans]:<c>[b2_oth])', cagr='g'))
    A(Row('m_adj', '  Adjusted EBITDA margin %', 'RATIO', all='=IFERROR(<c>[adjebitda]/<c>[rev],"")', cagr='avg'))
    A(Row('chk_b2', '  Check: model bridge vs company-published Adj. EBITDA (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[adjebitda_pub]),ROUND(<c>[adjebitda]-<c>[adjebitda_pub],1),"n/p")', h=None,
          cells={k: '=IF(ISNUMBER(%s[adjebitda_pub]),ROUND(%s[adjebitda]-%s[adjebitda_pub],1),"n/p")' % (k, k, k) for k in 'GMS'}))
    A(Row('def_b2', '  Definition basis: unchanged since the S-1 (Jan-2025) — EBITDA plus SBC, transaction / acquisition costs, integration & restructuring, lender fees on discrete amendments, impairments & other non-recurring items', 'DEF',
          note='Definition changes flagged here: “Acquisition related expenses” renamed “Transaction-related expenses” (Q1-25) and widened to IPO / secondary-offering professional fees; no other changes.'))
    A(Row('lbl_ebita', 'To Adjusted EBITA:', 'MEMO'))
    A(Row('b2_lessda', '  (−) Depreciation and amortization', 'VAL', all='=-<c>[da]'))
    A(Row('b2_addam', '  (+) Amortization of acquired intangible assets', 'VAL', all='=<c>[amort]'))
    A(Row('b2_lessoth', '  (−) Other income (expense), net', 'VAL', all='=-<c>[oth]'))
    A(Row('b2_ebita', '  = Adjusted EBITA (model; via Adj. EBITDA)', 'GP', all='=<c>[adjebitda]+<c>[b2_lessda]+<c>[b2_addam]+<c>[b2_lessoth]', cagr='g'))
    A(Row('chk_b2b', '  Check: Adj. EBITA via Adj. EBITDA − EBITA bridge (should be 0)', 'CHK', all='=ROUND(<c>[b2_ebita]-<c>[ebita],1)'))
    S.blank()

    A(Row('sec_b3', 'RECONCILIATION: GAAP NET INCOME → ADJUSTED NET INCOME → ADJUSTED EPS (company definition — adjustments are NOT tax-effected)', 'SEC',
          note='ADJ. EPS BRIDGE — Karman reconciles per share: GAAP EPS + transaction, integration, lender fees, SBC and “other non-recurring costs” (which in EPS also include items outside EBITDA: the $2.5m Q2-25 debt-cost write-off in interest expense and discrete tax items). No tax effect is deducted. Rebuilt here in $ and divided by diluted shares.'))
    A(Row('b3_ni', 'Net income (GAAP)', 'GP', all='=<c>[ni]', cagr='g'))
    A(Row('b3_trans', '  (+) Transaction-related expenses', 'VAL', all='=<c>[trans]'))
    A(Row('b3_integ', '  (+) Integration expenses and non-recurring restructuring costs', 'VAL', all='=<c>[integ]'))
    A(Row('b3_lender', '  (+) Lender and administrative agent fees', 'VAL', all='=<c>[lender]'))
    A(Row('b3_sbc', '  (+) Share-based compensation', 'VAL', all='=<c>[sbc]'))
    A(Row('b3_oth', '  (+) Other non-recurring costs (EBITDA items)', 'VAL', all='=<c>[othnr]'))
    A(Row('b3_debt', '  (+) Write-off of unamortized debt issuance costs (in interest expense)', 'VAL', hist='adj_debtwo', h='sum', qe=0, ae='sum', f=0,
          comment='FY2025 release fn. 7: $2.5m write-off of unamortized issuance costs on the TCW term loan refinanced by the Citi Term Loan B (Q2-25).'))
    A(Row('b3_taxd', '  (+) Discrete / non-recurring tax items (entity-status change, tax-refund write-off)', 'VAL', hist='adj_taxdisc', h='sum', qe=0, ae='sum', f=0,
          comment='FY2025 release fn. 7: one-time $1.5m tax expense due to the change in entity tax status (Q4-25 per the 9M vs FY per-share bridge). The tax-refund write-off is disclosed only per share (in the rounding line).'))
    A(Row('b3_plug', '  (+/−) Per-share rounding & items disclosed only per share (published Adj. EPS × diluted shares − Σ above)', 'VAL',
          histf='=IF(ISNUMBER(<c>[adjeps_pub]),<c>[adjeps_pub]*<c>[sh_d]-SUM(<c>[b3_ni]:<c>[b3_taxd]),0)', h='sum', qe=0, ae='sum', f=0,
          note='Company reconciles in per-share amounts rounded to $0.01 (±$0.005 × ~132m shares ≈ ±$0.7m per period). Forecast = 0.'))
    A(Row('adjni', '  = Adjusted net income (model bridge; company definition)', 'KEY', all='=SUM(<c>[b3_ni]:<c>[b3_plug])', cagr='g'))
    A(Row('b3_sh', '  Weighted-average diluted shares / units (m)', 'SH', all='=<c>[sh_d]'))
    A(Row('adjeps', 'Adjusted EPS – diluted ($) (model bridge)', 'EPSK', all='=IFERROR(<c>[adjni]/<c>[b3_sh],"")', cagr='g'))
    A(Row('adjeps_pub', '  Company-published Adjusted EPS ($)', 'EPSM', hist='adjeps_pub', cells={'G': 0.06, 'M': 0.16, 'S': 0.25}, comment=SRC_REC + ' FY2024 Adj. EPS ($0.13) first published in the FY2025 release; 2024 quarters per the 2025 releases (per unit).'))
    A(Row('chk_b3', '  Check: model bridge vs company-published Adj. EPS (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[adjeps_pub]),ROUND(<c>[adjeps]-<c>[adjeps_pub],2),"n/p")', h=None,
          cells={k: '=IF(ISNUMBER(%s[adjeps_pub]),ROUND(%s[adjeps]-%s[adjeps_pub],2),"n/p")' % (k, k, k) for k in 'GMS'}, fmt='0.00;\\(0.00\\);\\-'))
    A(Row('def_b3', '  Definition basis: Adjusted EPS first published Q1-25 (2024 comparatives per unit); adjustments pre-tax; no amortization add-back', 'DEF'))
    A(Row('lbl_b3m', 'Memo — model measure (tax-effected, excl. acquired-intangible amortization; comparable to peers’ “cash EPS”):', 'MEMO'))
    A(Row('t_adj', '  Tax rate applied to adjustments (model)', 'DRV', histf=0.25, fc={'QE': '=$AI$%d' % SCN['tax'], 'AE': '=$AI$%d' % SCN['tax'], 'F': '=<c>[etr]'},
          note='Blended federal + state rate assumed on add-backs (historical 25%); forecast = model ETR.'))
    A(Row('adjni_x', '  Adjusted net income ex-amortization, tax-effected (model)', 'GP',
          all='=<c>[ni]+(<c>[amort]+<c>[trans]+<c>[integ]+<c>[lender]+<c>[sbc]+<c>[othnr]+<c>[b3_debt])*(1-<c>[t_adj])+<c>[b3_taxd]', cagr='g'))
    A(Row('adjeps_x', '  Adjusted EPS ex-amortization, tax-effected — diluted ($) (model)', 'EPSB', all='=IFERROR(<c>[adjni_x]/<c>[sh_d],"")', cagr='g'))
    S.blank()

    # =====================================================================================================
    A(Row('sec_gm', 'GROWTH & MARGINS', 'SEC', note='GROWTH & MARGINS (consolidated) — forecast outputs'))
    yy = lambda k: '=IFERROR(<c>[%s]/<y>[%s]-1,"")' % (k, k)
    nyy = {'C': None, 'E': None, 'F': None, 'G': None, 'H': None, 'I': None}
    A(Row('gm_rev', '  Revenue y/y %', 'PCT', all=yy('rev'), cells=nyy, cagr='avg'))
    A(Row('gm_org', '  Revenue — organic y/y %', 'PCT', all='=IF(ISNUMBER(<c>[acq_inc]),IFERROR(<c>[gm_rev]-<c>[gm_acq],""),"")', cells=nyy, cagr='avg',
          note='Organic = total growth less disclosed / derived incremental acquisition sales (available FY24, Q2/26 and forecast). Company: organic growth 25%+ in 2025A and 2026E; 24.4% in Q2-26.'))
    A(Row('gm_acq', '  Revenue — acquisition y/y %', 'PCT', all='=IF(ISNUMBER(<c>[acq_inc]),IFERROR(<c>[acq_inc]/<y>[rev],""),"")', cells=nyy, cagr='avg'))
    A(Row('gm_ebitda', '  Adjusted EBITDA y/y %', 'PCT', all=yy('adjebitda'), cells=nyy, cagr='avg'))
    A(Row('gm_ebita', '  Adjusted EBITA y/y %', 'PCT', all=yy('ebita'), cells=nyy, cagr='avg'))
    A(Row('gm_oi', '  Operating income (GAAP) y/y %', 'PCT', all=yy('oi'), cells=nyy, cagr='avg'))
    A(Row('gm_ni', '  Net income y/y %', 'PCT', all=yy('ni'), cells=nyy, cagr='avg'))
    A(Row('gm_eps', '  Adjusted EPS (company definition) y/y %', 'PCT', all=yy('adjeps'), cells=dict(nyy, J=None, K=None, L=None, M=None, N=None, O=None, P=None), cagr='avg',
          note='Not meaningful before 2026 (per-unit pre-IPO vs post-IPO shares).'))
    A(Row('gm_gm', '  Gross margin %', 'RATIO', all='=IFERROR(<c>[gp]/<c>[rev],"")', cagr='avg'))
    A(Row('gm_adj', '  Adjusted EBITDA margin %', 'RATIO', all='=IFERROR(<c>[adjebitda]/<c>[rev],"")', cagr='avg'))
    A(Row('gm_ebitam', '  Adjusted EBITA margin (model) %', 'RATIO', all='=IFERROR(<c>[ebita]/<c>[rev],"")', cagr='avg'))
    A(Row('gm_inc', '  Incremental Adj. EBITDA margin (ΔAdj. EBITDA / ΔSales)', 'RATIO', all='=IFERROR((<c>[adjebitda]-<y>[adjebitda])/(<c>[rev]-<y>[rev]),"")', cells=nyy, cagr='avg'))
    A(Row('gm_oim', '  Operating margin (GAAP) %', 'RATIO', all='=IFERROR(<c>[oi]/<c>[rev],"")', cagr='avg'))
    A(Row('gm_nim', '  Net margin %', 'RATIO', all='=IFERROR(<c>[ni]/<c>[rev],"")', cagr='avg'))
    A(Row('gm_ga', '  G&A % of revenue', 'RATIO', all='=IFERROR(<c>[ga]/<c>[rev],"")', cagr='avg'))
    S.blank()

    # =====================================================================================================
    A(Row('sec_cf', 'CONSOLIDATED CASH FLOW STATEMENT', 'SEC',
          note='CONSOLIDATED CASH FLOW — historical quarters derived from YTD filings (Q2 = 6M − 3M, Q4 = FY − 9M). Forecast annual 2026E–2030E linked to the IS / BS roll-forward.'))
    A(Row('cf_ni', 'Net income', 'VAL', hist='cf_ni', h='sum', fc={'AE': '=<c>[ni]', 'F': '=<c>[ni]'}, comment=SRC_XBRL))
    A(Row('lbl_adj', 'Adjustments:', 'VAL'))
    A(Row('cf_da', '  Depreciation and amortization', 'VAL', hist='cf_da', h='sum', fc={'AE': '=<c>[da]', 'F': '=<c>[da]'}))
    A(Row('cf_sbc', '  Share-based / unit-based compensation', 'VAL', hist='cf_sbc', h='sum', fc={'AE': '=<c>[sbc]', 'F': '=<c>[sbc]'},
          comment='Per the Adj. EBITDA reconciliation (non-cash P-Unit / RSU expense).'))
    A(Row('cf_fin', '  Amortization (and write-off) of debt issuance costs', 'VAL', hist='cf_fin', h='sum', fc={'AE': '=<c>[dic_am]', 'F': '=<c>[dic_am]'}, comment=SRC_XBRL + ' (AmortizationOfFinancingCosts).'))
    A(Row('cf_dtax', '  Deferred income taxes', 'VAL', hist='cf_dtax', h='sum', fc={'AE': -3.0, 'F': '=-0.15*<c>[amort]'}, comment=SRC_XBRL,
          note='Deferred tax benefit from book amortization of acquired intangibles (stock acquisitions; no tax step-up) ≈ 15% of amortization.'))
    A(Row('cf_wc', '  Changes in operating assets & liabilities (incl. other non-cash items)', 'VAL', hist='wc', h='sum',
          fc={'AE': '=-(<c>[bs_ar]-<pa>[bs_ar])-(<c>[bs_ca]-<pa>[bs_ca])-(<c>[bs_inv]-<pa>[bs_inv])+(<c>[bs_ap]-<pa>[bs_ap])+(<c>[bs_pay]-<pa>[bs_pay])+(<c>[bs_cl]-<pa>[bs_cl])',
              'F': '=-(<c>[bs_ar]-<pa>[bs_ar])-(<c>[bs_ca]-<pa>[bs_ca])-(<c>[bs_inv]-<pa>[bs_inv])+(<c>[bs_ap]-<pa>[bs_ap])+(<c>[bs_pay]-<pa>[bs_pay])+(<c>[bs_cl]-<pa>[bs_cl])'},
          note='Historical = CFO less the items above (residual). Forecast linked to the BS: −Δ(receivables, contract assets, inventory) + Δ(payables, accrued payroll, contract liabilities). Contract-asset build is the main driver.'))
    A(Row('cfo', 'Net cash provided by (used in) operating activities', 'GP', hist='cfo', h='sum', fc={'AE': '=SUM(<c>[cf_ni]:<c>[cf_wc])', 'F': '=SUM(<c>[cf_ni]:<c>[cf_wc])'}, comment=SRC_XBRL))
    A(Row('capex', 'Purchases of property, plant and equipment', 'VAL', hist='capex', h='sum', fc={'AE': '=-$AI$%d' % SCN['capex'], 'F': '=-<c>[rev]*<c>[capex_pct]'}, comment=SRC_XBRL,
          note='2026E: ~$35–38m capital investment plan (Investor Update 16-Sep-26; 1H/26 actual $21.9m). 2027E+: % of sales.'))
    A(Row('acq', 'Acquisitions, net of cash acquired', 'VAL', hist='acq', h='sum', fc={'AE': '=S[@]-<c>[ma_spend]', 'F': '=-<c>[ma_spend]'}, comment=SRC_XBRL + ' Q2/25 = 6M ($126.3m: MTI, ISP).',
          cells={'K': 0.0, 'L': -126.279},
          note='2026E = 1H/26 actual (Seemann / MSC $210.0m) + Walker; 2027E+ = M&A lever spend.'))
    A(Row('cfi_oth', 'Other investing activities, net', 'VAL', hist='cfi_oth', h='sum', fc={'AE': '=S[@]', 'F': 0}, cells={'K': -6.0, 'L': 0.0}))
    A(Row('cfi', 'Net cash used in investing activities', 'GP', hist='cfi', h='sum', fc={'AE': '=SUM(<c>[capex]:<c>[cfi_oth])', 'F': '=SUM(<c>[capex]:<c>[cfi_oth])'}, comment=SRC_XBRL))
    A(Row('borrow', 'Proceeds from term loans / revolver borrowings', 'VAL', hist='borrow', h='sum', cells={'K': 0.0, 'L': 405.0},
          fc={'AE': '=<c>[tl_inc]+MAX(0,<c>[revolver]-<pa>[revolver])', 'F': '=<c>[tl_inc]+MAX(0,<c>[revolver]-<pa>[revolver])'}, comment=SRC_XBRL + ' Q2/25: $375m Citi Term Loan B + $30m revolver draw (6M).'))
    A(Row('repay', 'Repayments of notes payable / revolver', 'VAL', hist='repay', h='sum', fc={'AE': '=<c>[tl_sched]+MIN(0,<c>[revolver]-<pa>[revolver])', 'F': '=<c>[tl_sched]+MIN(0,<c>[revolver]-<pa>[revolver])'}))
    A(Row('lease_prin', 'Finance-lease principal payments', 'VAL', hist='lease_prin', h='sum', fc={'AE': '=<c>[fl_prin]', 'F': '=<c>[fl_prin]'}))
    A(Row('dic', 'Payments of debt issuance costs', 'VAL', hist='dic', h='sum', fc={'AE': '=<c>[dic_paid]', 'F': '=<c>[dic_paid]'}))
    A(Row('ipo', 'Proceeds from IPO / equity issuance, net', 'VAL', hist='ipo', h='sum', fc={'AE': 0, 'F': 0}, comment='Feb-2025 IPO: net proceeds $153.8m (primary).'))
    A(Row('bb_cf', 'Share repurchases (model; none to date)', 'VAL', fc={'AE': 0, 'F': '=-<c>[bb_cash]'}))
    A(Row('cff_oth', 'Other financing activities, net (member distributions, contingent consideration, taxes on vested awards; pre-2024 note proceeds)', 'VAL', hist='cff_oth', h='sum',
          cells={'K': 1.474, 'L': -1.919 - 0.0}, fc={'AE': '=S[@]', 'F': 0}))
    A(Row('cff', 'Net cash provided by (used in) financing activities', 'GP', hist='cff', h='sum', fc={'AE': '=SUM(<c>[borrow]:<c>[cff_oth])', 'F': '=SUM(<c>[borrow]:<c>[cff_oth])'}, comment=SRC_XBRL))
    A(Row('dcash', 'Change in cash and cash equivalents (incl. restricted)', 'GP', hist='dcash', h='sum', fc={'AE': '=<c>[cfo]+<c>[cfi]+<c>[cff]', 'F': '=<c>[cfo]+<c>[cfi]+<c>[cff]'}))
    A(Row('cash_b', 'Cash — beginning', 'VAL', cells={'C': 17.046, 'D': '=C[cash_e]', 'E': '=D[cash_e]', 'F': '=E[cash_e]', 'G': '=D[cash_e]', 'H': '=F[cash_e]', 'I': '=H[cash_e]', 'J': '=D[cash_e]',
                                                         'K': '=J[cash_e]', 'L': '=K[cash_e]', 'M': '=J[cash_e]', 'N': '=L[cash_e]', 'O': '=N[cash_e]', 'P': '=J[cash_e]',
                                                         'Q': '=P[cash_e]', 'R': '=Q[cash_e]', 'S': '=P[cash_e]', 'V': '=P[cash_e]', 'W': '=V[cash_e]', 'X': '=W[cash_e]', 'Y': '=X[cash_e]', 'Z': '=Y[cash_e]'},
          comment='31-Dec-2021 cash $17.0m = 31-Dec-2022 cash $6.6m + FY2022 decrease $10.4m (IPO prospectus cash-flow statement).'))
    A(Row('cash_e', 'Cash — end', 'GP', cells={c: '=%s[cash_b]+%s[dcash]' % (c, c) for c in 'CDEFGHIJKLMNOPQRSVWXYZ'}))
    A(Row('chk_cf', '  Check: CFO + CFI + CFF = change in cash (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[cfo]),ROUND(<c>[cfo]+<c>[cfi]+<c>[cff]-<c>[dcash],1),"")', h=None,
          cells={k: '=ROUND(%s[cfo]+%s[cfi]+%s[cff]-%s[dcash],1)' % (k, k, k, k) for k in 'GMS'}))
    A(Row('chk_cf2', '  Check: cash-flow ending cash vs balance-sheet cash (should be 0)', 'CHK',
          cells={c: '=IF(ISNUMBER(%s[bs_cash]),ROUND(%s[cash_e]-%s[bs_cash],1),"")' % (c, c, c) for c in 'CDHIJKLMNOPQRSVWXYZ'}))
    A(Row('lbl_cfm', '(Memo)', 'VAL'))
    A(Row('fcf', 'Free cash flow (CFO − capex; model definition — Karman does not publish FCF)', 'KEY', all='=IF(ISNUMBER(<c>[cfo]),<c>[cfo]+<c>[capex],"")', cells={'T': None, 'U': None}, cagr='g'))
    A(Row('fcf_g', '  FCF y/y %', 'PCT', all='=IFERROR(<c>[fcf]/<y>[fcf]-1,"")', cells=dict(nyy, T=None, U=None)))
    A(Row('fcf_m', '  FCF % of revenue', 'RATIO', all='=IFERROR(<c>[fcf]/<c>[rev],"")', cells={'T': None, 'U': None}, cagr='avg'))
    A(Row('fcf_conv', '  FCF / Adjusted net income (company definition) conversion %', 'RATIO', all='=IFERROR(<c>[fcf]/<c>[adjni],"")', cells={'T': None, 'U': None}, cagr='avg'))
    A(Row('fcf_ps', '  FCF per diluted share ($)', 'EPSB', all='=IFERROR(<c>[fcf]/<c>[sh_d],"")', cells={'T': None, 'U': None}))
    A(Row('lbl_capex', 'Capex ratios', 'VAL'))
    A(Row('capex_pct', '  Capex % of revenue', 'DRV', all='=IFERROR(-<c>[capex]/<c>[rev],"")', cells={'T': None, 'U': None}, fc={'W': 0.045, 'X': 0.04, 'Y': 0.035, 'Z': 0.035}, cagr='avg',
          note='Elevated in 2025–26 (new Salt Lake City nozzle / launcher facility, Skagit energetics expansion); fading toward ~3.5% maintenance + growth.'))
    A(Row('capex_dep', '  Capex / depreciation of PP&E (x)', 'RATIO', all='=IFERROR(-<c>[capex]/<c>[dep],"")', cells={'T': None, 'U': None}, fmt='0.0\\x'))
    S.blank()

    # ---------------- Buybacks ----------------
    A(Row('sec_bb', 'SHARE BUYBACK SCHEDULE (no programme authorised to date — leverage-floor plug only)', 'SEC'))
    A(Row('bb_px', '  Avg buyback price ($)', 'EPSV', fc={'AE': '=<c>[px]', 'F': '=<pa>[@]*(1+<c>[px_g])'}))
    A(Row('bb_cash', '  Buyback cash deployed (USDm)', 'VAL', fc={'AE': 0, 'F': '=<c>[bb_plug]+{SC:%d}' % SCN['bb']}))
    A(Row('bb_sh', '  Implied shares repurchased (m)', 'SH', fc={'AE': '=IFERROR(<c>[bb_cash]/<c>[bb_px],0)', 'F': '=IFERROR(<c>[bb_cash]/<c>[bb_px],0)'}))
    A(Row('sh_iss', '  Shares issued under equity plans (m)', 'SH', fc={'AE': 0.25, 'F': 0.4}))
    A(Row('sh_beg', '  Beginning shares outstanding (m)', 'SH', fc={'AE': '=P[bs_sh]', 'F': '=<pa>[sh_end]'}))
    A(Row('sh_end', '  Ending shares outstanding (m)', 'SH', fc={'AE': '=<c>[sh_beg]-<c>[bb_sh]+<c>[sh_iss]', 'F': '=<c>[sh_beg]-<c>[bb_sh]+<c>[sh_iss]'}))
    A(Row('bb_pct', '  % of shares repurchased', 'RATIO', fc={'AE': '=IFERROR(<c>[bb_sh]/<c>[sh_beg],"")', 'F': '=IFERROR(<c>[bb_sh]/<c>[sh_beg],"")'}))
    S.blank()

    # =====================================================================================================
    A(Row('sec_bs', 'CONSOLIDATED BALANCE SHEET', 'SEC',
          note='BS — historical at each reported quarter-end (1H column = 30-Jun; Q4 = 31-Dec). 30-Sep-24 and 31-Dec-22 from the IPO prospectus; 31-Mar / 30-Jun-24 not published (pre-IPO). Forecast = first-principles roll-forward from 31-Dec-25 (2026E) onward.'))
    A(Row('lbl_assets', 'ASSETS', 'VAL'))
    bs = lambda key, label, dk, style='VAL', fcf=None, cm=None, note=None: A(Row(key, label, style, hist=dk, h='stock', fc=fcf or {}, comment=cm, note=note))
    bs('bs_cash', '  Cash and cash equivalents (incl. restricted)', 'bs_cash', fcf={'AE': '=<c>[cash_e]', 'F': '=<c>[cash_e]'}, cm=SRC_XBRL + ' Balance sheets: 10-K / 10-Q; 31-Dec-22 and 30-Sep-24 from the IPO prospectus.')
    bs('bs_ar', '  Accounts receivable, net', 'bs_ar', fcf={'AE': '=<c>[rev]*<c>[dso]/365', 'F': '=<c>[rev]*<c>[dso]/365'})
    bs('bs_ca', '  Contract assets (unbilled)', 'bs_ca', fcf={'AE': '=<c>[rev]*<c>[ca_pct]', 'F': '=<c>[rev]*<c>[ca_pct]'})
    bs('bs_inv', '  Inventory', 'bs_inv', fcf={'AE': '=<c>[cogs]*<c>[inv_d]/365', 'F': '=<c>[cogs]*<c>[inv_d]/365'}, note='31-Dec-22 / 30-Sep-24: inventory included within prepaid & other in the prospectus presentation.')
    bs('bs_pre', '  Prepaid and other current assets', 'bs_pre2', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    A(Row('bs_tca', 'Total current assets', 'GP', all='=IF(ISNUMBER(<c>[bs_cash]),SUM(<c>[bs_cash]:<c>[bs_pre]),"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    bs('bs_ppe', '  Property, plant and equipment, net', 'bs_ppe', fcf={'AE': '=<pa>[@]-<c>[capex]-<c>[dep]-<c>[cfi_oth]', 'F': '=<pa>[@]-<c>[capex]-<c>[dep]-<c>[cfi_oth]'}, note='PP&E roll-forward: prior + capex − depreciation of PP&E.')
    bs('bs_gw', '  Goodwill', 'bs_gw', fcf={'AE': '=<pa>[@]-<c>[acq]*(1-<c>[int_pct26])', 'F': '=<pa>[@]+<c>[ma_spend]*(1-<c>[ma_intpct])'}, note='Goodwill + acquisition consideration not allocated to identified intangibles.')
    bs('bs_int', '  Intangible assets, net', 'bs_int', fcf={'AE': '=<pa>[@]-<c>[acq]*<c>[int_pct26]-<c>[amort]', 'F': '=<pa>[@]+<c>[ma_spend]*<c>[ma_intpct]-<c>[amort]'}, note='Intangibles roll-forward: prior + acquired intangibles − amortization.')
    bs('bs_orou', '  Operating lease right-of-use assets', 'bs_orou', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    bs('bs_frou', '  Finance lease right-of-use assets', 'bs_frou', fcf={'AE': '=<pa>[@]-<c>[rou]+<c>[fl_new]', 'F': '=<pa>[@]-<c>[rou]+<c>[fl_new]'})
    bs('bs_oa', '  Other assets (incl. deferred offering costs, marketable securities)', 'bs_oa', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    A(Row('bs_ta', 'TOTAL ASSETS', 'KEY', all='=IF(ISNUMBER(<c>[bs_cash]),<c>[bs_tca]+SUM(<c>[bs_ppe]:<c>[bs_oa]),"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    S.blank()
    A(Row('lbl_le', "LIABILITIES AND STOCKHOLDERS' EQUITY", 'VAL'))
    bs('bs_ap', '  Accounts payable', 'bs_ap', fcf={'AE': '=<c>[cogs]*<c>[ap_d]/365', 'F': '=<c>[cogs]*<c>[ap_d]/365'})
    bs('bs_pay', '  Accrued payroll and related expenses', 'bs_pay', fcf={'AE': '=<c>[rev]*<c>[pay_pct]', 'F': '=<c>[rev]*<c>[pay_pct]'})
    bs('bs_cl', '  Contract liabilities', 'bs_cl', fcf={'AE': '=<c>[rev]*<c>[cl_pct]', 'F': '=<c>[rev]*<c>[cl_pct]'})
    bs('bs_ollc', '  Current portion of operating lease liabilities', 'bs_oll_c', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    bs('bs_fllc', '  Current portion of finance lease liabilities', 'bs_fll_c', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    bs('bs_debtc', '  Current portion of term note / notes payable', 'bs_debt_c', fcf={'AE': '=-<c>[tl_sched]', 'F': '=-<c>[tl_sched]'})
    bs('bs_taxp', '  Income taxes payable', 'bs_taxp', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    bs('bs_ocl', '  Other current liabilities', 'bs_ocl', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    A(Row('bs_tcl', 'Total current liabilities', 'GP', all='=IF(ISNUMBER(<c>[bs_ap]),SUM(<c>[bs_ap]:<c>[bs_ocl]),"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    bs('bs_rev', '  Revolving line of credit', 'bs_rev', fcf={'AE': '=<c>[revolver]', 'F': '=<c>[revolver]'})
    bs('bs_debtlt', '  Term note, net of current portion and issuance costs', 'bs_debt_lt', fcf={'AE': '=<c>[debt_cv]-<c>[bs_debtc]', 'F': '=<c>[debt_cv]-<c>[bs_debtc]'})
    bs('bs_olllt', '  Operating lease liabilities, net of current', 'bs_oll_lt', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    bs('bs_flllt', '  Finance lease liabilities, net of current', 'bs_fll_lt', fcf={'AE': '=<c>[fll]-<c>[bs_fllc]', 'F': '=<c>[fll]-<c>[bs_fllc]'})
    bs('bs_oltl', '  Other liabilities', 'bs_oltl2', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    bs('bs_dtl', '  Deferred tax liabilities', 'bs_dtl', fcf={'AE': '=<pa>[@]+<c>[cf_dtax]', 'F': '=<pa>[@]+<c>[cf_dtax]'})
    A(Row('bs_tl', 'Total liabilities', 'KEY', all='=IF(ISNUMBER(<c>[bs_ap]),<c>[bs_tcl]+SUM(<c>[bs_rev]:<c>[bs_dtl]),"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    A(Row('lbl_eq', "Stockholders' / members' equity:", 'VAL'))
    bs('bs_pic', "  Common stock & APIC (members' equity before the IPO)", 'bs_pic', fcf={'AE': '=<pa>[@]+<c>[cf_sbc]+<c>[ipo]+S[cff_oth]', 'F': '=<pa>[@]+<c>[cf_sbc]+<c>[ipo]-<c>[bb_cash]'},
       note="Pre-IPO members' equity shown entirely here (retained earnings = 0). 2026E: + SBC + taxes withheld on vested awards (1H actual).")
    bs('bs_re', '  Retained earnings', 'bs_re', fcf={'AE': '=<pa>[@]+<c>[ni]', 'F': '=<pa>[@]+<c>[ni]'})
    bs('bs_aoci', '  Accumulated other comprehensive income', 'bs_aoci', fcf={'AE': '=<pa>[@]', 'F': '=<pa>[@]'})
    A(Row('bs_eq', "Total stockholders' equity", 'GP', all='=IF(ISNUMBER(<c>[bs_pic]),SUM(<c>[bs_pic]:<c>[bs_aoci]),"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    A(Row('bs_tle', "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", 'KEY', all='=IF(ISNUMBER(<c>[bs_tl]),<c>[bs_tl]+<c>[bs_eq],"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    A(Row('chk_bs', 'BS tie-out check (TA − TL&E)', 'CHK', all='=IF(ISNUMBER(<c>[bs_ta]),ROUND(<c>[bs_ta]-<c>[bs_tle],1),"")', cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    A(Row('chk_ta', '  Check: model total assets vs reported (should be 0)', 'CHK', histf='=IF(ISNUMBER(<c>[ta_rep]),ROUND(<c>[bs_ta]-<c>[ta_rep],1),"")', h=None,
          cells={k: '=IF(ISNUMBER(%s[ta_rep]),ROUND(%s[bs_ta]-%s[ta_rep],1),"")' % (k, k, k) for k in 'MS'}))
    A(Row('ta_rep', '  Memo: total assets as reported', 'MEMO', hist='bs_ta', h='stock'))
    A(Row('bs_sh', '  Memo: common shares outstanding at period end (m)', 'SH', hist='bs_shares', h='stock', fc={'AE': '=<c>[sh_end]', 'F': '=<c>[sh_end]'}, comment='Balance-sheet cover data (10-Q / 10-K).'))
    S.blank()

    # ---------------- Working capital ----------------
    A(Row('sec_wc', 'WORKING CAPITAL & CASH CONVERSION', 'SEC', note='WORKING CAPITAL — forecast drivers (blue = input). Historical ratios annualise quarters (×4) and half-years (×2).'))
    ann = '*IF(LEFT("<per>",1)="Q",4,IF(LEFT("<per>",2)="1H",2,1))'
    A(Row('dso', '  DSO — receivables / revenue × 365', 'DSO', histf='=IFERROR(<c>[bs_ar]/(<c>[rev]' + ann + ')*365,"")', fc={'AE': 58, 'F': 58}, cagr=None))
    A(Row('ca_pct', '  Contract assets % of revenue', 'DRV', histf='=IFERROR(<c>[bs_ca]/(<c>[rev]' + ann + '),"")', fc={'AE': 0.26, 'W': 0.25, 'X': 0.24, 'Y': 0.235, 'Z': 0.23},
          note='Contract assets 33% of FY25 sales, 25.7% of Q2-26 annualised sales; Karman targets faster conversion (Investor Update: 94 days vs peers 97).'))
    A(Row('inv_d', '  Inventory days — inventory / COGS × 365', 'DSO', histf='=IFERROR(<c>[bs_inv]/(<c>[cogs]' + ann + ')*365,"")', fc={'AE': 15, 'F': 15}))
    A(Row('ap_d', '  Payable days — payables / COGS × 365', 'DSO', histf='=IFERROR(<c>[bs_ap]/(<c>[cogs]' + ann + ')*365,"")', fc={'AE': 40, 'F': 40}))
    A(Row('pay_pct', '  Accrued payroll % of revenue', 'DRV', histf='=IFERROR(<c>[bs_pay]/(<c>[rev]' + ann + '),"")', fc={'AE': 0.021, 'F': 0.021}))
    A(Row('cl_pct', '  Contract liabilities % of revenue', 'DRV', histf='=IFERROR(<c>[bs_cl]/(<c>[rev]' + ann + '),"")', fc={'AE': 0.036, 'F': 0.036}))
    A(Row('nwc', '  Operating NWC (receivables + contract assets + inventory − payables − accrued payroll − contract liabilities)', 'VAL',
          all='=IF(ISNUMBER(<c>[bs_ar]),<c>[bs_ar]+<c>[bs_ca]+N(<c>[bs_inv])-<c>[bs_ap]-<c>[bs_pay]-<c>[bs_cl],"")', cells={'T': None, 'U': None}))
    A(Row('nwc_pct', '  NWC % of revenue (annualised)', 'RATIO', histf='=IFERROR(<c>[nwc]/(<c>[rev]' + ann + '),"")', fc={'AE': '=IFERROR(<c>[nwc]/<c>[rev],"")', 'F': '=IFERROR(<c>[nwc]/<c>[rev],"")'}))
    A(Row('dnwc', '  ΔNWC (y/y)', 'VAL', cells={c: '=IFERROR(%s[nwc]-%s[nwc],"")' % (c, p) for c, p in {'D': 'C', 'J': 'D', 'P': 'J', 'V': 'P', 'W': 'V', 'X': 'W', 'Y': 'X', 'Z': 'Y', 'S': 'M', 'M': 'G'}.items()}))
    S.blank()

    # ---------------- BS schedules ----------------
    A(Row('sec_sched', 'BALANCE SHEET FORECAST SCHEDULES', 'SEC', note='BS FORECAST SCHEDULES — explicit driver assumptions (blue = input).'))
    A(Row('blk_roll', 'Asset roll-forwards & non-cash items', 'BLK'))
    A(Row('amort_ex', '  Amortization of existing acquired intangibles (USDm)', 'SCHED', histf='=N(<c>[amort])', h=None, fc={'AE': 38.5, 'W': 33.0, 'X': 26.0, 'Y': 24.0, 'Z': 23.5},
          note='FY2025 10-K schedule: 2026 $29.3m, 2027 $23.9m, 2028–30 ~$22.6m (pre-Seemann / MSC). Seemann / MSC added ~$61m of intangibles (Q2-26 amortization $9.2m / qtr incl. short-lived backlog). 2026E = 1H actual $20.1m + 2 × $9.2m.'))
    A(Row('int_pct26', '  Acquired intangibles % of 2026 acquisition consideration', 'SCHED', fc={'AE': 0.34},
          note='Seemann / MSC: Δ intangibles + 1H amortization ≈ $61m on $210m (29%); Walker assumed 45% ⇒ blended ~34%.'))
    A(Row('dil', '  Dilutive securities (m shares — RSU / PSU)', 'SCHED', fc={'AE': 0.05, 'F': 0.4}, fmt='0.00'))
    A(Row('px_g', '  Share-price appreciation % (buyback pricing)', 'SCHED', f=0.10))
    A(Row('fl_new', '  New finance-lease ROU assets / liabilities (non-cash)', 'SCHED', fc={'AE': 25.0, 'F': '=<c>[rou]'}, note='2026E: 1H/26 additions (incl. Seemann facilities) ~$21m + 2H est.; 2027E+ = ROU amortization (flat asset base).'))
    A(Row('dic_am', '  Amortization of debt issuance costs (non-cash interest)', 'SCHED', fc={'AE': 2.0, 'F': 2.2}))
    A(Row('blk_debt', 'Debt schedule (Citi Term Loan B + revolver; finance leases)', 'BLK'))
    A(Row('tl_prin', '  Term-loan principal (period end)', 'SCHEDC', hist='tl_principal', h='stock', fc={'AE': '=P[@]+<c>[tl_inc]+<c>[tl_sched]', 'F': '=<pa>[@]+<c>[tl_inc]+<c>[tl_sched]'},
          comment='Debt note in each 10-Q / 10-K: Term note $502.8m (31-Dec-25); $772m after the $265m Third-Amendment add-on (2-Feb-26); $764.0m at 30-Jun-26; +$100m Sixth Amendment (26-Aug-26) ⇒ $863.96m original principal.'))
    A(Row('tl_inc', '  Incremental term loans (input)', 'SCHED', fc={'AE': 365.0, 'F': 0}, note='2026E: $265m (Feb-26, Seemann / MSC) + $100m (Aug-26, Walker).'))
    A(Row('tl_sched', '  Scheduled amortization (input, negative)', 'SCHED', fc={'AE': -8.2, 'F': -8.64}, note='1% p.a. of original principal (~$8.6m on $864m); 2026E = 1H actual $3.9m + 2H.'))
    A(Row('dic_paid', '  Debt issuance costs paid (input, negative)', 'SCHED', fc={'AE': -6.4, 'F': 0}, note='1H/26 $4.9m + est. $1.5m on the Aug-26 repricing / add-on.'))
    A(Row('debt_cv', '  Term note & other notes — carrying value (current + LT, net of issuance costs)', 'SCHEDC', all='=IF(ISNUMBER(<c>[bs_debtlt]),N(<c>[bs_debtc])+<c>[bs_debtlt],"")',
          fc={'AE': '=<pa>[@]+<c>[tl_inc]+<c>[tl_sched]+<c>[dic_paid]+<c>[dic_am]', 'F': '=<pa>[@]+<c>[tl_inc]+<c>[tl_sched]+<c>[dic_paid]+<c>[dic_am]'}, cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    A(Row('fll', '  Finance-lease liabilities (current + LT)', 'SCHEDC', all='=IF(ISNUMBER(<c>[bs_fllc]),<c>[bs_fllc]+<c>[bs_flllt],"")',
          fc={'AE': '=<pa>[@]+<c>[fl_prin]+<c>[fl_new]', 'F': '=<pa>[@]+<c>[fl_prin]+<c>[fl_new]'}, cells={'E': None, 'F': None, 'G': None, 'T': None, 'U': None}))
    A(Row('fl_prin', '  Finance-lease principal payments (negative)', 'SCHED', fc={'AE': -4.4, 'F': '=-<pa>[fll]*0.045'}))
    A(Row('cash_pre', '  Cash before revolver (opening cash + CFO + CFI + non-revolver financing)', 'SCHEDC',
          fc={'AE': '=<pa>[bs_cash]+<c>[cfo]+<c>[cfi]+<c>[tl_inc]+<c>[tl_sched]+<c>[lease_prin]+<c>[dic]+<c>[ipo]+<c>[bb_cf]+<c>[cff_oth]-<pa>[revolver]',
              'F': '=<pa>[bs_cash]+<c>[cfo]+<c>[cfi]+<c>[tl_inc]+<c>[tl_sched]+<c>[lease_prin]+<c>[dic]+<c>[ipo]+<c>[bb_cf]+<c>[cff_oth]-<pa>[revolver]'}))
    A(Row('min_cash', '  Minimum cash balance', 'SCHED', fc={'AE': 40, 'F': 50}))
    A(Row('revolver', '  Revolver / incremental borrowings outstanding (year end; $150m revolver + assumed add-ons)', 'SCHEDC', hist='bs_rev', h='stock', fc={'AE': '=MAX(0,<c>[min_cash]-<c>[cash_pre])', 'F': '=MAX(0,<c>[min_cash]-<c>[cash_pre])'},
          note='Draws when cash would fall below the minimum (funds M&A above FCF); repaid as cash builds. Balances above the $150m revolver commitment assume further term-loan add-ons (uncapped incremental capacity per the Fourth Amendment), priced at the revolver rate.'))
    A(Row('r_tl', '  Term-loan interest rate (SOFR + margin)', 'SCHED', cells={'T': 0.0613, 'U': 0.0596}, fc={'AE': '=U[@]', 'F': 0.058},
          note='6.46% at 30-Jun-26 (SOFR + 2.75%) ⇒ SOFR ≈ 3.71%; SOFR + 2.25% from 3-Aug-26 ⇒ ~5.96%. Q3 blended. 2027E+ 5.8% (modest SOFR decline).'))
    A(Row('r_fl', '  Finance-lease implicit rate', 'SCHED', fc={'AE': 0.082, 'F': 0.082}, note='Weighted-average discount rate for finance leases 8.21% (FY2025 10-K).'))
    A(Row('r_rev', '  Revolver interest rate', 'SCHED', f=0.06))
    A(Row('r_cash', '  Interest income yield on opening cash', 'SCHED', fc={'AE': 0.03, 'F': 0.03}))
    A(Row('blk_lev', 'Leverage-targeted buybacks (repurchases plug to a minimum net debt / Adj. EBITDA)', 'BLK'))
    A(Row('lev_min', '  Minimum net debt / adjusted EBITDA (x) (input)', 'LEV', f='={SC0:63}', note='Scenario-driven floor (single value per case); surplus cash below this leverage goes to buybacks.'))
    A(Row('nd_pre', '  Net debt before buybacks (year end)', 'SCHEDC',
          f='=<c>[debt_cv]+<c>[fll]+<pa>[revolver]-(<pa>[bs_cash]+<c>[cfo]+<c>[cfi]+<c>[tl_inc]+<c>[tl_sched]+<c>[lease_prin]+<c>[dic]+<c>[ipo]+<c>[cff_oth])',
          note='Approximation using CFO before any buyback-driven interest effect.'))
    A(Row('nd_tgt', '  Target minimum net debt  =  min. leverage × adjusted EBITDA', 'SCHEDC', f='=<c>[lev_min]*<c>[adjebitda]'))
    A(Row('bb_plug', '  Share repurchases: plug to minimum leverage', 'SCHEDC', f='=MAX(0,<c>[nd_tgt]-<c>[nd_pre])'))
    A(Row('lbl_hr', 'Historical reference (driver context)', 'BLK'))
    A(Row('hr_da', '  Total D&A % of revenue', 'RATIO', all='=IFERROR(<c>[da]/<c>[rev],"")', cagr='avg'))
    A(Row('hr_am', '  Acquired-intangible amortization % of revenue', 'RATIO', all='=IFERROR(<c>[amort]/<c>[rev],"")', cagr='avg'))
    A(Row('hr_int', '  Interest expense / average total debt (incl. finance leases)', 'RATIO',
          cells={c: '=IFERROR(%s[int]/AVERAGE(%s[debt_cv]+%s[fll]+N(%s[bs_rev]),%s[debt_cv]+%s[fll]+N(%s[bs_rev])),"")' % (c, c, c, c, p, p, p) for c, p in {'D': 'C', 'J': 'D', 'P': 'J', 'V': 'P', 'W': 'V', 'X': 'W', 'Y': 'X', 'Z': 'Y'}.items()}))
    S.blank()

    # =====================================================================================================
    A(Row('sec_ratio', 'RATIO ANALYSIS', 'SEC'))
    A(Row('blk_roic', 'DuPont decomposition of ROIC', 'BLK'))
    ann_cols = 'CDJPVWXYZ'
    rc = lambda t: {c: t.replace('<c>', c) for c in ann_cols}
    A(Row('ro_ebita', 'Adjusted EBITA (model)', 'VAL', cells=rc('=<c>[ebita]')))
    A(Row('ro_t', 'Tax rate (cash-tax proxy: 25% historical / model ETR forecast)', 'RATIO', cells=dict(rc('=<c>[t_adj]'))))
    A(Row('nopat', 'NOPAT  =  Adj. EBITA × (1 − tax rate)', 'VAL', cells=rc('=IFERROR(<c>[ro_ebita]*(1-<c>[ro_t]),"n/a")')))
    A(Row('ic', 'Invested capital (IC)  =  Equity + Net debt (incl. finance leases)', 'VAL', cells=rc('=IFERROR(<c>[ro_eq]+<c>[ro_nd],"n/a")')))
    A(Row('ro_eq', '  Total equity', 'VAL', cells=rc('=<c>[bs_eq]')))
    A(Row('ro_nd', '  Net debt  =  Term debt + revolver + finance leases − cash', 'VAL', cells=rc('=<c>[nd]')))
    A(Row('roic', 'ROIC  =  NOPAT / IC', 'KEYP', cells=rc('=IFERROR(<c>[nopat]/<c>[ic],"n/a")')))
    A(Row('ro_m', '  Margin  =  Adj. EBITA / Sales', 'RATIO', cells=rc('=IFERROR(<c>[ro_ebita]/<c>[rev],"n/a")')))
    A(Row('ro_tu', '  Capital turnover  =  Sales / IC', 'RATIO', cells=rc('=IFERROR(<c>[rev]/<c>[ic],"n/a")'), fmt='0.00\\x'))
    A(Row('ro_tb', '  Tax burden  =  (1 − tax rate)', 'RATIO', cells=rc('=IFERROR(1-<c>[ro_t],"n/a")')))
    A(Row('ro_chk', '  Check: Margin × Turnover × Tax burden  =  ROIC', 'RATIO', cells=rc('=IFERROR(<c>[ro_m]*<c>[ro_tu]*<c>[ro_tb],"n/a")')))
    S.blank()
    A(Row('blk_ronta', 'RONTA decomposition', 'BLK'))
    A(Row('rn_nopat', 'NOPAT  =  Adj. EBITA × (1 − tax rate)', 'VAL', cells=rc('=<c>[nopat]')))
    A(Row('rn_ta', '  Total assets', 'VAL', cells=rc('=<c>[bs_ta]')))
    A(Row('rn_gw', '  − Goodwill & intangible assets', 'VAL', cells=rc('=-(<c>[bs_gw]+<c>[bs_int])')))
    A(Row('rn_nibcl', '  − Non-interest-bearing current liabilities (total CL excl. debt & lease liabilities)', 'VAL', cells=rc('=-(<c>[bs_tcl]-N(<c>[bs_debtc])-N(<c>[bs_fllc])-N(<c>[bs_ollc]))')))
    A(Row('nta', '  = Net tangible assets', 'GP', cells=rc('=SUM(<c>[rn_ta]:<c>[rn_nibcl])')))
    A(Row('ronta', 'RONTA  =  NOPAT / NTA', 'KEYP', cells=rc('=IFERROR(<c>[rn_nopat]/<c>[nta],"n/a")')))
    S.blank()
    A(Row('blk_roe', 'Return on Equity (ROE)', 'BLK'))
    A(Row('roe_ni', 'Net income', 'VAL', cells=rc('=<c>[ni]')))
    A(Row('roe_eq', "Stockholders' equity", 'VAL', cells=rc('=<c>[bs_eq]')))
    A(Row('roe', 'ROE  =  NI / Equity', 'KEYP', cells=rc('=IFERROR(<c>[roe_ni]/<c>[roe_eq],"n/a")')))
    S.blank()
    A(Row('blk_levr', 'Leverage', 'BLK'))
    A(Row('nd', 'Net debt  =  term debt (carrying) + revolver + finance leases − cash', 'VAL',
          cells={c: '=IFERROR(%s[debt_cv]+N(%s[bs_rev])+%s[fll]-%s[bs_cash],"")' % (c, c, c, c) for c in 'CDHJLMNOPQRSVWXYZ'}))
    A(Row('lev_e', 'Adjusted EBITDA (LTM for quarters)', 'VAL',
          cells=dict({c: '=%s[adjebitda]' % c for c in 'CDJPVWXYZ'}, **{'L': '=SUM(I[adjebitda],K[adjebitda],L[adjebitda])+H[adjebitda]',
                                                                     'M': '=SUM(I[adjebitda],K[adjebitda],L[adjebitda])+H[adjebitda]', 'N': '=SUM(I[adjebitda],K[adjebitda],L[adjebitda],N[adjebitda])',
                                                                     'O': '=P[adjebitda]', 'Q': '=SUM(L[adjebitda],N[adjebitda],O[adjebitda],Q[adjebitda])',
                                                                     'R': '=SUM(N[adjebitda],O[adjebitda],Q[adjebitda],R[adjebitda])', 'S': '=SUM(N[adjebitda],O[adjebitda],Q[adjebitda],R[adjebitda])'})))
    A(Row('lev', 'Net debt / adjusted EBITDA (x)', 'LEVK', cells={c: '=IFERROR(%s[nd]/%s[lev_e],"n/a")' % (c, c) for c in 'CDJLMNOPQRSVWXYZ'}))
    A(Row('lev_memo', '  Memo: covenant — springing first-lien net leverage ≤ 6.50x (only if revolver usage exceeds threshold; not tested at 30-Jun-26)', 'MEMO'))
    S.blank()

    # =====================================================================================================
    A(Row('sec_val', 'VALUATION', 'SEC', note='VALUATION — current share price input $34.14 (NYSE close 2-Oct-2026; MarketBeat). Update as required.'))
    vc = 'VWXYZ'
    A(Row('px', 'Share price ($) — current', 'PX', cells=dict({'V': 34.14}, **{c: '=V[px]' for c in 'WXYZ'}), comment='KRMN closing price on 2-Oct-2026 ($34.14), per MarketBeat (marketbeat.com, 2-Oct-2026). User-updatable input.'))
    A(Row('v_sh', 'Diluted shares (m)', 'SH', cells={c: '=%s[sh_d]' % c for c in vc}))
    A(Row('mcap', 'Market capitalisation (USDm)', 'VAL', cells={c: '=IFERROR(%s[px]*%s[v_sh],"n/a")' % (c, c) for c in vc}))
    A(Row('v_nd', 'Net debt incl. finance leases (USDm)', 'VAL', cells={c: '=%s[nd]' % c for c in vc}))
    A(Row('ev', 'Enterprise value (USDm)', 'GP', cells={c: '=IFERROR(%s[mcap]+%s[v_nd],"n/a")' % (c, c) for c in vc}))
    A(Row('lbl_mult', 'Multiples', 'VAL'))
    A(Row('ev_s', '  EV / Sales', 'EVX', cells={c: '=IFERROR(%s[ev]/%s[rev],"n/a")' % (c, c) for c in vc}))
    A(Row('ev_e', '  EV / Adjusted EBITDA', 'EVX', cells={c: '=IFERROR(%s[ev]/%s[adjebitda],"n/a")' % (c, c) for c in vc}))
    A(Row('ev_a', '  EV / Adjusted EBITA (model)', 'EVX', cells={c: '=IFERROR(%s[ev]/%s[ebita],"n/a")' % (c, c) for c in vc}))
    A(Row('ev_ic', '  EV / IC', 'EVX', cells={c: '=IFERROR(%s[ev]/%s[ic],"n/a")' % (c, c) for c in vc}))
    A(Row('pe_g', '  P / E (GAAP diluted)', 'EVX', cells={c: '=IFERROR(%s[px]/%s[eps_d],"n/a")' % (c, c) for c in vc}))
    A(Row('pe_a', '  P / E (Adjusted EPS, company definition)', 'EVX', cells={c: '=IFERROR(%s[px]/%s[adjeps],"n/a")' % (c, c) for c in vc}))
    A(Row('pe_x', '  P / E (Adjusted EPS ex-amortization, tax-effected — model)', 'EVX', cells={c: '=IFERROR(%s[px]/%s[adjeps_x],"n/a")' % (c, c) for c in vc}))
    A(Row('fcfy', '  FCF yield', 'RATIO', cells={c: '=IFERROR(%s[fcf]/%s[mcap],"n/a")' % (c, c) for c in vc}))


SCENARIO_TABLE = [
    # row, label, bull, base, bear, note, kind
    (9, 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear', 'Bull', 'Base', 'Bear', 'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of FY26 ranges.', 'title'),
    (11, 'FY26 outlook — Q2-26 release (6-Aug-26)', 'High', 'Mid', 'Low', None, 'ohead'),
    (12, '  FY26 revenue ($m)', 745.0, 737.5, 730.0, 'Raised from $720–735m (Q1-26) and $715–730m (FY25 release); excludes acquisitions after 6-Aug-26 (Walker).', 'oval'),
    (13, '  FY26 Adjusted EBITDA ($m)', 222.5, 218.75, 215.0, 'Raised from $208.5–219.5m (Q1-26) and $207–218m (FY25 release).', 'oval'),
    (15, 'FY26 point estimates (all cases)', None, None, None, 'Not guided — analyst estimates.', 'phead'),
    (16, '  Tax rate (GAAP), 2H/26E', None, 0.24, None, '1H/26 ETR 21.8%; Q2-26 27.2% (§162(m)).', 'pval%'),
    (17, '  Capital expenditures ($m)', None, 36.5, None, 'Investor Update 16-Sep-26: ~$35–38m 2026 capital investments.', 'pval'),
    (18, '  Share-based compensation per quarter, 2H/26E ($m)', None, 1.5, None, 'Q2-26 RSU / PSU expense $1.4m.', 'pval'),
    (19, '  Transaction + integration costs, 2H/26E total ($m)', None, 6.0, None, 'Walker deal / integration; 1H/26 $7.0m.', 'pval'),
]


def lever(row, name, bull_d, bear_d, base_vals, note, pct=True, floor=False):
    out = [(row, name, bull_d, 'Δ →', bear_d, note, 'lhead%' if pct else 'lhead')]
    for i, (yr, v) in enumerate(zip(['2027E', '2028E', '2029E', '2030E'], base_vals)):
        r = row + 1 + i
        if floor:
            out.append((r, '  ' + yr, '=MAX(0,AI%d+$AH$%d)' % (r, row), v, '=MAX(0,AI%d+$AJ$%d)' % (r, row), None, 'lval'))
        else:
            out.append((r, '  ' + yr, '=AI%d+$AH$%d' % (r, row), v, '=AI%d+$AJ$%d' % (r, row), None, 'lval%' if pct else 'lval'))
    return out


SCENARIO_TABLE += lever(21, 'HSMD_growth (Hypersonics & Strategic Missile Defense revenue y/y)', 0.05, -0.08, [0.18, 0.15, 0.13, 0.11],
                        'Interceptor ramps (THAAD, SM-3, PAC-3 MSE content; $90bn+ prime awards), NGI and hypersonic test programs; FY25 +30.9%, 1H/26 +21.7%.')
SCENARIO_TABLE += lever(27, 'SL_growth (Space & Launch revenue y/y)', 0.05, -0.08, [0.15, 0.13, 0.11, 0.10],
                        'Legacy + emerging launch providers; new multi-year LTA (Q2-26) vs launch-schedule timing; FY25 +30.2%, 1H/26 +17.0%.')
SCENARIO_TABLE += lever(33, 'TMIDS_growth (Tactical Missiles & Integrated Defense Systems revenue y/y)', 0.05, -0.08, [0.24, 0.18, 0.15, 0.12],
                        'UAS / C-UAS, tactical SRMs (ISP), PrSM / GMLRS munitions replenishment, European footprint; FY25 +48.5%, 1H/26 +41.1% (incl. acquisitions).')
SCENARIO_TABLE += lever(39, 'MDS_growth (Maritime Defense Systems revenue y/y)', 0.05, -0.08, [0.20, 0.17, 0.14, 0.12],
                        'Columbia / Virginia-class submarine build-rate ramp ($76bn+ awards); disclosed from Q1-26 (Seemann / MSC).')
SCENARIO_TABLE += lever(45, 'ADJ_EBITDA_margin (Adjusted EBITDA margin, outlook / organic basis)', 0.01, -0.02, [0.300, 0.303, 0.306, 0.310],
                        'FY25 30.8%; FY26 outlook mid 29.7%; IPO target ~30%+; operating leverage vs capacity-ramp costs.')
SCENARIO_TABLE += lever(51, 'M&A_spend (acquisition spend, $m)', 150, -150, [200, 225, 250, 250],
                        'Since IPO: ~2.5 deals p.a., $5–15m EBITDA each at ~10x (~$300m in 2026). Funded by revolver / term-loan add-ons.', pct=False, floor=True)
SCENARIO_TABLE += lever(57, 'Buybacks ($m)', 0, 0, [0, 0, 0, 0], 'No repurchase authorisation; capital priority is organic capacity and M&A.', pct=False, floor=True)
SCENARIO_TABLE += [(63, 'Min. net debt / adj. EBITDA (x) — buyback plug', 2.5, 2.0, 2.0, 'Surplus cash below this leverage floor goes to buybacks (Model leverage-targeted buyback rows).', 'levrow')]
