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
