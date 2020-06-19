from serialization import DurakSerialized
import random
from network import Networking


class DurakNetGame:
    def __init__(self, renderer, network_endpoint: Networking, my_id):
        self._renderer = renderer
        self._game_id = None
        self._network = network_endpoint
        self._game = DurakSerialized()
        self._my_id = my_id

    @classmethod
    def rand_id(cls):
        return random.getrandbits(64)

    def _new_game(self):
        print('No games were detected! Making a game.')
        self._game = DurakSerialized()
        self._game.game_id = self.rand_id()

    def _join_game(self, data):
        self._opp_id = data['pid']
        self._game = DurakSerialized(data['state'])

    def start(self):
        print(f'My ID is #{self._my_id}')


