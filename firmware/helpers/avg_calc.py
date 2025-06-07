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
    flowData = np.zeros(samplesCount)
    eventsX = []
    eventsY = []
    deadtime = 0
    for i in range(int(rebootOffset), samplesCount):
        timestamp = t_seconds[i]
        isOutsideDeadTime = timestamp >= deadtime
        isWithinTimeWindow = isWithinDailyWindow(timestamp, morningWindow[0], morningWindow[1]) \
                          or isWithinDailyWindow(timestamp, eveningWindow[0], eveningWindow[1])
        
        eventsCount = countWateringEvents(timestamp, timeWindowDays, eventlist)
        currentFlow = WATER_PER_EVENT_ML * eventsCount / timeWindowDays
        flowData[i] = currentFlow
        
        nextWateringWindowTime = getNextWateringWindow(timestamp, [morningWindow, eveningWindow])
        futureFlow = WATER_PER_EVENT_ML * countWateringEvents(nextWateringWindowTime, timeWindowDays, eventlist) / (timeWindowDays)

        print(f"t={getSecondsSinceMidnight(timestamp):05} currentFlow={currentFlow:5.1f} ({averageSetpoint:.1f}), futureFlow={futureFlow:5.1f} ({minSetpoint:.1f})")

        shouldBeWatered = (currentFlow < averageSetpoint) or (futureFlow < minSetpoint)
        if isOutsideDeadTime and isWithinTimeWindow and shouldBeWatered:
            print("   Preconditions ok, triggering")
            eventsX.append(timestamp)
            eventsY.append(eventsCount+1)
            eventlist.append(timestamp)
            deadtime = timestamp + DEADTIME_S
        updateWateringEvents(timestamp, timeWindowDays, eventlist)
    return flowData, eventsX, eventsY

start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(days=7)

# Generate time data at 1-minute intervals
time_list = [start_time + timedelta(seconds=i) for i in range(0, int((end_time - start_time).total_seconds()), 60)]
t_seconds = np.array([int(t.timestamp() + 2*3600) for t in time_list])  # Simulated UTC+2

# Define parameter sets to plot
param_sets = [
    {"averageSetpoint": 4000, "minSetpoint": 3000, "timeWindowDays": 3, "rebootOffset": 0},
    {"averageSetpoint": 4000, "minSetpoint": 3000, "timeWindowDays": 2, "rebootOffset": 0},
    # {"averageSetpoint": 2500, "minSetpoint": 2000, "timeWindowDays": 3, "rebootOffset": 10*60},
    # {"averageSetpoint": 10000, "minSetpoint": 7000, "timeWindowDays": 3, "rebootOffset": 4.1*24*60},
]

# Create separate plots for each parameter set
for idx, params in enumerate(param_sets):
    flow, eventsX, eventsY = wateringLogic(t_seconds, **params)
    eventsX = [datetime.fromtimestamp(ts - 2*3600) for ts in eventsX]
    label = f"avg={params['averageSetpoint']}, min={params['minSetpoint']}, tw={params['timeWindowDays']}, offset={params['rebootOffset']:.1f}"

    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.set_title(f"Simulation: {label}")
    ax1.set_xlabel("Hour of Day")
    ax1.set_ylabel("Flow", color='tab:blue')
    ax1.plot(time_list, flow, label="Flow", color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()  # Create a second y-axis for events
    ax2.set_ylabel("Events", color='tab:red')
    ax2.plot(eventsX, eventsY, label="Events", color='tab:red', alpha=0.6, linewidth=0, marker=".")
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # X-axis formatting
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax1.set_xlim(start_time, end_time)
    plt.setp(ax1.get_xticklabels(), rotation=90)

    # Grid
    ax1.grid(True, which='minor', linestyle=':', linewidth=0.5)
    ax1.grid(True, which='major', linestyle='--', linewidth=0.8)

    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()