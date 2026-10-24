#!/usr/bin/env python3
from cv_tn import run
import time

print("=== before up ===")
print(run("hciconfig hci0; echo WAIT1", wait=4))
time.sleep(6)
print("=== one up ===")
print(run("hciconfig hci0 up; hciconfig hci0; echo WAIT2", wait=5))
