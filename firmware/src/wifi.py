import uasyncio as asyncio
import network

class Wifi():
    def __init__(self, console):
        self.console = console

    async def Scan(self, printResults = False):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wifis = wlan.scan()
        if printResults:
            for wifi in wifis:
                self.console.write(f"RSSI: {wifi[3]:04}   Channel: {wifi[2]:02}   SSID: {wifi[0].decode('utf-8')}")
        return wifis

    async def ReadRssi(self, ssid):
        wifis = await self.Scan(False)
        for wifi in wifis:
            _ssid = wifi[0].decode('utf-8')
            if (ssid == _ssid):
                return wifi[3]
        return None

    async def AccessPointStart(self, ssid, password):
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=ssid, password=password)
        await asyncio.sleep_ms(500)
        info = ap.ifconfig()
        self.console.write(f'Access Point started ({ssid})\nNetwork info: {info}')
        return info

    async def AccessPointStop(self):
        ap = network.WLAN(network.AP_IF)
        ap.active(False)
        self.console.write('Access Point stopped.')
    
    async def Connect(self, ssid, password, timeout_ms=10000):
        self.console.write(f'Connecting to WiFi ({ssid})...')
        wlan = network.WLAN(network.STA_IF)
        if (not ssid) or (not password):
            wlan.active(False)
            return None
        
        network.WLAN(network.AP_IF).active(False) # disable access point mode

        LOOP_TIME_MS = 100
        wlan.active(True)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            await asyncio.sleep_ms(LOOP_TIME_MS)
            timeout_ms -= LOOP_TIME_MS
            if timeout_ms <= 0:
                self.console.write('Connection timeout.')
                return None
        
        info = wlan.ifconfig()
        ip = info[0]
        self.console.write(f'Connected. IP: {ip}')
        return ip
    
    async def Disconnect(self):
        self.console.write('Disconnecting from WiFi...')
        wlan = network.WLAN(network.STA_IF)
        wlan.disconnect()