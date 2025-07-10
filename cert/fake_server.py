#!/usr/bin/env python3
import ssl
import socket
import os
import threading

# Configuration
LISTEN_IP = '0.0.0.0' # Listen for connections from all IPs
HTTPS_PORT = 443
CERT_FILE = 'temp_server_cert.pem'
KEY_FILE = 'temp_server_key.pem'

def generate_self_signed_cert(cert_file, key_file):
    """Generate temporary SSL server certificate"""
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        print(f"Generating temporary server certificate '{cert_file}' and '{key_file}'...")
        # openssl must be installed
        subj = "/CN=api.smartthings.com"
        os.system(f'openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout {key_file} -out {cert_file} -subj "{subj}"')
    print("Temporary server certificate ready.")

def handle_client(conn, addr):
    """Handle client connection and output data"""
    print(f"\n>>> [Connection established] From: {addr}")
    try:
        while True:
            data = conn.recv(8192)
            if not data:
                break
            
            decoded_data = data.decode('utf-8', errors='ignore')
            print("\n" + "="*20 + " Data received " + "="*20)
            print(decoded_data)
            
            # Find token in 'Authorization' header
            for line in decoded_data.splitlines():
                if 'authorization' in line.lower():
                    print("\n" + "*"*20 + " 🎉 Token found! 🎉 " + "*"*20)
                    token = line.split(' ')[-1]
                    print(f"Extracted token: {token}")
                    print("*"*56)
                    print("Copy this token and use it in your Homebridge configuration.")

            # Must send normal HTTP response to air conditioner to complete connection procedure
            conn.sendall(b'HTTP/1.1 200 OK\r\n\r\n')

    except Exception as e:
        print(f"[Error] Error handling client: {e}")
    finally:
        print(f"<<< [Connection closed] From: {addr}")
        conn.close()

def main():
    """Run fake server to receive and output token"""
    generate_self_signed_cert(CERT_FILE, KEY_FILE)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((LISTEN_IP, HTTPS_PORT))
        sock.listen(5)
        
        print("\n" + "="*50)
        print(f"Fake Samsung cloud server has started. (Port: {HTTPS_PORT})")
        print("Now set your air conditioner to Wi-Fi setup mode and try connecting with the SmartThings app.")
        print("="*50)

        while True:
            conn, addr = sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == '__main__':
    try:
        main()
    except PermissionError:
        print("\n[Error] Root privileges required to use port 443. Please run with 'sudo python3 fake_server.py'.")
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        # Delete temporary certificate files on exit
        if os.path.exists(CERT_FILE): os.remove(CERT_FILE)
        if os.path.exists(KEY_FILE): os.remove(KEY_FILE)
