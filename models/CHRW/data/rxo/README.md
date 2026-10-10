# RXO source data pack: CHRW acquisition of RXO (announced 5-Oct-2026)

All data comes from SEC EDGAR: RXO CIK 1929561 and CHRW CIK 1043277. Figures are in USD millions unless stated otherwise. Per-share figures are in USD and share counts are in millions.

## Files
| File | Contents |
|---|---|
| `deal_terms.json` / `deal_terms.md` | Deal terms, each with a source URL and an exact quote. Includes a derived consideration bridge (equity value → EV, cash, new shares, ownership). |
| `rxo_data.csv` | RXO standalone financials in long format: `key,period,value,unit,source,note` (~2,600 rows). The `source` column holds the EDGAR URL plus the table, row and column. |
| `raw/` | Downloaded filings (10-K, 10-Q, earnings-release 8-K exhibits, Form 10/A, Coyote 8-Ks, merger agreement, support agreement, slide JPGs, XBRL companyfacts). |
| `work/` | Parsing, assembly and validation scripts (`parse_pr.py`, `build_pr.py`, `assemble.py`, `validate.py`, `deal_terms.py`) and intermediate JSON. To rebuild, re-run `parse_pr.py`, then `build_pr.py`, then `assemble.py`, then `validate.py`. |

## Method
* **Primary source:** the quarterly earnings-release Ex.99.1 tables, Q4/22 through Q2/26 (15 releases). They contain the P&L, balance sheet, cash flow, revenue by service, gross margin, the Adj. EBITDA reconciliation and the Adj. NI/EPS reconciliation. They also carry prior-year comparatives, which supply Q1/22–Q3/22 and FY2021.
* **Value selection:** where a period appears in more than one filing, the **latest-filed value** is used. The `note` column records the originally reported number.
* **Supplementary sources:**
  * Form 10/A Ex.99.1: June 30, 2022 balance sheet, March 31, 2022 equity, FY2021 free cash flow.
  * Q3/22 10-Q: September 30, 2022 balance sheet.
  * 10-Q/10-K debt footnotes: debt by instrument at every period end from Q3/22.
  * Release text: brokerage volume metrics and outlook.
  * Merger agreement: capitalization.
* **Three-month cash flow figures** are derived as YTD(n) − YTD(n−1); Q4 = FY − 9M. The note column flags each one. P&L Q4s are reported directly as three-month columns in the Q4 releases, so no P&L derivation was needed.
* **Year-end balance sheet values** are stored under both `FY20xx` and `Q4/xx`.
* **Sign conventions:**
  * Expenses are positive. `other_expense_income` is positive when it is an expense.
  * `tax` is positive for a provision and negative for a benefit.
  * Cash-flow outflows (capex, acquisitions) are negative, as on the CF statement.
* Shares are converted from thousands to millions.

## Coverage
* **Periods:** FY2021 (XPO carve-out) through FY2025; Q1/22–Q2/26; LTM_Q2/25 and LTM_Q2/26 (sums of four quarters).
* **P&L:**
  * Revenue: `rev_brokerage`, `rev_last_mile`, `rev_managed_transportation`, `rev_elims`, `rev_total`. Also `rev_freight_forwarding` and `rev_managed_transportation_excl_ff` as memo items for 2022–2023.
  * Costs: `cost_transportation_services`, `direct_operating_expense`, `sga`, `dep_amort`.
  * Transaction and restructuring items: `transaction_integration_costs` and `restructuring_costs` (face lines), `transaction_integration_restructuring` (their sum) and `impairment`.
  * Below the operating line: `op_income`, `other_expense_income`, `debt_extinguishment_loss`, `interest_expense`, `pretax`, `tax`, `net_income`.
  * Per share: `eps_basic`/`eps_diluted` and `shares_basic_wavg`/`shares_diluted_wavg`.
* **Non-GAAP:**
  * `adj_ebitda` and `adj_ebitda_margin_pct`, with every reconciliation line as `adjebitda_*`.
  * `adj_net_income` and `adj_eps`, with every line as `adjeps_*`, plus `adjeps_diluted_shares`.
  * Gross margin (company-defined): `gross_margin`, `gross_margin_pct`, `gross_margin_brokerage`/`_complementary`, `gross_margin_pct_brokerage`/`_complementary`. The full gross-margin build by service is under the `gmtab_*` keys.
* **Brokerage KPIs:** `brokerage_volume_growth_yoy_pct` (Q4/22–Q2/26), `brokerage_truckload_volume_growth_yoy_pct` and `brokerage_ltl_volume_growth_yoy_pct` (Q3/23 onward), and `brokerage_truckload_spot_mix_pct` (Q4/25–Q2/26).
* **Balance sheet:**
  * Every line on the face, plus `total_liabilities` (derived as current + long-term), `net_debt` (derived) and `shares_outstanding_period_end`.
  * Debt by instrument, principal and carrying (`debt_*_principal` / `debt_*_carrying`): revolver, ABL, term loan, 7.50% 2027 notes, 6.375% 2031 notes, finance leases/other, total.
* **Cash flow:** `cfo`, `cfi`, `cff`, `capex`, `acquisitions`, `share_based_comp`, `proceeds_ppe_sales`, `buybacks`, `equity_issuance_proceeds`, cash interest and taxes. Also `fcf_company_defined` (where published) and `fcf_cfo_less_capex` (derived).
* **Other:**
  * Coyote facts.
  * ABL terms.
  * Q3/26 outlook.
  * Shares outstanding from the 10-Q cover.
  * RSUs, PSUs and pre-funded warrants.

## Validation
`work/validate.py` runs 256 checks. All pass within rounding of ±1–2m, or ±0.03 for EPS.
* Revenue by service + eliminations = total revenue, for all 23 periods.
* Revenue − operating cost lines = operating income; operating income − other − debt extinguishment − interest = pretax; pretax − tax = net income.
* The Adj. EBITDA and Adj. NI reconciliations sum to the published totals.
* Assets = liabilities + equity, at every available balance-sheet date.
* Q1+Q2+Q3+Q4 = FY for the main P&L, adj. EBITDA, adj. NI, CFO, capex and SBC, for FY2022–FY2025. EPS and adjusted EPS quarterly sums are within ±0.03.

## Anomalies, restatements and comparability
1. **Managed transportation recast.** From the Q2/24 release, Freight Forwarding is included in Managed Transportation, with 2023 recast. For a consistent series, `rev_managed_transportation` for 2021–2022 is computed as reported MT + FF. The original values are kept as `rev_managed_transportation_excl_ff` and `rev_freight_forwarding`.
2. **Q4/24 and FY2024 revised after the release.** The 10-K changed the tax line by $5m:
   * Net income moved from −20 to −25 (Q4/24) and from −285 to −290 (FY2024).
   * Diluted EPS moved from −0.12 to −0.15 (Q4/24) and from −2.14 to −2.17 (FY2024).
   * The release's separate $(5)m "Discrete tax item" in the adj. NI reconciliation is set to 0 on the latest basis. Adj. NI is unchanged at 10 / 17.
   * The FY2024 balance sheet also changed slightly (Coyote measurement-period adjustments): total assets moved from 3,418 to 3,414.
3. **FY2022 balance sheet:** the Q4/22 release figures differ from the 10-K/later comparatives (total assets 2,038 vs 2,031; receivables 907 vs 900). The latest figures are used.
4. **Gross margin definition.** From the Q2/23 release, gross margin also deducts direct D&A. Later releases recast prior-year comparatives (e.g. Q4/22 219 → 218). **Q1/22 and FY2021 remain on the old basis**: Q1/22 is the "Adjusted gross margin" from the Q1/23 release, which excludes direct D&A of roughly $1m.
5. **Q3/24 other expense of $216m** is a non-cash deemed non-pro rata distribution tied to the Aug-2024 discounted PIPE. It is included in "Restructuring and other costs" in the Adj. EBITDA and Adj. NI reconciliations (Q3/24: 218).
6. **Q4/25 goodwill impairment:** $12m.
7. **Debt extinguishment loss:** $11m in Q1/26, from redeeming the 7.50% 2027 notes at 101.875%.
8. **Coyote comparability.**
   * Coyote (UPS's truckload brokerage) closed 16-Sep-2024 for $1.038bn cash, which became $1.048bn after a $10m working-capital adjustment paid in Q1/25. Goodwill was $493m and intangibles $459m.
   * It was funded with equity rather than debt. The PIPE (12-Aug-2024) sold 20.95m shares at $20.21 plus 6.26m pre-funded warrants at $20.20 (~$550m) to MFN and Orbis. The public offering (Sep-2024) sold 22.12m shares at $26.00 (gross $575m). Total gross proceeds were $1,125m; the delayed-draw term loan was not drawn.
   * Results include Coyote only from 16-Sep-2024, so 2024 is partial (Coyote revenue $796m in FY2024). Pro forma revenue was $6,390m for FY2024 and $7,079m for FY2023.
   * Brokerage volume growth is pro forma (Coyote in both periods) from Q4/24. Q3/24 volume growth is **legacy RXO only**.
9. **Share counts.**
   * Basic/diluted weighted average shares (169.6m in Q2/26) exceed common shares outstanding (164.9m) because the 4.58m pre-funded warrants are in basic WASO.
   * Q1–Q3/22 EPS uses the 115.163m distribution shares.
   * Adjusted diluted shares differ from GAAP diluted in loss quarters.
10. **Q2/26 cash flow:** H1/26 CFO was −47, so Q2/26 is −40, driven by a $223m increase in receivables on 25% revenue growth.
11. **FY2021 is a carve-out from XPO.** It has no debt, an XPO net-investment equity line and allocated corporate costs. Form 10 public-company pro forma Adj. EBITDA was $268m vs $277m historical.

## Gaps
* **No segment Adj. EBITDA.** RXO reports one reportable segment and does not publish Adj. EBITDA for Brokerage, Managed Transportation, Last Mile or Corporate. Only revenue, cost of transportation, direct opex, direct D&A and gross margin are disclosed by service (Truck brokerage vs Complementary services).
* **Q1/22 (31-Mar-2022) balance sheet** was not published; only total equity (1,043) is available, from the Form 10 equity rollforward. Q1/22 is also missing other_expense_income.
* **Debt-by-instrument for Q1/22–Q2/22** is not applicable: RXO had no debt before the Oct-2022 spin, and debt detail starts at FY2022.
* **Company-defined FCF** was published only for FY2021 (Form 10: CFO − capex + PP&E proceeds = 117) and in the Q1/23 release (Q1/23 30, Q1/22 91). `fcf_cfo_less_capex` is analyst-derived.
* **Capitalized software** is not split from PP&E capex: RXO reports a single "Payment for purchases of property and equipment" line.
* **Brokerage volume:**
  * Total brokerage volume growth is not given for Q1/22–Q3/22.
  * Truckload/LTL splits are missing for Q4/22–Q2/23.
  * Absolute load counts and gross profit per load are not disclosed in numeric form; they appear only in earnings-presentation slide images, which were not captured.
* **Q3/26:** only guidance (Adj. EBITDA $35–45m) and the 9-Sep-2026 qualitative update. Q3/26 results had not been reported as of 5-Oct-2026.
* **Deal documents:** costs to achieve the synergies, synergy phasing beyond "within two years", the permanent financing mix and a reverse termination fee are not disclosed or do not exist.
