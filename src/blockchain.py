from src.tools import get_time, MetaSingleton, hash
from src.transaction import TransactionsList, State
from src.node import NodesList
from src.block import Chain, Block
from src.config import Host, NodeType
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# TODO when transaction are passed nodes to nodes int fields becomes string, this might create issues.


def dropDuplicates(l_):
    return [dict(t) for t in {tuple(d.items()) for d in l_}]


class Blockchain(metaclass=MetaSingleton):

    def __init__(self):
        self._type: NodeType = NodeType.UNKNOWN
        self.txs: TransactionsList = TransactionsList()
        # Create the genesis block
        genesis_block = Block(index=1, transactions=TransactionsList(), previous_hash='0000', nonce='genesis')

        self.chain = Chain(blocks=[genesis_block])
        self.nodes: NodesList = NodesList()
        self.current_block = None

        self.mining_process = None
        self.mining_process_queue = None

    def consideredTransactions(self):
        for tx in self.chain.transactions():
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
        else:
            logger.warning(f"Unable to set blockchain type current is {self._type}, wants {type_}")

    @property
    def chain_size(self):
        return self.chain.__len__()

    def getConnectedNodes(self):
        return self.nodes

    def addNode(self, address, type_=None, register_back=False, spread=False):
        """
        Add a new node to the list of nodes
        :param type_:
        :param spread: spread new node info to other nodes
        :param host: ip and port of the current api instance
        :param register_back: tell whether or not the node just registered received a call back to register the current node
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        added = self.nodes.addNode(address, type_=type_, register_back=register_back, spread=spread)

        if not added:
            return 400
        return 201

    def resolveConflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        rv = False

        # Grab and verify the chains from all the nodes in our network
        for chain, length in self.nodes.othersChains():
            rv = rv or self.replaceChainIfBetter(chain)
        return rv

    def replaceChainIfBetter(self, chain):
        # print('replaceChainIfBetter, chain:', chain)
        if chain.__len__() > self.chain.__len__():
            # FIXME if same size, take the one having the most transactions
            self.endCurrentMiningProcess()
            self.txs.updateStateCdt(from_=State.IN_CHAIN, to_=State.WAITING, cdt=lambda tx: True if self.chain.containsTx(tx) and not chain.containsTx(tx) else False)
            self.txs.updateStateCdt(from_=State.WAITING, to_=State.IN_CHAIN, cdt=lambda tx: True if chain.containsTx(tx) else False)
            self.chain = chain  # FIXME update transactions
            print('Chain replaced')
            return True
        return False

    def mine(self, spread=False):
        """
        Create a new Block in the Blockchain
        :return: New Block
        """

        if self.current_block is not None:
            return 'Is already Mining', 401

        if spread:
            self.nodes.spreadMiningRequest()

        tx_list: TransactionsList = TransactionsList(self.txs.select())

        if len(tx_list) == 0:
            return "Not enough transactions to mine", 401

        self.current_block = Block(index=self.chain.__len__() + 1,
                                   transactions=tx_list,
                                   previous_hash=self.chain.lastBlockhash())

        return "Mining of a new block started", 200

    def getBalance(self, public_key):
        return self.chain.getBalance(public_key)

    def getBalanceByToken(self, public_key, token):
        return self.chain.getBalanceByToken(public_key, token)

    def createTransaction(self, tx, spread=False):
        added, tx = self.txs.addTransactionFromDict(tx, create=True)

        if not added:
            return False, self.txs.error

        if spread:
            tx.spread(self.nodes)

        return True, 'ok'

    def createNFT(self, token, nb, gth_private_key):
        added, tx = self.txs.addTransaction(
            id_=None,
            token=f'nft_{hash(str(nb))}_{token}',
            sender=Blockchain.get_GTH_public_key(),
            private_key=gth_private_key,
            recipient=Blockchain.get_GTH_public_key(),
            amount=1,
            create=True
        )

        if not added:
            return False, self.txs.error

        return True, tx['token']

    def updateMiningState(self):
        """
        used to check if this node has found the solution to the POW
        :return:
        """
        if not self.current_block:
            print('current block?', self.current_block)
            return "No block mined", 400

        if not self.current_block.powFinished():
            print('pow not finished', self.current_block.powFinished())
            return "Pow not finished", 400

        # Reset the current list of transactions
        self.current_block.completeBlock()
        self.chain.addBlock(self.current_block)
        self.current_block = None

        self.nodes.spreadChain(self.chain)
        # If at some point, blockchain version is changed, check if these transactions are in, otherwise try to add them back.
        # Also, transactions in the blockchain after 10+ blocks can be removed because we can be kind of sure that they are in the blockchain for ever

        return 'Mining step finished, block found', 200

    def endCurrentMiningProcess(self):
        """
        If a mining process is going in this node, then end it.
        Probably because a better chain has been received.
        """
        self.current_block = None

    @staticmethod
    def is_GTH(public_key):
        return str(public_key) == Blockchain.get_GTH_public_key()

    @staticmethod
    def get_GTH_public_key():
        return '107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470'

    @staticmethod
    def get_time():
        return get_time()

    def nftExists(self, token):
        for tx in self.consideredTransactions():
            if tx['token'] == token:
                return True
        return False

    def __del__(self):
        logger.info('Blockchain.__del__: Informing other nodes of current exiting')
        self.nodes.removeMe()

