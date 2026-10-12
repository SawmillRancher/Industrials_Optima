"""Booz Allen earnings-release parser (8-K Item 2.02, Ex. 99.1).

The releases come in two formats: HTML tables (FY2011 - Q4 FY2019; one table row per line after h2t.py, cells joined by ' | ')
and, from Q1 FY2020, a PDF-rendered page whose tables flatten into one block of text. Both are tokenised the same way into
entries (label, [numbers]): a label is a run of non-numeric tokens, followed by the run of numeric tokens after it.
  - numbers: 1,979,280 / (48,937) / (48,937  (dropped ')' in the table format = negative) / 1.43 / 9.7 %; '—' and '-' = 0.
  - footnote markers '(a)'..'(j)' stay in the label; '(1)'..'(4)' directly after a backlog / contract-type label are footnotes.
Entries are split by exhibit section (statement of operations, balance sheet, cash flows, EPS, non-GAAP, operating data) and
looked up by a regex on the end of the label. Column order follows the release header: three months current / prior, then
year-to-date (Q2-Q3) or fiscal year (Q4) current / prior.
"""
import re

NUM = re.compile(r'^\$?\(?\$?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\)?%?x?$')
DASH = {'—', '-', '–', '—%', '-%'}
FOOT_AFTER = re.compile(r'(Unfunded|Options|Reimbursable|Fixed-Price|Funded|Bill|Security|Materials|Headcount|\*)$')
SECTIONS = [('is', r'(Statements?|Statement) of Operations'), ('ci', r'Statements? of Comprehensive Income'),
            ('bs', r'Balance Sheets?'), ('cf', r'Statements? of Cash Flows'), ('eps', r'Earnings Per Share Calculations'),
            ('ng', r'Non-GAAP Financial Information'), ('op', r'Operating Data')]

def flatten(text):
    t = text.replace(' | ', ' ').replace('|', ' ')
    t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'\$\s+', '$', t)
    t = re.sub(r'(\d)\s+%', r'\1%', t)
    return re.sub(r'\s+', ' ', t)

def tokens(text):
    return flatten(text).split(' ')

def to_num(tok):
    tok = tok.lstrip('$')
    if tok in DASH: return 0.0
    m = NUM.match(tok)
    if not m: return None
    v = float((m.group(1) + (m.group(2) or '')).replace(',', ''))
    return -v if '(' in tok else v

def entries(text):
    out, lab, nums = [], [], []
    toks = [t for t in tokens(text) if t]
    for i, tok in enumerate(toks):
        v = to_num(tok)
        # a dash between words ('Cash and cash equivalents — beginning of period') is part of the label
        if tok in DASH and lab and not nums and i + 1 < len(toks) and re.match(r'^[a-z]', toks[i + 1]):
            lab.append(tok); continue
        # footnote markers right after a label: (1)..(4) with no number yet, or a letter marker
        if v is not None and re.fullmatch(r'\(\d\)', tok) and lab and not nums and FOOT_AFTER.search(lab[-1]):
            lab.append(tok); continue
        if v is None or (tok.lstrip('$') in DASH and not lab and not nums):
            if nums:
                out.append((' '.join(lab), nums)); lab, nums = [], []
            if tok.lstrip('$') not in DASH: lab.append(tok)
            continue
        nums.append(v)
    if lab or nums: out.append((' '.join(lab), nums))
    return out

class Release:
    def __init__(self, text):
        self.text = text
        self.E = entries(text)
        self.flat = flatten(text)
        self.sec = self._sections()

    def _sections(self):
        """index range of each exhibit: first entry whose label carries the company header + exhibit title (the page-1 exhibit index
        of the old releases has no company header)."""
        pos = {}
        for i, (lab, _) in enumerate(self.E):
            for name, rx in SECTIONS:
                if name in pos: continue
                if re.search(rf'Holding Corp\w*\.? (?:\(\w+\) )?(?:Condensed )?(?:Consolidated )?{rx}', lab):
                    pos[name] = i
        st = sorted(pos.items(), key=lambda kv: kv[1])
        return {name: (i, st[k + 1][1] if k + 1 < len(st) else len(self.E)) for k, (name, i) in enumerate(st)}

    def rows(self, sec):
        a, b = self.sec.get(sec, (0, 0))
        return self.E[a:b]

    def find(self, sec, rx, after=None, nth=0, need=1):
        """first entry in the section whose label ends with rx (case-insensitive) and that has >= need numbers."""
        rows = self.rows(sec) if sec else self.E
        start = 0
        if after:
            for i, (lab, _) in enumerate(rows):
                if re.search(after, lab, re.I): start = i; break
        k = 0
        for lab, nums in rows[start:]:
            if re.search(rf'(?:^|\W)(?:{rx})\s*(?:\([a-z]\)|\*)?\s*:?\s*$', lab, re.I) and len(nums) >= need:
                if k == nth: return nums
                k += 1
        return None

    def units(self, sec):
        a, b = self.sec.get(sec, (0, 0))
        head = ' '.join(lab for lab, _ in self.E[a:min(b, a + 4)])
        if re.search(r'in thousands', head, re.I): return 1e-3
        if re.search(r'in millions', head, re.I): return 1.0
        return None
