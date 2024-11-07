#!/bin/bash
echo "Changing nameserver..."
echo "nameserver 8.8.8.8" | tee /etc/resolv.conf > /dev/null

# Restart Grass Node
pkill -f random_gtvpn.py
echo "Killing openvpn..."
killall openvpn
sleep 10
python3 random_gtvpn.py JP KR US RO TH VN BR MY QA RU ZZ ID AR &
sleep 10

echo "Running grass.py..."
pkill -f grass.py
python3 grass.py &
