from src.blockchain import Blockchain
from src.blockchain import Chain
from src.tools import BcEncoder
from src.keys import PublicKey, PrivateKey
from src.config import Host

import uuid
import sys
from urllib.parse import urlparse
from uuid import uuid4
import time
import requests
from flask import Flask, jsonify, request
import json

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
host = Host()
blockchain = Blockchain()


@app.route('/get_new_private_key', methods=['GET'])
def get_private_key():
    host.host = request.host

    private_key = PrivateKey.generate(encoded=True)
    response = {'message': f'{private_key}'}
    return jsonify(response), 201


@app.route('/get_new_public_key', methods=['GET'])
def get_public_key():
    host.host = request.host

    values = request.get_json()
    if values is None or 'private_key' not in values:
        return "Error: Please supply a private key", 400
    private_key = values.get('private_key')
    public_key = PublicKey.generate_from_private_key(private_key, encoded=True)
    response = {'message': f'{public_key}'}
    return jsonify(response), 201


@app.route('/start', methods=['GET'])
def launch():
    host.host = request.host
    response = {'message': f'node initialized'}
    return jsonify(response), 200


@app.route('/status', methods=['GET'])
def status():
    host.host = request.host

    response = {'message': f'Node is OK'}
    return jsonify(response), 200


@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    host.host = request.host
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount', 'private_key', 'token']
    if not all(k in values for k in required):
        print('return', f'Missing value among {", ".join(required)}', 400)
        return f'Missing value among {", ".join(required)}', 400

    print('new transaction sc', values['sc'] if 'sc' in values else "no sc")
    # Create a new transaction if the transaction is valid
    created, msg = blockchain.createTransaction(values, spread=True)
    if not created:
        return jsonify({'message': f"Transaction can't be created, Reason: {msg}"}), 401
    return jsonify({'message': f'ok'}), 201


@app.route('/create_nft', methods=['POST'])
def create_nft():
    """
    :root_param token: the token that have to be used to buy the NFT
    :root_param nb: id of the nft to prevent nft having the same id
    :root_param private_key : private key of gth
    :return:
    """
    host.host = request.host

    values = request.get_json()
    required = ['token', 'nb', 'gth_private_key']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    created, msg = blockchain.createNFT(token=values['token'],
                                        nb=values['nb'],
                                        gth_private_key=values['gth_private_key'])
    if not created:
        return f'Transaction can\'t be created, Reason: {msg}', 401
    return jsonify({'id': msg}), 201


@app.route('/transaction/add', methods=['POST'])
def add_transaction():
    host.host = request.host

    values = request.get_json()

    required = ['tx']
    if not all(k in values for k in required):
        return f'Missing value among {", ".join(required)}', 400

    print("values", type(values), values)
    created, msg = blockchain.createTransaction(values['tx'], spread=False)
    if created:
        return 'Transaction added', 201
    return msg, 401


@app.route('/create_item', methods=['POST'])
def create_item():
    host.host = request.host

    """
    :root_param token: the token that have to be used to buy the item
    :root_param nb: id of the item to prevent nft having the same id
    :root_param private_key : private key of gth
    :return:
    """
    values = request.get_json()
    required = ['token', 'nb']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    return json.dumps({
        'message': f'Transaction will be added, Reason: ok',
        'token': f'item_{hash(str(values["nb"]))}_{values["token"]}'
    }), 201


@app.route('/chain', methods=['GET'])
def chain():
    host.host = request.host

    response = {
        'chain': blockchain.chain.__dict__(),
        'length': blockchain.chain_size,
    }
    return json.dumps(response), 200


@app.route('/ping', methods=['GET'])
def ping():
    host.host = request.host

    return json.dumps({'pong': 'oui',
                       'waitingTxs': blockchain.txs.__dict__()}), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    host.host = request.host
    values = request.get_json()
    code = 201
    message = 'New nodes have been added if not already present'

    nodes = values.get('nodes')
    if nodes is None or type(nodes) != list:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        code = blockchain.registerNode(node, register_back=True)
        if code == 400:
            print("Warning: error while adding node", node)
            code = 400

    if code == 401:
        message = "Error while adding nodes"

    return jsonify({
        'message': message,
        'total_nodes': blockchain.nodes.__str__()}), code


@app.route('/nodes/register_back', methods=['POST'])
def register_back_node():
    host.host = request.host

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
        'total_nodes': str(blockchain.nodes),
    }
    return json.dumps(response), code


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    host.host = request.host

    replaced = blockchain.resolveConflicts()

    response = {
        'message': 'Our chain is authoritative',
        'chain': blockchain.chain.__dict__()
    }
    if replaced:
        response['message'] = 'Our chain was replaced',

    return json.dumps(response), 200


@app.route("/nodes/list", methods=['GET'])
def get_nodes_list():
    host.host = request.host
    balance = blockchain.getConnectedNodes()
    return jsonify({'nodes': balance}), 200


@app.route('/mine', methods=['GET'])
def mine():
    host.host = request.host
    values = request.get_json()

    response, code = blockchain.updateMiningState()

    if code:
        return jsonify(response), code

    if values and 'spread' in values and values['spread'] is True:
        print('spread mine process')
        response, code = blockchain.mine(spread=True)

    else:
        response, code = blockchain.mine(spread=False)

    if code != 200:
        return jsonify(response), code

    return json.dumps(response), code


@app.route('/chain_found', methods=['POST'])
def chain_found():
    host.host = request.host

    values = request.get_json()
    required = ['chain']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    print('raw chain received', values['chain'])
    blockchain.replaceChainIfBetter(Chain.from_dict(values['chain']))
    return 'ok', 200


@app.route("/get_balance", methods=['GET'])
def get_balance():
    host.host = request.host

    values = request.get_json()

    if values is None or 'user_id' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.getBalance(values['user_id'])
    return jsonify(balance), 200


@app.route("/get_balance_by_token", methods=['POST'])
def get_balance_by_token():
    host.host = request.host

    values = request.get_json()

    if values is None or 'user_id' not in values or 'token' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.getBalanceByToken(values['user_id'], values['token'])
    return jsonify({'balance': balance}), 200


@app.route("/testcd", methods=['GET'])
def test__():
    return 'test cd 8', 200

# TODO check pairs details
