from render import ConsoleRenderer
from durak import Durak


def local_game():
    g = Durak()
    renderer = ConsoleRenderer()

    renderer.help()

    while not g.winner:
        renderer.render_game(g, my_index=0)

        renderer.sep()
        choice = input('Your choice: ')
        parts = choice.lower().split(' ')
        if not parts:
            break

        command = parts[0]

        try:
            if command == 'f':
                r = g.finish_turn()
                print(f'Turn finished: {r}')
            elif command == 'a':
                index = int(parts[1]) - 1
                card = g.current_player.cards[index]
                if not g.attack(card):
                    print('you cannot play this card!')
            elif command == 'd':
                index = int(parts[1]) - 1
                new_card = g.opponent_player.cards[index]
                def_index = int(input('Which position to defend? ')) - 1
                old_card = list(g.field.keys())[def_index]
                if not g.defend(old_card, new_card):
                    print('you cannot do that')
            elif command == 'q':
                print('QUIT!')
                break
        except IndexError:
            print('invalid card choice')
        except ValueError:
            print('enter a number after the command')

        if g.winner:
            print(f'GAME OVER! The winner is player #{g.winner + 1}')
            break


if __name__ == '__main__':
    local_game()
