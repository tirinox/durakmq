import socket
import json
from threading import Thread


class BroadcastNetworking:
    BUFFER_SIZE = 4096

    def get_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def _reader_worker(self):
        self._reader_socket = self.get_socket()
        self._reader_socket.bind(("", self.port_no))
        print('started thread')
        while True:
            data, _ = self._reader_socket.recvfrom(self.BUFFER_SIZE)
            try:
                j = json.loads(data.decode('utf-8', errors='ignore'), encoding='utf-8')
                print("data recv:", j)
            except json.JSONDecodeError:
                print('reader: JSON error!')

    def __init__(self, port_no=37020):
        self.port_no = port_no

        self._writer_sock = self.get_socket()
        Thread(target=self._reader_worker).start()

    def send_json(self, j):
        data = bytes(json.dumps(j), 'utf-8')
        self._writer_sock.sendto(data, ("<broadcast>", self.port_no))

