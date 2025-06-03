import asyncio
from microdot import Microdot, Response

#TODO the whole file is based on generated code,
# as a proof of concept only. rethink the approach

import time
import ujson as json
from machine import RTC

server = Microdot()
rtc = RTC()
Response.default_content_type = 'application/json'

@server.route('/')
async def index(request):
    return 'Auto watering system. To be updated.'

@server.route('/time', methods=['GET', 'POST'])
async def handle_time(request):
    if request.method == 'GET':
        dt = rtc.datetime()  # (year, month, day, weekday, hour, minute, second, microsecond)
        return json.dumps({
            'year': dt[0],
            'month': dt[1],
            'day': dt[2],
            'hour': dt[4],
            'minute': dt[5],
            'second': dt[6]
        })

    elif request.method == 'POST':
        try:
            data = request.json
            required_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
            if not all(f in data for f in required_fields):
                return {'error': 'Missing one or more time fields'}, 400
            
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
            return {'status': 'RTC set'}
        except Exception as e:
            return {'error': str(e)}, 400

class Webserver:
    def __init__(self):
        pass

    async def runTask(self):
        await server.start_server()