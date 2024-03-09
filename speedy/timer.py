import time
from loguru import logger


class Clock:
    def __init__(self, start_now=True):
        self.start_time = None
        if start_now:
            self.start()

    def start(self):
        self.start_time = time.time()

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
