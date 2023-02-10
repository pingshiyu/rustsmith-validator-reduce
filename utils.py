import string
import random
import time

SECONDS_IN_MINUTE = 60

def random_str(size : int = 32, chars : str = string.ascii_letters+string.digits) -> str:
    """
    Gets one of the (26 * 2 + 10)^16 ~ O(10^28) possible strings
    """
    return ''.join(random.choice(chars) for _ in range(size))

class timeout(object):
    """
    Courtesy of https://stackoverflow.com/a/15190306
    """

    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        self.start_time = time.time()
        self.death_time = self.start_time + self.seconds
        return self

    def __exit__(self, type, value, traceback):
        pass

    @property
    def timed_out(self):
        return time.time() > self.death_time

    @property
    def remaining(self):
        return self.death_time - time.time()

    @property
    def elapsed(self):
        return time.time() - self.start_time