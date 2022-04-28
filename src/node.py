import time
from typing import List

import threading

from src.block import Chain
from src.config import Host, NodeType

import requests
import json
from urllib.parse import urlparse
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        return ', '.join(n.__str__() for n in self.nodes)

    def __dict__(self):
        return {'nodes': [f'http://{str(i)}' for i in self.nodes]}  # TODO check if http:// is necessary

    def spreadNewNode(self, address, type_):
        for node in self.nodes:
            node.register(address, type_)

    def spreadTransaction(self, tx):
        for node in self.nodes:
            node.sendTransaction(tx)

    def addNode(self, address, type_=None, register_back=False, spread=False):
        host = self.parseAddress(address)
        if host is None:
            logger.error('Host is None')
            return False

        if host in self.__str__():
            logger.warning(f"Node host {host} already registered")
            return False

        node = Node(host, type_)

        if node.type == NodeType.UNKNOWN:
            logger.warning(f"Invalid node type for address: {address}  host  {host}")
            return False

        if spread:
            self.spreadNewNode(address, node.type.value)
        self.nodes.append(node)
        if register_back:
            node.register_back(spread=len(self.nodes) == 1)
            return True
        return True

    def parseAddress(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            host = parsed_url.netloc
        elif parsed_url.path:
            if parsed_url.scheme:
                host = parsed_url.scheme + ':' + parsed_url.path
            else:
                host = parsed_url.path
        else:
            logger.warning(f"parseAddress cannot parse: {address}")
            return None
        return host

    def othersChains(self):
        for node in self.nodes:
            chain, length = node.getChain()
            logger.debug(f'chain received {chain}')
            chain = Chain.from_dict(chain)
            if chain is not None:
                yield chain, length
            else:
                logger.warning(f"Invalid chain {chain}")

    def spreadChain(self, chain):
        for node in self.nodes:
            node.sendChain(chain.__dict__())

    def spreadMiningRequest(self):
        for node in self.nodes:
            node.sendMiningRequest()

    def firstConnection(self, host):
        self.addNode(host, type_=None, register_back=True)

    def removeMe(self):
        for n in self.nodes:
            n.unregister()

    def unregister(self, host):
        logger.info(f'Unregister {host} from {self.__str__()}')
        if host in self.__str__():
            self.nodes = list(filter(lambda x: x.__str__() != host, self.nodes))
            return True
        return False


class Node:
    def __init__(self, host, type_):
        self.host = host
        self.type = None if type_ is None else NodeType(type_)

        if self.type is None:
            self.getType()
        if self.type == NodeType.UNKNOWN:
            logger.error('New Node type is UNKNOWN')
        else:
            logger.info(f"NODE Created {self.__repr__()}")

    def __str__(self):
        return self.host

    def __repr__(self):
        return f'host: {self.host} type: {self.type.value}'

    def sendMiningRequest(self):
        if self.type == NodeType.MANAGER:
            logger.debug(f"Not sending mining request to {self.__repr__()} since is NodeType.MANAGER")
            return
        response = requests.get(f'http://{self.host}/mine')

        if response.status_code != 200:
            logger.error(f"Mine request sent to {self.__str__()} received error code {response.status_code}, Reason: {response.reason}, {response.content}")

    def sendTransaction(self, tx):
        response = requests.post(f'http://{self.host}/transaction/add', json={'tx': tx})

        if response.status_code != 201:
            logger.warning(f"Transaction sent to {self.__str__()} received error code {response.status_code}, Reason: {response.reason}, {response.content}")

    def getType(self):
        try:
            logger.info(f"Send get_type request to {self.host}")
            response = requests.get(f'http://{self.host}/get_type')
            rj = response.json()
            logger.info(f"Response {rj} received to get_type")
        except ConnectionRefusedError as e:
            logger.error(f"[ConnectionRefusedError] Connection to http://{self.host} refused {e}")
            self.type = NodeType.UNKNOWN
            return
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[ConnectionError] Connection to http://{self.host} failed {e}")
            self.type = NodeType.UNKNOWN
            return

        try:
            if response.status_code == 200 and 'type' in rj:
                self.type = NodeType(rj['type'])
        except Exception as e:
            logger.warning(f'can\'t set type {rj["type"]} {e}')
            self.type = NodeType.ALL

    def getChain(self):
        try:
            response = requests.get(f'http://{self.host}/chain')
            rj = response.json()
        except ConnectionRefusedError:
            logger.error(f"[ConnectionRefusedError] Connection to http://{self.host} refused")
            return None, 0

        if response.status_code == 200 and 'chain' in rj and 'length' in rj:
            length = rj['length']
            chain = rj['chain']
            return chain, length
        logger.error(f'getChain() Invalid response from node {self.host}')
        return None, 0

    def sendChain(self, chain):
        try:
            requests.post(f'http://{self.host}/chain_found', json={'chain': chain})
        except ConnectionRefusedError:
            print("[ConnectionRefusedError] Connection to", f"http://{self.host}", "refused", file=sys.stderr)
            return

    @run_in_thread
    def register(self, address, type_):
        try:
            logger.info(f'[thread] Register {address} http://{self.host}/nodes/register')
            requests.post(f'http://{self.host}/nodes/register', json={"node": address, 'type': type_, 'register_back': True})
        except requests.exceptions.RequestException as e:
            logger.error(f"[thread] Error register(self, address, type_) {e}")
            return False
        return True

    @run_in_thread
    def register_back(self, spread=False, tries=20):
        try:
            logger.info(f"Call register back on http://{self.host}/nodes/register  spread {spread}  current host {Host().host}")
            session = requests.Session()
            retry = Retry(connect=tries, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            requests.post(f'http://{self.host}/nodes/register', json={"node": Host().host, "type": Host().type.value, "spread": spread, "register_back": False})
        except requests.exceptions.RequestException as e:
            logger.error(f"[thread] register_back(self, spread=False, tries=20) {e}")
            return False
        return True

    def getNodesList(self):
        try:
            response = requests.get(f'http://{self.host}/nodes/list')
            rj = response.json()
        except ConnectionRefusedError:
            logger.error(f"Connection to http://{self.host} refused")
            return None, 0

        if response.status_code == 200 and 'nodes' in rj:
            nodes = rj['nodes']
            return nodes
        logger.warning(f'[getNodesList]: Invalid response from node {self.host}')
        return []

    def unregister(self):
        try:
            logger.info(f"Unregister from {self.host}")
            requests.post(f'http://{self.host}/nodes/unregister', json={"port": Host().port})
        except requests.exceptions.RequestException as e:
            logger.error(f"unregister() {e}")
