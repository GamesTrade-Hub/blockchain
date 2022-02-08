from src.tools import MetaSingleton

import sys


class Host(metaclass=MetaSingleton):
    def __init__(self):
        self._host = None

    @property
    def host(self):
        print("return host being", self._host)
        return f'http://{self._host}'

    @host.setter
    def host(self, host):
        if self._host is not None:
            return
        print('set host being', self._host)
        self._host = host

    def __del__(self):
        print("host destroyed", file=sys.stderr)
