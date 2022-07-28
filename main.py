from argparse import ArgumentParser
from src.blockchain.server import app, Blockchain
from src.blockchain.config import NodeType, Host
from time import sleep


# FIXME regrouper ça et wsgi en mettant en place config


def debug():
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-t', '--type', default='all', type=str, help='Type of node (all|miner|manager)', choices=['all', 'miner', 'manager'])
    # parser.add_argument('-fc', '--first_connection', default='http://20.188.58.215:5000', type=str, help='first connection url')
    parser.add_argument('-fc', '--first_connection', default='http://127.0.0.1:5000', type=str, help='first connection url (or \'none\'')
    args = parser.parse_args()

    bc: Blockchain = Blockchain()
    bc.type = NodeType(args.type)
    if args.first_connection != 'none':
        bc.add_node(args.first_connection, register_back=True)
    app.run(host='0.0.0.0', port=Host().port, debug=False)  # if debug is True server is started twice


if __name__ == '__main__':
    debug()
