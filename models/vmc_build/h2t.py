#!/usr/bin/env python3
"""Convert an EDGAR HTML filing to compact text: one table row per line, cells joined by ' | '.
Usage: h2t.py in.htm > out.txt"""
import re, sys, html
t = open(sys.argv[1], encoding='latin-1').read()
t = re.sub(r'(?is)<(script|style|head).*?</\1>', '', t)
t = re.sub(r'(?is)<ix:header>.*?</ix:header>', '', t)
def cell_text(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s).replace('\xa0', ' ').replace('​','')
    return re.sub(r'\s+', ' ', s).strip()
def row_repl(m):
    cells = re.findall(r'(?is)<t[dh][^>]*>(.*?)</t[dh]>', m.group(0))
    out = []
    for c in cells:
        c = cell_text(c)
        if not c: continue
        if c in ('$', '%', ')', '%)') and out:
            if c != '$': out[-1] += c
            continue
        if out and out[-1] == '$': out[-1] = '$' + c; continue
        out.append(c)
    return '\n' + ' | '.join(out) + '\n' if out else '\n'
t = re.sub(r'(?is)<tr[^>]*>.*?</tr>', row_repl, t)
t = re.sub(r'(?i)</(p|div|h\d|li)>|<br\s*/?>', '\n', t)
t = re.sub(r'<[^>]+>', ' ', t)
t = html.unescape(t).replace('\xa0', ' ')
t = re.sub(r'[ \t]+', ' ', t)
t = re.sub(r'\n\s*\n+', '\n', t)
sys.stdout.write(t)
