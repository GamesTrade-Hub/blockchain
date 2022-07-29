#!/bin/bash

screen -dmS auto_miner
screen -S auto_miner -X stuff 'prod_node/bin/python3.8 autominer.py\n'
