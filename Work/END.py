class UdpSender:
    """UDP sender for forwarding signals."""

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

    def send_angle(self, angle: float) -> None:
        packet = {
            "angle": angle
        }

        data = json.dumps(packet).encode("utf-8")

        self.socket.sendto(
            data,
            (self.ip, self.port),
        )

    def close(self) -> None:
        self.socket.close()


# IN THE MAIN WINDOW INIT 
self.angle_sender = UdpSender(
    ANGLE_FORWARD_IP,
    ANGLE_FORWARD_PORT,
)
