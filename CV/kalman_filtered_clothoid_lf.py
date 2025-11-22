import cv2
import numpy as np
from pyclothoids import Clothoid
import math

# ------------------ Kalman Filter Class ------------------
class LaneKalman:
    def __init__(self):
        self.kf = cv2.KalmanFilter(4, 4, 0, cv2.CV_32F)
        # State: [k0, dk, theta0, y_offset]
        self.kf.transitionMatrix = np.array([[1, 1, 0, 0],
                                             [0, 1, 0, 0],
                                             [0, 0, 1, 1],
                                             [0, 0, 0, 1]], np.float32)
        self.kf.measurementMatrix = np.eye(4, dtype=np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1e-4
        self.kf.measurementNoiseCov = np.eye(4, dtype=np.float32) * 1e-2
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
        self.kf.statePost = np.zeros((4, 1), np.float32)

    def predict(self):
        return self.kf.predict()

    def correct(self, k0, dk, theta0, y_offset):
        measurement = np.array([[np.float32(k0)],
                                [np.float32(dk)],
                                [np.float32(theta0)],
                                [np.float32(y_offset)]])
        return self.kf.correct(measurement)

# ------------------ Lane Detection Helpers ------------------
def make_coordinates(image, line_parameters):
    slope, intercept = line_parameters
    y1 = image.shape[0]
    y2 = int(y1 * 3/5)
    slope = slope if slope != 0 else 0.001
    x1 = int((y1 - intercept) / slope)
    x2 = int((y2 - intercept) / slope)
    return np.array([x1, y1, x2, y2], dtype=int)

def average_slope_intercept(image, lines):
    if lines is None:
        return None, None
    left_fit, right_fit = [], []
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        if x2 - x1 == 0: continue
        slope, intercept = np.polyfit((x1, x2), (y1, y2), 1)
        if abs(slope) < 0.3: continue
        if slope < 0: left_fit.append((slope, intercept))
        else: right_fit.append((slope, intercept))
    left_line = make_coordinates(image, np.mean(left_fit, axis=0)) if left_fit else None
    right_line = make_coordinates(image, np.mean(right_fit, axis=0)) if right_fit else None
    return left_line, right_line

def canny(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    return cv2.Canny(blur, 50, 150)

def region_of_interest(image):
    height, width = image.shape[:2]
    polygons = np.array([[(int(width*0.1), height),
                          (int(width*0.9), height),
                          (int(width*0.55), int(height*0.6))]])
    mask = np.zeros_like(image)
    cv2.fillPoly(mask, polygons, 255)
    return cv2.bitwise_and(image, mask)

def display_lines(image, lines):
    line_image = np.zeros_like(image)
    for line in lines:
        if line is not None:
            x1, y1, x2, y2 = line
            cv2.line(line_image, (x1, y1), (x2, y2), (255,0,0), 10)
    return line_image

# ------------------ Clothoid Helper ------------------
def compute_curvature(line):
    # Simple approximation from slope
    if line is None: return 0.0, 0.0, 0.0
    x1, y1, x2, y2 = line
    slope = (y2 - y1) / (x2 - x1 + 1e-6)
    theta0 = math.atan(slope)
    k0 = slope / 1000  # approximate curvature
    dk = k0 / 50        # approximate curvature change
    return k0, dk, theta0

def draw_clothoid(image, k0, dk, theta0, X0, Y0, length=200):
    cl = Clothoid.Forward(X0, Y0, theta0, k0, X0 + length, Y0)
    s_array = np.linspace(0, cl.length, 50)
    pts = np.array([[int(cl.X(s)), int(cl.Y(s))] for s in s_array])
    for i in range(len(pts)-1):
        cv2.line(image, tuple(pts[i]), tuple(pts[i+1]), (0,255,0), 4)

# ------------------ Main Video Pipeline ------------------
cap = cv2.VideoCapture("/Users/sofia/Desktop/computer_vision/turn_video_new.mp4")

# Separate Kalman filters for left and right lanes
left_kalman = LaneKalman()
right_kalman = LaneKalman()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    canny_image = canny(frame)
    cropped_image = region_of_interest(canny_image)
    lines = cv2.HoughLinesP(cropped_image, 2, np.pi/180, 50, minLineLength=20, maxLineGap=10)
    left_line, right_line = average_slope_intercept(frame, lines)

    # Compute curvature and tangent for both lanes
    k0_left, dk_left, theta_left = compute_curvature(left_line)
    k0_right, dk_right, theta_right = compute_curvature(right_line)
    y_offset = frame.shape[0] // 2

    # Kalman filter prediction & correction
    left_kalman.predict()
    corrected_left = left_kalman.correct(k0_left, dk_left, theta_left, y_offset)
    k0_left_corr, dk_left_corr, theta_left_corr, y_left_corr = corrected_left.flatten()

    right_kalman.predict()
    corrected_right = right_kalman.correct(k0_right, dk_right, theta_right, y_offset)
    k0_right_corr, dk_right_corr, theta_right_corr, y_right_corr = corrected_right.flatten()

    # Draw clothoids
    if left_line is not None:
        draw_clothoid(frame, k0_left_corr, dk_left_corr, theta_left_corr, left_line[0], y_left_corr)
    if right_line is not None:
        draw_clothoid(frame, k0_right_corr, dk_right_corr, theta_right_corr, right_line[0], y_right_corr)

    # Draw Hough lines for reference
    line_image = display_lines(frame, [left_line, right_line])
    combined = cv2.addWeighted(frame, 0.8, line_image, 1, 1)

    cv2.imshow("Lane Detection with Clothoids", combined)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
