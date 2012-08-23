#!/usr/bin/env python

import os
import subprocess

unr = "unr-original"
rot = "original"

for f in os.listdir(unr):
    f1 = os.path.join(unr, f)
    f2 = os.path.join(rot, f)
    
    cmd = ["convert", "-rotate", "270", f1, f2]
    print cmd
    
    subprocess.Popen(cmd)

