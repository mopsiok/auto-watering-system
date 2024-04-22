import uasyncio as asyncio

class Logic:
    #TODO make it a config
    WATERING_TIME_SEC = 60
    WATERING_CYCLE_PERIOD_SEC = 3600

    WATERING_STATUS_IDLE = 0
    WATERING_STATUS_OPENING = 1
    WATERING_STATUS_ONGOING = 2
    WATERING_STATUS_CLOSING = 3

    def __init__(self, valve, waterPump, nutrientsPump, console):
        self.uptime = 0
        self.lastWateringUptime = 0
        self.wateringCyclesCount = 0

        self.wateringTriggers = [self.__periodicTrigger, ]
        self.wateringStatus = self.WATERING_STATUS_IDLE
        self.triggerAtStartup = True
        
        self.valve = valve
        self.waterPump = waterPump
        self.nutrientsPump = nutrientsPump
        self.console = console

    def addWateringTrigger(self, triggerCallback):
        self.wateringTriggers.append(triggerCallback)

    async def runTask(self):
        await self.valve.close()
        while True:
            await asyncio.sleep(1)
            self.uptime += 1
            await self.__handleWatering()

    def __periodicTrigger(self):
        if self.uptime >= (self.lastWateringUptime + self.WATERING_CYCLE_PERIOD_SEC):
            self.console.write("Periodic trigger.")
            return True
        if self.triggerAtStartup:
            self.console.write("Startup trigger.")
            self.triggerAtStartup = False
            return True
        return False

    async def __handleWatering(self):
        if (self.wateringStatus == self.WATERING_STATUS_IDLE) and self.__checkTriggers():
            self.console.write("Trigger detected, running single watering cycle.")
            self.wateringStatus = self.WATERING_STATUS_OPENING
    
        if self.wateringStatus == self.WATERING_STATUS_OPENING:
            self.lastWateringUptime = self.uptime
            self.wateringCyclesCount += 1
            self.console.write("Opening the valve.")
            await self.valve.open()
            self.wateringStatus = self.WATERING_STATUS_ONGOING

        if self.wateringStatus == self.WATERING_STATUS_ONGOING:
            if self.uptime >= self.lastWateringUptime + self.WATERING_TIME_SEC:
                self.wateringStatus = self.WATERING_STATUS_CLOSING

        if self.wateringStatus == self.WATERING_STATUS_CLOSING:
            self.console.write("Closing the valve.")
            await self.valve.close()
            self.wateringStatus = self.WATERING_STATUS_IDLE

    def __checkTriggers(self):
        result = False
        for trigger in self.wateringTriggers:
            if trigger():
                # don't exit early, update all triggers on the list
                result = True
        return result