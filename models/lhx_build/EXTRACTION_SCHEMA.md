# LHX data extraction: schema and rules

Give this file, unchanged, to every extraction agent. Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (L3Harris Technologies, Inc., CIK 0000202058; named Harris Corporation until 25-Jun-2019 — same registrant; Harris was the legal and accounting acquirer in the 29-Jun-2019 merger with L3 Technologies). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$LHX_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. Record the URLs given in the period index in `sources`.
- **Period index:** `$LHX_SRC/period_index.json` maps each period key to `release` (list: earnings release and, in 2022–23, the quarterly "investor letter"; Q3-26 also has an earnings appendix), `filing` (10-Q, or 10-K / 10-KT for annual, Q4 and the transition period), `next_release` and `next_filing` (the same documents one year later, for comparatives). Each entry has `txt` (file name in `$LHX_SRC/txt`) and `url`.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative.
  - "—" means zero.
- **Optional cross-check:** `$LHX_SRC/cf_202058.json` (XBRL company facts).
- Do not use any source outside `$LHX_SRC`. Do not fetch anything from the web.

## Period keys
| Key | Period |
|---|---|
| `2013` … `2019` | Harris Corporation fiscal years ended the Friday nearest 30 June (FY2019 = 30-Jun-2018 – 28-Jun-2019, pre-merger). Annual records only. |
| `Q3-19`, `Q4-19` | The two quarters of the fiscal transition period: 29-Jun-2019 – 27-Sep-2019 and 28-Sep-2019 – 3-Jan-2020 (L3Harris, post-merger). |
| `TP19` | The six-month fiscal transition period ended 3-Jan-2020 (Form 10-KT). |
| `Q1-20` … `Q3-26` | Fiscal quarters of the fiscal years ended the Friday nearest 31 December. |
| `2020` … `2025` | Fiscal years ended the Friday nearest 31 December (2024 = 53 weeks, ended 3-Jan-2025). |

## Basis rules
- **Quarters:** income statement, non-GAAP bridges, segment data and orders / backlog come from that quarter's release (three-month / "quarter" columns), **as originally reported**. Where the release omits a statement or line, use that quarter's 10-Q.
  - Q4 = the Q4 release's three-month column. Only if that is missing, use FY − 9M, and say so in `notes`.
  - `Q4-19` = the transition-period release's quarter column; `TP19` = its two-quarter column and the 10-KT.
- **Balance sheet:** the period-end statement.
- **Cash flow:** the **year-to-date** statement; set `cf.ytd_months` to 3, 6, 9 or 12 (`Q3-19`: 3; `Q4-19` and `TP19`: 6). If the release also prints the three-month column, still record year to date.
- **Annual records:** the Q4 release twelve-month columns plus that year's 10-K. **The 10-K wins** when they differ (note the difference).
- **Prior-year comparatives (`py`):** the prior-year column as presented in this period's documents. Set `py.restated` true, with the reason, if it differs from what was originally reported (segment recasts, discontinued operations, accounting changes).
- **Units:** USD millions as published (the releases print whole millions; keep decimals where printed); shares in millions; per-share as published; percentages as numbers in percent (15.9 = 15.9%).
- **Signs:**
  - costs positive (`cogs`, `sga`, `interest_exp`, `tax`);
  - two-sided items signed by their effect on earnings / cash (income or inflow +, expense or outflow −);
  - cash flow as presented.
- **Null vs zero:** a line shown as "—" = 0.0. A line not presented = null (omit the key). **Never estimate.** Any computed value (sum, difference, FY − 9M) is stated in `notes`.

## Output
One JSON file per period: `models/lhx_build/data/<period_key>.json`. Write valid JSON: no comments, no trailing commas.

```json
{
  "period": "Q2-25", "period_end": "YYYY-MM-DD", "weeks": 13,
  "sources": {"release": "https://...", "filing": "https://..."},
  "is": {
    "lines_raw": [["exact label as printed, top to bottom, incl. per-share and share lines", "value as shown (signed as shown)"]],
    "sales": null, "cogs": "positive", "sga": "positive (engineering, selling & administrative / general & administrative)",
    "other_op_lines": [["exact label (e.g. Business divestiture-related (losses) gains, Impairment of goodwill and other assets)", "positive = expense"]],
    "op_income": null,
    "nonop_lines": [["exact label (e.g. Non-service FAS pension income, Other non-operating income, net, Non-operating income (loss))", "signed: income positive"]],
    "interest_exp": "positive", "interest_inc": "positive", "interest_net": "positive = net expense (when only a net line is printed)",
    "ebt": null, "tax": "positive = expense",
    "cont_ops": null, "disc_ops": "signed", "net_income": null, "nci": "positive = deducted", "ni_parent": null,
    "pref_div": "positive = deducted (subsidiary preferred stock deemed dividends, 2026)", "ni_common": null,
    "shares_basic": null, "shares_diluted": null, "eps_basic": null, "eps_dil": "diluted EPS, total / attributable",
    "eps_dil_cont": "diluted EPS from continuing operations", "dps": "cash dividends paid per common share"
  },
  "seg": {
    "basis": "the measure the company calls segment profit in this period (e.g. 'segment operating income', 'adjusted segment operating income')",
    "segments": [{"name": "exact", "sales": null, "op_income": "segment operating income as presented in the segment table",
                  "adj_op_income": "adjusted / non-GAAP segment operating income if published separately", "organic_growth": "percent, if published",
                  "orders": null, "book_to_bill": null, "funded_backlog": null, "backlog": null}],
    "intersegment": "signed (eliminations in revenue)", "other_rev": "signed (corporate / other non-reportable revenue)",
    "corp_lines": [["exact label of each line between Σ segment operating income and consolidated operating income (unallocated corporate expense, FAS/CAS operating adjustment / pension adjustment, amortization of acquisition-related intangibles, merger / integration, LHX NeXt, impairments, divestiture gains...)", "signed: income +, expense −"]],
    "seg_op_total_pub": "Σ segment operating income / 'segment operating income' total as published",
    "adj_seg_op_pub": "published adjusted segment operating income (total) and", "adj_seg_margin_pub": "its margin (percent)",
    "kpis": {"orders": null, "book_to_bill": null, "backlog": "total backlog at period end", "funded_backlog": null,
             "organic_growth": "total organic revenue growth percent as published", "organic_rev_cur": null, "organic_rev_py": "prior-year organic revenue base ($m)"},
    "seg_note": "segment structure in force / recasts"
  },
  "ngaap": {
    "adj_ebit_pub": null, "adj_ebit_margin_pub": null,
    "adj_ebit_bridge": [["exact label (start line first)", "value"]],
    "adj_eps_pub": "non-GAAP EPS as published in this period (headline non-GAAP EPS)", "adj_eps_label": "exact label",
    "pension_adj_eps_pub": "pension adjusted non-GAAP diluted EPS, where published",
    "eps_bridge_start": null, "eps_bridge_start_label": "exact",
    "eps_bridge": [["exact label", "per-share value as added (pre-tax items +, tax effect as shown)"]],
    "item_amounts": [["exact label", "pretax $m as added (expense added back +, gain removed −)", "op | nonop | tax | below_ni | discops", "CAT"]],
    "items_tax_effect": "$m income-tax effect of the adjustments (negative = reduces non-GAAP income), where published in $",
    "items_nci": "$m NCI portion of the adjustments, where published",
    "adj_ni_pub": "non-GAAP net income / income from continuing operations in $m, where published",
    "nongaap_tax_rate_pub": "percent", "adj_ebt_pub": null,
    "fcf_pub": null, "adj_fcf_pub": null, "fcf_bridge": [["exact label (start line first)", "value"]],
    "guidance": "forward guidance text (ranges for revenue, organic growth, segment margin, EPS, tax, interest, capex, FCF, shares, pension, by segment), with prior ranges where printed",
    "notes": "definition of each adjusted measure in this period"
  },
  "cf": {
    "ytd_months": 12,
    "lines_raw": [["exact label, top to bottom, every line", "year-to-date value as shown"]],
    "net_income": null, "da": "depreciation and amortization, total (sum the lines if split)",
    "amort_acq": "amortization of acquisition-related intangibles, if a separate line or disclosed", "sbc": null, "deferred_tax": null,
    "pension_contrib": "signed", "pension_income": "signed (net periodic benefit income / pension and OPEB income)",
    "cfo": null, "capex": "negative", "ppe_proceeds": null, "acquisitions": "negative", "divest": null, "cfi": null,
    "debt_proceeds": null, "debt_repay": "negative", "cp_net": "signed (change in commercial paper / short-term debt)", "dividends": "negative",
    "buyback": "negative", "stock_iss": null, "cff": null, "fx": null, "net_change": null,
    "cash_begin": null, "cash_end": null
  },
  "bs": {
    "lines_raw": [["exact label, top to bottom, every line", "value"]],
    "cash": null, "ar": "receivables", "contract_assets": null, "inventories": null, "held_for_sale_a": null, "tca": "total current assets (null if not presented)",
    "ppe": null, "rou": null, "goodwill": null, "intangibles": null, "ta": null,
    "st_debt": "short-term debt + current portion of long-term debt", "ap": null, "contract_liab": "contract liabilities / advance payments and unearned income",
    "comp_benefits": null, "held_for_sale_l": null, "tcl": "total current liabilities (null if not presented)",
    "ltd": null, "pension_liab": "defined benefit plans (where a separate line)", "deferred_tax_l": null, "tl": null,
    "mezz": "mezzanine equity (2026)", "equity_parent": null, "nci": null, "te": null, "tle": null,
    "shares_out": "shares outstanding at period end from the 10-Q / 10-K balance sheet or cover (m)", "shares_out_cover": ["cover-page count (m)", "as-of date"]
  },
  "py": {"restated": false, "notes": null,
         "is": {"sales": null, "op_income": null, "ni_parent": null, "eps_dil": null, "eps_dil_cont": null},
         "segments": [{"name": "exact", "sales": null, "op_income": null}], "adj_eps_pub": null, "adj_seg_op_pub": null},
  "extra": {
    "employees": null, "rd_company_funded": null,
    "pension": {"fas_cas_operating_adj": "signed, income +", "non_service_fas_pension_income": null, "cas_cost": null, "fas_service_cost": null},
    "rev_mix": [["label (customer / geography / contract type split from the 10-K)", "$m or %"]],
    "acquisitions": [["name", "close date", "consideration $m", "segment"]],
    "divestitures": [["name", "date", "proceeds $m", "notes"]], "debt_maturities": [["year", "$m"]],
    "amort_schedule": [["year", "$m"]], "buyback": "shares repurchased (m), amount $m, average price, remaining authorization",
    "notes": null
  },
  "notes": "computed values; any self-check that does not pass and why"
}
```
`extra` is for annual records (10-K / 10-KT) and may be omitted for quarters, except `extra.buyback` and `extra.pension`, which are wanted wherever the 10-Q / release prints them.

## Adjusting-item categories (CAT)
| Code | Meaning |
|---|---|
| AMORT | Acquired-intangible amortization |
| ACQ | Acquisition, merger, divestiture transaction and integration costs |
| STEPUP | Inventory step-up and other purchase accounting |
| RESTR | Restructuring, LHX NeXt implementation, workforce / facility consolidation |
| PENSION | Pension items (settlements, curtailments, pension adjustment) |
| SBC | Stock-based compensation |
| DEBT | Debt extinguishment / refinancing |
| GAIN | (Gain) / loss on sale of businesses or assets |
| IMPAIR | Impairment |
| LEGAL | Litigation |
| OTHER | Any other item; keep the company's label |
| TAX | Tax effect of the items |
| TAXD | Discrete tax items (tax reform etc.) |
| NCI | Share attributable to NCI |

## Self-checks before writing each period
Re-read the source if any of these fail, and report any failure that remains, with the reason, in `notes`.
- **IS:** sales − cogs − sga − Σ other_op = op_income; op_income + Σ nonop − interest_exp + interest_inc (or − interest_net) = ebt; ebt − tax = cont_ops; cont_ops + disc_ops = net_income; net_income − nci = ni_parent (±1).
- **Segments:** Σ segment sales + intersegment + other_rev = sales; Σ segment op_income + Σ corp_lines = op_income (±1).
- **Non-GAAP:** eps_bridge_start + Σ eps_bridge = adj_eps_pub (±0.01).
- **Cash flow:** cfo + cfi + cff + fx = net_change; cash_begin + net_change = cash_end (±1).
- **Balance sheet:** ta = tle; components sum to subtotals (±1).
