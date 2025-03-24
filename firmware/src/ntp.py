import ntptime
import time

def sync():
    ntptime.settime()

def getCurrentTime():
    t = time.localtime()
    return f"{t[3]:02}:{t[4]:02}:{t[5]:02}"
