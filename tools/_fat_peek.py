#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "python3 -c \""
        "import struct,os;"
        "fd=os.open('/dev/mmcblk1',os.O_RDONLY);"
        "mbr=os.read(fd,512);"
        "os.close(fd);"
        "print('MBR',mbr[510],mbr[511],'p1type',mbr[0x1BE+4],'p1lba',struct.unpack_from('<I',mbr,0x1BE+8)[0],'oem0',mbr[3:11]);"
        "fd=os.open('/dev/mmcblk1p1',os.O_RDONLY);"
        "bs=os.read(fd,512);"
        "bps=struct.unpack_from('<H',bs,11)[0];"
        "spc=bs[13];res=struct.unpack_from('<H',bs,14)[0];"
        "nf=bs[16];root=struct.unpack_from('<H',bs,17)[0];"
        "tot16=struct.unpack_from('<H',bs,19)[0];fz=struct.unpack_from('<H',bs,22)[0];"
        "tot32=struct.unpack_from('<I',bs,32)[0];"
        "print('P1',bs[3:11],'bps',bps,'spc',spc,'res',res,'nf',nf,'root',root,'tot16',tot16,'fz',fz,'tot32',tot32,'lab',bs[43:54],'fs',bs[54:62]);"
        "off=(res+nf*fz)*bps;"
        "os.lseek(fd,off,0);"
        "d=os.read(fd,1024);"
        "os.close(fd);"
        "print('root_off',off);"
        "[print('ENT',i//32,d[i:i+11],hex(d[i+11]),struct.unpack_from('<H',d,i+26)[0],struct.unpack_from('<I',d,i+28)[0]) for i in range(0,len(d),32) if d[i] not in (0,5)]"
        "\"",
        wait=6.0,
    )
)
