import pynput
from typing import Union

from .command import Command


class KeyCommand(Command):
    def __init__(self, key: Union[pynput.keyboard.Key, pynput.keyboard.KeyCode] = None, press: bool = True, time=0.0):
        if not key:
            name = f"Key {'press' if press else 'release'}"
            key = pynput.keyboard.Key.space
            keyname = " "
        else:
            if isinstance(key, pynput.keyboard.KeyCode):
                keyname = chr(key.vk) if 32 <= key.vk <= 126 else str(key.vk)
            elif isinstance(key, pynput.keyboard.Key):
                keyname = key.name
            else:
                raise ValueError(f"Unknown key type: {key}")
            name = f"Key {keyname} {'press' if press else 'release'}"
        super().__init__(name, time)
        self.keyname = keyname
        self.key = key
        self.press = press

    def update(self, key: Union[pynput.keyboard.Key, pynput.keyboard.KeyCode] = None, press: bool = None, time: float = None):
        if key:
            self.key = key
            if isinstance(key, pynput.keyboard.KeyCode):
                self.keyname = key.char if key.char else key.vk
            elif isinstance(key, pynput.keyboard.Key):
                self.keyname = key.name
        if press is not None:
            if isinstance(press, bool):
                self.press = press
        if time:
            self.time = time
        key_str = f"{self.keyname} " if self.key else ""
        self.name = f"Key {key_str}{'press' if self.press else 'release'}"

    def execute(self, keyboard: pynput.keyboard.Controller):
        if self.press:
            keyboard.press(self.key)
        else:
            keyboard.release(self.key)

    def __dict__(self):
        if isinstance(self.key, pynput.keyboard.KeyCode):
            k, v = "keycode", self.key.vk
        elif isinstance(self.key, pynput.keyboard.Key):
            k, v = "key", self.key.name
        else:
            raise ValueError(f"Unknown key type: {self.key}")
        return {"name": self.name, "type": "key", "time": self.time, "keytype": k, "value": v, "press": self.press}
