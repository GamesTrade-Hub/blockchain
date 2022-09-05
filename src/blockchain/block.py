import sys
from typing import List, Iterator, Optional, Tuple, Union

from src.blockchain.config import Host
from src.blockchain.keys import sign, has_valid_signature, PublicKey, Signature
from src.blockchain.tools import BcEncoder, hash__, get
from src.blockchain.transaction import TransactionsList, State, Transaction
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
        if cancel_queue.qsize() and cancel_queue.get(block=False) == "cancel":
            logger.info(f"Cancel received while doing POW")
            sys.exit(0)
        nonce += 1 + random()

    sleep(1)
    nonce_queue.put(nonce)
    print("nonce found in subprocess", nonce)
    get(f"{host}/private/__end_mining_process")
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
        nonce: Optional[Signature] = None,
        hash_: Optional[str] = None,
    ):
        """
        Class to handle blocks in the blockchain. Allows to serialize and deserialize blocks.

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
        self._hash: str = hash_ or hash__(self.__encode(full=False))
        self._nonce: Optional[Signature] = nonce
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

    def __str__(self) -> str:
        return self.__dict__().__str__()

    def __dict__(self) -> dict:
        return {**self.__to_dict(full=True), **{"hash": self._hash}}

    @classmethod
    def from_dict(cls, dictionary: dict) -> Union["Block", Tuple[None, str]]:
        block = cls(
            index=dictionary["index"],
            transactions=TransactionsList.from_dict(dictionary["transactions"]),
            previous_hash=dictionary["previous_hash"],
            validator=PublicKey(dictionary["validator"]),
            nonce=Signature(dictionary["nonce"]),
            hash_=dictionary["hash"],
        )
        if not block.valid():
            logger.warning(f"Invalid block: {block.error}")
            return None, "Invalid block"
        return block

    @classmethod
    def from_string(cls, string: str) -> Union["Block", Tuple[None, str]]:
        return Block.from_dict(ast.literal_eval(string))

    def __to_dict(self, full: bool = True) -> dict:
        """
        Make the block a dictionary
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        :param full: if full includes nonce and pow_time
        :return: block as a dictionary
        """
        d = {
            "index": self._index,
            "transactions": self._txs.__dict__(),
            "previous_hash": self._previous_hash,
        }
        if full:
            d = {
                **d,
                **{
                    "nonce": self._nonce.encode(),
                    "validator": self._validator.encode(),
                    "hash": self._hash,
                },
            }
        return d

    def __encode(self, full: bool = True) -> str:
        d = self.__to_dict(full=full)
        return d.__str__()

    @staticmethod
    def valid_pow(block_hash, nonce) -> bool:
        """
        Validates the Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f"{block_hash}{nonce}"
        guess_hash = hash__(guess)
        return guess_hash[:4] == "0000"

    @staticmethod
    def valid_poa(block_hash: str, nonce: Signature, validator: PublicKey) -> bool:
        """
        Validates the Proof
        :param block_hash: hash of the block
        :param nonce: signature of the block hash signed by the validator
        :param validator: public key of the node which created the block
        :return: <bool> True if correct, False if not.
        """
        from src.blockchain.blockchain_manager import BlockchainManager

        print(f"{nonce.signature=}", f"{block_hash=}", f"{validator=}")
        return (
            has_valid_signature(nonce.signature, block_hash, validator)
            and validator.encode() in BlockchainManager().authorized_nodes_public_keys
        )

    def valid_transactions(self) -> bool:
        if not self._txs.valid():
            self.error = self._txs.error
            return False
        return True

    def valid(self) -> bool:
        if self._index == 1 and self._txs.__len__() == 0:
            return True
        # if not Block.valid_pow(self._hash, self._nonce):
        #     self.error = f'Invalid POW nonce: {self._nonce}, hash: {self._hash}'
        #     logger.warning(f'Invalid block {self.error}')
        #     return False
        if not Block.valid_poa(self._hash, self._nonce, self._validator):
            self.error = f"Invalid POA: {self._nonce}, hash: {self._hash}"
            logger.warning(f"Invalid block {self.error}")
            return False
        if not self.valid_transactions():
            print(f"Invalid block {self.error}")
            return False
        return True

    def confirm_selected_transactions(self) -> None:
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

    @property
    def index(self) -> int:
        return self._index

    @property
    def transactions(self) -> TransactionsList:
        return self._txs

    @property
    def validator(self) -> PublicKey:
        return self._validator

    @property
    def nonce(self) -> Optional[Signature]:
        return self._nonce

    @property
    def previous_hash(self) -> str:
        return self._previous_hash

    @property
    def hash(self) -> str:
        """
        SHA-256 hash of a Block
        """
        return self._hash

    def __iter__(self) -> Iterator[Transaction]:
        return self._txs.__iter__()
