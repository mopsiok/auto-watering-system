import time, ntptime
import ujson as json
from machine import RTC

UTC_TIMEZONE_OFFSET_SECONDS = 2*3600

rtc = RTC()

def syncNtp():
    ntptime.settime()
    local_time = time.localtime(time.mktime(time.localtime()) + UTC_TIMEZONE_OFFSET_SECONDS)
    rtc.datetime((local_time[0],  # year
                  local_time[1],  # month
                  local_time[2],  # day
                  local_time[6],  # weekday (0 = Monday)
                  local_time[3],  # hour
                  local_time[4],  # minute
                  local_time[5],  # second
                  0               # microsecond
                ))

def isTimeSynced():
    # just after startup, the default datetime for this HW is around 01.01.2021
    # this hack quickly determines whether the time is synchronized
    currentYear = getCurrentDateTime()[0]
    return (currentYear >= 2025)

def getCurrentDateTime():
    # (year, month, day, weekday, hour, minute, second, microsecond)
    return rtc.datetime()

def getCurrentSeconds():
    return int(time.time())

def getCurrentDateTimeStr(printTime=True, printDate=False):
    dt = getCurrentDateTime()
    time_ = f"{dt[4]:02}:{dt[5]:02}:{dt[6]:02}"
    date_ = f"{dt[2]:02}.{dt[1]:02}.{dt[0]:04}"
    return f"{date_ if printDate else ""}{" " if printDate & printTime else ""}{time_ if printTime else ""}"

def setCurrentDateTimeJson(data):
    required_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
    if not all(f in data for f in required_fields):
        raise Exception('Missing one or more time fields')
    
    dt = tuple(map(int, [
        data['year'],
        data['month'],
        data['day'],
        0,  # weekday (ignored)
        data['hour'],
        data['minute'],
        data['second'],
        0   # microsecond
    ]))
    rtc.datetime(dt)