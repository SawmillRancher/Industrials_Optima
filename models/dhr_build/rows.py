"""Row registry helper for inspection scripts: R[key] -> Model row number (rebuilds the spec without writing a workbook)."""
import fw, build
build.scen_layout(build.V0); build.build_spec(build.V0); build.build_spec2(build.V0); fw.number_rows(8)
R = fw.R
