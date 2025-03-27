import uasyncio as asyncio
from bsp import *
from config import Config
from configPrivate import WIFI_SSID, WIFI_PASSWORD
from logic import Logic
from wifi import Wifi
import ntp
from UartConsole import UartConsole

#TODO to be considered:
# - awesome web server lib https://github.com/jczic/MicroWebSrv2
# - alternative: https://github.com/miguelgrinberg/microdot/tree/main
# - check config keys and values
# - hour-based triggering - what if watering once a day is too much?
#       specify hour and its repetition period in days (since Monday/Sunday)?
# - server for online config and monitoring
# - local access point fallback (some problems on android)

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
    'periodic_watering_online_hours': [8, ],
    'periodic_watering_offline_cycle_s': 24*60*60
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

async def runNetworkTask(config: dict, console):
    wifi = Wifi(console)
    ssid = config['wifi_ssid']
    rssi = await wifi.ReadRssi(ssid)
    console.write(f"RSSI for {ssid}: {rssi}")
    ip = await wifi.Connect(ssid, config['wifi_password'], config['wifi_connection_timeout_ms'])
    ntp.sync()

    # problems with AP (not visible on android)
    # if ip == None:
    #     await wifi.AccessPointStart("ap_test", "abecadlo") #TODO

    # TODO add starting server once connection is made, no need for separate boot.py as it can run on access point, temporarily

async def main():
    console = UartConsole(CONSOLE_UART, CONSOLE_TX_PIN, CONSOLE_RX_PIN, print_output=True)
    config = Config(configFilePath, defaultConfig, console, configPrecheck, configToString)
    gpioHandler = GpioHandler(console)
    valve = Valve(console)
    waterPump = WaterPump()
    nutrientsPump = NutrientsPump()
    logic = Logic(valve, waterPump, nutrientsPump, config.config, console)
    logic.addWateringTrigger(gpioHandler.checkButtonTrigger)

    asyncio.create_task(gpioHandler.runTask())
    asyncio.create_task(logic.runTask())
    asyncio.create_task(runNetworkTask(config.config, console))

    while True:
        await asyncio.sleep(1)
        console.write(f"[{ntp.getCurrentTime()}] Uptime: {logic.uptime:05}   Last watering: {logic.lastTriggerUptime:05}   Watering counter: {logic.wateringCount:03}")


try:
    asyncio.run(main())
finally:  # Prevent LmacRxBlk:1 errors.
    #optional cleanup
    asyncio.new_event_loop()