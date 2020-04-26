# LaneGuidance Software
# Version: 10!
# Date Created: 2 Mar 2020
# Last Modified: 21 April 2020
# Updates this version: 
# Navigation is ON through the intersection. 
# Dead end logic is ON. 
# Opening logic adjusted (starts at int_count =1). 
# Intersection logic updated to allow for tight intersection areas


# setup
import cv2
import numpy as np
import time
from datetime import datetime
import sys
from picamera.array import PiRGBArray
from picamera import PiCamera

global turn
global delay


# camera intialization global
global initialized, camera
initialized = False

# set initial state machine
" State values modify which if statements the program runs through as it makes decisions"
intersection_state = 0
state1 = 0
int_count = 0  # start at one for purposes of the "starting area"
fail_safe_count = 0
nav_write = sys.stdout
nav_msg_size = 50

right_int_count = 0
left_int_count = 0
camera_init = 0

# delay timers
delay_90 = 6
delay_180 = 12
delay_0 = 1

# create log file
now = datetime.now()
logfile = str("log") + str(now) + str(".txt")


def nav(nav_write_input):
    global nav_write, camera, initialized
    nav_write = nav_write_input
    
    # initialize the camera
    if not initialized:
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.rotation = 180
        initialized = True

    # # Uncomment to diable nav with testing turret
    # msg("<STP>")
    main()


def msg(command):
    global nav_write
    if nav_write == sys.stdout:
        print(command)
    else:
        nav_write.write(command.encode('utf-8'))
        nav_write.flush()


def lane_roi(frame):
    """Define a region of interest (polygon) for processing yellow lanes"""
    # Define Region of Interest (ROI)
    rows, cols = frame.shape[:2]
    bottom_left = [cols * 0.00, rows * 1.00]
    mid_left = [cols * 0.00, rows * 0.7]
    top_left = [cols * 0.1, rows * 0.40]
    top_right = [cols * 0.9, rows * 0.40]
    mid_right = [cols * 1.0, rows * 0.7]
    bottom_right = [cols * 1.00, rows * 1.00]

    lane_vertices = np.array([[bottom_left, mid_left, top_left, top_right, mid_right, bottom_right]], dtype=np.int32)
    return lane_vertices


def process_lanes(frame, lane_vertices):
    """ Process yellow lane lines using a series of open cv modules"""
    mask = np.zeros_like(frame)
    if len(mask.shape) == 2:
        cv2.fillPoly(mask, lane_vertices, 255)
    else:
        # In case the input image has a channel dimension
        cv2.fillPoly(mask, lane_vertices, (255,) * mask.shape[2])

    ROI = cv2.bitwise_and(frame, mask)

    # Convert image to grayscale and HSV, and filter out colors that aren't yellow
    grey = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
    processed_hsv = cv2.cvtColor(ROI, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([10, 30, 130], dtype=int)
    upper_yellow = np.array([40, 255, 255], dtype=int)
    mask_yellow = cv2.inRange(processed_hsv, lower_yellow, upper_yellow)
    processed = cv2.bitwise_and(grey, mask_yellow)

    # Smooth the Image for processing. Kernel size must be odd. Larger kernel size means more processing
    kernel_size = 3

    processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)

    # detect edges in the image
    low_threshold = 50
    high_threshold = 150

    lane_edges = cv2.Canny(processed, low_threshold, high_threshold)
    return lane_edges


def create_lanes(lane_edges, frame):
    """ Use hough line transform to create many lines which roughly map the edges we created earlier """
    global int_count

    # Hough Lines - Create lines over the lanes
    # these are important parameters for adjusting how it will create lines. Adjusting them can fix issues
    lines = cv2.HoughLinesP(lane_edges, rho=1, theta=np.pi / 360, threshold=50, minLineLength=150, maxLineGap=100)

    # Create Main Lines by averaging all detected hough lines
    # Bin main lines into three separate categories: left, right, center
    line_image = np.zeros_like(frame)

    left_fit = []
    right_fit = []
    center_fit = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            if (y2 - 50) < y1 < (y2 + 50):
                center_fit.append((x1, y1, x2, y2))
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            else:
                slope = (y2 - y1) / (x2 - x1)
                if slope < 0:
                    left_fit.append((x1, y1, x2, y2))
                    cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                elif slope > 0:
                    right_fit.append((x1, y1, x2, y2))
                    cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                elif x1 < 300:
                    left_fit.append((x1, y1, x2, y2))
                    cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                elif x1 > 340:
                    right_fit.append((x1, y1, x2, y2))
                    cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                else:
                    pass

    left_line, right_line, center_line = [], [], []
    if len(left_fit) > 0:
        left_fit_avg = np.average(left_fit, axis=0)
        x1 = int(left_fit_avg[0])
        y1 = int(left_fit_avg[1])
        x2 = int(left_fit_avg[2])
        y2 = int(left_fit_avg[3])
        left_line = [x1, y1, x2, y2]
        left_line = np.array(left_line)

    if len(right_fit) > 0:
        right_fit_avg = np.average(right_fit, axis=0)
        x1 = int(right_fit_avg[0])
        y1 = int(right_fit_avg[1])
        x2 = int(right_fit_avg[2])
        y2 = int(right_fit_avg[3])
        right_line = [x1, y1, x2, y2]
        right_line = np.array(right_line)

    if len(center_fit) > 0:
        center_fit_avg = np.average(center_fit, axis=0)
        x1 = int(center_fit_avg[0])
        y1 = int(center_fit_avg[1])
        x2 = int(center_fit_avg[2])
        y2 = int(center_fit_avg[3])
        center_line = [x1, y1, x2, y2]
        center_line = np.array(center_line)

        # this is a detection lane at 400 pixels down from the top of the screen (out of 480) that will assist counting
        # when a center line crosses
        detection_lane = 300  # may need to be tweaked
        # count the number of times a center line crosses the detection lane
        # two int_counts lets the robot know its in the center of an intersection
        if intersection_state == 1:
            avg_center_line = (int(center_line[1]) + int(center_line[3])) / 2
            AbsDistance_center = abs(avg_center_line - detection_lane)
            if AbsDistance_center <= 50:
                int_count += 1
                with open(logfile, "a") as f:
                    print("yellow counted", file = f)
            with open(logfile, "a") as f:
                print("lane counter is ON! - Abs Distance =", AbsDistance_center, "center_line =", avg_center_line, file=f)

    return right_line, left_line, center_line


def draw_lanes(frame, right_line, left_line, center_line, left_int, right_int, quad1_int, quad2_int, quad3_int,
               quad4_int):
    # draw lane lines
    # may not be necessary in final code. Draws the lanes on an image
    thickness = 10
    lane_image = np.zeros_like(frame)

    if len(right_line) > 0:
        x1, y1, x2, y2 = right_line.reshape(4)
        cv2.line(lane_image, (x1, y1), (x2, y2), [255, 0, 0], thickness)
    if len(left_line) > 0:
        x1, y1, x2, y2 = left_line.reshape(4)
        cv2.line(lane_image, (x1, y1), (x2, y2), [0, 255, 0], thickness)
    if len(center_line) > 0:
        x1, y1, x2, y2 = center_line.reshape(4)
        cv2.line(lane_image, (x1, y1), (x2, y2), [0, 0, 255], thickness)
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

    return lane_image


def show_test(lane_image):
    """ displays picture with lanes and intersections - for testing/visualization purposes only """
    cv2.namedWindow('lanes', cv2.WINDOW_AUTOSIZE)  # create a window
    cv2.imshow('lanes', lane_image)  # show the image in that window


def navigation(frame, center_line, right_line, left_line):
    global turn
    global delay
    global state1
    global intersection_state
    global int_count
    global delay_180

    """ Navigation decision making script """
    center_recalibration = 0.95  # move the center point slightly left
    height, width, _ = frame.shape
    mid = int((width / 2)*center_recalibration)
    nav_point_x = mid

    if len(center_line) > 0:
        center_length = abs(center_line[0] - center_line[3])
    else:
        center_length = 0
    # if no intersections are visible and there is a right, left, and center lane command a turn around (dead end)
    with open(logfile, "a") as f:
        print("C=", center_line, center_length, "L_l=", left_line, "R_l=", right_line, file=f)
    if state1 == 0 and len(center_line) > 0 and center_length > 20 and \
            (int(center_line[1]) + int(center_line[3])) / 2 > 200 and len(right_line) > 0 and len(left_line) > 0:
        left_x2 = left_line[2]
        right_x2 = right_line[0]
        nav_point_x = int((left_x2 + right_x2) / 2)
        with open(logfile, "a") as f:
            print("turn around", file=f)
        delay = delay_180
        turn = "<LLL>"
        start_turn = time.time()
        while int(time.time() - start_turn) < delay:
            command = turn
            msg(command)
        state1 = 0
        intersection_state = 0
        int_count = 0
        command = "<FWD>"
    # guidance decisions for most normal situations - may need to add later movement based on testing
    elif len(right_line) > 0 and len(left_line) > 0:
        left_x2 = left_line[2]
        right_x2 = right_line[0]
        nav_point_x = int((left_x2 + right_x2) / 2)
        if left_line[0] > 250:
            command = "<RGT>"
        elif right_line[2] < 390:
            command = "<LFT>"
        elif nav_point_x > int(1.1 * mid):
            command = "<RRR>"
        elif nav_point_x < int(.9 * mid):
            command = "<LLL>"
        else:
            command = "<FWD>"
    elif len(right_line) > 0:
        right_x2 = right_line[0]
        nav_point_x = int(right_x2 - 200)
        if nav_point_x < int(mid):
            command = "<LLL>"
        elif right_line[2] < 390:
            command = "<LFT>"
        else:
            command = "<FWD>"
    elif len(left_line) > 0:
        left_x2 = left_line[2]
        left_x1 = left_line[0]
        nav_point_x = int(left_x2 + 200)
        if nav_point_x > int(mid):
            command = "<RRR>"
        elif left_line[0] > 250:
            command = "<RGT>"
        else:
            command = "<FWD>"
    else:
        with open(logfile, "a") as f:
            print("no lines detected - drive straight", file=f)
        command = "<FWD>"

    # cv2.line(lane_image, (mid, height), (nav_point_x, int(height/2)), [0, 255, 255], 10)
    return command


def intersection_roi(frame):
    """ Define Region of Interest (ROI) for the intersection """
    # currently the full screen, but can be adjusted to filter further
    rows, cols = frame.shape[:2]
    bottom_left = [cols * 0.1, rows * 1]
    top_left = [cols * 0.1, rows * 0.0]
    bottom_right = [cols * 0.9, rows * 1]
    top_right = [cols * 0.9, rows * 0.0]
    intersection_vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
    return intersection_vertices


def process_intersection(frame, intersection_vertices):
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
    lower_purple = np.array([130, 80, 100], dtype=int)
    upper_purple = np.array([170, 255, 210], dtype=int)
    mask_purple = cv2.inRange(processed_hsv, lower_purple, upper_purple)
    processed = cv2.bitwise_and(gray, mask_purple)

    # smoothing
    kernel_size = 3

    processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)

    # detect edges in the image
    low_threshold = 130
    high_threshold = 150

    intersection_edges = cv2.Canny(processed, low_threshold, high_threshold)

    return intersection_edges, processed


def create_intersection(intersection_edges, frame):
    """ Create intersections. The program bins intersections into right, left, and horizontal bins.
    Horizontal bins are further filtered into four quadrants from top to bottom. T
    his keeps the computer from trying to average two different horizontal lines into
    one, which causes errors """

    global intersection_state
    global state1
    global int_count
    global left_int_count
    global right_int_count
    global fail_safe_count

    # Hough Lines for intersection
    lines = cv2.HoughLinesP(intersection_edges, rho=1, theta=np.pi / 360, threshold=50, minLineLength=30, maxLineGap=70)
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
            if x2 == x1:
                slope = 0
                pass
            else:
                slope = int((y2 - y1) / (x2 - x1))

            if (y2 - 20) < y1 < (y2 + 20):
                horizontal_fit.append((x1, y1, x2, y2))
                # cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
            elif slope < -1 / 2:
                left_fit.append((x1, y1, x2, y2))
                # cv2.line(line_image, (x1, y1), (x2, y2), (255, 255, 0), 2)

            elif slope > 1 / 2:
                right_fit.append((x1, y1, x2, y2))
                # cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 255), 2)

            else:
                horizontal_fit.append((x1, y1, x2, y2))
                # cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
    else:
        pass
    # Average horizontal lines into four quadrants
    if len(horizontal_fit) > 0:
        for [x1, y1, x2, y2] in horizontal_fit:
            if 0 < ((int(y1)+int(y2))/2) <= 120:
                quad1.append((x1, y1, x2, y2))
            elif 120 < ((int(y1)+int(y2))/2) <= 240:
                quad2.append((x1, y1, x2, y2))
            elif 240 < ((int(y1)+int(y2))/2) <= 360:
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
        left_int_count += 1
    left_int = np.array(left_int)

    if len(right_fit) > 0:
        right_fit_avg = np.average(right_fit, axis=0)
        x1 = int(right_fit_avg[0])
        y1 = int(right_fit_avg[1])
        x2 = int(right_fit_avg[2])
        y2 = int(right_fit_avg[3])
        right_int = [x1, y1, x2, y2]
        right_int_count += 1
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

    # Count the number of horizontal intersection lines that pass through the detection lane at the bottom of the screen
    # by adding 1 to the int count
    detection_lane = 250
    if len(quad3_int) > 0:
        avg_y = (int(quad3_int[1]) + int(quad3_int[3]))/2
        AbsDistance = abs(avg_y - detection_lane)
        if intersection_state == 1:
            if AbsDistance <= 30 and avg_y > detection_lane:
                int_count += 1
                fail_safe_count += 1
                with open(logfile, "a") as f:
                    print("purple counted", file =f)
            with open(logfile, "a") as f:
                print("intersection counter is ON! - Abs Distance =", AbsDistance, "center_line =", avg_y, file=f)

    #  Fail safe counter for tight intersections. If it misses the quad three this will back it up
    elif len(quad4_int) > 0 and fail_safe_count == 0:
        avg_y = (int(quad4_int[1]) + int(quad4_int[3]))/2
        AbsDistance = abs(avg_y - detection_lane)
        if intersection_state == 1:
            if (AbsDistance <= 30) and (avg_y > 420):
                int_count += 1
                with open(logfile, "a") as f:
                    print("FAILSAFE purple counted", file = f)
    with open(logfile, "a") as f:
        print("L:", left_int, "R:", right_int, "q1", quad1_int, "q2", quad2_int,"q3:",
              quad3_int, "q4:", quad4_int, file=f)


    """ state modifier"""
    # state1 == 1 when the camera detects intersection lines and the bottom of those lines is low enough in the field
    # of view that the system can make a guidance decision with a high degree of confidence. This ensures we see the
    # entire intersection before making a decision. State1 == 1 turns 'on' the guidance decision function
    # while state1 == 0 the robot simply drives between yellow lines while scanning for intersections. After a guidance
    # decision is made, state1 == 2 and the guidance decision is locked in and turned off.
    # intersection_state == 0 indicates a guidance decision has not been made. The robot will simply drive through
    # yellow lines. After a guidance decision has been made intersection_state == 1 and the robot will continue to
    # navigate while counting purple and yellow lines that cross through a boundary line at the bottom of the screen.
    # after counting two lines, the robot is approximately in the center of the intersection,
    # intersection_state == 2....the robot sends a command to go left, straight, or right and resets all states to zero
    if state1 == 2:
        if int_count == 2:
            intersection_state = 2
    elif lines is not None:
        if len(left_int) > 0 and left_int[1] > 200:
            state1 = 1
        elif len(quad3_int) > 0 and 240 < quad3_int[1] < 300:
            state1 = 1
        elif len(right_int) > 0 and right_int[3] > 200:
            state1 = 1

    return slope, left_int, right_int, quad1_int, quad2_int, quad3_int, quad4_int


def guidance_decision(left_int, right_int, quad1_int, quad2_int, quad3_int, quad4_int):
    global turn
    global intersection_state
    global int_count
    global state1
    global delay
    global delay_180
    global delay_90
    global delay_0

    turn_left = 0
    priority = turn_left

    if len(left_int) > 0:
        turn = "<LLL>"
        delay = delay_90
        intersection_state = 1
    elif (len(quad1_int) > 0 and len(quad2_int) > 0 and (abs(quad1_int[1] - quad2_int[1]) > 100)) or \
            (len(quad1_int) > 0 and len(quad3_int) > 0) or (len(quad2_int) > 0 and
                                                len(quad3_int) > 0 and (abs(quad2_int[1] - quad3_int[1]) > 100)):
        turn = "<FWD>"
        delay = delay_0
        intersection_state = 1
    elif len(right_int) > 0:
        turn = "<RRR>"
        delay = delay_90
        intersection_state = 1
    else:
        with open(logfile, "a") as f:
            print("guidance decisions aren't working", turn, file=f)
        state1 = 0
        intersection_state = 0
        int_count = 0
        turn = "<FWD>"
        delay = delay_0

    # for testing
    with open(logfile, "a") as f:
        print("guidance decision is:", turn, file=f)


def main():
    global state1
    global intersection_state
    global int_count
    global logfile
    global fail_safe_count
    global camera

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

    lane_vertices = lane_roi(frame)
    lane_edges = process_lanes(frame, lane_vertices)
    right_line, left_line, center_line = create_lanes(lane_edges, frame)
    intersection_vertices = intersection_roi(frame)
    intersection_edges, processed = process_intersection(frame, intersection_vertices)
    slope, left_int, right_int, quad1_int, quad2_int, quad3_int, quad4_int = create_intersection(intersection_edges,
                                                                                                 frame)
    # lane_image = draw_lanes(frame, right_line, left_line, center_line, left_int, right_int, quad1_int, quad2_int,
                            # quad3_int, quad4_int)
    if state1 == 1:
        # make a guidance decision
        guidance_decision(left_int, right_int, quad1_int, quad2_int, quad3_int, quad4_int)
        filename = '1test_image' + str(time.time()) + ".jpg"
        cv2.imwrite(filename, frame)
        filename_2 = '1edge_image' + str(time.time()) + ".jpg"
        cv2.imwrite(filename_2, intersection_edges)
        filename_4 = '1processed_image' + str(time.time()) + ".jpg"
        cv2.imwrite(filename_4, processed)
        command = navigation(frame, center_line, right_line, left_line)
        msg(command)
        state1 = 2
    elif intersection_state == 0:
        # Navigate yellow lines
        command = navigation(frame, center_line, right_line, left_line)
        msg(command)
    elif intersection_state == 1:
        # command = navigation(frame, center_line, right_line, left_line)
        command = "<FWD>"
        msg(command)
        with open(logfile, "a") as q:
            print("drive", command, file=q)
            print("int count is:", int_count, file=q)
    elif intersection_state == 2:
        # execute decision and reset all states
        with open(logfile, "a") as q:
            print("Go", turn, file=q)
        # pause execution of decisions until turn has been completed
        start_turn = time.time()
        while int(time.time() - start_turn) < delay:
            command = turn
            msg(command)
        state1 = 0
        intersection_state = 0
        int_count = 0
        fail_safe_count = 0

    with open(logfile, "a") as q:
        print("intersection_state=", intersection_state, "state1=", state1,  file=q)
    # show_test(lane_image)

    key_pressed = cv2.waitKey(1) & 0xFF          # Delay for key press to quit and frame rate (1 ms)
    if key_pressed == ord('q'):

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

        # cleanup
        cv2.destroyAllWindows()


if __name__=="__main__":
    while True:
        nav(sys.stdout)

cv2.waitKey()
