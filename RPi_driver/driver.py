# File:     driver.py
# Author:   Lea Chandler
# Date:     4/1/2020
# Version:  1
# Platform: Rasbian Buster with Python3
#
# Driver for the police academy robot. 

import os
import sys
import time
from datetime import datetime

from navigation import nav, nav_msg_size
from targeting import target, target_msg_size

testing = True # change to false to run on hardware

def driver():
    # navigation pipe
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0: # child
        os.close(r)
        nav_write = os.fdopen(w, 'w')
        nav(nav_write)
        sys.exit(0)
    os.close(w)
    nav_read = os.fdopen(r)
    
    # targeting pipe
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0: # child
        os.close(r)
        target_write = os.fdopen(w, 'w')
        target(target_write)
        sys.exit(0)
    os.close(w)
    target_read = os.fdopen(r)
    
    # receive and parse messages
    while True:
        is_nav_msg = process_msg(nav_read, nav_msg_size, process_nav_msg)
        is_target_msg = process_msg(target_read, target_msg_size, process_target_msg)
        if testing and not is_nav_msg and not is_target_msg:
            break # end program if testing 
        

def process_nav_msg(words):
    print("{}".format(words[0]))
    # TODO: handle commands


def process_target_msg(words):
    print("{}".format(words[0]))
    # TODO: handle commands


def process_msg(read, msg_size, process_fcn):
    # read messages without trailing whitespace
    msg = (read.read(msg_size)).strip()
    if not msg:
        return False # no message received
    
    # get the message receive time
    received = float(datetime.now().strftime('%S.%f'))
    
    # split message by words and get the sent time
    words = msg.split()
    sent = float(words[-1])
    
    # if delay between sending and receiving is greater than 0.5s, clear the
    #    assume that received messages will be old and clear the input buffer
    dt = received - sent
    if dt > 0.5:
        read.flush()
    
    # route parsed messgae to the correct handles (nav or target)
    process_fcn(words)
    return True


if __name__=="__main__":
    driver()
