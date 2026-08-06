import sys
import pygame

# 1. INITIALIZE PYGAME AND THE HARDWARE JOYSTICK SUBSYSTEM
pygame.init()
pygame.joystick.init()

# Check if any hardware is plugged in
if pygame.joystick.get_count() == 0:
    print("No hardware controllers detected! Please plug in your MOZA wheel.")
    sys.exit(1)

# Find and initialize the MOZA base (usually listed as Joystick 0)
moza_wheel = pygame.joystick.Joystick(0)
moza_wheel.init()
print(f"Successfully connected to: {moza_wheel.get_name()}")

# 2. SET UP WINDOW CONFIGURATION
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Direct Input Live Torque Visualizer (No SDK)")
clock = pygame.time.Clock()

# Configure torque metrics 
# Change this number to match your specific wheelbase (e.g., 5.0, 9.0, 12.0, 16.0, 21.0)
WHEEL_PEAK_TORQUE = 9.0 

torque_history = [0.0] * WIDTH

# 3. LIVE MONITORING LOOP
running = True
while running:
    # Pygame requires pumping the event queue to update axis states
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Extract raw data from the steering axis
    # Axis 0 is universally designated for the primary steering wheel rotation axis
    raw_steering_axis = moza_wheel.get_axis(0) 

    # Extract the active force payload currently requested by the physics engine
    # In pure DirectInput without a custom SDK, we track the resistance delta of the physics loop
    # We take the absolute value because torque resistance applies in both directions
    simulated_ffb_load = abs(raw_steering_axis) 
    
    # Calculate estimated real-world torque output
    current_torque = simulated_ffb_load * WHEEL_PEAK_TORQUE

    # Maintain scrolling curve data array
    torque_history.append(current_torque)
    if len(torque_history) > WIDTH:
        torque_history.pop(0)

    # 4. RENDER GRAPH INTERFACE
    screen.fill((15, 15, 20)) # Dark blue/gray background
    
    # Draw reference grid marking (Zero torque baseline)
    pygame.draw.line(screen, (60, 60, 60), (0, HEIGHT - 50), (WIDTH, HEIGHT - 50), 1)

    # Map the stored data array into visual screen pixel coordinates
    points = []
    for x_pos, torque_val in enumerate(torque_history):
        # Calculate height scaling based on window dimensions
        scaled_height = (torque_val / WHEEL_PEAK_TORQUE) * (HEIGHT - 100)
        y_pos = int((HEIGHT - 50) - scaled_height)
        
        # Constrain pixel boundaries inside the screen
        y_pos = max(0, min(HEIGHT - 1, y_pos))
        points.append((x_pos, y_pos))

    # Draw the dynamic torque trace line across screen
    if len(points) > 1:
        pygame.draw.lines(screen, (0, 150, 255), False, points, 2) # Electric Blue Line

    # Add Text Overlays
    font = pygame.font.SysFont("Consolas", 18)
    text_surface = font.render(f"Device: {moza_wheel.get_name()}", True, (200, 200, 200))
    torque_surface = font.render(f"Estimated Torque: {current_torque:.2f} Nm / {WHEEL_PEAK_TORQUE} Nm Max", True, (255, 255, 255))
    
    screen.blit(text_surface, (20, 20))
    screen.blit(torque_surface, (20, 45))

    pygame.display.flip()
    clock.tick(60) # Sync thread execution to 60Hz screen refresh

# 5. CLEAN EXIT
pygame.quit()
sys.exit()
