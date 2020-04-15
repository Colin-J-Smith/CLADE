# File:     targeting.py
# Author:   Lea Chandler
# Date:     4/6/2020
# Version:  1
# Platform: Rasbian Buster with Python3
#
# Targeting module for the police academy robot

import sys
from datetime import datetime

global target_write
target_msg_size = 50

# commands
fire = "FIR"
stop = "STP" # send STP when target is found
up = "UPP"
down = "DWN"
left = "LFT"
right = "RGT"
home = "<HOM>" # send HOM when target has been hit


def target(target_write_input):
    global target_write
    target_write = target_write_input
    while (True):
        send_msg(home)

def send_msg(command):
    global target_write, target_msg_size
    time = datetime.now().strftime('%S.%f')
    command += " " + str(time)
    msg = command.ljust(target_msg_size)
    
    try:
        target_write.write(msg)
        target_write.flush()
    except:
        sys.exit(0)

    if target_write == sys.stdout:
        print("")


if __name__=="__main__":
    target(sys.stdout)
