from src.tools import MetaSingleton
import sys
from enum import Enum


class NodeType(Enum):
    ALL = 'all'
    MINER = 'miner'
    MANAGER = 'manager'


class Host(metaclass=MetaSingleton):
    def __init__(self):
        self._host = None
        self._type = None

    @property
    def host(self):
        print("return host being", self._host)
        return f'http://{self._host}'

    @host.setter
    def host(self, host):
        if self._host is not None:
            return
        self._host = host

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type_):
        if isinstance(type_, NodeType) and self._type is None:
            self._type = type_

    def __del__(self):
        print("host destroyed", file=sys.stderr)
