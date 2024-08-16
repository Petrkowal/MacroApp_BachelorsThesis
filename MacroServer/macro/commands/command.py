class Command:

    def __init__(self, name, time):
        self.name = name
        self.time = time

    def execute(self):
        raise NotImplementedError

    def __str__(self, controller=None):
        return f"{self.name} at {self.time}"

    def __repr__(self):
        return f"{self.name} at {self.time}"

    def __dict__(self):
        return {"name": self.name, "time": self.time}
