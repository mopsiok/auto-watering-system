import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, timezone
import os

from firmware.src.WateringController import WateringController

def simulate(controller: WateringController, start_time, end_time, seconds_per_step):
    times, avg_flow = [], []
    p_terms, i_terms, d_terms, control_signals = [], [], [], []
    eventsX, eventsY = [], []
    t = start_time
    while t <= end_time:
        should_water, (current_average, control, (p,i,d)) = controller.run_single_iteration(int(t.timestamp()))
        
        times.append(t)
        avg_flow.append(current_average)
        control_signals.append(control)
        p_terms.append(p)
        i_terms.append(i)
        d_terms.append(d)
        
        if should_water:
            eventsX.append(t)
            eventsY.append(current_average)

        t += timedelta(seconds=seconds_per_step)

    return times, avg_flow, eventsX, eventsY, p_terms, i_terms, d_terms, control_signals

# Simulation constants
LITERS_PER_WATERING = 4.0
WATERING_WINDOWS = [(9 * 3600, 9 * 3600 + 15 * 60), (19 * 3600, 21 * 3600)]
SIM_DAYS = 50
SECONDS_PER_STEP = 60
STEADY_STATE_OFFSET_DAYS = 5

# Config
# Kp, Ki, Kim, Kipb, Kd = 0.6, 0.003, 1.0, 0.3,  0 # good for large setpoints (>10l)
# Kp, Ki, Kim, Kipb, Kd = 0.5, 0.001, 1.2, 0.2, 0 #GOOD stability, but visible offset
# Kp, Ki, Kim, Kipb, Kd = 1, 0.001, 1, 0.02, 0 #pretty small offsets, good stability
Kp, Ki, Kimax, Kidec, Kd = 1, 0.001, 1, 0.1, 0 # smaller chance to trigger 3x waterings in single window (for bigger setpoints)

default_params = {
    'setpoint': 14,
    'deadtime_sec': 10*60,
    'time_window_days': 1,
    'kp': Kp,
    'ki': Ki,
    'kd': Kd,
    'kimax': Kimax,
    'kidec': Kidec
}

params_list = []
for liters in range(1,15):
    params = dict(default_params)
    params['setpoint'] = liters
    params_list.append(params)

current_dir = os.path.dirname(os.path.abspath(__file__))
for p in params_list:
    filename = f"{current_dir}/outputs/sim_p={p['kp']}_i={p['ki']}_d={p['kd']}_im={p['kimax']}_id={p['kidec']}_setp={p['setpoint']}_dead={p['deadtime_sec']}.png"
    print(f"Simulating: {filename}")

    controller = WateringController(**p,
                                    liters_per_event=LITERS_PER_WATERING,
                                    watering_windows=WATERING_WINDOWS)
    
    start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=SIM_DAYS)
    times, avg_flow, eventsX, eventsY, p_terms, i_terms, d_terms, control_signals = simulate(controller, start_time, end_time, seconds_per_step=SECONDS_PER_STEP)

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    steady_state_timestamp = times[0] + timedelta(days=STEADY_STATE_OFFSET_DAYS)
    steady_state_events = sum([1 for t in eventsX if t > steady_state_timestamp])
    actual_average = steady_state_events * controller.liters_per_event / (SIM_DAYS - STEADY_STATE_OFFSET_DAYS)

    ax1.set_title(f"events in steady state: {steady_state_events}")
    ax1.set_ylabel("Average Liters/Day", color='tab:blue')
    ax1.plot(times, avg_flow, label="Moving Average", color='tab:blue')
    ax1.axhline(p['setpoint'], color='gray', linestyle='--', label=f"Target: {p['setpoint']:.1f} L/day")
    ax1.axhline(actual_average, color='violet', linestyle='--', label=f"Actual (steady): {actual_average:.1f} L/day")
    ax1.plot(eventsX, eventsY, linestyle='', marker='o', color='tab:red', label="Watering Event", markersize=5)
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2.set_title("PID Controller Components")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Control Output")
    ax2.plot(times, p_terms, label="P Term", color='tab:green')
    ax2.plot(times, i_terms, label="I Term", color='tab:orange')
    ax2.plot(times, d_terms, label="D Term", color='tab:purple')
    ax2.plot(times, control_signals, label="Total Control", color='black', linestyle='--')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.5)

    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=12))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.setp(ax2.get_xticklabels(), rotation=90)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')