import time
import pynput

from .command import Command


class TextInput(Command):
    def __init__(self, text: str = "", time=0):
        super().__init__(f"Text input: {text}", time)
        self.text = text

    def update(self, text: str = None, time: float = None):
        if text:
            self.text = text
        if time:
            self.time = time
        self.name = f"Text input: {self.text}"
    def execute(self, keyboard: pynput.keyboard.Controller):
        keyboard.type(self.text)

    def __dict__(self):
        return {"name": self.name, "type": "textinput", "time": self.time, "text": self.text}
