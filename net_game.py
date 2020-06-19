from serialization import DurakSerialized
import random
from network import Networking


class DurakNetGame:
    def __init__(self, renderer, network: Networking):
        self._renderer = renderer
        self._network = network
        self._game_id = None
        self._game = DurakSerialized()
        self._my_id = self.rand_id()

    @classmethod
    def rand_id(cls):
        return random.getrandbits(64)

    def _send_message(self, action, data=None):
        data = data or {}
        self._network.send_json_broadcast({
            'action': action,
            'pid': self._my_id,
            **data
        })

    def _new_game(self):
        print('No games were detected! Making a game.')
        self._game = DurakSerialized()
        self._game.game_id = self.rand_id()

    def _join_game(self, data):
        self._opp_id = data['pid']
        self._game = DurakSerialized(data['state'])

    def start(self):
        print(f'My ID is #{self._my_id}')

