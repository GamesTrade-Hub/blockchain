from typing import List, Iterator, Optional

from src.blockchain.tools import get_time, BcEncoder
from src.blockchain.smart_contracts import SmartContract, Type
from src.blockchain.keys import PublicKey, PrivateKey, PublicKeyContainer, Signature

import json
from uuid import uuid4
from enum import IntEnum
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class State(IntEnum):
    WAITING = 0
    SELECTED = 1  # Meaning 'In current block'
    IN_CHAIN = 2
    VALIDATED = 3  # Meaning, in the chain since enough blocks to be sure that this won't ever change

    def encode(self):
        return int(self)

    @classmethod
    def decode(cls, enm):
        return cls(enm)


class TransactionsList:
    def __init__(self, transactions=None):
        if transactions is None:
            transactions = list()

        self._txs: List[Transaction] = transactions
        self.error = None

    def __len__(self):
        return self._txs.__len__()

    def select(self):
        """
        Only entry point where you call smart contract validation
        This function has to be used wisely since it changes the state of the transactions
        """
        self.reset_usage_smart_contract()
        for tx in self._txs:
            if tx.can_be_added(self):
                tx.state = State.SELECTED
        return [tx for tx in self._txs if tx.state == State.SELECTED]

    def create_add_transaction(
        self,
        id_,
        token: str,
        sender: str,
        recipient: str,
        amount,
        time_=None,
        sc_=None,
        signature=None,
        private_key=None,
        state=State.WAITING,
        create=False,
    ):
        """
        add Transaction to the transaction list if the transaction is valid.
        Sign the transaction if there is a private key and the transaction is not already signed
        :return: True if the transaction is added false otherwise.
        """
        tx = Transaction(
            id_,
            token,
            sender,
            recipient,
            amount,
            time_,
            sc_,
            signature=signature,
            private_key=private_key,
            state=state,
        )
        if not tx.valid(create=create):
            self.error = tx.error
            return None, None
        self._txs.append(tx)
        return True, tx

    def add_from_dict(self, tx, create=False):
        tx = Transaction.from_dict(tx, create=create)
        if not tx.valid(create=create):
            self.error = tx.error
            return False, None
        self._txs.append(tx)
        return True, tx

    @classmethod
    def from_dict(cls, dictionary):
        print("transaction from dict", dictionary)
        txs = cls(
            transactions=[
                Transaction.from_dict(tx, create=False)
                for tx in dictionary["transactions"]
            ]
        )
        if not txs.valid():
            print("Transaction set not valid", txs.error)
        return txs

    def __dict__(self):
        return {"transactions": [tx.__dict__() for tx in self._txs]}

    def valid(self):
        # FIXME check transactions timestamp (must have a minimum gap between each of them if they are the same maybe
        # not, just check id are different) / smart contract validity
        if not all([tx.valid() for tx in self._txs]):
            self.error = ", ".join(
                [tx.error for tx in self._txs if tx.error is not None]
            )
            return False
        return True

    def update_state(self, from_, to_):
        for tx in self._txs:
            if tx.state == from_:
                tx.state = to_

    def update_state_cdt(self, from_, to_, cdt):
        for tx in [tx for tx in self._txs if cdt(tx)]:
            if tx.state in from_:
                tx.state = to_

    def all(self, except_id):
        for tx in self._txs:
            if tx.id != except_id:
                yield tx

    def transactions(
        self, min_state=State.WAITING, max_state=State.VALIDATED
    ) -> Iterator["Transaction"]:
        for tx in self._txs:
            if min_state <= tx.state <= max_state:
                yield tx

    def __iter__(self):
        return self._txs.__iter__()

    def __add__(self, other):
        return TransactionsList(self._txs + other._txs)

    def __iadd__(self, other):
        self._txs += other._txs
        return self

    # Smart contract related ##################
    def reset_usage_smart_contract(self):
        for tx in self._txs:
            tx.reset_usage_smart_contract()

    ###########################################


class Transaction:
    def __init__(
        self,
        id_: str,
        token: str,
        sender: str,
        recipient: str,
        amount: float,
        time_: int,
        sc_: SmartContract,
        signature: str = None,
        private_key: str = None,
        state: State = None,
    ):
        """
        Creates a transaction
        if the transaction is not signed, then you must provide the private key to sign it.
        If signature is None and private_key is None as well, the transaction is invalid.
        :param id_: unique uuid4 of the transaction (str)
        :param token: token of the transaction (str)
        :param sender: sender of the transaction (PublicKey)
        :param recipient: recipient of the transaction (PublicKey)
        :param amount: amount of the transaction (float)
        :param time_: timestamp of the transaction (int)
        :param sc_: smart contract of the transaction (SmartContract)
        :param signature: signature of the transaction (tuple) (if None, the transaction is signed using the private key)
        :param private_key: private key of the sender (PrivateKey) (not optional if signature is None)
        :param state: state of the transaction in the blockchain (State)
        """
        if state == State.SELECTED:
            raise 'Transaction can\'t be created in "selected" state because this state is specific to the node and ' "does not exist in the blockchain "

        # ## Full transaction ## #
        # # Raw transaction # #
        self._id = id_ or str(uuid4())
        self._token = token
        logger.debug(f"sender id {sender}")
        self._sender: PublicKeyContainer = PublicKeyContainer(sender)
        self._recipient: PublicKeyContainer = PublicKeyContainer(recipient)
        self._amount: float = amount
        self._time: int = time_ or get_time()
        self._smart_contract: SmartContract = SmartContract(sc_, self) or SmartContract(
            None, self
        )
        # # =============== # #
        self._signature: Optional[Signature] = Signature(signature) if signature is not None else None
        # ## ================ ## #

        if self._sender.key is None or self._recipient.key is None:
            logger.warning("Invalid public key")
            self.error = "Invalid key"
            return

        if self._signature is None:
            self.sign(PrivateKey(private_key))

        self.error = None
        self.state = state or State.WAITING
        self._used = False

    # Smart contract related
    def is_used_to_validate_smart_contract(self):
        return self._used

    def use_to_validate_smart_contract(self):
        self._used = True

    def reset_usage_smart_contract(self):
        self._used = False
        self._smart_contract.reset_state()

    ########################

    @property
    def id(self):
        return self._id

    @property
    def time(self):
        return self._time

    @property
    def smart_contract(self):
        return self._smart_contract

    def __getitem__(self, item):
        m = {
            "recipient": self._recipient.__str__(),
            "sender": self._sender.__str__(),
            "amount": self._amount,
            "token": self._token.__str__(),
        }
        return m[item]

    def has_valid_attrs(self):
        from src.blockchain.blockchain_manager import BlockchainManager

        if (
            self._sender == self._recipient
            and BlockchainManager.is_admin(self._sender) is False
        ):
            self.error = "Sender and recipient can't be the same"
            return False
        if self.is_nft() and self._amount != 1:
            self.error = "NFT transfer amount has to be 1"
            return False
        if self.is_item() and self._amount != int(self._amount):
            self.error = "Item transfer amount has to be natural integer > 0"
            return False
        if self._amount <= 0:
            self.error = "amount can't be <= 0"
            return False
        if self._smart_contract.contract_type == Type.INVALID:
            self.error = "Invalid smart contract"
            return False
        return True

    def does_not_violate_the_portfolio(self):
        from src.blockchain.blockchain_manager import (
            BlockchainManager,
        )

        if (
            self.is_nft()
            and not BlockchainManager.is_admin_of_token(self._sender, self._token)
        ) and BlockchainManager().get_balance_by_token(
            self._sender.__str__(), self._token
        ) < self._amount:
            self.error = (
                f"User does not have nft {self._token} to proceed the transaction"
            )
            logger.info(f"ERROR while adding transaction {self.error=} {self.id=}")
            return False

        if (
            BlockchainManager.is_admin_of_token(self._sender, self._token) is False
            and BlockchainManager().get_balance_by_token(
                self._sender.__str__(), self._token
            )
            < self._amount
        ):
            self.error = (
                f"User does not have enough {self._token} to proceed the transaction"
            )
            logger.info(f"ERROR while adding transaction {self.error=} {self.id=}")

            return False

        if (
            BlockchainManager.is_admin_of_token(self._recipient, self._token)
            and BlockchainManager.is_admin_of_token(self._sender, self._token)
            and self.is_nft()
            and BlockchainManager().nft_exists(self._token)
        ):
            self.error = "NFT with this id already exists"
            logger.info(f"ERROR while adding transaction {self.error=} {self.id=}")

            return False
        return True

    def has_valid_signature(self):
        if not bool(self._signature):
            self.error = "transaction not signed"
            return False
        if not self._sender.verify(self._signature, self.__encode(full=False)):
            self.error = "Invalid signature"
            return False
        return True

    def valid(self, create=False):
        if not self.has_valid_signature() or not self.has_valid_attrs():
            print("Invalid transaction", self.error)
            return False
        return True

    # def validToCreate(self):
    #     return self.hasValidAttrs() and self.hasValidAttrsToCreate() and self.hasValidSignature()

    def __to_dict(self, full=True):
        """
        Used for in class computation
        :param full: includes signature field if true
        :return: transaction as a dict
        """
        d = {
            "id": self._id,
            "token": self._token,
            "sender": self._sender.__str__(),
            "recipient": self._recipient.__str__(),
            "amount": self._amount,
            "time": self._time,
            "smart_contract": self._smart_contract.__dict__(),
        }
        if full:
            d = {**d, **{"signature": self._signature}}
        return d

    def __encode(self, full=False):
        """
        Used for in class computation
        encode transaction
        :param full: bool, encode full transaction if true (including signature)
        :return: encoded transaction
        """
        return self.__to_dict(full).__str__()

    def __str__(self):
        """
        Used for export
        """
        return self.__dict__().__str__()

    def __dict__(self):
        """
        Used for export
        """
        return {
            **self.__to_dict(full=True),
            **{"signature": self._signature.encode(), "state": self.state.encode()},
        }

    def sign(self, private_key: PrivateKey):
        try:
            self._signature = private_key.sign(self.__encode(full=False))
        except BaseException as e:
            self.error = e
            logger.warning(f"Unable to sign transaction {e}")
            self._signature = None
        logger.info(f"signature {self._signature} {type(self._signature)}")

    @classmethod
    def from_dict(cls, dictionary, create=False):
        tx = cls(
            id_=dictionary["id"] if "id" in dictionary else None,
            token=dictionary["token"],
            sender=dictionary["sender"],
            recipient=dictionary["recipient"],
            amount=dictionary["amount"],
            time_=dictionary["time"] if "id" in dictionary else None,
            sc_=dictionary["smart_contract"]
            if "smart_contract" in dictionary
            else None,
            signature=dictionary["signature"] if "signature" in dictionary else None,
            private_key=dictionary["private_key"]
            if "private_key" in dictionary
            else None,
            state=State.decode(dictionary["state"]) if "state" in dictionary else None,
        )
        if not tx.valid(create=create):
            logger.warning(f"Invalid transaction {tx.error} {tx.__dict__()}")
            return tx
        return tx

    def is_nft(self):
        return self._token[:4] == "nft_"

    def is_item(self):
        return self._token[:5] == "item_"

    def spread(self, nodes):
        """
        Spread transaction to other nodes
        """
        if not self.valid():
            logger.warning("Can't spread an invalid transaction")
            return

        nodes.spread_transaction(self.__dict__())

    def can_be_added(self, txs):
        return self.state == State.WAITING and (
            self._smart_contract.is_validated() or self._smart_contract.run(txs=txs)
        )
