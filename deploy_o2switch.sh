#!/bin/bash

# Help section
# Specify that the first argument is the config file name with config.json as default
if [ $# -eq 0 ] || [ $1 == "-h" ] || [ $1 == "--help" ]; then
    echo "Usage: $0 [config_file_name|config_file_path]"
    echo "Example: $0 ./configs/prod.config.json"
    echo "Default config file name is ./configs/config.json"
    exit 1
fi


echo "Update pip ..."
/home2/krfu8777/virtualenv/blockchain/3.8/bin/python3.8 -m pip install --upgrade pip --no-input

echo "Install requirements ..."
/home2/krfu8777/virtualenv/blockchain/3.8/bin/python3.8 -m pip install -r requirements/prod.txt --no-input

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
port=`/home2/krfu8777/virtualenv/blockchain/3.8/bin/python3.8 -c "import json; print(json.load(open('$config_file'))['port'])"`

mkdir -p ~/.gth
mkdir -p /root/.gth

echo "Run app on 0.0.0.0: ..."
GTH_CONFIG=$config_file /home2/krfu8777/virtualenv/blockchain/3.8/bin/gunicorn \
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


