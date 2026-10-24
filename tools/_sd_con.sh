#!/bin/sh
python3 - <<'PY'
import mmap, os, struct
fd=os.open('/dev/mem', os.O_RDWR|os.O_SYNC)
m=mmap.mmap(fd, 0x4000, offset=0x21D60000)
print('CON0', hex(struct.unpack_from('<I', m, 0x130)[0]))
print('CON1', hex(struct.unpack_from('<I', m, 0x134)[0]))
print('USRID', hex(struct.unpack_from('<I', m, 0x68)[0]))
print('CLKDIV', hex(struct.unpack_from('<I', m, 8)[0]))
m.close(); os.close(fd)
PY
# confirm kernel nops
python3 - <<'PY'
import mmap, os
PHYS=0x40200000
fd=os.open('/dev/mem', os.O_RDONLY|os.O_SYNC)
for name,off in [('hcs',0x5A756C),('samp',0x5B7318),('drv',0x5B7358)]:
    page=(PHYS+off)&~0xfff
    rel=(PHYS+off)-page
    m=mmap.mmap(fd, rel+4, offset=page)
    print(name, m[rel:rel+4].hex())
    m.close()
os.close(fd)
PY
echo CON
