import uasyncio as asyncio
from bsp import *
from config import Config
from configPrivate import *
from logic import Logic
from wifi import Wifi
from UartConsole import UartConsole
import mytime, webserver

#TODO is it a problem when the user changes ssid/password while being on AP mode, then trying to reconnect?
# solutions:
# - reboot the board (easy)
# - redesign the app to asyncio events (might be needed anyway, as it is getting more complicated)
#       e.g. changing the triggering of watering to queue, to avoid stupid wrappers

#TODO to be considered:
# - check config keys and values
# - hour-based triggering - what if watering once a day is too much?
#       specify hour and its repetition period in days (since Monday/Sunday)?

configFilePath = 'config.json'
defaultConfig = {
    'wifi_ssid': WIFI_SSID,
    'wifi_password': WIFI_PASSWORD,
    'wifi_connection_timeout_ms': 15000,
    'water_pump_duty_percent': 50,
    'water_pump_time_s': 40,
    'nutrients_pump_duty_percent': 100,
    'nutrients_pump_volume_ml': 25,
    'valve_closing_time_s': 7,
    # 'periodic_watering_online_hours': [8, ], #TODO not supported for now
    'periodic_watering_offline_cycle_s': 4*24*60*60
    }

def configPrecheck(config: dict):
    return True

def configToString(config: dict):
    string = ""
    for key in config.keys():
        if key in ["wifi_ssid", "wifi_password"]:
            continue
        string += f"\t{key: <27} = {config[key]}\n"
    return string

class GpioHandler:
    def __init__(self, console):
        self.console = console
        self.led = Led()
        self.button = Button(TRIGGER_BUTTON_PIN, activeLow=True)
        self.buttonPressed = False

    async def runTask(self):
        while True:
            self.led.toggle()
            if self.button.isPressed():
                self.console.write("Button trigger.")
                self.buttonPressed = True
            await asyncio.sleep_ms(100)
    
    def checkButtonTrigger(self):
        if self.buttonPressed:
            self.buttonPressed = False
            return True
        return False

async def tryConnectWifiOrAp(wifi: Wifi, config: dict, console):
    try:
        ssid = config['wifi_ssid']
        rssi = wifi.ReadRssi(ssid)
        console.write(f"RSSI for {ssid}: {rssi}")
        await wifi.Connect(ssid, config['wifi_password'], config['wifi_connection_timeout_ms'])

        isConnected = wifi.IsConnected()
        if isConnected:
            await asyncio.sleep(3)
            console.write(f"Syncing time with NTP")
            mytime.syncNtp()
        else:
            console.write(f"Starting access point with SSID={AP_SSID}")
            await wifi.ApStart(AP_SSID, AP_PASSWORD)
        return isConnected
    except Exception as e:
        console.write(f"Error while network handling: {str(e)}")
        return False

async def runNetworkTask(wifi: Wifi, config: dict, console):
    NETWORK_CONNECT_RERUN_PERIOD_SEC = 10*60
    isConnected = False
    while(True):
        if not isConnected:
            isConnected = tryConnectWifiOrAp(wifi, config, console)
        await asyncio.sleep(NETWORK_CONNECT_RERUN_PERIOD_SEC)

console = UartConsole(CONSOLE_UART, CONSOLE_TX_PIN, CONSOLE_RX_PIN, print_output=True)
config = Config(configFilePath, defaultConfig, console, configPrecheck, configToString)
wifi = Wifi(console)

async def main():
    gpioHandler = GpioHandler(console)
    valve = Valve(console)
    waterPump = WaterPump()
    nutrientsPump = NutrientsPump()
    logic = Logic(valve, waterPump, nutrientsPump, config.config, console)
    logic.addWateringTrigger(gpioHandler.checkButtonTrigger)

    asyncio.create_task(gpioHandler.runTask())
    asyncio.create_task(logic.runTask())
    asyncio.create_task(runNetworkTask(wifi, config.config, console))

    webserver.start()
    logic.addWateringTrigger(webserver.checkWebWateringTrigger)
    console.write('Webserver started')

    while True:
        await asyncio.sleep(1)
        wifiStr = wifi.GetIp()# if wifi.IsConnected() else "x"
        apStr = wifi.ApGetIp()# if wifi.ApIsReady() else "x"
        console.write(f"[{mytime.getCurrentDateTimeStr()}][{wifiStr}|{apStr}] Uptime: {logic.uptime:05}   Last watering: {logic.lastTriggerUptime:05}   Watering counter: {logic.wateringCount:03}")


try:
    asyncio.run(main())
finally:  # Prevent LmacRxBlk:1 errors.
    #optional cleanup
    asyncio.new_event_loop()