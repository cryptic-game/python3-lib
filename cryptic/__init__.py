import socket
import json
from os import environ
from uuid import uuid4
import time

timeout = 30

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

        self.awaiting = []
        self.tags_data = {}

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
            print(frame)
            data = frame["data"]

            if "tag" in frame:

                endpoint = frame["endpoint"]
                user = frame["user"]
                tag = frame["tag"]

                response = {"tag": tag, "data": self.handle(endpoint, data, user)}

                self.send(response)
            else:
                ms = frame["ms"]
                tag = frame["tag"]

                if tag in self.awaiting:
                    self.tags_data.update({tag:data})

                else:
                    self.handle_ms(ms, data, tag)

    def stop(self):
        self.sock.close()

    def send(self, data):
        x = str(json.dumps(data))

        self.sock.send(x.encode("utf-8"))

    def send_ms(self, ms, data, tag  = str(uuid4())):

        ms_data = {"ms": ms, "data": data, "tag": tag}
        self.send(ms_data)

        return tag

    def wait_for_response(self, ms, data):

        tag = self.asyncro_call(ms, data)

        return self.wait(tag)

    def asyncro_call(self, ms, data):

        tag = str(uuid4())

        self.send_ms(ms, data, tag)

        self.awaiting.append(tag)

        return tag

    def wait(self, tag):

        time_start_waiting = time.time()

        while tag not in self.tags_data.keys():
            time.sleep(0.01)

            if time.time() - time_start_waiting > timeout:
                raise TimeoutError()

        data = self.tags_data[tag]

        del (self.tags_data[tag])
        del (self.awaiting[tag])

        return data
