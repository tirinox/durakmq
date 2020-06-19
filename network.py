import socket
import json
import time
import logging
import threading


class Networking:
    BUFFER_SIZE = 4096
    TIME_OUT = 1.0  # sec

    @classmethod
    def get_socket(cls, broadcast=False, timeout=TIME_OUT):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if broadcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        return sock

    def recv_json(self):
        try:
            data, addr = self._socket.recvfrom(self.BUFFER_SIZE)
            return json.loads(data.decode('utf-8', errors='ignore'), encoding='utf-8'), addr
        except json.JSONDecodeError:
            logging.error(f'JSONDecodeError!')
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            raise
        return None, None

    def recv_json_until(self, predicate, timeout):
        t0 = time.monotonic()
        while time.monotonic() < t0 + timeout:
            data, addr = self.recv_json()
            if predicate(data):
                return data, addr
        return None, None

    def run_reader_thread(self, callback):
        def reader_job():
            while True:
                data, _ = self.recv_json()
                if data:
                    callback(data)
        threading.Thread(target=reader_job, daemon=True).start()

    def bind(self, to=""):
        self._socket.bind((to, self.port_no))
        self._remote_addr = to

    def __init__(self, port_no, broadcast=False):
        self.port_no = port_no
        self._remote_addr = None
        self._socket = self.get_socket(broadcast=broadcast)

    def send_json(self, j, to):
        data = bytes(json.dumps(j), 'utf-8')
        return self._socket.sendto(data, (to, self.port_no))

    def send_json_broadcast(self, j):
        return self.send_json(j, "<broadcast>")

    def __del__(self):
        logging.info('Closing socket')
        self._socket.close()
