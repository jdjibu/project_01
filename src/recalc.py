"""Recalculate an .xlsx in headless LibreOffice so formula results are cached in the file
(xlsxwriter writes formulas without values). Usage: python src/recalc.py in.xlsx [out.xlsx]"""
import os
import subprocess
import sys
import time
from pathlib import Path

import uno  # LibreOffice's Python-UNO bridge
from com.sun.star.beans import PropertyValue


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def recalc(src: Path, dst: Path, port: int = 2002):
    proc = subprocess.Popen(["soffice", "--headless", "--invisible", "--nologo", "--norestore",
                             f"--accept=socket,host=127.0.0.1,port={port};urp;"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ctx = uno.getComponentContext()
        resolver = ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", ctx)
        for _ in range(60):
            try:
                remote = resolver.resolve(f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("could not connect to LibreOffice")
        desktop = remote.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", remote)
        doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(src.resolve())), "_blank", 0,
                                           (prop("Hidden", True),))
        doc.calculateAll()
        doc.storeToURL(uno.systemPathToFileUrl(str(dst.resolve())),
                       (prop("FilterName", "Calc MS Excel 2007 XML"),))
        doc.close(True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    s = Path(sys.argv[1])
    d = Path(sys.argv[2]) if len(sys.argv) > 2 else s
    recalc(s, d)
    print("recalculated", d)
