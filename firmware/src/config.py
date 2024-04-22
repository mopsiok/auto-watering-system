try:
    import ujson as json
except:
    import json

class Config:
    def __init__(self, jsonPath: str, defaultConfig: dict, console, precheckCallback = None, toStringCallback = None):
        #TODO abstract class for default config and callbacks will be a good option for future
        self.jsonPath = jsonPath
        self.config = defaultConfig.copy()
        self.console = console
        self.precheckCallback = precheckCallback
        self.toStringCallback = toStringCallback
        self.load()

    def precheck(self, config: dict):
        return (self.precheckCallback == None) or (self.precheckCallback(config))
    
    def print(self):
        if self.toStringCallback:
            self.console.write(self.toStringCallback(self.config))

    def load(self):
        try:
            with open(self.jsonPath, 'r') as f:
                tmp = json.loads(f.read())
                if self.precheck(tmp):
                    self.config = tmp.copy()
                else:
                    self.console.write("Prechecks failed, loading default config")
        except Exception as error:
            self.console.write("No valid file found, saving default config")
            self.save()
        self.console.write(f"Loaded config")
        self.print()

    def save(self):
        if not self.precheck(self.config):
            self.console.write("Prechecks failed, saving aborted")
            return
        try:
            with open(self.jsonPath, 'w') as f:
                f.write(json.dumps(self.config))
        except Exception as error:
            self.console.write("Error during saving config")
