"""
Flask API that allows the user to use route "new_node" to create a new node.
It runs on port 5001.
"""


from uuid import uuid4
import time
import requests
from flask import Flask, jsonify, request
import json
import sys
import signal
import logging
# from log import Log

# log = Log().getLogger()
from src.interface.autorunner import AutoRunner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    gunicorn_logger.setLevel(logging.DEBUG)
    logger.handlers = gunicorn_logger.handlers
    logger.setLevel(gunicorn_logger.level)

logger.info("run blockchain/server.py")

ar = AutoRunner()

# Instantiate the Node
app = Flask(__name__)


@app.route('/nodes/new', methods=['GET', 'POST'])
def consensus():

    response = {
        'message': 'The new node is being created',
    }
    values = request.get_json()

    ar.create_node_instance(values['name'] if 'name' in values else None)

    return json.dumps(response), 200


@app.route('/nodes/terminate', methods=['GET', 'POST'])
def consensus():

    response = {
        'message': 'node terminated',
    }
    values = request.get_json()

    required = ['id']

    if not all(k in values for k in required):
        return jsonify({'message': f'Missing value among {", ".join(required)}'}), 400

    ar.terminate_instance(values['id'])

    return json.dumps(response), 200


@app.route('/nodes/terminate_all', methods=['GET', 'POST'])
def consensus():

    response = {
        'message': 'nodes terminated',
    }

    ar.terminate_all_instances()

    return json.dumps(response), 200



