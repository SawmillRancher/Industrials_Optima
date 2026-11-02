# THEON data extraction: schema and rules

Adapted from `templates/EXTRACTION_SCHEMA_TEMPLATE.md` for an IFRS, EUR, half-year reporter that is not an SEC registrant. Give this file, unchanged, to every extraction agent.

## Sources
- **Theon is not an SEC registrant.** EDGAR (CIK 0002095508) holds only Schedule 13G filings about its Kopin stake; use it for the Kopin investment facts only. Everything else comes from Theon's regulated disclosures: the listing prospectus (24-Jan-2024), annual reports, semi-annual reports, trading updates and deal press releases, as indexed in `filings.csv`. Record the document URL in `sources` for every record.
- **Text versions** of every document are in `$THEON_SRC/txt`: one table row per line, cells joined by ` | `. PDFs are converted with the pdf skill's text extraction; keep page numbers in `notes` for tables.
- **Nothing from third-party summaries** (news sites, aggregators, broker notes). If a figure exists only there, leave the key null and say so in `notes`.

## Basis rules
- **Periods:** `2021`, `2022`, `2023`, `2024`, `2025` (annual); `H1-24`, `H1-25`, `H1-26` (six months); `Q1-25`, `Q3-25`, `Q1-26`, `Q2-26`, `Q3-26` (trading updates: revenue, adjusted EBIT, order intake, backlog only). H2 is **derived** later in `normalize.py` as FY − H1 (flows) and as the 31-Dec balance (stocks); never extract an H2 record.
- **Annual records:** the annual report wins over the preliminary-results release when they differ; note both.
- **Half-year records:** the semi-annual report wins over the trading update.
- **Prior-year comparatives (`py`):** as presented in each document, with `restated` true and the reason when they differ from the original print (e.g. purchase-price-allocation finalisation, IFRS reclassifications).
- **Units:** EUR millions to one decimal as published (thousands ÷ 1,000); shares in millions (3 dp); per-share as published; percentages as numbers (3.5 = 3.5%).
- **Share capital events:** record shares / EPS / DPS exactly as published, with `is.per_share_basis` noting any share reorganisation (pre-IPO capital, the Feb-2024 primary issue, any 2026 rights offering). Don't adjust them yourself.
- **Signs:** costs positive; two-sided items signed by their effect on earnings / cash; cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented = null. **Never estimate.** Any computed value (sum, difference, FY − H1) is stated in `notes`.

## Output
One JSON file per period: `models/theon_build/data/<period_key>.json`. Valid JSON only.

```json
{
  "period": "H1-26", "period_end": "2026-06-30",
  "sources": {"report": "https://...", "release": "https://...", "pages": "..."},
  "is": {
    "revenue": null, "cost_of_sales": "positive", "gross_profit": null,
    "selling_distribution": "positive", "admin": "positive", "rnd": "positive",
    "other_op_income": "signed: income positive", "other_op_expense": "positive",
    "other_op_lines": [["exact label", "positive = expense"]],
    "op_profit": null, "ebit_company": null,
    "finance_income": "positive", "finance_costs": "positive", "fx_result": "signed",
    "share_of_associates": "signed", "fv_gains_investments": "signed",
    "ebt": null, "tax": "positive = expense", "net_income": null, "nci": "positive = deducted", "ni_parent": null,
    "shares_basic": null, "shares_diluted": null, "eps_basic": null, "eps_dil": null,
    "dps_declared": null, "per_share_basis": "text",
    "da_total": null, "dep_ppe": null, "dep_rou": null, "amort_intangibles": null, "amort_acquired": null, "sbc": null
  },
  "ops": {
    "order_intake": null, "backlog_end": null, "book_to_bill": null,
    "revenue_by_product": [["exact label", null]], "revenue_by_region": [["exact label", null]],
    "revenue_by_customer_type": [["exact label", null]],
    "organic_growth_pct": null, "acquired_revenue": null, "fx_effect": null,
    "units_delivered": null, "employees": null,
    "kpi_note": "definitions in force (e.g. organic excludes Harder Digital / Kappa until anniversary)"
  },
  "ngaap": {
    "adj_ebit_pub": null, "adj_ebit_margin_pub": null, "adj_ebitda_pub": null, "adj_ni_pub": null, "adj_eps_pub": null,
    "bridge_start": null, "bridge_start_label": "exact",
    "item_amounts": [["exact label", "pretax EURm as added", "after-tax EURm", "op | nonop | tax | below_ni", "CAT"]],
    "guidance": "FY revenue range, adjusted EBIT margin, organic growth, capex, tax, dividend policy, medium-term targets — verbatim",
    "notes": "definition of each adjusted measure in this period"
  },
  "cf": {
    "ytd_months": 6, "ebt_or_ni_start": null, "start_label": "exact", "dep": null, "amort": null, "sbc": null,
    "finance_cost_addback": null, "tax_paid": "negative", "wc_change": "signed sum of change lines", "cfo": null,
    "capex_ppe": "negative", "capex_intangibles": "negative", "capitalised_development": "negative",
    "acquisitions_net_cash": "negative", "investments_fin_assets": "negative", "divest": null, "cfi": null,
    "debt_proceeds": null, "debt_repay": "negative", "lease_principal": "negative", "interest_paid": "negative",
    "dividends": "negative", "share_issue": null, "buyback": "negative", "cff": null, "fx": null, "net_change": null,
    "cash_begin": null, "cash_end": null, "lines_raw": [["exact label", "value as shown"]]
  },
  "bs": {
    "cash": null, "trade_receivables": null, "contract_assets": null, "inventories": null, "other_ca": null, "tca": null,
    "ppe": null, "rou": null, "goodwill": null, "intangibles": null, "investments_fin_assets": null, "associates": null,
    "deferred_tax_asset": null, "other_nca": null, "ta": null,
    "st_borrowings": null, "lease_cl": null, "trade_payables": null, "contract_liabilities": null, "other_cl": null, "tcl": null,
    "lt_borrowings": null, "lease_ncl": null, "deferred_tax_liab": null, "other_ncl": null, "tl": null,
    "share_capital": null, "share_premium": null, "reserves": null, "retained_earnings": null,
    "equity_parent": null, "nci": null, "te": null, "tle": null, "shares_out": null,
    "net_debt_company": null, "net_debt_definition": "exact wording (leases in / out)",
    "lines_raw": [["exact label", "value"]]
  },
  "py": {"restated": false, "notes": null, "is": {}, "ops": {}, "adj_ebit_pub": null},
  "extra": {
    "acquisitions": [["name", "close date", "consideration EURm", "PPA: goodwill / intangibles / other"]],
    "financial_investments": [["name", "date", "stake %", "cost EURm", "carrying value EURm"]],
    "debt_facilities": [["facility", "amount EURm", "rate", "maturity"]],
    "amort_schedule": [["year", "EURm"]], "notes": null
  },
  "notes": "computed values; any self-check that does not pass and why"
}
```

## Adjusting-item categories (CAT)
As in the template: AMORT, ACQ, STEPUP, RESTR, SBC, DEBT, GAIN, IMPAIR, LEGAL, OTHER, TAX, TAXD, NCI, plus **FVI** for fair-value movements on financial investments (Exosens, Kopin) and **IPO** for listing costs.

## Self-checks before writing each period
- **IS:** gross_profit − opex lines ± other operating = op_profit; op_profit + finance income − finance costs ± fx ± associates ± fv = ebt; ebt − tax = net_income; net_income − nci = ni_parent (±0.1).
- **Adjusted EBIT:** bridge_start + Σ items = adj_ebit_pub (±0.1); adj_ebit_pub ÷ revenue = adj_ebit_margin_pub (±0.1 pt).
- **Operations:** Σ product / region splits = revenue (±0.1); backlog_end = backlog_begin + order_intake − revenue ± acquired backlog (note the residual).
- **Cash flow:** cfo + cfi + cff + fx = net_change; cash_begin + net_change = cash_end (±0.1).
- **Balance sheet:** ta = tle; components sum to subtotals (±0.1); company net debt reproduced from borrowings, leases and cash per its stated definition.
