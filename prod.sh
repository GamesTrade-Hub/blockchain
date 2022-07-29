#!/bin/bash

sudo add-apt-repository main -y
sudo add-apt-repository universe -y
sudo add-apt-repository restricted -y
sudo add-apt-repository multiverse -y
sudo apt update -y

sudo apt-get install python3.8 -y
sudo apt-get install python3-distutils python-setuptools python3.8-dev -y
sudo apt-get install build-essential -y
sudo apt-get install libgmp3-dev -y
sudo apt-get install python3-pip -y
sudo apt install gunicorn -y

echo "Update pip ..."
/usr/bin/python3.8 -m pip install --upgrade pip

echo "Install venv ..."
sudo apt-get install python3-virtualenv -y
#/usr/bin/python3.8 -m pip install -U --force-reinstall virtualenv
#/usr/bin/python3.8 -m pip install virtualenv

echo "Install nginx ..."
sudo apt install nginx -y

echo "Create venv prod_node ..."
virtualenv prod_node

#echo "Setup nginx reverse-proxy ..."
#sudo service nginx stop
#sudo cp ./nginx.conf /etc/nginx/nginx.conf
#sudo service nginx start


#echo "Compile node"
#
#rm -rf ./bin/* && cd bin
#
#pyinstaller --noconfirm --onefile --console  "../main.py" -n node


echo "Install requirements ..."
./prod_node/bin/python3.8 -m pip install -r requirements/prod.txt

echo "Run app 0.0.0.0:5000 ..."
./prod_node/bin/gunicorn -b 0.0.0.0:5000 --workers=1 wsgi:app --daemon --log-file .gunicorn.logs --access-logfile .gunicorn_access.logs --error-logfile .gunicorn_errors.logs --log-level DEBUG
#gunicorn -b 0.0.0.0:5000 --workers=1 wsgi:app

echo "check if running"
ps aux | grep gunicorn

#screen -R prod

#https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-14-04

