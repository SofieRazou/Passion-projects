import csv
import time
import os

OUTPUT_FILE = r"C:\dspace_live\capt_live.csv"
SAMPLE_PERIOD = 0.02  # 50 Hz

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

file_exists = os.path.exists(OUTPUT_FILE)

with open(OUTPUT_FILE, "a", newline="", buffering=1) as csv_file:
    writer = csv.writer(csv_file)

    if not file_exists:
        writer.writerow([
            "pc_time",
            "angle_rad",
            "torque_nm",
            "current_a",
            "current_b",
            "current_c"
        ])
        csv_file.flush()

    while True:
        # Replace these expressions with the actual ControlDesk
        # variable-access expressions.
        angle = angle_variable.Value
        torque = torque_variable.Value
        current_a = current_a_variable.Value
        current_b = current_b_variable.Value
        current_c = current_c_variable.Value

        writer.writerow([
            time.time(),
            angle,
            torque,
            current_a,
            current_b,
            current_c
        ])

        # Make the row visible to your external Python process immediately.
        csv_file.flush()

        time.sleep(SAMPLE_PERIOD)
      
