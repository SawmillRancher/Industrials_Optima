"""Parse a Loar earnings release (8-K Ex. 99.1, text form) into its numbered tables.

Each table: {'title', 'rows': [(label, [values], block_header)], 'hdr': [...]}. block_header is the most recent
"Three/Six/Nine Months Ended" / "Year(s) Ended" line seen inside the table (end-market tables come in two blocks).
"""
import re

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').strip()
    if t in ('—', '–', '-', '―'): return 0.0
    neg = t.startswith('(')
    t = t.strip('()').replace(',', '')
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v

BLOCK = re.compile(r'(Three|Six|Nine|Twelve) Months Ended|Years? Ended', re.I)

def parse_tables(txt):
    out, cur, blk = {}, None, ''
    for line in txt.splitlines():
        m = re.match(r'^\s*Table\s*[–-]?\s*(\d)\s*:?', line)
        if m:
            cur = int(m.group(1)); blk = ''
            out[cur] = {'title': line.strip(), 'rows': [], 'hdr': []}
            continue
        if cur is None: continue
        if BLOCK.search(line) and len(line) < 160:
            blk = line.strip()
        if '|' not in line:
            if line.strip(): out[cur]['hdr'].append(line.strip())
            continue
        cells = [c.strip() for c in line.split('|')]
        lab, vals = cells[0], [pnum(c) for c in cells[1:]]
        if pnum(lab) is not None or not vals or any(v is None for v in vals):
            out[cur]['hdr'].append(line.strip()); continue
        out[cur]['rows'].append((lab, vals, blk))
    return out

def organic(txt):
    """Organic net sales sentences: [(growth %, $m increase, $m organic sales), ...] in order of appearance."""
    t = re.sub(r'\s+', ' ', txt)
    res = []
    for m in re.finditer(r'Organically[^$]{0,60}?net sales increased ([\d.]+)% or \$([\d.]+) million, to \$([\d.]+) million', t):
        res.append((float(m.group(1)) / 100, float(m.group(2)), float(m.group(3))))
    return res
