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
        self._port = None

    @property
    def host(self):
        return None if self._host is None else f'http://{self._host}'

    @host.setter
    def host(self, host):
        if self._host is not None:
            return
        self._host = host

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        if self._port is not None:
            return
        self._port = port

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type_):
        if isinstance(type_, NodeType) and self._type is None:
            self._type = type_

    def __del__(self):
        print("host destroyed", file=sys.stderr)
