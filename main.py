from argparse import ArgumentParser
from src import app

# FIXME regrouper ça et wsgi en mettant en place config

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5002, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
