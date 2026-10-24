#!/usr/bin/env python3
from cv_tn import run

print(run("echo TN_OK; hciconfig hci0; echo ---", wait=4))
