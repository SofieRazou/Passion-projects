import cv2
import numpy as np

# ------------------- Helpers -------------------
def color_mask(image):
    """Highlight lane colors (yellow & white)"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask_white = cv2.inRange(hsv, (0, 0, 180), (180, 25, 255))
    mask_yellow = cv2.inRange(hsv, (15, 100, 100), (35, 255, 255))
    mask = cv2.bitwise_or(mask_white, mask_yellow)
    return cv2.bitwise_and(image, image, mask=mask)

def roi(image):
    h, w = image.shape[:2]
    polygon = np.array([[
        (0, h),
        (w, h),
        (w, int(h*0.5)),
        (0, int(h*0.5))
    ]], np.int32)
    mask = np.zeros_like(image[:,:,0])
    cv2.fillPoly(mask, polygon, 255)
    return cv2.bitwise_and(image[:,:,0], mask, mask=mask)

def canny(image):
    blur = cv2.GaussianBlur(image, (5,5), 0)
    return cv2.Canny(blur, 50, 150)

def cluster_lines(lines, w):
    """Split Hough points into left/right clusters based on x-coordinate"""
    left_pts, right_pts = [], []
    if lines is None: return left_pts, right_pts
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        if (x1+x2)/2 < w/2:
            left_pts.append((x1,y1))
            left_pts.append((x2,y2))
        else:
            right_pts.append((x1,y1))
            right_pts.append((x2,y2))
    return left_pts, right_pts

def fit_curve(points, degree=2):
    """Fit a smooth polynomial curve"""
    if len(points) < 3:
        return None
    pts = np.array(points)
    pts = pts[pts[:,1].argsort()]  # sort by y
    ys, xs = pts[:,1], pts[:,0]
    coeffs = np.polyfit(ys, xs, degree)
    return coeffs

def draw_curve(img, coeffs, y_min, y_max, color=(0,255,0), thickness=4):
    if coeffs is None: return
    ys = np.linspace(y_min, y_max, y_max - y_min)
    xs = np.polyval(coeffs, ys)
    for i in range(len(ys)-1):
        cv2.line(img, (int(xs[i]), int(ys[i])), (int(xs[i+1]), int(ys[i+1])), color, thickness)

# ------------------- Main -------------------
cap = cv2.VideoCapture("/Users/sofia/Desktop/computer_vision/test4.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    mask = color_mask(frame)
    roi_img = roi(mask)
    edges = canny(roi_img)

    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=20, minLineLength=20, maxLineGap=10)
    h, w = frame.shape[:2]
    left_pts, right_pts = cluster_lines(lines, w)

    left_coeffs = fit_curve(left_pts, degree=2)
    right_coeffs = fit_curve(right_pts, degree=2)

    y_min, y_max = int(h*0.5), h
    draw_curve(frame, left_coeffs, y_min, y_max, (0,0,255))
    draw_curve(frame, right_coeffs, y_min, y_max, (0,255,0))

    cv2.imshow("Lane Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
