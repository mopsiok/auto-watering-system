# Majority of the code is AI generated, I only wanted to test the watering logic.
# Don't rely on it.

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta

# morningWindow = []

currentAverage=0
def wateringLogic(t_seconds, averageSetpoint=4, timeWindowDays=4, rebootOffset=0):
    global currentAverage
    samplesCount = len(t_seconds)
    output = np.zeros(samplesCount)
    # for i in range(int(rebootOffset), samplesCount):
        
    #     output[i] = amplitude * np.sin(2 * np.pi * frequency * t_seconds[i] / 86400 + phase)
    return output

# Define the start and end time
start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=7)

# Generate time data at 1-minute intervals
time_list = [start_time + timedelta(seconds=i) for i in range(0, int((end_time - start_time).total_seconds()), 60)]
t_seconds = np.array([(t - start_time).total_seconds() for t in time_list])

# Define parameter sets to plot
param_sets = [
    {"averageSetpoint": 4, "timeWindowDays": 3, "rebootOffset": 0},
    {"averageSetpoint": 2.5, "timeWindowDays": 3, "rebootOffset": 10*60},
    {"averageSetpoint": 10, "timeWindowDays": 3, "rebootOffset": 4.1*24*60},
]

# Plot setup
plt.figure(figsize=(14, 6))
for params in param_sets:
    currentAverage = 0
    y = wateringLogic(t_seconds, **params)
    label = f"setpoint={params['averageSetpoint']}, tw={params['timeWindowDays']}, offset={params['rebootOffset']:.1f}"
    plt.plot(time_list, y, label=label)

# Axes formatting
ax = plt.gca()

# Set x-axis major ticks every 3 hours with labels
ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Set x-axis minor ticks every hour for the grid
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))

# Set x-axis limits to match full 7-day window exactly
ax.set_xlim(start_time, end_time)

# Grid formatting
ax.grid(True, which='minor', linestyle=':', linewidth=0.5)
ax.grid(True, which='major', linestyle='--', linewidth=0.8)

# Labeling and layout
plt.xticks(rotation=90)
plt.xlabel("Hour of Day")
plt.ylabel("y = f(t)")
plt.title("Simulation of y = f(t) Over One Week")
plt.legend()
plt.tight_layout()

plt.show()
