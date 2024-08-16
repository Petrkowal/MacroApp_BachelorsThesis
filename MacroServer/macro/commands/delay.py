import time

from .command import Command


class Delay(Command):
    def __init__(self, delay=0.1, time=0):
        delay = round(delay, 3)
        super().__init__(f"Delay {delay}", time)
        self.delay = delay

    def update(self, delay=None, time=None):
        if delay is not None:
            delay = round(delay, 3)
            self.delay = delay
        if time:
            self.time = time
        self.name = f"Delay {self.delay}"

    def execute(self, controller=None):
        time.sleep(self.delay)

    def __dict__(self):
        return {"name": self.name, "type": "delay", "time": self.time, "delay": self.delay}
