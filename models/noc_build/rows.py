"""Row registry of the NOC Model sheet without writing the workbook (for QA scripts): replays the row specification."""
import fw
from spec import scen_layout, build_spec
from spec2 import build_spec2
from build import V0

def registry():
    if not fw.SPEC:
        scen_layout(V0); build_spec(V0); build_spec2(V0); fw.number_rows(8)
    return fw.R
