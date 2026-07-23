import struct

packet = struct.pack(
    "<ddd",
    angle,
    torque,
    timestamp
)

sock.sendto(packet, ("127.0.0.1", 50000))
