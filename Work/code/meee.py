def poll_moza_wheel(self) -> None:
    """Poll the Moza wheel once (called by QTimer)."""

    if self.wheel is None:
        return

    max_wheel_degs = 900.0

    try:
        pygame.event.pump()

        raw_axis = self.wheel.get_axis(0)

        # Steering angle
        self.latest_angle_moza = raw_axis * (max_wheel_degs / 2.0)

        # Simulated torque (replace with real value if available)
        self.latest_torque_moza = abs(raw_axis) * MOZA_R5_MAX_TORQUE

        # Send steering angle
        payload = struct.pack("<d", self.latest_angle_moza)
        self.moza_sock.sendto(payload, (CONTROL_IP, CONTROL_PORT))

    except Exception as error:
        print(f"Moza polling error: {error}")
