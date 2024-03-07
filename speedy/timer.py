import time

class Clock:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def since_start(self):
        if self.start_time is None:
            raise ValueError("Clock has not been started.")
        return time.time() - self.start_time