from typing import List, Iterator

from src.blockchain.block import Block
import logging

from src.blockchain.transaction import Transaction, TransactionsList

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


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
        for tx in self.transactions:
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

    @property
    def last_blockhash(self):
        return self.last_block.hash

    @property
    def last_block(self) -> Block:
        return self._blocks[-1]

    def add_block(self, block):
        block.confirm_selected_transactions()
        self._blocks.append(block)

    @property
    def blocks(self) -> List[Block]:
        return self._blocks

    @property
    def transactions(self) -> TransactionsList:
        tl = TransactionsList()
        for block in self._blocks:
            tl += block.transactions
        return tl

    def get_balance_by_token(self, public_key, token) -> float:
        from src.blockchain.blockchain_manager import BlockchainManager
        balance = 0

        for tx in BlockchainManager().considered_transactions():
            if tx['recipient'] == public_key and tx['token'] == token:
                balance += tx['amount']
            if tx['sender'] == public_key and tx['token'] == token and tx['recipient'] != public_key:
                balance -= tx['amount']
        return balance

    def get_balance(self, public_key):
        from src.blockchain.blockchain_manager import BlockchainManager
        balance = {}

        for tx in BlockchainManager().considered_transactions():
            if tx['recipient'] == public_key:
                if tx['token'] not in balance:
                    balance[tx['token']] = 0
                balance[tx['token']] += tx['amount']
            if tx['sender'] == public_key and tx['recipient'] != public_key:
                if tx['token'] not in balance:
                    balance[tx['token']] = 0
                balance[tx['token']] -= tx['amount']
        return balance
