# THEON data extraction: schema and rules

Adapted from `templates/EXTRACTION_SCHEMA_TEMPLATE.md` for an IFRS, EUR, non-SEC issuer whose statements are PDFs. Extraction is scripted (`extract.py` + `parse_stmt.py`), not done by hand; this file documents what the scripts store, so a re-extraction or a manual correction follows the same rules.

## Sources
- **Theon is not an SEC registrant.** EDGAR (CIK 0002095508) holds only Schedule 13G filings about its Kopin stake. The user accepted regulator-filed documents in lieu of EDGAR filings for a foreign issuer, so the historical figures come from Theon's own regulated disclosures at `media.theon.com`, listed in `doc_urls.txt` and `filings.csv`:
  - annual reports FY2021–25 (FY2023 restates FY2022 and the 1-Jan-2022 balance sheet; FY2025 restates FY2024 for the associates policy);
  - semi-annual reports H1-24, H1-25, H1-26;
  - Q1 and 9M trading updates, which carry condensed statements of profit or loss, financial position and cash flows plus the APM reconciliation;
  - results / trading-update press releases (order intake, backlog, EPS, guidance) and deal releases (`manual_items.json`).
- **Text versions:** `fetch.py` downloads the PDFs to `$THEON_SRC/pdf` and converts them with `pdftotext -layout` to `$THEON_SRC/txt`. Raw files are never committed.
- **Nothing from third-party summaries** (news sites, aggregators, broker notes) and nothing from call transcripts except as labelled, unverified guidance context.

## Parsing rules (`parse_stmt.py`)
- A text line is split into cells on runs of 2+ spaces; a segment is a label followed by its numbers. Annual and semi-annual reports print two statements side by side, so each document spec gives character-column cuts (`(first_line, last_line, c0, c1)`).
- Numbers: `1,234,567` (comma documents) or `1.234.567` (dot documents: AR2023, Q1-24 update), `(x)` negative, `–`/`-` zero. Integers ≤ 31 or 1900–2100 are dates, not amounts. Decimal-marked numbers (EPS) are kept as printed; whole euros are stored in EUR m to 6 dp.
- An unlabeled value line borrows the label of the text line above (labels that wrap). Trailing note references (`10.`, `11c.`, `9`) are stripped. Ligatures (ﬁ, ﬀ) and the missing-"ti" glyph are repaired.

## Stored record (`data/<period>.json`)
Period keys: `2020`–`2025`, `Q1-yy`, `H1-yy`, `9M-yy` (year-to-date, as printed). Each record holds the figures of the document that first presented the period, plus every later comparative under `cmp[<doc id>]`.

```json
{
  "period": "H1-25", "months": 6, "source_doc": "H1-25",
  "sources": {"doc": "theon-group-semi-annual-report-30-06-2025", "url": "https://media.theon.com/..."},
  "is":  {"rev", "cogs", "gp", "oinc", "ogain", "admin", "sell", "rnd", "imp", "oexp", "assoc", "assoc_pos": "in_op | below_op",
          "op", "finc", "fcost", "netfin", "ebt", "taxc", "taxd", "ni", "ni_par", "nci", "eps_b", "eps_d"},
  "bs":  {"ppe", "intang", "rou", "invprop", "assoc_bs", "ltloan", "onca", "ofa", "dta", "tnca", "inv", "ar", "orec", "ofa_c", "prep", "td", "cash", "tca", "ta",
          "eqp", "nci_bs", "te", "debt", "bbl", "sri", "lease", "grants", "dtl", "accr", "tncl", "ap", "lease_c", "debt_c", "bbl_c", "cl", "itp", "accr_c", "tcl", "tl", "tle"},
  "cf":  {"start", "noncash", "wc", "wc_lines", "cashgen", "noncash_derived", "taxp", "intp", "cfo", "capex", "acq", "cfi", "debt_pro", "debt_rep",
          "lease_cf", "eq_iss", "buyback", "div", "cff", "net", "beg", "fx", "end", "other_lines"},
  "ng":  {"ebit_pub", "nri", "adj_ebit", "adj_ebitda"},
  "rev": {"region": {"europe", "asia", "americas", "africa", "oceania"}, "product": {"night", "thermal", "platform", "isr", "misc", "other"}},
  "cmp": {"<later doc id>": {"is": {}, "bs": {}, "cf": {}, "ng": {}, "rev": {}}}
}
```

- **Signs: as printed.** Income and inflows positive, expenses and outflows negative (e.g. `cogs` −298.664). `normalize.py` flips expenses to positive model keys.
- **Null vs zero:** a printed `–` is 0.0; a line not printed is absent. Nothing is estimated.
- **Suffixes:** `_c` marks the current-liability / current-asset occurrence of a label that appears twice (loans, leases, buy-back liability, other financial assets).
- **Derived values** (all labelled): `noncash_derived` = cash generated before working capital − profit (full statements); `nri` = adjusted EBIT − EBIT (equals the printed non-recurring line; Q1-26 prints the amount above its label).

## Manual items (`manual_items.json`)
Order intake (YTD), soft backlog and options; Q1 EPS printed only in releases; weighted shares, H1 EPS, NCI profit and fair-value gains from the notes; dividends; restatement wording; the restated Q1-25 adjusted EBIT / EBITDA; guidance history; deal terms (Harder Digital, Kappa, Exosens, MERIO, HGH, other investments); capital events (IPO, rights issue, buy-back programme, RCF, HGH term loan); the share price basis. Every item carries its source URL.

## Self-checks (`check_data.py`)
- **IS:** gross profit; operating profit (lines + share of associates when presented inside); EBT (+ associates when presented below); net income (±0.0011 €m).
- **BS:** non-current + current assets = total assets; equity + liabilities = total; TA = TL&E.
- **CF:** CFO + CFI + CFF = net change; beginning + net change + FX = ending cash; cash generated − tax − interest = CFO.
- **APM:** printed EBIT = operating profit; Σ products and Σ regions = revenue.
- **Quarter sums:** Σ Q1–Q4 = FY for revenue, operating profit, net income, CFO / CFI / CFF, D&A and published adjusted EBIT.
- **Explained exceptions** are listed in `check_data.py` (`EXCEPT`) and in the README.
