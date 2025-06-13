import requests, json
from datetime import datetime

DEVICE_IP = "192.168.0.157"

def send(endpoint: str, method: str, jsonPayload = None):
    response = requests.request(method, f"http://{DEVICE_IP}/{endpoint}", json=jsonPayload)
    return response.status_code, response.json()

def time_set(time_values : dict | None = None):
    if time_values == None:
        time_values = get_current_time()
    print(send('time', 'post', time_values))

def time_get():
    print(send('time', 'get'))

def get_current_time():
    now = datetime.now()
    return {'year': now.year,
            'month': now.month,
            'day': now.day,
            'hour': now.hour,
            'minute': now.minute,
            'second': now.second}

if __name__ == "__main__":
    time_get()
    time_set()
    time_get()
    _, wifiConfig = send('wifiConfig', 'get')
    _, controlConfig = send('controlConfig', 'get')
    _, hwConfig = send('hwConfig', 'get')
    print(wifiConfig)
    print(controlConfig)
    print(hwConfig)
