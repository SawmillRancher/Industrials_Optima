# MBGL data extraction: schema and rules

This file is derived from `templates/EXTRACTION_SCHEMA_TEMPLATE.md`. Extraction is scripted (`extract.py`) because there are few periods. The rules below are what the script implements.

## Sources
- **SEC EDGAR only.** Mobility Global, CIK 0002090312 ("S&P Global Mobility Holding Co" until Jan-2026). S&P Global, CIK 0000064040, for the Mobility segment memo. Investor-relations sites are blocked; the releases are the 8-K exhibits.
- **Text versions** of every document are in `$MBGL_SRC/txt`, named `<registrant>_<filing date>_<form>_<document>.txt`. Each table row is on one line with its cells joined by ` | `. `extract.py` drops empty, zero-width and non-breaking cells. URLs are in `filings.csv` and are recorded in each record's `sources`.
- **Text quirks:**
  - "(25 )" is negative.
  - "—" / "-" means zero.
  - `%` cells are dropped, which matters for the column index of twelve-month columns in S&P Global Q4 releases.
  - Footnote markers in labels ("Other (1)") must be allowed for.
- **Ex. 99.2 (FY2025 quarterly data)** is slide images with a hidden 1-pt text layer that loses blank cells. Read the slide images (`exhibit992002.jpg`, `exhibit992003.jpg`) and transcribe them. Then check that every segment column re-adds to its published Adjusted EBITDA.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Periods** use the carve-out (combined) statements, as filed:
  - FY2023–25 from the Form 10 audited statements;
  - Q1-25 / Q1-26 from the Form 10 interims;
  - Q2-25 / Q2-26 from the 10-Q three-month columns;
  - Q3-25 / Q4-25 from Ex. 99.2.
- **Segment detail:** Form 10 MD&A reconciliations (FY, Q1) and the release Exhibits 4–5 (Q2). Where filed detail exists, it wins over Ex. 99.2: Ex. 99.2 groups the ELT transition cost into "other" and splits Q2-25 "severance and other".
- **Cash flow** is year to date (`cf.ytd_months` 3, 6 or 12); normalize.py derives Q2 = 1H − Q1. Q3 / Q4-25 are not published.
- **Balance sheets:** 31-Dec-2023 from the first Form 10 draft (DRS 23-Oct-2025); other year ends and Mar / Jun-2026 from the Form 10 / 10-Q.
- **Units:** USD millions, whole millions as published; shares in millions; per-share as published.
- **Signs:** costs positive; other income shown as presented ("Other income, net (1)" = income of 1, stored as `othinc_exp` = −1); cash flow as presented.
- **Null vs zero:** "—" = 0.0. A line not presented = absent (null). **Never estimate.** Per-share data exists only where the company printed a share count (Q2-25, Q2-26).

## Record layout (`data/<period>.json`)
```json
{
  "period": "Q2-26", "sources": ["https://..."], "notes": ["..."],
  "is": {"rev": 0, "opex": 0, "sga": 0, "dep": 0, "amort": 0, "da": "Q3/Q4-25 only", "op": 0, "othinc_exp": "FY only",
         "int": 0, "ebt": 0, "tax": 0, "ni": 0, "eps_basic": "Q2", "eps_dil": "Q2", "sh_basic": "Q2", "sh_dil": "Q2"},
  "seg": {"cfx|b2b|corp": {"rev": 0, "sub": 0, "nsub": 0, "us": 0, "intl": 0, "opex": 0, "sga": 0, "da": 0, "texp": 0, "op": 0,
          "amort": 0, "dep": 0, "sbc": 0, "trans": 0, "sev": 0, "sev_oth": 0, "integ": 0, "acqdisp": 0, "legal": 0, "elt": 0,
          "other": 0, "adjop": 0, "adj": 0}},
  "mix": {"rev": 0, "sub": 0, "nsub": 0, "us": 0, "intl": 0},
  "ng": {"adj_ebitda": 0, "adjop_total": 0, "adj_total": 0, "op_total": 0, "fcf": 0, "fcf_h1": "Q2", "labels": "company item wording",
         "ebitda_da": "Form 10 periods", "ebitda_int": "Form 10 periods"},
  "cf": {"ytd_months": 6, "ni": 0, "dep": 0, "amort": 0, "prov": 0, "def_tax": 0, "sbc": 0, "restr": 0, "cfo": 0, "capex": 0,
         "acq": 0, "eqinv": 0, "loan_in": 0, "disp": 0, "cfi": 0, "notes": 0, "transfers": 0, "loan_out": 0, "contingent": 0,
         "cff": 0, "fx": 0, "net": 0, "cash_begin": 0, "cash_end": 0},
  "bs": {"cash": 0, "due_from_c": 0, "ar": 0, "prepaid": 0, "tca": 0, "ppe": 0, "rou": 0, "gw": 0, "intang": 0, "due_from_nc": 0,
         "onca": 0, "ta": 0, "ap": 0, "due_to_c": 0, "accr": 0, "unearned": 0, "ocl": 0, "tcl": 0, "lease": 0, "dtl": 0,
         "due_to_nc": 0, "ltd": 0, "oncl": 0, "tl": 0, "pci": 0, "aoci": 0, "teq": 0, "tle": 0},
  "ex992": {"rev": 0, "opex": 0, "sga": 0, "da": 0, "op": 0, "int": 0, "ebt": 0, "tax": 0, "ni": 0},
  "spgi": {"rev": 0, "exp": 0, "op": 0, "op_ng": 0, "ng_adj": 0, "amort": 0, "adj_op": 0, "sub": 0, "nsub": 0},
  "guidance": {"rev": [0, 0], "rev_growth": [0, 0], "adj_ebitda": [0, 0], "date": "YYYY-MM-DD", "dps_q": 0}
}
```
- `spgi` for FY2022 holds `rev_pf`, `op_pf`, `adj_op_pf` and `rev_reported` (S&P Global non-GAAP pro forma; reported Mar–Dec).
- 2026 S&P Global releases have no Mobility non-GAAP schedule, so they carry rev / exp / op / sub / nsub only.

## Adjusting-item grouping (model rows)
| Model row | Company items |
|---|---|
| SBC | stock-based compensation |
| Transaction costs | stand-up of the spin business in connection with the separation |
| Severance & other | employee severance; acquisition integration; acquisition & disposition-related costs; ELT transition; legal settlement recovery; other (statutory labor-law accrual, lease impairment) |

The company wording per period is stored in `ng.labels` and written as a cell comment on the model's "severance & other" row.

## Self-checks (`check_data.py`, ±1 whole-$m rounding)
- **IS:** revenue − expenses = OP; OP − other − interest = EBT; EBT − tax = NI; NI / shares = EPS (±0.005).
- **Segments:**
  - Σ segment revenue = revenue; Σ segment OP (incl. corporate) = OP.
  - Segment OP + D&A + SBC + items = Segment Adjusted EBITDA; segment OP + amortization + items = segment Adjusted OP.
  - Subscription + non-subscription = revenue; U.S. + international = revenue.
- **Non-GAAP:** NI + interest + tax + D&A + SBC + items = Adjusted EBITDA (Form 10 reconciliation); Σ segment Adjusted EBITDA = consolidated.
- **Ex. 99.2:** vs filed statements (Q1-25, Q2-25, FY2025); Σ 2025 quarters = FY.
- **Cash flow:** CFO + CFI + CFF + FX = net change; beginning + net = ending; FCF = CFO + capex.
- **Balance sheet:** TA = TL&E; components sum to subtotals; BS cash = CF ending cash.
- **S&P Global:** revenue − expenses = OP; OP + adjustments + amortization = adjusted OP; subscription + non-subscription = revenue; Σ quarters = FY. The revenue difference vs the carve-out is reported as information.
