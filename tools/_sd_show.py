#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo MOUNTS; cat /proc/mounts | grep -E 'mmc|sd|vfat'; "
        "echo ---FIND; "
        "for d in /userdata/sd /media/sd /mnt/sd /sdcard /run/media /mnt; do "
        "  [ -d \"$d\" ] && echo DIR $d && ls -la \"$d\" 2>/dev/null | head -20; "
        "done; "
        "echo ---SESS; "
        "python3 - <<'PY'\n"
        "import os, json, time\n"
        "roots=[]\n"
        "for p in ('/userdata/sd','/media/sd','/mnt/sd','/sdcard'):\n"
        "    if os.path.isdir(p): roots.append(p)\n"
        "print('roots', roots)\n"
        "for root in roots:\n"
        "    for dirpath, dirnames, filenames in os.walk(root):\n"
        "        for name in filenames:\n"
        "            path=os.path.join(dirpath, name)\n"
        "            try:\n"
        "                st=os.stat(path)\n"
        "            except OSError:\n"
        "                continue\n"
        "            print('%10d  %s' % (st.st_size, path))\n"
        "PY\n"
        "echo ---HTTP; wget -q -O - http://127.0.0.1:8090/v1/sessions; echo; "
        "wget -q -O - http://127.0.0.1:8090/v1/status; echo",
        wait=10.0,
    )
)
