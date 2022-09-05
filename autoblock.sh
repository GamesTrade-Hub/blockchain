#!/bin/bash

# If first argument is start, start miner if stop, stop miner
if [ $# -eq 1 ] && [ "$1" = "start" ]; then
    echo "Starting miner..."

    screen -dmS auto_miner_prod
    screen -S auto_miner_prod -X stuff 'prod_node/bin/python3.8 src/autominer.py --node_address 127.0.0.1:5000\n'

    screen -dmS auto_miner_dev
    screen -S auto_miner_dev -X stuff 'prod_node/bin/python3.8 src/autominer.py --node_address 127.0.0.1:5010\n'

elif [ $# -eq 1 ] && [ "$1" = "stop" ]; then
    echo "Stopping miner..."

    screen -ls auto_miner_prod | grep -E '\s+[0-9]+\.' | awk -F ' ' '{print $1}' | while read s; do screen -XS $s quit; done
    screen -ls auto_miner_dev | grep -E '\s+[0-9]+\.' | awk -F ' ' '{print $1}' | while read s; do screen -XS $s quit; done

else
    echo "Usage: $0 [start|stop]"
fi

