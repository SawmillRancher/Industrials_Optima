"""Industrial 3-statement financial model template generator.

Modeled on the Moog Inc. workbook (Model / Bull-Base-Bear / DCF / Charts).
The generator takes a CompanyConfig, strips Moog-specific hardcoded values
from the base template, parameterizes labels, and writes an Excel workbook
ready to be populated from SEC filings.
"""

from .config import CompanyConfig, SegmentLine
from .builder import build_template

__all__ = ["CompanyConfig", "SegmentLine", "build_template"]
