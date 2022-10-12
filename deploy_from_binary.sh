#!/bin/bash

GTH_CONFIG='./configs/prod.config.json' ./wsgi_standalone.bin

echo "Check if running"
ps aux | grep gunicorn

#screen -R prod

#https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-14-04


