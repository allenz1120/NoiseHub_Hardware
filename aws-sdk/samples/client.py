# echo-client.py

import socket
import json

HOST = "192.168.1.14"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    message = {"noise": 1, "temperature":70}
    s.connect((HOST, PORT))
    payload = json.dumps(message).encode('utf-8')
    s.sendall(payload)
    data = s.recv(1024)

print(f"Received {data!r}")
