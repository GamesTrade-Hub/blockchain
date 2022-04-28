import sys
from src.tools import BcEncoder, hash__, get
from src.transaction import TransactionsList, State
from src.config import Host
from random import random
from multiprocessing import Process, Queue
import json
import ast
import requests
from time import sleep
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


def proofOfWork(block_hash, queue, host):
    """
    Simple Proof of Work Algorithm:
     - Find a number p' such that hash(pp') contains leading 5 zeroes
     - Where p is the previous nonce, and p' is the new nonce

    :return: <int>
    """

    nonce = 0
    while Block.valid_proof(block_hash, nonce) is False:
        nonce += 1 + random()

    sleep(1)
    queue.put(nonce)
    print('nonce found in subprocess', nonce)
    get(f'{host}/do_not_use/end_mining_process')
    sys.exit(0)


class Chain:
    def __init__(self, blocks=None):
        if blocks is None:
            blocks = list()
        self._blocks = blocks

    def valid(self):
        # TODO All transactions must have diff ids

        valid = all([isinstance(b, Block) and b.valid() for b in self._blocks]) and all([a.hash__ == b.previous_hash for a, b in zip(self._blocks[:-2], self._blocks[1:-1])])

        if not valid:
            print('chain not valid',
                  all([isinstance(b, Block) for b in self._blocks]),
                  all([b.valid() for b in self._blocks]),
                  all([a.hash__ == b.previous_hash for a, b in zip(self._blocks[:-1], self._blocks[1:])])
                  )
            print(self.__str__())
        return valid

    def containsTx(self, transaction):
        for tx in self.transactions():
            if tx.id == transaction.id and tx.time == transaction.time:
                return True
        return False

    @classmethod
    def from_dict(cls, chain):
        chain = cls(blocks=[Block.from_dict(b) for b in chain['chain']])
        if not chain.valid():
            print("chain not valid return none")
            return None
        return chain

    def __str__(self):
        return self.__dict__().__str__()

    def __dict__(self):
        return {'chain': [block.__dict__() for block in self._blocks]}

    def __len__(self):
        return self._blocks.__len__()

    def lastBlockhash(self):
        return self._blocks[-1].hash__

    def addBlock(self, block):
        block.confirmSelectedTransactions()
        self._blocks.append(block)

    def transactions(self):
        for b in self._blocks:
            for tx in b.transactions():
                yield tx

    def getBalanceByToken(self, public_key, token):
        from src.blockchain import Blockchain
        balance = 0

        for tx in Blockchain().consideredTransactions():
            if tx['recipient'] == public_key and tx['token'] == token:
                balance += tx['amount']
            if tx['sender'] == public_key and tx['token'] == token and tx['recipient'] != public_key:
                balance -= tx['amount']
        return balance

    def getBalance(self, public_key):
        from src.blockchain import Blockchain
        balance = {}

        for tx in Blockchain().consideredTransactions():
            if tx['recipient'] == public_key:
                if tx['token'] not in balance:
                    balance[tx['token']] = 0
                balance[tx['token']] += tx['amount']
            if tx['sender'] == public_key and tx['recipient'] != public_key:
                if tx['token'] not in balance:
                    balance[tx['token']] = 0
                balance[tx['token']] -= tx['amount']
        return balance


class Block:
    def __init__(self, index, transactions, previous_hash, nonce=None, hash_=None):
        ## Full block ##
        # Raw block #
        self._index = index
        self._txs: TransactionsList = transactions
        self._previous_hash = previous_hash
        # ========= #
        self._hash = hash_ or hash__(self.__encode(full=False))
        self._nonce = nonce
        ## ========== ##

        self.error = None
        self.mining_process_queue = Queue()
        logger.info(f"Create new block with call back host {Host().host}")
        self.mining_process: Process = Process(target=proofOfWork, args=(self._hash, self.mining_process_queue, Host().host))

        if not self._nonce:
            self.mining_process.start()

    @property
    def previous_hash(self):
        return self._previous_hash

    def __str__(self):
        return self.__dict__().__str__()

    def __dict__(self):
        return {**self.__to_dict(full=True), **{'hash': self._hash}}

    @classmethod
    def from_dict(cls, dictionary):
        b = cls(index=dictionary['index'],
                transactions=TransactionsList.from_dict(dictionary['transactions']),
                previous_hash=dictionary['previous_hash'],
                nonce=dictionary['nonce'],
                hash_=dictionary['hash']
                )
        if not b.valid():
            print('warning: invalid block: ', b.error)
            return None, 'Block not valid'
        return b

    @classmethod
    def from_string(cls, string):
        return Block.from_dict(ast.literal_eval(string))

    def __to_dict(self, full=True):
        """
        Make the block a dictionary
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        :param full: if full includes nonce and pow_time
        :return:
        """
        d = {
            'index': self._index,
            'transactions': self._txs.__dict__(),
            'previous_hash': self._previous_hash
        }
        if full:
            d = {**d, **{
                'nonce': self._nonce,
                'hash': self._hash,
            }}
        return d

    def __encode(self, full=True):
        d = self.__to_dict(full=full)
        return d.__str__()

    @property
    def hash(self):
        """
        Creates a SHA-256 hash of a Block
        """
        return self._hash

    @staticmethod
    def valid_proof(block_hash, nonce):
        """
        Validates the Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{block_hash}{nonce}'
        guess_hash = hash__(guess)
        return guess_hash[:4] == "0000"

    def valid_transactions(self):
        if not self._txs.valid():
            self.error = self._txs.error
            return False
        return True

    def valid(self):
        if self._index == 1 and self._txs.__len__() == 0 and self._nonce == 'genesis':
            return True
        if not Block.valid_proof(self._hash, self._nonce):
            self.error = f'Invalid POW nonce: {self._nonce}, hash: {self._hash}'
            print('block not valid', self.error)
            return False
        if not self.valid_transactions():
            print('block not valid', self.error)
            return False
        return True

    def powFinished(self):
        return self._nonce is None and not self.mining_process_queue.empty()

    def completeBlock(self):
        if not self.powFinished():
            print('This method is not meant to be called if the node did not find the POW')
        self._nonce = self.mining_process_queue.get()
        # sleep(1)  # Let time to the process to end before killing it
        # self.mining_process.terminate()
        # print('is alive', self.mining_process.is_alive())
        # self.mining_process.kill()
        # print('is alive', self.mining_process.is_alive())
        self.mining_process_queue.close()
        del self.mining_process_queue
        # del self.mining_process
        print('nonce found:', self._nonce)

    def __stopMining(self):
        if self.mining_process and self.mining_process.is_alive():
            self.mining_process.kill()

    def confirmSelectedTransactions(self):
        self._txs.updateState(from_=State.SELECTED, to_=State.IN_CHAIN)

    def __del__(self):
        self._txs.updateState(from_=State.SELECTED, to_=State.WAITING)
        self.__stopMining()

    def transactions(self):
        for tx in self._txs.transactions():
            yield tx
