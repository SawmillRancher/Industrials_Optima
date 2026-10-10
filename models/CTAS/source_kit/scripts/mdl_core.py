"""Core layout engine for the CTAS model: periods/columns, row registry, formula
templating and template-cloned styles (MLM_Model.xlsx conventions)."""
import re
from copy import copy
from openpyxl.utils import get_column_letter as L
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

# ------------------------------------------------------------------ periods
class P:
    def __init__(self, name, fy, q, col, fc):
        self.name, self.fy, self.q, self.col, self.fc = name, fy, q, col, fc
        self.is_q = q is not None
        self.L = L(col)
    def __repr__(self): return self.name

PERIODS = []
c = 3
for fy in range(2006, 2013):
    PERIODS.append(P(f'FY{fy}', fy, None, c, False)); c += 1
for fy in range(2013, 2027):
    for q in (1, 2, 3, 4):
        PERIODS.append(P(f'FY{fy}Q{q}', fy, q, c, False)); c += 1
    PERIODS.append(P(f'FY{fy}', fy, None, c, False)); c += 1
PERIODS.append(P('FY2027Q1', 2027, 1, c, False)); c += 1
for q in (2, 3, 4):
    PERIODS.append(P(f'FY2027Q{q}', 2027, q, c, True)); c += 1
PERIODS.append(P('FY2027', 2027, None, c, True)); c += 1
for fy in range(2028, 2032):
    PERIODS.append(P(f'FY{fy}', fy, None, c, True)); c += 1
BYNAME = {p.name: p for p in PERIODS}
NOTE_COL = c            # CK
CAGR_COLS = [c + 2, c + 3, c + 4, c + 5]   # CM..CP
SCN_LBL = c + 8          # CS
SCN_BULL, SCN_BASE, SCN_BEAR, SCN_NOTE = c + 9, c + 10, c + 11, c + 12
SWITCH = f'${L(NOTE_COL)}$2'
LAST_COL = PERIODS[-1].col

def header(p):
    if p.is_q:
        return f'Q{p.q}/{str(p.fy)[2:]}' + ('E' if p.fc else '')
    return f'FY{p.fy}' + ('E' if p.fc else '')

def prior_year(p):
    if p.is_q:
        return BYNAME.get(f'FY{p.fy-1}Q{p.q}')
    return BYNAME.get(f'FY{p.fy-1}')

def quarters(p):
    return [BYNAME.get(f'FY{p.fy}Q{q}') for q in (1, 2, 3, 4)]

HIST = [p for p in PERIODS if not p.fc]
FCQ = [p for p in PERIODS if p.fc and p.is_q]
FCA = [p for p in PERIODS if p.fc and not p.is_q]
A27 = BYNAME['FY2027']

# ------------------------------------------------------------------ row registry
class Row:
    def __init__(self, key, label, style='line', fmt='n0', h=None, fq=None, f27=None, fa=None,
                 note=None, level=0, cagr=False, notestyle=None):
        self.key, self.label, self.style, self.fmt = key, label, style, fmt
        self.h, self.fq, self.f27, self.fa = h, fq, f27, fa
        self.note, self.level, self.cagr, self.notestyle = note, level, cagr, notestyle
        self.r = None

class Sheet:
    def __init__(self, start_row=8):
        self.rows = []
        self.R = {}
        self.next = start_row
    def add(self, row):
        row.r = self.next
        if row.key:
            assert row.key not in self.R, row.key
            self.R[row.key] = row.r
        self.rows.append(row)
        self.next += 1
        return row
    def blank(self):
        self.rows.append(Row(None, None, 'blank')); self.rows[-1].r = self.next; self.next += 1

# ------------------------------------------------------------------ formula templating
TOK = re.compile(r'\{([A-Za-z0-9_]+)(?:@([^}]+))?\}')
def resolve(tpl, p, R, scn=None):
    """Replace {key} / {key@spec} tokens. spec: py (prior-year same period), pa (prior annual),
    q1..q4 (quarter of same FY), $P:FY2026Q1 absolute period, P:FY2026 relative-row period,
    S (scenario CHOOSE for this period's lever row), $ (absolute same column)."""
    def rep(m):
        k, spec = m.group(1), m.group(2)
        if k == 'col':
            return p.L
        if k not in R:
            raise KeyError(f'unknown row key {k} in {tpl}')
        r = R[k]
        if spec is None:
            return f'{p.L}{r}'
        if spec == 'py':
            pp = prior_year(p)
            if pp is None: raise KeyError(f'no prior year for {p}')
            return f'{pp.L}{r}'
        if spec == 'pa':
            pp = BYNAME.get(f'FY{p.fy-1}')
            return f'{pp.L}{r}'
        if spec in ('q1', 'q2', 'q3', 'q4'):
            pp = BYNAME[f'FY{p.fy}Q{spec[1]}']
            return f'{pp.L}{r}'
        if spec.startswith('$P:'):
            pp = BYNAME[spec[3:]]
            return f'${pp.L}${r}'
        if spec.startswith('P:'):
            pp = BYNAME[spec[2:]]
            return f'{pp.L}{r}'
        if spec == '$':
            return f'${p.L}${r}'
        if spec == 'abs':
            return f'${L(SCN_BASE)}${r}'
        raise KeyError(spec)
    return TOK.sub(rep, tpl)

# ------------------------------------------------------------------ styles
FMT = {
    'n0': '#,##0;\\(#,##0\\);\\-',
    'n1': '#,##0.0;\\(#,##0.0\\);\\-',
    'n2': '0.00;\\(0.00\\);\\-',
    'p1': '0.0%;\\(0.0%\\);\\-',
    'x1': '0.0\\x;\\(0.0"x)";\\-',
    'x2': '0.00\\x;\\(0.00"x)";\\-',
    'd0': '0"d";\\(0"d")";\\-',
    'gen': 'General',
    'dt': 'dd-mmm-yy',
    'n0g': '#,##0',
}
WHITE, BLUE, BLACK = 'FFFFFFFF', 'FF0000FF', 'FF000000'
F_DARK, F_GREEN, F_TOTAL, F_FC, F_SCHED, F_CAGRH = 'FF2F3E46', 'FF52796F', 'FFCAD2C5', 'FFFFFDE7', 'FFE9ECEC', 'FF84A98C'
thin = Side(style='thin'); med = Side(style='medium')

def fill(rgb): return PatternFill('solid', fgColor=rgb)
def font(sz=12, b=False, color=None, i=False):
    return Font(name='Calibri', sz=sz, b=b, i=i, color=color)

LABEL_STYLE = {
    'sec':   dict(font=font(12, True, WHITE), fill=fill(F_DARK)),
    'sub':   dict(font=font(11, True, WHITE), fill=fill(F_GREEN)),
    'key':   dict(font=font(12, True), border='top'),
    'line':  dict(font=font(12)),
    'yoy':   dict(font=font(12, False, 'FF404040')),
    'pct':   dict(font=font(12)),
    'total': dict(font=font(11, True, WHITE), fill=fill(F_DARK), border='top'),
    'check': dict(font=font(12, True, 'FF595959')),
    'memo':  dict(font=font(12, True, 'FF666666')),
    'def':   dict(font=font(11, True, 'FFC00000')),
    'sched': dict(font=font(12, False, 'FF404040'), fill=fill(F_SCHED)),
    'input': dict(font=font(12)),
    'head':  dict(font=font(12, True)),
    'blank': dict(font=font(11)),
}

def style_label(cell, style):
    s = LABEL_STYLE.get(style, LABEL_STYLE['line'])
    cell.font = s['font']
    if 'fill' in s: cell.fill = s['fill']
    if s.get('border') == 'top': cell.border = Border(top=thin)

def style_value(cell, style, fmt, p, is_formula):
    if style in ('sec', 'sub'):
        cell.font = LABEL_STYLE[style]['font']; cell.fill = LABEL_STYLE[style]['fill']; return
    bold = style in ('key', 'total')
    if style == 'def':
        cell.font = font(10, True, 'FFC00000'); return
    if p is not None and p.fc:
        color = BLUE if (not is_formula and style not in ('check',)) else BLACK
        cell.font = font(12, bold or (not is_formula), color)
    else:
        if style == 'yoy' and is_formula:
            color = 'FFA6A6A6'
        else:
            color = BLUE if not is_formula else BLACK
        cell.font = font(12, bold, color)
    cell.number_format = FMT[fmt]
    cell.alignment = Alignment(horizontal='right')
    if style == 'total':
        cell.fill = fill(F_TOTAL)
    elif p is not None and p.fc:
        cell.fill = fill(F_FC)
    if style in ('key', 'total'):
        cell.border = Border(top=thin)
