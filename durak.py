import random

# масти
SPADES = '♠'
HEARTS = '♥'
DIAMS = '♦'
CLUBS = '♣'

# достоинтсва карт
NOMINALS = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# поиск индекса по достоинству
NAME_TO_VALUE = {n: i for i, n in enumerate(NOMINALS)}

# карт в руке при раздаче
CARDS_IN_HAND_MAX = 6

N_PLAYERS = 2

# эталонная колода (каждая масть по каждому номиналу) - 36 карт
DECK = [(nom, suit) for nom in NOMINALS for suit in [SPADES, HEARTS, DIAMS, CLUBS]]


class Player:
    def __init__(self, index, cards):
        self.index = index
        self.cards = list(map(tuple, cards))

    def take_cards_from_deck(self, deck: list):
        lack = max(0, CARDS_IN_HAND_MAX - len(self.cards))
        n = min(len(deck), lack)
        self.add_cards(deck[:n])
        del deck[:n]
        return self

    def sort_hand(self):
        self.cards.sort(key=lambda c: (NAME_TO_VALUE[c[0]], c[1]))
        return self

    def add_cards(self, cards):
        self.cards += list(cards)
        self.sort_hand()
        return self

    def __repr__(self):
        return f"Player{self.cards!r}"

    def take_card(self, card):
        self.cards.remove(card)

    @property
    def n_cards(self):
        return len(self.cards)

    def __getitem__(self, item):
        return self.cards[item]


def rotate(l, n):
    return l[n:] + l[:n]


class Durak:
    NORMAL = 'normal'
    TOOK_CARDS = 'took_cards'
    GAME_OVER = 'game_over'

    def __init__(self, rng: random.Random = None):
        self.attacker_index = 0

        self.rng = rng or random.Random()

        self.deck = list(DECK)
        self.rng.shuffle(self.deck)

        self.players = [Player(i, []).take_cards_from_deck(self.deck)
                        for i in range(N_PLAYERS)]

        self.trump = self.deck[0][1]

        self.field = {}  # atack card: defend card
        self.winner = None

    def card_match(self, card1, card2):
        if card1 is None or card2 is None:
            return False
        n1, _ = card1
        n2, _ = card2
        return n1 == n2

    def can_beat(self, card1, card2):
        nom1, suit1 = card1
        nom2, suit2 = card2

        nom1 = NAME_TO_VALUE[nom1]
        nom2 = NAME_TO_VALUE[nom2]

        if suit2 == self.trump:
            return suit1 != self.trump or nom2 > nom1
        elif suit1 == suit2:
            return nom2 > nom1
        else:
            return False

    def can_add_to_field(self, card):
        if not self.field:
            return True

        for attack_card, defend_card in self.field.items():
            if self.card_match(attack_card, card) or self.card_match(defend_card, card):
                return True

        return False

    @property
    def attacking_cards(self):
        return list(filter(bool, self.field.keys()))

    @property
    def defending_cards(self):
        return list(filter(bool, self.field.values()))

    @property
    def any_unbeated_card(self):
        return any(c is None for c in self.defending_cards)

    @property
    def current_player(self):
        return self.players[self.attacker_index]

    @property
    def opponent_player(self):
        return self.players[(self.attacker_index + 1) % N_PLAYERS]

    def attack(self, card):
        assert not self.winner

        if not self.can_add_to_field(card):
            return False
        cur, opp = self.current_player, self.opponent_player
        cur.take_card(card)
        self.field[card] = None
        return True

    def defend(self, attacking_card, defending_card):
        assert not self.winner

        if self.field[attacking_card] is not None:
            return False
        if self.can_beat(attacking_card, defending_card):
            self.field[attacking_card] = defending_card
            self.opponent_player.take_card(defending_card)
            return True
        return False

    def attack_succeed(self):
        return any(def_card is None for _, def_card in self.field.items())

    def defend_variants(self, card):
        unbeaten_cards = [c for c in self.field.keys() if self.field[c] is None]
        return [i for i, att_card in enumerate(unbeaten_cards) if self.can_beat(att_card, card)]

    def finish_turn(self):
        assert not self.winner

        took_cards = False
        if self.attack_succeed():
            self._take_all_field()
            took_cards = True
        else:
            self.field = {}

        for p in rotate(self.players, self.attacker_index):
            p.take_cards_from_deck(self.deck)
            if not self.deck:
                self.winner = p.index
                return self.GAME_OVER

        if took_cards:
            return self.TOOK_CARDS
        else:
            self.attacker_index = self.opponent_player.index
            return self.NORMAL

    def _take_all_field(self):
        cards = self.attacking_cards + self.defending_cards
        self.opponent_player.add_cards(cards)
        self.field = {}
