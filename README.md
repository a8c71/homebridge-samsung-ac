# Homebridge Samsung AC (Legacy Model)

A Homebridge **platform** plugin for integrating legacy Samsung air conditioners (using TLSv1 communication protocol) with Apple HomeKit.

This plugin includes patches to resolve TLS compatibility issues that occur in modern Node.js environments (v17 and above). Additionally, **certificates are embedded in the plugin**, so users no longer need to obtain or configure `.pem` files directly. You can set up the plugin with only the **IP address and token**.

Converted to **Platform** approach, you can isolate unstable air conditioner devices in a **Child Bridge** to ensure the stability of the entire Homebridge system.

## Key Features ✨

* **Legacy Samsung AC Support**: Supports models using TLSv1 communication protocol
* **Latest Homebridge Compatible**: Resolves all TLS/HTTP errors occurring in modern versions like Node.js v17, v18, v22
* **Stability Assurance**: **Child Bridge** support allows isolation of air conditioner non-response issues so they don't affect other accessories
* **Embedded Certificates**: Very simple setup as no separate `.pem` file configuration is needed
* **UI Configuration Support**: All settings can be easily configured through Homebridge UI
* **Stable Communication**: Includes status caching, automatic retry, and periodic status polling features

## Prerequisites Checklist

* Latest version of Homebridge (UI environment recommended)
* Fixed IP address for the air conditioner
* Python 3 and OpenSSL (usually already installed if Homebridge is installed)
* **Router admin page access permissions** (needed for DNS setting changes)

## Installation 💻

Search for `homebridge-samsung-ac` in the 'Plugins' tab of Homebridge UI and install it.

---

## 🔑 Air Conditioner Token Extraction Method (Required Procedure)

To use this plugin, you need the air conditioner's unique authentication token. The token is extracted using a technique called **DNS Spoofing**, which intercepts the communication between the air conditioner and Samsung's cloud server (`api.smartthings.com`).

### **Step 1: Prepare Fake Server Script**

1. Copy the Python code below and save it as `fake_server.py` on your computer (or NAS/Raspberry Pi where Homebridge is installed). This script acts as a fake server to receive air conditioner communications.

    ```python
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
    ```

### **Step 2: DNS Spoofing Setup (Most Important!)**

1. **Check script execution computer's IP address:** Check the **internal IP address** of the computer (NAS, Raspberry Pi, etc.) where you will run `fake_server.py`. (e.g., `192.168.1.10`)
2. **Access router admin page:** Access your router's admin page in a web browser (usually `192.168.0.1` or `192.168.1.1`).
3. **Find DNS settings menu:** Look for functions like **'Static DNS', 'DNS Hostname'** in 'Advanced Settings' under 'LAN Settings' or 'DNS' related menus. (Menu names may vary by router manufacturer)
4. Enter the following content and save/apply. This setting will redirect air conditioner requests intended for `api.smartthings.com` to your computer.
    * **Host name / Domain name:** `api.smartthings.com`
    * **IP address:** The **script execution computer's IP address** confirmed above (e.g., `192.168.1.10`)

    ![Router DNS Setting Example](https://i.imgur.com/u5jJmYQ.png)

### **Step 3: Execute Token Extraction**

1. **Run fake server:** Navigate to the folder containing `fake_server.py` in terminal (PuTTY, etc.) and run the script with **root privileges**. (Root privileges needed to use port 443)
    ```bash
    sudo python3 fake_server.py
    ```
2. **Attempt air conditioner connection:** Set your air conditioner to **Wi-Fi setup mode** and proceed with the network connection procedure using the **SmartThings app**.
3. **Check token:** After the air conditioner connects to Wi-Fi and attempts to communicate with Samsung's server, it will connect to our PC's fake server due to DNS settings. At this time, **`Extracted token: XXXXXXXX`** will be displayed in the terminal along with the data sent by the air conditioner.
4. **Restore settings:** If you successfully obtained the token, press `Ctrl + C` in the terminal to stop the fake server and **be sure to delete the router's DNS settings changed in Step 2 to restore to original state**. Otherwise, internet usage may be affected.

---

## Configuration ⚙️

Click the 'Add Air Conditioner' button in the plugin settings screen of Homebridge UI to configure each device.

| Key | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `name` | Air conditioner name to display in Home app | - | **Yes** |
| `ip` | Fixed IP address of the air conditioner | - | **Yes** |
| `token`| Authentication token extracted above | - | **Yes** |
| `deviceIndex` | Device index to **read** status from (starting from 0) | `0` | No |
| `setDeviceIndex`| Device index to **send** commands to | `deviceIndex` | No |
| `swingModeType` | Command type to control swing (rotation) function | `comfort` | No |
| `pollingInterval`| Status synchronization interval (seconds). Disabled if 0 | - | No |
| `timeout`| Request response wait time (ms) | `5000` | No |
| `cacheDuration`| Status information cache retention time (ms) | `30000` | No |
| `debug` | Enable detailed logging. Use for troubleshooting | `false` | No |
| `minTemp` | Minimum settable temperature (°C) | `18` | No |
| `maxTemp` | Maximum settable temperature (°C) | `30` | No |
| `manufacturer`| Manufacturer name to display in Home app | `Samsung` | No |
| `model`| Model name to display in Home app | `AC-Model` | No |
| `serialNumber`| Serial number to display in Home app | `(same as name)`| No |

#### `config.json` Direct Edit Example

```json
{
  "bridge": {
    "...": "..."
  },
  "platforms": [
    {
      "platform": "SamsungACPlatform",
      "name": "Samsung ACs",
      "accessories": [
        {
          "name": "Living Room AC",
          "ip": "192.168.1.50",
          "token": "YOUR-EXTRACTED-TOKEN-HERE",
          "pollingInterval": 30,
          "debug": false,
          "minTemp": 18,
          "maxTemp": 30
        },
        {
          "name": "Bedroom AC",
          "ip": "192.168.1.51",
          "token": "ANOTHER-TOKEN-HERE",
          "pollingInterval": 30
        }
      ]
    }
  ]
}
```

🚀 **For Stability, Child Bridge Setting (Strongly Recommended)**

To prevent the air conditioner's non-response issue from affecting other accessories, it is strongly recommended to run this plugin in a child bridge.

1. **Plugin Settings Navigation**: In the Homebridge UI, go to the 'Plugins' tab and find Homebridge Samsung Ac.
2. **Click Settings Icon**: Click the wrench (settings) icon on the right side of the plugin.
3. **Bridge Settings**: In the pop-up menu, select **'Bridge Settings'**.
4. **Run in a separate Child Bridge**: Enable the **'Run in a separate Child Bridge'** option.
5. **Save and Restart**: **Save** the settings and restart Homebridge.

⚠️ **Security Warning**

This plugin uses an old security protocol (TLSv1) to communicate with the air conditioner. It is strongly recommended to use it only in a trusted local network environment.
