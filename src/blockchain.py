import hashlib
import json
import sys
import uuid
from urllib.parse import urlparse
from uuid import uuid4
import time
from fastecdsa import curve, ecdsa, keys, point
import requests
from datetime import datetime
from enum import Enum
from src.smart_contracts import SmartContract, Type


# TODO when transaction are passed nodes to nodes int fields becomes string, this might create issues.

class BcEncoder(json.JSONEncoder):
    def default(self, o):
        # print("start", o)
        # print(o.__dict__)
        # for i in o.__dict__:
        #     print(':', i, o.__dict__[i])
        #     if o.__dict__[i].__class__.__module__ != 'builtins':
        #         print("no builtin result", o.__dict__[i].__class__.__module__,  json.dumps(o.__dict__[i], cls=BcEncoder))
        return {i: (o.__dict__[i].__str__() if o.__dict__[i].__class__.__module__ != '__builtin__' else o.__dict__[i]) for i in o.__dict__}


class Step(Enum):
    IDLE = 0
    SETUP_BLOCK_BOUNDS = 1
    WAITING_FOR_TXS_SELECTION = 2
    SELECT_TXS = 3
    MINING = 4


def dropDuplicates(l_):
    return [dict(t) for t in {tuple(d.items()) for d in l_}]


class Blockchain:
    def __init__(self, verbose=False):
        self.tmp_state = 0
        self.step = Step.IDLE

        self.Txs = list()
        self.selected_Txs = list()
        self.time_limit_Txs = None

        self.chain = []
        self.nodes = list()
        self.print_v = print if verbose else lambda *a, **k: None

        # Create the genesis block
        self.newBlock(previous_hash='1', nonce=100)
        self.print_v("Blockchain coin created")

    @property
    def chain_size(self):
        return len(self.chain)

    @property
    def last_block(self):
        return self.chain[-1]

    def getConnectedNodes(self):
        return self.nodes

    def registerNode(self, address, register_back=False, host=''):
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
            if parsed_url.scheme:
                new_node = parsed_url.scheme + ':' + parsed_url.path
            else:
                new_node = parsed_url.path
        else:
            raise ValueError('Invalid URL')

        if new_node in self.nodes:
            return 202

        self.nodes.append(new_node)
        # print("add node", new_node)

        if not register_back:
            return 201

        try:
            requests.post(f'http://{new_node}/nodes/register_back', json={"node": host})
        except requests.exceptions.RequestException as e:
            print("ERROR", e, file=sys.stderr)
            return 401
        return 201

    def validChain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # print(f'{last_block}')
            # print(f'{block}')
            # print("\n-----------\n")
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

    def resolveConflicts(self):
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

        # for node in neighbours:
        #     try:
        #         requests.get(f'http://{node}/nodes/resolve')
        #     except ConnectionRefusedError:
        #         print("[ConnectionRefusedError] Connection to", f"http://{node}", "refused", file=sys.stderr)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length == max_length and self.validChain(chain) and chain[-1]['pow_time'] < self.last_block['pow_time']:
                        max_length = length
                        new_chain = chain

                    if length > max_length and self.validChain(chain):
                        max_length = length
                        new_chain = chain

            except ConnectionRefusedError:
                print("[ConnectionRefusedError] Connection to", f"http://{node}", "refused", file=sys.stderr)

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def newBlock(self, nonce=None, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param nonce: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        if self.step == Step.SELECT_TXS:
            self.step = Step.MINING

        if self.step != Step.MINING and nonce is None:
            return None

        block = {
            'index': self.chain_size + 1,
            'transactions_timestamp': self.time_limit_Txs,
            'transactions': dropDuplicates(self.selected_Txs),
            'previous_hash': previous_hash or self.last_block['hash'],
        }
        block['nonce'] = nonce or self.proofOfWork(self.hash(block))  # TODO this task can be canceled if an other node has found
        block['pow_time'] = Blockchain.get_time()
        block['hash'] = self.hash(block)

        # Reset the current list of transactions
        self.Txs = list([tx for tx in self.Txs if tx['id'] not in [tx_['id'] for tx_ in self.selected_Txs]])
        self.time_limit_Txs = None
        self.selected_Txs = list()
        self.step = Step.IDLE

        self.chain.append(block)
        return block

    # def newTransaction(self, transaction_id, sender, recipient, amount, time_stamp):
    #     """
    #     Creates a new transaction to go into the next mined Block
    #     :param transaction_id: id of the transaction. If None, this node initiate the transaction and send it to others.
    #     :param sender: Address of the Sender
    #     :param recipient: Address of the Recipient
    #     :param amount: Amount
    #     :param time_stamp: When the transaction was sent
    #     :return: The index of the Block that will hold this transaction
    #     """
    #
    #     transaction = {
    #         'id': transaction_id or str(uuid4()),
    #         'sender': sender,
    #         'recipient': recipient,
    #         'amount': amount,
    #         'time': time_stamp or time.time_ns()
    #     }
    #     self.Txs.append(transaction)
    #
    #     # if transaction_id is None:
    #     #     for node in self.nodes:
    #     #         response = requests.post(f'http://{node}/transaction/new', json=transaction)
    #     #
    #     #         if response.status_code != 200:
    #     #             print(f"Transaction sent to {node} received error code {response.status_code}")
    #
    #     return self.last_block['index'] + 1

    def proofOfWork(self, block_hash):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous nonce, and p' is the new nonce

        :return: <int>
        """

        nonce = 0
        while self.valid_proof(block_hash, nonce) is False:
            nonce += 1

        return nonce

    def selectTxs(self):
        """
        """

        if self.step == Step.WAITING_FOR_TXS_SELECTION:
            self.step = Step.SELECT_TXS

        if self.step != Step.SELECT_TXS:
            print(f'Wrong step for selecting Txs, current step is {self.step}', file=sys.stderr)
            return

        # print("DEBUG self.Txs", self.Txs)  # FIXME to remove
        self.selected_Txs = list([tx for tx in self.Txs if self.transactionCanBeAdded(tx)])
        # print("DEBUG self.selected_Txs", self.selected_Txs)  # FIXME to remove
        self.step = Step.MINING

    def setTmpState(self, state=1):
        self.tmp_state = state

    def getTmpState(self):
        return self.tmp_state

    def transactionCanBeAdded(self, transaction):
        # print('transactionCanBeAdded', transaction['time'], self.time_limit_Txs, transaction['time'] < self.time_limit_Txs, transaction['sc'].run(Txs=self.Txs))
        return transaction['time'] < self.time_limit_Txs and transaction['sc'].run(Txs=self.Txs)

    def setupBlock(self, time_limit, block):
        if self.step == Step.IDLE:
            self.step = Step.SETUP_BLOCK_BOUNDS

        if self.step != Step.SETUP_BLOCK_BOUNDS:
            print(f'Wrong step for setup block bounds, current step is {self.step}', file=sys.stderr)
            return

        self.time_limit_Txs = Blockchain.get_time()

        if time_limit and self.time_limit_Txs > time_limit:  # Don't accept a time higher than your current
            self.time_limit_Txs = time_limit

        if time_limit is None:
            for node in self.nodes:
                requests.post(f'http://{node}/create_block', json={"time_limit": self.time_limit_Txs,
                                                                   "block": self.chain_size + 1})

        self.step = Step.WAITING_FOR_TXS_SELECTION
        # print('final', self.time_limit_Txs)
        return self.time_limit_Txs, self.chain_size + 1

    def isReadyForTxsSelection(self):
        return self.step == Step.WAITING_FOR_TXS_SELECTION

    def isMining(self):
        return self.step == Step.MINING

    def getStep(self):
        return self.step

    def getTxs(self, time_limit):
        return [tx for tx in self.Txs if tx['time'] < time_limit]

    def getBalance(self, public_key):
        balance = {}

        if Blockchain.is_GTH(public_key):
            return -1

        for block in self.chain:
            # print("DEBUG NEXT BLOCK", block['hash'], file=sys.stderr)
            for tx in block['transactions']:
                # print("DEBUG 1 balance", balance, tx, file=sys.stderr)
                if tx['recipient'] == public_key:
                    if tx['token'] not in balance:
                        balance[tx['token']] = 0
                    balance[tx['token']] += tx['amount']
                if tx['sender'] == public_key:
                    if tx['token'] not in balance:
                        balance[tx['token']] = 0
                    balance[tx['token']] -= tx['amount']
                # print("DEBUG 2 balance", balance, tx, file=sys.stderr)

        return balance

    def getBalanceByToken(self, public_key, token):
        balance = 0

        if Blockchain.is_GTH(public_key):
            return -1

        for block in self.chain:
            # print("DEBUG NEXT BLOCK", block['hash'], file=sys.stderr)
            for tx in block['transactions']:
                print("DEBUG 1 balance", balance, tx, file=sys.stderr)
                if tx['recipient'] == public_key and tx['token'] == token:
                    balance += tx['amount']
                if tx['sender'] == public_key and tx['token'] == token:
                    balance -= tx['amount']
                # print("DEBUG 2 balance", balance, tx, file=sys.stderr)

        return balance

    def createTransaction(self, transaction_id, token, sender, recipient, amount, time_, smart_contract=None):
        if sender == recipient:
            return None, 'Sender and recipient can\'t be the same'
        # FIXME also have to check that other transactions doesn't change this statement. Maybe this check has to be done at the transactions selection step
        if self.is_GTH(sender) is False and self.getBalanceByToken(sender, token) < amount:
            return None, 'User does not have enough money to proceed the transaction'

        tx_id = transaction_id or str(uuid4())
        transaction = {  # TODO create a class for this object
            'id': tx_id,
            'token': token,
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'time': time_ or Blockchain.get_time(),
            'sc': SmartContract(self.chain, self.Txs, smart_contract, tx_id)
        }
        # print("create transaction at time", transaction['time'], "id", transaction["id"])

        if transaction['sc'].contractType == Type.INVALID:
            return None, 'Invalid smart contract'
        return transaction, "ok"

    def addTransactionPool(self, transaction, private_key, public_key, transmission):
        """
        Add transaction to waiting transactions list, spread the transaction to other nodes it transmission is True
        :param public_key: public key of the sender
        :param transaction: transaction content
        :param private_key: private key of the sender
        :param transmission: spread out the transaction to other nodes it transmission is True
        :return: index of the last block in the chain [useless]
        """
        # serializable_transaction = transaction.copy()
        # serializable_transaction['sc'] = serializable_transaction['sc'].__str__()

        # TODO you are not supposed to send private key, instead the node have to create the transaction then send it back to the guy who want the transaction to get the encrypted version
        signature = Blockchain.getSignature(transaction, private_key)
        public_key = Blockchain.public_key_to_point(public_key)
        encoded_transaction = json.dumps(transaction, sort_keys=True, cls=BcEncoder).encode()
        is_valid = ecdsa.verify(signature, encoded_transaction, public_key, curve.secp256k1, ecdsa.sha256)

        if not is_valid:
            print(f'Warning: transaction {transaction} is not valid, signature check failed.')
            return self.last_block['index']

        # print('append in Txs', transaction)
        self.Txs.append(transaction)

        if not transmission:
            return self.last_block['index'] + 1

        # Transmission to other nodes
        for node in self.nodes:
            # print("dump with bcencoder")
            tmp = json.dumps(transaction, cls=BcEncoder)
            # print("result", tmp)
            # print('re load')
            json_transaction = json.loads(tmp)
            json_transaction['private_key'] = private_key  # TODO as explained above
            # print("send transaction dict\n", json_transaction, "\nfor transaction dict\n", transaction)
            response = requests.post(f'http://{node}/transaction/new', json=json_transaction)

            if response.status_code != 201:
                print(f"Transaction sent to {node} received error code {response.status_code}, Reason: {response.reason}, {response.content}")

        return self.last_block['index'] + 1

    @staticmethod
    def generate_private_key():
        private_key = keys.gen_private_key(curve.secp256k1)
        return private_key

    @staticmethod
    def generate_public_key(private_key, string=False):
        public_key = keys.get_public_key(private_key, curve.secp256k1)
        if string:
            return Blockchain.point_to_public_key(public_key)
        return public_key

    @staticmethod
    def getSignature(transaction, private_key):
        encoded_transaction = json.dumps(transaction, sort_keys=True, cls=BcEncoder).encode()
        signature = ecdsa.sign(encoded_transaction, private_key, curve.secp256k1, ecdsa.sha256)
        return signature

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        do_not_use = ['hash', 'nonce']
        block = {a: block[a] for a in block if a not in do_not_use}
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        # print("block to encode", block)  FIXME to remove
        block_string = json.dumps(block, sort_keys=True, cls=BcEncoder).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(block_hash, nonce):
        """
        Validates the Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{block_hash}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def is_GTH(public_key):
        return str(public_key) == '107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470'

    @staticmethod
    def public_key_to_point(public_key):
        pk = str(public_key).split('A')
        return point.Point(int(pk[0]), int(pk[1]), curve.secp256k1)

    @staticmethod
    def point_to_public_key(key_as_point):
        return str(key_as_point.x) + 'A' + str(key_as_point.y)

    @staticmethod
    def get_time():
        return time.time_ns()

    # @staticmethod
    # def is_GTH(private_key):
    #     return hashlib.sha224(str.encode(str(private_key))).hexdigest() == '16e32b6f4cede45149e02a0f81499f97fe7e6e79ee337492ff131bcf'


# 2081444576893621343727462635361680480016528058863000989987875154810052104272519241468249812662668563130259817649756265743308017717653468619451285872265293
# 2081444576893621343727462635361680480016528058863000989987875154810052104272519241468249812662668563130259817649756265743308017717653468619451285872265293
