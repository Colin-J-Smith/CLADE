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
import threading
from datetime import datetime

from LaneGuidev10 import nav, nav_msg_size
from targeting import target, target_msg_size

# ----------------
# Setup
# ----------------

# lists for sending commands between modules
global nav_cmds, target_cmds

# Arduino comms variables
mtr_write = None
tur_write = None
arduino_port_tur = "/dev/ttyACM0"
arduino_baudrate_tur = 9600
arduino_port_mtr = "/dev/ttyUSB0"
arduino_baudrate_mtr = 9600

# testing variable
testing_pi_driver = False

# ----------------
# Driver Function
# ----------------

def driver():
    global mtr_write, tur_write
    
    # open serial to Arduino (or stdout for testing)
    if testing_pi_driver:
        mtr_write = sys.stdout
        tur_write = sys.stdout
        print("test output")
    else:
        tur_write = serial.Serial(port=arduino_port_tur, baudrate=arduino_baudrate_tur)
        mtr_write = serial.Serial(port=arduino_port_mtr, baudrate=arduino_baudrate_mtr)
        print("HW output")

    # Run navigation and targeting frame by frame. If navigation is turning, it
    # won't return until it is complete. If targeting is aiming, it won't
    # return until it is complete.
    while True:
        nav(mtr_write)
        target(tur_write)


if __name__=="__main__":
    driver()
