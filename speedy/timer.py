import time
from loguru import logger
__all__ = ['Clock']

class Clock:
    def __init__(self, start_now=True):
        self.start_time = None
        self.time_table = {}
        if start_now:
            self.start()
        self.pbar_counter = 0
        self.last_print = time.time()

    def start(self):
        self.start_time = time.time()
        self.last_check = self.start_time

    def since_start(self):
        if self.start_time is None:
            raise ValueError("Clock has not been started.")
        return time.time() - self.start_time

    def log(self, custom_logger=None):
        msg = "Time elapsed: {:.2f} seconds.".format(self.since_start())
        if custom_logger:
            custom_logger(msg)
        else:
            logger.info(msg)

    def since_last_check(self):
        now = time.time()
        elapsed = now - self.last_check
        self.last_check = now
        return elapsed

    def update(self, name):
        if not name in self.time_table:
            self.time_table[name] = 0
        self.time_table[name] += self.since_last_check()

    def print_table(self, every=1):
        now = time.time()
        if now - self.last_print > every:
            self.pbar_counter += 1
            total_time = sum(self.time_table.values())
            desc = "Time table: "
            for name, t in self.time_table.items():
                percentage = (t / total_time) * 100
                desc += "{}: {:.2f}%, {}s".format(name, percentage, t)
            print(desc)
            self.last_print = now
