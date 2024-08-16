import pynput

from .mouse_command import MouseCommand


class MouseClick(MouseCommand):
    def __init__(self, button: pynput.mouse.Button = None, press: bool = True, x: int = 0, y: int = 0, absolute: bool = True,
                 time=0):
        if button is None:
            button = pynput.mouse.Button.left
        name = f"Mouse {'press' if press else 'release'} {button}"
        if absolute:
            name += f" at {x}, {y}"
        else:
            name += f" by {x}, {y}"
        super().__init__(name, time)
        self.button = button
        self.press = press
        self.x = x
        self.y = y
        self.absolute = absolute

    def update(self, x: int = None, y: int = None, press: bool = None, button: pynput.mouse.Button = None, time=None, absolute=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if press is not None:
            self.press = press
        if button is not None:
            self.button = button
        if time is not None:
            self.time = time
        if absolute is not None:
            self.absolute = absolute

        self.name = f"Mouse {'press' if self.press else 'release'} {self.button}"
        if self.absolute:
            self.name += f" at {self.x}, {self.y}"
        else:
            self.name += f" by {self.x}, {self.y}"

    def execute(self, mouse: pynput.mouse.Controller):
        if self.absolute:
            mouse.position = (self.x, self.y)
        else:
            mouse.move(self.x, self.y)
        if self.press:
            mouse.press(self.button)
        else:
            mouse.release(self.button)

    def __dict__(self):
        return {"name": self.name,
                "type": "click",
                "time": self.time,
                "button": self.button.value,
                "press": self.press,
                "x": self.x,
                "y": self.y,
                "absolute": self.absolute}
