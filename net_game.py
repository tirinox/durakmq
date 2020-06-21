from render import GameRenderer
from serialization import DurakSerialized
from network import Networking
from util import rand_id


class DurakNetGame:
    def __init__(self, renderer: GameRenderer, my_id, remote_id, remote_addr, ports):
        self._renderer = renderer

        self._game = None

        self._my_id = int(my_id)
        self._remote_id = int(remote_id)
        self._remote_addr = remote_addr

        assert self._my_id != 0 and self._remote_id != 0 and self._my_id != self._remote_id

        me_first = self._my_id < self._remote_id
        self._my_index = 0 if me_first else 1

        network1 = Networking(port_no=ports[0])
        network2 = Networking(port_no=ports[1])

        self._receiver = network1 if me_first else network2
        self._sender = network2 if me_first else network1

        self._receiver.bind("")

    def _send_game_state(self):
        self._sender.send_json({
            'action': 'state',
            'state': self._game.serialized()
        }, self._remote_addr)

    def start(self):
        print(f'Мой ID #{self._my_id}, мой индекс {self._my_index}')
        print(f'Удаленный адрес {self._remote_addr}')

        # while self._game.winner is None:
        #     self._renderer.render_game(self._my_index)
        #     self._renderer.sep()
        self._renderer.help()

        def reader(data):
            if data['action'] == 'state':
                self._game = DurakSerialized(data['state'])
                print('Пришел ход от соперника!')
                self._renderer.render_game(self._game, self._my_index)

        self._receiver.run_reader_thread(reader)

        if self._my_index == 0:
            # игрок с индексом 0 создает игру!
            self._game = DurakSerialized()
            self._game.game_id = rand_id()

            # и отсылает ее сопернику
            self._send_game_state()
            self._renderer.render_game(self._game, self._my_index)

        while True:
            q = input('Ваш ход (q = выход)? ')

            parts = q.lower().split(' ')
            if not parts:
                continue

            command = parts[0]

            g = self._game

            try:
                if command == 'f':
                    r = g.finish_turn()
                    if r == g.GAME_OVER:
                        r_str = 'игра окончена!'
                    elif r == g.TOOK_CARDS:
                        r_str = 'взяли карты.'
                    else:
                        r_str = 'бито.'
                    print(f'Ход завершен: {r_str}')
                elif command == 'a':
                    index = int(parts[1]) - 1
                    card = g.current_player.cards[index]
                    if not g.attack(card):
                        print('ОШИБКА! Вы не можете ходить этой картой!')
                elif command == 'd':
                    index = int(parts[1]) - 1
                    new_card = g.opponent_player.cards[index]
                    max_pos = len(g.field) + 1
                    def_index = int(input(f'Какую позицию защищать (1-{max_pos})')) - 1
                    old_card = list(g.field.keys())[def_index]
                    if not g.defend(old_card, new_card):
                        print('ОШИБКА! Нельзя так отбиться!')
                elif command == 'q':
                    print('Вы вышли из игры!')
                    break
            except IndexError:
                print('ОШИБКА! Неверный выбор карты')
            except ValueError:
                print('Введите число через пробел после команды')

            self._send_game_state()

            if g.winner:
                outcome = 'Вы победили!' if g.winner == self._my_index else 'Вы проиграли!'
                print(f'Игра окончена! {outcome}')
                break


