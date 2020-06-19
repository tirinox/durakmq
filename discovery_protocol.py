import random
import network


class DiscoveryProtocol:
    A_DISCOVERY = 'discovery'
    A_STOP_SCAN = 'stop_scan'

    def __init__(self, pid, port_no=37020):
        assert pid
        self._pid = pid
        self._network = network.Networking(port_no, broadcast=True)

    def _send_action(self, action):
        self._network.send_json_broadcast({'action': action, 'pid': self._pid})

    def _is_message_for_me(self, d):
        return d and d.get('action') in [self.A_DISCOVERY, self.A_STOP_SCAN] and d.get('pid') != self._pid

    def run(self):
        while True:
            print('Scanning...')
            self._send_action(self.A_DISCOVERY)
            data, addr = self._network.recv_json_until(self._is_message_for_me, timeout=5.0)

            if data:
                action = data['action']
                if action == self.A_DISCOVERY:
                    self._send_action(self.A_STOP_SCAN)
                elif action == self.A_STOP_SCAN:
                    pass
                return addr, data['pid']


if __name__ == '__main__':
    pid = random.getrandbits(64)
    print('pid =', pid)
    info = DiscoveryProtocol(pid).run()
    print("success: ", info)
