"""Framework: MLM-template layout for FedEx with two history bases side by side, style cloning, row registry and per-column
formula context.

Columns (Model sheet):
  legacy basis (fiscal years ended 31 May, FedEx Freight consolidated, as originally reported)
    C-I   FY2006-FY2012 (annual) | J-CA Q1 FY13 - Q4 FY26 with FY subtotals (FY2013 ... FY2026)
  calendar basis (years ended 31 December, FedEx Freight in discontinued operations, Express U.S. Domestic / International segments)
    CB-CK Q1/24-Q4/25 with 2024 and 2025 totals | CL-CN Q1/26-Q3/26 (actual) | CO Q4/26E | CP 2026E | CQ-CU 2027E-2031E
  CV modelling notes | CX-DA CAGRs | DD-DH scenario input table. Template columns right of the forecast block keep their order
  (template column index + 16). Year-on-year links never cross the two bases.
"""
import copy, json, os
import openpyxl
from openpyxl.utils import get_column_letter as L, column_index_from_string as CI
from openpyxl.styles import Font
from openpyxl.comments import Comment
import normalize

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, 'MLM_Model.xlsx')

class Col:
    def __init__(self, c, label, kind, year, q=None, basis='C'):
        self.c, self.label, self.kind, self.year, self.q, self.basis = c, label, kind, year, q, basis
        self.prior = None; self.prevq = None
    def __repr__(self): return f'{self.c}:{self.label}'

LA0, LQ0, LAL = 2006, 2013, 2026           # legacy: first annual fiscal year, first quarterly fiscal year, last fiscal year
CY0, FYC, FYL = 2024, 2026, 2031           # calendar: first year, current (partly estimated) year, last forecast year
COLS, ANN, QC, LANN, LQC = [], {}, {}, {}, {}
_i = CI('C')
for y in range(LA0, LQ0):
    col = Col(L(_i), f'FY{y}', 'A', y, basis='L'); COLS.append(col); LANN[y] = col; _i += 1
for y in range(LQ0, LAL + 1):
    for q in (1, 2, 3, 4, None):
        col = Col(L(_i), f'Q{q} FY{str(y)[2:]}' if q else f'FY{y}', 'Q' if q else 'A', y, q, 'L')
        (LQC.__setitem__((y, q), col) if q else LANN.__setitem__(y, col)); COLS.append(col); _i += 1
for y in range(CY0, FYC + 1):
    yy = str(y)[2:]
    for q in (1, 2, 3, 4, None):
        if q:
            kind, lab = ('QE', f'Q{q}/{yy}E') if (y == FYC and q == 4) else ('Q', f'Q{q}/{yy}')
            col = Col(L(_i), lab, kind, y, q); QC[(y, q)] = col
        else:
            kind, lab = ('E26', f'{y}E') if y == FYC else ('A', y)
            col = Col(L(_i), lab, kind, y); ANN[y] = col
        COLS.append(col); _i += 1
for y in range(FYC + 1, FYL + 1):
    col = Col(L(_i), f'{y}E', 'AE', y); COLS.append(col); ANN[y] = col; _i += 1
assert LANN[2012].c == 'I' and LANN[2026].c == 'CA' and QC[(2024, 1)].c == 'CB' and ANN[2025].c == 'CK' and QC[(2026, 3)].c == 'CN' \
    and QC[(2026, 4)].c == 'CO' and ANN[2026].c == 'CP' and ANN[2031].c == 'CU', (LANN[2026], ANN[2025], ANN[2026], ANN[2031])
for col in COLS:
    A_, Q_ = (LANN, LQC) if col.basis == 'L' else (ANN, QC)
    if col.q is None:
        if col.year - 1 in A_: col.prior = A_[col.year - 1].c
    else:
        if (col.year - 1, col.q) in Q_: col.prior = Q_[(col.year - 1, col.q)].c
        if col.q > 1: col.prevq = Q_[(col.year, col.q - 1)].c
        elif (col.year - 1, 4) in Q_: col.prevq = Q_[(col.year - 1, 4)].c
COLMAP = {c.c: c for c in COLS}
HISTK = ('A', 'Q')
FCK = ('QE', 'E26', 'AE')

Q1, Q2, Q3, QE, E26 = 'CL', 'CM', 'CN', 'CO', 'CP'         # calendar 2026 quarters (Q1-Q3 actual, Q4 estimate) / 2026E
LQ = Q3                                                     # last actual quarter (30-Sep-2026)
A25, A24 = 'CK', 'CF'
PQ1, PQ3, PQ4 = 'CG', 'CI', 'CJ'                            # Q1/25 - Q3/25 (prior-year nine months), Q4/25
NOTE = 'CV'
SW = '$CV$2'                                                # scenario switch
SL, SBULL, SBASE, SBEAR, SNOTE = 'DD', 'DE', 'DF', 'DG', 'DH'
CAGR = ('CX', 'CY', 'CZ', 'DA')
LASTC = 'DH'
TSHIFT = -16                                                # template column index - TSHIFT = FDX column index (right block)

def pkey(col):
    yy = str(col.year)[2:]
    if col.basis == 'L': return f'L{col.year}' if col.kind == 'A' else f'LQ{col.q}-{yy}'
    if col.kind == 'A': return f'CY{col.year}'
    if col.kind == 'Q': return f'CQ{col.q}-{yy}'
    return None

DATA = normalize.run()
MAN = normalize.MAN
def num(x):
    if isinstance(x, bool) or x is None: return None
    return x if isinstance(x, (int, float)) else None
def xget(per, key):
    return (DATA.get(per, {}).get('x') or {}).get(key)

_tmpl_wb = openpyxl.load_workbook(TEMPLATE)
TM = _tmpl_wb['Model']
ARCH = {'section': 8, 'blank': 9, 'block': 10, 'line_b': 162, 'line': 161, 'growth': 237, 'pct': 212, 'memo': 180, 'check': 179,
        'driver': 153, 'total': 166, 'text': 215, 'sub': 217, 'eps': 187, 'eps_total': 188, 'eps_memo': 191, 'sched': 378, 'memo_calc': 181}
NF = {'m': '#,##0;\\(#,##0\\);\\-', 'm1': '#,##0.0;\\(#,##0.0\\);\\-', 'pct': '0.0%;\\(0.0%\\);\\-', 'ps': '0.00;\\(0.00\\);\\-',
      'x': '0.0\\x', 'x2': '0.00\\x;\\(0.00"x)";\\-', 'd': '0\\d;\\(0")d";\\-', 'gen': 'General', 'yrs': '0" yrs"',
      'm2': '#,##0.00;\\(#,##0.00\\);\\-', 'pct2': '0.00%;\\(0.00%\\);\\-'}
BLUE, BLACK, GRAY = 'FF0000FF', 'FF000000', 'FFA6A6A6'
SRC_KIND = {'A': 'BV', 'Q': 'BX', 'QE': 'BY', 'E26': 'CA', 'AE': 'CB'}

def tcol(ci):
    letter = L(ci)
    if letter == 'B': return 'B'
    if letter in COLMAP: return SRC_KIND[COLMAP[letter].kind]
    return L(ci + TSHIFT)

def clone_row_style(ws, src_row, dst_row, c0=2, c1=CI(LASTC)):
    for ci in range(c0, c1 + 1):
        ws.cell(dst_row, ci)._style = copy.copy(TM[f'{tcol(ci)}{src_row}']._style)

def set_color(cell, rgb, bold=None):
    f = copy.copy(cell.font)
    cell.font = Font(name=f.name, sz=f.sz, b=f.b if bold is None else bold, i=f.i, u=f.u, color=rgb)

def comment(cell, text, w=420, h=160):
    c = Comment(text, 'FDX model'); c.width, c.height = w, h
    cell.comment = c

class Row:
    def __init__(self, key, label, arch, nf, kw):
        self.key, self.label, self.arch, self.nf, self.kw = key, label, arch, nf, kw
        self.r = None; self.spec2 = False
SPEC, R = [], {}
def add(key, label='', arch='line', nf='m', **kw):
    if key in R: raise KeyError('dup ' + key)
    SPEC.append(Row(key, label, arch, nf, kw)); R[key] = None
    return key
_bn = [0]
def blank():
    _bn[0] += 1
    return add(f'_b{_bn[0]}', '', 'blank', 'gen')
def number_rows(start):
    r = start
    for row in SPEC:
        R[row.key] = r; row.r = r; r += 1
    return r

class _Ctx: col = None
CTX = _Ctx()
def V(key, c=None): return f'{c or CTX.col.c}{R[key]}'
def P(key): return f'{CTX.col.prior}{R[key]}'
def PQ(key): return f'{CTX.col.prevq}{R[key]}'
def Q(key, y, q): return f'{QC[(y, q)].c}{R[key]}'
def Y(key, y): return f'{ANN[y].c}{R[key]}'
def S26(key): return f'=SUM({Q1}{R[key]}:{QE}{R[key]})'
def SUMQ(key):
    y = CTX.col.year
    return f'=SUM({QC[(y, 1)].c}{R[key]}:{QC[(y, 4)].c}{R[key]})'
