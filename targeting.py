# File:        targeting.py
# Author:      Lea Chandler
# Date:        4/6/2020
# Version:     1
# Platform:    Rasbian Buster with Python3
# Description: Targeting module for the police academy robot
#
# When called, targeting module gets a frame from the camera (see Known
# Issues). If a continous command is being sent, it sends the command again.
# Otherwise, if not waiting after sending a command or firing, the image is
# processed. If no target is found, the module will return control to the
# driver. If a target is found, the module will keep control and process images
# for aiming until the target is hit.
#
# Known issues:
# The Luxonis camera outputs data at a constant FPS (currently set to 12), and
# will fill the data buffer and crash if the data is not read fast enough. Much
# of the targeting design focuses on reading from this buffer constantly, even
# if the data will not be used.

# --------------------------
# IMPORTS
# --------------------------

import sys
import cv2
import time
import imutils
import numpy as np
from datetime import datetime

import luxonis_resources.depthai as depthai
from camera_init import camera_init 

# --------------------------
# GLOBALS
# --------------------------

# constants
cmd_delay = 0        # sec, delay before processing next image when aiming
fire_delay = 3       # sec, delay before processing next image after shooting
target_persist = 1.5 # sec, how long that seeing a target "persists"
cmd_timeout = 0      # sec, how long to send continuous cmd after first issue

# commands
fire    = "<FIR>"
stop    = "<STP>" # unused
up      = "<UPP>"
down    = "<DWN>"
left    = "<LFT>"
right   = "<RGT>"
home    = "<HOM>" # send HOM when target has been hit/no bad target in sight

# image processing masks (HSV has two red areas)
lower_red1 = np.array([0, 100, 120], dtype=int)
upper_red1 = np.array([10, 255, 255], dtype=int)
lower_red2 = np.array([170, 100, 120], dtype=int)
upper_red2 = np.array([180, 255, 255], dtype=int)

# targeting callibration
target_threshold = 3000 # red area threshold to determine valid target
tolX = 10               # tolerance for x "center" of image, in pixels
tolY = 10               # tolerance for y "center" of image, in pixels
offsetX = 22            # x-offset of center of image, in pixels
offsetY = 20            # y-offset of center of image, in pixels

# variables
global target_write     # object, to write commands to
camera = camera_init()  # object, Luxonis camera
target_last_seen = 0    # time, when target was last seen
fire_wait_start = 0     # time, wait start after firing
cmd_wait_start = 0      # time, wait start after sending command
cmd_start = 0           # time, first continuous command sent
last_cmd = home         # value, last command that was sent
sending_cmd = False     # bool, true if currently sending a continuous cmd


# --------------------------
# SUBSYSTEM FUNCTIONS
# --------------------------

def target(target_write_input):
    global target_write, sending_cmd
    
    # global writer initialization
    target_write = target_write_input

    is_aiming = True
    while is_aiming:

        # get camera data
        data_packets = camera.get_available_data_packets()

        # continous command timer (currently not sending continuous)
        if sending_cmd and time_since(cmd_start) < cmd_timeout:
            send_msg(last_cmd)
            continue
        else:
            sending_cmd = False
        
        # image processing
        for packet in data_packets:
            if packet.stream_name == 'previewout':
                data = packet.getData() # [Height, Width, Channel]
                data0 = data[0,:,:]
                data1 = data[1,:,:]
                data2 = data[2,:,:]
                frame_bgr = cv2.merge([data0, data1, data2])
                frame_bgr = cv2.flip(frame_bgr, 0)
                processed_frame, is_aiming = process_image(frame_bgr)
                #cv2.imshow("targeting", processed_frame)
                break
        
        if cv2.waitKey(1) == ord('q'):
            break


def send_msg(command, start_continuous=False):
    global cmd_wait_start, cmd_start, last_cmd, sending_cmd
    
    # command wait timer
    if time_since(cmd_wait_start) < cmd_delay: # currently not used
        return

    # send command
    if target_write == sys.stdout:
        print(command)
    else:
        print(command)
        target_write.write(command.encode('utf-8'))

    # start cmd wait timer
    cmd_wait_start = NOW()

    # start continous commands
    if start_continuous:
        sending_cmd = True
        last_cmd = command
        cmd_start = NOW()


def command_from_target_location(dx, dy):
    global fire_wait_start
    fire_ready = False # bool, true if aligned horizontally

    # status log
    print("Found target at ({}, {}), shooting at ({}+-{}, {}+-{})"
            .format(dx, dy, offsetX, tolX, offsetY, tolY))

    # horizontal axis alignment
    if dx - offsetX > tolX:
        #print("left")
        send_msg(left, True)
    elif dx - offsetX < -tolX:
        #print("right")
        send_msg(right, True)
    else:
        fire_ready = True
   
    # vertical axis aligment
    if dy - offsetY > tolY:
        #print("down")
        send_msg(down, True)
    elif dy - offsetY < -tolY:
        #print("up")
        send_msg(up, True)
    elif fire_ready:
        #time.sleep(1)
        #print("firing")
        if time_since(fire_wait_start) < fire_delay:
            return
        send_msg(fire)
        fire_wait_start = NOW() # wait after firing for target to fall


# --------------------------
# IMAGE PROCESSING FUNCTIONS
# --------------------------

def get_contours(frame):
    
    # kernel size for img processing (must be odd, larger = more processing)
    kernel_size = 25

    # Convert image to grayscale and HSV
    grey_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # create mask for red HSV values
    mask_red1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # apply the mask and a threshold
    processed = cv2.bitwise_and(grey_img, mask_red)
    processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)
    processed = cv2.threshold(processed, 30, 255, cv2.THRESH_BINARY)[1]
    
    # find contours
    contours = cv2.findContours(processed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    return contours


def draw_contours(frame, contour):
    
    # compute the center of the contour
    M = cv2.moments(contour)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # find image center
    processed_frame = frame
    height,width = processed_frame.shape[:2]
    x0 = width/2
    y0 = height/2

    # calculate offset from center
    dx = cX - x0
    dy = cY - y0
    
    # draw the contour and center of the shape on the image
    text = "Bad Guy: (" + str(dx) + "," + str(dy) + ")"
    cv2.drawContours(processed_frame, [contour], -1, (0,255,0), 2)
    cv2.circle(processed_frame, (cX, cY), 7, (255, 255, 255), -1)
    cv2.putText(processed_frame, text, (cX - 75, cY - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)   
    return processed_frame, dx, dy


def get_largest_contour(contours):
    if contours: # the list is not empty
        largest_contour = max(contours, key = cv2.contourArea)
        size = cv2.contourArea(largest_contour)
    else: # the list is empty
        largest_contour = None
        size = 0
    return largest_contour, size


def draw_no_target(frame):
    
    # add "no target" text to the image 
    processed_frame = frame    
    cv2.putText(processed_frame, "No target found", (20, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)   
    return processed_frame


def process_image(frame):
    global target_last_seen
    processed_frame = frame
    
    # get all red contours from the image
    red_contours = get_contours(frame)

    # get the largest red contour
    largest_contour, contour_size = get_largest_contour(red_contours)

    # if the largest contour is small, assume no target has been found
    if contour_size < target_threshold:
        processed_frame = draw_no_target(frame)

    # otherwise, assume a bad guy has been found
    else:
        processed_frame, dx, dy  = draw_contours(frame, largest_contour)
        command_from_target_location(dx, dy)
        target_last_seen = NOW()

    # If the target was seen recently, assume we still see the it (the camera
    # takes a sec to refocus when it moves). Otherwise, return turret to home
    is_aiming = True
    if time_since(target_last_seen) > target_persist:
        is_aiming = False
        send_msg(home)
    
    return processed_frame, is_aiming


# --------------------------
# UTIL FUNCTIONS
# --------------------------

# time in seconds since given time
def time_since(given_time):
    return int(NOW() - given_time)


# time right now
def NOW():
    return time.time()


# print commands to console when debugging as standalone module
if __name__=="__main__":
    while True:
        target(sys.stdout)
