from dataclasses import dataclass

import json
from os.path import exists, join, expanduser
from typing import Optional

from src.blockchain.keys import PrivateKey, PublicKey
from src.blockchain.tools import MetaSingleton
from src.blockchain.credentials import PUBLIC_KEY, PRIVATE_KEY
import sys
from enum import Enum
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

gth_config_folder = expanduser("~/.gth")

config_file_path: Optional[str] = join(
    gth_config_folder,
    'config.json'
) if exists(join(gth_config_folder, 'credentials')) else None
config_file_path = config_file_path or ('./config.json' if exists('./config.json') else None)

LIMIT_TRANSACTIONS_BLOCK = 1


class NodeType(Enum):
    ALL = 'all'
    MINER = 'miner'
    MANAGER = 'manager'
    UNKNOWN = 'UNKNOWN'


class Host(metaclass=MetaSingleton):
    def __init__(self):
        self._host = None
        self._type = None
        self._port = None

    @property
    def host(self):
        return f'http://<unknown>:{self._port}' if self._host is None else f'http://{self._host}'

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
        logger.warning("Host destroyed")


@dataclass
class Config:
    nodes: list
    type: NodeType
    port: int
    authorized_nodes_pbk: list

    @classmethod
    def from_file(cls, file):
        raw_cfg = json.load(open(file, 'r'))
        raw_cfg['type'] = NodeType(raw_cfg['type'])
        return cls(**raw_cfg)
