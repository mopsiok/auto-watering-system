import uasyncio as asyncio
import machine

VALVE_CLOSE_PIN = 21
VALVE_OPEN_PIN = 20

WATER_PUMP_PIN = 19
WATER_PUMP_FREQ_HZ = 10000
WATER_PUMP_FLOW_ML_SEC = 160 # water flow with 100% duty cycle [ml/s]

NUTRIENTS_PUMP_PIN = 18
NUTRIENTS_PUMP_FREQ_HZ = 10000
NUTRIENTS_PUMP_FLOW_ML_SEC = 1.58 # nutrients flow with 100% duty cycle [ml/s]

TRIGGER_BUTTON_PIN = 9

LED_PIN = "LED"

CONSOLE_UART = 0
CONSOLE_TX_PIN = 0
CONSOLE_RX_PIN = 1

class Valve:
    STATUS_CLOSED = 1
    STATUS_OPENED = 2

    DEADTIME_MS = 10

    def __init__(self, console):
        self.closePin = machine.Pin(VALVE_CLOSE_PIN, machine.Pin.OUT, value=0)
        self.openPin = machine.Pin(VALVE_OPEN_PIN, machine.Pin.OUT, value=0)
        self.console = console

    async def close(self):
        self.__disable()
        await asyncio.sleep_ms(Valve.DEADTIME_MS)
        self.closePin.on()

    async def open(self):
        self.__disable()
        await asyncio.sleep_ms(Valve.DEADTIME_MS)
        self.openPin.on()

    async def checkStatus(self):
        openValue = self.openPin.value()
        closeValue = self.closePin.value()
        if (openValue and closeValue):
            self.console.write(f"[ERR] Forbidden valve state detected! Closing.")
            await self.close()
            return Valve.STATUS_CLOSED
        
        if (closeValue and not openValue):
            return Valve.STATUS_CLOSED
        elif (not closeValue and openValue):
            return Valve.STATUS_OPENED
        else:
            # for sanity-check only, should be closed by logic at startup
            self.console.write(f"Changing valve default safe-state to closed.")
            await self.close()
            return Valve.STATUS_CLOSED
    
    def __disable(self):
        self.openPin.off()
        self.closePin.off()

class PwmWrapper():
    DUTY_RAW_MAX_VALUE = 65535
    PERCENT_MAX = 100

    def __init__(self, pwmPin: int, freqHz: int, activeLow: bool = False):
        self.gpio = machine.Pin(pwmPin)
        self.pwm = machine.PWM(self.gpio)
        self.pwm.freq(freqHz)
        self.activeLow = activeLow
        self.setRawValue(0)
    
    def deinit(self):
        if not self.pwm:
            self.pwm.deinit()
        if self.gpio:
            if self.activeLow:
                self.gpio.on()
            else:
                self.gpio.off()

    def setRawValue(self, dutyCycleRaw: int):
        if self.pwm:
            dutyCycleRaw = min(dutyCycleRaw, PwmWrapper.DUTY_RAW_MAX_VALUE)
            if self.activeLow: #for active-low outputs, max value is zero output
                dutyCycleRaw = PwmWrapper.DUTY_RAW_MAX_VALUE - dutyCycleRaw
            self.pwm.duty_u16(dutyCycleRaw)
    
    def setPercentValue(self, dutyCyclePercent: int):
        dutyCyclePercent = min(dutyCyclePercent, PwmWrapper.PERCENT_MAX)
        duty = int((dutyCyclePercent * PwmWrapper.DUTY_RAW_MAX_VALUE) / PwmWrapper.PERCENT_MAX)
        self.setRawValue(duty)

class WaterPump(PwmWrapper):
    def __init__(self):
        super().__init__(WATER_PUMP_PIN, WATER_PUMP_FREQ_HZ)

class NutrientsPump(PwmWrapper):
    def __init__(self):
        super().__init__(NUTRIENTS_PUMP_PIN, NUTRIENTS_PUMP_FREQ_HZ)

class Led(machine.Pin):
    def __init__(self):
        super().__init__(LED_PIN, machine.Pin.OUT)
        self.off()

class Button:
    def __init__(self, pin: int, activeLow: bool = True):
        pull = machine.Pin.PULL_UP if activeLow else machine.Pin.PULL_DOWN
        self.button = machine.Pin(pin, machine.Pin.IN, pull)
        self.activeLow = activeLow

    def isPressed(self):
        value = bool(self.button.value())
        # activeLow = 0 and value = 1
        # OR
        # activeLow = 1 and value = 0
        return bool(self.activeLow ^ value)