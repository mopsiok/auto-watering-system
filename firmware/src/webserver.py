from config import *
import mytime
from microdot import Microdot, Response
import asyncio

WEB_PORT = 80

server = Microdot()
Response.default_content_type = 'application/json'

_triggerCallback = None
_controlConfig = None
_hwConfig = None
_wifiConfig = None
_console = None

@server.route('/controlConfig', methods=['GET', 'POST'])
async def handle_control_config(request):
    if request.method == 'GET':
        if _controlConfig:
            return _controlConfig.values
        else:
            return {'error': 'No config provided'}        
    elif request.method == 'POST':
        if _controlConfig and _controlConfig.update(request.json):
            return {'status': 'Updated'}
        return {'error': 'check logs'}, 400


@server.route('/hwConfig', methods=['GET', 'POST'])
async def handle_hw_config(request):
    if request.method == 'GET':
        if _hwConfig:
            return _hwConfig.values
        else:
            return {'error': 'No config provided'}        
    elif request.method == 'POST':
        if _hwConfig and _hwConfig.update(request.json):
            return {'status': 'Updated'}
        return {'error': 'check logs'}, 400


@server.route('/wifiConfig', methods=['GET', 'POST'])
async def handle_wifi_config(request):
    if request.method == 'GET':
        if _wifiConfig:
            values = _wifiConfig.values.copy()
            values['password'] = "___"
            values['ap_password'] = "___"
            return values
        else:
            return {'error': 'No config provided'}        
    elif request.method == 'POST':
        if _wifiConfig and _wifiConfig.update(request.json):
            return {'status': 'Updated'}
        return {'error': 'check logs'}, 400


@server.route('/trigger', methods=['GET'])
async def handle_trigger(request):
    try:
        if _triggerCallback:
            _triggerCallback()
        return {'status': 'Triggered'}
    except Exception as e:
        return {'error': str(e)}, 400


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

@server.route('/ntpsync', methods=['GET'])
async def handle_ntp_sync(request):
    try:
        mytime.syncNtp()
        return {'status': 'Time synchronized'}
    except Exception as e:
        return {'error': str(e)}, 400


@server.route('/')
async def index(request):
    return 'Auto watering system'
    
def start(triggerCallback, controlConfig: ControlConfig, hwConfig: HwConfig, wifiConfig: WifiConfig, console):
    global _triggerCallback, _controlConfig, _hwConfig, _wifiConfig, _console
    _triggerCallback = triggerCallback
    _controlConfig = controlConfig
    _hwConfig = hwConfig
    _wifiConfig = wifiConfig
    _console = console
    asyncio.create_task(server.start_server(port=WEB_PORT))