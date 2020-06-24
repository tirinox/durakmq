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

    def _send_quit(self):
        self._sender.send_json({
            'action': 'quit'
        }, self._remote_addr)

    def _handle_finish(self):
        g = self._game
        if g.field:
            r = g.finish_turn()
            if r == g.GAME_OVER:
                r_str = 'игра окончена!'
            elif r == g.TOOK_CARDS:
                r_str = 'взяли карты.'
            else:
                r_str = 'бито.'
            print(f'Ход завершен: {r_str}')
            return True
        else:
            print('Пока ход не сделал, чтобы его завершить!')
            return False

    def _handle_attack(self, parts):
        g = self._game
        index = int(parts[1]) - 1
        card = g.current_player.cards[index]
        if not g.attack(card):
            print('ОШИБКА! Вы не можете ходить этой картой!')
            return False
        else:
            return True

    def _handle_defence(self, parts):
        g = self._game
        index = int(parts[1]) - 1
        new_card = g.opponent_player.cards[index]
        if g.field:
            max_pos = len(g.field)
            def_index = int(input(f'Какую позицию защищать (1-{max_pos})')) - 1
            old_card = list(g.field.keys())[def_index]
            if not g.defend(old_card, new_card):
                print('ОШИБКА! Нельзя так отбиться!')
            else:
                return True
        else:
            print('Пока нечего отбивать!')
            return False

    def _new_game(self):
        # игрок с индексом 0 создает игру!
        self._game = DurakSerialized()

        # и отсылает ее сопернику
        self._send_game_state()
        self._renderer.render_game(self._game, self._my_index)

    def _on_remote_message(self, data):
        action = data['action']
        if action == 'state':
            self._game = DurakSerialized(data['state'])
            print('Пришел ход от соперника!')
            self._renderer.render_game(self._game, self._my_index)
        elif action == 'quit':
            print('Соперник вышел!')
            exit(0)

    def start(self):
        print(f'Мой ID #{self._my_id}, мой индекс {self._my_index}')
        print(f'Удаленный адрес {self._remote_addr}')

        self._renderer.help()

        self._receiver.run_reader_thread(self._on_remote_message)

        if self._my_index == 0:
            # игрок с индексом 0 создает игру!
            self._new_game()

        while True:
            q = input('Ваш ход (q = выход)? ')

            parts = q.lower().split(' ')
            if not parts:
                continue

            command = parts[0]

            good_move = False  # флаг, удачный ли был ход после ввода команды

            g = self._game

            try:
                if command == 'f':
                    good_move = self._handle_finish()
                elif command == 'a' and g.attacker_index == self._my_index:
                    good_move = self._handle_attack(parts)
                elif command == 'd' and g.attacker_index != self._my_index:
                    good_move = self._handle_defence(parts)
                elif command == 'q':
                    print('Вы вышли из игры!')
                    self._send_quit()
                    break
                else:
                    print('Неизвестная команда.')
            except IndexError:
                print('ОШИБКА! Неверный выбор карты')
            except ValueError:
                print('Введите число через пробел после команды')

            if good_move:
                self._send_game_state()
                self._renderer.render_game(g, self._my_index)

                if g.winner:
                    outcome = 'Вы победили!' if g.winner == self._my_index else 'Вы проиграли!'
                    print(f'Игра окончена! {outcome}')
                    break
