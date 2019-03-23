import socket
import json
from os import environ


class MicroService:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, name, handle, handle_ms, auth):
        self.name = name
        self.handle = handle
        self.handle_ms = handle_ms
        self.auth = auth

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
        reg = {"action": "register", "name": self.name, "auth": self.auth}

        self.send(reg)

    def start(self):
        while True:
            frame = json.loads(self.sock.recv(4096))

            if not frame:
                break

            data = frame["data"]

            if "tag" in frame:
                tag = frame["tag"]
                endpoint = frame["endpoint"]

                response = {"tag": tag, "data": self.handle(endpoint, data)}

                self.send(response)
            else:
                ms = frame["ms"]

                self.handle_ms(ms, data)

    def stop(self):
        self.sock.close()

    def send(self, data):
        self.sock.send(str(json.dumps(data)).encode("utf-8"))

    def send_ms(self, ms, data):
        ms_data = {"ms": ms, "data": data}
        self.send(ms_data)