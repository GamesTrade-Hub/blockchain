from dataclasses import dataclass
import os
import json
from os.path import exists, join, expanduser
from typing import Optional

from src.blockchain.keys import PublicKeyContainer, PrivateKey
from src.blockchain.tools import MetaSingleton
from enum import Enum
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger.setLevel(logging.DEBUG)
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)


"""
Priority to get config file:
1. Config file in home (~/.gth/) directory
2. Config file in current directory

The name of the config file is "config.json" or specified by the environment variable "GTH_CONFIG"
"""

gth_config_folder = expanduser("~/.gth")
config_file_name = (
    os.environ["GTH_CONFIG"] if "GTH_CONFIG" in os.environ else "configs/dev.config.json"
)

config_file_path: Optional[str] = (
    join(gth_config_folder, config_file_name)
    if exists(join(gth_config_folder, config_file_name))
    else join("./", config_file_name)
    if exists(join("./", config_file_name))
    else None
)
logger.debug(f"config file path: {config_file_path}")

LIMIT_TRANSACTIONS_BLOCK = 1


class NodeType(Enum):
    ALL = "all"
    MINER = "miner"
    MANAGER = "manager"
    UNKNOWN = "UNKNOWN"


class Host(metaclass=MetaSingleton):
    def __init__(self):
        self._host = None
        self._type = None
        self._port = None

    @property
    def host(self):
        return (
            f"http://<unknown>:{self._port}"
            if self._host is None
            else f"http://{self._host}"
        )

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
    public_key: PublicKeyContainer
    private_key: PrivateKey

    @classmethod
    def from_file(cls, file):
        raw_cfg = json.load(open(file, "r"))
        raw_cfg["type"] = NodeType(raw_cfg["type"])
        raw_cfg["public_key"] = PublicKeyContainer(raw_cfg["public_key"])
        raw_cfg["private_key"] = PrivateKey(raw_cfg["private_key"])
        return cls(**raw_cfg)


conf: Config = Config.from_file(config_file_path)
PRIVATE_KEY: PrivateKey = conf.private_key
PUBLIC_KEY: PublicKeyContainer = conf.public_key
logger.debug(f"{PUBLIC_KEY.is_valid()=}")

assert PUBLIC_KEY.is_valid(), "Invalid keys"

