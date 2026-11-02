# EXENS data extraction: schema and rules

Exosens SAS (Euronext Paris: EXENS, ISIN FR001400Q9V2). IFRS as adopted by the EU, euros, calendar fiscal year, half-year
reporter (H1 / FY statements; Q1 and Q3 revenue trading updates). Derived from the DHR / TDY / WAB / ONON schemas.

## Sources
- **Not an SEC registrant.** EDGAR holds only the Citibank F-6EF ADR registration (CIK 0002109666, 5-Feb-2026), which has no
  financial statements. Sources are the regulator-filed (AMF) documents published on www.exosens.com/investors:
  Universal Registration Documents (URD 2024, URD 2025), the IPO Registration Document (July 2024, with FY2021–23 audited
  statements), the half-year financial reports (H1 2024, H1 2025, H1 2026), and the results / revenue press releases.
- **Text versions** of every document are in `$EXENS_SRC/txt/<doc>.txt` (`pdftotext -layout`; one PDF page per form feed).
  Record `sources` as `"<doc>.txt p.<page printed on the page>"` (or the line range) per section.
- **Text quirks:** tables sometimes split a cell across two lines (a label on one line, the numbers on the next);
  columns can shift when a line is wrapped. Check each number against the printed total before writing it.
  Negative numbers appear as `-1,234` or `(1,234)`; "—" or "-" alone means zero.

## Basis rules
- **Record values exactly as printed, including the sign** (expenses negative in the income statement and cash flow,
  as Exosens prints them). Do not re-sign.
- **Units:** statements are in € thousands → write € millions with **three decimals** (÷ 1,000). APM tables
  (segment, Adjusted EBITDA / EBIT, cash conversion) are printed in € millions to one decimal → write them as printed.
  Shares in **units** as printed (weighted average number of shares); per-share in €; percentages as printed numbers
  (14.8 = +14.8%).
- **Which column:** for a period file take the **current-period column** of the document that first reported it:
  - `2021`, `2022`, `2023`: IPO Registration Document (FY2023 statements with FY2022 comparatives; FY2022 statements with
    FY2021 comparatives). Cross-check FY2023 against the URD 2024 comparative column and note any difference.
  - `2024`: URD 2024 (as originally reported, Microwave Amplification included).
  - `2024R`: the **restated** FY2024 column of URD 2025 (continuing operations after the Microwave Amplification disposal).
  - `2025`: URD 2025.
  - `H1-23`: H1 2024 report comparative column. `H1-24`: H1 2024 report. `H1-25`: H1 2025 report (as originally reported).
    `H1-25R`: the restated H1 2025 column of the H1 2026 report. `H1-26`: H1 2026 report.
  - Balance sheets are not restated for IFRS 5 presentation of a disposed unit; take the statement as printed.
- **Prior-year comparatives (`py`):** record the comparative column as presented in each document when it differs from
  the original print, with `restated: true` and the reason (IFRS 5 Microwave Amplification; any reclassification).
- **Null vs zero:** a line printed as 0 or "-" = 0.0. A line not presented = null (omit the key). **Never estimate.**
  Any computed value (H2 = FY − H1, a sum) is stated in `notes`; do not compute anything in the period files
  (normalize.py derives H2).

## Output
One JSON file per period: `models/exens_build/data/<period_key>.json` with keys `2021`, `2022`, `2023`, `2024`, `2024R`,
`2025`, `H1-23`, `H1-24`, `H1-25`, `H1-25R`, `H1-26`. Valid JSON only (no comments, no trailing commas).

```json
{
  "period": "2025", "period_end": "2025-12-31", "basis": "continuing operations (Microwave Amplification discontinued, IFRS 5)",
  "sources": {"is": "URD_2025.txt p.217", "bs": "...", "cf": "...", "seg": "...", "ng": "...", "notes": "..."},
  "is": {
    "rev": null, "cos": "cost of sales (negative)", "ext": "other purchases and external expenses", "taxes": "taxes and duties other than income tax",
    "staff": "employee benefit expense", "oth_op_inc": null, "oth_op_exp": null, "dna_prov": "depreciation, amortisation and charges to provisions",
    "rop": "recurring / current operating profit", "oth_inc": null, "oth_exp": null, "op": "operating profit",
    "cost_net_debt": null, "deriv": "net gains (losses) on derivative instruments", "fin_oth": "other financial", "net_fin": "net financial income (expense)",
    "ebt": null, "tax": "income tax (negative = expense)", "ni_cont": "net profit from continuing operations", "disc": "net profit from discontinued operations",
    "ni": "net profit attributable to shareholders", "eps_basic": null, "eps_dil": null, "eps_basic_cont": null, "eps_basic_disc": null,
    "wsh": "weighted average number of shares (units)", "wsh_dil": null, "pref_div": "preferential dividend deducted for EPS (€ thousands → millions)"
  },
  "seg": {
    "amp_rev": null, "di_rev": null, "elim_rev": null, "tot_rev": null,
    "amp_agp": null, "di_agp": null, "oth_agp": null, "agp": "adjusted gross profit / margin total",
    "amp_agp_pct": null, "di_agp_pct": null, "agp_pct": null,
    "amp_g": "reported growth %", "di_g": null, "tot_g": null, "amp_lfl": "like-for-like growth %", "di_lfl": null, "tot_lfl": null,
    "seg_note": "structure / basis in force (e.g. 2024 restated excl. Microwave Amplification)"
  },
  "ng": {
    "op": null, "dna_impair": "depreciation, amortisation and impairment net (first two lines of the D&A note)", "oth_inc_exp": null, "ebitda": null,
    "sbc": "share-based payment add-back", "nonrec": "non-recurring costs add-back", "adj_ebitda": null, "dna_ex_ppa": "D&A excluding PPA (and brand impairment)", "adj_ebit": null,
    "mgmt_cos": "cost of sales (management basis)", "mgmt_rd": "R&D costs", "mgmt_sga": "sales, general & administration", "mgmt_oth": null, "mgmt_rop": null,
    "cap_rd": "capitalised R&D costs", "capex": "capital expenditure excl. capitalised R&D", "capex_growth": null, "capex_maint": null, "cash_conv_pct": null,
    "fcf_pre_growth": null, "fcf": "free cash flow after growth capex (H1 reports)", "ni_ex_ppa": "net profit excluding PPA effects", "ni_cont_ex_ppa": null,
    "ni_ex_brand": "net profit excl. brand impairment (H1-26)", "adj_items_text": "verbatim description of the share-based payment and non-recurring items",
    "definition": "verbatim Adjusted EBITDA / Adjusted EBIT definition wording"
  },
  "dna": {"dna_ex_ifrs16": null, "dna_rou": null, "impair_current": null, "provisions": null, "total": null, "ppa_amort": "PPA amortisation if stated", "brand_impair": null},
  "fin": {"int_bank": null, "int_lease": null, "cost_net_debt": null, "fx": null, "deriv_inc": null, "deriv_exp": null, "deriv_net": null, "other": null, "net_fin": null},
  "tax": {"current": null, "deferred": null, "total": null, "etr_pct": null},
  "cf": {
    "ni": "starting line as printed (continuing ops from 2025)", "fin_cash": null, "fin_noncash": null, "tax": null, "dna_prov": null, "oth": null,
    "tax_paid": null, "wc": null, "cfo": null,
    "capex": "purchases of intangible assets and PP&E (negative)", "disposals": null, "acq": "acquisitions net of cash", "divest": null, "grants": null, "oth_fin_assets": null, "cfi": null,
    "sh_iss": null, "sh_iss_costs": null, "treasury": null, "div": "dividends paid", "conv_int": null, "ncb_in": null, "ncb_out": null, "cb_in": null, "cb_out": null,
    "int_paid": null, "lease_rep": null, "lease_int": null, "deriv_inc": null, "inv_inc": null, "loan_costs": null, "early_rep": null, "oth_fin": null, "cff": null,
    "fx": null, "net_change": null, "disc_cf": "cash flow from discontinued operations line (if printed)", "beg": null, "end": null,
    "lines_raw": [["exact label", "value as printed"]]
  },
  "bs": {
    "gw": null, "intang": null, "ppe": null, "rou": null, "eq_inv": null, "oth_nca": null, "dta": null, "tnca": null,
    "inv": null, "ar": null, "deriv_a": null, "oca": null, "cash": null, "tca": null, "ta": null,
    "sh_cap": null, "sh_prem": null, "reserves": null, "teq": null,
    "ncb": "non-current loans and borrowings", "ncll": "non-current lease liabilities", "pens": null, "oncl": null, "dtl": null, "tncl": null,
    "cb": "current loans and borrowings", "cll": null, "deriv_l": null, "ap": null, "ocl": "current provisions and other current liabilities", "tcl": null, "tle": null,
    "shares_out": "shares in issue at period end (units)", "treasury": "treasury shares (units)",
    "lines_raw": [["exact label", "value"]]
  },
  "debt": {"tlb": "Term Loan B carrying amount", "tlb_gross": null, "leases": null, "oth_liab": null, "accrued_int": null, "overdraft": null, "gross_debt": null,
           "cash": null, "net_debt": null, "adj_ebitda_lev": "Adjusted EBITDA (pro forma if stated) used for leverage", "leverage_x": null, "rcf_drawn": null,
           "legacy_debt": "pre-IPO bonds / loans (2021–23): label and amount"},
  "equity": {"sbc_ifrs2": null, "capital_increase": null, "dividends": null, "treasury_adj": null, "other": null},
  "extra": {"employees": null, "dps_declared": "€ per share for the year", "acquisitions": [["name", "close date", "consideration €m", "goodwill €m", "segment", "revenue contribution"]],
            "divestitures": [["name", "date", "notes"]], "guidance": "verbatim outlook text", "events": "other significant events",
            "intangibles_net": {"dev_tech": null, "software": null, "cust_brands": null, "other": null}, "amort_intang": null, "dep_ppe": null, "dep_rou": null},
  "py": {"restated": false, "notes": null, "is": {}, "seg": {}, "ng": {}, "cf": {}, "bs": {}},
  "notes": "computed values; any self-check that does not pass and why"
}
```

Press-release KPIs go in `data/releases.json` (one object per release): quarterly revenue by segment (Q1 / Q3 and the 9M
tables), reported / like-for-like / scope / FX growth by segment and group, adjusted gross margin by segment (H1, 9M, FY),
adjusted EBITDA, adjusted EBIT, net profit excl. PPA, free cash flow, net debt and leverage, guidance wording, and the
reporting basis of each table (originally reported vs restated).

## Self-checks before writing each period
Re-read the source if any of these fail, and report any failure that remains, with the reason, in `notes`.
- **IS:** rev + cos + ext + taxes + staff + oth_op_inc + oth_op_exp + dna_prov = rop; rop + oth_inc + oth_exp = op;
  op + cost_net_debt + deriv + fin_oth = ebt (net_fin = cost_net_debt + deriv + fin_oth); ebt + tax = ni_cont; ni_cont + disc = ni (±0.002).
- **Segments:** amp_rev + di_rev + elim_rev = tot_rev = is.rev (±0.15); amp_agp + di_agp + oth_agp = agp (±0.15).
- **Bridge:** op + dna_impair + oth_inc_exp = ebitda; ebitda + sbc + nonrec = adj_ebitda; adj_ebitda + dna_ex_ppa = adj_ebit (±0.15).
- **Cash flow:** sum of operating lines = cfo; sum of investing lines = cfi; sum of financing lines = cff; cfo + cfi + cff + fx (+ disc_cf) = end − beg (±0.002).
- **Balance sheet:** tnca + tca = ta; teq + tncl + tcl = tle = ta; components sum to subtotals (±0.002).
- **EPS:** ni ÷ wsh ≈ eps_basic (±0.01).
