import socket
import json
from os import environ


class MicroService:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, name, handle):
        self.name = name
        self.handle = handle

        host = '127.0.0.1'
        port = 1239

        if 'MSSOCKET_HOST' in environ:
            host = environ['MSSOCKET_HOST']
        if 'MSSOCKET_PORT' in environ:
            port = environ['MSSOCKET_PORT']

        self.server_address = (host, port)

    def run(self):
        self.connect()
        self.register()
        self.start()

    def connect(self):
        self.sock.connect(self.server_address)

    def register(self):
        reg = {"action": "register", "name": "echo"}

        self.send(reg)

    def start(self):
        while True:
            frame = json.loads(self.sock.recv(4096))

            if not frame:
                break

            tag = frame["tag"]
            data = frame["data"]
            endpoint = frame["endpoint"]

            response = {"tag": tag, "data": self.handle(endpoint, data)}

            self.send(response)

    def stop(self):
        self.sock.close()

    def send(self, data):
        self.sock.send(str(json.dumps(data)).encode("utf-8"))
