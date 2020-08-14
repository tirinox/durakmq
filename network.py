import socket
import json
import time
import logging
import threading


class Networking:
    BUFFER_SIZE = 4096  # размер буфера для примем сообщений
    TIME_OUT = 1.0  # время таймаута при ожидании данных в сокет

    @classmethod
    def get_socket(cls, broadcast=False, timeout=TIME_OUT):
        """
        Создает UDP сокет
        :param broadcast: широковещателньый или нет
        :param timeout: тайм аут
        :return: сокет
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # чтобы на одной машине можно было слушать тотже порт
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            # на Windows используется SO_REUSEADDR
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if broadcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        return sock

    def recv_json(self):
        """
        Получить JSON из сокета
        :return: dict или list
        """
        try:
            # получить датаграмму и адрес из сокета
            data, addr = self._socket.recvfrom(self.BUFFER_SIZE)
            # декодируем в юникод и загружаем из JSON
            return json.loads(data.decode('utf-8', errors='ignore'), encoding='utf-8'), addr
        except json.JSONDecodeError:
            logging.error(f'JSONDecodeError!')
        except socket.timeout:
            pass  # ничего не пришло
        except KeyboardInterrupt:
            raise
        return None, None

    def recv_json_until(self, predicate, timeout):
        """
        Несколько раз пытается получить JSON в течение timeout секунд, пока на полученных данных
        функция predicate не вернет True
        :param predicate: функция, чтобы проверять данные
        :param timeout: тайм аут
        :return:
        """
        t0 = time.monotonic()
        while time.monotonic() < t0 + timeout:
            data, addr = self.recv_json()
            if predicate(data):
                return data, addr
        return None, None

    def run_reader_thread(self, callback):
        """
        Запускает отдельный поток, чтобы получать данные из сокета
        :param callback: функция, которая вызывается, если получены данные
        """
        self.read_running = True

        def reader_job():
            while self.read_running:
                data, _ = self.recv_json()
                if data:
                    callback(data)

        # daemon=True, чтобы не зависал, если выйдет основной поток
        thread = threading.Thread(target=reader_job, daemon=True)
        thread.start()
        return thread

    def bind(self, to=""):
        """
        Привязаться к порту, то есть начать слушать с него сообщения
        После bind можно вызывать recv_json
        :param to: интерфейс ("" - любой)
        """
        self._socket.bind((to, self.port_no))

    def __init__(self, port_no, broadcast=False):
        self.port_no = port_no
        self._socket = self.get_socket(broadcast=broadcast)

    def send_json(self, j, to):
        """
        Отправляет JSON
        :param j: данные
        :param to: адрес кому отправить
        """
        data = bytes(json.dumps(j), 'utf-8')
        return self._socket.sendto(data, (to, self.port_no))

    def send_json_broadcast(self, j):
        """
        Оправляет JSON данные широковещательно
        :param j: данные
        :return:
        """
        return self.send_json(j, "<broadcast>")

    def __del__(self):
        logging.info('Closing socket')
        self._socket.close()
