# File:     targeting.py
# Author:   Lea Chandler
# Date:     4/6/2020
# Version:  1
# Platform: Rasbian Buster with Python3
#
# Targeting module for the police academy robot

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

global target_write, camera, initialized, target_last_seen, fire_wait_start, cmd_wait_start, last_cmd
cmd_delay = 0.5      # sec, delay before processing next image when targeting
fire_delay = 1.5     # sec, delay before processing next image after shooting
target_persist = 1.5 # sec, how long that seeing a target "persists"
cmd_timeout = 0      # sec, how long to send continuous command after issue
initialized = False  # bool, if module has been initialized yet


# commands
fire    = "<FIR>"
stop    = "<STP>" # send STP when target is found
up      = "<UPP>"
down    = "<DWN>"
left    = "<LFT>"
right   = "<RGT>"
home    = "<HOM>" # send HOM when target has been hit/no bad target in sight

# image processing masks
lower_red1 = np.array([0, 100, 120], dtype=int)
upper_red1 = np.array([10, 255, 255], dtype=int)
lower_red2 = np.array([170, 100, 120], dtype=int)
upper_red2 = np.array([180, 255, 255], dtype=int)
lower_green = np.array([30, 100, 50], dtype=int)
upper_green = np.array([90, 255, 255], dtype=int)

# targeting callibration
target_threshold = 5000
tolX = 10       # tolerance for x "center" of image, in pixels
tolY = 10       # tolerance for y "center" of image, in pixels
offsetX = 25   # x-offset of center of image from center of robot, in pixels
offsetY = 30  # y-offset of center of image from center of robot, in pixels


# --------------------------
# SUBSYSTEM FUNCTIONS
# --------------------------

def target(target_write_input):
    global target_write, initialized, camera, target_last_seen, fire_wait_start, last_cmd
    target_write = target_write_input
    
    if not initialized:
        camera = camera_init()
        target_last_seen = time.time()
        fire_wait_start = time.time()
        cmd_wait_start = time.time()
        last_cmd = home
        initialized = True

    is_aiming = True
    while is_aiming:
        data_packets = camera.get_available_data_packets()

        # timer handling
        if int(time.time - cmd_start) < cmd_timeout:
            send_msg(last_cmd, False)
            continue
        elif int(time.time() - cmd_wait_start) < cmd_delay:
            continue
        elif int(time.time() - fire_wait_start) < fire_delay:
            continue

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
                cv2.imshow("targeting", processed_frame)
                break
        
        if cv2.waitKey(1) == ord('q'):
            break


def send_msg(command, send_continuous):
    global cmd_wait_start, cmd_start, last_cmd
    if target_write == sys.stdout:
        print(command)
        return
    target_write.write(command.encode('utf-8'))
    cmd_wait_start = time.time()
    if send_continuous:
        cmd_start = time.time()


def command_from_target_location(dx, dy):
    global fire_wait_start
    fire_ready = False

    print("Found target at ({}, {}), shooting at ({}+-{}, {}+-{})"
            .format(dx, dy, offsetX, tolX, offsetY, tolY))

    if dx - offsetX > tolX:
        print("left")
        send_msg(left, True)
    elif dx - offsetX < -tolX:
        print("right")
        send_msg(right, True)
    else:
        fire_ready = True
   
    if dy - offsetY > tolY:
        print("down")
        send_msg(down, True)
    elif dy - offsetY < -tolY:
        print("up")
        send_msg(up, True)
    elif fire_ready == True:
        print("firing")
        send_msg(fire, False)
        fire_wait_start = time.time()


# --------------------------
# IMAGE PROCESSING FUNCTIONS
# --------------------------

def get_contours(grey_img, mask):
    
    # kernel size for img processing (must be odd, larger = more processing)
    kernel_size = 25

    # apply the mask and a threshold
    processed = cv2.bitwise_and(grey_img, mask)
    processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)
    processed = cv2.threshold(processed, 30, 255, cv2.THRESH_BINARY)[1]
    
    # find contours
    contours = cv2.findContours(processed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    return contours, processed


def process_targets(frame):

    # Convert image to grayscale and HSV
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    processed_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # create mask for red HSV values
    mask_red1 = cv2.inRange(processed_hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(processed_hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
   
    # create mask for green HSV values
    mask_green = cv2.inRange(processed_hsv, lower_green, upper_green)

    # get red and green contours and thresholded images
    contours_red, processed_red = get_contours(grey, mask_red)
    contours_green, processed_green = get_contours(grey, mask_green)

    # return the red and green contours
    return contours_red, contours_green


def draw_contours(frame, contour, label):
    
    # compute the center of the contour
    M = cv2.moments(contour)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # find image center
    contour_img = frame
    height,width = contour_img.shape[:2]
    x0 = width/2
    y0 = height/2

    # calculate offset from center
    dx = cX - x0
    dy = cY - y0
    
    # draw the contour and center of the shape on the image
    text = label+": ("+str(dx)+","+str(dy)+")"
    cv2.drawContours(contour_img, [contour], -1, (0,255,0), 2)
    cv2.circle(contour_img, (cX, cY), 7, (255, 255, 255), -1)
    cv2.putText(contour_img, text, (cX - 75, cY - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)   
    return contour_img, dx, dy


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
    contour_img = frame    
    cv2.putText(contour_img, "No target found", (20, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)   
    return contour_img


def process_image(frame):
    global target_last_seen
    
    # get all red and green contours from the image
    bad_guy_contours, good_guy_contours = process_targets(frame)

    # get the largest red and green contours
    largest_contour_bad, bad_size = get_largest_contour(bad_guy_contours)
    largest_contour_good, good_size = get_largest_contour(good_guy_contours)

    # if the largest contours are too small, assume no target has been found
    if bad_size < target_threshold and good_size < target_threshold:
        contour_img = draw_no_target(frame)
        
    # if the red contour is larger, assume a bad guy has been found
    elif bad_size > good_size:
        contour_img, dx, dy  = draw_contours(frame, largest_contour_bad, 'Bad guy')
        command_from_target_location(dx, dy)
        target_last_seen = time.time()
        
    # if the green contour is larger, assume a good guy has been found
    else:
        contour_img, _, _ = draw_contours(frame, largest_contour_good, 'Good guy')

    is_aiming = True
    if int(time.time() - target_last_seen) > target_persist:
        is_aiming = False
        send_msg(home, False)
    
    return contour_img, is_aiming


if __name__=="__main__":
    while True:
        target(sys.stdout)
