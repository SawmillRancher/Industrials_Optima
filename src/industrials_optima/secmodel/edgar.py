"""SEC EDGAR client for downloading company facts, submissions and filing XBRL.

All data used by the financial model comes exclusively from SEC EDGAR
(https://www.sec.gov / https://data.sec.gov).  The client is deliberately
polite: it sends a descriptive User-Agent and throttles requests to stay
within the SEC fair-access guidelines (<10 requests/second).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

import requests

SEC_DATA = "https://data.sec.gov"
SEC_WWW = "https://www.sec.gov"

# SEC asks that automated tools identify themselves with a contact address.
DEFAULT_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT", "Industrials Optima Research payton.liske@gmail.com"
)


class EdgarClient:
    """Thin, cached HTTP client for SEC EDGAR endpoints."""

    def __init__(
        self,
        cik: str,
        cache_dir: str | os.PathLike,
        user_agent: str = DEFAULT_USER_AGENT,
        min_interval: float = 0.15,
    ) -> None:
        # EDGAR keys everything on a zero-padded 10 digit CIK.
        self.cik = str(int(cik)).zfill(10)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}
        )
        self.min_interval = min_interval
        self._last_request = 0.0

    # ------------------------------------------------------------------ #
    # low level fetch with on-disk caching + throttling
    # ------------------------------------------------------------------ #
    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.time()

    def _get(self, url: str, cache_name: str, binary: bool = False) -> str | bytes:
        cache_path = self.cache_dir / cache_name
        if cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path.read_bytes() if binary else cache_path.read_text("utf-8")

        for attempt in range(5):
            self._throttle()
            resp = self.session.get(url, timeout=60)
            if resp.status_code == 200:
                if binary:
                    cache_path.write_bytes(resp.content)
                    return resp.content
                cache_path.write_text(resp.text, "utf-8")
                return resp.text
            # 403/429 -> back off and retry
            time.sleep(2 ** attempt)
        resp.raise_for_status()
        raise RuntimeError(f"failed to fetch {url}")

    # ------------------------------------------------------------------ #
    # high level endpoints
    # ------------------------------------------------------------------ #
    def company_facts(self) -> dict:
        raw = self._get(
            f"{SEC_DATA}/api/xbrl/companyfacts/CIK{self.cik}.json",
            "companyfacts.json",
        )
        return json.loads(raw)

    def submissions(self) -> dict:
        raw = self._get(
            f"{SEC_DATA}/submissions/CIK{self.cik}.json", "submissions.json"
        )
        return json.loads(raw)

    def filing_index(self, accession: str) -> dict:
        acc_nodash = accession.replace("-", "")
        raw = self._get(
            f"{SEC_WWW}/Archives/edgar/data/{int(self.cik)}/{acc_nodash}/index.json",
            f"index_{acc_nodash}.json",
        )
        return json.loads(raw)

    def instance_url(self, accession: str) -> Optional[str]:
        """Locate the XBRL *instance* document within a filing.

        The instance is the ``.xml`` file that is **not** one of the linkbase
        files (``_cal``/``_def``/``_lab``/``_pre``), the schema (``.xsd``),
        ``FilingSummary.xml`` or a rendered ``R*.xml`` report.  Returns ``None``
        for filings that pre-date Copart's XBRL adoption.
        """
        acc_nodash = accession.replace("-", "")
        try:
            idx = self.filing_index(accession)
        except Exception:
            return None
        candidates = []
        for item in idx.get("directory", {}).get("item", []):
            name = item["name"]
            low = name.lower()
            if not low.endswith(".xml"):
                continue
            if any(s in low for s in ("_cal", "_def", "_lab", "_pre")):
                continue
            if low.startswith("r") and low[1:2].isdigit():
                continue
            if low in ("filingsummary.xml",):
                continue
            candidates.append(name)
        if not candidates:
            return None
        # Prefer the conventional "cprt-YYYYMMDD*.xml" / "*_htm.xml" instance.
        candidates.sort(key=lambda n: (0 if "cprt" in n.lower() else 1, len(n)))
        chosen = candidates[0]
        return (
            f"{SEC_WWW}/Archives/edgar/data/{int(self.cik)}/{acc_nodash}/{chosen}"
        )

    def instance_document(self, accession: str) -> Optional[str]:
        url = self.instance_url(accession)
        if not url:
            return None
        acc_nodash = accession.replace("-", "")
        fname = url.rsplit("/", 1)[-1]
        raw = self._get(url, f"inst_{acc_nodash}_{fname}")
        return raw if isinstance(raw, str) else raw.decode("utf-8", "replace")
