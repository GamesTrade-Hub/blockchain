import hashlib
import json
import sys
from urllib.parse import urlparse
from uuid import uuid4
import time

import requests
from flask import Flask, jsonify, request

from enum import Enum


class Step(Enum):
    IDLE = 0
    SETUP_BLOCK_BOUNDS = 1
    WAITING_FOR_TXS_SELECTION = 2
    SELECT_TXS = 3
    MINING = 4


class Blockchain:
    def __init__(self, verbose=False):
        self.tmp_state = 0
        self.step = Step.IDLE

        self.Txs = []
        self.selected_Txs = set()
        self.time_limit_Txs = None

        self.chain = []
        self.nodes = set()
        self.print_v = print if verbose else lambda *a, **k: None

        # Create the genesis block
        self.new_block(previous_hash='1', nonce=100)
        self.print_v("Blockchain coin created")

    def register_node(self, address, register_back=False, host=''):
        """
        Add a new node to the list of nodes
        :param host: ip and port of the current api instance
        :param register_back: tell whether or not the node just registered received a call back to register the current node
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)

        if parsed_url.netloc:
            new_node = parsed_url.netloc
        elif parsed_url.path:
            new_node = parsed_url.scheme + ':' + parsed_url.path
        else:
            raise ValueError('Invalid URL')

        self.nodes.add(new_node)
        if register_back:
            print("call back node", f'http://{new_node}/nodes/register_back', {"node": host}, file=sys.stderr)
            print(f'http://{new_node}/ping', file=sys.stderr)
            requests.get(f'http://{new_node}/ping')
            print("get ok", file=sys.stderr)
            requests.post(f'http://{new_node}/nodes/register_back', json={"node": host})

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if (not self.valid_proof(block['hash'], block['nonce'])) and block['previous_hash'] == block['hash']:
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        self.step = Step.IDLE

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length == max_length and self.valid_chain(chain) and chain[-1]['pow_time'] < self.last_block['pow_time']:
                    max_length = length
                    new_chain = chain

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, nonce=None, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param nonce: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        print('prepare to add block', file=sys.stderr)

        if self.step == Step.SELECT_TXS:
            self.step = Step.MINING

        if self.step != Step.MINING and nonce is None:
            return None

        block = {
            'index': self.chain_size + 1,
            'transactions_timestamp': self.time_limit_Txs,
            'transactions': list(self.selected_Txs),
            'previous_hash': previous_hash or self.last_block['hash'],
        }
        block['proof'] = nonce or self.proof_of_work(self.hash(block))
        block['pow_time'] = time.time_ns()
        block['hash'] = self.hash(block)

        # Reset the current list of transactions
        self.Txs = [tx for tx in self.selected_Txs if tx['id'] not in self.selected_Txs]
        self.time_limit_Txs = None
        self.selected_Txs = []
        self.step = Step.IDLE

        self.chain.append(block)
        print('add block', file=sys.stderr)
        return block

    def new_transaction(self, transaction_id, sender, recipient, amount, time_):
        """
        Creates a new transaction to go into the next mined Block
        :param transaction_id: id of the transaction. If None, this node initiate the transaction and send it to others.
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :param time: When the transaction was sent
        :return: The index of the Block that will hold this transaction
        """

        transaction = {
            'id': transaction_id or str(uuid4()),
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time': time_ or time.time_ns()
        }
        self.Txs.append(transaction)

        if transaction_id is None:
            for node in self.nodes:
                response = requests.post(f'http://{node}/transactions/new', json=transaction)

                if response.status_code != 200:
                    print(f"Transaction sent to {node} received error code {response.status_code}")

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        do_not_use = ['hash', 'nonce']
        block = {a: block[a] for a in block if a not in do_not_use}
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        print("ici", block)
        print(json.dumps(block))
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, block_hash):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous nonce, and p' is the new nonce

        :return: <int>
        """

        nonce = 0
        while self.valid_proof(block_hash, nonce) is False:
            nonce += 1

        # TODO tout reset pour le prochain block
        return nonce

    @staticmethod
    def valid_proof(block_hash, nonce):
        """
        Validates the Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{block_hash}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def select_Txs(self):
        """
        """

        if self.step == Step.WAITING_FOR_TXS_SELECTION:
            self.step = Step.SELECT_TXS

        if self.step != Step.SELECT_TXS:
            print(f'Wrong step for selecting Txs, current step is {self.step}', file=sys.stderr)
            return

        self.selected_Txs = self.Txs

        for node in self.nodes:
            response = requests.post(f'http://{node}/get_Txs', json={"time_limit": self.time_limit_Txs})

            if response.status_code == 200:
                self.selected_Txs = self.selected_Txs.union(set(response.json()['Txs']))

        self.selected_Txs = [tx for tx in self.selected_Txs if self.transactionIsValid(tx)]
        self.step = Step.MINING

    def setTmpState(self, state=1):
        self.tmp_state = state

    def getTmpState(self):
        return self.tmp_state

    def transactionIsValid(self, transaction):
        return transaction['time'] < self.time_limit_Txs

    def setupBlock(self, time_limit, block):
        if self.step == Step.IDLE:
            self.step = Step.SETUP_BLOCK_BOUNDS

        if self.step != Step.SETUP_BLOCK_BOUNDS:
            print(f'Wrong step for setup block bounds, current step is {self.step}', file=sys.stderr)
            return

        if self.time_limit_Txs is None or time.time_ns() < self.time_limit_Txs:
            self.time_limit_Txs = time.time_ns()

        # FIXME bad node can add bad time limit
        if time_limit and time_limit < self.time_limit_Txs and block == self.chain_size + 1:
            self.time_limit_Txs = time_limit

        if time_limit is None:
            for node in self.nodes:
                response = requests.post(f'http://{node}/create_block', json={"time_limit": self.time_limit_Txs,
                                                                              "block": self.chain_size + 1})
                if response.status_code == 200:
                    time_limit = response.json()['time_limit']  # FIXME this can be missing
                    block = response.json()['block']

                    if time_limit and time_limit < self.time_limit_Txs and block == self.chain_size + 1:
                        self.time_limit_Txs = time_limit

        self.step = Step.WAITING_FOR_TXS_SELECTION
        return self.time_limit_Txs, self.chain_size + 1

    @property
    def chain_size(self):
        return len(self.chain)

    def isReadyForTxsSelection(self):
        return self.step == Step.WAITING_FOR_TXS_SELECTION

    def isMining(self):
        return self.step == Step.MINING

    def getStep(self):
        return self.step

    def get_Txs(self, time_limit):
        return [tx for tx in self.Txs if tx['time'] < time_limit]

    def get_balance(self, user_id):
        balance = 0

        for block in self.chain:
            for tx in block['transactions']:
                if tx['recipient'] == user_id:
                    balance += tx['amount']
                if tx['sender'] == user_id:
                    balance -= tx['amount']

        return balance
