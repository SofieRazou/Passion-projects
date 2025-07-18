import cv2 as cv
import numpy as np
import serial
import time

# --- Serial Setup ---
BAUDRATE  = 9600
PORT = '/dev/cu.usbmodem11301'
TIMEOUT = 0.1

arduino = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=TIMEOUT)
time.sleep(2)
arduino.flush()

# --- Video Setup ---
cap = cv.VideoCapture("moonrec.mp4")

# --- Moon Phase Counters ---
full, crescent, gibbous, new = 0, 0, 0, 0
prev_state = None  # Track previous state to avoid resending same command

while True:
    isTrue, frame = cap.read()
    if not isTrue:
        break

    # --- Preprocessing ---
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (9, 9), 2)

    # --- Circle Detection (Moon) ---
    circles = cv.HoughCircles(
        gray, cv.HOUGH_GRADIENT, dp=1.2, minDist=100,
        param1=100, param2=30, minRadius=50, maxRadius=200
    )

    if circles is not None:
        if prev_state != "found":
            arduino.write(b"found\n")
            arduino.flush()
            prev_state = "found"

        circles = np.uint16(np.around(circles))
        for (x, y, r) in circles[0, :]:
            mask = np.zeros_like(gray)
            cv.circle(mask, (x, y), r, 255, thickness=-1)

            moon_region = cv.bitwise_and(gray, gray, mask=mask)
            _, thresh = cv.threshold(moon_region, 100, 255, cv.THRESH_BINARY)

            illuminated_area = cv.countNonZero(thresh)
            total_area = cv.countNonZero(mask)
            ratio = illuminated_area / total_area if total_area != 0 else 0

            if ratio > 0.9:
                phase = "Full moon"
                full += 1
            elif ratio < 0.1:
                phase = "New moon"
                new += 1
            elif ratio > 0.5:
                phase = "Gibbous"
                gibbous += 1
            else:
                phase = "Crescent"
                crescent += 1

            # Show Detection
            cv.circle(frame, (x, y), r, (0, 0, 255), 4)
            cv.putText(frame, phase, (x - 40, y - r - 10), cv.FONT_ITALIC, 0.7, (0, 0, 255), 2)
            print(f"Illuminated ratio: {ratio:.2f} => {phase}")
    else:
        if prev_state != "not found":
            arduino.write(b"not found\n")
            arduino.flush()
            prev_state = "not found"

    cv.imshow('DAMOON', frame)

    if cv.waitKey(30) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv.destroyAllWindows()

phases = {
    "Full moon": full,
    "New moon": new,
    "Gibbous": gibbous,
    "Crescent": crescent
}
print("Most common detected phase:", max(phases, key=phases.get))
