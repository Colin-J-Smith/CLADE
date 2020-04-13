# test_camera.py
# Author: Lea Chandler
# Date: 2/17/2020
# 
# Test driver for the Luxonis USB3 stereo camera using the DepthAI shared
# library. Code modified from:
# https://github.com/luxonis/depthai-python-extras
#
# TODO
# - debug flag to show frames

import sys
from time import time
import cv2

import resources.depthai as depthai
from camera_init import camera_init


# ------------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------------

# default font
font = cv2.FONT_HERSHEY_SIMPLEX

# camera pipeline
pipeline = camera_init()

# fps calc vars
t_start = time()
count = 0
fps = 0

# ------------------------------------------------------------------------------
# GET IMAGES
# ------------------------------------------------------------------------------

while True:
    # retreive data from the device (data is stored in packets)
    data_packets = pipeline.get_available_data_packets()

    # get image data from each camera (there's some other packets besides left and right - ignore them)
    for packet in data_packets:
        if packet.stream_name == 'left' or packet.stream_name == 'right':
            frame_bgr = packet.getData() # returns [Height, Width, Channel]
            #cv2.putText(frame_bgr, packet.stream_name, (25, 25), font, 1.0, (0, 0, 0))
            #cv2.putText(frame_bgr, "fps: " + str(fps), (25, 50), font, 1.0, (0, 0, 0))
            #cv2.imshow(packet.stream_name, frame_bgr)        
        #end
        count+=1
    #end

    # FPS calculation
    t_curr = time()
    if t_start + 1.0 < t_curr: # if one second has elapsed
        t_start = t_curr
        fps = count
        count = 0

    if cv2.waitKey(1) == ord('q'):
        break
#end

del p  # in order to stop the pipeline object should be deleted, otherwise device will continue working. This is required if you are going to add code after the main loop, otherwise you can ommit it.

print('py: DONE.')
