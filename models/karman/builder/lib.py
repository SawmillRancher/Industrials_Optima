"""Framework: column map, TDY style copy, formula templating."""
import re
from copy import copy
import openpyxl
from openpyxl.styles import Font
from openpyxl.comments import Comment

import os
HERE = os.path.dirname(os.path.abspath(__file__))
TDY = openpyxl.load_workbook(os.path.join(HERE, '..', '..', 'templates', 'TDY_Model.xlsx'))
TM = TDY['Model']

# (column, period label, type, TDY style column)
COLS = [
    ('C', '2022', 'A', 'CC'), ('D', '2023', 'A', 'CC'),
    ('E', 'Q1/24', 'Q', 'CD'), ('F', 'Q2/24', 'Q', 'CE'), ('G', '1H/24', 'H', 'CF'), ('H', 'Q3/24', 'Q', 'CG'), ('I', 'Q4/24', 'Q', 'CH'), ('J', '2024', 'A', 'CI'),
    ('K', 'Q1/25', 'Q', 'CD'), ('L', 'Q2/25', 'Q', 'CE'), ('M', '1H/25', 'H', 'CF'), ('N', 'Q3/25', 'Q', 'CG'), ('O', 'Q4/25', 'Q', 'CH'), ('P', '2025', 'A', 'CI'),
    ('Q', 'Q1/26', 'Q', 'CJ'), ('R', 'Q2/26', 'Q', 'CK'), ('S', '1H/26', 'H', 'CL'), ('T', 'Q3/26E', 'QE', 'CM'), ('U', 'Q4/26E', 'QE', 'CN'), ('V', '2026E', 'AE', 'CO'),
    ('W', '2027E', 'F', 'CP'), ('X', '2028E', 'F', 'CQ'), ('Y', '2029E', 'F', 'CR'), ('Z', '2030E', 'F', 'CS'),
]
DATA_COLS = [c[0] for c in COLS]
CTYPE = {c[0]: c[2] for c in COLS}
CPER = {c[0]: c[1] for c in COLS}
CSTYLE = {c[0]: c[3] for c in COLS}
CSTYLE.update({'AA': 'CT', 'AB': 'CU', 'AC': 'CV', 'AD': 'CW', 'AE': 'CZ', 'AF': 'DA', 'AG': 'DB', 'AH': 'DC', 'AI': 'DD', 'AJ': 'DE', 'AK': 'DF'})
PER2COL = {c[1]: c[0] for c in COLS}
YOY = {'D': 'C', 'J': 'D', 'K': 'E', 'L': 'F', 'M': 'G', 'N': 'H', 'O': 'I', 'P': 'J', 'Q': 'K', 'R': 'L', 'S': 'M', 'T': 'N', 'U': 'O',
       'V': 'P', 'W': 'V', 'X': 'W', 'Y': 'X', 'Z': 'Y'}
PA = {'D': 'C', 'J': 'D', 'P': 'J', 'V': 'P', 'W': 'V', 'X': 'W', 'Y': 'X', 'Z': 'Y'}   # prior annual column
YEARS = {  # year group -> q1,q2,h,q3,q4,fy
    '24': dict(q1='E', q2='F', h='G', q3='H', q4='I', fy='J'),
    '25': dict(q1='K', q2='L', h='M', q3='N', q4='O', fy='P'),
    '26': dict(q1='Q', q2='R', h='S', q3='T', q4='U', fy='V'),
}
COL2YEAR = {}
for y, d in YEARS.items():
    for v in d.values():
        COL2YEAR[v] = y
SCEN_ROW_OFF = {'W': 0, 'X': 1, 'Y': 2, 'Z': 3}
ANNUAL_HIST = ['C', 'D', 'J', 'P']
FC_COLS = ['T', 'U', 'V', 'W', 'X', 'Y', 'Z']

BLUE, BLACK, GREEN = 'FF0000FF', 'FF000000', 'FF008000'
NUM1 = '#,##0.0;\\(#,##0.0\\);\\-'
NUM0 = '#,##0;\\(#,##0\\);\\-'


class Row:
    def __init__(self, key, label, style, hist=None, h=None, fc=None, cells=None, all=None, histf=None,
                 note=None, comment=None, cagr=None, fmt=None, ae=None, hist_from=None, qe=None, f=None):
        self.key, self.label, self.style = key, label, style
        self.hist = hist          # key in data.H, or dict, or None
        self.h = h                # 'sum' | 'stock' | 'avg' | None  (half-year column)
        self.fc = dict(fc or {})  # 'QE'/'AE'/'F' or column letters -> template
        if qe is not None: self.fc['QE'] = qe
        if f is not None: self.fc['F'] = f
        if ae == 'sum': self.fc.setdefault('AE', '=SUM(<q1>[@],<q2>[@],<q3>[@],<q4>[@])')
        elif ae is not None: self.fc.setdefault('AE', ae)
        self.cells = dict(cells or {})
        self.all = all
        self.histf = histf
        self.note, self.comment, self.cagr, self.fmt = note, comment, cagr, fmt


class Sheet:
    def __init__(self, ws):
        self.ws = ws
        self.rows = []      # list of (rownum, Row)
        self.keys = {}
        self.cur = 8

    def add(self, row, blank_before=0):
        self.cur += blank_before
        self.rows.append((self.cur, row))
        if row.key:
            assert row.key not in self.keys, row.key
            self.keys[row.key] = self.cur
        self.cur += 1
        return row

    def blank(self, n=1):
        self.cur += n

    def r(self, key):
        return self.keys[key]

    def render(self, tmpl, col, selfrow):
        def rk(m):
            k = m.group(1)
            if k == '@':
                return str(selfrow)
            return str(self.keys[k])
        s = re.sub(r'\[([A-Za-z0-9_@]+)\]', rk, tmpl)
        yr = COL2YEAR.get(col)
        rep = {'<c>': col, '<y>': YOY.get(col, '#'), '<pa>': PA.get(col, '#')}
        if yr:
            for k, v in YEARS[yr].items():
                rep['<%s>' % k] = v
        if col in SCEN_ROW_OFF:
            rep['<so>'] = str(SCEN_ROW_OFF[col])
        for k, v in rep.items():
            s = s.replace(k, v)
        # scenario helper: {SC:AH22} -> CHOOSE over AH/AI/AJ with row offset for W..Z
        def sc(m):
            base = int(m.group(1)) + SCEN_ROW_OFF.get(col, 0)
            return 'CHOOSE(MATCH($AA$2,{"Bull","Base","Bear"},0),$AH$%d,$AI$%d,$AJ$%d)' % (base, base, base)
        s = re.sub(r'\{SC:(\d+)\}', sc, s)
        def sc0(m):
            base = int(m.group(1))
            return 'CHOOSE(MATCH($AA$2,{"Bull","Base","Bear"},0),$AH$%d,$AI$%d,$AJ$%d)' % (base, base, base)
        s = re.sub(r'\{SC0:(\d+)\}', sc0, s)
        assert '#' not in s.replace('"n/a"', '').replace('n/p', ''), (tmpl, col, s)
        return s


def copy_style(src, dst):
    dst.font = copy(src.font)
    dst.fill = copy(src.fill)
    dst.border = copy(src.border)
    dst.alignment = copy(src.alignment)
    dst.number_format = src.number_format
    dst.protection = copy(src.protection)


def set_color(cell, rgb, bold=None):
    f = copy(cell.font)
    cell.font = Font(name=f.name, sz=f.sz, b=(f.b if bold is None else bold), i=f.i, u=f.u, color=rgb,
                     strike=f.strike, vertAlign=f.vertAlign)


def note_comment(text, author='Model'):
    c = Comment(text, author)
    c.width, c.height = 420, 160
    return c
