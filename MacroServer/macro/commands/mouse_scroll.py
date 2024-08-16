import pynput
import time
from typing import Union

from .mouse_command import MouseCommand


class MouseScroll(MouseCommand):
    def __init__(self, x: int = 0, y: int = 0, time=0):
        super().__init__(f"Mouse Scroll {x}, {y}", time)
        self.x = x
        self.y = y

    def update(self, x: int = None, y: int = None, time=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if time:
            self.time = time
        self.name = f"Mouse Scroll {self.x}, {self.y}"

    def execute(self, mouse: pynput.mouse.Controller):
        mouse.scroll(self.x, self.y)

    def __dict__(self):
        return {"name": self.name,
                "type": "scroll",
                "time": self.time,
                "x": self.x,
                "y": self.y}
