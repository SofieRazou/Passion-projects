import subprocess

# Start your external Python script
subprocess.Popen(["python", "C:\\MyProject\\steering_controller.py"])

# Start another script
subprocess.Popen(["python", "C:\\MyProject\\data_logger.py"])
