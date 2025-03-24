import uasyncio as asyncio
from bsp import *

class Logic:
    STATUS_IDLE = 0
    STATUS_VALVE_CLOSING = 1
    STATUS_PUMPS_RUNNING = 2
    STATUS_VALVE_OPENING = 3

    def __init__(self, valve: Valve, waterPump: WaterPump, nutrientsPump: NutrientsPump, config: dict, console):
        self.uptime = 0
        self.wateringCount = 0

        self.wateringTriggers = [self.__periodicTrigger, ]
        self.lastTriggerUptime = 0
        self.triggerAtStartup = True
        self.status = self.STATUS_IDLE
        
        self.valve = valve
        self.waterPump = waterPump
        self.nutrientsPump = nutrientsPump
        self.config = config
        self.console = console

    def addWateringTrigger(self, triggerCallback):
        self.wateringTriggers.append(triggerCallback)

    async def runTask(self):
        await self.valve.open()
        while True:
            await asyncio.sleep(1)
            self.uptime += 1
            await self.__handleWatering()

    def __periodicTrigger(self):
        if self.uptime >= (self.lastTriggerUptime + self.config['periodic_watering_offline_cycle_s']):
            self.console.write("Periodic trigger.")
            return True
        if self.triggerAtStartup: #TODO remove when new flow is finished
            self.console.write("Startup trigger.")
            self.triggerAtStartup = False
            return True
        return False

    async def __handleWatering(self):
        if (self.status == self.STATUS_IDLE) and self.__checkTriggers():
            self.console.write("Trigger detected, running single watering cycle. Closing the valve.")
            await self.valve.close()
            self.statusTimestamp = self.uptime
            self.status = self.STATUS_VALVE_CLOSING
    
        if self.status == self.STATUS_VALVE_CLOSING:
            if self.uptime >= self.statusTimestamp + self.config['valve_closing_time_s']:
                waterPercent = self.config['water_pump_duty_percent']
                nutrientsPercent = self.config['nutrients_pump_duty_percent']
                self.console.write(f"Starting water ({waterPercent}%) and nutrient ({nutrientsPercent}%) pumps")
                self.waterPump.setPercentValue(waterPercent)
                self.nutrientsPump.setPercentValue(nutrientsPercent)
                self.statusTimestamp = self.uptime
                self.status = self.STATUS_PUMPS_RUNNING

        if self.status == self.STATUS_PUMPS_RUNNING:
            waterPumpFinished = self.uptime >= self.statusTimestamp + self.config['water_pump_time_s']
            nutrientsTimeDelta = round(self.config['nutrients_pump_volume_ml'] * self.config['nutrients_pump_duty_percent'] / NUTRIENTS_PUMP_FLOW_ML_SEC / 100)
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
        result = False
        for trigger in self.wateringTriggers:
            if trigger():
                # don't exit early, update all triggers on the list
                result = True
        if result:
            self.lastTriggerUptime = self.uptime
            self.wateringCount += 1
        return result