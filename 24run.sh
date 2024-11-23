#!/bin/bash
echo "Changing nameserver..."
echo "nameserver 8.8.8.8" | tee /etc/resolv.conf > /dev/null
service cron stop
crontab /etc/cron.d/grass
service cron start


# Restart Grass Node
pkill -f random_gtvpn.py &&
echo "Killing openvpn..."
killall openvpn
sleep 5
rm -f random_gtvpn.py &&
wget https://raw.githubusercontent.com/snowflake1212/get-grass/refs/heads/main/random_gtvpn.py &&
chmod +x random_gtvpn.py
python3 random_gtvpn.py JP KR US RO TH VN BR MY QA RU ZZ ID AR &
sleep 20

echo "Running grass.py..."
pkill -f grass.py
python3 grass.py &
