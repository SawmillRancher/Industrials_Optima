"""Parse the 2026-format L3Harris earnings release text ($LHX_SRC/txt) into tables: {'SUM' | 'T<n>': {'title', 'rows': [(label, [values], [raw cells])]}}.
Rows are 'label | v1 | v2 ...'; '(1,234)' / '(1,234' -> -1234; '—' -> 0.0; footnote digits after labels are stripped."""
import re, os
S = os.environ.get('LHX_SRC', '/tmp/lhx_src')

def pnum(t):
    t = t.strip().replace('$', '').replace('%', '').replace(' ', '')
    if t in ('—', '–', '-'): return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?', t): return None
    return -float(t) if neg else float(t)

def tables(fn):
    out = {}; cur = None
    for line in open(os.path.join(S, 'txt', fn)).read().split('\n'):
        m = re.match(r'\s*Table (\d+) - (.*)', line)
        if m: cur = f'T{m.group(1)}'; out[cur] = {'title': m.group(2), 'rows': []}; continue
        if line.startswith('SUMMARY FINANCIAL RESULTS'): cur = 'SUM'; out[cur] = {'title': 'summary', 'rows': []}; continue
        if line.startswith(('PAGE', 'Forward-Looking', 'SEGMENT RESULTS')):
            if cur == 'SUM': cur = None
            continue
        if cur and ' | ' in line:
            cells = [c.strip() for c in line.split(' | ')]
            lab = re.sub(r' \(see Table \d\)', '', cells[0]); lab = re.sub(r'\s+\d$', '', lab); lab = re.sub(r'\s+\d(?= \()', '', lab)
            out[cur]['rows'].append((lab, [pnum(c) for c in cells[1:]], cells[1:]))
    return out
