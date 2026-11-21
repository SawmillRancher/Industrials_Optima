"""FedEx earnings-release / recast-exhibit parser (text from h2t.py: one table row per line, cells joined by ' | ').

parse(text) -> list of entries {sec, ctx, label, cells, vals}:
  sec  : table the row belongs to, identified from the heading lines above it:
         is (consolidated income statement / financial highlights), bs, cf, recon (non-GAAP reconciliations), capex,
         exp (FedEx Express segment), tnt (TNT Express), gnd (FedEx Ground), frt (FedEx Freight), kin (FedEx Kinko's / Office),
         fec (Federal Express segment, FY2025-26), usd (Express U.S. Domestic), intl (Express International)
  ctx  : the (up to four) text lines directly above the row (sub-headings such as 'Average Daily Package Volume (000s):')
  vals : numeric cells (same positions as cells); '(1,234' and '(1,234)' are negative, an em dash is 0.0, 'NM' and text are None.
Known quirks handled: dropped ')' after negatives, '%)' / 'pts)' cells, headings split over several lines."""
import re

DROP = {'', '$', ')', '%', ')%', '%)', 'pts)', 'pts', 'pt', 'bp', 'bps'}
DASH = {'—', '–', '-', '— —', '—%', '-%'}

def num(c):
    c = c.strip()
    if c in DASH: return 0.0
    t = c.replace('$', '').replace(',', '').replace('%', '').strip()
    neg = t.startswith('(') or t.endswith(')')
    t = t.strip('()').strip()
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

SEGS = [('U.S. DOMESTIC', 'usd'), ('EXPRESS INTERNATIONAL', 'intl'), ('FEDERAL EXPRESS', 'fec'), ('TNT EXPRESS', 'tnt'),
        ('EXPRESS SEGMENT', 'exp'), ('GROUND SEGMENT', 'gnd'), ('FREIGHT SEGMENT', 'frt'), ('KINKO', 'kin'), ('OFFICE SEGMENT', 'kin'),
        ('FEDEX CORP', 'is'), ('FEDEX CORPORATION', 'is'), ('CONSOLIDATED', 'is')]

KEYS = re.compile(r'RECONCILIATION|EARNINGS PER SHARE FORECAST|BALANCE SHEET|CASH FLOWS|CAPITAL EXPENDITURES|HIGHLIGHTS|STATEMENTS? OF INCOME|OPERATING STATISTICS')

def classify(win, cur):
    """Heading = the short lines above the row (long footnote / narrative lines ignored; headings may be split one word per line);
    the text around the last table keyword decides the section."""
    keep = [w for w in win if len(w) < 70 and not re.match(r'^\(?\d+\)? ?[–-] ', w) and not (w.endswith('.') and len(w) > 12)]
    h = re.sub(r'\s+', ' ', ' '.join(keep).upper())[-400:]
    ms = list(KEYS.finditer(h))
    if not ms: return cur
    m = ms[-1]; k = m.group(0); near = h[max(0, m.start() - 58): m.end() + 45]
    if 'RECONCILIATION' in near or 'FORECAST' in k: return 'recon'
    if 'BALANCE SHEET' in k: return 'bs'
    if 'CASH FLOWS' in k: return 'cf'
    if 'CAPITAL EXPENDITURES' in k: return 'capex'
    for kk, s in SEGS:
        if kk in near: return s
    return cur

def parse(text):
    out, win, sec = [], [], None
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if ' | ' not in line:
            win.append(line); continue
        if win:
            sec = classify(win, sec)
            ctx = [w for w in win[-4:]]
            win = []
        cells = [c.strip() for c in line.split(' | ')]
        cells = [c for c in cells if c not in DROP]
        merged, neg = [], False
        for c in cells:                       # '($ | 895' = negative 895 (opening parenthesis in its own cell)
            if c in ('($', '$(', '(', '$ (', '( $'): neg = True; continue
            merged.append('(' + c if neg and not c.startswith('(') else c); neg = False
        cells = merged
        if not cells: continue
        label, rest = cells[0], cells[1:]
        if label and label[0].islower() and ctx and len(ctx[-1]) < 60:      # label wrapped over two lines ('FedEx Express' / 'segment | ...')
            label = ctx[-1] + ' ' + label; ctx = ctx[:-1]
        label = re.sub(r'(?<=[A-Za-z\)’\'])\s*(\(\d\)|\d)(\s*,\s*\d?)?\s*,?$', '', label)   # footnote markers
        if num(label) is not None and not re.search(r'[A-Za-z]', label):
            rest, label = cells, ''
        out.append({'sec': sec, 'ctx': ctx, 'label': re.sub(r'\s+', ' ', label), 'cells': rest, 'vals': [num(c) for c in rest]})
    return out

if __name__ == '__main__':
    import sys
    for e in parse(open(sys.argv[1]).read()):
        print(e['sec'], '|', ' / '.join(e['ctx'])[-60:], '|', e['label'][:50], '|', e['vals'])
