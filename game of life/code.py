import time
import board
import digitalio
from analogio import AnalogIn
import random

# Initialize CV input
cv_in = AnalogIn(board.A0)

# Initialize output gates
gates = [
    digitalio.DigitalInOut(board.D1),
    digitalio.DigitalInOut(board.D2),
    digitalio.DigitalInOut(board.D3),
    digitalio.DigitalInOut(board.D6),
    digitalio.DigitalInOut(board.D10),
    digitalio.DigitalInOut(board.D9),
    digitalio.DigitalInOut(board.D8),
    digitalio.DigitalInOut(board.D7),
]

for gate in gates:
    gate.direction = digitalio.Direction.OUTPUT

# Initialize the Game of Life grid
grid_size = 8
grid = [[False for _ in range(grid_size)] for _ in range(grid_size)]

# Function to initialize the grid based on ADC value
def initialize_grid_with_seed(adc_value):
    random.seed(adc_value)
    for row in range(grid_size):
        for col in range(grid_size):
            grid[row][col] = random.choice([True, False])

# Function to get the number of live neighbors for a cell
def get_live_neighbors(row, col):
    live_neighbors = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if not (i == 0 and j == 0):
                if 0 <= row + i < grid_size and 0 <= col + j < grid_size:
                    if grid[row + i][col + j]:
                        live_neighbors += 1
    return live_neighbors

# Function to update the grid
def update_grid():
    global grid
    new_grid = [[False for _ in range(grid_size)] for _ in range(grid_size)]
    for row in range(grid_size):
        for col in range(grid_size):
            live_neighbors = get_live_neighbors(row, col)
            if grid[row][col]:
                if live_neighbors in [2, 3]:
                    new_grid[row][col] = True
            else:
                if live_neighbors == 3:
                    new_grid[row][col] = True
    grid = new_grid

# Function to print the grid (for debugging)
def print_grid():
    for row in grid:
        print("".join(["#" if cell else "." for cell in row]))
    print()

# Threshold ADC value for trigger detection
adc_threshold = 37000

# Flag to detect the rising edge of the trigger
trigger_detected = False

# Initialize row readers
row_readers = [0 for _ in range(grid_size)]

# Function to read ADC value
def read_adc():
    return cv_in.value

# Pulse counter and group counter
pulse_count = 0
group_count = 0

last_adc_value = None
adc_threshold_value = 100  # Define a threshold value for ADC change

def get_stable_adc_value_with_threshold():
    global last_adc_value
    current_adc_value = read_adc()
    if last_adc_value is None or abs(current_adc_value - last_adc_value) > adc_threshold_value:
        last_adc_value = current_adc_value
    return last_adc_value

# Function to process input trigger
def process_trigger():
    global pulse_count, group_count, row_readers
    pulse_count += 1

    # Update gates based on the current cell in each row
    for i, gate in enumerate(gates):
        cell_state = grid[i][row_readers[i]]
        gate.value = cell_state
        row_readers[i] = (row_readers[i] + 1) % grid_size

    # Update grid every 8 pulses
    if pulse_count >= 8:
        pulse_count = 0
        update_grid()
        print_grid()  # Debugging line to print the grid state

        # Reset row readers
        row_readers = [0 for _ in range(grid_size)]

        group_count += 1
        if group_count >= 16:  # Reinitialize grid every 128 pulses
            group_count = 0
            adc_value = get_stable_adc_value_with_threshold()  # Use threshold-based ADC value for seeding
            initialize_grid_with_seed(adc_value)
            print(f"Grid reinitialized with seed: {adc_value}")

# Main loop
while True:
    adc_value = read_adc()

    if adc_value >= adc_threshold and not trigger_detected:
        trigger_detected = True
        process_trigger()

    elif adc_value < adc_threshold and trigger_detected:
        trigger_detected = False  # Reset the detection flag after the trigger ends

    time.sleep(0.001)  # Sleep time adjustment
