# setup
import cv2
import numpy as np
import time
from datetime import datetime
import sys
from picamera.array import PiRGBArray
from picamera import PiCamera

camera = PiCamera()
camera.resolution = (640, 480)
camera.rotation = 180

# camera distortion corrections
k = np.array([[243.48186479, 0., 305.08168044],
              [0., 244.0802712, 226.73721762],
              [0., 0., 1.]])

d = np.array([-2.67227451e-01, 6.92939876e-02, 2.32058609e-03, 2.62454856e-05, -7.75020091e-03])

# grab a reference to the raw camera capture
rawCapture = PiRGBArray(camera, size=(640, 480))
camera.capture(rawCapture, format="bgr")

# convert to numpy array for use by cv2
raw_frame = rawCapture.array

# un-distort image
h, w = raw_frame.shape[:2]
new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(k, d, (w, h), 0)
map_x, map_y = cv2.initUndistortRectifyMap(k, d, None, new_camera_matrix, (w, h), 5)

frame = cv2.remap(raw_frame, map_x, map_y, cv2.INTER_LINEAR)


""" Define Region of Interest (ROI) for the intersection """
# currently the full screen, but can be adjusted to filter further
rows, cols = frame.shape[:2]
bottom_left = [cols * 0.1, rows * 1]
top_left = [cols * 0.1, rows * 0.0]
bottom_right = [cols * 0.9, rows * 1]
top_right = [cols * 0.9, rows * 0.0]
intersection_vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)

""" filter the region of interest (ROI) for the intersection using open cv modules"""

mask = np.zeros_like(frame)
if len(mask.shape) == 2:
    cv2.fillPoly(mask, intersection_vertices, 255)
else:
    # In case the input image has a channel dimension
    cv2.fillPoly(mask, intersection_vertices, (255,) * mask.shape[2])

ROI = cv2.bitwise_and(frame, mask)

# process image
# Convert image to grayscale and HSV, and filter out colors that aren't purple"
gray = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
processed_hsv = cv2.cvtColor(ROI, cv2.COLOR_BGR2HSV)
lower_purple = np.array([130, 80, 80], dtype=int)
upper_purple = np.array([170, 255, 220], dtype=int)
mask_purple = cv2.inRange(processed_hsv, lower_purple, upper_purple)
processed = cv2.bitwise_and(gray, mask_purple)

# smoothing
kernel_size = 3

processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)

# detect edges in the image
low_threshold = 130
high_threshold = 150

intersection_edges = cv2.Canny(processed, low_threshold, high_threshold)


filename = '1edge_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, intersection_edges)
filename = '1processed_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, processed)
filename = '1HSV_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, processed_hsv)
filename = '1frame_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, frame)