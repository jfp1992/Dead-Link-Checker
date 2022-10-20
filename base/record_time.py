import time

from base.custom_logging import xlogging


class RecordTime:
    def __init__(self, benched_module):
        """RecordTime:
        Use: .start to start the timer
        Use: .stop to stop the timer and log time taken
        :param benched_module: lower case string to identify code block execution time for logging purposes"""
        self.start_time = None
        self.stop_time = None
        self.benched_module = benched_module
        self.freeze_time = 0

    def start(self):
        """Gets an instance of datetime
        Put this before an action - to be used with stop_timer function
        :return: void"""
        self.start_time = time.perf_counter()

    def stop(self):
        """Gets an instance of datetime
        Put this after an action - to be used with start_timer function
        :return: void"""
        self.stop_time = time.perf_counter()
        self.freeze_time = round(self.stop_time, 2) - round(self.start_time, 2)
        return [self.freeze_time, f"{self.benched_module} finished in {self.freeze_time} second(s)"]
