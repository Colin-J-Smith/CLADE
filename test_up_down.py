import os
import sys
import time
import serial
from datetime import datetime

# commands
fire    = "<FIR>"
stop    = "<STP>" # send STP when target is found
up      = "<UPP>"
down    = "<DWN>"
left    = "<LFT>"
right   = "<RGT>"
home    = "<HOM>" # send HOM when target has been hit/no bad target in sight


arduino_port_tur = "/dev/ttyACM0"
arduino_baudrate_tur = 9600

tur_write = serial.Serial(port=arduino_port_tur, baudrate=arduino_baudrate_tur)

t_end = time.time() + 2
while time.time() < t_end:
    tur_write.write(up.encode('utf-8'))

t_end = time.time() + 2
while time.time() < t_end:
    tur_write.write(down.encode('utf-8'))
