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
import imutils
import numpy as np
from datetime import datetime

import luxonis_resources.depthai as depthai
from camera_init import camera_init

# --------------------------
# GLOBALS
# --------------------------

global target_write, pipeline
target_msg_size = 50

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

# TODO
# targeting callibration
tolX = 5    # tolerance for x "center" of image, in pixels
tolY = 5    # tolerance for y "center" of image, in pixels
offsetX = 0 # x-offset of center of image from center of robot, in pixels
offsetY = 0 # y-offset of center of image from center of robot, in pixels


# --------------------------
# SUBSYSTEM FUNCTIONS
# --------------------------

def target(target_write_input):
    global target_write, pipeline
    i = 0
    target_write = target_write_input
    pipeline = camera_init()
    while True:
        # retreive data from the device (data is stored in packets)
        data_packets = pipeline.get_available_data_packets()

        # get image data from the left and right cameras
        for packet in data_packets:
            if packet.stream_name == 'left': #or packet.stream_name == 'right':
                frame_bgr = packet.getData() # [Height, Width, Channel]
                print(len(frame_bgr[0]))
                print(len(frame_bgr[1]))
                print(len(frame_bgr[2]))
                print(len(frame_bgr))
                print(frame_bgr)
                cv2.imshow(packet.stream_name,frame_bgr)
                return
                #processed_frame = process_image(frame_bgr[2])
                #cv2.imshow(packet.stream_name, processed_frame)

        if cv2.waitKey(1) == ord('q'):
            break
    del pipeline


def send_msg(command):
    global target_write, target_msg_size
    time = datetime.now().strftime('%S.%f')
    command += " " + str(time)
    msg = command.ljust(target_msg_size)
    
    try:
        target_write.write(msg)
    except:
        sys.exit(0)

    if target_write == sys.stdout:
        print("")


def command_from_target_location(dx, dy):
    send_msg(stop) # command wheels to stop if target is found
    
    print("Found target at ({}, {})".format(dx, dy))

    if dx + offsetX > tolX: # center is in right side of image
        send_msg(left)
    elif dx + offsetX < -tolX:
        send_msg(right)
    
    if dy + offsetY > tolY: # center is in top half
        send_msg(down)
    elif dy + offsetY < -tolY:
        send_msg(up)


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

    # get all red and green contours from the image
    bad_guy_contours, good_guy_contours = process_targets(frame)

    # get the largest red and green contours
    largest_contour_bad, bad_size = get_largest_contour(bad_guy_contours)
    largest_contour_good, good_size = get_largest_contour(good_guy_contours)

    # if the largest contours are too small, assume no target has been found
    if bad_size < 8000 and good_size < 8000:
        contour_img = draw_no_target(frame)
        send_msg(home)
        
    # if the red contour is larger, assume a bad guy has been found
    elif bad_size > good_size:
        contour_img, dx, dy  = draw_contours(frame, largest_contour_bad, 'Bad guy')
        command_from_target_location(dx, dy)
        
    # if the green contour is larger, assume a good guy has been found
    else:
        contour_img, _, _ = draw_contours(frame, largest_contour_good, 'Good guy')
        send_msg(home)
    
    return contour_img


if __name__=="__main__":
    target(sys.stdout)
