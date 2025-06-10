import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Config
LITERS_PER_WATERING = 4.0
DEADTIME_SECONDS = 10 * 60
WATERING_WINDOWS = [(9 * 3600, 9 * 3600 + 15 * 60), (19 * 3600, 21 * 3600)]
TIME_WINDOW_DAYS = 1.3
SECONDS_PER_STEP = 60
SIM_DAYS = 21
# Kp, Ki, Kd = 0.6, 0.001, 0
# Kp, Ki, Kd = 0.6, 0.0005, 0
# Kp, Ki, Kd = 0.5, 0.0003, 0
Kp, Ki, Kd = 0.6, 0.003, 0
# INTEGRAL_MAX = (LITERS_PER_WATERING - Kp*1.1) / Ki  # Anti-windup limit on integral error
INTEGRAL_MAX = (LITERS_PER_WATERING) / Ki  # Anti-windup limit on integral error
INTEGRAL_PULLBACK =  (0.3*LITERS_PER_WATERING) / Ki

def seconds_since_midnight(ts):
    return ts % 86400

def is_within_window(ts):
    t_day = seconds_since_midnight(ts)
    for wstart, wstop in WATERING_WINDOWS:
        if wstart <= t_day <= wstop:
            return True
    return False

def trim_old_events(now, log):
    cutoff = now - TIME_WINDOW_DAYS * 86400
    return [t for t in log if t >= cutoff]

def calc_daily_avg(now, log):
    recent = trim_old_events(now, log)
    return (len(recent) * LITERS_PER_WATERING) / TIME_WINDOW_DAYS

def simulate(setpoint_liters_per_day):
    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=SIM_DAYS)

    t_seconds = int(start_time.timestamp())
    t_end = int(end_time.timestamp())

    times = []
    avg_liters_per_day = []
    eventsX = []
    eventsY = []

    p_terms = []
    i_terms = []
    d_terms = []
    control_signals = []

    #on real code, only include artificial events if no data is available from before reboot (flash)
    event_log = []
    # events_needed = round(setpoint_liters_per_day * TIME_WINDOW_DAYS / LITERS_PER_WATERING)
    # interval_seconds = TIME_WINDOW_DAYS * 86400 / events_needed
    # for i in range(events_needed):
    #     synthetic_event_time = t_seconds - int((events_needed - i) * interval_seconds)
    #     event_log.append(synthetic_event_time)

    last_event_time = -999999
    integral_error = 0.0
    last_error = 0.0

    while t_seconds <= t_end:
        now_dt = datetime.fromtimestamp(t_seconds)
        times.append(now_dt)

        avg = calc_daily_avg(t_seconds, event_log)
        avg_liters_per_day.append(avg)

        error = setpoint_liters_per_day - avg

        # Update and clamp integral at all times
        integral_error += error
        integral_error = max(min(integral_error, INTEGRAL_MAX), -INTEGRAL_MAX)

        # PID components
        proportional = Kp * error
        integral = Ki * integral_error
        derivative = error - last_error
        derivative_term = Kd * derivative
        last_error = error

        control = proportional + integral + derivative_term

        # Store PID components
        p_terms.append(proportional)
        i_terms.append(integral)
        d_terms.append(derivative_term)
        control_signals.append(control)

        if is_within_window(t_seconds) and (t_seconds - last_event_time >= DEADTIME_SECONDS):
            if control >= LITERS_PER_WATERING:
                event_log.append(t_seconds)
                last_event_time = t_seconds
                eventsX.append(now_dt)
                eventsY.append(avg)

                # Pullback integral to prevent immediate follow-up watering
                integral_error -= INTEGRAL_PULLBACK

        t_seconds += SECONDS_PER_STEP

    return times, avg_liters_per_day, eventsX, eventsY, len(event_log), p_terms, i_terms, d_terms, control_signals

# Run simulation
setpoint = 18
times, avg_flow, eventsX, eventsY, total_events, p_terms, i_terms, d_terms, control_signals = simulate(setpoint)

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

actual_average = total_events*LITERS_PER_WATERING/SIM_DAYS

# Subplot 1: Moving average
ax1.set_title(f"Moving Average of Watering - Total Events: {total_events}")
ax1.set_ylabel("Average Liters/Day", color='tab:blue')
ax1.plot(times, avg_flow, label="Moving Average", color='tab:blue')
ax1.axhline(setpoint, color='gray', linestyle='--', label=f"Target: {setpoint:0.1f} L/day")
ax1.axhline(actual_average, color='violet', linestyle='--', label=f"Actual: {actual_average:0.1f} L/day")
ax1.plot(eventsX, eventsY, linestyle='', marker='o', color='tab:red', label="Watering Event", markersize=5)
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.legend()
ax1.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: PID components
ax2.set_title("PID Controller Components")
ax2.set_xlabel("Time")
ax2.set_ylabel("Control Output")
ax2.plot(times, p_terms, label="P Term", color='tab:green')
ax2.plot(times, i_terms, label="I Term", color='tab:orange')
ax2.plot(times, d_terms, label="D Term", color='tab:purple')
ax2.plot(times, control_signals, label="Total Control", color='black', linestyle='--')
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.5)

# X-axis formatting
ax2.xaxis.set_major_locator(mdates.HourLocator(interval=12))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
plt.setp(ax2.get_xticklabels(), rotation=45)

plt.tight_layout()
plt.show()
