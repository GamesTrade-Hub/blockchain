import uuid
import sys
from urllib.parse import urlparse
from uuid import uuid4
import time
import requests
from flask import Flask, jsonify, request
from .blockchain import Blockchain, BcEncoder
import json
#import docker


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
print("Identifier :", node_identifier)

# client = docker.DockerClient()
# container = client.containers.get("magical_meitner")
# ip_add = container.attrs['NetworkSettings']['IPAddress']
# print("ip_add", ip_add)

# Instantiate the Blockchain
blockchain = Blockchain(verbose=True)


@app.route('/get_new_private_key', methods=['GET'])
def get_private_key():
    private_key = Blockchain.generate_private_key()
    response = {'message': f'{private_key}'}
    return jsonify(response), 201


@app.route('/get_new_public_key', methods=['GET'])
def get_public_key():
    values = request.get_json()
    if values is None or 'private_key' not in values:
        return "Error: Please supply a private key", 400
    private_key = values.get('private_key')
    public_key = Blockchain.generate_public_key(private_key, string=True)
    response = {'message': f'{public_key}'}
    return jsonify(response), 201


@app.route('/start', methods=['GET'])
def launch():
    response = {'message': f'node initialized'}
    return jsonify(response), 201


@app.route('/status', methods=['GET'])
def status():
    response = {'message': f'Node is OK'}
    return jsonify(response), 201


@app.route('/transaction/new', methods=['POST'])
def new_transactions():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'private_key', 'token']
    if not all(k in values for k in required):
        return f'Missing value among {", ".join(required)}', 400

    # print('new transaction sc', values['sc'] if 'sc' in values else "no sc")
    # Create a new transaction if the transaction is valid
    transaction, msg = blockchain.createTransaction(values['id'] if 'id' in values else None,
                                                    values['token'],
                                                    values['sender'],
                                                    values['recipient'],
                                                    values['amount'],
                                                    values['time'] if 'id' in values else None,
                                                    values['sc'] if 'sc' in values else None)
    if transaction is None:
        response = {'message': f"Transaction can't be created, Reason: {msg}"}
        return jsonify(response), 401
    # If the transaction already have an id when received, it means the transaction has been received by an other node and is spread out to others
    blockchain.addTransactionPool(transaction, values['private_key'], values['sender'], 'id' not in values)
    response = {'message': f'Transaction will be added, Reason: {msg}'}
    return json.dumps(response, cls=BcEncoder), 201


@app.route('/transaction/create_nft', methods=['POST'])
def create_nft():
    values = request.get_json()
    required = ['recipient', 'sender', 'private_key']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    transaction, msg = blockchain.createTransaction(
        values['id'] if 'id' in values else None,
        str('nft_') + str(uuid.uuid4()),  # TODO perform a check to ensure this doesn't exist yet
        values['sender'],
        values['recipient'],
        1,
        values['time'] if 'id' in values else None,
        values['sc'] if 'sc' in values else None
    )
    if transaction is None:
        return jsonify({'message': f'Transaction can\'t be created, Reason: {msg}'}), 401

    blockchain.addTransactionPool(transaction, values['private_key'], values['sender'], 'id' not in values)

    # print('token created', transaction["token"])
    return json.dumps({
        'message': f'Transaction will be added, Reason: {msg}',
        'token': transaction["token"]
    }), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': blockchain.chain_size,
    }
    return json.dumps(response, cls=BcEncoder), 200


@app.route('/ping', methods=['GET'])
def ping():
    return json.dumps({'pong': blockchain.getTmpState(),
                       'waitingTxs': blockchain.Txs}, cls=BcEncoder), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    code = 201
    message = 'New nodes have been added if not already present'

    nodes = values.get('nodes')
    if nodes is None or type(nodes) != list:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        code = blockchain.registerNode(node, register_back=True, host=request.host)
        if code == 202:
            print("Warning: Node already added")
            code = 201
        if code == 401:
            break

    if code == 401:
        message = "Error while adding nodes"

    return jsonify({
        'message': message,
        'total_nodes': list(blockchain.nodes)}), code


@app.route('/nodes/register_back', methods=['POST'])
def register_back_node():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()
    message = 'New node have been added'

    node = values.get('node')
    if node is None:
        return "Error: Please supply a valid node", 400

    code = blockchain.registerNode(node)
    if code == 401:
        message = "Error while adding node"

    response = {
        'message': message,
        'total_nodes': list(blockchain.nodes),
    }
    return json.dumps(response, cls=BcEncoder), code


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolveConflicts()

    response = {
        'message': 'Our chain is authoritative',
        'chain': blockchain.chain
    }
    if replaced:
        response['message'] = 'Our chain was replaced',

    return json.dumps(response, cls=BcEncoder), 200


@app.route("/nodes/list", methods=['GET'])
def get_nodes_list():
    balance = blockchain.getConnectedNodes()
    return jsonify({'nodes': balance}), 200


@app.route('/mine', methods=['GET'])
def mine():
    # Select transactions
    if blockchain.isReadyForTxsSelection() is False:
        if blockchain.isMining() is True:
            return 'Node already mining', 400
        return 'Node not ready to mine : Block bounds not found', 400

    # TODO spread the mining process to other nodes
    blockchain.selectTxs()

    # We run the proof of work algorithm to get the next proof...
    blockchain.newBlock()

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    # blockchain.new_transaction(
    #     sender="0",
    #     recipient=node_identifier,
    #     amount=1,
    # ) FIXME reward is for the fastest miner

    # Forge the new Block by adding it to the chain

    response = blockchain.last_block
    return json.dumps(response, cls=BcEncoder), 200


@app.route('/create_block', methods=['POST'])
def create_block():
    values = request.get_json() or {}

    response = blockchain.setupBlock(values['time_limit'] if 'time_limit' in values else None,
                                     values['block'] if 'block' in values else None)

    if response is None:
        return 'Can\'t create block', 400

    time_limit, block = response
    return jsonify({'time_limit': time_limit, 'block': block}), 200


#@app.route('/get_Txs', methods=['POST'])
#def get_Txs():
#    values = request.get_json()

#    time_limit = int(values.get('time_limit'))
#    if time_limit is None or time_limit <= 0:
#        return "Error: Please supply a valid time limit", 400

#    response = {
#        'Txs': blockchain.getTxs(time_limit),
#    }
#    return json.dumps(response, cls=BcEncoder), 200


@app.route("/get_balance", methods=['GET'])
def get_balance():
    values = request.get_json()

    if values is None or 'user_id' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.getBalance(values['user_id'])
    return jsonify(balance), 200


@app.route("/get_balance_by_token", methods=['POST'])
def get_balance_by_token():
    values = request.get_json()

    if values is None or 'user_id' not in values or 'token' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.getBalanceByToken(values['user_id'], values['token'])
    return jsonify({'balance': balance}), 200


@app.route("/testcd", methods=['GET'])
def test__():
    return 'test cd 8', 200

# TODO check pairs details
