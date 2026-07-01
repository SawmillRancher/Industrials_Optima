"""SEC-filings financial model builder (Copart and other industrials).

Pulls company financials exclusively from SEC EDGAR (XBRL company facts plus the
XBRL instance documents filed with each 10-K / 10-Q) and renders a multi-tab,
Moog-style Excel model covering 15 years of annual and quarterly history,
including all reported operating segments.
"""

from .build import build_copart_model

__all__ = ["build_copart_model"]
