from durak import Game
from render import render_game


def main():
    print('Help')
    print('  1. a [card_no] -- attack with a card')
    print('  2. d [card_no] [position] -- defend with a card at position')
    print('  3. f -- finish the turn (if there are unbeaten cards then the defender takes them all')
    print('  3. q -- quit')

    g = Game()

    while not g.winner:
        render_game(g)
        print('-' * 100)
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
                card = g.current_player().cards[index]
                if not g.attack(card):
                    print('you cannot play this card!')
            elif command == 'd':
                index = int(parts[1]) - 1
                new_card = g.opponent_player().cards[index]
                def_index = int(input('Which position to defend?')) - 1
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
    main()