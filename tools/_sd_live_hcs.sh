#!/bin/sh
# Patch mmc_send_if_cond to always return 0 so ACMD41 sets HCS.
# phys = 0x40200000 + (VA - 0xffffffc008000000)
PHYS=0x407a89f8
echo '=== before ==='
devmem $PHYS 32
devmem $((PHYS+4)) 32
devmem $((PHYS+8)) 32
devmem $((PHYS+12)) 32
echo '=== patch mov w0,0; ret ==='
devmem $PHYS 32 0x52800000
devmem $((PHYS+4)) 32 0xD65F03C0
echo '=== after ==='
devmem $PHYS 32
devmem $((PHYS+4)) 32
echo LIVE
