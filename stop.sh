#!/bin/bash

#pkill gunicorn

port=$1
pid=`ps ax | grep gunicorn | grep $port | awk '{split($0,a," "); print a[1]}' | head -n 1`
if [ -z "$pid" ]; then
  echo "no gunicorn deamon on port $port"
else
  kill $pid
  echo "killed gunicorn deamon on port $port"
fi


# ps aux | grep gunicorn # to find it