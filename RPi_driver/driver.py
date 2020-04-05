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

from navigation import nav, nav_msg_size
from targeting import target, target_msg_size

# states
initializing = 0
looking = 1
turning = 2
shooting = 3
state = initializing

# file objects for reading/writing
mtr_write = None
tur_write = None
nav_read = None
target_read = None

# Arduino comms variables
arduino_port_tur = "/dev/ttyUSB0"
arduino_baudrate_tur = 9600
arduino_port_mtr = "/dev/ttyUSB1"
arduino_baudrate_mtr = 9600

# testing variables
testing_pi_driver = True

def driver():
    while True:
        if state == initializing:
            init()
        elif state == looking:
            look()
        elif state == turning:
            turn()
        elif state == shooting:
            shoot()
        else:
            break # something went wrong


def init():
    global state, nav_read, target_read, mtr_write, tur_write

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
    
    # open serial to Arduino (or stdout for testing)
    if testing_pi_driver:
        mtr_write = sys.stdout
    else:
        tur_write = serial.Serial(port=arduino_port_tur, baudrate=arduino_baudrate_tur)
        mtr_write = serial.Serial(port=arduino_port_mtr, baudrate=arduino_baudrate_mtr)

    # change state
    state = looking


def look():
    process_msg(nav_read, nav_msg_size, process_nav_msg)
    process_msg(target_read, target_msg_size, process_target_msg)


def turn(): # if turning, ignore targeting commands
    process_msg(nav_read, nav_msg_size, process_nav_msg)
    target_read.flush()


def shoot(): # if shooting, ignore navigation commands
    nav_read.fush()
    process_msg(target_read, target_msg_size, process_target_msg)


def send_msg_mtr(msg):
    # forward message to the Arduino (without timestamp)
    mtr_write.write(msg)
    if mtr_write == sys.stdout:
        print("")


def send_msg_tur(msg):
    # forward message to the Arduino (without timestamp)
    tur_write.write(msg)
    if tur_write == sys.stdout:
        print("")


def process_nav_msg(words):
    # TODO: handle state transitions
    send_msg_mtr(" ".join(words[0:-1]))


def process_target_msg(words):
    # TODO: handle state transitions
    send_msg_tur(" ".join(words[0:-1]))


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
    
    # if delay between sending and receiving is greater than 0.5s, assume that
    #    the received messages will be old and clear the input buffer
    dt = received - sent
    if dt > 0.5:
        read.flush()
    
    # route parsed message to the correct handler (nav or target).
    # depending on design, the driver might just forward messages from the
    #    modules to the Arduino with no additional processing
    process_fcn(words)
    return True


if __name__=="__main__":
    driver()
