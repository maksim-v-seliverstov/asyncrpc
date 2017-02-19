import time
from collections import OrderedDict


class Cleaner:

    def __init__(self, clear_timeout=60):
        self.data = OrderedDict()

        self.monitoring_timeout = clear_timeout / 2

        self.__start_ts = None
        self.__finish_ts = None
        self.__clear_count = 0

    def popleft(self, count):
        for _ in range(count):
            _, v = self.data.popitem(last=False)
            v.clear()
        self.__start_ts = None
        self.__finish_ts = None

    def try_clear(self):
        if self.__start_ts is None:
            self.__start_ts = time.perf_counter()
            return

        if time.perf_counter() - self.__start_ts > self.monitoring_timeout and self.__finish_ts is None:
            self.__finish_ts = time.perf_counter()
            self.__clear_count = len(self.data)
            return

        if self.__finish_ts and time.perf_counter() - self.__finish_ts > self.monitoring_timeout:
            self.popleft(self.__clear_count)
            self.__start_ts = None
            self.__finish_ts = None
            return
