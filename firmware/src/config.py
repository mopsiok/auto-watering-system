try:
    import ujson as json
except:
    import json

class JsonConfig:
    def __init__(self, filePath: str, defaultConfig: dict, console):
        self.filePath = filePath
        self.defaultConfig = defaultConfig
        self.console = console
        self.values = {} #should not be set directly, use load() or update() instead
        if not self.load(self.filePath):
            self.update(jsonValues=None, rawValues=self.defaultConfig)

    def specificPrecheck(self, values: dict):
        return True

    def precheck(self, values: dict):
        try:
            all_fields_present = all(field in values for field in self.defaultConfig.keys())
            fields_count_ok = len(values) == len(self.defaultConfig)
            if (not all_fields_present) or (not fields_count_ok):
                return False
            for key in values.keys():
                value_type = type(values[key])
                default_type = type(self.defaultConfig[key])
                if (default_type in [str, int, bool]) and (value_type != default_type):
                    return False
                if (default_type == float) and (value_type not in [float, int]):
                    return False
            return self.specificPrecheck(values)
        except Exception as error:
            return False

    def load(self, filePath):
        try:
            with open(filePath, 'r') as f:
                tmp = json.loads(f.read())
                if self.precheck(tmp):
                    self.values = tmp.copy()
                    return True
                else:
                    self.console.write(f"Prechecks failed while loading ({filePath})")
        except Exception as error:
            self.console.write(f"Invalid or non-existing file ({filePath})")
        return False

    def update(self, jsonValues: str | None, rawValues: dict = {}):
        try:
            if jsonValues != None:
                rawValues = json.loads(jsonValues)
        except Exception as error:
            self.console.write(f"Invalid json string")
            return False
        
        if not self.precheck(rawValues):
            self.console.write(f"Prechecks failed while updating ({self.filePath})")
            return False
        
        try:
            with open(self.filePath, 'w') as f:
                f.write(json.dumps(rawValues))
            self.values = rawValues.copy()
            self.console.write(f"Updated config ({self.filePath})")
            return True
        except Exception as error:
            self.console.write(f"Error during updating ({self.filePath})")
        return False


class WifiConfig(JsonConfig):
    def __init__(self, console):
        defaultConfig = {"ssid": "your-ssid",
                         "password": "your-pass",
                         "ap_ssid": "auto-watering",
                         "ap_password": "abecadlo"}
        super().__init__("wifiConfig.json", defaultConfig, console)

    def specificPrecheck(self, values: dict):
        return (values['ssid'] != "") and \
               (values['password'] != "") and \
               (values['ap_ssid'] != "") and \
               (values['ap_password'] != "")


class HwConfig(JsonConfig):
    def __init__(self, console):
        defaultConfig = {"water_pump_time_s": 40,
                         "water_pump_duty_percent": 50,
                         "nutrients_pump_volume_ml": 25,
                         "nutrients_pump_duty_percent": 100,
                         "valve_closing_time_s": 7}
        super().__init__("hwConfig.json", defaultConfig, console)

    def specificPrecheck(self, values: dict):
        return (values['water_pump_time_s'] > 0) and \
               (values['water_pump_duty_percent'] > 0) and \
               (values['water_pump_duty_percent'] <= 100) and \
               (values['nutrients_pump_volume_ml'] > 0) and \
               (values['nutrients_pump_duty_percent'] > 0) and \
               (values['nutrients_pump_duty_percent'] <= 100) and \
               (values['valve_closing_time_s'] > 0)


class ControlConfig(JsonConfig):
    def __init__(self, console):
        defaultConfig = {"setpoint": 4.0,
                         "deadtime_sec": 10*60,
                         "watering_windows": [(9 * 3600, 9 * 3600 + 15 * 60), (19 * 3600, 21 * 3600)],
                         "time_window_days": 1.0,
                         "kp": 1.0,
                         "ki": 0.001,
                         "kimax": 1.0,
                         "kidec": 0.1,
                         "kd": 0.0}
        super().__init__("controlConfig.json", defaultConfig, console)

    def specificPrecheck(self, values: dict):
        #TODO check watering windows
        return (values['setpoint'] > 0) and \
               (values['deadtime_sec'] > 0) and \
               (values['time_window_days'] > 0) and \
               (values['kp'] >= 0) and \
               (values['ki'] >= 0) and \
               (values['kimax'] >= 0) and \
               (values['kidec'] >= 0) and \
               (values['kd'] >= 0)
