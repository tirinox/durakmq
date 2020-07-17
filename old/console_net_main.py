from old.render import ConsoleRenderer
from discovery_protocol import DiscoveryProtocol
from util import rand_id

PORT_NO = 37020
PORT_NO_AUX = 37021

from old.render import GameRenderer
from serialization import DurakSerialized
from network import Networking


class DurakNetGame:
    def __init__(self, renderer: GameRenderer, my_id, remote_id, remote_addr, ports):
        self._renderer = renderer

        self._game = DurakSerialized()  # геймплей

        self._my_id = int(my_id)
        self._remote_id = int(remote_id)
        self._remote_addr = remote_addr

        # проверка на адекватность ID
        assert self._my_id != 0 and self._remote_id != 0 and self._my_id != self._remote_id

        # кто ходит первый выбираем просто сравнивая ID (они же случайные)!
        me_first = self._my_id < self._remote_id
        # мой индекс 0 если я первый, и 1 иначе. у соперника наоборот
        self._my_index = 0 if me_first else 1

        # две сетевых примочки на разны портах
        network1 = Networking(port_no=ports[0])
        network2 = Networking(port_no=ports[1])

        # кто слушает какой порт выбираем также на базе сравнения ID как чисел
        self._receiver = network1 if me_first else network2
        self._receiver.bind("")

        self._sender = network2 if me_first else network1

    def _send_game_state(self):
        self._sender.send_json({
            'action': 'state',
            'state': self._game.serialized()
        }, self._remote_addr)

    def _send_quit(self):
        self._sender.send_json({
            'action': 'quit'
        }, self._remote_addr)

    def _handle_finish(self, my_turn):
        g = self._game
        if g.field:
            if my_turn and g.any_unbeaten_cards:
                print('Не можете вынудить соперника взять карты!')
                return False
            elif not my_turn and not g.any_unbeaten_cards:
                print('Только атакующий может сказать "Бито!"')
                return False
            else:
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
            variants = g.defend_variants(new_card)

            print(f'variants {variants} - {new_card}')

            if len(variants) == 1:
                def_index = variants[0]
            elif len(variants) >= 2:
                max_pos = len(g.field)
                def_index = int(input(f'Какую позицию отбить {new_card} (1-{max_pos})? ')) - 1
            else:
                print('Вам придется взять карты!')
                return False

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
            self._game = DurakSerialized(data['state'])  # обновить остояние
            print('Пришел ход от соперника!')
            self._renderer.render_game(self._game, self._my_index)
        elif action == 'quit':
            print('Соперник вышел!')
            exit(0)

    def _game_loop(self):
        while True:
            q = input('Ваш ход (q = выход)? ')

            parts = q.lower().split(' ')
            if not parts:
                continue

            command = parts[0]

            good_move = False  # флаг, удачный ли был ход после ввода команды
            g = self._game

            # мой ли ход атаковать?
            is_my_turn = g.attacker_index == self._my_index

            try:
                if command == 'f':
                    good_move = self._handle_finish(is_my_turn)
                elif command == 'a' and is_my_turn:
                    good_move = self._handle_attack(parts)
                elif command == 'd' and not is_my_turn:
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
                # если ход удачный, пошлем копию состояния игры
                self._send_game_state()
                self._renderer.render_game(g, self._my_index)

                # проверка на окончание игры (если есть победитель, в g.winner - этог индекс)
                if g.winner is not None:
                    outcome = 'Вы победили!' if g.winner == self._my_index else 'Вы проиграли!'
                    print(f'Игра окончена! {outcome}')
                    break

    def start(self):
        print(f'Мой ID #{self._my_id}, мой индекс {self._my_index}')
        print(f'Удаленный адрес {self._remote_addr}')
        self._renderer.help()

        if self._my_index == 0:
            # игрок с индексом 0 создает игру!
            self._new_game()

        self._receiver.run_reader_thread(self._on_remote_message)
        self._game_loop()


def main():
    my_pid = rand_id()

    discovery = DiscoveryProtocol(my_pid, port_no=PORT_NO)
    print('Сканирую локальную сеть...')
    (remote_addr, _port), remote_pid = discovery.run()
    del discovery

    renderer = ConsoleRenderer()
    game = DurakNetGame(renderer, my_pid, remote_pid, remote_addr, [PORT_NO, PORT_NO_AUX])
    game.start()


if __name__ == '__main__':
    main()
