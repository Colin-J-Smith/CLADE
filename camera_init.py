# camera_init.py
# Author: Lea Chandler
# Date: 2/17/2020
# 
# Camera pipeline object initialization for the Luxonis USB3 stereo camera
# using the DepthAI shared library. Code modified from:
# https://github.com/luxonis/depthai-python-extras

# --------------------------
# IMPORTS
# --------------------------

import luxonis_resources.depthai as depthai
import os
from os import path
from pathlib import Path


# --------------------------
# RESOURCE PATHS
# --------------------------

def relative_to_abs_path(relative_path):
    dirname = Path(__file__).parent
    return str((dirname / relative_path).resolve())

device_cmd_file    = relative_to_abs_path('luxonis_resources/depthai.cmd')
blob_file          = relative_to_abs_path('luxonis_resources/mobilenet_ssd.blob')


# --------------------------
# INIT
# --------------------------

def camera_init(streams=None, configs=None):

    # output streams: left, right, previewout, metaout, disparity, depth_sipp, depth_color_h
    if streams is None:
        #streams = ['left', 'right', 'previewout'] # make sure to always put 'left' first
        streams = ['left', 'previewout'] # make sure to always put 'left' first
 
    # camera configs
    if configs is None:
        configs = {
            'streams': streams,
            'depth': {
                'calibration_file': '', # we're going to do our own calibration since we're not using their AI
                'padding_factor': 0.3
            },
            'ai': { 
                'blob_file': blob_file,
                'calc_dist_to_bb': False                # I think this will decrease processing time
            },
            'board_config': {
                'swap_left_and_right_cameras': True,    # True for 1097 (RPi Compute) and 1098OBC (USB w/onboard cameras)
                'left_fov_deg': 69.0,                   # Same on 1097 and 1098OBC
                'left_to_right_distance_cm': 7.5,       # Distance between stereo cameras
            }
        }

    # camera init
    if not depthai.init_device(device_cmd_file):
        print("Error initializing device. Try to reset it.")
        exit(1)

    # create the pipeline, here is the first connection with the device
    pipeline = depthai.create_pipeline(config=configs)
    if pipeline is None:
        print('Pipeline is not created.')
        exit(2)

    return pipeline

# --------------------------
# GET_IMAGE
# --------------------------

def get_image(pipeline):
    # retreive data from the device (data is stored in packets)
    data_packets = pipeline.get_available_data_packets()

    # get image data from the left and right cameras
    for packet in data_packets:
        if packet.stream_name == 'previewout':
            data = packet.getData() # [Height, Width, Channel]
            data0 = data[0,:,:]
            data1 = data[1,:,:]
            data2 = data[2,:,:]
            frame_bgr = cv2.merge([data0, data1, data2])
            frame_bgr = cv2.flip(frame_bgr, 0)
            cv2.imshow(packet.stream_name, processed_frame)
            return frame_bgr
