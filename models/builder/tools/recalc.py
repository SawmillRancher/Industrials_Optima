"""Recalculate an xlsx with headless LibreOffice (always-recalc profile). Usage: recalc.py in.xlsx out_dir"""
import os, subprocess, sys, shutil, tempfile

XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
"""


def recalc(src, out_dir):
    prof = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lo_profile')
    os.makedirs(os.path.join(prof, 'user'), exist_ok=True)
    open(os.path.join(prof, 'user', 'registrymodifications.xcu'), 'w').write(XCU)
    os.makedirs(out_dir, exist_ok=True)
    cmd = ['soffice', f'-env:UserInstallation=file://{os.path.abspath(prof)}', '--headless', '--norestore',
           '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', out_dir, src]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
    return os.path.join(out_dir, os.path.basename(src))


if __name__ == '__main__':
    print(recalc(sys.argv[1], sys.argv[2]))
