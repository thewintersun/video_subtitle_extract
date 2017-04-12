#!/bin/bash

echo "copying fonts to system"
sudo mkdir /usr/share/fonts/newfonts/
sudo cp ./fonts/* /usr/share/fonts/newfonts/

sudo apt-get install -y python-pil
sudo apt-get install bc

sudo pip install python_Levenshtein
sudo pip2 install python_Levenshtein

sudo pip install lxml

sudo pip install beautifulsoup4

sudo pip install you-get

sudo pip install mysql-python

sudo pip install pyyaml
sudo pip2 install pyyaml

#sudo apt-get install -y mysql-server
sudo apt-get install -y mysql-client
sudo apt-get install -y libmysqlclient-dev
sudo apt-get install python-setuptools
sudo apt-get install -y libmysqld-dev
sudo apt-get install libmysqlclient-dev
sudo apt-get install python-dev
sudo easy_install mysql-python

sudo apt-get install ffmpeg

#
sudo pip install scipy
sudo pip install pydub
sudo pip2 install pydub
sudo pip install python_speech_features
