

class MotionSimulator:
    def __init__(self, initial_position=299, final_position=0, initial_velocity=0, acceleration=0.5, max_velocity=None):
        # Store the original values to reset later
        self.initial_position = initial_position
        self.initial_final_position = final_position
        self.initial_velocity = initial_velocity
        self.initial_acceleration = -abs(acceleration)  # Ensure acceleration is negative
        self.initial_max_velocity = max_velocity

        # Set the current state using the initial values
        self.position = initial_position
        self.final_position = final_position
        self.velocity = initial_velocity
        self.acceleration = self.initial_acceleration
        self.max_velocity = max_velocity
        self.running = True

    def step(self):
        if not self.running:
            return (self.final_position, False)

        self.position += self.velocity
        self.velocity += self.acceleration

        if self.max_velocity is not None:
            self.velocity = max(min(self.velocity, 0), -abs(self.max_velocity))  # Constrain to negative velocities

        # Check if we've reached or passed the final position
        if self.position <= self.final_position:
            self.position = self.final_position
            self.velocity = 0
            self.running = False

        return (round(self.position), self.running)

    def reset(self):
        """Reset the simulator to its initial state."""
        self.position = self.initial_position
        self.final_position = self.initial_final_position
        self.velocity = self.initial_velocity
        self.acceleration = self.initial_acceleration
        self.max_velocity = self.initial_max_velocity
        self.running = True

