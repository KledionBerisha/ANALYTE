"""Open the docx in headless LibreOffice via UNO, update all indexes (TOC/LOF/LOT) and fields,
save back as docx and also export a PDF."""
import subprocess, time, sys, os, pathlib
import uno
from com.sun.star.beans import PropertyValue

src = pathlib.Path(sys.argv[1]).resolve()
out_docx = pathlib.Path(sys.argv[2]).resolve()
out_pdf = pathlib.Path(sys.argv[3]).resolve()

proc = subprocess.Popen(["soffice", "--headless", "--invisible", "--nologo", "--norestore",
                         '--accept=socket,host=127.0.0.1,port=2002;urp;'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ctx = None
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(60):
    try:
        ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(1)
if ctx is None:
    raise SystemExit("could not connect to soffice")
smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

def pv(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(src)), "_blank", 0, (pv("Hidden", True),))
# update indexes twice (page numbers can shift after the TOC grows)
for _ in range(2):
    idx = doc.getDocumentIndexes()
    for i in range(idx.getCount()):
        idx.getByIndex(i).update()
    doc.getTextFields().refresh()
    doc.refresh()
doc.storeToURL(uno.systemPathToFileUrl(str(out_docx)), (pv("FilterName", "MS Word 2007 XML"),))
doc.storeToURL(uno.systemPathToFileUrl(str(out_pdf)), (pv("FilterName", "writer_pdf_Export"),))
doc.close(True)
try:
    desktop.terminate()
except Exception:
    pass
proc.wait(timeout=60)
print("ok")
