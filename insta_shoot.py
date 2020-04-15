import os
import sys
import time
import serial
from datetime import datetime

arduino_port_tur = "/dev/ttyACM0"
arduino_baudrate_tur = 9600

tur_write = serial.Serial(port=arduino_port_tur, baudrate=arduino_baudrate_tur)
tur_write.write("<FIR>".encode('utf-8'))
