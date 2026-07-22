import socket
import time

UDP_IP = "127.0.0.1"      # Same PC
UDP_PORT = 50000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

counter = 0

while counter<10:
    try:
        message = f"HELLO FROM DSPACE {counter}"

        sock.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))

        print("Sent:", message)

        counter += 1
        for i in range(len(dir(plat.ActiveVariableDescription.Variables))):
                var = plat.ActiveVariableDescription.Variables.Item(i)
                vars.append({var.Name, var.ValueConverted})
                if ((var.Name == 'AO_ch8') or (var.Name== 'AO_ch16') or (var.Name=='Torque')):
                    my_vars.append({var.Name, var.ValueConverted})   
                    print(f"Value of {var.Name} is {var.ValueConverted}")
        time.sleep(1)

    except KeyboardInterrupt:
        print("Exciting with Ctrl+C...")



vars = []
my_vars = []
       
# all dSpace model variables ['finalTime', 'currentTime', 'modelStepSize', 'simState', 'errorNumber', 'sumOfResetTime', 'Active ErrorSet', 'Error Activated', 'Error Switching', 'Flags', 'Trigger', 'AO_ch8', 'AO_ch16', 'Torque', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'UpperLimit', 'LowerLimit', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Out1', 'Gain', 'Out1', 'Gain', 'Out1', 'Gain', 'Out1', 'Gain', 'Out1', 'Gain', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'Value', 'AnalogInput_ch1', 'AnalogInput_ch2', 'ADC', 'ADC', 'Out1', 'Gain', 'Out1', 'Gain', 'Position', 'Speed', 'Index Detected']
