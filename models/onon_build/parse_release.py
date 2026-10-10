"""Table reader for On Holding release / MD&A text (h2t output): splits a document into tables, reads the period-group
headers ("Year ended" / "Three-month period ended" / "Six-month" / "Nine-month" / balance-sheet dates) and maps each value
to (group, year, class) so the extractor can pick the current-period column without relying on fixed positions."""
import re

NUM = re.compile(r'^\(?-?[\d,]*\.?\d+\)?$')

def num(s):
    s = s.strip().replace('—', '').replace('–', '')
    if s in ('', '-'): return 0.0 if s == '' else None
    if not NUM.match(s): return None
    neg = s.startswith('(')
    v = float(s.strip('()').replace(',', ''))
    return -v if neg else v

def is_dash(s): return s.strip() in ('—', '–', '—')

def group_kind(text):
    t = text.lower()
    if 'three-month' in t or 'three months' in t: return '3M'
    if 'six-month' in t or 'six months' in t: return '6M'
    if 'nine-month' in t or 'nine months' in t: return '9M'
    if 'year ended' in t or 'fiscal year' in t or 'twelve' in t or 'for the year' in t: return 'FY'
    return None

def tables(text):
    """Yield dict(ctx, unit, cols, rows) for each table that has a '(CHF in ...)' header."""
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('(CHF in') or ln.startswith('(in CHF'):
            unit = 0.001 if 'thousand' in ln else 1.0
            hdr = [c.strip() for c in ln.split('|')[1:]]
            # group line(s) above the header
            groups = []
            for back in (1, 2, 3):
                if i - back < 0: break
                g = lines[i - back]
                kinds = [group_kind(x) for x in g.split('|')]
                kinds = [k for k in kinds if k]
                if kinds: groups = kinds; break
            ctx = ' '.join(lines[max(0, i - 6):i])
            j = i + 1
            classes = None
            rows = []
            while j < len(lines):
                if '|' not in lines[j]:
                    # bridge short caption lines inside a table ("Exclude the impact of:", "Adjustments for:", "Earnings per share")
                    nxt = lines[j + 1] if j + 1 < len(lines) else ''
                    if len(lines[j].strip()) < 45 and '|' in nxt and not nxt.startswith('(CHF') and group_kind(nxt) is None \
                            and not lines[j].strip().startswith('Unaudited') and 'period ended' not in lines[j]:
                        j += 1; continue
                    break
                cells = [c.strip() for c in lines[j].split('|')]
                if cells[0] in ('Class A',) or (cells[0] == '' and 'Class A' in cells):
                    classes = [c for c in cells if c.startswith('Class')]
                elif cells[0].startswith('(Audited') or cells[0].startswith('(Unaudited'):
                    pass
                else:
                    rows.append(cells)
                j += 1
            yield dict(ctx=ctx, unit=unit, hdr=hdr, groups=groups, classes=classes, rows=rows, line=i)
            i = j
        else:
            i += 1

def colmap(t):
    """List of column descriptors: (group, year_token, kind) where kind in {'v','pct','cc'}; class labels attached for adj NI tables."""
    hdr, groups = t['hdr'], t['groups'] or [None]
    cols = []
    gi = -1; seen_years = []
    for h in hdr:
        hl = h.lower()
        if 'constant currency' in hl: cols.append(('cc', None)); continue
        if '%' in hl or 'change' in hl: cols.append(('pct', None)); continue
        cols.append(('v', h))
    # assign groups: a new group starts when the year sequence restarts (value col after a pct col, or repeated pattern)
    out = []
    ng = len(groups)
    vals = [c for c in cols if c[0] == 'v']
    per_group = max(1, len(vals) // ng) if ng else len(vals)
    vi = 0
    for kind, tok in cols:
        if kind == 'v':
            g = groups[min(vi // per_group, ng - 1)] if ng else None
            out.append((g, tok, 'v')); vi += 1
        else:
            g = groups[min(max(vi - 1, 0) // per_group, ng - 1)] if ng else None
            out.append((g, None, kind))
    if t['classes']:
        cl = t['classes']
        out = [(g, tok, k, cl[n] if n < len(cl) else None) for n, (g, tok, k) in enumerate(out)]
    else:
        out = [(g, tok, k, None) for (g, tok, k) in out]
    return out

def row_values(t, cells):
    """Map a data row onto the column descriptors. Exact match on count; otherwise drop pct/cc columns; otherwise left-align
    the first group only (returns partial)."""
    cm = colmap(t)
    vals = cells[1:]
    if len(vals) == len(cm):
        return [(c, num(v)) for c, v in zip(cm, vals)]
    vonly = [c for c in cm if c[2] == 'v']
    if len(vals) == len(vonly):
        return [(c, num(v)) for c, v in zip(vonly, vals)]
    # Basic EPS Class B style rows: '—' placeholders with a missing pct; left-align values of the first group
    g0 = cm[0][0]
    res = []
    for c, v in zip(cm, vals):
        if c[0] != g0: break
        res.append((c, num(v)))
    return res

def label(cells):
    return re.sub(r'\s*\(\d\)\s*$', '', cells[0]).strip()
