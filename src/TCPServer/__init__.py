import logging
import sys


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
logging.StreamHandler(sys.stdout)
