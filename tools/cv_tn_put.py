#!/usr/bin/env python3
"""Write a local file onto the board over telnet."""
import sys
from pathlib import Path

from cv_tn import run

src = Path(sys.argv[1])
dst = sys.argv[2]
text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if "ENDFILE" in text:
    raise SystemExit("sentinel in %s" % src)
out = run(
    "cat > %s << 'ENDFILE'\n%sENDFILE\nchmod 755 %s\nwc -c %s" % (dst, text, dst, dst),
    wait=6.0,
)
print(out)
