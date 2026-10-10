# Model lessons: per-model nuances

This is the companion to [`MODEL_BUILD_PLAYBOOK.md`](MODEL_BUILD_PLAYBOOK.md). The playbook gives the standard process. This file records what each of the 33 models built so far had to handle that the standard doesn't cover: basis choices, bridge definitions, data quirks, deal blocks, calibration tricks and valuation choices, plus the reusable rule behind each one. The general rules drawn from these entries are in section 5 of the playbook.

**How to use it:** before you build, find the two or three models most like the new company in the finder below and read their entries in full. Each entry links its lessons to playbook phases through the tags [sources] [extraction] [basis] [build] [bridges] [calibration] [BS/CF] [valuation] [QA] [tooling].

**Keep it current:** every new model adds its entry in the same format, under the right sector.

**Provenance:** the entries were compiled from each workbook's basis notes, Modelling Notes column, cell comments and scenario-table rationale, plus the build README and commit message. Where an entry calls something a defect (such as leftover template text), the defect is in that workbook as committed.

## Finder: which models to read for which situation

| Situation | Read |
|---|---|
| Multi-segment US GAAP industrial with organic / acquisition / FX growth | DHR, TMO, STE, LECO, ESAB, WWD, CW |
| Single reportable segment (build by end market or revenue stream) | KRMN, LOAR, RBA, UBER |
| Volume × price unit economics | MLM, VMC (tons × ASP), ODFL, SAIA (tons × rev/cwt), XPO, CHRW (shipments × AGP), RBA (GTV × take rate), UBER (gross bookings × take rate) |
| Backlog, book-to-bill and government contracts | BWXT, HII, CW, WAB |
| Serial acquirer (M&A lever, acquired vs organic) | HEI, LOAR, TDY, WCN, CSGP |
| Large pending or just-closed deal | DHR (Masimo, StatLab), CTAS (UniFirst), CHRW (RXO pro forma tab), MLM (LNA), CSGP (Zonda), UBER (Delivery Hero), ESAB (Eddyfi), TMO |
| Spin-offs, discontinued operations, recast history | DHR, STE, BWXT, XPO, ESAB (spin-co carve-out), MLM |
| Adjusted-measure definition changed over time | TDY, LOAR, RBA, MLM, VMC, CPRT, LECO |
| Company publishes no non-GAAP measures or no guidance | ODFL, HEI, BC, RMS, DHR (EBITDA), STE (EBITDA) |
| Operating-ratio guidance (trucking / LTL) | SAIA, ODFL, XPO, TFII |
| IFRS, non-USD, or not an SEC registrant | ONON (CHF, 20-F), RMS (EUR, AMF filings), BC (EUR), TFII (40-F) |
| Half-year reporter | RMS, BC |
| Recent IPO (short history from the prospectus) | LOAR, ONON, KRMN |
| Non-December fiscal year / 52–53-week years | STE (Mar), CTAS (May), HEI (Oct), WWD (Sep), CPRT (Jul), TDY (52/53-week) |
| Net-cash balance sheet | RMS, CPRT, ODFL |
| Convertibles, mandatory preferred, two-class EPS, dual-class shares | ESAB, BWXT (convertibles / MCPS), RBA (participating preferred), ONON, HEI (share classes) |
| Pension (CAS / FAS, non-service income) | HII, CW |
| Private company, LBO | R&Y |

---

## Aerospace, defense & industrial technology

### TDY — Teledyne Technologies (RBA template → became the TDY template; US GAAP / USD m / 52-53-week FY ending Sunday nearest 31-Dec)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 quarterly, Q3–Q4/26E calibrated. 53-week years are FY2009, FY2015 and FY2020, each with a 14-week Q4 ending 3-Jan of the next calendar year. Period keys follow the fiscal year, not the calendar date. Basis is "latest filing presenting the period", with one exception: FY2006–07 segments exist only on the legacy four-segment basis and sit in memo rows; FY2008–09 use the FY2010 10-K recast. Continental Motors (sold Apr-2011) is in FY2006–07 continuing ops and became disc ops from the FY2010 10-K. ASU 2017-07 recast 2017; ASC 606 did not restate 2017. Acquired-intangible amortization has been its own IS line since Q2-21 (Q1/21 and FY2019–20 reclassified); earlier periods are not re-presented.
- **Operating build:** four segments, each running GAAP OI → + acquired-intangible amortization → + other items (step-up, transaction costs) → non-GAAP segment OI (disclosed by segment from Q1/21, checked against the published figure). Product-line sales are memo rows. Non-GAAP corporate expense is kept separate from corporate adjusting items. Organic growth = total growth less the "incremental sales from recent acquisitions" figure quoted in the release text.
- **Bridges & definitions:** No adjusted OI was published for 2006–Q3/16 or 2018–19. Q4/16–Q4/17 excluded e2v charges only. The 2020 comparatives on the FLIR-era definition first appeared in the 2021 releases. Q1-21 "adjusted" OI was 141.1 as first published and 150.9 once recast in Q2-21, after the 14-May-21 FLIR close. The e2v-era bridge started from pre-ASU 2017-07 OI (FY2017: 335.6 vs 321.7 recast), so the model carries a separate basis-difference line. The 2005–07 "pro forma" EPS excluded pension (net of CAS recovery) and stock-option expense; those items are kept out of the current-definition memo. The tax effect is derived as the company's after-tax column minus its pre-tax column. TDY publishes no EBITDA; the model EBITDA bridge is labelled as a model measure.
- **Data quirks & corrections:** No local copy was found for the Q4-2008 and Q2-2014 releases; both were re-fetched from the EDGAR index. Other points: Q4/24 includes a $52.5m trademark impairment; Q4/22 shows a −$4.0m integration credit; FY2016 adjusted EPS was re-presented in a later release (5.37 → 5.53); interest is reported net.
- **Deals & special blocks:** Future-M&A lever: acquired sales = spend ÷ EV/sales, with a mid-year convention. Intangibles are 30% of consideration, based on Excelitas A&D ($208.2m of $702.8m). 2026E M&A = 1H actual only.
- **Calibration & scenarios:** The anchor is FY26 non-GAAP EPS of $24.45–24.65 plus Q3 guidance of $6.05–6.15. Q3E is solved to the Q3 guide and Q4E = FY − 1H − Q3E. One margin Δ is applied uniformly to all segments. The tax rate on adjustments equals the GAAP outlook rate, so the outlook EPS is hit exactly. 2026E amortization of $226m is backed out of the per-share outlook bridge ($3.70 after tax); the 10-K schedule gives $219.1m, which excludes 2026 deals. Q3/Q4 segment growth uses the Q2/26 y/y rate after the Excelitas anniversary.
- **Balance sheet, cash & capital:** No dividend. Buybacks are a scenario amount (opportunistic, M&A first). The $450m Apr-2026 maturity is in the schedule. Interest is gross on opening debt even though historical interest is net. Pension income is non-cash and reversed in the CF; prepaid pension grows (plans overfunded, no contributions).
- **Valuation:** Share price $615, per the user. DCF NOPAT = (non-GAAP OI − cash transaction costs) × (1 − t). SBC is already expensed. M&A spend is deducted in 2027–30E only. Mauboussin EV/NOPAT on 2028E.
- **Reusable lessons:**
  - [calibration] When the company guides a quarter as well as the year, calibrate that quarter to its own guide and make Q4 the residual (FY − 1H − Q3E).
  - [calibration] Back out guided amortization from the per-share outlook bridge (after-tax $/share × shares ÷ (1 − t)) rather than relying only on the 10-K schedule, which excludes later deals.
  - [bridges] If a historical bridge starts from a pre-ASU (originally reported) GAAP line, add a basis-difference row with the original and recast values in a comment.
  - [bridges] Keep legacy one-off exclusions (pension, stock options) out of the current-definition memo series.
  - [sources] Check the release cache against the full 8-K index before extraction; quarterly gaps hide easily.

### KRMN — Karman Holdings (TDY template; US GAAP / USD m / calendar FY)
- **Coverage & basis:** FY2022–23 annual from the 424B4 (13-Feb-2025). Quarterly from Q1/24, taken from comparatives in the 2025 10-Qs. Balance sheets for 31-Mar-24 and 30-Jun-24 were never published; 31-Dec-22 and 30-Sep-24 come from the prospectus, and FY2021 ending cash is derived from the prospectus CF. At the IPO (14-Feb-25) a Corporate Conversion turned TCFIII Spaceco LLC's 159–167m units into 132.3m shares, so pre-IPO per-unit EPS is not comparable and EPS growth is "n/m" until 2026. Pre-IPO members' equity sits entirely in the APIC row. CIK 0002040127.
- **Operating build:** One reportable segment, built from four end markets. Maritime Defense Systems is disclosed from Q1-26. The 2025 recast moved about $7m of 9M/24 revenue from Space & Launch to Hypersonics and did not restate FY2022–23; the original basis is kept as a memo row. Margins are modelled at group Adj. EBITDA level. Q3/Q4E end-market revenue = 1H/26 share × outlook-implied 2H revenue. Backlog includes $345m acquired at Q2/26; implied book-to-bill is shown.
- **Bridges & definitions:** (1) GAAP OI → model Adj. EBITA → company Adj. EBITDA. (2) NI → EBITDA, with other income left inside EBITDA → Adj. EBITDA. (3) Adj. EPS is not tax-effected and includes items outside EBITDA: the $2.5m Q2-25 debt-cost write-off in interest and $1.5m of entity-status discrete tax. Items disclosed only per share go into a rounding line (about ±$0.7m per period). A memo EPS, tax-effected at 25% and excluding amortization, is added for peer comparability. The only definition change is a label change: "Acquisition related" became "Transaction-related" in Q1-25.
- **Data quirks & corrections:** Q1/25 revenue is $100.124m on the IS but $100.128m in the end-market table; the IS figure is used. The prospectus balance sheets put inventory inside prepaid. D&A is split between COGS (release footnote) and opex. Opex D&A is derived from XBRL as OperatingExpenses − G&A; finance-lease ROU amortization also comes from XBRL.
- **Deals & special blocks:** Walker (closed 28-Aug-26, about $95m) came after the outlook, which reads "excluding the impact of any future acquisitions", so it runs through the M&A lever rather than the calibration. EV/sales of 2.6–2.8x is derived from ~10x EBITDA × a 27% margin (Investor Update). Intangibles are 29% of consideration for Seemann and an assumed 45% for Walker.
- **Calibration & scenarios:** Revenue anchor $730–745m, Adj. EBITDA anchor $215–222.5m. The 2H split follows the prior-year Q3:Q4 revenue pattern, and EBITDA is spread pro rata to revenue.
- **Balance sheet, cash & capital:** Term Loan B with 1% p.a. amortization of original principal, plus add-ons ($265m Feb-26, $100m Aug-26). The SOFR level is backed out of the reported all-in rate. Revolver balances above the $150m commitment are labelled as assumed further add-ons. Finance leases (8.21%) count as debt. There is no buyback authorization, so buybacks are a leverage-floor plug only. The leverage covenant memo is springing only.
- **Valuation:** $34.14 (close 2-Oct-26, MarketBeat). The DCF starts from Adj. EBITA and deducts SBC and transaction costs again, because the company definition excludes them. P/E is 50/40/28x on the untaxed company Adj. EPS. Beta comes from peers because the trading history is short.
- **Reusable lessons:**
  - [calibration] Read the guidance wording for "excluding future acquisitions". Deals that close after the outlook date go in the M&A block, not the calibration.
  - [bridges] If company adjusted EPS is not tax-effected, rebuild it exactly as published, then add a tax-effected, ex-amortization memo EPS. Label clearly which one the P/E uses.
  - [valuation] If the company's EBITDA excludes SBC, NOPAT must deduct SBC again.
  - [extraction] Derive acquired sales from total growth minus organic growth × prior-year revenue when only percentages are given (Q2/26: $38.9m).
  - [BS/CF] A revolver draw above the facility size is a hidden financing assumption. Label it, or cap it and flag the shortfall.

### HEI — HEICO (MLM template, US GAAP / USD / FY ends 31 Oct)
- **Coverage & basis:** FY2006–25 annual, with quarterly history from Q1 FY13 to Q3 FY26; Q4/26E is the only estimate quarter. XBRL starts in Q3 FY2010. There are seven 5-for-4 splits (×4.77 cumulative): each filing's share data is multiplied by 1.25^(splits after its filing date). Common (HEI) and Class A (HEI.A) shares are combined. Q4 WASO = 4 × FY − ΣQ1–Q3. SFAS 160 applies from FY2010, so FY2006–08 minority interests are recast as NCI and the pre-FY2010 cash flow is recast to start from consolidated NI. ASU 2016-09 applies from FY2017.
- **Operating build:** FSG and ETG revenue = prior year × (1 + company-reported organic + acquired growth), where acquired growth = total − organic. Organic figures are curated from releases, and qualified figures are excluded. Segment sales include intersegment sales, which are eliminated at a ratio. Corporate is derived. Gross margin is an input and SG&A is the plug, because segment OI is reported but segment GP is not. Amortization of existing intangibles comes from the 10-Q schedule (FY27 $170.8m … FY30 $149.0m).
- **Bridges & definitions:** HEICO publishes EBITDA only from the Q4 FY2018 release (with FY17 comparatives), and the model ties to it. Adj. EBITDA is a model definition: plus acquisition costs, plus non-cash contingent-consideration remeasurement (from the cash-flow statement), minus the FY23 $9.1m contingent-consideration gain, plus intangible impairments. Adjusted EPS removes the ASU 2016-09 option tax benefit net of NCI (mostly Q1; FY totals = XBRL × the Q1 net/gross ratio) and the TCJA net benefit. The only published adjusted EPS is Q1 FY16 ($.49 ÷ 1.25³). Wencor costs were largely non-deductible, so a true-up row brings after-tax costs to the disclosed figure. The adjusting-item tax rate is the ETR bounded 15–40%.
- **Data quirks & corrections:** Interest expense is derived as OI + other income − PBT. Q3/23 Wencor costs are reconstructed from segment FY − Q4. Dividends are semi-annual (Jan/Jul), with special dividends in FY13/14. FY2009–12 redeemable NCI is derived as a residual.
- **Deals & special blocks:** Wencor and Exxelia (FY23) and the FY26 deals are carried through the acquired-growth % (Q4/26E = the Q3 contribution; 2027E = annualisation). The future-M&A lever uses a mid-year convention, with intangibles ~35% and PP&E ~4% of spend (from the Wencor PPA).
- **Calibration & scenarios:** There is no numeric guidance. The FY26 target cells are **optional and blank by default**; the calibration Δ only activates if a target (e.g. consensus) is entered.
- **Balance sheet, cash & capital:** Four note tranches, including the Jul-26 issue; the revolver plugs to minimum cash. There is no open-market buyback (none since FY2010), so buybacks run only below a leverage floor (Bull 1.5x / Base 1.0x / Bear 0.5x). Redeemable NCI (put rights) is held flat in mezzanine. NCI distributions are ~80% of NCI income. LTM Adj. EBITDA in quarter columns allows quarter-end leverage.
- **Valuation:** The HEI price ($302.45) is applied to both classes, and the note warns that HEI.A trades ~20% lower, which overstates market cap. Redeemable NCI is deducted in the EV bridge and IC. The DCF discounts to 31-Oct, and because FY2026 is ~complete, the explicit period starts FY2027E.
- **Reusable lessons:**
  - [basis] Split-adjust with factor = ratio^(number of splits after the source's filing date); derive Q4 shares as 4 × FY − ΣQ1–3.
  - [calibration] For companies without guidance, make the calibration targets optional inputs (blank = driver-based, Δ = 0) rather than inventing an anchor.
  - [bridges] When transaction costs are non-deductible, true up the model tax effect to the disclosed after-tax amount.
  - [build] Where the company discloses organic growth, decompose acquired growth as total − organic and roll deal annualisation into the next year's acquired %.
  - [valuation] For dual-class shares at different prices, note the overstatement (or use a blended price); deduct redeemable NCI in both EV and IC.
  - [valuation] When the fiscal year is nearly complete at the valuation date, put its flows in year-end net debt and start the explicit DCF the following year.

### LOAR — Loar Holdings Inc. (MLM template, US GAAP / USD m / Dec FYE)
- **Coverage & basis:** All periods as originally reported. FY2012–21 are annual P&L / bridge-only columns built from the IPO prospectus (424B4, 26-Apr-2024) NI → Adj. EBITDA reconciliation. FY2017 = predecessor (1-Jan–1-Oct) + successor (2-Oct–31-Dec) summed as presented. Quarters run Q1/22–Q2/26: 2022–23 come from the prospectus quarterly tables and the 2024 release comparatives. Quarter-end BS starts Q1-24; FY22–23 year-ends come from the prospectus. The registrant was Loar Holdings, LLC (204 common units) until the IPO on 29-Apr-2024, so per-share data starts Q2-24 and FY24 share weighting is as published. Template columns shifted −42.
- **Operating build:** 4 end markets × OEM / aftermarket (release Table 5), first disclosed FY2022. Q1-23 = 1H-23 − Q2-23. The "Other" line was called "Non-Aerospace" in the Q2/Q3-25 releases. A "not split" residual row covers pre-2022 history and 2022 quarters. Organic vs acquired sales use the company definition (acquired businesses become organic from the 13th month), with a check row on published organic growth.
- **Bridges & definitions:** (1) NI → EBITDA → Adj. EBITDA as published, with lines that come and go (MSA fees to 2017, COVID 2020–22, refinancing costs below OI from Q2-24). (2) Model Adj. EBITA, checked as EBITA + depreciation = published Adj. EBITDA. (3) Adj. EPS: the Q1-26 release added tax-effected amortization of acquired intangibles to the definition and restated only Q1-25 and Q2-25. The model applies the current definition from Q2-24. The tax rate on the amortization add-back is backed out of the restated quarters (20.2%); 24% is an input for 2024 and 20.2% for 2H-25. Memo rows rebuild the prior definition and check it against every originally published figure (Q2-24–Q4-25, FY24, FY25). The company's tax adjustment excludes SBC and transaction costs, which it treats as non-deductible.
- **Deals & special blocks:** PPAs sit in the closing-quarter column for SCHROTH, DAC + CAV (aggregated), AAI, Beadlight, LMB (EUR consideration, includes debt repaid) and Harper (contingent consideration of $15.3m, max $55m, carried as a liability). The amortization schedule is the 10-K schedule, which predates Harper, plus Harper (~$10.2m p.a.) plus ~$4.4m of other / step-up amortization, reconciled to the FY26 ~$65m guide.
- **Calibration & scenarios:** Revenue Δ is solved to FY26 sales ($665–675m). In Q3/Q4 the 1H y/y growth includes LMB and Harper, so explicit acquisition-sales inputs (~$15m and ~$16m a quarter) keep organic growth separate. Margin Δ is solved to Adj. EBITDA ($265–270m). NI and Adj. EPS guidance are information rows only. M&A lever: $300m p.a. at 6.0x EV / sales.
- **Balance sheet, cash & capital:** Term loans (SOFR + 4.25%) are prepayable at par, with a sweep to minimum cash. Debt-cost accretion (~$1m a quarter) raises the carrying value and is added back in CFO. There is no buyback programme: the leverage floor only starts returning cash from 2027E.
- **Valuation:** $75.00 early-Oct-2026 quote. DCF NOPAT = (Adj. EBIT after all D&A − transaction & integration costs) × (1 − t), with D&A, including acquired amortization, added back. The rationale text calls SBC a real cost, but the NOPAT row label deducts only transaction / integration costs. Opening IC adds Harper's $249.8m. Charts show `#N/A` for 2012–21 returns (no BS), by design.
- **Reusable lessons:**
  - [bridges] When a definition change restates only some comparatives, back out the implied tax rate on the new add-back from the restated periods and apply it to the unrestated ones. Keep prior-definition memo checks against every original print.
  - [calibration] If the YTD y/y growth used for 2H includes acquisitions that are still inorganic, add their sales as an explicit input instead of letting the growth rate carry them.
  - [basis] Predecessor / successor years are summed as presented and labelled. Per-share rows start at the IPO quarter, and pre-IPO LLC units are flagged as not meaningful.
  - [extraction] Watch for line renames between releases ("Other" ↔ "Non-Aerospace") and map them to one row.
  - [QA] The Bull-Base-Bear P/E comment (N26) still carries the MLM text ("MLM has traded at ~25–35x…"). Grep every comment on the Bull-Base-Bear and DCF tabs for the template ticker.

### BWXT — BWX Technologies (MLM template, US GAAP / USD / Dec FY)
- **Coverage & basis:**
  - History: 2012–13 annual and Q1/14–Q2/26 quarterly, on the continuing-ops basis after the Power Generation (BWE) spin on 30-Jun-2015. Q1/14 = 6M/14 − Q2/14; balance sheets from the Dec-14 recast; pre-spin balance sheets are not shown.
  - Cash flow 2014–Q2/15 stays consolidated (includes PG), and 2014 returns are suppressed.
  - Segments: Government/Commercial from 2022 (2020 annual and 2021 quarters recast). NOG/NSG/NPG kept as memo. Before 2021, backlog uses a Commercial proxy (NE/NPG) with Government as the remainder.
- **Operating build:** backlog roll-forward. Bookings = revenue × book-to-bill: 1.0x for quarters (naval awards are lumpy), with scenario B2B for annual years. A derived "adjustments/de-bookings" line closes the historical roll and is nil in the forecast. Equity income of technical-services JVs is modelled as % of Government revenue. Commercial is split into core, PCG (closed 1-Jul-26, price undisclosed, assumed ~2.4x sales) and medical (~$130m, not separately reported).
- **Bridges & definitions:**
  - Pension/OPEB mark-to-market sat in OI until 2017 and in Other–net from 2018 (ASU 2017-07); the EBITDA bridge treats it differently either side of 2018.
  - Adjusted EBITDA was first published in Q3/21 (for 2020–21).
  - Acquisition amortization has been added back to non-GAAP since 2025.
  - A per-share rounding row reproduces published non-GAAP EPS.
  - Q4/17 was a loss quarter, but the company used 100.4m non-GAAP diluted shares (−0.8 residual).
  - Tax on adjustments: 35% statutory for 2012–13 (no company figure).
- **Deals & special blocks:** medical sale to Nordic Capital (~80% sold, 20% retained), closing assumed 31-Mar-2027. Proceeds are scenario-based ($800m Bull / $750m Base and Bear). The carrying value is an assumption, split 60% PP&E / 25% goodwill / 15% intangibles. The gain sits in OI and is excluded from non-GAAP; the retained stake goes to equity-method investments.
- **Calibration & scenarios:** uniform growth Δ to revenue ~$3.8bn; uniform margin Δ to adj. EBITDA $662–672m. Non-GAAP EPS and FCF are information rows only. The 2026E advance-billings % is set so FCF lands in the guided range.
- **Balance sheet, cash & capital:** 4.125% 2028/2029 notes; 0% convertible notes due 2030 ($1.25bn, conversion $262.51, capped call $396.24 ignored as anti-dilutive), with treasury-stock-method dilution above the conversion price, driven by the appreciating share price. A fees/capitalized-interest row is calibrated to 1H/26 interest ($10.0m vs $16.5m of coupons). Cash includes restricted cash from 2018.
- **Valuation:** $152.29, taken from a Form 4 tax-withholding price (1-Sep-26). The convertible is counted at face in net debt. The DCF excludes the 2026E UFCF (flag = 0) because YE26 net debt already reflects it. 2027E UFCF adds after-tax medical proceeds.
- **Reusable lessons:**
  - [build] Backlog roll-forward: derive a historical "adjustments" plug (closing − opening − bookings + revenue), and hold quarterly book-to-bill at 1.0 for lumpy government awards.
  - [BS/CF] Model convertible dilution with the treasury-stock method on the forecast share price and ignore capped calls in GAAP EPS. Deduct the convert at face in EV.
  - [valuation] When valuation net debt is taken at the current-year end, set that year's UFCF inclusion flag to 0 to avoid double counting.
  - [build] For divestitures with a retained stake, derecognise assets by an explicit split and move the retained piece to equity-method investments.
  - [calibration] When modelled interest misses actuals because of capitalized interest, add a fees/capitalized-interest row calibrated to YTD interest.
  - [sources] With market data blocked, use the latest price in an SEC filing (Form 4 withholding price) and date it.

### CW — Curtiss-Wright (MLM template, US GAAP / USD / Dec FY)
- **Coverage & basis:** FY2006–12 annual, quarterly from 2013, as originally reported. 2006–10 statements come from 10-K text; 2011+ from XBRL statement renderings. Segment structure has changed four times: FC/MC/MT → FC/Controls/ST (2013) → C/I, Defense, Energy/Power (2014–20) → A&I, DE, N&P (2020 restated in the 2021 releases). Pre-2020 totals sit in a "not on current segment basis" row with the legacy detail in memo. End-market taxonomy also changed (legacy rows kept).
- **Operating build:** segment growth × incremental margin. Q3/Q4-26E growth = (segment guidance end-point − 1H) ÷ 2H/25 − 1, by scenario. Segment margin is solved to segment adjusted-OI guidance. Then a total-level uniform Δ is applied, because segment ranges do not sum to the total range (high OI pairs with −$44m corporate). Opex lines are presentation only; gross profit is the residual.
- **Bridges & definitions:**
  - The consistent adjusted framework dates only from Q2/18 (DRG; first-year purchase accounting). 2012 and 2015 have one-off adjusted figures; other pre-2018 periods are adjusted = GAAP, flagged.
  - Adjusted EBITDA is model-defined (CW publishes none); first-year backlog amortization sits in both adjustments and D&A (<$3m/qtr).
  - Adjusted EPS plug = published × diluted shares − (GAAP + after-tax items); it captures non-operating exclusions such as executive pension settlements and discrete tax.
  - Adjusted EPS keeps the originally published 2020 figure (later restated to $6.59).
  - FCF and adjusted FCF bridges: adjusted FCF existed 2015–23 only. FCF residuals come from later CFO restatements, and the conversion definition changed in 2023.
- **Data quirks & corrections:** order numbers are narrative-rounded. The $17m Q2/26 equity-securities gain is in GAAP other income guidance but excluded from adjusted. Tax rate on historical adjustments is bounded to 15–40%.
- **Calibration & scenarios:** guidance of 5-Aug-26. EPS is not forced because it predates the $300m 10b5-1 buybacks (Aug–Oct). FCF guidance ($585–605m) is hit by solving 2026E DSO (a working-capital calibration).
- **Balance sheet, cash & capital:** the Dec-26 $200m 4.24% notes are repaid from cash; 2028/2030 are refinanced at ~5.5%. Buybacks = max(minimum $60m "offset dilution", leverage plug). Non-service pension income is non-cash: it accretes the prepaid pension asset and is reversed in CFO. Capex is net of grant proceeds.
- **Valuation:** ~$544.21 (early-Oct quote, approximate). The DCF excludes 2026E (cash flow is in YE26 net debt). Pension income is excluded from UFCF, and the overfunded plan is not deducted.
- **Reusable lessons:**
  - [calibration] When segment guidance ranges don't sum to the total, drive segments from their own end-points, then apply a single total-level Δ to hit the total.
  - [calibration] Use FCF guidance to solve a working-capital driver (DSO) for the current year, then hold it.
  - [calibration] Don't force EPS guidance that predates announced 10b5-1 buybacks; show the gap.
  - [bridges] Where the adjusted framework is intermittent, define adjusted = GAAP in non-published periods with a flag, and use an EPS plug row only in published periods.
  - [BS/CF] Model non-service pension income as a non-cash accretion to the prepaid pension asset.
  - [BS/CF] Combine a minimum anti-dilution buyback with the leverage plug (max of the two).

### WWD — Woodward (MLM template via STE kit; first playbook build; US GAAP / USD / FY ends 30-Sep)
- **Coverage & basis:** FY2011–20 annual, Q1/21–Q3/26 quarterly, as originally reported (CIK 108312). Restatements are not recast but kept as memo rows: FY2016 cost reclass, and FY2018 ASU 2017-07, which moved segment earnings (Aero $301.8m → $308.6m). Energy was renamed Industrial in FY2016. No splits since Feb-2008.
- **Operating build:** sales by primary market from the 10-Q/10-K revenue note (FY2019+, Q4 = FY − 9M), × segment margin, + adjusted nonsegment expense = adjusted EBIT. Industrial markets were redefined in the FY2023 10-K: FY21–22 annual from that 10-K and FY23 quarters from FY24 10-Q comparatives (latest filing presenting the period); the old split is a legacy memo. Segment earnings are after amortization. History falls back to segment totals where markets are unpublished.
- **Bridges & definitions:** there is no operating-income line, so EBIT is the company definition (NI + tax + interest expense − interest income). Adjusted measures exist from Q2 FY2018; FY2011–17 adjusted = GAAP (flagged). The company's per-period adjusting-item labels are stored as cell comments on each grouped category row. FY2018–19 L'Orange backlog amortization is already in D&A and is not added back twice. Historical tax effect = published adjusted NI − NI − items (includes the German rate change in FY2025).
- **Data quirks & corrections:**
  - Releases show CFO as one line, so working capital is derived (CFO − NI − D&A − SBC − deferred tax).
  - Q1 FY22/FY23 deferred tax is untagged in XBRL and treated as 0.
  - FY2023 Σ quarters ≠ FY by $1.4m (COGS↔R&D reclass); the year total is used.
  - check_data runs 724 checks.
- **Deals & special blocks:** PPAs for L'Orange, Safran EMA and Valve Research. The ONTIC pilot-controls sale ($180m) has its gain = proceeds − net assets held for sale; it is adjusted out and reclassified to investing. Revenue for the divested lines is undisclosed (flagged input 0).
- **Calibration & scenarios:** Q4/26E only. Sales Δ is solved to FY25 × (1 + guided growth). Margin Δ is solved to adjusted EPS by back-solving the required Q4 adjusted EBIT = (NI target − 9M) ÷ (1 − t) + net interest. Segment growth, margin and FCF guidance are information rows.
- **Balance sheet, cash & capital:** EUR private-placement notes are converted at 30-Sep-25 FX. The $450m U/V/W notes close exactly at FY-end. The revolver has a headroom memo against its $1.0bn commitment. The company's "EBITDA leverage" (total debt / TTM EBITDA) is shown next to model net leverage. Working-capital days compare year-end to year-end.
- **Valuation:** $382.17 = weighted-average June-2026 repurchase price (10-Q Part II Item 2). The FY ends a week before valuation, so FY2026E is the base year and FY27–31E are explicit; Mauboussin uses FY2029E. Market inputs are labelled assumptions (FRED blocked).
- **Reusable lessons:**
  - [sources] When market data is blocked, the 10-Q Part II Item 2 average repurchase price is an SEC-sourced share price; cite the month.
  - [extraction] If releases give CFO as a single line, derive working capital from XBRL SBC and deferred tax, and treat missing tags as 0 with a note.
  - [bridges] Store the company's verbatim adjusting-item labels per period as comments on grouped category rows.
  - [calibration] For EPS guidance, back-solve the required adjusted EBIT through tax and interest, then solve the margin Δ.
  - [valuation] When FY end ≈ valuation date, roll the DCF: that FY is the base year and net debt is taken at its end.
  - [BS/CF] Add a revolver-headroom memo row so the minimum-cash plug can't silently exceed the commitment.

### HII — Huntington Ingalls Industries (DSV template, US GAAP as reported / USD millions / FY Dec)
- **Coverage & basis:** 2015–1H26 from 10-K/10-Q XBRL and 8-K Ex. 99.1 (CIK 0001501585). FY2015–16 are as originally reported; FY2017+ are as recast for ASU 2017-07 in the 2018 10-K (non-service pension moved below OI). Technical Solutions was formed Dec-2016 (renamed Mission Technologies 2022). Q1–Q3/15 stay on the original "Other" basis; Q4/15 and FY2015 are recast. Q4 = FY − 9M. Restricted cash is included from FY2019. Unbilled receivables are separate from FY2017 (ASC 606).
- **Operating build:** Ingalls, Newport News and MT. Segment revenue includes intersegment sales (intersegment n/d before 2018). Segment D&A and capex are quarterly from 2024 (ASU 2023-07). Backlog is funded/unfunded; implied awards = Δbacklog + revenue; book-to-bill is 1.0x in out-years. MT equity income from JVs is shown separately.
- **Bridges & definitions:** GAAP OI + Operating FAS/CAS + non-current state taxes = segment OI (HII non-GAAP). Adj EBIT additionally removes the items HII itself adjusted: the Q2-15 $136m Katrina insurance gain, 2015 impairments ($75m goodwill + $27m TS intangible) and 2019 impairments ($29m + $6m). The 2020 $13m impairment is not adjusted. HII's adjusted NI definition kept changing (2015–16; 2017–18 tax reform; 2019; 2020–21 "pension-adjusted") and stopped after FY2021. The model therefore holds one constant definition: ex total FAS/CAS, ex non-current state tax, ex non-recurring items, tax-effected at the statutory rate, plus the 2017 discrete items ($56m TCJA + $7m). Other income and other non-operating are derived residuals (e.g. a $120m FY2023 gain). Debt-extinguishment losses ($44m 2015, $22m 2017, $21m 2020) sit inside interest expense, shown as a memo row.
- **Calibration & scenarios:** FY26 guidance from the Q2-26 release (30-Jul-26):
  - Shipbuilding revenue $10.2–10.4bn at a 6.0–6.5% margin.
  - MT revenue $3.0–3.2bn at a ~5% margin (Bull/Bear ±25bp).
  - FCF $500–600m.
  - FAS/CAS −$44m, state tax −$20m, interest $105m, non-op retirement $213m.
  - ETR ~17%, D&A ~$330m, capex 4–5%.
  Q3/Q4 = (FY − 1H)/2. Shipbuilding guidance is split between Ingalls and NNS by 1H revenue mix, and 2H OI by 2H revenue × 1H margin weights. Cost of service revenues is the balancing line. 2026E contract assets are solved so FCF = guidance by scenario ($600/550/500m).
- **Balance sheet, cash & capital:** retiree-benefits CF ≈ FAS/CAS adjustment − non-op retirement benefit (within ±$5m FY23–25), accreting the net pension asset. FCF follows HII's definition: CFO − capex + grant proceeds. PP&E is rolled forward net of grants. Debt is held at $2.7bn, with the 2027 $600m and 2028 $621m maturities refinanced at 3.9–4.0%. Buybacks were $0 in FY25/1H26 and resume at $200m+ in 2027E. DPS is $1.38/qtr, +3%. Amortization follows the 10-K schedule (2026 $84m … 2030 $41m).
- **Valuation:** $275 user price. Historical average prices exist only for 2015–17 (the 10-K Item 5 high/low table was dropped from FY2018). The DCF excludes non-cash FAS income from UFCF and makes no pension adjustment to net debt. P/E is 16.5x Base, 19x Bull, 14x Bear.
- **Reusable lessons:**
  - [calibration] When the company guides FCF, solve the swing working-capital item (contract assets) so current-year FCF = guidance, then carry its days forward.
  - [calibration] Allocate aggregate guidance (shipbuilding) to segments by 1H revenue mix, and allocate OI by 2H revenue × 1H margin weights.
  - [bridges] If the company's adjusted-NI definition is unstable or discontinued, use one labelled model definition for all periods and show the company figures beside it.
  - [BS/CF] For defense contractors (CAS pension), model the FAS/CAS split explicitly. The non-cash FAS income goes into a retiree-benefits CF line and is excluded from UFCF.

### WAB — Wabtec (MLM template, US GAAP / USD / December FY)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 quarterly, as originally reported. Shares and per-share data before Jun-2013 are restated for the 2-for-1 split. Faiveley from 30-Nov-16. The GE Transportation merger (25-Feb-19) triggered a segment recast in Q4-19, and product-line sales are published from 2019, with Q1–Q3/19 on the Q4-19 recast basis. CIK 0000943452.
- **Operating build:** product lines (Freight: Services, Equipment, Components, Digital Intelligence; Transit: OE, Aftermarket) → segment sales × adjusted operating margin. A "not split by product line" row carries the pre-2019 segment totals. Backlog memos: 12-month and total by segment, 12-month backlog ÷ annualised sales, and implied orders = Δ total backlog + sales (Wabtec publishes no orders; the figure includes FX and acquired backlog). Sales-change bridge as published (acquisitions / portfolio optimisation / FX / organic) with a check row. Forecast segment adjusting items = consolidated items × the segment's 1H share.
- **Bridges & definitions:**
  - EBITDA was first published in 2019. The 2019 definition is OI + D&A; from 2020 it is OI + other income + D&A, with a basis-difference row. From Q3-25 inventory purchase-accounting is added back.
  - Adjusted OI and EPS: 2019 is on the merger basis with amortisation not added back; all amortisation is added back from Q1-20. FY19 adjusted EPS was later restated to $4.86 vs $4.17 as originally reported, and the model keeps the original.
  - Per-period company item labels are stored as cell comments on the total-items row.
  - Before Q4-17 only narrative per-share bridges exist (FY06, Q4-09, FY11, 2016). These are entered as $/share inputs × diluted shares.
  - Adjusted EPS uses the company's "fully diluted shares" where published, which differ from GAAP diluted shares in loss quarters (Q1-19). The check tolerates ±0.02 for two-class rounding.
- **Deals & special blocks:** PPAs for Inspection Technologies (1-Jul-25), Frauscher (1-Dec-25) and Dellner (10-Feb-26) sit in the closing-quarter column, with a deal-name row. The Q3/Q4-26E growth inputs add the non-anniversaried deal sales as analyst estimates.
- **Calibration & scenarios:** two solves. (1) A uniform growth Δ across all product lines solves FY26 sales to $12.30–12.60bn, using a "sales sensitivity to +1.00 of growth" helper row so the solve is closed-form. (2) A uniform segment-margin Δ solves FY26 adjusted EPS to $10.60–10.90: required 2H adjusted OI = (required adjusted NI + NCI) ÷ (1 − t) + interest − other income. The five-year outlook (350+ bp margin expansion over 2025–29) informs the margin levers.
- **Balance sheet, cash & capital:**
  - Notes maturity ladder, including the €500m 2027 notes at book value.
  - Prepayable pool covers the revolver, CP and receivables securitisation.
  - Leverage-floor buybacks against the company's 2.0–2.5x target.
  - DPS × beginning shares to avoid circularity with buybacks.
  - Treasury-stock method for repurchased shares.
  - Existing-intangible amortisation follows the 10-Q schedule ($356m in 2027 and so on).
- **Valuation:** $280 from Form 4 sales (1-Sep-26). NOPAT deducts cash restructuring. The Dellner consideration is excluded from 2026E UFCF and added to opening IC. The BBB P/E comment still quotes MLM ($518.70): template leakage.
- **Reusable lessons:**
  - [calibration] For a closed-form revenue solve, add a helper row giving FY revenue sensitivity to +1.00 of growth on the remaining quarters; Δ = (target − pre-calibration) ÷ sensitivity.
  - [calibration] When the guided KPI is EPS, back into required 2H adjusted OI through NCI, tax, interest and other income, so adjusting items drop out on both sides.
  - [bridges] Store the company's line-item wording and amounts per period as a comment on the total-adjustments cell. Category rows can then stay few while the audit trail is kept.
  - [bridges] Narrative-only per-share bridges: input $/share as published (split-adjusted) and convert at diluted shares in a separately labelled row.
  - [build] Without published orders, derive implied orders from the backlog roll-forward and label what it includes (FX, acquired backlog).

## Construction materials

### MLM — Martin Marietta Materials (TDY template → source of the current MLM template; US GAAP / USD m / calendar FY)
- **Coverage & basis:** FY2006–25 annual, quarterly from Q1/13. Pre-2019 balance sheets come from the 10-K Exhibit 13 annual report; FY2008 comes from the FY2009 comparative, recast for SFAS 160. The basis is hybrid: Midlothian cement and Texas ready-mix are disc ops from Q3/25, the 2025 quarters are recast to continuing ops, and 2024 and earlier stay as originally reported. 2025 y/y therefore compares mixed bases, which is noted in the workbook.
- **Operating build:** Aggregates shipments (internal tons included, thousands → millions) × ASP × an uplift factor (revenue ÷ shipments × ASP) that captures freight and internal sales. The product-line revenue basis changed twice: net sales to 2017, products & services ex freight 2018–22, total revenues from 2023. A derived "freight outside product lines" row (consolidated − Σ lines) keeps the build tying. Building Materials revenue is not split by product line before Q3/11, and gross profit not before Q4/12. ASP is not published for 2006–12 or Q3/14–2015 (TXI heritage/acquired split only), so the company's price-change % fills those years. Interproduct elimination starts in 2016. The Specialties Q3/Q4E growth input is +5% instead of the Q2 y/y +69%, which is inflated by Premier Magnesia until it anniversaries. Segments (East/West, recast Q1-26) are memo rows.
- **Bridges & definitions:** The company's start line changed from NI attributable including disc ops (to Q3/21) to continuing ops (from Q4/21). For 2006–Q3/09, EBITDA was reconciled from operating cash flow; the model rebuilds it from NI and carries a residual row. EBITDA became "Adjusted EBITDA" in 2018. Equity-affiliate results were added in 2019. From 2024 only deals of at least $2.0bn (Building Materials) or $200m (Specialties) have their costs added back. Q2–Q3/15 had no quarterly EBITDA. Adjusted EPS was published only sporadically, so one model definition is applied to all periods, with a plug to the published figure where one exists.
- **Deals & special blocks:** LNA closed 21-Aug-26: 41 days in Q3, then a full Q4. Standalone history comes from the target's audited and interim financials (8-K Ex. 99.1/99.2). The PPA comes from the pro forma Ex. 99.3:
  - purchase-accounting D&A of $380m, of which $365m is intangible amortization on $5.9bn of intangibles;
  - a $59m inventory markup;
  - a deferred tax liability of $2,039m at 24.6%;
  - 10.95m consideration shares at $576.70 (pro forma).

  $85m of synergies × a realisation lever. A pro forma full-year Adj. EBITDA memo drives leverage and EV multiples, and working capital is sized on pro forma full-year revenue. The QUIKRETE exchange produced a $1.98bn pre-tax gain ($1.43bn after tax, in disc ops).
- **Calibration & scenarios:** Guidance excludes LNA, so only legacy is calibrated. Step 1 solves a revenue Δ to $7.2–7.4bn, using a "revenue sensitivity to +1.00 growth" helper for a closed-form linear solve. Step 2 solves a gross-margin Δ to legacy Adj. EBITDA of $2.36–2.50bn. LNA is added on top. The tax rate comes from the mid-point reconciliation (279 / 1,322 = 21.1%).
- **Balance sheet, cash & capital:** $5.5bn of new notes (5.52% blended) and a $1.5bn prepayable term loan. Surplus cash repays the facilities first. Buybacks are zero until leverage falls below the floor (target under 2.5x within 24 months; 3.7x at close). DPS rises 5% in August.
- **Valuation:** $518.70, the price on Form 4 grants dated 31-Aug-26, because EDGAR was the only reachable price source. DCF opening IC includes the $13.5bn LNA consideration. LNA amortization is largely non-deductible, so NOPAT overstates the tax shield.
- **Reusable lessons:**
  - [calibration] Calibrate in two steps, revenue Δ then margin Δ. A linear sensitivity helper row gives a closed-form solve without goal-seek or circularity.
  - [build] When product-line tables change revenue basis, add a derived "outside product lines" row so build vs consolidated ties in every period.
  - [build] Override the Q2 y/y trend with an organic input when an acquisition anniversaries inside the forecast quarters.
  - [BS/CF] In the closing year, size working capital and leverage on pro forma full-year revenue and EBITDA.
  - [valuation] Without a user price, a dated Form 4 transaction price on EDGAR is a traceable fallback. Flag it to be updated.

### VMC — Vulcan Materials (TDY template; US GAAP / USD m / calendar FY)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 quarterly. All periods are as originally reported, unlike TDY. The registrant changed in Nov-2007: legacy CIK 0000103973, current CIK 0001396009 (Florida Rock deal). Before 2018, delivery revenues sat outside the segments; ASC 606 moved freight into segment revenues. Restricted cash is in the CF from FY2017.
- **Operating build:** Aggregates = tons × freight-adjusted price − unit cash cost = cash gross profit (a company non-GAAP measure, checked against the published figure). Freight & delivery is modelled as a ratio to freight-adjusted revenue, and DDA&A per ton is a driver. Asphalt and Concrete are built from shipments and price. Legacy Cement/Calcium sit in memo rows but are included in group totals. 2007–09 had a combined asphalt-and-concrete segment. Aggregates reserves and reserve life are shown as annual disclosure rows.
- **Bridges & definitions:** No EBITDA was published in 2006; EBITDA only (continuing ops) ran 2007–10. Adjusted EBITDA arrived in FY2011 at $440.4m and was restated in the FY2012 release to $351.8m. From Q4/15, deferred-revenue amortization is no longer deducted, so Q1–Q3/15 do not sum to FY2015. In Q4/22–Q1/23, disc ops were removed after tax inside the EBITDA build; from Q2/23 tax includes disc ops and the pre-tax disc-ops gain or loss moves into the Adjusted EBITDA bridge. The FY2008 release EBITDA came before the $252.7m goodwill impairment that was booked in the 10-K. Adjusted EPS is per-share only: "items in Adj. EBITDA, net of tax" plus discrete tax. The tax effect = per-share item × shares − pre-tax items. 2014 adjusted EPS figures come from the 2015 comparatives because the 2014 releases gave narrative only. The model Adj. EBIT bridge has a known residual: tax on disc ops.
- **Data quirks & corrections:** Releases for Q2/14–Q3/14 label calcium as "Cement". The 2007 price covers legacy Vulcan only.
- **Deals & special blocks:** Revenue of divested businesses is not disclosed, so a "divested share of prior-year quarter" input is used: Houston asphalt about 4–5%; California ready-mix about 46%, inferred from the −15% y/y with two of three months owned. Both are labelled analyst estimates. The M&A lever runs on EV/EBITDA with a PP&E/intangibles/goodwill split and a depletion life.
- **Calibration & scenarios:** Adj. EBITDA guide $2.4–2.6bn. Guided volume (+1–3%), price (+4–6%) and LSD cost are applied first; the residual Δ goes onto aggregates unit cash cost ($/ton), weighted by prior-year quarter. Point estimates for DDA&A ($700m), interest ($215m) and tax ($340m) come from the company's projected Adj. EBITDA bridge. The SAG guide is split evenly between quarters.
- **Balance sheet, cash & capital:** Notes ladder, a %-refinanced input, and CP/revolver to minimum cash. Buybacks plug to a leverage floor (company target 2.0–2.5x). Dividends = DPS × opening shares. Vulcan retires repurchased shares, so their cost goes to retained earnings; legacy treasury stock appears only before 2009. Leverage on annualised 1H EBITDA does not match the company's 1.7x TTM.
- **Valuation:** $243, per the user. NOPAT = (Adj. EBIT − adjusting items) × (1 − t). P/E 28x Base. A company-published ROIC (Adj. EBITDA / average IC) is shown as a memo row.
- **Reusable lessons:**
  - [calibration] Apply every guided driver first, then put the calibration Δ on the one unguided or least-specific driver (here unit cash cost).
  - [calibration] Take forecast point estimates (DD&A, interest, tax) from the company's projected EBITDA→NI outlook bridge where one is published.
  - [QA] A definition change part-way through a year breaks Σ Q = FY. Exempt that measure and year in check_data and comment the cell.
  - [build] When divested revenue is undisclosed, base Q3/Q4E on prior-year quarter × (1 − divested share input), labelled as an estimate.
  - [bridges] When a company re-states an adjusted figure in a later release, keep the in-force original and quote the restated value in the comment (FY2011 440.4 vs 351.8).

## Welding & fabrication

### LECO — Lincoln Electric Holdings (MLM template; two builds: LECO builder-tools, LECO2 standalone; US GAAP as reported / USD / Dec FY)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 quarterly, as originally reported. 2-for-1 split May-2011: per-share data and pre-split share counts restated (×2 shares, ÷2 DPS). Current 3 segments (Americas Welding, International Welding, Harris) from Q1/16; LECO recast only FY2013 and Q1/14–Q3/15 (8-K 10-Feb-2016), so the Q1–Q4/13 cells are left blank. LECO2 derives Q4/15 on the new basis as FY15 recast (Q4/16 release) − 9M/15 recast. Legacy 5-segment structure (2009–Q4/15) and NA/Europe/Other Countries (2006–08) are kept as memo.
- **Operating build:** segment net sales = prior-year × (1 + volume + price + acquisitions + FX), using the company "Change in Net Sales by Segment" table (USD thousands ÷ prior-year segment sales). HPG "price" is mostly silver/copper pass-through (+37.5% 1H/26), so Base sets it to ~0%. In 2016, Americas Welding price as published includes Venezuela hyperinflation (+15.4%), offset by FX (−17.7%). Acquisition anniversaries are pro-rated by month (Alloy Steel: one month in Q3/26E).
- **Bridges & definitions:** three bridges: OI → adjusted OI; NI → EBIT → Adjusted EBIT (segment profit; EBIT = OI + other income, plus equity earnings while reported); NI → adjusted NI/EPS. Adjusted EBITDA is model-only (LECO publishes none). Adjusted OI for 2006–08 is n/p, or taken from release narrative / 10-K MD&A. Before ~2018 LECO showed special items after tax only, so the tax effect is derived as published adjusted NI − NI − pre-tax items − discrete tax − NCI share. 2009 Jin Tai items were disclosed after tax only and are used as pre-tax (±$0.3m residual).
- **Data quirks & corrections:** in 2009–15 the 10-Q balance sheets fold goodwill/intangibles into other assets; LECO2 takes Goodwill from XBRL. Q1/13 DPS = $0 because the dividend was accelerated into Dec-2012. Interest income was a separate line to 2017/2022 and has been netted since.
- **Calibration & scenarios:** guidance is given on the call only (not in the 8-K), so it is marked unverified. Two anchors: (1) a uniform volume Δ solving FY26 net sales growth to "low double-digit"; (2) a uniform margin Δ solving 2H/26 adjusted profit = 2H/25 + guided incremental margin (mid-20%) × Δ 2H sales. LECO2 adds the 10-Sep-26 Jefferies "low 20s" update and the RISE 2030 targets as memo rows.
- **Balance sheet, cash & capital:** private-placement notes with a scheduled ladder (2028/29/30). Revolver ("amounts due banks") to minimum cash; 2026E revolver change keyed to the reported 30-Jun-26 balance. Buybacks plug to a net-debt/EBITDA floor. 2H/26 buybacks are a scenario input.
- **Valuation:** $275.54 (6-Oct-26, via web search). The DCF deducts rationalization and transaction costs as cash items; adjusted EBIT already expenses SBC and amortization.
- **Two builds compared:**
  - Margin forecast: LECO builds 2027E+ adjusted EBIT from a Δ bridge (price $ × fall-through + volume $ × incremental + (acq+FX) $ × prior margin), so margin is an output. LECO2 uses per-segment margin levers (AW_mgn/IW_mgn/HPG_mgn).
  - Margin denominator: LECO uses total segment sales including inter-segment (company basis); LECO2 uses external sales.
  - The builds contradict each other on three facts: the label cut-over ("EBIT, as adjusted" until 2019 vs until 2017), Venezuela deconsolidation (Q4/15 vs Q2/16) and the split date (27 vs 31-May-2011).
  - Rate inputs also differ: 4.16% effective rate vs 4.57% coupon; tax 23.5% vs 23%; capex 2.7% vs 2.5%.
  - RONTA: LECO2 deducts goodwill and intangibles; LECO leaves them inside other assets.
  - LECO's Bull-Base-Bear P/E comment still quotes MLM ("≈28x … at $518.70").
- **Reusable lessons:**
  - [extraction] When the issuer recasts years but not quarters, derive the missing Q4 as FY recast − 9M recast and leave unrecast quarters blank. Don't mix bases.
  - [calibration] When guidance is an incremental margin rather than a profit level, set the target as prior-year half + incremental × Δ sales and solve the margin Δ.
  - [build] Treat metals pass-through "price" separately from real pricing in scenario levers.
  - [QA] When two builds of the same company disagree on a dated fact, resolve it from the filing before reuse.
  - [basis] State whether segment margins are on total or external sales; it changes the history and the levers.

### ESAB — ESAB Corporation (MLM template, US GAAP / USD / Dec FY, fiscal quarters end on the Friday nearest quarter end)
- **Coverage & basis:** spun from Colfax on 4-Apr-2022. 2019–Q1/22 are on the carve-out (combined) basis from the Form 10 (10-12B/A, 17-Mar-2022), CIK 0001877322. The pre-spin Colfax "Fabrication Technology" segment (2012–21, Colfax CIK 0001420800) is memo only and flagged as not comparable; Charts also mixes the two bases.
- **Operating build:** two segments (Americas; EMEA & APAC). Growth = organic + acquisitions + FX (ESAB gives no price/volume split). The 2027E+ Δ adjusted-EBITDA bridge is organic $ × incremental margin (30–35%) + FX $ × prior margin. Russia is tracked separately because headline metrics are "core" (ex-Russia, from Q2/22).
- **Bridges & definitions:**
  - NI (cont. ops) → EBITDA → adjusted EBITDA → core adjusted EBITDA → adjusted EBITA.
  - NI → adjusted NI → core adjusted EPS, with MCPS dividends added back and shares if-converted.
  - Definition flags: separation costs added back 2022–23; performance option awards added back from 2026.
  - 2019–20 "Other" line = balance between the Form 10 components and published adjusted EBITDA (carve-out allocations).
  - Tolerated residuals: ±0.2 in 2021 quarters (release rounding); ±$0.01–0.03 EPS because the company builds adjusted EPS from rounded per-share items.
- **Deals & special blocks:**
  - Eddyfi ($1.45bn, closed 1-Jun-2026). Its June contribution ($21.4m: Americas $9.6m from MD&A, EMEA derived) sits inside Q2/26 segment actuals. It is stripped from the 2026E base before 2027E segment growth, and Eddyfi is modelled separately from Q3/26E.
  - Eddyfi standalone history is IFRS (8-K/A), memo only.
  - PPA from the 10-Q Note 3, with amortization by intangible class (backlog $17m/2y ends May-2028) and a $5.9m step-up split June / Q3.
  - The EWM anniversary is day-weighted (49/91 days).
  - Asbestos from divested Colfax businesses runs through disc ops.
- **Calibration & scenarios:** the FY26 outlook includes Eddyfi. Two Δs: organic growth → core sales growth (11–14%), and legacy margin → core adj. EBITDA ($615–625m). Core adjusted EPS is memo.
- **Balance sheet, cash & capital:** 2029/2031 notes, TLA and revolver (debt carried at face, with a held deferred-fee carrying adjustment). $175m 6.50% MCPS converts ~Jun-2029 at the mid-ratio (1.35m shares). No 2H/26 buybacks (deleveraging). Working capital is sized on pro forma full-year sales, including Eddyfi's pre-closing days.
- **Valuation:** $69.94 (3-Oct-26). EV deducts NCI plus net asbestos (~$55m). DCF opening IC adds the Eddyfi consideration. EV/EBITDA uses 2026E pro forma for the full Eddyfi year. The Bull-Base-Bear P/E comment and the snapshot comment ("Model rows 290–292 … Model!CF2") are leftovers from the template/LECO, and the switch cell is wrong (ESAB's switch is AT2).
- **Reusable lessons:**
  - [build] When a deal closes inside the last actual quarter, record its stub contribution as a memo row and remove it from the base before applying organic growth.
  - [build] Pro-rate acquisition anniversaries by days consolidated, not by whole quarters.
  - [basis] Spin-cos: carve-out years go in the main columns; the parent's segment goes in a memo under the parent's CIK, explicitly marked not comparable.
  - [bridges] Where the company headline excludes a geography ("core"), carry the excluded slice as its own rows through every bridge.
  - [BS/CF] Size year-end working capital and leverage EBITDA on a pro forma full-year basis in the deal year.
  - [valuation] Treat legacy liabilities (asbestos net of insurance) as debt-like in the EV bridge.

## Transportation & logistics

### TFII — TFI International (Moog-based parameterized generator, IFRS as filed in 40-F / USD millions / FY Dec)
- **Coverage & basis:** FY19–FY25 annual, quarterly FY21Q3–FY25Q3 (from EDGAR IFRS XBRL company facts, CIK 0001588823, plus 6-K MD&A exhibits). EDGAR has nothing before FY19 because the NYSE cross-listing came in late 2020. Pre-FY19 history is on SEDAR, which is blocked. TFI switched from CAD to USD reporting in the FY20 40-F. FY20Q1, FY20Q2 and FY21Q1 have no MD&A exhibit on EDGAR. FY19 was loaded only so the template's FY20 y/y formulas have a denominator.
- **Operating build:** a legacy 4-segment block (Package & Courier, LTL, TL, Logistics; FY19–FY23) and a current 3-segment block (FY24+). P&C was folded into LTL in the FY24 40-F; the FY23 restated comparative confirms this, with LTL revenue up ~$580M, which equals prior-year P&C. FY24 y/y cells reach across into the legacy block, with P&C added back to LTL. Segment financials come from the "Segment Reporting (Details)" R-files, which are in $ thousands. Quarterly KPIs (rev/cwt, shipments, tonnage, truck count, rev/truck/week, owner-operators, OR%) are parsed from the MD&A narrative. The forecast is (1+volume y/y)(1+yield y/y)−1 per segment and scenario.
- **Bridges & definitions:** TFI discloses no GAAP→adjusted bridge components, so Adj EBIT % and incremental margin were repointed from the empty adjusted-OP row to GAAP EBIT. COGS, R&D, SG&A, backlog, DIO and DPO were left blank because the IFRS taxonomy uses materials & services, personnel, other opex and D&A instead.
- **Data quirks & corrections:** FY24 `CashAndCashEquivalents` is XBRL-tagged as 0. FY21/FY22 `FinanceCosts` are sign-flipped (abs() applied). Standalone `Goodwill` is tagged only through FY22 and is then merged into `IntangibleAssetsAndGoodwill`. Moog template residue survived throughout the workbook: Moog source comments on segment, bridge, BS and price rows; "A&D / F-35" DCF rationale; a $310 price in the reverse-DCF text; and a note that the "CD column appears mis-aligned by one segment block".
- **Calibration & scenarios:** LT margin anchors (LTL 15% op margin / 85% adj OR; TL ~12%; Logistics ~9–10%) set the Base end-point and the Bull ceiling. Q1/26 actuals were 4.7% / 8.3% / 8.9%. These targets come from prior calls and cannot be verified on EDGAR (transcript hosts are blocked). Corporate cost ramps 3%/yr off the FY25 gap between segment EBIT and consolidated EBIT.
- **Balance sheet, cash & capital:** cash is a literal plug (Cash = TL&E − non-cash assets), which exposed a FY26E gap of −$126M. Buybacks = −MIN(30% × FCF, |FY25 buyback $226M|), because Q1/26 buybacks were $0 vs $56M a year earlier. Dividends = DPS × diluted shares, with DPS +4%/yr.
- **Valuation:** share price is a CLI parameter ($150). The DCF uses a 10-year fade (FY31–40) and a Mauboussin block, but its rationale text was still Moog's.
- **Reusable lessons:**
  - [extraction] Don't take XBRL company facts on trust for IFRS filers. Tags can be zero (cash), sign-flipped (finance costs) or discontinued and merged (goodwill). Tie each fact to the face statement.
  - [sources] For a foreign filer, EDGAR history starts at the US listing. Record the reporting-currency switch date and keep an FX reference series (BoC IEXE0101 stitched to FXUSDCAD) for any pre-switch data entered by hand.
  - [basis] When a segment is absorbed into another, prove it with the restated comparative (Δ = absorbed segment's prior-year revenue) and compute y/y across blocks with the absorbed segment added back.
  - [QA] Dump every cell comment, note and DCF text cell and grep for the template company's name, programs and prices. In TFI, hundreds of Moog comments survived a "stripped" template.
  - [calibration] Label LT targets that come from calls rather than filings as unverified in the sheet itself.

### ODFL — Old Dominion Freight Line (MLM template, US GAAP / USD / Dec FY)
- **Coverage & basis:** FY2006–12 annual, quarterly Q1/13–Q2/26. All periods are as originally reported. Split restatement by document filing date covers three 3-for-2 splits (2010, 2012, 2020) and a 2-for-1 (2024), with cumulative factors ×1/6.75, 1/4.5, 1/3, 1/2. Operating statistics are on the total-tons basis to 2013 and LTL from Q1/14. The 2014 releases restated 2013 to the LTL basis, but the model keeps the originals and flags the switch with a "statistics basis" definition row. The LTL / other services split exists only from 2019.
- **Operating build:** Work days × tons/day → tons; × 20 cwt × rev/cwt (ex-fuel + fuel surcharge) → statistics-basis revenue. Add a "revenue-recognition / undelivered-freight adjustment" (reported − statistics basis, which includes other services before 2019) to reach reported revenue. There is a volume / ex-fuel yield / fuel bridge with a Σ check. Cost is an operating-ratio build across nine expense lines as % of revenue. `workdays.py` reproduces every published work-day count (weekdays less 7 named holidays) and fills the unpublished years.
- **Bridges & definitions:** ODFL publishes no non-GAAP measures, so every bridge is a model definition. Adj. EBITDA excludes disposal gains (from the cash-flow statement) and only the one-offs ODFL itself quantified: Q2-07 −$2.0m pricing resolution, Q4-17 +$9.8m TCJA bonus, and Q3-22 −$15.8m SWB reduction. Adj. EPS tax-effects these at the ETR excluding discretes and removes the Q4-17 $104.9m DTL revaluation. The checks run against **XBRL facts** (OperatingIncomeLoss, NetIncomeLoss, D&A, GainLossOnSale), using the earliest-filed fact, rather than against a published adjusted figure.
- **Data quirks & corrections:** The XBRL disposal gain/loss sign convention changed in 2019, so that check compares absolute values. XBRL D&A is the cash-flow D&A, which differs from the IS by <$0.05m. Condensed 10-Q cash-flow statements lump working capital with other items. Tons/day not published in 2014–15 and 2018–19 is derived as tons ÷ work days.
- **Calibration & scenarios:** There is no guidance. Q3/26E is anchored to the 3-Sep-26 Item 7.01 mid-quarter update (Aug tons/day −0.9%; QTD rev/cwt +11.3%, +4.8% ex fuel), and the fuel surcharge is implied from the two. Q4 tons/day and yield, and the Q3/Q4 OR, use 2016–25 sequential seasonality: best / average / worst for Bull / Base / Bear. The best Q2→Q3 case is the 2020 COVID rebound (−332bp; −166bp excluding it). A uniform proportional shift on the seven variable cost ratios hits the OR target. 2027E+ uses an OR lever, with variable lines scaled to the FY26E mix.
- **Balance sheet, cash & capital:** Debt is minimal ($20m Series B, due May-27; $400m revolver undrawn). Buybacks plug to a **scenario target cash balance** (Bull $150m / Base $250m / Bear $400m) rather than to leverage. The 2H/26 buyback is phased ¼ in Q3 and ¾ in Q4 in WASO. Repurchased shares are cancelled, so their cost goes to retained earnings. 2026E is rolled forward from the 30-Jun BS.
- **Valuation:** Price $198.39 = the latest observable EDGAR price (a Form 4 sale on 25-Aug-26). Net cash; capex is gross of disposal proceeds.
- **Reusable lessons:**
  - [build] For LTL carriers, carry a statistics-basis → reported revenue adjustment row; the KPIs exclude undelivered-freight revenue.
  - [tooling] Rebuild the company's work-day calendar in code and verify it against every published count before using it to fill gaps.
  - [bridges] With no non-GAAP published, adjust only for items the company quantified itself, and check bridge inputs against XBRL facts (absolute values where tag signs flip).
  - [calibration] With no guidance, use the mid-quarter update for the current quarter and min / mean / max historical sequential change by scenario. Flag outlier years (COVID) in the note.
  - [BS/CF] For net-cash companies, plug buybacks to a scenario target cash balance instead of a leverage floor.
  - [QA] The Bull-Base-Bear P/E comment still quotes MLM ("MLM has traded at ~25–35x … $518.70"). Grep every sheet's comments for template-company text.

### SAIA — Saia, Inc. (MLM template, US GAAP / USD / December FY)
- **Coverage & basis:**
  - FY2006–12 annual and quarterly from Q1/13 through Q2/26, continuing operations; Jevic was sold Jun-06 and shown as disc ops to 2010.
  - 3-for-2 split May-13.
  - ASC 606 adopted 2018, with 2017 as reported.
  - FY2008 is taken from the 10-K because the Q4/08 release pre-dated the $35.5m goodwill impairment.
  - From Q1/18, weight-priced TL is included in the LTL statistics, a basis break. Company-reported change % memos are used for y/y across it.
  - CIK 0001177702.
- **Operating build:**
  - Tonnage/workday × workdays; shipments = tonnage × 2,000 ÷ weight/shipment.
  - Core rev/cwt ex-fuel = core price (GRI + renewals) − weight-mix elasticity (0.75x assumed vs ~1.3x implied in Q2/26).
  - Fuel surcharge = DOE diesel × Saia table ($1.25 base, +0.5% per $0.05; program revised 18-Jan-16, applied to 2016+ only) × capture ratio (trailing-4Q ≈ 0.74; range 0.69–0.77).
  - Other revenue as % of LTL.
  - The cost build follows the reported lines: SWB per shipment; PT %; FOS = prior × ex-fuel growth + 0.31 × Δ surcharge revenue (fuel pass-through calibrated on Q2/26); D&A as % of opening net PP&E.
- **Data quirks & corrections:**
  - Rev/cwt ex-fuel is reported only for 2006–Q3/07 and from 2020. Other years are derived as all-in × (1 − fuel %), about ±1% on the overlap years.
  - Q4 fuel % = (FY% × FY rev − ΣQ1–Q3) ÷ Q4 rev.
  - DOE diesel quarterly averages come from Knight-Swift 10-Qs/10-Ks (cross-checked to Heartland and Marten), with Q4 = 4×FY − ΣQ1–Q3. Q3/26 is the 13-week EIA average.
  - Quarterly SBC for 2013–17 = annual ÷ 4.
  - Saia's tariff site was unreachable, so the table parameters are flagged "verify".
- **Bridges & definitions:** adjusted OI/OR follows the company's ad-hoc exclusions: integration (2006–07), goodwill impairment (2008), the 2009 vacation-policy benefit (commentary only), and terminal-sale gains net of RE impairment (Q3/21, Q3/25; 9M-only publication). Adj. EBITDA is model-defined because Saia publishes no EBITDA. Adjusted EPS is published only when items exist (Q4/17 Tax Act −$34m). The ETR on adjustments is bounded 15–40%.
- **Calibration & scenarios:**
  - The OR guidance is the anchor: Q3/26E = Q2 OR + guided sequential change (~+100 bp); Q4/26E solves FY OR = FY25 adjusted OR 89.6% − guided improvement (Base = low end, 100 bp).
  - SWB/shipment is the balancing line, shown as a % shift vs run-rate.
  - Q3 tonnage is the Jul–Aug interim 8-K figure (+8.3%).
  - Diesel is held near spot in all cases, a pass-through rather than a scenario call.
- **Balance sheet, cash & capital:**
  - $100m 6.09% PGIM notes plus the revolver to minimum cash; the company runs lean cash ($19.7m).
  - Unused-commitment and LC fees are a separate input.
  - No active buyback (the last was 2007); the leverage floor is net debt 0x Base and 0.5x Bull.
  - PP&E is kept at cost less accumulated depreciation.
  - Deferred tax is a share of tax expense.
- **Valuation:** $350, user-provided. Net capex in UFCF. The BBB carries both a Saia P/E comment (G26) and a stale MLM one (N26, $518.70).
- **Reusable lessons:**
  - [build] Model fuel surcharge as diesel × the carrier's published table × an empirical capture ratio, and model the fuel cost side as a pass-through coefficient calibrated on a recent y/y quarter.
  - [sources] When DOE/EIA isn't directly fetchable, take quarterly diesel averages from peer carriers' 10-Qs that print them (Knight-Swift; cross-check Heartland/Marten).
  - [calibration] For OR-guided companies, solve on OR and make the largest controllable cost line (SWB/shipment) the plug, showing the implied shift for reasonableness.
  - [basis] Across a KPI-definition break (TL folded into LTL), compute y/y from the company's like-for-like change memos rather than from level series.
  - [extraction] Prefer the 10-K over a release that pre-dates a year-end charge (goodwill impairment booked after the release).

### XPO — XPO, Inc. (MLM template, US GAAP / USD / December FY)
- **Coverage & basis:** history is re-based to Q1/22–Q2/26: GXO spun Aug-21, intermodal sold Mar-22, RXO spun 1-Nov-22. The 2022 P&L, segment, non-GAAP and CF data come from the recast continuing-operations comparatives in the 2023 releases, which also adopted the natural-expense income statement. The balance sheet starts at 31-Dec-22 because Q1–Q3/22 included RXO. 2022 y/y KPI changes come from company-reported change %, since the 2021 operating data is not carried. CIK 0001166003.
- **Operating build:**
  - North American LTL: pounds/day × working days ÷ 100,000 = cwt; × yield ex-fuel; × a "revenue recognition & other" ratio (in-transit deferral, accessorials) that ties statistics to reported revenue.
  - Fuel surcharge revenue as % of ex-fuel revenue (held at Q2/26 28.2% for 2H, then the 2023–25 average).
  - Adjusted OR lever.
  - Volume/yield revenue bridge, with yield as the residual.
  - Europe: USD growth including FX translation, and margin.
  - Corporate: run-rate cost.
  - Monthly LTL operating 8-Ks (Item 7.01) feed the Q3 tonnage input (Aug-26 +3.7%).
- **Bridges & definitions:**
  - Adjusted EBITDA includes pension income (other income) and real-estate gains. LTL adjusted OI excludes both under the current definition.
  - The company reconciliation started from continuing-ops NI in 2022–24 and from NI in 2025+; a basis-difference row handles this.
  - Adjusted EPS check tolerance is ±$0.015, because XPO uses unrounded shares and releases print millions.
  - Adjusted diluted shares include anti-dilutive awards in loss periods.
  - FCF (CFO − capex + proceeds) was published only 2022–1H/23.
  - The FY2021 LTL target base ($62m real-estate gains and pension included) is kept "as first published" for the 2021–27 CAGR target memos, even though definitions have since changed.
- **Calibration & scenarios:** XPO gives planning assumptions, not revenue/EBITDA/EPS guidance (capex $500–600m, interest $205–215m, ETR 23–24%, ~118m diluted shares). The 2H build uses prior-year quarter + Q2 y/y OR improvement (−300 bp); nothing is solved. Levers: LTL_vol, LTL_yield, LTL_OR, EU growth and margin, leverage floor (an assumption: Base 1.25x, Bull 1.5x, Bear 1.0x; no published target).
- **Balance sheet, cash & capital:**
  - Notes interest on carrying value includes debenture accretion (~7.45%).
  - Term loans are prepayable down to minimum cash before any buybacks; Term Loan B $100m was prepaid Jul-26.
  - Repurchased shares are retired against APIC, with the excess charged to retained earnings once APIC is exhausted.
  - Restricted cash is a memo = CF cash − BS cash.
  - Deferred tax is a share of the provision (82% in FY25 with bonus depreciation, normalising to 25%).
- **Valuation:** $180, user-provided; the Q2/26 buyback average was $205.22. Leases are treated as operating. NOPAT deducts cash adjusting costs. Net capex in UFCF.
- **Reusable lessons:**
  - [basis] After a spin, start history at the first year the recast continuing-ops comparatives cover, and start the BS at the first post-spin balance sheet. Never mix pre-spin balances into the columns.
  - [build] Include a "revenue ÷ (cwt × yield)" ratio row so operating statistics tie exactly to reported revenue.
  - [calibration] When the company gives planning assumptions only, use them as point estimates and info rows rather than forcing a revenue/EBITDA solve.
  - [bridges] For LT targets set on an old base year, freeze the base "as first published" in the scenario table and note that the definitions have since changed.
  - [BS/CF] Follow the company's equity mechanics for buybacks (retire vs treasury; APIC-first then retained earnings) so equity ties.

### CHRW — C.H. Robinson Worldwide (MLM template + RXO PF deal tab, US GAAP / USD / Dec FY)
- **Coverage & basis:** FY2006–12 annual, quarterly Q1/13–Q2/26; Q3–Q4/26E, 2026E, 2027E–30E. Each period is taken as originally reported in its own 8-K Ex. 99.1. Segments (NAST / GF / Robinson Fresh / All Other) start in Q4/16 and are recast to 2014 from the FY2016 10-K and the Jan-2017 Ex. 99.3. Robinson Fresh was folded into All Other in 2019, and the current-basis row = Robinson Fresh + legacy All Other (memo rows, 2014–18). The headline profit line was renamed over time: "gross profits" (to 2008), then "net revenues" (2009–18), then AGP (2019+). GAAP gross profit is presented only from Q1/23 (with 2022 comparatives).
- **Operating build:** NAST = volume y/y × AGP-per-shipment y/y. GF = ocean shipments (the proxy, ~55–60% of GF AGP) × implied AGP/shipment. All Other = growth. Volume KPIs are transcribed from release narrative, which the company rounds to the nearest 0.5%. Pre-2018 NAST volume = AGP-weighted average of the stated TL and LTL rates. AGP/shipment = (1+AGP g)/(1+vol g)−1. Revenue is an output (AGP ÷ AGP margin), because freight pass-through moves revenue far more than AGP. Opex = headcount × cost per head, with a "Lean AI" productivity lever (volume per employee) that decouples headcount from volume; other SG&A is a % of AGP. Service-line AGP is history only, with a Σ check.
- **Bridges & definitions:** There are four bridges: GP→AGP (+ direct software amortization); OI→adjusted OI (the company definition from Q2/22, a model bridge before that); NI→EBITDA→Adj. EBITDA (model definition, SBC not added back); EPS→adj. EPS. Published adjusted figures use the **latest dollar reconciliation that presents each period**: 2023 quarters come from 2024 comparatives, and Q1/23–Q1/25 are derived as 6M − Q2 from the next year's Q2 release. The Q4/23 published $103.2m (original definition) is absorbed by an explicit "other company-defined items" plug row. The Q3/19 Chicago property gain is a *model* item (the company did not adjust it), while the Q2/22 Kansas City gain is a company item.
- **Data quirks & corrections:** Purchased transportation for 2006–08 is not on the face of the statements, so it is derived as revenue − gross profits. Interest expense exists only as release narrative from Q2/20. Retained earnings and AOCI come from XBRL (2008+), and the stock/APIC/treasury line is derived. DPS comes from the XBRL tag, with Q4 = FY − 9M. Repurchases include shares tendered for withholding. A held-for-sale cash line (2023–25) is needed for the cash check.
- **Deals & special blocks:** The RXO PF tab covers: $17.25 + 0.0856 shares, with elections prorated (~57/43); capitalization from the merger agreement (pre-funded warrants and PSUs at max) that reconciles to $5.3bn; the RXO change-of-control put at 101%; the bridge facility; a PPA with intangibles at ~17% of EV (assumption); synergy phasing; and accretion on the **deal definition** (which excludes acquisition amortization). Accretion is shown two ways: vs standalone with buybacks (−3.8%) and "company-style" with no post-2026 standalone buybacks (−2.4%), plus the synergy level needed to break even. RXO history uses the latest-filed values, with FY2021 = the XPO carve-out.
- **Calibration & scenarios:** The anchor is FY26 adjusted OI of $964m–$1.04bn (deck slide, not the release). A uniform Δ on AGP-per-shipment / growth is solved across all segments. The Q3/Q4 opex is the prior-year quarter × 1H y/y. Restructuring is stripped from the 2026E cost-per-head base so it doesn't compound into 2027E+.
- **Balance sheet, cash & capital:** Senior notes have scheduled 2028 maturities; the revolver and receivables securitization are prepayable to a minimum cash balance. Buybacks plug to a minimum of 1.5x net debt/EBITDA. The 2026E buyback column is 2H only. Prepaid/other is the 2026E BS-closing line. Share count is cross-checked to the merger-agreement capitalization rep.
- **Valuation:** Price $151.88 = the 16-day VWAP in the deal press release. The DCF deducts the cash restructuring cost that adjusted EBIT adds back.
- **Reusable lessons:**
  - [build] For brokers and pass-through businesses, forecast the net-revenue measure (AGP) and back out gross revenue through a margin; never drive the forecast off gross revenue.
  - [extraction] KPIs that exist only in release narrative (rounded y/y %) need a quote-level source pack and a note on the rounding convention.
  - [bridges] When the company re-presents prior-year adjusted figures, tie to the latest reconciliation and derive missing quarters as 6M − Q2 from the next year's release.
  - [bridges] Separate "model items" from "company items" within one adjusting row, and say which is which in the cell comment.
  - [build] Strip one-offs (restructuring) out of the base-year unit cost before growing it into the out-years.
  - [valuation] On deal tabs, show accretion both against the standalone with buybacks and on the company's comparison basis, and solve for the synergies/margins needed to hit the company's claim.

### UBER — Uber Technologies (MLM template, US GAAP / USD m / calendar FY)
- **Coverage & basis:** FY2016 (S-1), Q1/18–Q2/26, Q3/Q4-26E, 2027E–30E. IPO 10-May-2019; pre-IPO EPS is on pre-conversion common shares (n/m). 2018–19 revenue is as originally reported ($11,270m / $14,147m, against $10,433m / $13,000m restated in the 2020 10-K for excess Driver payments; no OI effect). Interest income is shown separately for all periods on the 2026 presentation, using XBRL InvestmentIncomeInterest. CIK 0001543151.
- **Operating build:** Gross Bookings (GB) × take rate → revenue. Segment OI = prior year + ΔGB × incremental margin (scenario lever) from 2027E. KPIs: trips = GB ÷ GB/trip; MAPCs = trips ÷ (frequency × months). Freight GB = revenue. Take rate for Q3/Q4 = prior-year quarter × the Q2 y/y take-rate ratio, which carries the 2026 business-model changes (Q2/26: −8pp revenue growth). Corporate G&A and platform R&D are forecast as % of GB.
- **Bridges & definitions:** the segment measure changed from Segment Adjusted EBITDA (to Q4/25, kept as a legacy memo block with a Σ check) to Segment OI (from Q1/26, recast to Q1/24 by 8-K 12-Jan-2026). NI → EBITDA → Adjusted EBITDA → Non-GAAP OI has a "definitional differences" plug used only in published periods. Example: FY24 acquisition and financing costs were $68m in Non-GAAP OI vs $25m in Adjusted EBITDA. Non-GAAP EPS is the company definition from Q1/24; before that the model applies one definition with a 21% tax rate. Non-GAAP NI deducts the Freight Holding contingently issuable shares loss. GAAP G&A is the forecast plug.
- **Data quirks & corrections:** valuation-allowance releases (Q4/24 $6.4bn, Q3/25 $5.0bn) distort the GAAP ETR, so the Non-GAAP ETR is used for NOPAT. Before 2026, the current portion of debt sat inside accrued liabilities. Unallocated revenue and GB rows absorb the 2016–18 splits.
- **Deals & special blocks:** Delivery Hero (switch; assumed close 1-Oct-2027). Inputs come from the 8-K Ex. 99.2 deck (EUR translated at 1.12). The PPA derecognises the 24.8% equity-method stake and $1.64bn total return swaps. Ownership is assumed at 75%. NCI is at offer value. $4.2bn of net debt is assumed. The PPA is illustrative because no offer document has been published. Synergies are >$1.2bn within 18 months.
- **Calibration & scenarios:** Uber guides one quarter ahead. Uniform GB and segment-margin Δs are solved for Q3/26 GB $58.25–60.25bn and the Adjusted EBITDA translation $2.86–2.96bn, then applied unchanged to Q4. Non-GAAP EPS is not forced.
- **Balance sheet, cash & capital:** insurance reserves are driven at 12.5% of Mobility GB (negative NWC). Buybacks = MAX(leverage plug, minimum % of FCF; FY25 ~67%). Prepayable term loans and DH debt are the cash plug. Repurchases are retired against APIC. The interest-income yield includes restricted insurance float.
- **Valuation:** $70.97 from Form 4 code-F withholding prices (16-Sep-2026). Non-operating stakes (Didi, Aurora, Grab) are excluded from IC and added to EV at carrying value. Terminal ΔWC = |NWC| × g, because negative NWC releases cash as the business grows.
- **Reusable lessons:**
  - [calibration] For one-quarter-ahead guidance, solve the guided quarter and carry the same Δ into the rest of the year.
  - [bridges] When two company non-GAAP measures differ, keep a definitional-difference plug that is active only in published periods.
  - [valuation] Strip equity stakes out of IC and the EV bridge, and add them back at carrying value.
  - [BS/CF] Drive float-like liabilities from the volume metric (GB), not from revenue.
  - [basis] Apply a new face-statement presentation (interest income split out) to all history, using XBRL.

## Life sciences & healthcare

### DHR — Danaher (MLM template 6-Oct-26, US GAAP / USD m / Dec FYE, Friday-nearest quarter ends)
- **Coverage & basis:** FY2006–12 annual, then quarterly. The income statement, segments and adjusted EPS use the hybrid recast; BS and CF are as originally reported. A segment-only recast is applied to a year's quarters only when all four quarters have it. Each recast cell's comment quotes the original figures. 2-for-1 split in Jun-2010.
- **Operating build:** Three segments: prior-year quarter × (1 + core growth + FX). Core growth for 2026E = Σ quarterly core increments ÷ FY25. Masimo and StatLab enter core only once owned more than a year (2028E). Segment "other adjustments" are published only for FY24, Q4-24, FY25 and Q4-25. Other quarters are allocated from adjusted-EPS footnotes (per-cell comments) and tie to the FY totals. Diagnostics is shown as legacy with the reported segment as memo. Corporate cost is ~$(90)m a quarter, as guided.
- **Bridges & definitions:** Adjusted EBITDA is a model definition (= adjusted OP + depreciation). Adjusted OP is a company definition introduced in Q4-25 and applied back to 2006. Adjusted EPS: discrete items only to 2014; amortization added from Q1-15 (2015 comparatives restated); a single tax line, discrete tax and investment FV items from Q2-16 / 2018; MCPS if-converted 2019–23; continuing ops from Q4-23. Narrative bridges for 2006–13 are after-tax. Where items are only per-share, $ = per-share × diluted shares. In recast periods the item detail is on the original basis, so a residual row absorbs the difference. Everything ties within ±$0.02. FCF definition: PP&E proceeds are excluded in 2010–12, and continuing ops apply from 2023. Note CF253 says the add-back started "Q1-16" while the flag row says Q1-15.
- **Deals & special blocks:** Masimo stopped filing after closing, so pro forma Q2/26 = Q2/25 × (1 + Q1/26 growth). The 16-day stub is estimated from the published 4.0% acquisition impact on growth (~$92m). The PPA life (~20 years) is implied from the amortization guidance ($1.9bn vs the $1.7bn schedule). StatLab's price is undisclosed: 7.5x (~$2.0bn) is a flagged assumption with a closing switch. The 10-K amortization schedule is published in $bn to one decimal.
- **Calibration & scenarios:** Core-growth Δ is solved to the FY guide (3–4%). The margin Δ is solved to the Q3 adjusted-OP margin guide (~26.5%) in Q3 and to FY adjusted EPS in Q4. Required 2H adjusted OP = required adjusted NE ÷ (1 − adjusted tax) + net interest − adjusted other income. GAAP tax = adjusted tax − tax effect of items.
- **Balance sheet, cash & capital:** Multi-currency notes at carrying amounts with dated maturities. Euro CP to minimum cash. Dividends = DPS × beginning shares to avoid circularity. BS-vs-CF cash differences are disc-ops cash. The deferred-tax benefit on amortization is an input.
- **Valuation:** $221.21 close on 5-Oct-26. NOPAT is taxed on pre-amortization adjusted OP with a depreciation-only add-back. Opening IC = 2025A + Masimo + StatLab.
- **Reusable lessons:**
  - [extraction] Where segment-level adjusting items are published only for some periods, allocate quarterly items from the footnotes that name the segment, comment each cell, and tie to the FY totals.
  - [deals] For a target that stops filing, derive the stub from "acquisition impact on growth" and imply the PPA life from the amortization guidance.
  - [calibration] Back-solve EPS guidance to an operating-profit target in closed form.
  - [basis] Apply a segment-only recast to a year only when all four quarters are recast.
  - [QA] Cross-check modelling-note dates against the definition-flag row.

### TMO — Thermo Fisher Scientific (MLM template, US GAAP as reported / USD m / calendar FY, fiscal quarters end on the Saturday nearest quarter-end)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 quarterly, Q3/Q4-26E, 2027E–30E. All periods as originally reported (no recasts). FY2006 was reported in USD thousands and was converted; it includes Fisher Scientific for only ~7 weeks (merger 9-Nov-2006). CIK 0000097745.
- **Operating build:** four segments from Q1/14 (LSS / AI / SD / LPBS). Revenue = prior-year revenue × (1 + organic + acquisitions/divestitures + FX), with segment organic growth from the 10-K/10-Q MD&A tables (2021+, rounded to whole %). Segment income = adjusted OI (company definition). Laboratory Products & Services was renamed LPBS in Q4/21 and kept as one continuous row. The 2006–13 two- and three-segment structures are a legacy memo block, not recast. Eliminations are forecast as a % of gross segment revenue.
- **Bridges & definitions:** GAAP OI → adjusted OI (Σ segment income), tied to every published reconciliation. Segment-income checks use ±2 because company rounding changed from 2024. GAAP NI → adjusted NI/EPS has explicit rows for (a) a "basis difference: company start vs model" line, (b) equity-method items: investee amortization to 2021, then the full equity in earnings from 2022, (c) disc ops to 2021, (d) NCI adjustments from 2023. TMO publishes no adjusted EBITDA, so model adjusted EBITDA = adjusted OI + depreciation. Depreciation comes from a release footnote ("Consolidated depreciation expense is $x").
- **Data quirks & corrections:** Microbiology Q4/25 = FY $645m − 9M $473m. The microbiology closing date was not filed on EDGAR, so a days-owned input is used (assumed 31-Aug-2026 = 65 of 91 days in fiscal Q3). SBC comes from XBRL ShareBasedCompensation. Cash includes restricted cash from 2017.
- **Deals & special blocks:** Solventum P&F run-rate = the 10-Q acquisition contribution (+9% of Q1/25 LSS) ÷ 3 months. Clario run-rate = the +6% LPBS contribution × Q2/25 × 4. Clario's PPA amortization is added on top of the FY25 10-K schedule because the deal closed after year-end. The microbiology sale gain is booked in "restructuring and other" (excluded from adjusted). Held-for-sale assets and liabilities are removed from the 2026E BS, and the $50m seller note goes to other assets.
- **Calibration & scenarios:** FY26 guidance was given on the call, not in the 8-K. Two Δs are solved: uniform organic Δ to revenue $47.4–48.1bn, and uniform margin Δ to adjusted OM (+80bp ±10bp). Adjusted EPS is an output, not forced. A third calibration solves 2H "other operating items" so that FY26 FCF = $6.9–7.4bn, offset in other current liabilities. The FX input (−0.5%/−0.75%) reconciles to the mid-point.
- **Balance sheet, cash & capital:** net interest includes ~$390m p.a. of swap income in interest income. The $4bn FY26 buyback was fully executed in 1H, so the 2026E buyback row is 2H only. CP is the plug to minimum cash. Buybacks resume above a net-debt/EBITDA floor (3.5x post-Clario → ~2.5x). DPS × beginning shares avoids circularity. The deferred-tax unwind is set at 25% of amortization.
- **Valuation:** $676.76 (5-Oct-2026). UFCF on adjusted OI (amortization excluded) adds back depreciation only, and deducts restructuring and integration costs as cash costs. The microbiology gain is excluded. Opening IC adds the $9.1bn Clario price. EV/EBITDA is on 2026E pro forma (Clario's 12 pre-close weeks).
- **Reusable lessons:**
  - [calibration] When guidance is call-only, record that fact and the call date in header row 3 and in the outlook block.
  - [calibration] Calibrate FCF too when it is guided, through one "other operating" plug with an explicit BS offset.
  - [build] Infer the run-rate of an acquisition from the 10-Q "acquisitions %" contribution × the prior-year segment revenue.
  - [bridges] Keep equity-method results as a separate bridge line, because the company switched from investee amortization only to the full result in 2022.
  - [BS/CF] For an undisclosed divestiture closing date, use a days-owned input in the fiscal quarter, and note the fiscal quarter's start and end dates.

### STE — STERIS plc (MLM template, US GAAP / USD m / FY ends 31-Mar)
- **Coverage & basis:** FY2012–21 annual, Q1/22–Q1/27, Q2–Q4/27E, FY28E–31E. Three registrants: CIK 815065 to FY2015, 1624899 for FY2016–19, 1757898 after. Hybrid basis: as reported through FY2022; FY2023+ continuing operations (Dental moved to disc ops in the Q4 FY24 release; sold Sep-2024). For the FY2023 recast quarters, R&D, restructuring and other are scaled to the restated FY totals, with SG&A as the plug. Q1–Q3 FY24 come from the FY25 comparatives.
- **Operating build:** segment × revenue type (Healthcare and Life Sciences: capital / consumables / service; AST: service / capital), with a Σ check to published segment revenue. Healthcare Products + Healthcare Specialty Services (FY16–20) are combined. Corporate costs are reported separately only from FY2019. FY2012–15 segment OI uses the adjusted figures from the non-GAAP tables, and corporate is the plug. The growth bridge (as reported → organic → constant-currency organic) is published from FY2017.
- **Bridges & definitions:** GAAP OI → adjusted OI, plus an adjusted gross profit sub-bridge. The definition-flag row marks each structural change in the column where it takes effect. NI → EBITDA → adjusted EBITDA is a model definition: adjusted OI + depreciation and other amortization, with a check. Adjusted EBIT is full-cost (after acquired-intangible amortization) for ROIC. In the EPS bridge, the historical tax effect is derived as published adjusted NI − GAAP NI − pre-tax items (FY2012–15 items are shown net of tax). The originally reported adjusted EPS including Dental is rebuilt from the recast adjusted disc-ops income and checked.
- **Data quirks & corrections:** in Q1 FY22 (GAAP net loss), adjusted EPS uses diluted shares through a manual input row. STERIS's own FY2023 recast has a $0.4m residual in the amortization split. From Q1/26, releases are in USD m to one decimal, so checks use ±0.15. Goodwill and intangibles are combined in FY12–15 releases and split with 10-K goodwill.
- **Deals & special blocks:** PPA table with columns for Synergy (Nov-15, preliminary), Cantel (Jun-21; $721m debt assumed and repaid) and BD instruments (Aug-23). Item 2.05 restructuring: $55–70m through FY2030, phased as an input.
- **Calibration & scenarios:** revenue Δ makes FY27 revenue = FY26 × (1 + 7.0/7.5/8.0%). Margin Δ is solved to adjusted EPS $11.10/11.20/11.30 via required OI = (NI − Q1 actual + NCI) ÷ (1 − t) + non-operating. GAAP EPS and FCF (~$800m) are information rows.
- **Balance sheet, cash & capital:** private-placement notes are repaid at maturity, and the 2031 public notes are refinanced at ~5%. The revolver is the plug. From FY28E, buybacks plug to a maximum leverage. Working-capital drivers are set at fiscal year-end (31-Mar) levels, because Q1 receivables are seasonally low.
- **Valuation:** $211.07 (5-Oct-2026). Discount dates are set to 31-Mar. UFCF is full-cost adjusted EBIT + total DD&A − acquisition, integration and restructuring cash costs. NCI (~$14m) is deducted.
- **Reusable lessons:**
  - [basis] When a recast gives only totals, scale minor opex lines to the restated totals, let SG&A absorb the residual, and comment it.
  - [bridges] Where the company shows items only net of tax, derive the tax line as published adjusted NI − GAAP NI − pre-tax items.
  - [QA] Widen the check tolerance from the column where the issuer's rounding unit changes, and flag it in the definition row.
  - [BS/CF] Set forecast working-capital days from fiscal year-end balances, not annualised quarters.
  - [QA] The BBB tab carries the same MLM N26 and P40 ("Model!CF2") comments as CTAS; the STE switch is AU2.

## Business, environmental & marketplace services

### CTAS — Cintas, incl. UniFirst block (MLM template, US GAAP as reported / USD m / FY ends 31-May)
- **Coverage & basis:** FY2006–12 annual, Q1 FY13–Q1 FY27 quarterly, Q2–Q4 FY27E, FY28E–31E. Quarters as originally reported. Per-share data and shares are restated for the 4-for-1 split (11-Sep-2024). 86 releases were used. CIK 0000723254; UniFirst CIK 0000717954.
- **Operating build:** UR&FS / FA&S / All Other from FY2016 (FY2015 recast). The legacy four segments to FY2015 are memo rows. Segment build: organic growth → revenue → gross margin → S&A → segment OI. "Uniforms and other rental items in service" is a Cintas-specific working-capital asset, driven as % of UR&FS revenue.
- **Bridges & definitions:** Cintas publishes no adjusted EBITDA. Model EBITDA ties to the FY2012–14 company EBITDA (from the Debt/EBITDA tables, which exclude interest income). Adjusted EPS is published only when special items occur (FY09–11, FY14–15, FY17–23, FY26+). The definition row stores the company's exact wording per column (e.g. "EPS cont. ops excl. G&K expenses and ASU 2016-09 benefit"). An "other company-defined items & rounding" plug covers ASU 2016-09, the two-class method and the Q3/22 equity-method tax benefit. The tax on adjusting items uses the period ETR, bounded at 15–40%. Organic growth (net of acquisitions, FX and workdays) is tied to the published figure.
- **Data quirks & corrections:** Q3/26 UniFirst costs ($1.1m) sat in S&A as first reported but became a separate line later. Dividends were annual (declared in Q2) until FY2020 and quarterly from FY2021 (special in FY2015, catch-up in FY2021). FY2007–09 organic growth was not disclosed.
- **Deals & special blocks:** UniFirst toggle and closing date (31-Dec-2026) feed days consolidated. The standalone run-rate = UNF LTM built from 8-K quarters, because UNF's August FY was not yet filed. UNF costs are re-mapped to the Cintas presentation: GM = 63.3% COGS ex-D&A + ~85% of D&A. The 424B3 PPA gives goodwill $2.85bn and intangibles $1.29bn (customer relationships /15y, trade names /3y → $98m, then $83m), plus a net PP&E step-up of +$0.4m. Synergies of $375m are phased 25/55/85/100% with a 65/35 COGS/S&A split. Integration cost of $350m is an assumption scaled from G&K.
- **Calibration & scenarios:** guidance excludes UniFirst, so legacy-only rows are calibrated and checked. Q1/27 had 66 vs 65 workdays, so the Q1 extra-day effect is stripped from the trend before projecting Q2–Q4. Adjusted OI is back-solved from EPS guidance as EPS × guidance shares (404.3m, ex-future buybacks) ÷ (1 − 20.4%) + $103m net interest.
- **Balance sheet, cash & capital:** $2.8bn acquisition debt at 5%. Buybacks are paused after the $229m executed to 22-Sep (input). From FY28E, buybacks plug to 1.25x. Capitalized contract-cost additions are assumed equal to their amortization (cash-neutral). Working capital is sized on pro forma full-year revenue, and acquired NWC is excluded from ΔNWC.
- **Valuation:** $198.95 from a Form 4 phantom-unit credit price (15-Sep-2026), because no market feed was available. UFCF deducts all D&A, including PPA amortization. Opening IC adds the $5.35bn consideration.
- **Reusable lessons:**
  - [calibration] Remove known calendar effects (workdays, 53rd week) from the YTD trend before projecting the rest of the year.
  - [calibration] When a pending deal is outside guidance, calibrate and check a legacy-only memo series, then add the deal block on top.
  - [build] Re-map a target's cost presentation to the acquirer's (D&A inside COGS) before applying margins.
  - [bridges] For sporadic adjusted EPS, populate the published and check rows only in published periods, and quote the definition text per column.
  - [QA] The Bull-Base-Bear (BBB) tab still carries MLM leftovers: column N labels ("attributable to MLM", "LNA"), the N26 P/E comment, and the P40 comment that cites "Model!CF2" and rows 290–292, although the CTAS switch is CK2.

### WCN — Waste Connections (MLM template, US GAAP / USD / Dec FY)
- **Coverage & basis:** FY2006–12 annual, quarterly from Q1/13, as originally reported. There are **two CIKs**: legacy Delaware 0001057058 to Q1/16, then Ontario 0001318220 from Q2/16. Old WCN was the accounting acquirer in the 1-Jun-16 Progressive merger, a net 1:1 exchange. 3-for-2 splits in Mar-07, Nov-10 and Jun-17 are handled with an explicit split-factor row (×3.375 / 2.25 / 1.5 / 1.0). For 2006–08, pre-SFAS 160 pre-tax income is re-presented before minority interest.
- **Operating build:** Service lines are gross of intercompany: collection, disposal & transfer, recycling, E&P (from FY2012, R360), and intermodal & other. Intercompany eliminations are a % of gross (~45–50% of landfill revenue is internalized). Solid waste growth = price/yield + surcharges + volume + recycling + FX + closed operations. A separate MD&A $ revenue bridge has its Q4 = FY − Q1−Q2−Q3. Recycling and intermodal were combined to 2011, so the 2012 y/y is overstated. From Q1/26 the company switched from core price to "yield" and from volume to unit volume; core price is kept as memo. Segments were re-cut in Q1/10, Q2/16, Q3/20 and Q2/23, and Q4 is not derived in re-cut years.
- **Bridges & definitions:** Adj. EBITDA uses the company definition, which was called "adjusted OI before D&A" (FY2008–12) and was not published for 2006–07; it adds back closure/post-closure accretion. Adjusted EPS adds back amortization from FY2012, after-tax only for FY2012–Q2/13, so the bridge has an after-tax item row. **Adjusted FCF** is a third company bridge (CFO ± book overdraft − PP&E capex + disposals + transaction items; landfill land is excluded). Adjusted EBITA is used as the consistent operating measure. Where GAAP is a loss, the company uses diluted shares for adjusted EPS.
- **Data quirks & corrections:** These are documented as known check residuals rather than forced. FY2008: the company figure starts from net income restated for FSP APB 14-1 ($102.9m vs $105.6m). Q3/15: the release preceded the $494m impairment booked in the 10-Q. FY2010: CFO was restated $328.4m → $332.2m. Q4 adjusted FCF was published only for Q4/16–Q4/17. The 2016–18 cash check differs by held-for-sale cash.
- **Calibration & scenarios:** FY26 outlook: revenue $10.02–10.05bn (uniform growth Δ), Adj. EBITDA $3.33–3.34bn (cost-ratio Δ), and **CFO $2.63–2.68bn**, which is hit by calibrating 2026E working capital with receivables as the BS plug. Adjusted FCF and NI are memo rows. D&A, amortization and interest are point estimates from the outlook reconciliation, with (FY − 1H) ÷ 2 for Q3/Q4.
- **Balance sheet, cash & capital:** Twelve senior-note tranches with scheduled maturities; the revolver plugs to minimum cash. Buybacks plug to a 2.5–3.0x leverage floor. The dividend is raised each October (+10%). Restricted cash is included from 2018.
- **Valuation:** User price $155. The DCF deducts cash transaction costs, adds back intangible amortization, and treats landfill land capex as capex.
- **Reusable lessons:**
  - [sources] Check for re-domiciles or mergers that change the CIK, and pull both registrants' filings.
  - [bridges] Where an adjusted measure was once presented item-by-item after tax, carry an "after-tax adjustments" row so the bridge still reconciles.
  - [bridges] Write known, explained check residuals (restated starting points, releases issued before a 10-Q impairment) into the check-row note instead of plugging them away.
  - [calibration] If the company guides CFO, calibrate the working-capital line (with one BS plug, e.g. receivables) so CFO hits the end-point.
  - [build] For vertically integrated waste companies, build gross of intercompany and eliminate as a % of gross.
  - [QA] Template leaks survived here too: the DCF says "Rationale (Martin Marietta characteristics)" and the BBB P/E comment quotes MLM's $518.70.

### CLH — Clean Harbors (MLM template, US GAAP / USD / December FY)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 quarterly, as originally reported. Q4 = FY − 9M and CF is de-cumulated from YTD. CIK 0000822818. Segment history is long and messy:
  - Technical / Site Services 2006–08;
  - four to five segments 2009–12 (Eveready, Jul-09);
  - Safety-Kleen acquired 28-Dec-12, giving five to six segments 2013–17;
  - ES + Safety-Kleen from Q1/18 (2017 recast);
  - Safety-Kleen renamed SKSS in Q1/21.
- **Operating build:** ES service lines from the ASC 606 third-party revenue disaggregation (2018+): Technical Services, Field & ER, Industrial & Other, SK Environmental Services ES portion. Adding intersegment revenue gives segment direct revenues; segment Adj. EBITDA = direct revenues × margin. SKSS: SK Oil plus the SK ES portion, with an explicit base-oil spread narrative (the 2026 supply-disruption spike normalises). Corporate costs are % of revenue. KPI memos: incineration utilisation and landfill volumes. Legacy segment structures are kept as memo rows with Σ checks.
- **Bridges & definitions:**
  - Adj. EBITDA definition flags by column: credit-agreement basis → disc ops removed (2009–10) → inventory step-up (2013–14) → goodwill impairment (2014–17) → business-sale gains/losses → SBC added back from Q1/21, with prior years not restated → Kimball start-up costs (Q4/24–Q4/25) → transaction costs (Q4/25).
  - Adjusted EPS was published Q3/14–Q1/24 only; afterwards the model rebuilds it as GAAP + items × (1 − t).
  - Adjusted FCF = CFO − capex + disposal proceeds + excluded strategic growth capex (Kimball, Phoenix Hub, HQ purchase).
- **Deals & special blocks:** ES&H ($305m) and EnviroServe ($470m) were pending and excluded from FY26 guidance, so the model adds them separately:
  - closing dates are model assumptions (1-Sep-26, inferred from notes-release language about revolver draws; 1-Nov-26);
  - days-consolidated rows;
  - run-rate revenue and EBITDA from the deal releases;
  - synergies phased by a DEAL_syn lever;
  - an assumed PPA (receivables ≈ 60 days, PP&E ~35%, intangibles ~25% of consideration);
  - $600m 6.25% 2034 notes from ~1-Oct-26.
  A pro forma full-year Adj. EBITDA memo drives leverage and valuation, and working capital is sized on pro forma full-year revenue.
- **Calibration & scenarios:** a uniform ES/SKSS margin Δ solves legacy FY26 Adj. EBITDA to the guidance end-point ($1,350–1,410m). Guided D&A, accretion, SBC and interest are split evenly as (FY mid − 1H) ÷ 2, and interest adds the Q4 coupon on post-guidance notes. Tax uses the guidance-implied rate (tax $180.5m / pre-tax $686.5m = 26.3%). A Q3 y/y guide (+24–28%) is shown as a memo.
- **Balance sheet, cash & capital:**
  - Environmental-liability roll-forward: + accretion − cash spend.
  - Term loan amortises 1%, with a $600m swap at 3.46% to Sep-27.
  - Revolver to minimum cash; draws above $600m are treated as incremental term debt.
  - Buybacks = max(minimum programme, leverage plug).
  - Repurchased shares are retired against retained earnings.
  - No common dividend.
  - Cash includes restricted cash from 2018 (ASU 2016-18).
- **Valuation:** $321.34 from a Form 4 open-market sale (14-Aug-26), because EDGAR was the only price source reachable. NOPAT deducts SBC and transaction costs because the company's Adj. EBITDA adds them back. Opening IC includes the 2026 deal consideration.
- **Data quirks (QA):** the workbook still carries many MLM-template comments: aggregates tons/ASP, cement, LNA financial statements, "MLM Form 8-K", MLM-basis EBITDA wording, the MLM $518.70 share-price comment on a valuation row, and the CF2 switch comment naming "Other Building Materials, Specialties and LNA". The BBB P/E comment cites MLM as well.
- **Reusable lessons:**
  - [calibration] When guidance explicitly excludes pending deals, calibrate a "legacy" sub-total to guidance and layer the deals on top, with a pro forma memo for leverage.
  - [calibration] For guided cost items, split the 2H as (FY mid − 1H) ÷ 2, then add items announced after the guidance date (new notes coupon) explicitly.
  - [bridges] If a company stops publishing adjusted EPS (CLH after Q1/24), keep the series as a model rebuild and flag the column "not published from …".
  - [valuation] When Adj. EBITDA adds back SBC, deduct SBC (and transaction costs) in DCF NOPAT.
  - [QA] Grep every cell comment and note for template-company tokens (MLM, aggregates, cement, LNA, $518.70). Comment leakage survived QA here even though the cell values were clean.

### CSGP — CoStar Group (MLM template, US GAAP / USD m / Dec FYE)
- **Coverage & basis:** 2006–25 annual and Q1/13–Q2/26 quarterly. History comes from XBRL statements, with 2006–10 from 10-K HTML. Q4 = FY − 9M throughout. The 10-for-1 split (Jun-2021) is applied ×10 to earlier shares. Template columns are not re-based (notes in CF). From Q1-25 the 10-Qs show only total equity; components come from the 10-K. CF cash includes restricted cash from 2020.
- **Operating build:** Current product lines (CoStar / LoopNet / Other CRE / Residential) and CRE / Residential segment Adj. EBITDA come from the Q4-25 recast. Revenue goes back to Q1/23 and segment EBITDA to Q1/24. For 2015–22, legacy lines are mapped approximately, in black font (CoStar Suite + Information Services ≈ CoStar). Legacy product lines and the NA / International segments are kept as memo with Σ checks. KPI: net new bookings (definition varies pre-2016; Q4 often given only for the year). Opening shares come from the 10-Q cover (dei:EntityCommonStockSharesOutstanding).
- **Bridges & definitions:** Only EBITDA was published to 2008. Adj. EBITDA arrived in Q1-10 with FY09 comparatives; HQ costs were added in 2010–11; debt extinguishment moved out later; lessor D&A sits in other income and is excluded from bridge D&A (derived $3–9m a quarter). Adjusted NI is taxed at the company's assumed rate (40% to 2011, 38% 2012–17, 25% 2018–21, 26% 2022+). The model applies 40% in 2006–08, where nothing was published. Non-GAAP NI was not published in the Q4-24 release; the company recast it in Feb-26. It was renamed Adjusted NI in Q4-25. Tolerances: ±1 for whole-$m recast segment data, ≤$0.6m on adjusted NI.
- **Deals & special blocks:** Zonda closed 21-Aug-26 for $800m, after the company's FY26 guidance. It has its own block: standalone ~$170m revenue at 23% margin, 41 days consolidated in Q3, and an estimated PPA (40% intangibles, 10-year life, DTL at 26%) flagged "replace with Q3-26 10-Q". Pro forma full-year Adj. EBITDA and revenue (for DSO) are used for leverage and valuation.
- **Calibration & scenarios:** Calibration runs on "legacy ex-Zonda" memo rows against guidance. Revenue uses sequential growth: Q3 = Q2 × (1 + g + Δ), Q4 = Q2 × ((1+g)² + 2Δ), solved linearly, because y/y comparisons are distorted by Domain / Matterport anniversaries. The margin Δ is per segment and sits in one row: the Q3 column holds the CRE Δ and the Q4 column the Residential Δ. The interest guide predates the Zonda cash outflow. S&M is the GAAP plug.
- **Balance sheet, cash & capital:** 2.80% notes due Jul-2030, refinanced at ~5.5%. Revolver to minimum cash. Leverage floor 0.5x / 1.0x / 0.0x. The 2026E buyback row covers 2H only. ASC 606 deferred commissions are part of working capital.
- **Valuation:** Price $30.78 from a Form 4 director sale on 7-Aug-26. NOPAT uses the company's 26% non-GAAP tax rate (FY25 GAAP ETR 77%). The DCF deducts SBC and acquisition costs. Domain NCI is deducted in the bridge.
- **Reusable lessons:**
  - [calibration] When guidance excludes a just-closed deal, calibrate a legacy memo series and add the deal on top.
  - [calibration] Choose sequential q/q seeds when y/y comparisons are distorted by acquisition anniversaries.
  - [sources] With no market feed, use a dated Form 4 price.
  - [valuation] Use the company's assumed non-GAAP tax rate for NOPAT when the GAAP ETR is distorted.
  - [deals] Estimated PPAs carry a "replace with 10-Q" note and a pro forma EBITDA memo for leverage.

### RBA — RB Global / Ritchie Bros. (HII template → RBA framework, US GAAP 2015+ / USD millions / FY Dec)
- **Coverage & basis:** FY2006–12 annual, Q1/13–Q2/26 (CIK 0001046102). The filings change over time:
  - 2006–15: 40-F / 6-K (Canadian GAAP 2006–10; IFRS for 2011–12 and the 2013–14 quarters).
  - FY2013–14 annuals: US GAAP as recast in the FY2015 10-K.
  - 2015+: 10-K / 10-Q.
  "Latest filing that presents the period" is used throughout. ASC 606 (2018) recast 2017 in full but 2016 only at total revenue, so a memo row bridges the gap. Pre-2017 revenue is on the net agency basis. Pre-2018 CF reconciles unrestricted cash only. IronPlanet from 31-May-2017; IAA from 20-Mar-2023. Extraction ran as parallel agents on one JSON schema, with item categories and signs by income effect.
- **Operating build:** GTV by sector × service take rate, plus inventory sales (% of GTV) and inventory rate (5–9%). The current sector basis (Automotive / HE&T / Other) was recast from Q1/25 in the Q2-26 release. The legacy Auto/CC&T/Other basis (2023–Q1/26) is kept as memo. Non-automotive GTV = total − Auto stays comparable across the re-presentation. GAP was renamed GTV in Q3-17 (Q2/17 revised 1,257.4 → 1,254.3, excluding EquipmentOne buyer premiums). Before 2018 the take rate = total revenue / GAP, because inventory gains were netted in revenue. SG&A is the balancing line to adjusted EBITDA.
- **Bridges & definitions:** the adjusted EBITDA definition row has about 14 flagged changes. Examples:
  - 2011–12: only a margin was published (36.9% / 36.8%); the dollar amounts are model-computed.
  - 2015–Q1/16: published only as the TTM leverage denominator (Q1/Q4 derived).
  - Q3-21: retroactive redefinition back to Q3/19. Q1/19–Q2/19 were never republished and stay on the old definition.
  - Q3-23: dropped an IAA item retroactively (Q2/23 307.8 → 306.9).
  The company's exact wording sits in cell comments per item. Adjusted NI moves to a two-class base from Q1/23 (Series A participating preferred): NI available to common, less the "related allocation to preferred" of the adjustments, with RNCI adjustment and J.M. Wood accretion from Q3/25. Adjusted D&A excludes acquired-intangible amortization only from 2023.
- **Deals & special blocks:** BigIron closed 15-May-2026 ($316.6m; preliminary PPA intangibles $79.1m = 25%). IAA prepaid consigned vehicle charges are a purchase-accounting reversal (2023–Q2/25).
- **Calibration & scenarios:** FY26 outlook from the Q2-26 release (4-Aug-26): GTV +9–11% (raised from 6–9%), adj EBITDA $1,495–1,545m, tax 23–25%, capex $350–400m on the company definition. Q3/Q4 sectors = prior-year quarter × 1H momentum. There is a take-rate Δ (bps) input. Adjusted EBITDA is split by quarterly revenue.
- **Balance sheet, cash & capital:**
  - Series A preferred: $485m, 5.5% cumulative (~$6.7m/qtr), in temporary equity; allocation % ≈ 3.5%.
  - Debt: $2,904m (TLA to Apr-2030, 6.75% 2028 secured, 7.75% 2031 unsecured), ~$100m/yr repaid.
  - Working capital: receivables and auction proceeds payable are driven as days of GTV, not revenue.
  - Buybacks: the 2026E schedule includes only the 2H buyback, since 1H is already in the share counts. NCIB is $500m / 10m shares.
  - Cash: cash = CF ending cash − restricted cash.
- **Valuation:** $80 user price. Adjusted net debt follows the company definition (ex restricted cash and leases). Preferred, RNCI and NCI are deducted. NOPAT is after SBC.
- **Reusable lessons:**
  - [bridges] When a release recomputes comparatives under a new definition, those periods take the new definition. Periods never republished stay on the old one, and the flag row says so.
  - [basis] When a sector re-presentation has no long history, find an aggregate that stays invariant across it (total − Automotive) and model on that, with legacy sectors as memo.
  - [build] For marketplaces, drive receivables and payables off GTV days. Revenue days mislead when the take rate and gross/net basis change.
  - [build] With participating preferred, use two-class EPS: forecast an allocation % and deduct the "related allocation" in the adjusted-NI bridge.
  - [BS/CF] When 1H actual share counts already reflect buybacks, the current-year buyback schedule must cover 2H only.

### CPRT — Copart (RBA template, US GAAP as reported / USD millions / FY ends 31-Jul)
- **Coverage & basis:** FY2006–12 annual, quarterly from FY2013. Q4 = 10-K less the 10-Q nine-month YTD. Shares are restated for the 2-for-1 splits of Mar-2012, Apr-2017, Nov-2022 and Aug-2023. ASC 606 was adopted in FY2019 (modified retrospective, no recast) and ASC 842 from FY2020. The US/International segments start in the FY2016 10-K (FY2014+ recast). Service/vehicle-sales by segment is available annually from FY2017 and quarterly from FY2018. FY2009–12 is entity-wide geography; FY2013 is n/d (North America/UK basis then). Redeemable NCI sits in temporary equity from FY2024.
- **Operating build:** US = prior year × (1+units y/y) × (1+service revenue per unit y/y). Vehicle sales grow by an input. International is built on units. Vehicle-sales GM is 11.5% (range 10–16%), yard ops 49.5% of service revenue (incl. yard D&A and SBC), D&A 4.9% of revenue. G&A is the balancing line to adjusted EBITDA, sanity-checked against the 6–9% historical range. Since FY2021 the earnings releases split yard D&A and SBC onto separate lines; the 10-K face (which includes them) is used for a consistent series.
- **Bridges & definitions:** Copart publishes no EBITDA, so model adjusted EBITDA = EBITDA + Copart's own non-GAAP items. Copart gives those items after tax only, so they are grossed up at 38% (≤FY2017), 27% (FY2018) and 25% (FY2019+). Impairment and debt extinguishment use the exact pre-tax IS amounts. Tax-only items stay out of the EBITDA bridge. Definition flags:
  - Q3/14: one-off ($29.1m ERP impairment + Hurricane Sandy).
  - Q4/16: framework starts (FX + ASU 2016-09; non-GAAP diluted shares exclude the ASU 2016-09 effect, kept as a share-count row).
  - Q1/17 through Q3/19: payroll taxes, impairment and acquisition fees, non-operating disposals, TCJA repatriation, integration and sales-tax reserve, discrete tax.
  - Q2/21: share adjustment removed.
  - Q1/22: FX dropped, with FY2021 comparatives recomputed (the latest presentation is used).
  - Q1/24 onward: nothing published, so adjusted = GAAP.
  The EPS check tolerates ±0.01 from split rounding.
- **Data quirks & corrections:** from FY2021, interest expense is shown net within interest income. Impairment/other operating is an IS-face residual. FY2022 includes a $16.8m loss on redeeming the $400m notes.
- **Deals & special blocks:** the pending ACV Auctions deal (10-Sep-2026, $10.50/sh cash tender) is excluded. The note says ~$2bn of cash would displace buybacks.
- **Calibration & scenarios:** there is no guidance, so every case is a model assumption. Levers: US and International units, US RPU, adjusted EBITDA margin (FY26 40.3%, FY25 41.2%, FY21 ~45%), buybacks and the net-cash floor. Tax is 20.5% (FY26 19.3%, lowered by option excess benefits).
- **Balance sheet, cash & capital:** no funded debt since May-2022. The HTM Treasury portfolio is held flat. Interest income = ~3.8% × (prior year-end cash + HTM). A "min net debt / adj. EBITDA" floor is set negative, so buybacks step up to cap net cash at |x| × EBITDA. FY2026 buybacks were $1,633m. No dividend; repurchases are retired against retained earnings. Capex is lumpy land buying (FY20–25 ~10–20% of revenue; FY26 7.2%).
- **Valuation:** $27 user price. NOPAT = (Adj EBIT − SBC)(1−t). Net cash includes HTM. Leases are not treated as debt. Redeemable NCI is deducted. The BBB Bull P/E comment still cites RB Global's 20–30x (template leak).
- **Reusable lessons:**
  - [bridges] When the company gives non-GAAP items net of tax only, gross up at the statutory rate in force each year and state the rates. Use exact pre-tax amounts where the IS shows them.
  - [bridges] When a company stops publishing non-GAAP, flag "adjusted = GAAP" from that column and default forecast items to nil.
  - [BS/CF] For a net-cash company, use a negative leverage floor (cap on net cash) to drive excess-capital buybacks, and earn interest on cash + investments.
  - [QA] Grep the BBB and DCF comments for the template company (RB Global survived here).

### CPRT (v1) — Copart (SEC-only builder, US GAAP as reported / USD millions / FY ends 31-Jul)
- **Coverage & basis:** FY2011–FY2025 on a Q1–Q4 + FY grid; the half-year columns were dropped. CIK 0000900075. EPS and share counts are as reported and **not** split-adjusted, so a note warns they are not comparable across split dates. The cash flow is shown for fiscal years only, because interim CF is filed YTD. The change in NWC is labelled "(est.)".
- **Operating build:** US / International segments with segment OI from ~FY2016. Earlier years show geographic revenue as filed.
- **Bridges & definitions:** `earnings.py` parses 8-K Ex. 99.1 "Reconciliation of GAAP to Non-GAAP" tables for FY2016–FY2023 plus a one-off Q3 FY2014. The items are deemed repatriation, TCJA/discrete tax, disposal of non-operating assets, impairment, acquisition/integration, legacy sales-tax reserve, FX, ASU 2016-09 option tax effects, payroll taxes on executive comp, and other. All are net of tax. The bridge is non-GAAP NI = GAAP NI attributable + Σ items, with a check (=0) and an implied non-GAAP EPS cross-check. Copart reverted to GAAP-only reporting from FY2024 and has never published adjusted EBITDA, constant-currency or FCF measures. NI is split into total (incl. NCI) and attributable, so EPS ties exactly ($1.73 FY2018, $1.28 FY2023, $1.59 FY2025).
- **Calibration & scenarios:** FY26E–30E driver-based with a scenario toggle. One lever is buyback as % of shares retired per year.
- **Valuation:** "Avg. share price" is a manual input (the only non-SEC input). EV = market cap + net debt. The DCF runs off the model's FCF.
- **Reusable lessons:**
  - [basis] Split-adjust per-share history. Leaving EPS as reported (v1) breaks every per-share trend; v2 restated for all four 2-for-1 splits.
  - [bridges] Start the non-GAAP bridge from NI *attributable*, not total NI, or EPS will not tie.
  - [extraction] Harvest the non-GAAP tables directly from 8-K Ex. 99.1 with a dedicated parser. XBRL does not carry them.

## Consumer & luxury (IFRS, non-USD)

### RMS — Hermès International (MLM template, IFRS / EUR / December FY)
- **Coverage & basis:** FY2006–08 key figures only (revenue, ROI, OI, NI, CFO, capex, equity, net cash) from the 2010 registration document, because no 2006–09 annual reports are on the IR site. Full statements start FY2009, taken from the comparative column of the 2010 document. Half-year interim columns run from H1/13: H1 as reported, H2 = FY − H1 for flows, and H2 balances are the 31-Dec figures. There is a quarterly revenue memo from Q1/14 inside the half-year columns ("1st/2nd quarter of the half" rows, so Q3 sits in the H2 column). Everything is as originally reported: 2018 is pre-IFRS 16 and not restated. Hermès is not an SEC registrant; EDGAR holds only F-6 ADR registrations (CIK 0001450490 / 0001436949), so the sources are AMF documents on finance.hermes.com.
- **Operating build:** seven métiers, each = prior period × (1 + company constant-currency growth + group currency effect). Currency effect = reported − constant growth. Tableware is folded into Other Hermès sectors from 2014, with a memo row as originally reported. Perfume became Beauty in 2020. Margins are modelled at group level (gross-margin and ROI-margin levers) because IFRS 8 segments are geographic. Revenue and ROI by area are a memo with Σ checks. The Unallocated / Holding row covers free-share plans and central costs.
- **Bridges & definitions:**
  - NI → OI → ROI → EBITDA, plus "EBITDA after lease payments" as a pre-IFRS 16 comparable.
  - Recurring NI / EPS excluding non-recurring items and the French exceptional tax (2017 surtaxes net of the 3% dividend-tax refund €20m; 2025 contribution €331m). This ties to the published "NI excl. the exceptional contribution", which is rounded to €0.1bn / €0.01bn, so the check reads 0 when the model is within that rounding.
  - Adjusted FCF: before 2019 the company measure was "free cash flow" with no lease repayments; flagged at the 2018/2019 columns.
  - Cash → net cash → restated net cash: adds >3-month deposits from 2017 and deducts financial liabilities from 2020.
- **Data quirks & corrections:**
  - FY2009–11 métier revenue is printed in whole €m, so checks run ±1–3.
  - The 2015 reclassification moved free-share expense from S&A to other income & expenses; 2014 is left as reported.
  - The H1 exceptional contribution is estimated from the disclosed ETR with and without it.
  - Bank overdrafts are derived as BS cash − CF net cash where not printed.
  - The HK property gain (€52.7m, 2018) and the Shang Xia deconsolidation (€91.1m, 2020) were untaxed, so the tax-effect row is zero for both.
- **Calibration & scenarios:** no numeric guidance. H2/26E = H2/25 × (1 + cc growth + an H2 currency point estimate; H1/26 was −4.5 pts). 2026E cc growth = H1 actual and H2E weighted by 2025 halves. 2026E ETR is 33% including the contribution (about 5 pts); 2027E+ uses 28.5%, with the contribution assumed not renewed. Levers: cc growth by métier, GM, ROI margin, buybacks, exceptional dividends, payout.
- **Balance sheet, cash & capital:** there is no debt schedule (net cash, no financial debt). In its place:
  - an IFRS 16 schedule: new leases as % of revenue, ROU depreciation as % of opening ROU, lease repayments ≈ ROU depreciation;
  - financial income = yield × opening restated net cash − lease interest;
  - NCI dividends = NCI income;
  - buybacks sized to serve free-share plans, floored at 0;
  - exceptional dividends (€5 or €10/share in some years) as a separate lever;
  - ordinary DPS = payout × recurring EPS, paid the following year.
- **Valuation:** €1,299.50, the Euronext close on 2-Oct-26 from the IR quote feed. The DCF uses ROI as adjusted EBIT, keeps ROU depreciation in EBIT as a lease-cost proxy, and excludes leases from net debt. IC = equity + leases − restated net cash. ROIC is above 60%.
- **Reusable lessons:**
  - [sources] For a non-SEC issuer, check EDGAR for F-6-only ADR CIKs, record that in the header, and source from the regulator-filed documents (AMF URDs).
  - [basis] For H1/FY reporters, put quarterly revenue in "first/second quarter of the half" memo rows inside the half-year columns, with a Σ-quarters vs half check, rather than adding quarterly columns.
  - [bridges] When a company publishes an adjusted figure only rounded (€0.1bn), write the check as "0 = within published rounding" and say so in the label.
  - [bridges] Keep country-specific tax levies (the French exceptional contribution) as a separate "of which" tax row so the recurring ETR and the forecast can drop them when the law lapses.
  - [BS/CF] For net-cash companies, replace the revolver schedule with a yield-on-opening-net-cash line and treat exceptional dividends as their own lever.

### BC — Brunello Cucinelli (MLM template, IFRS / EUR / Dec FY, H1/H2 reporter)
- **Coverage & basis:** FY2011–H1/26 in H1 / H2 / FY columns (H2 = FY − H1), with a Q1/Q3 revenue memo (Q3 = 9M − H1). Not an SEC registrant: everything comes from the IR site and eMarket Storage. IPO Apr-2012 (60.0m → 68.0m shares). IFRS 15 applies from 2018, but 2017 is kept as originally reported (the 2018 restatement of 2017 comparatives is not applied). IFRS 16 applies from 2019 (modified retrospective; 2018 not restated). Pre-2017 "revenues from sales and services" included other operating income, which the model shows separately. Channels changed in 2021 (mono/multi-brand → wholesale) and regions changed in 2021 and again in 2025 (Europe incl. Italy); legacy regions are kept as memo rows.
- **Operating build:** Retail = average DOS × sales density (which includes e-commerce and hard shops). Wholesale grows with a growth lever. Geography is a reconciled output: regional growth inputs are scaled pro rata so that Σ regions = the channel build. First margin = revenue − production costs, and operating costs are built by nature (services ex-outsourced, payroll, other) as % of revenue. D&A is split into right-of-use and the rest.
- **Bridges & definitions:** Net profit → EBITDA (company) → normalised EBITDA (only the items BC itself normalised: 2012 IPO costs €6.2m, 2016 payroll €1.5m, 2020 "for Humanity" inventory €31.7m, 2025 Saks provision €8.1m) → EBITDA pre-IFRS 16 (less in-scope rents) → EBIT pre-IFRS 16. Items BC named but did not normalise (COVID 2020–21, the Russia goodwill write-off, R&D credits) are deliberately left in. The pre-IFRS 16 figures tie to company figures for 2019–H1/24, with a derived "other IFRS 16 items" line for things like 2020 rent concessions. 2021–22 ROU depreciation includes key money (a proxy). BC publishes no adjusted EPS; normalised net profit ties for 2015–18. The adjusting-item tax rate is the period ETR bounded to 20–35%, unless the company states the tax effect.
- **Data quirks & corrections:** FY2019's €0.35 DPS was revoked and FY2020 paid nothing; FY2011 DPS is not disclosed. FY2026 share capital was raised to €200m by a reserve transfer (no shares issued).
- **Calibration & scenarios:** Guidance is **constant-FX** revenue growth (+10–11%). The required H2 cFX growth is solved analytically, the Δ is applied to retail only (wholesale is held because the order book is already collected), and an FX effect row is set to neutral. The 2028 €1.8bn plan target is shown as a memo with a "model vs plan %" row.
- **Balance sheet, cash & capital:** There are no open-market buybacks; treasury purchases serve stock grants and are re-issued (share-count neutral). The ROU / lease-liability roll-forward has new leases as % of revenue and an interest rate on opening liabilities, and out-year lease payments = depreciation + interest. Bank debt plugs to €150m minimum cash. NFP excluding leases ties to the company's "core" figure. Dividends run on a 50% payout and are paid the next May on prior-year DPS × shares. The H2 cash flow is derived from the BS movement.
- **Valuation:** €80.18 Milan close. The DCF is **pre-IFRS 16** (all rents as opex, so lease liabilities are not deducted from EV) and runs from the 30-Jun-26 BS, so H2/26E is the first explicit period. EV is shown both with and without leases. Cost of equity adds an Italy country premium of ~1%. NCI is deducted.
- **Reusable lessons:**
  - [basis] For IFRS 16 adopters, carry a pre-IFRS 16 bridge (rents in scope from the lease note) and tie it to the company's "excl. IFRS 16" figures for as long as they are published.
  - [bridges] Adjust only for items the company actually normalised, and list the named-but-not-normalised items in the note so the choice is visible.
  - [calibration] When guidance is constant-FX, calibrate the cFX growth and keep the FX translation effect as a separate input row.
  - [calibration] Apply the calibration Δ only to the line that is genuinely open (retail); hold lines with a committed order book (wholesale).
  - [build] When channel and region disclosures both exist, pick one as the driver and scale the other pro rata, with a Σ check.
  - [valuation] Keep the DCF lease basis consistent: pre-IFRS 16 UFCF goes with EV excluding lease liabilities, and IC excludes ROU / leases.

### ONON — On Holding AG (MLM template, IFRS / CHF m / Dec FYE; NYSE listing in USD; 20-F / 6-K filer)
- **Coverage & basis:** FY2019–20 come from the 424B4 (16-Sep-2021): CHF thousands converted to millions, and shares / per-share ×1,250 for the 2021 share reorganisation. FY2019 has no BS or CF. Q1–Q2/21 come from the 2022 releases' comparatives. BS starts Q3-21 (FY20 from the FY21 release). Shares are Class A-equivalent (A + B ÷ 10). In loss periods the company reports diluted = basic. Template columns shifted −45.
- **Operating build:** Regions: EMEA / Americas / APAC from 2023 (FY21 and 2022 quarters restated); the former Europe / NA / APAC / RoW split is kept as memo, with RoW derived. Each region = prior year × (1 + cc growth + FX translation). Constant-currency growth is published only from Q1-24, and the annual cc figure uses full-year rates, so it does not equal Σ quarters. Channel (DTC = sales − wholesale) and product mix are shown as share drivers, with shoes as the residual.
- **Bridges & definitions:** Adj. EBITDA = NI + tax − financial income + financial expense − FX result + D&A + SBC, plus IPO / equity transaction costs in 2021–22. Adjusted NI sums the Class A and B columns. The tax effect applies only to the deductible part of SBC (~1–2%). Annual columns use the full-year table because the company computes the tax effect annually and quarters do not add up. Tolerances: ±0.15 EBITDA, ±0.35 adjusted NI for class rounding, ±0.4 BS.
- **Data quirks & corrections:** The FY2021 release prints the Q4-21 operating result as (354.9). GP − SG&A gives (177.5), which also ties to FY − 9M, EBT and Adj. EBITDA, so the model uses (177.5). Q1-22 cash is net of a CHF 25.8m overdraft; a memo line nets it in the cash check. Lease liabilities are shown separately only from Q1-25.
- **Calibration & scenarios:** Q3 cc Δ is solved to the Q3 guide (~17%) and Q4 cc Δ to FY cc growth (low-20% → 20–23%). A uniform 2H FX Δ is solved to FY CHF sales "at current spot" (3.47–3.56bn). GM and Adj. EBITDA margin Δs are solved to guidance. The guidance excludes the Q3-26 tariff refund (~CHF 53m). The refund is not a company adjusting item, so it lifts reported Adj. EBITDA; the model carries it on a separate line with "excl. refund" memo series. The Base case follows the Investor Day 2029 targets, shown as information rows.
- **Balance sheet, cash & capital:** IFRS 16: RoU as % of sales, with new leases as the plug and principal ≈ RoU depreciation. No bank debt. Buybacks: USD 1bn authorisation spread evenly from Q4-26 to 2029 (1/13 a quarter), converted at USD/CHF, with a renewal assumed for 2030. Opening shares use Q2 weighted basic as a 30-Jun proxy.
- **Valuation:** USD price × USD/CHF input (0.80, cross-checked against Investor Day USD/CHF pairs). DCF: rent-as-opex, SBC deducted, USD risk-free rate (FX held at spot). Valuation shows net debt both including and excluding leases.
- **Reusable lessons:**
  - [calibration] Use separate per-quarter Δs when a quarterly guide and a full-year guide coexist, and add an FX Δ when guidance is stated both in cc and in reporting currency at spot.
  - [calibration] One-offs the company excludes from guidance but not from its adjusted metric get their own line, plus a guidance-basis memo series.
  - [bridges] If the company computes adjusted tax annually, the FY column uses the FY table rather than Σ Q.
  - [BS/CF] The cash check must net overdrafts the CF statement nets.
  - [QA] Template residue survived here: the Bull-Base-Bear N26 comment cites MLM; the P40 comment cites "Model rows 290–292 / Model!CF2" (another build's rows) with author "User"; DCF headers say "USDm" / "($)" in a CHF model.

## Private company / LBO

### R&Y — R. & Y. Tool and Die Co. Limited (standalone private model + LBO, unaudited compilation statements / CAD whole dollars / FY Dec)
- **Coverage & basis:** FY2021–FY2025 from annual compilation statements (GD Barkwell CPA). The IS and BS are as reported. FY2021 cash flow cannot be computed because there is no FY2020 BS.
- **Operating build:** detailed cost-of-sales schedule (materials, repairs & maintenance by equipment/buildings, shop amortization) and line-item G&A. FY2021 revenue includes $60,000 of COVID grants. Amortization is split between office equipment (G&A) and building and shop equipment (COGS).
- **Bridges & definitions:** a bottom-up NI → EBITDA − capex bridge. Interest is bundled inside "bank charges and interest" and is added back whole. Incremental EBITDA % = ΔEBITDA / ΔRevenue (n/a for FY2021).
- **Data quirks & corrections:** the CF is implied: NI + amortization + Δ future income tax liability (= deferred tax) + Δ every BS account. Implied capex = Δ net PP&E + total amortization; a positive value means net disposals exceeded additions (FY2023). Related-party advances (due to/from director, KEL Tooling, Related Group) are classified as financing. A tie-out check compares implied ending cash with BS cash.
- **Balance sheet, cash & capital:** the PP&E roll-forward includes implied depreciation rate (D&A / opening NBV), implied remaining life (NBV / D&A) and capex/D&A. ROIC uses DuPont with an identity check. NIBCL excludes the interest-bearing bank loan.
- **Deals & special blocks:** the LBO tab has gold toggle cells:
  - Entry multiple and leverage (turns of EBITDA).
  - Interest on opening debt, mandatory amortization (% of opening debt) and cash sweep (% of FCF after mandatory).
  - Minimum cash funded at close and held as a floor, plus fees as % of EV.
  - NWC as % of Δrevenue; exit multiple defaults to entry (no expansion).
  - A Base/Bull/Bear selector for growth, margin and capex, defaulting to history (rev CAGR ~10%, EBITDA margin ~17%, capex 3–4%). Tax ≈ FY25 ETR / CDN small-business rate.
  There are no interim distributions. The Base case returns ~2.6x / ~21% IRR, with closed-form and live `=IRR` agreeing. Entry × exit grids show IRR and MOIC.
- **Reusable lessons:**
  - [BS/CF] Implied CF for private companies: put related-party and director balances in financing, not working capital. Show implied capex with its sign explained (net disposals possible).
  - [build] With no prior-year BS, the first year's CF and capex-dependent ratios must be n/a. Do not back-fill them.
  - [valuation] Default the LBO exit multiple to the entry multiple and the operating levers to historical averages, so the base IRR reflects no re-rating.
