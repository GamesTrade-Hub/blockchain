from src.block import Chain
from src.config import Host

import requests
import json
from urllib.parse import urlparse
import sys


class NodesList:
    def __init__(self):
        self.nodes = list()

    def __str__(self):
        return ', '.join(n.__str__() for n in self.nodes)

    def spreadTransaction(self, tx):
        for node in self.nodes:
            response = requests.post(f'http://{node.host}/transaction/add', json={'tx': tx})

            if response.status_code != 201:
                print(f"Transaction sent to {node} received error code {response.status_code}, Reason: {response.reason}, {response.content}")

    def addNode(self, address, register_back=False):
        parsed_url = urlparse(address)

        if parsed_url.netloc:
            host = parsed_url.netloc
        elif parsed_url.path:
            if parsed_url.scheme:
                host = parsed_url.scheme + ':' + parsed_url.path
            else:
                host = parsed_url.path
        else:
            return False

        if host in self.nodes:
            return False
        node = Node(host)
        if self.alreadyExists(node):
            return False

        self.nodes.append(node)
        if register_back:
            return NodesList.register_back(node)

        return True

    def othersChains(self):
        for node in self.nodes:
            chain, length = node.getChain()
            print('chain received', chain)
            chain = Chain.from_dict(chain)
            if chain is not None:
                yield chain, length
            else:
                print("Invalid chain", chain)

    def alreadyExists(self, node):
        for n in self.nodes:
            if n.host == node.host:
                return True
        return False

    @staticmethod
    def register_back(node):
        try:
            requests.post(f'http://{node.__str__()}/nodes/register_back', json={"node": Host().host})
        except requests.exceptions.RequestException as e:
            print("Error", e, file=sys.stderr)
            return False
        return True

    def spreadChain(self, chain):
        for node in self.nodes:
            node.sendChain(chain.__dict__())

    def spreadMiningRequest(self):
        for node in self.nodes:
            response = requests.get(f'http://{node.host}/mine')

            if response.status_code != 200:
                print(f"Mine request sent to {node} received error code {response.status_code}, Reason: {response.reason}, {response.content}")


class Node:
    def __init__(self, host):
        self.host = host

    def __str__(self):
        return self.host

    def getChain(self):
        try:
            response = requests.get(f'http://{self.host}/chain')
            rj = response.json()
        except ConnectionRefusedError:
            print("[ConnectionRefusedError] Connection to", f"http://{self.host}", "refused", file=sys.stderr)
            return None, 0

        if response.status_code == 200 and 'chain' in rj and 'length' in rj:
            length = rj['length']
            chain = rj['chain']
            return chain, length
        print('[chain] Invalid response from node', self.host)
        return None, 0

    def sendChain(self, chain):
        try:
            response = requests.post(f'http://{self.host}/chain_found', json={'chain': chain})
        except ConnectionRefusedError:
            print("[ConnectionRefusedError] Connection to", f"http://{self.host}", "refused", file=sys.stderr)
            return
