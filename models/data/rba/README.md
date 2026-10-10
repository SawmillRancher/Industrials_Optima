# RB Global (Ritchie Bros.) data-extraction spec

Company: RB Global, Inc. (formerly Ritchie Bros. Auctioneers Inc.), SEC CIK 0001046102. Fiscal year = calendar year.
Sources: SEC EDGAR only (www.sec.gov/Archives/edgar/data/1046102/...). Use a User-Agent header on every request:
`curl -sS -A "Industrials Optima research payton.liske@gmail.com" <url>` (EDGAR rejects requests without one; keep to <5 req/s).
Filing index JSON: https://www.sec.gov/Archives/edgar/data/1046102/<accession-no-dashes>/index.json
Filing list (with accession numbers, form types, primary docs): /tmp/claude-0/-home-user-Industrials-Optima/57d287ef-453d-572d-9db4-e0d79b45f5ce/scratchpad/filings.txt
(6-K rows pre-2016 are also in that file. For 8-K earnings releases use the EX-99.1 exhibit.)

Parse HTML with python (bs4 + lxml are installed; pandas.read_html works too). Prefer parsing tables programmatically over reading by eye. Save raw downloads under
/tmp/claude-0/-home-user-Industrials-Optima/57d287ef-453d-572d-9db4-e0d79b45f5ce/scratchpad/rba/raw/ (reuse files that are already there).

## Units & signs
- USD millions (convert from thousands if the filing is in $000s; keep 1 decimal or more, do not round to integers). Shares in millions. Per-share in USD.
- Revenue / expense lines: positive numbers as the magnitude (expenses positive).
- Lines that can be either sign (gains/losses, other income, FX, NCI): signed by their effect on income (gain/income = +, loss/expense = −).
- Cash flow: signed as presented in the cash-flow statement (outflows negative).
- If a value is not disclosed for a period, OMIT the key (do not write 0). Write 0 only when the filing shows "—"/nil for that line.
- Always use the LATEST filing that reports a period (i.e. recast/restated figures) unless told otherwise, and note restatements in `notes`.

## Period keys
Quarter: "Q1/13" … "Q4/25", "Q1/26", "Q2/26". Annual: "2006" … "2025". Six-month: "1H/26".
For quarterly-era years also give the annual FY figures (key "2015" etc.) from the 10-K / Q4 release so totals can be checked.
Q4 figures: take directly from the Q4 earnings release (three months ended Dec 31) when given; otherwise FY − 9M and say so in notes.

## Output JSON (one file per agent) — structure
```
{
  "periods": {
     "<period key>": {
        "is":   { <IS keys> },
        "ops":  { <operating-metric keys> },
        "adj_ebitda": { "ebitda_published": x, "adj_ebitda_published": x,
                        "items": [ {"label": "<company wording>", "cat": "<CAT>", "value": x}, ... ] },
        "adj_ni":     { "adj_ni_published": x, "adj_eps_published": x, "base": "<what GAAP line the company bridge starts from>",
                        "items": [ {"label": "...", "cat": "<CAT>", "value": x}, ... ] },
        "bs":   { <BS keys> },      # only where asked
        "cf":   { <CF keys> },      # only where asked
        "src":  ["<url>", ...]
     }
  },
  "notes": ["<free text: definition changes, basis/restatement notes, anything odd — cite period + url>"]
}
```
Adjusting items: `value` as the amount ADDED in the company's reconciliation (add-back of a cost = positive; removal of a gain = negative; tax effect usually negative).

## IS keys
service_rev, inv_sales_rev, total_rev, comm_rev (legacy "commissions"), fee_rev (legacy "fees"),
seller_rev (transactional seller revenue, 2023+), buyer_rev (transactional buyer revenue), mkt_services_rev (marketplace services revenue),
cost_services (costs of services / legacy "direct expenses"; excl. D&A), cost_inventory (cost of inventory sold),
sga, acq_costs (acquisition-related [and integration] costs), da (depreciation and amortization, total as on IS),
gain_disp_ppe (gain/(loss) on disposition of PP&E, signed), impairment (impairment loss, as a positive cost),
other_op (any other line inside operating income not listed, signed by income effect — give label in notes), op_income,
interest_exp (positive), interest_income (positive), other_income (other income (loss), net incl. equity income, signed),
fx (foreign exchange gain (loss), signed), other_nonop (any other non-operating line, signed — label in notes),
pretax, tax (expense positive), net_income, nci (net income attributable to NCI, signed as reported),
ni_controlling (net income attributable to controlling interests / stockholders),
pref_div (cumulative dividends on Series A Senior Preferred, positive), pref_alloc (allocated earnings to preferred, positive),
rnci_adj (adjustment of redeemable NCI, signed as it affects NI to common), ni_common (net income available to common stockholders),
shares_basic, shares_diluted (weighted avg, m), eps_basic, eps_diluted, dps_declared (dividends declared per share in the period).
Also: memo_debt_extinguishment (loss on debt extinguishment/ write-off of debt costs if embedded in interest or other lines, positive).

## Ops keys (operating metrics)
gtv (GTV; legacy "gross auction proceeds" GAP pre-2017; "GMV" 2017-2021 — note the label in notes),
gtv_auto, gtv_cct (CC&T, legacy sector basis 2023-24), gtv_other_legacy (Other on the legacy basis),
gtv_het (Heavy Equipment & Transportation, current basis), gtv_other (Other on current basis),
lots_total, lots_auto, lots_cct, lots_other_legacy, lots_het, lots_other (thousands of lots),
inventory_return, inventory_rate, service_take_rate (as published, fraction e.g. 0.20),
rev_us, rev_canada, rev_europe, rev_australia, rev_other_geo, rev_international (if only US/Canada/International given),
acq_revenue_contribution (revenue contributed by acquisitions in the period if disclosed; label which acquisition in notes),
num_auctions / bidders / buyers etc. only if easily available (optional).

## Adjusting-item categories (CAT)
SBC (stock-based compensation), ACQ (acquisition-related and integration costs), RESTR (restructuring / severance),
AMORT (amortization of acquired intangible assets), DISP ((gain)/loss on disposition of PP&E / sale of property, and related costs),
EXEC (executive transition / retention), DIVEST ((gain)/loss on divestiture / deconsolidation and related costs),
DEBT (debt refinancing / extinguishment / write-off of deferred financing costs), LEGAL (other legal, advisory and non-income-tax expense),
IMPAIR (impairment losses), FV (change in fair value of derivatives / hedges), TERM (merger termination costs / fees),
OTHER (any other pre-tax item — keep company label), TAX (tax effect of the adjustments), TAXD (discrete tax items: tax-law changes,
reorganisation, uncertain tax positions, valuation allowance), PREF (related allocation to Series A preferred), RNCI (adjustment of redeemable NCI),
D&A / INT / INTINC / TAXEXP for the EBITDA build lines (NI + D&A + interest expense − interest income + tax expense = EBITDA).

## BS keys (period end)
cash, restricted_cash, receivables, prepaid_consigned, inventory, advances_auction, other_current, tax_receivable, held_for_sale,
total_ca, ppe, rou (operating lease ROU), equity_investments, other_noncurrent, intangibles, goodwill, dta, total_assets,
auction_proceeds_payable, trade_other_liab, current_lease_liab, tax_payable, st_debt, current_ltd, held_for_sale_liab, total_cl,
lt_lease_liab, ltd, other_ncl, dtl, total_liab, temp_pref (Series A Senior Preferred, temporary equity), temp_rnci (redeemable NCI),
share_capital, apic, retained_earnings, aoci, equity_parent, nci, total_equity, total_le, shares_outstanding_end (m).
Make sure your components sum to the reported totals; put any residual in other_current / other_noncurrent / other_ncl and say so.

## CF keys (annual, and 1H/26 = six months)
net_income, da, sbc, deferred_tax, amort_debt_costs, gain_disp (as presented, usually negative for a gain), impairment, loss_deconsol,
other_noncash (all other non-cash adjustments), chg_wc (net changes in operating assets & liabilities — the total), cfo;
capex_ppe (property, plant & equipment additions, negative), capex_intangibles (intangible asset additions, negative),
proceeds_disp (proceeds on disposition of PP&E, positive), acquisitions (net of cash acquired, negative), other_investing, cfi;
debt_issued, debt_repaid, st_debt_net, debt_issue_costs, dividends_common, dividends_pref, buybacks, shares_issued (options/ESPP),
withholding_tax (tax withheld on SBC), other_fin, cff; fx_effect, chg_cash, cash_begin, cash_end,
cash_basis ("cash" or "cash+restricted" — what the CF statement reconciles).
Check: cfo + cfi + cff + fx_effect = chg_cash; components sum to subtotals (put residuals in other_* and say so).
