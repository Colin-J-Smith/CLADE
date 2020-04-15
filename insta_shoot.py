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
tur_write.write("right".encode('utf-8'))
tur_write.write("right".encode('utf-8'))
tur_write.write("right".encode('utf-8'))
tur_write.write("left".encode('utf-8'))
tur_write.write("left".encode('utf-8'))
tur_write.write("left".encode('utf-8'))
