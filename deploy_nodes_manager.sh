#!/bin/bash

sudo apt-get install software-properties-common -y

sudo add-apt-repository main -y
sudo add-apt-repository universe -y
sudo add-apt-repository restricted -y
sudo add-apt-repository multiverse -y
sudo apt update -y

sudo apt-get install python3 -y
sudo apt-get install python3-distutils python-setuptools python3-dev build-essential libgmp3-dev python3-pip gunicorn -y

echo "Install venv ..."
sudo apt-get install python3-virtualenv -y

echo "Install nginx ..."
sudo apt install nginx -y

echo "Create venv prod_node ..."
virtualenv prod_node

echo "Update pip ..."
./prod_node/bin/python3 -m pip install --upgrade pip --no-input

echo "Install requirements ..."
./prod_node/bin/python3 -m pip install -r requirements/prod_nodes_manager.txt --no-input


echo "Run app on 0.0.0.0: ..."
./prod_node/bin/gunicorn \
  --bind 0.0.0.0:5020 \
  --workers=1 wsgi:app \
  --daemon \
  --log-file ~/.gth/.gunicorn_5020.logs \
  --access-logfile ~/.gth/.gunicorn_access_5020.logs \
  --error-logfile ~/.gth/.gunicorn_errors_5020.logs \
  --log-level DEBUG \
  --timeout 9000


echo "Check if running"
ps aux | grep gunicorn


#https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-14-04

