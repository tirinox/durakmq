from serialization import DurakSerialized
from network import Networking
from util import rand_id


class DurakNetGame:
    def __init__(self, renderer, network_endpoint: Networking, my_id, remote_id):
        self._renderer = renderer
        self._network = network_endpoint

        self._game = DurakSerialized()
        self._game.game_id = rand_id()

        self._my_id = int(my_id)
        self._remote_id = int(remote_id)

        assert self._my_id != 0 and self._remote_id != 0 and self._my_id != self._remote_id

        me_first = self._my_id < self._remote_id
        self._my_index = 0 if me_first else 1

    def start(self):
        print(f'My ID is #{self._my_id}')

        # while self._game.winner is None:
        #     self._renderer.render_game(self._my_index)
        #     self._renderer.sep()

        self._network.run_reader_thread(lambda data: print('reader:', data))
        while True:
            q = input('enter (q = exit)? ')
            if q == 'q':
                break
            else:
                self._network.send_json({'message': q}, self.remote_addr)





