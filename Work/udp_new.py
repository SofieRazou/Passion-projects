import socket
import struct
import time

# Network Configuration
UDP_IP = "134.105.60.99"
UDP_PORT = 55001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

VAR_PATH = r'Platform()://Model Root/Subsystem2/Ch16/Out1'

try:
    active_platforms = Application.ActiveExperiment.Platforms

    if len(active_platforms) == 0:
        raise RuntimeError("No active platform found. Ensure your experiment is open.")

    my_platform = active_platforms[0]

    print(f"Connected to Platform: {my_platform.Name}")
    print(f"Looking for: {VAR_PATH}")

    # --------------------------------------------------
    # Inspect VariableDescriptions
    # --------------------------------------------------

    vds = my_platform.VariableDescriptions

    print("\nVariableDescriptions object:")
    print(type(vds))

    print("\nMethods:")
    print(dir(vds))

    print("\nNumber of variables:", vds.Count)

    print("\nPrinting first 10 variable descriptions...")

    for i in range(min(vds.Count, 10)):
        try:
            print("\n--------------------------------")
            print("Index:", i)

            var = vds.Item(i)

            print("Object:", var)
            print("Type:", type(var))
            print("Members:")
            print(dir(var))

        except Exception as e:
            print("Could not access item", i)
            print(e)

    # --------------------------------------------------
    # Try accessing your variable directly
    # --------------------------------------------------

    print("\nChecking if variable exists...")

    try:
        print("Contains:", vds.Contains(VAR_PATH))

        var = vds.Item(VAR_PATH)

        print("\nVariable found!")
        print(var)
        print(type(var))

        print("\nVariable members:")
        print(dir(var))

    except Exception as e:
        print("Could not access variable using path.")
        print(e)

except Exception:
    import traceback
    print("\n--- SCRIPT EXCEPTION ENCOUNTERED ---")
    print(traceback.format_exc())
