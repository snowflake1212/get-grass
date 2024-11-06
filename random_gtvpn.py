#!/usr/bin/env python3
import requests
import os
import sys
import subprocess
import base64
import time
import re
import glob
import random

# Konfigurasi koneksi
MAX_RETRY_LIMIT = 1  # Batas percobaan koneksi ke setiap server
CONNECTION_TIMEOUT = 10  # Timeout untuk requests.get dalam detik
VPN_CONNECTION_TIMEOUT = 10  # Timeout koneksi untuk memastikan stabilitas
CHECK_IP_TIMEOUT = 5  # Timeout untuk mengecek IP setelah terhubung ke VPN

# Mengecek apakah OpenVPN terinstall
def check_openvpn_installed():
    try:
        subprocess.run(['openvpn', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        print("Error: OpenVPN is not installed. Please install it using 'sudo apt install openvpn'.")
        exit(1)

check_openvpn_installed()

# Mengecek argumen input untuk menerima lebih dari satu negara
if len(sys.argv) < 2:
    print('usage: ' + sys.argv[0] + ' [country name | country code]...')
    exit(1)
countries = sys.argv[1:]

# Mengambil data dari VPNGate API dengan penanganan timeout
try:
    vpn_data = requests.get('http://www.vpngate.net/api/iphone/', timeout=CONNECTION_TIMEOUT).text.replace('\r', '')
    servers = [line.split(',') for line in vpn_data.split('\n') if len(line.split(',')) > 1]
    labels = servers[1]
    labels[0] = labels[0][1:]
    servers = servers[2:]
except requests.exceptions.Timeout:
    print("Request to VPNGate API timed out.")
    exit(1)
except Exception as e:
    print(f"Error fetching VPN servers data: {e}")
    exit(1)

# Menyaring server berdasarkan negara yang dipilih
filtered_servers = []
for country in countries:
    index = 6 if len(country) == 2 else 5
    desired = [s for s in servers if country.lower() in s[index].lower()]
    filtered_servers.extend(desired)

print(f'Found {len(filtered_servers)} servers for countries: {", ".join(countries)}')

# Menyaring server yang mendukung OpenVPN
supported = [s for s in filtered_servers if len(s[-1]) > 0]
print(f"{len(supported)} of these servers support OpenVPN")

# Mengurutkan server berdasarkan negara dan ping dari terkecil ke terbesar
sorted_servers = sorted(supported, key=lambda s: (s[6], int(s[3]) if s[3].isdigit() else float('inf')))

# Menampilkan hasil yang telah diurutkan
print("\nSorted servers by country and ping (from lowest to highest):")
for server in sorted_servers:
    print(f"IP: {server[1]}, Country: {server[6]}, Ping: {server[3]} ms")

# Membuat folder 'ovpn' jika belum ada
os.makedirs('ovpn', exist_ok=True)

# Mendownload dan menyimpan setiap file .ovpn dari server yang sesuai
for server in supported:
    ip = server[1]
    config_base64 = server[-1]
    try:
        ovpn_data = base64.b64decode(config_base64).decode('utf-8')
        filename = f'ovpn/{ip}.ovpn'
        with open(filename, 'w') as f:
            f.write(ovpn_data)
            f.write('\ndata-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305:AES-128-CBC')
            f.write('\nscript-security 2\nup /etc/openvpn/update-resolv-conf\ndown /etc/openvpn/update-resolv-conf')
        print(f'Downloaded: {filename}')
    except Exception as e:
        print(f'Failed to download config for server {ip}: {e}')

# Menghapus semua file yang cocok dengan pola '219.*.ovpn' di folder 'ovpn'
pattern = re.compile(r"^(219|221)\..*\.ovpn$")
for file_path in glob.glob('ovpn/*.ovpn'):
    file_name = os.path.basename(file_path)
    if pattern.match(file_name):
        os.remove(file_path)
        print(f"Deleted {file_path} before starting connections.")

print("Cleanup complete.")

# Mengambil daftar file .ovpn untuk koneksi acak
ovpn_files = glob.glob('ovpn/*.ovpn')
if not ovpn_files:
    print("No .ovpn configuration files found in the 'ovpn' directory.")
    exit(1)

# Fungsi untuk koneksi VPN menggunakan file konfigurasi dari folder 'ovpn' secara acak
def connect_random_vpn():
    config_path = random.choice(ovpn_files)  # Pilih file secara acak
    print(f"\nConnecting to VPN server using config file: {config_path}")
    vpn_process = subprocess.Popen(['openvpn', config_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return vpn_process

# Fungsi untuk mengecek koneksi internet
def check_internet():
    try:
        requests.get("http://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

# Fungsi untuk mengecek IP yang aktif
def check_active_ip(expected_ip):
    try:
        response = requests.get("http://api.ipify.org", timeout=CHECK_IP_TIMEOUT)
        if response.text.strip() == expected_ip:
            return True
    except requests.ConnectionError:
        return False
    return False

# Loop utama untuk mencoba koneksi acak tanpa menunggu
vpn_process = None

def terminate_vpn():
    global vpn_process
    if vpn_process:
        vpn_process.terminate()
        vpn_process.wait()
        vpn_process = None
        print("VPN connection terminated.")

try:
    while True:
        # Jika ada koneksi VPN yang aktif, hentikan
        if vpn_process:
            terminate_vpn()
            print('\nVPN disconnected')
            time.sleep(5)

        # Mulai koneksi VPN baru dengan file konfigurasi acak
        retry_count = 0
        while retry_count < MAX_RETRY_LIMIT:
            vpn_process = connect_random_vpn()
            time.sleep(VPN_CONNECTION_TIMEOUT)  # Waktu tunggu untuk koneksi

            # Periksa apakah proses VPN berhasil dijalankan
            if vpn_process.poll() is None:
                print("Waiting for IP assignment...")
                time.sleep(5)  # Tunggu beberapa detik untuk IP terdistribusi
                # Mendapatkan IP yang diharapkan dari file .ovpn yang digunakan
                config_path = vpn_process.args[1]  # ambil path konfigurasi
                with open(config_path) as f:
                    config_data = f.read()
                    expected_ip = re.search(r'remote\s+([\d\.]+)', config_data).group(1)
                
                # Cek koneksi internet dan IP aktif
                if check_internet() and check_active_ip(expected_ip):
                    print(f"Connected to VPN server with IP: {expected_ip}.")
                    
                    # Loop pengecekan koneksi setiap 5 menit (300 detik)
                    while True:
                        time.sleep(300)  # Tunggu 5 menit sebelum uji koneksi berikutnya
                        if not check_internet() or not check_active_ip(expected_ip):  # Jika koneksi gagal
                            print("Internet connection lost or IP mismatch. Reconnecting...")
                            terminate_vpn()  # Putuskan koneksi VPN
                            break  # Keluar dari loop pengecekan untuk mencoba koneksi berikutnya

                    break  # Keluar dari loop percobaan jika koneksi berhasil
                else:
                    print("Failed to establish a working connection, retrying...")
            else:
                print("Failed to connect to VPN server, retrying...")
            retry_count += 1
            terminate_vpn()
            time.sleep(5)

        # Jika setelah MAX_RETRY_LIMIT koneksi gagal, lanjut ke file berikutnya
        if retry_count >= MAX_RETRY_LIMIT:
            print("Moving to a new random configuration file after reaching retry limit.")

except KeyboardInterrupt:
    print("\nTerminating VPN connection...")
    terminate_vpn()
    print("VPN terminated")