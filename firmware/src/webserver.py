from config import *
import mytime
from microdot import Microdot, Response
import asyncio

WEB_PORT = 80

server = Microdot()
Response.default_content_type = 'application/json'

triggerWatering = False

@server.route('/')
async def index(request):
    return 'Auto watering system. To be updated.'

@server.route('/time', methods=['GET', 'POST'])
async def handle_time(request):
    try:
        if request.method == 'GET':
            return {'time': mytime.getCurrentDateTimeStr(True, True)}
        elif request.method == 'POST':
            mytime.setCurrentDateTimeJson(request.json)
            return {'status': 'RTC set'}
    except Exception as e:
        return {'error': str(e)}, 400
        
@server.route('/ntpsync')
async def handle_ntp_sync(request):
    try:
        mytime.syncNtp()
        return {'status': 'Time synchronized'}
    except Exception as e:
        return {'error': str(e)}, 400
    
@server.route('/trigger')
async def handle_trigger(request):
    global triggerWatering
    try:
        triggerWatering = True
        return {'status': 'Triggered'}
    except Exception as e:
        return {'error': str(e)}, 400
    
def start():
    asyncio.create_task(server.start_server(port=WEB_PORT))

def checkWebWateringTrigger():
    global triggerWatering
    if triggerWatering:
        triggerWatering = False
        return True
    return False