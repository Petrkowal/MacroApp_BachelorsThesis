import pynput

from .command import Command


class MouseCommand(Command):
    def __init__(self, name, time):
        super().__init__(name, time)

    def execute(self, mouse: pynput.mouse.Controller):
        raise NotImplementedError
