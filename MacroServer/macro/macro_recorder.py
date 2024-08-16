from dataclasses import dataclass, field

import pynput
import time

from .commands import *


@dataclass
class InputRecorderOptions:
    record_mouse_move: bool = True
    mouse_position_relative: bool = False
    record_mouse_click: bool = True
    record_mouse_scroll: bool = True
    record_keyboard: bool = True
    record_time: bool = True
    time_offset: float = 0.0
    move_timeout: float = 0.05
    callbacks: [callable] = field(default_factory=list)
    mouse_callbacks: [callable] = field(default_factory=list)
    keyboard_callbacks: [callable] = field(default_factory=list)


class InputRecorder:
    def __init__(self, options: InputRecorderOptions):
        self.options = InputRecorderOptions(options.record_mouse_move, options.mouse_position_relative, options.record_mouse_click,
                                            options.record_mouse_scroll, options.record_keyboard, options.record_time, options.time_offset, options.move_timeout,
                                            options.callbacks, options.mouse_callbacks, options.keyboard_callbacks)
        self.start_time = 0
        self.keyboard_listener = None
        self.mouse_listener = None
        self.mouse_origin = None
        self.recorded_events: list[Command] = []
        self.key_to_stop = pynput.keyboard.Key.esc
        self.on_stop_callback = None
        self.current_pos = (None, None)
        self.stop_listener = False
        self.last_move = time.perf_counter()

    def add_callback(self, callback, mouse=False, keyboard=False):
        if mouse:
            self.options.mouse_callbacks.append(callback)
        if keyboard:
            self.options.keyboard_callbacks.append(callback)
        if not mouse and not keyboard:
            self.options.callbacks.append(callback)

    def remove_callback(self, callback):
        if callback in self.options.callbacks:
            self.options.callbacks.remove(callback)
        if callback in self.options.mouse_callbacks:
            self.options.mouse_callbacks.remove(callback)
        if callback in self.options.keyboard_callbacks:
            self.options.keyboard_callbacks.remove(callback)

    def start(self):
        self.stop()
        self.stop_listener = False
        self.recorded_events = []
        self.keyboard_listener = pynput.keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.keyboard_listener.start()
        if self.options.record_mouse_move or self.options.record_mouse_click or self.options.record_mouse_scroll:
            self.mouse_listener = pynput.mouse.Listener(on_move=self.on_move, on_click=self.on_click,
                                                        on_scroll=self.on_scroll)
            self.mouse_listener.start()
        self.mouse_origin = pynput.mouse.Controller().position
        self.start_time = time.perf_counter()

    def resume(self, resume_time):
        self.start()
        self.start_time = resume_time

    def on_press(self, key):
        if key == self.key_to_stop:
            if self.on_stop_callback:
                self.on_stop_callback()
            self.stop_listener = True
            return False

        if self.options.record_keyboard:
            if self.options.record_time:
                dt = time.perf_counter() - self.start_time + self.options.time_offset
            else:
                dt = 0
            event = KeyCommand(key, True, dt)
            self.recorded_events.append(event)
            for callback in self.options.callbacks:
                callback(event)
            for callback in self.options.keyboard_callbacks:
                callback(event)

    def on_release(self, key):
        if self.options.record_time:
            dt = time.perf_counter() - self.start_time + self.options.time_offset
        else:
            dt = 0
        event = KeyCommand(key, False, dt)
        self.recorded_events.append(event)
        for callback in self.options.callbacks:
            callback(event)
        for callback in self.options.keyboard_callbacks:
            callback(event)

    def on_move(self, x, y):
        if not self.options.record_mouse_move:
            return
        if self.stop_listener:
            return False
        if time.perf_counter() - self.last_move < self.options.move_timeout:
            return
        self.last_move = time.perf_counter()

        if self.options.mouse_position_relative:
            x -= self.mouse_origin[0]
            y -= self.mouse_origin[1]

        if self.options.record_time:
            dt = time.perf_counter() - self.start_time + self.options.time_offset
        else:
            dt = 0
        event = MouseMove(x, y, not self.options.mouse_position_relative, dt)
        self.recorded_events.append(event)
        for callback in self.options.callbacks:
            callback(event)
        for callback in self.options.mouse_callbacks:
            callback(event)

    def on_click(self, x, y, btn, press):
        if not self.options.record_mouse_click:
            return
        if self.stop_listener:
            return False

        if self.options.mouse_position_relative:
            x -= self.mouse_origin[0]
            y -= self.mouse_origin[1]

        if self.options.record_time:
            dt = time.perf_counter() - self.start_time + self.options.time_offset
        else:
            dt = 0
        event = MouseClick(btn, press, x, y, True, dt)
        self.recorded_events.append(event)
        for callback in self.options.callbacks:
            callback(event)
        for callback in self.options.mouse_callbacks:
            callback(event)

    def on_scroll(self, x, y, dx, dy):
        if not self.options.record_mouse_scroll:
            return
        if self.stop_listener:
            return False

        if self.options.record_time:
            dt = time.perf_counter() - self.start_time + self.options.time_offset
        else:
            dt = 0
        event = MouseScroll(dx, dy, dt)
        self.recorded_events.append(event)
        for callback in self.options.callbacks:
            callback(event)
        for callback in self.options.mouse_callbacks:
            callback(event)

    def stop(self, no_join=False):
        self.stop_listener = True
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        if no_join:
            return
        self.join()

    def join(self):
        if self.keyboard_listener:
            self.keyboard_listener.join()
        if self.mouse_listener:
            self.mouse_listener.join()
        self.keyboard_listener = None
        self.mouse_listener = None

    def get_events(self):
        return self.recorded_events
