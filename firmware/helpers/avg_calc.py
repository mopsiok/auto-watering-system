# Majority of the code is AI generated, I only wanted to test the watering logic.
# Don't rely on it.

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime, timedelta
import time

WATER_PER_EVENT_ML = 4000
DEADTIME_S = 10*60
SEC_IN_DAY = 24*3600
morningWindow = [9*3600, 9.25*3600]
eveningWindow = [19*3600, 21*3600]

def getSecondsSinceMidnight(timestamp):
    t = time.gmtime(timestamp)
    return t[3] * 3600 + t[4] * 60 + t[5]

def isWithinDailyWindow(timestamp, wstart, wstop):
    return wstart <= getSecondsSinceMidnight(timestamp) <= wstop

def getNextWateringWindow(timestamp, windows): 
    # NOTE: windows must be sorted earliest to latest
    secondsSinceMidnight = getSecondsSinceMidnight(timestamp)
    todayMidnight = timestamp - secondsSinceMidnight

    # check if there is any window today
    for wstart, wstop in windows:
        if wstart > secondsSinceMidnight:
            return todayMidnight + wstart

    # all windows passed for today, return the first window of tomorrow
    return todayMidnight + SEC_IN_DAY + windows[0][0]

def countWateringEvents(tstop, timeWindowDays, eventlist):
    count = 0
    for event in eventlist:
        if (tstop - timeWindowDays * SEC_IN_DAY) <= event <= tstop:
            count += 1
    return count

def updateWateringEvents(now, timeWindowDays, eventlist):
    time_limit = now - (timeWindowDays * SEC_IN_DAY)
    eventlist[:] = [e for e in eventlist if e >= time_limit]

def wateringLogic(t_seconds, averageSetpoint=4, minSetpoint=3, timeWindowDays=4, rebootOffset=0):
    eventlist = [] #will be global on embedded
    samplesCount = len(t_seconds)
    flow = np.zeros(samplesCount)
    events = np.zeros(samplesCount)
    deadtime = 0
    for i in range(int(rebootOffset), samplesCount):
        timestamp = t_seconds[i]
        isOutsideDeadTime = timestamp >= deadtime
        isWithinTimeWindow = isWithinDailyWindow(timestamp, morningWindow[0], morningWindow[1]) \
                          or isWithinDailyWindow(timestamp, eveningWindow[0], eveningWindow[1])
        
        eventsCount = countWateringEvents(timestamp, timeWindowDays, eventlist)
        currentFlow = WATER_PER_EVENT_ML * eventsCount / timeWindowDays
        flow[i] = currentFlow
        events[i] = eventsCount
        
        nextWateringWindowTime = getNextWateringWindow(timestamp, [morningWindow, eveningWindow])
        futureFlow = WATER_PER_EVENT_ML * countWateringEvents(nextWateringWindowTime, timeWindowDays, eventlist) / (timeWindowDays*10) #TODO

        shouldBeWatered = (currentFlow < averageSetpoint) or (futureFlow < minSetpoint)
        if shouldBeWatered:
            print(f"Should be watered! t={timestamp} ({getSecondsSinceMidnight(timestamp)}) currentFlow={currentFlow} ({averageSetpoint}), futureFlow={futureFlow} ({minSetpoint})")
        
        if isOutsideDeadTime and isWithinTimeWindow and shouldBeWatered:
            # print(f"Should be watered! t={timestamp} ({getSecondsSinceMidnight(timestamp)}) currentFlow={currentFlow} ({averageSetpoint}), futureFlow={futureFlow} ({minSetpoint})")
            print("   Preconditions ok, triggering")
            eventlist.append(timestamp)
            deadtime = timestamp + DEADTIME_S
        updateWateringEvents(timestamp, timeWindowDays, eventlist)
    return flow, events

start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=7)

# Generate time data at 1-minute intervals
time_list = [start_time + timedelta(seconds=i) for i in range(0, int((end_time - start_time).total_seconds()), 60)]
t_seconds = np.array([int(t.timestamp() + 2*3600) for t in time_list]) #dirty hack for +2 UTC timezone, doesn't matter in sim scenario

# Define parameter sets to plot
param_sets = [
    {"averageSetpoint": 4000, "minSetpoint": 3000, "timeWindowDays": 3, "rebootOffset": 0},
    # {"averageSetpoint": 2500, "minSetpoint": 2000, "timeWindowDays": 3, "rebootOffset": 10*60},
    # {"averageSetpoint": 10000, "minSetpoint": 7000, "timeWindowDays": 3, "rebootOffset": 4.1*24*60},
]

# Plot setup
plt.figure(figsize=(14, 6))
for params in param_sets:
    flow,events = wateringLogic(t_seconds, **params)
    label = f"avg={params['averageSetpoint']}, min={params['minSetpoint']}, tw={params['timeWindowDays']}, offset={params['rebootOffset']:.1f}"
    plt.plot(time_list, flow, label=label)
    plt.plot(time_list, events, label=label)

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
