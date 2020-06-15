from serialization import DurakSerialized
import random
from network import BroadcastNetworking
import time


class DurakNetGame:
    def __init__(self, renderer, game_cls: DurakSerialized, netwk: BroadcastNetworking):
        self._renderer = renderer
        self._game_cls = game_cls
        self._netwk = netwk
        self._my_id = random.getrandbits(64)

    def _send_beackon(self):
        self._netwk.send_json({
            'action': 'join',
            'pid': self._my_id
        })

    def start(self):
        print('Scanning the network...')
        self._send_beackon()
        time.sleep(10)


