import socket
import struct
import time

DESTINATION_IP = "127.0.0.1"   # GUI on the same computer
DESTINATION_PORT = 50000
SEND_PERIOD = 0.01             # 100 Hz

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

variables = plat.ActiveVariableDescription.Variables

# Locate the three variables once, before starting transmission.
wanted_names = ("AO_ch8", "AO_ch16", "Torque")
wanted_vars = {}

for i in range(variables.Count):
    var = variables.Item(i)

    if var.Name in wanted_names:
        wanted_vars[var.Name] = var

print("Found variables:", list(wanted_vars.keys()))

missing = [name for name in wanted_names if name not in wanted_vars]

if missing:
    raise RuntimeError("Missing variables: " + ", ".join(missing))

sequence = 0

while True:
    try:
        ao_ch8 = float(wanted_vars["AO_ch8"].ValueConverted)
        ao_ch16 = float(wanted_vars["AO_ch16"].ValueConverted)
        torque = float(wanted_vars["Torque"].ValueConverted)

        # Packet:
        # uint32 sequence number
        # float32 AO_ch8
        # float32 AO_ch16
        # float32 Torque
        packet = struct.pack(
            "<Ifff",
            sequence,
            ao_ch8,
            ao_ch16,
            torque
        )

        sock.sendto(packet, (DESTINATION_IP, DESTINATION_PORT))

        sequence = (sequence + 1) & 0xFFFFFFFF
        time.sleep(SEND_PERIOD)

    except KeyboardInterrupt:
        print("UDP transmission stopped.")
        break

    except Exception as error:
        print("Transmission error:", error)
        time.sleep(0.1)

sock.close()
