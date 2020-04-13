# File:     driver.py
# Author:   Lea Chandler
# Date:     4/1/2020
# Version:  1
# Platform: Rasbian Buster with Python3
#
# Driver for the police academy robot

import os
import sys
import time
import serial
from datetime import datetime

def child(writer):
    i = 0
    while (i < 10):
        msg = "{}".format(i)
        writer.write(msg)
        i = i+1

def parent(reader):
    while (True):
        msg = reader.read(1)
        if msg:
            print(msg)


if __name__=="__main__":
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        writer = os.fdopen(w, 'w')
        child(writer)
        sys.exit(0)
    os.close(w)
    reader = os.fdopen(r)
    parent(reader)
    sys.exit(0)
