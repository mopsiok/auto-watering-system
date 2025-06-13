import uasyncio as asyncio
from bsp import *
from config import *
from WateringController import WateringController
import mytime

class Logic:
    STATUS_IDLE = 0
    STATUS_VALVE_CLOSING = 1
    STATUS_PUMPS_RUNNING = 2
    STATUS_VALVE_OPENING = 3

    def __init__(self, console):
        self.uptime = 0
        self.wateringCount = 0

        self.manualTriggerFlag = False
        self.lastTriggerUptime = 0
        self.status = self.STATUS_IDLE
        
        self.valve = Valve(console)
        self.waterPump = WaterPump()
        self.nutrientsPump = NutrientsPump()
        self.controlConfig = ControlConfig(console)
        self.hwConfig = HwConfig(console)

        liters_per_event = 4.0 #TODO calculate based on hw config and bsp
        self.controllerPrescalerCounter = 0 #TODO to be removed when triggering logic changes
        self.controller = WateringController(self.controlConfig.values["setpoint"],
                                             liters_per_event,
                                             self.controlConfig.values["deadtime_sec"],
                                             self.controlConfig.values["watering_windows"],
                                             self.controlConfig.values["time_window_days"],
                                             self.controlConfig.values["kp"],
                                             self.controlConfig.values["ki"],
                                             self.controlConfig.values["kd"],
                                             self.controlConfig.values["kimax"],
                                             self.controlConfig.values["kidec"])
        self.console = console
        asyncio.create_task(self.runTask())

    def manualTrigger(self):
        self.manualTriggerFlag = True

    async def runTask(self):
        await self.valve.open()
        while True:
            await asyncio.sleep(1)
            self.uptime += 1
            await self.__handleWatering()

    def __controllerTrigger(self):
        # Triggers single water cycle based on given average water volume poured daily
        # Only triggers within specific time window, and only when time is synchronized with external source
        # Also accounts for dead-time for better water absorption

        if self.__shouldRunSingleIteration():
            t = mytime.getCurrentSeconds()
            should_water, _ = self.controller.run_single_iteration(t)
            return should_water
        return False

    async def __handleWatering(self):
        if (self.status == self.STATUS_IDLE) and self.__checkTriggers():
            self.console.write("Trigger detected, running single watering cycle. Closing the valve.")
            await self.valve.close()
            self.statusTimestamp = self.uptime
            self.status = self.STATUS_VALVE_CLOSING
    
        if self.status == self.STATUS_VALVE_CLOSING:
            if self.uptime >= self.statusTimestamp + self.hwConfig.values['valve_closing_time_s']:
                waterPercent = self.hwConfig.values['water_pump_duty_percent']
                nutrientsPercent = self.hwConfig.values['nutrients_pump_duty_percent']
                self.console.write(f"Starting water ({waterPercent}%) and nutrient ({nutrientsPercent}%) pumps")
                self.waterPump.setPercentValue(waterPercent)
                self.nutrientsPump.setPercentValue(nutrientsPercent)
                self.statusTimestamp = self.uptime
                self.status = self.STATUS_PUMPS_RUNNING

        if self.status == self.STATUS_PUMPS_RUNNING:
            waterPumpFinished = self.uptime >= self.statusTimestamp + self.hwConfig.values['water_pump_time_s']
            nutrientsTimeDelta = round(self.hwConfig.values['nutrients_pump_volume_ml'] * self.hwConfig.values['nutrients_pump_duty_percent'] / NUTRIENTS_PUMP_FLOW_ML_SEC / 100)
            nutrientsPumpFinished = self.uptime >= self.statusTimestamp + nutrientsTimeDelta
            if waterPumpFinished:
                self.waterPump.setPercentValue(0)
            if nutrientsPumpFinished:
                self.nutrientsPump.setPercentValue(0)
            if waterPumpFinished and nutrientsPumpFinished:
                self.console.write("Opening the valve")
                await self.valve.open()
                self.status = self.STATUS_VALVE_OPENING

        if self.status == self.STATUS_VALVE_OPENING:
            self.console.write("Watering cycle finished")
            self.status = self.STATUS_IDLE

    def __checkTriggers(self):
        if (self.__controllerTrigger() or self.manualTriggerFlag):
            self.manualTriggerFlag = False
            self.lastTriggerUptime = self.uptime
            self.wateringCount += 1
            return True
        return False
    
    def __shouldRunSingleIteration(self):
        # check whether time is synchronised and allow to execute every full minute
        # just after startup, the default datetime for this HW is around 01.01.2021
        # this hack quickly determines whether the time is synchronized
        dateTime = mytime.getCurrentDateTime()
        currentYear = dateTime[0]
        currentSecond = dateTime[6]
        return (currentYear >= 2025) and (currentSecond == 0)
