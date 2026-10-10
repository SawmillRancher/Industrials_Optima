"""Scan every sheet's values, labels and cell comments for leftover template-company or other-model text.

Usage: python3 residue_scan.py <model.xlsx> [--allow TOKEN ...] [--extra TOKEN ...]

Leftover template text in Bull-Base-Bear / DCF comments shipped in at least ten models (the MLM "$518.70" P/E comment, "Martin
Marietta characteristics" in DCF rationale, snapshot comments citing another build's switch cell "Model!CF2"). Run this before
release; any hit must be fixed or explicitly allowed. Tokens are matched case-insensitively as whole words.
--allow drops a default token (e.g. --allow aggregates for a construction-materials company).
--extra adds tokens (the previous company used as a kit source, its ticker and its share price).
Comment authors other than the current build are also listed.
"""
import re
import sys

import openpyxl

DEFAULT = ['MLM', 'Martin Marietta', 'LNA', 'Lhoist', '518.70', 'aggregates', 'Magnesia', 'QUIKRETE', 'Moog', 'Model!CF2',
           'RB Global', 'Teledyne', 'TDY template', 'HII template', 'DSV']


def main(path, tokens):
    pats = [(t, re.compile(r'(?<![A-Za-z0-9])' + re.escape(t) + r'(?![A-Za-z0-9])', re.I)) for t in tokens]
    wb = openpyxl.load_workbook(path)
    hits, authors = [], {}
    for ws in wb:
        for row in ws.iter_rows():
            for c in row:
                texts = []
                if isinstance(c.value, str) and not c.value.startswith('='):
                    texts.append(('value', c.value))
                if c.comment is not None:
                    texts.append(('comment', c.comment.text or ''))
                    authors[c.comment.author] = authors.get(c.comment.author, 0) + 1
                for kind, t in texts:
                    for tok, p in pats:
                        if p.search(t):
                            hits.append(f'{ws.title}!{c.coordinate} [{kind}] {tok}: {t.strip()[:110]!r}')
    for h in hits:
        print(h)
    print('comment authors:', authors)
    print(f'{len(hits)} residue hits')
    return 1 if hits else 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0].startswith('--'):
        sys.exit(__doc__)
    path, rest = args[0], args[1:]
    tokens, mode = list(DEFAULT), None
    for a in rest:
        if a in ('--allow', '--extra'):
            mode = a
        elif mode == '--allow':
            tokens = [t for t in tokens if t.lower() != a.lower()]
        elif mode == '--extra':
            tokens.append(a)
    sys.exit(main(path, tokens))
