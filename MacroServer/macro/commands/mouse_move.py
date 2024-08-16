import pynput

from .mouse_command import MouseCommand


class MouseMove(MouseCommand):
    def __init__(self, x: int = 0, y: int = 0, absolute: bool = True, time=0):
        if absolute:
            name = f"Mouse Move to {x}, {y}"
        else:
            name = f"Mouse Move by {x}, {y}"
        super().__init__(name, time)
        self.x = x
        self.y = y
        self.absolute = absolute

    def update(self, x: int = None, y: int = None, absolute: bool = None, time=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if absolute is not None:
            self.absolute = absolute
        if time:
            self.time = time
        self.name = f"Mouse Move to {self.x}, {self.y}" if self.absolute else f"Mouse Move by {self.x}, {self.y}"

    def execute(self, mouse: pynput.mouse.Controller):
        if self.absolute:
            mouse.position = (self.x, self.y)
        else:
            mouse.move(self.x, self.y)

    def __dict__(self):
        return {"name": self.name,
                "type": "move",
                "time": self.time,
                "x": self.x,
                "y": self.y,
                "absolute": self.absolute}
