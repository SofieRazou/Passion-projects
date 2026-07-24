# # import socket
# # import time

# # UDP_IP = "127.0.0.1"      # Same PC
# # UDP_PORT = 50000

# # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# # counter = 0

# # while counter<10:
# #     try:
# #         message = f"HELLO FROM DSPACE {counter}"

# #         sock.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))

# #         print("Sent:", message)

# #         counter += 1
# #         for i in range(len(dir(plat.ActiveVariableDescription.Variables))):
# #                 var = plat.ActiveVariableDescription.Variables.Item(i)
# #                 vars.append({var.Name, var.ValueConverted})
# #                 if ((var.Name == 'AO_ch8') or (var.Name== 'AO_ch16') or (var.Name=='Torque')):
# #                     my_vars.append({var.Name, var.ValueConverted})   
# #                     print(f"Value of {var.Name} is {var.ValueConverted}")
# #         time.sleep(1)

# #     except KeyboardInterrupt:
# #         print("Exciting with Ctrl+C...")



# # vars = []
# # my_vars = []


# import socket
# import time
# import json

# UDP_IP = "127.0.0.1"
# UDP_PORT = 50000

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# interesting = ["AO_ch8", "AO_ch16", "Torque"]

# try:
#     while True:

#         values = {}

#         # Iterate through all dSPACE variables
#         for i in range(plat.ActiveVariableDescription.Variables.Count):

#             var = plat.ActiveVariableDescription.Variables.Item(i)

#             if var.Name in interesting:
#                 values[var.Name] = var.ValueConverted

#         # Convert to JSON
#         packet = json.dumps(values)

#         # Send
#         sock.sendto(packet.encode("utf-8"), (UDP_IP, UDP_PORT))

#         print(packet)

#         time.sleep(0.01)      # 100 Hz

# except KeyboardInterrupt:
#     print("Stopped.")

# finally:
#     sock.close()
# # all dSpace model variables ['finalTime', 'currentTime', 'modelStepSize', 'simState', 'errorNumber', 'sumOfResetTime', 'Active ErrorSet', 'Error Activated', 'Error Switching', 'Flags', 'Trigger', 'AO_ch8', 'AO_ch16', 'Torque', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'UpperLimit', 'LowerLimit', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Gain', 'Out1', 'Gain', 'Out1', 'Gain', 'Out1', 'Gain', 'Out1', 'Gain', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'AnalogInput_ch1', 'AnalogInput_ch2', 'ADC', 'ADC', 'Out1', 'Gain', 'Out1', 'Gain', 'Position', 'Speed', 'Index Detected']
import socket
import time
import json

UDP_IP = "127.0.0.1"
UDP_PORT = 50000

SAMPLE_TIME = 0.01       # 100 Hz
MAX_RUNTIME = 30.0      # Automatically stop after 0.5 minutes

TARGET_VARIABLES = (
    "AO_ch8",
    "AO_ch16",
    "Torque",
)
found_angle = False
plat = Application.ActiveExperiment.Platforms.Item(0)
print(f"Running experiment on platform: {plat.Name}")


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

running = True
variable_handles = {}


def find_target_variables():
    """Find the required dSPACE variables once."""

    found = {}
    variables = plat.ActiveVariableDescription.Variables

    # Use Count when supported by the dSPACE collection
    try:
        variable_count = variables.Count
    except Exception:
        variable_count = len(dir(variables))

    for i in range(variable_count):
        try:
            var = variables.Item(i)
            angle = variables.Item(65)
            found[angle.Name] = angle
            if var.Name in TARGET_VARIABLES:
                    found[var.Name] = var
                    
        except Exception:
            continue

    return found


try:
    variable_handles = find_target_variables()

    print("Found variables:", list(variable_handles.keys()))

    missing_variables = [
        name
        for name in TARGET_VARIABLES
        if name not in variable_handles
    ]

    if missing_variables:
        print("Missing variables:", missing_variables)

    print("UDP sender started.")
    print("Press Ctrl+C to stop.")
    print("Maximum runtime:", MAX_RUNTIME, "seconds")

    start_time = time.time()
    packet_counter = 0

    while running:

        current_time = time.time()
        elapsed_time = current_time - start_time

        # Fallback termination condition
        if elapsed_time >= MAX_RUNTIME:
            print("Maximum runtime reached.")
            break

        values = {
            "packet": packet_counter,
            "timestamp": current_time,
            "elapsed_time": elapsed_time,
        }

        for variable_name in TARGET_VARIABLES:

            variable_handle = variable_handles.get(variable_name)

            if variable_handle is None:
                values[variable_name] = None
                continue

            try:
                values[variable_name] = variable_handle.ValueConverted

            except Exception as error:
                values[variable_name] = None
                print(
                    "Could not read {}: {}".format(
                        variable_name,
                        error
                    )
                )

        packet = json.dumps(values)

        sock.sendto(
            packet.encode("utf-8"),
            (UDP_IP, UDP_PORT)
        )

        # Do not print every packet at 100 Hz
        if packet_counter % 100 == 0:
            print("Sent:", packet)

        packet_counter += 1

        time.sleep(SAMPLE_TIME)

except KeyboardInterrupt:
    print("\nCtrl+C detected. Stopping sender.")

except Exception as error:
    print("Sender error:", error)

finally:
    running = False
    sock.close()

    print("UDP socket closed.")
    print("Packets sent:", packet_counter)
    print("Sender terminated cleanly.")
