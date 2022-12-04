import time
from typing import List, Optional, Iterator, Union

import threading

from src.blockchain.chain import Chain
from src.blockchain.config import Host, NodeType
from src.blockchain.tools import post, get
from requests import Session
import json
from urllib.parse import urlparse
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger.setLevel(logging.DEBUG)
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)


def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        logger.info("Start thread")
        t.start()
        return t

    return run


class NodesList:
    def __init__(self):
        self.nodes: List[Node] = list()

    def __str__(self):
        return ", ".join(n.__str__() for n in self.nodes)

    def __dict__(self):
        return {"nodes": [f"http://{str(i)}" for i in self.nodes]}

    def spread_new_node(self, address, type_):
        for node in self.nodes:
            node.register(address, type_)

    def spread_transaction(self, tx):
        for node in self.nodes:
            node.send_transaction(tx)

    def add_node(self, address: str, type_: Optional[str] = None, register_back: bool = False, spread: bool = False) -> bool:
        """
        Add a node to the list of nodes if valid and not already in the list.
        :param address: address of the node such as "localhost:5000"
        :param type_: type of the node such as "miner" or "manager"
        :param register_back: whether to call back the node to register itself
        :param spread: whether to spread the node to the other nodes
        :return: True if the node was added, False otherwise
        """
        host = self.parse_address(address)
        if host is None:
            logger.error("Host is None")
            return False

        if host in self.__str__():
            logger.warning(f"Node host {host} already registered")
            return False

        node = Node(host, type_)

        if node.type == NodeType.UNKNOWN:
            logger.warning(f"Invalid node type for address: {address} host {host}")
            return False

        if spread:
            self.spread_new_node(address, node.type.value)
        logger.info(f"Add node {node} in node list")
        self.nodes.append(node)
        if register_back:
            node.register_back(spread=len(self.nodes) == 1)
            return True
        return True

    def parse_address(self, address: str) -> Optional[str]:
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            host = parsed_url.netloc
        elif parsed_url.path:
            if parsed_url.scheme:
                host = parsed_url.scheme + ":" + parsed_url.path
            else:
                host = parsed_url.path
        else:
            logger.warning(f"parseAddress cannot parse: {address}")
            return None
        return host

    def others_chains(self) -> Iterator[Union[Chain, int]]:
        for node in self.nodes:
            chain, length = node.get_chain()
            logger.debug(f"chain received {chain}")
            chain = Chain.from_dict(chain)
            if chain is not None:
                yield chain, length
            else:
                logger.warning(f"Invalid chain {chain} from node {node}")

    def spread_chain(self, chain):
        for node in self.nodes:
            node.send_chain(chain.__dict__())

    def spread_mining_request(self):
        logger.info("Spread mining request")

        for node in self.nodes:
            node.send_mining_request()

    def spread_block_creation_request(self):
        logger.info("Spread block creation request")

        for node in self.nodes:
            node.send_block_creation_request()

    def first_connection(self, host):
        self.add_node(host, type_=None, register_back=True)

    def remove_me(self):
        for n in self.nodes:
            n.unregister()

    def unregister(self, host):
        logger.info(f"Unregister {host} from {self.__str__()}")
        if host in self.__str__():
            self.nodes = list(filter(lambda x: x.__str__() != host, self.nodes))
            return True
        return False


class Node:
    def __init__(self, host, type_):
        self.host = host
        self.type = None if type_ is None else NodeType(type_)

        if self.type is None:
            self.get_type()
        if self.type == NodeType.UNKNOWN:
            logger.error("New Node type is UNKNOWN")
        else:
            logger.info(f"NODE Created {self.__repr__()}")

    def __str__(self):
        return self.host

    def __repr__(self):
        return f"host: {self.host} type: {self.type.value}"

    def send_mining_request(self):
        """
        Not used anymore, use send_block_creation_request instead
        :return:
        """
        if self.type == NodeType.MANAGER:
            logger.debug(
                f"Not sending mining request to {self.__repr__()} since is NodeType.MANAGER"
            )
            return
        response = get(f"http://{self.host}/mine")

        if response and response.status_code != 200:
            logger.error(
                f"Mine request sent to {self.__str__()} received error code {response.status_code}, "
                f"Reason: {response.reason}, {response.content}"
            )

    def send_block_creation_request(self):
        """
        Send a request to the node to create a block.
        :return:
        """
        if self.type == NodeType.MANAGER:
            logger.debug(
                f"Not sending block creation request to {self.__repr__()} since is NodeType.MANAGER"
            )
            return
        response = get(f"http://{self.host}/block/new", timeout=0.0001)  # TODO add route to new_block

        if response and response.status_code != 200:
            logger.error(
                f"Block creation request sent to {self.__str__()} received error code {response.status_code}, "
                f"Reason: {response.reason}, {response.content}"
            )

    def send_transaction(self, tx):
        response = post(f"http://{self.host}/transaction/add", json_={"tx": tx})

        if response and response.status_code != 201:
            logger.warning(
                f"Transaction sent to {self.__str__()} received error code {response.status_code}, Reason: {response.reason}, {response.content}"
            )

    def get_type(self):
        response = get(f"http://{self.host}/get_type")
        if response is None or response.status_code != 200:
            self.type = NodeType.UNKNOWN
            return

        rj = response.json()

        try:
            if response.status_code == 200 and "type" in rj:
                self.type = NodeType(rj["type"])
        except Exception as e:
            logger.warning(f'can\'t set type {rj["type"]} {e}')
            self.type = NodeType.UNKNOWN

    def get_chain(self):
        response = get(f"http://{self.host}/chain")
        if response is None:
            return None, 0

        rj = response.json()

        if response.status_code == 200 and "chain" in rj and "length" in rj:
            length = rj["length"]
            chain = rj["chain"]
            return chain, length

        logger.error(f"getChain() Invalid response from node {self.host}")
        return None, 0

    def send_chain(self, chain):
        post(f"http://{self.host}/chain_found", json_={"chain": chain})

    @run_in_thread
    def register(self, address, type_):
        response = post(
            f"http://{self.host}/nodes/register",
            json_={"node": address, "type": type_, "register_back": True},
        )
        return not not response

    @run_in_thread
    def register_back(self, spread=False, tries=20):
        logger.info(
            f"Call register back on http://{self.host}/nodes/register  spread {spread}  current host {Host().host}"
        )
        session = Session()
        retry = Retry(connect=tries, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        response = post(
            f"http://{self.host}/nodes/register",
            json_={
                "node": Host().host,
                "type": Host().type.value,
                "spread": spread,
                "register_back": False,
            },
        )
        return not not response

    def get_nodes_list(self):
        response = get(f"http://{self.host}/nodes/list")
        if not response:
            return []

        rj = response.json()

        if response.status_code == 200 and "nodes" in rj:
            nodes = rj["nodes"]
            return nodes
        logger.warning(f"[getNodesList]: Invalid response from node {self.host}")
        return []

    def unregister(self):
        post(f"http://{self.host}/nodes/unregister", json_={"port": Host().port})
