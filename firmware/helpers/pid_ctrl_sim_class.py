import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

class WateringController:
    # Constants
    SECONDS_IN_DAY = 86400

    def __init__(self, setpoint, liters_per_event, deadtime_sec, watering_windows, time_window_days, kp, ki, kd, kimax, kidec,
                 load_event_log_callback = None, store_event_log_callback = None):
        """
        kimax[>0]: maximum absolute value for integral part, as a portion of single liters_per_event. Can also be larger than 1.
        kidec[0..1]: portion of kimax that gets decreased from integral part on every watering event
        """
        # configs
        self.setpoint = setpoint
        self.liters_per_event = liters_per_event
        self.deadtime_sec = deadtime_sec
        self.watering_windows = watering_windows
        self.time_window_days = time_window_days
        self.kp = kp
        self.ki = ki
        self.integral_max = (kimax * liters_per_event) / ki
        self.integral_dec = kidec
        self.kd = kd

        # pid state
        self.integral_error = 0.0
        self.last_error = 0.0
        self.last_event_time = 0

        # event logs to estimate average watering
        self.event_log = []
        if load_event_log_callback:
            self.event_log = load_event_log_callback()
        self.store_event_log_callback = store_event_log_callback

    def run_single_iteration(self, current_time_seconds):
        self.__trim_old_events(current_time_seconds)
        current_average = self.__get_daily_average()
        control, pid_values = self.__pid_update(current_average, self.setpoint)

        is_outside_deadtime = current_time_seconds - self.last_event_time >= self.deadtime_sec
        should_water = self.__is_within_window(current_time_seconds) \
                        and is_outside_deadtime \
                        and control >= self.liters_per_event
        if should_water:
            self.__add_new_event(current_time_seconds)
            self.integral_error -= self.integral_dec * self.integral_max #decrease the integral a bit so it doesn't get triggered again instantly

        return should_water, (current_average, control, pid_values)

    def __trim_old_events(self, current_time_seconds):
        cutoff = int(current_time_seconds - self.time_window_days * WateringController.SECONDS_IN_DAY)
        self.event_log = [t for t in self.event_log if t > cutoff]

    def __add_new_event(self, current_time_seconds):
        self.event_log.append(current_time_seconds)
        self.last_event_time = current_time_seconds
        if self.store_event_log_callback:
            self.store_event_log_callback(self.event_log)

    def __get_daily_average(self):
        return (len(self.event_log) * self.liters_per_event) / self.time_window_days

    def __pid_update(self, current_value, setpoint_value):
        error = setpoint_value - current_value
        self.integral_error += error
        self.integral_error = max(min(self.integral_error, self.integral_max), -self.integral_max)
        derivative = error - self.last_error
        self.last_error = error

        p = self.kp * error
        i = self.ki * self.integral_error
        d = self.kd * derivative
        control = p + i + d
        return control, (p, i, d)

    def __is_within_window(self, current_time_seconds):
        seconds_since_midnight = current_time_seconds % WateringController.SECONDS_IN_DAY
        for wstart, wstop in self.watering_windows:
            if wstart <= seconds_since_midnight <= wstop:
                return True
        return False

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
for liters in range(2,15):
    params = dict(default_params)
    params['setpoint'] = liters
    params_list.append(params)

for p in params_list:
    filename = f"outputs/sim_p={p['kp']}_i={p['ki']}_d={p['kd']}_im={p['kimax']}_id={p['kidec']}_setp={p['setpoint']}_dead={p['deadtime_sec']}.png"
    print(f"Simulating: {filename}")

    controller = WateringController(**p,
                                    liters_per_event=LITERS_PER_WATERING,
                                    watering_windows=WATERING_WINDOWS)
    
    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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