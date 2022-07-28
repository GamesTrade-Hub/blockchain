import sys
from typing import List

from src.blockchain.config import Host
from src.blockchain.keys import sign, has_valid_signature, PublicKey, Signature
from src.blockchain.tools import BcEncoder, hash__, get
from src.blockchain.transaction import TransactionsList, State
from src.blockchain.config import Host, PRIVATE_KEY
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


def proof_of_work(block_hash, nonce_queue, cancel_queue, host):
    """
    DEPRECATED
    Simple Proof of Work Algorithm:
     - Find a number p' such that hash(pp') contains leading 5 zeroes
     - Where p is the previous nonce, and p' is the new nonce

    :return: <int>
    """

    nonce = 0
    while Block.valid_pow(block_hash, nonce) is False:
        if cancel_queue.qsize() and cancel_queue.get(block=False) == 'cancel':
            logger.info(f'Cancel received while doing POW')
            sys.exit(0)
        nonce += 1 + random()

    sleep(1)
    nonce_queue.put(nonce)
    print('nonce found in subprocess', nonce)
    get(f'{host}/private/__end_mining_process')
    sys.exit(0)


def proof_of_authority(block_hash) -> Signature:
    """
    Proof of Authority.
    :return: <int>
    """

    signature = sign(block_hash, PRIVATE_KEY)
    return Signature(signature)


class Block:
    def __init__(
            self,
            index: int,
            transactions: TransactionsList,
            previous_hash: str,
            validator: PublicKey,
            nonce: Signature = None,
            hash_=None
    ):
        """
        :param index: index of the block in the chain
        :param transactions: transactions list included in the block (TransactionsList)
        :param previous_hash: hash of the previous block
        :param validator: public key of the node which created the block
        :param nonce: signature of the block hash signed by the validator
        :param hash_: hash of the block content
        """
        ## Full block ##
        # Raw block #
        self._index = index
        self._txs: TransactionsList = transactions
        self._previous_hash = previous_hash
        # ========= #
        self._hash = hash_ or hash__(self.__encode(full=False))
        self._nonce: Signature = nonce
        self._validator: PublicKey = validator
        ## ========== ##

        self.error = None
        # self.nonce_queue = Queue()
        # self.cancel_queue = Queue()
        # logger.info(f"Create new block with call back host {Host().host}")
        # self.mining_process: Process = Process(target=proof_of_work,
        #                                        args=(self._hash, self.nonce_queue, self.cancel_queue, Host().host))

        if not self._nonce:
            self._nonce = proof_of_authority(self._hash)

    @property
    def previous_hash(self):
        return self._previous_hash

    def __str__(self):
        return self.__dict__().__str__()

    def __dict__(self):
        return {**self.__to_dict(full=True), **{'hash': self._hash}}

    @classmethod
    def from_dict(cls, dictionary):
        block = cls(
            index=dictionary['index'],
            transactions=TransactionsList.from_dict(dictionary['transactions']),
            previous_hash=dictionary['previous_hash'],
            validator=PublicKey(dictionary['validator']),
            nonce=Signature(dictionary['nonce']),
            hash_=dictionary['hash']
        )
        if not block.valid():
            logger.warning(f'Invalid block: {block.error}')
            return None, 'Invalid block'
        return block

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
                'nonce': self._nonce.encode(),
                'validator': self._validator.encode(),
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
    def valid_pow(block_hash, nonce):
        """
        Validates the Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{block_hash}{nonce}'
        guess_hash = hash__(guess)
        return guess_hash[:4] == "0000"

    @staticmethod
    def valid_poa(block_hash: str, nonce: Signature, validator: PublicKey):
        """
        Validates the Proof
        :param block_hash: hash of the block
        :param nonce: signature of the block hash signed by the validator
        :param validator: public key of the node which created the block
        :return: <bool> True if correct, False if not.
        """
        from src.blockchain.chain import Blockchain

        print(f"{nonce.signature=}", f"{block_hash=}", f"{validator=}")
        return has_valid_signature(nonce.signature, block_hash, validator) and \
               validator.encode() in Blockchain().authorized_nodes_public_keys

    def valid_transactions(self):
        if not self._txs.valid():
            self.error = self._txs.error
            return False
        return True

    def valid(self):
        if self._index == 1 and self._txs.__len__() == 0:
            return True
        # if not Block.valid_pow(self._hash, self._nonce):
        #     self.error = f'Invalid POW nonce: {self._nonce}, hash: {self._hash}'
        #     logger.warning(f'Invalid block {self.error}')
        #     return False
        if not Block.valid_poa(self._hash, self._nonce, self._validator):
            self.error = f'Invalid POA: {self._nonce}, hash: {self._hash}'
            logger.warning(f'Invalid block {self.error}')
            return False
        if not self.valid_transactions():
            print(f'Invalid block {self.error}')
            return False
        return True

    def confirm_selected_transactions(self):
        """
        Update transactions in current block by changing their state from selected to in_chain.
        """
        self._txs.update_state(from_=State.SELECTED, to_=State.IN_CHAIN)

    def __del__(self):
        """
        When block is deleted, set back the SELECTED transactions in it to WAITING.
        :return:
        """
        self._txs.update_state(from_=State.SELECTED, to_=State.WAITING)
        # self.__stop_mining()

    def transactions(self):
        for tx in self._txs.transactions():
            yield tx


class Chain:
    def __init__(self, blocks=None):
        if blocks is None:
            blocks = list()
        self._blocks: List[Block] = blocks

    def valid(self):
        # TODO All transactions must have diff ids

        valid = all([isinstance(b, Block) and b.valid() for b in self._blocks]) and all(
            [a.hash == b.previous_hash for a, b in zip(self._blocks[:-2], self._blocks[1:-1])])

        # print('valid?', valid, [type(b) for b in self._blocks])
        # if not valid:
        #     print(
        #         'Chain not valid',
        #         all([isinstance(b, Block) for b in self._blocks]),
        #         all([b.valid() for b in self._blocks]),
        #         all([a.hash == b.previous_hash for a, b in zip(self._blocks[:-1], self._blocks[1:])])
        #     )
        #     print(self.__str__())
        return valid

    def contains(self, transaction):
        for tx in self.transactions():
            if tx.id == transaction.id and tx.time == transaction.time:
                return True
        return False

    @classmethod
    def from_dict(cls, chain):
        if chain is None:
            logger.warning("Chained received to be parsed is None")
            return None
        chain = cls(blocks=[Block.from_dict(b) for b in chain['chain']])
        if not chain.valid():
            logger.warning("Parsed chain not valid")
            return None
        return chain

    def __str__(self):
        return self.__dict__().__str__()

    def __dict__(self):
        return {'chain': [block.__dict__() for block in self._blocks]}

    def __len__(self):
        return self._blocks.__len__()

    def last_blockhash(self):
        return self._blocks[-1].hash

    def add_block(self, block):
        block.confirm_selected_transactions()
        self._blocks.append(block)

    def blocks(self):
        for block in self._blocks:
            yield block

    def transactions(self):
        for block in self.blocks():
            for tx in block.transactions():
                yield tx

    def get_balance_by_token(self, public_key, token) -> float:
        from src.blockchain.chain import Blockchain
        balance = 0

        for tx in Blockchain().considered_transactions():
            if tx['recipient'] == public_key and tx['token'] == token:
                balance += tx['amount']
            if tx['sender'] == public_key and tx['token'] == token and tx['recipient'] != public_key:
                balance -= tx['amount']
        return balance

    def get_balance(self, public_key):
        from src.blockchain.chain import Blockchain
        balance = {}

        for tx in Blockchain().considered_transactions():
            if tx['recipient'] == public_key:
                if tx['token'] not in balance:
                    balance[tx['token']] = 0
                balance[tx['token']] += tx['amount']
            if tx['sender'] == public_key and tx['recipient'] != public_key:
                if tx['token'] not in balance:
                    balance[tx['token']] = 0
                balance[tx['token']] -= tx['amount']
        return balance
