# Targeting Software for a Live PiCam Feed
# Version: 4
# Author: Dan Warner
# Date Created: 11 Mar 2020, Dan Warner
# Last Modified: 17 Mar 2020, Lea Chandler
# TODO: test this


# setup
import cv2
import numpy as np
import imutils
import os
import time
from picamera.array import PiRGBArray
from picamera import PiCamera

# display options
show_thresholds = False
show_final_contour = False

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

    # create mask for lower red HSV values
    lower_red = np.array([0, 100, 120], dtype=int)
    upper_red = np.array([10, 255, 255], dtype=int)
    mask_red1 = cv2.inRange(processed_hsv, lower_red, upper_red)

    # create mask for upper red HSV values
    lower_red = np.array([170, 100, 120], dtype=int)
    upper_red = np.array([180, 255, 255], dtype=int)
    mask_red2 = cv2.inRange(processed_hsv, lower_red, upper_red)
    
    # create complete red mask
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
   
    # create mask for green HSV values
    lower_green = np.array([30, 100, 50], dtype=int)
    upper_green = np.array([90, 255, 255], dtype=int)
    mask_green = cv2.inRange(processed_hsv, lower_green, upper_green)

    # get red and green contours and thresholded images
    contours_red, processed_red = get_contours(grey, mask_red)
    contours_green, processed_green = get_contours(grey, mask_green)
   
    # show thresholded images
    if show_thresholds:
        cv2.namedWindow('Green threshold', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Green threshold', processed_green)
        cv2.namedWindow('Red threshold', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Red threshold', processed_red)

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
    
    # draw the contour and center of the shape on the image
    text = label+": ("+str(cX-x0)+","+str(cY-y0)+")"
    cv2.drawContours(contour_img, [contour], -1, (0,255,0), 2)
    cv2.circle(contour_img, (cX, cY), 7, (255, 255, 255), -1)
    cv2.putText(contour_img, text, (cX - 75, cY - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)   
    return contour_img


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


def process_frame(frame):

    # get all red and green contours from the image
    bad_guy_contours, good_guy_contours = process_targets(frame)

    # get the largest red and green contours
    largest_contour_bad, bad_size = get_largest_contour(bad_guy_contours)
    largest_contour_good, good_size = get_largest_contour(good_guy_contours)

    # if the largest contours are too small, assume no target has been found
    if bad_size < 8000 and good_size < 8000:
        contour_img = draw_no_target(frame)
        if show_final_contour: cv2.imshow('No target found', contour_img)

    # if the red contour is larger, assume a bad guy has been found
    elif bad_size > good_size:
        contour_img = draw_contours(frame, largest_contour_bad, 'Bad guy')
        if show_final_contour: cv2.imshow('Bad Guy!', contour_img)

    # if the green contour is larger, assume a good guy has been found
    else:
        contour_img = draw_contours(frame, largest_contour_good, 'Good guy')
        if show_final_contour: cv2.imshow('Good Guy!', contour_img)
    
    return contour_img


def main():
    
    frame_height = 640
    frame_width = 480

    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = (frame_height, frame_width)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=camera.resolution))

    # allow the camera to warmup
    time.sleep(0.1)


    # initialize the video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output_videos/PiCam_feed', fourcc, 30, camera.resolution, 1)
    
    # capture frames from the camera
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        
        # convert to numpy array for use by cv2
        frame = f.array
    
        # Apply image processing
        processed_frame = process_frame(frame)
        
        # Write and display the processed frame
        out.write(processed_frame)
        cv2.imshow("Live target finding", processed_frame)
        
        # Delay for key press to quit and frame rate (1 ms)
        key_pressed = cv2.waitKey(1) & 0xFF
        if key_pressed == ord('q'): break
        
        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

    # cleanup
    out.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()


# Functions:
#
# Name:         get_contours
# Description:  Finds contours in an image using a given mask
# Usage:        contours, processed = get_contours(grey_img, mask):
#   contours        - the contours found in the image
#   processed       - the final thresholded image
#   grey_img        - the grey image to process
#   mask            - the HSV color mask to apply to the image
#
# Name:         process_targets
# Description:  Finds the red and green contours in an image
# Usage:        contour_red, contour_green = process_targets(frame)
#   frame           - the image to process
#   contour_red     - all red contours in the image
#   contour_green   - all green contours in the image
#
# Name:         draw_contours
# Description:  Draws the given contour and its center on the given image
# Usage:        contour_img = draw_contours(frame, contour, label)
#   contour_img     - the image with contours
#   frame           - the base image
#   contour         - the contour to draw
#   label           - text to label the center
#
# Name:         get_largest_contour
# Description:  Finds the largest contour and its size from the given contours
# Usage:        largest_contour, size = get_largest_contour(contours)
#   largest_contour - the contour with the largest area
#   size            - the area of the largest contour
#   contours        - a list of contours

