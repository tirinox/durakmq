from durak import Durak


def card_2_str(card):
    return '[' + ''.join(card) + ']' if card is not None else '[  ]'


def cards_2_str(cards, enum=True):
    if enum:
        cards = (f"{i}. {card_2_str(c)}" for i, c in enumerate(cards, start=1))
    else:
        cards = (card_2_str(c) for c in cards)
    return ", ".join(cards)


def render_game(durak: Durak, my_index=None):
    print('-' * 100)

    print(f'Trump is [{durak.trump}], {len(durak.deck)} crd. in deck')

    for player in durak.players:
        marker = " <-- ATTACKS" if player.index == durak.attacker_index else ""
        me_marker = " (me) " if player.index == my_index else ""
        print(f"{player.index + 1}: {cards_2_str(player.cards)}{marker}{me_marker}")

    if durak.winner:
        print(f'GAME OVER! Player {durak.winner} is the winner!')
    elif durak.field:
        print()
        attacking_cards = cards_2_str(durak.attacking_cards(), enum=False)
        print(f'ATTACK: {attacking_cards}')
        defending_cards = cards_2_str(durak.defending_cards(), enum=False)
        print(f'DEFEND: {defending_cards}')

