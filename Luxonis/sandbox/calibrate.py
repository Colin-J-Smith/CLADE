# calibrate.py
# Author: Lea Chandler
# Date: 2/17/2020
# 
# Calibration for theLuxonis USB3 stereo camera using the DepthAI shared
# library. Code modified from:
# https://github.com/luxonis/depthai-python-extras
# and
# https://github.com/realizator/stereopi-tutorial
#
# TODO
# - clean up argparser

#import time
#import numpy as np
#import os
from pathlib import Path
#import shutil
#import json
#import cv2

import resources.depthai as depthai
from camera_init import camera_init
from  calibration_utils import *

# camera settimgs
cam_width = 1280
cam_height = 1280


# ------------------------------------------------------------------------------
# CAPTURE CALIBRATION IMGS
# ------------------------------------------------------------------------------

def capture():
    # Delete Dataset directory if asked
    if args['image_op'] == 'delete':
        shutil.rmtree('dataset/')

    # Creates dirs to save captured images
    try:
        for path in ["left","right"]:
            Path("dataset/"+path).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print("An error occurred trying to create image dataset directories:",e)
        exit(0)

    # camera pipeline
    pipeline = camera_init()

    num_of_polygons = 0
    polygons_coordinates = []

    image_per_polygon_counter = 0 # variable to track how much images were captured per each polygon
    complete = False # Indicates if images have been captured for all polygons

    polygon_index = args['polygons'][0] # number to track which polygon is currently using
    total_num_of_captured_images = 0 # variable to hold total number of captured images

    capture_images = False # value to track the state of capture button (spacebar)
    captured_left_image = False # value to check if image from the left camera was capture
    captured_right_image = False # value to check if image from the right camera was capture

    run_capturing_images = True # value becames False and stop the main loop when all polygon indexes were used

    calculate_coordinates = False # track if coordinates of polygons was calculated
    total_images = args['count']*len(args['polygons'])

    while run_capturing_images:
        
        data_packets = pipeline.get_available_data_packets()
        
        for packet in data_packets:
            
            if packet.stream_name == 'left' or packet.stream_name == 'right':
                frame = packet.getData()
                
                if calculate_coordinates == False:
                    height, width = frame.shape
                    polygons_coordinates = setPolygonCoordinates(height, width)
                    num_of_polygons = len(args['polygons'])
                    print("Starting image capture. Press the [ESC] key to abort.")
                    print("Will take %i total images, %i per each polygon." % (total_images,args['count']))
                    calculate_coordinates = True

                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

                if capture_images == True:
                    if packet.stream_name == 'left':
                        filename = image_filename(packet.stream_name,polygon_index,total_num_of_captured_images)
                        cv2.imwrite("dataset/left/" + str(filename), frame)
                        print("py: Saved image as: " + str(filename))
                        captured_left_image = True

                    elif packet.stream_name == 'right':
                        filename = image_filename(packet.stream_name,polygon_index,total_num_of_captured_images)
                        cv2.imwrite("dataset/right/" + str(filename), frame)
                        print("py: Saved image as: " + str(filename))
                        captured_right_image = True

                    if captured_right_image == True and captured_left_image == True:
                        capture_images = False
                        captured_left_image = False
                        captured_right_image = False
                        total_num_of_captured_images += 1
                        image_per_polygon_counter += 1

                        if image_per_polygon_counter == args['count']:
                            image_per_polygon_counter = 0
                            try:
                                polygon_index = args['polygons'][args['polygons'].index(polygon_index)+1]
                            except IndexError:
                                complete = True

                if complete == False:
                    cv2.putText(frame, "Align cameras with callibration board and press spacebar to capture the image", (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0))
                    cv2.putText(frame, "Polygon Position: %i. " % (polygon_index) + "Captured %i of %i images." % (total_num_of_captured_images,total_images), (0, 700), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0))
                    cv2.polylines(frame, np.array([getPolygonCoordinates(polygon_index, polygons_coordinates)]), True, (0, 0, 255), 4)
                    # Resizing drastically reduces the framerate
                    # original image is 1280x720. reduce by 2x so it fits better.
                    # aspect_ratio = 1.5
                    # new_x, new_y = int(frame.shape[1]/aspect_ratio), int(frame.shape[0]/aspect_ratio)
                    # resized_image = cv2.resize(frame,(new_x,new_y))
                    cv2.imshow(packet.stream_name, frame)
                else:
                    # all polygons used, stop the loop
                    run_capturing_images = False

        key = cv2.waitKey(1)

        if key == ord(" "):
            capture_images = True

        elif key == ord("q"):
            print("py: Calibration has been interrupted!")
            exit(0)


    del pipeline # need to manualy delete the object, because of size of HostDataPacket queue runs out (Not enough free space to save {stream})

    cv2.destroyWindow("left")
    cv2.destroyWindow("right")
#end capture()

# ------------------------------------------------------------------------------
# PROCESS CALIBRATION IMGS
# ------------------------------------------------------------------------------


def process():
    print("Starting image processing")
    cal_data = StereoCalibration()
    try:
        cal_data.calibrate("dataset", args['square_size_cm'], "./resources/camera.calib")
    except AssertionError as e:
        print("[ERROR] " + str(e))
        exit(0)
#end process()


if __name__ == '__main__':
    args = vars(parse_args())
    print("Using Arguments=",args)

    if 'capture' in args['mode']:
        capture()
    else:
        print("Skipping capture.")

    if 'process' in args['mode']:
        process()
    else:
        print("Skipping process.")

    print('py: DONE.')
#end main
