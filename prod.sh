
echo "Intall venv ..."
pip3 install virtualenv

echo "Install nginx ..."
sudo apt install nginx

echo "Create venv prod_node ..."
virtualenv prod_node

echo "Use venv prod_node ..."
source prod_node/bin/activate

echo "Setup nginx reverse-proxy ..."
sudo service nginx stop
copy ./nginx.conf /etc/nginx/nginx.conf
sudo service nginx start


#echo "Compile node"
#
#rm -rf ./bin/* && cd bin
#
#pyinstaller --noconfirm --onefile --console  "../main.py" -n node

echo "Install requirements ..."
pip3 install -r requirements/prod.txt

echo "Run app ..."
gunicorn -b 0.0.0.0:5000 --workers=1 wsgi:app


#screen -R prod

