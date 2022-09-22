#!/bin/bash

# Help section
# Specify that the first argument is the config file name with config.json as default
if [ $# -eq 0 ] || [ $1 == "-h" ] || [ $1 == "--help" ]; then
    echo "Usage: $0 [config_file_name|config_file_path]"
    echo "Example: $0 ./configs/prod.config.json"
    echo "Default config file name is ./configs/config.json"
    exit 1
fi

sudo apt-get install software-properties-common -y

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

echo "Install venv ..."
sudo apt-get install python3-virtualenv -y
#/usr/bin/python3.8 -m pip install -U --force-reinstall virtualenv
#/usr/bin/python3.8 -m pip install virtualenv

echo "Install nginx ..."
sudo apt install nginx -y

echo "Create venv prod_node ..."
virtualenv prod_node || /home/gth_group/.local/bin/virtualenv prod_node


#echo "Setup nginx reverse-proxy ..."
#sudo service nginx stop
#sudo cp ./nginx.conf /etc/nginx/nginx.conf
#sudo service nginx start


#echo "Compile node"
#
#rm -rf ./bin/* && cd bin
#
#pyinstaller --noconfirm --onefile --console  "../main.py" -n node


echo "Update pip ..."
./prod_node/bin/python3.8 -m pip install --upgrade pip --no-input

echo "Install requirements ..."
./prod_node/bin/python3.8 -m pip install -r requirements/prod.txt --no-input

# function that return 0 if the string contains a substring and 1 otherwise
function contains() {
    string="$1"
    substring="$2"
    if test "${string#*$substring}" != "$string"
    then
        return 0    # $substring is in $string
    else
        return 1    # $substring is not in $string
    fi
}


# if the first argument exists and contains "config.json", save it in a variable
if [ $# -eq 1 ] && contains "$1" "config.json"; then
    config_file=$1
else
    config_file="./configs/config.json"
fi

echo "Using config file: $config_file"

# Parse the json config file and save the values in bash variables
port=`./prod_node/bin/python3.8 -c "import json; print(json.load(open('$config_file'))['port'])"`

mkdir -p ~/.gth
mkdir -p /root/.gth

echo "Run app on 0.0.0.0: ..."
GTH_CONFIG=$config_file ./prod_node/bin/gunicorn \
  --bind 0.0.0.0:$port \
  --workers=1 wsgi:app \
  --daemon \
  --log-file ~/.gth/.gunicorn_$port.logs \
  --access-logfile ~/.gth/.gunicorn_access_$port.logs \
  --error-logfile ~/.gth/.gunicorn_errors_$port.logs \
  --log-level DEBUG \
  --timeout 120

#gunicorn -b 0.0.0.0:5000 --workers=1 wsgi:app

echo "Check if running"
ps aux | grep gunicorn

#screen -R prod

#https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-14-04


