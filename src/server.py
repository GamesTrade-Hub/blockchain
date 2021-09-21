import flask
import sys
from urllib.parse import urlparse
from uuid import uuid4
import time
import requests
from flask import Flask, jsonify, request
from .blockchain import Blockchain

# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
print("Identifier :", node_identifier)

blockchain = None


@app.route('/start', methods=['GET'])
def launch():
    global blockchain
    if blockchain is None:
        blockchain = Blockchain(verbose=True)
    response = {'message': f'node initialized'}
    return jsonify(response), 201


@app.route('/stop', methods=['GET'])
def stop():
    global blockchain
    blockchain = None
    response = {'message': f'node stopped'}
    return jsonify(response), 201


@app.route('/status', methods=['GET'])
def status():
    if blockchain is None:
        response = {'message': f'Node isn\'t initialized'}
    else:
        response = {'message': f'Node is initialized'}
    return jsonify(response), 201


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing value', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['id'] if 'id' in values else None,
                                       values['sender'],
                                       values['recipient'],
                                       values['amount'],
                                       values['time'] if 'id' in values else None
                                       )

    response = {'message': f'Transaction will be added to Block {index} or the next one'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    response = {
        'chain': blockchain.chain,
        'length': blockchain.chain_size,
    }
    return jsonify(response), 200


@app.route('/wait', methods=['POST'])
def wait():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()

    blockchain.setTmpState(12)
    if values and 'seconds' in values:
        time.sleep(int(values['seconds']))
    else:
        time.sleep(20)
    return jsonify({}), 200


@app.route('/ping', methods=['GET'])
def ping():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    print("PING", blockchain.getTmpState(), file=sys.stderr)
    return jsonify({'pong': blockchain.getTmpState()}), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.registerNode(node, register_back=True, host=request.host)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/register_back', methods=['POST'])
def register_back_node():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()

    node = values.get('node')
    if node is None:
        return "Error: Please supply a valid node", 400

    blockchain.registerNode(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    replaced = blockchain.resolveConflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route("/nodes/list", methods=['GET'])
def get_nodes_list():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    balance = blockchain.getConnectedNodes()
    return jsonify({'nodes': balance}), 200


@app.route('/mine', methods=['GET'])
def mine():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    # Select transactions
    if blockchain.isReadyForTxsSelection() is False:
        if blockchain.isMining() is True:
            return 'Node already mining', 400
        return 'Node not ready to mine : Block bounds not found', 400

    blockchain.select_Txs()

    # We run the proof of work algorithm to get the next proof...
    blockchain.new_block()

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    # blockchain.new_transaction(
    #     sender="0",
    #     recipient=node_identifier,
    #     amount=1,
    # ) FIXME reward is for the fastest miner

    # Forge the new Block by adding it to the chain

    response = blockchain.last_block
    return jsonify(response), 200


@app.route('/create_block', methods=['POST'])
def create_block():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json() or {}

    response = blockchain.setupBlock(values['time_limit'] if 'time_limit' in values else None,
                                     values['block'] if 'block' in values else None)

    if response is None:
        return 'Can\'t create block', 400

    time_limit, block = response
    return jsonify({'time_limit': time_limit, 'block': block}), 200


@app.route('/get_Txs', methods=['POST'])
def get_Txs():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()

    time_limit = int(values.get('time_limit'))
    if time_limit is None or time_limit <= 0:
        return "Error: Please supply a valid time limit", 400

    response = {
        'Txs': blockchain.get_Txs(time_limit),
    }
    return jsonify(response), 200


@app.route("/get_balance", methods=['GET'])
def get_balance():
    if blockchain is None:
        response = {'message': f'Failed: node not initialized'}
        return jsonify(response), 401
    values = request.get_json()

    if 'user_id' not in values:
        return 'Invalid request please specify user id', 400

    balance = blockchain.get_balance(values['user_id'])
    return jsonify({'balance': balance}), 200


@app.route("/testcd", methods=['GET'])
def test__():
    return 'test cd 8', 200

# TODO check pairs details
