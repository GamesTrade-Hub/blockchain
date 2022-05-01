
sudo apt-get install python3.8
sudo apt-get install python3-distutils python-setuptools python3.8-dev

echo "Update pip ..."
/usr/bin/python3.8 -m pip install --upgrade pip

echo "Install venv ..."
apt-get upgrade python-virtualenv
/usr/bin/python3.8 -m pip install -U --force-reinstall virtualenv
/usr/bin/python3.8 -m pip install virtualenv

echo "Install nginx ..."
sudo apt install nginx

echo "Create venv prod_node ..."
virtualenv prod_node

echo "Use venv prod_node ..."
source prod_node/bin/activate

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
#gunicorn -b 0.0.0.0:5000 --workers=1 wsgi:app --daemon --access-logfile .node_logs --error-logfile .node_errlogs
gunicorn -b 0.0.0.0:5000 --workers=1 wsgi:app


#screen -R prod

#https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-14-04