#!/bin/bash
cd /home/ubuntu
sudo apt update
git clone https://github.com/hthome1/tasks.git

sudo sed -i "s/node1/18.216.159.151/g" /home/ubuntu/tasks/portfolio/settings.py

cd tasks
./install.sh

sudo reboot