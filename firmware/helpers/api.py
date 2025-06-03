import requests
from datetime import datetime

# TODO for testing only, refactor that shit

PI_URL = "http://192.168.0.157:5000/time"

def get_current_time_fields():
    now = datetime.now()
    return {
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute,
        'second': now.second
    }

def set_time_on_pi():
    payload = get_current_time_fields()
    try:
        response = requests.post(PI_URL, json=payload)
        if response.status_code == 200:
            print("Time set successfully:", response.json())
        else:
            print(f"Failed to set time (status {response.status_code}):", response.text)
    except requests.RequestException as e:
        print("Error communicating with Raspberry Pi:", e)

def get_time_from_pi():
    try:
        response = requests.get(PI_URL)
        if response.status_code == 200:
            data = response.json()
            print("Time on device:", data)
        else:
            print(f"Failed to get time (status {response.status_code}):", response.text)
    except requests.RequestException as e:
        print("Error communicating with Raspberry Pi:", e)

if __name__ == "__main__":
    set_time_on_pi()
    get_time_from_pi()