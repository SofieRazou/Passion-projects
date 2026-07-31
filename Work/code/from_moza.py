import socket
import struct
import time
import pygame

CONTROL_IP = "134.105.60.99"
CONTROL_PORT = 55001

moza_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
pygame.joystick.init()


if pygame.joystick.get_count() == 0:
    print("Moza R5 is not detected. Please try again")
    exit()

wheel = pygame.joystick.Joystick(0)
wheel.init()

print(f"Connected successfully to: {wheel.get_name()}")
print(f"Streaming real-time steering angle data over address: {CONTROL_IP} from port: {CONTROL_PORT}")


max_wheel_degs = 900.0
clock = pygame.time.Clock()
try:
    while True:
        pygame.event.pump()
        raw_axis = wheel.get_axis(0)

        angle_degrees = raw_axis*(max_wheel_degs/2.0)

        payload = struct.pack('<d', float(angle_degrees))
        moza_sock.sendto(payload, (CONTROL_IP, CONTROL_PORT))

        print(f"\rWheel Axis: {raw_axis:6.3f} | Angle: {angle_degrees:6.2f}", end = "")
        clock.tick_busy_loop(100) #update frequency for verbosin 

except KeyboardInterrupt:
    print("\n Stream got interrupted by the user")

finally:
    moza_sock.close()
    pygame.quit()