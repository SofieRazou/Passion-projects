import cv2
import numpy as np
from sklearn.linear_model import RANSACRegressor

# ------------------- Color & Gradient Mask -------------------
def color_and_gradient_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_white = cv2.inRange(hsv, (0,0,200), (180,30,255))
    mask_yellow = cv2.inRange(hsv, (15,100,100), (35,255,255))
    color_mask = cv2.bitwise_or(mask_white, mask_yellow)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(sobelx**2 + sobely**2)
    scaled = np.uint8(255*grad_mag/np.max(grad_mag))
    grad_mask = cv2.inRange(scaled, 30, 255)

    combined = cv2.bitwise_or(color_mask, grad_mask)
    return combined

# ------------------- Perspective Transform -------------------
def perspective_transform(img):
    h, w = img.shape[:2]
    src = np.float32([[w*0.45,h*0.6],[w*0.55,h*0.6],[w*0.95,h],[w*0.05,h]])
    dst = np.float32([[w*0.2,0],[w*0.8,0],[w*0.8,h],[w*0.2,h]])
    M = cv2.getPerspectiveTransform(src,dst)
    Minv = cv2.getPerspectiveTransform(dst,src)
    warped = cv2.warpPerspective(img,M,(w,h),flags=cv2.INTER_LINEAR)
    return warped, Minv

# ------------------- Sliding Window Search -------------------
def sliding_window_polyfit(binary_warped, degree=3):
    h, w = binary_warped.shape
    histogram = np.sum(binary_warped[h//2:,:], axis=0)
    midpoint = w//2
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint

    nwindows = 9
    window_height = h//nwindows
    margin = 100
    minpix = 50

    nonzero = binary_warped.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])

    leftx_current = leftx_base
    rightx_current = rightx_base

    left_inds, right_inds = [], []

    for window in range(nwindows):
        win_y_low = h - (window+1)*window_height
        win_y_high = h - window*window_height
        win_xleft_low = leftx_current - margin
        win_xleft_high = leftx_current + margin
        win_xright_low = rightx_current - margin
        win_xright_high = rightx_current + margin

        good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                          (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
        good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                           (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]

        left_inds.append(good_left_inds)
        right_inds.append(good_right_inds)

        if len(good_left_inds) > minpix:
            leftx_current = int(np.mean(nonzerox[good_left_inds]))
        if len(good_right_inds) > minpix:
            rightx_current = int(np.mean(nonzerox[good_right_inds]))

    left_inds = np.concatenate(left_inds)
    right_inds = np.concatenate(right_inds)

    leftx, lefty = nonzerox[left_inds], nonzeroy[left_inds]
    rightx, righty = nonzerox[right_inds], nonzeroy[right_inds]

    left_fit = None
    right_fit = None

    # RANSAC + weighted polyfit
    if len(leftx) > 0:
        X = lefty.reshape(-1,1)
        ransac = RANSACRegressor()
        ransac.fit(X, leftx)
        left_fit = np.polyfit(X.flatten(), ransac.predict(X), degree)
    if len(rightx) > 0:
        X = righty.reshape(-1,1)
        ransac = RANSACRegressor()
        ransac.fit(X, rightx)
        right_fit = np.polyfit(X.flatten(), ransac.predict(X), degree)

    return left_fit, right_fit

class KalmanPoly:
    """Kalman filter for cubic polynomial coefficients with velocity"""
    def __init__(self, process_noise=1e-3, measurement_noise=1e-2):
        self.state = None  # [a,b,c,d, da,db,dc,dd] for cubic
        self.P = None
        self.Q = np.eye(8) * process_noise
        self.R = np.eye(4) * measurement_noise

    def update(self, measurement):
        if measurement is None:
            return self.state[:4] if self.state is not None else None
        z = np.array(measurement)
        if self.state is None:
            self.state = np.hstack([z, [0,0,0,0]])  # initial velocity zero
            self.P = np.eye(8)
            return z
        # Predict
        x_pred = self.state.copy()
        x_pred[:4] += x_pred[4:]  # position + velocity
        P_pred = self.P + self.Q
        # Update (measurement only for coefficients)
        K = P_pred[:4,:4] @ np.linalg.inv(P_pred[:4,:4] + self.R)
        self.state[:4] = x_pred[:4] + K @ (z - x_pred[:4])
        self.state[4:] = x_pred[4:]  # keep velocity unchanged
        self.P = P_pred
        return self.state[:4]


# ------------------- Draw Lane -------------------
def draw_lane(original, left_fit, right_fit, Minv):
    h, w = original.shape[:2]
    ploty = np.linspace(0, h-1, h)
    color_warp = np.zeros_like(original)

    left_fitx = left_fit[0]*ploty**3 + left_fit[1]*ploty**2 + left_fit[2]*ploty + left_fit[3] if left_fit is not None else ploty*0
    right_fitx = right_fit[0]*ploty**3 + right_fit[1]*ploty**2 + right_fit[2]*ploty + right_fit[3] if right_fit is not None else ploty*0 + w-1

    pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
    pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])
    pts = np.hstack((pts_left, pts_right))
    cv2.fillPoly(color_warp, np.int_([pts]), (0,255,0))

    # Draw lane lines
    cv2.polylines(color_warp, np.int_([pts_left[0]]), False, (0,0,255), 5)
    cv2.polylines(color_warp, np.int_([pts_right[0]]), False, (255,0,0), 5)

    newwarp = cv2.warpPerspective(color_warp, Minv, (w,h))
    return cv2.addWeighted(original, 1, newwarp, 0.7, 0)

# ------------------- Main -------------------
cap = cv2.VideoCapture("/Users/sofia/Desktop/computer_vision/turn_video_new.mp4")
kalman_left = KalmanPoly()
kalman_right = KalmanPoly()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    mask = color_and_gradient_mask(frame)
    warped, Minv = perspective_transform(mask)
    left_fit, right_fit = sliding_window_polyfit(warped)

    # Kalman smoothing
    left_fit = kalman_left.update(left_fit)
    right_fit = kalman_right.update(right_fit)

    lane_img = draw_lane(frame, left_fit, right_fit, Minv)
    cv2.imshow("Curved Lane Detection + Kalman", lane_img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
