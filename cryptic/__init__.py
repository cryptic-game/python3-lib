import socket
import json
from os import environ
from uuid import uuid4


class MicroService:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, name, handle, handle_ms):
        self.name = name
        self.handle = handle
        self.handle_ms = handle_ms

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
        reg = {"action": "register", "name": self.name}

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
                user = frame["user"]

                response = {"tag": tag, "data": self.handle(endpoint, data, user)}

                self.send(response)
            else:
                ms = frame["ms"]
                tag = frame["tag"]

                self.handle_ms(ms, data, tag)

    def stop(self):
        self.sock.close()

    def send(self, data):
        self.sock.send(str(json.dumps(data)).encode("utf-8"))

    def send_ms(self, ms, data, tag):
        ms_data = {"ms": ms, "data": data, "tag": tag}
        self.send(ms_data)

    def send_ms(self, ms, data):
        tag = str(uuid4())
        self.send_ms(ms, data, tag)

        return tag
