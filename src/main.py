from argparse import ArgumentParser

import flask
from flask import Flask, request

from blockchain import Blockchain

if __name__ == '__main__':
    bc = Blockchain()

# Docker ?