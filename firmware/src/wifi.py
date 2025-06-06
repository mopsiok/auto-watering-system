import uasyncio as asyncio
import network

class Wifi():
    def __init__(self, console):
        self.console = console
        self.wlan = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)

    async def Connect(self, ssid, password, timeout_ms=10000):
        self.console.write(f'Connecting to WiFi ({ssid})...')
        if (not ssid) or (not password):
            return None
        
        self.ApStop()

        LOOP_TIME_MS = 100
        self.wlan.active(True)
        self.wlan.connect(ssid, password)
        while not self.IsConnected():
            await asyncio.sleep_ms(LOOP_TIME_MS)
            timeout_ms -= LOOP_TIME_MS
            if timeout_ms <= 0:
                self.console.write('Connection timeout.')
                return None
        
        ip = self.GetIp()
        self.console.write(f'Connected. IP: {ip}')
        return ip
    
    def Disconnect(self):
        self.console.write('Disconnecting from WiFi...')
        self.wlan.disconnect()

    def Stop(self):
        self.wlan.active(False)

    def IsConnected(self):
        return self.wlan.isconnected()
    
    def GetIp(self):
        return self.wlan.ifconfig()[0]

    def Scan(self, printResults = False):
        self.ApStop()
        self.wlan.active(True)
        wifis = self.wlan.scan()
        if printResults:
            for wifi in wifis:
                self.console.write(f"RSSI: {wifi[3]:04}   Channel: {wifi[2]:02}   SSID: {wifi[0].decode('utf-8')}")
        return wifis

    def ReadRssi(self, ssid):
        wifis = self.Scan(False)
        for wifi in wifis:
            _ssid = wifi[0].decode('utf-8')
            if (ssid == _ssid):
                return wifi[3]
        return None

    async def ApStart(self, ssid, password):
        self.Stop()
        self.ap.active(True)
        self.ap.config(essid=ssid, password=password)
        await asyncio.sleep_ms(1000)
        info = self.ap.ifconfig()
        self.console.write(f'Access Point started ({ssid})\nNetwork info: {info}')
        return info

    def ApStop(self):
        self.ap.active(False)

    def ApIsReady(self):
        return self.ap.active()

    def ApGetIp(self):
        return self.ap.ifconfig()[0]
    
