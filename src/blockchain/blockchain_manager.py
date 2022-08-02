from typing import List, Optional

from src.blockchain.chain import Chain
from src.blockchain.tools import get_time, MetaSingleton, hash__
from src.blockchain.transaction import TransactionsList, State
from src.blockchain.node import NodesList
from src.blockchain.block import Block
from src.blockchain.config import Host, NodeType, conf, PRIVATE_KEY, PUBLIC_KEY, LIMIT_TRANSACTIONS_BLOCK
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO when transaction are passed nodes to nodes int fields becomes string, this might create issues.


def drop_duplicates(l_):
    return [dict(t) for t in {tuple(d.items()) for d in l_}]


def get_authorized_nodes_public_keys():
    return conf.authorized_nodes_pbk


class BlockchainManager(metaclass=MetaSingleton):

    def __init__(self):
        self._type: NodeType = NodeType.UNKNOWN
        self.txs: TransactionsList = TransactionsList()
        # Create the genesis block
        genesis_block: Block = Block(
            index=1,
            transactions=TransactionsList(),
            previous_hash='0000',
            validator=PUBLIC_KEY,
            nonce=None
        )

        self.chain: Chain = Chain(blocks=[genesis_block])
        self.nodes: NodesList = NodesList()
        self.current_block: Optional[Block] = None

        self.mining_process = None
        self.mining_process_queue = None

        self.authorized_nodes_public_keys: List[str] = get_authorized_nodes_public_keys()

    def considered_transactions(self):
        for tx in self.chain.transactions:
            yield tx
        for tx in self.txs.transactions(min_state=State.SELECTED, max_state=State.SELECTED):
            yield tx

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type_):
        if isinstance(type_, NodeType) and (self._type is None or self._type == NodeType.UNKNOWN):
            Host().type = type_
            self._type = type_
        elif type_ != self._type:
            logger.warning(f"Unable to set blockchain type current is {self._type}, wants {type_}")

    @property
    def chain_size(self):
        return self.chain.__len__()

    def get_connected_nodes(self):
        return self.nodes

    def add_node(self, address, type_=None, register_back=False, spread=False):
        """
        Add a new node to the list of nodes
        :param address: Address of the node. Eg. 'http://192.168.0.5:5000'
        :param type_: Type of the node (optional)
        :param register_back: tell whether the node just registered received a call back to register the current node
        :param spread: spread new node info to other nodes
        :return: True if the node was added, False if not
        """

        added = self.nodes.add_node(address, type_=type_, register_back=register_back, spread=spread)

        if not added:
            return 400
        return 201

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        logger.debug('Start resolveConflicts')
        rv = False

        # Grab and verify the chains from all the nodes in our network
        for chain, length in self.nodes.others_chains():
            rv = rv or self.replace_chain_if_better(chain)
        return rv

    def replace_chain_if_better(self, chain):
        logger.info(f"Replace chain if better")
        if chain and chain.__len__() > self.chain.__len__():
            # self.end_current_mining_process()
            logger.info('Replace chain because the other one is longer')
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
                logger.info('Replace chain because the other has older transactions')
                self.replace_chain(chain)
                return True
        return False

    def replace_chain(self, chain):
        self.txs.update_state_cdt(
            from_=[State.IN_CHAIN, State.SELECTED, State.VALIDATED], to_=State.WAITING,
            cdt=lambda tx: True if self.chain.contains(tx) and not chain.contains(tx) else False
        )
        self.txs.update_state_cdt(
            from_=[State.WAITING, State.SELECTED], to_=State.IN_CHAIN,
            cdt=lambda tx: True if chain.contains(tx) else False
        )  # Some transactions are present twice, once in a block and once in self.txs
        self.chain = chain
        logger.info('Chain replaced')

    def mine(self, spread=False):
        """
        DEPRECATED
        Create a new Block in the Blockchain
        :return: New Block
        """

        logger.warning("Mine is deprecated, use new_authority_block instead")

        if self.current_block is not None:
            return 'Is already Mining', 401

        tx_list: TransactionsList = TransactionsList(self.txs.select())

        if len(tx_list) == 0:
            return "Not enough transactions to mine", 401

        if spread:
            self.nodes.spread_mining_request()

        self.current_block = Block(
            index=self.chain.__len__() + 1,
            transactions=tx_list,
            previous_hash=self.chain.last_blockhash,
            validator=PUBLIC_KEY
        )

        return "Mining of a new block started", 200

    def new_authority_block(self, spread=False) -> (str, int):
        """
        Create a new Block in the Blockchain
        :return: New Block
        """

        logger.debug("New authority block")
        logger.debug(f"Current block: {self.current_block is not None}")
        if self.current_block is not None:
            return 'A block is already being created', 401

        logger.debug('select transactions')
        tx_list: TransactionsList = TransactionsList(self.txs.select())
        logger.debug(f"{tx_list.__len__()} transactions selected")

        if len(tx_list) < LIMIT_TRANSACTIONS_BLOCK and not spread:
            logger.warning("Not enough transactions to mine")
            return "Not enough transactions to create new block", 401

        if len(tx_list) < LIMIT_TRANSACTIONS_BLOCK and spread:
            logger.info("Not enough transactions to mine. Spreading block/new to other nodes")
            self.nodes.spread_block_creation_request()
            return "Not enough transactions to create new block. Spread to others", 401

        self.current_block = Block(
            index=self.chain.__len__() + 1,
            transactions=tx_list,
            validator=PUBLIC_KEY,
            previous_hash=self.chain.last_blockhash
        )

        self.chain.add_block(self.current_block)
        logger.info('Block created and added to chain. Spread to other nodes')
        self.current_block = None
        self.nodes.spread_chain(self.chain)

        return "New block created and spread", 200

    def get_balance(self, public_key) -> dict:
        return self.chain.get_balance(public_key)

    def get_balance_by_token(self, public_key, token) -> float:
        return self.chain.get_balance_by_token(public_key, token)

    def create_transaction(self, tx, spread=False):
        added, tx = self.txs.add_from_dict(tx, create=True)

        if not added:
            return False, self.txs.error

        if spread:
            tx.spread(self.nodes)

        return True, 'ok'

    def create_nft(self, token, nb, gth_private_key):
        added, tx = self.txs.create_add_transaction(
            id_=None,
            token=f'nft_{hash__(str(nb))}_{token}',
            sender=BlockchainManager.get_gth_public_key(),
            private_key=gth_private_key,
            recipient=BlockchainManager.get_gth_public_key(),
            amount=1,
            create=True
        )

        if not added:
            return False, self.txs.error

        return True, tx['token']

    def update_mining_state(self):
        """
        DEPRECATED
        used to check if this node has found the solution to the POW
        :return:
        """
        logger.warning("update_mining_state is deprecated")
        if not self.current_block:
            logger.debug(f'current block? {self.current_block}')
            return "No block mined", 400

        if not self.current_block.pow_finished():
            logger.info(f'pow not finished {self.current_block.pow_finished()}')
            return "Pow not finished", 400

        # Reset the current list of transactions
        self.current_block.add_found_nonce_and_close_queues()
        self.chain.add_block(self.current_block)
        self.current_block = None

        self.nodes.spread_chain(self.chain)
        # If at some point, blockchain version is changed, check if these transactions are in, otherwise try to add them back.
        # Also, transactions in the blockchain after 10+ blocks can be removed because we can be kind of sure that they are in the blockchain for ever

        return 'Mining step finished, block found', 200

    def end_current_mining_process(self):
        """
        DEPRECATED
        If a mining process is going on in this node, then end it.
        Probably because a better chain has been received.
        """
        logger.warning("end_current_mining_process is deprecated")
        self.current_block = None

    @staticmethod
    def is_gth(public_key):
        return str(public_key) == BlockchainManager.get_gth_public_key()

    @staticmethod
    def get_gth_public_key():
        return '107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470'

    @staticmethod
    def get_time():
        return get_time()

    def nft_exists(self, token):
        for tx in self.considered_transactions():
            if tx['token'] == token:
                return True
        return False

    def __del__(self):
        logger.info('Blockchain.__del__: Informing other nodes of current exiting')
        self.nodes.remove_me()

