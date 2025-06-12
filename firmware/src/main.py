import uasyncio as asyncio
from bsp import *
from config import *
from logic import Logic
from wifi import Wifi
from UartConsole import UartConsole
import mytime, webserver

#TODO is it a problem when the user changes ssid/password while being on AP mode, then trying to reconnect?
# solutions:
# - reboot the board (easy)
# - redesign the app to asyncio events (might be needed anyway, as it is getting more complicated)
#       e.g. changing the triggering of watering to queue, to avoid stupid wrappers
# - alternatively, only expose single function for external trigger

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

async def connectWifiOrAp(wifi: Wifi, config: WifiConfig, console):
    if not wifi.IsConnected():
        await wifi.Connect(config.values['ssid'], config.values['password'])
    
    if not wifi.IsConnected():
        ap_ssid = config.values['ap_ssid']
        console.write(f"Starting access point with SSID={ap_ssid}")
        await wifi.ApStart(ap_ssid, config.values['ap_password'])
        return False
    return True

async def runNetworkTask(wifi: Wifi, config: WifiConfig, console):
    NETWORK_CONNECT_RERUN_PERIOD_SEC = 10*60
    while(True):
        try:
            isConnected = await connectWifiOrAp(wifi, config, console)
            if isConnected:
                await asyncio.sleep(5)
                console.write(f"Syncing time with NTP")
                mytime.syncNtp()
        except Exception as e:
            console.write(f"Error while network handling: {str(e)}")
        await asyncio.sleep(NETWORK_CONNECT_RERUN_PERIOD_SEC)

async def main():
    console = UartConsole(CONSOLE_UART, CONSOLE_TX_PIN, CONSOLE_RX_PIN, print_output=True)
    wifiConfig = WifiConfig(console)
    wifi = Wifi(console)
    gpioHandler = GpioHandler(console)
    logic = Logic(console)
    logic.addWateringTrigger(gpioHandler.checkButtonTrigger)

    asyncio.create_task(gpioHandler.runTask())
    asyncio.create_task(logic.runTask())
    asyncio.create_task(runNetworkTask(wifi, wifiConfig, console))

    webserver.start()
    logic.addWateringTrigger(webserver.checkWebWateringTrigger)
    console.write('Webserver started')

    while True:
        await asyncio.sleep(1)
        wifiStr = wifi.GetIp() if wifi.IsConnected() else "x"
        apStr = wifi.ApGetIp() if wifi.ApIsReady() else "x"
        console.write(f"[{mytime.getCurrentDateTimeStr()}][{wifiStr}|{apStr}] Uptime: {logic.uptime:05}   Last watering: {logic.lastTriggerUptime:05}   Watering counter: {logic.wateringCount:03}")


try:
    asyncio.run(main())
finally:  # Prevent LmacRxBlk:1 errors.
    #optional cleanup
    asyncio.new_event_loop()