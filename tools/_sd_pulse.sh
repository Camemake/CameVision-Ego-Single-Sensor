#!/bin/sh
# Pulse vcc3v3_sd GPIO (phandle 0xb9 pin 12) so the card can leave SDSC.
python3 - <<'PY'
import os
# resolve phandle 0xb9
want=b'\x00\x00\x00\xb9'
found=None
for root, dirs, files in os.walk('/proc/device-tree'):
    if 'phandle' in files:
        p=open(os.path.join(root,'phandle'),'rb').read()
        if p[:4]==want:
            found=root
            break
print('gpio node', found)
if found:
    print('name', open(os.path.join(found,'name'),'rb').read())
    print('compat', open(os.path.join(found,'compatible'),'rb').read() if os.path.exists(os.path.join(found,'compatible')) else b'')
PY
echo "=== gpiochips ==="
ls /sys/class/gpio
for c in /sys/class/gpio/gpiochip*; do
  echo $c base=$(cat $c/base) ngpio=$(cat $c/ngpio) label=$(cat $c/label)
done
# regulator sysfs
for r in /sys/class/regulator/regulator.*; do
  n=$(cat $r/name)
  if [ "$n" = "vcc3v3_sd" ]; then
    echo REG $r
    ls $r
    echo state=$(cat $r/state)
    echo 0 > $r/enable 2>/tmp/ren.err || true
    echo DISABLE_ERR=$(cat /tmp/ren.err)
    echo state2=$(cat $r/state)
  fi
done
echo PULSE
