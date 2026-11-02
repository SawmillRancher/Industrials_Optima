"""Framework: MLM-template layout re-based on Exosens' half-year history, style cloning, row registry and per-column formula context.

Columns (Model sheet):  C-D FY2021-2022 (annual; IPO registration document) | E-G H1/23, H2/23, FY2023 | H-J H1/24, H2/24, FY2024 |
K-M H1/25, H2/25, FY2025 | N H1/26 | O H2/26E | P 2026E | Q-T 2027E-2030E | U modelling notes | W-Z CAGRs | AC-AG scenario input table.
Template columns right of the forecast block keep their order (template letter − 63).
Half-year columns are the interim reporting unit (Exosens publishes H1 / FY statements and Q1 / Q3 revenue); H2 = FY − H1.
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
    def __init__(self, c, label, kind, year, h=None):
        self.c, self.label, self.kind, self.year, self.h = c, label, kind, year, h
        self.prior = None; self.prevh = None
    def __repr__(self): return f'{self.c}:{self.label}'

COLS, ANN, HC = [], {}, {}
_i = CI('C')
for y in (2021, 2022):
    col = Col(L(_i), y, 'A', y); COLS.append(col); ANN[y] = col; _i += 1
for y in range(2023, 2027):
    yy = str(y)[2:]
    for h in (1, 2, None):
        if h:
            if y == 2026 and h == 2: kind, lab = 'HE', 'H2/26E'
            else: kind, lab = 'H', f'H{h}/{yy}'
            col = Col(L(_i), lab, kind, y, h); HC[(y, h)] = col
        else:
            kind, lab = ('E26', '2026E') if y == 2026 else ('A', y)
            col = Col(L(_i), lab, kind, y); ANN[y] = col
        COLS.append(col); _i += 1
for y in range(2027, 2031):
    col = Col(L(_i), f'{y}E', 'AE', y); COLS.append(col); ANN[y] = col; _i += 1
assert ANN[2025].c == 'M' and HC[(2026, 1)].c == 'N' and HC[(2026, 2)].c == 'O' and ANN[2026].c == 'P' and ANN[2030].c == 'T', (ANN[2025], ANN[2026], ANN[2030])
for col in COLS:
    if col.h is None:
        if col.year - 1 in ANN: col.prior = ANN[col.year - 1].c
    else:
        if (col.year - 1, col.h) in HC: col.prior = HC[(col.year - 1, col.h)].c
        if col.h == 2: col.prevh = HC[(col.year, 1)].c
        elif (col.year - 1, 2) in HC: col.prevh = HC[(col.year - 1, 2)].c
COLMAP = {c.c: c for c in COLS}
HISTK = ('A', 'H')
FCK = ('HE', 'E26', 'AE')

# key column letters (used by the row specs)
H1, H2, E26 = 'N', 'O', 'P'            # H1/26 actual, H2/26E, 2026E
A25, A24, H125, H225 = 'M', 'J', 'K', 'L'
NOTE = 'U'
SW = '$U$2'                            # scenario switch
SL, SBULL, SBASE, SBEAR, SNOTE = 'AC', 'AD', 'AE', 'AF', 'AG'   # scenario table columns
CAGR = ('W', 'X', 'Y', 'Z')
LASTC = 'AG'
TSHIFT = 63                            # template column index − TSHIFT = EXENS column index (right block)
assert CI(NOTE) + TSHIFT == CI('CF') and CI(SL) + TSHIFT == CI('CN')

def pkey(col):
    if col.kind == 'A': return str(col.year)
    if col.kind == 'H': return f'H{col.h}-{str(col.year)[2:]}'
    return None

# ---------------------------------------------------------------- data
DATA = normalize.run()
MAN = normalize.MAN
def num(x):
    if isinstance(x, bool) or x is None: return None
    return x if isinstance(x, (int, float)) else None
def xget(per, key):
    return (DATA.get(per, {}).get('x') or {}).get(key)

# ---------------------------------------------------------------- styles (cloned from the MLM template)
_tmpl_wb = openpyxl.load_workbook(TEMPLATE)
TM = _tmpl_wb['Model']
ARCH = {'section': 8, 'blank': 9, 'block': 10, 'line_b': 162, 'line': 161, 'growth': 237, 'pct': 212, 'memo': 180, 'check': 179,
        'driver': 153, 'total': 166, 'text': 215, 'sub': 217, 'eps': 187, 'eps_total': 188, 'eps_memo': 191, 'sched': 378, 'memo_calc': 181}
NF = {'m': '#,##0;\\(#,##0\\);\\-', 'm1': '#,##0.0;\\(#,##0.0\\);\\-', 'pct': '0.0%;\\(0.0%\\);\\-', 'ps': '0.00;\\(0.00\\);\\-',
      'x': '0.0\\x', 'x2': '0.00\\x;\\(0.00"x)";\\-', 'd': '0\\d;\\(0")d";\\-', 'gen': 'General', 'yrs': '0" yrs"',
      'm2': '#,##0.00;\\(#,##0.00\\);\\-', 'pct2': '0.00%;\\(0.00%\\);\\-', 'm3': '#,##0.000;\\(#,##0.000\\);\\-'}
BLUE, BLACK, GRAY = 'FF0000FF', 'FF000000', 'FFA6A6A6'
SRC_KIND = {'A': 'BV', 'H': 'BX', 'HE': 'BY', 'E26': 'CA', 'AE': 'CB'}

def tcol(ci):
    """template column letter for EXENS column index ci"""
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
    c = Comment(text, 'EXENS model'); c.width, c.height = w, h
    cell.comment = c

# ---------------------------------------------------------------- registry
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
def PH(key): return f'{CTX.col.prevh}{R[key]}'
def Hc(key, y, h): return f'{HC[(y, h)].c}{R[key]}'
def Y(key, y): return f'{ANN[y].c}{R[key]}'
def S26(key): return f'={H1}{R[key]}+{H2}{R[key]}'
def SUMH(key):
    """annual column = sum of its two halves (historical annual columns 2023+)"""
    y = CTX.col.year
    return f'={HC[(y, 1)].c}{R[key]}+{HC[(y, 2)].c}{R[key]}'
