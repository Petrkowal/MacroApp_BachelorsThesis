import os
import threading

from .commands import *

import pynput.keyboard
import pynput.mouse
import time
import json


class Macro:
    def __init__(self, name, description, commands: list[Command], repeat, position, timing):
        self.macro_id = ""
        self.name = name
        self.set_name(name)
        self.description = description
        self.commands = commands.copy()
        self.repeat = repeat
        self.timing = timing
        self.exit = False
        self.position = position
        self.keys_held_down = set()
        self.btns_held_down = set()
        self.keys_lock = threading.Lock()

    def release_all_keys(self, keyboard: pynput.keyboard.Controller):
        with self.keys_lock:
            for key in self.keys_held_down:
                keyboard.release(key)

    def release_all_btns(self, mouse: pynput.mouse.Controller):
        for btn in self.btns_held_down:
            mouse.release(btn)

    def add_to_held_keys(self, key):
        with self.keys_lock:
            self.keys_held_down.add(key)

    def rem_from_held_keys(self, key):
        with self.keys_lock:
            self.keys_held_down.remove(key)

    def execute(self):
        self.exit = False
        if not self.commands:
            if not self.load_commands():
                return "error"

        keyboard = pynput.keyboard.Controller()
        mouse = pynput.mouse.Controller()
        for i in range(self.repeat):
            start_time = time.perf_counter()
            for command in self.commands:
                if self.exit:
                    break
                if self.timing:
                    total_time = time.perf_counter() - start_time
                    if command.time > total_time:
                        time.sleep(command.time - total_time)

                    if self.exit:
                        break

                self.dispatch_command(command, keyboard, mouse)

        self.release_all_keys(keyboard)
        self.release_all_btns(mouse)
        return "success" if not self.exit else "stopped"

    def dispatch_command(self, command, keyboard, mouse):
        if isinstance(command, KeyCommand):
            command.execute(keyboard)
            if command.press:
                self.add_to_held_keys(command.key)
            else:
                if command.key in self.keys_held_down:
                    self.rem_from_held_keys(command.key)
        elif isinstance(command, TextInput):
            command.execute(keyboard)
        elif isinstance(command, MouseCommand):
            if isinstance(command, MouseClick):
                if command.press:
                    self.btns_held_down.add(command.button)
                else:
                    if command.button in self.btns_held_down:
                        self.btns_held_down.remove(command.button)
            command.execute(mouse)
        else:
            command.execute()

    def stop(self):
        self.exit = True

    def save(self, path="macros/", overwrite=False, only_info=False):
        self.set_name(self.name)
        try:
            if not path.endswith("/"):
                path += "/"
            path += f"{self.macro_id}.json"
            if os.path.exists(path) and not overwrite:
                return
            dct = self.__dict__()
            commands = {"commands": dct["commands"]}
            dct.pop("commands")
            macro_dump = json.dumps(dct)
            commands_dump = json.dumps(commands)
            with open(path, "w") as file:
                file.write(macro_dump)
            if not only_info:
                with open(f"{path[:-5]}.commands.json", "w") as file:
                    file.write(commands_dump)

        except Exception as e:
            print(f"Error saving macro: {e}")

    def load_commands(self):
        macro = Macro.load(f"macros/{self.macro_id}")
        if not macro:
            return False
        self.commands = macro.commands.copy()
        if not self.commands:
            return False
        return True

    @staticmethod
    def load(path):
        try:
            if not path.endswith(".json"):
                path += ".json"
            with open(path, "r") as file:
                dump_macro = file.read()
            with open(f"{path[:-5]}.commands.json", "r") as file:
                dump_commands = file.read()
            macro_json = json.loads(dump_macro)
            macro_commands_json = json.loads(dump_commands)
            commands = []
            for command in macro_commands_json["commands"]:
                if command["type"] == "key":
                    if command["keytype"] == "keycode":
                        key = pynput.keyboard.KeyCode.from_vk(command["value"])
                    elif command["keytype"] == "key":
                        key = getattr(pynput.keyboard.Key, command["value"])
                    else:
                        raise ValueError(f"Unknown key type: {command['keytype']}")
                    # key = pynput.keyboard.KeyCode.from_vk(command["key"])
                    commands.append(KeyCommand(key, command["press"], command["time"]))
                elif command["type"] == "delay":
                    commands.append(Delay(command["delay"], command["time"]))
                elif command["type"] == "click":
                    btn_values = command["button"]
                    # make tuple from btn_values
                    btn_tuple = (btn_values[0], btn_values[1], btn_values[2])
                    button = pynput.mouse.Button(btn_tuple)
                    commands.append(
                        MouseClick(button, command["press"], command["x"], command["y"], command["absolute"],
                                   command["time"]))
                elif command["type"] == "move":
                    commands.append(MouseMove(command["x"], command["y"], command["absolute"], command["time"]))
                elif command["type"] == "scroll":
                    commands.append(MouseScroll(command["x"], command["y"], command["time"]))
                elif command["type"] == "textinput":
                    commands.append(TextInput(command["text"], command["time"]))
                else:
                    print(f"Unknown command type: {command['type']}")
            fname = os.path.basename(path)
            fname = fname.split(".")[0]
            macro = Macro(macro_json["name"], macro_json["description"], commands, macro_json["repeat"],
                          macro_json["position"], macro_json["timing"])
            return macro

        except FileNotFoundError:
            print(f"File not found: {path}")
            return None

    def set_name(self, name):
        try:
            self.name = name
            self.macro_id = name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*",
                                                                                                                  "_").replace(
                "?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
            self.macro_id = ''.join(e for e in self.macro_id if e.isalnum() or e == "_")
        except Exception as e:
            print(f"Error setting name: {e}")

    def set_description(self, description):
        self.description = description

    def set_repeat(self, repeat):
        self.repeat = repeat

    def get_position(self):
        return self.position

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    @staticmethod
    def get_all_macros_info():
        macros_info = []
        for file in os.listdir("macros"):
            if file.endswith(".json") and not file.endswith(".commands.json"):
                try:
                    with open(f"macros/{file}", "r") as f:

                        macro_json = json.loads(f.read())
                        macros_info.append({"name": macro_json["name"], "description": macro_json["description"],
                                            "position": macro_json["position"], "repeat": macro_json["repeat"],
                                            "macro_id": file[:-5], "timing": macro_json["timing"]})
                except Exception as e:
                    print(f"Could not read file {file}: {e}")
                    continue
        return {"macro_list": macros_info}

    @staticmethod
    def get_all_macros_info_objects():
        macros_info = Macro.get_all_macros_info()
        macros = []
        for macro in macros_info["macro_list"]:
            tmp = Macro(macro["name"], macro["description"], [], macro["repeat"], macro["position"], macro["timing"])
            macros.append(tmp)
        return macros

    def delete(self):
        try:
            if os.path.exists(f"macros/{self.macro_id}.json"):
                os.remove(f"macros/{self.macro_id}.json")
            if os.path.exists(f"macros/{self.macro_id}.commands.json"):
                os.remove(f"macros/{self.macro_id}.commands.json")
        except Exception as e:
            print(f"Error deleting macro: {e}")

    def __dict__(self):
        return {"name": self.name, "description": self.description, "repeat": self.repeat, "position": self.position,
                "commands": [c.__dict__() for c in self.commands], "timing": self.timing}
