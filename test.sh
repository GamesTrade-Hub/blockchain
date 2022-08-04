#!/bin/bash


echo $#


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
    config_file="config.json"
fi

echo "Using config file: $config_file"





