import socket
import json


class BroadcastNetworking:
    BUFFER_SIZE = 4096

    def __init__(self, port_no=37020):
        self.port_no = port_no
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", self.port_no))
        self.socket = sock

    def send_json(self, j):
        data = bytes(json.dumps(j), 'utf-8')
        self.socket.sendto(data, ("<broadcast>", self.port_no))

    def receive_json(self):
        data, _ = self.socket.recvfrom(self.BUFFER_SIZE)
        try:
            return json.loads(data.decode('utf-8', errors='ignore'), encoding='utf-8')
        except json.JSONDecodeError:
            return None
