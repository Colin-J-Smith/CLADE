# camera_init.py
# Author: Lea Chandler
# Date: 2/17/2020
# 
# Camera pipeline object initialization for the Luxonis USB3 stereo camera
# using the DepthAI shared library. Code modified from:
# https://github.com/luxonis/depthai-python-extras

import resources.depthai as depthai
import os
from os import path
from pathlib import Path


# ------------------------------------------------------------------------------
# Resource paths
# ------------------------------------------------------------------------------

def relative_to_abs_path(relative_path):
    dirname = Path(__file__).parent
    return str((dirname / relative_path).resolve())

device_cmd_file    = relative_to_abs_path('resources/depthai.cmd')
blob_file          = relative_to_abs_path('resources/mobilenet_ssd.blob')


# ------------------------------------------------------------------------------
# Init
# ------------------------------------------------------------------------------

def camera_init(streams=None, configs=None):

    # output streams: left, right, previewout, metaout, disparity, depth_sipp
    if streams is None:
        streams = ['left', 'right'] # make sure to always put 'left' first
 
    # camera configs
    if configs is None:
        configs = {
            'streams': streams,
            'depth': {
                'calibration_file': '', # we're going to do our own calibration since we're not using their AI
                # 'type': 'median',
                'padding_factor': 0.3
            },
            'ai': {  # camera won't run without this config defined, but we don't use it
                'blob_file': blob_file,
                'calc_dist_to_bb': False # I think this will decrease processing time
            },
            'board_config': {
                'swap_left_and_right_cameras': True, # True for 1097 (RPi Compute) and 1098OBC (USB w/onboard cameras)
                'left_fov_deg': 69.0, # Same on 1097 and 1098OBC
                'left_to_right_distance_cm': 7.5, # Distance between stereo cameras
            }
        }

    # camera init
    if not depthai.init_device(device_cmd_file):
        print("Error initializing device. Try to reset it.")
        exit(1)
    #end

    # create the pipeline, here is the first connection with the device
    pipeline = depthai.create_pipeline(config=configs)
    if pipeline is None:
        print('Pipeline is not created.')
        exit(2)
    #end

    return pipeline
#end camera_init()
