import logging
from typing import Optional, Iterator

from src.blockchain.block import Block
from src.blockchain.chain import Chain
from src.blockchain.config import (
    Host,
    NodeType,
    PUBLIC_KEY,
    LIMIT_TRANSACTIONS_BLOCK,
)
from src.blockchain.keys import PublicKeyContainer, GTH_PUBLIC_KEY
from src.blockchain.node import NodesList
from src.blockchain.tools import get_time, MetaSingleton, hash__
from src.blockchain.transaction import TransactionsList, State, Transaction

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# TODO when transaction are passed nodes to nodes int fields becomes string, this might create issues.


def drop_duplicates(l_) -> list:
    return [dict(t) for t in {tuple(d.items()) for d in l_}]


class BlockchainManager(metaclass=MetaSingleton):
    """Main blockchain class that allows to do all needed operations on the underlying blockchain"""

    def __init__(self):
        """
        Initialize the blockchain. Create genesis block.
        """
        self._type: NodeType = NodeType.UNKNOWN
        self.txs: TransactionsList = TransactionsList()
        # Create the genesis block
        genesis_block: Block = Block(
            index=1,
            transactions=TransactionsList(),
            previous_hash="0000",
            validator=PUBLIC_KEY,
            nonce=None,
        )

        self.chain: Chain = Chain(blocks=[genesis_block])
        self.nodes: NodesList = NodesList()
        self.current_block: Optional[Block] = None

        self.mining_process = None
        self.mining_process_queue = None

    def considered_transactions(self) -> Iterator[Transaction]:
        """
        Return all transactions that are considered for the next block
        :return: yield transactions one by one
        """
        for tx in self.chain.transactions:
            yield tx
        for tx in self.txs.transactions(
                min_state=State.SELECTED, max_state=State.SELECTED
        ):
            yield tx

    @property
    def type(self) -> NodeType:
        """Return the type of the node"""
        return self._type

    @type.setter
    def type(self, type_) -> None:
        """Set the type of the node"""
        if isinstance(type_, NodeType) and (
                self._type is None or self._type == NodeType.UNKNOWN
        ):
            Host().type = type_
            self._type = type_
        elif type_ != self._type:
            logger.warning(
                f"Unable to set blockchain type current is {self._type}, wants {type_}"
            )

    @property
    def chain_size(self) -> int:
        """Return the size of the chain"""
        return self.chain.__len__()

    def get_connected_nodes(self) -> NodesList:
        """Return the list of connected nodes"""
        return self.nodes

    def add_node(
            self, address: str, type_=None, register_back=False, spread=False
    ) -> int:
        """
        Add a new node to the list of nodes
        :param address: Address of the node. Eg. 'http://192.168.0.5:5000'
        :param type_: Type of the node (optional)
        :param register_back: tell whether the node just registered received a call back to register the current node
        :param spread: spread new node info to other nodes
        :return: 201 if the node was added, 400 if not
        """

        added = self.nodes.add_node(
            address, type_=type_, register_back=register_back, spread=spread
        )

        if not added:
            return 400
        return 201

    def resolve_conflicts(self) -> bool:
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        logger.debug("Start resolveConflicts")
        rv = False

        # Grab and verify the chains from all the nodes in our network
        for chain, length in self.nodes.others_chains():
            rv = rv or self.replace_chain_if_better(chain)
        return rv

    def replace_chain_if_better(self, chain: Chain) -> bool:
        """
        If the chain is valid and longer than the current chain, replace it.
        :param chain: check to compare with the current chain
        :return: True if the chain was replaced, False if not
        """
        logger.info(f"Replace chain if better")
        if chain and chain.__len__() > self.chain.__len__():
            # self.end_current_mining_process()
            logger.info("Replace chain because the other one is longer")
            self.replace_chain(chain)
            return True

        oldest_transaction_mine = -1
        oldest_transaction_other = -1
        if chain and chain.__len__() == self.chain.__len__():
            for tx_c1, tx_c2 in zip(self.chain.transactions, chain.transactions):
                if tx_c1 < oldest_transaction_mine or tx_c1 == -1:
                    oldest_transaction_mine = tx_c1
                if tx_c2 < oldest_transaction_other or tx_c2 == -1:
                    oldest_transaction_other = tx_c2
            if oldest_transaction_mine > oldest_transaction_other:
                logger.info("Replace chain because the other has older transactions")
                self.replace_chain(chain)
                return True
        return False

    def replace_chain(self, chain) -> None:
        """
        Replace the local chain with the one received from a peer node
        :param chain: new chain to replace the current one
        :return: None
        """
        self.txs.update_state_cdt(
            from_=[State.IN_CHAIN, State.SELECTED, State.VALIDATED],
            to_=State.WAITING,
            cdt=lambda tx: True
            if self.chain.contains(tx) and not chain.contains(tx)
            else False,
        )
        self.txs.update_state_cdt(
            from_=[State.WAITING, State.SELECTED],
            to_=State.IN_CHAIN,
            cdt=lambda tx: True if chain.contains(tx) else False,
        )  # Some transactions are present twice, once in a block and once in self.txs
        self.chain = chain
        logger.info("Chain replaced")

    def new_authority_block(self, spread: bool = False) -> (str, int):
        """
        Create a new Block in the Blockchain
        :return: string message and error code
        """

        logger.debug("New authority block")
        logger.debug(f"Current block: {self.current_block is not None}")
        if self.current_block is not None:
            return "A block is already being created", 401

        logger.debug("select transactions")
        tx_list: TransactionsList = TransactionsList(self.txs.select())
        logger.debug(f"{tx_list.__len__()} transactions selected")

        if len(tx_list) < LIMIT_TRANSACTIONS_BLOCK and not spread:
            err_msg = "Not enough transactions to create a new block"
            logger.warning(err_msg)
            return err_msg, 401

        if len(tx_list) < LIMIT_TRANSACTIONS_BLOCK and spread:
            info_msg = "Not enough transactions to create a new block, spreading"
            logger.info(info_msg)
            self.nodes.spread_block_creation_request()
            return info_msg, 401

        self.current_block = Block(
            index=self.chain.__len__() + 1,
            transactions=tx_list,
            validator=PUBLIC_KEY,
            previous_hash=self.chain.last_blockhash,
        )

        self.chain.add_block(self.current_block)
        logger.info("Block created and added to chain. Spread to other nodes")
        self.current_block = None
        self.nodes.spread_chain(self.chain)

        return "New block created and spread", 200

    def get_balance(self, public_key) -> dict:
        """
        Return the balance of a public key
        :param public_key: public key of the account
        :return: dictionary with the balance for all the tokens
        """
        return self.chain.get_balance(public_key)

    def get_balance_by_token(self, public_key, token) -> float:
        """
        Return the balance of a public key for a specific token
        :param public_key: public key of the account
        :param token: token to check the balance
        :return: value of the balance for the token
        """
        return self.chain.get_balance_by_token(public_key, token)

    def create_transaction(self, tx, spread=False) -> (bool, str):
        """
        Create a new transaction to add to the next block
        :param tx: transaction to add
        :param spread: whether to spread the transaction to other nodes
        :return: (True, "ok") if the transaction was added, (False, error_message) if not
        """
        added, tx = self.txs.add_from_dict(tx, create=True)

        if not added:
            return False, self.txs.error

        if spread:
            tx.spread(self.nodes)

        return True, "ok"

    def create_nft(self, token: str,
                   nb: str,
                   adm_private_key: str,
                   adm_public_key: str,
                   ) -> (bool, str):
        """
        Create a new NFT to add to the next block
        :param token: name of the nft
        :param nb: index of the nft
        :param adm_private_key: Token Admin private key
        :return: (False, error_message) if the nft was not added, (True, nft id) if it was added
        """
        if '_' in token:
            return False, "Token name cannot contain '_'"

        added, tx = self.txs.create_add_transaction(
            id_=None,
            token=f"nft_{hash__(str(nb))}_{token}",
            sender=adm_public_key,
            private_key=adm_private_key,
            recipient=adm_public_key,
            amount=1,
            create=True,
        )

        if not added:
            return False, self.txs.error

        return True, tx["token"]

    @staticmethod
    def is_gth(public_key) -> bool:
        """
        Check if a public key is the GamesTrade Hub's public key
        :param public_key: public key to check
        :return: True if it is the GTH's public key, False otherwise
        """
        return str(public_key) == GTH_PUBLIC_KEY.encode()

    @staticmethod
    def is_admin(public_key: PublicKeyContainer) -> bool:
        """
        Check if a public key is an admin's public key
        :param public_key: public key to check
        :return: True if it is an admin's public key, False otherwise
        """
        return public_key.is_valid() and public_key.is_token_admin()

    @staticmethod
    def get_time() -> int:
        """
        :return: the current time in nanoseconds
        """
        return get_time()

    def nft_exists(self, token: str) -> bool:
        """
        Check if a nft exists
        :param token: name of the nft to check
        :return: True if it exists, False otherwise
        """
        for tx in self.considered_transactions():
            if tx["token"] == token:
                return True
        return False

    def __del__(self):
        logger.info("Blockchain.__del__: Informing other nodes of current exiting")
        self.nodes.remove_me()

    @classmethod
    def is_admin_of_token(cls, sender: PublicKeyContainer, token: str) -> bool:
        return sender.is_token_admin() and \
               (sender.data == token.split("_")[-1] or sender.data == "ADMINPASS")
