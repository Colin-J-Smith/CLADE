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
bottom_left = [cols * 0.0, rows * 1]
top_left = [cols * 0.0, rows * 0.0]
bottom_right = [cols * 1, rows * 1]
top_right = [cols * 1, rows * 0.0]
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
lower_purple = np.array([130, 70, 80], dtype=int)
upper_purple = np.array([170, 255, 220], dtype=int)
mask_purple = cv2.inRange(processed_hsv, lower_purple, upper_purple)
processed = cv2.bitwise_and(gray, mask_purple)

# smoothing
kernel_size = 5

processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)

# detect edges in the image
low_threshold = 110
high_threshold = 130

intersection_edges = cv2.Canny(processed, low_threshold, high_threshold)

filename = '1edge_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, intersection_edges)
filename = '1processed_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, processed)
filename = '1HSV_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, processed_hsv)
filename = '1frame_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, frame)

# for report
# Hough Lines for intersection
lines = cv2.HoughLinesP(intersection_edges, rho=1, theta=np.pi / 360, threshold=50, minLineLength=60, maxLineGap=70)
line_image = np.zeros_like(frame)

# Create Main Lines by averaging all detected hough lines for intersection
left_fit = []
right_fit = []
horizontal_fit = []
quad1 = []
quad2 = []
quad3 = []
quad4 = []
slope = []
if lines is not None:
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        if (x1 - 5) < x2 < (x1 + 5):
            slope = 0
            pass
        else:
            slope = int((y2 - y1) / (x2 - x1))

        if (y2 - 40) < y1 < (y2 + 40):
            horizontal_fit.append((x1, y1, x2, y2))
            cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
        elif slope < -1 / 2:
            left_fit.append((x1, y1, x2, y2))
            cv2.line(line_image, (x1, y1), (x2, y2), (255, 255, 0), 2)

        elif slope > 1 / 2:
            right_fit.append((x1, y1, x2, y2))
            cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 255), 2)

        else:
            pass
            #horizontal_fit.append((x1, y1, x2, y2))
            #cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 255), 2)


else:
    pass
# Average horizontal lines into four quadrants
if len(horizontal_fit) > 0:
    for [x1, y1, x2, y2] in horizontal_fit:
        if 0 < ((int(y1) + int(y2)) / 2) <= 120:
            quad1.append((x1, y1, x2, y2))
        elif 120 < ((int(y1) + int(y2)) / 2) <= 240:
            quad2.append((x1, y1, x2, y2))
        elif 240 < ((int(y1) + int(y2)) / 2) <= 360:
            quad3.append((x1, y1, x2, y2))
        else:
            quad4.append((x1, y1, x2, y2))

left_int, right_int, quad1_int, quad2_int, quad3_int, quad4_int = [], [], [], [], [], []

if len(left_fit) > 0:
    left_fit_avg = np.average(left_fit, axis=0)
    x1 = int(left_fit_avg[0])
    y1 = int(left_fit_avg[1])
    x2 = int(left_fit_avg[2])
    y2 = int(left_fit_avg[3])
    left_int = [x1, y1, x2, y2]

left_int = np.array(left_int)

if len(right_fit) > 0:
    right_fit_avg = np.average(right_fit, axis=0)
    x1 = int(right_fit_avg[0])
    y1 = int(right_fit_avg[1])
    x2 = int(right_fit_avg[2])
    y2 = int(right_fit_avg[3])
    right_int = [x1, y1, x2, y2]

right_int = np.array(right_int)

if len(quad1) > 0:
    quad1_avg = np.average(quad1, axis=0)
    x1 = int(quad1_avg[0])
    y1 = int(quad1_avg[1])
    x2 = int(quad1_avg[2])
    y2 = int(quad1_avg[3])
    quad1_int = [x1, y1, x2, y2]
quad1_int = np.array(quad1_int)

if len(quad2) > 0:
    quad2_avg = np.average(quad2, axis=0)
    x1 = int(quad2_avg[0])
    y1 = int(quad2_avg[1])
    x2 = int(quad2_avg[2])
    y2 = int(quad2_avg[3])
    quad2_int = [x1, y1, x2, y2]
quad2_int = np.array(quad2_int)

if len(quad3) > 0:
    quad3_avg = np.average(quad3, axis=0)
    x1 = int(quad3_avg[0])
    y1 = int(quad3_avg[1])
    x2 = int(quad3_avg[2])
    y2 = int(quad3_avg[3])
    quad3_int = [x1, y1, x2, y2]
quad3_int = np.array(quad3_int)

if len(quad4) > 0:
    quad4_avg = np.average(quad4, axis=0)
    x1 = int(quad4_avg[0])
    y1 = int(quad4_avg[1])
    x2 = int(quad4_avg[2])
    y2 = int(quad4_avg[3])
    quad4_int = [x1, y1, x2, y2]
quad4_int = np.array(quad4_int)

thickness = 10
lane_image = np.zeros_like(frame)
if len(left_int) > 0:
    x1, y1, x2, y2 = left_int.reshape(4)
    cv2.line(lane_image, (x1, y1), (x2, y2), [255, 255, 0], thickness)
if len(right_int) > 0:
    x1, y1, x2, y2 = right_int.reshape(4)
    cv2.line(lane_image, (x1, y1), (x2, y2), [255, 0, 255], thickness)
if len(quad1_int) > 0:
    x1, y1, x2, y2 = quad1_int.reshape(4)
    cv2.line(lane_image, (x1, y1), (x2, y2), [255, 255, 255], thickness)
if len(quad2_int) > 0:
    x1, y1, x2, y2 = quad2_int.reshape(4)
    cv2.line(lane_image, (x1, y1), (x2, y2), [200, 200, 200], thickness)
if len(quad3_int) > 0:
    x1, y1, x2, y2 = quad3_int.reshape(4)
    cv2.line(lane_image, (x1, y1), (x2, y2), [120, 120, 120], thickness)
if len(quad4_int) > 0:
    x1, y1, x2, y2 = quad4_int.reshape(4)
    cv2.line(lane_image, (x1, y1), (x2, y2), [80, 80, 80], thickness)

filename = '1line_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, line_image)

filename = '1lane_image' + str(datetime.now()) + ".jpg"
cv2.imwrite(filename, lane_image)
