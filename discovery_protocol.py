import random
import network
import logging
import concurrent.futures as fut
import threading


class DiscoveryProtocol:
    A_DISCOVERY = 'discovery'
    A_STOP_SCAN = 'stop_scan'

    def __init__(self, pid, port_no):
        assert pid
        self._my_pid = pid
        self._network = network.Networking(port_no, broadcast=True)
        self._network.bind()

    def _send_action(self, action, data=None):
        """
        Форматирует JSON для обмена командами
        :param action: имя команды
        :param data: доп. данные, если надо
        :return:
        """
        data = data or {}
        self._network.send_json_broadcast({'action': action, 'sender': self._my_pid, **data})

    def _is_message_for_me(self, d):
        """
        Проверяет, относится ли принятый пакет к нашему протоколу обнаружения
        (1) должен быть определнный action
        (2) отправитель sender должен быть не я, а кто-то другой, потому что
            мы также получаем собственные пакеты)
        :param d: словарь данных
        :return:
        """
        return d and d.get('action') in [self.A_DISCOVERY, self.A_STOP_SCAN] and d.get('sender') != self._my_pid

    def run(self):
        while True:
            logging.info('Scanning...')
            # рассылаем всем сообщение A_DISCOVERY
            self._send_action(self.A_DISCOVERY)

            # ждем приемлемого ответа не более 5 секунд, игнорируя таймауты и неревалентные пакеты
            data, addr = self._network.recv_json_until(self._is_message_for_me, timeout=5.0)

            # если пришло что-то наше
            if data:
                action, sender = data['action'], data['sender']
                # кто-то нам отправил A_DISCOVERY
                if action == self.A_DISCOVERY:
                    # отсылаем ему сообщение остановить сканирование A_STOP_SCAN, указав его PID
                    self._send_action(self.A_STOP_SCAN, {'to_pid': sender})
                    # todo: что делать, если оно не дошло? тот пир продолжит сканировать дальше...
                elif action == self.A_STOP_SCAN:
                    # если получили сообщение остановить сканирование, нужно выяснить нам ли оно предназначено
                    if data['to_pid'] != self._my_pid:
                        continue  # это не нам; игнорировать!
                return addr, sender

    def run_in_background(self, callback: callable):
        """
        Ищет соперника в фоне и вызывает callback
        :param callback:
        :return:
        """
        def await_with_callback():
            results = self.run()
            callback(*results)
        threading.Thread(target=await_with_callback, daemon=True).start()


if __name__ == '__main__':
    print('Testing the discovery protocol.')
    pid = random.getrandbits(64)
    print('pid =', pid)
    info = DiscoveryProtocol(pid, 37020).run()
    print("success: ", info)
