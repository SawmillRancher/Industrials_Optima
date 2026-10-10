"""Forecast inputs (blue cells) for the Hermès model. All are analyst assumptions unless a source is cited.

Scenario-dependent drivers (constant-currency growth by métier, gross margin, recurring operating margin, buybacks,
exceptional dividends, payout) live in scenario.py; the values here apply to every case.
"""

Y = (2026, 2027, 2028, 2029, 2030)


def by_year(*vals):
    return dict(zip(Y, vals))


# share price: Euronext close 2-Oct-2026 (Hermès IR site quote feed, finance.hermes.com)
PX = 1299.5
PX_NOTE = ("Share price €1,299.50 = Euronext Paris close on 2-Oct-2026 (quote feed on finance.hermes.com); market cap "
           "€137.2bn on 105.57m shares. Update as needed.")

ASSUMP = {
    # revenue: currency effect on reported growth (group, all métiers); 2026E H2 point estimate is in the scenario table
    "fx": by_year(None, 0.0, 0.0, 0.0, 0.0),
    "fx_note": ("2027E+: no currency effect assumed (constant-currency growth = reported growth). H1/26: −4.5 pts "
                "(> €360m negative impact on revenue)."),
    # P&L cost drivers
    "oie_pct": by_year(0.069, 0.069, 0.069, 0.069, 0.069),
    "oie_note": ("Other income and expenses (net, incl. D&A booked outside cost of sales, free-share plan expense, "
                 "provisions) % of revenue: 6.9% in 2025 (€1,106m), 6.8% in H1/26. Sales & administrative expenses are "
                 "the balancing line to the recurring-operating-margin lever."),
    "da_pct": by_year(0.037, 0.037, 0.037, 0.037, 0.037),
    "da_note": ("D&A of PP&E and intangibles incl. impairment (excl. right-of-use) % of revenue: 3.6% in 2025 "
                "(€575m), 3.6% in H1/26; capacity build-out (leather workshops 2026–30) keeps it rising."),
    "sbc_pct": by_year(0.0082, 0.0082, 0.0082, 0.0082, 0.0082),
    "assoc": by_year(None, 50.0, 52.0, 54.0, 56.0),
    "nci_pct": by_year(0.005, 0.005, 0.005, 0.005, 0.005),
    "etr": by_year(None, 0.285, 0.285, 0.285, 0.285),
    "etr_note": ("2027E+: 28.5% = 2025 ETR excluding the French exceptional contribution (company); the contribution "
                 "is assumed not renewed after 2026."),
    "cash_yield": by_year(0.020, 0.020, 0.020, 0.020, 0.020),
    "cash_note": ("Return on opening restated net cash: 2025 (net financial income €207m + lease interest €55m) / "
                  "opening restated net cash €12.0bn = 2.2%; 2.0% assumed with lower euro rates."),
    "lease_rate": by_year(0.026, 0.026, 0.026, 0.026, 0.026),
    # cash flow
    "capex_pct": by_year(None, 0.070, 0.068, 0.066, 0.064),
    "capex_note": ("Operating investments % of revenue: 7.3% (2025, €1,161m), 7.0% (2024); leather workshops "
                   "(Charleville-Mézières 2027, Colombelles 2028, Les Andelys 2030), Le Noirmont watch site (2028)."),
    "oinv": by_year(None, -100.0, -100.0, -100.0, -100.0),
    "oinv_note": ("Financial investments in partners (vertical integration) net of dividends received: 2025 −€0.2bn "
                  "acquisitions of financial assets, +€75m dividends received."),
    "div_h2_26": -30.0,
    "new_leases": by_year(0.035, 0.035, 0.035, 0.035, 0.035),
    "lease_note": ("New leases (ROU additions) % of revenue — 2025: ROU €1,786m → €2,002m after €351m depreciation "
                   "(≈ €570m additions incl. FX). Lease repayments ≈ ROU depreciation."),
    "rou_dep": by_year(0.195, 0.195, 0.195, 0.195, 0.195),
    # working capital
    "d_inv": by_year(200.0, 200.0, 200.0, 200.0, 200.0),
    "d_ar": by_year(10.0, 10.0, 10.0, 10.0, 10.0),
    "d_ap": by_year(62.0, 62.0, 62.0, 62.0, 62.0),
    "taxl_pct": by_year(0.25, 0.25, 0.25, 0.25, 0.25),
    # shares
    "bb_issued": by_year(0.08, 0.08, 0.08, 0.08, 0.08),
    "dil_sec": by_year(0.20, 0.20, 0.20, 0.20, 0.20),
    "px_g": by_year(None, 0.07, 0.07, 0.07, 0.07),
}
