from old.render import ConsoleRenderer
from durak import Durak
import random


def local_game():
    # rng = random.Random(42)  # игра с фиксированным рандомом (для отладки)
    rng = random.Random()  # случайная игра

    g = Durak(rng=rng)
    renderer = ConsoleRenderer()

    renderer.help()

    while not g.winner:
        renderer.render_game(g, my_index=0)

        renderer.sep()
        choice = input('Ваш выбор: ')
        # разбиваем на части: команда - пробел - номер карты
        parts = choice.lower().split(' ')
        if not parts:
            break

        command = parts[0]

        try:
            if command == 'f':
                r = g.finish_turn()
                print(f'Ход окончен: {r}')
            elif command == 'a':
                index = int(parts[1]) - 1
                card = g.attacking_player[index]
                if not g.attack(card):
                    print('Вы не можете ходить с этой карты!')
            elif command == 'd':
                index = int(parts[1]) - 1
                new_card = g.defending_player[index]

                # варианты защиты выбранной картой
                variants = g.defend_variants(new_card)

                if len(variants) == 1:
                    def_index = variants[0]
                else:
                    def_index = int(input(f'Какую позицию отбить {new_card}? ')) - 1

                old_card = list(g.field.keys())[def_index]
                if not g.defend(old_card, new_card):
                    print('Не можете так отбиться')
            elif command == 'q':
                print('QUIT!')
                break
        except IndexError:
            print('Неправильный выбор карты')
        except ValueError:
            print('Введите число через пробел после команды')

        if g.winner:
            print(f'Игра окончена, победитель игрок: #{g.winner + 1}')
            break


if __name__ == '__main__':
    local_game()
