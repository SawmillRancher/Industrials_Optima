"""Command-line entry point: build the Copart SEC-filings Excel model.

Usage::

    python -m industrials_optima.secmodel.build [--out PATH] [--cache DIR] [--first-fy YEAR]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .edgar import EdgarClient
from .model import COPART_CIK, CopartModel
from .workbook import WorkbookBuilder


def build_copart_model(
    out_path: str | Path = "models/Copart_SEC_Model.xlsx",
    cache_dir: str | Path = ".sec_cache/copart",
    first_fy: int = 2011,
) -> Path:
    """Download Copart's SEC data, assemble it and write the Excel model.

    Returns the path to the written workbook.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    client = EdgarClient(COPART_CIK, cache_dir)
    model = CopartModel(client)
    print("• Downloading consolidated XBRL company facts …")
    model.load_consolidated()
    print("• Downloading & parsing filing instances for segment data …")
    model.load_segments()
    model.build_periods(first_fy=first_fy)
    print(
        f"• Assembled {len(model.annual_ends)} fiscal years "
        f"and {len(model.quarter_ends)} quarters."
    )
    wb = WorkbookBuilder(model).build()
    wb.save(out_path)
    print(f"• Wrote {out_path}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Copart SEC-filings Excel model")
    ap.add_argument("--out", default="models/Copart_SEC_Model.xlsx")
    ap.add_argument("--cache", default=".sec_cache/copart")
    ap.add_argument("--first-fy", type=int, default=2011)
    args = ap.parse_args()
    build_copart_model(args.out, args.cache, args.first_fy)


if __name__ == "__main__":
    main()
