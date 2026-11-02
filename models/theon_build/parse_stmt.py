"""Parse statement lines from pdftotext -layout output of Theon's reports.

A line can hold one or two statements side by side (annual-report spreads). Each line is split into segments
(label, [numbers]); a segment starts at a text cell and collects the numeric cells that follow it.
Numbers: '1,234,567' or '1.234.567' (thousand separators, chosen per document with sep), '(1,234)' negative,
'–' / '-' zero. Note references ('10.', '11c.', '38a.') are dropped. Values are returned in EUR millions.
"""
import re

DASH = {'–', '-', '—', '−'}

def _num(tok, sep):
    t = tok.strip().replace(' ', '').replace(' ', '')
    if t in DASH: return 0.0
    neg = t.startswith('(') or t.startswith('-') or t.startswith('−')
    t = t.strip('()').lstrip('-−').rstrip(')').lstrip('€')
    if sep == ',':
        if re.fullmatch(r'\d+', t) and (int(t) <= 31 or 1900 <= int(t) <= 2100): return None   # day / year, not an amount
        if re.fullmatch(r'\d{1,3}(,\d{3})+|\d+', t): v = float(t.replace(',', ''))
        elif re.fullmatch(r'\d+\.\d+', t): v = Dec(t)
        else: return None
    else:
        if re.fullmatch(r'\d+', t) and (int(t) <= 31 or 1900 <= int(t) <= 2100): return None   # day / year, not an amount
        if re.fullmatch(r'\d{1,3}(\.\d{3})+|\d+', t): v = float(t.replace('.', ''))
        elif re.fullmatch(r'\d+,\d+', t): v = Dec(t.replace(',', '.'))
        else: return None
    return (Dec(-v) if isinstance(v, Dec) else -v) if neg else v

class Dec(float):
    """a number printed with a decimal mark (per-share data, ratios): not scaled to EUR m"""

NOTE_REF = re.compile(r'^\d{1,2}[a-z]?\.$|^\d{1,2}[a-z]?\.,?\s*\d{0,2}[a-z]?\.?$|^\d{1,2}\.[a-z]?\.?$')

def segments(line, sep=','):
    cells = [c for c in re.split(r'\s{2,}', line.strip()) if c != '']
    # a cell may hold 'label 10. 443,416,352 352,364,019' (single spaces): split further on single spaces before numbers
    toks = []
    for c in cells:
        parts = c.split(' ')
        buf = []
        for p in parts:
            if _num(p, sep) is not None or p in DASH or NOTE_REF.match(p):
                if buf: toks.append(' '.join(buf)); buf = []
                toks.append(p)
            else:
                buf.append(p)
        if buf: toks.append(' '.join(buf))
    segs, cur = [], None
    for t in toks:
        if NOTE_REF.match(t) and cur is not None and not cur[1]: continue
        v = _num(t, sep) if not NOTE_REF.match(t) else None
        if v is None and t not in DASH:
            if cur is not None and not cur[1]:
                cur[0] = (cur[0] + ' ' + t).strip()
            else:
                cur = [t, []]; segs.append(cur)
        else:
            if t in DASH: v = 0.0
            if cur is None: cur = ['', []]; segs.append(cur)
            cur[1].append(v)
    return [(lab, vals) for lab, vals in segs]

def table(lines, sep=',', scale=1e6):
    """list of (lineno, label, [values]) for every segment carrying numbers; whole-euro integers → EUR m (6 dp),
    decimal-marked numbers (EPS, ratios) kept as printed. An unlabeled left segment borrows the text of the line above."""
    out, prev_text = [], ''
    for i, ln in lines:
        segs = segments(ln, sep)
        for j, (lab, vals) in enumerate(segs):
            if vals:
                if not lab and j == 0 and prev_text: lab = prev_text
                out.append((i, lab, [float(v) if isinstance(v, Dec) else round(v / scale, 6) for v in vals]))
        txt = [lab for lab, vals in segs if not vals and lab]
        if segs and not any(v for _, v in segs): prev_text = txt[0] if txt else ''
        elif segs: prev_text = ''
    return out

def read(path, a, b, c0=0, c1=None):
    """lines a..b (1-based, inclusive), optionally only character columns c0:c1 (for side-by-side pages)"""
    with open(path, encoding='utf-8', errors='ignore') as f:
        L = f.read().split('\n')
    return [(i, L[i - 1][c0:c1]) for i in range(a, min(b, len(L)) + 1)]

if __name__ == '__main__':
    import sys
    path, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    sep = sys.argv[4] if len(sys.argv) > 4 else ','
    c0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    c1 = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != '-' else None
    for i, lab, vals in table(read(path, a, b, c0, c1), sep):
        print(f'{i}: {lab[:70]} | ' + ' '.join(f'{v:,.6f}' if abs(v) < 1e5 else str(v) for v in vals))
