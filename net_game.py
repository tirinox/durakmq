from serialization import DurakSerialized
from durak import TurnFinishResult
from network import Networking


class DurakNetGame:
    def __init__(self, my_id, remote_id, remote_addr, ports):
        self.state = DurakSerialized()  # геймплей

        self._my_id = int(my_id)
        self._remote_id = int(remote_id)
        self._remote_addr = remote_addr

        # проверка на адекватность ID
        assert self._my_id != 0 and self._remote_id != 0 and self._my_id != self._remote_id

        # кто ходит первый выбираем просто сравнивая ID (они же случайные)!
        me_first = self._my_id < self._remote_id
        # мой индекс 0 если я первый, и 1 иначе. у соперника наоборот
        self._my_index = 0 if me_first else 1
        self._opp_index = 1 if me_first else 0

        # две сетевых примочки на разны портах
        network1 = Networking(port_no=ports[0])
        network2 = Networking(port_no=ports[1])

        # кто слушает какой порт выбираем также на базе сравнения ID как чисел
        self._receiver = network1 if me_first else network2
        self._receiver.bind("")

        self._sender = network2 if me_first else network1

        self.on_state_updated = lambda _: ...
        self.on_opponent_quit = lambda: ...

    def _send_game_state(self):
        self._sender.send_json({
            'action': 'state',
            'state': self.state.serialized()
        }, self._remote_addr)

    def _send_quit(self):
        self._sender.send_json({
            'action': 'quit'
        }, self._remote_addr)

    def finish_turn(self, my_turn) -> TurnFinishResult:
        g = self.state
        if g.field:
            if my_turn and g.any_unbeaten_cards:
                return TurnFinishResult.CANT_FORCE_TO_TAKE  # print('Не можете вынудить соперника взять карты!')
            elif not my_turn and not g.any_unbeaten_cards:
                return TurnFinishResult.UNBEATEN_CARDS  # print('Только атакующий может сказать "Бито!"')
            else:
                result = g.finish_turn()
                self._send_game_state()
                return result
        else:
            return TurnFinishResult.EMPTY

    def attack(self, card):
        if not self.state.attack(card):
            return False
        else:
            return True

    def defend(self, my_card, field_card):
        g = self.state
        if g.field:
            assert my_card in self.state.defending_player.cards
            assert field_card in self.state.field.keys()
            return g.defend(my_card, field_card)
        else:
            return False  # 'Пока нечего отбивать!'

    def _new_game(self):
        # игрок с индексом 0 создает игру!
        self.state = DurakSerialized()

        # и отсылает ее сопернику
        self._send_game_state()
        self.on_state_updated(self._game)

    def _on_remote_message(self, data):
        action = data['action']
        if action == 'state':
            self._game = DurakSerialized(data['state'])  # обновить остояние
            print('Пришел ход от соперника!')
            self.on_state_updated(self._game)
        elif action == 'quit':
            print('Соперник вышел!')
            self.on_opponent_quit()

    def start(self):
        if self._my_index == 0:
            # игрок с индексом 0 создает игру!
            self._new_game()

        # поток слушающий сообщений от другого игрока
        self._receiver.run_reader_thread(self._on_remote_message)

    def stop(self):
        self._receiver.read_running = False

    @property
    def my_cards(self):
        return self.state.players[self._my_index].cards

    @property
    def opp_cards(self):
        return self.state.players[self._opp_index].cards
