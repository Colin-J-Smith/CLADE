# LaneGuidance Software
# Version: 2
# Date Created: 2 Mar 2020
# Last Modified: 10 Mar 2020


# setup
import cv2
import numpy as np
import time
from picamera.array import PiRGBArray
from picamera import PiCamera

# set initial state machine
intersection_state = 1
state1 = 0
int_on = 0
global turn



def lane_roi(frame):
    # Define Region of Interest (ROI)
    rows, cols = frame.shape[:2]
    bottom_left = [cols * 0.00, rows * 1.00]
    top_left = [cols * 0.15, rows * 0.30]
    bottom_right = [cols * 1.00, rows * 1.00]
    top_right = [cols * 0.85, rows * 0.30]
    lane_vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
    return lane_vertices


def process_lanes(frame, lane_vertices):
    # Create a polygon at the bottom of the frame to target only lane lines that we want to see

    mask = np.zeros_like(frame)
    if len(mask.shape) == 2:
        cv2.fillPoly(mask, lane_vertices, 255)
    else:
        # In case the input image has a channel dimension
        cv2.fillPoly(mask, lane_vertices, (255,) * mask.shape[2])

    ROI = cv2.bitwise_and(frame, mask)

    # Convert image to grayscale and HSV, and filter out colors that aren't white or yellow
    grey = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
    processed_hsv = cv2.cvtColor(ROI, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([10, 0, 130], dtype=int)
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
    # Hough Lines - Create lines over the lanes

    # these are important parameters for adjusting how it will create lines. Adjusting them can fix issues
    lines = cv2.HoughLinesP(lane_edges, rho=1, theta=np.pi / 360, threshold=50, minLineLength=150, maxLineGap=100)

    # Create Main Lines by averaging all detected hough lines
    line_image = np.zeros_like(frame)

    left_fit = []
    right_fit = []
    center_fit = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            if (y2 - 30) < y1 < (y2 + 30):
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

    return right_line, left_line, center_line


def draw_lanes(frame, right_line, left_line, center_line, left_int, right_int, bottom_int, top_int):
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
    if len(bottom_int) > 0:
        x1, y1, x2, y2 = bottom_int.reshape(4)
        cv2.line(lane_image, (x1, y1), (x2, y2), [0, 255, 255], thickness)
    if len(top_int) > 0:
        x1, y1, x2, y2 = top_int.reshape(4)
        cv2.line(lane_image, (x1, y1), (x2, y2), [100, 100, 100], thickness)

    return lane_image


def show_test(lane_image):
    # displays picture with lanes and intersections - for testing/visualization purposes
    cv2.namedWindow('lanes', cv2.WINDOW_AUTOSIZE)  # create a window
    cv2.imshow('lanes', lane_image)  # show the image in that window


def navigation(frame, center_line, right_line, left_line, lane_image):
    # navigation decision making script
    height, width, _ = frame.shape
    mid = int(width / 2)
    nav_point_x = mid

    if len(center_line) > 50 and center_line[0] > 300 and len(right_line) > 0 and len(left_line) > 0:
        left_x2 = left_line[2]
        right_x2 = right_line[0]
        nav_point_x = int((left_x2 + right_x2) / 2)
        print('turn around')  # this eventually needs to include a motor command

    elif len(right_line) > 0 and len(left_line) > 0:
        left_x2 = left_line[2]
        right_x2 = right_line[0]
        nav_point_x = int((left_x2 + right_x2) / 2)
        if nav_point_x > int(1.1 * mid):
            print('turn right')  # this eventually needs to include a motor command
        elif nav_point_x < int(.9 * mid):
            print('turn left')  # this eventually needs to include a motor command
        else:
            print("drive straight")  # this eventually needs to include a motor command
    elif len(right_line) > 0:
        right_x2 = right_line[0]
        right_x1 = right_line[2]
        nav_point_x = int(mid + right_x2 - right_x1)
        print('turn left')  # this eventually needs to include a motor command
    elif len(left_line) > 0:
        left_x2 = left_line[2]
        left_x1 = left_line[0]
        nav_point_x = int(mid + left_x2 - left_x1)
        print('turn right')  # this eventually needs to include a motor command

    cv2.line(lane_image, (mid, height), (nav_point_x, int(height/2)), [0, 255, 255], 10)
    return lane_image

def intersection_ROI(frame):
    # Define Region of Interest (ROI) for the intersection

    rows, cols = frame.shape[:2]
    bottom_left = [cols * 0.0, rows * 1]
    top_left = [cols * 0.0, rows * 0.0]
    bottom_right = [cols * 1, rows * 1]
    top_right = [cols * 1, rows * 0]
    intersection_vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
    return intersection_vertices


def process_intersection(frame, intersection_vertices):
    # filter the region of interest (ROI) for the intersection

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
    lower_purple = np.array([140, 125, 60], dtype=int)
    upper_purple = np.array([170, 255, 240], dtype=int)
    mask_purple = cv2.inRange(processed_hsv, lower_purple, upper_purple)
    processed = cv2.bitwise_and(gray, mask_purple)

    # smoothing
    kernel_size = 3

    processed = cv2.GaussianBlur(processed, (kernel_size, kernel_size), 0)

    # detect edges in the image
    low_threshold = 50
    high_threshold = 150

    intersection_edges = cv2.Canny(processed, low_threshold, high_threshold)
    cv2.namedWindow('intedge', cv2.WINDOW_AUTOSIZE)  # create a window
    cv2.imshow('intedge', intersection_edges)  # show the image in that window

    return intersection_edges


def create_intersection(intersection_edges, frame):
    global intersection_state
    global state1
    global int_on
    # Hough Lines for intersection

    lines = cv2.HoughLinesP(intersection_edges, rho=1, theta=np.pi / 360, threshold=30, minLineLength=30, maxLineGap=70)
    line_image = np.zeros_like(frame)

    # Create Main Lines by averaging all detected hough lines for intersection
    left_fit = []
    right_fit = []
    horizontal_fit = []
    bottom_fit = []
    top_fit = []
    y1list = []
    slope = []
    if lines is not None:
        int_on = 1
        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            # Fit first order function
            # params = np.polyfit((x1, y1), (x2, y2), 1)
            if x2 == x1:
                pass
            else:
                slope = (y2 - y1) / (x2 - x1)

            if slope < -1 / 2:
                left_fit.append((x1, y1, x2, y2))
                cv2.line(line_image, (x1, y1), (x2, y2), (255, 255, 0), 2)

            elif slope > 1 / 2:
                right_fit.append((x1, y1, x2, y2))
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 255), 2)

            else:
                horizontal_fit.append((x1, y1, x2, y2))
                y1list.append(y1)
                cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
    else:
        pass

    if len(y1list) > 0:
        y1_avg = np.average(y1list)

        for [x1, y1, x2, y2] in horizontal_fit:
            if y1 < 1.1 * y1_avg:
                top_fit.append((x1, y1, x2, y2))
                cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 255), 2)
            else:
                bottom_fit.append((x1, y1, x2, y2))
                cv2.line(line_image, (x1, y1), (x2, y2), (100, 100, 100), 2)

    cv2.namedWindow('intlines', cv2.WINDOW_AUTOSIZE)  # create a window
    cv2.imshow('intlines', line_image)  # show the image in that window

    left_int, right_int, bottom_int, top_int = [], [], [], []

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

    if len(bottom_fit) > 0:
        bottom_fit_avg = np.average(bottom_fit, axis=0)
        x1 = int(bottom_fit_avg[0])
        y1 = int(bottom_fit_avg[1])
        x2 = int(bottom_fit_avg[2])
        y2 = int(bottom_fit_avg[3])
        bottom_int = [x1, y1, x2, y2]
    bottom_int = np.array(bottom_int)

    if len(top_fit) > 0:
        top_fit_avg = np.average(top_fit, axis=0)
        x1 = int(top_fit_avg[0])
        y1 = int(top_fit_avg[1])
        x2 = int(top_fit_avg[2])
        y2 = int(top_fit_avg[3])
        top_int = [x1, y1, x2, y2]
    top_int = np.array(top_int)

    if lines is not None:
        if state1 == 2:
            if len(bottom_int) > 0 and bottom_int[1] > 360:
                intersection_state = 2
            if len(right_int) > 0 and right_int[3] > 360:
                intersection_state = 2
            if len(left_int) > 0 and left_int[1] > 360:
                intersection_state = 2
        elif len(left_int) > 0 and 300 < left_int[1] < 400:
                state1 = 1
        elif len(bottom_int) > 0 and 300 < bottom_int[1] < 400:
                state1 = 1
        elif len(right_int) > 0 and 300 < right_int[1] < 400:
                state1 = 1
        else:
            state1 = 0

    # draw intersection lines
    thickness = 10

    intersection_image = np.zeros_like(frame)

    if len(left_int) > 0:
        x1, y1, x2, y2 = left_int.reshape(4)
        cv2.line(intersection_image, (x1, y1), (x2, y2), [255, 0, 0], thickness)
    if len(right_int) > 0:
        x1, y1, x2, y2 = right_int.reshape(4)
        cv2.line(intersection_image, (x1, y1), (x2, y2), [0, 255, 0], thickness)
    if len(top_int) > 0:
        x1, y1, x2, y2 = top_int.reshape(4)
        cv2.line(intersection_image, (x1, y1), (x2, y2), [0, 0, 255], thickness)
    if len(bottom_int) > 0:
        x1, y1, x2, y2 = bottom_int.reshape(4)
        cv2.line(intersection_image, (x1, y1), (x2, y2), [255, 255, 0], thickness)

    print(bottom_int)
    print(left_int)
    print(right_int)
    print(top_int)
    return slope, left_int, right_int, top_int, bottom_int


def guidance_decision(left_int, right_int, top_int):
    global turn

    turn_left = 0
    priority = turn_left

    if len(left_int) > 0 and priority == 0:
        turn = "left"
    elif len(top_int) > 0:
        turn = "straight"
    elif len(right_int) > 0:
        turn = "right"
    else:
        turn = "Backwards"

    print('guidance decision is:', turn)

    intersection_state = 1

    return intersection_state


def main():
    global state1
    global intersection_state
    global int_on

    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.rotation = 180
    camera.framerate = 2
    rawCapture = PiRGBArray(camera, size=(640, 480))

    # allow the camera to warmup
    time.sleep(0.1)

    # capture frames from the camera
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

        # convert to numpy array for use by cv2
        frame = f.array

        lane_vertices = lane_roi(frame)
        lane_edges = process_lanes(frame, lane_vertices)
        right_line, left_line, center_line = create_lanes(lane_edges, frame)
        intersection_vertices = intersection_ROI(frame)
        intersection_edges = process_intersection(frame, intersection_vertices)
        slope, left_int, right_int, top_int, bottom_int = create_intersection(intersection_edges, frame)
        lane_image = draw_lanes(frame, right_line, left_line, center_line, left_int, right_int, bottom_int, top_int)
        if state1 == 1:
            guidance_decision(left_int, right_int, top_int)
            navigation(frame, center_line, right_line, left_line, lane_image)
            state1 = 2
        elif intersection_state == 1:
            navigation(frame, center_line, right_line, left_line, lane_image)
        elif intersection_state == 2:
            # execute decision and reset state
            print("Go", turn)
            state1 = 0
            intersection_state = 1
            int_on = 0
        show_test(lane_image)
        # Delay for key press to quit and frame rate (1 ms)
        key_pressed = cv2.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break

        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)

    # cleanup
    cv2.destroyAllWindows()


main()

cv2.waitKey()  # turn it off when I key stroke within
